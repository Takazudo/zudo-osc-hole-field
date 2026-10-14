import json,os,pathlib,resource,subprocess,sys,time,uuid
P=pathlib.Path
if len(sys.argv)>1:
 cg=P('/sys/fs/cgroup')/P('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
 pid=os.fork()
 if pid==0:
  os.setsid();time.sleep(10);os._exit(0)
 print(json.dumps({'stage':'inside','pid':os.getpid(),'detached_child':pid,'cgroup':str(cg),'child_cgroup':P(f'/proc/{pid}/cgroup').read_text(),'limits':{k:(cg/k).read_text().strip() for k in ['memory.max','memory.swap.max','pids.max']}}),flush=True)
 time.sleep(10)
else:
 unit='e16-kill-fixture-'+uuid.uuid4().hex+'.scope'
 cmd=['/usr/bin/systemd-run','--user','--scope','--quiet','--collect','--no-ask-password','--expand-environment=no','--unit='+unit,'-p','MemoryMax=67108864','-p','MemorySwapMax=0','-p','TasksMax=4','-p','RuntimeMaxSec=1s','-p','TimeoutStopSec=1s','/usr/bin/python3','-I','-S','-B',__file__,'inside']
 print(json.dumps({'command':cmd}),flush=True);started=time.monotonic()
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
 print(json.dumps({'stage':'exit','code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'elapsed_seconds':time.monotonic()-started}),flush=True)
 observed=json.loads(r.stdout.strip())
 for key in ['pid','detached_child']:
  p=P('/proc')/str(observed[key]);state=(p/'status').read_text().split('State:',1)[1].splitlines()[0].strip() if p.exists() else 'absent'
  print(json.dumps({'stage':'process_after','pid':observed[key],'state':state}),flush=True)
 state=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=LoadState,ActiveState,ControlGroup'],capture_output=True,text=True,timeout=3)
 print(json.dumps({'stage':'cleanup','unit':unit,'properties':state.stdout,'actual_cgroup_absent':not P(observed['cgroup']).exists()}),flush=True)
 assert r.returncode!=0 and not P(observed['cgroup']).exists()
