import hashlib,importlib.util,json,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts.pcbgen import audit_zone_silk_scope as audit
spec=importlib.util.spec_from_file_location('recovery',Path(__file__).resolve().parents[2]/'circuit/routing/issue189/core236-audit-recovery/recover_isolated.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
class RecoveryTests(unittest.TestCase):
 def test_resource_stop_boundaries(self):
  sample={'available_kib':2*1024*1024,'total_rss_kib':12*1024*1024}
  self.assertIsNone(recovery.stop_reason(sample,1,2))
  self.assertEqual(recovery.stop_reason(sample,2,2),'INCONCLUSIVE_100_MINUTE_BUDGET')
  for delta in ({'available_kib':sample['available_kib']-1},{'total_rss_kib':sample['total_rss_kib']+1}):
   self.assertEqual(recovery.stop_reason(sample|delta,1,2),'INCONCLUSIVE_EARLY_MEMORY_STOP')
 def test_owned_child_cleanup_reaps_real_process(self):
  proc=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)
  try:
   self.assertTrue(recovery.process_tree([proc.pid]));recovery.clean(proc,[])
   self.assertIsNotNone(proc.returncode);self.assertEqual(recovery.process_tree([proc.pid]),{})
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
 def test_controller_memory_stop_retains_result_and_never_starts_downstream(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'verified-inputs.json').write_text(json.dumps(dict(counts={'verified':221},resume_artifact=11673646039)))
   spawn=subprocess.Popen;children=[]
   def own_child(command,**kwargs):
    self.assertIn('--isolate-fixture-processes',command);self.assertIn(str(root/'resume/core236-zone-recovery'),command)
    proc=spawn([sys.executable,'-c','import time; time.sleep(60)'],**kwargs);children.append(proc);return proc
   with patch.object(recovery,'ROOT',root),patch.object(recovery,'owned_containers',return_value=[]),patch.object(recovery,'available',return_value=1),patch.object(recovery.subprocess,'Popen',side_effect=own_child):
    with self.assertRaises(SystemExit):recovery.controller()
   result=json.loads((root/'controller-result.json').read_text());self.assertEqual(result['status'],'INCONCLUSIVE_EARLY_MEMORY_STOP');self.assertEqual(len(result['phases']),1);self.assertEqual(len(children),1);self.assertIsNotNone(children[0].returncode)
   tail=json.loads((root/'telemetry.jsonl').read_text().splitlines()[-1]);self.assertEqual(tail['tree_rss_kib'],{});self.assertEqual(tail['owned_containers_remaining'],[])
 def test_failed_validation_retains_timing_and_raises(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with self.assertRaisesRegex(ValueError,'native failure'):
    with audit.fixture_timing(root,'zone',0,1,'native_validation'):raise ValueError('native failure')
   events=[json.loads(x) for x in (root/'fixture-timings.jsonl').read_text().splitlines()]
   self.assertEqual([x['phase'] for x in events],['started','failed']);self.assertGreaterEqual(events[1]['seconds'],0)
 def test_every_later_zone_is_enumerated_before_first_fixture(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);before=root/'before.kicad_pcb';after=root/'after.kicad_pcb';out=root/'output'
   for path in (before,after):
    path.write_text('(kicad_pcb)')
    for suffix in ('.kicad_pro','.kicad_dru'):path.with_suffix(suffix).write_text('{}')
   class Poly:
    def CloneDropTriangulation(self):return Poly()
    def Area(self):return 1
    def BooleanSubtract(self,p):pass
    def IsEmpty(self):return False
    def OutlineCount(self):return 1
   def zone(uid,layer):return SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:uid),GetIsRuleArea=lambda:False,GetNetname=lambda:'AGND',GetLayerSet=lambda:SimpleNamespace(Seq=lambda:[layer]),GetFilledPolysList=lambda l:Poly())
   board=SimpleNamespace(Zones=lambda:[zone('first','F.Cu'),zone('second','B.Cu'),zone('later','F.Mask'),zone('internal','In1.Cu')])
   native=SimpleNamespace(LoadBoard=lambda p:board,LayerName=lambda l:l)
   def scope(path,board,uid,layer,growth,native,size):return ({'zone_uuid':uid,'layer':layer,'selected_item_uuids':[uid],'artwork_count':1,'conservative_margin_nm':0,'growth_boxes_nm':[]},[[uid]],{uid})
   seen=[]
   def classify(*args):
    required=json.loads((out/'required-scope.json').read_text());self.assertEqual([r['uuid'] for r in required['zones']],['first','second','later']);self.assertEqual(required['planned_paired_fixtures'],6)
    seen.append(args[5]);return {'new_identities':[]}
   with patch.dict(sys.modules,pcbnew=native),patch.object(audit.subprocess,'check_output',return_value='10.0.6'),patch.object(audit,'classification_scope',side_effect=scope),patch.object(audit,'classify_zone',side_effect=classify):
    audit.main(before,after,out,classify=True,batch_size=16,isolate_fixtures=True)
   self.assertEqual(seen,['first','second','later'])
 def test_exact221_prefix_and_mutations(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);resume=root/'resume';resume.mkdir();before=root/'before.kicad_pcb';after=root/'after.kicad_pcb';before.write_text('before');after.write_text('after')
   for source in (before,after):
    for suffix in ('.kicad_pro','.kicad_dru'):source.with_suffix(suffix).write_text(suffix)
   digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
   (resume/'result.json').write_text(json.dumps(dict(version='10.0.6',before_sha256=digest(before),after_sha256=digest(after))))
   report=json.dumps(dict(kicad_version='10.0.6',included_severities=['error','warning','exclusion'],violations=[])).encode();first=None
   for uid,n,count in [('601e02b2-8ccb-5c28-83e5-03789d47fbbd',1757,220),('e389d344-872d-538e-9bfc-39577adb1686',1635,1)]:
    selected=[str(i) for i in range(n)];(resume/f'zone-{uid}-scope.json').write_text(json.dumps(dict(zone_uuid=uid,selected_item_uuids=selected)))
    rows=[];batches=audit.artwork_batches(selected,16)
    for stage,index,ids in [(s,i,ids) for s in (0,1) for i,ids in enumerate(batches)][:count]:
     folder=resume/f'zone-{uid}'/f'{stage}-batch-{index:04d}';folder.mkdir(parents=True);fixture=folder/'osc-core.kicad_pcb';fixture.write_text(f'{stage}:{index}')
     for suffix in ('.kicad_pro','.kicad_dru'):fixture.with_suffix(suffix).write_text(suffix)
     (folder/'drc.json').write_bytes(report);rows.append(dict(stage=stage,batch_index=index,item_uuids=ids,fixture_sha256=digest(fixture),native_geometry_sha256='0'*64,report_sha256=digest(folder/'drc.json'),identities=[]))
     if first is None:first=folder
    (resume/f'zone-{uid}-progress.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
   with patch.object(recovery,'BEFORE',digest(before)),patch.object(recovery,'AFTER',digest(after)):
    self.assertEqual(len(recovery.verify_prefix(resume,before,after)['reports']),221)
    for path,error in [(first/'drc.json','raw report'),(first/'osc-core.kicad_pcb','fixture bytes'),(first/'osc-core.kicad_pro','native context')]:
     saved=path.read_bytes();path.write_bytes(b'changed')
     with self.assertRaisesRegex(ValueError,error):recovery.verify_prefix(resume,before,after)
     path.write_bytes(saved)
    progress=resume/'zone-601e02b2-8ccb-5c28-83e5-03789d47fbbd-progress.jsonl';rows=progress.read_text().splitlines();rows[0],rows[1]=rows[1],rows[0];progress.write_text('\n'.join(rows)+'\n')
    with self.assertRaisesRegex(ValueError,'ordered prefix'):recovery.verify_prefix(resume,before,after)
if __name__=='__main__':unittest.main()
