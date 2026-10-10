"""Reviewed five-wave controller; authenticates each terminal artifact first.

Never dispatches bootstrap/after tasks. An ambiguous admission, partial wave or
failed proof leaves an atomic checkpoint and stops; it never retries a packet.
"""
import argparse,datetime,hashlib,json,subprocess,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
from scripts.pcbgen.core_audit_waves import validate_plan,reconcile_wave
REPO='Takazudo/zudo-osc-hole-field'
def api(path):return a.github_json(path)
def download(pin,path):
 a.authenticate_artifact(pin['artifact_id'],pin['run'],pin['producer_commit'],pin['artifact_sha256'])
 with Path(path).open('wb') as out:subprocess.run(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(pin['artifact_id'])+'/zip'],stdout=out,check=True)
 with Path(path).open('rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!=pin['artifact_sha256']:raise ValueError('downloaded native archive digest mismatch')
def sequence(repo,source,config,output,reviewed_commit,reviewed_plan_sha,ci_run):
 repo=Path(repo);source=Path(source);config=Path(config);output=Path(output)
 if output.exists():raise ValueError('sequence output must be disjoint/new; inspect prior checkpoint, never repeat')
 output.mkdir(parents=True);state=dict(status='PREPARING; NO_DISPATCH',source=reviewed_commit,plan_sha256=reviewed_plan_sha,waves=[],adopted=False,resume_approvals=[])
 try:
  plan_path=config/'before-wave-plan.json'
  if a.SHA(plan_path.read_bytes())!=reviewed_plan_sha:raise ValueError('reviewed wave plan digest mismatch')
  if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=reviewed_commit or subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=repo,text=True).strip():raise ValueError('reviewed clean sequence source required')
  ci=api('actions/runs/'+str(ci_run));jobs=api('actions/runs/'+str(ci_run)+'/jobs?per_page=100')['jobs']
  if ci['head_sha']!=reviewed_commit or ci['status']!='completed' or ci['conclusion']!='success' or len(jobs)!=5 or any(j['conclusion']!='success' for j in jobs):raise ValueError('exact-head CI not successful')
  m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(repo);plan=validate_plan(m,json.loads(plan_path.read_bytes()));leaves,bindings=p.load_approved(m,kernel,source,config,repo,[])
  for index in range(5):
   from scripts.pcbgen.core_audit_waves import select_wave
   select_wave(m,leaves,plan,index,bindings)
   branch=subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()
   if api('git/ref/heads/'+branch)['object']['sha']!=reviewed_commit:raise ValueError('remote reviewed head changed')
   prior=api('actions/workflows/378789207/runs?branch='+branch+'&event=workflow_dispatch&per_page=100')['workflow_runs'];known={r['id'] for r in prior}
   admitted={r['run'] for r in state['waves']}
   if any(r['head_sha']==reviewed_commit and r['id'] not in admitted for r in prior):raise ValueError('existing exact-source admission; inspect/review, never repeat')
   # Exclusive marker is written BEFORE the one admission request. Lost/failed
   # responses are ambiguous and require human review, not a second request.
   marker=output/('wave-'+str(index)+'-admission.json')
   inputs=dict(board='osc-core',core_audit_task_pilot=True,core_audit_task_mode='before-wave',core_audit_wave=str(index),core_audit_resume=json.dumps(state['resume_approvals'],separators=(',',':')),reviewed_commit=reviewed_commit,reviewed_manifest_sha256=a.SHA((config/'manifest.json').read_bytes()),adopt_run='',recover_core=False,replay_jl=False,replay_jr=False,local_repair=False)
   with marker.open('x') as f:json.dump(dict(ref=branch,inputs=inputs),f)
   subprocess.run(['gh','api','--method','POST','repos/'+REPO+'/actions/workflows/378789207/dispatches','--input',str(marker)],check=True)
   state['status']='ADMITTED_WAVE_'+str(index);a.atomic(output/'sequence.json',state)
   candidates=[]
   for attempt in range(20):
    runs=api('actions/workflows/378789207/runs?branch='+branch+'&event=workflow_dispatch&per_page=100')['workflow_runs'];candidates=[r for r in runs if r['id'] not in known and r['head_sha']==reviewed_commit]
    if candidates:break
    time.sleep(3)
   if len(candidates)!=1:raise ValueError('ambiguous admitted run; stop without retry')
   run=candidates[0]['id'];state['waves'].append(dict(index=index,run=run,status='ACTIVE'));a.atomic(output/'sequence.json',state);print('ADMITTED wave='+str(index)+' run='+str(run),flush=True)
   # One50-minute job; do not extend or retry it. Authenticated partial outputs
   # are retained locally even when the wave gate rejects continuation.
   deadline=time.monotonic()+3300
   while True:
    execution=api('actions/runs/'+str(run))
    if execution['status']=='completed':break
    if time.monotonic()>=deadline:raise ValueError('terminal job not observed; stop without further admission')
    time.sleep(30)
   artifacts=api('actions/runs/'+str(run)+'/artifacts')['artifacts']
   artifacts=[x for x in artifacts if x['name']=='core-audit-task-pilot-'+str(run)]
   if len(artifacts)!=1:raise ValueError('missing/ambiguous wave artifact')
   artifact=artifacts[0];pinbase=dict(artifact_id=artifact['id'],artifact_sha256=artifact['digest'].split(':')[1],run=run,producer_commit=reviewed_commit)
   archive=output/('wave-'+str(index)+'.zip');download(pinbase,archive)
   with zipfile.ZipFile(archive) as z:producer=json.loads(z.read('producer.json'))
   pin=dict(pinbase,manifest_sha256=a.identity(m),policy=kernel,orchestration=p.revision(repo,reviewed_commit),ledgers=producer['ledgers']);approval=output/('wave-'+str(index)+'-approval.json');a.atomic(approval,pin);approval_sha=a.SHA(approval.read_bytes())
   new=p.authenticate_checkpoints(archive,approval,approval_sha,m,kernel,repo,output/('wave-'+str(index)+'-raw'))
   state['waves'][-1].update(artifact=artifact,approval_sha256=approval_sha,retained_receipt_task_ids=sorted(new),terminal_conclusion=execution['conclusion']);a.atomic(output/'sequence.json',state)
   leaves=reconcile_wave(m,plan,index,leaves,new,producer,source/'before/osc-core.kicad_pcb',source/'after/osc-core.kicad_pcb',kernel,bindings)
   if execution['conclusion']!='success':raise ValueError('native job failed despite partial receipts')
   state['resume_approvals'].append(dict(approval=pin,approval_sha256=approval_sha));state['waves'][-1]['status']='AUTHENTICATED_AND_RECONCILED';state['completed_task_ids']=sorted(leaves);a.atomic(output/'sequence.json',state)
  if len(leaves)!=323:raise ValueError('before-stage total differs from323')
  state['status']='BEFORE_STAGE323_OF426; STOP_FOR_AFTER_STAGE_REVIEW'
 except BaseException as error:
  state.update(status='STOPPED_NO_AUTOMATIC_RETRY',error_type=type(error).__name__,error=str(error));raise
 finally:a.atomic(output/'sequence.json',state)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--config',required=True);parser.add_argument('--output',required=True);parser.add_argument('--reviewed-commit',required=True);parser.add_argument('--reviewed-plan-sha',required=True);parser.add_argument('--ci-run',type=int,required=True);args=parser.parse_args();sequence(Path.cwd(),args.source,args.config,args.output,args.reviewed_commit,args.reviewed_plan_sha,args.ci_run)
