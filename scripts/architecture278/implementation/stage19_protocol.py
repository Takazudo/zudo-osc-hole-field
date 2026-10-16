"""Pure, fail-closed protocol for one future Stage18 XML export; no native calls."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import xml.etree.ElementTree as ET

SOURCE = '91403f4d78b72757187d8cfdbb4d2dc436a3cf72'
IMAGE = 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
RUN = 'osc-stage18-native-001'
LIMIT = 250 * 1024 * 1024
META_LIMIT = 12 * 1024 * 1024
JSON_LIMIT = 1024 * 1024
COMMANDS = [['kicad-cli', 'version'], ['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', '/output/netlist.xml', '/inputs/stage18/generated/a01.kicad_sch']]
RUNTIME = ('stage19_protocol.py', 'stage19_container.py', 'stage19_host.py', 'stage19_retention.py', 'stage17_retain.py')
REVIEWED = set(RUNTIME) | {'request.json', 'proposal.json', 'owner-approval.json', 'input-binding.json', 'docker-argv.json', 'docker-inspect.json', 'capability.json', 'live-review.json'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def load(path, limit=JSON_LIMIT):
    path = Path(path)
    need(not path.is_symlink() and path.is_file(), 'regular JSON file required: ' + str(path))
    with path.open('rb') as f:
        raw = f.read(limit + 1)
    need(len(raw) <= limit, 'JSON byte quota')
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'duplicate JSON key')
            result[k] = v
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def inventory(root):
    root = Path(root)
    need(root.is_dir() and not root.is_symlink(), 'regular input root required')
    rows = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            need(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'symlink/special input rejected')
            if stat.S_ISREG(mode):
                rows[str(path.relative_to(root))] = digest(path)
    return rows


def bound(value, proposal):
    for key in ('run_id', 'nonce', 'source_commit', 'verification_commit', 'request_sha256'):
        need(value.get(key) == proposal[key], 'binding mismatch: ' + key)


def fresh(value, now, max_age):
    a, b = value.get('issued_at_unix'), value.get('expires_at_unix')
    need(type(a) in (int, float) and type(b) in (int, float) and math.isfinite(a) and math.isfinite(b), 'finite approval times required')
    need(a <= now < b and 0 < b - a <= max_age, 'expired/future approval')


def approval(value, proposal, now):
    need(value.get('approved') is True and value.get('native_export_opportunities') == 1, 'explicit single-export approval required')
    # Owner approval precedes the host-created nonce; bind every other immutable field.
    for key in ('run_id', 'source_commit', 'verification_commit', 'request_sha256', 'run_path'):
        need(value.get(key) == proposal[key], 'owner approval binding: ' + key)
    need(isinstance(value.get('approved_by'), str) and value['approved_by'].strip(), 'owner identity required')
    need(isinstance(value.get('approval_reference'), str) and value['approval_reference'].strip(), 'owner evidence reference required')
    fresh(value, now, 86400)


def admission(control, proposal, now):
    control = Path(control)
    value = load(control / 'admit.json')
    need(value.get('approved') is True, 'admission not approved')
    bound(value, proposal)
    fresh(value, now, 300)
    approval(load(control / 'owner-approval.json'), proposal, now)
    review = load(control / 'live-review.json')
    bound(review, proposal)
    need(review.get('approved') is True and isinstance(review.get('reviewer'), str) and review['reviewer'].strip(), 'independent live review required')
    need(review.get('independent_of_implementation') is True, 'independent reviewer declaration required')
    fresh(review, now, 300)
    hashes = value.get('reviewed_sha256')
    need(isinstance(hashes, dict) and set(hashes) == REVIEWED, 'exact reviewed inventory required')
    for name, sha in hashes.items():
        need(not (control / name).is_symlink() and digest(control / name) == sha, 'reviewed hash mismatch: ' + name)
    # Review itself explicitly binds the two actual host/container proofs.
    need(review.get('capability_sha256') == hashes['capability.json'] and review.get('docker_inspect_sha256') == hashes['docker-inspect.json'], 'live proof substitution')
    return value


def capability(proof, proposal):
    bound(proof, proposal)
    need(proof.get('limits') == {'cpu.max': '200000 100000', 'memory.max': '4294967296', 'memory.swap.max': '0', 'pids.max': '128'}, 'cgroup limits mismatch')
    need(proof.get('output_capacity_bytes') == LIMIT and proof.get('interfaces') == ['lo'], 'tmpfs/network mismatch')
    need(type(proof.get('uid')) is int and proof['uid'] > 0 and type(proof.get('gid')) is int and proof['gid'] > 0 and 0 not in proof.get('groups', [0]), 'non-root identity required')
    need(proof.get('readonly') == {'/': True, '/inputs/stage17/generated': True, '/inputs/stage18/generated': True, '/control': True, '/dev/shm': True}, 'read-only mount proof required')
    need(proof.get('other_path_writable') == {p: False for p in ('/dev', '/dev/mqueue', '/etc/hosts', '/etc/hostname', '/etc/resolv.conf')}, 'extra writable path')


def xml_export(path):
    need(Path(path).stat().st_size > 0, 'empty XML')
    # Reject declarations in a bounded streaming pass, including cross-chunk tokens.
    tail = b''
    with Path(path).open('rb') as f:
        while chunk := f.read(65536):
            data = tail + chunk
            need(b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper() and b'\x00' not in data, 'DTD/entity/non-UTF8 XML rejected')
            tail = data[-16:]
    stack = []; elements = []; tools = []; count = 0
    for event, element in ET.iterparse(path, events=('start', 'end')):
        if event == 'start':
            if not stack:
                need(element.tag == 'export' and element.get('version') == 'E', 'wrong XML export root')
            stack.append(element.tag); elements.append(element); count += 1
            need(len(stack) <= 64 and count <= 100000, 'XML structure quota exceeded')
        else:
            if element.tag == 'tool':
                need(stack == ['export', 'design', 'tool'], 'tool outside design')
                tools.append(element.text)
            stack.pop(); elements.pop(); element.clear()
            if elements:
                elements[-1].remove(element)
    need(tools == ['Eeschema 10.0.6'], 'wrong XML exporter version')


def docker_argv(repo, run, nonce="<fresh-nonce>"):
    inputs = Path(repo) / 'design/architecture-278/implementation'
    run = Path(run)
    argv = ['docker', 'run', '--detach', '--pull=never', '--name', RUN, '--label', 'osc.run_nonce=' + nonce, '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--cpus', '2', '--memory', '4g', '--memory-swap', '4g', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--ipc', 'none', '--log-driver', 'none', '--tmpfs', '/output:rw,noexec,nosuid,nodev,size=262144000,mode=1777']
    for stage in ('stage17', 'stage18'):
        argv += ['--mount', f'type=bind,src={inputs}/{stage}/generated,dst=/inputs/{stage}/generated,readonly']
    argv += ['--mount', f'type=bind,src={run},dst=/control,readonly', '--mount', f'type=bind,src={run}/empty,dst=/dev/mqueue,readonly', '--workdir', '/output']
    for item in ('HOME=/output/home', 'XDG_CONFIG_HOME=/output/config', 'XDG_CACHE_HOME=/output/cache', 'TMPDIR=/output/tmp', 'PYTHONDONTWRITEBYTECODE=1'):
        argv += ['--env', item]
    return argv + ['--entrypoint', '/usr/bin/timeout', IMAGE, '-s', 'KILL', '600', 'python3', '-B', '/control/stage19_container.py']


def owned_container(rows, proposal):
    need(isinstance(rows, list) and len(rows) == 1, 'one owned container required')
    row = rows[0]
    need(re.fullmatch('[0-9a-f]{64}', row.get('Id', '')) is not None, 'full container ID required')
    need(row.get('Config', {}).get('Labels', {}).get('osc.run_nonce') == proposal['nonce'], 'foreign container; do not touch')
    return row['Id']


def inspect_container(rows, repo, run):
    need(isinstance(rows, list) and len(rows) == 1, 'one container inspection required')
    row = rows[0]; host = row['HostConfig']; config = row['Config']
    need(config['Image'] == IMAGE and config['Entrypoint'] == ['/usr/bin/timeout'] and config['Cmd'] == ['-s', 'KILL', '600', 'python3', '-B', '/control/stage19_container.py'], 'image/timeout mismatch')
    need(host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] is True and host['NanoCpus'] == 2000000000 and host['Memory'] == 4294967296 and host['MemorySwap'] == 4294967296 and host['PidsLimit'] == 128, 'Docker limits mismatch')
    need(host['Privileged'] is False and host['CapDrop'] == ['ALL'] and not host.get('CapAdd') and 'no-new-privileges' in host['SecurityOpt'] and host['IpcMode'] == 'none' and host['LogConfig']['Type'] == 'none', 'Docker isolation mismatch')
    expected = {'/control': str(run), '/dev/mqueue': str(Path(run) / 'empty')}
    for stage in ('stage17', 'stage18'):
        expected[f'/inputs/{stage}/generated'] = str(Path(repo) / 'design/architecture-278/implementation' / stage / 'generated')
    mounts = row['Mounts']
    binds = [m for m in mounts if m['Type'] == 'bind']
    need(len(binds) == 4 and {m['Destination']: m['Source'] for m in binds} == expected and all(m['RW'] is False for m in binds), 'input/control mounts mismatch')
    need(all(m['Type'] == 'bind' or (m['Type'] == 'tmpfs' and m['Destination'] == '/output') for m in mounts), 'unexpected Docker volume')
    need(host['Tmpfs'] == {'/output': 'rw,noexec,nosuid,nodev,size=262144000,mode=1777'}, 'Docker tmpfs mismatch')
