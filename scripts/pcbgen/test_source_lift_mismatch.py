import unittest
from fractions import Fraction as F
from unittest.mock import patch
from shapely.geometry import box
from scripts.pcbgen.source_lift_mismatch import lift_floor, intersect_floor, audit_source_support


class SourceLiftMismatchTests(unittest.TestCase):
    def test_exact_disjoint_sources_and_orthogonal_component(self):
        profile = [(3, box(0, 0, 2, 1), 1), (3, box(3, 0, 5, 1), -1)]
        lo, hi = lift_floor(profile, 3, 3., 2.)
        # rho*t/3*(1/A_source+1/A_return) = 2. Exactly unchanged
        # vertical component plus arbitrary in-plane mismatch is >=2.
        self.assertLessEqual(lo, 2.)
        self.assertGreaterEqual(hi, 2.)
        for in_plane in [F(0), F(1, 7), F(100)]:
            self.assertGreaterEqual(F(2) + in_plane**2, F(lo))
        self.assertEqual(lift_floor(profile, 0, 3., 2.), [0., 0.])

    def test_overlap_cancellation_and_reversal(self):
        p = box(0, 0, 1, 1)
        self.assertEqual(lift_floor([(3, p, 1), (3, p, -1)], 3, 1., 1.), [0., 0.])
        profile = [(3, p, 1), (3, box(.5, 0, 1.5, 1), -1)]
        a = lift_floor(profile, 3, 3., 1.)
        b = lift_floor([(l, p, -i) for l, p, i in profile], 3, 3., 1.)
        self.assertEqual(a, b)
        self.assertLessEqual(a[0], 1.)
        self.assertGreaterEqual(a[1], 1.)

    def test_uses_cross_lower_not_energy_upper(self):
        with patch('scripts.pcbgen.source_lift_mismatch.source_lift_region',
                   return_value={'cross_interval': [.25, .5], 'energy_upper': [100., 100.]}):
            self.assertEqual(lift_floor([], 0, 1., 1.), [.25, .5])

    def test_intersection_not_addition_and_contradiction(self):
        self.assertEqual(intersect_floor([.3, 1.], [.2, .4]), [.3, 1.])
        self.assertEqual(intersect_floor([0., 1.], [.2, .4]), [.2, 1.])
        with self.assertRaises(ValueError):
            intersect_floor([0., .1], [.2, .4])
        with self.assertRaises(ValueError):
            lift_floor([], 0, 0., 1.)

    def test_pointwise_source_audit_overlap_and_partial_cut(self):
        import numpy as np
        import shapely
        from types import SimpleNamespace
        xy = np.array([[0,0],[1,0],[1,1],[0,1]], dtype=np.longdouble)
        triangles = np.array([[0,1,2],[0,2,3]])
        polygons = shapely.polygons(np.asarray(xy[triangles], dtype=float))
        sheet = SimpleNamespace(metric_xy=xy, triangles=triangles,
                                polygons=polygons, tree=shapely.STRtree(polygons))
        p = box(0,0,1,1)
        profiles = [[(0,p,1)], [(0,p,1),(0,p,-1)]]
        stored = np.array([[.5,0],[.5,0]])
        result = audit_source_support([sheet], profiles, [stored])
        self.assertEqual(len(result[0]['source_triangles']), 2)
        self.assertEqual(result[0]['source_triangles'][0]['signed_density_A_per_mm2'], ['1','0'])
        with self.assertRaises(ValueError):
            audit_source_support([sheet], [[(0,box(0,0,.5,1),1)],[]], [stored])
        with self.assertRaises(ValueError):
            audit_source_support([sheet], profiles, [np.zeros((2,2))])

    def test_linear_lift_floor_is_not_universal_over_3d_currents(self):
        # Unit slab, rho=1, v=0; top g(x)=+1 for x<1/2, -1 otherwise.
        # G=int_0^x g is triangular, G(0)=G(1)=0, integral G²=1/12.
        # q=(-G*h',0,g*h) has div=0, prescribed top trace, insulated
        # bottom/sides when h(0)=0,h(1)=1. With h=z², its full energy
        # is 1/5 + (1/12)*(4/3)=14/45, below the LINEAR lift's 1/3.
        quadratic_full_energy = F(1,5) + F(1,12)*F(4,3)
        self.assertEqual(quadratic_full_energy, F(14,45))
        self.assertLess(quadratic_full_energy, F(1,3))


if __name__ == '__main__':
    unittest.main()
