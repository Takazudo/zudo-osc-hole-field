import copy,json,unittest
import stage6_rebudget as s
class RebudgetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.prior=json.loads((s.a.OUT/'stage5/candidate-report.json').read_text())['candidate']
  cls.base=json.loads((s.a.OUT/'stage4/candidate-report.json').read_text())['candidate']
  cls.assembly=json.loads((s.a.OUT/'assembly-report.json').read_text())
  cls.spec=json.loads((s.OUT/'header-repair-input.json').read_text())
  cls.mechanical=json.loads((s.OUT/'mechanical-input.json').read_text())
 def run_case(self,prior=None,base=None,spec=None,mechanical=None):
  return s.rebuild(prior or self.prior,base or self.base,self.assembly,spec or self.spec,mechanical or self.mechanical)
 def test_current_accounting(self):
  c,changes,m=self.run_case();self.assertEqual(len(c['paths']),225);self.assertEqual(len(c['returns']),240)
  self.assertEqual(len(c['wire_checks']),270);self.assertEqual(m['summary']['qualified_rows'],0)
  self.assertEqual(m['summary']['electrical_UNKNOWN_rows'],225)
 def test_inconsistent_board_face_rejected(self):
  p=copy.deepcopy(self.mechanical);p['middle_GH_opposite_surface_z_mm']=50
  with self.assertRaisesRegex(ValueError,'face datum'):self.run_case(mechanical=p)
 def test_registered_wire_coordinates(self):
  c,_,_=self.run_case()
  for w in c['wire_checks']:
   self.assertEqual(48.4,w['middle_pad_xyz_mm'][2]);self.assertAlmostEqual(s.math.dist(w['front_pad_xyz_mm'],w['middle_pad_xyz_mm']),w['straight_pad_distance_mm'])
 def test_illicit_front_pad_change_rejected(self):
  p=copy.deepcopy(self.prior);p['paths'][0]['actual_identity']='invented'
  with self.assertRaisesRegex(ValueError,'endpoint'):self.run_case(prior=p)
 def test_nonmiddle_allowance_change_rejected(self):
  p=copy.deepcopy(self.prior);p['paths'][0]['segments']['rear_trace_mm']+=1
  with self.assertRaisesRegex(ValueError,'allowance'):self.run_case(prior=p)
 def test_missing_return_rejected(self):
  p=copy.deepcopy(self.prior);p['returns'].pop()
  with self.assertRaisesRegex(ValueError,'return inventory'):self.run_case(prior=p)
 def test_return_ownership_change_rejected(self):
  p=copy.deepcopy(self.prior);p['returns'][0]['instance']='O9'
  with self.assertRaisesRegex(ValueError,'return ownership'):self.run_case(prior=p)
 def test_middle_return_target_change_rejected(self):
  p=copy.deepcopy(self.prior);row=next(r for r in p['returns'] if r.get('middle_return_corridors'));row['middle_return_corridors'][0]['to']='invented'
  with self.assertRaisesRegex(ValueError,'corridor identity'):self.run_case(prior=p)
 def test_aggregate_cap_change_rejected(self):
  p=copy.deepcopy(self.prior);p['shared_aggregate_capacitance'][0]['invented_extracted_value']=1
  with self.assertRaisesRegex(ValueError,'shared cap'):self.run_case(prior=p)
 def test_unsupported_translation_rejected(self):
  p=copy.deepcopy(self.spec);p['moves'].append({'instance':'O1','header_ref':'invented','delta_mm':[1,0]})
  with self.assertRaisesRegex(ValueError,'unknown header'):self.run_case(spec=p)
if __name__=='__main__':unittest.main()
