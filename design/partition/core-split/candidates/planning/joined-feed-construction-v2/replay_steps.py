#!/usr/bin/env python3
"""Resumable, hash-ledgered E16 replay driver (source-only; no KiCad/native call).

Every step writes OUT/steps/<name>.json binding the exact SHA-256 of its
inputs, methods and outputs. With --resume a step is reused only when its
ledger, inputs, methods and every output still match; otherwise any partial or
stale output is moved to OUT/rejected/ (never deleted) and the step reruns, so
every dependent step is rebuilt too. Original retained receipts are untouched.
"""
import argparse,hashlib,json,os,shutil,subprocess,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
TIMEOUT='180s'
EVAL_METHODS=['evaluate_access.py','staged_caps.py','connectivity.py','port_obligations.py','clip_sheets.py','evidence/board-access-design.json']
ACCESS_METHODS={'construct_access.py':['construct_access.py'],'two_face.py':['two_face.py','construct_access.py']}
CAND05_INPUTS=[HERE/f for f in ['construct.py','mechanical.py','contact.py']]+[ROOT/p for p in ['scripts/partition/core_split_candidates.py','design/partition/core-split/candidates/two.json','design/partition/core-split/candidates/input-lock.json','boards/osc-core/osc-core.kicad_pcb']]
CAND05_FILES=['KA.kicad_pcb','KB.kicad_pcb','terminals.json','contacts.json.gz','mechanical.json.gz','source-dispositions.json.gz']
# Round table: (name, method script, arguments, planes from the previous evaluation?).
ROUNDS=[('r1','construct_access.py',['--method','via'],True),('r2','construct_access.py',['--method','route'],False),('r3','construct_access.py',['--method','route'],True),
        # r4 repeats r3 unchanged: route targets are built once from the input graph, so r3 closures are new targets.
        ('r4','construct_access.py',['--method','route'],True),
        ('t1','two_face.py',['--use-fed-transitions','--only','evidence/e16/t1-batch.json'],True),
        ('t2','two_face.py',['--use-fed-transitions'],True)]
ROUND_NAMES=[r[0] for r in ROUNDS]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(c,m):
 if not c:raise SystemExit('replay: '+m)
def files(p):
 p=Path(p)
 if p.is_dir():return {str(q.relative_to(p)):sha(q) for q in sorted(p.rglob('*')) if q.is_file()}
 return {'':sha(p)} if p.exists() else None
class Ledger:
 def __init__(self,out,resume,python):
  self.out=out;self.resume=resume;self.python=python;(out/'steps').mkdir(parents=True,exist_ok=True);self.log=[]
 def rel(self,p):
  p=Path(p)
  for base in (self.out,ROOT):
   if p.is_relative_to(base):return str(p.relative_to(base))
  return str(p)
 def reject(self,name,outputs,why):
  dest=self.out/'rejected'/f'{name}-{time.strftime("%Y%m%dT%H%M%S")}-{os.getpid()}';moved=[]
  for o in outputs:
   if o.exists():dest.mkdir(parents=True,exist_ok=True);shutil.move(str(o),dest/o.name);moved.append(self.rel(o))
  stamp=self.out/'steps'/f'{name}.json'
  # The ledger shares its step name with outputs such as <step>.json: keep it under a distinct name.
  if stamp.exists():dest.mkdir(parents=True,exist_ok=True);shutil.move(str(stamp),dest/('ledger-'+stamp.name))
  if moved or dest.exists():self.log.append({'step':name,'rejected':why,'moved_to':self.rel(dest),'outputs':moved})
 def run(self,name,command,inputs,methods,outputs,check=None):
  stamp=self.out/'steps'/f'{name}.json';inputs=[HERE/q for q in inputs];methods=[HERE/q for q in methods]
  bound={'inputs':{self.rel(p):sha(p) for p in inputs},'methods':{self.rel(p):sha(p) for p in methods},'command':[str(c) for c in command]}
  if stamp.exists() or any(o.exists() for o in outputs):
   need(self.resume,f'{name}: output exists; fresh OUTDIR or --resume required')
   old=json.loads(stamp.read_text()) if stamp.exists() else None
   if old is None:why='partial: outputs without a completed ledger'
   elif any(old.get(k)!=bound[k] for k in bound):why='stale: '+','.join(k for k in bound if old.get(k)!=bound[k])
   elif old.get('exit_code')!=0:why='failed earlier run'
   elif any(files(o)!=old['outputs'].get(self.rel(o)) for o in outputs):why='output bytes differ from ledger'
   else:
    self.log.append({'step':name,'reused':True});print(json.dumps({'step':name,'reused':True}),flush=True);return old
   self.reject(name,outputs,why)
  start=time.monotonic();proc=subprocess.Popen(['timeout',TIMEOUT,self.python]+[str(c) for c in command],cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  pipes={}
  readers=[threading.Thread(target=lambda k,f:pipes.__setitem__(k,f.read()),args=(k,f)) for k,f in (('out',proc.stdout),('err',proc.stderr))]
  for t in readers:t.start()
  _,status,usage=os.wait4(proc.pid,0)
  for t in readers:t.join()
  code=os.waitstatus_to_exitcode(status);proc.returncode=code;stdout,stderr=pipes['out'],pipes['err']
  rec=dict(bound,step=name,exit_code=code,elapsed_seconds=round(time.monotonic()-start,3),
           stdout_tail=stdout[-4000:],stderr_tail=stderr[-4000:],peak_rss_KiB=usage.ru_maxrss,
           outputs={self.rel(o):files(o) for o in outputs},native_calls=0)
  if check and proc.returncode==0:rec['check']=check()
  stamp.write_text(json.dumps(rec,indent=1)+'\n');self.log.append({'step':name,'exit_code':proc.returncode,'elapsed_seconds':rec['elapsed_seconds']})
  print(json.dumps({'step':name,'exit_code':proc.returncode,'seconds':rec['elapsed_seconds'],'tail':stdout.strip().splitlines()[-1:] }),flush=True)
  need(proc.returncode==0,f'{name} failed ({proc.returncode}): {stderr[-600:]}')
  return rec
def main():
 p=argparse.ArgumentParser();p.add_argument('--python',required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--board',choices=['KA','KB'],action='append',help='default: both, serialized')
 p.add_argument('--through',choices=ROUND_NAMES,default=ROUND_NAMES[-1],help='last access round to build')
 p.add_argument('--resume',action='store_true',help='reuse only fully hash-validated steps; reject stale/partial ones');a=p.parse_args()
 started=time.strftime('%Y-%m-%dT%H:%M:%S%z');out=a.output;need(out.is_absolute() and not out.is_relative_to(ROOT),'absolute OUTDIR outside the repository required')
 need(a.resume or not out.exists(),'fresh OUTDIR required (or --resume)');out.mkdir(parents=True,exist_ok=True)
 L=Ledger(out,a.resume,a.python);c5=out/'cand05'
 expected=json.loads((HERE/'evidence/e16/index.json').read_text())['candidate05']
 L.run('cand05',['construct.py','--output',c5],CAND05_INPUTS,[],[c5],check=lambda:{f:sha(c5/f)==expected[f] for f in CAND05_FILES})
 need(all(sha(c5/f)==expected[f] for f in CAND05_FILES),'candidate05 no longer replays byte-for-byte')
 ports=HERE/'evidence/mandatory-physical-ports-review.json';design=HERE/'evidence/board-access-design.json'
 rounds=ROUNDS[:ROUND_NAMES.index(a.through)+1]
 for b in a.board or ['KA','KB']:
  norm=out/f'{b}-normalized.json'
  L.run(f'{b}-normalize',['normalize_board.py','--board-id',b,'--pcb',c5/f'{b}.kicad_pcb','--terminals',c5/'terminals.json','--output',norm],[c5/f'{b}.kicad_pcb',c5/'terminals.json',ports],['normalize_board.py'],[norm])
  def evaluate(tag,src):
   e=out/f'{b}-eval-{tag}'
   L.run(f'{b}-eval-{tag}',['evaluate_access.py','--source',src,'--clip-helper','clip_sheets.py','--design',design,'--python',a.python,'--output',e],[src],EVAL_METHODS,[e]);return e
  prev=norm;e=evaluate('base',norm)
  for name,script,args,planes in rounds:
   args=list(args);extra=[HERE/args[args.index('--only')+1]] if '--only' in args else []
   if planes:args+=['--planes',e/'clipped-sheets.json']
   src,rep=out/f'{b}-access-{name}.json',out/f'{b}-access-{name}-report.json'
   L.run(f'{b}-access-{name}',[script,*args,'--source',prev,'--graph',e/'port-graph.json','--census',e/'port-obligations.json','--output',src,'--report',rep],
         [prev,e/'port-graph.json',e/'port-obligations.json']+([e/'clipped-sheets.json'] if planes else [])+extra,ACCESS_METHODS[script],[src,rep])
   prev=src;e=evaluate(name,src)
 log=out/'replay-log.json';prior=json.loads(log.read_text()) if log.exists() else {};runs=prior.get('invocations',[prior] if prior else [])
 runs.append({'started':started,'through':a.through,'boards':a.board or ['KA','KB'],'resume':a.resume,'log':L.log})
 log.write_text(json.dumps({'invocations':runs},indent=1)+'\n')
if __name__=='__main__':main()
