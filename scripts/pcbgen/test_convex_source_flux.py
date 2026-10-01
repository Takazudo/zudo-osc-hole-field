import math
import unittest
from fractions import Fraction as F
from scripts.pcbgen.convex_source_flux import domain_bounds,coefficient_bounds


class ConvexSourceFluxTest(unittest.TestCase):
    def test_actual_thin_roundrect_and_circle(self):
        p={'kind':'roundrect','half_size_nm':[737500,200000],'corner_radius_nm':100000}
        lo,hi,d2=domain_bounds(p);actual=4*.7375*.2-(4-math.pi)*.1**2
        self.assertLess(float(lo),actual);self.assertGreater(float(hi),actual)
        v=coefficient_bounds(p,minimum_height_mm=.07,maximum_height_mm=.08,rho_max_ohm_mm=2.3e-5,profile_area_min_mm2=.01,drill_free=True)
        exact=max(2.3e-5*(h/3+float(d2)/(math.pi**2*h)) for h in (.07,.08))
        self.assertGreaterEqual(v['unit_normalized_redistribution_energy_ohm_upper'],exact/actual)
        self.assertGreaterEqual(v['net_to_uniform_profile_energy_ohm_upper'],exact*(100-1/actual))
        circle={'kind':'circle','half_size_nm':[750000,750000],'corner_radius_nm':0}
        self.assertLess(float(domain_bounds(circle)[0]),math.pi*.75**2)
        with self.assertRaises(ValueError):coefficient_bounds(p,minimum_height_mm=.07,maximum_height_mm=.08,rho_max_ohm_mm=2.3e-5,profile_area_min_mm2=.01,drill_free=False)

    def test_uniform_square_and_higher_mode(self):
        p={'kind':'rectangle','half_size_nm':[500000,500000]}
        r=coefficient_bounds(p,minimum_height_mm=.1,maximum_height_mm=.1,rho_max_ohm_mm=1.,profile_area_min_mm2=1.,drill_free=True)
        self.assertEqual(r['net_to_uniform_profile_energy_ohm_upper'],0.)
        # g=cos(7*pi*x), zero net current and ||g||2^2=1/2. Its exact
        # foil correction has positive energy even though the net term is 0.
        exact=(.1/3+1/((7*math.pi)**2*.1))/2
        self.assertGreaterEqual(r['unit_normalized_redistribution_energy_ohm_upper']/2,exact)
        self.assertGreater(exact,0.)


if __name__=='__main__':unittest.main()
