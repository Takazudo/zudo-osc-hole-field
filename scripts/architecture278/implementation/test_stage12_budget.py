import copy,json,unittest
import stage12_budget as b
class BudgetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=[json.loads(p.read_text())for p in [b.OUT/'budget-input.json',b.old.prior.OUT/'inventory-report.json',b.old.prior.OUT/'interfaces-report.json',b.old.prior.OUT/'electrical-report.json',b.ROOT/'design/standard/electrical-standard.json',b.ROOT/'design/partition/partition-input.json']]
 def test_complete(self):
  r=b.build_report(*self.data);self.assertEqual(len(r['resistance_endpoint_mapping']),106);self.assertEqual(len(r['coherent_DC_cases']),225);self.assertIsNone(r['complete_error_bound_V'])
 def test_offset_coefficients_against_transfer(self):
  for a,x in [(0,0),(.25,.75),(.5,.5),(1,1)]:
   base=b.transfer(2,1,a,x)['out_V']
   for name,c in b.coefficients(a,x).items():
    shifted=b.transfer(2,1,a,x,errors={name:.0001})['out_V'];self.assertAlmostEqual((shifted-base)/.0001,c,places=9)
 def test_summer_noise_gain(self):self.assertEqual(b.coefficients(.5,.5)['summer'],-4)
 def test_reference_correlation(self):
  c=b.coefficients(.5,.5);self.assertEqual(c['REF_positive'],0);self.assertGreater(c['REF_negative'],.99)
 def test_nominal_matches_prior(self):
  for a,x in [(0,0),(.2,.8),(.5,.5),(1,1)]:
   expected=b.old.operating_case(5,x,-5,a,.0005)['out_ideal_loaded_V'];self.assertAlmostEqual(b.transfer(5,-5,a,x)['out_V'],expected)
 def test_unknown_domain_rejected(self):
  with self.assertRaises(ValueError):b.edge_domains('invented_copper')
 def test_GH_domains_separate(self):self.assertEqual(b.edge_domains('GH_harness'),['wire','crimp_termination','GH_mated_contact','GH_header_pin_termination'])
 def test_no_endpoint_omission(self):
  d=copy.deepcopy(self.data);d[3]['power_and_return_endpoint_paths'].pop()
  with self.assertRaises(ValueError):b.build_report(*d)
 def test_net_mutation(self):
  d=copy.deepcopy(self.data);row=d[3]['power_and_return_endpoint_paths'][0];d[2]['edges'][row['edge_indices'][0]]['net']='bad'
  with self.assertRaises(ValueError):b.build_report(*d)
 def test_limit_domain_preserved(self):
  d=copy.deepcopy(self.data);d[5]['load_distribution']['return_plane_resistance_ceiling_ohm']=.1
  with self.assertRaises(ValueError):b.build_report(*d)
 def test_new_acceptance_rejected(self):
  d=copy.deepcopy(self.data);d[0]['new_criteria_approved']=True
  with self.assertRaises(ValueError):b.build_report(*d)
 def test_nonfinite_transfer(self):
  with self.assertRaises(ValueError):b.transfer(float('nan'),0,.5,.5)
 def test_physical_resistor_corners(self):
  rows=b.resistor_corner_cases(self.data[1]);self.assertEqual(len(rows),5)
  for r in rows:
   self.assertEqual(r['physical_corner_count'],1024)
   self.assertEqual(len(r['maximum_error']['physical_resistor_fraction']),10)
   self.assertLessEqual(r['minimum_error']['error_V'],r['maximum_error']['error_V'])
 def test_no_borrowed_timing_or_pitch_acceptance(self):
  r=b.criteria(self.data[4],self.data[5],self.data[0]);self.assertIsNone(r['timing']['A01_settling_target_s']);self.assertIn('NOT ESTABLISHED',r['pitch']['A01_pitch_acceptance'])
 def test_resistor_identity_mutation(self):
  inv=copy.deepcopy(self.data[1]);inv['packages']['R7124']['attributes']['MPN']='other'
  with self.assertRaises(ValueError):b.resistor_corner_cases(inv)
 def test_criteria_note_mutation(self):
  d=copy.deepcopy(self.data);cell=next(c for c in d[4]['cells']if c['id']=='bipolar_attenuverter');cell['notes']=[]
  with self.assertRaises(ValueError):b.criteria(d[4],d[5],d[0])
 def test_warmup_mutation(self):
  d=copy.deepcopy(self.data);d[4]['calibration']['warmup_minutes']=0
  with self.assertRaises(ValueError):b.criteria(d[4],d[5],d[0])
 def test_known_bias_impedance(self):
  q=b.bias_terms(.5,.5)['known_linear_coefficients_V_per_A'];self.assertAlmostEqual(q['manual_noninverting_bias'],-1/(1/26000+1/1e7));self.assertEqual(q['summer_inverting_bias'],-100000)
 def test_nominal_resistor_mutation(self):
  d=copy.deepcopy(self.data[1]);d['packages']['R7101']['unit_records'][0]['value']='1000 Ω'
  with self.assertRaises(ValueError):b.resistor_corner_cases(d)
if __name__=='__main__':unittest.main()
