"""Future supervisor: requires fresh owner approval and live independent admission.

Import and --help are inert. Do not run main until a separately authorized native run.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time

import stage17_retain as raw
import stage19_protocol as p
import stage19_retention as retention
import stage19_request as requests


def metadata_bytes(base):
    total = 0
    for directory, dirs, files in os.walk(base, followlinks=False):
        if Path(directory) == base:
            dirs[:] = [d for d in dirs if d not in ('retained', 'retained.partial')]
        for name in dirs + files:
            path = Path(directory) / name
            p.need(not path.is_symlink(), 'metadata symlink')
        for name in files:
            path = Path(directory) / name
            p.need(path.is_file(), 'special metadata file')
            total += path.stat().st_size
    p.need(total <= p.META_LIMIT, 'metadata quota exceeded')
    return total


def save(base, name, value):
    payload = p.json_bytes(value)
    p.need(metadata_bytes(base) + len(payload) <= p.META_LIMIT, 'metadata quota exceeded')
    with (base / name).open('xb') as f:
        f.write(payload); f.flush(); os.fsync(f.fileno())


def command(argv, *, seconds=20, limit=p.JSON_LIMIT):
    chunks = []
    raw.stream(argv, limit, time.monotonic() + seconds, chunks.append)
    return b''.join(chunks)


def checkout(repo, request):
    commit = request['verification_commit']
    p.need(command(['git', '-C', str(repo), 'rev-parse', 'HEAD']).decode().strip() == commit, 'exact verification checkout required')
    p.need(request['source_commit'] == p.SOURCE and request['native_argv'] == p.COMMANDS and request['image'] == p.IMAGE, 'request contract mismatch')
    p.need(Path(__file__).resolve().parent == repo / 'scripts/architecture278/implementation', 'run committed host script directly')
    p.need(request == requests.request(commit), 'request incomplete or differs from immutable source contract')
    p.need(set(request['runtime_sha256']) == set(p.RUNTIME), 'exact runtime set required')
    for name, sha in request['runtime_sha256'].items():
        relative = 'scripts/architecture278/implementation/' + name
        p.need(request['verification_files_sha256'].get(relative) == sha, 'runtime not committed')
    for relative, sha in request['verification_files_sha256'].items():
        path = repo / relative
        p.need(path.resolve().is_relative_to(repo) and not path.is_symlink() and p.digest(path) == sha, 'working source drift: ' + relative)
        import hashlib
        blob = command(['git', '-C', str(repo), 'show', commit + ':' + relative], limit=p.LIMIT)
        p.need(hashlib.sha256(blob).hexdigest() == sha, 'commit source drift: ' + relative)
    actual = {}
    for stage in ('stage17', 'stage18'):
        root = repo / 'design/architecture-278/implementation' / stage / 'generated'
        actual.update({stage + '/generated/' + k: v for k, v in p.inventory(root).items()})
    p.need(actual == request['input_files_sha256'] and len(actual) == 72, 'exact generated inventory required')


def host_preflight():
    p.need(os.name == 'posix' and Path('/proc/meminfo').exists(), 'Linux/WSL runtime required')
    p.need(os.environ.get('HEAVY_GUARD_HELD') == '1', 'shared heavy guard required')
    lock = Path.home() / '.agent-guard/heavy/slot-0.lock'
    p.need(lock.is_file(), 'shared heavy lock missing')
    result = subprocess.run(['flock', '-n', str(lock), 'true'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    p.need(result.returncode == 1, 'heavy guard lock not held or flock error')
    available = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
    p.need(available > 4 * 1024 * 1024, 'host memory admission failed')


def orchestrate(repo, base, request_path, approval_path):
    repo = repo.resolve(); base = base.absolute()
    p.need(base.name == p.RUN and not base.exists() and not base.is_symlink() and base.parent.resolve() == base.parent, 'fresh canonical run path required')
    request = p.load(request_path)
    host_preflight(); checkout(repo, request)
    proposal = {'run_id': p.RUN, 'run_path': str(base), 'nonce': secrets.token_hex(32), 'source_commit': p.SOURCE, 'verification_commit': request['verification_commit'], 'request_sha256': p.digest(request_path), 'native_export_opportunities': 1, 'automatic_retry': False}
    owner = p.load(approval_path); p.approval(owner, proposal, time.time())
    p.need(not command(['docker', 'ps', '-a', '--filter', 'name=^/' + p.RUN + '$', '--format', '{{.ID}}']).strip(), 'container name already exists; do not touch')
    base.mkdir(); (base / 'empty').mkdir()
    for name in p.RUNTIME:
        shutil.copyfile(repo / 'scripts/architecture278/implementation' / name, base / name)
    # Preserve the exact approved request serialization, not a JSON reserialization.
    shutil.copyfile(request_path, base / 'request.json')
    save(base, 'owner-approval.json', owner); save(base, 'proposal.json', proposal)
    save(base, 'input-binding.json', request['input_files_sha256'])
    argv = p.docker_argv(repo, base, proposal['nonce']); save(base, 'docker-argv.json', argv)
    start = time.monotonic(); verified = False; launched = False; cid = None
    try:
        # Once launch is attempted, never retry, even if the client response is lost.
        launched = True
        cid = command(argv).decode().strip()
        p.need(len(cid) == 64 and all(c in '0123456789abcdef' for c in cid), 'unknown container launch result')
        inspection = json.loads(command(['docker', 'inspect', p.RUN])); save(base, 'docker-inspect.json', inspection)
        p.need(p.owned_container(inspection, proposal) == cid, 'launch ID mismatch')
        p.inspect_container(inspection, repo, base)
        proof_saved = False
        while time.monotonic() - start < 520:
            metadata_bytes(base)
            def exists(name):
                return subprocess.run(['docker', 'exec', cid, 'test', '-f', '/output/' + name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5).returncode == 0
            if not proof_saved and exists('ready'):
                proof = json.loads(command(['docker', 'exec', cid, 'cat', '/output/capability.json']))
                p.capability(proof, proposal); save(base, 'capability.json', proof)
                print('WAITING: independent reviewer must inspect actual proofs and atomically publish live-review.json then admit.json. Native NOT RUN.', flush=True)
                proof_saved = True
            if exists('done.json'):
                remaining = min(60, 580 - (time.monotonic() - start))
                p.need(remaining > 0, 'retention budget exhausted')
                receipt = retention.retain(cid, base / 'retained', proposal, admission_sha256=p.digest(base / 'admit.json') if (base / 'admit.json').exists() else None, capability_sha256=p.digest(base / 'capability.json') if (base / 'capability.json').exists() else None, seconds=remaining)
                save(base, 'retention.json', receipt)
                save(base, 'assessment.json', {'native': receipt['native'], 'retention': receipt['status'], 'logical_parity': 'NOT RUN; use Stage18 source comparator after retention'})
                verified = True
                return 0 if receipt['native']['native_success'] else 1
            time.sleep(.2)
        raise TimeoutError('supervisor completion deadline')
    except BaseException as error:
        save(base, 'host-failure.json', {'error': str(error), 'verified_copy': verified, 'native_result': 'UNKNOWN unless durable receipts establish it', 'automatic_retry': False})
        raise
    finally:
        if launched:
            # Resolve a lost launch response only through this run's random label.
            # A colliding name or any unprovable identity must never be touched.
            try:
                actual = json.loads(command(['docker', 'inspect', cid or p.RUN]))
                owned = p.owned_container(actual, proposal)
            except Exception:
                owned = None
                print('Container ownership unproved: no kill/remove; no retry. A successfully launched supervisor has its own 600s timeout.', flush=True)
            if owned:
                if not verified:
                    print('Unverified retention: preserving live evidence until hard deadline; no retry.', flush=True)
                    while time.monotonic() - start < 590:
                        time.sleep(.5)
                subprocess.run(['docker', 'kill', owned], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                try:
                    save(base, 'docker-final.json', json.loads(command(['docker', 'inspect', owned])))
                finally:
                    if verified:
                        command(['docker', 'rm', owned])
                    else:
                        print('UNVERIFIED RETENTION: stopped container is NOT removed. Preserve host receipts/partial copy; tmpfs may be lost at stop.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--owner-approval', type=Path, required=True)
    args = parser.parse_args()
    return orchestrate(args.repo, args.run, args.request, args.owner_approval)


if __name__ == '__main__':
    raise SystemExit(main())
