"""Synthetic translation-space algebra; no project pose evaluation."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class StaticRegionTests(unittest.TestCase):
    def test_forbidden_offset_direction(self):
        m=[(0,0),(2,0),(2,2),(0,2)];o=[(10,0),(12,0),(12,2),(10,2)]
        self.assertEqual(set(s.forbidden_vertices(m,o)),{(8.,-2.),(12.,-2.),(12.,2.),(8.,2.)})
    def test_circle_center_minus_moving_polygon(self):
        self.assertEqual(set(s.forbidden_vertices([(1,1),(3,1),(3,2),(1,2)],[(10,20)])),{(7.,18.),(9.,18.),(9.,19.),(7.,19.)})
    def test_empty_containment_and_nonsampled_domain(self):
        self.assertEqual(s.translation_domain([10,10,14,14],[0,0,5,5]),[10,10,9,9])
        self.assertEqual(s.translation_domain([10,10,20,20],[2,3,8,9]),[8,7,12,11])
    def test_integer_hull_rejects_interior_duplicates(self):
        self.assertEqual(set(s.hull_int([(0,0),(2,0),(2,2),(0,2),(1,1),(0,0)])),{(0,0),(2,0),(2,2),(0,2)})
    def test_curved_bounds_survive_rounding_extremes(self):
        import math
        from shapely.geometry import Point,box
        true=box(-1,-1,1,1)
        for delta in (-1e-6,1e-6):
            rounded=box(-1+delta,-1+delta,1+delta,1+delta)
            lower,upper=s.forbidden_bounds(rounded,.35)
            self.assertTrue(all(true.distance(Point(x,y))<.35 for x,y in lower.exterior.coords))
            for j in range(129):
                t=j*math.pi/256
                self.assertTrue(upper.covers(Point(1+.35*math.cos(t),1+.35*math.sin(t))))
            lo,hi=s.forbidden_bounds(rounded,0)
            self.assertTrue(true.covers(lo))
            self.assertTrue(hi.covers(true))
    def test_boundary_only_remainder_prevents_exclusion(self):
        from shapely.geometry import box,LineString
        lower=box(0,0,1,1)
        domain=lower.union(LineString([(1,0),(2,0)]))
        self.assertEqual(domain.difference(lower).area,0)
        self.assertFalse(s.excluded(lower,domain))
        self.assertTrue(s.excluded(lower,lower))
    def test_concave_input_refused(self):
        with self.assertRaises(AssertionError):
            s.convex_geometry([(0,0),(2,0),(1,1),(2,2),(0,2)])
    def test_empty_clipped_lower_bound_is_valid(self):
        from shapely.geometry import box
        lower,upper=s.forbidden_bounds(box(0,0,1,1),0)
        domain=box(1.0001,.25,1.0005,.75)
        lo,hi=lower.intersection(domain),upper.intersection(domain)
        self.assertTrue(lo.is_empty)
        self.assertFalse(hi.is_empty)
        self.assertFalse(hi.buffer(1e-9).covers(lo))
        self.assertTrue(s.bounds_nested(lo,hi))
    def test_nonempty_outside_lower_bound_still_rejected(self):
        from shapely.geometry import box
        self.assertFalse(s.bounds_nested(box(2,2,3,3),box(0,0,1,1)))

if __name__=='__main__':unittest.main()
