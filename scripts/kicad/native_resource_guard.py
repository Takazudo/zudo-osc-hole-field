#!/usr/bin/env python3
"""Opt-in admitted Linux/systemd/Docker worker guard. Never admits a job itself."""
import argparse
from contextlib import contextmanager
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time

GIB = 1024 ** 3
CAP = 6 * GIB
AGGREGATE_CAP = 12 * GIB
FLOOR = 2 * GIB
ABORT_FREE = 5 * GIB // 2


def identity(value):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', value):
        raise ValueError('worker identity must be a short lowercase alphanumeric/hyphen token')
    return value


def memory_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise ValueError('MemAvailable missing')


def event_values(text):
    return {k: int(v) for k, v in (line.split() for line in text.splitlines())}


def stop_reason(available, events, initial_events, elapsed, deadline):
    if available <= ABORT_FREE:
        return 'free-memory guard (2.5GiB early abort; 2GiB mandatory floor)'
    if any(events.get(k, 0) > initial_events.get(k, 0) for k in ('oom', 'oom_kill')):
        return 'worker OOM event'
    if elapsed >= deadline:
        return 'whole-command deadline'
    return None


def docker_membership(inspect, cgroup_text, slice_path):
    config = inspect['HostConfig']
    if config['Memory'] != CAP or config['MemorySwap'] != CAP:
        raise ValueError('Docker memory/swap caps differ from6GiB/no additional swap')
    if config['CgroupParent'] != slice_path.rsplit('/', 1)[-1]:
        raise ValueError('Docker slice parent differs')
    paths = [line.split(':', 2)[2] for line in cgroup_text.splitlines() if line.startswith('0::')]
    if len(paths) != 1 or not paths[0].startswith(slice_path.rstrip('/') + '/'):
        raise ValueError('Docker container outside shared worker slice')


def cgroup_limits(cgroup, cap=CAP):
    controllers = (Path('/sys/fs/cgroup') / 'cgroup.controllers').read_text().split()
    if 'memory' not in controllers:
        raise ValueError('cgroup v2 memory controller missing')
    if (cgroup / 'memory.max').read_text().strip() != str(cap):
        raise ValueError('shared slice cap missing: ' + str(cap))
    if (cgroup / 'memory.swap.max').read_text().strip() != '0':
        raise ValueError('shared slice zero swap cap missing')
    for name in ('memory.current', 'memory.peak', 'memory.events'):
        if not (cgroup / name).is_file():
            raise ValueError('missing cgroup evidence: ' + name)


def run(args, **kwargs):
    kwargs.setdefault('timeout', 20)
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout.strip()


def local_docker():
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
        raise ValueError('custom Docker endpoint/context not admitted')
    endpoint = json.loads(run(['docker', 'context', 'inspect']))[0]['Endpoints']['docker']['Host']
    if endpoint != 'unix:///var/run/docker.sock':
        raise ValueError('requires verified local system Docker daemon')
    info = json.loads(run(['docker', 'info', '--format', '{{json .}}']))
    if info['CgroupDriver'] != 'systemd' or str(info['CgroupVersion']) != '2':
        raise ValueError('requires systemd cgroupv2 Docker')
    if not info.get('MemoryLimit') or not info.get('SwapLimit'):
        raise ValueError('Docker daemon lacks memory/swap support')


def require_local_image():
    pin = Path('scripts/kicad/pin.env').read_text()
    matched = re.search(r"^KICAD_IMAGE='(kicad/kicad@sha256:[0-9a-f]{64})'$", pin, re.MULTILINE)
    if not matched:
        raise ValueError('invalid pinned KiCad image identity')
    image = matched.group(1)
    metadata = json.loads(run(['docker', 'image', 'inspect', image]))[0]
    if image not in metadata.get('RepoDigests', []):
        raise ValueError('exact pinned image not locally authenticated; never pull during admission')
    return image


def require_harmless_fixture(image, command):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('immutable locally imported harmless fixture image required')
    entry = str(Path('scripts/kicad/run_resource_fixture.py').resolve())
    prefix = [sys.executable, entry, '--image', image, '--mode']
    if command[:len(prefix)] != prefix or command[len(prefix):] not in (['aggregate'], ['hold']):
        raise ValueError('harmless qualification permits only the reviewed fixture runner')
    metadata = json.loads(run(['docker', 'image', 'inspect', image]))[0]
    if metadata.get('Id') != image or metadata.get('Config', {}).get('Entrypoint') != ['/fixture']:
        raise ValueError('local fixture image identity/entrypoint mismatch')


def worker_containers(worker, timeout=20):
    return run(['docker', 'ps', '-aq', '--filter', 'label=epic242.native.worker=' + worker],
               timeout=timeout).splitlines()


def command_error(error):
    stderr = getattr(error, 'stderr', None)
    return str(error) + (': ' + stderr.strip() if stderr else '')


@contextmanager
def cleanup_lease(path, owner_uid, deadline):
    """One worker's guard/watchdog cleanup lease; root may open the user's file."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid or info.st_mode & 0o077:
            raise ValueError('untrusted worker cleanup lock')
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError('worker cleanup lease unavailable within deadline')
                time.sleep(0.1)
        yield
    finally:
        os.close(fd)


def unit_state(unit, remaining):
    load = run(['systemctl', 'show', unit, '--property=LoadState', '--value'], timeout=remaining())
    active = run(['systemctl', 'show', unit, '--property=ActiveState', '--value'], timeout=remaining())
    return load, active


def unit_settled(load, active):
    return (load == 'not-found' and active == 'inactive') or (load != 'not-found' and active in ('inactive', 'failed'))


def stop_unit_if_present(unit, remaining):
    load, active = unit_state(unit, remaining)
    if unit_settled(load, active):
        return None
    stop_error = None
    try:
        run(['sudo', '-n', 'systemctl', 'stop', unit], timeout=remaining())
    except Exception as error:
        stop_error = command_error(error)
    # Even a successful stop must prove its final state. Transient units can
    # disappear while systemctl is answering and may return nonzero then.
    try:
        final = unit_state(unit, remaining)
    except Exception as state_error:
        return (stop_error + '; ' if stop_error else '') + 'final unit state unknown: ' + command_error(state_error)
    if unit_settled(*final):
        return None
    return (stop_error + '; ' if stop_error else 'stop returned without settling; ') + 'final unit state=' + repr(final)


def cleanup(worker, producer_units, anchor=None):
    failures = []
    deadline = time.monotonic() + 60
    def remaining():
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError('60-second targeted cleanup budget exhausted')
        return min(3, left)
    # Stop producers before containers; keep the independent watchdog alive.
    for unit in producer_units:
        try:
            failure = stop_unit_if_present(unit, remaining)
            if failure:
                failures.append('producer stop failed: ' + unit + ': ' + failure)
        except Exception as error:
            failures.append('producer state unknown: ' + unit + ': ' + command_error(error))
    removal_errors = {}
    def record_survivors():
        try:
            survivors = worker_containers(worker, timeout=3)
            if survivors:
                failures.append('labeled container survivors after cleanup: ' + repr(survivors) +
                                '; removal errors=' + repr({cid: removal_errors.get(cid) for cid in survivors}))
        except Exception as error:
            failures.append('container survivor state unknown: ' + command_error(error) +
                            '; removal errors=' + repr(removal_errors))
    while True:
        try:
            containers = worker_containers(worker, timeout=remaining())
        except TimeoutError:
            record_survivors()
            break
        except Exception as error:
            failures.append('container discovery/final state unknown: ' + command_error(error))
            break
        if not containers:
            break
        for cid in containers:
            try:
                run(['docker', 'rm', '-f', cid], timeout=remaining())
            except Exception as error:
                removal_errors[cid] = command_error(error)
        try:
            remaining()
            time.sleep(min(0.2, max(0, deadline - time.monotonic())))
        except TimeoutError:
            record_survivors()
            break
    if anchor:
        try:
            failure = stop_unit_if_present(anchor, remaining)
            if failure:
                failures.append('anchor stop failed: ' + failure)
        except Exception as error:
            failures.append('anchor state unknown: ' + command_error(error))
    for unit in producer_units:
        try:
            load, active = unit_state(unit, remaining)
            if not unit_settled(load, active):
                failures.append('producer service survivor: ' + unit + ': ' + repr((load, active)))
        except Exception as error:
            failures.append('producer survivor state unknown: ' + command_error(error))
    return failures


def populated_workers(parent):
    # A crashed frontend releases flock; kernel populations still reserve capacity.
    return [child.name for child in parent.glob('epic242-*.slice')
            if event_values((child / 'cgroup.events').read_text()).get('populated', 0)]


def admission_mutex():
    directory = Path('/tmp/epic242-native-slots')
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise ValueError('untrusted local slot directory')
    fd = os.open(directory / 'admission', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        os.close(fd)
        raise ValueError('another worker is entering admission; no automatic retry')
    return fd


def require_capacity(parent, available=None):
    workers = populated_workers(parent)
    if len(workers) >= 2:
        raise ValueError('two populated worker slices already exist, including stale runs')
    if available is not None:
        # Reserve the unconsumed headroom of already admitted workers too.
        reserved = sum(max(0, CAP - int((parent / name / 'memory.current').read_text()))
                       for name in workers)
        if available < CAP + FLOOR + reserved:
            raise ValueError('insufficient free memory for existing worker headroom plus new worker and floor')


def acquire_slot():
    directory = Path('/tmp/epic242-native-slots')
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise ValueError('untrusted local slot directory')
    for index in (1, 2):
        fd = os.open(directory / str(index), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            os.close(fd)
    raise ValueError('both local slots occupied; no automatic queue/retry')


def process_identity(pid):
    # /proc stat comm may contain spaces; field22 follows the final ')' delimiter.
    return Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()[19]


def watchdog(config_path):
    config = json.loads(Path(config_path).read_text())
    worker = identity(config['worker'])
    cg = Path(config['cgroup'])
    initial = event_values((cg / 'memory.events').read_text())
    reason = None
    while reason is None:
        try:
            try:
                parent_start = process_identity(config['parent_pid'])
            except FileNotFoundError:
                reason = 'parent guard identity missing'
                parent_start = None
            if reason is not None:
                pass
            elif parent_start != config['parent_start']:
                reason = 'parent guard identity changed'
            elif Path(config['closing']).exists():
                # Parent already stopped producers and proved no labeled survivors.
                pass
            else:
                cgroup_limits(cg)
                cgroup_limits(Path('/sys/fs/cgroup/epic242.slice'), AGGREGATE_CAP)
                reason = stop_reason(memory_available(), event_values((cg / 'memory.events').read_text()),
                                     initial, time.time(), config['deadline'])
        except Exception as error:
            reason = 'watchdog read/parent failure: ' + str(error)
        if reason is None:
            time.sleep(1)
    try:
        with cleanup_lease(config['cleanup_lock'], config['owner_uid'], time.monotonic() + 60):
            failures = cleanup(worker, config['units'], config['anchor'])
            result = {'reason': reason, 'cleanup_failures': failures, 'worker': worker,
                      'parent_pid': config['parent_pid'], 'parent_start': config['parent_start'],
                      'finished_at': time.time()}
            temporary = Path(config['result'] + '.tmp')
            temporary.write_text(json.dumps(result) + '\n')
            temporary.replace(config['result'])
    except Exception as error:
        failures = ['watchdog cleanup state unknown: ' + command_error(error)]
        Path(config['result']).write_text(json.dumps({'reason': reason, 'cleanup_failures': failures,
            'worker': worker, 'parent_pid': config['parent_pid'], 'parent_start': config['parent_start'],
            'finished_at': time.time()}) + '\n')
    return 1 if failures else 0


def execute(args):
    worker = identity(args.worker)
    if not args.admission_id or not args.command or args.command[0] == '--':
        raise ValueError('explicit parent admission ID and command required')
    if not 0 < args.seconds <= 2580:
        raise ValueError('deadline must be within existing43min CI bound; use300 for pilot')
    if os.environ.get('KICAD_CLI_BIN'):
        raise ValueError('native-binary fallback prohibited in bounded Docker mode')
    slice_unit = 'epic242-w' + worker.encode('ascii').hex() + '.slice'
    anchor = 'epic242-' + worker + '-anchor.service'
    checks = 'epic242-' + worker + '-checks.service'
    plan = {'admission_id': args.admission_id, 'worker': worker, 'sha': args.sha,
            'command': args.command, 'seconds': args.seconds, 'memory_max': CAP,
            'memory_swap_max': 0, 'aggregate_memory_max': AGGREGATE_CAP, 'free_floor': FLOOR, 'early_abort_free': ABORT_FREE,
            'slice': slice_unit, 'global_admission': 'parent excludes ALL other native jobs; local flock covers only this guard'}
    print(json.dumps({'proposal_plan': plan}), flush=True)
    if args.plan:
        return 0
    if not re.fullmatch(r'[0-9a-f]{40}', args.sha or ''):
        raise ValueError('full immutable reviewed SHA required')
    if Path('/proc/1/comm').read_text().strip() != 'systemd':
        raise ValueError('PID 1 must be systemd for independent watchdog and slice control')
    if run(['git', 'rev-parse', 'HEAD']) != args.sha:
        raise ValueError('checkout differs from admitted SHA')
    if run(['git', 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tracked checkout dirty')
    # This opt-in must be wired only by a separately reviewed run.sh patch.
    hook = Path('scripts/kicad/run.sh').read_bytes()
    required_hook = (b'--memory=6442450944', b'--memory-swap=6442450944', b'--cgroup-parent=',
                     b'EPIC242_NATIVE_DEADLINE', b'epic242.native.worker=', b'--kill-after=5s',
                     b'10.0.6', b'--pull=never')
    if any(token not in hook for token in required_hook) or not args.hook_sha256 or hashlib.sha256(hook).hexdigest() != args.hook_sha256:
        raise ValueError('exact reviewed Docker resource hook digest required; fail closed')
    local_docker()
    if getattr(args, 'harmless_fixture_image', None):
        require_harmless_fixture(args.harmless_fixture_image, args.command)
    else:
        require_local_image()
    if memory_available() < CAP + FLOOR:
        raise ValueError('less than8GiB available for6GiB worker+2GiB floor')
    # Refuse BEFORE claiming identity or entering cleanup: never delete another run.
    if worker_containers(worker):
        raise ValueError('worker label already exists; never overwrite prior run')
    for existing_unit in (anchor, checks, 'epic242-' + worker + '-watchdog.service'):
        if run(['systemctl', 'show', existing_unit, '--property=LoadState', '--value']) != 'not-found':
            raise ValueError('worker unit already exists; no cleanup of prior units')
    claim = Path('/tmp/epic242-' + worker + '-claim')
    if claim.exists() or claim.is_symlink():
        raise ValueError('worker identity already claimed; choose a new worker')
    for existing_path in (Path('/tmp/epic242-' + worker + '-watchdog.json'),
                          Path('/tmp/epic242-' + worker + '-watchdog.json.result')):
        if existing_path.exists() or existing_path.is_symlink():
            raise ValueError('watchdog identity already exists; choose a new worker')
    if Path(args.evidence).exists():
        raise ValueError('evidence destination exists; never overwrite')
    admission = admission_mutex()
    try:
        require_capacity(Path('/sys/fs/cgroup/epic242.slice'), memory_available())
        slot = acquire_slot()
    except Exception:
        os.close(admission)
        raise
    # Atomic identity claim closes the gap between refusing old labels and creating units.
    try:
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.write(fd, (args.sha + '\n').encode())
        os.close(fd)
    except Exception:
        os.close(slot)
        os.close(admission)
        raise
    units = []
    claimed = False
    watch_unit = 'epic242-' + worker + '-watchdog.service'
    private_dir = Path(tempfile.mkdtemp(prefix='epic242-' + worker + '-', dir='/tmp'))
    watch_config = private_dir / 'watchdog.json'
    watch_result = Path(str(watch_config) + '.result')
    closing = private_dir / 'closing'
    cleanup_lock = private_dir / 'cleanup.lock'
    lock_fd = os.open(cleanup_lock, os.O_CREAT | os.O_EXCL | os.O_RDONLY | os.O_NOFOLLOW, 0o600)
    os.close(lock_fd)
    process = None
    evidence = {'plan': plan, 'samples': [], 'status': 'FAIL / NOT ACCEPTED'}
    observed_containers = set()
    interrupted = []
    def terminate(signum, frame):
        interrupted.append(signum)
    old_handlers = {sig: signal.signal(sig, terminate) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        # Identity was atomically reserved; clean partially started units too.
        claimed = True
        # Only the anchor starts before caps; no native command may run yet.
        run(['sudo', '-n', 'systemd-run', '--unit=' + anchor, '--slice=' + slice_unit,
             '--property=KillMode=control-group', '--property=TimeoutStopSec=2s',
             '--property=RuntimeMaxSec=' + str(args.seconds + 120), '/usr/bin/sleep', 'infinity'])
        units.append(anchor)
        run(['sudo', '-n', 'systemctl', 'set-property', '--runtime', slice_unit,
             'MemoryAccounting=yes', 'MemoryMax=' + str(CAP), 'MemorySwapMax=0'])
        run(['sudo', '-n', 'systemctl', 'set-property', '--runtime', 'epic242.slice',
             'MemoryAccounting=yes', 'MemoryMax=' + str(AGGREGATE_CAP), 'MemorySwapMax=0'])
        cgroup_limits(Path('/sys/fs/cgroup/epic242.slice'), AGGREGATE_CAP)
        cg = run(['systemctl', 'show', slice_unit, '--property=ControlGroup', '--value'])
        if cg != '/epic242.slice/' + slice_unit:
            raise ValueError('worker slice path differs from dedicated aggregate parent')
        cgroup = Path('/sys/fs/cgroup') / cg.lstrip('/')
        cgroup_limits(cgroup)
        os.close(admission)
        admission = None
        events = event_values((cgroup / 'memory.events').read_text())
        initial = events.copy()
        watch_data = {'worker': worker, 'parent_pid': os.getpid(), 'parent_start': process_identity(os.getpid()),
                      'deadline': time.time() + args.seconds, 'cgroup': str(cgroup),
                      'units': [checks], 'anchor': anchor, 'closing': str(closing), 'result': str(watch_result),
                      'cleanup_lock': str(cleanup_lock), 'owner_uid': os.getuid()}
        # O_EXCL: no reuse/overwrite of watchdog configuration.
        with watch_config.open('x') as output:
            json.dump(watch_data, output)
        run(['sudo', '-n', 'systemd-run', '--unit=' + watch_unit,
             '--property=RuntimeMaxSec=' + str(args.seconds + 120), '--property=TimeoutStopSec=2s',
             sys.executable, str(Path(__file__).resolve()), '--watchdog', str(watch_config)])
        command = ['sudo', '-n', 'systemd-run', '--wait', '--pipe', '--collect',
                   '--unit=' + checks, '--slice=' + slice_unit, '--property=KillMode=control-group',
                   '--property=RuntimeMaxSec=' + str(args.seconds), '--property=TimeoutStopSec=2s',
                   '--property=User=' + str(os.getuid()), '--property=WorkingDirectory=' + str(Path.cwd()),
                   '--setenv=EPIC242_NATIVE_SLICE=' + slice_unit,
                   '--setenv=EPIC242_NATIVE_WORKER=' + worker,
                   '--setenv=EPIC242_NATIVE_DEADLINE=' + str(int(time.time()) + args.seconds),
                   '--setenv=PATH=' + os.environ['PATH'], '--', *args.command]
        units.insert(0, checks)
        process = subprocess.Popen(command)
        started = time.monotonic()
        while True:
            if run(['systemctl', 'show', watch_unit, '--property=ActiveState', '--value']) != 'active':
                raise ValueError('independent watchdog not active')
            available = memory_available()
            events = event_values((cgroup / 'memory.events').read_text())
            elapsed = time.monotonic() - started
            evidence['samples'].append({'seconds': elapsed, 'available': available,
                                        'worker_current': int((cgroup / 'memory.current').read_text()), 'events': events})
            reason = stop_reason(available, events, initial, elapsed, args.seconds)
            if interrupted:
                reason = 'signal ' + str(interrupted[-1])
            cgroup_limits(cgroup)
            cgroup_limits(Path('/sys/fs/cgroup/epic242.slice'), AGGREGATE_CAP)
            for cid in worker_containers(worker):
                inspected = json.loads(run(['docker', 'inspect', cid]))[0]
                if inspected['State']['Running']:
                    pid = inspected['State']['Pid']
                    docker_membership(inspected, Path('/proc/' + str(pid) + '/cgroup').read_text(), cg)
                    observed_containers.add(cid)
                    if getattr(args, 'harmless_fixture_image', None):
                        ready_file = private_dir / 'membership.json'
                        temporary_ready = private_dir / 'membership.tmp'
                        temporary_ready.write_text(json.dumps({'worker': worker, 'sha': args.sha,
                            'parent_pid': os.getpid(), 'parent_start': process_identity(os.getpid()),
                            'image_id': args.harmless_fixture_image, 'container_id': cid,
                            'slice_path': cg, 'verified_at': time.time()}) + '\n')
                        temporary_ready.replace(ready_file)
            if reason:
                raise ValueError(reason)
            code = process.poll()
            if code is not None:
                evidence['exit_code'] = code
                if code:
                    raise ValueError('native command nonzero exit')
                break
            time.sleep(1)
        if not observed_containers:
            raise ValueError('no running Docker container membership observed; proof incomplete')
        evidence['observed_containers'] = sorted(observed_containers)
        evidence['peak'] = int((cgroup / 'memory.peak').read_text())
        evidence['status'] = 'COMMAND PASS ONLY; native acceptance requires exact complete evidence'
    except Exception as error:
        evidence['reason'] = str(error)
    finally:
        evidence['observed_containers'] = sorted(observed_containers)
        failures = []
        if claimed:
            try:
                with cleanup_lease(str(cleanup_lock), os.getuid(), time.monotonic() + 60):
                    failures = cleanup(worker, [checks] if checks in units else [])
                    if not failures and evidence.get('reason') != 'whole-command deadline':
                        closing.write_text('producer and labeled container cleanup complete\n')
                        failure = stop_unit_if_present(anchor, lambda: 3)
                        if failure:
                            failures.append('anchor stop failed: ' + failure)
            except Exception as error:
                failures.append('guard cleanup state unknown: ' + command_error(error))
            if not failures:
                # A deadline watchdog may be waiting for the lease. Let it record
                # its own cause before stopping it, without holding the lock.
                if evidence.get('reason') == 'whole-command deadline':
                    watch_deadline = time.monotonic() + 15
                    while not watch_result.exists() and time.monotonic() < watch_deadline:
                        time.sleep(0.1)
                    if not watch_result.exists():
                        failures.append('deadline watchdog result missing after cleanup')
                if not failures:
                    try:
                        if evidence.get('reason') == 'whole-command deadline':
                            failure = stop_unit_if_present(anchor, lambda: 3)
                            if failure:
                                failures.append('anchor stop failed: ' + failure)
                        if not failures:
                            failure = stop_unit_if_present(watch_unit, lambda: 3)
                            if failure:
                                failures.append('watchdog stop failed: ' + failure)
                    except Exception as error:
                        failures.append('watchdog stop state unknown: ' + command_error(error))
        if watch_result.exists():
            evidence['watchdog'] = json.loads(watch_result.read_text())
            evidence['status'] = 'FAIL / WATCHDOG TERMINATION'
        if process is not None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                failures.append('systemd-run frontend required kill')
        if failures:
            evidence['cleanup_failures'] = failures
            evidence['status'] = 'FAIL / CLEANUP BLOCKER'
        if admission is not None:
            os.close(admission)
        os.close(slot)
        for sig, old in old_handlers.items():
            signal.signal(sig, old)
        destination = Path(args.evidence)
        if destination.exists():
            raise ValueError('evidence destination exists; never overwrite')
        destination.write_text(json.dumps(evidence, indent=2) + '\n')
    return 0 if evidence['status'].startswith('COMMAND PASS') else 1


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--watchdog':
        return watchdog(sys.argv[2])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hook-sha256', help='Exact SHA256 of separately reviewed installed resource hook')
    parser.add_argument('--harmless-fixture-image', help='Only the reviewed non-native fixture runner; native image preflight not required')
    parser.add_argument('--plan', action='store_true', help='No commands/reads of cgroups/Docker; print proposed invocation')
    parser.add_argument('--admission-id', required=True)
    parser.add_argument('--worker', required=True)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--seconds', required=True, type=int)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ['--']:
        args.command = args.command[1:]
    try:
        return execute(args)
    except Exception as error:
        print('GUARD REFUSAL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
