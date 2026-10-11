"""Read-only capability receipt. Never starts a worker or replaces missing controls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

method, evidence = (Path(x).resolve() for x in sys.argv[1:])
evidence.mkdir(exist_ok=False)
def run():
    packet = json.loads((Path(__file__).parents[1] / 'minimum-native-request.json').read_text())
    checks = {}


    def command(name, argv):
        try:
            p = subprocess.run(argv, cwd=method, text=True, capture_output=True, timeout=30)
            checks[name] = {'argv': argv, 'returncode': p.returncode,
                            'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}
            return p.stdout.strip() if p.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks[name] = {'argv': argv, 'error': str(exc)}
            return None


    failures = []
    head = command('head', ['git', 'rev-parse', 'HEAD'])
    if head != packet['source_commit']:
        failures.append('exact method HEAD mismatch')
    if command('tracked_status', ['git', 'status', '--porcelain', '--untracked-files=no']) != '':
        failures.append('method checkout not tracked-clean')
    for name, expected in packet['input_file_sha256'].items():
        actual = hashlib.sha256((method/name).read_bytes()).hexdigest()
        checks[name] = actual
        if actual != expected:
            failures.append('source digest mismatch: '+name)
    checks['pid1'] = Path('/proc/1/comm').read_text().strip()
    if checks['pid1'] != 'systemd':
        failures.append('PID1 is not systemd')
    guard = Path.home()/'.codex/scripts/heavy-guard.sh'
    checks['outer_heavy_guard'] = {'path': str(guard), 'readable': os.access(guard, os.R_OK)}
    if not os.access(guard, os.R_OK):
        failures.append('required outer heavy-guard missing or unreadable; no replacement permitted')
    else:
        checks['outer_heavy_guard']['sha256'] = hashlib.sha256(guard.read_bytes()).hexdigest()
        checks['outer_heavy_guard']['applicability'] = 'PRESENT; requires independent instruction/source review before use'
    for name in ('docker', 'systemd-run', 'systemctl', 'sudo', 'python3'):
        checks['binary_'+name] = shutil.which(name)
        if not shutil.which(name):
            failures.append('missing binary '+name)
    checks['python_actual'] = sys.executable
    checks['cgroup_controllers'] = Path('/sys/fs/cgroup/cgroup.controllers').read_text().strip() if Path('/sys/fs/cgroup/cgroup.controllers').exists() else None
    if 'memory' not in (checks['cgroup_controllers'] or '').split():
        failures.append('cgroupv2 memory controller unavailable')
    if command('sudo', ['sudo', '-n', 'true']) is None:
        failures.append('noninteractive sudo unavailable')
    info = command('docker_info', ['docker', 'info', '--format', '{{json .}}'])
    if info:
        d = json.loads(info)
        checks['docker_summary'] = {k:d.get(k) for k in ('CgroupDriver','CgroupVersion','ServerVersion')}
        if d.get('CgroupDriver') != 'systemd' or str(d.get('CgroupVersion')) != '2':
            failures.append('Docker requires systemd cgroupv2')
    else:
        failures.append('Docker unavailable')
    if command('pinned_image_local', ['docker', 'image', 'inspect', packet['image'], '--format', '{{json .RepoDigests}}']) is None:
        failures.append('exact pinned image absent locally; no image preparation attempted')
    receipt = {'admission_id':'epic242-o1-k1402-route-20261011-1347',
               'reserved_worker':'o1-k1402-route-1347-a', 'method_sha':head,
               'status':'CAPABILITY_BLOCKED' if failures else 'CAPABILITY_REVIEW_READY',
               'failures':failures, 'checks':checks,
               'route_status':'NOT_STARTED', 'native_workers_started':0,
               'docker_probe_containers_started':0, 'artifact_authentication':'NOT_STARTED',
               'fixture_preparation':'NOT_STARTED', 'python_numerical_binding':'NOT_STARTED',
               'cleanup':{'worker_or_container_created':False, 'resource_reservation_releasable':True},
               'evidence_policy':'Native guard --evidence must be a NEW JSON FILE, never a directory.',
               'next_step':'Report capabilities to parent; no retries, replacement controls or additional phases.'}
    (evidence/'capability-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('status','failures','route_status','native_workers_started')}, indent=2))
    return 1 if failures else 0


try:
    code = run()
except Exception as exc:
    receipt = {'admission_id':'epic242-o1-k1402-route-20261011-1347',
               'status':'CAPABILITY_BLOCKED', 'error':str(exc),
               'route_status':'NOT_STARTED', 'native_workers_started':0,
               'docker_probe_containers_started':0,
               'cleanup':{'worker_or_container_created':False,
                          'resource_reservation_releasable':True}}
    (evidence/'capability-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))
    code = 1
sys.exit(code)
