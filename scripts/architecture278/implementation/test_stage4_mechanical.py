import json,unittest
import stage4_occupied as occupied
import stage4_mechanical as mechanical
class Stage4MechanicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.i=occupied.build();cls.m=mechanical.build()
 def test_complete_whole_units(self):
  ledger=json.loads((occupied.ROOT/'design/architecture-278/source-ledger.json').read_text());units=ledger['package_units'];self.assertEqual(self.i['package_count'],4809);self.assertEqual(self.i['unit_count'],6796)
  for p in self.i['rows']:
   source=[units[i]for i in p['unit_pin_record_indices']];self.assertEqual({u['ref']for u in source},{p['ref']});self.assertEqual(set(p['units']),{u['unit']for u in source})
 def test_unknown_is_not_free(self):
  for p in self.i['rows']:
   self.assertIsNone(p['new_candidate_occupied_solid'])
   if p['population_group']!='OCTAVE_REF':self.assertIsNone(p['new_candidate_placement'])
 def test_shared_rigid_whole_group(self):
  a=json.loads((occupied.ROOT/'design/architecture-278/implementation/assembly-report.json').read_text());old={p['ref']:p for p in a['shared_middle_placements']};rows=[p for p in self.i['rows']if p['population_group']=='OCTAVE_REF'];self.assertEqual(len(rows),30)
  for p in rows:
   q=p['new_candidate_placement'];o=old[p['ref']]
   for pin,points in o['pads_mm'].items():self.assertEqual(q['pads_mm'][pin],[[x+6,y]for x,y in points])
  self.assertEqual(self.m['shared_group']['same_face_DIN_conflicts'],[])
 def test_retained_coordinates_dependency(self):
  r=self.m['retained_K_XY_interpretation'];self.assertEqual(r['package_count'],2585);self.assertEqual(r['intersecting_unique_packages'],1744);self.assertEqual(len(r['all_K_bearing_other_functions']),24)
 def test_connector_exclusions_not_clearance(self):
  r=self.m['connector'];self.assertEqual(r['DIN_contact_count'],480);self.assertEqual(r['middle_header_count'],85);self.assertEqual(len(r['minimum_tail_or_center_GH_land_exclusions']),7);self.assertIsNone(r['drill_mm']);self.assertIsNone(r['flange_hole_coordinates'])
 def test_rotated_tail_does_not_use_unsafe_square(self):
  # At45 degrees a .29-square corner can exceed the short half-width.
  self.assertFalse(mechanical.tail_circle_overlap(0,0,[.13,.13,.2,.2]))
  self.assertTrue(mechanical.tail_circle_overlap(0,0,[.1,.1,.2,.2]))
 def test_two_grips_not_one(self):
  r=self.m['service'];self.assertEqual(len(r['grips']),2);self.assertEqual(r['same_card_finger_gap_mm'],2);self.assertEqual(r['adjacent_card_finger_gap_mm'],4)
if __name__=='__main__':unittest.main()
