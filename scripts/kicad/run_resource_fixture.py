#!/usr/bin/env python3
"""Tiny static fixture only; no KiCad, network, image pull or native fallback."""
import argparse
import os
import re
import subprocess
import time


def fixture_command(image, mode, env):
    worker = env.get('EPIC242_NATIVE_WORKER', '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', worker):
        raise ValueError('bounded worker missing')
    parent = 'epic242-w' + worker.encode('ascii').hex() + '.slice'
    if env.get('EPIC242_NATIVE_SLICE') != parent:
        raise ValueError('fixture slice differs from admitted worker')
    deadline = env.get('EPIC242_NATIVE_DEADLINE', '')
    if not deadline.isdecimal() or not 0 < int(deadline) - time.time() <= 2580:
        raise ValueError('fixture deadline absent/expired')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image) or mode not in ('aggregate', 'hold'):
        raise ValueError('immutable reviewed fixture image/mode required')
    if env.get('DOCKER_HOST') or env.get('DOCKER_CONTEXT'):
        raise ValueError('remote Docker refused')
    return ['docker', 'run', '--rm', '--pull=never', '--network=none', '--cpus=0.5',
            '--pids-limit=16', '--memory=6442450944', '--memory-swap=6442450944',
            '--cgroup-parent=' + parent, '--label', 'epic242.native.worker=' + worker,
            image, mode]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--mode', choices=('aggregate', 'hold'), required=True)
    args = parser.parse_args()
    try:
        command = fixture_command(args.image, args.mode, os.environ)
    except ValueError as error:
        parser.error(str(error))
    raise SystemExit(subprocess.run(command, check=False).returncode)
