#!/usr/bin/env python3
"""Copy the compact, hash-bound E16 receipts from a replay directory into evidence/e16.

Appends rounds to the retained index. Existing receipts are never overwritten:
a file that already exists must be byte-identical, or packaging stops. The
replay step ledgers and content comparisons are retained under replay/.
"""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
import replay_steps
HERE=Path(__file__).resolve().parent
ROUNDS=['base']+replay_steps.ROUND_NAMES
SCRIPT={name:script for name,script,_,_ in replay_steps.ROUNDS}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(path,data):
 if path.exists():
  if path.read_bytes()!=data:raise SystemExit(f'refusing to overwrite retained receipt {path.name}')
  return
 path.write_bytes(data)
def gz(data):return gzip.compress(data,mtime=0)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,default=HERE/'evidence/e16')
 p.add_argument('--rounds',default='r4,t1,t2',help='rounds to append');p.add_argument('--replay-tag',required=True);a=p.parse_args()
 run=a.run.resolve();out=a.output;new=a.rounds.split(',');index=json.loads((out/'index.json').read_text())
 for f in ['construct_access.py','two_face.py','replay_steps.py','replay_e16.sh','compare_replay.py','package_e16.py']:
  # methods records the bytes behind the retained base-r3 run; current bytes go to methods_added.
  index.setdefault('methods_added',{})[f]=sha(HERE/f)
 for b in ['KA','KB']:
  rows=index['boards'][b]['rounds']
  for r in new:
   if r in rows:raise SystemExit(f'{b} {r} already retained')
   i=ROUNDS.index(r);prev=ROUNDS[i-1];ev=run/f'{b}-eval-{r}';e=json.loads((ev/'evaluation.json').read_text())
   rows[r]={'unresolved':e['unresolved_physical_pad_count'],'direct':e['unresolved_direct_load_count'],'supplemental':e['unresolved_supplemental_count'],
            'method_script':SCRIPT[r],'source_sha256':sha(run/f'{b}-access-{r}.json'),
            'steps':[{k:s[k] for k in ['step','exit_code','elapsed_seconds','output_sha256','command']} for s in e['steps']]}
   for s in e['steps']:put(out/f'{b}-{r}-{s["step"]}-execution.json',(json.dumps(s,indent=1)+'\n').encode())
   rep=run/f'{b}-access-{r}-report.json';put(out/f'{b}-access-{r}-report.json.gz',gz(rep.read_bytes()))
   rows[r]['access_report']={k:v for k,v in json.loads(rep.read_text()).items() if k in ('method','batch','counts','elapsed_seconds','peak_KiB','output_sha256','parameters_mm')}
   before={x['pad_id']:x for x in json.loads((run/f'{b}-eval-{prev}/port-obligations.json').read_text())['unresolved']}
   now={x['pad_id'] for x in json.loads((ev/'port-obligations.json').read_text())['unresolved']}
   rows[r]['newly_disconnected_vs_previous']=sorted(set(now)-set(before))
   rows[r]['closed_vs_previous']=len(set(before)-now)
   rows[r]['closed_identities']=[{k:before[x][k] for k in ['pad_id','ref','pad','net','direct_load']} for x in sorted(set(before)-now)]
  last=new[-1];final=run/f'{b}-eval-{last}'
  put(out/f'{b}-{last}-port-obligations.json',(final/'port-obligations.json').read_bytes());put(out/f'{b}-{last}-port-graph.json.gz',gz((final/'port-graph.json').read_bytes()))
  base_ids={o['id'] for o in json.loads((run/f'{b}-access-r3.json').read_text())['objects']}
  delta=[o for o in json.loads((run/f'{b}-access-{last}.json').read_text())['objects'] if o['id'] not in base_ids]
  put(out/f'{b}-access-delta-r4-{last}.json.gz',gz(json.dumps(delta,sort_keys=True,separators=(',',':')).encode()))
  index['boards'][b]['access_objects_after_r3']=len(delta);index['boards'][b]['final_round']=last
 rd=out/'replay'/a.replay_tag;rd.mkdir(parents=True,exist_ok=True)
 for f in sorted((run/'steps').glob('*.json')):put(rd/f.name,f.read_bytes())
 if (run/'replay-log.json').exists():put(rd/'replay-log.json',(run/'replay-log.json').read_bytes())
 index['files']={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='index.json'}
 (out/'index.json').write_text(json.dumps(index,indent=1)+'\n');print(json.dumps({b:{r:v['unresolved'] for r,v in d['rounds'].items()} for b,d in index['boards'].items()}))
if __name__=='__main__':main()
