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

    def test_bleeder_reduces_dc_gain_and_driven_time_constant(self):
        final=5*100000/110000
        tau=1e-8/(1/10000+1/100000)
        for pin_cap in (0,4.5e-12):
            a,b=model.advance((0,0),5,5,.1,10000,10000,1e-8,pin_cap,100000)
            self.assertAlmostEqual(a,final,places=10)
            self.assertAlmostEqual(b,final,places=10)
        a,b=model.advance((0,0),5,5,tau,10000,10000,1e-8,0,100000)
        self.assertAlmostEqual(a,final*(1-math.exp(-1)),places=10)

    def test_open_drive_uses_bleeder_only_and_ignores_forcing(self):
        expected=5/math.e
        for r1 in (1,10000,1e12):
            a,b=model.advance((5,5),-100,100,.001,r1,10000,1e-8,0,100000,False)
            self.assertAlmostEqual(a,expected,places=10)
            self.assertEqual(a,b)
        driven=model.advance((5,5),0,0,.001,10000,10000,1e-8,0,100000)[0]
        self.assertLess(driven,expected/1000)

    def test_bleeder_two_node_initial_derivative_matches_kcl(self):
        for driven in (True,False):
            dt=1e-12
            a,b=model.advance((3,2),5,5,dt,10000,10000,1e-8,4.5e-12,100000,driven)
            expected_a=((5-3)/10000*driven-(3-2)/10000-3/100000)/1e-8
            expected_b=(3-2)/10000/4.5e-12
            self.assertAlmostEqual((a-3)/dt/expected_a,1,delta=.0001)
            self.assertAlmostEqual((b-2)/dt/expected_b,1,delta=.0001)

    def test_bleeder_linear_ramp_composition(self):
        for pin_cap in (0,4.5e-12):
            whole=model.advance((1,1),0,5,1e-6,10000,10000,1e-8,pin_cap,100000)
            half=model.advance((1,1),0,2.5,.5e-6,10000,10000,1e-8,pin_cap,100000)
            split=model.advance(half,2.5,5,.5e-6,10000,10000,1e-8,pin_cap,100000)
            for a,b in zip(whole,split):self.assertAlmostEqual(a,b,places=10)

    def test_invalid_bleed_and_undefined_open_drive_are_rejected(self):
        for bleed in (-1,0,True,math.inf,math.nan):
            with self.assertRaises(ValueError):model.advance((0,0),0,5,1,1,1,1,0,bleed)
        with self.assertRaises(ValueError):model.advance((0,0),0,5,1,1,1,1,0,None,False)

    def test_assumed_leakage_changes_open_drive_equilibrium(self):
        for pin_cap in (0,4.5e-12):
            a,b=model.advance((5,5),0,0,.1,10000,10000,1e-8,pin_cap,100000,False,20e-6)
            self.assertAlmostEqual(a,2,places=10)
            self.assertAlmostEqual(b,2,places=10)
        a,b=model.advance((5,5),0,0,.001,10000,10000,1e-8,0,100000,False,20e-6)
        self.assertAlmostEqual(a,2+3/math.e,places=10)
