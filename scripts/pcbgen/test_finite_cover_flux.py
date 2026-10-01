import math
import unittest
from fractions import Fraction as F
from scripts.pcbgen.finite_cover_flux import annulus_poincare_upper,tangent_cover_radius_squared,cover_poincare_upper,exact_tree_source_balance


class FiniteCoverFluxTest(unittest.TestCase):
    def test_actual_via_and_pth_octagonal_cover(self):
        for ri,ro in [(.15,.35),(.61,.915),(.5,.85),(.545,.9),(.4,.8)]:
            self.assertGreater(ro*ro,tangent_cover_radius_squared(ri))
            for k in range(721):
                theta=k*math.pi/360;r=ro;x,y=r*math.cos(theta),r*math.sin(theta)
                self.assertTrue(abs(x)>=ri or abs(y)>=ri or abs(x)+abs(y)>=1.5*ri)
            self.assertGreater(annulus_poincare_upper(ri,ro),ro*ro)

    def test_signed_source_partition_exact_overlap_cancellation(self):
        # Nonzero opposite injections remain explicit even with total zero.
        q=[F(3,2),F(-7,3),F(1,6),F(2,3)]
        flux=exact_tree_source_balance(q,[-1,0,1,0]);self.assertEqual(flux,[F(0),F(-13,6),F(1,6),F(2,3)])
        upper=cover_poincare_upper(local_poincare_mm2=[1,2,3,4],source_area_upper_mm2=5,parents=[-1,0,1,0],overlap_area_lower_mm2=[None,.1,.2,.3])
        self.assertGreater(upper,0)
        with self.assertRaises(ValueError):exact_tree_source_balance([1,-1+1e-12],[-1,0])
        with self.assertRaises(ValueError):cover_poincare_upper(local_poincare_mm2=[1,1],source_area_upper_mm2=1,parents=[-1,0],overlap_area_lower_mm2=[None,0])


if __name__=='__main__':unittest.main()
