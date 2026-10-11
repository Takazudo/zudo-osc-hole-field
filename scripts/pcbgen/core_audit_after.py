"""Exact after-stage scheduling and full bootstrap-backed geometry authority."""
import copy,json
from pathlib import Path
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_geometry as g,core_audit_waves as w
BOOTSTRAP=('d75c4a949e37ac545c7e5cebbd95c516faff8352',38098640864,11686834647,'776d50d05aecd67a60cff1bd285c9a3aedf80c54517fdbde0545686d8716aba5','33dcc38ca02a185f9b96d980f8f92d7608cf6c8296710b5ed3afd7b88e684d00')
BOOTSTRAP_ORCHESTRATION='abd9d8b7335ba9c2cb40873570ce7e7f53af601c3866213d46ce720ec1f21926'
PLAN_SHA='02c2bdd83b35da54f23093956ccf9658001ce4d2ecae132585838bad871db9ce'
_SEAL=object()
def is_after(t):return (t['zone_uuid'],t['layer'],t['stage'])==g.TARGET
class StageBindings(dict):
 def __init__(self,seal,original,fact):
  if seal is not _SEAL:raise ValueError('authenticated bootstrap capability required')
  self._seal=seal;self._original=copy.deepcopy(original);self._fact=copy.deepcopy(fact)
  if len(original)!=3 or fact['reference_sha256'] in original:raise ValueError('original three controls required')
  super().__init__(original|{fact['reference_sha256']:fact['signature']})
 @property
 def fact(self):return copy.deepcopy(self._fact)
 def evidence(self,m,kernel):
  f=self._fact
  if self._seal is not _SEAL or dict(self)!=self._original|{f['reference_sha256']:f['signature']} or f['manifest_sha256']!=a.identity(m) or f['validator_revision']!=kernel['validator_revision'] or f['image']!=a.IMAGE or f['source_sha256']!=m['source_sha256'] or f['context_sha256']!=m['context_sha256']:raise ValueError('stale or altered bootstrap binding')
  return a.identity(f)
def require_binding(m,t,kernel,bindings):
 if not is_after(t):return None
 if not isinstance(bindings,StageBindings):raise ValueError('after-stage requires authenticated bootstrap capability, not JSON signatures')
 token=bindings.evidence(m,kernel)
 if t['expected_geometry']!=bindings.fact['reference']:raise ValueError('after-stage geometry substituted')
 return token
def validate_pin(pin,approval_sha,repo):
 from scripts.pcbgen import core_audit_pilot as p
 key=(pin['producer_commit'],pin['run'],pin['artifact_id'],pin['artifact_sha256'],approval_sha)
 if key!=BOOTSTRAP or pin['ledgers']!={} or not p.historical_orchestration(pin,repo,BOOTSTRAP_ORCHESTRATION):raise ValueError('wrong or unreviewed bootstrap source/artifact/history')
def authenticate_binding(archive,approval,m,kernel,repo,destination,original,offline=False):
 from scripts.pcbgen import core_audit_pilot as p
 approval=Path(approval);sha=a.SHA(approval.read_bytes());pin=json.loads(approval.read_bytes());validate_pin(pin,sha,repo)
 fact=p.authenticate_geometry(archive,approval,sha,m,kernel,repo,destination,original,_offline_bootstrap=offline)
 if fact['producer']['producer_commit']!=BOOTSTRAP[0] or fact['producer']['run']!=BOOTSTRAP[1] or fact['completed_drc_tasks']!=0:raise ValueError('bootstrap producer/stage changed')
 return StageBindings(_SEAL,original,fact)
def validate_plan(m,plan,bindings,kernel):
 # Byte identity is separately checked by load_plan; semantic validation does
 # not allow a self-consistent substitute manifest or stage.
 if not isinstance(bindings,StageBindings) or plan['native_geometry_fact']!=bindings.fact:raise ValueError('proposed bootstrap fact altered')
 bindings.evidence(m,kernel)
 tasks={t['task_id']:t for t in m['tasks']}
 if len(tasks)!=426 or len(m['tasks'])!=426:raise ValueError('exact unique426 manifest required')
 rows=sorted((t for t in m['tasks'] if is_after(t)),key=lambda t:t['batch_index'])
 if len(rows)!=103 or [t['batch_index'] for t in rows]!=list(range(103)):raise ValueError('exact after0–102 scope required')
 ids=[t['task_id'] for t in rows];base=plan['baseline_task_ids'];missing=plan['missing_task_ids']
 if len(base)!=323 or len(set(base))!=323 or set(base)!=set(tasks)-set(ids) or len(missing)!=103 or len(set(missing))!=103 or set(missing)!=set(ids):raise ValueError('missing/duplicate/substituted baseline or after IDs')
 for t in rows:require_binding(m,t,kernel,bindings)
 packets=[dict(packet_index=i//8,batch_indices=[t['batch_index'] for t in rows[i:i+8]],task_ids=[t['task_id'] for t in rows[i:i+8]]) for i in range(0,103,8)]
 waves=[];coverage=323
 for i in range(0,13,2):
  ps=packets[i:i+2];new=[x for packet in ps for x in packet['task_ids']];waves.append(dict(wave=i//2,packet_indices=[packet['packet_index'] for packet in ps],task_ids=new,prior_count=coverage,new_count=len(new),expected_coverage=coverage+len(new)));coverage+=len(new)
 if plan['packets']!=packets or plan['waves']!=waves or plan['bounds']!=dict(global_native_workers=2,shared_command_seconds=2400,job_minutes=50,worker_memory_gib=6,aggregate_rss_kib=12582912,minimum_available_kib=2097152) or plan['manifest_sha256']!=a.identity(m):raise ValueError('proposed packets/waves/bounds/manifest altered')
 return plan
def load_plan(config,m,bindings,kernel):
 path=Path(config)/'after103-proposed-wave-plan.json'
 if a.SHA(path.read_bytes())!=PLAN_SHA:raise ValueError('reviewed103-plan file changed')
 return validate_plan(m,json.loads(path.read_bytes()),bindings,kernel)
def select_wave(m,leaves,plan,index,bindings,kernel):
 validate_plan(m,plan,bindings,kernel)
 if type(index) is not int or not 0<=index<7:raise ValueError('after wave must0–6')
 prior=set(plan['baseline_task_ids'])|{k for wave in plan['waves'][:index] for k in wave['task_ids']}
 if set(leaves)!=prior:raise ValueError('exact prior after coverage required; no replay or partial advance')
 packets=[plan['packets'][i]['task_ids'] for i in plan['waves'][index]['packet_indices']];a.selection(m,leaves,packets)
 return packets
def reconcile_wave(m,plan,index,prior,new,producer,before,after,kernel,bindings):
 packets=select_wave(m,prior,plan,index,bindings,kernel);expected={k for packet in packets for k in packet}
 if set(new)!=expected or set(prior)&set(new):raise ValueError('missing/duplicate/replayed after task IDs')
 if producer.get('mode')!='after-wave' or producer.get('wave')!=index or producer.get('prior_task_ids')!=sorted(prior) or producer.get('requested_task_ids')!=sorted(expected) or producer.get('stage_geometry_sha256')!=bindings.evidence(m,kernel) or producer.get('stage_geometry_fact')!=bindings.fact:raise ValueError('after producer wave/stage/binding changed')
 if producer.get('status')!='PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN' or producer.get('cleanup_errors') or producer.get('owned_containers_remaining') or producer.get('process_tree_after_cleanup'):raise ValueError('partial/native/guard/cleanup failure; stop after wave')
 tasks={t['task_id']:t for t in m['tasks']};paths,raw,texts,ctx=a.sources(before,after);cache=(texts,ctx,[a.artwork_ids(s) for s in texts],{})
 for key,b in new.items():
  t=tasks[key];token=require_binding(m,t,kernel,bindings);a.verify_leaf(m,t,b,before,after,kernel,bindings[a.identity(t['expected_geometry'])],b['provenance'],cache,stage_geometry=token)
  if any(v['severity']=='error' for v in json.loads(b['report'])['violations']):raise ValueError('native error; stop after wave')
 return dict(prior)|dict(new)
def load_previous(m,kernel,source_root,config,repo,before_resume,after_resume,bindings,leaves):
 from scripts.pcbgen import core_audit_pilot as p
 if len(before_resume)!=5:raise ValueError('all five before approvals required separately')
 plan=load_plan(config,m,bindings,kernel)
 for i,ref in enumerate(after_resume):
  approval=source_root/('after-approval-'+str(i)+'.json');a.atomic(approval,ref['approval']);dest=source_root/('after-verified-'+str(i))
  new=p.authenticate_checkpoints(source_root/('after-checkpoint-'+str(i)+'.zip'),approval,ref['approval_sha256'],m,kernel,repo,dest)
  producer=json.loads((dest/'producer.json').read_bytes());leaves=reconcile_wave(m,plan,i,leaves,new,producer,source_root/'before/osc-core.kicad_pcb',source_root/'after/osc-core.kicad_pcb',kernel,bindings)
 return leaves,plan
def verify_worker_packet(m,kernel,bindings,task_ids):
 tasks={t['task_id']:t for t in m['tasks']}
 if not task_ids or len(task_ids)>8 or len(task_ids)!=len(set(task_ids)) or not set(task_ids)<=set(tasks):raise ValueError('wrong/duplicate after worker packet')
 expected=[t for t in sorted(m['tasks'],key=lambda t:t['batch_index']) if is_after(t)]
 packets=[[t['task_id'] for t in expected[i:i+8]] for i in range(0,len(expected),8)]
 if task_ids not in packets:raise ValueError('worker packet differs from exact reviewed after batches')
 for key in task_ids:
  if not is_after(tasks[key]):raise ValueError('worker stage substitution')
  require_binding(m,tasks[key],kernel,bindings)
