"""Isolate a nonclosing pilot via with separate pinned KiCad processes."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('receipt',type=Path);p.add_argument('work',type=Path);a=p.parse_args()
    rows=json.loads(a.receipt.read_text())['added'];a.work.mkdir(parents=True,exist_ok=True);results=[]
    for index,row in enumerate(rows):
        board=a.work/f'without-{index}.kicad_pcb';report=a.work/f'without-{index}.json'
        for command in (['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/diagnose_fanout.py',str(a.candidate),str(a.receipt),str(board),str(index)],['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/ratsnest.py',str(board),str(report)]):
            done=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if done.returncode:raise RuntimeError(f'{command[3]} failed: {done.stdout[-500:]}')
        results.append({'index':index,'ref':row['ref'],'pad':row['pad'],'native_edges_without_pair':json.loads(report.read_text())['native_unconnected_edges']})
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
