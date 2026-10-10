import collections,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
archive=Path(sys.argv[1]);artifact=json.loads(Path(sys.argv[2]).read_bytes());output=Path(sys.argv[3]);repo=Path.cwd();data=repo/'circuit/routing/issue189/core236-task-checkpoints'
m=json.loads((data/'manifest.json').read_bytes());kernel=a.policy(repo);before=Path('/tmp/issue189-task-source/before/osc-core.kicad_pcb');after=Path('/tmp/issue189-task-source/after/osc-core.kicad_pcb');tasks=a.validate_manifest(m,before,after,kernel)
assert a.SHA((data/'manifest.json').read_bytes())=='e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e'
assert artifact['workflow_run']['id']==38081076014 and artifact['workflow_run']['head_sha']=='53c3034aea893f4f64848789f3d57302c066919a'
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==artifact['digest'].split(':')[1]
with zipfile.ZipFile(archive) as z:producer=json.loads(z.read('producer.json'))
# Approval is pinned from authenticated GitHub metadata and the externally
# reviewed exact producer code, never from a caller-provided leaf pass flag.
pin=dict(producer_commit='53c3034aea893f4f64848789f3d57302c066919a',run=38081076014,artifact_id=artifact['id'],artifact_sha256=artifact['digest'].split(':')[1],manifest_sha256=a.identity(m),policy=kernel,orchestration=p.revision(repo,'53c3034aea893f4f64848789f3d57302c066919a'),ledgers=producer['ledgers'])
assert pin['orchestration']==json.loads((data/'orchestration-revision.json').read_bytes())
approval=output.with_suffix('.approval.json');a.atomic(approval,pin)
leaves=p.authenticate_checkpoints(archive,approval,a.SHA(approval.read_bytes()),m,kernel,repo,output)
paths,raw,texts,ctx=a.sources(before,after);cache=(texts,ctx,[a.artwork_ids(t) for t in texts],{});bindings=json.loads((data/'native-geometry-bindings.json').read_bytes());prior=json.loads((data/'completed-receipts.json').read_bytes());packets=json.loads((data/'pilot-plan.json').read_bytes())['packets'];requested={k for packet in packets for k in packet}
assert len(prior)==235 and len(requested)==16 and not set(prior)&set(leaves) and set(leaves)<=requested
errors=0;warnings=collections.Counter();new_receipts={};native_versions=set()
for key,b in leaves.items():
 t=tasks[key];a.verify_leaf(m,t,b,before,after,kernel,bindings[a.identity(t['expected_geometry'])],b['provenance'],cache)
 report=json.loads(b['report']);native_versions.add(report['kicad_version']);errors+=sum(v['severity']=='error' for v in report['violations']);warnings.update(v['type'] for v in report['violations'] if v['severity']=='warning');new_receipts[key]=b['receipt']
assert not producer['adopted']
cleanup_clean=not producer['owned_containers_remaining'] and not producer['process_tree_after_cleanup'] and not producer.get('cleanup_errors')
all_ids=set(prior)|set(leaves);missing=sorted(set(tasks)-all_ids);coverage=collections.Counter((tasks[k]['layer'],tasks[k]['stage']) for k in all_ids)
assert len(all_ids)<=251 and len(missing)==426-len(all_ids)
try:a.final_union(m,before,after,[{'task_id':k} for k in prior]+list(leaves.values()),kernel,bindings)
except ValueError as error:assert 'incomplete final task coverage' in str(error)
else:raise AssertionError('partial union incorrectly accepted')
telemetry=[json.loads(x) for x in (output/'telemetry.jsonl').read_text().splitlines()] if (output/'telemetry.jsonl').exists() else []
proof=dict(status='AUTHENTICATED PARTIAL TASK UNION; NOT ELIGIBILITY',run=38081076014,producer_commit=pin['producer_commit'],artifact=artifact,artifact_sha256_locally_verified=True,approval_sha256=a.SHA(approval.read_bytes()),producer=producer,prior_verified_count=235,new_verified_count=len(leaves),completed_count=len(all_ids),required_count=426,missing_count=len(missing),coverage={str(k):v for k,v in coverage.items()},new_task_ids=sorted(leaves),requested_missing_ids=sorted(requested-set(leaves)),all_missing_ids=missing,new_receipts=new_receipts,new_fixture_raw_native_errors=errors,new_fixture_native_versions=sorted(native_versions),raw_warning_counts=dict(warnings),peak_aggregate_rss_kib=max((x['total_rss_kib'] for x in telemetry),default=None),minimum_available_kib=min((x['available_kib'] for x in telemetry),default=None),full_coverage_gate='REJECTED INCOMPLETE AS REQUIRED',complete_reports_groups_connectivity_publication='NOT RUN; STILL REQUIRED',adopted=False,rerouting=False,after_native_geometry_bound=False,automatic_retry=False,cleanup_verified_clean=cleanup_clean)
a.atomic(output.with_suffix('.proof.json'),proof);print(json.dumps({k:v for k,v in proof.items() if k not in ('producer','artifact','new_receipts','all_missing_ids','requested_missing_ids','new_task_ids')},indent=2))
