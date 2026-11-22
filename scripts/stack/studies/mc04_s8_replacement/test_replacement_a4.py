"""MC04-S8 Part A4: each of the three narrow relaxations applies to its own target only (no KiCad)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a4 as a4  # noqa: E402

DOC = json.loads(a4.OUT.read_text())
T = {r['ic']: r for r in DOC['targets']}


class Relaxations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = a4.A4()
        cls.s.prepare()

    def test_each_relaxation_is_scoped_to_its_target(self):
        s = self.s
        # C5210 (a 1206 capacitor) is displaceable only for U5210
        for mode, expect in ((None, False), ('U5209', False), ('U8409', False), ('U5210', True)):
            s.mode = mode
            self.assertEqual(s.evictable2('K', 'C5210'), expect, mode)
        # R8263, already re-placed by the gate, is a fixed obstacle except for U5209
        row = next(r for r in s.gate['replacement']['footprints'] if r['ref'] == 'R8263')
        f = s.build_field()
        for mode, fixed_expected in ((None, True), ('U5210', True), ('U5209', False)):
            s.mode = mode
            fixed, fps = s.obstacles(f, 'K', row['new_face'], [('R8263', row['new_courtyard'])], 0.0, 0.0)
            self.assertEqual(('ruled or re-placed part', 'R8263') in fixed, fixed_expected, mode)
            self.assertEqual('R8263' in fps, not fixed_expected, mode)
        s.mode = None

    def test_r8263_rule(self):
        m = next(x for x in T['U5209']['passives_moved'] if x['ref'] == 'R8263')
        r = m['relaxation']
        self.assertLessEqual(r['from_6093081c_mm'], rp.LIMIT_MM)
        self.assertLessEqual(r['to_U8211_after_mm'], r['to_U8211_before_mm'])
        ok, _ = self.s.partner_ok('K', 'R8263', (m['origin'][0], m['origin'][1]))
        self.assertTrue(ok)
        far, _ = self.s.partner_ok('K', 'R8263', (self.s.p0['R8263']['x_mm'] + 30.0, self.s.p0['R8263']['y_mm']))
        self.assertFalse(far)

    def test_c5210_high_impedance_side(self):
        o = self.s.fps[('K', 'C5210')]['origin']
        self.assertEqual(self.s.hiz_added('K', 'C5210', tuple(o)), 0.0)
        self.assertGreaterEqual(self.s.hiz_added('K', 'C5210', (o[0] + 40.0, o[1] + 40.0)), a4.HIZ_LIMIT_MM)
        for m in T['U5210'].get('passives_moved', []):
            if m['ref'] == 'C5210':
                self.assertLess(m['relaxation']['added_run_estimate_mm'], a4.HIZ_LIMIT_MM)

    def test_chain_is_only_for_u8409_and_never_moves_u8412_beyond_24_mm(self):
        self.assertIn('chain_search', T['U8409']) if T['U8409']['result'] != 'fits within 24 mm' else None
        for ic, r in T.items():
            if ic != 'U8409':
                self.assertNotIn('chain', r)
            for b in r.get('blocks_moved', []):
                self.assertLessEqual(b['moved_mm'], rp.LIMIT_MM)
                self.assertNotIn(b['ic'], self.s.buffer_ics)

    def test_outcome_is_reported(self):
        self.assertEqual(DOC['all_within_rules'], all(r['result'] == 'fits within 24 mm' for r in DOC['targets']))
        for r in DOC['targets']:
            if r['result'] != 'fits within 24 mm':
                self.assertGreaterEqual(r['smallest_obstacle_set']['count'], 1)

    def test_result_is_a_fresh_build(self):
        self.assertEqual(json.dumps(a4.build(), indent=1) + '\n', a4.OUT.read_text())


if __name__ == '__main__':
    unittest.main()
