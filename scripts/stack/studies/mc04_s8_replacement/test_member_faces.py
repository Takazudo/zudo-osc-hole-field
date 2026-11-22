"""MC04-S8 Revision 6 follow-up: the other-face member check is current and covers every mixed-face block."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import member_faces as mf  # noqa: E402
import replacement as rp  # noqa: E402


class MemberFaces(unittest.TestCase):
    def test_current(self):
        self.assertEqual(json.dumps(mf.build(), indent=1) + '\n', mf.OUT.read_text())

    def test_every_mixed_face_block_is_checked(self):
        s = rp.Study()
        rec = json.loads(mf.REC.read_text())
        mixed = {r['ic'] for r in rec['placed']
                 if any(s.fps[(r['board'], m)]['side'] != s.fps[(r['board'], r['ic'])]['side'] for m in r['block'])}
        doc = json.loads(mf.OUT.read_text())
        self.assertEqual({b['ic'] for b in doc['blocks']}, mixed)
        for b in doc['blocks']:
            self.assertEqual(b['all_clear'], all(x['blocked_by'] is None for x in b['other_face_members']))


if __name__ == '__main__':
    unittest.main()
