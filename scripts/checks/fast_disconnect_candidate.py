"""Bound a discrete candidate and its counterexamples; never hardware admission."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "design/power/fast-disconnect-candidate.json"
SOURCES = ROOT / "design/power/fast-disconnect-candidate-sources.json"
REPORT = ROOT / "design/power/fast-disconnect-candidate-report.json"
STANDARD = ROOT / "design/standard/electrical-standard.json"
SUPPLY = ROOT / "design/power/supply-architecture.json"
PRECISION = ROOT / "design/power/precision-output-cell-report.json"
PRECISION_SPEC = ROOT / "design/power/precision-output-cell.json"
PROTECTION_AUDIT = ROOT / "design/power/protection58-audit.json"

SOURCE_VALUES = {
    "mos_VDS_abs_V": 60, "mos_VGS_abs_V": 20,
    "mos_VGSth_min_V_at_26uA_25C": 0.6, "mos_VGSth_max_V_at_26uA_25C": 1.4,
    "mos_Ron_max_ohm_at_4p5V_30mA_25C": 4,
    "mos_Qg_max_C_at_10V_48V_230mA_25C": 1.4e-9,
    "mos_Ciss_max_F_at_0VGS_25VDS_1MHz": 41e-12,
    "mos_toff_delay_max_s_at_6ohm_driver": 10e-9,
    "mos_fall_max_s_at_6ohm_driver": 12.3e-9,
    "mos_off_A_at_0VGS_60VDS_25C": 1e-7, "mos_off_A_at_0VGS_60VDS_150C": 5e-6,
    "pnp_storage_max_s_at_reverse_1mA_base": 225e-9,
    "pnp_fall_max_s_at_reverse_1mA_base": 75e-9,
    "pnp_CBO_max_A_at_30V_25C": 50e-9,
    "pnp_VBEsat_max_V_at_10mA_1mA_25C": 0.85,
    "diode_reverse_max_A_at_75V_25C": 5e-9, "diode_reverse_max_A_at_75V_150C": 80e-9,
    "diode_reverse_recovery_max_s_at_10mA": 3e-6,
    "zener_V_nom_V": 8.2, "zener_Vmax_V_at_5mA_25C": 8.61,
    "zener_FR4_power_W_at_25C": 0.3,
    "whole_gate_network_charge_max_C": None, "complete_disconnect_delay_max_s": None,
}
PARTS = {
    "Q_LOCAL": ("BSS138NH6327XTSA2", {"D": "LOCAL", "S": "SOURCE_COMMON", "G": "GATE"}, None),
    "Q_EXT": ("BSS138NH6327XTSA2", {"D": "EXTERNAL_LIMITED", "S": "SOURCE_COMMON", "G": "GATE"}, None),
    "Q_UP": ("MMBT3906,215", {"E": "VP", "B": "PNP_BASE", "C": "PULLUP"}, None),
    "D_BLOCK": ("BAS116,215", {"A": "PULLUP", "K": "FEED"}, None),
    "R_FEED_A": ("RC1210FR-071KL", {"1": "FEED", "2": "GATE"}, 1000),
    "R_FEED_B": ("RC1210FR-071KL", {"1": "FEED", "2": "GATE"}, 1000),
    "R_GS": ("RC0805FR-0710KL", {"1": "GATE", "2": "SOURCE_COMMON"}, 10000),
    "Z_GS": ("BZT52C8V2-E3-08", {"K": "GATE", "A": "SOURCE_COMMON"}, None),
    "R_BE": ("RC0805FR-07100KL", {"1": "PNP_BASE", "2": "VP"}, 100000),
    "R_BASE": ("RC0805FR-0710KL", {"1": "PNP_BASE", "2": "PERMIT_SINK"}, 10000),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive(value: object, name: str) -> None:
    try:
        valid = type(value) in (float, int) and math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} requires a positive finite physical magnitude")


def validate(spec: dict) -> dict:
    if spec["protection_implemented"] or "NOT IMPLEMENTED" not in spec["status"]:
        raise ValueError("Candidate cannot claim implemented protection")
    if spec["source_values"] != SOURCE_VALUES:
        raise ValueError("Sourced values/test conditions changed, or an unknown timing bound was invented")
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text())["sources"]}
    parts = {p["ref"]: p for p in spec["parts"]}
    if len(parts) != len(spec["parts"]) or set(parts) != set(PARTS):
        raise ValueError("Candidate population changed")
    for ref, (mpn, terminals, value) in PARTS.items():
        p = parts[ref]
        if p["mpn"] != mpn or p["terminals"] != terminals or p.get("value_ohm") != value or sources[p["source"]]["mpn"] != mpn:
            raise ValueError(f"{ref} identity/value/source-referenced boundary changed")
    d = spec["diagnostics"]
    expected = {"body_diode_drop_V", "PNP_on_drop_V", "blocking_diode_on_drop_V", "cutoff_VGS_V_not_off_leakage_guarantee", "ideal_bias_injection_A_for_KCL", "hybrid_drive_delay_s_sensitivity", "future_soft_start_ms_sensitivity", "current_limited_drive_mA_sensitivity", "note"}
    if set(d) != expected:
        raise ValueError("Unclassified diagnostic input")
    for name, value in d.items():
        if name == "note":
            continue
        for item in value if isinstance(value, list) else [value]:
            positive(item, name)
    if not d["hybrid_drive_delay_s_sensitivity"]:
        raise ValueError("At least one hybrid delay sensitivity required")
    if d["cutoff_VGS_V_not_off_leakage_guarantee"] >= SOURCE_VALUES["mos_VGSth_min_V_at_26uA_25C"]:
        raise ValueError("Diagnostic cutoff must stay below the threshold test, without claiming zero-VGS leakage")
    if d["body_diode_drop_V"] > 1.2:
        raise ValueError("Body-diode diagnostic changed outside its declared 25 C voltage screen")
    checked, missing = [], []
    for s in sources.values():
        path = ROOT / s["file"]
        if path.exists():
            if sha(path) != s["sha256"] or path.stat().st_size != s["bytes"]:
                raise ValueError("Retained source changed: " + s["id"])
            checked.append(s["id"])
        else:
            missing.append(s["id"])
    return {"verified_local_bytes": checked, "local_cache_not_present": missing}


def linear_solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Small independent nodal solve; no MOSFET dynamics are modeled."""
    a = [row[:] + [v] for row, v in zip(matrix, rhs)]
    for k in range(len(a)):
        pivot = max(range(k, len(a)), key=lambda i: abs(a[i][k]))
        a[k], a[pivot] = a[pivot], a[k]
        if a[k][k] == 0:
            raise ValueError("Singular nodal system")
        scale = a[k][k]
        a[k] = [v / scale for v in a[k]]
        for i in range(len(a)):
            if i != k:
                scale = a[i][k]
                a[i] = [v - scale * w for v, w in zip(a[i], a[k])]
    return [row[-1] for row in a]


def sense_nodes(vin: float, injected_A: float, drive_R: float, sense_R: float,
                local_R: float, contact_R: float, load_R: float) -> dict:
    """Unknowns [DRIVE,JACK,SOURCE_COMMON], ideal FB=Vin.

    SOURCE_COMMON connects FB through one MOS and JACK through the other MOS
    plus R_SENSE. Gate bleed/clamp current enters this node, not an ideal gate.
    """
    rd, rs, rl, rq, load = drive_R, sense_R + contact_R, local_R, contact_R, load_R
    matrix = [[1 / rl, 0, 1 / rq],
              [0, -1 / rs, 1 / rs + 1 / rq],
              [-1 / rd, 1 / rd + 1 / load + 1 / rs, -1 / rs]]
    values = linear_solve(matrix, [vin * (1 / rl + 1 / rq), vin / rq + injected_A, 0])
    return dict(zip(("drive_V", "jack_V", "source_common_V"), values))


def pullup_screen(source_V: float, rail_V: float, feed_R: float, bleed_R: float,
                  on_drop_V: float, diode_drop_V: float, clamp_V: float) -> dict:
    """Ideal piecewise DC countermodel, not a guaranteed Zener/PNP transfer."""
    headroom = rail_V - on_drop_V - diode_drop_V - source_V
    vgs = max(0, min(clamp_V, headroom * bleed_R / (feed_R + bleed_R)))
    total = max(0, (headroom - vgs) / feed_R)
    bleed = vgs / bleed_R
    return {"source_V": source_V, "VGS_V": vgs, "pullup_current_mA": total * 1000,
            "bleed_current_mA": bleed * 1000, "zener_current_mA": max(0, total - bleed) * 1000,
            "zener_power_W": max(0, total - bleed) * vgs}



def coupled_sense_nodes(vin: float, drive_R: float, sense_R: float,
                        local_R: float, contact_R: float, load_R: float,
                        pullup_V: float, feed_R: float, bleed_R: float,
                        clamp_V: float) -> dict:
    """Close the ideal DC pull-up KCL; output saturation is reported, not solved.

    The sense network is affine in injected current. Each driver branch is
    affine in common-source voltage; solve their intersection and retain only
    the branch consistent with its own gate/clamp voltage.
    """
    args = (drive_R, sense_R, local_R, contact_R, load_R)
    zero = sense_nodes(vin, 0, *args)
    unit = sense_nodes(vin, 1, *args)
    slope = unit["source_common_V"] - zero["source_common_V"]
    for mode, resistance, offset in (("clamped", feed_R, clamp_V),
                                      ("unclamped", feed_R + bleed_R, 0)):
        current = (pullup_V - zero["source_common_V"] - offset) / (resistance + slope)
        nodes = sense_nodes(vin, current, *args)
        headroom = pullup_V - nodes["source_common_V"]
        unclamped_vgs = headroom * bleed_R / (feed_R + bleed_R)
        if current >= 0 and ((mode == "clamped" and unclamped_vgs >= clamp_V)
                             or (mode == "unclamped" and 0 <= unclamped_vgs < clamp_V)):
            return {"signal_V": vin, **nodes, "pullup_current_A": current,
                    "VGS_V": min(clamp_V, unclamped_vgs), "branch": mode}
    if pullup_V <= zero["source_common_V"]:
        return {"signal_V": vin, **zero, "pullup_current_A": 0, "VGS_V": 0, "branch": "off"}
    raise ValueError("No self-consistent piecewise sense-driver solution")


def drive_nodes(vin: float, injected_A: float, contact_R: float, load_R: float) -> dict:
    """Hybrid DC: current enters drive common source, isolated sense is neutral."""
    rq, out, sense, local = contact_R, 998 + contact_R, 4990 + 0.12, 1e7
    matrix = [[1 / local, 1 / sense, 0],
              [-1 / rq, -1 / out, 1 / rq + 1 / out],
              [0, 1 / out + 1 / load_R + 1 / sense, -1 / out]]
    values = linear_solve(matrix, [vin * (1 / local + 1 / sense), injected_A, vin / sense])
    return dict(zip(("drive_V", "jack_V", "source_common_V"), values))


def calculate(spec: dict) -> dict:
    validate(spec)
    standard = json.loads(STANDARD.read_text())
    architecture = json.loads(SUPPLY.read_text())
    contract, supply = architecture["contract"], architecture["selected_requirement"]
    previous = json.loads(PRECISION.read_text())
    cell = json.loads(PRECISION_SPEC.read_text())
    audit = json.loads(PROTECTION_AUDIT.read_text())
    general_outputs = [row for row in audit["outputs"] if row["kind"] == "general"]
    precision_outputs = [row for row in audit["outputs"] if row["kind"] == "precision"]
    if len(general_outputs) != 66 or len(precision_outputs) != 16 or audit["output_count"] != 82:
        raise ValueError("Original82/16/66 output obligation changed; review population/concurrency")
    general_cell = next(row for row in standard["cells"] if row["id"] == "general_output")
    s, d = spec["source_values"], spec["diagnostics"]
    signals = standard["signals"]
    rail = contract["source_requirement"]["required_load_voltage_magnitude_V"]
    signal = max(abs(v) for v in signals["bipolar_cv_nominal_V"])
    fault = max(abs(v) for v in signals["input_continuous_fault_V"])
    load = signals["minimum_output_load_ohm"]
    r = previous["resistance_bounds"]
    rgs = PARTS["R_GS"][2]
    rgs_max = rgs * r["maximum_factor"]
    gate_q = 2 * s["mos_Qg_max_C_at_10V_48V_230mA_25C"]
    cutoff = d["cutoff_VGS_V_not_off_leakage_guarantee"]
    contact_R = s["mos_Ron_max_ohm_at_4p5V_30mA_25C"]
    baseline = sense_nodes(signal, 0, 998 + 2 * contact_R, 4990, 1e7, contact_R, load)
    biased = sense_nodes(signal, d["ideal_bias_injection_A_for_KCL"], 998 + 2 * contact_R, 4990, 1e7, contact_R, load)
    gain = sense_nodes(0, 1, 998 + 2 * contact_R, 4990, 1e7, contact_R, load)["jack_V"]
    allowed_injection = signals["precision_load_error_max_V"] / abs(gain)
    # To claim the sourced 4.5 V Ron condition, this bleed alone draws >=V/R.
    minimum_on_bleed = 4.5 / rgs_max
    coupled_sense = [coupled_sense_nodes(vin, 998 + 2 * contact_R, 4990, 1e7,
        contact_R, load, rail["+12V"][1] - d["PNP_on_drop_V"] - d["blocking_diode_on_drop_V"],
        500, rgs, s["zener_V_nom_V"]) for vin in (-signal, 0, signal)]
    for row in coupled_sense:
        row["required_drive_outside_even_maximum_rail_magnitudes"] = not (
            -rail["-12V"][1] <= row["drive_V"] <= rail["+12V"][1])
    max_source = signal * (1 + (r["drive_max_ohm"] + contact_R) / load)
    rows = [pullup_screen(x, rail["+12V"][1], 500, rgs, d["PNP_on_drop_V"], d["blocking_diode_on_drop_V"], s["zener_V_nom_V"]) for x in (-max_source, 0, max_source)]
    low_headroom = pullup_screen(max_source, rail["+12V"][0], 500 * r["maximum_factor"], rgs * r["minimum_factor"], d["PNP_on_drop_V"], d["blocking_diode_on_drop_V"], s["zener_V_nom_V"])
    count = cell["replication_screen"]["precision_sense_channels"]
    main_i, sense_i = fault / r["drive_min_ohm"], fault / r["sense_min_ohm"]
    sense_delay = cell["conditions"]["relay_off_s_at_25C"]
    guard = cell["conditions"]["off_rail_diagnostic_guard_V"]
    accessible_C = contract["source_requirement"]["nominal_capacitance_ceiling_uF"]["+12V"] * 1e-6 * (1 - contract["source_requirement"]["capacitance_tolerance_fraction"])
    drive_delay_budget = (guard * accessible_C / count - sense_i * sense_delay) / main_i
    all_drive_count = audit["output_count"]
    all_drive_delay_budget = (guard * accessible_C - count * sense_i * sense_delay) / (all_drive_count * main_i)
    hybrid = []
    for delay in d["hybrid_drive_delay_s_sensitivity"]:
        charge = count * (main_i * delay + sense_i * sense_delay)
        hybrid.append({"assumed_drive_release_s": delay, "sense_release_s_conditional_25C": sense_delay,
                       "conservative_C_needed_F_for_guard": charge / guard,
                       "maximum_detection_delay_s_for_assumed_accessible_C": (guard * accessible_C - charge) / (count * (main_i + sense_i))})
    all_outputs_collapse = [{"assumed_equal_drive_release_s": delay,
        "conservative_C_needed_F_for_guard": (all_drive_count * main_i * delay + count * sense_i * sense_delay) / guard,
        "maximum_detection_delay_s_for_assumed_accessible_C": (guard * accessible_C - all_drive_count * main_i * delay - count * sense_i * sense_delay) / (all_drive_count * main_i + count * sense_i)} for delay in d["hybrid_drive_delay_s_sensitivity"]]
    positive_base_mA = rail["+12V"][1] / (PARTS["R_BASE"][2] * r["minimum_factor"]) * 1000
    bleed_mA = previous["isolated_off_boundary"]["bleeder_each_enabled_current_upper_mA"] * count
    limited = d["current_limited_drive_mA_sensitivity"]
    if d["future_soft_start_ms_sensitivity"] < contract["source_requirement"]["soft_start_min_ms"]:
        raise ValueError("Future soft-start sensitivity cannot weaken the original minimum duration")
    hybrid_dc = [dict(signal_V=vin, **drive_nodes(vin, limited / 1000, contact_R, load)) for vin in (-signal, 0, signal)]
    normal = supply["normal_with_allowances_mA"]
    # No existing auxiliary allowance is removed. Gate/clamp current can flow
    # through the output amplifier into the negative rail and is charged there.
    def budget(drive_count: int, drive_current_mA: float, ramp_ms: float) -> dict:
        candidate = {"+12V": normal["+12V"] + drive_count * (drive_current_mA + positive_base_mA) + bleed_mA,
                     "-12V": normal["-12V"] + drive_count * drive_current_mA + bleed_mA,
                     "+5V": normal["+5V"] + math.ceil(count / 2) * 5}
        env = contract["load_envelope"]
        continuous = {k: math.ceil(v * (1 + env["reserve_fraction"]) / env["current_rounding_mA"]) * env["current_rounding_mA"] for k, v in candidate.items()}
        ramp = {k: contract["source_requirement"]["nominal_capacitance_ceiling_uF"][k] * (1 + contract["source_requirement"]["capacitance_tolerance_fraction"]) * rail[k][1] / ramp_ms for k in candidate}
        unrounded = {k: continuous[k] + ramp[k] + env["fault_increment_mA"][k] for k in candidate}
        transient = {k: math.ceil(v / env["current_rounding_mA"]) * env["current_rounding_mA"] for k, v in unrounded.items()}
        maximum = contract["source_requirement"]["maximum_delivered_current_mA"]
        return {"drive_count": drive_count, "assumed_current_limit_mA_each": drive_current_mA, "soft_start_min_ms_sensitivity": ramp_ms,
                "normal_mA": candidate, "continuous_requirement_mA": continuous, "ramp_increment_mA": ramp,
                "unrounded_transient_mA": unrounded, "rounded_transient_mA": transient,
                "maximum_delivered_mA_unchanged": maximum,
                "worst_return_current_ceiling_A_unchanged": sum(maximum.values()) / 1000,
                "protection_path_max_mohm_at_prospective_continuous": {k: cell["limits_preserved"]["supply_protection_drop_V"] * 1e6 / continuous[k] for k in candidate},
                "strict_limiter_window_mA": {k: maximum[k] - transient[k] for k in candidate},
                "arithmetic_windows_positive": all(maximum[k] > transient[k] for k in candidate)}
    report = {
        "status": "REJECTED DIRECT SENSE CIRCUIT; DRIVE/HYBRID TIMING UNSOURCED; no implementation admission",
        "protection_implemented": False,
        "original_envelope": {"signal_max_V": signal, "external_fault_max_V": fault, "load_min_ohm": load,
            "precision_load_error_max_V": signals["precision_load_error_max_V"], "settling_deadline_s": cell["limits_preserved"]["settling_deadline_s"],
            "supply_drop_max_V": cell["limits_preserved"]["supply_protection_drop_V"]},
        "power_off_polarity_counterexamples": [
            {"external_V": polarity * fault, "assumed_internal_V": 0,
             "off_assumption_source_V": min(0, polarity * fault) + d["body_diode_drop_V"],
             "grounded_gate_VGS_V": -min(0, polarity * fault) - d["body_diode_drop_V"],
             "source_referenced_ideal_gate_VGS_V": 0,
             "finding": "Negative external voltage makes the grounded-gate OFF assumption self-inconsistent; do not infer a steady RDS current from that transient voltage." if polarity < 0 else "Positive external voltage does not produce that particular false-on condition with the internal node held at zero."}
            for polarity in (-1, 1)],
        "off_state_limits": {"verdict": "UNSOURCED", "scope": "Source-referenced bleed is necessary but not a complete off-state proof. Both body diodes point from common source toward their drains. Rail absent is not permission to ground GATE.",
            "positive_common_mode_counterexample": "Without D_BLOCK, a still-positive SOURCE_COMMON/GATE can forward-bias Q_UP collector-base into an absent VP rail; the G-S clamp/bleed provides an unwanted analog-to-control path.",
            "remaining": "Actual driver leakage, temperature, dV/dt/Miller injection, positive and negative source motion, clamp charge and independent permit are unresolved; VGS=0 table leakage is not guaranteed at the diagnostic 0.1 V cutoff."},
        "sense_injection": {"verdict": "REJECTED AS DRAWN - conditional DC countermodel requires unavailable amplifier swing", "condition": "DC ideal-amplifier countermodel with the stated ON contact resistance; any real implementation must first satisfy gate/rail operating conditions.",
            "baseline_nodes_V": baseline, "nodes_with_diagnostic_injection_V": biased,
            "diagnostic_injection_A": d["ideal_bias_injection_A_for_KCL"],
            "jack_change_V": biased["jack_V"] - baseline["jack_V"], "injection_transfer_ohm": gain,
            "diagnostic_uncompensated_static_error_allocation_V": signals["precision_load_error_max_V"],
            "maximum_injection_A_for_diagnostic_static_error_allocation": allowed_injection,
            "minimum_ON_bleed_A_at_4p5V_gate": minimum_on_bleed,
            "minimum_uncompensated_static_shift_V_in_linear_countermodel": abs(gain) * minimum_on_bleed,
            "minimum_RGS_ohm_for_diagnostic_static_error_allocation": 4.5 / allowed_injection,
            "coupled_resistive_driver_countermodel": coupled_sense,
            "meaning": "The gate is insulated; the external gate-source resistor and clamp are not. This injection creates DC transfer/offset error, not automatically the difference between unloaded and loaded output. The1mV static allocation is diagnostic, not a newly inferred original absolute-accuracy limit. Calibration could remove a constant offset at one point; the captured signal-dependent driver additionally requires amplifier swing outside the rails in this countermodel. No compensation redesign is captured."},
        "resistive_pullup_DC_sensitivity": {"verdict": "NEEDS BENCH", "nominal_clamp_assumption_V": s["zener_V_nom_V"],
            "rows": rows, "minimum_rail_positive_signal_screen": low_headroom,
            "base_sink_upper_mA_each": positive_base_mA,
            "scope": "Assumed PNP/diode drops and ideal 8.2 V clamp. Vz max is specified at5mA, not arbitrary fault current. This is a countermodel for current burden, not a guaranteed operating envelope.",
            "gate_and_clamp_current_return": "Complete pullup current returns to analog SOURCE_COMMON; drive feedback can compensate voltage but its amplifier must carry the current."},
        "turnoff_evidence": {"verdict": "UNSOURCED", "two_MOS_Qg_table_upper_C": gate_q,
            "conditional_charge_over_min_bleed_current_s": gate_q * rgs_max / cutoff,
            "PNP_base_reverse_current_initial_screen_A": s["pnp_VBEsat_max_V_at_10mA_1mA_25C"] / PARTS["R_BE"][2],
            "PNP_reverse_current_required_by_timing_table_A": 0.001,
            "MOS_table_delay_plus_fall_s": s["mos_toff_delay_max_s_at_6ohm_driver"] + s["mos_fall_max_s_at_6ohm_driver"],
            "whole_network_charge_max_C": None, "whole_disconnect_max_s": None,
            "gaps": "Qg bound is at10V gate/48V drain/230mA/25C, not every cold-collapse trajectory. Add clamp/diode/driver charge and Miller/source motion; PNP resistor discharge does not provide the tested reverse base current. Ciss max at one bias cannot replace a charge bound over the full transition."},
        "hybrid_DC_headroom_screen": {"verdict": "NEEDS BENCH", "assumed_gate_current_A": limited / 1000,
            "rows": hybrid_dc, "maximum_ideal_jack_error_V": max(abs(row["jack_V"] - row["signal_V"]) for row in hybrid_dc),
            "additional_output_sink_power_screen_W": (signal * (1 + (998 + contact_R) / load) + rail["-12V"][1]) * limited / 1000,
            "scope": "Fixed4-ohm MOS contacts at their conditional25C row; isolated sense carries no driver bias. Ideal amplifier DC only. Offset, finite gain, package heat, actual supply/temperature, charge injection and1ms transient target remain unverified."},
        "hybrid_collapse": {"verdict": "UNSOURCED", "precision_output_count": count,
            "condition": "All16 precision jacks simultaneously held at+12V during cold collapse; constant-current bound, no credit for bleeders or regulator sinking. Sense release uses conditional25C PhotoMOS table only.",
            "main_initial_A_each": main_i, "sense_initial_A_each": sense_i,
            "diagnostic_guard_V_not_original_requirement": guard,
            "optimistic_reachable_capacitance_F": accessible_C,
            "capacitance_is_not_fitted_or_locally_reachable_proof": True,
            "both_PhotoMOS_C_required_F": count * (main_i + sense_i) * sense_delay / guard,
            "hybrid_max_drive_release_s_with_zero_detection_delay": drive_delay_budget,
            "RGS_max_ohm_for_conditional_MOS_Q_over_I_proof_ignoring_all_extra_charge": drive_delay_budget * cutoff / gate_q,
            "sensitivities": hybrid,
            "scope": "Only these16 precision outputs are counted; unqualified remaining66 outputs/30 reference connections cannot be assigned zero injection. Local capacitors disconnected by the fault cannot be counted."},
        "all_output_obligations": {"verdict": "UNSOURCED", "total_drive_contacts": all_drive_count,
            "precision_count": len(precision_outputs), "general_count": len(general_outputs),
            "general_output_uids": [row["uid"] for row in general_outputs],
            "general_source_connections": general_cell["connections"], "general_source_notes": general_cell["notes"],
            "material_difference": "General outputs use local feedback before998ohm and need one drive disconnect, not a second precision sense contact. The1mV load-error target is precision-specific; general +/-5V is specified unloaded. This can simplify circuitry but does not waive signal fidelity or permit arbitrary bias/distortion.",
            "common_fault_obligations": "All82 share998ohm series resistance and sustained external +/-12V, off/partial-rail/GND-loss analysis. General unipolar/gate outputs are still externally bipolar fault ports; a single MOS body diode is not a bidirectional disconnect. No slower release or backpower exemption found.",
            "envelope_0_to_8V_uids": [row["uid"] for row in general_outputs if row["uid"].endswith('.ENV')],
            "plus8V_gate_headroom_screen": pullup_screen(max(signals["envelope_V"]), rail["+12V"][0], 500 * r["maximum_factor"], rgs * r["minimum_factor"], d["PNP_on_drop_V"], d["blocking_diode_on_drop_V"], s["zener_V_nom_V"]),
            "plus8V_limit": "This BSS138N driver does not establish the4.5V gate condition at+8V. A lower-gate-voltage guaranteed MOSFET or floating/boosted drive must be proved; no catalog typical curve is an exemption.",
            "complete_concurrent_collapse_sensitivity": {"condition": "All82 drives and16 precision senses externally driven during the same cold collapse; concurrency sensitivity, not a new claim of simultaneous-all-output-short supply capacity.30 reference paths remain unquantified.",
                "maximum_equal_drive_release_s_zero_detector_delay": all_drive_delay_budget,
                "optimistic_reachable_C_F": accessible_C, "rows": all_outputs_collapse},
            "conclusion": "The16-cell hybrid cannot close issue59. Only removal of the extra sense contact is established for the other66; an actually cheaper compliant drive circuit is not established."},
        "hybrid_power_sensitivity": {"verdict": "UNSOURCED", "sense_LED_mA_on_plus5": math.ceil(count / 2) * 5,
            "all_existing_auxiliary_allowances_retained": True,
            "sixteen_precision_at_current_ramp": budget(count, limited, contract["source_requirement"]["soft_start_min_ms"]),
            "sixteen_precision_at_future_slower_ramp": budget(count, limited, d["future_soft_start_ms_sensitivity"]),
            "all_82_drive_contacts_at_future_slower_ramp": budget(cell["replication_screen"]["drive_channels"], limited, d["future_soft_start_ms_sensitivity"]),
            "sixteen_resistive_pullups_at_negative_signal_sensitivity": budget(count, max(row["pullup_current_mA"] for row in rows), d["future_soft_start_ms_sensitivity"]),
            "limitations": "The4mA current-limited source is a proposed replacement for the resistive pull-up, not a captured circuit. Includes gate current on BOTH analog rails, base current on+12,16 bleeders and40mA sense LEDs on+5. Driver overhead must fit retained supervision allowance. Remaining output/reference families, leakage, dynamic loads and real string grouping still open."},
        "slower_startup_review": {"current_minimum_ms": contract["source_requirement"]["soft_start_min_ms"],
            "future_sensitivity_ms": d["future_soft_start_ms_sensitivity"],
            "original_standard_note": standard["supply_architecture"]["capacitance_policy"],
            "interpretation": "No faster than10ms is a minimum duration, so15ms is not forbidden by this cited rule. No maximum startup deadline found in OSC-ES-1/source contract. Actual module sequencing/functional startup must still be qualified; this does not change shutdown timing or any source file."},
        "current_neutral_alternative": {"mpn": "VOM1271T", "source": "vom1271", "verdict": "UNSOURCED",
            "mechanism": "Floating photovoltaic output between GATE and SOURCE_COMMON avoids the DC rail-to-sense-node bias path.",
            "turnoff_65us_value_class": "TYPICAL ONLY at IF20mA,CL200pF,25C; maximum blank in retained Rev1.9",
            "meaning": "No guaranteed release bound. IF10mA gives sourced minimum VOC/ISC but not a turnoff maximum; LED burden and full gate charge remain."},
        "open_obligations": spec["open_obligations"],
    }
    # No JSON NaN/Infinity is allowed to turn a failed calculation into a report.
    json.dumps(report, allow_nan=False)
    return report


def run(check: bool = False) -> None:
    spec = json.loads(SPEC.read_text())
    cache = validate(spec)
    report = calculate(spec)
    report["input_sha256"] = {str(p.relative_to(ROOT)): sha(p) for p in (SPEC, SOURCES, STANDARD, SUPPLY, PRECISION, PRECISION_SPEC, PROTECTION_AUDIT, Path(__file__).resolve())}
    body = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if check:
        if not REPORT.exists() or REPORT.read_text() != body:
            raise ValueError("Fast-disconnect candidate report drift")
    else:
        REPORT.write_text(body)
    print("PASS: candidate arithmetic/identity checks; sense circuit rejected, complete timing UNSOURCED")
    print(f"Source bytes verified locally: {len(cache['verified_local_bytes'])}; absent optional caches: {cache['local_cache_not_present']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    run(parser.parse_args().check)
