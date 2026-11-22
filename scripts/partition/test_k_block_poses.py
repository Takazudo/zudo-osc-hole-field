"""MC04-S7: the K poses of the moved function blocks."""
import json
import math
import unittest

from scripts.partition import k_block_poses as kb


class Poses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reloc, cls.out = kb.poses()
        cls.committed = {b['ic']: b['k_poses'] for b in json.loads(kb.RELOCATION.read_text())['blocks']}

    def test_committed_poses_are_fresh(self):
        self.assertEqual(self.committed, self.out)

    def test_every_member_has_a_pose_on_one_face_near_its_ic(self):
        for b in self.reloc['blocks']:
            poses = self.out[b['ic']]
            self.assertEqual(set(poses), set(b['members']))
            self.assertEqual(len({p['side'] for p in poses.values()}), 1, b['ic'])
            ic = poses[b['ic']]
            far = max(math.hypot(p['x_mm'] - ic['x_mm'], p['y_mm'] - ic['y_mm']) for p in poses.values())
            self.assertLessEqual(far, 16.0, b['ic'])

    def test_a_full_board_fails_clearly(self):
        real = kb.nearest
        kb.nearest = lambda grid, masks, target: None
        try:
            with self.assertRaisesRegex(ValueError, 'no room for the IC on K'):
                kb.poses()
        finally:
            kb.nearest = real


if __name__ == '__main__':
    unittest.main()
