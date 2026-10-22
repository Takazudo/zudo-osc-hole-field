"""Local WSL controller for the single selected-zone diagnostic on a disposable copy of the frozen core.

Local-only counterpart of osc_fill_check.py for the two-pair +12V question:
same owned-container records, read-only oracle mounts, 1 CPU / 2 GiB /
zero extra swap / 64 PIDs / network none, fresh per-create resource gate,
owned cleanup and the existing 590 s controller / 420 s payload / 430 s
attach ceilings. The hosted gate is replaced by local_gate from the
synthetic adapter (never spoofed). Original board files are mounted
read-only and hash-checked before and after. No DRC, no acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import sys
import time
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ci'))
import osc_candidate_check as c
import osc_fill_check as f
import osc_frozen_fill as inv
import osc_frozen_topology as topology
import osc_synthetic_local as local
import osc_single_zone_payload as payload
import osc_zone_drc_payload as drcpayload

TOTAL_SECONDS=f.TOTAL_SECONDS
PAYLOAD_SECONDS=f.PAYLOAD_SECONDS
ATTACH_SECONDS=f.ATTACH_SECONDS
WRAPPER_SECONDS=f.WRAPPER_SECONDS
CLEANUP_RESERVE=f.CLEANUP_RESERVE
LAUNCH_RESERVE=f.LAUNCH_RESERVE
OUTER_STOP_SECONDS=600
STATUS=payload.STATUS
MODE='LOCAL_WSL_SINGLE_ZONE'
PAYLOAD_NAME='osc_single_zone_payload.py'
DRC_PAYLOAD_NAME='osc_zone_drc_payload.py'
BUNDLE=(PAYLOAD_NAME,DRC_PAYLOAD_NAME,'osc_frozen_fill.py','osc_frozen_topology.py')
MODES={'zone':(PAYLOAD_NAME,[],payload.STATUS),'candidate':(DRC_PAYLOAD_NAME,['candidate'],drcpayload.CANDIDATE_STATUS),'drc':(DRC_PAYLOAD_NAME,['drc'],drcpayload.DRC_STATUS)}

def bundle_sources():
    return {PAYLOAD_NAME:Path(__file__).with_name(PAYLOAD_NAME).resolve(),DRC_PAYLOAD_NAME:Path(__file__).with_name(DRC_PAYLOAD_NAME).resolve(),
            'osc_frozen_fill.py':Path(inv.__file__).resolve(),'osc_frozen_topology.py':Path(topology.__file__).resolve()}

def board_pins():
    return {**c.PINS,**{'boards/osc-core/'+name:h for name,h in inv.PINS.items()}}

def resource_preflight():
    state=Path(os.environ['OSC_STATE']);measurement={'status':'FAILED','measured_at_monotonic':time.monotonic()}
    try:
        local.local_gate(os.environ,require_guard=False)
        c.DEADLINE=float(os.environ['OSC_DEADLINE'])
        if c.DEADLINE-time.monotonic()<200: raise TimeoutError('insufficient prelaunch reserve')
        docker=os.environ['OSC_REAL_DOCKER']
        f.local_docker_endpoint(docker,Path.cwd(),measurement)
        total=json.loads(c.checked(c.run_command([docker,'info','--format','{{json .MemTotal}}'],Path.cwd(),10,isolated=False)))
        active=c.checked(c.run_command([docker,'ps','-q'],Path.cwd(),10,isolated=False))
        measurement.update(f.capacity_decision(local.host_meminfo(),shutil.disk_usage('/').free,total,active))
        if not measurement['passed']: raise ValueError('capacity or serial-exclusion gate failed')
        measurement['status']='PASS'
    except Exception as exc:
        measurement['error']=str(exc)[:500];raise
    finally:
        (state/('resource-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(measurement))

def extra_mounts(args,output,candidate):
    """Only the local candidate/drc modes add a writable /output and a read-only /candidate bind mount."""
    result=list(args);i=result.index(c.IMAGE);extra=[]
    if output:
        p=Path(output)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink(): raise ValueError('output mount must be an existing absolute directory')
        extra+=['--volume',str(p)+':/output']
    if candidate:
        p=Path(candidate)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink() or not (p/'manifest.json').is_file(): raise ValueError('candidate mount must be an existing directory with manifest.json')
        extra+=['--volume',str(p)+':/candidate:ro']
    result[i:i]=extra
    return result

def adapter(argv):
    if os.environ.get('OSC_LOCAL_ADAPTER')!='1': raise ValueError('local adapter shim invoked outside a local run')
    root=Path(os.environ['OSC_INPUT_ROOT']);bundle=Path(os.environ['OSC_PAYLOAD'])
    args=f.readonly_args(argv,root,bundle)
    args=extra_mounts(args,os.environ.get('OSC_OUTPUT'),os.environ.get('OSC_CANDIDATE'))
    resource_preflight()
    c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    is_payload=any('/analysis/'+name in a for a in args[args.index(c.IMAGE)+1:] for name in (PAYLOAD_NAME,DRC_PAYLOAD_NAME))
    f.require_budget(ATTACH_SECONDS+CLEANUP_RESERVE+7+10 if is_payload else 40+CLEANUP_RESERVE+7)
    if is_payload and float(os.environ['OSC_COMMAND_DEADLINE'])-time.monotonic()<PAYLOAD_SECONDS+10+7:
        raise TimeoutError('insufficient wrapper budget after setup for payload and create')
    return c.adapter(args,memory_policy='fill-2g-noswap',execution_policy='fill-430' if is_payload else 'fill-probe-20')

def summarize(receipt,detail):
    summary={k:str(receipt[k])[:500] for k in ('status','error','cleanup_error','after_error') if k in receipt}
    summary['elapsed_seconds']=receipt.get('elapsed_seconds');summary['cleanup']=[r.get('status') for r in receipt.get('cleanup',[])]
    summary['source_hashes_unchanged']=receipt.get('before')==receipt.get('after') and 'before' in receipt
    if isinstance(detail,dict):
        summary['payload_status']=detail.get('status');summary['payload_failure']=detail.get('failure');summary['payload_elapsed']=detail.get('elapsed_seconds')
        worker=detail.get('worker',{}) if isinstance(detail.get('worker'),dict) else {}
        summary['fill']=worker.get('fill');summary['selected_after']=(worker.get('after') or {}).get('selected')
        summary['pairs']={phase:{name:{k:row.get(k) for k in ('connected','symmetric','unconnected_count')}|({'cluster_a_size':row['cluster_a'].get('size'),'selected_zone_in_cluster':row['cluster_a'].get('selected_zone_member'),'bridging':{k:len(v) for k,v in row['bridging_vias'].items()} if isinstance(row.get('bridging_vias'),dict) else None} if isinstance(row.get('cluster_a'),dict) else {})
            for name,row in (worker.get(phase) or {}).get('pairs',{}).items()} for phase in ('before','after','reloaded')}
        summary['memory_peak']=max((r.get('values',{}).get('memory.peak',0) for r in detail.get('memory_telemetry',[])),default=None)
    return json.dumps(summary,sort_keys=True)

def run(args):
    started=time.monotonic();c.DEADLINE=started+TOTAL_SECONDS;c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    root=Path(args.source).resolve();out=Path(args.out).resolve()
    if root==out or out.is_relative_to(root): raise ValueError('separate output required')
    payload_name,payload_args,expected_status=MODES[args.payload]
    output=Path(args.output).resolve() if args.output else None;candidate=Path(args.candidate).resolve() if args.candidate else None
    # Argument validation before any side effect: no directories, no allowlist mutation.
    if args.payload in ('candidate','drc') and output is None: raise ValueError('--output required for '+args.payload)
    if args.payload=='drc' and candidate is None: raise ValueError('--candidate required for drc')
    if output is not None and output.exists(): raise ValueError('output directory must not pre-exist')
    out.mkdir(exist_ok=False)
    if output is not None: output.mkdir(mode=0o755)
    old_pins=c.PINS;c.PINS=board_pins()
    r={'status':'STARTED','mode':MODE,'payload':args.payload,'output':str(output) if output else None,'candidate':str(candidate) if candidate else None,'hosted':False,'source_sha':c.SOURCE,'tooling_sha':os.environ.get('TOOLING_SHA'),'image':c.IMAGE,
       'target_zone':payload.TARGET_ZONE,'pairs':payload.PAIRS,'commands':[],'cleanup':[],'full_board_fill':False,'board_acceptance':False,'drc':'NOT RUN: whole-board DRC is outside this two-pair selected-zone diagnostic',
       'deadline_policy':{'total_seconds':TOTAL_SECONDS,'outer_stop_seconds':OUTER_STOP_SECONDS,'payload_seconds':PAYLOAD_SECONDS,'attach_seconds':ATTACH_SECONDS,
           'wrapper_seconds':WRAPPER_SECONDS,'cleanup_reserve_seconds':CLEANUP_RESERVE,'launch_reserve_seconds':LAUNCH_RESERVE,'stage_caps':payload.STAGE_CAPS,
           'started_monotonic':started,'deadline_monotonic':c.DEADLINE}}
    state=None;docker=None;failed=False
    def save():
        (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
    def call(argv,seconds=10,env=None):
        result=c.run_command(argv,root,seconds,env);r['commands'].append(result);save();return result
    try:
        save()
        local.local_gate(os.environ)
        r['authorization']=local.authorization(args.authorization)
        t=r['tooling_sha']
        if not t or len(t)!=40 or any(x not in '0123456789abcdef' for x in t):raise ValueError('tooling SHA')
        r['host']={'platform':platform.platform(),'python':sys.version.split()[0]}
        r['before']=c.snapshot(root)
        sources=bundle_sources()
        if set(sources)!=set(BUNDLE) or any(p.name!=name for name,p in sources.items()):raise ValueError('bundle sources')
        r['tool_hashes']={p.name:c.sha(p) for p in [Path(__file__),Path(local.__file__),Path(c.__file__),Path(f.__file__),*sources.values()]}
        if c.checked(call(['git','rev-parse','HEAD']))!=c.SOURCE:raise ValueError('source SHA')
        docker=shutil.which('docker')
        if not docker:raise ValueError('Docker missing')
        r['docker_server_version']=c.checked(call([docker,'version','--format','{{json .Server.Version}}']))
        f.local_docker_endpoint(docker,root,r)
        capacity=f.capacity_decision(local.host_meminfo(),shutil.disk_usage('/').free,
            json.loads(c.checked(call([docker,'info','--format','{{json .MemTotal}}']))),c.checked(call([docker,'ps','-q'])))
        r['resource_check']=capacity
        if not capacity['passed']:raise ValueError('resource gate')
        r['image_identity']=local.image_identity(c.checked(call([docker,'image','inspect',c.IMAGE])))
        state=local.state_dir(args.state);r['state']=str(state);bundle=state/'analysis';bundle.mkdir()
        for name,src in sources.items(): shutil.copyfile(src,bundle/name)
        if {x.name for x in bundle.iterdir()}!=set(BUNDLE) or any(c.sha(bundle/name)!=r['tool_hashes'][name] for name in BUNDLE):raise ValueError('bundle hash')
        shim=state/'docker';shim.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -B '+shlex.quote(str(Path(__file__).resolve()))+' --adapter "$@"\n');shim.chmod(0o700)
        env={'PATH':str(state)+os.pathsep+os.environ['PATH'],'OSC_STATE':str(state),'OSC_REAL_DOCKER':docker,'OSC_INPUT_ROOT':str(root),
             'OSC_PAYLOAD':str(bundle),'OSC_DEADLINE':str(c.DEADLINE),'OSC_LOCAL_ADAPTER':'1'}
        if output is not None: env['OSC_OUTPUT']=str(output)
        if candidate is not None: env['OSC_CANDIDATE']=str(candidate);r['candidate_manifest_sha256']=c.sha(candidate/'manifest.json')
        f.require_budget(LAUNCH_RESERVE)
        env['OSC_COMMAND_DEADLINE']=str(time.monotonic()+WRAPPER_SECONDS)
        result=call(['bash','scripts/kicad/run.sh','python3','-B','/analysis/'+payload_name,*payload_args],WRAPPER_SECONDS,env)
        f.collect_resources(state,r);save()
        detail=None
        try:
            detail=json.loads(result['output']);(out/'zone.json').write_text(json.dumps(detail,indent=2)+'\n')
        except Exception as exc: r['payload_parse_error']=type(exc).__name__+': '+str(exc)[:200]
        c.cleanup_owned(state,docker,root,c.run_command,outcomes=r['cleanup']);save()
        c.normal_exit(r['cleanup'])
        c.checked(result)
        if detail is None:raise ValueError('payload JSON missing or malformed')
        if args.payload=='zone': payload.validate_result(detail)
        else: r['host_verification']=verify_output(args.payload,detail,output,candidate)
        r['status']=expected_status
    except Exception as exc:
        failed=True;r.update(status='FAILED',error=type(exc).__name__+': '+str(exc)[:700])
    finally:
        c.RESERVE_SECONDS=7
        if state is not None:
            try:
                c.cleanup_owned(state,docker,root,c.run_command,outcomes=r['cleanup'])
                if len(r['cleanup'])!=2 or any(x['status']!='REMOVED_CONFIRMED' for x in r['cleanup']):raise ValueError('two owned exits not confirmed')
            except Exception as exc:failed=True;r.update(status='FAILED',cleanup_error=str(exc)[:500])
            try:f.collect_resources(state,r)
            except Exception as exc:failed=True;r.update(status='FAILED',resource_receipt_error=str(exc)[:500])
        try:r['after']=c.snapshot(root)
        except Exception as exc:failed=True;r.update(status='FAILED',after_error=str(exc)[:500])
        r['elapsed_seconds']=time.monotonic()-started
        if r['elapsed_seconds']>TOTAL_SECONDS:failed=True;r.update(status='FAILED',deadline_exceeded=True)
        save();c.PINS=old_pins
        detail=None
        if (out/'zone.json').is_file():
            try: detail=json.loads((out/'zone.json').read_text())
            except Exception: detail=None
        print(summarize(r,detail),flush=True)
    return int(failed)

def verify_output(mode,detail,output,candidate):
    """Host-side re-verification of exported artifacts; never trusts the container's receipt alone."""
    if not isinstance(detail,dict) or detail.get('status')!=MODES[mode][2] or detail.get('board_acceptance') is not False or 'failure' in detail: raise ValueError('payload status')
    if detail.get('refill_zones_option_used') is not False: raise ValueError('refill option')
    verification={}
    if mode=='candidate':
        manifest=json.loads((output/'manifest.json').read_text())
        if c.sha(output/'manifest.json')!=detail.get('manifest_sha256'): raise ValueError('manifest hash')
        for kind in ('before','after'):
            for name,expected in manifest['exported'][kind].items():
                p=output/kind/name
                if p.is_symlink() or not p.is_file() or c.sha(p)!=expected or detail['exported'][kind][name]!=expected: raise ValueError('exported hash '+kind+'/'+name)
        if manifest['exported']['before']['osc-core.kicad_pro']!=inv.PINS['osc-core.kicad_pro'] or manifest['exported']['before']['osc-core.kicad_dru']!=inv.PINS['osc-core.kicad_dru']: raise ValueError('pinned project/rules')
        verification['nonfill_host']={kind:inv.semantic_hash(output/kind/'osc-core.kicad_pcb') for kind in ('before','after')}
        if len({*verification['nonfill_host'].values(),manifest['nonfill_sha256']['input']})!=1: raise ValueError('host non-fill semantic hash mismatch')
        verification['owners_host']={kind:payload.zone_fill_owners(output/kind/'osc-core.kicad_pcb') for kind in ('before','after')}
        if verification['owners_host']['before']['filled_polygon_by_zone'] or set(verification['owners_host']['after']['filled_polygon_by_zone'])!={payload.TARGET_ZONE}: raise ValueError('host fill ownership')
        if detail.get('input_before')!=inv.PINS or detail.get('input_after')!=inv.PINS: raise ValueError('input identity')
        if detail.get('worker_summary',{}).get('fill',{}).get('returned') is not True or detail['worker_summary'].get('failure') is not None: raise ValueError('worker fill')
        for name,expected in manifest['exported_receipts'].items():
            if c.sha(output/name)!=expected or detail['exported_receipts'][name]!=expected: raise ValueError('exported receipt hash '+name)
        exported_worker=json.loads((output/'zone.json').read_text())
        if exported_worker.get('fill',{}).get('returned') is not True or 'failure' in exported_worker: raise ValueError('exported worker receipt')
        if detail.get('command',{}).get('status')!='COMPLETE' or detail.get('normalize',{}).get('status')!='COMPLETE': raise ValueError('worker commands')
    else:
        manifest=json.loads((output/'drc-manifest.json').read_text())
        if manifest.get('candidate_manifest_sha256')!=c.sha(candidate/'manifest.json'): raise ValueError('candidate manifest hash')
        for kind in ('before','after'):
            p=output/('drc-'+kind+'.json');expected=detail['drc_'+kind]['report_sha256']
            if p.is_symlink() or not p.is_file() or c.sha(p)!=expected or manifest['reports'][kind]!=expected: raise ValueError('report hash '+kind)
            counts,identities=inv.drc_summary(p)
            if counts!=detail['drc_'+kind]['counts'] or inv.digest(sorted(identities.items()))!=detail['drc_'+kind]['identities']['identity_sha256']: raise ValueError('report summary mismatch '+kind)
            if detail['commands'][kind].get('status')!='COMPLETE' or detail['commands'][kind].get('exit_code')!=0: raise ValueError('drc command '+kind)
            verification['host_counts_'+kind]=counts
    frames=detail.get('memory_telemetry',[])
    if not frames or any('error' in f or f.get('values',{}).get('memory.max')!=inv.MEMORY_CAP or f.get('values',{}).get('memory.swap.max')!=0 for f in frames): raise ValueError('telemetry')
    if any(f.get('events_since_baseline',{}).get(k,0)>0 for f in frames for k in ('oom','oom_kill')): raise ValueError('OOM event')
    if not isinstance(detail.get('elapsed_seconds'),(int,float)) or not 0<=detail['elapsed_seconds']<=PAYLOAD_SECONDS: raise ValueError('payload deadline')
    return verification

def parse(argv):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('run');a.add_argument('source');a.add_argument('out')
    a.add_argument('--state',required=True);a.add_argument('--authorization',required=True)
    a.add_argument('--payload',choices=sorted(MODES),default='zone');a.add_argument('--output');a.add_argument('--candidate')
    b=sub.add_parser('cleanup');b.add_argument('state');b.add_argument('out')
    return p.parse_args(argv)

def main(argv):
    if argv[:1]==['--adapter']:return adapter(argv[1:])
    args=parse(argv)
    return run(args) if args.command=='run' else local.cleanup(args)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
