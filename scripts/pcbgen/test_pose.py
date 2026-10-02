"""Test source precedence without importing the native KiCad module."""
import unittest
from scripts.pcbgen.pose import SourcePose, source_pose


class SourcePoseTests(unittest.TestCase):
    def test_fixed_hardware_has_exact_lock_pose_without_optional_fields(self):
        self.assertEqual(source_pose({}, 180), SourcePose('F.Cu', 180, True))

    def test_equivalent_full_turn_does_not_replace_lockfile_angle(self):
        for angle in ('-180', '180', '540'):
            self.assertEqual(source_pose({'KiCadOrientationDeg': angle}, 180).orientation, 180)

    def test_conflicting_hardware_fields_are_rejected(self):
        for fields in ({'BoardSide': 'B.Cu'}, {'KiCadOrientationDeg': '90'}):
            with self.assertRaises(ValueError):
                source_pose(fields, 0)

    def test_free_pose_is_unchanged_without_explicit_directive(self):
        self.assertEqual(source_pose({}), SourcePose(None, None, False))
        self.assertEqual(source_pose({'BoardSide': 'B.Cu', 'KiCadOrientationDeg': '37'}),
                         SourcePose('B.Cu', 37, False))

    def test_source_origin_locking_retains_existing_region_policy(self):
        self.assertTrue(source_pose({'FootprintOriginMm': '1,2'}).force_lock)
        self.assertFalse(source_pose({'FootprintOriginMm': '1,2', 'BoardRegion': 'cell'}).force_lock)

    def test_invalid_angles_and_sides_fail_before_native_mutation(self):
        for angle in ('nan', 'inf', '-inf', 'broken', None, True):
            with self.subTest(angle=angle), self.assertRaises(ValueError):
                source_pose({'KiCadOrientationDeg': angle})
        with self.assertRaises(ValueError):
            source_pose({'BoardSide': 'In1.Cu'})


if __name__ == '__main__':
    unittest.main()
