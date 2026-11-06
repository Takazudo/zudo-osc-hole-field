import copy,json,unittest
import stage8_mechanical as m
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.build()
 def test_complete_packages(self):
  self.assertEqual(len(self.r['placements']),56);self.assertEqual(sum(bool(p['panel_uid'])for p in self.r['placements'].values()),7);self.assertEqual(sum(len(p['units'])for p in self.r['placements'].values()),76)
 def test_fixed_move_rejected(self):
  p=json.loads((m.OUT/'placement-input.json').read_text());s=json.loads((m.OUT/'mechanical-input.json').read_text());p['translations_from_stage7_mm']['J809']=[1,0]
  with self.assertRaisesRegex(AssertionError,'fixed'):m.build_from(p,s)
 def test_identified_exact_minima(self):
  widths=[r['width_mm']for r in self.r['identified_ligaments']];self.assertTrue(any(abs(v-.42)<1e-6 for v in widths));self.assertTrue(any(abs(v-.54)<1e-6 for v in widths))
 def test_no_fabricated_acceptance(self):
  self.assertFalse(self.r['physical_acceptance']);self.assertEqual(self.r['qualified_free_regions'],[]);self.assertTrue(self.r['rejected_straight_carrier_hardware_projections'])
 def test_routed_carrier_avoids_known_hardware(self):
  self.assertEqual(self.r['carrier_hardware_projections'],[]);self.assertEqual(self.r['anchor_hardware_projections'],[]);self.assertEqual(len(self.r['carrier_routed_members']),6);self.assertTrue(all('centreline_mm'in r for r in self.r['carrier_routed_members']))
 def test_router_bounds_enclose_cutouts(self):
  for a,b in zip(self.r['removed_rectangles'],self.r['manufacturing_sweep_bounds']):self.assertTrue(m.a.inside(a['box_mm'],b['box_mm']))
 def test_actual_pad_screen_distinguishes_courtyard(self):
  rows=[p for p in self.r['actual_pad_cut_margins']if p['fixed']and p['ref']in ['J809','J909','J1009']and p['pin']in ['S','T']]
  self.assertEqual(len(rows),6)
  for p in rows:self.assertAlmostEqual(p['minimum_cut_boundary_gap_mm'],.32);self.assertNotEqual(p['classification'],'CUT_INTERSECTS_PAD')
 def test_actual_manufacturing_topology_connected(self):
  self.assertTrue(all(x['connected_components']==1 for x in self.r['substrate_topology'].values()))
 def test_source_process_tolerance_fails_closed(self):
  p=json.loads((m.OUT/'placement-input.json').read_text());s=json.loads((m.OUT/'mechanical-input.json').read_text());s['tool_path_tolerance_mm']=.01
  with self.assertRaises(AssertionError):m.build_from(p,s)
 def test_structural_frame_planning_comparison(self):
  self.assertTrue(all(not r['planning_pass']for r in self.r['carrier_beam_planning']if r['rib_depth_mm']==2))
  self.assertTrue(all(r['planning_pass']and r['full_path_planning_pass']for r in self.r['carrier_beam_planning']if r['rib_depth_mm']==17))
 def test_clamp_stack_and_thread_engagement(self):
  q=self.r['carrier_proposal']['mount_stack'];self.assertEqual(q['boss_z_mm'][1],q['spacer_z_mm'][0]);self.assertEqual(q['spacer_z_mm'][1],q['PCB_z_mm'][0]);self.assertAlmostEqual(q['screw_underhead_length_mm']-(q['PCB_z_mm'][1]-q['PCB_z_mm'][0])-(q['spacer_z_mm'][1]-q['spacer_z_mm'][0]),q['thread_engagement_mm'])
 def test_all_actual_pads_clear_requested_edge(self):
  self.assertTrue(all(p['minimum_cut_boundary_gap_mm']>=.25 for p in self.r['actual_pad_cut_margins']))
  self.assertTrue(any(p['minimum_cut_boundary_gap_mm']<0 for p in self.r['standard_process_pad_margins']))
 def test_rotated_bypass_pin_identity(self):
  p=self.r['placements']['C3308'];seed=json.loads((m.a.OUT/'stage7/mechanical-report.json').read_text())['placements']['C3308'];self.assertEqual(p['pins'],seed['pins']);self.assertEqual(p['quarter_turn'],(seed['quarter_turn']+2)%4)
 def test_actual_service_force_sites(self):
  rows=self.r['actual_force_application_routes'];self.assertEqual(sum('GH insertion'in r['role']for r in rows),4);self.assertTrue(all('application_xy_mm'in r for r in rows));self.assertTrue(all(r['conditional_force_for_half_mm_deflection_N']>0 for r in rows if 'conditional_force_for_half_mm_deflection_N'in r))
 def test_force_strips_exclude_own_and_mount_perforations(self):
  for row in self.r['actual_force_application_routes']:
   if 'route_mm'not in row:continue
   holes=[b for p in self.r['placements'].values()if p['board']==row['board']for b in p['through_pad_keepouts_mm']]
   holes +=[m.expand([*q['centre_mm'],*q['centre_mm']],q['hole_diameter_mm']/2)for q in self.r['mounts']if q['board']==row['board']]
   self.assertFalse(any(m.locality.hit(a,b,m.expand(h,.5))for a,b in zip(row['route_mm'],row['route_mm'][1:])for h in holes),row['ref'])
   mount=next(q for q in self.r['mounts']if q['id']==row['mount']);self.assertAlmostEqual(__import__('math').dist(row['route_mm'][-1],mount['centre_mm']),2)
if __name__=='__main__':unittest.main()
