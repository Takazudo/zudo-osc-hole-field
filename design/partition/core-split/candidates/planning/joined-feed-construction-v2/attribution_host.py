"""E16 fixed Linux host adapter: source-owned provisioning, retention and cleanup.

No import or source test provisions a scope, namespace, mount, authority or key.
The only production entry verifies owner-delegated signed exact authority inside the
unchanged shared guard. Host permission/resource qualification remains separate.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import re
import resource
import selectors
import signal
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
import attribution_supervisor as S
import attribution_containment as C
from numerical_unit_guard import UnitGuard

HERE=Path(__file__).resolve().parent
PYTHON='/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python'
HOST_LOG_MAX=1024**2
HOST_RECEIPTS=256*1024
TAIL_SECONDS=15.
HOST_LIMITS={'total_seconds':180,'total_memory_bytes':S.MEMORY_MAX,'active_scope_memory_bytes':S.ACTIVE_SCOPE_MEMORY,'swap_bytes':0,
             'outer_bytes':S.OUTER_MEMORY,'launcher_bytes':S.LAUNCHER_MEMORY,
             'supervisor_bytes':S.SUPERVISOR_MEMORY,'bootstrap_bytes':S.BOOTSTRAP_MEMORY,
             'controller_filecache_bytes':S.CONTROLLER_FILECACHE,'shared_guard_helper_bytes':S.SHARED_GUARD_MEMORY,
             'outside_swap_contract':C.CONTRACT,'envelope_memory_bytes':C.ROOT_MEMORY,'external_shared_service_reserve_bytes':C.EXTERNAL_RESERVE,
             'envelope_bootstrap_bytes':C.BOOTSTRAP_MEMORY,'envelope_control_bytes':C.CONTROL_MEMORY,
             'envelope_runtime_seconds':C.RUNTIME_SECONDS,'envelope_stop_seconds':C.STOP_SECONDS,
             'envelope_receipt_bytes':C.RECEIPT_MAX,'envelope_log_bytes':C.LOG_MAX,'worker_bytes':S.WORKER_MEMORY,
             'aggregate_output_bytes':S.OUTPUT_MAX,'host_log_bytes':HOST_LOG_MAX,
             'supervisor_log_bytes':S.LOG_RESERVE,'host_receipt_bytes':HOST_RECEIPTS,
             'shared_guard_receipt_bytes':4096,'supervisor_receipt_bytes':S.RECEIPT_RESERVE,'host_tail_seconds':TAIL_SECONDS,
             'supervisor_cleanup_seconds':S.CLEANUP_SECONDS,'tmpfs_retention_copies':2}


def need(ok,message):S.need(ok,message)


def remaining(deadline,reserve=0.):
    value=deadline-time.monotonic()-reserve
    need(value>0,'host deadline exhausted')
    return value


class DeadlineWatchdog:
    """Soft exception reserves cleanup; the second alarm is kernel-default fatal.

    No helper process is added. Blocking Python syscalls are interrupted rather
    than relying only on checkpoints. A hard expiry cannot be swallowed by the
    broad negative-receipt handlers. The shared scope has its own runtime limit.
    """
    def __init__(self,deadline,cleanup_seconds=10.):
        self.deadline=deadline;self.reserve=cleanup_seconds
    def __enter__(self):
        self.old_handler=signal.getsignal(signal.SIGALRM)
        self.old_timer=signal.getitimer(signal.ITIMER_REAL)
        need(self.old_timer==(0.,0.),'inherited process timer refused')
        self.arm(self.deadline)
        return self
    def arm(self,deadline):
        self.deadline=deadline
        signal.signal(signal.SIGALRM,self.soft)
        signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-time.monotonic()-self.reserve))
    def soft(self,number,frame):
        signal.signal(signal.SIGALRM,signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL,max(.001,self.deadline-time.monotonic()))
        raise TimeoutError('host watchdog: work stopped for bounded cleanup')
    def __exit__(self,*args):
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,self.old_handler)


def prove_no_host_swap(text=None):
    text=Path('/proc/meminfo').read_text() if text is None else text
    match=re.search(r'^SwapTotal:\s+(\d+)\s+kB$',text,re.M)
    need(match is not None and int(match.group(1))==0,
         'outside controllers require host SwapTotal=0; no host configuration fallback')


def read_small(path,limit=8*1024**2):
    path=Path(path)
    need(path.is_absolute() and path.resolve()==path,'canonical metadata path required')
    with path.open('rb') as stream:data=stream.read(limit+1)
    need(len(data)<=limit,'metadata size cap')
    return json.loads(data)


def run_name(request):
    need(re.fullmatch('[0-9a-f]{32}',request['run_id']) and request['attempt']==1,'invalid fixed operation identity')
    return 'e16-attribution-'+request['run_id']+'-1.scope'


def fixed_arguments(request_path,digest,authority,reservation):
    need(re.fullmatch('[0-9a-f]{64}',digest),'exact request digest required')
    result=[]
    for key,value in (('--request',request_path),('--digest',digest),('--authority',authority),('--reservation',reservation)):
        result.extend((key,str(value)))
    return result


def worker_command(request_path,digest,authority,reservation):
    return [PYTHON,'-I','-S','-B','-X','pycache_prefix=/dev/null',str(HERE/'attribution_worker.py'),
            *fixed_arguments(request_path,digest,authority,reservation)]


def scope_command(request,args,started):
    """Documented systemd255/util-linux options; no shell/privileged fallback."""
    left=max(.001,started+180-time.monotonic()-7)
    return ['systemd-run','--user','--scope','--quiet','--collect','--no-ask-password',
            '--expand-environment=no','--unit='+run_name(request),
            '--description='+scope_description(request,args[args.index('--digest')+1]),
            '-p','Delegate=memory','-p','MemoryMax='+str(S.MEMORY_MAX),
            '-p','MemorySwapMax=0','-p','OOMPolicy=continue','-p','TasksMax=32',
            '-p',f'RuntimeMaxSec={left:.6f}s','-p','TimeoutStopSec=1s',
            'unshare','--user','--map-current-user','--keep-caps','--mount',
            '--propagation','private',PYTHON,'-I','-S','-B','-X','pycache_prefix=/dev/null',str(HERE/'attribution_host.py'),
            '--contained','--started',repr(started),*args]


def _capture(command,deadline,*,log=None,limit=HOST_LOG_MAX,enter_group=None):
    """Bounded controller command/log transport, killed on first cap/deadline."""
    proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,start_new_session=True,
                          preexec_fn=None if enter_group is None else lambda:C.enter(enter_group))
    selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
    os.set_blocking(proc.stdout.fileno(),False)
    count=0;small=bytearray();failure=None
    try:
        while selector.get_map() or proc.poll() is None:
            remaining(deadline)
            for key,_ in selector.select(min(.02,remaining(deadline))):
                block=os.read(key.fileobj.fileno(),65536)
                if not block:selector.unregister(key.fileobj);continue
                count+=len(block);need(count<=limit,'host log quota exhausted')
                if log is not None:log.write(block);log.flush()
                else:small.extend(block)
        code=proc.wait(timeout=remaining(deadline))
        need(code==0,'host command failed ('+str(code)+'): '+command[0]+': '+bytes(small[-1024:]).decode(errors='replace'))
        return bytes(small)
    except BaseException as exc:
        failure=exc
        raise
    finally:
        if proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:proc.wait(timeout=max(.001,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                if failure is None:raise ValueError('controller command cleanup incomplete')
        selector.close();proc.stdout.close()


class HostOps:
    """Actual OS operations. Tests replace this object, never run native probes."""
    def command(self,command,deadline):return _capture(command,deadline,limit=32768)
    def current_cgroup(self):
        rel=Path('/proc/self/cgroup').read_text().strip().split('::',1)[1]
        return Path('/sys/fs/cgroup')/rel.lstrip('/')
    def write(self,path,value):Path(path).write_text(value)
    def read(self,path):return Path(path).read_text().strip()
    def mkdir(self,path):Path(path).mkdir(exist_ok=False)
    def rmdir(self,path):Path(path).rmdir()
    def exists(self,path):return Path(path).exists()


class OwnedLayout:
    """Only newly created exact children/mount are eligible for cleanup."""
    def __init__(self,parent,work,capacity,deadline,ops=None):
        self.parent,self.work=Path(parent),Path(work)
        self.capacity=capacity;self.deadline=deadline;self.ops=ops or HostOps()
        self.supervisor=self.parent/'supervisor';self.worker=self.parent/'worker'
        self.created=[];self.mounted=False;self.enabled=False;self.moved=False

    def provision(self):
        o=self.ops
        need(o.read(self.parent/'memory.max')==str(S.MEMORY_MAX) and
             o.read(self.parent/'memory.swap.max')=='0','scope kernel limits differ')
        need(o.read(self.parent/'cgroup.procs').split()==[str(os.getpid())],
             'unexpected scope processes; ownership not established')
        need('memory' in o.read(self.parent/'cgroup.controllers').split(),'memory delegation unavailable')
        o.mkdir(self.supervisor);self.created.append(self.supervisor)
        o.write(self.supervisor/'cgroup.procs',str(os.getpid()));self.moved=True
        o.write(self.parent/'cgroup.subtree_control','+memory');self.enabled=True
        o.mkdir(self.worker);self.created.append(self.worker)
        for path,maximum in ((self.supervisor,S.SUPERVISOR_MEMORY),(self.worker,S.WORKER_MEMORY)):
            o.write(path/'memory.max',str(maximum));o.write(path/'memory.swap.max','0')
            need(o.read(path/'memory.max')==str(maximum) and o.read(path/'memory.swap.max')=='0','delegated limits failed')
        need(o.read(self.parent/'cgroup.procs')=='','scope internal process escaped accounting')
        # Hard aggregate bound during all full input validation and numerical
        # work: scoped1344 + outer64 + systemd-run64 + file-cache64 + guard512 =2048MiB.
        # Inside scoped1344: worker1216 + supervisor64 + sticky bootstrap64.
        # The initial2GiB scope is only bounded metadata/bootstrap; tighten it
        # before full validation or worker launch, never rely on after-run peaks.
        o.write(self.parent/'memory.max',str(S.ACTIVE_SCOPE_MEMORY))
        need(o.read(self.parent/'memory.max')==str(S.ACTIVE_SCOPE_MEMORY),'active aggregate scope cap failed')
        o.command(['mount','--no-mtab','--internal-only','-t','tmpfs','-o',
                   f'size={self.capacity},nr_inodes=16384,nosuid,nodev,noexec,mode=0700',
                   'e16-attribution',str(self.work)],self.deadline)
        self.mounted=True

    def cleanup(self):
        o=self.ops;errors=[]
        if self.worker in self.created:
            try:
                if o.exists(self.worker/'cgroup.kill'):o.write(self.worker/'cgroup.kill','1')
                while 'populated 1' in o.read(self.worker/'cgroup.events'):
                    remaining(self.deadline);time.sleep(.005)
            except BaseException as exc:errors.append('worker kill: '+str(exc))
        if self.mounted:
            try:
                o.command(['umount','--no-mtab','--internal-only',str(self.work)],self.deadline)
                self.mounted=False
            except BaseException as exc:errors.append('unmount: '+str(exc))
        # Controller must be disabled before moving the supervisor back into
        # the scope root; cgroup v2 forbids internal tasks with enabled children.
        if self.enabled:
            try:o.write(self.parent/'cgroup.subtree_control','-memory');self.enabled=False
            except BaseException as exc:errors.append('controller release: '+str(exc))
        if self.moved and not self.enabled:
            try:o.write(self.parent/'cgroup.procs',str(os.getpid()));self.moved=False
            except BaseException as exc:errors.append('supervisor release: '+str(exc))
        for path in reversed(self.created):
            try:o.rmdir(path)
            except BaseException as exc:errors.append('cgroup removal: '+str(exc))
        need(not errors,'; '.join(errors))
        self.created=[]
        return {'worker_empty':True,'tmpfs_unmounted':True,'owned_cgroups_removed':True}


def tmpfs_capacity(claim_bytes):
    need(type(claim_bytes) is int and 0<=claim_bytes<HOST_RECEIPTS,'claim output quota')
    available=S.OUTPUT_MAX-HOST_LOG_MAX-S.LOG_RESERVE-HOST_RECEIPTS-S.RECEIPT_RESERVE-claim_bytes
    return (available//2//4096)*4096


def resource_snapshot(layout):
    result={}
    for path in (layout.parent,layout.supervisor,layout.worker):
        values={key:layout.ops.read(path/key) for key in ('memory.max','memory.current','memory.peak',
                'memory.swap.max','memory.swap.current','memory.events','cgroup.events')}
        try:values['memory.swap.peak']=layout.ops.read(path/'memory.swap.peak')
        except OSError:values['memory.swap.peak']='NOT AVAILABLE: kernel does not expose swap.peak'
        need(values['memory.swap.max']=='0' and values['memory.swap.current']=='0','nonzero swap observed')
        events={k:int(v) for k,v in (line.split() for line in values['memory.events'].splitlines())}
        need(events.get('oom',0)==0 and events.get('oom_kill',0)==0,'OOM event observed')
        result[path.name]=values
    return result


class RetentionFailure(ValueError):
    def __init__(self,reason,inventory):
        super().__init__(reason)
        self.inventory=inventory


def retain_tree(source,destination,deadline,*,aggregate_limit,other_bytes=0):
    """Full durable copy plus original charged together; then release originals.

    The mount capacity is at most half the remaining aggregate quota, so even a
    full-copy failure leaves truthful negative evidence below the hard cap.
    No file, row or zero-energy component is omitted to force a successful fit.
    """
    source,destination=Path(source),Path(destination)
    total,files=S._inventory(source,deadline,aggregate_limit-other_bytes)
    need(2*total+other_bytes<=aggregate_limit,'retention aggregate quota exhausted')
    try:
        destination.mkdir(exist_ok=False)
        for name,record in sorted(files.items()):
            remaining(deadline)
            src=source/name;dst=destination/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            h=hashlib.sha256();copied=0
            fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with src.open('rb') as inp,os.fdopen(fd,'wb') as out:
                while True:
                    remaining(deadline);block=inp.read(65536)
                    if not block:break
                    out.write(block);h.update(block);copied+=len(block)
                out.flush();os.fsync(out.fileno())
            need(h.hexdigest()==record['sha256'] and copied==record['bytes'],'retention identity mismatch')
        # Confirm the retained copies before releasing the originals, including all
        # failure-path files. The original mount remains until explicit cleanup.
        retained_total,retained_files=S._inventory(destination,deadline,aggregate_limit-other_bytes)
        need(retained_files==files and retained_total==total,'retained output differs')
        for name in files:(source/name).unlink()
        for base,dirs,_ in os.walk(source,topdown=False):
            for name in dirs:(Path(base)/name).rmdir()
        return {'bytes':total,'files':files,'source_released':True,'retention_complete':True}
    except BaseException as exc:
        raise RetentionFailure(str(exc),{'bytes':total,'files':files,'source_released':False,
            'retention_complete':False,'partial_destination':str(destination)}) from exc


def _host_receipt(root,record,deadline):
    remaining(deadline)
    record.update(electrical_acceptance=False,whole_board_acceptance=False,adopted=False)
    data=S.encoded(record);need(len(data)<=HOST_RECEIPTS//4-4096,'host receipt quota exhausted')
    S._write_new(root/'terminal.pending',data)
    remaining(deadline)
    (root/'terminal.pending').rename(root/'terminal.json')
    if time.monotonic()>=deadline:
        (root/'terminal.json').rename(root/'terminal.late-unaccepted.json')
        raise ValueError('host terminal exceeded deadline')


def _verify(request_path,digest,authority,reservation,deadline,*,metadata_only=False):
    import attribution_admission as admission
    request=admission.verify_for_host(request_path,digest,authority,reservation,deadline=deadline,metadata_only=metadata_only)
    need(request['host_limits']==HOST_LIMITS and request['python']==PYTHON,'unreviewed host operation binding')
    need(Path.cwd()==Path(request['checkout']),'host execution checkout differs')
    return request


def prove_reservation_owner():
    state=Path(pwd.getpwuid(os.getuid()).pw_dir)/'.local/state/zudo-e16-attribution/reservation.lock'
    owner=int(os.environ['E16_HOST_CONTROLLER_PID']);descriptor=int(os.environ['E16_HOST_LOCK_FD'])
    pid=os.getppid()
    while pid>1 and pid!=owner:
        text=Path(f'/proc/{pid}/status').read_text()
        pid=int(re.search(r'^PPid:\s+(\d+)$',text,re.M).group(1))
    need(pid==owner,'exclusive reservation controller is not an ancestor')
    need(os.path.samefile(f'/proc/{owner}/fd/{descriptor}',state),'reservation descriptor identity differs')
    check=os.open(state,os.O_RDWR|os.O_NOFOLLOW)
    try:
        try:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        raise ValueError('exclusive numerical reservation lock is not held')
    finally:os.close(check)


def contained(request_path,digest,authority,reservation,started):
    """Inside the authenticated scope and private user/mount namespace."""
    resource.setrlimit(resource.RLIMIT_AS,(S.BOOTSTRAP_MEMORY,resource.getrlimit(resource.RLIMIT_AS)[1]))
    deadline=started+180
    remaining(deadline)
    import attribution_admission as admission
    admission.check_environment(os.environ)
    metadata=read_small(request_path)
    UnitGuard(metadata['guard_sha256']).prove_owner()
    prove_reservation_owner()
    request=_verify(request_path,digest,authority,reservation,deadline,metadata_only=True)
    need(os.getuid()==os.geteuid()==pwd.getpwnam('takazudo').pw_uid,'namespace changed account identity')
    need(Path('/proc/self/ns/mnt').stat().st_ino!=int(os.environ['E16_PARENT_MOUNT_NS']),
         'private mount namespace missing')
    root=Path(request['output']);staging=root/'staging';staging.mkdir(exist_ok=False)
    work=staging/'.work.partial';work.mkdir()
    claim_bytes=int(os.environ['E16_CLAIM_BYTES'])
    parent=HostOps().current_cgroup()
    need(parent.name==run_name(request),'unexpected owned scope identity')
    layout=OwnedLayout(parent,work,tmpfs_capacity(claim_bytes),deadline-5)
    failure=None;result=None;retained=None;cleanup=None;resources=None
    try:
        layout.provision()
        request=_verify(request_path,digest,authority,reservation,deadline)
        # The enclosing cgroup now bounds resident memory. The outer Python and
        # systemd-run retain their 64MiB address-space ceilings independently.
        resource.setrlimit(resource.RLIMIT_AS,(resource.RLIM_INFINITY,resource.RLIM_INFINITY))
        os.environ['E16_CGROUP_PARENT']=str(parent)
        os.environ['E16_CGROUP_WORKER']=str(layout.worker)
        os.environ['E16_GUARD_ENTRY_AT']=repr(started)
        contain=S.LinuxContainment(parent,layout.worker,work,request['guard_sha256'])
        result=S.supervise(worker_command(request_path,digest,authority,reservation),staging,
            started=started,containment=contain,tail_reserve_seconds=TAIL_SECONDS,
            prior_output_bytes=claim_bytes+HOST_LOG_MAX+HOST_RECEIPTS)
        resources=resource_snapshot(layout)
        need(int(resources[parent.name]['memory.peak'])+S.OUTER_MEMORY+S.LAUNCHER_MEMORY+S.CONTROLLER_FILECACHE+S.SHARED_GUARD_MEMORY<=S.MEMORY_MAX,
             'observed aggregate parent/controller memory bound exceeded')
        # Internal supervisor evidence is not the complete host receipt.
        (staging/'terminal.json').rename(staging/'supervisor.unaccepted.json')
        retained=retain_tree(work,root/'retained',deadline-7,aggregate_limit=S.OUTPUT_MAX,
                             other_bytes=claim_bytes+HOST_LOG_MAX+S.LOG_RESERVE+HOST_RECEIPTS+S.RECEIPT_RESERVE)
        need(result['status']=='COMPLETE','numerical worker/supervisor incomplete')
    except BaseException as exc:
        failure=str(exc)[:2048]
        if isinstance(exc,RetentionFailure):retained=exc.inventory
        # Retain full negative output if it still fits the same preallocated
        # two-copy reserve. Never retry the numerical operation.
        if retained is None and layout.mounted and not (root/'retained').exists():
            try:
                retained=retain_tree(work,root/'retained',deadline-7,aggregate_limit=S.OUTPUT_MAX,
                    other_bytes=claim_bytes+HOST_LOG_MAX+S.LOG_RESERVE+HOST_RECEIPTS+S.RECEIPT_RESERVE)
            except BaseException as retention_error:
                failure+='; retention: '+str(retention_error)[:512]
                if isinstance(retention_error,RetentionFailure):retained=retention_error.inventory
    finally:
        try:
            # Reserve remains strict even while leaving the supervisor subgroup.
            resource.setrlimit(resource.RLIMIT_AS,(S.SUPERVISOR_MEMORY,resource.RLIM_INFINITY))
            if layout.mounted and retained is not None and not retained.get('retention_complete'):
                retained['negative_artifact_loss_after_cleanup']=True
            cleanup=layout.cleanup()
        except BaseException as exc:failure=(failure or '')+'; cleanup: '+str(exc)[:1024]
    try:
        _,host_files=S._inventory(root,deadline-4,S.OUTPUT_MAX-claim_bytes-HOST_RECEIPTS)
        final_parent={key:HostOps().read(parent/key) for key in
                     ('memory.max','memory.current','memory.peak','memory.swap.max','memory.swap.current','memory.events')}
        if resources is None:resources={}
        resources['parent_after_cleanup_and_retention']=final_parent
        allowance=S.ACTIVE_SCOPE_MEMORY
        need(int(final_parent['memory.peak'])<=allowance and
             int(final_parent['memory.current'])+HOST_RECEIPTS<=allowance,'final aggregate memory bound exceeded')
        need(final_parent['memory.swap.max']==final_parent['memory.swap.current']=='0','final swap observed')
    except BaseException as exc:
        host_files={};failure=(failure or '')+'; contained final inventory: '+str(exc)[:1024]
    data={'schema':'e16-host-contained-v1','status':'INCOMPLETE' if failure else 'COMPLETE',
          'request_sha256':digest,'reason':failure,'supervisor':result,
          'retention':retained,'cleanup':cleanup,'resources':resources,'scope':str(parent),
          'elapsed_seconds':time.monotonic()-started,'host_files':host_files}
    raw=S.encoded(data);need(len(raw)<=HOST_RECEIPTS*3//8,'contained receipt exceeds reserve')
    remaining(deadline-3);S._write_new(root/'contained.unaccepted.json',raw)
    return 1 if failure else 0


def scope_description(request,digest):
    need(re.fullmatch('[0-9a-f]{64}',digest),'scope request digest required')
    return 'E16 attribution '+request['run_id']+' request '+digest


def _scope_state(unit,deadline):
    raw=_capture(['systemctl','--user','show',unit,
                  '--property=LoadState,ActiveState,ControlGroup,Description'],deadline,limit=8192)
    return dict(line.split('=',1) for line in raw.decode().splitlines() if '=' in line)


def _fresh_scope(unit,deadline):
    need(_scope_state(unit,deadline).get('LoadState')=='not-found',
         'scope identity already exists; never adopt or kill it')


def _scope_cleanup(unit,deadline,owner_description=None):
    """Stop only the fresh exact request-tagged unit, never a same-name stranger."""
    try:values=_scope_state(unit,deadline)
    except ValueError:raise ValueError('cannot establish owned scope state')
    if values.get('LoadState')=='not-found':return {'unit':unit,'collected':True}
    need(owner_description is not None and values.get('Description')==owner_description,
         'scope ownership description differs; cleanup refused')
    cg=values.get('ControlGroup','')
    if cg:
        path=Path('/sys/fs/cgroup')/cg.lstrip('/')
        need(path.name==unit,'scope cleanup identity differs')
        if path.exists() and (path/'cgroup.kill').exists():(path/'cgroup.kill').write_text('1')
    _capture(['systemctl','--user','stop',unit],deadline,limit=8192)
    while cg and path.exists():
        remaining(deadline);time.sleep(.01)
    return {'unit':unit,'collected':True}


def _guard_entry(request_path,digest,authority,reservation,watchdog):
    resource.setrlimit(resource.RLIMIT_AS,(S.OUTER_MEMORY,resource.getrlimit(resource.RLIMIT_AS)[1]))
    started=time.monotonic()  # Before authority/claims/provisioning or any decode.
    deadline=started+180
    import attribution_admission as admission
    admission.check_environment(os.environ)
    metadata=read_small(request_path)
    guard=UnitGuard(metadata['guard_sha256']);guard.prove_owner()
    # No host swap setting is changed. The alternative must prove complete
    # operation-owned containment before the old refusal can be bypassed.
    # The shared owner timestamps guard entry before spawning its command.
    # Its seconds-resolution timestamp is a conservative earlier bound; it is
    # never reset to the worker's or this Python process's launch time.
    info=(guard.directory/'slot-0.info').read_text()
    match=re.search(r'\bstarted=(\d+)\b',info);need(match is not None,'shared guard entry timestamp absent')
    elapsed=time.time()-int(match.group(1));need(0<=elapsed<180,'stale shared guard entry')
    started-=elapsed;deadline=started+180
    watchdog.arm(deadline)
    try:envelope=C.prove(metadata,digest,started,deadline)
    except (ValueError,OSError,KeyError):
        prove_no_host_swap()  # Retain the old host refusal on incomplete proof.
        raise
    request=_verify(request_path,digest,authority,reservation,deadline,metadata_only=True)
    state=Path(pwd.getpwuid(os.getuid()).pw_dir)/'.local/state/zudo-e16-attribution'
    state.mkdir(parents=True,exist_ok=True)
    need(state.resolve()==state,'reservation state symlink refused')
    fd=os.open(state/'reservation.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        import attribution_admission as admission
        need(not (envelope/run_name(request)).exists(),
             "active cgroup already exists; never adopt it")
        claim_path,claim_bytes=admission.claim(request,digest,deadline)
        root=Path(request['output']);need(root.is_absolute() and root.resolve()==root,'canonical retained output required')
        root.mkdir(exist_ok=False)
        failure=None;cleanup=None;inside=None
        old_limit=resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS,(S.OUTER_MEMORY,old_limit[1]))
        os.environ['E16_PARENT_MOUNT_NS']=str(Path('/proc/self/ns/mnt').stat().st_ino)
        os.environ['E16_CLAIM_BYTES']=str(claim_bytes);os.environ['E16_CLAIM_PATH']=str(claim_path)
        os.environ['E16_HOST_CONTROLLER_PID']=str(os.getpid());os.environ['E16_HOST_LOCK_FD']=str(fd)
        args=fixed_arguments(request_path,digest,authority,reservation)
        try:
            with (root/'host.log.partial').open('xb') as log:
                active=C.new_active(envelope,request)
                cmd=['/usr/bin/unshare','--user','--map-current-user','--keep-caps','--mount',
                     '--propagation','private',PYTHON,'-I','-S','-B','-X','pycache_prefix=/dev/null',
                     str(HERE/'attribution_host.py'),'--contained','--started',repr(started),*args]
                _capture(cmd,deadline-8,log=log,enter_group=active)
                log.flush();os.fsync(log.fileno())
            inside=read_small(root/'contained.unaccepted.json',HOST_RECEIPTS*3//8)
            need(inside['request_sha256']==digest and inside['status']=='COMPLETE','contained operation incomplete')
        except BaseException as exc:failure=str(exc)[:2048]
        finally:
            try:
                C.remove_tree(envelope/run_name(request),deadline-3)
                cleanup={'unit':run_name(request),'collected':True}
            except BaseException as exc:failure=(failure or '')+'; scope cleanup: '+str(exc)[:1024]
        try:
            inside=read_small(root/'contained.unaccepted.json',HOST_RECEIPTS*3//8)
            need(inside['request_sha256']==digest,'contained receipt binding differs')
            files=dict(inside['host_files'])
            for name,cap in (('host.log.partial',HOST_LOG_MAX),('contained.unaccepted.json',HOST_RECEIPTS*3//8)):
                path=root/name
                need(path.stat().st_size<=cap,'controller file exceeded cap')
                with path.open('rb') as stream:h=hashlib.file_digest(stream,'sha256').hexdigest()
                files[name]={'bytes':path.stat().st_size,'sha256':h}
            actual_names=set()
            for base,dirs,names in os.walk(root):
                for name in dirs:need(not (Path(base)/name).is_symlink(),'output symlink appeared')
                for name in names:
                    path=Path(base)/name
                    need(path.is_file() and not path.is_symlink(),'nonregular output appeared')
                    actual_names.add(str(path.relative_to(root)))
            need(actual_names==set(files),'output set changed after scoped hash pass')
            size=sum(x['bytes'] for x in files.values())
            need(size+claim_bytes+HOST_RECEIPTS<=S.OUTPUT_MAX,'aggregate final output quota')
        except BaseException as exc:
            size=None;files={};failure=(failure or '')+'; final inventory: '+str(exc)[:1024]
        result={'schema':'e16-attribution-host-terminal-v1','status':'INCOMPLETE' if failure else 'PENDING_SHARED_GUARD',
                'request_sha256':digest,'run_id':request['run_id'],'reason':failure,
                'request_kind':request['request_kind'],'qualification_only':request['request_kind']=='resource-qualification',
                'authority_path':str(Path(authority).resolve()),'reservation_path':str(Path(reservation).resolve()),
                'claim_path':str(claim_path),'claim_bytes':claim_bytes,'scope_cleanup':cleanup,
                'contained_receipt_sha256':files.get('contained.unaccepted.json',{}).get('sha256'),
                'retained_bytes':size,'files':files,'elapsed_seconds':time.monotonic()-started,
                'cleanup_complete':bool(cleanup and cleanup.get('collected')),'shared_guard_verdict_required':True,'guard_started_unix':int(match.group(1)),
                'guard_label':guard_label(request_path,digest,authority,reservation,request['guard_sha256']),
                'guard_cwd':str(Path.cwd())}
        try:
            extra=admission.finish_accounting(request,digest,result,deadline)
            result['accounting_output_bytes']=claim_bytes+extra
            need(claim_bytes+extra<65536,'aggregate accounting reserve exceeded')
            result['claim_sha256']=admission.sha(claim_path,deadline)
        except BaseException as exc:
            failure=(failure or '')+'; terminal accounting: '+str(exc)[:1024]
            result.update(status='INCOMPLETE',reason=failure)
        _host_receipt(root,result,deadline)
        return 1 if failure else 0
    finally:
        os.close(fd)


def guard_entry(request_path,digest,authority,reservation):
    with DeadlineWatchdog(time.monotonic()+180) as watchdog:
        return _guard_entry(request_path,digest,authority,reservation,watchdog)


def guard_command(request_path,digest,authority,reservation,guard_sha256):
    guard=UnitGuard(guard_sha256);guard.check()
    helper=HERE/'numerical_unit_guard.py'
    flags=['-I','-S','-B','-X','pycache_prefix=/dev/null']
    return ['bash',str(guard.path),'--',PYTHON,*flags,str(helper),'--inside',guard_sha256,'--',
            PYTHON,*flags,str(HERE/'attribution_host.py'),'--guard-entry',
            *fixed_arguments(request_path,digest,authority,reservation)]


def guard_label(request_path,digest,authority,reservation,guard_sha256):
    # Pure derivation mirrors guard_command without requiring a live guard at
    # read-only result inspection time. -B alone would still load stale .pyc.
    helper=HERE/'numerical_unit_guard.py'
    flags=['-I','-S','-B','-X','pycache_prefix=/dev/null']
    command=[PYTHON,*flags,str(helper),'--inside',guard_sha256,'--',PYTHON,*flags,
             str(HERE/'attribution_host.py'),'--guard-entry',
             *fixed_arguments(request_path,digest,authority,reservation)]
    value=' '.join(command)
    need(len(value.encode())<=3000,'shared guard label exceeds receipt reserve')
    return value


def accepted_result(request_path,digest):
    """Read-only acceptance from TWO durable receipts, never a new approval.

    The unchanged shared guard appends its runs.jsonl while fd200 is still held.
    Host output remains PENDING_SHARED_GUARD until that exact unique scheduler
    record is present and passes. No post-guard output mutation is necessary.
    """
    request=read_small(request_path)
    need(hashlib.sha256(S.encoded(request)).hexdigest()==digest,'request digest changed')
    receipt=read_small(Path(request['output'])/'terminal.json',HOST_RECEIPTS)
    need(receipt.get('status')=='PENDING_SHARED_GUARD' and receipt['request_sha256']==digest and
         receipt['run_id']==request['run_id'] and receipt['request_kind']==request['request_kind'],
         'host operation incomplete/unaccepted')
    need(receipt.get('cleanup_complete') is True and all(receipt.get(k) is False for k in
         ('electrical_acceptance','whole_board_acceptance','adopted')),'host acceptance/cleanup flags changed')
    import attribution_admission as admission
    admission.verify_policy(request)
    prefix='e16-attribution' if request['request_kind']=='production-attribution' else 'e16-attribution-qualification'
    need(receipt['guard_cwd']==request['checkout'],'guard checkout binding changed')
    need(receipt['guard_label']==guard_label(request_path,digest,receipt['authority_path'],
         receipt['reservation_path'],request['guard_sha256']),'guard command binding changed')
    grants=[]
    for key,kind,identity in (('authority_path','authorization','e16-operator'),('reservation_path','reservation','e16-controller')):
        grant=admission.verify_signature(Path(receipt[key]),prefix+'-'+kind+'-v1',identity,request['trust_sha256'])
        admission.verify_policy(grant)
        need(grant['request_sha256']==digest and grant['run_id']==request['run_id'] and
             grant['request_kind']==request['request_kind'] and grant['operation']==request['operation'] and
             S.encoded(grant['limits'])==S.encoded(request['limits']),'guard grant binding differs')
        need(all(type(grant[k]) in (int,float) and math.isfinite(grant[k]) for k in ('issued_unix','expires_unix')),
             'invalid historical grant times')
        grants.append(grant)
    need(grants[0]['approved'] is True and grants[1]['exclusive'] is True,'guard authority/reservation absent')
    ledger=Path(pwd.getpwuid(os.getuid()).pw_dir)/'.agent-guard/heavy/runs.jsonl'
    matches=[]
    with ledger.open('rb') as stream:
        for line in stream:
            need(len(line)<=16384,'oversized shared guard receipt')
            try:row=json.loads(line)
            except ValueError:continue
            if row.get('label')==receipt['guard_label'] and row.get('cwd')==receipt['guard_cwd']:
                matches.append((row,hashlib.sha256(line).hexdigest()))
    need(len(matches)==1,'missing/ambiguous exact durable guard receipt')
    row,row_hash=matches[0]
    need(row.get('verdict')=='PASS' and row.get('exit')==0 and type(row.get('min_mem_mb')) is int,
         'shared guard did not establish PASS')
    need(type(row.get('secs')) is int and 0<=row['secs']<=180 and
         receipt['guard_started_unix']<=row['ts']<=receipt['guard_started_unix']+180,
         'shared guard interval exceeds exact operation')
    need(all(g['issued_unix']<=receipt['guard_started_unix']+1 and g['expires_unix']>=row['ts'] for g in grants),
         'grants did not cover actual guarded interval')
    terminal_journal=admission.read_json(admission.state_directory()/(request['run_id']+'.terminal.json'))
    need(terminal_journal['request_sha256']==digest and terminal_journal['run_id']==request['run_id'] and
         terminal_journal['request_kind']==request['request_kind'] and
         terminal_journal['terminal_status']==receipt['status'] and terminal_journal['cleanup_complete'] is True and
         terminal_journal['output_manifest_sha256']==hashlib.sha256(S.encoded(receipt['files'])).hexdigest(),
         'immutable terminal journal/output binding differs')
    claim=admission.state_directory()/(request['run_id']+'.json')
    need(Path(receipt['claim_path'])==claim and admission.read_json(claim)['request_sha256']==digest,
         'consumed claim belongs to another operation')
    # Revalidate retained outputs and the immutable claim before deriving
    # acceptance. A matching scheduler row cannot bless edited result files.
    actual_total,actual_files=S._inventory(Path(request['output']),time.monotonic()+30,S.OUTPUT_MAX)
    actual_files.pop('terminal.json',None)
    need(actual_files==receipt['files'],'retained host output changed')
    with Path(receipt['claim_path']).open('rb') as stream:
        need(hashlib.file_digest(stream,'sha256').hexdigest()==receipt['claim_sha256'],'consumed claim changed')
    need(actual_total+receipt.get('accounting_output_bytes',receipt['claim_bytes'])+4096<=S.OUTPUT_MAX,
         'aggregate final output quota exceeded')
    # Complete means the contained operation reconciled and owned resources
    # were removed before the host receipt; acceptance flags remain false.
    need(receipt['scope_cleanup']['collected'] is True,'owned scope cleanup incomplete')
    envelope=C.accepted(request,digest,row_hash)
    need(actual_total+receipt.get('accounting_output_bytes',receipt['claim_bytes'])+4096+
         C.receipt_path(request).stat().st_size<=S.OUTPUT_MAX,'aggregate envelope output quota exceeded')
    need(all(g['expires_unix']>=envelope['terminal_unix'] for g in grants),
         'grants did not cover complete envelope tail')
    return dict(receipt,status='COMPLETE',envelope=envelope,shared_guard_receipt_sha256=row_hash,
                shared_guard_ledger=str(ledger),shared_guard=row)


def launch(request_path,digest,authority,reservation):
    """Queue only the fixed source-owned operation; never prepares approval."""
    resource.setrlimit(resource.RLIMIT_AS,(S.OUTER_MEMORY,resource.getrlimit(resource.RLIMIT_AS)[1]))
    request=read_small(request_path)
    need(request.get('schema')=='e16-attribution-request-v1' and request.get('request_kind') in
         ('production-attribution','resource-qualification') and not request.get('fixture_only') and
         not any(k in request.get('packet',{}) for k in ('fixture_only','fixture_removed')),
         'production host refuses fixture/inapplicable request')
    need(request['python']==PYTHON,'fixed numerical Python required')
    run_name(request)
    import attribution_admission as admission
    clean_env=admission.clean_environment(os.environ,inside=False)
    command=guard_command(request_path,digest,authority,reservation,request['guard_sha256'])
    guard_label(request_path,digest,authority,reservation,request['guard_sha256'])
    # Exec, rather than keeping another Python controller resident throughout
    # the operation. Queueing remains outside the numerical deadline. The
    # unchanged shared scheduler writes its own durable bounded receipt.
    checkout=Path(request['checkout'])
    need(checkout.is_absolute() and checkout.resolve()==checkout and checkout.is_dir(),'canonical checkout required')
    os.chdir(checkout)
    need(request['host_limits']==HOST_LIMITS,'sealed containment contract differs')
    args=fixed_arguments(request_path,digest,authority,reservation)
    unit=C.unit_name(request)
    need(C.properties(unit).get('LoadState')=='not-found','envelope unit already exists')
    command=C.command(request,args,os.getpid(),C.process_start(os.getpid()))
    os.execvpe(command[0],command,clean_env)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--launch',action='store_true');mode.add_argument('--guard-entry',action='store_true');mode.add_argument('--contained',action='store_true');mode.add_argument('--envelope',action='store_true')
    for name in ('request','digest','authority','reservation'):p.add_argument('--'+name,required=True)
    p.add_argument('--started',type=float)
    p.add_argument('--launcher-pid',type=int);p.add_argument('--launcher-start')
    a=p.parse_args();args=(a.request,a.digest,a.authority,a.reservation)
    if a.envelope:return C.outer(*args,a.launcher_pid,a.launcher_start)
    if a.launch:return launch(*args)
    if a.guard_entry:return guard_entry(*args)
    need(a.started is not None and math.isfinite(a.started),'guard-entry timestamp required')
    return contained(*args,a.started)


if __name__=='__main__':raise SystemExit(main())
