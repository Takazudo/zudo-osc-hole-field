"""Synthetic real-host envelope; no admission, keys, campaign or original inputs.

Only metadata/guard-command providers and small fixture ceilings are substituted.
Actual systemd, pidfd lock custody, namespaces, cgroups, tmpfs, retention and
cleanup use the implementation under test. This is NOT an executable packet.
"""
import fcntl,hashlib,json,os,pathlib,resource,subprocess,sys,tempfile,time,uuid
from unittest.mock import patch
from types import SimpleNamespace
P=pathlib.Path
SOURCE=P('/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-attribution-executor/design/partition/core-split/candidates/planning/joined-feed-construction-v2')
sys.path.insert(0,str(SOURCE))
import attribution_containment as C
import attribution_host as H
import attribution_admission as A
C.ROOT_MEMORY=192*1024**2;C.BOOTSTRAP_MEMORY=32*1024**2;C.CONTROL_MEMORY=64*1024**2;C.RUNTIME_SECONDS=6
H.S.MEMORY_MAX=96*1024**2;H.S.ACTIVE_SCOPE_MEMORY=96*1024**2;H.S.SUPERVISOR_MEMORY=64*1024**2;H.S.WORKER_MEMORY=48*1024**2
C.unit_name=lambda r:'e16-envelope-fixture-'+r['run_id']+'.service'
C.description=lambda r,d:'E16 synthetic envelope '+r['run_id']+' '+d

def data(root):
    run=root.name.removeprefix('e16-envelope-fixture-')
    r={'schema':'e16-attribution-request-v1','run_id':run,'attempt':1,'checkout':str(SOURCE.parents[5]),
       'host_limits':H.HOST_LIMITS,'guard_sha256':hashlib.sha256(P('/home/takazudo/.codex/scripts/heavy-guard.sh').read_bytes()).hexdigest()}
    return r,hashlib.sha256(A.canon(r)).hexdigest()

def configure(root):
    r,digest=data(root);A.state_directory=lambda:root/'fixture-state'
    H.read_small=lambda *args:r
    cmd=['bash','/home/takazudo/.codex/scripts/heavy-guard.sh','--','/usr/bin/python3','-I','-S','-B',__file__,'child',str(root)]
    H.guard_command=lambda *args:cmd
    H.guard_label=lambda *args:' '.join(cmd[3:])
    return r,digest

if len(sys.argv)>1 and sys.argv[1] in ('outer','child','inner','lockworker'):
    role=sys.argv[1];root=P(sys.argv[2]);r,digest=configure(root)
    if role=='outer':
        owner=json.loads((root/'launcher.json').read_text())
        code=C.outer('/fixture/no-request',digest,'/fixture/no-authority','/fixture/no-reservation',owner['pid'],owner['start'])
        raise SystemExit(code)
    if role=='child':
        from numerical_unit_guard import UnitGuard
        guard=UnitGuard(r['guard_sha256']);guard.prove_owner()
        info=(guard.directory/'slot-0.info').read_text();started=int(info.split('started=')[1].split()[0]);mono=time.monotonic()-(time.time()-started)
        mode=(root/'case').read_text()
        if mode=='coverage':
            C.enter(C.own_group().parent/'bootstrap')
        envelope=C.prove(r,digest,mono,mono+180)
        assert C.own_group_for(int(info.split('pid=')[1].split()[0]))==envelope/'control'
        custody=C.receive_guard_custody(r,digest,mono+180)
        guard.prove_owner(inherited_fd=custody)
        lock=root/'.local/state/zudo-e16-attribution/reservation.lock';lock.parent.mkdir(parents=True)
        reservation=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);fcntl.flock(reservation,fcntl.LOCK_EX|fcntl.LOCK_NB)
        os.environ.update(E16_GUARD_FD=str(custody),E16_HOST_CONTROLLER_PID=str(os.getpid()),E16_HOST_LOCK_FD=str(reservation))
        active=C.new_active(envelope,r)
        try:
            cmd=['/usr/bin/unshare','--user','--map-current-user','--keep-caps','--mount','--propagation','private','/usr/bin/python3','-I','-S','-B',__file__,'inner',str(root)]
            raw=H._capture(cmd,time.monotonic()+3,enter_group=active,limit=8192,pass_fds=(custody,reservation))
            (root/'inner.json').write_bytes(raw)
        finally:C.remove_tree(active,time.monotonic()+2)
        A.state_directory().mkdir()
        A.write_new(A.state_directory()/(r['run_id']+'.terminal.json'),A.canon({'fixture_only':True,'no_campaign_accounting':True}))
        print('synthetic mechanism complete',flush=True)
    if role in ('inner','lockworker'):
        from numerical_unit_guard import UnitGuard,prove_inherited_lock
        UnitGuard(r['guard_sha256']).prove_owner(inherited_fd=int(os.environ['E16_GUARD_FD']))
        with patch.object(H.pwd,'getpwuid',return_value=SimpleNamespace(pw_dir=str(root))):H.prove_reservation_owner()
        reopened=os.open(root/'.local/state/zudo-e16-attribution/reservation.lock',os.O_RDONLY)
        try:
            try:prove_inherited_lock(reopened,root/'.local/state/zudo-e16-attribution/reservation.lock')
            except SystemExit:pass
            else:raise AssertionError('reopened unlocked descriptor passed')
        finally:os.close(reopened)
        if role=='lockworker':
            print(json.dumps({'membership':P('/proc/self/cgroup').read_text().strip(),'inherited_guard_and_reservation':True,'reopened_lock_refused':True}));raise SystemExit(0)
    if role=='inner':
        work=root/'work';work.mkdir();parent=C.own_group()
        layout=H.OwnedLayout(parent,work,1024**2,time.monotonic()+3)
        layout.provision();result={'fixture_only':True}
        try:
            probe=subprocess.run(['/usr/bin/git','status','--porcelain'],cwd=r['checkout'],capture_output=True,text=True,timeout=2)
            (root/'git-probe.json').write_text(json.dumps({'returncode':probe.returncode,'stdout':probe.stdout[:8192],'stderr':probe.stderr[:8192]}))
            (work/'tiny').write_bytes(b'x'*4096)
            if (root/'case').read_text()=='failure':
                child=subprocess.Popen(['/usr/bin/python3','-I','-S','-B','-c','import os,time;os.setsid();time.sleep(10)'],preexec_fn=lambda:C.enter(layout.worker))
                (root/'failure-child').write_text(str(child.pid))
                raise RuntimeError('intentional synthetic failure with worker descendant')
            child=subprocess.run(['/usr/bin/python3','-I','-S','-B',__file__,'lockworker',str(root)],capture_output=True,text=True,timeout=1,preexec_fn=lambda:C.enter(layout.worker),pass_fds=(int(os.environ['E16_GUARD_FD']),int(os.environ['E16_HOST_LOCK_FD'])))
            assert child.returncode==0 and str(layout.worker).removeprefix('/sys/fs/cgroup') in child.stdout
            retained=H.retain_tree(work,root/'retained',time.monotonic()+2,aggregate_limit=16384)
            result={'fixture_only':True,'pid':os.getpid(),'scope':str(parent),'worker_membership':child.stdout.strip(),'mount_ns':os.readlink('/proc/self/ns/mnt'),'tmpfs_capacity':os.statvfs(work).f_blocks*os.statvfs(work).f_frsize,'resources':H.resource_snapshot(layout),'retention':retained}
        finally:result['cleanup']=layout.cleanup()
        print(json.dumps(result),flush=True)
else:
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    mode=sys.argv[1] if len(sys.argv)>1 else 'pass'
    assert mode in ('pass','coverage','failure','bootstrap')
    root=P('/tmp')/('e16-envelope-fixture-'+uuid.uuid4().hex);root.mkdir();(root/'case').write_text(mode);r,digest=configure(root)
    pid=os.fork()
    if pid==0:
        owner={'pid':os.getpid(),'start':C.process_start(os.getpid())};(root/'launcher.json').write_text(json.dumps(owner))
        args=H.fixed_arguments('/fixture/no-request',digest,'/fixture/no-authority','/fixture/no-reservation')
        cmd=C.command(r,args,owner['pid'],owner['start']);cmd=cmd[:cmd.index(H.PYTHON)]+['/usr/bin/python3','-I','-S','-B',__file__,'outer',str(root)]
        if mode=='bootstrap':cmd=[x.replace('MemoryMax=201326592','MemoryMax=200278016') for x in cmd]
        (root/'command.json').write_text(json.dumps(cmd));os.execvpe(cmd[0],cmd,A.clean_environment(os.environ))
    _,status=os.waitpid(pid,0);assert status==0
    # Queue time is outside the fixture runtime. Existing guard scheduling is
    # unchanged. Once ACTIVE, kernel6s+stop1 bounds every service descendant.
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        props=C.properties(C.unit_name(r))
        if props['LoadState']=='not-found':break
        time.sleep(.05)
    else:
        # Task-owned exact unit only, never another workload.
        assert C.properties(C.unit_name(r))['Description']==C.description(r,digest)
        subprocess.run(['/usr/bin/systemctl','--user','stop',C.unit_name(r)],check=True,timeout=3)
        raise RuntimeError('fixture observer deadline; retained '+str(root))
    print((root/'git-probe.json').read_text() if (root/'git-probe.json').exists() else 'no git probe')
    receipt=C.receipt_path(r)
    print(json.dumps({'fixture_root':str(root),'command':json.loads((root/'command.json').read_text()),'properties_after':props,'receipt':json.loads(receipt.read_text()) if receipt.exists() else None,'inner':json.loads((root/'inner.json').read_text()) if (root/'inner.json').exists() else None}),flush=True)
    assert receipt.exists(),'missing fixture envelope receipt'
    record=json.loads(receipt.read_text())
    if mode=='pass':
        assert record['status']=='COMPLETE',record
        C.accepted(r,digest,record['shared_guard_receipt_sha256'])
    else:
        assert record['status']=='INCOMPLETE' and (record['cleanup_complete'] or mode=='bootstrap'),record
        try:C.accepted(r,digest,record.get('shared_guard_receipt_sha256'))
        except ValueError:pass
        else:raise AssertionError('negative fixture accepted')
        if (root/'failure-child').exists():
            child=int((root/'failure-child').read_text());assert not P('/proc',str(child)).exists()
            print(json.dumps({'failure_child_reaped':child}),flush=True)
    import shutil
    shutil.rmtree(root)
    print(json.dumps({'fixture_root_removed':not root.exists(),'unit_collected':True,'guard_custody_released':True}),flush=True)
