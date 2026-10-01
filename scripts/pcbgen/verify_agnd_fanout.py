"""Full-native disposable AGND fanout promotion gate."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.verify_local_links import blocks,TRACK_NET_RE

def verify(source,candidate,receipt_path,before_ratsnest,after_ratsnest,drc_path,expected_sha,diagnosis_dir=None):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_sha:raise ValueError('source board changed since AGND pilot')
    receipt=json.loads(receipt_path.read_text());before=blocks(source);after=blocks(candidate)
    net=receipt['net']
    if net not in ('AGND','+12V','-12V','+5V') or any(row['net']!=net for row in receipt['added']):raise ValueError('invalid plane-net receipt')
    if before['non_copper']!=after['non_copper']:raise ValueError('non-copper full-board block changed')
    for kind in ('segment','via','arc'):
        if any(after[kind].get(key)!=block for key,block in before[kind].items()):raise ValueError(f'prior {kind} changed')
    tracks={r['track_uuid'] for r in receipt['added']};vias={r['via_uuid'] for r in receipt['added']}
    new_tracks=set(after['segment'])-set(before['segment']);new_vias=set(after['via'])-set(before['via'])
    if new_tracks!=tracks or new_vias!=vias or set(after['arc'])!=set(before['arc']):raise ValueError('new copper identity differs from AGND receipt')
    if any(not (m:=TRACK_NET_RE.search(after[kind][key])) or m[1]!=net for kind,keys in (('segment',tracks),('via',vias)) for key in keys):raise ValueError('wrong-net fanout copper')
    old=json.loads(before_ratsnest.read_text())['native_unconnected_edges'];new=json.loads(after_ratsnest.read_text())['native_unconnected_edges']
    if new>=old:raise ValueError('plane fanout did not reduce full native ratsnest')
    leave_one_out='NOT NEEDED'
    if old-new!=len(receipt['added']):
        if diagnosis_dir is None:raise ValueError('topology group needs leave-one-out native evidence')
        for index,row in enumerate(receipt['added']):
            without=blocks(diagnosis_dir/f'without-{index}.kicad_pcb')
            if without['non_copper']!=after['non_copper']:raise ValueError('leave-one-out changed non-copper board')
            for kind,missing in (('segment',row['track_uuid']),('via',row['via_uuid'])):
                if set(without[kind])!=set(after[kind])-{missing} or any(without[kind][key]!=after[kind][key] for key in without[kind]):raise ValueError('leave-one-out removed wrong copper')
            if without['arc']!=after['arc']:raise ValueError('leave-one-out arc changed')
            count=json.loads((diagnosis_dir/f'without-{index}.json').read_text())['native_unconnected_edges']
            if count!=new+1:raise ValueError('fanout pair not essential in final topology')
        leave_one_out='PASS - every pair removal increases native edge count by one'
    drc=json.loads(drc_path.read_text())
    if drc['kicad_version']!='10.0.6' or any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:raise ValueError('native DRC/parity failed')
    return {'status':'PASS - unvalidated draft plane fanout only','net':net,'source_sha256':expected_sha,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'vias_and_tracks_added':len(vias),'native_unconnected_edges_before':old,'native_unconnected_edges_after':new,'native_edge_reduction':old-new,'leave_one_out_essentiality':leave_one_out,'rule_errors':0,'schematic_parity_issues':0,'all_prior_non_copper_blocks_preserved':True,'prior_copper_preserved':sum(len(before[k]) for k in ('segment','via','arc'))}
def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('receipt',type=Path);p.add_argument('before_ratsnest',type=Path);p.add_argument('after_ratsnest',type=Path);p.add_argument('drc',type=Path);p.add_argument('expected_sha');p.add_argument('--output',type=Path,required=True);p.add_argument('--diagnosis-dir',type=Path);a=p.parse_args()
    report=verify(a.source,a.candidate,a.receipt,a.before_ratsnest,a.after_ratsnest,a.drc,a.expected_sha,a.diagnosis_dir)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
