"""Bind complete native snapshots to audited boards and explicit copper deltas."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stage41/native-pilot"))
from identity_guard import digest, kind, copper_contract, top_level_spans
from retirement_guard import bound_retirements
from acceptance import connectivity_gate


def stable(contract):
    return json.dumps(contract[:-1], separators=(',', ':'))


def compare_files(baseline, candidate, before_path, after_path, receipt_path, proposals, output):
    before, after = (json.loads(p.read_text()) for p in (before_path, after_path))
    receipt = json.loads(receipt_path.read_text())
    old_raw, new_raw = baseline.read_text(), candidate.read_text()
    for snapshot, raw in ((before, old_raw), (after, new_raw)):
        if snapshot['version'] != '10.0.6' or snapshot['board_sha256'] != digest(raw):
            raise ValueError('snapshot version/board binding')
    if receipt['canonical_sha256'] != digest(old_raw):
        raise ValueError('receipt baseline binding')
    audit = json.loads(candidate.with_name('identity-audit.json').read_text())
    if not audit['accepted_identity_only'] or audit['raw_sha256'] != digest(new_raw) or audit['canonical_sha256'] != digest(old_raw):
        raise ValueError('current complete identity audit missing')
    if audit['receipt_sha256'] != digest(receipt_path.read_text()) or audit['proposal_sha256'] != [digest(p.read_text()) for p in proposals]:
        raise ValueError('identity audit proposal/receipt binding')
    retired_hashes = {r['sha256'] for r in bound_retirements(receipt, old_raw)}
    retired = []; found = set()
    for a, b in top_level_spans(old_raw):
        raw = old_raw[a:b]
        if digest(raw) in retired_hashes:
            if kind(raw) not in ('segment', 'via') or digest(raw) in found:
                raise ValueError('ambiguous/non-copper retirement')
            found.add(digest(raw)); retired.append(stable(copper_contract(raw)))
    if found != retired_hashes: raise ValueError('missing reviewed retirement')
    added = []
    for path in proposals:
        proposal = json.loads(path.read_text())
        if proposal['removed_uuids']: raise ValueError('unexpected route retirement')
        for r in proposal['copper']:
            if r['kind'] == 'segment':
                shape = (r['start_nm'], r['end_nm'], [r['width_nm']], r['layer'])
            elif r['kind'] == 'via':
                shape = (r['at_nm'], [r['diameter_nm']], [r['drill_nm']], r['layers'])
            else: raise ValueError('unknown proposed copper')
            added.append(stable((r['kind'], r['uuid'], shape, r['net'])))
    if len(added) != len(set(added)) or len(retired) != len(set(retired)):
        raise ValueError('ambiguous explicit delta')
    result = connectivity_gate(before, after, retired, added, receipt['private_net_owners'])
    result.update(baseline_sha256=digest(old_raw), candidate_sha256=digest(new_raw), retired_objects=len(retired), added_objects=len(added))
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    if not result['accepted_connectivity_only']: raise SystemExit(1)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','candidate','before','after','receipt','output'): p.add_argument(name,type=Path)
    p.add_argument('--proposal',type=Path,action='append',default=[])
    a=p.parse_args();compare_files(a.baseline,a.candidate,a.before,a.after,a.receipt,a.proposal,a.output)
