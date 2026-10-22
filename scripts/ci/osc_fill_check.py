"""Job-local controller for disposable public frozen fill baseline only."""
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import sys
import tempfile
import time
import uuid
import osc_candidate_check as c
import osc_frozen_fill as inv
import osc_frozen_topology as topology

GIB=1024**3
TOTAL_SECONDS=590
PAYLOAD_SECONDS=420
ATTACH_SECONDS=430
WRAPPER_SECONDS=450
CLEANUP_RESERVE=40
LAUNCH_RESERVE=WRAPPER_SECONDS+CLEANUP_RESERVE+7

def require_budget(seconds):
    remaining=c.DEADLINE-time.monotonic()
    if remaining<seconds: raise TimeoutError('insufficient launch budget')
    return remaining

def local_docker_endpoint(docker,root,measurement=None):
    result=c.run_command([docker,'context','inspect','--format','{{json .Endpoints.docker.Host}}'],root,10,isolated=False)
    endpoint=json.loads(c.checked(result))
    if measurement is not None:
        measurement['docker_endpoint']=endpoint if endpoint=='unix:///var/run/docker.sock' else 'REJECTED_NONLOCAL_OR_MISSING'
    if endpoint!='unix:///var/run/docker.sock':
        raise ValueError('effective Docker endpoint is not the hosted local Unix socket')
    return endpoint

def capacity_decision(meminfo,disk_free,docker_total,active):
    values={}
    for line in meminfo.splitlines():
        fields=line.split()
        if fields and fields[0] in ('MemTotal:','MemAvailable:'):
            if len(fields)!=3 or fields[2]!='kB' or fields[0] in values: raise ValueError('invalid meminfo')
            values[fields[0]]=int(fields[1])*1024
    if set(values)!={'MemTotal:','MemAvailable:'}: raise ValueError('missing memory measurements')
    if type(docker_total) is not int or type(disk_free) is not int: raise ValueError('invalid capacity types')
    result={'host_total_bytes':values['MemTotal:'],'host_available_bytes':values['MemAvailable:'],
        'docker_total_bytes':docker_total,'disk_free_bytes':disk_free,'active_container_count':len(active.splitlines()) if active.strip() else 0,
        'container_memory_bytes':2*GIB,'host_reserve_bytes':2*GIB}
    result['passed']=(values['MemTotal:']>=6*GIB and values['MemAvailable:']>=4*GIB
        and docker_total>=6*GIB and disk_free>=4*GIB and not active.strip())
    return result

def resource_preflight():
    state=Path(os.environ['OSC_STATE']);measurement={'status':'FAILED','measured_at_monotonic':time.monotonic()}
    try:
        if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
            raise ValueError('fill requires GitHub-hosted Actions runner')
        if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
            raise ValueError('alternate Docker endpoint unsupported')
        c.DEADLINE=float(os.environ['OSC_DEADLINE'])
        if c.DEADLINE-time.monotonic()<200: raise TimeoutError('insufficient prelaunch reserve')
        docker=os.environ['OSC_REAL_DOCKER']
        local_docker_endpoint(docker,Path.cwd(),measurement)
        meminfo=Path('/proc/meminfo').read_text()
        disk_free=shutil.disk_usage('/').free
        info=c.run_command([docker,'info','--format','{{json .MemTotal}}'],Path.cwd(),10,isolated=False)
        total=json.loads(c.checked(info))
        ps=c.run_command([docker,'ps','-q'],Path.cwd(),10,isolated=False)
        active=c.checked(ps)
        measurement.update(capacity_decision(meminfo,disk_free,total,active))
        if not measurement['passed']: raise ValueError('capacity or serial-exclusion gate failed')
        measurement['status']='PASS'
    except Exception as exc:
        measurement['error']=str(exc)[:500];raise
    finally:
        (state/('resource-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(measurement))

def collect_resources(state,receipt):
    paths=sorted(state.glob('resource-*.json'))
    if len(paths)>8: raise ValueError('resource receipt count exceeded')
    receipt['resource_checks']=sorted([json.loads(p.read_text()) for p in paths],key=lambda r:r['measured_at_monotonic'])

def summary_for(receipt,detail=None):
    summary={k:str(receipt[k])[:500] for k in ('status','error','cleanup_error','after_error') if k in receipt}
    summary['cleanup']=[{k:r.get(k) for k in ('status','state_before_cleanup')} for r in receipt.get('cleanup',[])][:8]
    summary['source_hashes_unchanged']=receipt.get('before')==receipt.get('after') and 'before' in receipt
    summary['resource_checks']=receipt.get('resource_checks',[])
    summary['deadline_policy']=receipt.get('deadline_policy')
    summary['elapsed_seconds']=receipt.get('elapsed_seconds')
    if isinstance(detail,dict):
        summary['fill_status']=detail.get('status')
        summary['fill_failure']=str(detail.get('failure'))[:700]
        drc=detail.get('drc',{})
        summary['drc_counts']={k:drc.get(k) for k in ('before','after')}
        summary['drc_checkpoint_counts']=detail.get('drc_counts',{})
        summary['drc_checkpoints']={name:{k:row.get(k) for k in ('report_sha256','report_bytes','counts')}
            for name,row in detail.get('drc_checkpoints',{}).items()}
        summary['phase_results']=detail.get('phase_results',[])
        summary['command_outcomes']=[{k:row.get(k) for k in ('phase','status','error','exit_code','failure','start_monotonic_seconds','end_monotonic_seconds','deadline_monotonic_seconds','elapsed_seconds','log_sha256') if k in row}
            for row in detail.get('commands',[])][:4]
        summary['drc_delta_counts']={k:v.get('count') for k,v in drc.get('delta',{}).items() if isinstance(v,dict)}
        summary['selected_membership']={phase:{name:{'count':row.get('count'),'selected_members':row.get('selected_members')}
            for name,row in detail.get(phase,{}).get('membership',{}).items() if name in topology.EXPECTED}
            for phase in ('native_before','native_after')}
        summary['memory_telemetry']=[{k:r[k] for k in ('phase','point','monotonic_seconds','values','events_since_baseline','error') if k in r} for r in detail.get('memory_telemetry',[])][:16]
    encoded=json.dumps(summary,sort_keys=True)
    if len(encoded.encode())>16384:
        summary.pop('selected_membership',None);summary['membership_summary_omitted_for_bound']=True
        encoded=json.dumps(summary,sort_keys=True)
    if len(encoded.encode())>16384:
        summary.pop('memory_telemetry',None);summary['memory_summary_omitted_for_bound']=True
        encoded=json.dumps(summary,sort_keys=True)
    if len(encoded.encode())>16384: raise ValueError('bounded summary exceeds limit')
    return encoded

def readonly_args(argv, root, payload):
    mounts=[argv[i+1] for i,v in enumerate(argv[:-1]) if v=='--volume']
    if len(mounts)!=2 or mounts[0]!=str(root)+':/work': raise ValueError('unexpected oracle mounts')
    home=mounts[1]
    if not home.endswith(':/tmp/kicad-home') or not PurePosixPath(home.rsplit(':',1)[0]).is_absolute():
        raise ValueError('unexpected HOME mount')
    if any(a.startswith(('--mount','--volume=','--tmpfs','--read-only')) or a=='-v' for a in argv):
        raise ValueError('alternate mounts forbidden')
    if argv.count('--network')!=1 or argv[argv.index('--network')+1]!='none': raise ValueError('network must be none')
    result=list(argv)
    i=result.index(home); del result[i-1:i+1]
    result[result.index(mounts[0])]=mounts[0]+':ro'
    i=result.index(c.IMAGE)
    result[i:i]=['--read-only','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',
        '--tmpfs','/scratch:rw,nosuid,nodev,noexec,size=256m,mode=1777',
        '--volume',str(payload)+':/analysis:ro']
    return result

def adapter(argv):
    root=Path(os.environ['OSC_INPUT_ROOT']);payload=Path(os.environ['OSC_PAYLOAD'])
    args=readonly_args(argv,root,payload)
    resource_preflight()
    c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    is_payload=any('/analysis/osc_frozen_fill.py' in a for a in args[args.index(c.IMAGE)+1:])
    # Measure after both oracle setup and this container's capacity probes, before create.
    require_budget(ATTACH_SECONDS+CLEANUP_RESERVE+7+10 if is_payload else 40+CLEANUP_RESERVE+7)
    if is_payload and float(os.environ['OSC_COMMAND_DEADLINE'])-time.monotonic()<PAYLOAD_SECONDS+10+7:
        raise TimeoutError('insufficient wrapper budget after setup for payload and create')
    return c.adapter(args,memory_policy='fill-2g-noswap',execution_policy='fill-430' if is_payload else 'fill-probe-20')

def main():
    if len(sys.argv)!=3: raise ValueError('usage: osc_fill_check.py SOURCE OUT')
    root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    if root==out or out.is_relative_to(root): raise ValueError('output must be separate')
    out.mkdir(exist_ok=False)
    payload=Path(__file__).with_name('osc_frozen_fill.py').resolve()
    old_pins,old_deadline,old_reserve=c.PINS,c.DEADLINE,c.RESERVE_SECONDS
    started=time.monotonic();c.DEADLINE=started+TOTAL_SECONDS
    c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    c.PINS={**c.PINS,**{'boards/osc-core/'+name:h for name,h in inv.PINS.items()}}
    receipt=dict(status='STARTED',source_sha=c.SOURCE,tooling_sha=os.environ.get('TOOLING_SHA'),
        image=c.IMAGE,commands=[],cleanup=[],candidate_ingestion='UNIMPLEMENTED')
    receipt['deadline_policy']={'total_seconds':TOTAL_SECONDS,'payload_seconds':PAYLOAD_SECONDS,
        'attach_seconds':ATTACH_SECONDS,'wrapper_seconds':WRAPPER_SECONDS,'cleanup_reserve_seconds':CLEANUP_RESERVE,
        'launch_reserve_seconds':LAUNCH_RESERVE,'started_monotonic':started,'deadline_monotonic':c.DEADLINE}
    state=None;docker=None;failed=False
    def save(): (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    try:
        save()
        if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
            raise ValueError('fill requires GitHub-hosted Actions runner')
        if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
            raise ValueError('alternate Docker endpoint unsupported')
        tooling=receipt['tooling_sha']
        if not tooling or len(tooling)!=40 or any(x not in '0123456789abcdef' for x in tooling): raise ValueError('tooling SHA required')
        receipt['tool_hashes']={p.name:c.sha(p) for p in [Path(__file__),payload,Path(topology.__file__),Path(c.__file__)]}
        receipt['before']=c.snapshot(root)
        head=c.run_command(['git','rev-parse','HEAD'],root,10);receipt['commands'].append(head)
        if c.checked(head)!=c.SOURCE: raise ValueError('source HEAD mismatch')
        docker=shutil.which('docker')
        if not docker: raise ValueError('Docker unavailable')
        local_docker_endpoint(docker,root,receipt);save()
        pull=c.run_command([docker,'pull',c.IMAGE],root,120);receipt['commands'].append(pull);c.checked(pull)
        state=Path(tempfile.mkdtemp(prefix='osc-fill-owned-'))
        bundle=state/'analysis';bundle.mkdir()
        for src in (payload,Path(topology.__file__).resolve()): shutil.copyfile(src,bundle/src.name)
        if {x.name for x in bundle.iterdir()}!={'osc_frozen_fill.py','osc_frozen_topology.py'}: raise ValueError('bundle allowlist')
        if any(c.sha(bundle/src.name)!=receipt['tool_hashes'][src.name] for src in (payload,Path(topology.__file__))): raise ValueError('bundle hash')
        shim=state/'docker';shim.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(Path(__file__).resolve()))+' --adapter "$@"\n');shim.chmod(0o700)
        env={'PATH':str(state)+os.pathsep+os.environ['PATH'],'OSC_STATE':str(state),'OSC_REAL_DOCKER':docker,
             'OSC_INPUT_ROOT':str(root),'OSC_PAYLOAD':str(bundle),'OSC_DEADLINE':str(c.DEADLINE),
             'GITHUB_ACTIONS':os.environ['GITHUB_ACTIONS'],'RUNNER_ENVIRONMENT':os.environ['RUNNER_ENVIRONMENT']}
        commands=[*c.COMMANDS,['bash','scripts/kicad/run.sh','python3','-B','/analysis/osc_frozen_fill.py']]
        for n,command in enumerate(commands):
            require_budget(LAUNCH_RESERVE if n==2 else 200)
            first=len(receipt['cleanup'])
            env['OSC_COMMAND_DEADLINE']=str(time.monotonic()+(WRAPPER_SECONDS if n==2 else 20))
            result=c.run_command(command,root,WRAPPER_SECONDS if n==2 else 20,env);receipt['commands'].append(result);save()
            collect_resources(state,receipt);save()
            data=None
            if n==2:
                try:
                    data=json.loads(result['output'])
                    (out/'fill.json').write_text(json.dumps(data,indent=2)+'\n')
                except Exception as exc: receipt['payload_parse_error']=str(exc)
            c.cleanup_owned(state,docker,root,outcomes=receipt['cleanup']);save()
            c.normal_exit(receipt['cleanup'][first:])
            if n<2: c.exact_version(result)
            else:
                c.checked(result)
                if data is None: raise ValueError('fill JSON missing or malformed')
                inv.validate_result(data)
        receipt['status']='FILL_BASELINE_OBSERVATIONS_NOT_ACCEPTANCE'
    except Exception as exc:
        failed=True;receipt.update(status='FAILED',error=str(exc))
    finally:
        c.RESERVE_SECONDS=7 # release reserved cleanup budget; keep the original absolute deadline
        if state is not None:
            try:c.cleanup_owned(state,docker,root,outcomes=receipt['cleanup'])
            except Exception as exc:failed=True;receipt.update(status='FAILED',cleanup_error=str(exc))
            try:collect_resources(state,receipt)
            except Exception as exc:failed=True;receipt.update(status='FAILED',resource_receipt_error=str(exc))
        try:receipt['after']=c.snapshot(root)
        except Exception as exc:failed=True;receipt.update(status='FAILED',after_error=str(exc))
        try:
            receipt['elapsed_seconds']=time.monotonic()-started
            save()
            detail=None
            if (out/'fill.json').is_file():
                detail=json.loads((out/'fill.json').read_text())
            print(summary_for(receipt,detail),flush=True)
        finally: c.PINS,c.DEADLINE,c.RESERVE_SECONDS=old_pins,old_deadline,old_reserve
    return int(failed)

if __name__=='__main__':
    raise SystemExit(adapter(sys.argv[2:]) if sys.argv[1:2]==['--adapter'] else main())
