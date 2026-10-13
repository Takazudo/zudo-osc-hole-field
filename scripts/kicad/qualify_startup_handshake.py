#!/usr/bin/env python3
"""One admitted CI job: two sequential, short KiCad-oracle lifecycle checks."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.kicad import native_resource_guard as guard
from scripts.kicad.settle_only_pilot import prepare_image


def validate(env):
    sha = env.get('REVIEWED_COMMIT', '')
    hook = env.get('REVIEWED_HOOK_SHA256', '')
    if not re.fullmatch(r'[0-9a-f]{40}', sha) or guard.run(['git', 'rev-parse', 'HEAD']) != sha:
        raise ValueError('exact reviewed checkout required')
    if env.get('GITHUB_SHA') != sha:
        raise ValueError('workflow SHA differs from reviewed checkout')
    if not re.fullmatch(r'[0-9a-f]{64}', hook) or hashlib.sha256((ROOT / 'scripts/kicad/run.sh').read_bytes()).hexdigest() != hook:
        raise ValueError('reviewed hook digest differs')
    admission = guard.identity(env.get('PARENT_ADMISSION_ID', ''))
    if env.get('REQUEST_BOARD') != 'osc-core' or env.get('CONFLICTING_MODES') != 'false':
        raise ValueError('only exclusive osc-core lifecycle mode permitted')
    if guard.run(['git', 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tracked checkout dirty')
    run_id, attempt = env.get('GITHUB_RUN_ID', ''), env.get('GITHUB_RUN_ATTEMPT', '')
    if not run_id.isdecimal() or not attempt.isdecimal():
        raise ValueError('GitHub run identity required')
    prefix = guard.identity('life-' + run_id + '-' + attempt)
    return sha, hook, admission, prefix


def guard_command(sha, hook, admission, worker, evidence, failing):
    return [sys.executable, 'scripts/kicad/native_resource_guard.py',
            '--admission-id', admission, '--worker', guard.identity(worker),
            '--sha', sha, '--hook-sha256', hook, '--seconds', '60',
            '--evidence', str(evidence), '--',
            'bash', 'scripts/kicad/run.sh', '/bin/false' if failing else 'kicad-cli',
            *([] if failing else ['version'])]


def verify_phase(name, code, receipt, sha, hook, admission_id, worker, *, expected_plan_command=None):
    failing = name == 'intentional-failure'
    command = ['bash', 'scripts/kicad/run.sh', '/bin/false' if failing else 'kicad-cli',
               *([] if failing else ['version'])]
    plan = receipt.get('plan', {})
    if (plan.get('sha') != sha or plan.get('hook_sha256') != hook or
            plan.get('admission_id') != admission_id or plan.get('worker') != worker or
            plan.get('seconds') != 60 or plan.get('command') != (command if expected_plan_command is None else expected_plan_command) or
            plan.get('memory_max') != guard.CAP or
            plan.get('aggregate_memory_max') != guard.AGGREGATE_CAP):
        raise ValueError(name + ': reviewed source, admission, command or resource plan differs')
    if code != (1 if failing else 0):
        raise ValueError(name + ': guard exit differs from expected case')
    if receipt.get('status') != ('FAIL / NOT ACCEPTED' if failing else
                                 'COMMAND PASS ONLY; native acceptance requires exact complete evidence'):
        raise ValueError(name + ': guard status differs')
    if receipt.get('cleanup_failures') or receipt.get('watchdog'):
        raise ValueError(name + ': cleanup or watchdog failure')
    if receipt.get('pre_cleanup_state_errors'):
        raise ValueError(name + ': pre-cleanup state snapshot incomplete')
    if receipt.get('final_owned_state', {}).get('workload_absent') is not True:
        raise ValueError(name + ': final worker absence unproved')
    if receipt.get('memory_before_cleanup', {}).get('status') != 'OBSERVED':
        raise ValueError(name + ': kernel memory evidence missing')
    admissions = receipt.get('container_admissions', {})
    memberships = receipt.get('container_memberships', {})
    states = receipt.get('container_states', {})
    if len(admissions) != 2 or set(admissions) != set(memberships) or set(admissions) != set(states):
        raise ValueError(name + ': both short-lived helpers need exact admission and exit evidence')
    if set(receipt.get('observed_containers', [])) != set(admissions):
        raise ValueError(name + ': observed full IDs differ')
    expected_slice = 'epic242-w' + worker.encode().hex() + '.slice'
    exit_codes = []
    for cid, admission in admissions.items():
        request = admission['request']
        state = states[cid]
        membership = memberships[cid]
        expected_code = 1 if request.get('command') == ['/bin/false'] and failing else 0
        if request.get('command') not in ([['kicad-cli', 'version'], ['/bin/false']] if failing
                                          else [['kicad-cli', 'version']]):
            raise ValueError(name + ': helper command differs from reviewed request')
        if (not re.fullmatch(r'[0-9a-f]{64}', cid) or request.get('container_id') != cid or
                request.get('worker') != worker or admission.get('ack') != request.get('token', '') + ':' + cid or
                membership.get('worker') != worker or membership.get('container_id') != cid or
                membership.get('host_config') != {'Memory': guard.CAP, 'MemorySwap': guard.CAP,
                                                   'CgroupParent': expected_slice} or
                not membership.get('cgroup', '').startswith('0::/epic242.slice/' + expected_slice + '/') or
                state.get('Running') or state.get('Status') != 'exited' or
                state.get('OOMKilled') or state.get('Error')):
            raise ValueError(name + ': identity or retained terminal state differs')
        if state.get('ExitCode') != expected_code:
            raise ValueError(name + ': exit status differs for bound helper command')
        exit_codes.append(expected_code)
    commands = [value['request']['command'] for value in admissions.values()]
    expected = [['kicad-cli', 'version'], ['/bin/false'] if failing else ['kicad-cli', 'version']]
    if sorted(commands) != sorted(expected):
        raise ValueError(name + ': helper command inventory differs')
    codes = sorted(exit_codes)
    if codes != ([0, 1] if failing else [0, 0]):
        raise ValueError(name + ': retained exit codes differ')
    if failing:
        reason = receipt.get('reason', '')
        if 'terminal state' not in reason and 'native command nonzero exit' not in reason:
            raise ValueError('intentional failure reason is unrelated to command exit')
    elif receipt.get('exit_code') != 0:
        raise ValueError('successful driver exit missing')
    return {'guard_exit_code': code, 'container_ids': sorted(admissions),
            'retained_exit_codes': codes, 'final_workload_absent': True}


def execute(env):
    directory = Path(env['RUNNER_TEMP']) / 'epic242-startup-lifecycle'
    if directory.is_symlink():
        raise ValueError('lifecycle evidence directory is a symlink')
    directory.mkdir(exist_ok=True)
    receipt_path = directory / 'lifecycle.json'
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ValueError('lifecycle receipt exists; no overwrite')
    summary = {'status': 'BLOCKED / NOT QUALIFIED', 'source_sha': env.get('REVIEWED_COMMIT'),
               'hook_sha256': env.get('REVIEWED_HOOK_SHA256'), 'phases': {},
               'scope': 'two sequential guarded short-lived helpers; no board routing or native acceptance'}
    try:
        sha, hook, admission, prefix = validate(env)
        summary['admission_id'] = admission
        summary['image_preparation'] = prepare_image(directory)
        for name, failing in (('success', False), ('intentional-failure', True)):
            worker = prefix + ('-fail' if failing else '-ok')
            evidence = directory / (name + '.json')
            command = guard_command(sha, hook, admission, worker, evidence, failing)
            phase = {'worker': worker, 'command': command, 'guard_receipt': evidence.name,
                     'driver_log': name + '.log', 'status': 'NOT RUN'}
            summary['phases'][name] = phase
            with (directory / phase['driver_log']).open('x') as output:
                code = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT).returncode
            phase['guard_exit_code'] = code
            phase['status'] = 'NEGATIVE / UNVERIFIED'
            checked = verify_phase(name, code, json.loads(evidence.read_text()),
                                   sha, hook, admission, worker)
            phase.update(checked, status='PASS EXPECTED FAILURE' if failing else 'PASS SHORT SUCCESS')
        summary['status'] = 'PASS BOUNDED STARTUP/EXIT LIFECYCLE ONLY'
    except Exception as error:
        summary['reason'] = str(error)
    finally:
        receipt_path.write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['status'].startswith('PASS BOUNDED') else 1


if __name__ == '__main__':
    if sys.argv[1:] != ['run']:
        raise SystemExit('usage: qualify_startup_handshake.py run')
    raise SystemExit(execute(os.environ))
