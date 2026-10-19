"""Source regression and adversarial checks, not physical/native acceptance."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stage46_analyze',HERE/'analyze.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class EscapeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'geometry.json').read_text())
 def test_replay_all_screens(self):
  expected=json.loads((HERE/'results.json').read_text())
  actual=[a.analyze(self.data,w,m)[0] for m in [0,.01] for w in [.4,.15,.1]]
  self.assertEqual(actual,expected)
  for r in actual:
   self.assertGreater(r['window_boundary_distance_mm'],1)
   self.assertGreater(r['other_ground_distance_mm'],.6)
   self.assertTrue(all(v['empty'] for v in r['vias'].values()))
 def test_native_fill_evidence(self):
  self.assertEqual(self.data['native_open_edges'],117)
  self.assertEqual(self.data['witness_count'],806)
  self.assertEqual(self.data['witness_mismatches'],0)
  audit=self.data['area_audit']
  self.assertLessEqual(abs(audit['area_before_mm2']-audit['area_after_mm2']),audit['area_tolerance_mm2'])
 def test_missing_obstacles_changes_verdict(self):
  d=copy.deepcopy(self.data);d['objects']=[o for o in d['objects'] if o['net']=='AGND']
  r,*_=a.analyze(d)
  self.assertEqual(r['window_boundary_distance_mm'],0)
  self.assertTrue(all(not v['empty'] for v in r['vias'].values()))
 def test_added_ground_target_detected(self):
  from shapely.geometry import Point,mapping
  d=copy.deepcopy(self.data)
  _,reachable,_,seed=a.analyze(d)
  target=reachable.buffer(.05).difference(seed.buffer(.002)).representative_point().buffer(.0001)
  d['objects'].append(dict(id='test-target',name='synthetic target',net='AGND',layers=['B.Cu'],geometry=mapping(target)))
  r,*_=a.analyze(d)
  self.assertLess(r['other_ground_distance_mm'],.1)
 def test_local_export_replay(self):
  inputs=[a.ROOT/p for p in self.data['input_sha256']]
  if not all(p.exists() for p in inputs):self.skipTest('large ignored native inputs unavailable')
  for p in inputs:self.assertEqual(a.sha(p),self.data['input_sha256'][str(p.relative_to(a.ROOT))])
  self.assertEqual(json.loads(json.dumps(a.export())),self.data)
if __name__=='__main__':unittest.main()
