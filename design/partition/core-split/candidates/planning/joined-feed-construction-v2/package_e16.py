#!/usr/bin/env python3
"""Copy the compact, hash-bound E16 receipts from a replay directory into evidence/e16."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROUNDS=['base','r1','r2','r3']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gz(data,path):path.write_bytes(gzip.compress(data,mtime=0))
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,default=HERE/'evidence/e16');a=p.parse_args()
 run=a.run.resolve();out=a.output;out.mkdir(parents=True,exist_ok=True)
 index={'schema':'e16-index-v1','epoch':'E16','replay':'bash replay_e16.sh PYTHON FRESH_ABSOLUTE_DIR','native_calls':0,'accepted':False,
        'candidate05':{f:sha(run/'cand05'/f) for f in ['KA.kicad_pcb','KB.kicad_pcb','terminals.json','contacts.json.gz','mechanical.json.gz','source-dispositions.json.gz']},
        'methods':{f:sha(HERE/f) for f in ['construct.py','normalize_board.py','clip_sheets.py','staged_caps.py','connectivity.py','port_obligations.py','evaluate_access.py','construct_access.py','replay_e16.sh']},
        'boards':{}}
 for b in ['KA','KB']:
  rows={};norm=json.loads((run/f'{b}-normalized.json').read_text());ids={o['id'] for o in norm['objects']}
  for r in ROUNDS:
   ev=run/f'{b}-eval-{r}';e=json.loads((ev/'evaluation.json').read_text())
   rows[r]={'unresolved':e['unresolved_physical_pad_count'],'direct':e['unresolved_direct_load_count'],'supplemental':e['unresolved_supplemental_count'],
            'source_sha256':sha(run/(f'{b}-normalized.json' if r=='base' else f'{b}-access-{r}.json')),
            'steps':[{k:s[k] for k in ['step','exit_code','elapsed_seconds','output_sha256','command']} for s in e['steps']]}
   for s in e['steps']:(out/f'{b}-{r}-{s["step"]}-execution.json').write_text(json.dumps(s,indent=1)+'\n')
   if r!='base':
    rep=run/f'{b}-access-{r}-report.json';gz(rep.read_bytes(),out/f'{b}-access-{r}-report.json.gz')
    rows[r]['access_report']={k:v for k,v in json.loads(rep.read_text()).items() if k in ('method','counts','elapsed_seconds','peak_KiB','output_sha256','parameters_mm')}
   prev={x['pad_id'] for x in json.loads((run/f'{b}-eval-{ROUNDS[max(0,ROUNDS.index(r)-1)]}/port-obligations.json').read_text())['unresolved']}
   now={x['pad_id'] for x in json.loads((ev/'port-obligations.json').read_text())['unresolved']}
   rows[r]['newly_disconnected_vs_previous']=sorted(now-prev);rows[r]['closed_vs_previous']=len(prev-now)
  final=run/f'{b}-eval-r3'
  shutil.copyfile(final/'port-obligations.json',out/f'{b}-r3-port-obligations.json');gz((final/'port-graph.json').read_bytes(),out/f'{b}-r3-port-graph.json.gz')
  delta=[o for o in json.loads((run/f'{b}-access-r3.json').read_text())['objects'] if o['id'] not in ids]
  gz(json.dumps(delta,sort_keys=True,separators=(',',':')).encode(),out/f'{b}-access-delta.json.gz')
  index['boards'][b]={'normalized_sha256':sha(run/f'{b}-normalized.json'),'access_objects':len(delta),'rounds':rows}
 index['files']={f.name:sha(f) for f in sorted(out.iterdir()) if f.name!='index.json'}
 (out/'index.json').write_text(json.dumps(index,indent=1)+'\n');print(json.dumps({b:{r:v['unresolved'] for r,v in d['rounds'].items()} for b,d in index['boards'].items()}))
if __name__=='__main__':main()
