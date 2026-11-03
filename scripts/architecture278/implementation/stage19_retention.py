"""Bounded legacy byte transport plus independent Stage18 receipt validation."""
from pathlib import Path
import os
import math

import stage17_retain as raw
import stage19_protocol as p

REQUIRED = {'supervisor.stdout', 'supervisor.stderr', 'commands.json', 'resource.json', 'done.json'}


def isolated_stream(argv, limit, deadline, sink):
    # Retained scanners use asserts. Isolated Python ignores PYTHONOPTIMIZE;
    # never execute them with -O, including when the host interpreter uses -O.
    argv = list(argv)
    p.need(argv[3:5] == ['python3', '-c'], 'unexpected retention transport')
    argv.insert(4, '-I')
    return raw.stream(argv, limit, deadline, sink)


def verify(destination, receipt, proposal, admission_sha256=None, capability_sha256=None):
    destination = Path(destination)
    rows = receipt['files']
    total = raw.validate_manifest(rows, REQUIRED, p.LIMIT)
    p.need(total == receipt['bytes'] and receipt['status'] == 'VERIFIED_HASHED_COPY', 'invalid raw receipt')
    # Independent disk pass, not reliance on the copy routine's success flag.
    p.need(p.inventory(destination) == {r['path']: r['sha256'] for r in rows}, 'retained inventory/hash mismatch')
    for row in rows:
        p.need((destination / row['path']).stat().st_size == row['size'], 'retained size mismatch')
    names = {r['path'] for r in rows}
    done = p.load(destination / 'done.json'); commands = p.load(destination / 'commands.json')
    p.need(done.get('quiescent') is True, 'producer not quiescent')
    p.need(isinstance(commands, list) and len(commands) <= 2 and type(done.get('commands_attempted')) is int and done['commands_attempted'] == len(commands), 'attempt count mismatch')
    statuses = {'NATIVE_SUCCESS', 'NATIVE_FAILURE', 'VERSION_MISMATCH', 'SUPERVISOR_FAILURE', 'NATIVE_UNKNOWN'}
    status = done.get('status')
    p.need(status in statuses and done.get('native_success') is (status == 'NATIVE_SUCCESS'), 'inconsistent native status')
    p.need([r['argv'] for r in commands] == p.COMMANDS[:len(commands)], 'wrong native argv/order')
    for i, record in enumerate(commands):
        p.need({f'command-{i}.stdout', f'command-{i}.stderr'} <= names, 'missing command logs')
        p.need(record.get('exit') is None or type(record['exit']) is int, 'invalid exit code')
        for key in ('started_elapsed_seconds', 'elapsed_seconds'):
            value = record.get(key)
            p.need(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 500, 'invalid command time')
    if commands:
        p.need('consumed.json' in names, 'missing consumption receipt')
        consumed = p.load(destination / 'consumed.json'); p.bound(consumed, proposal)
        p.need(consumed.get('run_path') == proposal['run_path'] and consumed.get('automatic_retry') is False, 'consumption context mismatch')
        p.need(admission_sha256 is not None and capability_sha256 is not None and consumed.get('admission_sha256') == admission_sha256 and consumed.get('capability_sha256') == capability_sha256, 'consumption proof mismatch')
    if len(commands) == 2:
        p.need(commands[0]['exit'] == 0 and (destination / 'command-0.stdout').stat().st_size <= 64 and (destination / 'command-0.stdout').read_bytes().strip() == b'10.0.6', 'export without exact version gate')
    if status == 'NATIVE_SUCCESS':
        p.need(len(commands) == 2 and all(r['exit'] == 0 for r in commands) and 'netlist.xml' in names, 'incomplete successful export')
        p.xml_export(destination / 'netlist.xml')
    elif status == 'VERSION_MISMATCH':
        with (destination / 'command-0.stdout').open('rb') as f:
            version = f.read(65)
        p.need(len(commands) == 1 and commands[0]['exit'] == 0 and (len(version) > 64 or version.strip() != b'10.0.6'), 'invalid version mismatch')
    elif status == 'NATIVE_FAILURE':
        p.need(commands and type(commands[-1]['exit']) is int and commands[-1]['exit'] != 0, 'invalid native failure')
    elif status == 'SUPERVISOR_FAILURE':
        p.need(not commands, 'supervisor failure hides native attempt')
    elif status == 'NATIVE_UNKNOWN':
        p.need(bool(commands), 'unknown native status without attempt')
    resource = p.load(destination / 'resource.json')
    elapsed = resource.get('elapsed_seconds')
    p.need(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= 520, 'invalid resource duration')
    p.need(set(resource.get('cgroup', {})) == {'memory.peak', 'memory.events', 'cpu.stat'} and isinstance(resource.get('rusage_children'), list) and len(resource['rusage_children']) == 16, 'missing resource evidence')
    p.need(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in resource['rusage_children']), 'invalid rusage values')
    peak = resource['cgroup']['memory.peak'].strip()
    p.need(peak.isdecimal() and int(peak) <= 4294967296, 'invalid memory peak')
    for field in ('memory.events', 'cpu.stat'):
        values = {}
        for line in resource['cgroup'][field].splitlines():
            parts = line.split(); p.need(len(parts) == 2 and parts[1].isdecimal() and parts[0] not in values, 'invalid cgroup counters')
            values[parts[0]] = int(parts[1])
        p.need(bool(values), 'empty cgroup counters')
        if status == 'NATIVE_SUCCESS' and field == 'memory.events':
            p.need(values.get('oom', 0) == 0 and values.get('oom_kill', 0) == 0, 'successful export with OOM')
    return {'status': 'VERIFIED_HASHED_COPY_AND_RECEIPTS', 'bytes': total, 'files': rows, 'native': done, 'logical_parity': 'NOT RUN', 'cleanup_permitted': True}


def retain(container, destination, proposal, *, admission_sha256=None, capability_sha256=None, seconds=60, runner=isolated_stream):
    receipt = raw.retain(container, destination, REQUIRED, seconds=seconds, limit=p.LIMIT, runner=runner)
    result = verify(destination, receipt, proposal, admission_sha256, capability_sha256)
    # Durably publish directory entries as well as file content before cleanup.
    for directory in [p for p in Path(destination).rglob('*') if p.is_dir()] + [Path(destination), Path(destination).parent]:
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return result
