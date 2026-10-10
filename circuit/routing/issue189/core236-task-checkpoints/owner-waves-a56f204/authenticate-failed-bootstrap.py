import json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p
repo=Path.cwd();config=repo/'circuit/routing/issue189/core236-task-checkpoints';m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(repo);artifact=json.loads(Path('/tmp/issue189-owner-geometry-artifact.json').read_bytes());archive=Path('/tmp/issue189-owner-geometry.zip')
with zipfile.ZipFile(archive) as z:producer=json.loads(z.read('producer.json'))
pin=dict(producer_commit='a56f2041484231066b2248ff873d3863ccb0802a',run=38095685843,artifact_id=artifact['id'],artifact_sha256=artifact['digest'].split(':')[1],manifest_sha256=a.identity(m),policy=kernel,orchestration=p.revision(repo,'a56f2041484231066b2248ff873d3863ccb0802a'),ledgers=producer['ledgers']);approval=Path('/tmp/issue189-owner-geometry-failure-approval.json');a.atomic(approval,pin);sha=a.SHA(approval.read_bytes());destination=Path('/tmp/issue189-owner-geometry-failure-authenticated')
try:p.authenticate_geometry(archive,approval,sha,m,kernel,repo,destination,json.loads((config/'native-geometry-bindings.json').read_bytes()))
except ValueError as error:
 assert str(error)=='bootstrap failure/guard/cleanup/task scope';rejection=str(error)
else:raise AssertionError('failed bootstrap must never bind geometry')
assert producer['ledgers']=={} and producer['requested_task_ids']==[] and len(producer['prior_task_ids'])==323
assert not producer['cleanup_errors'] and not producer['owned_containers_remaining'] and not producer['process_tree_after_cleanup']
assert not list(destination.rglob('geometry-receipt.json')) and not list(destination.rglob('drc.json')) and not list(destination.rglob('complete.json'))
telemetry=[json.loads(x) for x in (destination/'telemetry.jsonl').read_text().splitlines()]
proof=dict(status='AUTHENTICATED_PARTIAL_FAILURE; GEOMETRY_BINDING_REJECTED',artifact=artifact,producer=producer,approval_sha256=sha,rejection=rejection,blocker="KiCad10 ZONE has GetIsRuleArea; bootstrap calls nonexistent IsRuleArea",completed_drc_tasks=0,coverage_unchanged=323,after_signature=None,independent_reload_receipt=False,known_bindings_unchanged=3,peak_aggregate_rss_kib=max(t['total_rss_kib'] for t in telemetry),minimum_available_kib=min(t['available_kib'] for t in telemetry),cleanup_clean=True,automatic_retry=False,after_tasks_admitted=False,adopted=False)
a.atomic('/tmp/issue189-owner-geometry-failure-proof.json',proof);print(json.dumps({k:v for k,v in proof.items() if k not in ('artifact','producer')},indent=2))
