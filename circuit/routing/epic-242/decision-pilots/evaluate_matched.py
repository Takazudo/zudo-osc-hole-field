#!/usr/bin/env python3
"""Replay saved native proofs and exact matched demands; never invokes native tools."""
import argparse
import json
from pathlib import Path
import sys
import check
import matching as m


def evaluate_pairs(before, after, fresh, domain, board):
    targets = {}
    for kind, row in domain['targets'].items():
        anchors = [p['uuid'] for p in row['anchor_records']]
        states = [m.closure_diagnostic(before, d, row['net_token'], anchors)['exact_pair_closed']
                  for d in (after, fresh)]
        check.require(states[0] == states[1], 'fresh exact pair mismatch')
        targets[kind] = {'closed': states[0], 'anchors': anchors, 'net_token': row['net_token']}
    obligations = domain['boards'][board]
    debt = []
    for name in ('source_connected_return_obligations', 'source_connected_rail_obligations'):
        for row in obligations[name]:
            states = [m.connected(d, row['net_token'], row['anchors']) for d in (after, fresh)]
            check.require(states[0] == states[1], 'fresh obligation mismatch')
            debt.append({**row, 'connected_after_and_fresh': states[0]})
    return {'targets': targets, 'exact_matched_closures': sum(r['closed'] for r in targets.values()),
            'obligations': debt, 'outstanding_obligations': sum(not r['connected_after_and_fresh'] for r in debt),
            'coupled_connectivity_success': all(r['closed'] for r in targets.values()) and all(r['connected_after_and_fresh'] for r in debt),
            'accepted': False, 'adopted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    args = parser.parse_args()
    check.source_checks()
    root = args.fixture.resolve()
    lock = check.read(root/'fixture-lock.json')
    report = check.read(check.HERE/'matched-demands.json')
    m.validate_fixture_method(lock, report, lock['domain'], lock['board'])
    check.require(report['spec_sha256'] == check.digest(check.HERE/'matching-spec.json'), 'stale published specification')
    for name, digest in lock['files'].items():
        check.require(check.digest(root/name) == digest, 'fixture input drift: '+name)
    sys.path.insert(0, str(check.ROOT))
    from scripts.partition.core_split_candidates import settled_data
    from scripts.pcbgen.route_jack_grid import connectivity_signature, warning_identities, split_pad_groups
    from scripts.pcbgen.copper_identity import retention
    from scripts.pcbgen.complete_native_warnings import complete_reports
    from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
    unchanged_nonrouting((root/'after/osc-core.kicad_pcb').read_text(), (root/'fresh/osc-core.kicad_pcb').read_text())
    before, bdrc, b = settled_data(root, 'before')
    after, adrc, a = settled_data(root, 'after')
    fresh, fdrc, f = settled_data(root, 'fresh')
    check.require(check.digest(before) == report['bindings'][lock['board']]['board_sha256'], 'wrong original board')
    check.require(check.digest(root/'before/dump.json') == report['bindings'][lock['board']]['dump_sha256'], 'wrong original dump')
    check.require(check.digest(after) == check.digest(fresh), 'fresh whole-board bytes differ; no implicit zone/artwork exception')
    for suffix in ('.kicad_pro', '.kicad_dru'):
        check.require(check.digest(after.with_suffix(suffix)) == check.digest(fresh.with_suffix(suffix)), 'fresh project/rules mismatch')
    check.require(connectivity_signature(a) == connectivity_signature(f), 'fresh full connectivity mismatch')
    check.require(warning_identities(adrc) == warning_identities(fdrc), 'fresh warnings mismatch')
    for drc in (bdrc, adrc, fdrc):
        check.require(not drc['schematic_parity'] and not any(v['severity'] == 'error' for v in drc['violations']), 'native error/parity')
    for dump in (a, f):
        check.require(not split_pad_groups(b, dump), 'original connected group split')
        copper = retention(b, dump)
        check.require(not copper['removed_objects'] and not copper['changed_existing_uuids'], 'original copper changed')
    check.require(retention(a, f)['added_objects'] == 0 and retention(a, f)['removed_objects'] == 0 and not retention(a, f)['changed_existing_uuids'], 'fresh copper mismatch')
    # Replay raw full-warning proofs, not a status string in pilot-receipt.json.
    audit = root/'complete-warnings'
    full_b, full_a, proof = complete_reports(before, after, bdrc, adrc, audit/'holes-before', audit/'holes-after', audit/'silk', audit/'zones')
    for name, value in [('complete-before-drc', full_b), ('complete-after-drc', full_a), ('proof', proof)]:
        check.require(value == check.read(audit/(name+'.json')), 'complete warning proof drift')
    check.require(not set(warning_identities(full_a))-set(warning_identities(full_b)), 'new full warnings')
    receipt = check.read(root/'pilot-receipt.json')
    check.require(receipt['complete_warning_proof'] == proof, 'pilot proof binding drift')
    for phase, path in [('before', before), ('after', after), ('fresh', fresh)]:
        check.require(receipt[phase+'_sha256'] == check.digest(path), 'pilot board binding drift')
    result = evaluate_pairs(b, a, f, report['domains'][lock['domain']], lock['board'])
    result.update(domain=lock['domain'], board=lock['board'], full_audit_replayed=True,
                  source_commit=lock['source_tree_sha'], fixture_lock_sha256=check.digest(root/'fixture-lock.json'),
                  status='SAVED EVIDENCE REPLAY; independent review/admission receipts still required; no architecture adoption')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
