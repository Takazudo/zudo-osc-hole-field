"""Bounded E16 subprocess supervision; NOT an authorization or scope creator.

The source-owned attribution_host adapter provisions the independently admitted
containment layout and owns retention/scope cleanup. This module proves that
layout and supervises one worker; it never creates authority. Only bounded
synthetic fixture subprocesses may use FixtureContainment.
"""
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

MEMORY_MAX = 2*1024**3
SUPERVISOR_MEMORY = 64*1024**2
OUTER_MEMORY = 64*1024**2
LAUNCHER_MEMORY = 64*1024**2
BOOTSTRAP_MEMORY = 64*1024**2
CONTROLLER_FILECACHE = 64*1024**2
SHARED_GUARD_MEMORY = 8*64*1024**2
ACTIVE_SCOPE_MEMORY = MEMORY_MAX-OUTER_MEMORY-LAUNCHER_MEMORY-CONTROLLER_FILECACHE-SHARED_GUARD_MEMORY
WORKER_MEMORY = ACTIVE_SCOPE_MEMORY-SUPERVISOR_MEMORY-BOOTSTRAP_MEMORY
OUTPUT_MAX = 64*1024**2
LOG_RESERVE = 1024**2
RECEIPT_RESERVE = 65536
CLEANUP_SECONDS = 10.


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(",", ":"),allow_nan=False)+"\n").encode()


def _write_new(path, data):
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"wb") as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def _event_values(path):
    return {k:int(v) for k,v in (line.split() for line in path.read_text().splitlines())}


class LinuxContainment:
    """Prove an existing kernel boundary; never accept caller asserted limits.

    The supervisor and worker use separate sibling cgroups below the tightened
    active parent, leaving explicitly budgeted external controller/guard reserves.
    Worker memory is capped below that parent to reserve supervisor/receipt space.
    Worker output is an exact dedicated tmpfs mount below the output root. Its
    kernel capacity leaves separate bounded log and terminal-receipt reserves.
    Scope/mount creation, ownership admission and eventual scope removal belong
    to attribution_host, not this checking API.
    """
    def __init__(self, parent, worker, work, guard_sha256):
        self.parent,self.worker,self.work = map(Path,(parent,worker,work))
        self.guard_sha256 = guard_sha256
        self.initial_events = None

    def prove(self, output_limit):
        from numerical_unit_guard import UnitGuard
        UnitGuard(self.guard_sha256).prove_owner(inherited_fd=int(os.environ['E16_GUARD_FD']))
        cg = Path("/sys/fs/cgroup")
        rel = Path("/proc/self/cgroup").read_text().strip().split("::",1)[1]
        own = cg / rel.lstrip("/")
        need(self.parent.resolve()==self.parent and self.worker.resolve()==self.worker,
             "noncanonical cgroup path")
        need(self.parent.is_relative_to(cg) and own.parent==self.parent and
             self.worker.parent==self.parent and own!=self.worker,"owned sibling cgroup layout absent")
        for path,maximum in ((self.parent,ACTIVE_SCOPE_MEMORY),(own,SUPERVISOR_MEMORY),
                             (self.worker,WORKER_MEMORY)):
            need((path/"memory.max").read_text().strip()==str(maximum) and
                 (path/"memory.swap.max").read_text().strip()=="0","memory/no-swap boundary absent")
        need(_event_values(self.worker/"cgroup.events")["populated"]==0,"worker cgroup is not fresh")
        need((self.worker/"cgroup.kill").exists(),"kernel cgroup kill unavailable")
        need(self.work.is_dir() and not any(self.work.iterdir()),"fresh dedicated output mount required")
        mount=[]
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            left,right=line.split(" - ",1)
            # Reject escaped names rather than guessing mountinfo decoding.
            if left.split()[4]==str(self.work):
                mount.append(right.split()[0])
        need(mount==["tmpfs"],"dedicated tmpfs worker output quota absent")
        stat=os.statvfs(self.work)
        self.capacity=stat.f_blocks*stat.f_frsize
        need(0 < self.capacity <= output_limit-LOG_RESERVE-RECEIPT_RESERVE,
             "worker filesystem quota exceeds aggregate reserve")
        need(len(list(Path("/proc/self/task").iterdir()))==1,"supervisor must be single-threaded before fork")
        self.initial_events=_event_values(self.worker/"memory.events")

    def launch(self, command):return command

    def enter(self):
        (self.worker/"cgroup.procs").write_text(str(os.getpid()))
        actual=Path("/proc/self/cgroup").read_text().strip().split("::",1)[1]
        need(Path("/sys/fs/cgroup")/actual.lstrip("/")==self.worker,"worker cgroup migration failed")

    def kill(self, process):
        (self.worker/"cgroup.kill").write_text("1")
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass

    def clean(self):
        return _event_values(self.worker/"cgroup.events")["populated"]==0

    def oom(self):
        final=_event_values(self.worker/"memory.events")
        return any(final.get(k,0)>self.initial_events.get(k,0) for k in ("oom","oom_kill","oom_group_kill"))


class FixtureContainment:
    """Synthetic tests only: no production cgroup/mount proof is claimed."""
    def __init__(self, root, *, pretend_oom=False):
        self.root=Path(root)
        self.pretend_oom=pretend_oom
        self.killed=False

    def prove(self, output_limit):
        need(self.root.parent==Path("/tmp") and self.root.name.startswith("e16-supervisor-fixture-"),
             "fixture root required")
        need(self.root.resolve()==self.root,"fixture symlink refused")
        self.file_limit=min(4*1024**2,output_limit-LOG_RESERVE-RECEIPT_RESERVE)

    def launch(self, command):
        # Start the stdlib wrapper through exec, avoiding preexec Python in test
        # runners that may already have numerical-library background threads.
        wrapper=("import os,resource,sys;"
                 "resource.setrlimit(resource.RLIMIT_AS,(402653184,402653184));"
                 "resource.setrlimit(resource.RLIMIT_CPU,(2,2));"
                 f"resource.setrlimit(resource.RLIMIT_FSIZE,({self.file_limit},{self.file_limit}));"
                 "resource.setrlimit(resource.RLIMIT_NOFILE,(64,64));"
                 "os.execvpe(sys.argv[1],sys.argv[1:],os.environ)")
        return [sys.executable,"-c",wrapper,*command]

    def kill(self, process):
        self.killed=True
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass

    def clean(self):return True
    def oom(self):return self.pretend_oom


def _inventory(root, deadline, limit):
    """Hash every retained file, refusing links, special files and large trees."""
    total=0;files={};count=0
    for base,dirs,names in os.walk(root,followlinks=False):
        need(time.monotonic()<deadline,"TIMEOUT during output hashing")
        count+=len(dirs)+len(names)
        need(count<=10000,"output file-count quota")
        for name in dirs:
            need(not (Path(base)/name).is_symlink(),"output directory symlink refused")
        for name in names:
            path=Path(base)/name
            need(not path.is_symlink() and path.is_file(),"nonregular output refused")
            total+=path.stat().st_size
            need(total<=limit,"aggregate output quota exhausted")
            digest=hashlib.sha256()
            with path.open("rb") as stream:
                while True:
                    need(time.monotonic()<deadline,"TIMEOUT during output hashing")
                    block=stream.read(65536)
                    if not block:break
                    digest.update(block)
            files[str(path.relative_to(root))]={"bytes":path.stat().st_size,"sha256":digest.hexdigest()}
    return total,files


def supervise(command, root, *, started, seconds=180., cleanup_seconds=CLEANUP_SECONDS,
              output_bytes=OUTPUT_MAX, prior_output_bytes=0, tail_reserve_seconds=0., containment, cancelled=lambda:False):
    """Internal one-attempt primitive; caller has already consumed admission.

    started MUST be the actual monotonic guard-entry time, not launch time.
    prior_output_bytes includes every earlier in-unit claim/log/receipt byte;
    no output outside this tree may be omitted by the future admission adapter.
    Production uses LinuxContainment and fixed 180s/64MiB. FixtureContainment
    allows smaller deterministic synthetic subprocess limits. No public CLI can
    invoke this API with production artifacts or fabricate authority/reservation.
    A supervisor COMPLETE receipt is the only acceptance marker; worker output
    stays below .work.partial and is never independently published.
    """
    root=Path(root)
    fixture=type(containment) is FixtureContainment
    need(type(containment) in (FixtureContainment,LinuxContainment),"unknown containment provider")
    need(0<cleanup_seconds<seconds<=180 and RECEIPT_RESERVE+LOG_RESERVE<output_bytes<=OUTPUT_MAX,
         "invalid supervision caps")
    need(fixture or (seconds==180 and output_bytes==OUTPUT_MAX and cleanup_seconds>=10),
         "production caps/reserves changed")
    need(type(prior_output_bytes) is int and 0 <= prior_output_bytes < output_bytes-LOG_RESERVE-RECEIPT_RESERVE, "prior claim/log accounting invalid")
    available=output_bytes-prior_output_bytes
    need(0 <= tail_reserve_seconds < seconds-cleanup_seconds, "invalid host tail reserve")
    deadline=started+seconds-tail_reserve_seconds;work_deadline=deadline-cleanup_seconds
    need(started<=time.monotonic()<work_deadline,"expired/future guard-entry time")
    need(root.is_absolute() and root.resolve()==root and root.parent.is_dir(),"canonical output root required")
    if fixture:
        need(root==containment.root,"fixture output root differs")
        root.mkdir(exist_ok=False)
        work=root/".work.partial";work.mkdir()
    else:
        work=root/".work.partial"
        need(containment.work==work and root.is_dir(),"production output layout differs")
        need(set(root.iterdir())=={work},"production output root is not fresh")
    result=None;proc=None;failure=None;logs=0;files={};total=None;clean=False
    selector=selectors.DefaultSelector()
    env=dict(os.environ,TMPDIR=str(work),E16_SUPERVISOR_WORK=str(work),E16_SUPERVISOR_RESULT=str(work/"result"),
             E16_WORK_DEADLINE=str(work_deadline),E16_OUTPUT_LIMIT=str(available-LOG_RESERVE-RECEIPT_RESERVE))
    for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):env[key]="1"
    log=(root/"worker.log.partial").open("xb")
    try:
        containment.prove(available)
        if not fixture:
            env["E16_OUTPUT_LIMIT"]=str(min(int(env["E16_OUTPUT_LIMIT"]),containment.capacity))
        need(not cancelled(),"CANCELLED before launch")
        proc=subprocess.Popen(containment.launch(list(command)),cwd=work,env=env,
                              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              start_new_session=True,preexec_fn=None if fixture else containment.enter,
                              pass_fds=() if fixture else (int(env['E16_GUARD_FD']),int(env['E16_HOST_LOCK_FD'])))
        for pipe in (proc.stdout,proc.stderr):
            os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ)
        while selector.get_map() or proc.poll() is None:
            need(time.monotonic()<work_deadline,"TIMEOUT")
            need(not cancelled(),"CANCELLED")
            for key,_ in selector.select(min(.02,max(0,work_deadline-time.monotonic()))):
                chunk=os.read(key.fileobj.fileno(),65536)
                if not chunk:
                    selector.unregister(key.fileobj);key.fileobj.close();continue
                allowance=LOG_RESERVE-logs
                log.write(chunk[:allowance]);logs+=min(len(chunk),allowance)
                need(len(chunk)<=allowance,"aggregate log quota exhausted")
        result=proc.wait(timeout=max(.001,work_deadline-time.monotonic()))
        need(result==0,"worker failed: "+str(result))
        need(not containment.oom(),"worker OOM")
    except BaseException as exc:
        failure=str(exc)[:2048] or type(exc).__name__
    finally:
        if proc is not None:
            try:
                containment.kill(proc)  # Also kill descendants after parent exit.
                proc.wait(timeout=max(.001,deadline-time.monotonic()-1))
                while not containment.clean() and time.monotonic()<deadline-1:time.sleep(.005)
                clean=containment.clean()
                if not clean:failure="owned worker cleanup incomplete"
                if containment.oom():failure="worker OOM"
            except BaseException as exc:failure="cleanup: "+str(exc)[:1900]
        else:clean=True
        for key in list(selector.get_map().values()):key.fileobj.close()
        selector.close()
        try:
            log.flush();os.fsync(log.fileno())
        except BaseException as exc:
            failure="log finalization: "+str(exc)[:1900]
        finally:
            try:log.close()
            except BaseException as exc:failure="log close: "+str(exc)[:1900]
    # Invalidate worker success before doing any further fallible validation.
    candidate=work/"result/terminal.json"
    worker_marker_revoked=False
    try:
        if candidate.exists() or candidate.is_symlink():
            destination=work/"result/terminal.worker-unaccepted.json"
            need(not destination.exists() and not destination.is_symlink(),"unaccepted worker marker already exists")
            candidate.rename(destination)
        worker_marker_revoked=True
    except BaseException as exc:
        failure="worker marker revocation: "+str(exc)[:1900]
    try:
        need(time.monotonic()<deadline-1,"TIMEOUT before terminal validation")
        total,files=_inventory(root,deadline-1,available-RECEIPT_RESERVE)
        if failure is None:
            worker_receipt=work/"result/terminal.worker-unaccepted.json"
            need(worker_receipt.stat().st_size<=RECEIPT_RESERVE,"worker receipt too large")
            receipt=json.loads(worker_receipt.read_text())
            need(receipt.get("status")=="COMPLETE","incomplete worker output")
            component=files.get(".work.partial/result/components.jsonl")
            need(component is not None and receipt.get("components_sha256")==component["sha256"],
                 "worker component digest mismatch")
            need(all(receipt.get(k) is False for k in ("electrical_acceptance","whole_board_acceptance","adopted")),
                 "worker acceptance flags changed")
    except BaseException as exc:
        failure=failure or str(exc)[:2048]
    record={"schema":"e16-supervisor-terminal-v1","status":"INCOMPLETE" if failure else "COMPLETE",
            "reason":failure,"worker_exit":None if proc is None else proc.returncode,
            "cleanup_complete":clean,"worker_marker_revoked":worker_marker_revoked,"fixture_only":fixture,"elapsed_seconds":time.monotonic()-started,
            "retained_bytes_before_receipt":total,"prior_output_bytes":prior_output_bytes,"log_bytes":logs,"files":files,
            "electrical_acceptance":False,"whole_board_acceptance":False,"adopted":False}
    data=encoded(record)
    # Large inventories do not consume the reserved terminal capacity on failure.
    if len(data)>RECEIPT_RESERVE:
        record.update(status="INCOMPLETE",reason="terminal inventory quota exhausted",files={})
        data=encoded(record)
    need(time.monotonic()<deadline,"terminal receipt deadline exceeded; output remains unaccepted")
    _write_new(root/"terminal.pending",data)
    need(time.monotonic()<deadline,"terminal commit deadline exceeded; output remains unaccepted")
    (root/"terminal.pending").rename(root/"terminal.json")
    if time.monotonic()>=deadline:
        (root/"terminal.json").rename(root/"terminal.late-unaccepted.json")
        raise ValueError("terminal commit exceeded deadline; result revoked")
    return record
