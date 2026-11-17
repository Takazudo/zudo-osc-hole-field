"""Frozen E5 NAND graph and timing-evidence coverage, not physical timing acceptance."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name('manifest.json')
REPORT = 'design/reports/io-partition.json'
LOGIC = 'design/spec/modules/envelope_logic.py'
REFS = ('U4524', 'U4526', 'U4527')
INPUTS = ('STAGE_FALL', 'FALL', 'RISE', 'HOLD_N', 'TOP_RAW', 'CURVED', 'READY')
PINS = (('1', '2', '3'), ('4', '5', '6'), ('9', '10', '8'), ('12', '13', '11'))
ROLES = {'U4524': (55, 57, 58, 60), 'U4526': (66, 68, 69, 70), 'U4527': (71, 72, 73, 74)}
OWNERS = ('sn74hc00dr', 'sn74hc74dr', 'sn74hc14dr')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins(root, manifest):
    for path, sha in manifest['sha256'].items():
        if digest(root / path) != sha:
            raise ValueError('source pin changed: ' + path)


def local(net):
    if not isinstance(net, str) or not net.startswith('/E5/'):
        raise ValueError('unexpected cluster signal net: ' + str(net))
    return net[4:]


def validate_pin_map(owner):
    rows = owner['pin_maps']
    if len(rows) != 1 or rows[0]['symbol'] != 'SN74HC00DR':
        raise ValueError('unexpected NAND owner pin map')
    pins = {p['symbol_pin']: p for p in rows[0]['pins']}
    if len(pins) != len(rows[0]['pins']) or set(pins) != {str(n) for n in range(1, 15)}:
        raise ValueError('incomplete or duplicate NAND pin map')
    for unit, (a, b, z) in enumerate(PINS, 1):
        for pin, function in ((a, f'{unit}A input'), (b, f'{unit}B input'), (z, f'{unit}Y NAND output')):
            if pins[pin]['footprint_pad'] != pin or pins[pin]['function'] != function:
                raise ValueError('NAND physical pin function changed')


def extract(report):
    packages = [p for p in report['physical_packages'] if p['ref'] in REFS]
    if len(packages) != 3 or {p['ref'] for p in packages} != set(REFS):
        raise ValueError('missing/duplicate cluster package')
    for p in packages:
        if p['mpn'] != 'SN74HC00DR' or p['instance'] != 'E5' or p['units'] != [1, 2, 3, 4, 5]:
            raise ValueError('wrong complete package identity')
    rows = [p for p in report['package_units'] if p['ref'] in REFS]
    keyed = {(p['ref'], p['unit']): p for p in rows}
    if len(keyed) != 15 or len(rows) != 15:
        raise ValueError('incomplete/duplicate package units')
    gates = []
    for ref in REFS:
        if keyed[ref, 5]['pins'] != {'7': 'AGND', '14': '+5V'}:
            raise ValueError('supply unit changed')
        for unit, (a, b, z) in enumerate(PINS, 1):
            p = keyed[ref, unit]
            if p['role'] != 'envelope:NAND' + str(ROLES[ref][unit - 1]) or set(p['pins']) != {a, b, z}:
                raise ValueError('wrong packed gate role or terminals')
            gates.append({'ref': ref, 'unit': unit, 'role': p['role'],
                          'inputs': [local(p['pins'][a]), local(p['pins'][b])],
                          'output': local(p['pins'][z]), 'physical_pins': {'inputs': [a, b], 'output': z}})
    nets = {n for g in gates for n in [*g['inputs'], g['output']]}
    external = {net: [] for net in sorted(nets)}
    for p in report['package_units']:
        if p['ref'] in REFS:
            continue
        for pin, net in p['pins'].items():
            if isinstance(net, str) and net.startswith('/E5/') and local(net) in nets:
                external[local(net)].append({'ref': p['ref'], 'unit': p['unit'], 'pin': pin, 'role': p['role']})
    for rows in external.values():
        rows.sort(key=lambda x: (x['ref'], x['unit'], x['pin']))
    # Retain known beyond-cluster sinks; never imply this three-package set is closed.
    required = {'L069': ('U4528', 2, '5'), 'L074': ('U4528', 1, '1'),
                'HOLD_ENABLE': ('D4535', 1, '2'), 'RISE_LINEAR': ('D4527', 1, '2'),
                'STAGE_HIGH': ('U4547', 3, '10')}
    for net, contact in required.items():
        if not any((p['ref'], p['unit'], p['pin']) == contact for p in external.get(net, [])):
            raise ValueError('required external contact absent: ' + net)
    return gates, external


def order_graph(gates, inputs):
    outputs = [g['output'] for g in gates]
    if len(outputs) != len(set(outputs)) or set(outputs) & set(inputs):
        raise ValueError('duplicate driver or input/output alias')
    boundary = {n for g in gates for n in g['inputs']} - set(outputs)
    if boundary != set(inputs):
        raise ValueError('missing/unexpected boundary input')
    depths = {n: 0 for n in inputs}
    ordered, pending = [], list(gates)
    while pending:
        ready = [g for g in pending if all(n in depths for n in g['inputs'])]
        if not ready:
            raise ValueError('cyclic or unresolved NAND graph')
        for g in ready:
            depths[g['output']] = 1 + max(depths[n] for n in g['inputs'])
            ordered.append(g)
            pending.remove(g)
    return ordered, {n: depths[n] for n in outputs}


def evaluate_graph(ordered, values):
    values = dict(values)
    for g in ordered:
        values[g['output']] = not all(values[n] for n in g['inputs'])
    return values


def compare(ordered, expression_module):
    counts = dict(STAGE_HIGH=0, HOLD_ENABLE=0, RISE_LINEAR=0, L074=0)
    for bits in itertools.product((False, True), repeat=len(INPUTS)):
        boundary = dict(zip(INPUTS, bits))
        actual = evaluate_graph(ordered, boundary)
        source = dict(boundary, HOLD=not boundary['HOLD_N'])
        for out, expr, invert in (('STAGE_HIGH', 'STAGE_HIGH', False), ('HOLD_ENABLE', 'HOLD_ENABLE', False),
                                  ('RISE_LINEAR', 'RISE_LINEAR', False), ('L074', 'RISE_CURVE', True)):
            expected = expression_module.evaluate(expression_module.EXPRESSIONS[expr], source)
            if invert:
                expected = not expected
            if actual[out] != expected:
                raise ValueError('Boolean correspondence failed: ' + out + ' ' + str(boundary))
            counts[out] += 1
    return counts


def timing_coverage(owners):
    observations = []
    for name, bundle in owners.items():
        sources = {s['source_id']: s for s in bundle['sources']['sources']}
        for fact in bundle['facts']['facts']:
            if fact['class'] not in ('TRANSIENT', 'RECOMMENDED_OPERATION', 'GUARANTEED_ELECTRICAL'):
                continue
            source = sources[fact['source_id']]
            observations.append({'device': name, 'fact': fact, 'source_record': source,
                                 'project_applicability': 'NOT_ESTABLISHED'})
    return {'retained_owner_observations': observations,
            'missing_project_acceptance': ['Applicability of HC00 propagation/output-transition table rows to actual load and corners; switching-test numeric CL remains unspecified',
                'Cascaded HC00 input edges below the source switching-test 6ns condition are not established by its 19ns output-transition maximum',
                'Applicability of HC74 D setup/hold table requirements; minimum CLK-to-Q and contamination-delay evidence remain missing',
                'actual clock/reset corners and jitter/skew',
                'actual output load, input slew and operating voltage/temperature',
                'receiver-specific allowable glitches and asynchronous raw-input behavior',
                'trace/via parasitics, decoupling and return constraints'],
            'physical_propagation_delay_ns': None, 'setup_slack_ns': None, 'hold_slack_ns': None,
            'permitted_incremental_trace_mm': None, 'permitted_incremental_capacitance_pF': None,
            'acceptance': 'NOT_ESTABLISHED; gate depth is not a delay or layout allowance'}


def run(root=ROOT):
    manifest = json.loads(MANIFEST.read_text())
    verify_pins(root, manifest)
    owners = {name: {kind: json.loads((root / '.claude/skills' / ('component-ti-' + name) / (kind + '.json')).read_text())
                     for kind in ('facts', 'sources', 'pin-map')} for name in OWNERS}
    validate_pin_map(owners['sn74hc00dr']['pin-map'])
    gates, external = extract(json.loads((root / REPORT).read_text()))
    ordered, depths = order_graph(gates, INPUTS)
    spec = importlib.util.spec_from_file_location('frozen_e5_logic', root / LOGIC)
    expressions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(expressions)
    counts = compare(ordered, expressions)
    result = {'source_commit': manifest['source_commit'], 'engineering_commit': manifest['engineering_commit'],
              'source_history': manifest['source_history'], 'inputs_sha256': manifest['sha256'],
              'packages': list(REFS), 'gate_units': gates, 'boundary_inputs': list(INPUTS),
              'external_contacts': external, 'maximum_gate_counts_from_boundary': depths,
              'boolean_assignments': 128, 'checked_output_counts': counts,
              'assignment_scope': 'All Boolean combinations, including unreachable state combinations; zero-delay steady-state equivalence only',
              'timing_coverage': timing_coverage(owners),
              'limitations': 'No hazards, metastability, analog behavior, physical timing, placement, routing, native, adoption or manufacturing acceptance. No physical clock inference from the ideal 50us SPICE fixture.'}
    verify_pins(root, manifest)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.output:
        if args.output.exists() or args.output.is_symlink():
            parser.error('output already exists; refusing to consume an attempt')
        target = args.output.resolve()
        if not target.is_relative_to((ROOT / '.circuit-cache').resolve()):
            parser.error('output must be a new file within this worktree ignored cache')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive reservation precedes all analysis, including a competing creator.
        with args.output.open('x') as stream:
            try:
                result = run()
            except Exception as exc:
                json.dump({'status': 'ADMISSION_OR_EXECUTION_FAILED', 'error': str(exc)}, stream)
                stream.write('\n')
                raise
            json.dump(result, stream, indent=2)
            stream.write('\n')
    else:
        print(json.dumps(run(), indent=2))


if __name__ == '__main__':
    main()
