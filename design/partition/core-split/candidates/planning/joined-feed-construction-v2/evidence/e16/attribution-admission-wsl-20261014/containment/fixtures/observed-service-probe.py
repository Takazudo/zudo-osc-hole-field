import json,os,pathlib,resource,subprocess,sys,time,uuid
P=pathlib.Path
resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536));resource.setrlimit(resource.RLIMIT_CPU,(3,3))
if len(sys.argv)>1:
 unit=sys.argv[1]
 cg=P('/sys/fs/cgroup')/P('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
 print(json.dumps({'inside_pid':os.getpid(),'cgroup':str(cg),'limits':{k:(cg/k).read_text().strip() for k in ['memory.max','memory.swap.max','pids.max']}}),flush=True)
 cmd=['/usr/bin/systemctl','--user','set-property','--runtime',unit,'RuntimeMaxSec=5s']
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=3)
 print(json.dumps({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}),flush=True)
 r=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=RuntimeMaxUSec,ActiveEnterTimestampMonotonic'],capture_output=True,text=True,timeout=3)
 print(json.dumps({'timer_readback':r.stdout,'stderr':r.stderr,'exit':r.returncode}),flush=True)
 sys.exit(0)
unit='e16-service-fixture-'+uuid.uuid4().hex+'.service'
cmd=['/usr/bin/systemd-run','--user','--quiet','--wait','--pipe','--collect','--no-ask-password','--expand-environment=no','--unit='+unit,'--service-type=exec','-p','Delegate=memory','-p','MemoryMax=201326592','-p','MemorySwapMax=0','-p','TasksMax=16','-p','RuntimeMaxSec=12s','-p','TimeoutStopSec=1s','/usr/bin/python3','-I','-S','-B',__file__,unit]
print(json.dumps({'command':cmd}),flush=True)
r=subprocess.run(cmd,timeout=16)
print(json.dumps({'exit':r.returncode,'unit':unit}),flush=True)
