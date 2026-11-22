"""MC04-S8 Revisions 6 and 7: every confirmed block passes the face-aware member check."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import member_faces as mf  # noqa: E402


class MemberFaces(unittest.TestCase):
    def test_current(self):
        self.assertEqual(json.dumps(mf.build(), indent=1) + '\n', mf.OUT.read_text())

    def test_every_confirmed_block_is_clear(self):
        doc = json.loads(mf.OUT.read_text())
        self.assertEqual(len(doc['blocks']), 6)  # five confirmed poses and the U4502 block
        for b in doc['blocks']:
            self.assertTrue(b['all_clear'], b['ic'])
            self.assertEqual(b['blocked_members'], [])


if __name__ == '__main__':
    unittest.main()
