import copy,json,unittest
import stage6_mechanical as m
class Stage6MechanicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=json.loads((m.OUT/'candidate-report.json').read_text())['candidate'];cls.s=json.loads((m.OUT/'mechanical-input.json').read_text());cls.e=json.loads((m.OUT.parent/'stage5/din-evidence.json').read_text());cls.r=m.build()
 def test_named_mating_contacts(self):
  contacts,flanges=m.register(self.c,self.s,self.e);self.assertEqual(len(contacts),480);self.assertEqual(len(flanges),10)
  for p in contacts:self.assertEqual(p['point_mm'],p['male_point_mm'])
  by={p['id']:p for p in contacts};self.assertEqual(by['O1:a1']['point_mm'],[12.54,189.37]);self.assertEqual(by['O1:c32']['point_mm'],[7.46,110.63])
 def test_mirror_mutation_rejected(self):
  for key in ['female_A_to_global_xy_matrix','male_B_to_global_xy_matrix']:
   s=copy.deepcopy(self.s);s[key][0][1]*=-1
   with self.assertRaises(AssertionError):m.register(self.c,s,self.e)
 def test_flange_sign_mutation_rejected(self):
  s=copy.deepcopy(self.s);s['female_flange_v_mm']=.3
  with self.assertRaises(AssertionError):m.register(self.c,s,self.e)
 def test_angle_mutation_rejected(self):
  c=copy.deepcopy(self.c);c['connector_turn_deg']=0
  with self.assertRaises(AssertionError):m.register(c,self.s,self.e)
 def test_pin_assignment_mutation_rejected(self):
  c=copy.deepcopy(self.c);r=next(r for r in c['paths']if r['DIN_pad_mm']is not None);r['DIN_pad_mm'][0]+=2.54
  with self.assertRaisesRegex(AssertionError,'electrical DIN'):m.register(c,self.s,self.e)
 def test_annular_mutation_recomputes(self):
  s=copy.deepcopy(self.s);old=m.register(self.c,s,self.e)[0];s['proposed_contact_pad_diameter_mm']+=.2;new=m.register(self.c,s,self.e)[0];self.assertAlmostEqual(new[0]['radius_mm']-old[0]['radius_mm'],.1)
 def test_all_prior_projections_resolved(self):
  self.assertEqual(len(self.r['stage5_twelve_resolution']),12);self.assertTrue(all(p['status']=='SOURCE_EXCLUSION_RESOLVED_BY_WHOLE_HEADER_MOVE'for p in self.r['stage5_twelve_resolution']))
  for key in ['remaining_GH_courtyard_exclusions','same_face_header_courtyard_conflicts','shared_middle_hole_or_pad_conflicts']:self.assertEqual(self.r[key],[])
  self.assertFalse(self.r['physical_acceptance']);self.assertTrue(self.r['remaining_unknown'])
 def test_reverting_headers_restores_exclusions(self):
  self.assertGreaterEqual(len(self.r['stage5_under_stronger_annular_envelope']),12)
 def test_z_is_not_opposite_face_clearance(self):
  z=self.r['conditional_Z'];self.assertLess(z['female_tail_tip_range_mm'][0],z['GH_reference_body_z_mm'][1]);self.assertEqual(self.r['rebudget']['counts'],[225,240,270]);self.assertGreaterEqual(self.r['rebudget']['minimum_wire_slack_mm'],10)
if __name__=='__main__':unittest.main()
