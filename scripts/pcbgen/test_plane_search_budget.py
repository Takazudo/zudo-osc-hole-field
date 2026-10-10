"""The single plane-fanout window must expose its own bounded search budget."""
import unittest
from unittest.mock import patch
from scripts.pcbgen.grid_router import route
from scripts.pcbgen.test_grid_router import board


class PlaneSearchBudgetTests(unittest.TestCase):
    def limits(self, plane=True, **kwargs):
        limits = []
        def exhausted(free, via_ok, src, goal, layer_cost, via_cost, limit, *args):
            limits.append(limit)
            return None, limit + 1
        events = []
        with patch('scripts.pcbgen.grid_router.astar', side_effect=exhausted):
            results, removed = route(board(), ['A'], res=.1,
                planes={'A': 'In1.Cu'} if plane else None,
                allowed_layers=['B.Cu'], diagnostics=events, log=lambda _: None, **kwargs)
        self.assertFalse(removed)
        self.assertTrue(results)
        self.assertTrue(all(r['path'] is None for r in results))
        self.assertTrue(events)
        self.assertEqual(limits, [a['limit'] for e in events for a in e['attempts']])
        return limits

    def test_explicit_plane_budget_reaches_astar_and_diagnostics(self):
        self.assertEqual(self.limits(max_expansions=5_000_000,
            plane_max_expansions=5_000_000), [5_000_000, 5_000_000])

    def test_default_and_global_bound_remain_in_force(self):
        self.assertEqual(self.limits(max_expansions=5_000_000), [300_000, 300_000])
        self.assertEqual(self.limits(max_expansions=7,
            plane_max_expansions=5_000_000), [7, 7])

    def test_plane_budget_does_not_change_signal_attempts(self):
        before = self.limits(plane=False, max_expansions=5_000_000)
        after = self.limits(plane=False, max_expansions=5_000_000,
                            plane_max_expansions=5_000_000)
        self.assertEqual(before, after)
        self.assertIn(300_000, after)
        self.assertIn(5_000_000, after)

    def test_plane_budget_must_be_a_positive_integer(self):
        for value in (0, -1, .5, float('inf'), float('nan'), True):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'positive integer'):
                route(board(), plane_max_expansions=value)


if __name__ == '__main__':
    unittest.main()
