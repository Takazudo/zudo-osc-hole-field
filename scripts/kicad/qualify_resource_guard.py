#!/usr/bin/env python3
"""Opt-in single-worker harmless CI control qualification; never runs KiCad."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

import native_resource_guard as guard

HERE = Path(__file__).resolve().parent


def capability_probe():
    if Path('/proc/1/comm').read_text().strip() != 'systemd':
        raise ValueError('chosen guard needs systemd PID1; no reconfiguration allowed')
    guard.local_docker()
    if 'memory' not in Path('/sys/fs/cgroup/cgroup.controllers').read_text().split():
        raise ValueError('cgroupv2 memory controller absent')
    if guard.memory_available() < guard.CAP + guard.FLOOR:
        raise ValueError('less than8GiB available; cannot reserve6GiB plus2GiB floor')
    guard.run(['sudo', '-n', 'systemctl', 'show', '--property=Version', '--value'])
    guard.run(['cc', '--version'])
    return {'pid1': 'systemd', 'docker': 'local/systemd/cgroupv2/memory+swap',
            'available_bytes': guard.memory_available(), 'no_reconfiguration': True}


def guard_command(args, worker, phase, image, directory):
    seconds = {'smoke': 20, 'timeout': 5, 'parent-death': 30, 'watchdog-death': 30}[phase]
    mode = 'aggregate' if phase == 'smoke' else 'hold'
    return [sys.executable, str(HERE / 'native_resource_guard.py'),
            '--admission-id', args.admission_id, '--worker', worker,
            '--sha', args.sha, '--hook-sha256', args.hook_sha256,
            '--seconds', str(seconds), '--evidence', str(directory / (phase + '.json')),
            '--harmless-fixture-image', image, '--', sys.executable,
            str(HERE / 'run_resource_fixture.py'), '--image', image, '--mode', mode]


def owned_units(worker):
    return ['epic242-' + worker + suffix for suffix in
            ('-checks.service', '-anchor.service', '-watchdog.service')]


def quiet(worker):
    if guard.worker_containers(worker, timeout=3):
        return False
    return all(guard.run(['systemctl', 'show', unit, '--property=ActiveState', '--value'],
                         timeout=3) in ('inactive', 'failed') for unit in owned_units(worker))


def wait_for(worker, predicate, process=None, seconds=60):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        if process is not None and process.poll() is not None:
            raise ValueError('guard terminated before observed running container/watchdog')
        time.sleep(0.25)
    raise ValueError('bounded observation timeout for ' + worker)


def membership(worker, expected_sha, image):
    records = [json.loads(p.read_text()) for p in
               Path('/tmp').glob('epic242-' + worker + '-*/membership.json')]
    if len(records) != 1:
        return None
    record = records[0]
    expected_slice = '/epic242.slice/epic242-w' + worker.encode().hex() + '.slice'
    if record.get('worker') != worker or record.get('sha') != expected_sha or record.get('image_id') != image or record.get('slice_path') != expected_slice:
        raise ValueError('guard membership handshake differs from admitted identity')
    return record


def ready(worker, expected_sha, image):
    watch = owned_units(worker)[2]
    if guard.run(['systemctl', 'show', watch, '--property=ActiveState', '--value'], timeout=3) != 'active':
        return False
    record = membership(worker, expected_sha, image)
    if not record:
        return False
    state = json.loads(guard.run(['docker', 'inspect', record['container_id']], timeout=3))[0]['State']
    return state['Running']


def phase_result(phase, code, evidence, watch_results, is_quiet, fault=None):
    if not is_quiet:
        raise ValueError('owned service/container survivors after ' + phase)
    if phase == 'smoke':
        if code or not evidence.get('status', '').startswith('COMMAND PASS') or not evidence.get('observed_containers'):
            raise ValueError('membership smoke did not establish observed shared-worker container')
    elif phase == 'parent-death':
        if code != -9 or not fault or not watch_results or any(r.get('cleanup_failures') or r.get('reason') not in ('parent guard identity missing', 'parent guard identity changed') or r.get('parent_pid') != fault.get('pid') or r.get('parent_start') != fault.get('proc_start') or r.get('finished_at', 0) < fault.get('injected_at', 0) for r in watch_results):
            raise ValueError('independent watchdog did not retain clean parent-death termination')
    else:
        if not code or not evidence.get('observed_containers') or evidence.get('status', '').startswith('COMMAND PASS') or evidence.get('cleanup_failures'):
            raise ValueError('fault phase must fail closed and clean up: ' + phase)
        if phase == 'watchdog-death' and evidence.get('reason') != 'independent watchdog not active':
            raise ValueError('supervisor death must trigger guard refusal')
        if phase == 'timeout' and evidence.get('reason') != 'whole-command deadline' and not any(r.get('reason') == 'whole-command deadline' for r in watch_results):
            raise ValueError('deadline case failed for an unrelated reason')
    return {'expected_fault': phase != 'smoke', 'exit_code': code,
            'status': 'PASS_HARMLESS_CONTROL_CASE', 'guard_evidence': evidence,
            'watchdog_evidence': watch_results, 'owned_survivors': False}


def qualify(args):
    directory = Path(args.evidence_directory)
    if directory.exists():
        raise ValueError('fresh evidence directory required')
    directory.mkdir(parents=True)
    report = {'status': 'FAIL', 'native_execution': False, 'global_workers_requested': 1,
              'sha': args.sha, 'hook_sha256': args.hook_sha256, 'phases': {},
              'limits': 'single-worker chosen systemd implementation only; no two-worker qualification or electrical acceptance'}
    image = None
    workers = []
    process = None
    active_worker = None
    try:
        if not args.admission_id or not re.fullmatch(r'[0-9a-f]{40}', args.sha):
            raise ValueError('exact SHA and explicit parent admission required')
        if guard.run(['git', 'rev-parse', 'HEAD']) != args.sha or guard.run(['git', 'status', '--porcelain', '--untracked-files=no']):
            raise ValueError('clean checkout differs from reviewed SHA')
        if hashlib.sha256((HERE / 'run.sh').read_bytes()).hexdigest() != args.hook_sha256:
            raise ValueError('reviewed hook digest differs')
        report['capabilities'] = capability_probe()  # BEFORE image/units/control mutation
        with tempfile.TemporaryDirectory(prefix='epic242-harmless-build-') as tmp:
            tmp = Path(tmp)
            source = HERE / 'fixtures/resource_guard_fixture.c'
            binary = tmp / 'fixture'
            guard.run(['cc', '-Os', '-static', '-o', str(binary), str(source)])
            archive = tmp / 'rootfs.tar'
            with tarfile.open(archive, 'w') as tar:
                tar.add(binary, arcname='fixture')
            image = guard.run(['docker', 'image', 'import', '--change', 'ENTRYPOINT ["/fixture"]', '--change', 'LABEL epic242.qualifier=' + uuid.uuid4().hex, str(archive)])
            report['fixture'] = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                                 'image_id': image, 'compiler': guard.run(['cc', '--version']).splitlines()[0]}
            prefix = 'q-' + uuid.uuid4().hex[:10]
            for phase in ('smoke', 'timeout', 'parent-death', 'watchdog-death'):
                worker = prefix + '-' + phase
                workers.append(worker)
                active_worker = worker
                command = guard_command(args, worker, phase, image, directory)
                fault = None
                with (directory / (phase + '.stdout.txt')).open('w') as log:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                    if phase in ('timeout', 'parent-death', 'watchdog-death'):
                        wait_for(worker, lambda: ready(worker, args.sha, image), process, seconds=20)
                        if phase == 'parent-death':
                            fault = {'pid': process.pid, 'proc_start': guard.process_identity(process.pid), 'injected_at': time.time(), 'signal': 'SIGKILL', 'target': 'owned parent frontend'}
                            process.kill()  # only this owned Python frontend
                        elif phase == 'watchdog-death':
                            fault = {'unit': owned_units(worker)[2], 'injected_at': time.time(), 'signal': 'SIGKILL', 'target': 'owned watchdog'}
                            guard.run(['sudo', '-n', 'systemctl', 'kill', '--signal=SIGKILL', owned_units(worker)[2]], timeout=3)
                    code = process.wait(timeout=75)
                process = None
                wait_for(worker, lambda: quiet(worker), seconds=60)
                # Parent death is checked through the independent watchdog's own receipt.
                watch_results = [json.loads(p.read_text()) for p in
                                 Path('/tmp').glob('epic242-' + worker + '-*/watchdog.json.result')]
                evidence_path = directory / (phase + '.json')
                evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
                report['phases'][phase] = phase_result(phase, code, evidence, watch_results, True, fault)
                report['phases'][phase]['fault_injection'] = fault
                report['phases'][phase]['verified_membership'] = membership(worker, args.sha, image)
                report['phases'][phase]['guard_stdout'] = (directory / (phase + '.stdout.txt')).read_bytes()[:65536].decode('utf-8', errors='replace')
                active_worker = None
            report['status'] = 'PASS_SINGLE_WORKER_HARMLESS_CONTROL_QUALIFICATION'
    except Exception as error:
        report['reason'] = str(error)
    finally:
        failures = []
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        # Cleanup only a worker actually started by this driver, never a prior label.
        if active_worker:
            failures.extend(guard.cleanup(active_worker, [owned_units(active_worker)[0]], owned_units(active_worker)[1]))
        for worker in workers:
            try:
                wait_for(worker, lambda: quiet(worker), seconds=60)
                if not quiet(worker):
                    failures.append('owned survivors: ' + worker)
                else:
                    watch = owned_units(worker)[2]
                    if guard.run(['systemctl', 'show', watch, '--property=ActiveState', '--value'], timeout=3) == 'active':
                        guard.run(['sudo', '-n', 'systemctl', 'stop', watch], timeout=3)
            except Exception as error:
                failures.append(str(error))
        if image:
            try:
                guard.run(['docker', 'image', 'rm', image], timeout=3)
            except Exception as error:
                failures.append('owned image cleanup: ' + str(error))
        if failures:
            report['cleanup_failures'] = failures
            report['status'] = 'FAIL_CLEANUP'
        # Retain raw evidence even when a phase's acceptance check failed.
        report['raw_phase_evidence'] = {}
        for phase, worker in zip(('smoke', 'timeout', 'parent-death', 'watchdog-death'), workers):
            raw = {'worker': worker}
            for filename, key in ((phase + '.json', 'guard_receipt'), (phase + '.stdout.txt', 'guard_stdout')):
                path = directory / filename
                if path.exists():
                    try:
                        raw[key] = json.loads(path.read_text()) if key == 'guard_receipt' else path.read_bytes()[:65536].decode('utf-8', errors='replace')
                    except Exception as error:
                        raw[key + '_read_error'] = str(error)
            for pattern, key in (('membership.json', 'membership'), ('watchdog.json.result', 'watchdog')):
                try:
                    raw[key] = [json.loads(p.read_text()) for p in Path('/tmp').glob('epic242-' + worker + '-*/' + pattern)]
                except Exception as error:
                    raw[key + '_read_error'] = str(error)
            report['raw_phase_evidence'][phase] = raw
        report['owned_image_removed'] = bool(image) and not failures
        (directory / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['status'].startswith('PASS_SINGLE') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission-id', required=True)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--hook-sha256', required=True)
    parser.add_argument('--evidence-directory', required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(qualify(args))
    except ValueError as error:
        print('QUALIFICATION REFUSED: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
