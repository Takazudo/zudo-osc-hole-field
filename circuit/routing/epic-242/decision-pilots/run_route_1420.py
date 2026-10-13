#!/usr/bin/env python3
"""Single parent-admitted O1/K1402 route; no apply/settle/fresh/audit or retry."""
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

import provision_host as host

ADMISSION = 'epic242-o1-k1402-route-20261011-1420'
REPOSITORY = 'Takazudo/zudo-osc-hole-field'
BRANCH = 'integration/epic-242-o1-k1402-route-1420'


def write(path, data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def request(method):
    host.require(os.environ.get('PARENT_ADMISSION_ID')==ADMISSION,'exact parent admission required')
    host.require(os.environ.get('GITHUB_REPOSITORY')==REPOSITORY and
                 os.environ.get('GITHUB_REF_NAME')==BRANCH,'exact isolated execution branch required')
    host.require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted','hosted runner required')
    run,attempt=os.environ.get('GITHUB_RUN_ID',''),os.environ.get('GITHUB_RUN_ATTEMPT','')
    host.require(run.isdecimal() and attempt=='1','new first-attempt Actions run required; no automatic retry')
    packet=json.loads((host.HERE/'minimum-native-request.json').read_text())
    host.verify_sources(method,packet)
    expected=json.loads((method/'circuit/routing/epic-242/decision-pilots/artifacts.json').read_text())
    host.require(packet['preparation_artifacts']==expected and len(expected)==6,'six frozen artifact bindings differ')
    return packet,'o1-k1402-r1420-'+run+'-'+attempt


def authenticate(method, artifacts, evidence):
    receipt={'status':'BLOCKED','admission_id':ADMISSION,'inputs':{},'native_started':False}
    try:
        packet,worker=request(method)
        artifacts.mkdir(exist_ok=False)
        deadline=time.monotonic()+900
        for board,expected in packet['preparation_artifacts'].items():
            host.require(Path(expected['file']).name==expected['file'],'unsafe artifact filename')
            api=f'repos/{REPOSITORY}/actions/artifacts/{expected["artifact_id"]}'
            def remaining():
                seconds=deadline-time.monotonic()
                host.require(seconds>0,'artifact preparation deadline exhausted')
                return min(120,seconds)
            metadata=json.loads(subprocess.check_output(['gh','api',api],text=True,timeout=remaining()))
            host.require(metadata['id']==expected['artifact_id'] and metadata['workflow_run']['id']==expected['run_id'] and not metadata['expired'],'artifact metadata mismatch/expired')
            target=artifacts/expected['file']
            with target.open('xb') as output,(evidence/f'download-{board}.log').open('x') as log:
                subprocess.run(['gh','api',api+'/zip'],stdout=output,stderr=log,check=True,timeout=remaining())
            actual=digest(target)
            host.require(actual==expected['sha256'],'full ZIP SHA mismatch: '+board)
            with zipfile.ZipFile(target) as archive:
                host.require(archive.testzip() is None,'ZIP CRC failure: '+board)
                members=len(archive.namelist())
            receipt['inputs'][board]={**expected,'actual_sha256':actual,'bytes':target.stat().st_size,
                                     'crc_members':members,'metadata':metadata}
            write(evidence/'artifact-authentication.json',receipt)
        receipt.update(status='PASS ALL SIX FULL ZIP HASHES AND CRCS',worker=worker)
        return 0
    except Exception as exc:
        receipt['error']=str(exc)
        return 1
    finally:write(evidence/'artifact-authentication.json',receipt)


def validate_inputs(fixture, packet):
    lock=json.loads((fixture/'fixture-lock.json').read_text())
    host.require(lock['source_tree_sha']==host.METHOD and lock['domain']=='O1' and lock['board']=='K1402','fixture identity/source mismatch')
    host.require(lock['artifact']['board_sha256']==packet['artifacts']['K1402']['board_sha256'],'fixture board binding mismatch')
    host.require(lock['artifact']['dump_sha256']==packet['artifacts']['K1402']['dump_sha256'],'fixture dump binding mismatch')
    for name,expected in lock['files'].items():
        host.require(digest(fixture/name)==expected,'fixture input mismatch: '+name)
    return lock['files']|{'fixture-lock.json':digest(fixture/'fixture-lock.json')}


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
    plan_ok=plan.get('admission_id')==ADMISSION and plan.get('sha')==host.METHOD and plan.get('seconds')==300 and plan.get('command')==payload
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


def execute(method, artifacts, evidence):
    receipt={'admission_id':ADMISSION,'status':'NOT STARTED','guard_invoked':False,
             'global_reservation':'one exclusive native worker; all other slots unused by parent admission',
             'method_sha':host.METHOD,'orchestration_sha':os.environ.get('GITHUB_SHA'),
             'driver_sha256':digest(Path(__file__)),'native_scope':'O1/K1402 route only; no subsequent phase'}
    fixture=None;initial=None;code=1
    try:
        packet,worker=request(method)
        receipt['worker']=worker
        provisioning=json.loads((evidence/'host.json').read_text())
        host.require(provisioning['status']=='PROVISIONING PASS ONLY; NO NATIVE ADMISSION OR EXECUTION','actual runner provisioning did not pass')
        host.require(provisioning['workflow_run_id']==os.environ['GITHUB_RUN_ID'] and provisioning['orchestration_sha']==os.environ['GITHUB_SHA'],'provisioning belongs to another runner')
        host.require(provisioning['python']['path']==sys.executable,'execution Python changed')
        receipt['python']={'path':sys.executable,'packages':{n:version(n) for n in packet['python']['versions']}}
        host.require(receipt['python']['packages']==packet['python']['versions'],'numerical versions changed')
        auth=json.loads((evidence/'artifact-authentication.json').read_text())
        host.require(auth['status']=='PASS ALL SIX FULL ZIP HASHES AND CRCS','six full ZIPs not authenticated')
        for name,binding in packet['preparation_artifacts'].items():
            host.require(auth['inputs'][name]['actual_sha256']==binding['sha256'] and digest(artifacts/binding['file'])==binding['sha256'],'authenticated ZIP changed')
        fixture=method/'design/partition/core-split/candidates/pilots/generated'/worker
        guard_path=evidence/'native-guard.json'
        planned=host.route_plan(method,sys.executable,fixture,guard_path,packet)
        argv=planned['argv'];argv[argv.index('--admission-id')+1]=ADMISSION;argv[argv.index('--worker')+1]=worker
        receipt['argv']=argv;receipt['fixture']=str(fixture)
        with (evidence/'fixture-prepare.log').open('x') as log:
            subprocess.run([sys.executable,'circuit/routing/epic-242/decision-pilots/prepare_matched.py',
                '--artifacts',str(artifacts),'--domain','O1','--board','K1402','--output',str(fixture)],
                cwd=method,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        initial=validate_inputs(fixture,packet)
        write(evidence/'initial-fixture-hashes.json',initial)
        receipt['source_hashes_before']=host.verify_sources(method,packet)
        receipt.update(status='SINGLE GUARDED ROUTE STARTING',guard_invoked=True)
        write(evidence/'route.json',receipt)
        with (evidence/'route-driver.log').open('x') as log:
            # Native guard owns its300s deadline and bounded cleanup. No competing outer kill.
            done=subprocess.run(argv,cwd=method,stdout=log,stderr=subprocess.STDOUT)
        receipt['guard_exit_code']=done.returncode
        guard=json.loads(guard_path.read_text())
        host.require(guard.get('plan',{}).get('worker')==worker,'guard worker differs from reserved identity')
        unchanged=all(digest(fixture/name)==sha for name,sha in initial.items())
        proposal_path=fixture/'matched-proposal.json'
        proposal=json.loads(proposal_path.read_text()) if proposal_path.exists() else None
        host.require((fixture/'matched-search-diagnostics.json').is_file(),'route diagnostics absent')
        payload=argv[argv.index('--evidence')+2:]
        receipt['result']=result_summary(guard,proposal,done.returncode,unchanged,payload)
        receipt['status']=receipt['result']['status']
        receipt['source_hashes_after']=host.verify_sources(method,packet)
        code=0 if receipt['result']['command_pass'] else 1
    except Exception as exc:
        receipt.update(status='FAIL / INCOMPLETE; STOP',error=str(exc))
        code=1
    finally:
        if initial is not None:
            try:
                receipt['final_input_hashes']={name:digest(fixture/name) if (fixture/name).is_file() else None for name in initial}
                receipt['inputs_unchanged']=receipt['final_input_hashes']==initial
                if not receipt['inputs_unchanged']:
                    receipt['status']='INPUT INTEGRITY FAILURE; STOP';code=1
            except Exception as exc:
                receipt.update(status='INPUT HASH READ FAILURE; STOP',input_hash_error=str(exc));code=1
        if fixture is not None and fixture.exists():
            try:shutil.copytree(fixture,evidence/'fixture')
            except Exception as exc:
                receipt.update(status='EVIDENCE COPY FAILURE; STOP',copy_error=str(exc));code=1
        if not receipt['guard_invoked']:
            receipt['cleanup']='No native guard invoked; zero task-created native resources'
        else:
            receipt['cleanup']='Inspect complete native-guard.json final_owned_state and cleanup receipts; absence/incompleteness is NOT clean'
        write(evidence/'route.json',receipt)
    return code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('authenticate','execute'))
    parser.add_argument('--method',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--evidence-directory',type=Path,required=True)
    args=parser.parse_args()
    method=args.method.resolve();artifacts=args.artifacts.resolve();evidence=args.evidence_directory.resolve()
    host.require(evidence.is_dir(),'workflow-initialized evidence directory required')
    target=evidence/('artifact-authentication.json' if args.mode=='authenticate' else 'route.json')
    host.require(not target.exists() and not target.is_symlink(),'existing receipt; no retry or overwrite')
    return (authenticate if args.mode=='authenticate' else execute)(method,artifacts,evidence)


if __name__=='__main__':sys.exit(main())
