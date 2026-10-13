"""Independent numerical checks and failure examples for proposed shape limits."""
import math
import unittest
from dataclasses import replace

import numpy as np
from scipy.integrate import quad
import robust_curve as robust


class RobustCurveTests(unittest.TestCase):
    def test_length_and_tangents_off_grid(self):
        f = robust.Family()
        v = np.asarray(f.direction)
        for gap, length in ((20.2,65.9),(24.173,66.031),(30.7,66.1)):
            p = robust.control(f,gap,robust.handle(f,gap,length))
            result,error = quad(lambda t: float(np.linalg.norm(robust.first(p,[t])[0])),
                                0,1,epsabs=1e-10,epsrel=1e-10)
            self.assertAlmostEqual(result,length,places=8)
            self.assertLess(error,1e-7)
            d = robust.first(p,[0,1]); d /= np.linalg.norm(d,axis=1)[:,None]
            np.testing.assert_allclose(d,[v,v*[1,-1,1]],atol=1e-12)

    def test_tolerance_cell_lower_bound_covers_interior(self):
        f=robust.Family();g0,g1=24.173,24.225;l0,l1=65.97,65.995
        hmax=robust.handle(f,g0,l1);hmin=robust.handle(f,g1,l0)
        bound,_,_=robust.sweep_cell(f,g0,g1,hmax,hmin)
        for g,l in ((g0,l0),(24.191,65.983),(g1,l1)):
            p=robust.control(f,g,robust.handle(f,g,l))
            t=(np.arange(512)+.173)/512
            d=robust.first(p,t);dd=robust.second(p,t)
            actual=np.linalg.norm(d,axis=1)**3/np.linalg.norm(np.cross(d,dd),axis=1)
            self.assertGreaterEqual(float(actual.min()),bound)

    def test_position_tube_does_not_bound_curvature(self):
        # y=a*cos(k*x): at x=0 speed=1 and radius=1/(a*k^2).
        amplitude=.001; frequency=100
        self.assertLess(amplitude,robust.Family().position_error_max_mm)
        self.assertLess(1/(amplitude*frequency**2),robust.Family().minimum_bend_radius_mm)

    def test_position_and_first_derivative_still_need_C2(self):
        amplitude=1e-6;frequency=1000;f=robust.Family()
        self.assertLess(amplitude,f.position_error_max_mm)
        self.assertLess(amplitude*frequency,f.first_derivative_error_max)
        self.assertGreater(amplitude*frequency**2,f.second_derivative_error_max_per_mm)
        self.assertLess(1/(amplitude*frequency**2),f.minimum_bend_radius_mm)

    def test_material_growth_cannot_spend_preparation_twice(self):
        f=robust.Family();bridges=2*max(f.anchor_height_range_mm)/(-f.direction[2])
        maximum=(max(f.free_length_range_mm)+2*f.tail_each_mm+bridges)*(1+f.first_derivative_error_max)
        self.assertGreater(84.5-maximum,4.5)
        self.assertLess(83.5-maximum,4.5)  # tempting84±.5 class fails

    def test_gap_includes_stack_height_and_end_stop(self):
        f=robust.Family()
        np.testing.assert_allclose(f.gap_range,[20.2,30.7],atol=1e-12)
        self.assertGreater(replace(f,anchor_height_range_mm=(1.8,2.2)).gap_range[1],f.gap_range[1])


if __name__=='__main__':unittest.main()
