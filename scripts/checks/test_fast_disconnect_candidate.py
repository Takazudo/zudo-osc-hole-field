"""Portable polarity, KCL, condition and budget counterexample regressions."""
import copy
import json
import unittest

from scripts.checks.fast_disconnect_candidate import SPEC, calculate, coupled_sense_nodes, drive_nodes, run, sense_nodes, validate


class FastDisconnectCandidateTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(SPEC.read_text())

    def test_exact_candidate_and_optional_source_bytes(self):
        validate(self.spec)

    def test_grounded_gate_is_not_safe_for_negative_external_voltage(self):
        cases = calculate(self.spec)["power_off_polarity_counterexamples"]
        negative, positive = cases
        self.assertGreater(negative["grounded_gate_VGS_V"], 4.5)
        self.assertLess(positive["grounded_gate_VGS_V"], 0)
        self.assertEqual([case["source_referenced_ideal_gate_VGS_V"] for case in cases], [0, 0])

    def test_source_referenced_bleed_cannot_be_changed_to_ground(self):
        self.spec["parts"][6]["terminals"]["2"] = "AGND"
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_both_sources_and_gates_must_be_shared(self):
        self.spec["parts"][1]["terminals"]["S"] = "EXTERNAL_LIMITED"
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_blocking_diode_orientation_is_not_optional(self):
        self.spec["parts"][3]["terminals"] = {"A": "FEED", "K": "PULLUP"}
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_default_off_base_reference_must_follow_emitter(self):
        self.spec["parts"][8]["terminals"]["2"] = "AGND"
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_missing_full_timing_bound_cannot_be_filled_by_typical_value(self):
        self.spec["source_values"]["complete_disconnect_delay_max_s"] = 22.3e-9
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_fixed_source_condition_cannot_be_reduced_to_typical_charge(self):
        self.spec["source_values"]["mos_Qg_max_C_at_10V_48V_230mA_25C"] = 1e-9
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_invalid_diagnostic_magnitudes_fail_closed(self):
        for invalid in (0, -1, float("nan"), float("inf"), True, "0.1", 10 ** 400):
            with self.subTest(invalid=repr(invalid)):
                candidate = copy.deepcopy(self.spec)
                candidate["diagnostics"]["cutoff_VGS_V_not_off_leakage_guarantee"] = invalid
                with self.assertRaises(ValueError):
                    calculate(candidate)

    def test_threshold_current_is_not_an_off_leakage_cutoff(self):
        self.spec["diagnostics"]["cutoff_VGS_V_not_off_leakage_guarantee"] = 0.6
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_sense_node_solution_satisfies_independent_KCL(self):
        vin, bias = 5, 50e-6
        nodes = sense_nodes(vin, bias, 1006, 4990, 1e7, 4, 10000)
        drive, jack, source = (nodes[k] for k in ("drive_V", "jack_V", "source_common_V"))
        self.assertAlmostEqual((vin - drive) / 1e7 + (vin - source) / 4, 0, places=12)
        self.assertAlmostEqual((source - vin) / 4 + (source - jack) / 4994, bias, places=12)
        self.assertAlmostEqual((jack - drive) / 1006 + (jack - source) / 4994 + jack / 10000, 0, places=12)
        self.assertGreater(abs(jack - vin), 0.24)

    def test_sense_bias_conflict_is_separate_from_low_on_resistance(self):
        row = calculate(self.spec)["sense_injection"]
        self.assertLess(row["maximum_injection_A_for_diagnostic_static_error_allocation"], 201e-9)
        self.assertGreater(row["minimum_ON_bleed_A_at_4p5V_gate"], 400e-6)
        self.assertGreater(row["minimum_RGS_ohm_for_diagnostic_static_error_allocation"], 22e6)

    def test_coupled_sense_driver_satisfies_driver_and_node_KCL(self):
        for vin in (-5, 0, 5):
            n = coupled_sense_nodes(vin, 1006, 4990, 1e7, 4, 10000, 11.33, 500, 10000, 8.2)
            current = n["pullup_current_A"]
            self.assertAlmostEqual((11.33 - n["source_common_V"] - n["VGS_V"]) / 500, current, places=12)
            self.assertAlmostEqual((n["source_common_V"] - vin) / 4 + (n["source_common_V"] - n["jack_V"]) / 4994, current, places=12)
            self.assertGreaterEqual(current, n["VGS_V"] / 10000 - 1e-12)
        rows = calculate(self.spec)["sense_injection"]["coupled_resistive_driver_countermodel"]
        self.assertEqual([r["required_drive_outside_even_maximum_rail_magnitudes"] for r in rows], [True, True, False])
        self.assertEqual([r["branch"] for r in rows], ["clamped", "clamped", "unclamped"])

    def test_drive_bias_is_inside_feedback_but_not_free_current(self):
        for vin in (-5, 0, 5):
            n = drive_nodes(vin, 4e-3, 4, 10000)
            self.assertLess(abs(n["jack_V"] - vin), 0.001)
            self.assertAlmostEqual((n["source_common_V"] - n["drive_V"]) / 4 + (n["source_common_V"] - n["jack_V"]) / 1002, 0.004, places=12)
        budget = calculate(self.spec)["hybrid_power_sensitivity"]["sixteen_precision_at_current_ramp"]
        self.assertGreater(budget["normal_mA"]["-12V"], 1500)

    def test_hybrid_concurrency_retains_sense_release_charge(self):
        row = calculate(self.spec)["hybrid_collapse"]
        self.assertEqual(row["precision_output_count"], 16)
        self.assertAlmostEqual(row["optimistic_reachable_capacitance_F"], 120e-6)
        self.assertLess(row["hybrid_max_drive_release_s_with_zero_detection_delay"], 83e-6)
        self.assertGreater(row["sensitivities"][1]["conservative_C_needed_F_for_guard"], 98e-6)
        self.assertLess(row["sensitivities"][2]["maximum_detection_delay_s_for_assumed_accessible_C"], 0)

    def test_future_slower_start_does_not_increase_any_current_ceiling(self):
        rows = calculate(self.spec)["hybrid_power_sensitivity"]
        now = rows["sixteen_precision_at_current_ramp"]
        future = rows["sixteen_precision_at_future_slower_ramp"]
        self.assertFalse(now["arithmetic_windows_positive"])
        self.assertTrue(future["arithmetic_windows_positive"])
        self.assertEqual(now["maximum_delivered_mA_unchanged"], future["maximum_delivered_mA_unchanged"])
        self.assertAlmostEqual(future["ramp_increment_mA"]["+12V"], 149.76)
        self.assertFalse(rows["all_82_drive_contacts_at_future_slower_ramp"]["arithmetic_windows_positive"])
        self.assertFalse(rows["sixteen_resistive_pullups_at_negative_signal_sensitivity"]["arithmetic_windows_positive"])

    def test_all_82_outputs_keep_their_fault_obligations(self):
        row = calculate(self.spec)["all_output_obligations"]
        self.assertEqual(row["total_drive_contacts"], 82)
        self.assertEqual(len(row["general_output_uids"]), 66)
        self.assertEqual(len(row["envelope_0_to_8V_uids"]), 6)
        self.assertLess(row["plus8V_gate_headroom_screen"]["VGS_V"], 4.5)
        collapse = row["complete_concurrent_collapse_sensitivity"]
        self.assertLess(collapse["maximum_equal_drive_release_s_zero_detector_delay"], 17e-6)
        self.assertLess(collapse["rows"][1]["maximum_detection_delay_s_for_assumed_accessible_C"], 0)

    def test_faster_ramp_cannot_hide_capacitor_current(self):
        self.spec["diagnostics"]["future_soft_start_ms_sensitivity"] = 5
        with self.assertRaises(ValueError):
            calculate(self.spec)

    def test_report_current_and_no_full_timing_claim(self):
        run(check=True)
        r = calculate(self.spec)
        self.assertIsNone(r["turnoff_evidence"]["whole_disconnect_max_s"])
        self.assertFalse(r["protection_implemented"])


if __name__ == "__main__":
    unittest.main()
