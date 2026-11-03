"""Generate/check an immutable Stage19 launch proposal; never launch anything."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import stage18_request as prior
import stage19_protocol as p

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation/stage19'
BASE = '979882b453036a4633a62a007644384dd624530e'


def request(commit):
    p.need(subprocess.check_output(['git', 'rev-parse', commit + '^{commit}'], cwd=ROOT, text=True).strip() == commit, 'full exact verification commit required')
    original = prior.request(p.SOURCE)
    p.need(json.loads((ROOT / 'design/architecture-278/implementation/stage18/native-request.json').read_text()) == original, 'historical request drift')
    bound = dict(original['source_and_verifier_sha256'])
    paths = sorted((ROOT / 'scripts/architecture278/implementation').glob('*stage19*.py'))
    paths += [OUT / name for name in ('README.md', 'review-independent.json', 'review-independent.md')]
    paths += [ROOT / 'scripts/architecture278/implementation/stage17_retain.py']
    for path in paths:
        bound[str(path.relative_to(ROOT))] = p.digest(path)
    for relative, sha in bound.items():
        blob = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=ROOT)
        p.need(hashlib.sha256(blob).hexdigest() == sha == p.digest(ROOT / relative), 'uncommitted verification bytes: ' + relative)
    return {'status': 'PROPOSAL ONLY; no native/container command executed', 'admission_granted': False,
        'source_commit': p.SOURCE, 'verification_commit': commit, 'image': p.IMAGE,
        'run_id': p.RUN, 'native_argv': p.COMMANDS, 'required_version_stdout': '10.0.6',
        'input_files_sha256': original['input_mount']['required_files_sha256'],
        'runtime_sha256': {name: bound['scripts/architecture278/implementation/' + name] for name in p.RUNTIME},
        'verification_files_sha256': dict(sorted(bound.items())), 'resources': original['resources'],
        'host_argv_after_fresh_approval': ['bash', '$HOME/.codex/scripts/heavy-guard.sh', '--', 'python3', '<exact-checkout>/scripts/architecture278/implementation/stage19_host.py', '--repo', '<exact-checkout>', '--run', '<fresh-parent>/' + p.RUN, '--request', '<published-stage19-native-request.json>', '--owner-approval', '<fresh-owner-approval.json>'],
        'docker_argv_template': p.docker_argv('<exact-checkout>', '<fresh-parent>/' + p.RUN),
        'owner_approval_required_fields': ['approved=true', 'approved_by', 'approval_reference', 'issued_at_unix', 'expires_at_unix (within 24h)', 'source_commit', 'verification_commit', 'request_sha256', 'run_id', 'run_path', 'native_export_opportunities=1'],
        'live_review_required_fields': ['approved=true', 'reviewer', 'independent_of_implementation=true', 'issued_at_unix', 'expires_at_unix (within 300s)', 'source_commit', 'verification_commit', 'request_sha256', 'run_id', 'nonce', 'capability_sha256', 'docker_inspect_sha256'],
        'admission_required_fields': ['approved=true', 'issued_at_unix', 'expires_at_unix (within 300s)', 'source_commit', 'verification_commit', 'request_sha256', 'run_id', 'nonce', 'reviewed_sha256 (exact inventory below)'],
        'admission_reviewed_files': sorted(p.REVIEWED),
        'automatic_retry': False, 'native_export_opportunities': 1,
        'post_retention_comparison_argv': original['post_retention_comparison_argv'],
        'remaining_host_preflight': ['Prefer Cloud. If its existing runtime cannot prove the requirements, assess X0X Linux/WSL afresh; historical receipts do not admit either host.', 'Existing Docker engine and digest-pinned linux/amd64 image; no installation, pull, or native version probe in preflight.', 'Fresh absent canonical run directory and container name; shared heavy guard locked, >4GiB available host memory.', 'Current actual read-only mounts, non-root uid/gid, cgroup v2 CPU/memory/swap/PID limits, no network, no other writable paths, 250MiB tmpfs and 600s external timeout.', 'Obtain fresh owner approval, then independent live proof review and exact hash-bound admission before the sole version/export opportunity.'],
        'historical_status': original['historical_status'], 'acceptance_contract': original['acceptance_contract']}


def protected():
    # New Stage19 files and appended work notes are the only allowed changes.
    changed = subprocess.check_output(['git', 'diff', BASE, '--name-only', '--diff-filter=DMRTUXB'], cwd=ROOT, text=True).splitlines()
    p.need(set(changed) <= {'design/architecture-278/implementation/WORK.md'}, 'historical/protected path changed: ' + repr(changed))
    additions = subprocess.check_output(['git', 'diff', BASE, '--name-only', '--diff-filter=A'], cwd=ROOT, text=True).splitlines()
    p.need(all(name.startswith('design/architecture-278/implementation/stage19/') or (name.startswith('scripts/architecture278/implementation/') and 'stage19' in Path(name).name) for name in additions), 'out-of-scope added path')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--commit'); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    protected()
    if args.check:
        saved = p.load(OUT / 'native-request.json')
        p.need((OUT / 'native-request.json').read_bytes() == p.json_bytes(request(saved['verification_commit'])), 'stale immutable request')
        print('Stage19 committed request and protected paths: PASS; native NOT RUN')
    else:
        p.need(args.commit, '--commit required')
        print(p.json_bytes(request(args.commit)).decode(), end='')


if __name__ == '__main__':
    main()
