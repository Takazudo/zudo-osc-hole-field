import copy,json,unittest
import stage11_electrical as e
class TestElectrical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=[json.loads(p.read_text())for p in [e.OUT/'electrical-input.json',e.prior.OUT/'inventory-report.json',e.prior.OUT/'interfaces-report.json',e.prior.OUT/'electrical-report.json']]
 def test_inventory(self):
  r=e.analyze(*self.data);self.assertEqual(len(r['power_endpoint_comparison']),106);self.assertFalse(r['hardware_acceptance'])
 def test_midpoint(self):
  p=e.wiper(.5,1e5,-5,5);self.assertEqual(p['sense_V'],0);self.assertEqual(p['thevenin_ohm'],25000)
 def test_position_correlation(self):
  p=e.wiper(1,1e5,-5,5);self.assertEqual(p['thevenin_ohm'],0);self.assertAlmostEqual(p['sense_V'],5e7/10001000)
 def test_current_conservation(self):
  for x in (0,.2,.5,.8,1):
   p=e.wiper(x,1e5,-5,5);self.assertAlmostEqual(p['high_endpoint_A']-p['low_endpoint_sink_A'],p['load_A'])
 def test_strap(self):
  r=e.analyze(*self.data);self.assertAlmostEqual(r['lowR_comparison']['bulk_at_temperature_ohm'],.00019950128)
 def test_no_false_power_pass(self):
  r=e.analyze(*self.data);self.assertTrue(all(p['actual_complete_resistance_ohm']is None for p in r['power_endpoint_comparison']))
 def test_pin_mutation(self):
  d=copy.deepcopy(self.data);d[1]['packages']['R7119']['pins']['1']='AGND'
  with self.assertRaisesRegex(ValueError,'net binding'):e.analyze(*d)
 def test_value_mutation(self):
  d=copy.deepcopy(self.data);d[1]['packages']['RV1308']['unit_records'][0]['value']='B103'
  with self.assertRaisesRegex(ValueError,'source value'):e.analyze(*d)
 def test_limit_mutation(self):
  d=copy.deepcopy(self.data);d[0]['return_limit_ohm']=.1
  with self.assertRaises(ValueError):e.analyze(*d)
 def test_sharing_mutation(self):
  d=copy.deepcopy(self.data);d[0]['equal_sharing_credit']=True
  with self.assertRaises(ValueError):e.analyze(*d)
 def test_nonfinite(self):
  d=copy.deepcopy(self.data);d[0]['strap']['width_mm']=float('nan')
  with self.assertRaises(ValueError):e.analyze(*d)
 def test_missing_endpoint(self):
  d=copy.deepcopy(self.data);d[3]['power_and_return_endpoint_paths'].pop()
  with self.assertRaises(ValueError):e.analyze(*d)
 def test_duplicate_endpoint(self):
  d=copy.deepcopy(self.data);d[3]['power_and_return_endpoint_paths'][1]=d[3]['power_and_return_endpoint_paths'][0]
  with self.assertRaises(ValueError):e.analyze(*d)
 def test_operating_case_no_cancellation(self):
  c=e.operating_case(-5,.5,5,.5,.0005)
  self.assertGreater(c['AGND_magnitude_envelope_subtotal_A'],.0012)
  self.assertAlmostEqual(c['return_shift_subtotal_V'],sum(c['terms_A'].values())*.0005)
 def test_candidate_tolerance(self):
  x=json.loads((e.OUT/'identity-report.json').read_text());r=e.tolerance_sensitivity(x)
  self.assertGreater(r['offset']['output_error_V'],0)
  self.assertAlmostEqual(r['REFN5_inverting_gain']['max_abs_error_from_minus5_V'],5*((1.001/.999)-1))
  x['candidate_assignments']['R7119']['candidate_ratings']['value_SI']=100
  with self.assertRaises(ValueError):e.tolerance_sensitivity(x)
 def test_complete_feed(self):
  r=e.analyze(*self.data);support=json.loads((e.OUT/'support-report.json').read_text());e.feed_alternative(r,support,self.data[2],self.data[3])
  self.assertEqual(len(r['lowR_complete_endpoint_paths'])+len(r['lowR_unmodified_front_endpoint_targets']),106)
  for row in r['lowR_complete_endpoint_paths']:
   self.assertEqual(len(row['new_segments']),3);self.assertEqual(row['new_segments'][1]['joints'],2)
   self.assertIsNone(row['complete_source_to_pad_resistance_ohm'])
 def test_wrong_strap_net(self):
  r=e.analyze(*self.data);support=json.loads((e.OUT/'support-report.json').read_text());support['low_R_feed_option']['straps'][0]['net']='AGND'
  with self.assertRaises(ValueError):e.feed_alternative(r,support,self.data[2],self.data[3])
 def test_strap_overbudget(self):
  r=e.analyze(*self.data);support=json.loads((e.OUT/'support-report.json').read_text());support['low_R_feed_option']['straps'][0]['developed_centerline_mm']=101
  with self.assertRaises(ValueError):e.feed_alternative(r,support,self.data[2],self.data[3])
 def test_broken_feed_suffix(self):
  d=copy.deepcopy(self.data);r=e.analyze(*d);support=json.loads((e.OUT/'support-report.json').read_text())
  target=next(x['to']for x in r['power_endpoint_comparison']if x['candidate_core_strap_replaces_K_PWR_branch'])
  original=next(x for x in d[3]['power_and_return_endpoint_paths']if x['to']==target)
  original['edge_indices']=[]
  with self.assertRaises(ValueError):e.feed_alternative(r,support,d[2],d[3])
if __name__=='__main__':unittest.main()
