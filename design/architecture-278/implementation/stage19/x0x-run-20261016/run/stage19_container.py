"""Future admitted native entry point. Importing this module never runs commands."""
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

import stage19_protocol as p


def save(root, name, value):
    (root / name).write_bytes(p.json_bytes(value))


def collect_capability(proposal, out):
    cg = Path('/sys/fs/cgroup')
    fs = os.statvfs(out)
    return {**{k: proposal[k] for k in ('run_id', 'nonce', 'source_commit', 'verification_commit', 'request_sha256')},
        'limits': {k: (cg / k).read_text().strip() for k in ('cpu.max', 'memory.max', 'memory.swap.max', 'pids.max')},
        'output_capacity_bytes': fs.f_blocks * fs.f_frsize, 'interfaces': sorted(os.listdir('/sys/class/net')),
        'uid': os.getuid(), 'gid': os.getgid(), 'groups': os.getgroups(),
        'readonly': {name: (not os.path.exists(name) if name == '/dev/shm' else False) or bool(os.statvfs(name).f_flag & os.ST_RDONLY) for name in ('/', '/inputs/stage17/generated', '/inputs/stage18/generated', '/control', '/dev/shm')},
        'other_path_writable': {name: os.access(name, os.W_OK) for name in ('/dev', '/dev/mqueue', '/etc/hosts', '/etc/hostname', '/etc/resolv.conf')},
        'mountinfo': Path('/proc/self/mountinfo').read_text()}


def verify_inputs(control, inputs, proposal):
    request = p.load(control / 'request.json')
    p.need(p.digest(control / 'request.json') == proposal['request_sha256'], 'request drift')
    p.need(request['source_commit'] == p.SOURCE == proposal['source_commit'] and request['verification_commit'] == proposal['verification_commit'], 'commit drift')
    binding = p.load(control / 'input-binding.json')
    p.need(binding == request['input_files_sha256'] and len(binding) == 72, 'exact 72-input binding required')
    p.need(p.inventory(inputs) == binding, 'input omission/substitution/extra file')
    p.need(set(request['runtime_sha256']) == set(p.RUNTIME), 'runtime inventory mismatch')
    for name, sha in request['runtime_sha256'].items():
        p.need(not (control / name).is_symlink() and p.digest(control / name) == sha, 'runtime drift: ' + name)


def execute_once(control, out, proposal, started, records, *, runner=subprocess.run, clock=time.monotonic, wall=time.time):
    """Dependency injection permits tests without launching KiCad or containers."""
    p.admission(control, proposal, wall())
    p.need(clock() - started < 300, 'late admission')
    with (out / 'consumed.json').open('xb') as f:
        f.write(p.json_bytes({**proposal, 'consumed_at_unix': wall(), 'automatic_retry': False, 'admission_sha256': p.digest(control / 'admit.json'), 'capability_sha256': p.digest(control / 'capability.json')}))
        f.flush(); os.fsync(f.fileno())
    for index, argv in enumerate(p.COMMANDS):
        remaining = 500 - (clock() - started)
        p.need(remaining > 0, 'native time budget exhausted')
        record = {'argv': argv, 'started_elapsed_seconds': clock() - started, 'exit': None}
        records.append(record); save(out, 'commands.json', records)
        with (out / f'command-{index}.stdout').open('xb') as stdout, (out / f'command-{index}.stderr').open('xb') as stderr:
            try:
                result = runner(argv, stdout=stdout, stderr=stderr, timeout=remaining)
                record['exit'] = result.returncode
            finally:
                record['elapsed_seconds'] = clock() - started - record['started_elapsed_seconds']
                save(out, 'commands.json', records)
        if record['exit'] != 0:
            return 'NATIVE_FAILURE'
        if index == 0:
            # Bound stdout reading even if a substituted version tool fills tmpfs.
            with (out / 'command-0.stdout').open('rb') as f:
                version = f.read(65)
            if len(version) > 64 or version.strip() != b'10.0.6':
                return 'VERSION_MISMATCH'
    p.xml_export(out / 'netlist.xml')
    return 'NATIVE_SUCCESS'


def main():
    out = Path('/output'); control = Path('/control'); started = time.monotonic()
    records = []; status = 'SUPERVISOR_FAILURE'
    sys.stdout = (out / 'supervisor.stdout').open('x', buffering=1)
    sys.stderr = (out / 'supervisor.stderr').open('x', buffering=1)
    save(out, 'commands.json', records)
    try:
        proposal = p.load(control / 'proposal.json')
        p.need(proposal['run_id'] == p.RUN and len(proposal['nonce']) == 64, 'fresh run binding required')
        for folder in ('home', 'config', 'cache', 'tmp'):
            (out / folder).mkdir()
        verify_inputs(control, Path('/inputs'), proposal)
        proof = collect_capability(proposal, out)
        save(out, 'capability.json', proof); p.capability(proof, proposal)
        (out / 'ready').write_text('capabilities verified; native NOT RUN\n')
        while not (control / 'admit.json').exists():
            if time.monotonic() - started >= 300:
                raise TimeoutError('fresh admission deadline; native NOT RUN')
            time.sleep(.2)
        p.need(p.load(control / 'capability.json') == proof, 'actual capability proof substitution')
        # Recheck inputs and live limits immediately before consuming admission.
        verify_inputs(control, Path('/inputs'), proposal)
        p.capability(collect_capability(proposal, out), proposal)
        status = execute_once(control, out, proposal, started, records)
    except BaseException:
        traceback.print_exc()
        status = 'NATIVE_UNKNOWN' if records else 'SUPERVISOR_FAILURE'
    finally:
        cg = Path('/sys/fs/cgroup')
        save(out, 'resource.json', {'elapsed_seconds': time.monotonic() - started, 'rusage_children': list(resource.getrusage(resource.RUSAGE_CHILDREN)), 'cgroup': {k: (cg / k).read_text() for k in ('memory.peak', 'memory.events', 'cpu.stat')}})
        sys.stdout.flush(); sys.stderr.flush()
        save(out, 'done.json', {'status': status, 'commands_attempted': len(records), 'native_success': status == 'NATIVE_SUCCESS', 'quiescent': True})
        # No producer writes after done; external timeout kills at 600 seconds.
        while time.monotonic() - started < 595:
            time.sleep(.25)


if __name__ == '__main__':
    main()
