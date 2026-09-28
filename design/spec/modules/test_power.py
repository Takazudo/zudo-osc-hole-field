"""Pin-map and protective-polarity checks for the draft power inlet."""
import unittest

from design.spec.modules.power import family


class PowerInletTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = {part.key: part for part in family().parts}

    def test_connector_is_exact_supply_contract(self):
        pins = self.parts['INLET'].pins
        self.assertEqual({pins[str(i)] for i in (1, 2)}, {'IN_N12'})
        self.assertEqual({pins[str(i)] for i in range(3, 9)}, {'AGND'})
        self.assertEqual({pins[str(i)] for i in (9, 10)}, {'IN_P12'})
        self.assertEqual({pins[str(i)] for i in (11, 12)}, {'IN_P5'})
        self.assertTrue(all(pins[str(i)] is None for i in range(13, 17)))

    def test_each_rail_passes_through_its_own_ptc(self):
        for key, incoming, output in (
            ('P12', 'IN_P12', '+12V'),
            ('N12', 'IN_N12', '-12V'),
            ('P5', 'IN_P5', '+5V'),
        ):
            self.assertEqual(self.parts['PTC_' + key].pins,
                             {'1': incoming, '2': output})

    def test_unidirectional_tvs_polarity(self):
        self.assertEqual(self.parts['TVS_P12'].pins, {'1': '+12V', '2': 'AGND'})
        self.assertEqual(self.parts['TVS_N12'].pins, {'1': 'AGND', '2': '-12V'})
        self.assertEqual(self.parts['TVS_P5'].pins, {'1': '+5V', '2': 'AGND'})

    def test_local_filter_bleeder_and_probe_per_rail(self):
        for key, rail in (('P12', '+12V'), ('N12', '-12V'), ('P5', '+5V')):
            for prefix in ('C100N_', 'C1U_', 'BLEED_'):
                self.assertEqual(self.parts[prefix + key].pins,
                                 {'1': rail, '2': 'AGND'})
            self.assertEqual(self.parts['TP_' + key].pins, {'1': rail})
        self.assertEqual(self.parts['TP_GND'].pins, {'1': 'AGND'})


if __name__ == '__main__':
    unittest.main()
