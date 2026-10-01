"""Exact represented-input and anisotropic slab checks for the depth map."""
from fractions import Fraction as F
import unittest
import numpy as np
from scripts.pcbgen.depth_map_envelope import bounds


class DepthMapEnvelopeTests(unittest.TestCase):
    def test_normal_and_tangential_slab_resistances_need_opposite_stretches(self):
        result=bounds([.125,.5],[(.0625,.25),(.25,.75)],1.,.5,2.)
        lo=F(result['resistance_operator_lower_factor_exact'])
        hi=F(result['resistance_operator_upper_factor_exact'])
        self.assertEqual((lo,hi),(F(1,4),F(4)))
        # Exact rectangular resistor: R_z scales rho*lambda; R_x scales
        # rho/lambda. A thickness-only resistance multiplier is invalid.
        for rho in [F(1,2),F(1),F(2)]:
            for stretch in [F(1,2),F(3,4),F(1),F(3,2),F(2)]:
                for ratio in [rho*stretch,rho/stretch]:
                    self.assertLessEqual(lo,ratio);self.assertGreaterEqual(hi,ratio)
                # Piola: side area stretches lambda while J_x shrinks by it;
                # horizontal area and J_z are both unchanged.
                self.assertEqual((1/stretch)*stretch,1)

    def test_binary32_values_are_preserved_exactly_before_ratios(self):
        nominal=np.float32(.07);lower=np.float32(.065);upper=np.float32(.08)
        rho=np.float32(.000021);rlo=np.float32(.000020);rhi=np.float32(.000024)
        result=bounds([nominal],[(lower,upper)],rho,rlo,rhi)
        f=lambda v:F(float(v))
        metric=max(f(upper)/f(nominal),f(nominal)/f(lower))
        self.assertEqual(F(result['global_metric_upper_exact']),metric)
        self.assertEqual(F(result['resistance_operator_lower_factor_exact']),f(rlo)/f(rho)/metric)
        self.assertEqual(F(result['resistance_operator_upper_factor_exact']),f(rhi)/f(rho)*metric)

    def test_nonpositive_unbounded_mismatched_or_excluding_bands_fail(self):
        for heights,intervals in [([],[]),([1.],[]),([1.],[(0.,2.)]),
                ([1.],[(.5,float('inf'))]),([1.],[(1.1,2.)]),([1.],[(.5,)])]:
            with self.subTest(heights=heights,intervals=intervals),self.assertRaises(ValueError):
                bounds(heights,intervals,1.,.5,2.)
        with self.assertRaises(ValueError):bounds([1.],[(.5,2.)],1.,1.1,2.)


if __name__=='__main__':unittest.main()
