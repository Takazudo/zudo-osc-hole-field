import json,os,pathlib,socket,subprocess,sys,time,uuid
P=pathlib.Path
if len(sys.argv)>1:
 cg=P('/sys/fs/cgroup')/P('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
 print(json.dumps({'stage':'inside','pid':os.getpid(),'cgroup':str(cg),'limits':{k:(cg.parent/k).read_text().strip() for k in ['memory.max','memory.swap.max','pids.max']}}),flush=True)
 time.sleep(1)
 s=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);s.connect(os.environ['NOTIFY_SOCKET'].replace('@','\0',1) if os.environ['NOTIFY_SOCKET'].startswith('@') else os.environ['NOTIFY_SOCKET']);s.sendall(b'READY=1');s.close()
 print(json.dumps({'stage':'ready','monotonic':time.monotonic()}),flush=True)
 time.sleep(10)
else:
 unit='e16-notify-fixture-'+uuid.uuid4().hex+'.service'
 cmd=['/usr/bin/systemd-run','--user','--quiet','--wait','--pipe','--collect','--no-ask-password','--expand-environment=no','--unit='+unit,'--service-type=notify','-p','NotifyAccess=all','-p','Delegate=memory','-p','DelegateSubgroup=bootstrap','-p','MemoryMax=67108864','-p','MemorySwapMax=0','-p','TasksMax=8','-p','RuntimeMaxSec=2s','-p','TimeoutStartSec=10s','-p','TimeoutStopSec=1s','/usr/bin/python3','-I','-S','-B',__file__,'inside']
 print(json.dumps({'command':cmd}),flush=True);start=time.monotonic()
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=7)
 print(json.dumps({'stage':'exit','code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'elapsed_seconds':time.monotonic()-start}),flush=True)
 rows=[json.loads(x) for x in r.stdout.splitlines()];cg=P(rows[0]['cgroup']).parent
 print(json.dumps({'stage':'cleanup','unit':unit,'actual_cgroup_absent':not cg.exists()}),flush=True)
 assert r.returncode!=0 and not cg.exists() and 2.5<time.monotonic()-start<6
