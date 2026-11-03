"""Source-only A01 native-handoff inventory. Never invokes a CAD executable."""
import argparse
from collections import Counter, defaultdict
import copy
import json
import re
from pathlib import Path
import stage15_packages as packages
import stage11_assessment as common

ROOT = packages.ROOT
OUT = packages.OUT.parent / 'stage16'
need = common.need
BOARD_PATHS = {
    'K': 'boards/osc-core/osc-core.kicad_pcb',
    'JR': 'boards/osc-jack-right/osc-jack-right.kicad_pcb',
    'P': 'boards/osc-control/osc-control-layout.kicad_pcb',
}
SCHEMATIC = 'schematic/sheets/offset.kicad_sch'


def props(node):
    return {x[1]: x[2] for x in node if isinstance(x, list) and x and x[0] == 'property'}


def schematic_symbols(text):
    result = defaultdict(list)
    for node in packages.a.c.sexpr(text):
        if not isinstance(node, list) or not node or node[0] != 'symbol':
            continue
        p = props(node)
        if 'Reference' not in p:
            continue
        result[p['Reference']].append({'lib_id': packages.a.c.field(node, 'lib_id')[0],
            'unit': int(packages.a.c.field(node, 'unit')[0]), 'properties': p})
    return dict(result)


def board_packages(text, refs):
    """Read selected top-level footprint blocks, not the many routing objects.

    This intentionally accepts the committed KiCad tab-indented source format;
    unsupported formatting is an explicit missing observation, never parity.
    """
    result = {}
    for match in re.finditer(r'(?ms)^\t\(footprint .*?^\t\)', text):
        block = match.group(0)
        refmatch = re.search(r'\(property "Reference" "([^"]+)"', block)
        if not refmatch or refmatch[1] not in refs:
            continue
        node = packages.a.c.sexpr(block)
        ref = refmatch[1]
        need(ref not in result, 'duplicate native footprint ' + ref)
        pins = defaultdict(list)
        for pad in node:
            if isinstance(pad, list) and pad and pad[0] == 'pad' and pad[1]:
                net = packages.a.c.field(pad, 'net')
                raw = net[-1] if net else None
                pins[pad[1]].append({'raw_net': raw,
                    'normalized_net': None if raw is None or raw.startswith('unconnected-(') else raw,
                    'local_at': packages.a.c.field(pad, 'at')})
        result[ref] = {'footprint': node[1], 'properties': props(node),
            'at': packages.a.c.field(node, 'at'), 'layer': packages.a.c.field(node, 'layer'),
            'pads': dict(pins)}
    return result


def analyze(inventory, overlay, graph, cap_input, network_input, native_symbols, native_boards):
    old = inventory['packages']; places = overlay['placements']
    need(set(places) == (set(old) - set(packages.REPLACED)) | {'RN7101', 'RN7102'}, 'exact candidate package migration')
    need(len(places) == 86, '86 packages required')
    expected_aliases = {}
    for network, refs in [('RN7101', packages.REPLACED[:4]), ('RN7102', packages.REPLACED[4:])]:
        for ref, pair in zip(refs, packages.PAIRS):
            for oldpin, newpin in zip(('1', '2'), pair):
                expected_aliases[ref + ':' + oldpin] = network + ':' + newpin
                need(old[ref]['pins'][oldpin] == places[network]['pins'][newpin], 'network migration net identity')
    need(overlay['endpoint_aliases'] == expected_aliases, 'exact twelve endpoint aliases')
    rows = {}; nets = defaultdict(list); nc = []; gaps = []
    for ref, placement in sorted(places.items()):
        canonical = old.get(ref)
        attrs = canonical['attributes'] if canonical else {}
        cap = cap_input['parts'].get(ref)
        network = ref in network_input['networks']
        mpn = cap['MPN'] if cap else network_input['MPN'] if network else attrs.get('MPN') or None
        manufacturer = 'KEMET' if cap else network_input['manufacturer'] if network else attrs.get('Manufacturer') or None
        if canonical:
            need(placement['pins'] == canonical['pins'], 'retained logical pins changed ' + ref)
        path = None if cap else placement['source']
        if path:
            need((ROOT/path).is_file(), 'missing declared footprint ' + path)
            pad_numbers = sorted(packages.a.c.footprint_pads(path))
            need(set(pad_numbers) == set(placement['pins']), 'footprint/source pin coverage ' + ref)
        else:
            pad_numbers = None
        native = native_symbols.get(ref, [])
        lib_ids = sorted({u['lib_id'] for u in native})
        symbol_paths = ['symbols/src/' + name.split(':')[-1] + '.kicad_sym' for name in lib_ids]
        for p in symbol_paths:
            need((ROOT/p).is_file(), 'missing captured symbol source ' + p)
        reasons = []
        if mpn is None:
            reasons.append('EXACT_MPN_UNSELECTED')
        if cap:
            reasons.extend(['CANDIDATE_POLARIZED_CAPACITOR_SYMBOL_UNBOUND', 'CANDIDATE_KEMET_FOOTPRINT_NOT_MATERIALIZED'])
        if network:
            reasons.append('CANDIDATE_NETWORK_SYMBOL_NOT_MATERIALIZED')
        if canonical:
            need(sorted(u['unit'] for u in native) == sorted(canonical['units']), 'canonical schematic unit coverage ' + ref)
            units = copy.deepcopy(canonical['unit_records'])
            if cap:
                for u in units:
                    u['value'] = str(cap['nominal_F']) + ' F'
                    u['attributes'].update(MPN=mpn, Manufacturer=manufacturer)
        else:
            units = [{'unit': e['element'], 'pins': {pin: placement['pins'][pin] for pin in e['pins']},
                      'value': '100000 Ω', 'replaces': e['replaces'], 'connected': e['connected']}
                     for e in overlay['elements'] if e['ref'] == ref]
        rows[ref] = {'ref': ref, 'pins': placement['pins'], 'selected_mpn': mpn,
            'selected_manufacturer': manufacturer,
            'identity_status': 'EXPLICIT_CANDIDATE_OVERRIDE' if cap or network else 'EXACT_CAPTURED_IDENTITY' if mpn else 'UNRESOLVED',
            'supplier_order_code': cap.get('supplier_order_code') if cap else network_input.get('supplier_order_code') if network else attrs.get('LCSC') or None,
            'canonical': None if not canonical else {'mpn': attrs.get('MPN') or None,
                'manufacturer': attrs.get('Manufacturer') or None, 'footprint': canonical['footprint'],
                'units': canonical['units'], 'values': [u['value'] for u in canonical['unit_records']],
                'board': canonical['current_board']},
            'footprint': {'path': path, 'captured_path': placement.get('captured_source_footprint_only', path),
                'status': 'MISSING_CANDIDATE_ASSET_SCALAR_GEOMETRY_ONLY' if cap else 'CANDIDATE_SOURCE_ONLY' if network else 'CAPTURED_LIBRARY_ASSET_NOT_NATIVE_CANDIDATE_BINDING',
                'pad_numbers': pad_numbers, 'native_ready': False},
            'symbol': {'paths': [] if cap or network else symbol_paths, 'canonical_paths': symbol_paths,
                'canonical_lib_ids': lib_ids,
                'status': 'MISSING_EXACT_CANDIDATE_BINDING' if cap or network else 'CAPTURED_SYMBOL_ONLY'},
            'placement': placement, 'unit_records': units,
            'extra_package_pins_outside_element_units': {'9': 'AGND'} if network else {},
            'gaps': reasons}
        for reason in reasons:
            gaps.append({'ref': ref, 'reason': reason})
        for pin, net in placement['pins'].items():
            endpoint = ref + ':' + pin
            if net is None:
                nc.append(endpoint)
            else:
                nets[net].append(endpoint)
    connected = {e for group in nets.values() for e in group}
    need(connected == set(graph['source_endpoints']) and set(nc) == set(graph['NC_source_endpoints']), 'graph endpoint partition')
    for ref, row in rows.items():
        for pin, net in row['pins'].items():
            node = graph['nodes'][ref + ':' + pin]
            need(node['net'] == net and node['pad_xyz_mm'] == row['placement']['pads_xyz_mm'][pin][0], 'graph pin geometry ' + ref + ':' + pin)
    comparisons = {}
    for ref in sorted(set(old) | set(rows)):
        canonical = old.get(ref)
        observed = native_boards.get(canonical['current_board'], {}).get(ref) if canonical else None
        target = rows.get(ref)
        observations = []
        if observed and target:
            observed_pins = {p: vals[0]['normalized_net'] for p, vals in observed['pads'].items()}
            observations = [{'field': 'pins', 'matches_candidate': observed_pins == target['pins']},
                {'field': 'MPN', 'matches_candidate': (observed['properties'].get('MPN') or None) == target['selected_mpn']}]
        comparisons[ref] = {'canonical_board': canonical['current_board'] if canonical else None,
            'observed_native_footprint': observed, 'canonical_schematic_units': native_symbols.get(ref, []),
            'status': 'REMOVED_IN_CANDIDATE' if target is None else 'CANDIDATE_NEW_NOT_IN_CANONICAL' if canonical is None else 'CANONICAL_ASSET_NOT_BOUND_TO_CANDIDATE',
            'field_observations': observations,
            'placement_parity': 'NOT_ESTABLISHED: canonical board coordinates/frame are not candidate split-board adoption'}
    counts = {'packages': len(rows), 'physical_pins_including_NC': sum(len(r['pins']) for r in rows.values()),
        'connected_pins': len(connected), 'NC_pins': len(nc), 'unit_records': sum(len(r['unit_records']) for r in rows.values()),
        'power_return_endpoints': sum(len(v) for n, v in nets.items() if n in ('AGND', '+12V', '-12V', '+5V')),
        'unresolved_exact_MPNs': sum(r['selected_mpn'] is None for r in rows.values()),
        'candidate_boards': dict(Counter(r['placement']['board'] for r in rows.values()))}
    need((counts['physical_pins_including_NC'], counts['unit_records'], counts['power_return_endpoints']) == (291, 120, 108), 'candidate counts')
    transport = {key: copy.deepcopy(graph[key]) for key in ('headers', 'DIN_pinmap', 'terminal_wires',
        'upstream_power_boundaries', 'wires', 'edges', 'nodes', 'local_net_groups', 'counts',
        'source_endpoints', 'NC_source_endpoints', 'source_evidence')}
    transport.update(status='SOURCE_ALLOCATION_ONLY_NOT_NATIVE_MATERIALIZED', native_ready=False,
        inventory_scope='Added connectors, contacts, housings, terminal wiring and allocated edges are separate from the86 circuit packages. This is not a complete procurement or assembled-harness BOM.',
        materialization_gap='Native connector symbols/footprints, split-board placement, harness assembly/termination and pin-net parity remain unbound; no materialization or electrical acceptance claimed.',
        length_scope='Allocated developed lengths and wire-cut budgets are not obstacle-aware routed copper or as-built wire measurements.')
    gaps.append({'ref': 'TRANSPORT_ASSEMBLY', 'reason': 'CONNECTOR_HARNESS_NATIVE_MATERIALIZATION_UNBOUND'})
    return {'status': 'PREPARATION_ONLY_NOT_NATIVE_READY', 'packages': rows,
        'nets': {n: sorted(v) for n, v in sorted(nets.items())}, 'NC_endpoints': sorted(nc),
        'counts': counts, 'endpoint_aliases': overlay['endpoint_aliases'], 'network_elements': overlay['elements'],
        'network_extra_pin_policy': overlay['exposed_pad'], 'network_unused_policy': overlay['unused_elements'],
        'capacitor_overrides': {r: {'selected': q, 'geometry': places[r]['candidate_geometry_source'],
            'pads_xyz_mm': places[r]['pads_xyz_mm'], 'captured_footprint_is_not_candidate': True}
            for r, q in cap_input['parts'].items()},
        'native_comparison': comparisons, 'gaps': gaps,
        'retained_metadata_findings': inventory['metadata_findings'],
        'transport_contract': transport,
        'transport_scope': '86 source circuit packages plus separately inventoried source transport contract. Candidate connector/wiring graph is included, but full assembly BOM and native connector materialization are not claimed.',
        'unit_scope': '120 logical unit records include eight network resistor elements, two unused. EP9 is a separate physical shield pin outside the four resistor element units, not an omitted connection.',
        'native_comparison_scope': 'Read-only text extraction of committed schematic and canonical boards. This is not a native netlist export, ERC, DRC or native candidate parity. Field comparisons are literal string/pin comparisons only: historical hashed internal net names may require an independently evidenced alias map; a literal mismatch is NOT classified as an electrical defect. Matching isolated fields cannot bind old boards to new split-board geometry.',
        'actual_copper_scope': 'All candidate graph lengths are allocation proxies. No routed copper or electrical acceptance inferred.',
        'native_ready': False, 'hardware_acceptance': False, 'component_geometry_changed': False,
        'native': 'NOT RUN', 'CAD': 'NOT RUN', 'ERC': 'NOT RUN', 'DRC': 'NOT RUN', 'simulation': 'NOT RUN', 'physical': 'NOT RUN'}


def build():
    base = packages.OUT.parent
    files = [base/'stage10/inventory-report.json', base/'stage15/package-report.json', base/'stage15/interfaces-report.json',
             base/'stage13/capacitor-input.json', base/'stage15/package-input.json']
    inputs = [json.loads(p.read_text()) for p in files]
    for source in inputs[:3]:
        common.bindings(source)
    symbols = schematic_symbols((ROOT/SCHEMATIC).read_text())
    refs = set(inputs[0]['packages']) | set(inputs[1]['placements'])
    boards = {key: board_packages((ROOT/path).read_text(), refs) for key, path in BOARD_PATHS.items()}
    r = analyze(*inputs, symbols, boards)
    files += [ROOT/SCHEMATIC] + [ROOT/p for p in BOARD_PATHS.values()]
    files += [base/'stage13/package-report.json', base/'stage15/paths-report.json', base/'stage15/rebudget-report.json',
              ROOT/'design/spec/modules/offset.py', ROOT/'design/standard/electrical-standard.json', ROOT/'design/standard/parts-shortlist.json',
              ROOT/'design/grid/placements.lock.json', Path(__file__), Path(__file__).with_name('test_stage16_inputs.py'),
              Path(packages.__file__), Path(common.__file__), Path(packages.a.__file__), Path(packages.a.c.__file__),
              ROOT/'scripts/architecture278/populated_mechanics.py']
    for row in r['packages'].values():
        files += [ROOT/p for p in row['symbol']['canonical_paths']]
        files += [ROOT/p for p in (row['footprint']['path'], row['footprint']['captured_path']) if p]
    r['source_sha256'] = {str(p.relative_to(ROOT)): common.digest(p) for p in sorted(set(files))}
    r['native_asset_paths'] = {'schematic': SCHEMATIC, 'canonical_boards': BOARD_PATHS}
    return r


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    r = build(); text = json.dumps(r, sort_keys=True, indent=2, allow_nan=False) + '\n'
    dest = OUT/'inputs-report.json'
    if args.check:
        need(dest.read_text() == text, 'stale Stage16 input report')
    else:
        OUT.mkdir(exist_ok=True); dest.write_text(text)
    print('PASS source-only86-package handoff inventory; native readiness BLOCKED')


if __name__ == '__main__':
    main()
