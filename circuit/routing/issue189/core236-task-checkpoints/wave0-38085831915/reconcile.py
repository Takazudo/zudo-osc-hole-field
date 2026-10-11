import collections,hashlib,json,sys,zipfile,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
from scripts.pcbgen.core_audit_waves import reconcile_wave
repo=Path.cwd();config=repo/'circuit/routing/issue189/core236-task-checkpoints';source=Path(sys.argv[1]);base=Path(sys.argv[6]);source.mkdir()
for name in ['compact.zip','metadata.json','checkpoint-0.zip']:os.link(base/name,source/name)
for stage in ['before','after']:
 (source/stage).mkdir()
 for path in (base/stage).iterdir():os.link(path,source/stage/path.name)
m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(repo);prior,bindings=p.load_approved(m,kernel,source,config,repo,[])
artifact=json.loads(Path(sys.argv[2]).read_bytes());archive=Path(sys.argv[3]);destination=Path(sys.argv[4])
with zipfile.ZipFile(archive) as z:producer=json.loads(z.read('producer.json'))
pin=dict(producer_commit='f67bef8211b40e43e93a8e16004ac1d77079f12f',run=38085831915,artifact_id=artifact['id'],artifact_sha256=artifact['digest'].split(':')[1],manifest_sha256=a.identity(m),policy=kernel,orchestration=p.revision(repo,'f67bef8211b40e43e93a8e16004ac1d77079f12f'),ledgers=producer['ledgers'])
approval=Path(sys.argv[5]).with_suffix('.approval.json');a.atomic(approval,pin);sha=a.SHA(approval.read_bytes());new=p.authenticate_checkpoints(archive,approval,sha,m,kernel,repo,destination)
leaves=reconcile_wave(m,json.loads((config/'before-wave-plan.json').read_bytes()),0,prior,new,producer,source/'before/osc-core.kicad_pcb',source/'after/osc-core.kicad_pcb',kernel,bindings)
tasks={t['task_id']:t for t in m['tasks']};warnings=collections.Counter();errors=0;versions=set()
for b in new.values():
 report=json.loads(b['report']);versions.add(report['kicad_version']);errors+=sum(v['severity']=='error' for v in report['violations']);warnings.update(v['type'] for v in report['violations'] if v['severity']=='warning')
telemetry=[json.loads(x) for x in (destination/'telemetry.jsonl').read_text().splitlines()]
try:a.final_union(m,source/'before/osc-core.kicad_pcb',source/'after/osc-core.kicad_pcb',list(leaves.values()),kernel,bindings)
except ValueError as error:assert 'incomplete final task coverage' in str(error)
else:raise AssertionError('incomplete267 accepted')
proof=dict(status='AUTHENTICATED267_OF426; SEQUENCE STOPPED; NOT ELIGIBILITY',artifact=artifact,approval_sha256=sha,producer=producer,new_task_ids=sorted(new),new_receipts={k:b['receipt'] for k,b in new.items()},completed_task_ids=sorted(leaves),missing_task_ids=sorted(set(tasks)-set(leaves)),completed_count=len(leaves),new_count=len(new),coverage=dict(collections.Counter(str((tasks[k]['layer'],tasks[k]['stage'])) for k in leaves)),raw_native_errors=errors,native_versions=sorted(versions),raw_warning_counts=dict(warnings),peak_aggregate_rss_kib=max(t['total_rss_kib'] for t in telemetry),minimum_available_kib=min(t['available_kib'] for t in telemetry),full_coverage_gate='REJECTED INCOMPLETE AS REQUIRED',other_final_gates='NOT RUN; STILL REQUIRED',dispatch_resume='REQUIRES PARENT REVIEW; NO AUTOMATIC RETRY',after_geometry_bootstrap='NOT RUN',adopted=False)
a.atomic(sys.argv[5],proof)
print(json.dumps({k:v for k,v in proof.items() if k not in ('artifact','producer','new_task_ids','new_receipts','completed_task_ids','missing_task_ids')},indent=2))
