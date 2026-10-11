#!/usr/bin/env python3
"""Read-only #253 cross-lane joins and saved native-dump comparison; no KiCad."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPLIT = ROOT / 'design/partition/core-split'


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_checks():
    decision = read(SPLIT / 'decision.json')
    contract = read(SPLIT / 'contract.json')
    require(decision['status'] == 'BLOCKED_ARCHITECTURE_SELECTION'
            and decision['selected_architecture'] is None
            and not decision['architecture_selection_ready']
            and not decision['production_generalization_ready'], 'unreviewed decision promotion')
    require(not contract['production_generalization_ready']
            and contract['final_board_ids'] is None
            and contract['final_stack_z_mm'] is None, 'unreviewed execution contract promotion')
    lock = read(HERE / 'source-lock.json')
    require(contract['immutable_inputs'] == lock['files'], 'contract/source lock drift')
    for path, expected in lock['files'].items():
        require(digest(ROOT / path) == expected, f'source drift: {path}')
    interface = read(SPLIT / 'candidates/interface-contract.json')
    baseline = read(ROOT / 'circuit/routing/epic-242/baseline/harness-contract.json')
    endpoints = {p['id']: p for p in interface['endpoints']}
    require(len(endpoints) == len(interface['endpoints']) == 390, 'endpoint identity census')
    for original in baseline['connectors']:
        actual = endpoints[original['id']]
        require(all(actual[k] == v for k, v in original.items()), f"endpoint drift: {original['id']}")
    require(interface['harnesses'] == baseline['harnesses'], 'harness IDs / order / signals drift')
    require(interface['fixed_panel'] == read(ROOT / 'design/grid/placements.lock.json'), 'fixed panel drift')
    require(len(interface['fixed_panel']['placements']) == 438, 'panel census')
    trims = read(ROOT / 'design/service/trimmer-functions.json')['trimmers']
    trim_refs = {p['ref'] for p in trims}
    require(len(trim_refs) == len(trims) == 100, 'trim identities')
    power = read(SPLIT / 'power/contract.json')
    require(len(power['power_parts']) == 13, 'POWER census')
    result = {}
    for option in ('two', 'three'):
        candidate = read(SPLIT / f'candidates/{option}.json')
        require(not candidate['selected'], 'candidate promoted without decision')
        parts = [p for b in candidate['boards'].values() for p in b['source_parts']]
        refs = [p['ref'] for p in parts]
        require(len(set(refs)) == len(refs) == 3385, 'source part coverage / duplicate')
        require(sum(p['dnp'] for p in parts) == 8, 'DNP changed')
        require({p['ref'] for p in parts if p['ref'].startswith('RV')} == trim_refs, 'trim coverage')
        for part in power['power_parts']:
            require('K' + candidate['ownership'][part['ref']] == part[f'{option}_owner'] == 'KA', 'POWER ownership mismatch')
        for board in candidate['boards'].values():
            owned = power['options'][option]['boards'][board['provisional_board_key']]
            require(len(board['source_parts']) == owned['package_count'], 'package ownership count mismatch')
            require(board['layers'] == 6 and board['face_z_mm'] is None, 'unreviewed layers / Z')
            for part in board['source_parts']:
                require(part['module'] in owned['instances'] or part['module'] == 'POWER', 'module crosses power ownership')
        shared = sorted(n for n, owners in candidate['net_owners'].items() if len(owners) > 1)
        require(shared == ['+12V', '+5V', '-12V', 'AGND'], 'unexpected shared signal net')
        result[option] = {'source_parts': len(parts), 'trimmers': len(trim_refs), 'shared_nets': shared,
                          'boards': {k: {'counts': b['counts'], 'courtyard_sum_mm2': b['source_part_courtyard_sum_mm2']}
                                     for k, b in candidate['boards'].items()}}
    return {'scope': 'SOURCE JOINS ONLY; no native/physical acceptance', 'locked_files': len(lock['files']),
            'harnesses': 195, 'endpoints': 390, 'panel_records': 438, 'options': result}


def compare_dumps(dumps):
    maps, rows = {}, {}
    for label, data in dumps.items():
        require(data['schema'] == 'grid-router-dump-1', f'{label}: schema')
        pads = {p['uuid']: (p['ref'], p['pad'], p['net']) for p in data['pads']}
        require(len(pads) == len(data['pads']), f'{label}: duplicate pad UUID')
        maps[label] = pads
        edges = sum(max(0, len(groups) - 1) for groups in data['islands'].values())
        require(edges == data['open_edges'], f'{label}: edge arithmetic')
        rows[label] = {'board_sha256': data['board_sha256'], 'pads': len(pads), 'open_edges': edges}
    baseline = maps['K1402']
    require(len(baseline) == 13406, 'accepted pad census')
    sets = {}
    for option, boards in [('two', ['two-A', 'two-B']), ('three', ['three-A', 'three-B', 'three-C'])]:
        counts = Counter(u for b in boards for u in maps[b])
        require(set(counts) == set(baseline), f'{option}: missing/new pad UUID')
        for b in boards:
            require(all(v == baseline[u] for u, v in maps[b].items()), f'{b}: pad identity drift')
        require(all(not baseline[u][2] for u, n in counts.items() if n > 1), 'duplicated electrical pad')
        nets = Counter(n for b in boards for n in {v[2] for v in maps[b].values()} if n)
        exclusive = {n for n, count in nets.items() if count == 1}
        shared = sorted(n for n, count in nets.items() if count > 1)
        require(len(exclusive) == 3553 and shared == ['+12V', '+5V', '-12V', 'AGND'], 'net domains')
        signature = lambda groups: sorted(tuple(sorted(g)) for g in groups)
        for n in exclusive:
            owner = next(b for b in boards if any(v[2] == n for v in maps[b].values()))
            require(signature(dumps[owner]['islands'].get(n, [])) == signature(dumps['K1402']['islands'].get(n, [])), f'{option}: open-group drift {n}')
        deficit = lambda b, ns: sum(max(0, len(dumps[b]['islands'].get(n, [])) - 1) for n in ns)
        sets[option] = {'unique_pads': len(counts), 'raw_pad_records': sum(counts.values()),
                        'duplicated_blank_net_pad_uuids': sum(n > 1 for n in counts.values()),
                        'exclusive_nets': len(exclusive), 'exclusive_open_groups_equal': True,
                        'exclusive_deficit': sum(deficit(b, exclusive) for b in boards),
                        'shared_domain_deficits': {n: {'K1402': deficit('K1402', [n]), **{b: deficit(b, [n]) for b in boards}} for n in shared}}
    return {'scope': 'Saved settled dump diagnostic; not routing rank, full warnings or migration acceptance',
            'limitations': ['Connected nets absent from islands: no complete connected-group equality proof.',
                           'Pad/track-seeded islands exclude exhaustive zone-only copper census.',
                           'Shared deficits are separate board domains, not physical cross-board joins.'],
            'boards': rows, 'sets': sets}


def artifact_checks(directory):
    dumps, bindings = {}, {}
    for label, receipt in read(HERE / 'artifacts.json').items():
        path = directory / receipt['file']
        require(digest(path) == receipt['sha256'], f'{label}: artifact SHA mismatch')
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(receipt['dump_member'])
        dumps[label] = json.loads(raw)
        bindings[label] = {**receipt, 'dump_sha256': hashlib.sha256(raw).hexdigest()}
    targets = {}
    for label, data in dumps.items():
        if label == 'K1402':
            continue
        manifest = read(SPLIT / f'candidates/pilots/{label}.json')
        targets[label] = {}
        for name, target in manifest['targets'].items():
            net = target['net_token']
            row = {'source_net': target['source_net'], 'net_token': net, 'pads': target['pads']}
            for board, dump in [(label, data), ('K1402', dumps['K1402'])]:
                pads = {p['uuid']: p for p in dump['pads']}
                groups = dump['islands'].get(net, [])
                indices = []
                for wanted in target['pads']:
                    p = pads[wanted['uuid']]
                    require((p['ref'], p['pad'], p['net']) == (wanted['ref'], wanted['pad'], net), 'pilot target identity drift')
                    found = [i for i, group in enumerate(groups) if wanted['uuid'] in group]
                    require(len(found) <= 1, 'target in duplicate native groups')
                    require(not groups or found, 'open-net target absent from native groups')
                    indices.extend(found)
                row[board] = {'net_open_groups': len(groups), 'target_group_indices': indices,
                              'status': ('NO_RECORDED_OPEN_DEMAND' if not groups else
                                         'TARGET_PADS_SAME_GROUP' if len(indices) > 1 and len(set(indices)) == 1 else
                                         'OPEN_NET_REQUIRES_REVIEWED_REMOTE_LANDING' if len(indices) == 1 else
                                         'TARGET_PADS_IN_DISTINCT_OPEN_GROUPS')}
            targets[label][name] = row
    return {'bindings': bindings, 'manifest_target_readiness': targets, **compare_dumps(dumps)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, help='Local directory containing exactly hash-verified saved ZIPs; no download or native execution')
    parser.add_argument('--check', action='store_true', help='Reject drift from committed verification (source portion only unless --artifacts supplied)')
    args = parser.parse_args()
    report = {'source': source_checks()}
    if args.artifacts:
        report['saved_native'] = artifact_checks(args.artifacts)
    if args.check:
        recorded = read(HERE / 'verification.json')
        require(all(recorded.get(k) == v for k, v in report.items()), 'published verification drift')
        print('PASS: source joins' + (' and authenticated saved native replay' if args.artifacts else '') + '; no new native evidence')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
