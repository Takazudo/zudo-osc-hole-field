"""Job-local controller for disposable public frozen fill baseline only."""
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import sys
import tempfile
import time
import osc_candidate_check as c
import osc_frozen_fill as inv
import osc_frozen_topology as topology

def summary_for(receipt,detail=None):
    summary={k:str(receipt[k])[:500] for k in ('status','error','cleanup_error','after_error') if k in receipt}
    summary['cleanup']=[{k:r.get(k) for k in ('status','state_before_cleanup')} for r in receipt.get('cleanup',[])][:8]
    summary['source_hashes_unchanged']=receipt.get('before')==receipt.get('after') and 'before' in receipt
    if isinstance(detail,dict):
        summary['fill_status']=detail.get('status')
        summary['fill_failure']=str(detail.get('failure'))[:700]
        drc=detail.get('drc',{})
        summary['drc_counts']={k:drc.get(k) for k in ('before','after')}
        summary['drc_delta_counts']={k:v.get('count') for k,v in drc.get('delta',{}).items() if isinstance(v,dict)}
        summary['selected_membership']={phase:{name:{'count':row.get('count'),'selected_members':row.get('selected_members')}
            for name,row in detail.get(phase,{}).get('membership',{}).items() if name in topology.EXPECTED}
            for phase in ('native_before','native_after')}
    encoded=json.dumps(summary,sort_keys=True)
    if len(encoded.encode())>8192:
        summary.pop('selected_membership',None);summary['membership_summary_omitted_for_bound']=True
        encoded=json.dumps(summary,sort_keys=True)
    if len(encoded.encode())>8192: raise ValueError('bounded summary exceeds limit')
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
    return c.adapter(readonly_args(argv,root,payload))

def main():
    if len(sys.argv)!=3: raise ValueError('usage: osc_fill_check.py SOURCE OUT')
    root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    if root==out or out.is_relative_to(root): raise ValueError('output must be separate')
    out.mkdir(exist_ok=False)
    payload=Path(__file__).with_name('osc_frozen_fill.py').resolve()
    old_pins,old_deadline=c.PINS,c.DEADLINE
    c.DEADLINE=time.monotonic()+480
    c.PINS={**c.PINS,**{'boards/osc-core/'+name:h for name,h in inv.PINS.items()}}
    receipt=dict(status='STARTED',source_sha=c.SOURCE,tooling_sha=os.environ.get('TOOLING_SHA'),
        image=c.IMAGE,commands=[],cleanup=[],candidate_ingestion='UNIMPLEMENTED')
    state=None;docker=None;failed=False
    def save(): (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    try:
        save()
        tooling=receipt['tooling_sha']
        if not tooling or len(tooling)!=40 or any(x not in '0123456789abcdef' for x in tooling): raise ValueError('tooling SHA required')
        receipt['tool_hashes']={p.name:c.sha(p) for p in [Path(__file__),payload,Path(topology.__file__),Path(c.__file__)]}
        receipt['before']=c.snapshot(root)
        head=c.run_command(['git','rev-parse','HEAD'],root,10);receipt['commands'].append(head)
        if c.checked(head)!=c.SOURCE: raise ValueError('source HEAD mismatch')
        docker=shutil.which('docker')
        if not docker: raise ValueError('Docker unavailable')
        pull=c.run_command([docker,'pull',c.IMAGE],root,120);receipt['commands'].append(pull);c.checked(pull)
        state=Path(tempfile.mkdtemp(prefix='osc-fill-owned-'))
        bundle=state/'analysis';bundle.mkdir()
        for src in (payload,Path(topology.__file__).resolve()): shutil.copyfile(src,bundle/src.name)
        if {x.name for x in bundle.iterdir()}!={'osc_frozen_fill.py','osc_frozen_topology.py'}: raise ValueError('bundle allowlist')
        if any(c.sha(bundle/src.name)!=receipt['tool_hashes'][src.name] for src in (payload,Path(topology.__file__))): raise ValueError('bundle hash')
        shim=state/'docker';shim.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(Path(__file__).resolve()))+' --adapter "$@"\n');shim.chmod(0o700)
        env={'PATH':str(state)+os.pathsep+os.environ['PATH'],'OSC_STATE':str(state),'OSC_REAL_DOCKER':docker,
             'OSC_INPUT_ROOT':str(root),'OSC_PAYLOAD':str(bundle)}
        commands=[*c.COMMANDS,['bash','scripts/kicad/run.sh','python3','-B','/analysis/osc_frozen_fill.py']]
        for n,command in enumerate(commands):
            if c.DEADLINE-time.monotonic()<200: raise TimeoutError('insufficient command and cleanup reserve')
            first=len(receipt['cleanup'])
            result=c.run_command(command,root,110,env);receipt['commands'].append(result);save()
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
        if state is not None:
            try:c.cleanup_owned(state,docker,root,outcomes=receipt['cleanup'])
            except Exception as exc:failed=True;receipt.update(status='FAILED',cleanup_error=str(exc))
        try:receipt['after']=c.snapshot(root)
        except Exception as exc:failed=True;receipt.update(status='FAILED',after_error=str(exc))
        try:
            save()
            detail=None
            if (out/'fill.json').is_file():
                detail=json.loads((out/'fill.json').read_text())
            print(summary_for(receipt,detail),flush=True)
        finally: c.PINS,c.DEADLINE=old_pins,old_deadline
    return int(failed)

if __name__=='__main__':
    raise SystemExit(adapter(sys.argv[2:]) if sys.argv[1:2]==['--adapter'] else main())
