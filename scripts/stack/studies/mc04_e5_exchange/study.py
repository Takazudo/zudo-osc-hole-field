"""One bounded room-only exchange at the frozen U4527 diagnostic point."""
import argparse
import copy
from decimal import Decimal
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
SPEC = Path(__file__).with_name('spec.json')
module = importlib.util.spec_from_file_location('e5_diagnostic_dependency', ROOT / 'scripts/stack/studies/mc04_e5_blockers/study.py')
diag = importlib.util.module_from_spec(module)
module.loader.exec_module(diag)
r1, sg, rp, lg = diag.r1, diag.sg, diag.rp, diag.lg
MOVING = ('U4527', 'U4517', 'R4577')
KEYS = {('K', ref) for ref in MOVING}
PAIR_CAP = 100000
POINT = (214, 2.25, 1.591, -1.591)


def within25(delta):
    # Exact decimal comparison of the retained four-decimal coordinate values.
    values = [Decimal(str(v)) for v in delta]
    return all(v.is_finite() for v in values) and sum(v*v for v in values) <= Decimal(625)


def translate(fp, dx, dy):
    out = copy.deepcopy(fp)
    out['origin'] = [round(fp['origin'][0] + dx, 4), round(fp['origin'][1] + dy, 4)]
    out['courtyard'] = [round(v, 4) for v in rp.shift(fp['courtyard'], dx, dy)]
    for pad in out['pads']:
        pad['bbox'] = [round(v, 4) for v in rp.shift(pad['bbox'], dx, dy)]
        pad['center'] = sg.centre(pad['bbox'])
    return out


def mutual(a, b, gap):
    return r1.mutual_conflict((a, b), gap) or r1.mutual_conflict((b, a), gap)


def fixed_hits(scene, fp, dx=0, dy=0, excluded=None):
    excluded = KEYS if excluded is None else set(excluded)
    if excluded != KEYS:
        raise ValueError('only the exact three exchange models may be excluded')
    if fp['ref'] not in MOVING or fp['side'] != 'B':
        raise ValueError('wrong exchange identity or face')
    return scene._violations('K', fp, dx, dy, excluded)


def ledger(report, old_ledger, expected):
    identities = {key: [row for row in report[key] if row['ref'] in expected['refs']]
                  for key in ('physical_packages', 'package_units')}
    if identities != expected['rows']:
        raise ValueError('complete package/unit/companion/analog-anchor identities changed')
    resistor = next(p for p in identities['physical_packages'] if p['ref'] == 'R4577')
    if resistor['mpn'] != '':
        raise ValueError('R4577 exact MPN must remain blank')
    original = []
    for net, rows in old_ledger.items():
        for row in rows:
            original.append({'net': net, **row, 'geometry_scope': 'explicitly movable whole package'
                             if row['ref'] in MOVING else 'frozen counterpart'})
    movable = [r for r in original if r['geometry_scope'] == 'explicitly movable whole package']
    if len(original) != 45 or len(movable) != 1 or (movable[0]['net'], movable[0]['ref'], movable[0]['unit'], movable[0]['pin']) != ('RISE', 'U4517', 4, '12'):
        raise ValueError('original 45-contact ledger or one movable annotation changed')
    # All signal-net contacts of the two newly movable bodies. Supplies are retained
    # in complete unit identities, not misrepresented as local analog signal nets.
    nets = {n for row in report['package_units'] if row['ref'] in ('U4517', 'R4577')
            for n in row['pins'].values() if isinstance(n, str) and n.startswith('/E5/')}
    expanded = {net: [] for net in sorted(nets)}
    for row in report['package_units']:
        for pin, net in row['pins'].items():
            if net in expanded:
                expanded[net].append({'ref': row['ref'], 'unit': row['unit'], 'pin': pin,
                    'role': row['role'], 'geometry_scope': 'explicitly movable whole package'
                    if row['ref'] in MOVING else 'frozen counterpart'})
    return {'original_45_contacts': original, 'original_movable_contacts': 1, 'original_frozen_contacts': 44,
            'expanded_signal_contacts': expanded, 'complete_source_identities': identities,
            'R4577_MPN': '', 'R4577_scope': 'Source 1kohm FALL_BASE_LIMIT analog boundary; retained R0603 model is not exact-body qualification',
            'physical_timing_analog_decoupling_acceptance': 'NOT_ESTABLISHED'}


def validate_diagnostic(receipt):
    if len(receipt['diagnostic_points']) != 7203:
        raise ValueError('diagnostic point count changed')
    unique = [p for p in receipt['diagnostic_points'] if p['all_obstructions_are_named_accepted_bodies'] is not None]
    if len(unique) != 1:
        raise ValueError('expected exactly one accepted-body-only diagnostic point')
    row = unique[0]
    if (row['target'], row['offset_index'], row['radius_mm'], row['diagnostic_offset_mm'], row['all_obstructions_are_named_accepted_bodies']) != ('U4527', 214, 2.25, [1.591, -1.591], ['R4577', 'U4517']):
        raise ValueError('frozen diagnostic point changed')
    hits = [receipt['blockers'][key] for key in row['blocker_ids']]
    if len(hits) != 16 or {r.get('ref') for r in hits} != {'R4577', 'U4517'} or any(r['class'] != 'accepted_body' for r in hits):
        raise ValueError('diagnostic blocker attribution changed')
    return row


def candidates(scene, fp, source_origin, probe, offsets):
    eligible, tests = [], []
    if len(offsets) > 2401:
        raise ValueError('individual enumeration cap exceeded')
    for index, (radius, dx, dy) in enumerate(offsets):
        moved = translate(fp, dx, dy)
        cumulative = [round(moved['origin'][i] - source_origin[i], 4) for i in (0, 1)]
        row = {'offset_index': index, 'radius_mm': radius, 'shift_from_accepted_mm': [dx, dy],
               'shift_from_original_mm': cumulative}
        if radius > 25 or radius < 0 or not within25((dx, dy)) or not within25(cumulative):
            row['disposition'] = 'FILTERED_DISPLACEMENT_BOUND'
        else:
            hits = fixed_hits(scene, fp, dx, dy)
            if mutual(moved, probe, scene.field.gap):
                hits = sorted(set(hits + ['fixed U4527 probe']))
            row['blockers'] = hits
            row['disposition'] = 'BLOCKED' if hits else 'INDIVIDUAL_ROOM_ONLY'
            if not hits:
                eligible.append({'offset_index': index, 'geometry': moved, 'shift_from_accepted_mm': [dx, dy],
                                 'shift_from_original_mm': cumulative})
        tests.append(row)
    return eligible, tests


def validate_final(scene, bodies):
    if {p['ref'] for p in bodies} != set(MOVING) or len(bodies) != 3:
        raise ValueError('final validation requires exactly all three models')
    for body in bodies:
        if fixed_hits(scene, body):
            raise ValueError('final exchange overlaps frozen scene')
    for index, a in enumerate(bodies):
        for b in bodies[index + 1:]:
            if mutual(a, b, scene.field.gap):
                raise ValueError('final exchange mutual conflict')


def pair_search(scene, probe, left, right, cap=PAIR_CAP):
    if not 1 <= cap <= PAIR_CAP:
        raise ValueError('invalid pair cap')
    tested = 0
    for a in left:
        for b in right:
            if tested == cap:
                return {'status': 'SEARCH_CAP_REACHED', 'pair_checks': tested}
            tested += 1
            if not mutual(a['geometry'], b['geometry'], scene.field.gap):
                bodies = [probe, a['geometry'], b['geometry']]
                validate_final(scene, bodies)
                return {'status': 'ROOM_EXCHANGE_WITNESS_ONLY', 'pair_checks': tested,
                        'witness_offset_indices': [a['offset_index'], b['offset_index']],
                        'candidate_geometry': bodies}
    return {'status': 'NO_PAIR_FIT_IN_DECLARED_DOMAIN', 'pair_checks': tested}


def experiment(scene, origins, offsets):
    probe = translate(scene.bodies['K', 'U4527'], POINT[2], POINT[3])
    if fixed_hits(scene, probe):
        return {'status': 'SOURCE_OR_PREDICATE_MISMATCH', 'reason': 'frozen U4527 probe fails against nonmoving scene', 'pair_checks': 0}
    lists, records = {}, {}
    for ref in ('U4517', 'R4577'):
        lists[ref], records[ref] = candidates(scene, scene.bodies['K', ref], origins[ref], probe, offsets)
    counts = {ref: {'enumerated': len(records[ref]), 'displacement_filtered': sum(r['disposition'] == 'FILTERED_DISPLACEMENT_BOUND' for r in records[ref]),
                    'individual_room': len(lists[ref])} for ref in lists}
    result = {'individual_tests': records, 'individual_counts': counts}
    if not all(lists.values()):
        result.update(status='NO_INDIVIDUAL_ROOM_FOR_EXCHANGE', pair_checks=0)
    else:
        result.update(pair_search(scene, probe, lists['U4517'], lists['R4577']))
    return result


def run(root=ROOT):
    spec = json.loads(SPEC.read_text());r1.verify_pins(root, spec)
    receipt = json.loads((root / spec['diagnostic_receipt']).read_text());point = validate_diagnostic(receipt)
    frozen = json.loads((root / 'scripts/stack/studies/mc04_r1/spec.json').read_text())
    gate = json.loads((root / 'design/stack/geometry/links/link-gate.json').read_text())
    rows = gate['replacement']['footprints']
    for index, ref in ((85, 'U4517'), (89, 'U4527'), (377, 'R4577')):
        if rows[index]['ref'] != ref or rows[index]['board'] != 'K':
            raise ValueError('historical search order changed')
    inp = lg.load_inputs(root)
    origins = {f['ref']: list(f['origin']) for f in inp['ci']['boards']['K'] if f['ref'] in MOVING}
    inp['ci']['boards'], accepted = r1.reconstruct(inp['ci']['boards'], rows, frozen['replacement'])
    unresolved = {(r['board'], r['ref']) for r in rows if r['new'] is None}
    if len(accepted) != 412 or len(unresolved) != 26:
        raise ValueError('retained scene counts changed')
    model = lg.GateModel(inp, lg.gate_sites(inp))
    scene = r1.Scene(SimpleNamespace(model=model, opts=inp['opts']), inp, gate['links'])
    for ref in MOVING:
        fp = scene.bodies['K', ref]
        expected = spec['geometry'][ref]
        if fp['origin'] != expected['current_origin'] or fp['side'] != expected['face'] or fp['angle'] != expected['angle'] or origins[ref] != expected['original_origin']:
            raise ValueError('frozen moving geometry changed: ' + ref)
    companions = {ref: scene.bodies['K', ref] for ref in spec['frozen_geometry']}
    for ref, fp in companions.items():
        e = spec['frozen_geometry'][ref]
        if fp['origin'] != e['origin'] or fp['side'] != e['face'] or fp['angle'] != e['angle']:
            raise ValueError('frozen companion/analog anchor changed: ' + ref)
    # Reproduce only the already recorded diagnostic point, not all 7203 points.
    fixed = {(board, ref) for board, refs in model.panel.items() for ref in refs}
    fixed.update(key for key in scene.bodies if key[1] in {p['ref'] for p in inp['raw']['lock']['placements']})
    d = diag.DiagnosticScene(scene, accepted, unresolved, fixed)
    reproduced = d.blockers('K', scene.bodies['K', 'U4527'], POINT[2], POINT[3])
    if reproduced != point['blocker_ids'] or any(d.registry[key] != receipt['blockers'][key] for key in reproduced):
        raise ValueError('SOURCE_OR_PREDICATE_MISMATCH: exact diagnostic blockers do not reproduce')
    report = json.loads((root / 'design/reports/io-partition.json').read_text())
    logic = json.loads((root / spec['logic_receipt']).read_text())
    interfaces = ledger(report, logic['external_contacts'], spec['identities'])
    offsets = rp.ring_offsets(.25, 24, 25)
    if len(offsets) != 2401 or offsets[214] != (2.25, 1.591, -1.591):
        raise ValueError('retained ring ordering changed')
    result = experiment(scene, origins, offsets)
    result.update({'source_commit': spec['source_commit'], 'engineering_commit': spec['engineering_commit'], 'inputs_sha256': spec['sha256'],
        'interface_ledger': interfaces, 'frozen_companion_and_analog_anchor_geometry': companions,
        'historical_novelty': 'U4517 row85 was already placed before U4527 row89; R4577 row377 is only a final-scene blocker, not a cause of that historical failure.',
        'canonical_unresolved': 26, 'canonical_changes': [], 'adopted_placements': [],
        'scope': 'Room-only necessary condition. No source net/part changes, timing/analog/decoupling/route acceptance, hardware adoption, native, DRC/fill or manufacturing.'})
    r1.verify_pins(root, spec)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():parser.error('output already exists; no attempt consumed')
    if not args.output.resolve().is_relative_to((ROOT/'.circuit-cache').resolve()):parser.error('output must be in ignored cache')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:
        try:result=run()
        except Exception as exc:
            json.dump({'status':'ADMISSION_OR_EXECUTION_FAILED','error':str(exc)},stream);stream.write('\n');raise
        json.dump(result,stream,indent=2);stream.write('\n')
    print(result['status'])
    completed = {'ROOM_EXCHANGE_WITNESS_ONLY', 'NO_INDIVIDUAL_ROOM_FOR_EXCHANGE',
                 'NO_PAIR_FIT_IN_DECLARED_DOMAIN', 'SEARCH_CAP_REACHED'}
    return 0 if result['status'] in completed else 1


if __name__=='__main__':sys.exit(main())
