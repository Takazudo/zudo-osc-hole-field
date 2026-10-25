import math
import unittest

import collet_clearance as c


class ColletClearanceTests(unittest.TestCase):
    def test_exact_flat_cylinder_resolves_false_capsule_failure(self):
        v = c.minimum_normal_component(.5445913286478836, .01)
        exact = c.cylinder_gap(1.95, 1, 2, v)-.35
        capsule = 1.95+v-2-.35
        self.assertGreater(exact, .25)
        self.assertLess(capsule, .25)
        self.assertAlmostEqual(exact, .4479660348233535)

    def test_sampled_surfaces_stay_above_analytic_bound(self):
        nominal = .5445913286478836
        alpha = math.asin(.01)
        lower = c.minimum_normal_component(nominal, .01)
        bound = c.cylinder_gap(1.95, 1, 2, lower)
        theta0 = math.acos(nominal)
        for delta in (-alpha, -.371*alpha, 0, .731*alpha, alpha):
            vz = math.cos(theta0+delta)
            transverse = math.sqrt(1-vz*vz)
            for height in (1.95, 1.973, 2.05):
                for along in (1, 1.317, 2.5):
                    for j in range(73):
                        z = height+along*vz+2*transverse*math.cos(2*math.pi*j/73)
                        self.assertGreaterEqual(z, bound-1e-12)

    def test_profile_and_retention_are_not_silently_dropped(self):
        self.assertEqual(set(c.BOARD_CLOSURES), {'outer_profile', 'board_warp', 'thermal', 'retention', 'registration'})
        self.assertAlmostEqual(math.fsum(c.BOARD_CLOSURES.values()), .35)

    def test_axis_cone_is_required_not_position_only(self):
        with self.assertRaises(ValueError):
            c.minimum_normal_component(.01, .2)
        with self.assertRaises(ValueError):
            c.minimum_normal_component(.5, 1)

    def test_axis_cone_xy_box_contains_sampled_cylinder(self):
        direction = (.5933040689317951, .5927989259019525, .5445913286478836)
        box = c.xy_box((23, 15.5), direction, math.asin(.01), 2)
        def cross(a, b):
            return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
        def normalize(a):
            length = math.sqrt(sum(v*v for v in a))
            return tuple(v/length for v in a)
        n = normalize(cross(direction, (0, 0, 1)))
        m = cross(direction, n)
        for tilt in (0, .371*math.asin(.01), math.asin(.01)):
            for azimuth in (0, 1, 2.3, 4.7):
                axis = tuple(math.cos(tilt)*direction[k]+math.sin(tilt)*(math.cos(azimuth)*n[k]+math.sin(azimuth)*m[k]) for k in range(3))
                disk_n = normalize(cross(axis, (0, 0, 1)))
                disk_m = cross(axis, disk_n)
                for along in (1, 1.341, 2.5):
                    for j in range(12):
                        angle = 2*math.pi*j/12
                        point = tuple((23, 15.5, 0)[k]+along*axis[k]+2*(math.cos(angle)*disk_n[k]+math.sin(angle)*disk_m[k]) for k in range(3))
                        self.assertTrue(box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3])

    def test_nonunit_and_nonfinite_axes_rejected(self):
        with self.assertRaises(ValueError):
            c.xy_box((0, 0), (1, 1, 0), 0, 2)
        with self.assertRaises(ValueError):
            c.cylinder_gap(float('nan'), 1, 2, .5)
        with self.assertRaises(ValueError):
            c.xy_box((0, 0), (1, 0, 0), 0, -2)

    def test_clearance_does_not_admit_missing_solids_or_physical_work(self):
        result = c.calculate()
        self.assertEqual(len(result['source_XY_screen']['ledger']), 12)
        self.assertGreater(result['source_XY_screen']['source_obstacle_count'], 100)
        self.assertFalse(result['accepted'])
        for name, value in result['gates'].items():
            if not name.startswith('conditional_outer_collet_'):
                self.assertFalse(value, name)


if __name__ == '__main__':
    unittest.main()
