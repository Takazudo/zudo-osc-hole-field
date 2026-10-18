import unittest
import ledger

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.d=ledger.build()
        self.rows={(r['link'],r['pin']):r for r in self.d['rows']}
    def test_no_guarantee_or_adoption(self):
        self.assertFalse(self.d['canonical_changed'])
        for r in self.d['rows']:
            self.assertIsNone(r['guaranteed_conductor_max_A'])
        for r in self.d['resistor_candidates'].values():
            self.assertFalse(r['CAD_applied'])
            self.assertFalse(r['order_ready'])
    def test_two_packages_not_four_comparators(self):
        for ref in ('U7107','U7108'):
            self.assertEqual(self.d['pin_bindings'][ref]['pins']['8'],'+12V')
            self.assertEqual(self.d['pin_bindings'][ref]['pins']['4'],'-12V')
        for key,r in self.rows.items():
            self.assertEqual(r['LM393_36V_transfer_allowance_A'],.0016 if key in [('J-PWR','1'),('J-PWR','2')] else 0)
    def test_candidate_initial_tolerance_and_single_LED(self):
        for pin in ('1','2'):
            r=self.rows['J-PWR',pin]
            self.assertAlmostEqual(r['after_candidate_resistors_A']-r['before_conditional_A'],3*12.48*(1/5594.4-1/5600)+24.85*(1/22077.9-1/22100))
    def test_logic_not_assumed_eight_powered_inputs(self):
        for ref in ('U7102','U7103'):
            pins=self.d['pin_bindings'][ref]['pins']
            self.assertIn('ENABLE',pins['1'])
            for pin in ('8','9','16'):self.assertEqual(pins[pin],'AGND')
        r=self.rows['J-PWR','3']
        self.assertEqual(r['before_conditional_A'],r['scenario_with_LM_allowance_A'])
        self.assertIn('ADG5412F logic input current',r['unknown_terms_retained'])
    def test_ground_envelope_no_equal_sharing(self):
        vals=[self.rows[k]['scenario_with_LM_allowance_A'] for k in [('J-SIG','2'),('J-SIG','7'),('J-PWR','4')]]
        self.assertEqual(vals,[vals[0]]*3)
        self.assertEqual(self.rows['J-SIG','1']['before_conditional_A'],50e-9)
        self.assertIn('OPA4197 output short-circuit current (driver)',self.rows['J-SIG','1']['unknown_terms_retained'])
    def test_exact_signal_driver(self):
        self.assertEqual(self.d['pin_bindings']['U7105']['pins']['8'],'/A01/SUM_NEG')
        self.assertEqual(self.d['pin_bindings']['U7105']['pins']['7'],'/A01/MANUAL_OFFSET')
    def test_deterministic(self):
        self.assertEqual((ledger.HERE/'ledger.json').read_text(),ledger.encoded())

if __name__=='__main__':unittest.main()
