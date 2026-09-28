"""Ensure #34 conditional savings cannot be booked as a rail maximum."""
import unittest
from scripts.schgen.analyze_rail_options import build


class RailOptions(unittest.TestCase):
    def test_actual_counts_and_fourth_case_gap(self):
        report=build();counts=report['captured_counts']
        self.assertEqual((counts['OPA4197IPWR_quads'],counts['OPA4196IDR_quads'],
                          counts['B104_100k_DC_pots']), (79,174,48))
        self.assertEqual((counts['magnitude_LEDs'],counts['clip_LEDs'],counts['stage_LEDs']),(92,10,12))
        self.assertEqual(report['practical_indicator_dimming_diagnostic_mA_per_analog_rail'],64.8)
        self.assertEqual(report['booked_savings_mA'],{'+12V':0,'-12V':0,'+5V':0})
        self.assertTrue(all(x is None for x in report['guaranteed_maximum_mA'].values()))
        for case in report['cases']:
            self.assertGreater(case['remaining_mA']['-12V'],report['ceilings_mA']['-12V'])
        self.assertAlmostEqual(report['non_additive_packing_stress_test']['hypothetical_remaining_mA']['-12V']-640,71.16866)

if __name__=='__main__':unittest.main()
