import copy,json,unittest
import stage13_capacitors as c
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=[json.loads(p.read_text())for p in (c.OUT/'capacitor-input.json',c.OUT.parent/'stage10/inventory-report.json',c.OUT.parent/'stage11/identity-input.json')]
 def reject(self,change,why):
  data=copy.deepcopy(self.data);change(data)
  with self.assertRaisesRegex(ValueError,why):c.analyze(*data)
 def test_conservation(self):
  r=c.analyze(*self.data);self.assertEqual(len(r['conservation']['unchanged_refs']),88);self.assertFalse(r['conservation']['topology_changed'])
 def test_conditioned_capacitance(self):
  r=c.analyze(*self.data);self.assertAlmostEqual(r['parts']['C7101']['temperature_qualification_intervals_F']['125'][0],3.384e-6);self.assertAlmostEqual(r['parts']['C7102']['temperature_qualification_intervals_F']['125'][1],29.04e-6)
  self.assertIsNone(r['parts']['C7102']['effective_service_C_guaranteed_F'])
 def test_polarity(self):self.reject(lambda d:d[0]['parts']['C7102']['pins'].update({'1':'AGND','2':'/A01/C534b2a_RAW_5V'}),'binding')
 def test_pads_mirrored_later(self):self.reject(lambda d:d[0]['parts']['C7102'].update(pin1_positive_local_xy_mm=[3.12,0]),'polarized')
 def test_land_not_0603(self):self.reject(lambda d:d[0]['parts']['C7102'].update(land_pad_size_xy_mm=[1,1]),'specified')
 def test_max_body_not_nominal(self):self.reject(lambda d:d[0]['parts']['C7101'].update(body_max_mm=[6,3.2,2.5]),'dimensions')
 def test_no_combined_life_claim(self):self.reject(lambda d:d[0]['qualification'].update(joint_operating_bias_temperature_age_guarantee=1e-6),'combined')
 def test_no_continuous_reverse(self):self.reject(lambda d:d[0]['qualification'].update(continuous_reverse_allowed=True),'combined')
 def test_no_reduced_voltage_derating(self):self.reject(lambda d:d[0]['qualification']['recommended_voltage_fraction'].update(above85_to125C=.67),'derating')
 def test_exact_input_50V(self):self.reject(lambda d:d[0]['parts']['C7101'].update(rated_voltage_at85C_V=35),'specified')
 def test_esr_conditions(self):
  r=c.analyze(*self.data);self.assertTrue(r['output_comparison']['below_TI_stability_limit_at_documented_condition']);self.assertFalse(r['output_comparison']['stability_qualified']);self.assertFalse(r['output_comparison']['noise_1_to1p5ohm_recommendation_established'])
 def test_no_invented_current(self):self.reject(lambda d:d[0]['source_envelope'].update(reference_charging_current_A=.01),'startup')
 def test_charge(self):
  r=c.analyze(*self.data);self.assertAlmostEqual(r['parts']['C7102']['startup']['nominal_charge_C'],110e-6);self.assertEqual(r['output_comparison']['charge_ratio'],22);self.assertAlmostEqual(r['parts']['C7102']['startup']['charge_current_for_proposed_10ms_linear_ramp_A'],.0121)
 def test_leakage_at_test_conditions(self):
  r=c.analyze(*self.data);self.assertAlmostEqual(r['parts']['C7102']['leakage_temperature_test_limits_A']['125'],92.4e-6)
 def test_local_bypass_preserved(self):self.reject(lambda d:d[1]['packages']['C7107']['source_package'].update(decouples_ref=None),'local bypass')
 def test_package_omission(self):self.reject(lambda d:d[1]['packages'].pop('C7107'),'conservation')
 def test_primary_hash(self):self.reject(lambda d:d[0]['evidence']['family'].update(sha256='0'*64),'primary bytes')
 def test_land_locator(self):self.reject(lambda d:d[0]['evidence']['family']['additional_locators'].pop(),'locators')
 def test_reference_grade_preserved(self):self.reject(lambda d:d[0]['application'].update(output_cap_range_F=[1e-6,100e-6]),'provenance')
if __name__=='__main__':unittest.main()
