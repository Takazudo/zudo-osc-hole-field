"""Guarded disposable full-board AGND batch with SHA-matched promotion.

Invoke via heavy-guard.sh. A failed native gate leaves the source PCB untouched.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.verify_agnd_fanout import verify

def run(*args):
    done=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if done.stdout:print(done.stdout[-1000:],end='',flush=True)
    if done.returncode:raise RuntimeError(f'{args[0]} failed with exit {done.returncode}')

def batch(board_id,index,limit,net):
    board=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb';project=board.with_suffix('.kicad_pro');schematic=board.with_suffix('.kicad_sch')
    if not all(p.exists() for p in (board,project,schematic)):raise FileNotFoundError(board)
    source_sha=hashlib.sha256(board.read_bytes()).hexdigest()
    slug={'AGND':'agnd','+12V':'plus12v','-12V':'minus12v','+5V':'plus5v'}[net]
    work=board.parent/'routing-work'/f'{slug}-batch-{index}';work.mkdir(parents=True,exist_ok=True)
    candidate=work/f'{board_id}.kicad_pcb';receipt=work/'geometry.json';before=work/'before-ratsnest.json';after=work/'after-ratsnest.json';drc=work/'drc.json'
    run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/ratsnest.py',str(board.relative_to(ROOT)),str(before.relative_to(ROOT)))
    baseline_drc=work/'baseline-drc.json'
    run('bash','scripts/kicad/run.sh','kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(baseline_drc.relative_to(ROOT)),str(board.relative_to(ROOT)))
    run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_agnd_fanout.py',board_id,'--board',str(board.relative_to(ROOT)),'--output',str(candidate.relative_to(ROOT)),'--receipt',str(receipt.relative_to(ROOT)),'--limit',str(limit),'--net='+net)
    run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/ratsnest.py',str(candidate.relative_to(ROOT)),str(after.relative_to(ROOT)))
    adjacent=board.parent/f'{board_id}-{slug}-batch-{index}.kicad_pcb'
    try:
        shutil.copy2(candidate,adjacent);shutil.copy2(project,adjacent.with_suffix('.kicad_pro'));shutil.copy2(schematic,adjacent.with_suffix('.kicad_sch'))
        run('bash','scripts/kicad/run.sh','kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc.relative_to(ROOT)),str(adjacent.relative_to(ROOT)))
        old_warnings=collections.Counter(v['type'] for v in json.loads(baseline_drc.read_text())['violations'] if v['severity']=='warning')
        new_warnings=collections.Counter(v['type'] for v in json.loads(drc.read_text())['violations'] if v['severity']=='warning')
        added_warnings=new_warnings-old_warnings
        if added_warnings:raise ValueError(f'new native DRC warnings: {dict(added_warnings)}')
        pair_count=len(json.loads(receipt.read_text())['added'])
        edge_delta=json.loads(before.read_text())['native_unconnected_edges']-json.loads(after.read_text())['native_unconnected_edges']
        diagnosis=None
        if edge_delta!=pair_count:
            diagnosis=work/'diagnosis'
            run('python3','scripts/pcbgen/diagnose_fanout_host.py',str(candidate.relative_to(ROOT)),str(receipt.relative_to(ROOT)),str(diagnosis.relative_to(ROOT)))
        result=verify(board,candidate,receipt,before,after,drc,source_sha,diagnosis)
        if hashlib.sha256(board.read_bytes()).hexdigest()!=source_sha:raise ValueError('source board changed before promotion')
        shutil.copy2(candidate,board)
        report={**result,'geometry':json.loads(receipt.read_text()),'batch_index':index,'draft':True,'physical_hot_ground_neck':'NOT RUN #65'}
        target=board.parent/'reports'/f'{slug}-batch-{index}.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(f'{board_id}: {net} batch {index} PROMOTED; {result["native_unconnected_edges_before"]}->{result["native_unconnected_edges_after"]}; {result["vias_and_tracks_added"]} vias/tracks',flush=True)
    finally:
        for path in (adjacent,adjacent.with_suffix('.kicad_pro'),adjacent.with_suffix('.kicad_sch')):path.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id',choices=('osc-jack-left','osc-jack-right'));p.add_argument('batch_index',type=int);p.add_argument('--limit',type=int,default=30);p.add_argument('--net',choices=('AGND','+12V','-12V','+5V'),default='AGND');a=p.parse_args()
    if a.batch_index<1 or not 1<=a.limit<=100:raise ValueError('invalid batch request')
    batch(a.board_id,a.batch_index,a.limit,a.net)
if __name__=='__main__':main()
