import copy,json,tempfile,unittest,zipfile,shutil
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import audit_fixture_tasks as a,core_audit_pilot as p,core_audit_after as h,core_audit_geometry as g
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'circuit/routing/issue189/core236-task-checkpoints'
class AfterTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.m=json.loads((CONFIG/'manifest.json').read_bytes());self.kernel=a.policy(ROOT);self.original=json.loads((CONFIG/'native-geometry-bindings.json').read_bytes());self.plan=json.loads((CONFIG/'after103-proposed-wave-plan.json').read_bytes());self.fact=self.plan['native_geometry_fact'];self.bindings=h.StageBindings(h._SEAL,self.original,self.fact);self.base={k:{} for k in self.plan['baseline_task_ids']}
 def test_exact_proposed_plan_and_seven_disjoint_waves(self):
  self.assertEqual(a.SHA((CONFIG/'after103-proposed-wave-plan.json').read_bytes()),h.PLAN_SHA)
  h.load_plan(CONFIG,self.m,self.bindings,self.kernel);leaves=dict(self.base);seen=set()
  for i,count in enumerate((16,16,16,16,16,16,7)):
   packets=h.select_wave(self.m,leaves,self.plan,i,self.bindings,self.kernel);ids={x for packet in packets for x in packet};self.assertEqual(len(ids),count);self.assertFalse(ids&seen);seen|=ids;leaves.update({k:{} for k in ids})
  self.assertEqual(set(leaves),{t['task_id'] for t in self.m['tasks']});self.assertEqual(len(seen),103)
 def test_plain_json_stale_binding_changed_fact_and_stage_rejected(self):
  t=next(t for t in self.m['tasks'] if h.is_after(t))
  with self.assertRaisesRegex(ValueError,'not JSON'):h.require_binding(self.m,t,self.kernel,dict(self.bindings))
  for mutate in (lambda b:b.update({self.fact['reference_sha256']:'0'*64}),lambda b:b._fact.update(signature='0'*64),lambda b:b._fact.update(context_sha256={}),lambda b:b._fact.update(source_sha256=['0'*64]*2),lambda b:b._fact.update(validator_revision='0'*64)):
   b=h.StageBindings(h._SEAL,self.original,self.fact);mutate(b)
   with self.assertRaises(ValueError):h.require_binding(self.m,t,self.kernel,b)
  bad=copy.deepcopy(t);bad['expected_geometry']['source_board_sha256']='0'*64
  with self.assertRaises(ValueError):h.require_binding(self.m,bad,self.kernel,self.bindings)
  with self.assertRaises(ValueError):h.StageBindings(object(),self.original,self.fact)
 def test_plan_missing_duplicate_ids_wrong_stage_bounds_and_fact(self):
  mutations=(lambda p:p['baseline_task_ids'].pop(),lambda p:p['baseline_task_ids'].__setitem__(0,p['baseline_task_ids'][1]),lambda p:p['missing_task_ids'].pop(),lambda p:p['missing_task_ids'].__setitem__(0,p['missing_task_ids'][1]),lambda p:p['packets'][0]['task_ids'].__setitem__(0,p['baseline_task_ids'][0]),lambda p:p['native_geometry_fact'].update(signature='0'*64),lambda p:p['bounds'].update(global_native_workers=3),lambda p:p['waves'][0].update(expected_coverage=999))
  for mutate in mutations:
   changed=copy.deepcopy(self.plan);mutate(changed)
   with self.assertRaises(ValueError):h.validate_plan(self.m,changed,self.bindings,self.kernel)
  for index,leaves in ((1,self.base),(0,self.base|{self.plan['missing_task_ids'][0]:{}}),(0,{k:v for k,v in self.base.items() if k!=next(iter(self.base))}),(7,self.base)):
   with self.assertRaises(ValueError):h.select_wave(self.m,leaves,self.plan,index,self.bindings,self.kernel)
 def test_worker_rejects_duplicate_missing_and_wrong_stage_packets(self):
  packet=self.plan['packets'][0]['task_ids'];h.verify_worker_packet(self.m,self.kernel,self.bindings,packet)
  for ids in ([],packet+[packet[0]],['unknown'],[self.plan['baseline_task_ids'][0]],self.plan['waves'][0]['task_ids']):
   with self.assertRaises(ValueError):h.verify_worker_packet(self.m,self.kernel,self.bindings,ids)
 def test_exact_historical_bootstrap_only_and_original_blobs_rehashed(self):
  pin=json.loads((CONFIG/'geometry-success-38098640864/artifact-approval.json').read_bytes());sha=h.BOOTSTRAP[-1]
  h.validate_pin(pin,sha,ROOT);self.assertTrue(p.approved_orchestration(pin,sha,ROOT))
  for k,v in (('producer_commit','0'*40),('run',0),('artifact_id',0),('artifact_sha256','0'*64)):
   with self.assertRaises(ValueError):h.validate_pin(pin|{k:v},sha,ROOT)
  with self.assertRaises(ValueError):h.validate_pin(pin,'0'*64,ROOT)
  changed=copy.deepcopy(pin);changed['orchestration']['blobs']['scripts/pcbgen/core_audit_geometry.py']='0'*64
  with self.assertRaises(ValueError):h.validate_pin(changed,sha,ROOT)
  with patch.object(p.subprocess,'check_output',return_value=b'altered historical source'):
   with self.assertRaises(ValueError):h.validate_pin(pin,sha,ROOT)
  failed=CONFIG/'owner-waves-a56f204/geometry-failed-38095685843/authenticated-artifact-approval.json';f=json.loads(failed.read_bytes())
  self.assertFalse(p.approved_orchestration(f,a.SHA(failed.read_bytes()),ROOT))
  with self.assertRaises(ValueError):h.validate_pin(f,a.SHA(failed.read_bytes()),ROOT)
 def synthetic_bootstrap(self,mutate=None):
  # ZIP production is synthetic, but every receipt/control/hash/extraction path
  # is real. Only external reviewed tuple/source and GitHub transport are mocked.
  receipt=json.loads((CONFIG/'geometry-success-38098640864/geometry-receipt.json').read_bytes())
  producer=json.loads((CONFIG/'geometry-success-38098640864/producer.json').read_bytes())
  if mutate:mutate(receipt,producer)
  raw=a.canonical(receipt)+b'\n';producer['geometry_receipt_sha256']=a.SHA(raw)
  archive=self.root/'synthetic.zip'
  with zipfile.ZipFile(archive,'w') as z:z.writestr('producer.json',a.canonical(producer));z.writestr('shard-0/geometry-receipt.json',raw)
  pin=json.loads((CONFIG/'geometry-success-38098640864/artifact-approval.json').read_bytes());pin['artifact_sha256']=a.SHA(archive.read_bytes());approval=self.root/'approval.json';a.atomic(approval,pin);sha=a.SHA(approval.read_bytes());key=(pin['producer_commit'],pin['run'],pin['artifact_id'],pin['artifact_sha256'],sha)
  return archive,approval,pin,key
 def authenticate_synthetic(self,mutate=None,offline=False,conclusion='success'):
  archive,approval,pin,key=self.synthetic_bootstrap(mutate)
  artifact=dict(id=pin['artifact_id'],expired=False,digest='sha256:'+pin['artifact_sha256'],workflow_run=dict(id=pin['run'],head_sha=pin['producer_commit']));execution=dict(id=pin['run'],head_sha=pin['producer_commit'],path='.github/workflows/routing-benchmark.yml',status='completed',conclusion=conclusion)
  with patch.object(h,'BOOTSTRAP',key),patch.object(p,'historical_orchestration',return_value=True),patch.object(a,'github_json',side_effect=[artifact,execution]) as network:
   b=h.authenticate_binding(archive,approval,self.m,self.kernel,ROOT,self.root/'verified',self.original,offline=offline)
   self.assertEqual(network.call_count,0 if offline else 2)
   return b
 def test_full_bootstrap_authentication_online_and_worker_offline(self):
  b=self.authenticate_synthetic();self.assertEqual(b.fact['signature'],self.fact['signature']);self.assertEqual(len(b),4)
  shutil.rmtree(self.root/'verified');b=self.authenticate_synthetic(offline=True);self.assertEqual(b.fact['native_receipt_sha256'],self.fact['native_receipt_sha256'])
 def test_actual_receipt_reload_control_stage_and_partial_mutations_rejected(self):
  mutations=(lambda r,p:r['independent_reloads'][1]['rows'][0].update(signature='0'*64),lambda r,p:[s['rows'][0].update(signature='0'*64) for s in r['independent_reloads']],lambda r,p:[s['rows'][-1].update(stage=0) for s in r['independent_reloads']],lambda r,p:r.update(saved=True),lambda r,p:p.update(status='INCOMPLETE_WORKER_FAILURE'),lambda r,p:p['prior_task_ids'].pop(),lambda r,p:p['prior_task_ids'].append(p['prior_task_ids'][0]))
  for mutate in mutations:
   with self.assertRaises(ValueError):self.authenticate_synthetic(mutate)
   if (self.root/'verified').exists():shutil.rmtree(self.root/'verified')
  with self.assertRaisesRegex(ValueError,'terminal success'):self.authenticate_synthetic(conclusion='failure')
 def test_offline_bypass_cannot_authenticate_other_artifacts(self):
  archive,approval,pin,key=self.synthetic_bootstrap()
  with self.assertRaises(ValueError):p.authenticate_checkpoints(archive,approval,key[-1],self.m,self.kernel,ROOT,self.root/'forged',_offline_bootstrap=True)
 def test_leaf_requires_binding_in_receipt_and_authenticated_producer(self):
  t=next(t for t in self.m['tasks'] if h.is_after(t));token=self.bindings.evidence(self.m,self.kernel);receipt={'task_id':t['task_id'],'stage_geometry_sha256':token};bundle={'receipt':receipt};origin={'stage_geometry_sha256':token};authority=a.VerifiedAuthority(a._SEAL,self.m,self.kernel,{t['task_id']:a.identity(receipt)},origin)
  with patch.object(a,'_verify_leaf_bytes',return_value=receipt) as verify:
   a.verify_leaf(self.m,t,bundle,'b','a',self.kernel,self.fact['signature'],authority,stage_geometry=token);self.assertEqual(verify.call_args.args[-1],token)
   with self.assertRaises(ValueError):a.verify_leaf(self.m,t,bundle,'b','a',self.kernel,self.fact['signature'],authority)
   bad=a.VerifiedAuthority(a._SEAL,self.m,self.kernel,{t['task_id']:a.identity(receipt)},{})
   with self.assertRaises(ValueError):a.verify_leaf(self.m,t,bundle,'b','a',self.kernel,self.fact['signature'],bad,stage_geometry=token)
 def test_after_reconciliation_requires_exact_producer_and_native_clean_report(self):
  ids=self.plan['waves'][0]['task_ids'];new={k:{'receipt':{},'provenance':{},'report':a.canonical({'violations':[]})} for k in ids};producer=dict(mode='after-wave',wave=0,prior_task_ids=sorted(self.base),requested_task_ids=sorted(ids),stage_geometry_fact=self.fact,stage_geometry_sha256=self.bindings.evidence(self.m,self.kernel),status='PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN',cleanup_errors=[],owned_containers_remaining=[],process_tree_after_cleanup={})
  with patch.object(a,'sources',return_value=([],[],['x','x'],{})),patch.object(a,'artwork_ids',return_value=set()),patch.object(a,'verify_leaf'):
   self.assertEqual(len(h.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',self.kernel,self.bindings)),339)
   for delta in ({'mode':'before-wave'},{'wave':1},{'stage_geometry_sha256':'0'*64},{'stage_geometry_fact':{}},{'prior_task_ids':[]},{'status':'INCOMPLETE_MEMORY_GUARD'},{'status':'INCOMPLETE_SHARED_40_MINUTE_BUDGET'},{'cleanup_errors':['x']},{'owned_containers_remaining':['x']},{'process_tree_after_cleanup':{'pid':1}}):
    with self.assertRaises(ValueError):h.reconcile_wave(self.m,self.plan,0,self.base,new,producer|delta,'b','a',self.kernel,self.bindings)
   with self.assertRaises(ValueError):h.reconcile_wave(self.m,self.plan,0,self.base,{ids[0]:new[ids[0]]},producer,'b','a',self.kernel,self.bindings)
   new[ids[0]]['report']=a.canonical({'violations':[{'severity':'error'}]})
   with self.assertRaisesRegex(ValueError,'native error'):h.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',self.kernel,self.bindings)
  with patch.object(a,'sources',return_value=([],[],['x','x'],{})),patch.object(a,'artwork_ids',return_value=set()),patch.object(a,'verify_leaf',side_effect=ValueError('silk fixture reached report cap')):
   with self.assertRaisesRegex(ValueError,'cap'):h.reconcile_wave(self.m,self.plan,0,self.base,new,producer,'b','a',self.kernel,self.bindings)
 def after_artifact(self,alter=None):
  archive,approval,pin,key=self.synthetic_bootstrap();receipt=json.loads((CONFIG/'geometry-success-38098640864/geometry-receipt.json').read_bytes())
  fact=g.validate_receipt(self.m,self.kernel,self.original,receipt)|dict(source_sha256=self.m['source_sha256'],context_sha256=self.m['context_sha256'],image=a.IMAGE,validator_revision=self.kernel['validator_revision'],manifest_sha256=a.identity(self.m),artifact_approval_sha256=key[-1],producer=pin,native_receipt_sha256=a.SHA(a.canonical(receipt)+b'\n'),stage_review_required=True)
  token=a.identity(fact);task=self.plan['packets'][0]['task_ids'][0];complete={'task_id':task,'stage_geometry_sha256':token};producer=dict(producer_commit='c'*40,run=99,mode='after-wave',wave=0,manifest_sha256=a.identity(self.m),policy=self.kernel,orchestration={'sha256':'current'},image=a.IMAGE,inspected_image_id='image-id',expected_image_id='image-id',stage_geometry_fact=fact,stage_geometry_sha256=token)
  if alter:alter(complete,producer)
  task=complete['task_id'];raw=a.canonical(complete)+b'\n';ledger=a.canonical({'tasks':{task:a.SHA(raw)}})+b'\n';producer['ledgers']={'shard-0/ledger.json':a.SHA(ledger)}
  path=self.root/'after.zip'
  with zipfile.ZipFile(path,'w') as z:
   z.writestr('producer.json',a.canonical(producer));z.writestr('shard-0/ledger.json',ledger);z.writestr('shard-0/'+task+'/complete.json',raw)
   for suffix in ('.kicad_pro','.kicad_dru'):z.writestr('shard-0/'+task+'/osc-core'+suffix,b'{}')
   z.writestr('geometry/bootstrap.zip',archive.read_bytes());z.writestr('geometry/approval.json',approval.read_bytes())
  after_pin={k:producer[k] for k in ('producer_commit','run','manifest_sha256','policy','orchestration','ledgers')}|dict(artifact_id=100,artifact_sha256=a.SHA(path.read_bytes()));after_approval=self.root/'after-approval.json';a.atomic(after_approval,after_pin)
  return path,after_approval,after_pin,key,pin,token
 def test_after_artifact_reauthenticates_embedded_bootstrap_before_authorizing_leaf(self):
  path,approval,pin,key,bootstrap,token=self.after_artifact()
  def api(url):
   v=bootstrap if str(bootstrap['run'])==url.split('/')[-1] or str(bootstrap['artifact_id'])==url.split('/')[-1] else pin
   if url.startswith('actions/artifacts/'):return dict(id=v['artifact_id'],expired=False,digest='sha256:'+v['artifact_sha256'],workflow_run=dict(id=v['run'],head_sha=v['producer_commit']))
   return dict(id=v['run'],head_sha=v['producer_commit'],path='.github/workflows/routing-benchmark.yml',status='completed',conclusion='success')
  with patch.object(h,'BOOTSTRAP',key),patch.object(p,'historical_orchestration',return_value=True),patch.object(p,'revision',return_value=pin['orchestration']),patch.object(a,'github_json',side_effect=api):
   leaves=p.authenticate_checkpoints(path,approval,a.SHA(approval.read_bytes()),self.m,self.kernel,ROOT,self.root/'after-verified');self.assertEqual(len(leaves),1);b=next(iter(leaves.values()));self.assertEqual(b['provenance'].origin['stage_geometry_sha256'],token);self.assertEqual(b['receipt']['stage_geometry_sha256'],token)
 def test_after_artifact_missing_binding_wrong_stage_and_altered_producer_rejected(self):
  for mutate in (lambda r,p:r.pop('stage_geometry_sha256'),lambda r,p:r.update(stage_geometry_sha256='0'*64),lambda r,p:r.update(task_id=self.plan['baseline_task_ids'][0]),lambda r,p:p.update(stage_geometry_fact={}),lambda r,p:p.update(stage_geometry_sha256='0'*64)):
   path,approval,pin,key,bootstrap,token=self.after_artifact(mutate)
   def api(url):
    v=bootstrap if url.split('/')[-1] in (str(bootstrap['run']),str(bootstrap['artifact_id'])) else pin
    if url.startswith('actions/artifacts/'):return dict(id=v['artifact_id'],expired=False,digest='sha256:'+v['artifact_sha256'],workflow_run=dict(id=v['run'],head_sha=v['producer_commit']))
    return dict(id=v['run'],head_sha=v['producer_commit'],path='.github/workflows/routing-benchmark.yml',status='completed',conclusion='success')
   with patch.object(h,'BOOTSTRAP',key),patch.object(p,'historical_orchestration',return_value=True),patch.object(p,'revision',return_value=pin['orchestration']),patch.object(a,'github_json',side_effect=api):
    with self.assertRaises(ValueError):p.authenticate_checkpoints(path,approval,a.SHA(approval.read_bytes()),self.m,self.kernel,ROOT,self.root/'after-negative')
   shutil.rmtree(self.root/'after-negative')
class AfterLeafAggregateTests(unittest.TestCase):
 def setUp(self):
  from scripts.pcbgen import test_audit_fixture_tasks as fixtures
  self.fixture=fixtures.TaskTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);f=self.fixture
  old=f.uid;f.uid=g.TARGET[0]
  for path in f.paths:path.write_text(path.read_text().replace(old,f.uid).replace('F.Cu','B.Cu'))
  required=copy.deepcopy(f.m['required_scope']);row=required['zones'][0];row['uuid']=f.uid;row['layer']='B.Cu';row['required_scope']['zone_uuid']=f.uid;row['required_scope']['layer']='B.Cu'
  required['before_sha256']=a.SHA(f.paths[0].read_bytes());required['after_sha256']=a.SHA(f.paths[1].read_bytes());f.m=a.build_manifest(required,*f.paths,f.kernel);f.bindings={a.identity(t['expected_geometry']):str(t['stage'])*64 for t in f.m['tasks']}
  original={a.identity(f.m['tasks'][0]['expected_geometry']):'0'*64,'control1':'a'*64,'control2':'b'*64};target=f.m['tasks'][1]['expected_geometry'];fact=dict(reference=target,reference_sha256=a.identity(target),signature='1'*64,manifest_sha256=a.identity(f.m),validator_revision=f.kernel['validator_revision'],image=a.IMAGE,source_sha256=f.m['source_sha256'],context_sha256=f.m['context_sha256'])
  self.bindings=h.StageBindings(h._SEAL,original,fact);self.token=self.bindings.evidence(f.m,f.kernel);f.bundles=[f.bundle(t) for t in f.m['tasks']];f.bundles[1]['receipt']['stage_geometry_sha256']=self.token
  for t,b in zip(f.m['tasks'],f.bundles):
   origin={'stage_geometry_sha256':self.token} if h.is_after(t) else {}
   b['provenance']=a.VerifiedAuthority(a._SEAL,f.m,f.kernel,{t['task_id']:a.identity(b['receipt'])},origin)
 def test_full_bytes_leaf_checkpoint_and_original_final_union_carry_binding(self):
  f=self.fixture;t=f.m['tasks'][1];b=f.bundles[1];checkpoint=f.root/'after-leaf';digest=a.write_checkpoint(checkpoint,t,b);loaded=a.read_checkpoint(checkpoint,t['task_id'],digest,b['provenance']);self.assertEqual(loaded['receipt']['stage_geometry_sha256'],self.token)
  result,proof=a.final_union(f.m,*f.paths,[f.bundles[0],loaded],f.kernel,self.bindings)
  self.assertTrue(proof['full_paired_zone_coverage']);self.assertEqual(result['stage_geometry_sha256'],self.token);self.assertEqual(result['stage_geometry_fact'],self.bindings.fact);self.assertFalse(proof['adopted'])
  with self.assertRaisesRegex(ValueError,'not JSON'):a.final_union(f.m,*f.paths,f.bundles,f.kernel,dict(self.bindings))
 def test_leaf_receipt_binding_missing_altered_or_wrong_stage_rejected(self):
  f=self.fixture
  for index,value in ((1,None),(1,'0'*64),(0,self.token)):
   b=copy.deepcopy(f.bundles[index]);t=f.m['tasks'][index]
   if value is None:b['receipt'].pop('stage_geometry_sha256')
   else:b['receipt']['stage_geometry_sha256']=value
   b['provenance']=a.VerifiedAuthority(a._SEAL,f.m,f.kernel,{t['task_id']:a.identity(b['receipt'])},{'stage_geometry_sha256':self.token})
   with self.assertRaisesRegex(ValueError,'binding|stage'):a.verify_leaf(f.m,t,b,*f.paths,f.kernel,self.bindings[a.identity(t['expected_geometry'])],b['provenance'],stage_geometry=self.token if index else None)
if __name__=='__main__':unittest.main()
