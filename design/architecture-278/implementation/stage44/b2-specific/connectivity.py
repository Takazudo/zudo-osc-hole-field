"""Bind complete native partitions to the exact reviewed B2 copper delta."""
from pathlib import Path
import json,sys
from audit import BASE,BASE_HASH,bound_retirements,contract
from identity_guard import digest,copper_contract,top_level_spans
from acceptance import connectivity_gate

def compare(candidate,receipt_path,proof_path,proposal_paths,snapshot_path,output):
    raw0,raw=BASE.read_text(),candidate.read_text();receipt=json.loads(receipt_path.read_text());proof=json.loads(proof_path.read_text())
    retirement=bound_retirements(receipt,raw0,proof);hashes={r['sha256'] for r in retirement}
    old=json.loads(BASE.with_name('connectivity-passfresh.json').read_text());new=json.loads(snapshot_path.read_text())
    if old['board_sha256']!=digest(raw0) or new['board_sha256']!=digest(raw):raise ValueError('snapshot binding')
    audit=json.loads(candidate.with_name('identity-audit.json').read_text())
    if not audit['accepted_identity_only'] or audit['raw_sha256']!=digest(raw) or audit['baseline_sha256']!=BASE_HASH or audit['receipt_sha256']!=digest(receipt_path.read_text()) or audit['branch_proof_sha256']!=digest(proof_path.read_text()) or audit['proposal_sha256']!=[digest(p.read_text()) for p in proposal_paths]:raise ValueError('current audit binding')
    stable=lambda c:json.dumps(c[:-1],separators=(',',':'))
    retired=[stable(copper_contract(raw0[a:z])) for a,z in top_level_spans(raw0) if digest(raw0[a:z]) in hashes]
    added=[]
    for p in proposal_paths:
        d=json.loads(p.read_text())
        if d['removed_uuids']:raise ValueError('unexpected route retirement')
        added.extend(stable(contract(r)) for r in d['copper'])
    if len(retired)!=len(set(retired)) or len(added)!=len(set(added)):raise ValueError('ambiguous explicit delta')
    result=connectivity_gate(old,new,retired,added,receipt['private_net_owners'])
    result.update(baseline_sha256=BASE_HASH,candidate_sha256=digest(raw),retired_objects=len(retired),added_objects=len(added))
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
    if not result['accepted_connectivity_only']:raise SystemExit(1)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    for n in ('candidate','receipt','proof','snapshot','output'):p.add_argument(n,type=Path)
    p.add_argument('--proposal',type=Path,action='append',default=[]);a=p.parse_args();compare(a.candidate,a.receipt,a.proof,a.proposal,a.snapshot,a.output)
