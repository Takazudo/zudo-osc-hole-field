#!/usr/bin/env python3
"""One separately admitted F3/K1402 route using the frozen method and packet."""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
REQUEST_ROOT = HERE.parents[4]
METHOD = '6f0783335fa23d760877a91db3b63f93c039b4b4'
PACKET_SHA = '10be49ae32997a36c54436e48226a295678e47dda1fc1c14f4569c72ef4bdd92'
REPOSITORY = 'Takazudo/zudo-osc-hole-field'
BRANCH = 'integration/epic-242-f3-k1402-access-v1'
WORKFLOW = 'epic242-f3-k1402-access.yml'
# Proposed identity only. Publishing this source does not grant admission.
ADMISSION = 'epic242-f3-k1402-route-20261011-1623'
DRIVER = 'circuit/routing/epic-242/decision-pilots/terminal-access/'


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value, indent=2)+'\n')
def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(argv, cwd=None, timeout=30):
    return subprocess.check_output(argv, cwd=cwd, text=True, timeout=timeout).strip()


def fresh(path):
    require(not path.exists() and not path.is_symlink(), 'existing evidence/path; no retry: '+str(path))


def historical_evidence(method, packet):
    name = DRIVER+'cohort-validation.json'
    commit = packet['cohort_evidence_commit']
    raw = subprocess.check_output(['git','show',commit+':'+name], cwd=method, timeout=30)
    sha = hashlib.sha256(raw).hexdigest()
    require(sha == packet['input_file_sha256'][name], 'historical cohort evidence hash mismatch')
    return {'commit':commit, 'path':name, 'sha256':sha, 'status':'AVAILABLE AND AUTHENTICATED'}


def verify_sources(method, packet):
    require(packet['source_commit'] == METHOD, 'wrong packet method')
    require(command(['git','rev-parse','HEAD'], method) == METHOD, 'exact method checkout required')
    require(not command(['git','status','--porcelain','--untracked-files=no'], method), 'dirty method checkout')
    expected = packet['input_file_sha256'] | packet['orchestration_control_sha256']
    for name, sha in expected.items():
        require(digest(method/name) == sha, 'method/control hash mismatch: '+name)
    historical_evidence(method, packet)  # Fail before provisioning if checkout lacks history.
    return expected


def identity():
    require(os.environ.get('PARENT_ADMISSION_ID') == ADMISSION, 'new exact parent admission required')
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY and os.environ.get('GITHUB_REF_NAME') == BRANCH, 'exact isolated K1402 branch required')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted', 'hosted runner required')
    run = os.environ.get('GITHUB_RUN_ID', '')
    require(run.isdecimal() and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'first attempt only; no retry')
    require(os.environ.get('GITHUB_EVENT_NAME') == 'push' and read(Path(os.environ['GITHUB_EVENT_PATH'])).get('created') is True, 'branch-creation push only')
    require(command(['git','rev-parse','HEAD'], REQUEST_ROOT) == os.environ.get('GITHUB_SHA'), 'orchestration checkout mismatch')
    require(not command(['git','status','--porcelain','--untracked-files=no'], REQUEST_ROOT), 'dirty orchestration checkout')
    return {'run_id':run, 'attempt':'1', 'orchestration_sha':os.environ['GITHUB_SHA'],
            'worker':'f3-k1402-access-v1-'+run+'-1', 'admission_id':ADMISSION}


def request(method, evidence, initializing=False):
    ident = identity()
    packet_path = HERE/'f3-packet/request.json'
    require(digest(packet_path) == PACKET_SHA, 'immutable packet digest mismatch')
    packet = read(packet_path)
    verify_sources(method, packet)
    if not initializing:
        require(read(evidence/'one-shot.json') == ident, 'one-shot launch receipt mismatch')
    return packet, ident


def initialize(method, evidence):
    packet, ident = request(method, evidence, initializing=True)
    # Detect recreation of an old branch as well as a rerun of this Actions run.
    url = f'repos/{REPOSITORY}/actions/runs?branch={BRANCH}&event=push&per_page=100'
    runs = json.loads(command(['gh','api',url]))
    require(runs['total_count'] == len(runs['workflow_runs']), 'incomplete branch run census')
    own = [r for r in runs['workflow_runs'] if r['path'] == '.github/workflows/'+WORKFLOW]
    require(len(own) == 1 and str(own[0]['id']) == ident['run_id'] and own[0]['head_sha'] == ident['orchestration_sha'], 'execution branch already used or run identity missing')
    fresh(evidence/'one-shot.json'); write(evidence/'one-shot.json', ident)
    write(evidence/'source-binding.json', {'identity':ident, 'packet_sha256':PACKET_SHA,
        'method_sha':METHOD, 'hashes':verify_sources(method, packet),
        'historical_evidence':historical_evidence(method, packet), 'native_started':False})


def python_binding(packet):
    record = {'path':sys.executable, 'resolved_path':str(Path(sys.executable).resolve()),
              'executable_sha256':digest(Path(sys.executable)), 'version':sys.version,
              'packages':{n:version(n) for n in packet['python']['versions']}}
    require(Path(sys.executable).is_absolute() and sys.version_info[:2] == (3,11), 'actual absolute Python3.11 required')
    require(record['packages'] == packet['python']['versions'], 'numerical dependency drift')
    return record


def provision(method, evidence):
    receipt = {'status':'BLOCKED', 'native_workers_started':0, 'probe_containers_started':0}
    try:
        packet, ident = request(method, evidence); receipt.update(identity=ident)
        receipt['python'] = python_binding(packet)
        require(Path('/proc/1/comm').read_text().strip() == 'systemd', 'systemd PID1 required')
        require('memory' in Path('/sys/fs/cgroup/cgroup.controllers').read_text().split(), 'cgroupv2 memory required')
        command(['sudo','-n','true'])
        sys.path.insert(0, str(method))
        from scripts.kicad import native_resource_guard as guard
        from scripts.kicad.settle_only_pilot import prepare_image
        require(Path(guard.__file__).resolve() == method/'scripts/kicad/native_resource_guard.py', 'wrong guard import')
        guard.local_docker()
        receipt['image_preparation'] = prepare_image(evidence)
        receipt['image'] = guard.require_local_image()
        require(receipt['image'] == packet['image'], 'image differs from packet')
        receipt['source_hashes_after'] = verify_sources(method, packet)
        receipt['free_bytes_after'] = guard.memory_available()
        require(receipt['free_bytes_after'] >= 8*1024**3, 'less than8GiB free after preparation')
        receipt['status'] = 'HOST PREPARATION PASS ONLY; NO ROUTE EXECUTED'
    except Exception as error:
        receipt['error'] = str(error); raise
    finally: write(evidence/'host.json', receipt)


def authenticate(method, artifacts, evidence):
    receipt = {'status':'BLOCKED', 'native_started':False}
    try:
        packet, ident = request(method, evidence); receipt['identity'] = ident
        binding = packet['cases']['K1402']['recovery_artifact']
        artifacts.mkdir(exist_ok=False)
        api = f'repos/{REPOSITORY}/actions/artifacts/{binding["artifact_id"]}'
        metadata = json.loads(command(['gh','api',api], timeout=120))
        require(metadata['id'] == binding['artifact_id'] and metadata['workflow_run']['id'] == binding['run_id'] and not metadata['expired'], 'wrong/expired recovery artifact')
        target = artifacts/binding['file']
        with target.open('xb') as output, (evidence/'download.log').open('x') as log:
            subprocess.run(['gh','api',api+'/zip'], stdout=output, stderr=log, check=True, timeout=120)
        require(digest(target) == binding['sha256'] and target.stat().st_size == binding['bytes'], 'complete recoveryZIP mismatch')
        with zipfile.ZipFile(target) as z:
            require(z.testzip() is None, 'ZIP CRC failure')
            receipt['members'] = len(z.namelist())
        receipt.update(status='PASS COMPLETE K1402 RECOVERY ZIP', binding=binding, metadata=metadata)
    except Exception as error:
        receipt['error'] = str(error); raise
    finally: write(evidence/'artifact-authentication.json', receipt)


def validate_inputs(method, fixture, packet):
    sys.path.insert(0, str(method/DRIVER))
    from f3_fixture import validate
    require(Path(sys.modules['f3_fixture'].__file__).resolve() == method/DRIVER/'f3_fixture.py', 'wrong fixture validator import')
    _, _, lock = validate(fixture, 'K1402', packet['cases']['K1402']['fixture_lock_sha256'])
    return lock['files'] | {'fixture-lock.json':digest(fixture/'fixture-lock.json')}


def route_argv(packet, ident, evidence, python):
    guard_path = evidence/'native-guard.json'; fresh(guard_path)
    require(guard_path.is_absolute() and guard_path.suffix == '.json', 'fresh absolute guard JSON file required')
    replacements = {'{ACTUAL_EXECUTION_PYTHON}':python, '{NEW_PARENT_CASE_ADMISSION_ID}':ADMISSION,
                    '{UNIQUE_CASE_WORKER}':ident['worker'], '{NEW_CASE_GUARD_JSON_FILE}':str(guard_path)}
    argv = [replacements.get(v,v) for v in packet['cases']['K1402']['route_argv']]
    require(not any('{' in v for v in argv), 'unbound route argv')
    return argv


# Retained two-probe result checks from run_route_1420.py, with only this method
# and admission binding changed. This is receipt review, not new qualification.
def result_summary(guard, proposal, exit_code, inputs_unchanged, payload):
    clean=guard.get('final_owned_state',{}).get('workload_absent') is True
    clean=clean and not guard.get('cleanup_failures') and not guard.get('watchdog') and not guard.get('pre_cleanup_state_errors')
    plan=guard.get('plan',{});worker=plan.get('worker','')
    expected_slice='epic242-w'+worker.encode().hex()+'.slice'
    ids=set(guard.get('container_admissions',{}))
    memberships=guard.get('container_memberships',{});states=guard.get('container_states',{})
    probes_ok=len(ids)==2 and ids==set(memberships)==set(states)
    for cid in ids:
        admission=guard['container_admissions'][cid];state=states.get(cid,{})
        member=memberships.get(cid,{})
        req=admission.get('request',{})
        probes_ok=probes_ok and re.fullmatch('[0-9a-f]{64}',cid) is not None
        probes_ok=probes_ok and req.get('command')==['kicad-cli','version'] and req.get('container_id')==cid
        probes_ok=probes_ok and admission.get('ack')==req.get('token','')+':'+cid
        probes_ok=probes_ok and req.get('worker')==worker and member.get('worker')==worker and member.get('container_id')==cid
        probes_ok=probes_ok and member.get('host_config')=={'Memory':6442450944,'MemorySwap':6442450944,'CgroupParent':expected_slice}
        probes_ok=probes_ok and member.get('cgroup','').startswith('0::/epic242.slice/'+expected_slice+'/')
        probes_ok=probes_ok and state.get('Status')=='exited' and not state.get('Running') and state.get('ExitCode')==0 and not state.get('OOMKilled') and not state.get('Error')
    probes_ok=probes_ok and set(guard.get('observed_containers',[]))==ids
    plan_ok=plan.get('admission_id')==ADMISSION and plan.get('sha')==METHOD and plan.get('seconds')==300 and plan.get('command')==payload
    plan_ok=plan_ok and plan.get('memory_max')==6442450944 and plan.get('memory_swap_max')==0 and plan.get('aggregate_memory_max')==12884901888
    plan_ok=plan_ok and plan.get('hook_sha256')=='f91b2c8846856a6d38a10eb9e6314b6ebec3222b68df37942f3716ab860d8c91'
    plan_ok=plan_ok and plan.get('free_floor')==2147483648 and plan.get('early_abort_free')==2684354560
    command_ok=exit_code==0 and guard.get('status')=='COMMAND PASS ONLY; native acceptance requires exact complete evidence'
    passed=command_ok and clean and probes_ok and plan_ok and inputs_unchanged and proposal is not None and proposal.get('removed_uuids')==[]
    additions=len(proposal.get('copper',[])) if proposal is not None else None
    return {'status':('NO IMPROVEMENT' if additions==0 else 'UNCHECKED PROPOSAL; NO CLOSURE OR ACCEPTANCE CLAIM') if passed else 'FAIL / INCOMPLETE; STOP',
            'command_pass':bool(passed),'copper_additions':additions,'removed_count':len(proposal.get('removed_uuids',[])) if proposal is not None else None,
            'both_retained_probes_pass':bool(probes_ok),'guard_plan_matches':bool(plan_ok),
            'cleanup_workload_absent':bool(clean),'container_ids':sorted(ids),'inputs_unchanged':inputs_unchanged}


def proposal_contract(proposal, packet):
    require(all(proposal.get(k) is False for k in ('accepted','adopted','coupled_connectivity_success')), 'false acceptance credit')
    require(proposal.get('removed_uuids') == [], 'cuts forbidden')
    demands = proposal.get('demands', [])
    order = packet['route_policy']['target_order']
    require([d['kind'] for d in demands] == order, 'original demand census/order changed')
    for d in demands:
        target = packet['demand_and_preservation_contract']['targets'][d['kind']]
        require(d['net'] == target['net_token'] and d['anchors'] == [p['uuid'] for p in target['anchor_records']], 'demand substitution')
        require(d['accepted'] is False and d['native_exact_pair_closed'] is False, 'false native credit')
    require(all(d['status'].startswith('NO_VALID_SAVED_ACCESS') and d['portal_counts'][0] == 0 for d in demands[:2]), 'original blocked rail state changed')


def inventory(fixture, evidence):
    return {name: {'status':'PRODUCED','sha256':digest(path)} if path.is_file() else {'status':'NOT PRODUCED'}
            for name,path in {'proposal':fixture/'matched-proposal.json', 'diagnostics':fixture/'matched-search-diagnostics.json',
                              'guard':evidence/'native-guard.json', 'route_log':evidence/'route-driver.log'}.items()}


def execute(method, artifacts, evidence):
    receipt = {'status':'NOT STARTED', 'guard_invoked':False, 'accepted':False, 'native_scope':'F3/K1402 route300s only'}
    initial = None; fixture = None; packet = None; code = 1
    try:
        packet, ident = request(method, evidence); receipt['identity'] = ident
        case = packet['cases']['K1402']; fixture = method/case['fixture']; fresh(fixture)
        host = read(evidence/'host.json'); auth = read(evidence/'artifact-authentication.json')
        require(host['status'] == 'HOST PREPARATION PASS ONLY; NO ROUTE EXECUTED' and host['identity'] == ident, 'wrong actual-host provisioning')
        require(host['python'] == python_binding(packet), 'actual execution Python changed')
        require(auth['status'] == 'PASS COMPLETE K1402 RECOVERY ZIP' and auth['identity'] == ident, 'wrong artifact authentication')
        require(digest(artifacts/case['recovery_artifact']['file']) == case['recovery_artifact']['sha256'], 'authenticated ZIP changed')
        prep = [v.replace('{ACTUAL_EXECUTION_PYTHON}',sys.executable).replace('{AUTHENTICATED_ARTIFACT_DIRECTORY}',str(artifacts)) for v in case['source_only_prepare_argv']]
        with (evidence/'fixture-prepare.log').open('x') as log:
            subprocess.run(prep,cwd=method,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        initial = validate_inputs(method, fixture, packet); write(evidence/'initial-fixture-hashes.json', initial)
        receipt['source_hashes_before'] = verify_sources(method, packet)
        # Leave the frozen guard its full deadline/cleanup; retain upload headroom.
        require(time.time()-read(evidence/'bootstrap.json')['started_epoch'] < 2580-600, 'insufficient enclosing job time; no native start')
        argv = route_argv(packet, ident, evidence, sys.executable); receipt['argv'] = argv
        receipt.update(status='SINGLE GUARDED ROUTE STARTING', guard_invoked=True)
        write(evidence/'route.json', receipt)
        with (evidence/'route-driver.log').open('x') as log:
            done = subprocess.run(argv,cwd=method,stdout=log,stderr=subprocess.STDOUT)
        receipt['guard_exit_code'] = done.returncode
        guard = read(evidence/'native-guard.json')
        require(guard.get('plan',{}).get('worker') == ident['worker'], 'guard worker mismatch')
        unchanged = validate_inputs(method, fixture, packet) == initial
        proposal = read(fixture/'matched-proposal.json'); proposal_contract(proposal, packet)
        require((fixture/'matched-search-diagnostics.json').is_file(), 'diagnostics absent')
        receipt['result'] = result_summary(guard,proposal,done.returncode,unchanged,argv[argv.index('--evidence')+2:])
        receipt['status'] = receipt['result']['status']; receipt['demands'] = proposal['demands']
        receipt['source_hashes_after'] = verify_sources(method, packet)
        code = 0 if receipt['result']['command_pass'] else 1
    except Exception as error: receipt.update(status='FAIL / INCOMPLETE; STOP', error=str(error))
    finally:
        try:
            if packet is not None: receipt['source_hashes_after'] = verify_sources(method, packet)
            if fixture is not None:
                receipt['outputs'] = inventory(fixture, evidence)
                if initial is not None:
                    receipt['final_input_hashes'] = {n:digest(fixture/n) if (fixture/n).is_file() else None for n in initial}
                    receipt['inputs_unchanged'] = receipt['final_input_hashes'] == initial
                    if not receipt['inputs_unchanged']: receipt['status']='INPUT INTEGRITY FAILURE; STOP'; code=1
        except Exception as error:
            receipt.update(status='FINAL INTEGRITY CHECK FAILURE; STOP', final_check_error=str(error)); code=1
        receipt['cleanup'] = 'Guard not invoked; no native resources created' if not receipt['guard_invoked'] else 'Only complete native-guard.json proves cleanup; missing/unknown proof blocks further admission'
        write(evidence/'route.json', receipt)
    return code


def finalize(method, evidence):
    # Always-run retention, including failed setup/prepare/route and missing outputs.
    packet = read(HERE/'f3-packet/request.json'); fixture = method/packet['cases']['K1402']['fixture']
    receipt = {'job_status':os.environ.get('JOB_STATUS'), 'outputs':inventory(fixture,evidence),
               'accepted':False, 'native_acceptance':'NOT RUN; original rails remain blocked',
               'cleanup':'Inspect complete guard receipt; absence is not clean or success'}
    try:
        if fixture.exists(): shutil.copytree(fixture,evidence/'fixture')
        receipt['fixture_retention'] = 'COPIED' if fixture.exists() else 'NOT PRODUCED'
    except Exception as error:
        receipt['retention_error'] = str(error); raise
    finally: write(evidence/'job-outcome.json', receipt)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('initialize','provision','authenticate','execute','finalize'))
    p.add_argument('--method',required=True,type=Path);p.add_argument('--artifacts',required=True,type=Path)
    p.add_argument('--evidence-directory',required=True,type=Path);a=p.parse_args()
    method=a.method.resolve();artifacts=a.artifacts.resolve();evidence=a.evidence_directory.resolve()
    require(evidence.is_dir(),'workflow-initialized evidence directory required')
    os.chdir(method)
    name={'initialize':'one-shot.json','provision':'host.json','authenticate':'artifact-authentication.json','execute':'route.json','finalize':'job-outcome.json'}[a.mode]
    fresh(evidence/name)
    if a.mode in ('authenticate','execute'): return globals()[a.mode](method,artifacts,evidence)
    globals()[a.mode](method,evidence)
    return 0


if __name__ == '__main__': sys.exit(main())
