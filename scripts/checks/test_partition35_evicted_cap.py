"""MC04-S6: evicted jack-board diodes are re-placed nearest-legal-first within the 24 mm locality."""
import math
import unittest

from scripts.checks import partition35_floorplan as fp


class EvictedDiodeCap(unittest.TestCase):
    def test_only_jack_board_diodes_use_nearest_first(self):
        self.assertTrue(fp.nearest_first('D4309', 'JR'))
        self.assertTrue(fp.nearest_first('D1201', 'JL'))
        self.assertFalse(fp.nearest_first('R8325', 'JR'))
        self.assertFalse(fp.nearest_first('D5201', 'K'))

    def test_nearest_ranking_orders_by_distance_and_ignores_cost(self):
        offsets = [(0.0, 20.0), (5.0, 0.0), (0.0, -3.0), (30.0, 0.0)]
        cost = lambda dx, dy: -math.hypot(dx, dy)  # noqa: E731  a cost that prefers far poses
        ranked = fp.ranked_offsets(offsets, cost, nearest=True)
        self.assertEqual([(dx, dy) for _, dx, dy in ranked], [(0.0, -3.0), (5.0, 0.0), (0.0, 20.0)])
        self.assertEqual([k for k, _, _ in ranked], [3.0, 5.0, 20.0])

    def test_offsets_beyond_the_cap_are_never_candidates(self):
        offsets = [(fp.CLUSTER_RADIUS_MM, 0.0), (fp.CLUSTER_RADIUS_MM + 0.5, 0.0), (0.0, 0.5)]
        for nearest in (True, False):
            ranked = fp.ranked_offsets(offsets, lambda dx, dy: 0.0, nearest=nearest)
            self.assertNotIn((fp.CLUSTER_RADIUS_MM + 0.5, 0.0), [(dx, dy) for _, dx, dy in ranked])
        self.assertEqual(fp.CLUSTER_RADIUS_MM, 24.0)

    def test_growth_ranking_is_unchanged_for_other_parts(self):
        offsets = [(0.0, 20.0), (5.0, 0.0)]
        ranked = fp.ranked_offsets(offsets, lambda dx, dy: abs(dy - 20.0), nearest=False)
        self.assertEqual([(dx, dy) for _, dx, dy in ranked], [(0.0, 20.0), (5.0, 0.0)])


if __name__ == '__main__':
    unittest.main()
