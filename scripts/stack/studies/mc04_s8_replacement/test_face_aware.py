"""MC04-S8 Revision 7: the face-aware search keeps each block member on its own face (synthetic mixed-face block)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402


class FakeField:
    """One obstacle, on face B only, at (5, 5)-(6, 6)."""

    def blocked(self, board, face, cy, pads):
        hit = face == 'B' and cy[0] < 6 and 5 < cy[2] and cy[1] < 6 and 5 < cy[3]
        return 'obstacle on B' if hit else None


def study(face_aware):
    s = rp.Study.__new__(rp.Study)
    s.face_aware = face_aware
    s.fps = {('K', 'U1'): {'origin': [0.0, 0.0], 'side': 'F', 'courtyard': [-1.0, -1.0, 1.0, 1.0]},
             ('K', 'R1'): {'origin': [5.5, 5.5], 'side': 'B', 'courtyard': [5.2, 5.2, 5.8, 5.8]},
             ('K', 'C1'): {'origin': [2.0, 0.0], 'side': 'F', 'courtyard': [1.6, -0.4, 2.4, 0.4]}}
    return s


class FaceAware(unittest.TestCase):
    def test_other_face_member_meets_the_obstacle_on_its_own_face(self):
        for aware, expect in ((True, False), (False, True)):
            s = study(aware)
            sh = s.shapes('K', ['U1', 'C1', 'R1'], 'F', 'U1')
            self.assertEqual(s.legal(FakeField(), 'K', 'F', sh['F'], 0.0, 0.0), expect, aware)

    def test_members_flip_with_the_block(self):
        s = study(True)
        s.shapes('K', ['U1', 'C1', 'R1'], 'F', 'U1')
        self.assertEqual([s.mf('K', r, 'F') for r in ('U1', 'C1', 'R1')], ['F', 'F', 'B'])
        self.assertEqual([s.mf('K', r, 'B') for r in ('U1', 'C1', 'R1')], ['B', 'B', 'F'])

    def test_flipped_block_puts_the_member_on_the_free_face(self):
        s = study(True)
        sh = s.shapes('K', ['U1', 'C1', 'R1'], 'F', 'U1')
        # the block on B is mirrored about the IC origin; R1 then lies on F, clear of the B obstacle
        self.assertTrue(s.legal(FakeField(), 'K', 'B', sh['B'], 0.0, 0.0))
        # shifted so that the mirrored IC (on B) sits on the obstacle, the pose is rejected
        self.assertFalse(s.legal(FakeField(), 'K', 'B', sh['B'], 5.5, 5.5))


if __name__ == '__main__':
    unittest.main()
