#!/usr/bin/env python3
"""Run one bounded source screen with before/after input and method seals."""
import argparse,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(candidate,kind,output):
 if output.exists() or output.with_suffix('.receipt.json').exists():raise ValueError('fresh evidence paths required')
 receipt=json.loads((candidate/'receipt.json').read_text());inputs={str(ROOT/p):h for p,h in receipt['input_sha256'].items()}
 feed=ROOT/'circuit/routing/epic-242/decision-pilots/feed-arrangement';lock=json.loads((feed/'source-lock.json').read_text())
 inputs.update({str(ROOT/p):h for p,h in lock['files'].items()})
 helpers=[HERE/'check_geometry.py',HERE/'check_solids.py',Path(__file__),feed/'source-lock.json',feed/'check.py',feed/'robust_curve.py']
 inputs.update({str(p):sha(p) for p in helpers+list(candidate.glob('*.json'))+list(candidate.glob('*.json.gz'))})
 def verify():
  for p,h in inputs.items():
   if sha(Path(p))!=h:raise ValueError('input drift '+p)
 verify();helper=HERE/('check_geometry.py' if kind=='sweep' else 'check_solids.py');command=[sys.executable,str(helper),'--candidate',str(candidate),'--output',str(output)]
 start=time.monotonic();result=subprocess.run(command,capture_output=True,text=True,timeout=175,check=True,cwd=ROOT);verify()
 output.with_suffix('.log').write_text(result.stdout+result.stderr)
 record={'status':'PASS_EXECUTION_SEALS_NOT_GEOMETRY_VERDICT','command':command,'input_sha256':inputs,'output_sha256':sha(output),'returncode':result.returncode,'elapsed_seconds':time.monotonic()-start,'memory_limit_bytes':2*1024**3,'child_timeout_seconds':175,'native_calls':0}
 output.with_suffix('.receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ['input_sha256','command']}))
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--kind',choices=['sweep','solids'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.candidate,a.kind,a.output)
