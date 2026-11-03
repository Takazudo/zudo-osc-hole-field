import copy
import json
import unittest
import stage14_electrical as s

class Electrical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files=[s.OUT/'electrical-input.json',s.OUT.parent/'stage13/capacitor-report.json',s.OUT.parent/'stage10/inventory-report.json',s.OUT/'interfaces-report.json']
        cls.args=[json.loads(p.read_text()) for p in files];cls.report=s.analyze(*cls.args)

    def test_charge_energy(self):
        r=self.report['capacitor_accounting'][1]
        self.assertAlmostEqual(r['initial_charge_interval_C'][1],121e-6)
        self.assertAlmostEqual(r['initial_energy_interval_J'][1],302.5e-6)
        self.assertAlmostEqual(r['assumed_linear_ramp_sensitivities'][1]['capacitor_current_interval_A'][1],.0121)
        self.assertAlmostEqual(self.report['capacitor_accounting'][0]['initial_charge_interval_C'][1],68.244e-6)

    def test_raw_current_not_buffer_output_load(self):
        self.assertEqual(self.report['raw_reference_endpoints'],['C7102:1','U7101:6','U7104:3'])
        self.assertAlmostEqual(self.report['raw_reference_conditioned_load_subtotals'][0]['raw_reference_load_subtotal_A'],7.715e-6)
        self.assertAlmostEqual(self.report['raw_reference_conditioned_load_subtotals'][2]['raw_reference_load_subtotal_A'],92.415e-6)
        self.assertAlmostEqual(self.report['supply_conditioned_subtotals'][2]['represented_supply_current_subtotal_A'],.001321215)

    def test_unknowns_not_zero(self):
        self.assertIsNone(self.report['startup_time_upper_bound_s'])
        self.assertIsNone(self.report['discharge_time_upper_bound_s'])
        self.assertFalse(self.report['backfeed_qualified'])
        self.assertFalse(self.report['effective_service_C_and_ESR_qualified'])
        self.assertEqual(self.report['disposition'],'CONDITIONAL_CANDIDATE')

    def reject(self,edit):
        args=copy.deepcopy(self.args);edit(args)
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_operating_current_not_startup(self):
        self.reject(lambda a:a[0]['reference_conditions'].update(guaranteed_startup_current_A=.01))

    def test_typical_startup_condition_preserved(self):
        self.reject(lambda a:a[0]['reference_conditions'].update(turn_on_test_capacitance_F=22e-6))

    def test_bias_not_offstate(self):
        self.reject(lambda a:a[0]['buffer_conditions'].update(off_state_input_current_bound_A=15e-9))

    def test_no_missing_validation_case(self):
        self.reject(lambda a:a[0]['validation_cases'].pop())

    def test_no_false_validation_pass(self):
        self.reject(lambda a:a[0]['validation_cases'][0].update(status='PASS'))

    def test_no_silent_bleed(self):
        self.reject(lambda a:a[0]['added_components'].append('bleed'))

    def test_no_raw_load_omission(self):
        self.reject(lambda a:a[3]['nodes']['C7101:1'].update(net='/A01/C534b2a_RAW_5V'))

    def test_no_lifetime_guarantee(self):
        self.reject(lambda a:a[1]['parts']['C7102'].update(effective_service_C_guaranteed_F=19.8e-6))

if __name__=='__main__':unittest.main()
