"""Conditioned ADG5401F candidate arithmetic, never protection admission."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'design/power/integrated-output-candidate.json'
SOURCES = ROOT / 'design/power/integrated-output-candidate-sources.json'
REPORT = ROOT / 'design/power/integrated-output-candidate-report.json'
PREVIOUS = ROOT / 'design/power/precision-output-cell.json'
PREVIOUS_REPORT = ROOT / 'design/power/precision-output-cell-report.json'
PREVIOUS_SOURCES = ROOT / 'design/power/precision-output-cell-sources.json'
STANDARD = ROOT / 'design/standard/electrical-standard.json'
SUPPLY = ROOT / 'design/power/supply-architecture.json'
AUDIT = ROOT / 'design/power/protection58-audit.json'
ZERO = '0' * 64
LOCKED_OBSERVATIONS = 'ee652ef42a68e09bc3fc99b1b2b53abc975d714ca976e37c5c9b55142aa8463e'
LOCKED_PARTS = '6db4edbba64e014a8612c2bbdc1f8dcb760ed57c3906def91a379e1492a0d1b1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positive(value, name):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(name + ': positive finite magnitude required')


def validate(spec):
    if spec['protection_implemented'] is not False or 'NOT IMPLEMENTED' not in spec['status']:
        raise ValueError('Candidate cannot claim implementation')
    if spec['identity']['mpn'] != 'ADG5401FBCPZ-RL7' or spec['identity']['package'] != 'CP-10-16':
        raise ValueError('Exact F-family identity/package changed')
    if spec['identity']['supplier_order_code'] != '505-ADG5401FBCPZ-RL7CT-ND':
        raise ValueError('Exact observed order identity changed')
    if digest(spec['parts']) != LOCKED_PARTS:
        raise ValueError('Reviewed source-facing topology or exact parts changed')
    if digest(spec['observed_datasheet_conditions']) != LOCKED_OBSERVATIONS:
        raise ValueError('Observed table values or their conditions changed')
    required = {'Ron_max_ohm', 'feedback_Ron_max_ohm', 'leakage_max_A',
                'supply_current_max_mA', 'complete_release_max_s', 'floating_ground_behavior'}
    if set(spec['project_guarantees']) != required or any(v is not None for v in spec['project_guarantees'].values()):
        raise ValueError('Missing project guarantees cannot become table/typical guarantees')
    p = spec['population']
    counts = tuple(p[k] for k in ('precision_outputs', 'general_outputs', 'reference_connections', 'assumed_packages_per_reference'))
    if any(type(v) is not int for v in counts) or counts != (16, 66, 30, 1):
        raise ValueError('Full original population must remain explicit')
    sensitivity = spec['sensitivity']
    if set(sensitivity) != {'assumed_complete_release_s', 'diagnostic_rail_excursion_V', 'future_soft_start_ms'}:
        raise ValueError('Unclassified sensitivity')
    if not isinstance(sensitivity['assumed_complete_release_s'], list) or not sensitivity['assumed_complete_release_s']:
        raise ValueError('Nonempty release sensitivity required')
    for key, value in sensitivity.items():
        for item in value if isinstance(value, list) else [value]:
            positive(item, key)
    checked, missing, unavailable = [], [], []
    for source in json.loads(SOURCES.read_text())['sources']:
        if source['availability'] == 'SOURCE UNAVAILABLE':
            if source['sha256'] != ZERO or source['file'] is not None or source['bytes'] is not None:
                raise ValueError('Unavailable raw source cannot carry a fabricated artifact hash')
            unavailable.append(source['id'])
        elif source['availability'] == 'AVAILABLE':
            if source['sha256'] == ZERO or not source['file'] or not source['bytes']:
                raise ValueError('Available source requires exact artifact metadata')
            path = ROOT / source['file']
            if path.exists():
                if sha(path) != source['sha256'] or path.stat().st_size != source['bytes']:
                    raise ValueError('Retained source drift: ' + source['id'])
                checked.append(source['id'])
            else:
                missing.append(source['id'])
        else:
            raise ValueError('Unknown source availability')
    return {'verified_local_bytes': checked, 'absent_optional_cache': missing, 'source_unavailable': unavailable}


def dc_nodes(signal, drive_R, feedback_R, local_R, load_R, fb_bias_A=0):
    """Ideal-amplifier KCL with both remote and persistent local feedback.

    The bias term is drawn from FB. It is a static transfer shift; compute the
    load-dependent change separately against the same bias at open circuit.
    """
    for name, value in [('drive_R', drive_R), ('feedback_R', feedback_R), ('local_R', local_R)]:
        positive(value, name)
    if load_R is not None:
        positive(load_R, 'load_R')
    a = (1 + drive_R / feedback_R) / local_R + 1 / feedback_R
    loading = 0 if load_R is None else drive_R / (load_R * local_R)
    jack = (signal * a + fb_bias_A) / (a + loading)
    load_current = 0 if load_R is None else jack / load_R
    drive = jack + drive_R * (load_current + (jack - signal) / feedback_R)
    return {'jack_V': jack, 'drive_V': drive}


def calculate(spec):
    validate(spec)
    standard = json.loads(STANDARD.read_text())
    arch = json.loads(SUPPLY.read_text())
    audit = json.loads(AUDIT.read_text())
    previous = json.loads(PREVIOUS.read_text())
    resistors = json.loads(PREVIOUS_REPORT.read_text())['resistance_bounds']
    signal = standard['signals']
    if signal['bipolar_cv_nominal_V'] != [-5, 5] or signal['input_continuous_fault_V'] != [-12, 12] or signal['minimum_output_load_ohm'] != 10000 or signal['output_series_ohm'] != 998:
        raise ValueError('Original signal/load/fault scenario changed')
    if (audit['output_count'], audit['precision_count'], len(audit['reference_receivers'])) != (82, 16, 30):
        raise ValueError('Original channel obligations changed')
    c = arch['contract']; source = c['source_requirement']; env = c['load_envelope']
    rail = source['required_load_voltage_magnitude_V']; obs = spec['observed_datasheet_conditions']; d = spec['sensitivity']
    if d['future_soft_start_ms'] < source['soft_start_min_ms']:
        raise ValueError('Future startup duration cannot weaken the original minimum')
    # Deliberately not a +/-12 guarantee: these values are observed at other supplies.
    drive_R = resistors['drive_max_ohm'] + obs['Ron_max_ohm_at_13p5V_full_temp']
    feedback_R = resistors['sense_max_ohm'] + obs['feedback_Ron_max_ohm_at_13p5V_full_temp']
    local_R = 1e7 * resistors['minimum_factor']
    bias = previous['conditions']['amplifier_bias_A_full_temp_PW'] + 2 * obs['on_leakage_max_A_per_terminal_at_16p5V_125C']
    dc = []
    for vin in (-5, 0, 5):
        for current in (-bias, 0, bias):
            loaded = dc_nodes(vin, drive_R, feedback_R, local_R, 10000, current)
            open_nodes = dc_nodes(vin, drive_R, feedback_R, local_R, None, current)
            dc.append({'signal_V': vin, 'lumped_FB_bias_A_sensitivity': current, **loaded,
                       'unloaded_jack_V': open_nodes['jack_V'],
                       'load_dependent_change_V': loaded['jack_V'] - open_nodes['jack_V'],
                       'uncalibrated_static_shift_V': loaded['jack_V'] - vin})
    parts = {p['ref']: p for p in spec['parts']}
    bleed_min = parts['R_BLEED_P']['value'] * resistors['minimum_factor']
    logic_r_min = parts['R_IN']['value'] * resistors['minimum_factor']
    logic_r_max = parts['R_IN']['value'] * resistors['maximum_factor']
    def budget(count, start_ms):
        # Each prospective switch includes its own pair of100k rail bleeders.
        # Keep existing amplifiers,110 input ICs and ALL auxiliary allowances.
        per = {'+12V': obs['IDD_max_mA_at_16p5V_full_temp'] + rail['+12V'][1] / bleed_min * 1000,
               '-12V': obs['ISS_max_mA_at_16p5V_full_temp'] + rail['-12V'][1] / bleed_min * 1000,
               '+5V': 2 * rail['+5V'][1] / logic_r_min * 1000 + obs['input_max_A_at_0or5V_table_supplies'] * 1000}
        normal = {k: arch['selected_requirement']['normal_with_allowances_mA'][k] + count * per[k] for k in per}
        quantum = env['current_rounding_mA']
        continuous = {k: math.ceil(v * (1 + env['reserve_fraction']) / quantum) * quantum for k, v in normal.items()}
        ramp = {k: source['nominal_capacitance_ceiling_uF'][k] * (1 + source['capacitance_tolerance_fraction']) * rail[k][1] / start_ms for k in per}
        transient_raw = {k: continuous[k] + ramp[k] + env['fault_increment_mA'][k] for k in per}
        transient = {k: math.ceil(v / quantum) * quantum for k, v in transient_raw.items()}
        window = {k: source['maximum_delivered_current_mA'][k] - transient[k] for k in per}
        return {'switch_packages': count, 'soft_start_ms_sensitivity': start_ms,
                'conditional_added_mA_per_package': per, 'normal_with_all_existing_allowances_mA': normal,
                'prospective_continuous_mA': continuous, 'ramp_increment_mA': ramp,
                'unrounded_transient_mA': transient_raw, 'rounded_transient_mA': transient,
                'original_maximum_delivered_mA': source['maximum_delivered_current_mA'],
                'strict_limiter_window_mA': window, 'arithmetic_windows_positive': all(v > 0 for v in window.values()),
                'extra_nominal_bypass_uF_each_analog_rail': count * obs['required_bypass_F_each_rail'] * 1e6,
                'protection_path_mohm_at_prospective_continuous': {k: c['inlet']['harness']['max_protection_drop_V'] * 1e6 / continuous[k] for k in per},
                'budget_status': 'UNSOURCED: table currents at16.5V, not actual12V; input current at0/5V, not guaranteed5.2V; bypass leakage, permit-driver power and complete reference topology remain unbounded'}
    cold_drive = 12 / resistors['drive_min_ohm']; cold_sense = 12 / resistors['sense_min_ohm']
    available_C = source['nominal_capacitance_ceiling_uF']['+12V'] * 1e-6 * (1 - source['capacitance_tolerance_fraction'])
    collapse = []
    for drives, senses in [(16, 16), (82, 16)]:
        current = drives * cold_drive + senses * cold_sense
        collapse.append({'drive_count': drives, 'sense_count': senses, 'initial_injection_A': current,
            'zero_detector_complete_release_budget_s': available_C * d['diagnostic_rail_excursion_V'] / current,
            'rows': [{'assumed_COMPLETE_release_s': delay,
                      'required_reachable_C_F': current * delay / d['diagnostic_rail_excursion_V'],
                      'maximum_detector_delay_s': available_C * d['diagnostic_rail_excursion_V'] / current - delay}
                     for delay in d['assumed_complete_release_s']]})
    fault_I = (12 + max(rail['+12V'][1], rail['-12V'][1])) / resistors['drive_min_ohm']
    conditional_idle = (rail['+12V'][1] * obs['IDD_max_mA_at_16p5V_full_temp'] + rail['-12V'][1] * obs['ISS_max_mA_at_16p5V_full_temp']) / 1000
    report = {
        'status': 'UNSOURCED project performance; candidate topology only; implementation gate OPEN',
        'protection_implemented': False, 'model_run': 'NOT RUN: no identified model can supply missing manufacturer guarantees',
        'identity': spec['identity'], 'original_limits': previous['limits_preserved'],
        'source_retention': {'PDF_bytes': 'SOURCE UNAVAILABLE; zero-hash records', 'official_HTML_and_PNG': 'AVAILABLE; distinct actual hashes', 'performance_fact_verdict': 'UNSOURCED'},
        'operating_range_screen': {'verdict': 'UNSOURCED', 'evidence_scope': 'Operation described by official web observation; complete PDF retention pending',
            'project_positive_rail_V': rail['+12V'], 'project_negative_magnitude_V': rail['-12V'],
            'observed_dual_range_V': obs['operating_dual_magnitude_V'],
            'minimum_positive_signal_limit_V': rail['+12V'][0] - obs['signal_positive_headroom_V'],
            'plus8V_headroom_margin_V': rail['+12V'][0] - obs['signal_positive_headroom_V'] - 8,
            'precision_5V_headroom_margin_V': rail['+12V'][0] - obs['signal_positive_headroom_V'] - max(r['drive_V'] for r in dc),
            'project_rails_inside_pm15_table_range': all(15 * .9 <= v <= 15 * 1.1 for k in ('+12V', '-12V') for v in rail[k]),
            'interpretation': 'Operation/headroom is documented; single+12 table requiresVSS=GND and cannot certify bipolar operation.'},
        'precision_DC_sensitivity': {'verdict': 'UNSOURCED', 'effective_drive_R_ohm': drive_R, 'effective_feedback_R_ohm': feedback_R,
            'minimum_local_feedback_R_ohm': local_R, 'rows': dc,
            'maximum_load_dependent_change_V': max(abs(r['load_dependent_change_V']) for r in dc),
            'maximum_uncalibrated_static_shift_V': max(abs(r['uncalibrated_static_shift_V']) for r in dc),
            'approximate_S_to_SFB_drop_at_5V_10kohm_V': 5 / 10000 * resistors['drive_max_ohm'],
            'scope': 'Other-supply table maxima are conditional sensitivities. Two40nA channel leakage magnitudes conservatively lumped atFB plus15nA amplifier bias. Static offset is separate from load error; finite amplifier gain/offset, calibration, added capacitance and1ms settling remain unverified.'},
        'feedback_states': {'enabled': 'D-S andDFB-SFB closed; internalD-DFB open; remote feedback includes998ohm;10M/10nF local feedback remains.',
            'powered_disabled_or_fault': 'Observed internalD-DFB feedback closes automatically;10M/10nF remains. Exact closure skew and actual12V resistance are unknown.',
            'unpowered_or_partial': 'Do not assume the powered local-feedback switch still operates. Passive10M/10nF remains, but unpowered amplifier functionality is not inferred.',
            'POC': 'Pin7 deliberately floating; optional30k source-to-GND pull disabled. IN absent is described asOFF;100k adds a local default-low bias only while reference is valid.',
            'fault_detection': 'S/SFB compare with localrails, not external intended-signal limits. External+/-12V may be inside actualrails and need not trip. Keep series resistors and independent supervision.'},
        'static_fault_screen': {'verdict': 'UNSOURCED', 'both_external_polarities_V': [-12, 12],
            'main_opposing_voltage_current_A': fault_I, 'sense_opposing_voltage_current_A': (12 + 12.48) / resistors['sense_min_ohm'],
            'cold_main_initial_A': cold_drive, 'cold_sense_initial_A': cold_sense,
            'existing_fault_allocation_mA_not_toleranced_proof': env['fault_increment_mA']['+12V'],
            'conditional_switch_I2R_plus_idle_W': fault_I ** 2 * obs['Ron_max_ohm_at_13p5V_full_temp'] + conditional_idle,
            'conditional_JEDEC_rise_C': (fault_I ** 2 * obs['Ron_max_ohm_at_13p5V_full_temp'] + conditional_idle) * obs['theta_JA_test_board_C_per_W'],
            'scope': '30mA drain clamp and61mA main continuous rows are ratings under stated conditions, not tolerance/temperature proof at12V. External998ohm bounds initial paths; moving it inward invalidates the cold-injection bound. S-SFB optimal<1V recommendation can be exceeded during opposing faults.'},
        'power_off_and_ground': {'verdict': 'UNSOURCED', 'official_retained_broad_claim': 'Manufacturer wiki describes powered and unpowered S/SFB protection up to+/-60V.',
            'grounded_supply_drain_leakage_max_A_observed': obs['off_drain_leakage_max_A_grounded_supplies_125C'],
            'floating_supply_drain_leakage_TYPICAL_A_observed': obs['off_drain_leakage_typ_A_floating_supplies'],
            'source_leakage_TYPICAL_A_observed': obs['source_off_leakage_typ_A_at_pm60V'],
            'conditional_two_drain_bleeder_equilibrium_V': 2 * obs['off_drain_leakage_max_A_grounded_supplies_125C'] * 100000 * resistors['maximum_factor'],
            'documented_GND_premise': {'locator': 'ADG5401F Rev0 printedp28,physicalindex27,Power Off Protection', 'minimal_extract': 'A GND reference must always be present to ensure proper operation.'},
            'limitation': 'The IC alone cannot establish localGND-loss protection because the datasheet expressly requires that reference. All observed leakage rows keepGND=0. Source current intoGND/supply is only typical; floating-drain current is only typical. Two-drain bleeder arithmetic is NOT a complete nonbackpower bound. LocalGND-open shifts logic,thresholds and absolute terminal references; no survival/isolation guarantee inferred.'},
        'collapse_sensitivity': {'verdict': 'UNSOURCED', 'diagnostic_guard_V_not_original_limit': d['diagnostic_rail_excursion_V'],
            'optimistic_reachable_C_F_not_fitted_proof': available_C, 'cases': collapse,
            'timing_boundary': '220ns tOFF and1.2us negative tRESPONSE are conditioned observations at15V. tRESPONSE ends when drain falls to90% ofrail, not guaranteed full isolation. Listed COMPLETE release delays are hypothetical, not renamed datasheet guarantees.',
            'missing': 'Actual12V release/detector, source slew, amplifier rail-clamp injection, partial-rail transition,30 reference paths, other input backfeed and physically reachable capacitors remain open.'},
        'population_and_budget': {'precision_outputs': 16, 'general_outputs': 66, 'reference_connections': 30,
            'existing_110_input_ICs_unchanged': True, 'original_maximum_return_A': sum(source['maximum_delivered_current_mA'].values()) / 1000,
            'general_0to8V_outputs': [r['uid'] for r in audit['outputs'] if r['kind'] == 'general' and r['uid'].endswith('.ENV')],
            'general_connection': 'One package perdrive: tieS/SFB andD/DFB as recommended for single-channel use; retain amplifier local feedback and external998ohm. No general-output fault exemption.',
            'reference_connection': '30 one-package receiver-side placements are a budget sensitivity only. Source-facing orientation and protection of source/receiver during every partial connector state need a separate circuit.',
            'cases': [budget(n, start) for n in (16, 82, 112) for start in (source['soft_start_min_ms'], d['future_soft_start_ms'])],
            'scope': 'Every modeled package includes own rail bleeders,100k IN pull-down and100k FF pull-up. FF pull-up counted fully conducting as a conservative demand allowance, not claimed normal state. No LED current and no current credit for removal of installed parts.'},
        'logic_and_bypass': {'conditional_IN_resistor_drop_at_table_max_input_V': logic_r_max * obs['input_max_A_at_0or5V_table_supplies'],
            'maximum_FF_resistor_current_A_at_supply_ceiling': rail['+5V'][1] / logic_r_min,
            'minimum_rail_bypass_F_requested': obs['required_bypass_F_each_rail'],
            'scope': 'Exact bypass identity retained from existing project; effective capacitance/ESR/leakage unqualified. A100k FF pull-up does not reproduce the1k timing test; no flag-delay guarantee transferred. Input table at0/5V does not certify5.2V bias.'},
        'next_step': 'Retain fullPDF and obtain an actual12V guarantee or qualification plan, then characterize the captured remote/local feedback cell including disable/fault/collapse. Do not run a typical model as proof of missing maxima. Capture independently observable return/rail permit and complete reference boundary before replication.',
        'open_obligations': spec['open_obligations'],
    }
    json.dumps(report, allow_nan=False)
    return report


def run(check=False):
    spec = json.loads(SPEC.read_text()); cache = validate(spec); report = calculate(spec)
    report['input_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in (SPEC, SOURCES, PREVIOUS, PREVIOUS_REPORT, PREVIOUS_SOURCES, STANDARD, SUPPLY, AUDIT, Path(__file__).resolve())}
    body = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if check:
        if not REPORT.exists() or REPORT.read_text() != body:
            raise ValueError('Integrated candidate report drift')
    else:
        REPORT.write_text(body)
    print('PASS: conditioned arithmetic/identity; project guarantees and implementation remain OPEN')
    print(json.dumps(cache))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--check', action='store_true'); run(p.parse_args().check)
