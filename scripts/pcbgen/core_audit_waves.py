"""Frozen before-stage scheduling and authenticated wave gates. No routing."""
import json
from pathlib import Path
from scripts.pcbgen import audit_fixture_tasks as a
BCU='e389d344-872d-538e-9bfc-39577adb1686'
BOUNDS=dict(max_workers=2,command_seconds=2400,job_minutes=50,maximum_aggregate_rss_kib=12582912,minimum_available_kib=2097152)
def build_plan(m,baseline):
 if len(m['tasks'])!=426 or len(baseline)!=251:raise ValueError('frozen426/251baseline required')
 tasks={t['task_id']:t for t in m['tasks']}
 if not set(baseline)<=set(tasks):raise ValueError('unknown baseline task')
 expected=[t for t in m['tasks'] if t['zone_uuid']==BCU and t['layer']=='B.Cu' and t['stage']==0 and 31<=t['batch_index']<=102]
 if [t['batch_index'] for t in expected]!=list(range(31,103)) or set(baseline)&{t['task_id'] for t in expected}:raise ValueError('before31–102 scope changed')
 # Baseline is exactly Fboth220+Bbefore31, not merely a count.
 if any(t['task_id'] not in baseline for t in m['tasks'] if t['layer']=='F.Cu' or (t['zone_uuid']==BCU and t['stage']==0 and t['batch_index']<31)):raise ValueError('baseline coverage changed')
 packets=[[t['task_id'] for t in expected[i:i+8]] for i in range(0,72,8)]
 return dict(schema=1,manifest_sha256=a.identity(m),baseline_ids=sorted(baseline),packets=packets,waves=[packets[i:i+2] for i in range(0,9,2)],expected_final_count=323,**BOUNDS)
def validate_plan(m,plan):
 if plan!=build_plan(m,plan['baseline_ids']):raise ValueError('frozen wave plan altered')
 return plan
def select_wave(m,leaves,plan,index,bindings):
 validate_plan(m,plan)
 if type(index) is not int or not 0<=index<5:raise ValueError('wave index must0–4')
 prior=set(plan['baseline_ids'])|{k for wave in plan['waves'][:index] for packet in wave for k in packet}
 if set(leaves)!=prior:raise ValueError('previous waves not fully authenticated/reconciled; replay or partial scope')
 packets=plan['waves'][index];a.selection(m,leaves,packets);tasks={t['task_id']:t for t in m['tasks']}
 if any(a.identity(tasks[k]['expected_geometry']) not in bindings for packet in packets for k in packet):raise ValueError('missing native geometry binding')
 return packets
def reconcile_wave(m,plan,index,prior,new,producer,before,after,kernel,bindings):
 packets=select_wave(m,prior,plan,index,bindings);expected={k for packet in packets for k in packet}
 if set(new)-expected or set(prior)&set(new):raise ValueError('unexpected or replayed wave task')
 tasks={t['task_id']:t for t in m['tasks']};paths,raw,texts,ctx=a.sources(before,after);cache=(texts,ctx,[a.artwork_ids(s) for s in texts],{})
 for key,b in new.items():
  t=tasks[key];a.verify_leaf(m,t,b,before,after,kernel,bindings[a.identity(t['expected_geometry'])],b['provenance'],cache)
  if any(v['severity']=='error' for v in json.loads(b['report'])['violations']):raise ValueError('native failure; stop sequence')
 # verify_leaf's original new_silk_identities rejects capped target warnings.
 if set(new)!=expected or producer.get('status')!='PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN' or producer.get('cleanup_errors') or producer.get('owned_containers_remaining') or producer.get('process_tree_after_cleanup'):raise ValueError('partial/guard/worker/cleanup failure; stop sequence')
 if producer.get('mode')!='before-wave' or producer.get('wave')!=index or producer.get('requested_task_ids')!=sorted(expected):raise ValueError('producer wave/packet provenance changed')
 return dict(prior)|dict(new)
