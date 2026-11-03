import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
import stage6_electrical as s

class Stage6ElectricalTests(unittest.TestCase):
    def test_position_correlated_peak_not_independent_bound(self):
        for vlo in (-5.025,0):
            peak=s.peak_wiper(120000,1010,9.9e6,vlo,5.025)
            sampled=max(abs(s.loaded_wiper(i/10000,120000,1010,9.9e6,vlo,5.025)['error_V'])for i in range(10001))
            self.assertGreaterEqual(abs(peak['error_V'])+1e-12,sampled)
            self.assertLess(abs(peak['error_V']),s.prior.budgets()['control_wiper']['fail_load_error_conservative_bound_V'])
            self.assertNotEqual(.5,peak['position']);self.assertNotEqual(1,peak['position'])
    def test_invalid_peak_domain_rejected(self):
        with self.assertRaises(ValueError):s.peak_wiper(100000,1000,1e7,1,5)
    def test_single_pole_limit(self):
        r=s.two_node_rc(100000,.5,1000,1e7,0,1e-8)
        self.assertAlmostEqual(s.prior.parallel(26000,1e7)*1e-8,r['time_constants_s'][0])
        self.assertEqual(0,r['denominator_s2_s_1'][0])
    def test_two_node_poles_reconstruct_coefficients(self):
        r=s.two_node_rc(120000,.5,1010,9.9e6,1e-9,10.5e-9);a,b,c=r['denominator_s2_s_1'];t1,t2=r['time_constants_s']
        self.assertAlmostEqual(a/c,t1*t2,places=18);self.assertAlmostEqual(b/c,t1+t2,places=15)
    def test_endpoint_position_has_one_pole(self):
        self.assertEqual(1,len(s.two_node_rc(100000,0,1000,1e7,1e-9,1e-8)['time_constants_s']))
    def test_negative_cap_rejected(self):
        with self.assertRaises(ValueError):s.two_node_rc(100000,.5,1000,1e7,-1e-9,1e-8)
    def test_wrong_archive_fails_closed(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'bad.zip';p.write_bytes(b'notamodel')
            with self.assertRaises(ValueError):s.inspect_archive(p)
    def test_macro_binding_uses_exact_family_and_pins(self):
        rows=s.model_binding(s.prior.source_context());self.assertTrue(rows)
        for r in rows:
            self.assertEqual('OPA4196IDR',r['MPN']);self.assertEqual('+12V',r['macro_pin_binding']['VCC']['net']);self.assertEqual('-12V',r['macro_pin_binding']['VEE']['net'])
            self.assertEqual({'IN+','IN-','VCC','VEE','OUT'},set(r['macro_pin_binding']))
    def test_wrong_supply_or_pin_role_rejected(self):
        original=s.prior.source_context()
        for mutation in ('rail','type','package'):
            ctx=copy.deepcopy(original)
            if mutation=='rail':ctx['bypin']['U1112','4']=(ctx['bypin']['U1112','4'][0],'+5V')
            elif mutation=='type':ctx['bypin']['U1112','1'][0]['pin_types']['1']='input'
            else:ctx['bypin']['U1112','1'][0]['ref']='U9999'
            with self.assertRaises((ValueError,KeyError)):s.model_binding(ctx)
    def test_offline_parameter_mutation_rejected(self):
        record=json.loads((s.OUT/'opax196-evidence.json').read_text());record['parameters']['I_I_B_A']*=100
        with self.assertRaises(ValueError):s.validate_evidence(record)
    def test_spice_suffix_m_is_milli_not_mega(self):
        self.assertEqual(.001,s.spice_number('1M'));self.assertEqual(1e6,s.spice_number('1MEG'))
    def test_no_qualification_promotion(self):
        r=s.build();self.assertFalse(r['accepted']);self.assertEqual('NOT RUN',r['simulator_execution']);self.assertEqual('NOT RUN',r['native'])
        self.assertLess(r['analytical_refinement']['return_budget_reconciliation']['required_resistance_for200uV_ohm'],.0005)
if __name__=='__main__':unittest.main()
