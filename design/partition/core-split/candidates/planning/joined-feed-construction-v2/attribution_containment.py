"""Task-local E16 notify-service envelope; no numerical or authority creation.

The account manager creates the service before exec. A fresh anonymous address
space and every admitted descendant stay under its hard memory/no-swap boundary.
Shared-manager and pre-exec file/kernel costs are a separate conservative reserve,
not charges purportedly transferred by migration. Qualification must include them.
"""
import base64
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT_MEMORY=1984*1024**2
CONTROL_MEMORY=576*1024**2
BOOTSTRAP_MEMORY=64*1024**2
EXTERNAL_RESERVE=64*1024**2
RUNTIME_SECONDS=174
STOP_SECONDS=1
LOG_MAX=4096
RECEIPT_MAX=16384
CONTRACT='task-local-notify-v1'


def need(ok,message):
    if not ok:raise ValueError(message)


def own_group():
    return Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')


def unit_name(request):
    need(re.fullmatch('[0-9a-f]{32}',request['run_id']) is not None,'invalid envelope run identity')
    return 'e16-attribution-envelope-'+request['run_id']+'.service'


def lock_custody(child,lock):
    """Duplicate the guard's actual open-file description, never reopen/relock.

    The same flock remains held until this wrapper exits after terminal work.
    Linux pidfd_getfd requires current ptrace access to our direct child. Refusal
    is fatal before readiness/claim; no privilege or alternate-lock fallback.
    """
    need(os.uname().machine=='x86_64','unreviewed pidfd syscall ABI')
    lib=ctypes.CDLL(None,use_errno=True);lib.syscall.restype=ctypes.c_long
    pidfd=os.pidfd_open(child,0)
    try:
        fd=lib.syscall(438,pidfd,200,0);error=ctypes.get_errno()
    finally:os.close(pidfd)
    if fd<0:
        raise OSError(error,os.strerror(error),'pidfd_getfd guard fd200')
    try:
        need(os.path.samefile(f'/proc/self/fd/{fd}',lock),'guard custody descriptor differs')
        os.dup2(fd,201,inheritable=False)
    finally:
        if fd!=201:os.close(fd)
    # Kept until process exit, not closed after guard PASS or receipt write.
    return 201


def process_start(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    except FileNotFoundError:return None


def duration_text(seconds):
    return (str(seconds//60)+'min ' if seconds>=60 else '')+str(seconds%60)+'s'


def properties(unit):
    names='LoadState,ActiveState,ControlGroup,Description,MainPID,Type,NotifyAccess,RuntimeMaxUSec,TimeoutStopUSec,ActiveEnterTimestampMonotonic,KillMode,SendSIGKILL,Restart'
    r=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property='+names],
        capture_output=True,text=True,timeout=2)
    need(r.returncode==0 and len(r.stdout)<8192,'cannot prove envelope unit properties')
    return dict(x.split('=',1) for x in r.stdout.splitlines() if '=' in x)


def description(request,digest):return 'E16 envelope '+request['run_id']+' request '+digest


def command(request,args,launcher_pid,launcher_start):
    import attribution_host as H
    digest=args[args.index('--digest')+1]
    import attribution_admission as A
    env=A.clean_environment(os.environ,inside=False)
    return ['/usr/bin/systemd-run','--user','--quiet','--no-block','--collect','--no-ask-password',
        '--expand-environment=no','--service-type=notify','--unit='+unit_name(request),
        '--description='+description(request,digest),
        *['--setenv='+key+'='+value for key,value in sorted(env.items())],
        '-p','UnsetEnvironment=LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT LD_DEBUG LD_DEBUG_OUTPUT LD_DYNAMIC_WEAK LD_BIND_NOW LD_BIND_NOT LD_HWCAP_MASK LD_ORIGIN_PATH LD_PROFILE LD_PROFILE_OUTPUT LD_SHOW_AUXV LD_TRACE_LOADED_OBJECTS LD_VERBOSE LD_WARN LD_ASSUME_KERNEL LD_POINTER_GUARD LD_PREFER_MAP_32BIT_EXEC LD_TRACE_PRELINKING LD_USE_LOAD_BIAS GLIBC_TUNABLES GCONV_PATH LOCPATH PYTHONHOME PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE PYTHONINSPECT',
        '-p','NotifyAccess=main','-p','Delegate=memory pids','-p','DelegateSubgroup=bootstrap',
        '-p','MemoryMax='+str(ROOT_MEMORY),'-p','MemorySwapMax=0','-p','TasksMax=48',
        '-p','LimitAS=67108864:infinity','-p','LimitCORE=0','-p','Restart=no',
        '-p','KillMode=control-group','-p','SendSIGKILL=yes',
        '-p','TimeoutStartSec=15s','-p','RuntimeMaxSec='+str(RUNTIME_SECONDS)+'s',
        '-p','TimeoutStopSec='+str(STOP_SECONDS)+'s',
        '-p','StandardOutput=null','-p','StandardError=null',
        '-p','WorkingDirectory='+request['checkout'],
        H.PYTHON,'-I','-S','-B','-X','pycache_prefix=/dev/null',str(HERE/'attribution_host.py'),
        '--envelope','--launcher-pid',str(launcher_pid),'--launcher-start',launcher_start,*args]


def verify_root(root,request):
    need(root.name==unit_name(request) and root.resolve()==root,'envelope cgroup identity differs')
    need((root/'memory.max').read_text().strip()==str(ROOT_MEMORY) and
         (root/'memory.swap.max').read_text().strip()=='0' and
         (root/'pids.max').read_text().strip()=='48','envelope hard limits absent')
    need((root/'memory.swap.current').read_text().strip()=='0','envelope swap observed')


def setup(root,request):
    verify_root(root,request)
    need(own_group()==root/'bootstrap','service bootstrap placement differs')
    need((root/'cgroup.procs').read_text().strip()=='' and
         (root/'bootstrap/cgroup.procs').read_text().split()==[str(os.getpid())],
         'unexpected bootstrap processes')
    need({p.name for p in root.iterdir() if p.is_dir()}=={'bootstrap'},'preexisting envelope children')
    (root/'cgroup.subtree_control').write_text('+memory +pids')
    for path,cap,tasks in ((root/'bootstrap',BOOTSTRAP_MEMORY,4),(root/'control',CONTROL_MEMORY,16)):
        if path.name=='control':path.mkdir()
        (path/'memory.max').write_text(str(cap));(path/'memory.swap.max').write_text('0')
        (path/'pids.max').write_text(str(tasks))
    return root/'control'


def enter(path):
    (path/'cgroup.procs').write_text(str(os.getpid()))
    need(own_group()==path,'child containment placement failed')


def prove(request,digest,started,deadline):
    """Before claim: actual placement and manager deadline, not env assertions."""
    import attribution_host as H
    own=own_group();root=own.parent
    need(own.name=='control','outer controller escaped envelope')
    verify_root(root,request)
    need((own/'memory.max').read_text().strip()==str(CONTROL_MEMORY) and
         (own/'memory.swap.max').read_text().strip()=='0','control limits absent')
    p=properties(unit_name(request))
    # Wait only for the main wrapper's notification. No work/claim before ACTIVE.
    while p.get('ActiveState')=='activating' and time.monotonic()<min(deadline,started+4):
        time.sleep(.02);p=properties(unit_name(request))
    need(p.get('ActiveState')=='active' and p.get('Description')==description(request,digest) and
         Path('/sys/fs/cgroup')/p['ControlGroup'].lstrip('/')==root,'unowned/inactive envelope')
    need(p.get('Type')=='notify' and p.get('NotifyAccess')=='main' and
         p.get('RuntimeMaxUSec')==duration_text(RUNTIME_SECONDS) and
         p.get('TimeoutStopUSec')=='1s' and p.get('KillMode')=='control-group' and
         p.get('SendSIGKILL')=='yes' and p.get('Restart')=='no','envelope termination contract differs')
    active=int(p['ActiveEnterTimestampMonotonic'])/1e6
    need(started<=active and active+RUNTIME_SECONDS+STOP_SECONDS<=started+180,
         'envelope manager deadline exceeds original guard interval')
    wrapper=int(p['MainPID'])
    need(own_group_for(wrapper)==root/'bootstrap','envelope main process escaped')
    import attribution_admission as A
    need(os.path.samefile(f'/proc/{wrapper}/fd/201',A.account_home()/'.agent-guard/heavy/slot-0.lock'),
         'envelope shared-slot custody absent')
    return root


def own_group_for(pid):
    return Path('/sys/fs/cgroup')/Path(f'/proc/{pid}/cgroup').read_text().strip().split('::',1)[1].lstrip('/')


def new_active(root,request):
    import attribution_host as H
    path=root/H.run_name(request)
    path.mkdir()  # Never adopt another operation's child.
    (path/'memory.max').write_text(str(H.S.MEMORY_MAX))
    (path/'memory.swap.max').write_text('0');(path/'pids.max').write_text('32')
    return path


def remove_tree(path,deadline):
    """Only a caller-proved task-owned subtree; kill migrated tasks too."""
    if not path.exists():return
    (path/'cgroup.kill').write_text('1')
    while 'populated 1' in (path/'cgroup.events').read_text():
        need(time.monotonic()<deadline,'envelope child cleanup timed out');time.sleep(.01)
    for child in sorted(path.iterdir()):
        if child.is_dir():remove_tree(child,deadline)
    path.rmdir()


def snapshot(root):
    return {k:(root/k).read_text().strip() for k in
        ('memory.max','memory.current','memory.peak','memory.swap.max','memory.swap.current','memory.events','pids.max')}


def notify(address,text):
    with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:
        sock.settimeout(1)
        sock.connect('\0'+address[1:] if address.startswith('@') else address)
        sock.sendall(text.encode())


def receipt_path(request):
    import attribution_admission as A
    return A.state_directory()/(request['run_id']+'.envelope.json')


def guard_row(request,label,started,deadline):
    import attribution_admission as A
    path=A.account_home()/'.agent-guard/heavy/runs.jsonl';matches=[]
    with path.open('rb') as f:
        while True:
            need(time.monotonic()<deadline,'guard receipt verification deadline')
            line=f.readline(16385)
            if not line:break
            need(len(line)<=16384,'shared guard historical row exceeds parser cap')
            try:row=json.loads(line)
            except ValueError:continue
            if row.get('label')==label and row.get('cwd')==request['checkout'] and row.get('ts',0)>=started:
                need(len(line)<=4096,'selected guard receipt exceeds reserve')
                matches.append((row,hashlib.sha256(line).hexdigest()))
    need(len(matches)==1,'missing/ambiguous envelope shared guard receipt')
    row,digest=matches[0]
    need(row['verdict']=='PASS' and row['exit']==0 and row['min_mem_mb'] is not None and
         row['ts']<=started+180,'envelope shared guard receipt failed/late')
    return digest


def _outer(request_path,digest,authority,reservation,launcher_pid,launcher_start):
    import attribution_admission as A
    import attribution_host as H
    from numerical_unit_guard import UnitGuard
    request=H.read_small(request_path)
    need(request.get('schema')=='e16-attribution-request-v1' and not request.get('fixture_only'),
         'envelope refuses fixture/inapplicable request')
    need(request['host_limits']==H.HOST_LIMITS and hashlib.sha256(A.canon(request)).hexdigest()==digest,
         'envelope request/contract differs')
    need(not receipt_path(request).exists(),'envelope identity already consumed; no retry')
    # Reap orphan guard utilities after killing their actual cgroup.
    lib=ctypes.CDLL(None,use_errno=True)
    need(lib.prctl(36,1,0,0,0)==0,'child subreaper unavailable')
    root=own_group().parent;control=setup(root,request)
    address=os.environ['NOTIFY_SOCKET']
    until=time.monotonic()+5
    while process_start(launcher_pid)==launcher_start:
        need(time.monotonic()<until,'initial launcher did not exit before guard');time.sleep(.01)
    clean=A.clean_environment(os.environ,inside=False)  # strips notify/service credentials
    guard=UnitGuard(request['guard_sha256']);guard.check()
    command=H.guard_command(request_path,digest,authority,reservation,request['guard_sha256'])
    label=H.guard_label(request_path,digest,authority,reservation,request['guard_sha256'])
    proc=None;started=None;mono=None;failure=None;log=bytearray();row_sha=None;cleanup=False;guard_start=None
    selector=selectors.DefaultSelector();next_extend=0
    try:
        proc=subprocess.Popen(command,env=clean,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=lambda:enter(control))
        guard_start=process_start(proc.pid)
        os.set_blocking(proc.stdout.fileno(),False);selector.register(proc.stdout,selectors.EVENT_READ)
        while proc.poll() is None or selector.get_map():
            now=time.monotonic()
            if started is None:
                try:info=(guard.directory/'slot-0.info').read_text()
                except FileNotFoundError:info=''
                match=re.match(r'pid=(\d+) started=(\d+) cwd=',info)
                if match and int(match[1])==proc.pid:
                    started=int(match[2]);elapsed=time.time()-started
                    need(0<=elapsed<=4,'guard notification latency exceeded')
                    mono=now-elapsed
                    need(process_start(proc.pid)==guard_start,'guard child identity changed')
                    lock_custody(proc.pid,guard.directory/'slot-0.lock')
                    notify(address,'READY=1')
                elif now>=next_extend:
                    notify(address,'EXTEND_TIMEOUT_USEC=15000000');next_extend=now+2
            else:need(now<mono+177,'envelope work deadline; cleanup reserved')
            for key,_ in selector.select(.02):
                block=os.read(key.fileobj.fileno(),4096)
                if not block:selector.unregister(key.fileobj);continue
                need(len(log)+len(block)<=LOG_MAX,'envelope log quota exceeded');log.extend(block)
        need(started is not None and proc.returncode==0,'guard failed or never admitted')
        row_sha=guard_row(request,label,started,mono+177)
    except BaseException as exc:failure=str(exc)[:2048]
    finally:
        selector.close()
        deadline=(mono+179) if mono is not None else time.monotonic()+2
        try:
            # Control and active are siblings. Killing the process tree alone
            # would miss migrated supervisor/worker descendants.
            children={p.name for p in root.iterdir() if p.is_dir()}
            allowed={'bootstrap','control',H.run_name(request)}
            need(children<=allowed,'unexpected envelope cgroup; external reconciliation required')
            for name in ('control',H.run_name(request)):remove_tree(root/name,deadline)
            if proc is not None:proc.wait(timeout=max(.001,deadline-time.monotonic()));proc.stdout.close()
            while True:
                try:
                    pid,_=os.waitpid(-1,os.WNOHANG)
                    if pid==0:
                        need(time.monotonic()<deadline,'orphan guard cleanup timed out');time.sleep(.01)
                except ChildProcessError:break
            cleanup=True
        except BaseException as exc:failure=(failure or '')+'; cleanup: '+str(exc)[:1024]
    data={'schema':'e16-task-local-envelope-v1','request_sha256':digest,'run_id':request['run_id'],
          'guard_pid':None if proc is None else proc.pid,'guard_process_start':guard_start,
          'contract':CONTRACT,'unit':unit_name(request),'root':str(root),'status':'INCOMPLETE' if failure else 'COMPLETE',
          'reason':failure,'guard_started_unix':started,'shared_guard_receipt_sha256':row_sha,
          'cleanup_complete':cleanup,'resources':snapshot(root),'external_reserve_bytes':EXTERNAL_RESERVE,
          'log_base64':base64.b64encode(log).decode('ascii'),'log_bytes':len(log),'electrical_acceptance':False,
          'whole_board_acceptance':False,'adopted':False,'terminal_unix':time.time()}
    # This receipt is outside the numerical inventory: it is written AFTER the
    # immutable journal and exact shared-guard row, and binds both explicitly.
    journal=A.state_directory()/(request['run_id']+'.terminal.json')
    data['terminal_journal_sha256']=A.sha(journal) if journal.is_file() else None
    data['elapsed_seconds']=None if mono is None else time.monotonic()-mono
    data['activation']=properties(unit_name(request))
    need(int(data['resources']['memory.current'])+RECEIPT_MAX<ROOT_MEMORY,'terminal memory reserve absent')
    raw=A.canon(data);need(len(raw)<=RECEIPT_MAX,'envelope receipt reserve exceeded')
    need(mono is None or time.monotonic()<mono+180,'envelope terminal exceeded original deadline')
    A.state_directory().mkdir(parents=True,exist_ok=True)
    A.write_new(receipt_path(request),raw)
    return 1 if failure else 0


def outer(request_path,digest,authority,reservation,launcher_pid,launcher_start):
    """Retain bounded setup refusal even before the guarded state machine starts."""
    import attribution_admission as A
    import attribution_host as H
    try:return _outer(request_path,digest,authority,reservation,launcher_pid,launcher_start)
    except BaseException as exc:
        request=H.read_small(request_path)
        need(request.get('schema')=='e16-attribution-request-v1' and not request.get('fixture_only') and
             hashlib.sha256(A.canon(request)).hexdigest()==digest,'unbound pre-guard failure')
        unit_name(request)  # Validate the fixed state-file identity before writing.
        data={'schema':'e16-task-local-envelope-v1','status':'INCOMPLETE','request_sha256':digest,
              'run_id':request['run_id'],'contract':CONTRACT,'unit':unit_name(request),
              'reason':type(exc).__name__+': '+str(exc)[:2048],
              'cleanup_complete':False,'cleanup':'Manager whole-service termination required; no success receipt',
              'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False}
        raw=A.canon(data);need(len(raw)<=RECEIPT_MAX,'negative envelope receipt quota')
        A.state_directory().mkdir(parents=True,exist_ok=True)
        path=receipt_path(request)
        if not path.exists():A.write_new(path,raw)
        # An already written receipt is never overwritten to manufacture success.
        return 1


def accepted(request,digest,guard_sha):
    import attribution_admission as A
    import attribution_host as H
    need(request.get('host_limits')==H.HOST_LIMITS,'sealed envelope contract differs')
    record=A.read_json(receipt_path(request),RECEIPT_MAX)
    need(record['request_sha256']==digest and record['run_id']==request['run_id'] and
         record['contract']==CONTRACT and record['status']=='COMPLETE' and
         record['cleanup_complete'] is True and all(record.get(k) is False for k in
             ('electrical_acceptance','whole_board_acceptance','adopted')),'incomplete task-local envelope')
    need(record['shared_guard_receipt_sha256']==guard_sha and
         record['terminal_journal_sha256']==A.sha(A.state_directory()/(request['run_id']+'.terminal.json')),
         'envelope immutable journal/guard binding differs')
    need(record['unit']==unit_name(request) and Path(record['root']).resolve()==Path(record['root']) and
         Path(record['root']).is_relative_to('/sys/fs/cgroup') and
         record['root']=='/sys/fs/cgroup'+record['activation']['ControlGroup'] and
         Path(record['root']).name==unit_name(request),
         'envelope retained identity differs')
    need(not Path(record['root']).exists() and properties(unit_name(request)).get('LoadState')=='not-found',
         'envelope not collected; acceptance refused')
    r=record['resources']
    need(r['memory.max']==str(ROOT_MEMORY) and int(r['memory.peak'])<=ROOT_MEMORY and
         r['memory.swap.max']==r['memory.swap.current']=='0','envelope resource proof differs')
    events=dict(x.split() for x in r['memory.events'].splitlines())
    need(int(events.get('oom',0))==int(events.get('oom_kill',0))==0,'envelope OOM')
    need(0<record['elapsed_seconds']<180,'envelope terminal time differs')
    return record
