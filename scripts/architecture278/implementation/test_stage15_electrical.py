import copy
import json
import unittest
import stage15_electrical as s

class Electrical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp=json.loads((s.OUT/'electrical-input.json').read_text());cls.report=s.analyze(cls.inp)

    def reject(self,edit):
        inp=copy.deepcopy(self.inp);edit(inp)
        with self.assertRaises(ValueError):s.analyze(inp)

    def test_exact_I_grade_full_temperature(self):
        self.reject(lambda i:i['matching'].update(ratio_error_I_full_temperature_fraction=.0001))
        self.reject(lambda i:i['matching'].update(specified_temperature_C=[-40,125]))

    def test_pin_and_EP_binding(self):
        self.reject(lambda i:i['pin_pairs'].update(R1=['1','2']))
        self.reject(lambda i:i['networks']['RN7102'].update(EP9=None))
        self.reject(lambda i:i['networks']['RN7102'].update(unused_elements=[]))

    def test_no_CMRR_or_calibration_promotion(self):
        self.reject(lambda i:i['matching'].update(CMRR_special_bound_used=True))
        self.reject(lambda i:i.update(calibration_changed=True))

    def test_coherent_summer_ratios(self):
        cases=list(s.network_cases(.000125));self.assertEqual(len(cases),64)
        for p,summer,restore in cases:
            self.assertLessEqual(max(summer)/min(summer),1.000125)
            self.assertLessEqual(max(restore)/min(restore),1.000125)
            self.assertAlmostEqual(p['ga']*summer[0],p['gm']*summer[1])
            self.assertAlmostEqual(p['ga']*summer[0],p['gcv']*summer[2])

    def test_ratio_only_CV_envelope(self):
        r=self.report['conditioned_error_allocation'][1]
        self.assertAlmostEqual(r['CV5V_network_only_error_interval_V'][1],.001250078125)
        self.assertAlmostEqual(r['CV5V_remaining_static_allocation_before_other_terms_V'],.000749921875)
        # Correlated all-low inputs/high feedback realizes the upper gain product.
        p={'ga':1.000125,'gm':1.000125,'gcv':1.000125,'gr':1.000125}
        difference=s.previous.transfer(0,5,.5,.5,**p)['out_V']-s.previous.transfer(0,0,.5,.5,**p)['out_V']
        self.assertAlmostEqual(difference-5,r['CV5V_network_only_error_interval_V'][1])

    def test_remaining_manual_loading_not_erased(self):
        rows={r['state']:r for r in self.report['conditioned_error_allocation'][0]['states']}
        self.assertGreater(abs(rows['manual_quarter']['nominal_loading_error_V']),.002)
        self.assertGreater(rows['manual_low']['maximum_witness']['error_V']-rows['manual_low']['minimum_witness']['error_V'],.01)

    def test_offset_coefficients_direct_perturbation(self):
        p={'ga':1.000125,'gm':1/1.000125,'gcv':1,'gr':1.000125,'ka':1.002,'kn':.998}
        co=s.offset_coefficients(p,.25,.75)
        self.assertAlmostEqual(co['summer'],-p['gr']*(1+p['ga']+p['gm']+p['gcv']))
        self.assertAlmostEqual(co['restore'],1+p['gr'])
        base=s.previous.transfer(1,1,.25,.75,**p)['out_V']
        pert=s.previous.transfer(1,1,.25,.75,errors={k:.0001 for k in s.ERRORS},**p)['out_V']
        self.assertAlmostEqual(pert-base,sum(co.values())*.0001)

    def test_unknowns_do_not_become_acceptance(self):
        self.assertIsNone(self.report['complete_static_error_bound_V'])
        self.assertIsNone(self.report['complete_load_error_bound_V'])
        self.assertFalse(self.report['pitch_acceptance'])
        self.assertTrue(all(r['criterion_met'] is None for r in self.report['load_change_cases']))
        self.assertTrue(all(not r['partial_is_complete_bound'] for t in self.report['conditioned_error_allocation'] for r in t['states']))

    def test_used_unused_branch_current_power(self):
        b=self.report['network_loading']
        self.assertAlmostEqual(b['declared_12V_differential_allocation_per_used_element']['maximum_current_A'],12/92500)
        self.assertAlmostEqual(b['package_conditional_power_W']['RN7101'],4*144/92500)
        self.assertEqual(b['output_loading_map']['summer_amplifier'],['R7124','R7125'])
        self.assertEqual(b['ratings']['resistor_to_EP_typical_pF'],5.5)
        self.assertEqual(b['ratings']['resistor_to_resistor_typical_pF'],1.4)
        for state in b['per_state_branch_allocations']:
            self.assertEqual(set(state['branches']),{'R7121','R7122','R7123','R7124','R7125','R7126'})
            for branch in state['branches'].values():
                self.assertAlmostEqual(branch['power_at_min_R_W'],branch['current_at_min_R_A']*branch['maximum_abs_witness_differential_V'])

    def test_absolute_tolerance_not_matching_for_bias(self):
        p={'ga':1,'gm':1,'gr':1,'ka':1}
        terms=s.known_bias_coefficients(p,.5,.5,.075)
        self.assertAlmostEqual(terms['summer_inverting'],107500)
        self.assertAlmostEqual(terms['restore_inverting'],107500)

if __name__=='__main__':unittest.main()
