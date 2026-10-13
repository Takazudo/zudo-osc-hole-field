#!/usr/bin/env python3
"""Unwired proposal: admitted Linux/systemd/Docker worker guard. No auto-admission."""
import argparse
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

GIB = 1024 ** 3
CAP = 6 * GIB
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


def worker_containers(worker):
    return run(['docker', 'ps', '-aq', '--filter', 'label=epic242.native.worker=' + worker]).splitlines()


def cleanup(worker, units):
    failures = []
    for unit in units:
        try:
            state = run(['systemctl', 'show', unit, '--property=LoadState', '--value'], timeout=3)
            if state != 'not-found':
                run(['sudo', '-n', 'systemctl', 'stop', unit], timeout=3)
        except Exception as error:
            failures.append(str(error))
    try:
        for cid in worker_containers(worker):
            run(['docker', 'rm', '-f', cid], timeout=3)
    except Exception as error:
        failures.append(str(error))
    return failures


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
            if process_identity(config['parent_pid']) != config['parent_start']:
                reason = 'parent guard identity changed'
            else:
                reason = stop_reason(memory_available(), event_values((cg / 'memory.events').read_text()),
                                     initial, time.time(), config['deadline'])
        except Exception as error:
            reason = 'watchdog read/parent failure: ' + str(error)
        if reason is None:
            time.sleep(1)
    failures = cleanup(worker, config['units'])
    Path(config['result']).write_text(json.dumps({'reason': reason, 'cleanup_failures': failures}) + '\n')
    return 1 if failures else 0


def execute(args):
    worker = identity(args.worker)
    if not args.admission_id or not args.command or args.command[0] == '--':
        raise ValueError('explicit parent admission ID and command required')
    if not 0 < args.seconds <= 2580:
        raise ValueError('deadline must be within existing43min CI bound; use300 for pilot')
    if os.environ.get('KICAD_CLI_BIN'):
        raise ValueError('native-binary fallback prohibited in bounded Docker mode')
    slice_unit = 'epic242-' + worker + '.slice'
    anchor = 'epic242-' + worker + '-anchor.service'
    checks = 'epic242-' + worker + '-checks.service'
    plan = {'admission_id': args.admission_id, 'worker': worker, 'sha': args.sha,
            'command': args.command, 'seconds': args.seconds, 'memory_max': CAP,
            'memory_swap_max': 0, 'free_floor': FLOOR, 'early_abort_free': ABORT_FREE,
            'slice': slice_unit, 'global_admission': 'parent excludes ALL other native jobs; local flock covers only this guard'}
    print(json.dumps({'proposal_plan': plan}), flush=True)
    if args.plan:
        return 0
    if not re.fullmatch(r'[0-9a-f]{40}', args.sha or ''):
        raise ValueError('full immutable reviewed SHA required')
    if run(['git', 'rev-parse', 'HEAD']) != args.sha:
        raise ValueError('checkout differs from admitted SHA')
    if run(['git', 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tracked checkout dirty')
    # This opt-in must be wired only by a separately reviewed run.sh patch.
    hook = Path('scripts/kicad/run.sh').read_bytes()
    required_hook = (b'--memory=6442450944', b'--cgroup-parent=', b'EPIC242_NATIVE_DEADLINE', b'epic242.native.worker=')
    if any(token not in hook for token in required_hook) or not args.hook_sha256 or hashlib.sha256(hook).hexdigest() != args.hook_sha256:
        raise ValueError('exact reviewed Docker resource hook digest required; fail closed')
    local_docker()
    if memory_available() < CAP + FLOOR:
        raise ValueError('less than8GiB available for6GiB worker+2GiB floor')
    # Refuse BEFORE claiming identity or entering cleanup: never delete another run.
    if worker_containers(worker):
        raise ValueError('worker label already exists; never overwrite prior run')
    for existing_unit in (anchor, checks, 'epic242-' + worker + '-watchdog.service'):
        if run(['systemctl', 'show', existing_unit, '--property=LoadState', '--value']) != 'not-found':
            raise ValueError('worker unit already exists; no cleanup of prior units')
    for existing_path in (Path('/tmp/epic242-' + worker + '-watchdog.json'), Path('/tmp/epic242-' + worker + '-watchdog.json.result')):
        if existing_path.exists():
            raise ValueError('watchdog identity already exists; choose a new worker')
    if Path(args.evidence).exists():
        raise ValueError('evidence destination exists; never overwrite')
    slot = acquire_slot()
    units = []
    claimed = False
    watch_unit = 'epic242-' + worker + '-watchdog.service'
    watch_config = Path('/tmp/epic242-' + worker + '-watchdog.json')
    watch_result = Path(str(watch_config) + '.result')
    process = None
    evidence = {'plan': plan, 'samples': [], 'status': 'FAIL / NOT ACCEPTED'}
    interrupted = []
    def terminate(signum, frame):
        interrupted.append(signum)
    old_handlers = {sig: signal.signal(sig, terminate) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        # Anchor creates the dedicated slice before configuring its aggregate limit.
        run(['sudo', '-n', 'systemd-run', '--unit=' + anchor, '--slice=' + slice_unit,
             '--property=KillMode=control-group', '/usr/bin/sleep', 'infinity'])
        claimed = True
        units.append(anchor)
        run(['sudo', '-n', 'systemctl', 'set-property', '--runtime', slice_unit,
             'MemoryAccounting=yes', 'MemoryMax=' + str(CAP), 'MemorySwapMax=0'])
        cg = run(['systemctl', 'show', slice_unit, '--property=ControlGroup', '--value'])
        cgroup = Path('/sys/fs/cgroup') / cg.lstrip('/')
        if int((cgroup / 'memory.max').read_text()) != CAP or (cgroup / 'memory.swap.max').read_text().strip() != '0':
            raise ValueError('shared slice cap verification failed')
        events = event_values((cgroup / 'memory.events').read_text())
        initial = events.copy()
        watch_data = {'worker': worker, 'parent_pid': os.getpid(), 'parent_start': process_identity(os.getpid()),
                      'deadline': time.time() + args.seconds, 'cgroup': str(cgroup),
                      'units': [checks, anchor], 'result': str(watch_result)}
        # O_EXCL: no reuse/overwrite of watchdog configuration.
        with watch_config.open('x') as output:
            json.dump(watch_data, output)
        run(['sudo', '-n', 'systemd-run', '--unit=' + watch_unit,
             '--property=RuntimeMaxSec=' + str(args.seconds + 120),
             sys.executable, str(Path(__file__).resolve()), '--watchdog', str(watch_config)])
        command = ['sudo', '-n', 'systemd-run', '--wait', '--pipe', '--collect',
                   '--unit=' + checks, '--slice=' + slice_unit, '--property=KillMode=control-group',
                   '--property=RuntimeMaxSec=' + str(args.seconds),
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
            for cid in worker_containers(worker):
                inspected = json.loads(run(['docker', 'inspect', cid]))[0]
                if inspected['State']['Running']:
                    pid = inspected['State']['Pid']
                    docker_membership(inspected, Path('/proc/' + str(pid) + '/cgroup').read_text(), cg)
            if reason:
                raise ValueError(reason)
            code = process.poll()
            if code is not None:
                evidence['exit_code'] = code
                if code:
                    raise ValueError('native command nonzero exit')
                break
            time.sleep(1)
        evidence['peak'] = int((cgroup / 'memory.peak').read_text())
        evidence['status'] = 'COMMAND PASS ONLY; native acceptance requires exact complete evidence'
    except Exception as error:
        evidence['reason'] = str(error)
    finally:
        failures = cleanup(worker, units) if claimed else []
        if claimed:
            try:
                if worker_containers(worker):
                    failures.append('labeled container survivors after cleanup')
                # Stop independent watchdog LAST, after driver stopped and containers gone.
                run(['sudo', '-n', 'systemctl', 'stop', watch_unit], timeout=3)
            except Exception as error:
                failures.append(str(error))
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
