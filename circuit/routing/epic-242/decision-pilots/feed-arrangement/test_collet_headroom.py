import math
import unittest
from unittest.mock import patch

import collet_headroom as h


class ColletHeadroomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = h.calculate()

    def test_axis_boundary_has_passing_and_failing_sides(self):
        angle = self.result['one_variable_local_boundaries']['axis_half_cone_pass_boundary_deg']
        args = (1.95, 1, 2, .5445913286478836)
        self.assertGreater(h.remaining_gap(*args, math.radians(angle-.001), .35), .25)
        self.assertLess(h.remaining_gap(*args, math.radians(angle+.001), .35), .25)

    def test_total_headroom_is_single_shared_pool(self):
        rows = self.result['one_closure_at_a_time']
        room = self.result['current_local_board_bound']['single_shared_headroom_mm']
        for row in rows:
            self.assertAlmostEqual(row['one_at_a_time_boundary_mm']-row['current_mm'], room)
        counter = self.result['counterexamples']['spending_full_shared_headroom_on_two_closures']
        self.assertFalse(counter['meets_residual_criterion'])

    def test_local_angular_pass_does_not_relax_shape_or_cut(self):
        row = next(q for q in self.result['axis_sensitivity'] if q['axis_cone_deg'] == 2)
        self.assertTrue(row['local_board_bound_pass'])
        self.assertFalse(row['within_current_C1_requirement'])
        self.assertFalse(row['diagnostic_shape_radius_bound_pass'])
        self.assertFalse(row['diagnostic_preparation_bound_pass'])

    def test_larger_cylinder_boundary_and_nearby_violation(self):
        bound = self.result['one_variable_local_boundaries']['maximum_outer_radius_mm']
        angle = math.asin(.01)
        self.assertAlmostEqual(h.remaining_gap(1.95, 1, bound, .5445913286478836, angle, .35), .25)
        self.assertLess(h.remaining_gap(1.95, 1, bound+.001, .5445913286478836, angle, .35), .25)

    def test_unmodeled_exterior_extension_can_consume_the_margin(self):
        self.assertFalse(self.result['counterexamples']['unmodeled_0p25mm_extension_toward_board']['meets_residual_criterion'])

    def test_no_qualification_or_permission_is_created(self):
        self.assertFalse(self.result['accepted'])
        self.assertEqual(len(self.result['qualification_ledger']), 11)
        for row in self.result['qualification_ledger']:
            self.assertFalse(row['qualified'])
            self.assertIsNone(row['qualification_evidence'])
        for name, value in self.result['gates'].items():
            if name not in ('source_bindings_verified', 'conditional_local_headroom_arithmetic'):
                self.assertFalse(value, name)

    def test_nonfinite_or_infeasible_inputs_rejected(self):
        with self.assertRaises(ValueError):
            h.remaining_gap(1.95, 1, 2, .5, float('nan'), .35)
        with self.assertRaises(ValueError):
            h.limiting_axis_angle(1, 1, 2, .5, .35, .25)

    def test_changed_persisted_source_evidence_is_rejected(self):
        original_read = h.base.read
        def changed_read(path):
            result = original_read(path)
            if path.name == 'collet-clearance.json':
                result['board_bound']['required_residual_mm'] = 0
            return result
        with patch.object(h.base, 'read', side_effect=changed_read):
            with self.assertRaisesRegex(ValueError, 'collet source evidence drift'):
                h.calculate()


if __name__ == '__main__':
    unittest.main()
