"""MC04-S8 Part A: the open re-placement study is current and its classes follow its own figures (no KiCad)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402

DOC = json.loads(rp.OUT.read_text())


class Study(unittest.TestCase):
    def test_result_is_a_fresh_build(self):
        self.assertEqual(json.dumps(rp.build(), indent=1) + '\n', rp.OUT.read_text())

    def test_covers_the_fifteen_open_replacements(self):
        # the Gate A list of the study's snapshot (MC04-S10: the current list no longer holds U5209 and U5210)
        items = [i for i in json.loads((rp.snapshot_root() / 'design/stack/gate-a-open-items.json').read_text())['items']
                 if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual([(r['board'], r['ic']) for r in DOC['ics']], [(i['board'], i['ref']) for i in items])
        self.assertEqual(len(DOC['ics']), 15)
        self.assertEqual(sum(DOC['counts'].values()), 15)

    def test_blocks_carry_their_decouplers(self):
        for r in DOC['ics']:
            self.assertEqual(r['block']['members'][0], r['ic'])
            self.assertTrue(r['block']['decouplers'], r['ic'])
            self.assertTrue(set(r['block']['decouplers']) <= set(r['block']['members']))

    def test_classes_follow_the_figures(self):
        for r in DOC['ics']:
            c = r.get('chosen')
            if r['class'] == '(i)':
                self.assertLessEqual(c['moved_mm'], rp.LIMIT_MM)
                self.assertNotIn('displaces', c)
            elif r['class'] == '(ii)':
                self.assertGreater(c['moved_mm'], rp.LIMIT_MM)
                self.assertNotIn('displacing_option', r)
                self.assertIn('locality_condition', r)
                self.assertEqual(min(x['moved_mm'] for x in r['nearest_legal']), c['moved_mm'])
            elif r['class'] == '(iii)':
                self.assertLessEqual(c['moved_mm'], rp.LIMIT_MM)
                self.assertGreater(min(x['moved_mm'] for x in r['nearest_legal']), rp.LIMIT_MM)
                self.assertTrue(c['displaces'])
                self.assertTrue(all(x[:1] in 'RCD' for x in c['displaces']))
                self.assertEqual([m['ref'] for m in r['displaced_moves']], c['displaces'])
                self.assertTrue(all(m['origin'] is not None for m in r['displaced_moves']), r['ic'])
            else:
                self.assertIsNone(c)

    def test_region_fill_is_reported(self):
        for board in ('K', 'JL', 'JR'):
            self.assertTrue(DOC['region_fill'][board])


if __name__ == '__main__':
    unittest.main()
