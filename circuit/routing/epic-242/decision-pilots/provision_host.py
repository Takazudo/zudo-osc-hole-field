#!/usr/bin/env python3
"""Provision an isolated CI host from frozen sources; never execute a route."""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
METHOD = '29140d4e19d526eed3a02a73c33f8ce4219c78f0'
PROVISION_SOURCES = {
    'scripts/pcbgen/with_route_guard.sh': '29afbe134f0a3c196ab01482382f3042ac32ce5c825ea0728eb416c536ff383e',
    'scripts/kicad/settle_only_pilot.py': '8bf1e311e08554501e33e099cff164b69704f81df0aabe91cd980fd5fd98b531',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def command(argv, cwd):
    return subprocess.check_output(argv, cwd=cwd, text=True, timeout=30).strip()


def verify_sources(method, packet):
    require(packet['source_commit'] == METHOD, 'method epoch changed')
    require(command(['git','rev-parse','HEAD'], method) == METHOD, 'exact method checkout required')
    require(not command(['git','status','--porcelain','--untracked-files=no'], method), 'tracked method checkout dirty')
    expected = dict(packet['input_file_sha256'])
    for path, digest in PROVISION_SOURCES.items():
        require(expected.get(path) == digest, 'provisioning source binding changed: '+path)
    for path, digest in expected.items():
        require(hashlib.sha256((method/path).read_bytes()).hexdigest() == digest, 'method file changed: '+path)
    return expected


def route_plan(method, python, fixture, evidence, packet):
    """Reviewable argv only. This module has no route execution branch."""
    require(Path(python).is_absolute(), 'execution-host Python must be absolute')
    require(not evidence.exists() and not evidence.is_symlink(), 'native evidence must be a NEW JSON FILE')
    require(evidence.suffix == '.json', 'native evidence must name a JSON file')
    require(not fixture.exists() and not fixture.is_symlink(), 'fixture must be a new private path')
    payload = ['bash','-c','bash scripts/kicad/run.sh kicad-cli version && exec "$@"',
               'epic242-route-probe',python,
               'circuit/routing/epic-242/decision-pilots/route_matched.py',
               '--domain','O1','--board','K1402','--fixture',str(fixture)]
    wrapper = ['bash','scripts/pcbgen/with_route_guard.sh',python,
               'scripts/kicad/native_resource_guard.py',
               '--admission-id','renewal-required-not-admitted',
               '--worker','renewal-worker-not-reserved','--sha',METHOD,
               '--hook-sha256',packet['input_file_sha256']['scripts/kicad/run.sh'],
               '--seconds','300','--evidence',str(evidence)]
    return {'status':'PLAN ONLY; RENEWED PARENT ADMISSION REQUIRED', 'cwd':str(method),
            'argv':wrapper+payload, 'native_seconds_including_both_probes':300,
            'python':python, 'six_zip_inputs':packet['preparation_artifacts'],
            'required_before_execution':['new parent admission and global capacity reservation',
                'new exact clean method checkout and execution-host version binding',
                'repeat trusted provisioning on actual execution host',
                'authenticate all six complete ZIPs and prepare exact O1/K1402 fixture',
                'verify fixture lock and immutable before hashes before route',
                'replace admission/worker placeholders with new parent-bound identities'],
            'required_after_execution':['both full-ID probe ACK/membership/retained successful exits',
                'proposal/diagnostics/logs even on failure', 'unchanged before hashes',
                'full guard memory/deadline/cleanup receipt'],
            'forbidden':'No two-A/apply/settle/fresh/audit, retries, cuts, wider bounds or fallback'}


def provision(method, evidence, packet):
    receipt = {'status':'BLOCKED', 'route_status':'NOT STARTED / NOT ADMITTED',
               'native_workers_started':0, 'probe_containers_started':0,
               'workflow_run_id':os.environ.get('GITHUB_RUN_ID'),
               'workflow_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
               'orchestration_sha':os.environ.get('GITHUB_SHA'),
               'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'source_hashes':verify_sources(method, packet)}
    try:
        require(os.environ.get('GITHUB_ACTIONS') == 'true' and
                os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted',
                'provisioning requires the existing GitHub-hosted dispatch policy')
        require(Path('/proc/1/comm').read_text().strip() == 'systemd', 'systemd PID1 required')
        require('memory' in Path('/sys/fs/cgroup/cgroup.controllers').read_text().split(), 'cgroupv2 memory required')
        command(['sudo','-n','true'], method)
        receipt['python'] = {'path':sys.executable,'version':sys.version,
                             'packages':{name:version(name) for name in ('numpy','scipy','shapely')}}
        require(receipt['python']['packages'] == packet['python']['versions'], 'numerical dependency version drift')
        # Import only after exact immutable-source validation, from the method checkout.
        sys.path.insert(0,str(method))
        from scripts.kicad import native_resource_guard as guard
        from scripts.kicad.settle_only_pilot import prepare_image
        require(Path(guard.__file__).resolve() == method/'scripts/kicad/native_resource_guard.py', 'guard imported from wrong checkout')
        os.chdir(method)
        guard.local_docker()
        receipt['dispatch'] = {'wrapper':'scripts/pcbgen/with_route_guard.sh',
                               'policy':'github-hosted direct dispatch; native guard still mandatory',
                               'GITHUB_ACTIONS':os.environ['GITHUB_ACTIONS'],
                               'RUNNER_ENVIRONMENT':os.environ['RUNNER_ENVIRONMENT']}
        receipt['image_preparation'] = prepare_image(evidence.parent)
        receipt['local_image'] = guard.require_local_image()
        receipt['source_hashes_after'] = verify_sources(method, packet)
        receipt['free_bytes_after'] = guard.memory_available()
        require(receipt['free_bytes_after'] >= guard.CAP+guard.FLOOR, 'less than8GiB free after preparation')
        receipt['status'] = 'PROVISIONING PASS ONLY; NO NATIVE ADMISSION OR EXECUTION'
        fixture = method/'design/partition/core-split/candidates/pilots/generated/o1-k1402-renewal-fixture'
        receipt['future_route_plan'] = route_plan(method,sys.executable,fixture,evidence.parent/'future-native-guard.json',packet)
    except Exception as exc:
        receipt['error'] = str(exc)
        raise
    finally:
        receipt['cleanup_scope'] = 'No native workload/units/containers created. Image preparation retains its own daemon-accounting/client outcome; failure never implies daemon cleanup.'
        evidence.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    require(not args.evidence.is_symlink(),'evidence symlink forbidden')
    method=args.method.resolve();evidence=args.evidence.resolve()
    require(not evidence.exists() and not evidence.is_symlink(),'new provisioning JSON file required')
    require(evidence.suffix == '.json','provisioning evidence must be JSON file')
    evidence.parent.mkdir(parents=True,exist_ok=True)
    try:
        packet=json.loads((HERE/'minimum-native-request.json').read_text())
        result=provision(method,evidence,packet)
    except Exception as exc:
        if not evidence.exists():
            evidence.write_text(json.dumps({'status':'BLOCKED','error':str(exc),
                'route_status':'NOT STARTED / NOT ADMITTED','native_workers_started':0,
                'probe_containers_started':0},indent=2)+'\n')
        print(str(exc),file=sys.stderr)
        return 1
    print(json.dumps({'status':result['status'],'python':result['python'],
                     'native_workers_started':0,'probe_containers_started':0},indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
