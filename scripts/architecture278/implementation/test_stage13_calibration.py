import copy,json,unittest
import stage13_calibration as c
class CalibrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=[json.loads(p.read_text())for p in [c.OUT/'calibration-input.json',c.prior.OUT/'budget-report.json',c.prior.old.prior.OUT/'inventory-report.json']]
 def test_complete(self):
  r=c.analyze(*self.data);self.assertEqual(len(r['cases']),11);self.assertEqual(r['observability']['generic_control_rank'],2);self.assertIsNone(r['load_criterion_met'])
 def test_actual_bounds(self):
  for g in (-1,0,1):
   r=c.check_case({},g)
   for key in ('atten_setting','offset_setting'):self.assertGreaterEqual(r[key]['setting'],0);self.assertLessEqual(r[key]['setting'],1)
 def test_nominal_positive_endpoint_unreachable(self):
  r=c.check_case({},1);self.assertFalse(r['atten_setting']['reachable']);self.assertEqual(r['atten_setting']['setting'],1)
 def test_zero_gain_preset(self):
  r=c.check_case({},0);self.assertTrue(r['atten_setting']['reachable']);self.assertAlmostEqual(r['observed_coefficients']['IN_gain'],0);self.assertAlmostEqual(r['observed_coefficients']['offset_V'],0)
 def test_hidden_CV_gain_not_removed(self):
  r=c.check_case({'gcv':1.004},0);self.assertAlmostEqual(r['CV_only_residual_at5V'],.020);self.assertGreater(r['maximum_abs_DC_model_residual_V'],.002)
 def test_fit_is_not_hardware(self):
  r=c.check_case({'gcv':1.004},0);self.assertEqual(r['mathematical_fit']['mathematical_model_residual_V'],0);self.assertFalse(r['mathematical_fit']['realized_in_hardware']);self.assertGreater(r['CV_only_residual_at5V'],.001)
 def test_load_never_zero_assumed(self):
  r=c.check_case({},0);self.assertIsNone(r['load_criterion_met']);self.assertTrue(all(x['output_load_change_V']is None for x in r['residuals']))
 def test_moving_user_control_loses_preset(self):
  r=c.check_case({},0);x=r['offset_setting']['setting'];self.assertNotAlmostEqual(c.observe({},.75,x)['IN_gain'],r['observed_coefficients']['IN_gain'])
 def test_unreachable_setting(self):
  r=c.bounded_setting(lambda x:2*x-1,2);self.assertFalse(r['reachable']);self.assertEqual(r['setting'],1)
 def test_saturation_not_accepted(self):
  r=c.analyze(*self.data);over=[x for x in r['saturation_cases']if x['over_supply_rail']];self.assertTrue(over);self.assertTrue(all(x['hardware_output_V']is None for x in over))
 def test_hardware_promotion_rejected(self):
  d=copy.deepcopy(self.data);d[0]['fitted_correction_is_hardware']=True
  with self.assertRaises(ValueError):c.analyze(*d)
 def test_new_control_rejected(self):
  d=copy.deepcopy(self.data);d[0]['actual_controls']['TRIM']='new'
  with self.assertRaises(ValueError):c.analyze(*d)
 def test_hidden_physical_corner_mutation(self):
  d=copy.deepcopy(self.data);d[1]['coherent_physical_resistor_corners'][0]['minimum_error']['physical_resistor_fraction']['R7124']=.1
  with self.assertRaises(ValueError):c.analyze(*d)
 def test_coupled_intercept(self):
  params={'errors':{'IN_buffer':.0001,'remote_buffer':.0001,'manual_amp':.0001}}
  J=c.control_sensitivity(params,.5,.5);self.assertGreater(J[2][0],0)
  eps=1e-5;left=c.observe(params,.5-eps,.5);right=c.observe(params,.5+eps,.5)
  self.assertAlmostEqual((right['offset_V']-left['offset_V'])/(2*eps),J[2][0],places=9)
  preset=c.check_case(params,0);self.assertTrue(preset['offset_setting']['reachable']);self.assertAlmostEqual(preset['observed_coefficients']['offset_V'],0)
 def test_unreachable_offset(self):
  r=c.check_case({'errors':{'output':6}},0);self.assertFalse(r['offset_setting']['reachable']);self.assertEqual(r['offset_setting']['setting'],0);self.assertGreater(r['observed_coefficients']['offset_V'],1)
if __name__=='__main__':unittest.main()
