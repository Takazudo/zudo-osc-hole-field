"""Current J source bridge rejects changed native copper support and drills."""
import copy
import unittest

from scripts.pcbgen.verify_jack_source_geometry_epoch import compare_epoch,verify


class JackGroundSourceEpochTest(unittest.TestCase):
    def test_current_exact_nominal_source_bridge(self):
        report=verify()
        self.assertEqual(report['boards']['osc-jack-left']['single_drill_SMD_nominal_covers'],84)
        self.assertEqual(report['boards']['osc-jack-right']['multi_drill_SMD_nominal_covers'],1)
        self.assertIn('boards/osc-jack-left/sheets/board_power_flags_JL.kicad_sch',report['source_sha256'])
        self.assertIn('boards/osc-jack-right/sheets/board_power_flags_JR.kicad_sch',report['source_sha256'])
        self.assertIn('only',report['status'])


if __name__ == '__main__':
    unittest.main()
