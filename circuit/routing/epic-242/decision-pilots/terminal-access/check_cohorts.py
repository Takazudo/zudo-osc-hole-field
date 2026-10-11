#!/usr/bin/env python3
"""One bounded F3/E1 pass using the unchanged local exact-access checker."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import zipfile

from check_saved import examine, DIRECTIONS, LENGTHS, INPUTS, METHOD
from exact_access import Geometry
from exact_access import EPS, point

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
COHORTS = {'F3': ('K1402', 'two-A', 'three-B'),
           'E1': ('K1402', 'two-B', 'three-C')}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def group_receipts(dump, target):
    """Fail closed unless two different complete native groups are recorded."""
    net = target['net_token']
    receipts, members = [], []
    for pad in target['anchor_records']:
        found = [sorted(g) for g in dump['islands'].get(net, []) if pad['uuid'] in g]
        assert len(found) == 1 and len(found[0]) == len(set(found[0])), 'missing/ambiguous native group'
        members.append(found[0])
        receipts.append({'status': 'RECORDED_OPEN_NET_GROUP',
                         'all_member_count': len(found[0]),
                         'all_members_sha256': sha(json.dumps(found[0], sort_keys=True, separators=(',', ':')).encode()),
                         'locator': {'net_token': net, 'contains_pad_uuid': pad['uuid']}})
    assert set(members[0]).isdisjoint(members[1]), 'not an open pair'
    return receipts


def owner(geometry, uid):
    if uid is None:
        return None
    for kind in ('pads', 'tracks', 'vias'):
        for obj in geometry.dump[kind]:
            if obj['uuid'] == uid.removesuffix(':NPTH'):
                return {'kind': kind, 'uuid': uid, 'ref': obj.get('ref'),
                        'pad': obj.get('pad'), 'net': obj['net'],
                        'record': obj}
    raise AssertionError('unknown obstacle ' + uid)


def load(board, args, manifest):
    binding = manifest['bindings'][board]
    path = args.k if board == 'K1402' else args.artifacts / binding['file']
    expected = INPUTS['K1402'][1] if board == 'K1402' else binding['sha256']
    assert sha(path.read_bytes()) == expected, 'artifact hash mismatch'
    member = 'fixture/before/dump.json' if board == 'K1402' else binding['dump_member']
    pcb = 'fixture/before/osc-core.kicad_pcb' if board == 'K1402' else 'working-result/before/osc-core.kicad_pcb'
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        raw = z.read(member)
        dump = json.loads(raw)
        assert sha(raw) == binding['dump_sha256']
        assert sha(z.read(pcb)) == binding['board_sha256'] == dump['board_sha256']
        if board == 'K1402':
            lock = json.loads(z.read('fixture/fixture-lock.json'))
            assert lock['source_tree_sha'] == METHOD and lock['board'] == board
            assert lock['spec_sha256'] == sha((PILOT / 'matching-spec.json').read_bytes())
            assert lock['matched_demands_sha256'] == sha((PILOT / 'matched-demands.json').read_bytes())
    return dump, {'retained_zip_file': path.name, 'retained_zip_sha256': expected,
                  'dump_member': member, 'dump_sha256': binding['dump_sha256'],
                  'board_member': pcb, 'board_sha256': binding['board_sha256'],
                  'published_input_binding': binding}


def cross_witness(geometry, endpoint, demand, witness, budget):
    start, end = witness['start_mm'], witness['end_mm']
    edge = geometry.terminal_edge(endpoint['uuid'], start, end, demand['net_token'],
                                 endpoint['layer'], endpoint['width_mm'], budget['clearance_mm'])
    via = geometry.via(end, demand['net_token'], budget['via_diameter_mm'],
                       budget['via_drill_mm'], budget['clearance_mm'])
    # Attribute actual failing constraints, never mistake nearest copper for a hole.
    foreign = []
    for result in (edge['sweep'], via):
        margin = result['checked_margins_mm']['foreign_copper']
        if margin is not None and margin < EPS:
            foreign.append(owner(geometry, result['nearest_foreign']))
    holes = []
    if via['checked_margins_mm']['existing_hole'] is not None and via['checked_margins_mm']['existing_hole'] < EPS:
        q = point(end)
        for shape, radius, uid in geometry.holes:
            margin = q.distance(shape) - radius - budget['via_diameter_mm'] / 2 - .25
            if margin < EPS:
                holes.append({'owner': owner(geometry, uid), 'margin_mm': margin})
    return {'edge': edge, 'via': via, 'pass': edge['pass'] and via['pass'],
            'failing_foreign_copper_owners': foreign, 'failing_existing_hole_owners': holes,
            'scope': 'Exact same local witness only. A failure here does not exclude all other escapes.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--k', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    versions = {name: version(name) for name in ('numpy', 'scipy', 'shapely')}
    assert versions == {'numpy': '2.2.6', 'scipy': '1.15.3', 'shapely': '2.1.2'}
    spec = json.loads((PILOT / 'matching-spec.json').read_text())
    manifest = json.loads((PILOT / 'matched-demands.json').read_text())
    budget = spec['budget']
    report = {'status': 'BOUNDED SOURCE-ONLY F3/E1 ACCESS SCREEN; NO NATIVE ADMISSION',
              'frozen_method_input': METHOD,
              'versions': versions,
              'source_sha256': {name: sha((HERE / name).read_bytes()) for name in ('exact_access.py', 'check_saved.py', 'check_cohorts.py')},
              'spec_sha256': sha((PILOT / 'matching-spec.json').read_bytes()),
              'manifest_sha256': sha((PILOT / 'matched-demands.json').read_bytes()),
              'assumptions': {'contact': 'Strict center-inside named-anchor is a sufficient diagnostic rule, not an owner-fixed physical constraint. Off-pad contact adequacy is untested.',
                              'templates': '0.1mm interior samples plus pad center; finite straight edges only. No result excludes other contacts, longer or curved/multisegment escapes.',
                              'directions': DIRECTIONS, 'lengths_mm': LENGTHS,
                              'comparison': 'Identical tests on all declared boards. Complete local escape on one side may be informative even when the other side is blocked. All original demands retained.',
                              'rules': budget, 'production_router_changed': False, 'hardware_changed': False},
              'inputs': {}, 'cohorts': {}}
    geometries = {}
    for board in dict.fromkeys(b for boards in COHORTS.values() for b in boards):
        dump, receipt = load(board, args, manifest)
        geometries[board] = Geometry(dump)
        report['inputs'][board] = receipt
    for name, boards in COHORTS.items():
        domain = manifest['domains'][name]
        assert list(boards) == spec['domains'][name]['boards']
        rows = {}
        for board in boards:
            geometry = geometries[board]
            demands = []
            for kind in spec['route_policy']['target_order']:
                target = domain['targets'][kind]
                assert all(geometry.pads[p['uuid']] == p for p in target['anchor_records'])
                groups = group_receipts(geometry.dump, target)
                assert target['boards'][board]['classification'] == 'BOTH_OPEN'
                assert groups == target['boards'][board]['original_groups']
                width = budget['rail_width_mm'] if target['net_token'] in spec['route_policy']['rail_nets'] else budget['signal_width_mm']
                endpoints = [examine(geometry, pad, width, budget, domain['common_bounds_mm']) for pad in target['anchor_records']]
                for endpoint in endpoints:
                    cert = endpoint['whole_pad_start_certificate']
                    cert['exact_constraint_owners'] = [owner(geometry, u) for u in cert.get('foreign_pad_uuids', [])]
                    best = endpoint['best_start_cap']
                    endpoint['best_start_cap_foreign_owner'] = owner(geometry, best['sweep']['nearest_foreign']) if best else None
                demands.append({'kind': kind, 'source_net': target['source_net'], 'net_token': target['net_token'],
                                'classification': 'BOTH_OPEN_REVERIFIED_FROM_RETAINED_FULL_NATIVE_GROUPS',
                                'original_groups': groups, 'endpoints': endpoints,
                                'both_endpoints_have_straight_escape': all(e['valid_swept_terminal_edges'] > 0 for e in endpoints),
                                'both_endpoints_have_edge_plus_new_via': all(e['valid_edges_ending_in_new_through_via'] > 0 for e in endpoints)})
                print(name, board, kind, [(e['anchor'], e['foreign_clear_full_width_start_caps'], e['valid_swept_terminal_edges'], e['valid_edges_ending_in_new_through_via']) for e in endpoints], flush=True)
            rows[board] = demands
        comparisons, witnesses = [], []
        for candidate in boards[1:]:
            for k, c in zip(rows['K1402'], rows[candidate]):
                comparisons.append({'candidate': candidate, 'kind': k['kind'], 'both_open': True,
                                    'incumbent_two_terminal_straight_access': k['both_endpoints_have_straight_escape'],
                                    'candidate_two_terminal_straight_access': c['both_endpoints_have_straight_escape'],
                                    'at_least_one_side_two_terminal_straight_access': k['both_endpoints_have_straight_escape'] or c['both_endpoints_have_straight_escape'],
                                    'incumbent_two_terminal_edge_plus_via': k['both_endpoints_have_edge_plus_new_via'],
                                    'candidate_two_terminal_edge_plus_via': c['both_endpoints_have_edge_plus_new_via']})
            for source, other in ((candidate, 'K1402'), ('K1402', candidate)):
                for demand in rows[source]:
                    for endpoint in demand['endpoints']:
                        for witness in endpoint['edge_and_via_witnesses']:
                            witnesses.append({'source_board': source, 'other_board': other,
                                              'kind': demand['kind'], 'anchor': endpoint['anchor'],
                                              'start_mm': witness['start_mm'], 'end_mm': witness['end_mm'],
                                              'other_board_check': cross_witness(geometries[other], endpoint, demand, witness, budget)})
        report['cohorts'][name] = {'common_bounds_mm': domain['common_bounds_mm'], 'boards': rows,
                                 'comparisons': comparisons, 'cross_board_witnesses': witnesses}
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
