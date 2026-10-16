import copy
import json
import unittest
import stage15_procedure as m
import stage15_allocation as a

class Procedure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text()) for p in [m.ROOT/'design/standard/electrical-standard.json',m.ROOT/'design/architecture-278/implementation/stage15-completion/allocation-report.json',m.OUT/'owner-decision.json']]
    def test_gain_budget_is_not_full_bound(self):
        r=m.analyze(*self.args);s=r['existing_model_support']
        self.assertAlmostEqual(s['CV_gain_only_max_abs_error_at5V_V'],.00100005,places=12)
        self.assertAlmostEqual(s['remaining_for_actual_baseline_and_all_other_static_terms_V'],.00099995,places=12)
        self.assertFalse(r['hardware_acceptance']);self.assertFalse(r['factory_calibration_performed'])
        self.assertEqual(r['protocol_status'],'PROPOSED_UNADOPTED')
    def test_fixed_baseline_error_cannot_be_subtracted_for_acceptance(self):
        target=0;baseline_error=.0012;gain=1.00020001;cv=5
        output=target+baseline_error+gain*cv
        raw=output-(target+cv);incremental=output-baseline_error-cv
        self.assertGreater(raw,.002);self.assertLess(incremental,.002)
    def test_cv_gain_does_not_depend_on_front_controls(self):
        p={'ka':1.002,'kn':.998,'ga':1.0001,'gm':1,'gcv':1.0001,'gr':1.0001}
        for at in (0,.5,1):
            for x in (0,.25,.5,.75,1):
                hi=a.affine(0,5,at,x,p);lo=a.affine(0,-5,at,x,p)
                self.assertAlmostEqual((hi['out_V']-lo['out_V'])/10,p['gr']*p['gcv'],places=12)
    def test_manual_setting_does_not_persist_after_move(self):
        p=dict.fromkeys(('ka','kn','ga','gm','gcv','gr'),1)
        self.assertEqual(a.affine(0,0,.5,.5,p)['out_V'],0)
        self.assertGreater(abs(a.affine(0,0,.5,.75,p)['out_V']),2)
    def test_owner_choice_cannot_restore_knob_voltage_claim(self):
        args=copy.deepcopy(self.args);args[2]['prescribed_voltage_at_knob_positions']=True
        with self.assertRaises(ValueError):m.analyze(*args)
    def test_criteria_not_relaxed(self):
        args=copy.deepcopy(self.args);args[0]['calibration']['static_precision_error_V']=.006
        with self.assertRaises(ValueError):m.analyze(*args)
    def test_distinct_load_target(self):
        r=m.analyze(*self.args);self.assertEqual((r['static_target_V'],r['load_change_target_V']),(.002,.001))
        self.assertEqual(len(r['finite_procedure']),8)
if __name__=='__main__':unittest.main()
