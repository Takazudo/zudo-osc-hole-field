import json,unittest,math,copy
import stage5_mechanical as m
class Stage5MechanicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.build()
 def test_whole_header_coverage(self):
  self.assertEqual(self.r['header_count'],85);self.assertEqual(self.r['contact_hole_count'],480);self.assertEqual(self.r['flange_hole_count'],10);self.assertEqual(len(self.r['moves']),8)
 def test_repair_does_not_claim_solids(self):
  for k in ['drill_envelope_land_exclusions','same_face_header_courtyard_conflicts','shared_rear_courtyard_hole_conflicts']:self.assertEqual(self.r[k],[])
  self.assertEqual(len(self.r['opposite_face_GH_courtyard_hole_projections_UNKNOWN']),12)
 def test_official_exact_parts_and_unknown_pad(self):
  e=json.loads((m.OUT/'din-evidence.json').read_text());self.assertEqual([s['mpn']for s in e['sources'][:2]],['09032966824','09031966922']);self.assertTrue(all(not s['restricted']for s in e['sources'][:2]));self.assertIsNone(e['copper_annular_pad_diameter_mm'])
 def test_larger_drill_not_tail_only(self):
  self.assertFalse(m.tail_circle_overlap(0,0,[.4,-.1,.6,.1],.145));self.assertTrue(m.tail_circle_overlap(0,0,[.4,-.1,.6,.1],.575))
 def test_angle_mutation_fails_closed(self):
  e=json.loads((m.OUT/'din-evidence.json').read_text());c={'connector_turn_deg':90}
  with self.assertRaisesRegex(AssertionError,'rotation datum'):m.contact_envelopes(c,e)
 def test_drill_evidence_mutation_recomputes(self):
  e=json.loads((m.OUT/'din-evidence.json').read_text());c={'connector_turn_deg':180,'origins_mm':{'O1':[2,45]},'connector_centre_mm':[8,105]}
  old=m.contact_envelopes(c,e);e['contact_drill_diameter_mm'][1]+=0.2;new=m.contact_envelopes(c,e)
  self.assertAlmostEqual(new[0][2]-old[0][2],.1)
  e['female_flange_hole_diameter_mm'][1]+=0.2;newer=m.contact_envelopes(c,e)
  self.assertAlmostEqual(newer[-1][2]-new[-1][2],.1)
 def test_wire_service_budget_preserved(self):
  self.assertGreaterEqual(self.r['rebudget']['minimum_wire_slack_mm'],10);self.assertEqual(self.r['overlength_count'],38)
if __name__=='__main__':unittest.main()
