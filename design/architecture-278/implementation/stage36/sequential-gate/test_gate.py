import math,unittest
import gate
class Gate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.a=gate.run()
 def test_constant_length_continuous_extrema(self):
  a=self.a['continuous'];Z=a['top_z_mm'][0];D=math.hypot(64,23)
  for t in [0,.123,3,7.49,11,15]:
   z=gate.s.exact_top(149,D,43.9+t,57.3,12,14.6)
   self.assertAlmostEqual(z,Z+t/2,places=5)
   self.assertGreaterEqual(z-12-43.9-t,a['local_straight_mm'][1]-1e-5)
 def test_no_double_budget_credit(self):
  setting=.5;lag=.25
  self.assertEqual(setting+2*lag,1)
  self.assertGreater(setting,self.a['open_span']['necessary_max_total_residual_mm_for_middle_board_only'])
 def test_failed_screen_reproduces_previous(self):
  x=self.a['open_span'];self.assertAlmostEqual(x['historical_stage35_bound_mm'],x['recomputed_same_bound_mm'],places=10)
  self.assertGreater(x['K4_deficit_mm'],0)
  self.assertTrue(x['not_a_global_slack_pass'])
 def test_conservative_continuous_ellipse_nesting(self):
  A0=43.9;B=74.805617;delta=.5
  for t in [0,.3,5,15]:
   lo=A0+t;mid=(lo+B)/2;major=(B-lo+delta)/2;minor=math.sqrt(major**2-((B-lo)/2)**2)
   for i in range(101):
    th=2*math.pi*i/100;x=minor*math.cos(th);z=mid+major*math.sin(th)
    self.assertLessEqual(math.hypot(x,z-A0)+math.hypot(x,z-B),B-A0+delta+1e-10)
 def test_missing_geometry_stays_missing(self):
  self.assertIsNone(self.a['latch']['maximum_certified_envelope_mm'])
  self.assertIsNone(self.a['sleeve']['maximum_certified_opening_travel_mm'])
  self.assertFalse(self.a['support_handoff']['housing_crimp_structural_credit'])
  self.assertEqual(self.a['planning_angle_deg'],15)
  self.assertEqual(self.a['verdict'],'UNKNOWN_NOT_SOURCE_FEASIBLE_HARD_STOP')
if __name__=='__main__':unittest.main()
