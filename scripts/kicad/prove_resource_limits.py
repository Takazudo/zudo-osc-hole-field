#!/usr/bin/env python3
"""Explicit harmless Docker kernel proof; never pulls/runs the KiCad image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
LIMIT = 64 * 1024 * 1024


def run(args, timeout=10):
    return subprocess.run(args, check=True, text=True, capture_output=True, timeout=timeout).stdout.strip()


def proof(destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('fresh evidence file required')
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
        raise ValueError('custom Docker endpoint refused')
    endpoint = json.loads(run(['docker', 'context', 'inspect']))[0]['Endpoints']['docker']['Host']
    if endpoint != 'unix:///var/run/docker.sock':
        raise ValueError('requires local daemon')
    info = json.loads(run(['docker', 'info', '--format', '{{json .}}']))
    if not info.get('MemoryLimit') or not info.get('SwapLimit') or str(info.get('CgroupVersion')) != '2':
        raise ValueError('requires actual memory/swap controls and cgroupv2')
    if not shutil.which('cc'):
        raise ValueError('C compiler absent; no install or fallback')
    available = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    if available < 3 * 1024 ** 3:
        raise ValueError('less than3GiB available; preserve2GiB free floor')
    tag = 'epic242-guard-proof:' + uuid.uuid4().hex
    container_ids = []
    image_created = False
    receipt = {'status': 'FAIL', 'native_kicad_execution': False,
               'scope': 'Docker kernel controls only, not systemd whole-worker qualification',
               'memory_limit_bytes': LIMIT, 'memory_swap_limit_bytes': LIMIT,
               'daemon': {k: info[k] for k in ('CgroupDriver', 'CgroupVersion', 'MemoryLimit', 'SwapLimit', 'ServerVersion')}}
    try:
        with tempfile.TemporaryDirectory(prefix='epic242-control-proof-') as tmp:
            tmp = Path(tmp)
            source = HERE / 'fixtures/resource_guard_fixture.c'
            binary = tmp / 'fixture'
            run(['cc', '-Os', '-static', '-o', str(binary), str(source)])
            archive = tmp / 'rootfs.tar'
            with tarfile.open(archive, 'w') as tar:
                tar.add(binary, arcname='fixture')
            receipt['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            receipt['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
            receipt['compiler'] = run(['cc', '--version']).splitlines()[0]
            receipt['image_digest'] = run(['docker', 'image', 'import', '--change', 'ENTRYPOINT ["/fixture"]', str(archive), tag])
            image_created = True
            def create(mode):
                cid = run(['docker', 'create', '--network', 'none', '--memory', str(LIMIT),
                           '--memory-swap', str(LIMIT), '--cpus', '0.5', '--pids-limit', '8',
                           tag, mode])
                container_ids.append(cid)
                return cid
            aggregate = create('aggregate')
            started = time.monotonic()
            result = subprocess.run(['docker', 'start', '-a', aggregate], text=True, capture_output=True, timeout=8)
            observed = json.loads(run(['docker', 'inspect', aggregate]))[0]
            state = observed['State']
            if observed['HostConfig']['Memory'] != LIMIT or observed['HostConfig']['MemorySwap'] != LIMIT:
                raise ValueError('actual container caps differ')
            if result.returncode != 70 or not state['OOMKilled'] or state['Running'] or state['Pid']:
                raise ValueError('aggregate80MiB child allocation did not fail under64MiB cap')
            receipt['aggregate'] = {'elapsed_seconds': time.monotonic() - started, 'exit_code': result.returncode,
                                    'oom_killed': state['OOMKilled'], 'stdout': result.stdout, 'stderr': result.stderr}
            hold = create('hold')
            started = time.monotonic()
            controller = subprocess.Popen(['docker', 'start', '-a', hold], text=True,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                controller.communicate(timeout=1)
                raise ValueError('hold process tree completed before deadline')
            except subprocess.TimeoutExpired:
                run(['docker', 'kill', '--signal', 'KILL', hold], timeout=3)
                stdout, stderr = controller.communicate(timeout=3)
            observed = json.loads(run(['docker', 'inspect', hold]))[0]
            state = observed['State']
            if state['Running'] or state['Pid'] != 0 or state['ExitCode'] != 137:
                raise ValueError('timeout process-tree cleanup not confirmed')
            receipt['timeout'] = {'elapsed_seconds': time.monotonic() - started, 'exit_code': state['ExitCode'],
                                  'running': state['Running'], 'init_pid': state['Pid'], 'stdout': stdout, 'stderr': stderr}
            receipt['status'] = 'PASS_HARMLESS_DOCKER_KERNEL_CONTROL_PROOF'
    except Exception as error:
        receipt['reason'] = str(error)
    finally:
        failures = []
        for cid in container_ids:
            try:
                run(['docker', 'rm', '-f', cid], timeout=3)
            except Exception as error:
                failures.append(str(error))
        if image_created:
            try:
                run(['docker', 'image', 'rm', tag], timeout=3)
            except Exception as error:
                failures.append(str(error))
        if failures:
            receipt['status'] = 'FAIL_CLEANUP'
            receipt['cleanup_failures'] = failures
        else:
            receipt['owned_containers_and_image_removed'] = True
        destination.write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if receipt['status'].startswith('PASS') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-harmless-proof', action='store_true', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(proof(args.evidence))
    except Exception as error:
        print('PROOF REFUSAL: ' + str(error))
        raise SystemExit(1)
