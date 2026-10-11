# Local read-only owner reconciliation. Never dispatches/native-executes.
import collections,json,sys,os,zipfile,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
from scripts.pcbgen.core_audit_waves import select_wave,reconcile_wave
index=int(sys.argv[1]);refs=json.loads(Path(sys.argv[2]).read_bytes());root=Path(sys.argv[3]);root.mkdir();repo=Path.cwd();config=repo/'circuit/routing/issue189/core236-task-checkpoints';base=Path('/tmp/issue189-f67bef8-wave-input-cached')
for name in ['compact.zip','metadata.json','checkpoint-0.zip']:os.link(base/name,root/name)
for stage in ['before','after']:
 (root/stage).mkdir()
 for f in (base/stage).iterdir():os.link(f,root/stage/f.name)
for i,ref in enumerate(refs):os.link(ref['local_archive'],root/('checkpoint-'+str(i+1)+'.zip'))
resume=[{k:v for k,v in r.items() if k!='local_archive'} for r in refs];m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(repo);prior,bindings=p.load_approved(m,kernel,root,config,repo,resume)
if len(sys.argv)==4:
 select_wave(m,prior,json.loads((config/'before-wave-plan.json').read_bytes()),index,bindings)
 a.atomic(root/'preflight.json',dict(status='AUTHENTICATED_PRIOR; NO_DISPATCH',completed_count=len(prior),completed_task_ids=sorted(prior),wave=index));print('PASS prior='+str(len(prior))+' wave='+str(index));[shutil.rmtree(root/('verified-'+str(i))) for i in range(len(refs)+1)];sys.exit()
artifact=json.loads(Path(sys.argv[4]).read_bytes());archive=Path(sys.argv[5]);output=Path(sys.argv[6]);execution=a.github_json('actions/runs/'+str(artifact['workflow_run']['id']))
if execution['status']!='completed' or execution['conclusion']!='success':raise ValueError('terminal workflow failure; retain outputs; no admission')
with zipfile.ZipFile(archive) as z:producer=json.loads(z.read('producer.json'))
pin=dict(producer_commit=execution['head_sha'],run=execution['id'],artifact_id=artifact['id'],artifact_sha256=artifact['digest'].split(':')[1],manifest_sha256=a.identity(m),policy=kernel,orchestration=p.revision(repo,execution['head_sha']),ledgers=producer['ledgers']);approval=output.with_suffix('.approval.json');a.atomic(approval,pin);sha=a.SHA(approval.read_bytes());new=p.authenticate_checkpoints(archive,approval,sha,m,kernel,repo,root/'new-native')
if index<5:
 leaves=reconcile_wave(m,json.loads((config/'before-wave-plan.json').read_bytes()),index,prior,new,producer,root/'before/osc-core.kicad_pcb',root/'after/osc-core.kicad_pcb',kernel,bindings)
else:raise ValueError('geometry uses separate authenticate_geometry entry point')
tasks={t['task_id']:t for t in m['tasks']};warnings=collections.Counter();errors=0;versions=set()
for b in new.values():
 report=json.loads(b['report']);versions.add(report['kicad_version']);errors+=sum(v['severity']=='error' for v in report['violations']);warnings.update(v['type'] for v in report['violations'] if v['severity']=='warning')
telemetry=[json.loads(x) for x in (root/'new-native/telemetry.jsonl').read_text().splitlines()]
try:a.final_union(m,root/'before/osc-core.kicad_pcb',root/'after/osc-core.kicad_pcb',list(leaves.values()),kernel,bindings)
except ValueError as error:assert 'incomplete final task coverage' in str(error)
else:raise AssertionError('incomplete before union accepted')
proof=dict(status='AUTHENTICATED_PARTIAL; NOT_ELIGIBILITY',wave=index,artifact=artifact,approval_sha256=sha,producer=producer,new_task_ids=sorted(new),new_receipts={k:b['receipt'] for k,b in new.items()},completed_task_ids=sorted(leaves),missing_task_ids=sorted(set(tasks)-set(leaves)),completed_count=len(leaves),new_count=len(new),raw_native_errors=errors,native_versions=sorted(versions),raw_warning_counts=dict(warnings),peak_aggregate_rss_kib=max(t['total_rss_kib'] for t in telemetry),minimum_available_kib=min(t['available_kib'] for t in telemetry),full_coverage_gate='REJECTED_INCOMPLETE',other_final_gates='NOT_RUN',adopted=False)
a.atomic(output,proof);refs.append(dict(approval=pin,approval_sha256=sha,local_archive=str(archive)));a.atomic(output.with_suffix('.resume.json'),refs)
print(json.dumps({k:v for k,v in proof.items() if k not in ('artifact','producer','new_task_ids','new_receipts','completed_task_ids','missing_task_ids')},indent=2))

# Prior immutable archives and original native outputs remain; these are redundant extraction copies only.
for i in range(len(resume)+1):shutil.rmtree(root/('verified-'+str(i)))
