"""MC04-S8 Part A2: the widened search for the seven class (ii) ICs (no KiCad)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402

DOC = json.loads(a2.OUT.read_text())


class Rotation(unittest.TestCase):
    def test_four_quarter_turns_return_the_rectangle(self):
        r, o = [10.0, 20.0, 14.0, 23.0], (11.0, 21.0)
        self.assertEqual([round(v, 4) for v in a2.rot(r, o, 360)], r)
        t = a2.rot(r, o, 90)
        self.assertAlmostEqual(t[2] - t[0], r[3] - r[1])
        self.assertAlmostEqual(t[3] - t[1], r[2] - r[0])
        x, y = a2.rot_pt((14.0, 21.0), o, 90)
        self.assertAlmostEqual((x, y), (11.0, 24.0))

    def test_every_orientation_was_searched(self):
        for r in DOC['ics']:
            seen = {(c['face'], c['turn_deg']) for c in r['nearest_legal_by_orientation']}
            self.assertTrue(seen, r['ic'])
            self.assertTrue({c['turn_deg'] for c in r['nearest_legal_by_orientation']} <= set(a2.TURNS))
            self.assertEqual(r['within_24mm']['poses_checked'] % 8, 0)  # 2 faces x 4 turns per offset
            best = min(c['moved_mm'] for c in r['nearest_legal_by_orientation'])
            self.assertLessEqual(best, r['part_a']['moved_mm'] + 1e-9, r['ic'])  # never worse than Part A


class Displacement(unittest.TestCase):
    def test_displaced_parts_follow_the_widened_rule(self):
        s = a2.A2()
        s.setup()
        for r in DOC['ics']:
            c = r['chosen'] or {}
            for m in c.get('displaced_moves', []):
                self.assertLessEqual(m['moved_mm'], rp.LIMIT_MM)
                self.assertTrue(s.evictable2(r['board'], m['ref']), m['ref'])
                self.assertIsNone(s.pk[m['ref']].get('decouples_ref'))

    def test_classes_and_facts(self):
        self.assertEqual([r['ic'] for r in DOC['ics']], list(a2.CLASS_II))
        for r in DOC['ics']:
            c = r['chosen']
            if r['class'] == '(iii)':
                self.assertLessEqual(c['moved_mm'], rp.LIMIT_MM)
                self.assertTrue(c['displaces'])
            if c and c['moved_mm'] > rp.LIMIT_MM:
                self.assertTrue(r['electrical'], r['ic'])
                for e in r['electrical']:
                    self.assertAlmostEqual(e['capacitance_after_estimate_pF'], round(e['run_after_estimate_mm'] * a2.PF_PER_MM, 2), delta=0.02)
        u = next(r for r in DOC['ics'] if r['ic'] == 'U4647')
        self.assertTrue(u['leds'])
        for ic in ('U1318', 'U8409', 'U4647'):
            self.assertIn('input_buffer_conditions', next(r for r in DOC['ics'] if r['ic'] == ic))

    def test_result_is_a_fresh_build(self):
        self.assertEqual(json.dumps(a2.build(), indent=1) + '\n', a2.OUT.read_text())


if __name__ == '__main__':
    unittest.main()
