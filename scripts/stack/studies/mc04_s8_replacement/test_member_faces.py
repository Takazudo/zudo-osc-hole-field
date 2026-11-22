"""MC04-S8 Revisions 6 to 8: every placed link-era pose has a computed face-aware check, and the record carries it."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import member_faces as mf  # noqa: E402
import replacement as rp  # noqa: E402

REC = json.loads((rp.ROOT / 'design/stack/geometry/links/link-era-replacements.json').read_text())
DOC = json.loads(mf.OUT.read_text())


class MemberFaces(unittest.TestCase):
    def test_current(self):
        self.assertEqual(json.dumps(mf.build(), indent=1) + '\n', mf.OUT.read_text())

    def test_every_placed_pose_is_checked_and_clear(self):
        checked = {(b['board'], b['ic']): b for b in DOC['blocks']}
        for r in REC['placed']:
            b = checked[(r['board'], r['ic'])]
            self.assertTrue(b['all_clear'], r['ic'])
            self.assertEqual(r['member_face_check']['all_clear'], b['all_clear'])
            self.assertEqual(r['member_face_check']['source'], 'member-faces.json (computed)')

    def test_every_mixed_face_block_in_the_record_is_checked(self):
        s = rp.Study()
        checked = {(b['board'], b['ic']) for b in DOC['blocks']}
        for r in REC['placed']:
            ic_side = s.fps[(r['board'], r['ic'])]['side']
            if any(s.fps[(r['board'], m)]['side'] != ic_side for m in r['block']):
                self.assertIn((r['board'], r['ic']), checked)
        mixed = [b for b in DOC['blocks'] if b['other_face_members']]
        for b in mixed:
            self.assertTrue(all(x['blocked_by'] is None for x in b['other_face_members']), b['ic'])

    def test_far_options_overlap_report(self):
        self.assertTrue(DOC['far_option_overlaps'])
        for o in REC['open']:
            for other in o.get('far_option_overlaps', []):
                self.assertIn(other, DOC['far_options'])


if __name__ == '__main__':
    unittest.main()
