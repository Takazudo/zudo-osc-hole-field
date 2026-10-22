"""Hosted-only synthetic qualification:120s absolute total, owned cleanup."""
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import time
import osc_candidate_check as c
import osc_fill_check as f
import osc_synthetic_zone as q

TOTAL=120
RESERVE=32

def remaining(need=0):
    left=c.DEADLINE-time.monotonic()
    if left<need:raise TimeoutError('insufficient synthetic total budget')
    return left

def adapter(argv):
    c.DEADLINE=float(os.environ['OSC_SYNTHETIC_DEADLINE']);c.RESERVE_SECONDS=RESERVE
    state=Path(os.environ['OSC_STATE']);root=Path(os.environ['OSC_INPUT_ROOT'])
    args=f.readonly_args(argv,root,Path(os.environ['OSC_PAYLOAD']))
    docker=os.environ['OSC_REAL_DOCKER']
    f.local_docker_endpoint(docker,root)
    cap=f.capacity_decision(Path('/proc/meminfo').read_text(),shutil.disk_usage('/').free,
        json.loads(c.checked(c.run_command([docker,'info','--format','{{json .MemTotal}}'],root,5))),
        c.checked(c.run_command([docker,'ps','-q'],root,5)))
    (state/('capacity-'+str(time.monotonic_ns())+'.json')).write_text(json.dumps(cap))
    if not cap['passed']:raise ValueError('fresh pre-create resource gate')
    remaining(RESERVE+15)
    status=c.adapter(args,memory_policy='fill-2g-noswap')
    # Each oracle invocation owns at most one container here. Cleanup before
    # returning to the wrapper, including nonzero exit; no client-timeout fiction.
    c.RESERVE_SECONDS=7
    outcomes=[]
    try:
        c.cleanup_owned(state,os.environ['OSC_REAL_DOCKER'],root,outcomes=outcomes)
    finally:
        (state/('cleanup-'+str(time.monotonic_ns())+'.json')).write_text(json.dumps(outcomes))
    if len(outcomes)!=1 or outcomes[0]['status']!='REMOVED_CONFIRMED':raise ValueError('synthetic cleanup unproven')
    s=outcomes[0]['state_before_cleanup']
    if s.get('Running') or s.get('ExitCode')!=0:status=1
    return status

def parse_output(text):
    rows=[]
    for line in text.splitlines():
        if line.startswith('{'):
            r=json.loads(line)
            if 'events' in r:rows.append(r)
    if not rows:raise ValueError('synthetic receipt missing')
    return rows[-1]

def main():
    started=time.monotonic();c.DEADLINE=started+TOTAL-5;c.RESERVE_SECONDS=RESERVE
    if len(sys.argv)!=3:raise ValueError('SOURCE OUT required')
    root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    if root==out or out.is_relative_to(root):raise ValueError('separate output required')
    out.mkdir(exist_ok=False)
    r={'status':'STARTED','source_sha':c.SOURCE,'tooling_sha':os.environ.get('TOOLING_SHA'),'image':c.IMAGE,'total_seconds':TOTAL,'commands':[],'cleanup':[],'full_board_executed':False,'candidate_ingestion':'UNIMPLEMENTED'}
    state=None;docker=None;failed=False
    def save():
        (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
    def call(args,seconds=10,env=None):
        result=c.run_command(args,root,seconds,env);r['commands'].append(result);save();return result
    try:
        save()
        if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':raise ValueError('hosted runner required')
        if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):raise ValueError('alternate Docker endpoint forbidden')
        t=r['tooling_sha']
        if not t or len(t)!=40 or any(x not in '0123456789abcdef' for x in t):raise ValueError('tooling SHA')
        r['before']=c.snapshot(root)
        r['tool_hashes']={p.name:c.sha(p) for p in [Path(__file__),Path(q.__file__),Path(c.__file__),Path(f.__file__)]}
        if c.checked(call(['git','rev-parse','HEAD']))!=c.SOURCE:raise ValueError('source SHA')
        docker=shutil.which('docker')
        if not docker:raise ValueError('Docker missing')
        f.local_docker_endpoint(docker,root,r)
        capacity=f.capacity_decision(Path('/proc/meminfo').read_text(),shutil.disk_usage('/').free,
            json.loads(c.checked(call([docker,'info','--format','{{json .MemTotal}}']))),c.checked(call([docker,'ps','-q'])))
        r['resource_check']=capacity
        if not capacity['passed']:raise ValueError('resource gate')
        # Pull belongs to120s total. Failure/insufficient time never starts fixture.
        c.checked(call([docker,'pull',c.IMAGE],45))
        remaining(RESERVE+30)
        state=Path(tempfile.mkdtemp(prefix='osc-synthetic-'));bundle=state/'analysis';bundle.mkdir()
        shutil.copyfile(q.__file__,bundle/'osc_synthetic_zone.py')
        if c.sha(bundle/'osc_synthetic_zone.py')!=r['tool_hashes']['osc_synthetic_zone.py']:raise ValueError('bundle hash')
        shim=state/'docker';shim.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(Path(__file__).resolve()))+' --adapter "$@"\n');shim.chmod(0o700)
        env={'PATH':str(state)+os.pathsep+os.environ['PATH'],'OSC_STATE':str(state),'OSC_REAL_DOCKER':docker,'OSC_INPUT_ROOT':str(root),'OSC_PAYLOAD':str(bundle),'OSC_SYNTHETIC_DEADLINE':str(c.DEADLINE)}
        result=call(['bash','scripts/kicad/run.sh','python3','-B','/analysis/osc_synthetic_zone.py'],remaining()-RESERVE-7,env)
        # Preserve first partial/failure result before checking command exit.
        detail=parse_output(result['output']);(out/'synthetic.json').write_text(json.dumps(detail,indent=2)+'\n')
        c.checked(result)
        if detail['status']!=q.STATUS:raise ValueError('synthetic qualification failed')
        r['status']=q.STATUS
    except Exception as exc:
        failed=True;r.update(status='FAILED',error=type(exc).__name__+': '+str(exc)[:700])
    finally:
        c.RESERVE_SECONDS=7
        if state is not None:
            try:
                c.cleanup_owned(state,docker,root,outcomes=r['cleanup'])
                for p in sorted(state.glob('cleanup-*.json')):r['cleanup'].extend(json.loads(p.read_text()))
                r['precreate_capacity']=[json.loads(p.read_text()) for p in sorted(state.glob('capacity-*.json'))]
                if len(r['cleanup'])!=2 or any(x['status']!='REMOVED_CONFIRMED' for x in r['cleanup']):raise ValueError('two owned exits not confirmed')
            except Exception as exc:failed=True;r.update(status='FAILED',cleanup_error=str(exc)[:500])
        try:r['after']=c.snapshot(root)
        except Exception as exc:failed=True;r.update(status='FAILED',after_error=str(exc)[:500])
        r['elapsed_seconds']=time.monotonic()-started
        if r['elapsed_seconds']>TOTAL:failed=True;r.update(status='FAILED',deadline_exceeded=True)
        save()
        print(json.dumps({k:r[k] for k in ('status','error','cleanup_error','elapsed_seconds','cleanup','before','after','resource_check') if k in r}),flush=True)
        if (out/'synthetic.json').is_file():print((out/'synthetic.json').read_text(),flush=True)
    return int(failed)

if __name__=='__main__':raise SystemExit(adapter(sys.argv[2:]) if sys.argv[1:2]==['--adapter'] else main())
