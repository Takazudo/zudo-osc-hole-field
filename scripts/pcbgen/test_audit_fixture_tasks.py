import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from scripts.pcbgen import audit_fixture_tasks as a
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_batch_text
class TaskTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.paths=[]
  self.uid='00000000-0000-4000-8000-000000000001';self.ids=['00000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000003']
  for stage in (0,1):
   p=self.root/str(stage)/'osc-core.kicad_pcb';p.parent.mkdir();p.write_text('(kicad_pcb (zone (uuid "'+self.uid+'") (layer "F.Cu") (polygon (pts (xy 0 0))) (filled_polygon (pts (xy '+str(stage+1)+' 1)))) '+' '.join('(footprint (uuid "'+uid+'") (pad "1" smd rect))' for uid in self.ids)+')');self.paths.append(p)
   p.with_suffix('.kicad_pro').write_text(json.dumps({'board':{'design_settings':{'rules':{'min_silk_clearance':0}}}}));p.with_suffix('.kicad_dru').write_text('rules')
  blobs={'native verifier':'a'*64};self.kernel=dict(image=a.IMAGE,version=a.VERSION,kernel_blobs=blobs,validator_revision=a.identity(blobs))
  scope=dict(zone_uuid=self.uid,layer='F.Cu',artwork_count=2,selected_item_uuids=self.ids,conservative_margin_nm=5000000,growth_boxes_nm=[[0,0,1,1]],planned_paired_fixtures=2,resume_prefix_count=0,required_new_reports=2)
  required=dict(version=a.VERSION,batch_size=16,before_sha256=a.SHA(self.paths[0].read_bytes()),after_sha256=a.SHA(self.paths[1].read_bytes()),planned_paired_fixtures=2,zones=[dict(uuid=self.uid,layer='F.Cu',net='AGND',before_area_nm2=1,after_area_nm2=2,native_added_area_nm2=1,native_added_shape_empty=False,native_added_outline_count=1,required_scope=scope)])
  self.m=a.build_manifest(required,*self.paths,self.kernel);self.bindings={a.identity(t['expected_geometry']):str(t['stage'])*64 for t in self.m['tasks']};self.bundles=[self.bundle(t) for t in self.m['tasks']]
 def bundle(self,t):
  paths,raw,texts,ctx=a.sources(*self.paths);pcb=a.fixture_bytes(t,texts,[set(self.ids),set(self.ids)],{});geo=self.bindings[a.identity(t['expected_geometry'])];native=a.canonical(dict(version=a.VERSION,fixture_sha256=a.SHA(pcb),context_sha256={s:a.SHA(v) for s,v in ctx.items()},native_geometry_sha256=geo));report=a.canonical(dict(kicad_version=a.VERSION,included_severities=['error','warning','exclusion'],violations=[]));r=dict(task_id=t['task_id'],fixture_sha256=a.SHA(pcb),native_validation_sha256=a.SHA(native),report_sha256=a.SHA(report),native_geometry_sha256=geo,identities=[])
  return dict(task_id=t['task_id'],fixture=pcb,context=ctx,native_validation=native,report=report,receipt=r,provenance={'policy':self.kernel})
 def verify(self,b=None,kernel=None):
  return a.verify_leaf(self.m,self.m['tasks'][0],b or self.bundles[0],*self.paths,kernel or self.kernel,self.bindings[a.identity(self.m['tasks'][0]['expected_geometry'])],(b or self.bundles[0])['provenance'])
 def test_exact_union_invokes_original_full_coverage_verifier(self):
  result,proof=a.final_union(self.m,*self.paths,self.bundles,self.kernel,self.bindings);self.assertTrue(proof['full_paired_zone_coverage']);self.assertEqual(proof['zones'][0]['fixtures'],2);self.assertNotIn('adopted',result);self.assertFalse(proof['adopted'])
 def test_stale_source_context_and_validator_fail_closed(self):
  for path in (self.paths[0],self.paths[0].with_suffix('.kicad_pro'),self.paths[1].with_suffix('.kicad_dru')):
   saved=path.read_bytes();path.write_bytes(b'changed')
   with self.assertRaises((ValueError,KeyError,json.JSONDecodeError)):a.validate_manifest(self.m,*self.paths,self.kernel)
   path.write_bytes(saved)
  k=copy.deepcopy(self.kernel);k['kernel_blobs']['native verifier']='b'*64;k['validator_revision']=a.identity(k['kernel_blobs'])
  with self.assertRaisesRegex(ValueError,'validator'):a.validate_manifest(self.m,*self.paths,k)
  with self.assertRaisesRegex(ValueError,'provenance'):self.verify(kernel=k)
 def test_altered_native_receipt_report_and_context(self):
  for field,value in [('native_validation',b'{}'),('report',a.canonical(dict(kicad_version='9.0.2',included_severities=[],violations=[]))),('context',{}),('fixture',b'changed'),('task_id','wrong')]:
   b=copy.deepcopy(self.bundles[0]);b[field]=value
   with self.assertRaises((ValueError,KeyError)):self.verify(b)
 def test_missing_report_and_ledger_native_mutation(self):
  t=self.m['tasks'][0];out=self.root/'checkpoints';digest=a.write_checkpoint(out,t,self.bundles[0]);folder=out/t['task_id'];origin=self.bundles[0]['provenance']
  b=a.read_checkpoint(out,t['task_id'],digest,origin);self.verify(b)
  saved=(folder/'complete.json').read_bytes();(folder/'complete.json').write_bytes(b'{}')
  with self.assertRaisesRegex(ValueError,'ledger hash'):a.read_checkpoint(out,t['task_id'],digest,origin)
  (folder/'complete.json').write_bytes(saved)
  native=folder/'native-validation.json';native.write_bytes(b'{}')
  b=a.read_checkpoint(out,t['task_id'],digest,origin)
  with self.assertRaises(ValueError):self.verify(b)
  (folder/'drc.json').unlink()
  with self.assertRaises(FileNotFoundError):a.read_checkpoint(out,t['task_id'],digest,origin)
 def test_duplicate_wrong_ids_and_incomplete_union(self):
  for bundles in ([self.bundles[0]],[self.bundles[0],self.bundles[0]],self.bundles+[dict(task_id='wrong')]):
   with self.assertRaisesRegex(ValueError,'coverage|ID'):a.final_union(self.m,*self.paths,bundles,self.kernel,self.bindings)
  ids=[t['task_id'] for t in self.m['tasks']]
  self.assertEqual(len(a.selection(self.m,{},[[ids[0]],[ids[1]]])),2)
  for packets in ([[ids[0],ids[0]]],[[ids[0]],[ids[0]]],[['wrong']]):
   with self.assertRaises(ValueError):a.selection(self.m,{},packets)
 def test_malformed_scope_and_unbound_geometry(self):
  for key,value in [('selected_item_uuids',list(reversed(self.ids))),('selected_item_uuids',[self.ids[0],self.ids[0]]),('growth_boxes_nm',[[0,0,-1,1]]),('conservative_margin_nm',0),('planned_paired_fixtures',1)]:
   scope=copy.deepcopy(self.m['required_scope']);scope['zones'][0]['required_scope'][key]=value
   with self.assertRaises(ValueError):a.build_manifest(scope,*self.paths,self.kernel)
  with self.assertRaisesRegex(ValueError,'geometry binding'):a.final_union(self.m,*self.paths,self.bundles,self.kernel,{})
 def test_partial_shard_status_cannot_produce_complete_union(self):
  b=copy.deepcopy(self.bundles[0]);b['status']='COMPLETE';b['zone_silk_scope_complete']=True
  with self.assertRaisesRegex(ValueError,'incomplete'):a.final_union(self.m,*self.paths,[b],self.kernel,self.bindings)
 def test_interruption_resume_preserves_only_committed_checkpoint(self):
  out=self.root/'interrupted';t=self.m['tasks'][0];digest=a.write_checkpoint(out,t,self.bundles[0]);other=out/self.m['tasks'][1]['task_id'];other.mkdir();(other/'native-validation.json').write_bytes(self.bundles[1]['native_validation']);(other/'drc.json.tmp').write_bytes(b'partial')
  restored=a.read_checkpoint(out,t['task_id'],digest,self.bundles[0]['provenance']);self.verify(restored)
  with self.assertRaises(FileNotFoundError):a.read_checkpoint(out,self.m['tasks'][1]['task_id'],'0'*64,self.bundles[1]['provenance'])
  self.assertEqual(a.selection(self.m,{t['task_id']:restored},[[self.m['tasks'][1]['task_id']]]),[self.m['tasks'][1]['task_id']])
if __name__=='__main__':unittest.main()
