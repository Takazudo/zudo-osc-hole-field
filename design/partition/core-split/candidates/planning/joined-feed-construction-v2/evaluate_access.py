#!/usr/bin/env python3
"""Seal bounded source-only cap, clip, graph and COMPLETE pad-census execution."""
import argparse,hashlib,json,resource,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
 if not c:raise ValueError(m)
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--clip-helper',type=Path,required=True);p.add_argument('--design',type=Path,required=True);p.add_argument('--python',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(a.output.is_absolute() and not a.output.exists(),'fresh absolute output directory');a.output.mkdir()
 source=a.source.resolve();clip=a.clip_helper.resolve();design=a.design.resolve();caps=a.output/'normalized-caps.json';planes=a.output/'clipped-sheets.json';graph=a.output/'port-graph.json';census=a.output/'port-obligations.json'
 methods=[Path(__file__).resolve(),HERE/'staged_caps.py',HERE/'connectivity.py',HERE/'port_obligations.py',clip]
 initial={str(q):sha(q) for q in [source,design]+methods};receipts=[]
 steps=[('caps',[source,HERE/'staged_caps.py'],[str(HERE/'staged_caps.py'),'--board',str(source),'--output',str(caps)],caps),('clip',[caps,clip,design],[str(clip),'--filtered-board',str(caps),'--design',str(design),'--clip-only','--output',str(planes)],planes),('graph',[caps,planes,HERE/'connectivity.py',HERE/'staged_caps.py'],[str(HERE/'connectivity.py'),'--board',str(caps),'--planes',str(planes),'--output',str(graph)],graph),('census',[caps,planes,graph,HERE/'port_obligations.py'],[str(HERE/'port_obligations.py'),'--board',str(caps),'--planes',str(planes),'--graph',str(graph),'--output',str(census)],census)]
 for name,inputs,args,out in steps:
  need(all(sha(Path(q))==h for q,h in initial.items()),'initial inputs/methods changed')
  seals={str(q):sha(q) for q in inputs};start=time.monotonic();command=['timeout','180s',str(a.python)]+args
  result=subprocess.run(command,capture_output=True,text=True)
  unchanged=all(sha(Path(q))==h for q,h in initial.items()) and all(sha(Path(q))==h for q,h in seals.items())
  receipt={'step':name,'input_sha256':seals,'command':command,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-start,'stdout':result.stdout,'stderr':result.stderr,'output_sha256':sha(out) if out.exists() else None,'inputs_before_after_equal':unchanged,'native_calls':0}
  (a.output/(name+'-execution.json')).write_text(json.dumps(receipt,indent=2)+'\n');receipts.append(receipt)
  print(json.dumps({'step':name,'exit_code':result.returncode,'seconds':receipt['elapsed_seconds'],'stdout':result.stdout}),flush=True)
  need(unchanged,'inputs/methods changed during source check');need(result.returncode==0,'source step failed: '+name)
 complete=json.loads(census.read_text());result={'status':'SOURCE_ALL_PHYSICAL_PORTS_CONNECTED' if not complete['unresolved'] else 'SOURCE_DISCONNECTED_PHYSICAL_PORTS','board':complete['board'],'initial_input_sha256':initial,'steps':receipts,'unresolved_physical_pad_count':len(complete['unresolved']),'unresolved_direct_load_count':complete['direct_loads'],'unresolved_supplemental_count':complete['supplemental'],'complete_physical_connectivity':not complete['unresolved'],'signed_load_proof_complete':False,'manufacturing_qualified':False,'accepted':False,'native_calls':0}
 (a.output/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','board','unresolved_physical_pad_count','unresolved_direct_load_count','unresolved_supplemental_count']}))
if __name__=='__main__':main()
