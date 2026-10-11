#!/usr/bin/env python3
"""Exclusive #245 reviewed-fixture before-board settle; never routes or adopts."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.kicad import native_resource_guard as guard

ROOT = Path(__file__).resolve().parents[2]
PILOTS = ('two-A', 'two-B', 'three-A', 'three-B', 'three-C')


def output_path(env):
    pilot = env.get('SETTLE_PILOT', '')
    run_id, attempt = env.get('GITHUB_RUN_ID', ''), env.get('GITHUB_RUN_ATTEMPT', '')
    if pilot not in PILOTS or not run_id.isdecimal() or not attempt.isdecimal():
        raise ValueError('reviewed pilot and unique Actions run/attempt required')
    return ROOT/'design/partition/core-split/candidates/pilots/generated'/f'decision-{pilot}-native-{run_id}-{attempt}'


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(env):
    output_path(env)
    commit = env.get('REVIEWED_COMMIT', '')
    hook = env.get('REVIEWED_HOOK_SHA256', '')
    if not re.fullmatch('[0-9a-f]{40}', commit) or guard.run(['git', 'rev-parse', 'HEAD']) != commit:
        raise ValueError('exact reviewed checkout required')
    if env.get('GITHUB_SHA') != commit:
        raise ValueError('dispatch workflow SHA must equal reviewed checkout')
    if not re.fullmatch('[0-9a-f]{64}', hook) or sha(ROOT/'scripts/kicad/run.sh') != hook:
        raise ValueError('reviewed hook mismatch')
    guard.identity(env.get('PARENT_ADMISSION_ID', ''))
    if env.get('REQUEST_BOARD') != 'osc-core' or env.get('CONFLICTING_MODES') != 'false':
        raise ValueError('only exclusive osc-core settle mode permitted')
    if guard.run(['git', 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tracked checkout dirty')
    return commit, hook


def verify_tree(directory, files):
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if actual != set(files) or any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('input tree membership differs or contains symlink')
    for name, expected in files.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(directory/name) != expected:
            raise ValueError('input hash differs: '+name)


def snapshot(output, destination, pilot):
    manifest = json.loads((output/'sha256.json').read_text())
    if len(manifest) != 293:
        raise ValueError('expected complete 293-file fixture')
    verify_tree(output, manifest | {'sha256.json': sha(output/'sha256.json')})
    seals = json.loads((ROOT/'design/partition/core-split/candidates/pilots/source-fixture-seals.json').read_text())[pilot]['files_sha256']
    if len(seals) != 291 or any(manifest.get(name) != value for name, value in seals.items()):
        raise ValueError('portable fixture seals differ')
    shutil.copytree(output, destination)
    files = manifest | {'sha256.json': sha(output/'sha256.json')}
    verify_tree(destination, files)
    for p in destination.rglob('*'):
        p.chmod(0o555 if p.is_dir() else 0o444)
    destination.chmod(0o555)
    return files


def preparation_stop(available, daemon_bytes, elapsed):
    if available <= guard.ABORT_FREE:
        return 'host free-memory early abort'
    if daemon_bytes >= guard.CAP:
        return 'whole Docker daemon accounting exceeds 6GiB preparation ceiling'
    if elapsed >= 300:
        return '300-second preparation deadline'
    return None


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise TimeoutError('300-second preparation deadline')
    return min(20, value)


def bounded_run(command, deadline):
    return guard.run(command, timeout=remaining(deadline))


def daemon_cgroup(deadline=None):
    call = guard.run if deadline is None else lambda command: bounded_run(command, deadline)
    pid = int(call(['systemctl', 'show', 'docker.service', '--property=MainPID', '--value']))
    if pid <= 0:
        raise ValueError('Docker daemon PID unavailable')
    paths = [line.split(':', 2)[2] for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if line.startswith('0::')]
    if len(paths) != 1 or paths[0] == '/' or '..' in Path(paths[0]).parts:
        raise ValueError('dedicated Docker daemon cgroup unavailable')
    return pid, Path('/sys/fs/cgroup')/paths[0].lstrip('/')



def accounting_groups(deadline=None):
    call = guard.run if deadline is None else lambda command: bounded_run(command, deadline)
    pid, docker = daemon_cgroup(deadline)
    groups = [docker]
    # containerd may be a separate system service, including image snapshotter
    # workers; charge the complete service, never merely the Docker API client.
    load = call(['systemctl','show','containerd.service','--property=LoadState','--value'])
    if load != 'not-found':
        path = call(['systemctl','show','containerd.service','--property=ControlGroup','--value'])
        if not path or path == '/' or '..' in Path(path).parts:
            raise ValueError('containerd accounting cgroup unknown')
        groups.append(Path('/sys/fs/cgroup')/path.lstrip('/'))
    groups = sorted(set(groups), key=lambda p: len(p.parts))
    groups = [p for p in groups if not any(p != q and p.is_relative_to(q) for q in groups)]
    # Verify all visible backend helpers are contained in charged groups. Unknown
    # backends/remote storage are refused below; disappeared PIDs are harmless.
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            name = (process/'comm').read_text().strip()
            if not name.startswith(('containerd','runc','dockerd')):
                continue
            paths = [line.split(':',2)[2] for line in (process/'cgroup').read_text().splitlines() if line.startswith('0::')]
            if len(paths) != 1 or not any((Path('/sys/fs/cgroup')/paths[0].lstrip('/')).is_relative_to(g) for g in groups):
                raise ValueError('unaccounted Docker backend: '+name)
        except FileNotFoundError:
            continue
    for group in groups:
        for field in ('memory.current','memory.events','memory.max'):
            if not (group/field).is_file():
                raise ValueError('missing backend memory accounting: '+str(group/field))
    return pid, groups

def prepare_image(evidence):
    """Bound pull time; observe entire daemon, not just the tiny Docker client.

    No daemon/service configuration changes. Sampling is an abort threshold,
    not a kernel hard cap on a pre-existing daemon. Failure blocks native start.
    """
    start = time.monotonic()
    deadline = start + 300
    guard.local_docker()
    remaining(deadline)
    image_match = re.search(r"^KICAD_IMAGE='(kicad/kicad@sha256:[0-9a-f]{64})'$", (ROOT/'scripts/kicad/pin.env').read_text(), re.M)
    if not image_match:
        raise ValueError('invalid pinned image')
    image = image_match[1]
    info = json.loads(bounded_run(['docker','info','--format','{{json .}}'], deadline))
    if info.get('Driver') not in ('overlay2','overlayfs') or info.get('Plugins',{}).get('Volume',[]) not in ([],['local']):
        raise ValueError('unreviewed Docker storage backend')
    pid, groups = accounting_groups(deadline)
    initial_events = {str(g): guard.event_values((g/'memory.events').read_text()) for g in groups}
    receipt = {'image': image, 'daemon_pid': pid, 'backend_cgroups': [str(g) for g in groups],
               'backend_memory_max': {str(g): (g/'memory.max').read_text().strip() for g in groups},
               'accounting': 'sum of disjoint Docker/containerd service cgroups and verified contained backend helpers; sampled abort threshold, not daemon hard-cap enforcement',
               'seconds_limit': 300, 'samples': [], 'status': 'STARTED'}
    process = None
    try:
        if guard.memory_available() < guard.CAP + guard.FLOOR:
            raise ValueError('less than8GiB free before preparation')
        remaining(deadline)
        with (evidence/'image-pull.log').open('w') as log:
            process = subprocess.Popen(['docker', 'pull', image], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                elapsed = time.monotonic()-start
                available = guard.memory_available()
                usage = sum(int((g/'memory.current').read_text()) for g in groups)
                events = {str(g): guard.event_values((g/'memory.events').read_text()) for g in groups}
                receipt['samples'].append({'elapsed': elapsed, 'daemon_bytes': usage, 'free_bytes': available})
                reason = preparation_stop(available, usage, elapsed)
                if any(events[str(g)].get(k,0) > initial_events[str(g)].get(k,0) for g in groups for k in ('oom','oom_kill')):
                    reason = 'Docker daemon OOM event'
                if accounting_groups(deadline) != (pid,groups):
                    reason = 'Docker daemon identity changed'
                remaining(deadline)
                if reason:
                    raise ValueError(reason)
                result = process.poll()
                if result is not None:
                    if result:
                        raise ValueError('digest-pinned pull failed: '+str(result))
                    break
                time.sleep(.2)
        metadata = json.loads(bounded_run(['docker','image','inspect',image],deadline))[0]
        remaining(deadline)
        if image not in metadata.get('RepoDigests', []):
            raise ValueError('pinned RepoDigest not authenticated')
        receipt.update(status='PASS', image_id=metadata['Id'], repo_digests=metadata['RepoDigests'])
        return receipt
    except Exception as error:
        receipt.update(status='BLOCKED', error=str(error))
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        receipt['pull_client_exit'] = None if process is None else process.returncode
        receipt['failure_scope'] = 'No native start after preparation failure; daemon is not stopped or reconfigured. Client cancellation does not prove absence of residual daemon work.'
        write(evidence/'image-preparation.json', receipt)


def execute(env):
    commit, hook = validate(env)
    pilot = env['SETTLE_PILOT']
    output = output_path(env)
    evidence = Path(env['RUNNER_TEMP'])/'epic242-candidate-settle-only'
    evidence.mkdir(exist_ok=True)
    if (evidence/'pilot.json').exists():
        raise ValueError('pilot receipt already exists')
    receipt = {'source_sha': commit, 'hook_sha256': hook, 'admission_id': env['PARENT_ADMISSION_ID'],
               'pilot': pilot, 'scope': 'one reviewed complete-fixture before-board settle only; NOT COMPLETE ACCEPTANCE',
               'subordinate_logging': 'Driver stdout/stderr retained; check internally captures successful subordinate output. Raw DRC can be capped; uncapped warning audit NOT RUN.',
               'status': 'STARTED'}
    files = None
    try:
        with (evidence/'dependencies.log').open('w') as log:
            subprocess.run([sys.executable,'-m','pip','install','-r','scripts/pcbgen/numerical-requirements.txt'], stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        prepare_image(evidence)
        with (evidence/'materialize.log').open('w') as log:
            subprocess.run([sys.executable,'scripts/partition/core_split_candidates.py','materialize','--pilot',pilot,'--output',str(output.relative_to(ROOT))], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        files = snapshot(output, evidence/'input-snapshot', pilot)
        write(evidence/'input-snapshot-sha256.json',files)
        worker = guard.identity('settle-'+pilot.lower()+'-'+env['GITHUB_RUN_ID']+'-'+env['GITHUB_RUN_ATTEMPT'])
        command = [sys.executable,'scripts/kicad/native_resource_guard.py','--admission-id',env['PARENT_ADMISSION_ID'],
                   '--worker',worker,'--sha',commit,'--hook-sha256',hook,'--seconds','300',
                   '--evidence',str(evidence/'guard.json'),'--',sys.executable,
                   'scripts/partition/core_split_candidates.py','settle','--board',str((output/'before/osc-core.kicad_pcb').relative_to(ROOT))]
        receipt['command'] = command
        write(evidence/'pilot.json',receipt)
        with (evidence/'settle-driver.log').open('w') as log:
            # Guard owns the native deadline/watchdog/cleanup. Do not kill the
            # guard before its bounded cleanup can publish the negative receipt.
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        receipt['exit_code'] = result.returncode
        receipt['status'] = 'SETTLE COMMAND SUCCEEDED; NOT COMPLETE ACCEPTANCE' if result.returncode == 0 else 'NEGATIVE / INCOMPLETE'
        return result.returncode
    except Exception as error:
        receipt.update(status='BLOCKED',error=str(error))
        return 1
    finally:
        if output.exists():
            try:
                shutil.copytree(output,evidence/'working-result')
            except Exception as error:
                receipt.update(status='EVIDENCE INTEGRITY FAILURE',retention_error=str(error))
                write(evidence/'pilot.json',receipt)
                raise
        if files is not None:
            try:
                verify_tree(evidence/'input-snapshot',files)
                receipt['snapshot_unchanged'] = True
            except Exception as error:
                receipt.update(snapshot_unchanged=False,status='EVIDENCE INTEGRITY FAILURE',error=str(error))
                write(evidence/'pilot.json',receipt)
                raise
        write(evidence/'pilot.json',receipt)


if __name__ == '__main__':
    os.chdir(ROOT)
    if sys.argv[1:] == ['validate']:
        validate(os.environ)
    elif sys.argv[1:] == ['run']:
        sys.exit(execute(os.environ))
    else:
        raise SystemExit('usage: settle_only_pilot.py validate|run')
