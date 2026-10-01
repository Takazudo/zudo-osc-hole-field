import copy
import json
from fractions import Fraction as F
import unittest
from unittest.mock import Mock, patch
from scripts.checks import negative_monitor_network as monitor

from scripts.checks.negative_monitor_network import (
    SPEC, NODES, calculate, nodal, resistor_corners, run, solve, validate)


class NegativeMonitorNetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(SPEC.read_text())
        cls.result = calculate(cls.spec)

    def test_cold_solution_matches_independent_series_parallel_reduction(self):
        r = {p['ref']: F(p['ohm']) for p in self.spec['resistors']}
        ref_ground = 1/(1/r['RB'] + 1/(r['RU']+r['RUG']) + 1/(r['RO']+r['ROG']))
        sense_ground = 1/(1/r['RG'] + 1/(r['RR']+ref_ground))
        vn = F(-1248, 100)
        sense = vn*sense_ground/(r['RN']+sense_ground)
        reference = sense*ref_ground/(r['RR']+ref_ground)
        actual, _, _ = nodal(self.spec, r, {'AGND': F(), 'VN': vn})
        self.assertEqual(actual['SENSE'], sense)
        self.assertEqual(actual['REF'], reference)
        self.assertEqual(actual['UV'], reference*r['RUG']/(r['RU']+r['RUG']))

    def test_kcl_with_independent_signed_pin_currents(self):
        resistance = next(resistor_corners(self.spec))
        currents = {'REF': F(1, 100000), 'SENSE': F(-2, 100000),
                    'UV': F(1, 100000), 'OV': F(-1, 100000)}
        v, _, _ = nodal(self.spec, resistance, {'AGND': F(), 'VN': F(1248,100)}, currents)
        for node in NODES:
            outward = F()
            for part in self.spec['resistors']:
                a, b = part['nodes']
                if node == a:
                    outward += (v[a]-v[b])/resistance[part['ref']]
                if node == b:
                    outward += (v[b]-v[a])/resistance[part['ref']]
            self.assertEqual(outward, currents[node])

    def test_cold_rating_is_conditional_on_leakage(self):
        self.assertEqual(self.result['resistor_corner_count'], 256)
        for row in self.result['pin_screen'].values():
            self.assertTrue(row['conditional_cold_within_absolute_rating'])
        changed = copy.deepcopy(self.spec)
        changed['conditions']['cold_uniform_leakage_per_pin_A'] = .001
        self.assertFalse(all(r['conditional_cold_within_absolute_rating']
                             for r in calculate(changed)['pin_screen'].values()))

    def test_normal_band_and_prior_overvoltage_leg(self):
        self.assertTrue(self.result['conditional_static_normal_band_accepted'])
        prior = copy.deepcopy(self.spec)
        next(p for p in prior['resistors'] if p['ref'] == 'RO')['ohm'] = 8870
        result = calculate(prior)
        self.assertFalse(result['conditional_static_normal_band_accepted'])
        self.assertLess(result['normal_OV_margin_V'], 0)

    def test_cold_pin_screen_is_not_functional_or_permit_acceptance(self):
        self.assertFalse(self.result['permit_accepted'])
        self.assertFalse(self.result['protection_implemented'])
        self.assertIsNone(self.result['maximum_detection_delay_s'])
        self.assertTrue(self.result['dynamic_native_bench'].startswith('NOT RUN'))
        # Negative inputs satisfy the absolute-rating screen, but are outside
        # the manufacturer's 0..5.5 V high-impedance fault-tolerant input range.
        self.assertLess(self.result['pin_screen']['SENSE']['conditional_cold_V'][0], 0)

    def test_exact_sources_and_missing_guarantees_cannot_be_promoted(self):
        validate(self.spec)
        for path, value in [(('comparator','power_on_reset_guarantee'), True),
                            (('comparator','propagation_max_s'), 100e-9),
                            (('comparator','input_bias_max_A'), 5e-12),
                            (('reference','startup_max_s'), .0025),
                            (('reference','pins','1'), 'AGND')]:
            changed = copy.deepcopy(self.spec)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(ValueError):
                validate(changed)

    def test_reference_collapse_can_hide_bad_rail_with_good_comparator_supply(self):
        case = self.result['reference_collapse_counterexample']
        self.assertEqual(case['comparator_supply_V'], 5)
        self.assertTrue(case['ideal_both_outputs_released'])
        self.assertFalse(case['negative_rail_in_normal_band'])
        self.assertGreater(case['ideal_UV_healthy_margin_V'], .01)
        self.assertGreater(case['ideal_OV_healthy_margin_V'], .01)

    def test_singular_network_and_negative_envelope_rejected(self):
        with self.assertRaisesRegex(ValueError, 'singular'):
            solve([[F()]], [F()])
        changed = copy.deepcopy(self.spec)
        changed['conditions']['powered_input_bias_per_pin_A'] = -1
        with self.assertRaisesRegex(ValueError, 'negative error'):
            calculate(changed)

    def test_generated_report_is_current(self):
        run(check=True)

    def test_every_required_source_record_is_bound(self):
        original = json.loads(monitor.SOURCES.read_text())
        for record in original['sources']:
            for missing in (True, False):
                changed = copy.deepcopy(original)
                if missing:
                    changed['sources'] = [r for r in changed['sources'] if r['id'] != record['id']]
                else:
                    next(r for r in changed['sources'] if r['id'] == record['id'])['mpn'] = 'WRONG-MPN'
                with self.subTest(source=record['id'], missing=missing), patch.object(
                        monitor, 'SOURCES', Mock(read_text=lambda: json.dumps(changed))):
                    with self.assertRaisesRegex(ValueError, 'required device/source'):
                        validate(self.spec)

    def test_source_hash_and_size_metadata_rejected_before_byte_verification(self):
        original = json.loads(monitor.SOURCES.read_text())
        for key, value in [('sha256','z'*64), ('sha256','0'*64), ('bytes',0), ('bytes',True)]:
            changed = copy.deepcopy(original)
            changed['sources'][0][key] = value
            with patch.object(monitor, 'SOURCES', Mock(read_text=lambda: json.dumps(changed))):
                with self.assertRaisesRegex(ValueError, 'primary evidence'):
                    validate(self.spec)


if __name__ == '__main__':
    unittest.main()
