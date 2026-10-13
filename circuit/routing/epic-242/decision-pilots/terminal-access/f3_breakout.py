#!/usr/bin/env python3
"""Prepare one exact local F3 terminal breakout; no search, native apply or credit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import f3_adapter as adapter


def prepare(original, domain, pool, budget, policy, board, repair):
    """Return disposable adapter inputs; copper is emitted only with a complete pair.

    Do not add the preview via to original: that would become an existing-hole
    obstacle and would not create a transition in anchor-only source masks.
    """
    require = adapter.require
    require(repair['schema'] == 'f3-exact-terminal-breakout-1', 'unknown breakout schema')
    require(board == repair['board'], 'wrong breakout board')
    require(adapter.digest(original) == repair['input_dump_canonical_sha256'], 'breakout physical input drift')
    require(original['board_sha256'] == repair['input_board_sha256'], 'breakout board epoch drift')
    require(domain['common_bounds_mm'] == repair['bounds_mm'], 'breakout bounds drift')
    dimensions = {k: budget[k] for k in ('signal_width_mm', 'clearance_mm', 'via_diameter_mm', 'via_drill_mm', 'raster_mm')}
    require(dimensions == repair['dimensions'], 'breakout dimension drift')
    target = domain['targets']['signal']
    require(target['net_token'] == repair['net'], 'breakout net substitution')
    anchor = target['anchor_records'][1]  # Preserve the frozen second-to-first direction.
    require(anchor['uuid'] == repair['anchor_uuid'] and anchor['ref'] == repair['ref']
            and anchor['pad'] == repair['pad'], 'breakout named source substitution')
    require(repair['landing_layer'] == 'In2.Cu', 'breakout landing layer drift')
    for xy in (repair['start_nm'], repair['via_nm']):
        require(len(xy) == 2 and all(type(v) is int for v in xy), 'integer breakout coordinates required')
    choice = {'start_nm': repair['start_nm'], 'end_nm': repair['via_nm'], 'via': True}
    choices = {p['uuid']: [] for p in target['anchor_records']}
    choices[anchor['uuid']] = [choice]
    groups, records, rejected = adapter.portals(original, target, choices, budget, domain['common_bounds_mm'])
    require(not rejected and len(groups[1]) == 1, 'breakout exact geometry rejected: '+str(rejected))
    record = records[groups[1][0]]
    require(record['node'][0] == repair['landing_layer'], 'breakout source transition lost')
    path = record['path']
    result = {'net': target['net_token'], 'island': [anchor['ref']+'.'+anchor['pad']],
              'path': path, 'width_nm': round(budget['signal_width_mm']*1e6),
              'via_diameter_nm': round(budget['via_diameter_mm']*1e6)}
    preview, _ = adapter.grid.copper_rows([result], 'fixture-253-F3-'+board,
        repair['id'], via_diameter=budget['via_diameter_mm'], via_drill=budget['via_drill_mm'])
    require(sum(r['kind'] == 'via' for r in preview) == 1, 'breakout via emission census')
    require(adapter.cumulative_fill_ok(original, preview, budget, policy, domain['common_bounds_mm']),
            'breakout original-baseline fill veto')
    repaired = copy.deepcopy(pool)
    require(choice not in repaired['signal'][anchor['uuid']], 'breakout already installed')
    repaired['signal'][anchor['uuid']].append(copy.deepcopy(choice))
    complete_groups, complete_records, _ = adapter.portals(original, target, repaired['signal'], budget, domain['common_bounds_mm'])
    require(len(complete_groups[0]) >= len(complete_groups[1]), 'breakout would reverse frozen search direction')
    require(groups[1][0] in complete_groups[1], 'breakout source marker omitted')
    receipt = {'status': 'SOURCE-ONLY LOCAL BREAKOUT; NO PAIR CLOSURE OR NATIVE APPLY',
        'repair_id': repair['id'], 'board': board, 'anchor_uuid': anchor['uuid'],
        'physical_input_unchanged': True, 'accepted': False, 'adopted': False,
        'native_exact_pair_closed': False, 'coupled_connectivity_success': False,
        'removed_uuids': [], 'source_marker': groups[1][0], 'source_record': record,
        'signal_portal_counts_after': list(map(len, complete_groups)),
        'preview_copper': preview, 'preview_only': True,
        'cumulative_original_baseline_fill': 'PASS SOURCE SCREEN; native gates not run',
        'emission_policy': 'Preview is never pre-added to physical input. Existing adapter.stitch emits the selected attachment exactly once only after a complete pair passes all gates; failure retains no breakout copper.'}
    return repaired, receipt


def source_binding(here, input_path, repair_path):
    """Seal the unchanged method plus this new producer before source preparation."""
    from importlib.metadata import version
    digest_file = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    packet_path = here/'f3-packet/request.json'
    adapter.require(digest_file(packet_path) ==
        '10be49ae32997a36c54436e48226a295678e47dda1fc1c14f4569c72ef4bdd92', 'frozen packet drift')
    packet = json.loads(packet_path.read_text())
    versions = {name: version(name) for name in packet['python']['versions']}
    adapter.require(versions == packet['python']['versions'], 'numerical versions drift')
    hashes = packet['input_file_sha256'] | packet['orchestration_control_sha256']
    for name, expected in hashes.items():
        adapter.require(digest_file(adapter.ROOT/name) == expected, 'frozen source/control drift: '+name)
    adapter.require(digest_file(input_path) == packet['cases']['two-A']['dump_sha256'], 'exact two-A dump bytes required')
    return {'scope': 'SOURCE-ONLY REPAIR PREPARATION; NOT NATIVE ADMISSION',
        'base_method_sha': packet['source_commit'], 'packet_sha256': digest_file(packet_path),
        'numerical_versions': versions, 'frozen_source_control_sha256': hashes,
        'repair_source_sha256': {name: digest_file(here/name) for name in
            ('f3_breakout.py', 'prove_f3_breakout.py', 'test_f3_breakout.py')},
        'input_dump_sha256': digest_file(input_path), 'repair_card_sha256': digest_file(repair_path)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--repair', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    read = lambda path: json.loads(path.read_text())
    here = Path(__file__).resolve().parent
    binding = source_binding(here, args.input, args.repair)
    repair = read(args.repair); original = read(args.input)
    manifest = read(here.parent/'matched-demands.json'); spec = read(here.parent/'matching-spec.json')
    domain = manifest['domains']['F3']
    pool = adapter.saved_pool(read(here/'cohort-validation.json'), domain)
    repaired, receipt = prepare(original, domain, pool, spec['budget'], spec['route_policy'], repair['board'], repair)
    adapter.require(not args.output.exists(), 'new disposable candidate directory required')
    args.output.mkdir(parents=True)
    # Original native group receipts stay intact; no fabricated native union.
    (args.output/'original-dump.json').write_bytes(args.input.read_bytes())
    for name, value in [('terminal-breakout.json', repair), ('adapter-pool.json', repaired), ('breakout-receipt.json', receipt)]:
        (args.output/name).write_text(json.dumps(value, indent=2)+'\n')
    binding['candidate_file_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output.iterdir())}
    (args.output/'source-binding.json').write_text(json.dumps(binding, indent=2)+'\n')
    print(json.dumps({'output': str(args.output), 'source_marker': receipt['source_marker'],
                      'signal_portal_counts_after': receipt['signal_portal_counts_after'],
                      'native': 'NOT RUN; no search or apply'}))


if __name__ == '__main__': main()
