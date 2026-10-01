import math
import unittest
from scripts.checks import monitor_rc_math as model


class MonitorRCMathTests(unittest.TestCase):
    def test_zero_pin_cap_matches_single_pole_and_ignores_r121(self):
        expected=5*(1-math.exp(-0.0001/(10000*1e-8)))
        for r2 in (1,10000,1e9):
            a,b=model.advance((0,0),5,5,.0001,10000,r2,1e-8,0)
            self.assertAlmostEqual(a,expected)
            self.assertEqual(a,b)

    def test_positive_pin_cap_retains_initial_state_and_lags(self):
        at_zero=model.advance((5,5),0,0,0,10000,10000,1e-8,1e-11)
        self.assertEqual(at_zero,(5,5))
        a,b=model.advance((5,5),0,0,1e-8,10000,10000,1e-8,1e-11)
        self.assertLess(a,b)
        self.assertLess(b,5)
        self.assertGreater(a,0)

    def test_r121_affects_only_positive_pin_cap_dynamics(self):
        fast=model.advance((0,0),5,5,1e-7,10000,1000,1e-8,1e-11)
        slow=model.advance((0,0),5,5,1e-7,10000,20000,1e-8,1e-11)
        self.assertGreater(fast[1],slow[1])

    def test_linear_ramp_composition(self):
        for pin_cap in (0,1e-11):
            whole=model.advance((0,0),0,5,1e-6,10000,10000,1e-8,pin_cap)
            half=model.advance((0,0),0,2.5,.5e-6,10000,10000,1e-8,pin_cap)
            split=model.advance(half,2.5,5,.5e-6,10000,10000,1e-8,pin_cap)
            for a,b in zip(whole,split):self.assertAlmostEqual(a,b,places=10)

    def test_steady_state_is_preserved(self):
        for pin_cap in (0,1e-11):
            self.assertEqual(model.advance((5,5),5,5,.1,10000,10000,1e-8,pin_cap),(5,5))

    def test_invalid_parameters_and_time_rejected(self):
        for pin_cap in (-1,math.nan,math.inf):
            with self.assertRaises(ValueError):model.advance((0,0),0,5,1,1,1,1,pin_cap)
        with self.assertRaises(ValueError):model.Trajectory([(0,0),(0,5)],(0,0),1,1,1,0)

    def test_observer_retains_brief_crossing_history(self):
        rows=[(0,5,5),(1,1,1),(2,5,5)]
        result=model.observer(rows,3,2,True)
        self.assertEqual([e['transition'] for e in result['crossings']],['fall_low','rise_high'])
        self.assertEqual(result['crossings'][0]['bracket_s'],[0,1])
        self.assertTrue(result['final'])
