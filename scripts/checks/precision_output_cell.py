"""Reproducible candidate-cell bounds, never a hardware/protection qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "design/power/precision-output-cell.json"
SOURCES = ROOT / "design/power/precision-output-cell-sources.json"
REPORT = ROOT / "design/power/precision-output-cell-report.json"
NETLIST = ROOT / "design/power/precision-output-cell-connectivity.txt"
SUPPLY = ROOT / "design/power/supply-architecture.json"
LEDGER = ROOT / "design/power/rail-ledger.json"
SWITCH_SOURCES = ROOT / "design/power/protection59-sources.json"
STANDARD = ROOT / "design/standard/electrical-standard.json"
PROTECTION_AUDIT = ROOT / "design/power/protection58-audit.json"

# These are transcriptions of the exact receipts, not tunable sensitivity inputs.
# Changes require review of the cited source/condition and the candidate itself.
SOURCE_CONDITIONS = {
    "resistor_tolerance": (0.01, "r499/r4990/r10m/r100k exact-part sheets"),
    "resistor_tcr_per_C": (0.0001, "r499/r4990/r10m/r100k exact-part sheets"),
    "relay_on_ohm_at_25C": (0.12, "photomos, printed p3, IF=5mA"),
    "relay_off_A_at_25C": (1e-6, "photomos, printed p3, IF=0, VL=60V"),
    "relay_off_s_at_25C": (0.0005, "photomos, printed p3, IF=5mA, IL=100mA, VL=10V"),
    "relay_recommended_contact_V_at_25C": (48, "photomos, printed p4"),
    "relay_abs_contact_V_at_25C": (60, "photomos, printed p2, absolute rating"),
    "amplifier_bias_A_full_temp_PW": (1.5e-8, "opa4197, printed p7, PW full-temperature row"),
    "amplifier_input_absolute_current_A": (0.01, "opa4197, printed p5, absolute input rating"),
    "amplifier_Iq_per_core_A_full_temp": (0.0015, "opa4197, printed p8, unloaded full-temperature row"),
    "amplifier_theta_JA_C_per_W_test_board": (92.6, "opa4197, printed p6, test-board metric"),
    "led_characterization_A": (0.005, "photomos, printed p3, Ron/timing characterization condition"),
    "led_Vf_max_at_5mA_25C": (1.7, "photomos, printed p3, IF=5mA"),
}
SENSITIVITY_CONDITIONS = {
    "relay_contact_cap_sensitivity_F",
    "floating_rail_diagnostic_C_F",
    "off_rail_diagnostic_guard_V",
    "resistor_screen_C",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value: object, name: str) -> None:
    # bool is a Python int subclass, but never a valid physical quantity here.
    try:
        finite = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number, not a boolean or string")


def validate_conditions(spec: dict) -> None:
    c = spec["conditions"]
    if not isinstance(c, dict):
        raise ValueError("Conditions must be an object with classified physical quantities")
    standard = json.loads(STANDARD.read_text())
    contract = json.loads(SUPPLY.read_text())["contract"]
    signals = standard["signals"]
    precision = next(cell for cell in standard["cells"] if cell["id"] == "precision_output")
    if not any("0/100p/1n/5n F cable loads" in note for note in precision["notes"]):
        raise ValueError("Authoritative precision cable envelope changed; review the 5 nF mapping")
    project = {
        "signal_max_V": max(abs(x) for x in signals["bipolar_cv_nominal_V"]),
        "fault_external_max_V": max(abs(x) for x in signals["input_continuous_fault_V"]),
        "load_min_ohm": signals["minimum_output_load_ohm"],
        "positive_rail_max_V": contract["source_requirement"]["required_load_voltage_magnitude_V"]["+12V"][1],
        "negative_rail_magnitude_max_V": contract["source_requirement"]["required_load_voltage_magnitude_V"]["-12V"][1],
        # OSC-ES-1 cells.precision_output.notes states the 0/100p/1n/5n sweep.
        "cable_max_F": 5e-9,
        "ambient_project_C": contract["load_envelope"]["ambient_C"],
    }
    if set(c) != set(project) | set(SOURCE_CONDITIONS) | SENSITIVITY_CONDITIONS:
        raise ValueError("Conditions are missing or unclassified; review their provenance/domain")
    for name, value in c.items():
        if name in ("ambient_project_C", "resistor_screen_C"):
            if not isinstance(value, list) or not value:
                raise ValueError(f"{name} requires a nonempty temperature list")
            for temperature in value:
                finite_number(temperature, name)
                if not -55 <= temperature <= 155:
                    raise ValueError(f"{name} lies outside the sourced resistor range")
            if value != sorted(set(value)):
                raise ValueError(f"{name} must be strictly increasing")
        else:
            finite_number(value, name)
            if value <= 0:
                raise ValueError(f"{name} must be positive")
    if c["resistor_tolerance"] >= 1 or c["resistor_tcr_per_C"] * 130 >= 1:
        raise ValueError("Tolerance/TCR would permit a nonpositive resistance")
    for name, value in project.items():
        if c[name] != value:
            raise ValueError(f"{name} changes the original scenario; update its source and review the model")
    for name, (value, locator) in SOURCE_CONDITIONS.items():
        if c[name] != value:
            raise ValueError(f"{name} must match the sourced condition at {locator}; not a sensitivity variable")
    bleeder = next(p for p in spec["parts"] if p["ref"] == "R_BLEED_P")["value"]
    finite_number(bleeder, "R_BLEED_P")
    if bleeder <= 0:
        raise ValueError("R_BLEED_P must be positive")
    steady = 2 * c["relay_off_A_at_25C"] * bleeder * (1 + c["resistor_tolerance"]) * (1 + c["resistor_tcr_per_C"] * 130)
    # This report computes a finite discharge time to the diagnostic guard. A
    # lower/equal guard never settles under the stated leakage, so reject it
    # explicitly rather than taking log(negative), dividing by zero or hiding it.
    if not steady < c["off_rail_diagnostic_guard_V"] < min(c["fault_external_max_V"], c["positive_rail_max_V"]):
        raise ValueError("Diagnostic guard must exceed steady leakage voltage and stay below the initial/fault voltage")
    audit = json.loads(PROTECTION_AUDIT.read_text())
    counts = {"drive_channels": audit["output_count"], "precision_sense_channels": audit["precision_count"], "reference_channels": len(audit["reference_receivers"])}
    for name, expected in counts.items():
        value = spec["replication_screen"][name]
        if type(value) is not int or value <= 0 or value != expected:
            raise ValueError(f"{name} must match the actual issue-58 population")
    for name in ("existing_plus5_continuous_mA", "unchanged_plus5_maximum_mA"):
        finite_number(spec["replication_screen"][name], name)


def validate(spec: dict, sources: dict) -> None:
    validate_conditions(spec)
    if spec["protection_implemented"] or "NOT IMPLEMENTED" not in spec["status"]:
        raise ValueError("Candidate must not assert implemented protection")
    for name, value in spec["limits_preserved"].items():
        finite_number(value, name)
    if spec["limits_preserved"] != {"load_error_mV": 1, "calibrated_error_mV": 2, "overshoot_percent": 10, "settling_error_mV": 1, "settling_deadline_s": 0.001, "supply_protection_drop_V": 0.04}:
        raise ValueError("Original precision, deadline and protection-drop limits changed")
    ids = {s["id"]: s for s in sources["sources"]}
    if len(ids) != len(sources["sources"]):
        raise ValueError("Duplicate source identity")
    parts = {p["ref"]: p for p in spec["parts"]}
    if len(parts) != len(spec["parts"]):
        raise ValueError("Duplicate reference")
    for part in parts.values():
        if ids[part["source"]]["manufacturer_mpn"] != part["mpn"]:
            raise ValueError("Part identity does not match its evidence")
    # These named edges are the actual safety boundary, not an abstract switch count.
    expected = {
        "K_DRIVE": {"1": "PERMIT_I_PLUS", "2": "LED_MID", "3": "DRIVE", "4": "SW_DRIVE"},
        "K_SENSE": {"1": "LED_MID", "2": "PERMIT_I_MINUS", "3": "SENSE_LIMITED", "4": "FB"},
        "R_ISO_A": {"1": "SW_DRIVE", "2": "ISO_MID"},
        "R_ISO_B": {"1": "ISO_MID", "2": "JACK"},
        "R_SENSE": {"1": "JACK", "2": "SENSE_LIMITED"},
        "R_LOCAL": {"1": "DRIVE", "2": "FB"},
        "C_LOCAL": {"1": "DRIVE", "2": "FB"},
        "R_BLEED_P": {"1": "VP", "2": "GND"},
        "R_BLEED_N": {"1": "VN", "2": "GND"},
        "U1": {"1": "DRIVE", "2": "FB", "3": "SIGNAL", "4": "VP", "5": "GND", "6": "SPARE_B", "7": "SPARE_B", "8": "SPARE_C", "9": "SPARE_C", "10": "GND", "11": "VN", "12": "GND", "13": "SPARE_D", "14": "SPARE_D"},
    }
    if set(parts) != set(expected):
        raise ValueError("Unexpected part population; review the calculation model")
    for ref, pins in expected.items():
        if parts[ref]["pins"] != pins:
            raise ValueError(f"Connectivity changed at {ref}; review the fault boundary")
    expected_values = {"R_ISO_A": 499, "R_ISO_B": 499, "R_SENSE": 4990,
                       "R_LOCAL": 10000000, "C_LOCAL": 1e-8,
                       "R_BLEED_P": 100000, "R_BLEED_N": 100000}
    for ref, value in expected_values.items():
        if parts[ref]["value"] != value:
            raise ValueError(f"{ref} value no longer matches exact-part evidence")
    for source in ids.values():
        path = ROOT / source["file"]
        if len(source["sha256"]) != 64 or int(source["sha256"], 16) == 0:
            raise ValueError("Available source requires actual bytes digest")
        if not source["locators"]:
            raise ValueError("Source missing locators")
        # Cached copyrighted bytes are optional for another checkout; never fabricated.
        if path.exists() and (digest(path) != source["sha256"] or path.stat().st_size != source["bytes"]):
            raise ValueError(f"Source bytes changed: {source['id']}")


def load_error(signal: float, drive: float, sense: float, local: float, load: float) -> float:
    """Ideal amplifier DC KCL, including current in both feedback resistors."""
    return signal * drive * sense / (load * (local + sense + drive) + drive * sense)


def floating_rail(voltage: float, series: float, capacitance: float, elapsed: float) -> float:
    """Counterexample: conductive failed boundary, initially empty unloaded capacitor."""
    return voltage * -math.expm1(-elapsed / (series * capacitance))


def calculate(spec: dict) -> dict:
    # Direct Python callers get the same protection as the command-line entry.
    validate(spec, json.loads(SOURCES.read_text()))
    p = {x["ref"]: x for x in spec["parts"]}
    c = spec["conditions"]
    v = lambda ref: p[ref]["value"]
    # Worst resistance drift across the entire specified resistor range, independent
    # of local ambient used by the power-derating curve; do not equate body to ambient.
    drift = c["resistor_tcr_per_C"] * max(abs(-55 - 25), abs(155 - 25))
    low = (1 - c["resistor_tolerance"]) * (1 - drift)
    high = (1 + c["resistor_tolerance"]) * (1 + drift)
    rd_min = (v("R_ISO_A") + v("R_ISO_B")) * low
    rd_max = (v("R_ISO_A") + v("R_ISO_B")) * high + c["relay_on_ohm_at_25C"]
    rs_min = v("R_SENSE") * low
    rs_max = v("R_SENSE") * high + c["relay_on_ohm_at_25C"]
    rl_min = v("R_LOCAL") * low
    fault = c["fault_external_max_V"] + max(c["positive_rail_max_V"], c["negative_rail_magnitude_max_V"])
    current = fault / rd_min
    resistor_power = fault ** 2 / (4 * v("R_ISO_A") * low)
    load_mV = load_error(c["signal_max_V"], rd_max, rs_max, rl_min, c["load_min_ohm"]) * 1000
    bias_mV = c["amplifier_bias_A_full_temp_PW"] * rs_max * 1000
    bleeder_max = v("R_BLEED_P") * high
    leak = 2 * c["relay_off_A_at_25C"]
    iq_power = 4 * c["amplifier_Iq_per_core_A_full_temp"] * (c["positive_rail_max_V"] + c["negative_rail_magnitude_max_V"])
    output_power = fault ** 2 / (4 * rd_min)
    guard = c["off_rail_diagnostic_guard_V"]
    passive_bleed_max = rd_min * guard / (c["fault_external_max_V"] - guard)
    ccontact = c["relay_contact_cap_sensitivity_F"]
    injection_series = 1 / (1 / rd_min + 1 / rs_min)
    cold_current = c["fault_external_max_V"] / injection_series
    # A cold-rail diagnostic circuit with both contacts still conductive and both
    # pin paths injecting one reservoir. Actual clamp topology remains unqualified.
    cold_bleed = v("R_BLEED_P") * high
    cold_final = c["fault_external_max_V"] * cold_bleed / (injection_series + cold_bleed)
    cold_tau = (1 / (1 / injection_series + 1 / cold_bleed)) * c["floating_rail_diagnostic_C_F"]
    replication = spec["replication_screen"]
    channels = sum(replication[k] for k in ("drive_channels", "precision_sense_channels", "reference_channels"))
    paired_strings = channels - replication["precision_sense_channels"]
    led_mA = c["led_characterization_A"] * 1000
    architecture = json.loads(SUPPLY.read_text())
    supply = architecture["selected_requirement"]
    contract = architecture["contract"]
    reserve = contract["load_envelope"]["reserve_fraction"]
    rounding = contract["load_envelope"]["current_rounding_mA"]
    normal = supply["normal_with_allowances_mA"]
    continuous = supply["minimum_continuous_mA"]
    if replication["existing_plus5_continuous_mA"] != continuous["+5V"] or replication["unchanged_plus5_maximum_mA"] != contract["source_requirement"]["maximum_delivered_current_mA"]["+5V"]:
        raise ValueError("Candidate's declared supply snapshot is stale")
    aux = {rail: next(r["mA"] for r in rows if r["id"] == "protection-supervision-discharge") for rail, rows in supply["allowances"].items()}
    plus12_strings_normal = normal["+12V"] - aux["+12V"] + math.ceil(channels / 6) * led_mA
    simultaneous_precision = replication["precision_sense_channels"]
    nominal_cap_ceiling = contract["source_requirement"]["nominal_capacitance_ceiling_uF"]["+12V"] * 1e-6
    cap_tolerance = contract["source_requirement"]["capacitance_tolerance_fraction"]
    ledger = json.loads(LEDGER.read_text())
    old_packages = [p for p in ledger["physical_ic_packages"] if p["symbol"] == "ADG5412FBRUZ"]
    # Python 3.12 changed float sum accumulation. Use an explicit compensated
    # sum so the same decimal ledger produces identical portable receipts.
    old_load = {rail: math.fsum(row["planning_allowance_mA"][rail] for row in ledger["worksheet_loads"] if row["label"] == "ADG5412FBRUZ") for rail in normal}
    tmux = next(s for s in json.loads(SWITCH_SOURCES.read_text())["sources"] if s["candidate"] == "TMUX7412FRRPR")
    tmux_unit = {"+12V": tmux["normal_iq_screen"]["positive_mA"], "-12V": tmux["normal_iq_screen"]["negative_mA"], "+5V": 0}
    tmux_delta = {rail: len(old_packages) * tmux_unit[rail] - old_load[rail] for rail in normal}
    bipolar_strings, bipolar_length = 7, 13
    positive_length = 6
    remaining_LEDs = channels - bipolar_strings * bipolar_length
    positive_strings = math.ceil(remaining_LEDs / positive_length)
    mixed_LED_mA = {"+12V": (bipolar_strings + positive_strings) * led_mA, "-12V": bipolar_strings * led_mA, "+5V": 0}
    precision_bleed_mA = simultaneous_precision * max(c["positive_rail_max_V"], c["negative_rail_magnitude_max_V"]) / (v("R_BLEED_P") * low) * 1000
    added_bleed = {"+12V": precision_bleed_mA, "-12V": precision_bleed_mA, "+5V": 0}

    def budget_case(delta: dict, bias: dict | None = None) -> dict:
        bias = mixed_LED_mA if bias is None else bias
        candidate_normal = {rail: normal[rail] + bias[rail] + added_bleed[rail] + delta.get(rail, 0) for rail in normal}
        candidate_continuous = {rail: math.ceil(value * (1 + reserve) / rounding) * rounding for rail, value in candidate_normal.items()}
        unrounded_transient = {rail: candidate_continuous[rail] + supply["full_capacitance_ramp_increment_mA"][rail] + contract["load_envelope"]["fault_increment_mA"][rail] for rail in normal}
        candidate_transient = {rail: math.ceil(value / rounding) * rounding for rail, value in unrounded_transient.items()}
        maximum = contract["source_requirement"]["maximum_delivered_current_mA"]
        return {"normal_mA": candidate_normal, "derived_continuous_requirement_mA": candidate_continuous, "unrounded_transient_demand_mA": unrounded_transient, "derived_transient_requirement_mA": candidate_transient, "transient_rounding_allowance_mA": {rail: candidate_transient[rail] - unrounded_transient[rail] for rail in normal}, "physical_ceiling_minus_unrounded_demand_mA": {rail: maximum[rail] - unrounded_transient[rail] for rail in normal}, "maximum_delivered_mA_unchanged": maximum, "transient_requirements_within_original_maxima": all(maximum[rail] >= candidate_transient[rail] for rail in normal), "positive_limiter_window_mA": {rail: maximum[rail] - candidate_transient[rail] for rail in normal}, "original_strict_limiter_windows_met_arithmetically": all(maximum[rail] > candidate_transient[rail] for rail in normal), "protection_path_resistance_max_mohm_at_candidate_continuous": {rail: spec["limits_preserved"]["supply_protection_drop_V"] * 1e6 / candidate_continuous[rail] for rail in normal}}
    report = {
        "status": "CALCULATED SCREENS ONLY; protection gate OPEN",
        "protection_implemented": False,
        "condition_validation": {"original_scenario": "Bound to OSC-ES-1 signals/precision-cell notes and existing supply contract; exact envelope retained because the model receipt describes that envelope", "source_backed_fixed_fields": {name: locator for name, (_, locator) in SOURCE_CONDITIONS.items()}, "variable_sensitivity_fields": sorted(SENSITIVITY_CONDITIONS), "sensitivity_domains": "Positive finite contact/reservoir capacitance; finite sorted resistor ambient screens within -55..155 C; diagnostic guard strictly above leakage equilibrium and below initial/fault voltage. These are assumptions, not sourced guaranteed values."},
        "resistance_bounds": {"method": "1% tolerance times +/-100 ppm/C across -55..155 C around 25 C; relay Ron bound is separately only at 25 C", "minimum_factor": low, "maximum_factor": high, "drive_min_ohm": rd_min, "drive_max_ohm": rd_max, "sense_min_ohm": rs_min, "sense_max_ohm": rs_max},
        "precision": {"verdict": "NEEDS BENCH", "ideal_DC_load_error_upper_mV": load_mV, "input_bias_contribution_upper_mV": bias_mV, "subtotal_mV": load_mV + bias_mV, "limit_load_mV": spec["limits_preserved"]["load_error_mV"], "conditional_subtotal_below_load_limit": load_mV + bias_mV <= spec["limits_preserved"]["load_error_mV"], "formula": "e=V*Rd*Rs/[RL*(Rlocal+Rs+Rd)+Rd*Rs]; bias <= Ib*Rs", "scope": "Ideal amplifier DC network plus PW bias bound; not total calibrated accuracy. Offset, finite gain, thermal drift, actual +/-12 V conditions and dynamic error remain open."},
        "sustained_contention": {"verdict": "NEEDS BENCH", "condition": "Intact rail reference; external +/-12 V against a drive bounded by maximum opposite rail; no credit for a fault trip", "maximum_differential_V": fault, "main_current_upper_mA": current * 1000, "sense_current_upper_mA": fault / rs_min * 1000, "each_499_power_upper_W": resistor_power, "sense_resistor_power_upper_W": fault ** 2 / rs_min, "main_relay_power_at_25C_Ron_W": current ** 2 * c["relay_on_ohm_at_25C"], "maximum_resistor_ambient_from_derating_C": 155 - 85 * resistor_power / 0.5, "ambient_screens": [{"ambient_C": t, "allowed_each_499_W": 0.5 * min(1, max(0, (155 - t) / 85)), "within_resistor_power_curve": resistor_power <= 0.5 * min(1, max(0, (155 - t) / 85))} for t in c["resistor_screen_C"]], "amplifier_output_stage_power_screen_W": output_power, "whole_quad_quiescent_power_upper_W": iq_power, "one_active_core_package_power_screen_W": iq_power + output_power, "four_active_cores_package_power_screen_W": iq_power + 4 * output_power, "one_active_core_Tj_test_board_at_30C": 30 + (iq_power + output_power) * c["amplifier_theta_JA_C_per_W_test_board"], "thermal_limit": "Single output-stage two-rail linear transistor model only; saturation, input-clamp redistribution and actual PCB thetaJA not established. Do not use the typical short-current or thermal-shutdown curves as protection."},
        "isolated_off_boundary": {"verdict": "UNSOURCED", "condition": "Both LEDs IF=0, two contact leakage paths each <=1 uA at 25 C and contact <=60 V; rail bleeders fitted, no other energizing port. Does not bound absolute floating common mode.", "two_contact_leakage_upper_uA": leak * 1e6, "single_rail_steady_differential_upper_V": leak * bleeder_max, "bleeder_each_enabled_current_upper_mA": max(c["positive_rail_max_V"], c["negative_rail_magnitude_max_V"]) / (v("R_BLEED_P") * low) * 1000, "bleeder_each_enabled_power_upper_W": max(c["positive_rail_max_V"], c["negative_rail_magnitude_max_V"]) ** 2 / (v("R_BLEED_P") * low), "diagnostic_guard_V_not_original_requirement": guard, "conditional_steady_below_diagnostic_guard": leak * bleeder_max < guard, "discharge_time_to_guard_s_for_assumed_cap": bleeder_max * c["floating_rail_diagnostic_C_F"] * math.log((c["positive_rail_max_V"] - leak * bleeder_max) / (guard - leak * bleeder_max)), "discharge_capacitance_F_is_assumption": c["floating_rail_diagnostic_C_F"], "meaning": "Finite bleed prevents indefinite charging in this bounded leakage-only model; multi-second discharge does not prove immediate power-off or whole-board non-backpower."},
        "ground_loss_counterexample": {"verdict": "UNSOURCED", "argument_result": "COUNTEREXAMPLE to resistor-only isolation argument; actual device behavior UNSOURCED", "scope": "Only a resistor-only boundary with conductive/unqualified switch state and floating unloaded rail; not a demonstrated original-spec violation or a claim that every ground-independent topology is impossible", "counterexample_rail_V_at_1ms": floating_rail(c["fault_external_max_V"], rd_min, c["floating_rail_diagnostic_C_F"], 0.001), "assumed_cap_F": c["floating_rail_diagnostic_C_F"], "series_ohm": rd_min, "bleeder_max_ohm_for_diagnostic_guard": passive_bleed_max, "bleeder_current_at_12V_A": 12 / passive_bleed_max, "observation": "Any finite series resistor charges an unloaded floating rail toward the external source. The exact final behavior of an unqualified CMOS switch is unknown; this allowed conductive counterexample defeats a universal resistor-only proof."},
        "transition_bounds": {"verdict": "NEEDS BENCH", "turnoff_table_s_at_25C_only": c["relay_off_s_at_25C"], "each_499_energy_J_during_table_turnoff": resistor_power * c["relay_off_s_at_25C"], "detection_delay_is_additional_and_unbounded": True, "contact_cap_F_sensitivity_only": ccontact, "contact_charge_C_for_full_rail_span_step": ccontact * fault, "charge_share_into_min_local_10n_V_sensitivity_only": ccontact * fault / (v("C_LOCAL") * 0.95), "passive_cable_RC_s": rd_max * c["cable_max_F"], "meaning": "Contact capacitance lies between contact pins, not from either pin to GND. Charge/RC arithmetic is not op-amp settling, clamp stress, overshoot or power-off qualification."},
        "cold_collapse_before_contact_release": {"verdict": "UNSOURCED", "circuit_assumption": "Initially zero rail, external +12 V, both closed contacts and conductive pin-to-rail injection paths, one 100 kohm bleed, no regulator sink. Counterexample screen; not a vendor clamp model.", "detection_delay_assumed_s": 0, "contact_delay_s_conditional_25C_table": c["relay_off_s_at_25C"], "cold_main_initial_mA": c["fault_external_max_V"] / rd_min * 1000, "cold_sense_initial_mA": c["fault_external_max_V"] / rs_min * 1000, "sense_max_differential_current_mA": fault / rs_min * 1000, "amplifier_input_absolute_limit_mA_not_operating_target": c["amplifier_input_absolute_current_A"] * 1000, "amplifier_powered_off_output_injection_limit": "UNSOURCED; no output-pin input-clamp limit inferred", "cold_rail_V_at_contact_delay_for_assumed_cap": cold_final * -math.expm1(-c["relay_off_s_at_25C"] / cold_tau), "local_reservoir_F_is_assumption_not_fitted": c["floating_rail_diagnostic_C_F"], "conservative_C_min_F_for_cold_current_and_guard": cold_current * c["relay_off_s_at_25C"] / guard, "conservative_C_min_F_for_max_differential_and_guard": fault / injection_series * c["relay_off_s_at_25C"] / guard, "formula": "C >= (V/Rdrive_min + V/Rsense_min)*(t_detect+t_release)/deltaV; ignores bleed conservatively; capacitor initial voltage and derated reachable capacitance required", "meaning": "Even zero detection delay does not prove collapse protection. Bleeders address steady relay leakage after opening, not pre-opening current. Actual hot release, detector latency, capacitance/ESR and all shared-rail contributors remain open."},
        "shared_reservoir_sensitivity": {"verdict": "UNSOURCED", "condition": "If all 16 precision jacks are externally held at +12 V through common cold collapse; fault concurrency contract and actual shared paths remain to be established", "channels": simultaneous_precision, "conservative_cold_C_min_F": simultaneous_precision * cold_current * c["relay_off_s_at_25C"] / guard, "existing_nominal_cap_ceiling_F": nominal_cap_ceiling, "optimistic_reachable_C_at_nominal_ceiling_minus_tolerance_F": nominal_cap_ceiling * (1 - cap_tolerance), "maximum_detection_plus_release_s_for_constant_current_screen": guard * nominal_cap_ceiling * (1 - cap_tolerance) / (simultaneous_precision * cold_current), "meaning": "Assigning the entire existing rail-capacitance ceiling to this one purpose is already optimistic; remote capacitors may be disconnected by the fault. More bulk cannot be silently added. This diagnostic 0.3 V guard is not an original hard requirement."},
        "permit_budget": {"verdict": "UNSOURCED", "series_LED_current_A": c["led_characterization_A"], "two_LED_compliance_min_V_at_25C": 2 * c["led_Vf_max_at_5mA_25C"], "two_LED_dissipation_upper_W_at_25C": 2 * c["led_Vf_max_at_5mA_25C"] * c["led_characterization_A"], "sixteen_precision_cells_current_A_if_one_5V_current_source_each": 16 * c["led_characterization_A"], "sixteen_cell_5V_input_power_W_excluding_driver_overhead": 16 * 5 * c["led_characterization_A"], "meaning": "No fitted driver. 80 mA at 5 V for this illustrative 16-cell permit arrangement must be placed in the original ledger; it is not free power or an authorized population change."},
        "full_population_LED_screen": {"verdict": "BLOCKER - deterministic spec violation", "scope": "Only the stated +5 V LED-bias arrangements; not a universal ban on isolated relays or other bias architectures", "channels": channels, "independent_5mA_strings_mA": channels * led_mA, "strings_with_only_precision_drive_sense_pairs": paired_strings, "precision_paired_arrangement_mA": paired_strings * led_mA, "plus5_original_maximum_mA": replication["unchanged_plus5_maximum_mA"], "precision_paired_LED_load_alone_exceeds_entire_rail_maximum": paired_strings * led_mA > replication["unchanged_plus5_maximum_mA"], "all_contacts_in_pairs_mA_if_grouping_allowed": math.ceil(channels / 2) * led_mA, "existing_normal_with_allowances_mA": normal, "existing_continuous_requirement_mA": continuous, "existing_auxiliary_allowance_mA": aux, "all_paired_plus5_normal_mA_even_replacing_entire_auxiliary_allowance": normal["+5V"] - aux["+5V"] + math.ceil(channels / 2) * led_mA, "plus12_six_LEDs_per_string_current_mA": math.ceil(channels / 6) * led_mA, "plus12_normal_mA_six_LED_strings_even_replacing_entire_auxiliary_allowance": plus12_strings_normal, "plus12_required_continuous_mA_with_original_reserve_and_rounding": math.ceil(plus12_strings_normal * (1 + reserve) / rounding) * rounding, "normal_increment_headroom_before_original_reserve_mA": {rail: continuous[rail] / (1 + reserve) - normal[rail] for rail in normal}, "lower_IF_limit": "2 mA is recommended at 25 C, but selected G3HS Ron and timing maxima are tested at 5 mA. Do not carry those maxima to 2 mA. Input operate threshold is not a full timing/Ron guarantee.", "alternative_next_step": "AQY234SX has 35 ohm Ron and 2 ms release maxima at 2 mA/25 C, unlike the G3HS 5 mA test. Higher resistance is plausible inside feedback; longer release worsens collapse hold-up. Series strings across +/-12 V could reduce current, but require a captured regulator, independently safe permit, min-rail/hot-Vf compliance, shared fault grouping and complete normal/reserve ledger. No rail allocation changes."},
        "mixed_LED_and_input_switch_sensitivity": {"verdict": "UNSOURCED", "status": "No part substitution, source-contract edit, or current saving booked", "string_allocation": {"bipolar_strings": bipolar_strings, "LEDs_per_bipolar_string": bipolar_length, "positive_strings": positive_strings, "maximum_LEDs_per_positive_string": positive_length, "positive_string_LED_total": remaining_LEDs, "total_LED_count": bipolar_strings * bipolar_length + remaining_LEDs}, "added_LED_bias_mA": mixed_LED_mA, "added_only_16_precision_cell_bleeders_mA": added_bleed, "existing_auxiliary_allowance_retained_in_full_mA": aux, "actual_existing_ADG_package_count": len(old_packages), "existing_ADG_planning_mA": old_load, "hypothetical_110_TMUX_delta_mA": tmux_delta, "TMUX_current_condition": tmux["normal_iq_screen"]["conditions"], "minimum_bipolar_string_compliance_V_at_25C_Vf_bound": sum(contract["source_requirement"]["required_load_voltage_magnitude_V"][rail][0] for rail in ("+12V", "-12V")) - bipolar_length * c["led_Vf_max_at_5mA_25C"], "minimum_positive_string_compliance_V_at_25C_Vf_bound": contract["source_requirement"]["required_load_voltage_magnitude_V"]["+12V"][0] - positive_length * c["led_Vf_max_at_5mA_25C"], "without_input_switch_substitution": budget_case({}), "with_conditioned_exact_110_input_switch_substitution": budget_case(tmux_delta), "limits": "Current minimum is a derived delivery requirement, not maximum capacity. All original maxima, reserve, ramp, fault increment and strict positive limiter windows remain. TMUX current at actual project rails, hot LED Vf, 14 real current regulators, all extra bleeders/reference loads, string/board fault grouping and independent permit must be captured; this arithmetic is not a complete power or protection design."},
        "bipolar_strings_without_IC_substitution": {"verdict": "UNSOURCED", "status": "Prospective requirement arithmetic only; existing contract remains 1700/1600/300 mA until captured change", "conditions": "128 LEDs grouped into 10..12 independent strings of at most 13 LEDs across +/-12 V at 5 mA; no 110-IC substitution; all existing auxiliary allowance retained, 16 precision-cell bleeders added. Real locality/string map and regulator/control overhead not proven.", "cases": [{"string_count": count, "bias_mA_each_analog_rail": count * led_mA, **budget_case({}, {"+12V": count * led_mA, "-12V": count * led_mA, "+5V": 0})} for count in (10, 11, 12)], "meaning": "Prospective 1800/1700 mA continuous and 2100/2000 mA transient requirements can equal the original analog maximum-delivered ceilings without changing the 4.6 A return or 40 mV target. Equality leaves ZERO positive limiter window, so the current full source acceptance still fails. Resolve actual limiter tolerance/dynamics and requirement window; do not claim selected or quietly rewrite the contract."},
        "open_obligations": spec["open_obligations"],
    }
    # Finite inputs can still overflow through extreme sensitivity products.
    # Fail closed before either direct callers or serialization receive infinity.
    def check_finite(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                check_finite(child)
        elif isinstance(value, list):
            for child in value:
                check_finite(child)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Sensitivity arithmetic produced a nonfinite result")
    check_finite(report)
    return report


def connectivity(spec: dict) -> str:
    lines = ["GENERATED by scripts/checks/precision_output_cell.py", spec["status"],
             "Pin connectivity only; not a KiCad schematic, netlist receipt or fabrication input.", ""]
    for p in spec["parts"]:
        lines.append(f"{p['ref']} {p['mpn']}")
        lines.extend(f"  {pin}: {net}" for pin, net in p["pins"].items())
    lines += ["", "Permit driver, supply decoupling and board integration are OPEN; see source spec.", ""]
    return "\n".join(lines)


def run(check: bool = False) -> None:
    spec, sources = json.loads(SPEC.read_text()), json.loads(SOURCES.read_text())
    validate(spec, sources)
    report = calculate(spec)
    report["input_sha256"] = {str(p.relative_to(ROOT)): digest(p) for p in (SPEC, SOURCES, SUPPLY, LEDGER, SWITCH_SOURCES, STANDARD, PROTECTION_AUDIT, Path(__file__).resolve())}
    outputs = {REPORT: json.dumps(report, indent=2, allow_nan=False) + "\n", NETLIST: connectivity(spec)}
    for path, body in outputs.items():
        if check:
            if not path.exists() or path.read_text() != body:
                raise ValueError(f"Generated candidate drift: {path.relative_to(ROOT)}")
        else:
            path.write_text(body)
    print("PASS: candidate topology/evidence receipts/arithmetic; hardware protection remains OPEN")
    for source in sources["sources"]:
        if not (ROOT / source["file"]).exists():
            print(f"NOT RUN: optional source-byte check for {source['id']}; retained acquisition receipt present, local PDF cache absent")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    run(parser.parse_args().check)
