"""Counterexamples and independent checks for the conditional source proposal."""
import json
import math
import unittest
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.spatial.distance import cdist
import check
import offset


class GeometryTests(unittest.TestCase):
    def test_nonrectangle_courtyard_cannot_be_silently_boxed(self):
        with self.assertRaisesRegex(ValueError, 'nonrectangular'):
            check.box([[[0, 0], [1, 0], [1, 1]]])

    def test_short_curve_theorem_refuses_long_curve_extrapolation(self):
        with self.assertRaisesRegex(ValueError, 'theorem domain'):
            check.min_chord(82, 25.908)

    def test_shared_xy_cannot_absorb_requested_travel(self):
        max_length = 2 * 25.908 * math.asin(24.4 / (2 * 25.908))
        self.assertLess(max_length - 24.4, 1.01)
        self.assertGreater(check.minimum_service_length(24.4, 10, 25.908), 47.99)

    def test_fixed_tangents_and_independent_adaptive_length(self):
        for gap in (21.4, 24.713, 31.4):
            p = offset.control(gap, offset.handle(gap))
            v = offset.first(p, [0, 1])
            np.testing.assert_allclose(v[0]/np.linalg.norm(v[0]), offset.V0, atol=1e-12)
            np.testing.assert_allclose(v[1]/np.linalg.norm(v[1]), offset.V1, atol=1e-12)
            length, error = quad(lambda t: float(np.linalg.norm(offset.first(p, [t])[0])),
                                 0, 1, epsabs=1e-10, epsrel=1e-10)
            self.assertAlmostEqual(length, 64, places=8)
            self.assertLess(error, 1e-7)

    def test_interval_boxes_cover_off_grid_samples(self):
        g0, g1 = 25.15, 25.20
        lo, hi, _, _, rb = offset.sweep_cells(g0, g1, offset.handle(g0), offset.handle(g1))
        ts = (np.arange(512) + .173) / 512
        for gap in (g0, g0+.0173, g1):
            p = offset.control(gap, offset.handle(gap))
            pts = offset.position(p, ts)
            self.assertTrue(np.all(pts >= lo) and np.all(pts <= hi))
            v, a = offset.first(p, ts), offset.second(p, ts)
            radii = np.linalg.norm(v, axis=1)**3 / np.linalg.norm(np.cross(v, a), axis=1)
            self.assertTrue(np.all(radii >= rb))

    def test_same_sign_rows_really_collide(self):
        pts = offset.position(offset.control(21.4, offset.handle(21.4)), np.linspace(0, 1, 1201))
        other = pts + [17, 0, 0]
        self.assertLess(float(cdist(pts, other).min()), 2.5908)
        reflected = pts * [1, -1, 1] + [17, 0, 0]
        self.assertGreater(float(cdist(pts, reflected).min()), 2.5908)

    def test_land_bridges_consume_preparation_allowance(self):
        self.assertAlmostEqual(2 * offset.BRIDGE, 5.498248859, places=8)
        self.assertLess(10 - 2 * offset.BRIDGE, 4.502)
        self.assertAlmostEqual(float(np.linalg.norm(offset.V0)), 1, places=12)

    def test_finite_tube_collet_proof_rejects_centerline_only_clearance(self):
        from clamps import exit_proof
        controls=[offset.control(g,h) for g in (21.4,31.4)
                  for h in (offset.handle(31.4)-1e-7,offset.handle(21.4)+1e-7)]
        proof=exit_proof(controls,offset.V0,offset.V1,1.2954)
        self.assertGreater(proof['m_squared_minus_rM'],3478)
        # Every control point progresses in +X, so a centerline half-space
        # assertion passes, but this sharp transverse bend clips the annulus.
        tight=np.array([[0.,0,0],[1.,0,0],[1.001,10,0],[2.001,10,0]])
        self.assertTrue(np.all(np.diff(tight[:,0])>0))
        with self.assertRaisesRegex(ValueError,'finite wire tube'):
            exit_proof([tight],np.array([1.,0,0]),np.array([1.,0,0]),1.2954)

    def test_budget_does_not_pass_using_unqualified_110mm_main(self):
        d = check.read(check.ROOT/'design/partition/partition-input.json')['load_distribution']
        self.assertAlmostEqual(check.path_drop(2.1, 4.6, 104, 78, d, .00015, .0002), 19.7672)
        self.assertGreater(check.path_drop(2.1, 4.6, 110, 78, d, .00015, .0002), 20)
        self.assertGreater(check.path_drop(2.1, 4.6, 104, 78, d), 20)

    def test_geometry_cannot_grant_native_or_physical_acceptance(self):
        p = json.loads((Path(__file__).parent/'offset-proposal.json').read_text())
        self.assertFalse(p['accepted'])
        for gate in ('face_contract', 'actual_copper', 'native', 'all_100_trim_access'):
            self.assertFalse(p['gates'][gate])


if __name__ == '__main__':
    unittest.main()
