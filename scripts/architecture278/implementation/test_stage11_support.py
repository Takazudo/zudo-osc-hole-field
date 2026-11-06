import copy,json,unittest
import stage11_support as s
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.spec=json.loads((s.OUT/'support-input.json').read_text());cls.result=s.build()
 def reject(self,path,value):
  q=copy.deepcopy(self.spec);v=q
  for k in path[:-1]:v=v[k]
  v[path[-1]]=value
  with self.assertRaises(ValueError):s.build(q)
 def test_no_physical_acceptance(self):self.assertFalse(self.result['physical_acceptance']);self.assertFalse(self.result['strength_qualified'])
 def test_thin_control_rail(self):self.reject(['control_rail_depth_mm'],2)
 def test_old_rear_width(self):self.reject(['rear_crossmember_width_mm'],4)
 def test_old_hole_cannot_take_sleeve(self):self.reject(['fasteners','PCB_M2p5_drill_mm'],2.7)
 def test_large_hole_edge(self):self.reject(['fasteners','PCB_M2p5_drill_mm'],6)
 def test_sleeve_wall(self):self.reject(['fasteners','PCB_sleeve_ID_mm'],3.3)
 def test_sleeve_bore(self):self.reject(['fasteners','PCB_sleeve_ID_mm'],2.5)
 def test_capture_shaft_hole(self):self.reject(['cradle_front_hole_diameter_mm'],5)
 def test_tail_relief(self):self.reject(['mount_tail_relief_diameter_mm'],2.4)
 def test_rear_shaft_relief(self):self.reject(['rear_shaft_relief_diameter_mm'],2)
 def test_bridge_cut(self):self.reject(['cradle_rear_bridge_height_y_mm'],4)
 def test_feed_net_identity(self):self.reject(['feed','nets'],['AGND','-12V','+12V'])
 def test_lane_spacing(self):self.reject(['feed','stud_x_mm'],[250,257,284])
 def test_length_budget(self):self.reject(['feed','maximum_developed_mm'],30)
 def test_bend_geometry(self):self.reject(['feed','bend_radius_mm'],12)
 def test_stud_hits_header(self):self.reject(['feed','stud_y_mm'],150)
 def test_revised_anchors(self):self.assertEqual(self.result['refined_frames']['control']['anchors_mm'],[[300,310],[315,310]])
 def test_failed_long_rails_retained(self):self.assertEqual(sum(not m['within_named_screen']for m in self.result['member_sensitivities']),4)
 def test_radius_and_service(self):
  r=self.result['low_R_feed_option'];self.assertEqual(r['straps'][0]['radius_datum'],'centreline');self.assertAlmostEqual(r['straps'][0]['bend_strain_geometric_outer_fibre_sensitivity'],1/6);self.assertEqual(r['side_opening_requirement']['external_space_beyond_reference_mm'],20)
 def test_unknown_pocket_not_free(self):self.assertLess(self.result['pot_capture_assemblies'][0]['guaranteed_pocket_clearance_before_unknown_body_tolerance_mm'],0)
if __name__=='__main__':unittest.main()
