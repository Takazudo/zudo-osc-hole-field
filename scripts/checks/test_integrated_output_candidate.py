"""Candidate topology, conditional evidence and original-envelope regressions."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.checks import integrated_output_candidate as candidate


class IntegratedOutputCandidateTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(candidate.SPEC.read_text())

    def test_exact_f_family_and_package(self):
        candidate.validate(self.spec)
        for key, value in [('mpn', 'ADG5401BCPZ-RL7'), ('package', 'MSOP')]:
            changed = copy.deepcopy(self.spec); changed['identity'][key] = value
            with self.assertRaises(ValueError): candidate.validate(changed)

    def test_external_current_limiting_cannot_move_to_drain(self):
        for ref in ('R_ISO_A', 'R_ISO_B', 'R_SENSE'):
            changed = copy.deepcopy(self.spec)
            next(p for p in changed['parts'] if p['ref'] == ref)['pins']['1'] = 'DRIVE'
            with self.assertRaises(ValueError): candidate.validate(changed)

    def test_signal_feedback_and_ground_pins_are_not_interchangeable(self):
        for pin, net in [('1', 'DRIVE'), ('2', 'FB'), ('4', 'NC'), ('9', 'JACK')]:
            changed = copy.deepcopy(self.spec)
            next(p for p in changed['parts'] if p['ref'] == 'U_PROTECT')['pins'][pin] = net
            with self.assertRaises(ValueError): candidate.validate(changed)

    def test_poc_cannot_silently_enable_ground_pull(self):
        next(p for p in self.spec['parts'] if p['ref'] == 'U_PROTECT')['pins']['7'] = 'GND'
        with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_persistent_local_feedback_cannot_disappear(self):
        self.spec['parts'] = [p for p in self.spec['parts'] if p['ref'] != 'R_LOCAL']
        with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_table_supply_and_typical_values_cannot_be_promoted(self):
        for key, value in [('table_dual_nominal_V', 12), ('Ron_max_ohm_at_13p5V_full_temp', 6), ('off_drain_leakage_typ_A_floating_supplies', 55e-9)]:
            changed = copy.deepcopy(self.spec); changed['observed_datasheet_conditions'][key] = value
            with self.assertRaises(ValueError): candidate.validate(changed)
        self.spec['project_guarantees']['complete_release_max_s'] = 220e-9
        with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_hypothetical_delay_remains_a_sensitivity(self):
        self.spec['sensitivity']['assumed_complete_release_s'] = [1e-9]
        report = candidate.calculate(self.spec)
        self.assertEqual(report['collapse_sensitivity']['verdict'], 'UNSOURCED')
        self.assertFalse(report['protection_implemented'])
        self.assertIsNone(self.spec['project_guarantees']['complete_release_max_s'])

    def test_nonphysical_sensitivity_inputs_rejected(self):
        for bad in (0, -1, float('nan'), float('inf'), True, '0.3', 10 ** 400):
            for key in ('diagnostic_rail_excursion_V', 'future_soft_start_ms'):
                changed = copy.deepcopy(self.spec); changed['sensitivity'][key] = bad
                with self.subTest(value=repr(bad), key=key):
                    with self.assertRaises(ValueError): candidate.calculate(changed)
        self.spec['sensitivity']['assumed_complete_release_s'] = []
        with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_no_weakened_original_population(self):
        self.spec['population']['general_outputs'] = 0
        with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_no_invented_pdf_hash(self):
        sources = json.loads(candidate.SOURCES.read_text())
        sources['sources'][0]['sha256'] = '1' * 64
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'sources.json'; p.write_text(json.dumps(sources))
            with patch.object(candidate, 'SOURCES', p):
                with self.assertRaises(ValueError): candidate.validate(self.spec)

    def test_dc_solution_satisfies_independent_kcl(self):
        for signal in (-5, 0, 5):
            for bias in (-95e-9, 0, 95e-9):
                for load in (None, 10000):
                    n = candidate.dc_nodes(signal, 1033.7, 8905.5, 9771300, load, bias)
                    jack, drive = n['jack_V'], n['drive_V']
                    self.assertAlmostEqual((signal - drive) / 9771300 + (signal - jack) / 8905.5 + bias, 0, places=13)
                    self.assertAlmostEqual((jack - drive) / 1033.7 + (jack - signal) / 8905.5 + (0 if load is None else jack / load), 0, places=13)

    def test_static_shift_is_distinct_from_load_error(self):
        r = candidate.calculate(self.spec)['precision_DC_sensitivity']
        self.assertLess(r['maximum_load_dependent_change_V'], .0005)
        self.assertGreater(r['maximum_uncalibrated_static_shift_V'], .0013)
        self.assertEqual(r['verdict'], 'UNSOURCED')

    def test_supply_operation_does_not_admit_pm12_table_performance(self):
        r = candidate.calculate(self.spec)['operating_range_screen']
        self.assertGreater(r['plus8V_headroom_margin_V'], 1.5)
        self.assertFalse(r['project_rails_inside_pm15_table_range'])

    def test_both_polarities_and_cold_concurrency_preserved(self):
        r = candidate.calculate(self.spec)
        self.assertEqual(r['static_fault_screen']['both_external_polarities_V'], [-12, 12])
        full = r['collapse_sensitivity']['cases'][1]
        self.assertEqual((full['drive_count'], full['sense_count']), (82, 16))
        self.assertGreater(full['initial_injection_A'], 1)
        self.assertLess(full['zero_detector_complete_release_budget_s'], 35e-6)
        self.assertLess(full['rows'][-1]['maximum_detector_delay_s'], 0)
        self.assertIn('not guaranteed full isolation', r['collapse_sensitivity']['timing_boundary'])

    def test_full_budget_retains_positive_window_requirement_and_ceilings(self):
        r = candidate.calculate(self.spec)['population_and_budget']
        self.assertEqual(len(r['general_0to8V_outputs']), 6)
        self.assertEqual(r['original_maximum_return_A'], 4.6)
        now, slower = [row for row in r['cases'] if row['switch_packages'] == 112]
        self.assertEqual(now['prospective_continuous_mA'], {'+12V': 1800, '-12V': 1700, '+5V': 300})
        self.assertFalse(now['arithmetic_windows_positive'])
        self.assertTrue(slower['arithmetic_windows_positive'])
        self.assertEqual(now['original_maximum_delivered_mA'], slower['original_maximum_delivered_mA'])
        self.assertAlmostEqual(slower['ramp_increment_mA']['+12V'], 149.76)
        self.assertAlmostEqual(now['extra_nominal_bypass_uF_each_analog_rail'], 11.2)
        self.assertGreater(now['normal_with_all_existing_allowances_mA']['+5V'], 236)

    def test_faster_startup_cannot_hide_ramp_demand(self):
        self.spec['sensitivity']['future_soft_start_ms'] = 5
        with self.assertRaises(ValueError): candidate.calculate(self.spec)

    def test_report_current_and_all_guarantees_open(self):
        candidate.run(check=True)
        self.assertTrue(all(value is None for value in self.spec['project_guarantees'].values()))


if __name__ == '__main__': unittest.main()
