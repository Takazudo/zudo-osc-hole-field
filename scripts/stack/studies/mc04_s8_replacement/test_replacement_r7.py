"""MC04-S8 Revision 7: the face-aware re-search record is current and its outcomes follow its figures."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402

DOC = json.loads(r7.OUT.read_text())


class R7Record(unittest.TestCase):
    def test_current(self):
        self.assertEqual(json.dumps(r7.build(), indent=1) + '\n', r7.OUT.read_text())

    def test_face_aware_and_model(self):
        self.assertTrue(DOC['face_aware'])
        self.assertEqual(DOC['model'], rp.MODEL)
        self.assertEqual(len(DOC['confirmed_first']), 5)

    def test_outcomes(self):
        self.assertEqual([r['ic'] for r in DOC['research']], list(r7.RESEARCH_A) + ['U5209'])
        for r in DOC['research']:
            if r['result'] == 'lands':
                self.assertLessEqual(r['pose']['moved_mm'], rp.LIMIT_MM)
                self.assertEqual(r['reason'], r7.REASON)
            else:
                self.assertEqual(r['result'], 'OPEN (link era)')
                self.assertIn('grid_caveat', r['proof'])
                if r.get('cheapest_option'):
                    self.assertGreater(r['cheapest_option']['pose']['moved_mm'], rp.LIMIT_MM)
                    self.assertTrue(r['cheapest_option']['electrical'])
        j = DOC['joint']
        if not j['placed']:
            self.assertFalse(j['runs'][0]['found'])
            for t, o in j['far_poses'].items():
                if o:
                    self.assertGreater(o['pose']['moved_mm'], rp.LIMIT_MM)


if __name__ == '__main__':
    unittest.main()
