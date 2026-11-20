import json
import unittest
from pathlib import Path

import shift_replace as s

R = json.loads((Path(__file__).with_name('result.json')).read_text())


class Tests(unittest.TestCase):
    def test_geo_clash(self):
        g = {'front_connector': [0, 0, 1, 1], 'front_tail': [0, 1, 1, 2], 'slot': [0, 2, 1, 3],
             'K_connector': [5, 5, 6, 6], 'K_tail': [5, 4, 6, 5]}
        h = {k: [v[0] + 0.5, v[1], v[2] + 0.5, v[3]] for k, v in g.items()}
        self.assertTrue(s.geo_clash(g, h, 'JL', 'JL'))
        far = {k: [v[0] + 50, v[1], v[2] + 50, v[3]] for k, v in g.items()}
        self.assertFalse(s.geo_clash(g, far, 'JL', 'JR'))

    def test_net_is_failed_minus_freed(self):
        for v in R['results'].values():
            for c in v['candidates']:
                self.assertEqual(c['net_unresolved_change'], len(c['left_without_place']) - len(c['freed_unresolved']))

    def test_combined_uses_only_improving_links(self):
        c = R['combined_improving_moves']
        want = sorted(k for k, v in R['results'].items() if v['best'] and v['best']['net_unresolved_change'] < 0)
        self.assertEqual(c['links'], want)
        self.assertEqual(c['link_clashes'], [])


if __name__ == '__main__':
    unittest.main()
