#!/usr/bin/env python3
"""Local native requests and separate operator attestations; never self-approve.

This is a workflow boundary, not a security boundary against the same Unix user.
The existing resource guard remains the sole native launcher and containment owner.
"""
import argparse
import hashlib
import json
import os
import pwd
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
E16 = 'design/partition/core-split/candidates/planning/joined-feed-construction-v2'
ORACLE_TEST = 'design.spec.cells.test_sweep_precision_vendor.PrecisionVendorSweepGate.test_original_network_returns_nonzero_for_supported_failure'
AUTHORITY_KEYS = ('EPIC242_ADMISSION_MODE', 'EPIC242_LOCAL_REQUEST',
                  'EPIC242_PARENT_LOCAL_REQUEST_SHA256', 'EPIC242_LOCAL_APPROVAL',
                  'EPIC242_LOCAL_APPROVAL_SHA256')
CI_KEYS = ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_SHA',
           'EPIC242_PARENT_ADMISSION_RUN_ID', 'EPIC242_PARENT_ADMISSION_SHA',
           'EPIC242_PARENT_REQUEST_SHA256', 'EPIC242_REVIEWED_HOOK_SHA256')
METHODS = ('scripts/kicad/local_native_admission.py', 'scripts/kicad/native_resource_guard.py',
           'scripts/kicad/native_start_gate.sh', 'scripts/kicad/run.sh', 'scripts/kicad/pin.env')
LIMITS = {'worker_bytes': 6442450944, 'aggregate_bytes': 12884901888, 'swap_bytes': 0,
          'launch_available_bytes': 8589934592, 'global_slots': 1}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def local_path(root, name, cache=False):
    path = Path(name)
    need(not path.is_absolute() and '..' not in path.parts and str(path) == name,
         'canonical repository-relative path required')
    result = root / path
    need(result.resolve() == result.absolute() and result.resolve().is_relative_to(root.resolve()),
         'symlink or escaping path refused')
    if cache:
        need(path.parts[0] == '.circuit-cache' and len(path.parts) > 1, 'ignored cache path required')
    return result


def clean_head(root):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
    need(not git('status', '--porcelain', '--untracked-files=no'), 'clean tracked checkout required')
    return git('rev-parse', 'HEAD')


def no_mixed_authority(env):
    need(not any(env.get(key) for key in CI_KEYS), 'mixed CI/local authority refused')


def persistent_claim_directory():
    # Account identity, not a caller-controlled HOME, fixes the replay ledger.
    return Path(pwd.getpwuid(os.getuid()).pw_dir) / '.local/state/epic242-native-admission'


def heavy_settings(env):
    return {key: value for key, value in env.items() if key.startswith('HEAVY_GUARD_') and key != 'HEAVY_GUARD_HELD'}


def check_shared_guard(request, env):
    need(env.get('HEAVY_GUARD_HELD', '0') != '1', 'launch local admission directly; nested heavy-guard bypass refused')
    need(heavy_settings(env) == request['heavy_guard_environment'], 'shared heavy guard configuration changed')
    need(env.get('HEAVY_GUARD_SLOTS', '1') == '1', 'local admission requires the existing single shared slot')
    default = Path.home() / '.agent-guard/heavy'
    need(Path(env.get('HEAVY_GUARD_DIR', str(default))) == default, 'alternate heavy queue refused')
    need(shutil.which('flock') is not None, 'WSL shared heavy guard flock backend missing')
    default.mkdir(parents=True, exist_ok=True)
    need(os.access(default, os.W_OK | os.X_OK), 'shared queue unavailable; refuse helper fail-open fallback')


def worker_name(request):
    need(re.fullmatch(r'[0-9a-f]{32}', request['run_id']), '32-hex local run ID required')
    need(type(request['attempt']) is int and 1 <= request['attempt'] <= 999999, 'positive bounded attempt required')
    suffix = 'e16-' + request['target'].lower() if request['kind'] == 'e16' else request['target']
    value = f"local-{request['run_id']}-{request['attempt']}-{suffix}"
    need(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', value), 'worker identity too long')
    return value


def command_and_inputs(request, root):
    """Allow only the one oracle test or one of the three existing E16 targets."""
    inputs = set(METHODS)
    if request['kind'] in ('startup-success', 'startup-failure'):
        need(request['target'] == request['kind'] and request['stage'] is None, 'startup target/stage mismatch')
        inputs.add('scripts/kicad/qualify_startup_handshake.py')
        inputs.add('scripts/kicad/settle_only_pilot.py')
        command = ['bash', 'scripts/kicad/run.sh'] + (['kicad-cli', 'version']
                  if request['kind'] == 'startup-success' else ['/bin/false'])
        return command, 60, inputs
    if request['kind'] == 'oracle':
        need(request['target'] == 'python' and request['stage'] is None, 'oracle target/stage mismatch')
        inputs.update(('design/spec/cells/test_sweep_precision_vendor.py',
                       'design/spec/cells/sweep_precision_vendor.py', 'design/spec/cells/_builder.py',
                       'design/spec/model_contracts.py', 'design/spec/modules/spice_trace.py',
                       '.circuit-cache/sources/opa197-model/SBOMA34D.ZIP',
                       '.circuit-cache/sources/opa197-model/OPAx197.LIB'))
        return ['python3', '-m', 'unittest', ORACLE_TEST], 1680, inputs
    need(request['kind'] == 'e16' and request['target'] in ('KA-t2', 'KB-t2', 'KB-p1'), 'unsupported local operation')
    stage = local_path(root, request['stage'], cache=True)
    e16 = read(stage / 'request.json')
    need(e16.get('admission_mode') == 'local' and e16.get('local_run_id') == request['run_id'] and
         e16.get('local_run_attempt') == request['attempt'] and
         e16['orchestration_commit'] == request['source_sha'], 'E16 local run binding differs')
    inputs.add(request['stage'] + '/request.json')
    for name in e16['staged_input_sha256']:
        inputs.add(request['stage'] + '/materialized/' + name)
    inputs.update(e16['protected_sha256'])
    inputs.add(E16 + '/native_validation.py')
    for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
        inputs.add(request['stage'] + '/' + request['target'] + '/filled/' + request['target'] + suffix)
    return ['python3', E16 + '/native_validation.py', 'worker', '--stage', request['stage'],
            '--target', request['target']], 2580, inputs


def prepare(root, output, kind, run_id, attempt, evidence, *, stage=None, target='python', heavy_guard=None):
    head = clean_head(root)
    destination = local_path(root, output, cache=True)
    need(destination.parent.is_dir() and not destination.exists(), 'fresh request with existing parent required')
    receipt = local_path(root, evidence, cache=True)
    need(receipt.parent.is_dir() and not receipt.exists(), 'fresh evidence with existing parent required')
    heavy = Path(heavy_guard or Path.home() / '.codex/scripts/heavy-guard.sh').resolve()
    need(heavy.is_file(), 'shared heavy guard unavailable')
    request = {'schema': 'epic242-local-native-request-v1', 'status': 'PREPARED; NOT ADMITTED',
               'checkout': str(root.resolve()), 'source_sha': head, 'request_path': output,
               'run_id': run_id, 'attempt': attempt, 'kind': kind, 'target': target,
               'stage': stage, 'evidence': evidence, 'limits': LIMITS,
               'heavy_guard': str(heavy), 'heavy_guard_sha256': sha(heavy),
               'heavy_guard_environment': heavy_settings(os.environ),
               'uid': os.getuid(), 'claim_directory': str(persistent_claim_directory())}
    request['worker'] = worker_name(request)
    command, seconds, inputs = command_and_inputs(request, root)
    request.update(command=command, seconds=seconds,
                   input_sha256={name: sha(local_path(root, name)) for name in sorted(inputs)})
    write(destination, request)
    return request


def validate_request(root, path, *, host=True, check_inputs=True):
    path = Path(path)
    request = read(path)
    need(request.get('schema') == 'epic242-local-native-request-v1' and
         request.get('status') == 'PREPARED; NOT ADMITTED', 'unsupported local request')
    need(local_path(root, request['request_path'], cache=True) == path, 'request path differs')
    need(re.fullmatch(r'[0-9a-f]{40}', request['source_sha']), 'immutable source SHA required')
    if host:
        need(request['checkout'] == str(root.resolve()) and request['uid'] == os.getuid(), 'request belongs to another checkout/user')
        need(clean_head(root) == request['source_sha'], 'request source SHA differs')
        need(sha(request['heavy_guard']) == request['heavy_guard_sha256'], 'shared heavy guard changed')
        need(Path(request['claim_directory']) == persistent_claim_directory() and
             Path(request['claim_directory']).resolve() == Path(request['claim_directory']), 'fixed account persistent claim directory required')
    need(request['worker'] == worker_name(request) and request['limits'] == LIMITS, 'worker/resource binding differs')
    command, seconds, inputs = command_and_inputs(request, root)
    need(request['command'] == command and request['seconds'] == seconds, 'exact allowed command/deadline differs')
    need(set(request['input_sha256']) == inputs, 'complete input seal set required')
    for name, digest in request['input_sha256'].items():
        need(re.fullmatch(r'[0-9a-f]{64}', digest), 'invalid input digest')
        # Filled copies legitimately change after fill. Inner phases still verify
        # immutable source/methods; native_validation owns the filled hash chain.
        mutable = request['kind'] == 'e16' and name.startswith(request['stage'] + '/' + request['target'] + '/filled/')
        if check_inputs or not mutable:
            need(sha(local_path(root, name)) == digest, 'sealed input changed: ' + name)
    local_path(root, request['evidence'], cache=True)
    return request


def approval_binding(request, digest):
    return {key: request[key] for key in ('request_path', 'checkout', 'source_sha', 'run_id', 'attempt',
            'kind', 'target', 'worker')} | {'request_sha256': digest}


def approve(root, path, digest, output, operator, reservation, qualification):
    request = validate_request(root, path)
    need(sha(path) == digest, 'operator-supplied exact request digest differs')
    need(all(type(value) is str and value.strip() for value in (operator, reservation, qualification)),
         'operator, global reservation and native qualification references required')
    destination = local_path(root, output, cache=True)
    need(destination != path, 'approval must be separate from request')
    receipt = {'schema': 'epic242-local-operator-approval-v1', 'approved': True,
               **approval_binding(request, digest), 'approval_path': output, 'operator': operator,
               'global_reservation_reference': reservation, 'native_qualification_reference': qualification,
               'attestation': 'Operator separately approves only this request and reserves one global native slot; all other native work excluded.',
               'approved_at_unix': int(time.time())}
    write(destination, receipt)
    return receipt


def validate_approval(root, path, request, digest):
    approval = read(path)
    need(approval.get('schema') == 'epic242-local-operator-approval-v1' and approval.get('approved') is True,
         'separate operator approval required')
    need(local_path(root, approval['approval_path'], cache=True) == path, 'approval path differs')
    need(all(approval.get(k) == v for k, v in approval_binding(request, digest).items()), 'operator approval binding differs')
    need(all(isinstance(approval.get(k), str) and approval[k].strip() for k in
             ('operator', 'global_reservation_reference', 'native_qualification_reference')), 'operator attestation incomplete')
    return approval


def authority(root, env, *, host=False):
    no_mixed_authority(env)
    need(env.get('EPIC242_ADMISSION_MODE') == 'local', 'explicit local authority required')
    path = local_path(root, env['EPIC242_LOCAL_REQUEST'], cache=True)
    digest = sha(path)
    need(digest == env['EPIC242_PARENT_LOCAL_REQUEST_SHA256'], 'parent-approved local request digest differs')
    request = validate_request(root, path, host=host, check_inputs=host)
    approval_path = local_path(root, env['EPIC242_LOCAL_APPROVAL'], cache=True)
    need(sha(approval_path) == env['EPIC242_LOCAL_APPROVAL_SHA256'], 'operator approval digest differs')
    validate_approval(root, approval_path, request, digest)
    return request


def claim(request, digest, directory):
    directory.mkdir(parents=True, exist_ok=True)
    # Persistent across reboot; a failed launch is still a consumed attempt.
    path = directory / (request['worker'] + '.json')
    with path.open('x') as stream:
        json.dump({'request_sha256': digest, 'source_sha': request['source_sha'],
                   'checkout': request['checkout'], 'claimed_at_unix': int(time.time())}, stream)
    return path


def execute(root, path, approval_path, *, env=None, claims=None):
    env = dict(os.environ if env is None else env)
    no_mixed_authority(env)
    request = validate_request(root, path)
    digest = sha(path)
    validate_approval(root, approval_path, request, digest)
    receipt = local_path(root, request['evidence'], cache=True)
    need(receipt.parent.is_dir() and not any(Path(str(receipt) + suffix).exists() for suffix in
             ('', '.driver.log', '.qualification.json')), 'fresh evidence parent/file required')
    context = {'EPIC242_ADMISSION_MODE': 'local', 'EPIC242_LOCAL_REQUEST': request['request_path'],
               'EPIC242_PARENT_LOCAL_REQUEST_SHA256': digest,
               'EPIC242_LOCAL_APPROVAL': str(approval_path.relative_to(root)),
               'EPIC242_LOCAL_APPROVAL_SHA256': sha(approval_path)}
    authority(root, context, host=True)
    check_shared_guard(request, env)
    claimed = claim(request, digest, claims or Path(request['claim_directory']))
    command = ['bash', request['heavy_guard'], '--', sys.executable, str(root / 'scripts/kicad/native_resource_guard.py'),
               '--admission-id', 'local-' + request['run_id'] + '-' + str(request['attempt']),
               '--worker', request['worker'], '--sha', request['source_sha'], '--hook-sha256',
               request['input_sha256']['scripts/kicad/run.sh'], '--seconds', str(request['seconds']),
               '--evidence', request['evidence'], '--', 'env',
               *[key + '=' + context[key] for key in AUTHORITY_KEYS], 'python3',
               'scripts/kicad/local_native_admission.py', 'worker']
    driver_log = Path(str(receipt) + '.driver.log')
    print('Guard output retained at ' + str(driver_log), flush=True)
    with driver_log.open('x') as output:
        result = subprocess.run(command, cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, check=False)
    unchanged, error = True, None
    try:
        authority(root, context)  # Approval and immutable inputs still bound.
        validate_request(root, path, host=True, check_inputs=False)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as failure:
        unchanged, error = False, str(failure)
    write(Path(str(claimed) + '.result'), {'exit_code': result.returncode, 'command': command,
        'request_sha256': digest, 'approval_sha256': context['EPIC242_LOCAL_APPROVAL_SHA256'],
        'driver_log': str(driver_log), 'driver_log_sha256': sha(driver_log),
        'post_run_inputs_unchanged': unchanged, 'post_run_error': error})
    if not unchanged:
        return 1
    if request['kind'] in ('startup-success', 'startup-failure'):
        # Reuse the existing complete lifecycle verifier. Only the exact outer
        # local worker command differs; helper identity/exit/cleanup checks stay.
        import importlib.util
        spec = importlib.util.spec_from_file_location('local_lifecycle', root / 'scripts/kicad/qualify_startup_handshake.py')
        lifecycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lifecycle)
        name = 'success' if request['kind'] == 'startup-success' else 'intentional-failure'
        status = {'status': 'FAIL / NOT QUALIFIED', 'request_sha256': digest, 'guard_exit_code': result.returncode}
        try:
            status['checked'] = lifecycle.verify_phase(name, result.returncode, read(receipt), request['source_sha'],
                request['input_sha256']['scripts/kicad/run.sh'], 'local-' + request['run_id'] + '-' + str(request['attempt']),
                request['worker'], expected_plan_command=command[command.index('--', 3) + 1:])
            status['status'] = 'PASS BOUNDED STARTUP PHASE ONLY'
        except (ValueError, KeyError, OSError) as error:
            status['reason'] = str(error)
        write(Path(str(receipt) + '.qualification.json'), status)
        return 0 if status['status'].startswith('PASS') else 1
    return result.returncode


def worker(root, env, proc=Path('/proc/self/cgroup'), cgroup=Path('/sys/fs/cgroup')):
    """Recheck after queueing, inside the actual guarded host service."""
    request = authority(root, env, host=True)
    name = request['worker']
    slice_name = 'epic242-w' + name.encode().hex() + '.slice'
    need(env.get('EPIC242_NATIVE_WORKER') == name and env.get('EPIC242_NATIVE_SLICE') == slice_name,
         'local worker/slice differs')
    expected = '0::/epic242.slice/' + slice_name + '/epic242-' + name + '-checks.service'
    need(proc.read_text().strip() == expected, 'worker outside actual guarded service')
    deadline = env.get('EPIC242_NATIVE_DEADLINE', '')
    need(re.fullmatch(r'[0-9]{10}', deadline) and 0 < int(deadline) - time.time() <= request['seconds'],
         'worker deadline expired or exceeds request')
    for path, cap in ((cgroup / 'epic242.slice', LIMITS['aggregate_bytes']),
                      (cgroup / 'epic242.slice' / slice_name, LIMITS['worker_bytes'])):
        need((path / 'memory.max').read_text().strip() == str(cap) and
             (path / 'memory.swap.max').read_text().strip() == '0', 'worker cgroup limits differ')
    return subprocess.run(request['command'], cwd=root, env=env, check=False).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    prep = subs.add_parser('prepare')
    prep.add_argument('--kind', choices=('oracle', 'e16', 'startup-success', 'startup-failure'), required=True)
    prep.add_argument('--output', required=True)
    prep.add_argument('--run-id', required=True)
    prep.add_argument('--attempt', type=int, required=True)
    prep.add_argument('--evidence', required=True)
    prep.add_argument('--stage')
    prep.add_argument('--target', default='python')
    approval = subs.add_parser('approve', help='OPERATOR ONLY: explicit attestation; never called by prepare or execute')
    approval.add_argument('--request', required=True)
    approval.add_argument('--request-sha256', required=True)
    approval.add_argument('--output', required=True)
    approval.add_argument('--operator', required=True)
    approval.add_argument('--reservation-reference', required=True)
    approval.add_argument('--qualification-reference', required=True)
    run = subs.add_parser('execute')
    run.add_argument('--request', required=True)
    run.add_argument('--approval', required=True)
    subs.add_parser('worker', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(ROOT, args.output, args.kind, args.run_id, args.attempt, args.evidence,
                    stage=args.stage, target=args.target)
            print(json.dumps({'status': 'PREPARED; NOT ADMITTED', 'request_sha256': sha(ROOT / args.output)}))
        elif args.action == 'approve':
            approve(ROOT, local_path(ROOT, args.request, cache=True), args.request_sha256, args.output,
                    args.operator, args.reservation_reference, args.qualification_reference)
            print('Operator attestation saved; no execution performed.')
        elif args.action == 'worker':
            return worker(ROOT, dict(os.environ))
        else:
            return execute(ROOT, local_path(ROOT, args.request, cache=True), local_path(ROOT, args.approval, cache=True))
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print('LOCAL NATIVE ADMISSION REFUSED: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
