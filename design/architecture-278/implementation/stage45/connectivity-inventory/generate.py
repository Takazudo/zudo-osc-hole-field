"""Source-only inventory of accepted native evidence; never edits a board."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/pcbgen'))
from netlist import read_netlist

S44 = 'design/architecture-278/implementation/stage44/b2-specific'
SNAPSHOT = '.circuit-cache/stage44-b2-fresh/connectivity-passfresh.json'
BOARD = '.circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb'
BOARD_HASH = 'd1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
NETLISTS = {'JL': 'osc-jack-left', 'JR': 'osc-jack-right', 'K': 'osc-core',
            'P': 'osc-control', **{f'O{i}': f'osc-octave-{i}' for i in range(1, 6)},
            'EL': 'osc-stage-optical'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2) + '\n'


def read(path):
    return json.loads((ROOT / path).read_text())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def export_snapshot():
    """Compact complete open partitions, not an invented replacement ratsnest."""
    bindings = read(S44 + '/evidence/local-artifact-bindings.json')
    require(sha(ROOT / SNAPSHOT) == bindings[SNAPSHOT]['sha256'], 'snapshot binding')
    require(sha(ROOT / BOARD) == BOARD_HASH, 'board binding')
    snapshot = read(SNAPSHOT)
    require(snapshot['board_sha256'] == BOARD_HASH, 'snapshot board')
    groups = {n: g for n, g in snapshot['groups'].items() if len(g) > 1}
    keys = {k for groupset in groups.values() for group in groupset for k in group}
    return {'source': SNAPSHOT, 'source_sha256': sha(ROOT / SNAPSHOT),
            'board_sha256': BOARD_HASH, 'native_open_edges': snapshot['native_open_edges'],
            'groups': groups, 'objects': {k: snapshot['objects'][k] for k in sorted(keys)}}


def export_geometry():
    sys.path.insert(0, str(ROOT / 'design/architecture-278/implementation/stage40/mult-copper-plan'))
    import native
    require(sha(ROOT / BOARD) == BOARD_HASH, 'geometry board binding')
    board = native.parse((ROOT / BOARD).read_text())
    projection = export_snapshot()
    keys = {(o['ref'], o['pin']) for o in projection['objects'].values() if o['kind'] == 'pad'}
    pads = {ref + ':' + p['pin']: p for ref, fp in board['footprints'].items()
            for p in fp['pads'] if (ref, p['pin']) in keys}
    proof = read(S44 + '/evidence/branches.json')
    anchors = [v for v in proof['via_contacts'] if not v['retire_screen']]
    for v in anchors:
        matches = [c for c in board['copper'] if c['kind'] == 'via' and c['uuid'] == v['uuid']]
        require(len(matches) == 1 and matches[0]['net'] == v['net'], 'anchor occurrence')
        v['native_source_geometry'] = matches[0]
    return {'board_sha256': BOARD_HASH, 'coordinates': 'panel XY mm; native XY = panel XY + (100,50)',
            'pads': pads, 'retained_B2_external_anchors': anchors,
            'parser_sha256': sha(ROOT / 'design/architecture-278/implementation/stage40/mult-copper-plan/native.py')}


def inventory(projection):
    bindings = read(S44 + '/evidence/local-artifact-bindings.json')
    require(projection['source'] == SNAPSHOT and
            projection['source_sha256'] == bindings[SNAPSHOT]['sha256'] and
            projection['board_sha256'] == BOARD_HASH, 'projection provenance')
    aliases = read('design/reports/board-net-tokens.json')
    rails = {'AGND', '+12V', '-12V', '+5V', '+12V_IN', '-12V_IN', '+5V_IN'}
    require(all(token == (name if name in rails else 'X' + hashlib.sha256(name.encode()).hexdigest()[:20].upper())
                for token, name in aliases.items()), 'semantic alias hash mismatch')
    geometry = json.loads((HERE / 'geometry.json').read_text())
    require(geometry['board_sha256'] == BOARD_HASH, 'geometry board')
    require(geometry['parser_sha256'] == sha(ROOT / 'design/architecture-278/implementation/stage40/mult-copper-plan/native.py'), 'geometry parser binding')
    partition = read('design/partition/partition.json')
    components, pins = {}, {}
    for board, basename in NETLISTS.items():
        cs, ns = read_netlist(ROOT / f'schematic/boards/{basename}.net')
        components[board] = {c.ref: c for c in cs}
        pins[board] = ns
    headers = {(c['board'], c['pcb_reference']): c for c in partition['connectors']}
    require(len(headers) == len(partition['connectors']), 'duplicate header reference')
    by_id = {c['id']: c for c in headers.values()}
    harnesses = {}
    for harness in partition['harnesses']:
        require(len(harness['header_ids']) == 2, 'non-pair harness requires explicit model')
        for hid in harness['header_ids']:
            require(hid not in harnesses, 'ambiguous harness owner')
            harnesses[hid] = harness
    rows, seen = [], set()
    for net, groups in sorted(projection['groups'].items()):
        require(len(groups) > 1, 'closed net in open inventory')
        semantic = aliases.get(net, net)
        require(not net.startswith('X') or net in aliases, 'missing semantic alias')
        group_rows, contacts, blocks = [], [], set()
        for index, group in enumerate(groups):
            require(group and len(group) == len(set(group)), 'empty/duplicate group')
            pad_rows = []
            for key in group:
                require(key not in seen, 'object in two components')
                seen.add(key)
                obj = projection['objects'][key]
                require(obj['net'] == net, 'wrong native net')
                if obj['kind'] != 'pad':
                    continue
                ref, pin = obj['ref'], obj['pin']
                require(pins['JL'].get((ref, pin)) == net, 'pad/netlist mismatch')
                c = components['JL'][ref]
                block = dict(c.fields).get('Block', '')
                blocks.add(block)
                pose = geometry['pads'][ref + ':' + pin]
                require(pose['net'] == net, 'geometry pad net')
                pad_rows.append({'ref': ref, 'pin': pin, 'block': block, 'value': c.value,
                                 'panel_xy_mm': pose['xy'], 'layers': pose['layers']})
                if ('JL', ref) not in headers:
                    continue
                header = headers['JL', ref]
                require(header['pin_map'].get(pin) == semantic, 'header/netlist mismatch')
                harness = harnesses.get(header['id'])
                require(harness is not None, 'header without explicit harness')
                mate_id = next(h for h in harness['header_ids'] if h != header['id'])
                mate = by_id[mate_id]
                # Same-number wiring is checked against both independent assignments.
                require(mate['pin_map'].get(pin) == semantic, 'mate pin assignment mismatch')
                require(pins[mate['board']].get((mate['pcb_reference'], pin)) == net,
                        'mate native net mismatch')
                contacts.append({'ref': ref, 'pin': pin, 'component': index,
                                 'header_id': header['id'], 'harness_id': harness['id'],
                                 'mate_board': mate['board'], 'mate_ref': mate['pcb_reference'],
                                 'mate_pin': pin, 'semantic_net': semantic,
                                 'status': 'intentional offboard boundary; local JL open remains a failure'})
            require(pad_rows, 'padless component needs a separate disposition')
            group_rows.append({'index': index, 'object_count': len(group),
                               'membership_sha256': hashlib.sha256(encoded(sorted(group)).encode()).hexdigest(),
                               'pads': sorted(pad_rows, key=lambda p: (p['ref'], p['pin']))})
        category = 'ground' if net == 'AGND' else 'local feed on interface net' if contacts else 'local circuit'
        closest = min((math.dist(a['panel_xy_mm'], b['panel_xy_mm']), a['ref'] + ':' + a['pin'], b['ref'] + ':' + b['pin'])
                      for i, g in enumerate(group_rows) for h in group_rows[i+1:]
                      for a in g['pads'] for b in h['pads'])
        rows.append({'native_net': net, 'semantic_net': semantic, 'board': 'JL',
                     'minimum_missing_connections': len(groups) - 1, 'blocks': sorted(blocks),
                     'category': category, 'components': group_rows, 'offboard_contacts': contacts,
                     'closest_cross_component_pad_pair': {'distance_mm': closest[0], 'pads': closest[1:],
                         'limit': 'pad-center screening only, not route length, copper-island distance or clearance proof'},
                     'status': 'UNFINISHED LOCAL ROUTING; not an intentional open'})
    require(seen == set(projection['objects']), 'unaccounted projection object')
    total = sum(r['minimum_missing_connections'] for r in rows)
    require(total == projection['native_open_edges'] == 117, 'open count changed')
    counts = Counter()
    for r in rows:
        counts[r['category']] += r['minimum_missing_connections']
    return {'board_sha256': BOARD_HASH, 'affected_nets': len(rows), 'local_open_edges': total,
            'intentional_local_open_edges': 0, 'open_edges_by_category': dict(sorted(counts.items())),
            'rows': rows, 'limits': 'Connectivity evidence is inherited from Stage44; no native or physical verification is rerun here. Component partitions do not prescribe a unique routing tree. Offboard mates do not excuse any local open.'}


def reuse():
    old = read(S44 + '/evidence/reuse.json')
    plan = read('design/architecture-278/implementation/stage40/mult-copper-plan/plan.json')
    _, pins = read_netlist(ROOT / 'schematic/boards/osc-jack-left.net')
    aliases = read('design/reports/board-net-tokens.json')
    rows, netmap = [], {}
    for p in old['packages']:
        a, b = p['B1'], p['B2']
        require(p['same_library_id'] and p['common_nonplacement_properties'], 'library/BOM mismatch')
        logical = plan['candidate_B1'][a]
        contacts = []
        pa = {pin: net for (ref, pin), net in pins.items() if ref == a}
        pb = {pin: net for (ref, pin), net in pins.items() if ref == b}
        require(set(pa) == set(pb), 'physical pin IDs differ')
        for pin, an in sorted(pa.items()):
            bn = pb[pin]
            require(an not in netmap or netmap[an] == bn, 'nonfunctional B1/B2 net mapping')
            netmap[an] = bn
            contacts.append({'pin': pin, 'B1_net': an, 'B2_net': bn,
                             'B1_semantic': aliases.get(an, an), 'B2_semantic': aliases.get(bn, bn)})
        rows.append({'B1': a, 'B2': b, 'fixed_front_hardware': logical['panel'],
                     'same_library_and_nonplacement_metadata': True,
                     'B2_actual_native_at': p['candidate_B2_at'],
                     'B1_plus_34_native_at': p['translated_B1_at'], 'layer': p['candidate_layer'],
                     'exact_translated_pose': p['candidate_B2_at'] == p['translated_B1_at'],
                     'contacts': contacts})
    require(len(set(netmap.values())) == len(netmap), 'non-bijective cell net mapping')
    require(old['candidate_sha256'] == BOARD_HASH, 'reuse board binding')
    return {'board_sha256': BOARD_HASH, 'package_pairs': len(rows),
            'physical_contacts_per_cell': sum(len(r['contacts']) for r in rows),
            'bijective_native_net_pairs': len(netmap), 'packages': rows,
            'pose_exceptions': [r['B2'] for r in rows if not r['exact_translated_pose']],
            'reused': 'circuit, physical pin map, library and nonplacement BOM metadata',
            'identical_manufactured_PCB_established': False,
            'reason': 'B1/B2 are cells on one shared JL substrate, with two different relative package poses and site-specific copper/foreign anchors. No independently separable common outline, mounts or interchangeable connector contract has been accepted. This does not prove a future common PCB impossible.',
            'qualification': 'Metadata equality does not resolve exact MPN omissions, inventory placement binding, sourcing, analog stability or physical qualification.'}


def build():
    projection = json.loads((HERE / 'open-partitions.json').read_text())
    result = {'inventory': inventory(projection), 'reuse': reuse(),
              'retained_B2_external_anchors': json.loads((HERE / 'geometry.json').read_text())['retained_B2_external_anchors']}
    sources = ['design/reports/board-net-tokens.json', 'design/partition/partition.json',
               S44 + '/evidence/local-artifact-bindings.json', S44 + '/evidence/reuse.json',
               'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json',
               'scripts/pcbgen/netlist.py', str((HERE / 'open-partitions.json').relative_to(ROOT)),
               str((HERE / 'geometry.json').relative_to(ROOT)), S44 + '/evidence/branches.json',
               'scripts/schgen/project_boards.py',
               'design/architecture-278/implementation/stage40/mult-copper-plan/native.py',
               str(Path(__file__).relative_to(ROOT))]
    sources += [f'schematic/boards/{name}.net' for name in NETLISTS.values()]
    result['source_sha256'] = {p: sha(ROOT / p) for p in sorted(sources)}
    return result


def table(result):
    lines = ['# Stage45 inherited local routing inventory', '',
             'Generated from the accepted Stage44 snapshot. All 117 opens remain failures.',
             'Groups separated by ` / ` are disconnected native components. A large group',
             'is abbreviated here; `inventory.json` contains every pad, coordinate and mate.',
             'The edge count is the minimum links needed, not an approved routing tree.', '',
             '| Semantic net | Missing links | Class | Disconnected pad groups |',
             '|---|---:|---|---|']
    for row in result['inventory']['rows']:
        groups = []
        for group in row['components']:
            pads = group['pads']
            groups.append(', '.join(p['ref'] + ':' + p['pin'] for p in pads) if len(pads) < 20
                          else f"{len(pads)} pads (main component; see JSON)")
        lines.append(f"| {row['semantic_net']} | {row['minimum_missing_connections']} | {row['category']} | {' / '.join(groups)} |")
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    if sys.argv[1:] == ['--export']:
        (HERE / 'open-partitions.json').write_text(encoded(export_snapshot()))
        (HERE / 'geometry.json').write_text(encoded(export_geometry()))
    elif sys.argv[1:] == ['--check']:
        result = build()
        require((HERE / 'inventory.json').read_text() == encoded(result), 'stale inventory')
        require((HERE / 'OPEN-NETS.md').read_text() == table(result), 'stale table')
        print('Stage45 deterministic inventory PASS')
    elif not sys.argv[1:]:
        result = build()
        (HERE / 'inventory.json').write_text(encoded(result))
        (HERE / 'OPEN-NETS.md').write_text(table(result))
    else:
        raise SystemExit('usage: generate.py [--export|--check]')
