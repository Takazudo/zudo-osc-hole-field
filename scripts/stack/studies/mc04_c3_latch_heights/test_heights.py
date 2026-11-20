import json
import unittest
from pathlib import Path

import heights

HERE = Path(__file__).resolve().parent


class Heights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = heights.run()

    def test_matches_retained_result(self):
        self.assertEqual(self.out, json.loads((HERE / 'result.json').read_text()))

    def test_every_case_accounted(self):
        self.assertEqual(sum(self.out['tally'].values()), 31)

    def test_lower_cases_have_all_neighbours_sourced_below_body(self):
        lim = self.out['closed_height_min_mm']
        for c in self.out['cases']:
            if c['verdict'].startswith('LOWER'):
                if c['verdict'].endswith('(sourced)'):
                    self.assertFalse(c['open_items'])
                self.assertTrue(all(n['max_mm'] is not None and n['max_mm'] < lim for n in c['neighbours']))

    def test_missing_height_stays_not_shown(self):
        ev = json.loads((HERE / 'evidence.json').read_text())
        for c in self.out['cases']:
            if any(ev['heights'].get(n['mpn']) is None for n in c['neighbours']):
                self.assertEqual(c['verdict'], 'NOT SHOWN')

    def test_changed_source_fails(self):
        ev = json.loads((HERE / 'evidence.json').read_text())
        ev['heights']['BAT54S,215']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            heights.verify_sources(ev)


if __name__ == '__main__':
    unittest.main()
