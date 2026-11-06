import copy,json,unittest
import stage11_identity as s
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.spec=json.loads((s.OUT/'identity-input.json').read_text());cls.inv=json.loads((s.OUT.parent/'stage10/inventory-report.json').read_text())
 def test_complete_exact_roles(self):
  r=s.analyze(self.spec,self.inv);self.assertEqual(r['counts'],{'source_refs':20,'resistors':17,'capacitors':3,'distinct_candidate_MPNs':10});self.assertFalse(r['source_values_changed'])
 def test_capacitance_gap_not_promoted(self):
  r=s.analyze(self.spec,self.inv)['reference_capacitor_application'];self.assertAlmostEqual(r['tolerance_only_min_F'],.9e-6);self.assertFalse(r['tolerance_only_establishes_application_min']);self.assertAlmostEqual(r['input_bypass_nominal_F'],.2e-6);self.assertFalse(r['input_bypass_recommendation_established'])
 def reject(self,fn):
  p=copy.deepcopy(self.spec);fn(p)
  with self.assertRaises(ValueError):s.analyze(p,self.inv)
 def test_missing_reference(self):self.reject(lambda p:p['selections'].pop('R7116'))
 def test_nominal_substitution(self):self.reject(lambda p:p['parts']['C0603C105K4RACTU'].update(value_SI=2.2e-6))
 def test_role_change(self):self.reject(lambda p:p['selections']['C7104'].update(role='unrelated bypass'))
 def test_pin_change(self):self.reject(lambda p:p['selections']['R7101']['captured_pins'].update({'1':'AGND'}))
 def test_exact_source_not_representative(self):self.reject(lambda p:p['sources']['RT0603BRD0710KL'].update(url='https://www.yageogroup.com/component-documentation/download/specsheet/RT0603BRD07100KL'))
 def test_effective_cap_not_invented(self):self.reject(lambda p:p['parts']['C0603C105K4RACTU'].update(effective_capacitance_at_bias_F=1e-6))
 def test_supplier_code_not_guessed(self):self.reject(lambda p:p['parts']['RT0603BRD0710KL'].update(supplier_order_code='invented'))
 def test_current_power_limits_conditioned(self):
  r=s.analyze(self.spec,self.inv);v=r['candidate_assignments']['R7113']['conditional_70C_limits'];self.assertLess(v['resistive_working_voltage_bound_V'],3.163);self.assertIsNone(v['hotter_than_70C_power_W'])
 def test_wrong_AI_cap_requirement(self):self.reject(lambda p:p['REF5050_application'].update(output_cap_range_F=[.1e-6,100e-6]))
if __name__=='__main__':unittest.main()
