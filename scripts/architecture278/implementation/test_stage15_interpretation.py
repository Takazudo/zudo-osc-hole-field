import copy
import json
import unittest
import stage15_interpretation as m

class Interpretation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text()) for p in [m.ROOT/'design/standard/electrical-standard.json',m.previous.OUT/'allocation-report.json',m.OUT/'measurement-contract.json']]
    def test_canonical_conditions_distinct(self):
        r=m.analyze(*self.args)
        self.assertEqual(r['canonical_static_target_V'],.002)
        self.assertEqual(r['canonical_static_condition'],'after factory calibration')
        self.assertEqual(r['canonical_load_change_target_V'],.001)
        self.assertIsNone(r['calibrated_static_residual_V'])
        self.assertFalse(r['calibration_performed'])
    def test_manual_endpoint_not_cv(self):
        r=m.analyze(*self.args)['unchanged_diagnostic_numbers']
        self.assertAlmostEqual(r['four_idealized_manual_endpoint_max_V'],.00600105005,places=12)
        self.assertEqual(r['manual_endpoint_signed_terms_V']['CV_slope'],0)
        self.assertAlmostEqual(sum(r['manual_endpoint_signed_terms_V'].values()),r['four_idealized_manual_endpoint_max_V'],places=12)
        self.assertLess(max(abs(x) for x in r['four_idealized_CV_5V_fixed_setting_interval_V']),.001001)
    def test_criterion_change_rejected(self):
        a=copy.deepcopy(self.args);a[0]['calibration']['static_precision_error_V']=.006
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_contract_adoption_rejected(self):
        a=copy.deepcopy(self.args);a[2]['status']='ADOPTED'
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_false_calibration_rejected(self):
        a=copy.deepcopy(self.args);a[2]['calibration_performed']=True
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_contract_missing_reference_rejected(self):
        a=copy.deepcopy(self.args);del a[2]['lanes']['paired_CV']['reference']
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_false_postcal_result_rejected(self):
        a=copy.deepcopy(self.args);a[2]['lanes']['calibrated_path']['acceptance_status']='PASS'
        with self.assertRaises(ValueError):m.analyze(*a)
if __name__=='__main__':unittest.main()
