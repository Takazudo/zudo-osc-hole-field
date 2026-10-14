import json,os,pathlib,resource,subprocess,sys,time,uuid
P=pathlib.Path
if len(sys.argv)>1 and sys.argv[1]=='inside':
 cg=P('/sys/fs/cgroup')/P('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
 print(json.dumps({'stage':'inside','pid':os.getpid(),'uid':os.getuid(),'cgroup':str(cg),'mount_ns':os.readlink('/proc/self/ns/mnt'),'limits':{k:(cg/k).read_text().strip() for k in ['memory.max','memory.swap.max','pids.max','cgroup.controllers','cgroup.procs']}}),flush=True)
 sup=cg/'probe';work=P(sys.argv[2]);created=False;enabled=False;moved=False;mounted=False
 try:
  sup.mkdir();created=True
  (sup/'cgroup.procs').write_text(str(os.getpid()));moved=True
  (cg/'cgroup.subtree_control').write_text('+memory');enabled=True
  (sup/'memory.max').write_text(str(64*1024**2));(sup/'memory.swap.max').write_text('0')
  subprocess.run(['/usr/bin/mount','--no-mtab','--internal-only','-t','tmpfs','-o','size=1048576,nr_inodes=32,nosuid,nodev,noexec,mode=0700','e16-fixture',str(work)],check=True,timeout=3);mounted=True
  (work/'synthetic').write_bytes(b'x'*4096)
  print(json.dumps({'stage':'tmpfs','stat_bytes':os.statvfs(work).f_blocks*os.statvfs(work).f_frsize,'membership':P('/proc/self/cgroup').read_text(),'memory':{k:(cg/k).read_text().strip() for k in ['memory.current','memory.peak','memory.swap.current','memory.events']}}),flush=True)
  (work/'synthetic').unlink()
 finally:
  if mounted:subprocess.run(['/usr/bin/umount','--no-mtab','--internal-only',str(work)],check=True,timeout=3)
  if enabled:(cg/'cgroup.subtree_control').write_text('-memory')
  if moved:(cg/'cgroup.procs').write_text(str(os.getpid()))
  if created:sup.rmdir()
  print(json.dumps({'stage':'inner_cleanup','mounted':mounted,'created':created}),flush=True)
else:
 import tempfile
 resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536));resource.setrlimit(resource.RLIMIT_CPU,(5,5))
 unit='e16-containment-fixture-'+uuid.uuid4().hex+'.scope';desc='E16 synthetic containment '+unit
 with tempfile.TemporaryDirectory(prefix='e16-containment-fixture-') as d:
  cmd=['/usr/bin/systemd-run','--user','--scope','--quiet','--collect','--no-ask-password','--expand-environment=no','--unit='+unit,'--description='+desc,'-p','Delegate=memory','-p','MemoryMax=201326592','-p','MemorySwapMax=0','-p','TasksMax=16','-p','RuntimeMaxSec=12s','-p','TimeoutStopSec=1s','/usr/bin/unshare','--user','--map-current-user','--keep-caps','--mount','--propagation','private','/usr/bin/python3','-I','-S','-B',__file__,'inside',d]
  print(json.dumps({'command':cmd,'parent_pid':os.getpid(),'parent_cgroup':P('/proc/self/cgroup').read_text(),'parent_mount_ns':os.readlink('/proc/self/ns/mnt')}),flush=True)
  started=time.monotonic()
  try:
   result=subprocess.run(cmd,timeout=16)
   print(json.dumps({'stage':'command_result','exit':result.returncode,'elapsed':time.monotonic()-started}),flush=True)
  finally:
   state=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=LoadState,ActiveState,ControlGroup,Description'],capture_output=True,text=True,timeout=3)
   print(json.dumps({'stage':'unit_after','exit':state.returncode,'stdout':state.stdout,'stderr':state.stderr}),flush=True)
   props=dict(x.split('=',1) for x in state.stdout.splitlines() if '=' in x)
   if props.get('LoadState')!='not-found':
    assert props.get('Description')==desc,'ownership differs, stop refused'
    subprocess.run(['/usr/bin/systemctl','--user','stop',unit],check=True,timeout=3)
   print(json.dumps({'stage':'cleanup','work_empty':not any(P(d).iterdir()),'scope_path_absent':not (P('/sys/fs/cgroup')/props.get('ControlGroup','_absent').lstrip('/')).exists()}),flush=True)
  sys.exit(result.returncode)
