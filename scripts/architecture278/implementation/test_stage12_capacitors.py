import copy
import json
import unittest
import stage12_capacitors as c


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = [json.loads(p.read_text()) for p in (
            c.OUT / 'capacitor-input.json', c.OUT.parent / 'stage10/inventory-report.json',
            c.OUT.parent / 'stage11/identity-input.json')]

    def reject(self, edit, message):
        data = copy.deepcopy(self.data)
        edit(data)
        with self.assertRaisesRegex(ValueError, message):
            c.analyze(*data)

    def test_conservation(self):
        result = c.analyze(*self.data)
        self.assertEqual(len(result['conservation']['unchanged_refs']), 88)
        self.assertEqual(result['conservation']['added_packages'], [])
        self.assertFalse(result['conservation']['topology_changed'])

    def test_retention_requirement(self):
        result = c.analyze(*self.data)
        for row in result['overlay'].values():
            self.assertAlmostEqual(row['initial_tolerance_interval_F'][0], 4.23e-6)
            self.assertAlmostEqual(row['required_combined_retention_after_initial_min_for_1uF'], 1 / 4.23)
            self.assertFalse(row['application_minimum_proven'])
            self.assertIsNone(row['effective_C_at_bias_temperature_age_F'])

    def test_no_esr_promotion(self):
        self.reject(lambda d: d[0]['part'].update(guaranteed_ESR_ohm=.01), 'guarantee')

    def test_no_bias_curve_promotion(self):
        self.reject(lambda d: d[0]['part'].update(guaranteed_bias_retention=.3), 'guarantee')

    def test_no_aging_family_borrow(self):
        self.reject(lambda d: d[0]['part'].update(guaranteed_aging_rate=.03), 'guarantee')

    def test_missing_package(self):
        self.reject(lambda d: d[1]['packages'].pop('C7107'), 'inventory')

    def test_added_resistor(self):
        self.reject(lambda d: d[0]['overlay'].update(Rextra={}), 'two-value')

    def test_changed_net(self):
        self.reject(lambda d: d[0]['overlay']['C7102']['pins'].update({'1': '+12V'}), 'topology')

    def test_changed_footprint(self):
        self.reject(lambda d: d[0]['overlay']['C7101'].update(footprint='C0805'), 'topology')

    def test_captured_mpn_change(self):
        self.reject(lambda d: d[0]['overlay']['C7101'].update(captured_MPN=''), 'captured')

    def test_local_bypass_dependency(self):
        self.reject(lambda d: d[1]['packages']['C7107']['source_package'].update(decouples_ref=None), 'association')

    def test_125C_not_inherited(self):
        self.reject(lambda d: d[0]['part'].update(temperature_range_C=[-55, 125]), 'specification')

    def test_invalid_plot_reading(self):
        self.reject(lambda d: d[0]['typical_visual_readings'].update({'5V_retained_fraction_interval': [float('nan'), .5]}), 'finite')

    def test_noise_not_stability(self):
        self.reject(lambda d: d[0]['application'].update(stability_ESR_max_ohm=1), 'binding')

    def test_missing_disclaimer_page(self):
        self.reject(lambda d: d[0]['evidence']['capacitor']['additional_locators'].pop(), 'locators')


if __name__ == '__main__':
    unittest.main()
