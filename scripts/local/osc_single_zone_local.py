"""Local WSL controller for the single selected-zone diagnostic on a disposable copy of the frozen core.

Local-only counterpart of osc_fill_check.py for the two-pair +12V question:
same owned-container records, read-only oracle mounts, 1 CPU / 2 GiB /
zero extra swap / 64 PIDs / network none, fresh per-create resource gate,
owned cleanup and the existing 590 s controller / 420 s payload / 430 s
attach ceilings. The hosted gate is replaced by local_gate from the
synthetic adapter (never spoofed). Original board files are mounted
read-only and hash-checked before and after. No DRC, no acceptance.

Deadline chains are budget profiles (osc_derived_fill.BUDGETS): 'standard'
is the hosted-parity chain above; 'fill-520-probe' is the single approved
F.Cu AGND probe whose only growth is the fill cap and the layers that must
contain it. The wrapper exports the outer stop it enforces and the heavy-guard
cap it was given; the controller refuses a mismatch, and refuses an exported
outer stop unless it is itself the session leader that the wrapper's process
group kill targets. These are consistency checks between cooperating scripts,
not authentication: a caller that forges the variables gets only the
controller's own cooperative deadline.
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
import osc_derived_fill as derived
import osc_derived_fill_payload as derivedpayload

PAYLOAD_SECONDS=f.PAYLOAD_SECONDS   # zone/candidate/drc payloads run only under the standard budget
CLEANUP_RESERVE=f.CLEANUP_RESERVE
STATUS=payload.STATUS
MODE='LOCAL_WSL_SINGLE_ZONE'
PAYLOAD_NAME='osc_single_zone_payload.py'
DRC_PAYLOAD_NAME='osc_zone_drc_payload.py'
DERIVED_PAYLOAD_NAME='osc_derived_fill_payload.py'
DERIVED_HELPER_NAME='osc_derived_fill.py'
BUNDLE=(PAYLOAD_NAME,DRC_PAYLOAD_NAME,DERIVED_PAYLOAD_NAME,DERIVED_HELPER_NAME,'osc_frozen_fill.py','osc_frozen_topology.py')
MODES={'zone':(PAYLOAD_NAME,[],payload.STATUS),'candidate':(DRC_PAYLOAD_NAME,['candidate'],drcpayload.CANDIDATE_STATUS),'drc':(DRC_PAYLOAD_NAME,['drc'],drcpayload.DRC_STATUS),
       'derive':(DERIVED_PAYLOAD_NAME,['derive'],derivedpayload.DERIVE_STATUS),'evaluate':(DERIVED_PAYLOAD_NAME,['evaluate'],derivedpayload.EVALUATE_STATUS)}
SPEC_MODES=('derive','evaluate')

def check_shared_constants():
    """The budget table mirrors two hosted values the container bundle cannot import; drift is an import-time failure here."""
    if derived.CLEANUP_RESERVE!=f.CLEANUP_RESERVE: raise ImportError('osc_derived_fill.CLEANUP_RESERVE differs from osc_fill_check')
    probe=f.readonly_args(['run','--volume','/s:/work','--volume','/h:/tmp/kicad-home','--network','none',c.IMAGE],'/s','/p')
    if not any(a.startswith('/scratch:') and a.endswith('size=%dm,mode=1777'%(derived.SCRATCH_TMPFS_BYTES//2**20)) for a in probe): raise ImportError('osc_derived_fill.SCRATCH_TMPFS_BYTES differs from the hosted scratch mount')
check_shared_constants()

def outer_stop_confirmation(b,outer,environ=os.environ):
    """Record and check the wrapper's exported outer stop and heavy-guard cap against this budget and this process's session."""
    record={'wrapper_outer_stop_seconds':outer,'heavy_guard_max_run_env':environ.get('OSC_HEAVY_GUARD_MAX_RUN'),'session_leader':os.getsid(0)==os.getpid()}
    if outer is None: return record
    if not record['session_leader']: raise ValueError('outer stop exported but this controller is not a session leader, so no process-group kill targets it')
    cap=record['heavy_guard_max_run_env']
    if cap is None or not cap.isdigit() or int(cap)<b['heavy_guard_max_run']: raise ValueError('heavy-guard cap '+str(cap)+' does not cover budget '+b['name'])
    return record

def bundle_sources():
    return {PAYLOAD_NAME:Path(__file__).with_name(PAYLOAD_NAME).resolve(),DRC_PAYLOAD_NAME:Path(__file__).with_name(DRC_PAYLOAD_NAME).resolve(),
            DERIVED_PAYLOAD_NAME:Path(derivedpayload.__file__).resolve(),DERIVED_HELPER_NAME:Path(derived.__file__).resolve(),
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

def extra_mounts(args,output,candidate,spec=None):
    """Only the local export modes add a writable /output plus read-only /candidate and /spec bind mounts."""
    result=list(args);i=result.index(c.IMAGE);extra=[]
    if output:
        p=Path(output)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink(): raise ValueError('output mount must be an existing absolute directory')
        extra+=['--volume',str(p)+':/output']
    if candidate:
        p=Path(candidate)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink() or not (p/'manifest.json').is_file(): raise ValueError('candidate mount must be an existing directory with manifest.json')
        extra+=['--volume',str(p)+':/candidate:ro']
    if spec:
        p=Path(spec)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink() or not (p/'spec.json').is_file() or not (p/'context.json').is_file(): raise ValueError('spec mount must be an existing directory with spec.json and context.json')
        extra+=['--volume',str(p)+':/spec:ro']
    result[i:i]=extra
    return result

def adapter(argv):
    if os.environ.get('OSC_LOCAL_ADAPTER')!='1': raise ValueError('local adapter shim invoked outside a local run')
    root=Path(os.environ['OSC_INPUT_ROOT']);bundle=Path(os.environ['OSC_PAYLOAD'])
    args=f.readonly_args(argv,root,bundle)
    args=extra_mounts(args,os.environ.get('OSC_OUTPUT'),os.environ.get('OSC_CANDIDATE'),os.environ.get('OSC_SPEC'))
    resource_preflight()
    c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    is_payload=any('/analysis/'+name in a for a in args[args.index(c.IMAGE)+1:] for name in (PAYLOAD_NAME,DRC_PAYLOAD_NAME,DERIVED_PAYLOAD_NAME))
    b=derived.budget(os.environ.get('OSC_BUDGET','standard'))
    f.require_budget(b['attach']+CLEANUP_RESERVE+7+10 if is_payload else 40+CLEANUP_RESERVE+7)
    if is_payload and float(os.environ['OSC_COMMAND_DEADLINE'])-time.monotonic()<b['payload']+10+7:
        raise TimeoutError('insufficient wrapper budget after setup for payload and create')
    if not is_payload: return c.adapter(args,memory_policy='fill-2g-noswap',execution_policy='fill-probe-20')
    return attach_adapter(args,b['attach'])

def attach_adapter(args,attach_seconds):
    """The hosted adapter unchanged (ownership record, labels, 1 CPU / 2 GiB / no extra swap / 64 PIDs, forbidden-option checks) with one ceiling swapped: only 'docker start --attach' receives the budget's attach seconds."""
    original=c.run_command
    def wrapped(argv,root,seconds=150,extra_env=None,isolated=True):
        if argv[1:3]==['start','--attach']: seconds=attach_seconds
        return original(argv,root,seconds,extra_env,isolated)
    c.run_command=wrapped
    try: return c.adapter(args,memory_policy='fill-2g-noswap',execution_policy='fill-430')
    finally: c.run_command=original

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
        compact=detail.get('worker_summary') if isinstance(detail.get('worker_summary'),dict) else {}
        if isinstance(compact.get('classification'),dict):
            summary['classification']={k:v.get('class') for k,v in compact['classification'].items()};summary['unconnected_count']=compact.get('unconnected_count')
            summary['fill']=compact.get('fill');summary['identity_key']=detail.get('identity_key')
        if isinstance(detail.get('reuse'),dict): summary['reuse']={k:detail['reuse'].get(k) for k in ('reusable','reason')}
        if isinstance(detail.get('parent'),dict): summary['parent']={k:detail['parent'].get(k) for k in ('reusable','reason')}
    return json.dumps(summary,sort_keys=True)

def run(args):
    started=time.monotonic();b=derived.budget(args.budget);c.DEADLINE=started+b['controller'];c.RESERVE_SECONDS=CLEANUP_RESERVE+7
    root=Path(args.source).resolve();out=Path(args.out).resolve()
    if root==out or out.is_relative_to(root): raise ValueError('separate output required')
    payload_name,payload_args,expected_status=MODES[args.payload]
    output=Path(args.output).resolve() if args.output else None;candidate=Path(args.candidate).resolve() if args.candidate else None
    spec_file=Path(args.spec).resolve() if args.spec else None
    # Argument validation before any side effect: no directories, no allowlist mutation.
    if args.payload in ('candidate','drc')+SPEC_MODES and output is None: raise ValueError('--output required for '+args.payload)
    if args.payload in ('drc','evaluate') and candidate is None: raise ValueError('--candidate required for '+args.payload)
    if args.payload in SPEC_MODES and spec_file is None: raise ValueError('--spec required for '+args.payload)
    if spec_file is not None and args.payload not in SPEC_MODES: raise ValueError('--spec only applies to derive/evaluate')
    spec=derived.load_spec(spec_file,topology.EXPECTED) if spec_file is not None else None
    derived.budget_allows(b,args.payload,spec['zones'] if spec else None,chained=args.payload=='derive' and candidate is not None)
    outer=os.environ.get('OSC_OUTER_STOP_SECONDS')
    if outer is None and b['name']!='standard': raise ValueError('wrapper did not confirm the outer stop for budget '+b['name'])
    if outer is not None and outer!=str(b['outer_stop']): raise ValueError('wrapper outer stop '+outer+' differs from budget '+b['name'])
    if output is not None and output.exists(): raise ValueError('output directory must not pre-exist')
    out.mkdir(exist_ok=False)
    if output is not None: output.mkdir(mode=0o755)
    old_pins=c.PINS;c.PINS=board_pins()
    r={'status':'STARTED','mode':MODE,'payload':args.payload,'output':str(output) if output else None,'candidate':str(candidate) if candidate else None,'hosted':False,'source_sha':c.SOURCE,'tooling_sha':os.environ.get('TOOLING_SHA'),'image':c.IMAGE,
       'target_zone':payload.TARGET_ZONE if spec is None else None,'pairs':payload.PAIRS if spec is None else spec['pairs'],'spec':spec,'commands':[],'cleanup':[],'full_board_fill':False,'board_acceptance':False,'repair_basis':False,
       'drc':'NOT RUN: whole-board DRC is outside this selected-zone connectivity diagnostic',
       'deadline_policy':{'budget':b['name'],'total_seconds':b['controller'],'outer_stop_seconds':b['outer_stop'],'outer_stop_confirmed_by_wrapper':outer is not None,'payload_seconds':b['payload'],'attach_seconds':b['attach'],
           'wrapper_seconds':b['wrapper'],'cleanup_reserve_seconds':CLEANUP_RESERVE,'launch_reserve_seconds':b['launch_reserve'],'worker_deadline_seconds':b['worker_deadline'],
           'post_stop_cleanup_seconds':b['post_stop_cleanup'],'heavy_guard_max_run_seconds':b['heavy_guard_max_run'],'pcb_limit_bytes':b['pcb_limit'],
           'adapter_execution_policy':"hosted 'fill-430' with docker start --attach swapped to %d s"%b['attach'],
           'stage_caps':derivedpayload.EVALUATE_CAPS if args.payload=='evaluate' else b['stage_caps'],
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
        r['deadline_policy']['outer_stop_confirmation']=outer_stop_confirmation(b,outer)
        r['before']=c.snapshot(root)
        if (root/'boards'/'osc-core'/'osc-core.kicad_pcb').stat().st_size!=derived.SOURCE_BOARD_BYTES: raise ValueError('source board size differs from the budget table assumption')
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
             'OSC_PAYLOAD':str(bundle),'OSC_DEADLINE':str(c.DEADLINE),'OSC_LOCAL_ADAPTER':'1','OSC_BUDGET':b['name']}
        if output is not None: env['OSC_OUTPUT']=str(output)
        if candidate is not None: env['OSC_CANDIDATE']=str(candidate);r['candidate_manifest_sha256']=c.sha(candidate/'manifest.json')
        if spec is not None:
            spec_dir=state/'spec';spec_dir.mkdir()
            (spec_dir/'spec.json').write_text(json.dumps({'zones':spec['zones'],'pairs':[list(p) for p in spec['pairs']],'note':spec['note']}))
            r['context']={'image_id':r['image_identity']['id'],'kicad':derived.KICAD_VERSION,'source_pins':dict(inv.PINS),'process':derived.PROCESS_VERSION,'tooling_sha':t,'budget':b['name']}
            (spec_dir/'context.json').write_text(json.dumps(r['context']));env['OSC_SPEC']=str(spec_dir)
            r['expected_identity_key']=None if args.payload=='derive' and candidate is not None else derived.identity_key(derived.identity(inv.PINS,spec['zones'],r['context']['image_id']))
        f.require_budget(b['launch_reserve'])
        env['OSC_COMMAND_DEADLINE']=str(time.monotonic()+b['wrapper'])
        result=call(['bash','scripts/kicad/run.sh','python3','-B','/analysis/'+payload_name,*payload_args],b['wrapper'],env)
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
        elif args.payload in SPEC_MODES:
            derivedpayload.validate_result(detail,args.payload,b['name'])
            r['host_verification']=verify_derived_output(args.payload,detail,output,candidate,root,r)
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
        if r['elapsed_seconds']>b['controller']:failed=True;r.update(status='FAILED',deadline_exceeded=True)
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

def verify_derived_output(mode,detail,output,candidate,root,receipt):
    """Host-side re-verification for derive/evaluate: identity recomputed from the host's own image inspect and pins, files re-hashed, classification recomputed."""
    verification={}
    source_nonfill=inv.semantic_hash(root/'boards'/'osc-core'/'osc-core.kicad_pcb');verification['source_nonfill_host']=source_nonfill
    if detail.get('source_nonfill')!=source_nonfill: raise ValueError('host source semantic hash mismatch')
    if detail.get('tooling_sha')!=receipt['tooling_sha'] or detail['identity']['image_id']!=receipt['image_identity']['id']: raise ValueError('context echo')
    budget_name=receipt.get('deadline_policy',{}).get('budget','standard')
    if detail.get('budget')!=budget_name: raise ValueError('payload budget echo')
    zones=receipt['spec']['zones']
    worker=json.loads((output/'zone.json').read_text())
    for name,expected in detail['exported_receipts'].items():
        if c.sha(output/name)!=expected: raise ValueError('exported receipt hash '+name)
    if worker.get('failure') is not None or worker.get('counts')!=payload.COUNTS: raise ValueError('exported worker receipt')
    if mode=='derive':
        manifest=json.loads((output/'manifest.json').read_text())
        if c.sha(output/'manifest.json')!=detail.get('manifest_sha256') or manifest.get('status')!=derived.MANIFEST_STATUS: raise ValueError('manifest')
        if manifest.get('budget')!=budget_name or manifest.get('stage_caps')!=derived.budget(budget_name)['stage_caps']: raise ValueError('manifest budget')
        parent=detail.get('parent');parent_key=None
        if (candidate is None)!=(parent is None): raise ValueError('parent record does not match the mounted candidate')
        if candidate is not None:
            recorded=derived.manifest_identity(json.loads((candidate/'manifest.json').read_text()),candidate)[0]
            parent_expected=derived.identity(inv.PINS,recorded['zones'],receipt['image_identity']['id'],derived.KICAD_VERSION,recorded.get('parent_key'))
            parent_check=derived.verify_derived(candidate,parent_expected,source_nonfill,inv.semantic_hash);verification['parent']=parent_check
            if not parent_check['reusable'] or parent_check['identity']!=parent.get('identity') or parent_check['ancestor_zones']!=parent.get('ancestor_zones'): raise ValueError('host parent verification: '+parent_check['reason'])
            parent_key=derived.identity_key(parent_check['identity'])
        expected=derived.identity(inv.PINS,zones,receipt['image_identity']['id'],derived.KICAD_VERSION,parent_key)
        reuse=derived.verify_derived(output,expected,source_nonfill,inv.semantic_hash);verification['reuse']=reuse
        if not reuse['reusable'] or reuse['identity']!=detail['identity'] or manifest['identity_key']!=detail['identity_key']: raise ValueError('host identity verification: '+reuse['reason'])
        if manifest['classification']!=detail['worker_summary']['classification']: raise ValueError('manifest classification')
        if detail['worker_summary']['fill'].get('returned') is not True: raise ValueError('fill')
    else:
        evaluation=json.loads((output/'evaluation.json').read_text())
        if c.sha(output/'evaluation.json')!=detail.get('evaluation_sha256') or evaluation.get('status')!=derivedpayload.EVALUATE_STATUS: raise ValueError('evaluation')
        if receipt['expected_identity_key']!=detail['identity_key'] or evaluation['identity_key']!=detail['identity_key']: raise ValueError('evaluate identity key differs from the host expectation')
        reuse=derived.verify_derived(candidate,detail['identity'],source_nonfill,inv.semantic_hash);verification['reuse']=reuse
        if not reuse['reusable']: raise ValueError('host reuse verification: '+reuse['reason'])
        if evaluation['classification']!=detail['worker_summary']['classification']: raise ValueError('evaluation classification')
    # Recompute the classification from the exported native observations instead of trusting the summary.
    table={r['uuid']:r for r in worker['reloaded']['zone_table']}
    if len(table)!=payload.COUNTS['zone'] or not set(zones)<=set(table): raise ValueError('exported zone table incomplete')
    recomputed={}
    for a,b in receipt['spec']['pairs']:
        key=a+'<->'+b;before=worker['before']['pairs'][key]['connected'];after=worker['reloaded']['pairs'][key]['connected']
        recomputed[key]={'before':before,'after':after}
        row=detail['worker_summary']['classification'][key]
        if (row['connected_before'],row['connected_after'])!=(before,after): raise ValueError('classification flags '+key)
        if (row['class'] in ('CONNECTED_ON_INPUT','CONNECTED_VIA_SELECTED_FILL'))!=(before or after) or (row['class']=='CONNECTED_ON_INPUT')!=before: raise ValueError('classification class '+key)
        if row['class']=='UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN' and not row['unfilled_net_zones']: raise ValueError('unevaluable without unfilled zones '+key)
        if row['class']=='OPEN_WITH_ALL_NET_ZONES_FILLED' and (row['unfilled_net_zones'] or not row['net_zones']): raise ValueError('open-all-filled flags '+key)
        net=topology.EXPECTED[a]['net']
        expected_net_zones=sorted(u for u,r in table.items() if r['net']==net and not r['rule_area'])
        if row['net_zones']!=expected_net_zones: raise ValueError('net zone list contradicts exported zone table '+key)
        filled=lambda u:bool(table[u]['counts']) and all(cnt>=1 for cnt in table[u]['counts'].values())
        if row['unfilled_net_zones']!=[u for u in expected_net_zones if not filled(u)]: raise ValueError('fill state contradicts exported zone table '+key)
    verification['recomputed_connectivity']=recomputed
    return verification

def adopt_legacy(args):
    """Write the adoption sidecar for a legacy single-zone candidate directory from its recorded controller receipt."""
    output=Path(args.candidate).resolve();receipt=json.loads(Path(args.receipt).read_text())
    if (output/derived.SIDECAR).exists(): raise FileExistsError('sidecar already present')
    if receipt.get('status')!=derived.LEGACY_STATUS or receipt.get('image')!=c.IMAGE: raise ValueError('receipt is not a passed legacy candidate run')
    image_id=receipt['image_identity']['id']
    if c.IMAGE not in receipt['image_identity']['repo_digests']: raise ValueError('receipt image digest')
    # The receipt is bound to this directory through the payload detail it recorded: manifest hash and exported board hashes.
    payload_runs=[cmd for cmd in receipt.get('commands',[]) if cmd.get('argv',[])[-2:]==['/analysis/'+DRC_PAYLOAD_NAME,'candidate']]
    if len(payload_runs)!=1: raise ValueError('receipt does not record exactly one candidate payload run')
    detail=json.loads(payload_runs[0]['output']);manifest=json.loads((output/'manifest.json').read_text())
    if detail.get('manifest_sha256')!=c.sha(output/'manifest.json') or detail.get('exported')!=manifest.get('exported') or detail.get('status')!=derived.LEGACY_STATUS: raise ValueError('receipt does not describe this candidate directory')
    sidecar=derived.legacy_sidecar(output/'manifest.json',image_id,args.attestation)
    sidecar['receipt']={'tooling_sha':receipt.get('tooling_sha'),'tool_hashes':receipt.get('tool_hashes'),'status':receipt.get('status')}
    (output/derived.SIDECAR).write_text(json.dumps(sidecar,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'sidecar':str(output/derived.SIDECAR),'identity_key':sidecar['identity_key']}))
    return 0

def parse(argv):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('run');a.add_argument('source');a.add_argument('out')
    a.add_argument('--state',required=True);a.add_argument('--authorization',required=True)
    a.add_argument('--payload',choices=sorted(MODES),default='zone');a.add_argument('--output');a.add_argument('--candidate');a.add_argument('--spec')
    a.add_argument('--budget',choices=sorted(derived.BUDGETS),default='standard')
    b=sub.add_parser('cleanup');b.add_argument('state');b.add_argument('out')
    e=sub.add_parser('budget');e.add_argument('name',choices=sorted(derived.BUDGETS));e.add_argument('key',choices=('outer_stop','heavy_guard_max_run','post_stop_cleanup','controller'))
    d=sub.add_parser('adopt-legacy');d.add_argument('candidate');d.add_argument('receipt');d.add_argument('--attestation',required=True)
    return p.parse_args(argv)

def main(argv):
    if argv[:1]==['--adapter']:return adapter(argv[1:])
    args=parse(argv)
    if args.command=='run': return run(args)
    if args.command=='adopt-legacy': return adopt_legacy(args)
    if args.command=='budget': print(derived.budget(args.name)[args.key]);return 0
    return local.cleanup(args)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
