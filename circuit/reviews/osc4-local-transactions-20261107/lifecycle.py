#!/usr/bin/env python3
"""Receipt lifecycle for transaction.py: atomic writes, phase checkpoints, owned native children,
signal propagation and collector-side reconciliation (issue #308).

On Actions run 42412490176 the K driver ended with exit 137 within a second of the timeout
wrapper's SIGINT, printed no traceback, and left its receipt at RUNNING. This module makes the
receipt durable at every step so that no process exit can leave it ambiguous:

- every receipt write is temp file + os.replace;
- a checkpoint is written before each native call, with the child's PID/PGID;
- the driver's own SIGINT/SIGTERM/SIGHUP handler writes the receipt first, then forwards the
  signal to the children it started, waits a bounded grace period, SIGKILLs only those children,
  and unwinds so run() finalises `INTERRUPTED; NOT ADOPTED` and exits 128+signal;
- a driver deadline (--max-minutes) uses the same path and finalises `TIMED OUT; NOT ADOPTED`;
- reconcile() lets the collector finish a receipt the driver could not, from the process exit
  status the shell saw, without ever fabricating a result.

Native children run in their own session (start_new_session=True): the driver can signal the
whole `bash scripts/kicad/run.sh -> docker` subtree, and a signal sent to the wrapper's process
group reaches them only through the driver, which records it. The KiCad container itself is not
in the host process tree: killing the docker client orphans it (observed on this host, #308). So
run.sh writes each container id into the directory named by KICAD_ORACLE_CIDDIR, which the driver
owns per invocation, and the driver `docker stop`s exactly those ids on its way out. Nothing
outside those children and containers is ever signalled.
"""
from __future__ import annotations
import hashlib,json,os,secrets,shutil,signal,subprocess,sys,time
from pathlib import Path

SCHEMA='osc4-transaction-receipt-2'
# Terminal outcomes. Only COMPLETED may carry raw_gate_passed=true; nothing ever sets adopted=true.
OUTCOMES=('COMPLETED','REJECTED','INTERRUPTED','TIMED_OUT','KILLED','ERROR','UNKNOWN')
DEADLINE_SIGNAL=signal.SIGALRM
HANDLED=(signal.SIGINT,signal.SIGTERM,signal.SIGHUP)
DEFAULT_GRACE_SECONDS=15.0


def utc():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())


def sha_bytes(b):return hashlib.sha256(b).hexdigest()


def hosted():
    # https://docs.github.com/en/actions/reference/workflows-and-actions/variables
    return os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'


def environment():
    return {'hosted':hosted(),'github_actions':os.environ.get('GITHUB_ACTIONS')=='true',
            'runner_environment':os.environ.get('RUNNER_ENVIRONMENT'),
            'github_run_id':os.environ.get('GITHUB_RUN_ID'),'github_run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT')}


def source_revision(root):
    try:
        done=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,timeout=20)
        return done.stdout.strip() if done.returncode==0 and done.stdout.strip() else 'unknown'
    except (OSError,subprocess.SubprocessError):return 'unknown'


def new_invocation():return f"{time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())}-{os.getpid()}-{secrets.token_hex(4)}"


def write_atomic(path,text):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(text);os.replace(tmp,path)


class Interrupted(BaseException):
    """Raised on the main thread by the signal handler so run() unwinds, finalises the receipt and exits 128+signal (124 for the deadline)."""
    def __init__(self,signum,reason):
        super().__init__(reason);self.signum=signum;self.reason=reason
    @property
    def exit_code(self):return 124 if self.signum==DEADLINE_SIGNAL else 128+self.signum


class StaleReceipt(RuntimeError):
    """A receipt for this spec already exists from another invocation; nothing was started."""


class Receipt:
    def __init__(self,path,data):self.path=Path(path);self.data=data

    def save(self):write_atomic(self.path,json.dumps(self.data,indent=1,sort_keys=True)+'\n')

    def checkpoint(self,phase,**extra):
        """Close the running phase and open `phase`; written before the expensive call it names starts."""
        now=utc();self.end_phase(now)
        self.data.setdefault('phases',[]).append({'phase':phase,'started_utc':now,**extra});self.data['phase']=phase;self.save()

    def end_phase(self,now=None):
        phases=self.data.get('phases') or []
        if phases and phases[-1].get('ended_utc') is None:phases[-1]['ended_utc']=now or utc()


class State:
    def __init__(self):
        self.receipt=None;self.children={};self.signals=[];self.interrupting=None;self.escalate=False
        self.grace=DEFAULT_GRACE_SECONDS;self.cwd=None;self.cid_dir=None;self.installed=False


STATE=State()


def _signal_name(signum):
    try:return signal.Signals(signum).name
    except ValueError:return str(signum)


def _handle(signum,frame):
    """Record the signal durably, forward it to owned children, then unwind run() once."""
    name=_signal_name(signum);deadline=signum==DEADLINE_SIGNAL
    STATE.signals.append({'signal':int(signum),'name':name,'utc':utc()})
    forward=signal.SIGTERM if deadline else signum
    receipt=STATE.receipt
    if receipt is not None:
        receipt.data['signals']=list(STATE.signals)
        if STATE.interrupting is None:
            receipt.data.update(status='TIMED OUT; NOT ADOPTED' if deadline else 'INTERRUPTED; NOT ADOPTED',
                                terminal_outcome='TIMED_OUT' if deadline else 'INTERRUPTED',
                                interrupt={'signal':int(signum),'name':name,'utc':utc(),'phase':receipt.data.get('phase'),
                                           'forwarded_signal':int(forward),'reason':'driver deadline' if deadline else f'{name} received'})
        # Written before anything else happens: a follow-up SIGKILL still leaves the signal on record.
        receipt.save()
    if STATE.interrupting is not None:
        STATE.escalate=True;return
    for pid,proc in list(STATE.children.items()):
        if proc.poll() is None:
            try:os.killpg(pid,forward)
            except ProcessLookupError:pass
    STATE.interrupting=Interrupted(int(signum),'driver deadline' if deadline else f'{name} received')
    raise STATE.interrupting


def install(deadline_seconds=None,grace=None):
    """Install the driver's handlers in the real process; unit tests calling run() directly keep Python's defaults."""
    if grace is not None:STATE.grace=float(grace)
    elif os.environ.get('OSC4_GRACE_SECONDS'):STATE.grace=float(os.environ['OSC4_GRACE_SECONDS'])
    for s in HANDLED:signal.signal(s,_handle)
    if deadline_seconds:
        signal.signal(DEADLINE_SIGNAL,_handle);signal.setitimer(signal.ITIMER_REAL,float(deadline_seconds))
    STATE.installed=True


def _reap(proc,call):
    """Grace period for a child that already received the forwarded signal, then SIGKILL on its session only."""
    deadline=time.monotonic()+STATE.grace
    while proc.poll() is None and time.monotonic()<deadline and not STATE.escalate:time.sleep(0.05)
    if proc.poll() is None:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        proc.wait();call['ended_by']='SIGKILL after grace'
    else:call['ended_by']='exited after signal'


def owned_containers(cid_dir):
    """Container ids scripts/kicad/run.sh wrote into the driver's own KICAD_ORACLE_CIDDIR."""
    if not cid_dir or not Path(cid_dir).is_dir():return []
    return [cid for f in sorted(Path(cid_dir).glob('*.cid')) for cid in [f.read_text().strip()] if cid]


def stop_owned_containers(cid_dir,stop_seconds=5):
    """docker stop exactly the containers listed in the driver's cid directory that still run; reported, never raised."""
    docker=shutil.which('docker');report=[]
    if not docker:return report
    for cid in owned_containers(cid_dir):
        try:
            state=subprocess.run([docker,'inspect','-f','{{.State.Running}}',cid],capture_output=True,text=True,timeout=30)
            if state.returncode!=0 or state.stdout.strip()!='true':continue  # exited and removed by --rm, or stopped
            done=subprocess.run([docker,'stop','-t',str(int(stop_seconds)),cid],capture_output=True,text=True,timeout=stop_seconds+60)
            report.append({'container':cid,'action':'docker stop','ok':done.returncode==0,'stderr':done.stderr.strip()[-300:],'utc':utc()})
        except (OSError,subprocess.SubprocessError) as e:report.append({'container':cid,'action':'docker stop','ok':False,'error':repr(e),'utc':utc()})
    return report


def sweep_containers(receipt=None):
    """Stop whatever owned container survived its client; appends to receipt['containers_stopped'] when something was stopped."""
    report=stop_owned_containers(STATE.cid_dir)
    if report and receipt is not None:receipt.data.setdefault('containers_stopped',[]).extend(report);receipt.save()
    return report


def owned_run(*args):
    """Drop-in for route_jack_grid.run(): same arguments, output and failure, with the child owned by the driver.

    The child starts in its own session so the whole oracle subtree (bash run.sh -> docker client) is
    reachable by one killpg, and every call is checkpointed in the receipt with its PID/PGID.
    """
    receipt=STATE.receipt
    proc=subprocess.Popen(args,cwd=STATE.cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    STATE.children[proc.pid]=proc
    call={'argv':[str(a) for a in args[:6]],'argc':len(args),'pid':proc.pid,'pgid':proc.pid,'started_utc':utc()}
    if receipt is not None:
        receipt.data.setdefault('native_calls',[]).append(call);receipt.data['current_child']=call;receipt.save()
    out=''
    try:out=proc.communicate()[0] or ''
    finally:
        if proc.poll() is None:_reap(proc,call)
        if proc.stdout:proc.stdout.close()
        STATE.children.pop(proc.pid,None)
        call.update(ended_utc=utc(),returncode=proc.returncode)
        if receipt is not None:receipt.data['current_child']=None;receipt.save()
        # A client that died from a signal leaves its container running; stop exactly the owned ones.
        if call.get('ended_by') or proc.returncode not in (0,):sweep_containers(receipt)
    if proc.returncode:
        print(out[-3000:]);raise RuntimeError(f'{args[:4]} failed ({proc.returncode})')
    return out


def outcome_for_exit(exit_status):
    """Map the exit status the shell saw to a terminal state; None means the status is not known."""
    if exit_status is None:return 'UNKNOWN',None
    if exit_status in (129,130,143):return 'INTERRUPTED','INTERRUPTED; NOT ADOPTED'
    if exit_status==124:return 'TIMED_OUT','TIMED OUT; NOT ADOPTED'
    if exit_status in (137,-9):return 'KILLED','KILLED; OUTCOME UNKNOWN; NOT ADOPTED'
    return 'ERROR','ERROR; NOT ADOPTED'


def _alive(pid):
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    except PermissionError:return True
    return True


def reconcile(path,exit_status,invocation=None,board=None,spec_name=None):
    """Collector side: finish a receipt the driver left nonterminal from the KNOWN process exit status.

    A terminal receipt is left untouched. A receipt from another invocation is refused (exit code 4),
    so a historical committed receipt can never be rewritten into this run's result. The prior bytes
    are appended to <spec>.raw-events.jsonl and summarised in a `recovery` block; adopted and
    raw_gate_passed are forced false; with no exit status the receipt stays nonterminal with
    terminal_outcome UNKNOWN. Nothing is signalled or killed here.
    """
    path=Path(path);events=path.with_name(path.stem+'.raw-events.jsonl')
    raw=path.read_bytes() if path.exists() else None
    prior=None;parse_error=None
    if raw is not None:
        try:prior=json.loads(raw)
        except ValueError as e:parse_error=repr(e)
        if not isinstance(prior,dict):prior,parse_error=None,parse_error or 'receipt is not a JSON object'
    if prior is not None and prior.get('terminal') is True:
        return {'action':'kept','exit_code':0,'status':prior.get('status'),'terminal_outcome':prior.get('terminal_outcome'),'path':str(path)}
    if invocation is not None and prior is not None and prior.get('invocation')!=invocation:
        return {'action':'refused','exit_code':4,'reason':f"receipt invocation {prior.get('invocation')!r} is not this run's {invocation!r}",
                'status':prior.get('status'),'path':str(path)}
    outcome,status=outcome_for_exit(exit_status)
    data=dict(prior) if prior is not None else {'schema':SCHEMA,'board':board,'spec_name':spec_name,'started_utc':None}
    if invocation is not None and prior is None:data['invocation']=invocation
    last=(prior or {}).get('phases') or []
    recovery={'reconciled_utc':utc(),'exit_status':exit_status,'prior_present':raw is not None,'prior_status':(prior or {}).get('status'),
              'prior_terminal_outcome':(prior or {}).get('terminal_outcome'),'prior_sha256':sha_bytes(raw) if raw is not None else None,
              'prior_parse_error':parse_error,'last_checkpoint':last[-1] if last else None,'raw_events':events.name,
              'invocation_verified':invocation is not None and prior is not None and prior.get('invocation')==invocation,
              'note':'terminal state written by the collector from the process exit status; the driver produced no result'}
    child=(prior or {}).get('current_child')
    if child and child.get('pid'):
        recovery['child_at_exit']={**child,'alive_at_reconcile':_alive(int(child['pid'])),'action':'reported only; never signalled by the collector'}
    cid_dir=(prior or {}).get('oracle_cid_dir')
    if cid_dir:
        # Containers the driver's own run.sh calls started are owned state; a SIGKILLed driver could not stop them.
        recovery['containers_stopped']=stop_owned_containers(cid_dir)
    if outcome=='UNKNOWN':
        data.update(terminal=False,terminal_outcome='UNKNOWN',adopted=False,raw_gate_passed=False,
                    status=(prior or {}).get('status') or 'RUNNING',recovery={**recovery,'note':'no exit status known (runner vanished?); left nonterminal'})
    else:
        if exit_status==0:recovery['note']='exit 0 but the receipt was left nonterminal; treated as an error, never as a result'
        data.update(status=status,terminal=True,terminal_outcome=outcome,adopted=False,raw_gate_passed=False,recovery=recovery)
        if data.get('schema')=='osc4-transaction-receipt-1':data['schema']=SCHEMA
    event={'utc':recovery['reconciled_utc'],'event':'reconcile','exit_status':exit_status,'outcome':outcome,
           'prior_raw':raw.decode('utf-8','backslashreplace') if raw is not None else None}
    with open(events,'a') as f:f.write(json.dumps(event,sort_keys=True)+'\n')
    write_atomic(path,json.dumps(data,indent=1,sort_keys=True)+'\n')
    return {'action':'reconciled','exit_code':0,'status':data['status'],'terminal_outcome':outcome,'terminal':data['terminal'],'path':str(path)}
