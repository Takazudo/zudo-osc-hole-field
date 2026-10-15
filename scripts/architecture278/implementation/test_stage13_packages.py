import copy,json,unittest
import stage13_packages as s
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.spec=json.loads((s.OUT/'package-input.json').read_text());cls.prior=json.loads((s.a.OUT/'stage10/mechanical-report.json').read_text());cls.r=s.analyze(cls.spec,cls.prior)
 def reject(self,fn):
  q=copy.deepcopy(self.spec);fn(q)
  with self.assertRaises(ValueError):s.analyze(q,self.prior)
 def test_population(self):self.assertEqual(len(self.r['placements']),90);self.assertTrue(self.r['conservation']['C7107_unchanged'])
 def test_only_two_changed(self):self.assertEqual([r for r,p in self.r['placements'].items()if p!=self.prior['placements'][r]],['C7101','C7102'])
 def test_polarity(self):
  a=self.r['placements']['C7101'];b=self.r['placements']['C7102'];self.assertGreater(a['pads_mm']['1'][0][0],a['pads_mm']['2'][0][0]);self.assertLess(b['pads_mm']['1'][0][0],b['pads_mm']['2'][0][0])
 def test_net_mutation(self):self.reject(lambda q:q['overlays']['C7101']['pins'].update({'1':'AGND'}))
 def test_unit_mutation(self):self.reject(lambda q:q['overlays']['C7101'].update(units=[]))
 def test_other_board(self):self.reject(lambda q:q['overlays']['C7101'].update(board='A01-jack'))
 def test_wrong_depth(self):self.reject(lambda q:q['overlays']['C7101'].update(pad_depth_mm=69.2))
 def test_package_collision(self):self.reject(lambda q:q['overlays']['C7101'].update(origin_mm=[251.5,197]))
 def test_edge(self):self.reject(lambda q:q['overlays']['C7101'].update(origin_mm=[237,190]))
 def test_hole(self):self.reject(lambda q:q['overlays']['C7101'].update(origin_mm=[240,178]))
 def test_DIN(self):self.reject(lambda q:q['overlays']['C7101'].update(origin_mm=[299,228]))
 def test_handle(self):self.reject(lambda q:q['overlays']['C7101'].update(origin_mm=[270,178]))
 def test_land_outside(self):self.reject(lambda q:q['overlays']['C7101']['geometry']['pad_sizes_mm'].update({'1':[10,10]}))
 def test_body_height(self):self.reject(lambda q:q['overlays']['C7101']['geometry'].update(body_max_mm=[6.3,3.5,7]))
 def test_primary_geometry_mutation(self):self.reject(lambda q:q['overlays']['C7101']['geometry'].update(evidence_sha256='0'*64))
 def test_unknown_MPN(self):self.reject(lambda q:q['overlays']['C7101'].update(candidate_MPN='unselected'))
 def test_invalidation_and_inventory(self):
  r=s.build();self.assertEqual(r['conservation']['source_units'],118);self.assertEqual(len(r['endpoint_delta_and_invalidation']['changed_source_pads']),4);self.assertIsNone(r['endpoint_delta_and_invalidation']['current_overlay_complete_path_metrics']);self.assertEqual(len(r['other_function_projection_reservations']),8)
 def test_actual_source_paths(self):
  self.assertEqual(len(self.r['local_reference_pad_paths']),6)
  for p in self.r['local_reference_pad_paths']:self.assertIn(p['to'],['U7101:2','U7101:4','U7101:6']);self.assertGreater(p['after_straight_floor_mm'],0)
if __name__=='__main__':unittest.main()
