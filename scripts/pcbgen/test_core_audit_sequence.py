import json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_sequence as s
from scripts.pcbgen import test_core_audit_waves as fixtures
class SequenceTests(unittest.TestCase):
 def test_bad_proof_stops_before_second_admission_and_atomic_marker_prevents_replay(self):
  fixture=fixtures.WaveTests();fixture.setUp();m=fixture.m;plan=fixture.plan
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);config=root/'config';config.mkdir();output=root/'out';a.atomic(config/'before-wave-plan.json',plan);a.atomic(config/'manifest.json',m)
   dispatched=[];head='a'*40
   def shell(cmd,**kwargs):
    if cmd[:2]==['git','rev-parse']:return head
    if cmd[:2]==['git','status']:return ''
    if cmd[:2]==['git','branch']:return 'reviewed-branch'
    raise AssertionError(cmd)
   def api(path):
    if path=='actions/runs/1':return dict(head_sha=head,status='completed',conclusion='success')
    if path=='actions/runs/1/jobs?per_page=100':return {'jobs':[{'conclusion':'success'}]*5}
    if path.startswith('git/ref/'):return {'object':{'sha':head}}
    if path.startswith('actions/workflows/'):return {'workflow_runs':[dict(id=100,head_sha=head)] if dispatched else []}
    if path=='actions/runs/100':return dict(status='completed',conclusion='success')
    if path=='actions/runs/100/artifacts':return {'artifacts':[dict(id=42,name='core-audit-task-pilot-100',digest='sha256:'+'b'*64)]}
    raise AssertionError(path)
   def post(cmd,**kwargs):dispatched.append(cmd)
   def download(pin,path):
    with zipfile.ZipFile(path,'w') as z:z.writestr('producer.json',json.dumps({'ledgers':{}}))
   with patch.object(s.subprocess,'check_output',side_effect=shell),patch.object(s.subprocess,'run',side_effect=post),patch.object(s,'api',side_effect=api),patch.object(a,'policy',return_value={}),patch.object(s.p,'load_approved',return_value=(fixture.base,fixture.bindings)),patch.object(s,'download',side_effect=download),patch.object(s.p,'revision',return_value={}),patch.object(s.p,'authenticate_checkpoints',return_value={}),patch.object(s,'reconcile_wave',side_effect=ValueError('proof mismatch')):
    with self.assertRaisesRegex(ValueError,'proof mismatch'):s.sequence(root,root,config,output,head,a.SHA((config/'before-wave-plan.json').read_bytes()),1)
    self.assertEqual(len(dispatched),1);self.assertTrue((output/'wave-0-admission.json').exists());self.assertFalse((output/'wave-1-admission.json').exists());state=json.loads((output/'sequence.json').read_bytes());self.assertEqual(state['status'],'STOPPED_NO_AUTOMATIC_RETRY');self.assertEqual(state['resume_approvals'],[])
    with self.assertRaisesRegex(ValueError,'disjoint'):s.sequence(root,root,config,output,head,'ignored',1)
    self.assertEqual(len(dispatched),1)
if __name__=='__main__':unittest.main()
