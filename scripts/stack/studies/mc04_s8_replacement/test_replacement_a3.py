"""MC04-S8 Part A3: the block-on-block rule for the last four ICs (no KiCad)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a3 as a3  # noqa: E402

DOC = json.loads(a3.OUT.read_text())


class BlockOnBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = a3.A3()
        cls.s.prepare()

    def test_targets(self):
        self.assertEqual([r['ic'] for r in DOC['targets']], list(a3.TARGETS))

    def test_moved_blocks_follow_the_rule(self):
        for r in DOC['targets']:
            if r['result'] != 'fits within 24 mm':
                continue
            self.assertLessEqual(r['pose']['moved_mm'], rp.LIMIT_MM)
            self.assertLessEqual(len(r['blocks_moved']), a3.MAX_BLOCKS)
            for b in r['blocks_moved']:
                self.assertLessEqual(b['moved_mm'], rp.LIMIT_MM)
                self.assertIn(b['turn_deg'], (0, 90, 180, 270))
                self.assertNotIn(b['ic'], self.s.buffer_ics)
                # rigid: the moved block carries exactly its own members (decouplers and cell-local passives)
                self.assertEqual(b['members'], self.s.ic_members[(r['board'], b['ic'])])
            for m in r['passives_moved']:
                self.assertLessEqual(m['moved_mm'], rp.LIMIT_MM)
                self.assertTrue(self.s.evictable2(r['board'], m['ref']))

    def test_input_buffers_are_never_displaced(self):
        self.assertTrue(self.s.buffer_ics)
        for r in DOC['targets']:
            self.assertFalse({b['ic'] for b in r.get('blocks_moved', [])} & self.s.buffer_ics)

    def test_targets_beyond_24_mm_name_their_smallest_obstacle_set(self):
        for r in DOC['targets']:
            if r['result'] == 'fits within 24 mm':
                continue
            s = r['smallest_obstacle_set']
            self.assertGreaterEqual(s['count'], 1)
            self.assertEqual(sum(s['by_type'].values()), s['count'])
            self.assertLessEqual(s['pose']['moved_mm'], rp.LIMIT_MM)
            self.assertTrue(r['trial_failures'] or r['candidates'] == 0)

    def test_owner_map_assigns_decouplers_to_their_ic(self):
        for (b, ic), ms in list(self.s.ic_members.items())[:200]:
            for m in ms:
                if self.s.pk.get(m, {}).get('decouples_ref') == ic:
                    self.assertEqual(self.s.owner[(b, m)], ic)

    def test_result_is_a_fresh_build(self):
        self.assertEqual(json.dumps(a3.build(), indent=1) + '\n', a3.OUT.read_text())


if __name__ == '__main__':
    unittest.main()
