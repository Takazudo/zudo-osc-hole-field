"""Local WSL containment adapter for the tiny synthetic qualification only.

The hosted controller (osc_synthetic_check.py) requires a GitHub-hosted runner.
This adapter is a separate local entry point: it never spoofs the hosted gates,
refuses to run inside any CI environment, requires the machine-wide heavy-guard
slot plus an explicit authorization note, uses the already-present pinned image
(no pull), and keeps the same 120 s total, 115 s internal deadline, resource
caps and owned-container cleanup. osc_synthetic_local.sh adds the independent
120 s outer stop and a post-stop cleanup pass. Never loads project CAD.
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
# Hosted controller modules live in scripts/ci; this local-only entry point stays outside the hosted sparse checkout.
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ci'))
import osc_candidate_check as c
import osc_fill_check as f
import osc_synthetic_check as s
import osc_synthetic_zone as q

TOTAL=s.TOTAL
RESERVE=s.RESERVE
OUTER_STOP_SECONDS=120
CLEANUP_SECONDS=30
STATUS=q.STATUS
MODE='LOCAL_WSL_CONTAINMENT'

def local_gate(environ):
    if any(environ.get(k) for k in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI')):
        raise ValueError('local adapter refuses hosted or CI environments')
    if environ.get('DOCKER_HOST') or environ.get('DOCKER_CONTEXT'):
        raise ValueError('alternate Docker endpoint forbidden')
    # heavy-guard.sh exports this only to the command holding its machine-wide slot.
    if environ.get('HEAVY_GUARD_HELD')!='1':
        raise ValueError('machine-wide heavy-guard slot not held')

def authorization(text):
    if not isinstance(text,str) or not 16<=len(text.strip())<=500:
        raise ValueError('explicit authorization note of 16-500 characters required')
    return text.strip()

def image_identity(output):
    rows=json.loads(output)
    if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict): raise ValueError('image inspect shape')
    row=rows[0];digests=row.get('RepoDigests')
    if not isinstance(digests,list) or c.IMAGE not in digests: raise ValueError('pinned image digest not present locally')
    image_id=row.get('Id')
    if not isinstance(image_id,str) or not image_id.startswith('sha256:') or len(image_id)!=71: raise ValueError('image id')
    return {'id':image_id,'repo_digests':digests,'size_bytes':row.get('Size')}

def state_dir(path):
    p=Path(path).resolve()
    if p.exists() or p.is_symlink(): raise ValueError('state directory must not pre-exist')
    p.mkdir(mode=0o700)
    return p

def adapter(argv):
    if os.environ.get('OSC_LOCAL_ADAPTER')!='1': raise ValueError('local adapter shim invoked outside a local run')
    if os.environ.get('GITHUB_ACTIONS') or os.environ.get('RUNNER_ENVIRONMENT'): raise ValueError('hosted environment')
    return s.adapter(argv)

def run(args):
    started=time.monotonic();c.DEADLINE=started+TOTAL-5;c.RESERVE_SECONDS=RESERVE
    root=Path(args.source).resolve();out=Path(args.out).resolve()
    if root==out or out.is_relative_to(root): raise ValueError('separate output required')
    out.mkdir(exist_ok=False)
    r={'status':'STARTED','mode':MODE,'hosted':False,'source_sha':c.SOURCE,'tooling_sha':os.environ.get('TOOLING_SHA'),
       'image':c.IMAGE,'total_seconds':TOTAL,'outer_stop_seconds':OUTER_STOP_SECONDS,'commands':[],'cleanup':[],
       'full_board_executed':False,'board_acceptance':False,'candidate_ingestion':'UNIMPLEMENTED'}
    state=None;docker=None;failed=False
    def save():
        (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
    def call(argv,seconds=10,env=None):
        result=c.run_command(argv,root,seconds,env);r['commands'].append(result);save();return result
    try:
        save()
        local_gate(os.environ)
        r['authorization']=authorization(args.authorization)
        t=r['tooling_sha']
        if not t or len(t)!=40 or any(x not in '0123456789abcdef' for x in t):raise ValueError('tooling SHA')
        r['host']={'platform':platform.platform(),'python':sys.version.split()[0]}
        r['before']=c.snapshot(root)
        r['tool_hashes']={p.name:c.sha(p) for p in [Path(__file__),Path(q.__file__),Path(s.__file__),Path(c.__file__),Path(f.__file__)]}
        if c.checked(call(['git','rev-parse','HEAD']))!=c.SOURCE:raise ValueError('source SHA')
        docker=shutil.which('docker')
        if not docker:raise ValueError('Docker missing')
        r['docker_server_version']=c.checked(call([docker,'version','--format','{{json .Server.Version}}']))
        f.local_docker_endpoint(docker,root,r)
        capacity=f.capacity_decision(Path('/proc/meminfo').read_text(),shutil.disk_usage('/').free,
            json.loads(c.checked(call([docker,'info','--format','{{json .MemTotal}}']))),c.checked(call([docker,'ps','-q'])))
        r['resource_check']=capacity
        if not capacity['passed']:raise ValueError('resource gate')
        # Offline by design: the pinned digest must already be present; no pull.
        r['image_identity']=image_identity(c.checked(call([docker,'image','inspect',c.IMAGE])))
        s.remaining(RESERVE+30)
        state=state_dir(args.state);r['state']=str(state);bundle=state/'analysis';bundle.mkdir()
        shutil.copyfile(q.__file__,bundle/'osc_synthetic_zone.py')
        if c.sha(bundle/'osc_synthetic_zone.py')!=r['tool_hashes']['osc_synthetic_zone.py']:raise ValueError('bundle hash')
        shim=state/'docker';shim.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -B '+shlex.quote(str(Path(__file__).resolve()))+' --adapter "$@"\n');shim.chmod(0o700)
        env={'PATH':str(state)+os.pathsep+os.environ['PATH'],'OSC_STATE':str(state),'OSC_REAL_DOCKER':docker,'OSC_INPUT_ROOT':str(root),
             'OSC_PAYLOAD':str(bundle),'OSC_SYNTHETIC_DEADLINE':str(c.DEADLINE),'OSC_LOCAL_ADAPTER':'1'}
        result=call(['bash','scripts/kicad/run.sh','python3','-B','/analysis/osc_synthetic_zone.py'],s.remaining()-RESERVE-7,env)
        # Preserve the first partial/failure result before checking command exit.
        detail=s.parse_output(result['output']);(out/'synthetic.json').write_text(json.dumps(detail,indent=2)+'\n')
        c.checked(result)
        if detail['status']!=STATUS:raise ValueError('synthetic qualification failed')
        r['status']=STATUS
    except Exception as exc:
        failed=True;r.update(status='FAILED',error=type(exc).__name__+': '+str(exc)[:700])
    finally:
        c.RESERVE_SECONDS=7
        if state is not None:
            try:
                c.cleanup_owned(state,docker,root,c.run_command,outcomes=r['cleanup'])
                for p in sorted(state.glob('cleanup-*.json')):r['cleanup'].extend(json.loads(p.read_text()))
                r['precreate_capacity']=[json.loads(p.read_text()) for p in sorted(state.glob('capacity-*.json'))]
                if len(r['cleanup'])!=2 or any(x['status']!='REMOVED_CONFIRMED' for x in r['cleanup']):raise ValueError('two owned exits not confirmed')
            except Exception as exc:failed=True;r.update(status='FAILED',cleanup_error=str(exc)[:500])
        try:r['after']=c.snapshot(root)
        except Exception as exc:failed=True;r.update(status='FAILED',after_error=str(exc)[:500])
        r['elapsed_seconds']=time.monotonic()-started
        if r['elapsed_seconds']>TOTAL:failed=True;r.update(status='FAILED',deadline_exceeded=True)
        save()
        print(json.dumps({k:r[k] for k in ('status','error','cleanup_error','elapsed_seconds','cleanup','before','after','resource_check','image_identity') if k in r}),flush=True)
        if (out/'synthetic.json').is_file():print((out/'synthetic.json').read_text(),flush=True)
    return int(failed)

def cleanup(args):
    """Post-stop pass: remove any owned container the killed controller left; fail closed on uncertainty."""
    state=Path(args.state).resolve();out=Path(args.out).resolve()
    record={'mode':'POST_STOP_CLEANUP','state':str(state),'status':'FAILED','outcomes':[]}
    try:
        if not state.is_dir():raise ValueError('state directory missing')
        docker=shutil.which('docker')
        if not docker:raise ValueError('Docker missing')
        c.DEADLINE=time.monotonic()+CLEANUP_SECONDS;c.RESERVE_SECONDS=2
        # Late-bound call so tests can intercept it; cleanup_owned binds run_command at definition time.
        c.cleanup_owned(state,docker,state,c.run_command,outcomes=record['outcomes'])
        record['status']='COMPLETE'
    except Exception as exc:
        record['error']=type(exc).__name__+': '+str(exc)[:500]
    finally:
        record['remaining_records']=sorted(p.name for p in state.glob('owned-*.json')) if state.is_dir() else None
        try:
            out.mkdir(exist_ok=True)
            (out/'post-stop-cleanup.json').write_text(json.dumps(record,indent=2)+'\n')
        except Exception as exc:
            record['receipt_error']=str(exc)[:200]
        print(json.dumps(record),flush=True)
    return int(record['status']!='COMPLETE')

def parse(argv):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('run');a.add_argument('source');a.add_argument('out')
    a.add_argument('--state',required=True);a.add_argument('--authorization',required=True)
    b=sub.add_parser('cleanup');b.add_argument('state');b.add_argument('out')
    return p.parse_args(argv)

def main(argv):
    if argv[:1]==['--adapter']:return adapter(argv[1:])
    args=parse(argv)
    return run(args) if args.command=='run' else cleanup(args)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
