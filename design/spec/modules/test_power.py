"""Pin-map and ordering boundary checks for the conditional EXT inlet."""
import unittest

from design.spec.modules.power import family


class PowerInletTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = {part.key: part for part in family().parts}

    def test_logical_inlet_matches_requirement_contract(self):
        pins = self.parts['INLET'].pins
        self.assertEqual(pins, {
            '1': '+12V_IN', '2': '-12V_IN', '3': '+5V_IN', '4': None,
            '5': 'AGND', '6': 'AGND', '7': 'AGND', '8': 'AGND',
        })

    def test_boundary_exposes_distinct_raw_and_load_rails(self):
        self.assertEqual(self.parts['BOUNDARY'].pins, {
            '1': '+12V_IN', '2': '-12V_IN', '3': '+5V_IN',
            '4': '+12V', '5': '-12V', '6': '+5V', '7': 'AGND',
        })
        self.assertFalse({'PTC_P12', 'PTC_N12', 'PTC_P5'} & self.parts.keys())

    def test_abstract_symbols_cannot_be_ordered_or_placed(self):
        for key in ('INLET', 'BOUNDARY'):
            part = self.parts[key]
            self.assertTrue(part.abstract)
            self.assertFalse(part.in_bom)
            self.assertEqual(part.footprint, '')
            self.assertEqual(part.attributes['MPN'], '')
            self.assertEqual(part.attributes['Implementation'],
                             'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE')

    def test_local_filter_bleeder_and_probe_per_rail(self):
        for key, rail in (('P12', '+12V'), ('N12', '-12V'), ('P5', '+5V')):
            for prefix in ('C100N_', 'C1U_', 'BLEED_'):
                self.assertEqual(self.parts[prefix + key].pins,
                                 {'1': rail, '2': 'AGND'})
            self.assertEqual(self.parts['TP_' + key].pins, {'1': rail})
        self.assertEqual(self.parts['TP_GND'].pins, {'1': 'AGND'})


if __name__ == '__main__':
    unittest.main()
