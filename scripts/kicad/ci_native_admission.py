#!/usr/bin/env python3
"""Fail-closed CI entry to the separately admitted native worker guard."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def admitted_command(env, head, args):
    run_id = env.get('GITHUB_RUN_ID', '')
    attempt = env.get('GITHUB_RUN_ATTEMPT', '')
    admitted_id = env.get('EPIC242_PARENT_ADMISSION_RUN_ID', '')
    admitted_sha = env.get('EPIC242_PARENT_ADMISSION_SHA', '')
    github_sha = env.get('GITHUB_SHA', '')
    hook_digest = env.get('EPIC242_REVIEWED_HOOK_SHA256', '')
    if not run_id.isdecimal() or not attempt.isdecimal() or not admitted_id or admitted_id != run_id:
        raise ValueError('parent admission must name this exact GitHub run ID')
    if not re.fullmatch(r'[0-9a-f]{40}', admitted_sha) or admitted_sha != github_sha or admitted_sha != head:
        raise ValueError('parent admission SHA must equal GitHub SHA and checked-out HEAD')
    if not re.fullmatch(r'[0-9a-f]{64}', hook_digest):
        raise ValueError('reviewed hook SHA-256 is required')
    if args.phase == 'python':
        suffix = 'python'
        if args.seconds != 1680:
            raise ValueError('Python native deadline must be 28 minutes')
    else:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,30}', args.board or ''):
            raise ValueError('invalid board identity')
        suffix = args.board
        if args.seconds != 2580:
            raise ValueError('board native deadline must be 43 minutes')
    worker = 'ci-' + run_id + '-' + attempt + '-' + suffix
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', worker):
        raise ValueError('worker identity exceeds supported length')
    if not args.command:
        raise ValueError('exact command required')
    return [sys.executable, str(Path(__file__).with_name('native_resource_guard.py')),
            '--admission-id', admitted_id, '--worker', worker, '--sha', admitted_sha,
            '--hook-sha256', hook_digest, '--seconds', str(args.seconds),
            '--evidence', args.evidence, '--', *args.command]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('python', 'board'), required=True)
    parser.add_argument('--board')
    parser.add_argument('--seconds', type=int, required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ['--']:
        args.command = args.command[1:]
    try:
        head = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, text=True,
                              capture_output=True, timeout=5).stdout.strip()
        command = admitted_command(os.environ, head, args)
    except (ValueError, subprocess.SubprocessError) as error:
        print('NATIVE ADMISSION REFUSED: ' + str(error), file=sys.stderr)
        return 1
    return subprocess.run(command, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
