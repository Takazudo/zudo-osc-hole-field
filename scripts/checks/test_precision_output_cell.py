"""Portable independent arithmetic and adversarial candidate-boundary checks."""
import json
import unittest

from scripts.checks.precision_output_cell import ROOT, SPEC, SOURCES, calculate, digest, floating_rail, load_error, validate, run
from scripts.checks.precision_output_cell_model import deck


class PrecisionOutputCandidateTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(SPEC.read_text())
        self.sources = json.loads(SOURCES.read_text())

    def test_source_bytes_and_exact_identity(self):
        validate(self.spec, self.sources)

    def test_old_relay_identity_cannot_inherit_new_catalog(self):
        self.spec["parts"][1]["mpn"] = "AQY232SX"
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_sense_resistor_cannot_be_bypassed(self):
        self.spec["parts"][2]["pins"]["3"] = "JACK"
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_permit_return_cannot_use_local_ground(self):
        self.spec["parts"][2]["pins"]["2"] = "GND"
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_bleeder_cannot_land_on_external_ground(self):
        self.spec["parts"][-1]["pins"]["2"] = "RACK_GND"
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_resistor_value_must_match_evidenced_mpn(self):
        self.spec["parts"][5]["value"] = 100
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_research_cannot_assert_implemented(self):
        self.spec["protection_implemented"] = True
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_original_deadline_cannot_be_relaxed(self):
        self.spec["limits_preserved"]["settling_deadline_s"] = 0.002
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_corrupt_retained_source_fails_closed(self):
        self.sources["sources"][1]["sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            validate(self.spec, self.sources)

    def test_dc_formula_against_two_node_kcl_solution(self):
        # Solve independent JACK and DRIVE equations with FB held at Vin.
        for rd, rs, local, load in [(998, 4990, 1e7, 1e4), (1500, 8200, 4.7e6, 1e5)]:
            vin = 5
            a, b, f = 1 / rd + 1 / rs + 1 / load, -1 / rd, vin / rs
            c, d, g = 1 / rs, 1 / local, vin * (1 / rs + 1 / local)
            jack = (f * d - b * g) / (a * d - b * c)
            self.assertAlmostEqual(vin - jack, load_error(vin, rd, rs, local, load), places=12)
            self.assertLess(load_error(vin, rd, rs, local, 1e20), 1e-15)

    def test_resistor_derating_is_not_room_temperature_only(self):
        screen = calculate(self.spec)["sustained_contention"]
        rows = {r["ambient_C"]: r for r in screen["ambient_screens"]}
        self.assertTrue(rows[100]["within_resistor_power_curve"])
        self.assertFalse(rows[105]["within_resistor_power_curve"])
        self.assertGreater(screen["each_499_power_upper_W"], 0.30)

    def test_resistance_does_not_isolate_a_floating_rail(self):
        self.assertGreater(floating_rail(12, 1000, 1e-5, 1e-3), 1)
        self.assertAlmostEqual(floating_rail(12, 1000, 1e-5, 10), 12)
        self.assertEqual(floating_rail(12, 1000, 1e-5, 0), 0)

    def test_leakage_bleed_and_pre_release_current_are_separate(self):
        report = calculate(self.spec)
        self.assertLess(report["isolated_off_boundary"]["single_rail_steady_differential_upper_V"], 0.3)
        collapse = report["cold_collapse_before_contact_release"]
        self.assertGreater(collapse["cold_rail_V_at_contact_delay_for_assumed_cap"], 0.7)
        self.assertGreater(collapse["conservative_C_min_F_for_max_differential_and_guard"], 50e-6)

    def test_more_capacitance_reduces_collapse_excursion_not_final_leakage_voltage(self):
        original = calculate(self.spec)
        self.spec["conditions"]["floating_rail_diagnostic_C_F"] *= 10
        larger = calculate(self.spec)
        key = "cold_rail_V_at_contact_delay_for_assumed_cap"
        self.assertLess(larger["cold_collapse_before_contact_release"][key], original["cold_collapse_before_contact_release"][key] / 9)
        self.assertEqual(larger["isolated_off_boundary"]["single_rail_steady_differential_upper_V"], original["isolated_off_boundary"]["single_rail_steady_differential_upper_V"])

    def test_contact_capacitance_is_between_contact_pins(self):
        text = deck(self.spec, "10k", "5n", 0.12, 1e-8)
        self.assertIn("CK_DRIVE DRIVE SW_DRIVE 2e-10", text)
        self.assertIn("CK_SENSE SENSE_LIMITED FB 2e-10", text)
        self.assertNotIn("CK_DRIVE DRIVE 0", text)
        self.assertIn("R_SENSE JACK SENSE_LIMITED 4990", text)
        self.assertIn("R_LOCAL DRIVE FB 10000000", text)

    def test_5V_relay_replication_does_not_create_a_new_power_envelope(self):
        budget = calculate(self.spec)["full_population_LED_screen"]
        self.assertEqual(budget["channels"], 128)
        self.assertEqual(budget["independent_5mA_strings_mA"], 640)
        self.assertEqual(budget["precision_paired_arrangement_mA"], 560)
        self.assertTrue(budget["precision_paired_LED_load_alone_exceeds_entire_rail_maximum"])
        self.assertGreater(budget["all_paired_plus5_normal_mA_even_replacing_entire_auxiliary_allowance"], 500)

    def test_budget_equality_is_not_a_positive_limiter_window(self):
        report = calculate(self.spec)
        cases = report["bipolar_strings_without_IC_substitution"]["cases"]
        for case in cases:
            self.assertTrue(case["transient_requirements_within_original_maxima"])
            self.assertFalse(case["original_strict_limiter_windows_met_arithmetically"])
            self.assertEqual(case["positive_limiter_window_mA"]["+12V"], 0)
            self.assertAlmostEqual(case["unrounded_transient_demand_mA"]["+12V"], 2049.64)
            self.assertAlmostEqual(case["physical_ceiling_minus_unrounded_demand_mA"]["-12V"], 52.34)
        mixed = report["mixed_LED_and_input_switch_sensitivity"]
        self.assertEqual(mixed["actual_existing_ADG_package_count"], 110)
        self.assertEqual(mixed["hypothetical_110_TMUX_delta_mA"]["+12V"], -77)
        self.assertTrue(mixed["with_conditioned_exact_110_input_switch_substitution"]["original_strict_limiter_windows_met_arithmetically"])

    def test_generated_bounds_and_model_receipt_match_inputs_without_running_oracle(self):
        run(check=True)
        report = json.loads((ROOT / "design/power/precision-output-cell-model.json").read_text())
        for path, expected in report["input_sha256"].items():
            self.assertEqual(digest(ROOT / path), expected)
        self.assertEqual(len(report["cases"]), 24)
        self.assertEqual(sum(row["stricter_400us_diagnostic_met"] for row in report["cases"]), 12)


if __name__ == "__main__":
    unittest.main()
