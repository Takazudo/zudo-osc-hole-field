import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p,core_audit_waves as w
class WaveTests(unittest.TestCase):
 def setUp(self):
  self.m={'tasks':[]}
  for layer,uid,count in [('F.Cu','f',110),('B.Cu',w.BCU,103)]:
   for stage in (0,1):
    for i in range(count):self.m['tasks'].append(dict(task_id=f'{layer}-{stage}-{i}',zone_uuid=uid,layer=layer,stage=stage,batch_index=i,expected_geometry={'geo':layer+str(stage)}))
  self.base={t['task_id']:{} for t in self.m['tasks'] if t['layer']=='F.Cu' or (t['stage']==0 and t['batch_index']<31)};self.plan=w.build_plan(self.m,self.base);self.bindings={a.identity(t['expected_geometry']):'a'*64 for t in self.m['tasks']}
 def test_exact72_disjoint_tasks_five_waves_and323(self):
  leaves=dict(self.base);seen=set()
  for index,expected in enumerate((16,16,16,16,8)):
   packets=w.select_wave(self.m,leaves,self.plan,index,self.bindings);ids={k for packet in packets for k in packet};self.assertEqual(len(ids),expected);self.assertFalse(ids&seen);seen|=ids;leaves.update({k:{} for k in ids})
  self.assertEqual(len(leaves),323);self.assertEqual(len(seen),72)
 def test_no_replay_partial_advance_or_after_scope(self):
  first=self.plan['waves'][0];one=first[0][0]
  for index,leaves in [(1,self.base),(0,self.base|{one:{}})]:
   with self.assertRaises(ValueError):w.select_wave(self.m,leaves,self.plan,index,self.bindings)
  changed=copy.deepcopy(self.plan);changed['waves'][0][0][0]='B.Cu-1-0'
  with self.assertRaises(ValueError):w.select_wave(self.m,self.base,changed,0,self.bindings)
  for key,value in [('max_workers',3),('command_seconds',4800),('job_minutes',100)]:
   with self.assertRaises(ValueError):w.validate_plan(self.m,self.plan|{key:value})
 def test_native_caps_proof_guard_cleanup_and_partial_stop(self):
  ids=[k for packet in self.plan['waves'][0] for k in packet];new={k:dict(receipt={},provenance={},report=a.canonical({'violations':[]})) for k in ids};producer=dict(status='PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN',mode='before-wave',wave=0,requested_task_ids=sorted(ids),cleanup_errors=[],owned_containers_remaining=[],process_tree_after_cleanup={})
  with patch.object(a,'sources',return_value=([],[],['x','x'],{})),patch.object(a,'artwork_ids',return_value=set()),patch.object(a,'verify_leaf'):
   self.assertEqual(len(w.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',{},self.bindings)),267)
   for delta in ({'status':'INCOMPLETE_MEMORY_GUARD'},{'status':'INCOMPLETE_SHARED_40_MINUTE_BUDGET'},{'cleanup_errors':['failed']},{'owned_containers_remaining':['cid']},{'wave':1}):
    with self.assertRaises(ValueError):w.reconcile_wave(self.m,self.plan,0,self.base,new,producer|delta,'b','a',{},self.bindings)
   with self.assertRaises(ValueError):w.reconcile_wave(self.m,self.plan,0,self.base,{ids[0]:new[ids[0]]},producer,'b','a',{},self.bindings)
   new[ids[0]]['report']=a.canonical({'violations':[{'severity':'error'}]})
   with self.assertRaisesRegex(ValueError,'native failure'):w.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',{},self.bindings)
  with patch.object(a,'sources',return_value=([],[],['x','x'],{})),patch.object(a,'artwork_ids',return_value=set()),patch.object(a,'verify_leaf',side_effect=ValueError('silk fixture reached report cap')):
   with self.assertRaisesRegex(ValueError,'cap'):w.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',{},self.bindings)
 def test_exact_old_approval_compatible_but_other_revision_not_relaxed(self):
  root=Path(__file__).resolve().parents[2];file=root/'circuit/routing/issue189/core236-task-checkpoints/pilot-38081076014/authenticated-artifact-approval.json';pin=json.loads(file.read_bytes());self.assertEqual(a.SHA(file.read_bytes()),p.OLD_APPROVAL_SHA);self.assertTrue(p.approved_orchestration(pin,p.OLD_APPROVAL_SHA,root))
  for key,value in [('run',0),('artifact_id',0),('artifact_sha256','a'*64)]:self.assertFalse(p.approved_orchestration(pin|{key:value},p.OLD_APPROVAL_SHA,root))
  self.assertFalse(p.approved_orchestration(pin,'0'*64,root))
  other=pin|{'producer_commit':'b'*40}
  with patch.object(p,'revision',side_effect=[pin['orchestration'],{'sha256':'changed'}]):self.assertFalse(p.approved_orchestration(other,'x',root))
if __name__=='__main__':unittest.main()
