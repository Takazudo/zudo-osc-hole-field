import unittest,copy,json
import stage9_support as s
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=s.build()
 def test_full_source_population(self):
  self.assertEqual(len(self.r['placements']),56);self.assertEqual(sum(len(p['units'])for p in self.r['placements'].values()),76);self.assertEqual(sum(bool(p['panel_uid'])for p in self.r['placements'].values()),7)
 def test_explicit_terminal_inventory(self):
  self.assertEqual(len(self.r['terminal_extensions']),15);self.assertEqual(len(self.r['terminal_lands']),15);self.assertEqual(len(self.r['LED_wire_lands']),6);self.assertEqual(len(self.r['retained_NC_terminals']),3);self.assertEqual(self.r['added_mating_interfaces'],0)
 def test_no_foreign_pin_apertures_on_main_boards(self):
  self.assertEqual(len(self.r['continuous_boards']),2);self.assertTrue(all(p['conditional_pad_depth_mm']in(35,36.6)for p in self.r['placements'].values()if not p['panel_uid']))
 def test_LED_supported_with_ordinary_edge_budget(self):
  self.assertEqual(len(self.r['LED_islands']),3);self.assertTrue(all(p['minimum_edge_mm']>=.25 for p in self.r['LED_wire_lands']))
 def test_unknowns_not_fit_claim(self):
  self.assertFalse(self.r['physical_acceptance']);self.assertEqual(self.r['qualified_free_regions'],[]);self.assertTrue(self.r['neighbor_hardware_projections'])
 def test_modeled_exclusions_fail_closed(self):
  self.assertTrue(all(not v for v in self.r['source_checks'].values()))
 def test_all_wire_routes_and_service_slack(self):
  self.assertEqual(len(self.r['inherited_service_wire_checks']),15)
  self.assertTrue(all(r['minimum_proxy_slack_mm']>=10 for r in self.r['inherited_service_wire_checks']))
  self.assertTrue(all(r['minimum_proposed_route_slack_mm']>=10 for r in self.r['terminal_extensions']))
 def test_guides_remove_carrier_material(self):
  self.assertTrue(self.r['carrier_wire_guides']);self.assertTrue(all(b['net_section_stress_MPa']<=80 for b in self.r['backing_paths']))
 def mutate(self,fn):
  spec=json.loads((s.OUT/'support-input.json').read_text());fn(spec)
  with self.assertRaises(AssertionError):s.build(spec)
 def test_reject_precision_island_shortcut(self):self.mutate(lambda x:x['LED_island'].update(ordinary_outline_boundary_allowance_mm=.05))
 def test_reject_small_island(self):self.mutate(lambda x:x['LED_island'].update(size_mm=[5,5]))
 def test_reject_short_terminal_wire(self):self.mutate(lambda x:x['terminal_wire'].update(nominal_mm=10))
 def test_reject_DIN_window_collision(self):self.mutate(lambda x:x['service_headers'].update(front_J_PWR_origin_mm=[142.55,159]))
 def test_reject_blocked_frame(self):self.mutate(lambda x:x['backing'].update(rib_width_mm=30))
 def test_reject_omitted_guide_allowance(self):self.mutate(lambda x:x['backing']['wire_guide_process'].update(radial_position_allowance_mm=0))
if __name__=='__main__':unittest.main()
