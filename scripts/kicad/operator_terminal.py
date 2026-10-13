#!/usr/bin/env python3
"""Operator-only PTY authentication after the shared guard's setsid boundary.

No password input/transcript is recorded. Only subsequent workload output is logged.
This helper never approves requests and never changes privilege or resource policy.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

try:
    from . import local_native_admission as admission
except ImportError:
    import local_native_admission as admission

ROOT = Path(__file__).resolve().parents[2]


def check_operator_terminal():
    admission.need(os.isatty(0) and os.isatty(1), 'operator authentication requires a real terminal')
    # Check the controlling terminal, not just inherited terminal file descriptors.
    fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
    os.close(fd)
    admission.need(os.environ.get('HEAVY_GUARD_HELD') == '1', 'operator PTY must be inside shared heavy guard')


def run_in_terminal(command, log, *, refresh_seconds=30):
    check_operator_terminal()
    admission.need(not log.exists(), 'fresh workload log required')
    # Inherited terminal only: never capture/pipe password input or auth output.
    result = subprocess.run(['sudo', '-v'], check=False)
    if result.returncode:
        return result.returncode
    result = subprocess.run(['sudo', '-n', 'systemctl', 'show', '--property=Version', '--value'], check=False)
    if result.returncode:
        return result.returncode
    print('Authentication ready. Workload output: ' + str(log), flush=True)
    process = None
    interrupted = []
    events = []
    def stop(signum, frame):
        interrupted.append(signum)
        if process is not None and process.poll() is None:
            process.terminate()
    old = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    try:
        with log.open('x') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            while True:
                try:
                    code = process.wait(timeout=refresh_seconds if not interrupted else 75)
                    return 1 if interrupted else code
                except subprocess.TimeoutExpired:
                    if interrupted:
                        process.kill()
                        process.wait(timeout=10)
                        return 1
                    # Same controlling PTY; noninteractive refresh cannot request
                    # another password or outlive the guarded producer.
                    try:
                        refreshed = subprocess.run(['sudo', '-n', '-v'], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
                        code = refreshed.returncode
                    except subprocess.SubprocessError:
                        code = 1
                    events.append({'at_unix': time.time(), 'exit_code': code})
                    if code:
                        stop(signal.SIGTERM, None)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=75)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for s, handler in old.items():
            signal.signal(s, handler)
        admission.write(Path(str(log) + '.auth-lifecycle.json'),
                        {'refresh_events': events, 'signals': interrupted, 'password_input_recorded': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--approval')
    parser.add_argument('--control-request-sha256')
    args = parser.parse_args()
    try:
        path = admission.local_path(ROOT, args.request, cache=True)
        if args.control_request_sha256:
            admission.need(args.approval is None, 'control and local approvals must remain separate')
            admission.no_mixed_authority(os.environ)
            request = admission.read(path)
            admission.need(admission.sha(path) == args.control_request_sha256, 'approved control request digest differs')
            admission.need(request['source_sha'] == admission.clean_head(ROOT) and request['checkout'] == str(ROOT), 'control checkout differs')
            admission.need(request['authentication'] == 'operator-pty', 'control request must bind PTY authentication')
            admission.need(request['uid'] == os.getuid(), 'control operator UID differs')
            admission.need(request['heavy_guard_environment'] == admission.heavy_settings(os.environ), 'shared guard configuration differs')
            admission.need(os.environ.get('HEAVY_GUARD_SLOTS', '1') == '1', 'single shared slot required')
            required = {'scripts/kicad/operator_terminal.py', 'scripts/kicad/local_native_admission.py',
                'scripts/kicad/qualify_resource_guard.py', 'scripts/kicad/run_resource_fixture.py',
                'scripts/kicad/fixtures/resource_guard_fixture.c', 'scripts/kicad/native_resource_guard.py',
                'scripts/kicad/run.sh', 'scripts/kicad/pin.env',
                str(Path.home() / '.codex/scripts/heavy-guard.sh')}
            admission.need(set(request['method_sha256']) == required, 'complete control method seals required')
            for name, digest in request['method_sha256'].items():
                admission.need(admission.sha(name) == digest, 'control method changed: ' + name)
            admission.need(request['method_sha256'].get('scripts/kicad/operator_terminal.py') == admission.sha(__file__), 'operator helper seal required')
            import re
            admission.need(re.fullmatch(r'[0-9a-f]{32}', request['local_run_id']) and
                           type(request['attempt']) is int and request['attempt'] > 0, 'control run/attempt required')
            directory = admission.local_path(ROOT, request['evidence_directory'], cache=True)
            admission.need(not directory.exists(), 'control evidence directory already used')
            command = ['python3', 'scripts/kicad/qualify_resource_guard.py', '--admission-id',
                'local-control-' + request['local_run_id'] + '-' + str(request['attempt']),
                '--sha', request['source_sha'], '--hook-sha256', request['method_sha256']['scripts/kicad/run.sh'],
                '--evidence-directory', str(directory)]
            admission.need(request['workload_command'] == command, 'control command differs')
            log = admission.local_path(ROOT, request['driver_log'], cache=True)
            check_operator_terminal()
            admission.claim(request | {'worker': 'local-control-' + request['local_run_id'] + '-' + str(request['attempt'])},
                            args.control_request_sha256, admission.persistent_claim_directory())
        else:
            admission.need(args.approval is not None, 'separate operator approval required')
            approval = admission.local_path(ROOT, args.approval, cache=True)
            request = admission.validate_request(ROOT, path)
            admission.need(request['authentication'] == 'operator-pty', 'PTY request required')
            digest = admission.sha(path)
            admission.validate_approval(ROOT, approval, request, digest)
            claim = admission.persistent_claim_directory() / (request['worker'] + '.json')
            admission.need(admission.read(claim)['request_sha256'] == digest, 'outer launcher claim required')
            check_operator_terminal()
            # A direct invocation cannot repeat the outer launch's authentication.
            admission.write(Path(str(claim) + '.operator-session'), {'request_sha256': digest})
            context = admission.local_context(ROOT, request, path, approval)
            command = admission.guard_command(ROOT, request, context)
            log = admission.local_path(ROOT, request['evidence'], cache=True)
            log = Path(str(log) + '.driver.log')
        return run_in_terminal(command, log)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print('OPERATOR TERMINAL REFUSED: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
