import unittest,json,copy
import stage10_mechanical as m
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.build();cls.spec=json.loads((m.OUT/'mechanical-input.json').read_text())
 def test_conservation(self):
  self.assertEqual(len(self.r['placements']),90);self.assertEqual(sum(len(p['units'])for p in self.r['placements'].values()),118);self.assertEqual(sum(len(p['pins'])for p in self.r['placements'].values()),285)
 def test_bypass_whole_owner(self):
  self.assertEqual(len(self.r['bypass_associations']),17)
  for b in self.r['bypass_associations']:self.assertEqual(self.r['placements'][b['capacitor']]['board'],self.r['placements'][b['target']]['board'])
 def test_all_modeled_exclusions(self):self.assertTrue(all(not v for v in self.r['source_checks'].values()))
 def test_exact_DIN_registration(self):
  self.assertEqual(len(self.r['DIN_contacts']),96)
  for pin,pts in self.r['din_connectors']['middle']['pads_xyz_mm'].items():self.assertEqual(pts[0][:2],self.r['din_connectors']['rear']['pads_xyz_mm'][pin][0][:2])
 def test_actual_LED_support_and_tails(self):self.assertEqual(len(self.r['LED_wire_lands']),8);self.assertEqual(len(self.r['terminal_extensions']),14);self.assertEqual(len(self.r['retained_NC_terminals']),3)
 def test_pot_source_datum(self):
  self.assertTrue(self.r['pot_datum']['bushingless']);self.assertEqual(self.r['pot_datum']['shaft_projection_past_panel_front_mm'],8);self.assertEqual(len(self.r['pot_rearshaft_relief_holes']),2)
 def test_all_middle_physical_host(self):self.assertIn('A01-middle',self.r['boards']);self.assertEqual(sum(m['board']=='A01-middle'for m in self.r['mounts']),4)
 def test_tool_access_not_claimed(self):self.assertTrue(self.r['installed_tool_board_blockers']);self.assertFalse(self.r['physical_acceptance']);self.assertTrue(self.r['historical_other_function_projections'])
 def mutation(self,fn):
  spec=copy.deepcopy(self.spec);fn(spec)
  with self.assertRaises(AssertionError):m.build(spec)
 def test_fixed_XY_mutation(self):self.mutation(lambda s:s['positions']['RV1307'].update(origin_mm=[219,269]))
 def test_missing_package(self):self.mutation(lambda s:s['positions'].pop('U7104'))
 def test_DIN_turn_mutation(self):self.mutation(lambda s:s.update(DIN_turn_deg=90))
 def test_precision_shortcut_mutation(self):self.mutation(lambda s:s.update(ordinary_boundary_allowance_mm=.05))
 def test_release_notch_mutation(self):self.mutation(lambda s:s.update(middle_access_edge_notches_mm=[]))
 def test_mount_over_package(self):self.mutation(lambda s:s['boards']['A01-jack']['mounts_mm'].__setitem__(0,s['positions']['U7102']['origin_mm']))
 def test_wrong_fixed_terminal_Z(self):self.mutation(lambda s:s.update(fixed_jack_LED_pad_z_proposal_mm=35))
if __name__=='__main__':unittest.main()
