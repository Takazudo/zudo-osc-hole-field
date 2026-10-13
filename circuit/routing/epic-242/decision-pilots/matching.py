#!/usr/bin/env python3
"""Issue253 source-only matched-demand manifest and exact-anchor focus adapter."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile
import check

HERE = Path(__file__).resolve().parent
TOOL_FILES = [str((HERE/name).relative_to(check.ROOT)) for name in
              ('check.py', 'matching.py', 'prepare_matched.py', 'route_matched.py',
               'evaluate_matched.py', 'matching-spec.json', 'matched-demands.json')] + [
    'scripts/pcbgen/grid_router.py', 'scripts/pcbgen/grid_apply.py',
    'scripts/pcbgen/route_jack_grid.py', 'scripts/pcbgen/copper_identity.py',
    'scripts/pcbgen/complete_native_warnings.py', 'scripts/partition/core_split_candidates.py',
    'scripts/pcbgen/numerical-requirements.txt', 'scripts/kicad/run.sh', 'scripts/kicad/pin.env', 'scripts/kicad/native_resource_guard.py']
# Bind transitive source readers and native audit helpers as well as entrypoints.
TOOL_FILES = sorted(set(TOOL_FILES + [str(p.relative_to(check.ROOT)) for folder in ('scripts/pcbgen', 'scripts/schgen') for p in (check.ROOT/folder).glob('*.py')]))


def tool_hashes():
    return {name: check.digest(check.ROOT/name) for name in TOOL_FILES}


def validate_fixture_method(receipt, report, domain, board):
    check.require(receipt['domain'] == domain and receipt['board'] == board, 'wrong private fixture')
    check.require(receipt['spec_sha256'] == report['spec_sha256'], 'stale fixture method')
    check.require(receipt['matched_demands_sha256'] == check.digest(HERE/'matched-demands.json'), 'stale fixture demand ledger')
    check.require(receipt['tool_sha256'] == tool_hashes(), 'fixture tool epoch drift')


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_dumps(directory):
    dumps, bindings = {}, {}
    for board, receipt in check.read(HERE / 'artifacts.json').items():
        path = directory / receipt['file']
        check.require(check.digest(path) == receipt['sha256'], f'{board}: artifact SHA mismatch')
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(receipt['dump_member'])
        dumps[board] = json.loads(raw)
        bindings[board] = {**receipt, 'dump_sha256': hashlib.sha256(raw).hexdigest(),
                           'board_sha256': dumps[board]['board_sha256']}
    return dumps, bindings


def pad(dump, ref, number):
    found = [p for p in dump['pads'] if (p['ref'], p['pad']) == (ref, number)]
    check.require(len(found) == 1, f'non-unique/missing pad {ref}.{number}')
    return found[0]


def group(dump, net, uid):
    groups = dump['islands'].get(net)
    if groups is None:
        return None
    found = [sorted(g) for g in groups if uid in g]
    check.require(len(found) == 1, 'missing/duplicate native group member')
    return found[0]


def connected(dump, net, anchors):
    """Dump schema omits fully connected nets; unknown/missing pad is never success."""
    by_uid = {p['uuid']: p for p in dump['pads']}
    check.require(all(u in by_uid and by_uid[u]['net'] == net for u in anchors), 'missing/wrong-net anchor')
    groups = [group(dump, net, u) for u in anchors]
    return all(g is None for g in groups) or all(g == groups[0] for g in groups)


def classify(k, candidate, net, anchors):
    # Exact anchor geometry is a matching requirement, not merely a net-name join.
    kp = {p['uuid']: p for p in k['pads']}
    cp = {p['uuid']: p for p in candidate['pads']}
    check.require(len(anchors) == 2 and anchors[0] != anchors[1], 'two distinct anchors required')
    for u in anchors:
        check.require(u in kp and u in cp and kp[u] == cp[u] and kp[u]['net'] == net, 'anchor identity/geometry mismatch')
    a, b = connected(k, net, anchors), connected(candidate, net, anchors)
    return ('BOTH_CONNECTED_NO_DEMAND' if a and b else 'PARTITION_INDUCED_REPAIR' if a else
            'CANDIDATE_ALREADY_CONNECTED' if b else 'BOTH_OPEN')


def require_matched(k, candidate, net, anchors):
    classification = classify(k, candidate, net, anchors)
    check.require(classification == 'BOTH_OPEN', f'not matched open demand: {classification}')
    return classification


def group_receipt(dump, net, uid):
    members = group(dump, net, uid)
    # Absence is explicit; never create an open group to manufacture a demand.
    return {'status': 'RECORDED_OPEN_NET_GROUP' if members is not None else 'NET_OMITTED_FROM_OPEN_TABLE',
            'all_member_count': len(members) if members is not None else None,
            'all_members_sha256': sha(members) if members is not None else None,
            'locator': {'net_token': net, 'contains_pad_uuid': uid}}


def preservation(dump, refs):
    touched = sorted((p for p in dump['pads'] if p['ref'] in refs), key=lambda p: p['uuid'])
    nets = sorted({p['net'] for p in touched if p['net']})
    return {'touched_pad_records': touched,
            'touched_net_groups': {n: {'all_groups_sha256': sha(sorted(sorted(g) for g in dump['islands'].get(n, []))),
                                      'recorded_groups': len(dump['islands'].get(n, [])),
                                      'all_member_count': sum(len(g) for g in dump['islands'].get(n, []))} for n in nets},
            'whole_board': {'pads_sha256': sha(sorted(dump['pads'], key=lambda p: p['uuid'])),
                            'full_open_groups_sha256': sha({n: sorted(sorted(g) for g in gs) for n, gs in dump['islands'].items()}),
                            'tracks_multiset_sha256': sha(sorted(sha(p) for p in dump['tracks'])),
                            'vias_multiset_sha256': sha(sorted(sha(p) for p in dump['vias'])),
                            'board_sha256': dump['board_sha256']},
            'required_after': ['Every original pad identity/geometry and all source-connected pad groups retained.',
                               'All original copper/nonrouting objects retained by UUID+geometry multiset, including duplicates; full board reader required for zones/nonrouting.',
                               'No new uncapped warning identities, errors or parity issues; fresh-copy full signatures agree.',
                               'No cuts/rip/zone changes, including unnamed victim nets outside search bounds.'],
            'group_provenance': 'Full UUID member sets (pads AND tracks/vias) are addressed by authenticated dump binding + net/anchor locator + digest; never reduced to pad-only membership.'}


def return_debt(k, candidate, touched, net='AGND'):
    """All source-connected power/return equivalences, not just a repair pair."""
    pads = sorted((p for p in touched if p['net'] == net), key=lambda p: p['uuid'])
    obligations = []
    for i, a in enumerate(pads):
        for b in pads[i+1:]:
            ids = [a['uuid'], b['uuid']]
            if connected(k, net, ids):
                kind = classify(k, candidate, net, ids)
                obligations.append({'net_token': net, 'anchors': ids, 'refs': [a['ref']+'.'+a['pad'], b['ref']+'.'+b['pad']],
                                    'classification': kind, 'baseline_improvement_credit': 0,
                                    'required_after': 'CONNECTED; restore if partition split, preserve otherwise'})
    return obligations


def build(dumps, bindings):
    spec = check.read(HERE / 'matching-spec.json')
    source = {option: check.read(check.SPLIT / f'candidates/{option}.json') for option in ('two', 'three')}
    copper = check.read(check.SPLIT / 'candidates/copper-contract.json')
    tokens = {n['source_net']: n['net_token'] for n in copper['options']['two']['nets']}
    k = dumps['K1402']
    result = {'schema': 'epic253-authenticated-matched-demands-1', 'spec_sha256': check.digest(HERE / 'matching-spec.json'),
              'status': 'SOURCE MATCHED; NATIVE NOT RUN / NOT ADMITTED', 'bindings': bindings, 'domains': {},
              'credit_policy': 'Only exact predeclared BOTH_OPEN pair closures can earn K-relative routing credit. Partition debt earns zero credit and blocks coupled success until restored.'}
    for name, domain in spec['domains'].items():
        board = source['two']['boards'][domain['boards'][1]]
        parts = {p['ref']: p for p in board['source_parts']}
        refs = set(domain['packages'] + domain['related_refs'])
        refs.update(p['ref'] for p in parts.values() if p.get('decouples_ref') in domain['packages'])
        for target in domain['targets'].values():
            refs.update(a['ref'] for a in target['anchors'])
        check.require(all(parts[r]['module'] == domain['module'] for r in refs), 'touched refs leave owned source module')
        rows = {}
        for kind, target in domain['targets'].items():
            net = tokens[target['source_net']]
            anchors = [pad(k, a['ref'], a['pad']) for a in target['anchors']]
            ids = [p['uuid'] for p in anchors]
            row = {**target, 'net_token': net, 'anchor_records': anchors, 'boards': {}}
            for label in domain['boards']:
                d = dumps[label]
                require_matched(k, d, net, ids)
                row['boards'][label] = {'classification': 'BOTH_OPEN',
                                        'original_groups': [group_receipt(d, net, u) for u in ids]}
            if kind in ('positive_supply', 'negative_supply'):
                check.require(parts[target['anchors'][1]['ref']]['decouples_ref'] == target['anchors'][0]['ref'], 'remote is not source-declared bypass')
            rows[kind] = row
        points = [xy for row in rows.values() for p in row['anchor_records'] for xy in p['poly']]
        margin = spec['budget']['window_margin_mm']
        bounds = [round(min(p[0] for p in points)/1e6-margin, 6), round(min(p[1] for p in points)/1e6-margin, 6),
                  round(max(p[0] for p in points)/1e6+margin, 6), round(max(p[1] for p in points)/1e6+margin, 6)]
        boards = {}
        for label in domain['boards']:
            d = dumps[label]
            preserved = preservation(d, refs)
            boards[label] = {'preservation': preserved,
                             'source_connected_return_obligations': return_debt(k, d, preserved['touched_pad_records']),
                             'source_connected_rail_obligations': [row for n in ('+12V', '-12V', '+5V')
                                                                 for row in return_debt(k, d, preserved['touched_pad_records'], n)]}
        result['domains'][name] = {'module': domain['module'], 'touched_ref_closure': sorted(refs),
                                  'source_packages': [parts[r] for r in sorted(refs)], 'targets': rows,
                                  'source_sensitive_locality': [s for s in board['sensitive_nets'] if set(s['refs']) & refs],
                                  'source_island_bindings': [{'island_id': s['island_id'], 'sha256': sha(s)} for s in board['islands']
                                                             if s['island_id'].startswith(domain['module']+'/')],
                                  'common_bounds_mm': bounds, 'coordinate_frame': {'name': 'native PCB', 'source_to_native_offset_mm': [100, 50]}, 'boards': boards,
                                  'scope': 'Minimal touched-package/bypass closure, NOT whole-module preservation; whole-board native gates still mandatory.'}
    return result


def focused(dump, domain):
    """Anchor-only masks prevent a large K group choosing a different landing."""
    result = copy.deepcopy(dump)
    result['islands'] = {}
    for row in domain['targets'].values():
        ids = [p['uuid'] for p in row['anchor_records']]
        actual = {p['uuid']: p for p in dump['pads']}
        check.require(all(actual.get(p['uuid']) == p for p in row['anchor_records']), 'focus anchor record drift')
        require_matched(dump, dump, row['net_token'], ids)
        result['islands'][row['net_token']] = [[u] for u in ids]
    result['open_edges'] = len(domain['targets'])
    result['scope'] = 'DERIVED ANCHOR-ONLY ROUTING MASK; original full dump is native authority; all geometry unchanged'
    return result


def validate_published(report, expected):
    check.require(report == expected, 'matched manifest/group/return obligation drift')


def validate_proposal(proposal, original):
    check.require(proposal['board_sha256'] == original['board_sha256'], 'proposal board drift')
    check.require(not proposal['removed_uuids'], 'removed copper forbidden')
    check.require(not proposal.get('accepted', False), 'fabricated native acceptance')


def closure_diagnostic(before, after, net, anchors):
    require_matched(before, before, net, anchors)
    bp, ap = ({p['uuid']: p for p in d['pads']} for d in (before, after))
    check.require(bp == ap, 'after pad identity/geometry changed')
    # A smaller raw open count or emitted route is deliberately irrelevant.
    return {'exact_pair_closed': connected(after, net, anchors), 'accepted': False,
            'scope': 'Connectivity diagnostic only; independent fresh/full warnings/copper/return gates mandatory'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts', required=True, type=Path)
    p.add_argument('--check', action='store_true')
    p.add_argument('--focus-domain', choices=('O1', 'F3', 'E1'))
    p.add_argument('--focus-board')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    check.source_checks()
    dumps, bindings = load_dumps(args.artifacts)
    report = build(dumps, bindings)
    if args.check:
        validate_published(report, check.read(HERE / 'matched-demands.json'))
        print('PASS: all12 source-matched open pairs in3 domains/9board-domain comparisons; no native execution')
    elif args.focus_domain:
        check.require(args.output is not None and not args.output.exists(), 'new output file required')
        domain = report['domains'][args.focus_domain]
        check.require(args.focus_board in domain['boards'], 'board outside matched domain')
        args.output.write_text(json.dumps(focused(dumps[args.focus_board], domain), separators=(',', ':'))+'\n')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
