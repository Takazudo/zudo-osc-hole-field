#!/usr/bin/env python3
"""S2b groundwork: jack-facing pin map for every input fault switch and the fault-row table.

Reads the instrument specification and the ADG5412F owner pin map. Manufacturer
rows are cited from the retained datasheets (ADG5412F Rev. C in circuit/sources,
TMUX7412F SCDS404B and TMUX6112 SCDS383F in .circuit-cache/sources/readiness-20261031/ds).
Adopted with S2b (E13, E15): this map reads the standard; it does not change the standard, the schematic or the inventory.
"""
import argparse
import collections
import hashlib
import functools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification  # noqa: E402

OUTPUT = ROOT / 'design/readiness/s2b-protection-map.json'
DS = ROOT / '.circuit-cache/sources/readiness-20261031/ds'
ADG_PDF = ROOT / 'circuit/sources/ic-library/ADG5412F.pdf'
# Channel 1 pins: ADG5412FBRUZ TSSOP-16 (owner pin map) and TMUX7412F (SCDS404B Table 6-1).
TMUX_WQFN = {'S1': '1', 'D1': '16', 'SEL1': '15', 'VSS': '2', 'GND': '3', 'VDD': '11', 'FF': '10'}
TMUX_TSSOP_PREVIEW = {'S1': '3', 'D1': '2', 'SEL1': '1', 'VSS': '4', 'GND': '5', 'VDD': '13', 'FF': '12'}

SOURCES = {
    'adg': ('ADG5412F/ADG5413F data sheet Rev. C', ADG_PDF, 'https://www.analog.com/media/en/technical-documentation/data-sheets/adg5412f_5413f.pdf'),
    'tmux7412f': ('TMUX741xF SCDS404B (November 2022)', DS / 'tmux7412f.pdf', 'https://www.ti.com/lit/ds/symlink/tmux7412f.pdf'),
    'tmux6112': ('TMUX611x SCDS383F (July 2025)', DS / 'tmux6112.pdf', 'https://www.ti.com/lit/ds/symlink/tmux6112.pdf'),
}

# Fault rows from the standard: input_continuous_fault_V +/-12 V, the G08 list
# (powered, unpowered, one rail missing, startup, both polarities, multiple patched
# inputs, ground present, rail lift and drain leakage) and the bare-clamp rejection.
FAULTS = [
    {'row': 'F1 powered, +/-12 V on the jack (input_continuous_fault_V)',
     'adg': ('PASS', 'Within VSS - VT .. VDD + VT the switch passes the signal (Rev. C index 25, page 26, Power-On Protection); downstream 10 k + BAT54S unchanged'),
     'tmux': ('PASS', 'Survival: overvoltage only beyond the supplies by VT (SCDS404B index 32, 9.3.2.4). Signal passing is a separate '
              'condition: VT is 0.7 V typical at 25 C only (7.5), RON rises exponentially within 3 V of VDD (9.3.4), and no RON '
              'maximum exists at +/-12 V (7.6 is +/-15 V +/-10 %, VS = -10..+10 V). Usable signal range: VSS .. VDD - 3 V, '
              'i.e. -12 .. +9 V at nominal rails. VDD - 3 V is guaranteed only with VSS = 0 V (7.8: RON <= 15 ohm at 85 C for '
              'VS = 0..7.8 V, VDD = 10.8..13.2 V); at +/-12 V dual supply it is an extrapolation; see usable_signal_range')},
    {'row': 'F2 powered, jack beyond a rail (rail sag or external source above +/-12 V)',
     'adg': ('PASS', 'Switch turns off; source to +/-55 V, 80 V across the channel (index 25, page 26)'),
     'tmux': ('PASS', 'Switch turns off regardless of logic; source to +/-60 V, 85 V source-to-supply and source-to-drain (index 31, 9.3.2.1; index 32, 9.3.2.4)')},
    {'row': 'F3 unpowered, rails at 0 V, GND present, +/-12 V on the jack',
     'adg': ('PASS', 'Switch off, inputs high impedance, +/-55 V blocked (index 25, Power-Off Protection). Source leakage +/-40 uA typical only; drain leakage +/-50 nA max at 85 C (Table 1, index 2)'),
     'tmux': ('PASS', 'Sources Hi-Z, +/-60 V blocked (index 32, 9.3.2.2). IS(FA) grounded +/-125 uA is TYPICAL only (7.6 TYP column; no maximum), '
              'so source-side fault leakage has no guaranteed bound, as for ADG5412F. ID(FA) grounded +/-50 nA is a maximum at 85 C (7.6, index 6)')},
    {'row': 'F4 unpowered, rails floating, GND present',
     'adg': ('PASS', 'Off whether supplies are 0 V or floating (index 25). Floating drain leakage +/-10 uA typical only'),
     'tmux': ('PASS', 'Hi-Z with VDD/VSS 0 V or floating (index 32). Floating-rail leakage recorded as typical only (protection59-sources.json)')},
    {'row': 'F5 GND absent (return open, board unplugged)',
     'adg': ('FAIL', 'Datasheet: a GND reference must always be present (index 25). Outside the protected envelope'),
     'tmux': ('FAIL', 'Same requirement (index 32, 9.3.2.2). No regression from ADG5412F')},
    {'row': 'F6 one analog rail missing, other present',
     'adg': ('PASS', 'Single-supply operation 8..44 V is specified; an input outside the remaining span is an overvoltage and turns the switch off. Conditional on VDD - VSS >= 8 V for the on state'),
     'tmux': ('UNKNOWN', '-12 V missing, +12 V present: PASS, VSS = 0 V is a specified single supply (VDD - VSS >= 8 V; 7.4, 9.1). '
              '+12 V missing, -12 V present: UNKNOWN, VDD = 0 V is below the recommended VDD minimum of 5 V (7.4) while the UVLO '
              'is defined on VDD - VSS = 12 V (7.5), so the device is not powered off by that definition and no datasheet text covers the state')},
    {'row': 'F7 +5 V enable present before the analog rails (startup, R-ADG)',
     'adg': ('PASS', 'Digital inputs tolerated without power; switch guaranteed off (index 25, Digital Input Protection); logic to 44 V'),
     'tmux': ('PASS', 'Fail-safe logic: logic before supplies, switch OFF, logic to +44 V (index 32, 9.3.2.3)')},
    {'row': 'F8 rail lift: a patched input must not energize an unpowered rail (bare-clamp rejection)',
     'adg': ('PASS', 'Source pins have specialized ESD with no diode path to the rails (index 24, ESD Performance)'),
     'tmux': ('PASS', 'Same statement: source ESD allows +/-60 V regardless of supply; powered-off protection prevents back-powering (index 32, 9.3.2.2 and 9.3.2.5)')},
    {'row': 'F9 several inputs patched at once in one quad (ADG-1/ADG-3 packing)',
     'adg': ('PASS', 'Rev. C index 24, page 25, Switch Architecture: "the channels undisturbed by the overvoltage input continue to operate normally without additional crosstalk"; 80 V channel stress (index 25). Project worst case 24 V. Qualitative manufacturer statement, no table limit'),
     'tmux': ('UNKNOWN', 'No published statement on undisturbed channels; only the 85 V source-to-drain stress rule (index 31) and -100 dB AC crosstalk. FF is shared across the four sources')},
    {'row': 'F10 drain leakage and RON on pitch-sensitive inputs',
     'adg': ('PASS', 'RON 14 ohm max, ID(on) +/-2.0 nA max at 85 C, +/-15 V table (Table 1); +/-12 V not guaranteed'),
     'tmux': ('PASS', 'Conditional: inside the usable signal range VSS .. VDD - 3 V (-12 .. +9 V at nominal rails) into the 100 k '
              'R_PD drain load. RON 14 ohm max and ID(ON) +/-2 nA max at 85 C exist in the +/-15 V +/-10 % table for VS = -10..+10 V '
              '(7.6); RON 15 ohm and RFLAT 0.5 ohm max at 85 C exist in the 12 V single-supply table for VS = 0..7.8 V (7.8, VSS = 0 V). '
              'Neither is a +/-12 V dual-supply guarantee. Above VDD - 3 V RON rises exponentially (9.3.4): UNKNOWN there')},
    {'row': 'F11 land and pin map (drop-in)',
     'adg': ('PASS', 'Current TSSOP-16 land'),
     'tmux': ('FAIL', 'Orderable only as WQFN-16 RRP (addendum index 40); the TSSOP-16 PW package with the ADG pin order is marked Preview. New land and pin map: S1 = pad 1, D1 = pad 16, SEL1 = pad 15')},
]

# TMUX7412F at +/-12 V: flat-RON region VSS .. VDD - 3 V (SCDS404B 9.3.4). Guaranteed only with VSS = 0 V
# (7.8: VS 0..7.8 V at VDD >= 10.8 V); at +/-12 V dual supply it is an extrapolation.
# Role ranges are the standard's signal classes.
STANDARD = ROOT / 'design/standard/electrical-standard.json'
SUPPLY_INPUT = ROOT / 'design/power/supply-architecture-input.json'
FLAT_HEADROOM_V = 3.0  # VDD - 3 V: SCDS404B 9.3.4 text; 7.8 tabulates it as VS <= 7.8 V at VDD = 10.8 V
USABLE_RANGE = {
    'range_V': [-12, 9], 'basis': 'VSS .. VDD - 3 V at nominal +/-12 V rails (9.3.4). Guaranteed only with VSS = 0 V: 7.8 gives RON '
    '<= 15 ohm (-40..85 C) for VS = 0..7.8 V at VDD = 10.8..13.2 V. At +/-12 V dual supply the limit is an extrapolation, not a table '
    'condition. The fault detector opens the switch beyond VDD + VT / VSS - VT, VT 0.7 V typical at 25 C only (7.5)',
    'roles': [
        {'role': 'audio inputs (filter IN, mix4 1-4, mix5 1-5, wavefolder IN, manual_ab A/B, mult IN, sample_hold IN, offset IN)',
         'inputs_per_unit': 3 + 8 + 10 + 2 + 4 + 2 + 2 + 6, 'normal_swing_V': [-5, 5], 'class': 'audio_nominal_V / mult nominal linear range',
         'verdict': 'PASS', 'margin_V': 4},
        {'role': 'bipolar CV inputs (envelope RISE/FALL, filter FREQ/RES/GAIN, mix4 ATTEN, offset OFFSET, oscillator FM/PWM, wavefolder FOLD/BIAS)',
         'inputs_per_unit': 12 + 9 + 2 + 6 + 10 + 4, 'normal_swing_V': [-5, 5], 'class': 'bipolar_cv_nominal_V',
         'verdict': 'PASS', 'margin_V': 4},
        {'role': 'gate and trigger inputs (envelope SIG, oscillator SYNC, sample_hold TRIGGER)',
         'inputs_per_unit': 6 + 5 + 2, 'normal_swing_V': [0, 5], 'class': 'gate_output_nominal_V (project gate level)',
         'verdict': 'PASS', 'margin_V': 4,
         'note': 'External gates above +9 V (common 0..10 V sources) enter the rising-RON region; into the high-impedance comparator path this is UNKNOWN, not FAIL'},
    ],
}


def pitch_role():
    """1V/OCT verdict against the standard's declared linear range and the required +12 V load-voltage minimum."""
    signals = json.loads(STANDARD.read_text())['signals']
    declared = signals.get('pitch_linear_range_V')
    row = {'role': 'pitch input (oscillator 1V/OCT)', 'inputs_per_unit': 5}
    if declared is None:
        return {**row, 'normal_swing_V': None, 'class': 'pitch_V_per_octave (no range in the standard)', 'verdict': 'FLAG', 'margin_V': None,
                'note': 'The standard defines 1 V/oct but no input range; a declared pitch linear range is needed'}
    low = json.loads(SUPPLY_INPUT.read_text())['source_requirement']['required_load_voltage_magnitude_V']['+12V'][0]
    nominal_top = signals['rails_V']['+12V'] - FLAT_HEADROOM_V
    low_top = round(low - FLAT_HEADROOM_V, 2)
    bottom_ok = declared[0] >= signals['rails_V']['-12V']
    margin = round(low_top - declared[1], 2)
    verdict = 'PASS' if bottom_ok and margin >= 0 else 'FAIL'
    return {**row, 'normal_swing_V': declared, 'class': 'pitch_linear_range_V (' + signals.get('pitch_linear_range_status', '') + ')',
            'verdict': verdict, 'margin_V': margin,
            'basis': {'nominal_flat_top_V': nominal_top, 'required_low_V': low, 'low_band_flat_top_V': low_top,
                      'rail_band_source': str(SUPPLY_INPUT.relative_to(ROOT)) + ' source_requirement.required_load_voltage_magnitude_V +12V (requirement contract; source NOT SELECTED)'},
            'note': ('Verdict covers signal passing only. The top of the declared range is compared with VDD - 3 V at the required +12V minimum; that limit '
                     'is guaranteed only at VSS = 0 V (7.8) and extrapolated at +/-12 V. The bottom lies in the flat region down to VSS. Downstream: '
                     'OPA4197 VCM (V-) - 0.1 .. (V+) + 0.1 V is guaranteed; its input-stage transition (V+) - 3 .. (V+) - 1.5 V has no CMRR limit, and the '
                     'declared top stays below it at that minimum. Accuracy is a separate gate: calibration scope stays 0..5 V at 25 C; the '
                     'clamp-leakage term is in precision_input_clamp (BAV199,215 precision variant on these inputs)')}

TMUX6112_ROWS = [
    ('Pin map', 'PASS', 'TSSOP-16 order matches the ADG5412F land: SEL1 1, D1 2, S1 3, VSS 4, GND 5 ... pin 12 is NC where ADG has FF, which the project leaves unconnected (SCDS383F Table 5-1, index 3)'),
    ('Logic sense', 'PASS', 'Logic 1 turns the switches on, as ADG5412F (Description, index 0)'),
    ('Supply', 'PASS', '+/-5 .. +/-17 V dual (Features, index 0)'),
    ('Signal range', 'PASS', 'VA = VSS .. VDD; envelope nodes REF9/REF8/AGND are inside the rails when powered'),
    ('RON', 'PASS', '210 ohm max at VS = +/-10 V, 85 C (6.5, index 5) in series with the 899 k drive divider and the hold clamp'),
    ('Hold-node leakage', 'PASS', 'IS(OFF)/ID(OFF) -0.14 .. +0.05 nA at 85 C, ID(ON) -0.25 .. +0.1 nA (6.5, index 5); +/-15 V table, not a +/-12 V guarantee'),
    ('Fault protection', 'NOT APPLICABLE', 'Not fault protected; analog pins VSS - 0.3 .. VDD + 0.3 V (6.1, index 4). The envelope switches are internal, not jack facing'),
    ('Logic before rails', 'PASS', 'SELx absolute maximum is VDD + 0.3 V (6.1, index 4). Candidate SEL hold: 100 k pull-up to +5 V, BAT54S clamp '
     'to +12V and a BAT54S pull-down to the logic output; SEL <= VDD + 0.24 V at 25 C (VF max at 0.1 mA). Below 25 C the VF margin is UNKNOWN (no curve)'),
    ('Logic before rails, PD definition 1', 'PASS',
     'Merged canonical row (f8e048f3) restated for the SEL hold. Definition 1 lets +5 V reach 0.8 V while VDD < 0.5 V; with the direct HC drive that '
     'exceeded VDD + 0.3 V. With the hold the driver only pulls SEL down through the BAT54S pull-down and the 100 k pull-up is clamped to +12V, so '
     'SEL <= VDD + 0.24 V at 25 C (VF max at 0.1 mA, hold current <= 54.5 uA) whatever the +5 V ramp; below 25 C UNKNOWN (no VF curve)'),
    ('SEL series resistor (current row only)', 'PASS',
     'Merged canonical row (f8e048f3): IDIG <= 30 mA (6.1, index 4). The SEL hold limits SEL current to the 100 k pull-up, <= 5.5 V / 100 k = 55 uA '
     '(5.5 V is a PROPOSED +5 V ceiling, not a sourced PD value), so the proposed separate 1 kOhm series resistor is not fitted'),
]


# Phase 24: leakage of the high_impedance_input clamp at SENSE, before (BAT54S,215) and after
# (BAV199,215, precision variant). BAT54S: project digitisation of the typical Fig. 2 curves at
# 25 C and 85 C (fact-clamp-diode-reverse-current-temperature), log-interpolated in temperature.
BAT54S_VR_V = [1, 5, 10, 15, 20, 25, 30]
BAT54S_TYP_UA = {25: [0.25, 0.48, 0.71, 1.02, 1.32, 1.59, 1.91], 85: [19.2, 27.5, 36.5, 43, 49.8, 57, 65]}
# BAV199 v.3 Fig. 4 curve (1) maximum values at VR = 75 V (project readings; Table 7 gives the 25 C
# and 150 C endpoints) and curve (2) typical values; fact-clamp-diode-ll-reverse-current-temperature.
BAV199_MAX_NA = {25: 5.0, 40: 6.6, 70: 13.0}
BAV199_TYP_NA = {25: 0.003, 40: 0.0066, 70: 0.035}
TMUX_RON_OHM = 14  # SCDS404B 7.6 RON maximum, +/-15 V table, -40..85 C (fact-fault-switch-t-ron-85c)
CENTS_PER_V = 1200
TEMPS = {'0-40 C': (0, 40), '0-70 C': (0, 70)}


def _interp_log(xs, ys, x):
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            f = (x - xs[i]) / (xs[i + 1] - xs[i])
            return math.exp(math.log(ys[i]) * (1 - f) + math.log(ys[i + 1]) * f)
    raise ValueError(x)


def bat54s_typ_ua(vr, temp):
    a, b = (math.log(_interp_log(BAT54S_VR_V, BAT54S_TYP_UA[t], vr)) for t in (25, 85))
    return math.exp(a + (b - a) * (temp - 25) / 60)


@functools.lru_cache(maxsize=None)
def spec():
    return specification()


def clamp_placements(role='high_impedance_input:D'):
    families, instances = spec()
    copies = collections.Counter(i.family for i in instances)
    out = collections.Counter()
    for family in families:
        for part in family.parts:
            if part.attributes.get('Role') == role and part.unit == 1:
                out[(family.name, part.key.rsplit('.', 1)[0], part.attributes.get('MPN'))] += copies[family.name]
    return out


# Phase 25: D_BOOT (BAT54S,215, pins 1+2 SENSE, pin 3 BUFFERED) across the unity follower. Its
# diode voltage is held at the follower offset, so its current is 2 Is sinh(VOS / Vt), fixed by
# VOS and independent of the rail clamp leakage, which still flows through r_eff unchanged.
# VOS maxima: OPA4197 SBOS737C 6.7 (index 6) 100 uV at 25 C, drift 4.5 uV/C max (VCM = (V+) - 1.5 V
# row, -40..125 C); OPA4196 SBOS869 6.7 (index 6) 100 uV at 25 C, drift 0.8 uV/C typical only.
# Both are VS = +/-18 V rows. Is is taken as the BAT54S typical IR at VR = 1 V (an upper estimate);
# the only maximum is 2 uA at VR = 25 V and 25 C (Table 7).
FOLLOWER = {'OPA4197': (100.0, 4.5, 'maximum'), 'OPA4196': (100.0, 0.8, 'typical only')}
BAT54S_IR_MAX_25C_UA = 2.0
BOOT_VF_MAX_V = 0.24        # BAT54S Table 7: VF <= 240 mV at IF = 0.1 mA, 25 C
FOLLOWER_ZO_OHM = 375       # OPA4197 6.7 ZO typical, f = 1 MHz, IO = 0 (no maximum)
TMUX_DRAIN_ABS_V = 0.7      # SCDS404B 7.1: Dx <= VDD + 0.7 V


def thermal_v(temp):
    return 8.617333e-5 * (temp + 273.15)


def boot_error_v(is_ua, vos_uv, temp, r_eff):
    return r_eff * 2 * is_ua * 1e-6 * math.sinh(vos_uv * 1e-6 / thermal_v(temp))


def precision_clamp():
    standard = json.loads(STANDARD.read_text())
    cell = next(c for c in standard['cells'] if c['id'] == 'high_impedance_input')
    values = {p['ref']: p.get('value') for p in cell['parts']}
    signals = standard['signals']
    source = signals['output_series_ohm'] + TMUX_RON_OHM
    r_eff = values['R_LIMIT'] + values['R_PD'] * source / (values['R_PD'] + source)
    rail = signals['rails_V']['+12V']
    # Part-key suffixes of the D clamp in each precision input (cell namespace + instance tag),
    # and the follower op-amp role chosen by each module (oscillator/mult precision, S&H cv).
    roles = [('pitch (oscillator 1V/OCT)', 'oscillator', '_1V_1V__D', signals['pitch_linear_range_V'], 'pitch_linear_range_V', 'OPA4197'),
             ('MULT IN', 'mult', '_IN_IN__D', signals['bipolar_cv_nominal_V'], 'bipolar_cv_nominal_V', 'OPA4197'),
             ('S&H IN', 'sample_hold', '_H1_IN___D', signals['bipolar_cv_nominal_V'], 'bipolar_cv_nominal_V', 'OPA4196')]
    placed = clamp_placements()
    boots = clamp_placements('high_impedance_input:D_BOOT')

    def error_v(v, temp):  # upper diode leaks into SENSE at VR = rail - V, lower diode out at rail + V
        return -(bat54s_typ_ua(rail + v, temp) - bat54s_typ_ua(rail - v, temp)) * 1e-6 * r_eff

    rows = []
    for name, family, tag, span, span_key, amp in roles:
        hits = {(k, m): n for (f, k, m), n in placed.items() if f == family and k.endswith(tag)}
        boot_hits = {(k, m): n for (f, k, m), n in boots.items() if f == family and k.endswith(tag + '_BOOT')}
        vos25, drift, drift_kind = FOLLOWER[amp]
        grid = [span[0] + 0.5 * i for i in range(int((span[1] - span[0]) / 0.5) + 1)]
        row = {'role': name, 'range_V': span, 'range_source': 'signals.' + span_key, 'follower': amp,
               'placements': [{'stem': k, 'mpn': m, 'per_unit': n} for (k, m), n in sorted(hits.items())],
               'bootstrap_placements': [{'stem': k, 'mpn': m, 'per_unit': n} for (k, m), n in sorted(boot_hits.items())]}
        boot25_max = boot_error_v(BAT54S_IR_MAX_25C_UA, vos25, 25, r_eff)
        row['bootstrap_25C'] = {'offset_bound_mV': round(boot25_max * 1e3, 4), 'offset_bound_cents': round(boot25_max * CENTS_PER_V, 3),
                                'basis': 'Is <= 2 uA (BAT54S IR maximum at 25 V, 25 C), |VOS| <= 100 uV; a fixed offset removed by the 25 C trim'}
        for label, (lo, hi) in TEMPS.items():
            before = max(abs(error_v(v, t) - error_v(v, 25)) for v in grid for t in range(lo, hi + 1))
            bound = (BAV199_MAX_NA[hi] + BAV199_MAX_NA[25]) * 1e-9 * r_eff
            typical = (BAV199_TYP_NA[hi] + BAV199_TYP_NA[25]) * 1e-9 * r_eff
            # Bootstrap drift, typical Is with the VOS maximum plus drift (worst sign: the 25 C
            # offset trimmed, the hot or cold offset grown by the full drift).
            boot = max(abs(boot_error_v(bat54s_typ_ua(1, t), vos25 + drift * abs(t - 25), t, r_eff) - boot_error_v(bat54s_typ_ua(1, 25), vos25, 25, r_eff))
                       for t in range(lo, hi + 1))
            row[label] = {'before_bat54s_typical_drift_mV': round(before * 1e3, 3), 'before_bat54s_typical_drift_cents': round(before * CENTS_PER_V, 2),
                          'before_bat54s_guaranteed': 'UNKNOWN (BAT54S IR maximum only at 25 C)',
                          'after_bav199_bound_mV': round(bound * 1e3, 4), 'after_bav199_bound_cents': round(bound * CENTS_PER_V, 3),
                          'after_bav199_typical_mV': round(typical * 1e3, 5),
                          'bootstrap_typical_drift_mV': round(boot * 1e3, 4), 'bootstrap_typical_drift_cents': round(boot * CENTS_PER_V, 3),
                          'bootstrap_guaranteed': 'UNKNOWN (no BAT54S IR maximum above 25 C; VOS drift ' + drift_kind + ')',
                          'total_after_cents': round((bound + boot) * CENTS_PER_V, 3)}
        rows.append(row)
    over = TMUX_DRAIN_ABS_V
    current_ua = over / values['R_LIMIT'] * 1e6
    sense_over = BOOT_VF_MAX_V + current_ua * 1e-6 * FOLLOWER_ZO_OHM
    return {
        'status': 'Adopted S2b (E15; phase 24 BAV199 rail clamp; phase 25 bootstrap clamp D_BOOT): precision variant of high_impedance_input',
        'model': {'r_eff_ohm': round(r_eff, 1), 'r_eff_basis': 'R_LIMIT + R_PD || (signals.output_series_ohm + TMUX7412F RON 14 ohm)',
                  'drift_definition': 'max over the role range (0.5 V steps) and the temperature span of |e(V,T) - e(V,25 C)|; cents at 1 V/oct (1 mV = 1.2 c)',
                  'before': 'BAT54S,215 typical Fig. 2 curves (project digitisation), log-interpolated in temperature and extrapolated below 25 C; no guaranteed bound exists',
                  'after_bound': '(IR max at the top temperature + IR max at 25 C) x r_eff; BAV199 Fig. 4 curve (1) at VR = 75 V, assuming IR does not rise at lower VR or below 25 C; source is the JLCPCB-hosted mirror (UNSOURCED until a manufacturer-hosted copy is compared)',
                  'after_typical': 'Fig. 4 curve (2) typical values',
                  'bootstrap': 'D_BOOT error r_eff x 2 Is sinh(VOS / Vt); its diode voltage is set by the follower, so it adds to and does not divert the BAV199 leakage term, which is unchanged. '
                               'Typical drift uses Is = BAT54S typical IR at 1 V (an upper estimate) and |VOS| = 100 uV + drift x |T - 25 C|'},
        'roles': rows,
        'placements_per_unit': {m: sum(n for (_, _, mm), n in placed.items() if mm == m) for m in sorted({m for (_, _, m) in placed})},
        'bootstrap_per_unit': sum(boots.values()),
        'opa4197_input_absolute_maximum': {
            'rows': 'SBOS737C 6.1 (index 4): signal input pins, common-mode (V-) - 0.5 .. (V+) + 0.5 V; current +/-10 mA. Footnote (1) is the general stress note; '
                    'no footnote lets the voltage row be exceeded when the current is limited. 7.3.7 (index 24-25): the ESD steering diodes are intended to remain '
                    'inactive in normal operation; current-limiting resistors and TVS are named only for EOS events. OPA4196 (S&H IN) has the same rows in SBOS869 6.1',
            'reading': 'Both rows apply. The VDD .. VDD + VT window is therefore not PASS on the current row alone',
            'declared_contract': 'With input_continuous_fault_V +/-12 V and the required load-rail minima (+12V 11.53 V, -12V 11.74 V) the jack exceeds the local rail by '
                                 'at most 0.47 V / 0.26 V: PASS against (V+) + 0.5 V with 0.03 V margin, independent of the clamp diode',
            'beyond_contract_without_bootstrap': 'A source at the supply maximum (+12V 12.3 V at source) against a load rail at 11.53 V gives 0.77 V. Then SENSE - V+ <= min(VT, VF): '
                                                 'BAT54S rail clamp VF <= 0.24 V at 0.1 mA, 25 C only; BAV199 VF has no maximum below 1 mA (UNKNOWN)',
            'beyond_contract_with_bootstrap': {
                'bound': f'SENSE - V+ <= VF(D_BOOT) + I x ZO <= {BOOT_VF_MAX_V} + {round(current_ua * 1e-6 * FOLLOWER_ZO_OHM, 3)} = {round(sense_over, 3)} V',
                'basis': f'The follower output limits at the rail (no phase reversal: OPA4197 SBOS737C 7.3.3 index 21, OPA4196 SBOS869 7.3.3 index 20). '
                         f'With the TMUX7412F drain inside its own absolute maximum (Dx <= VDD + {TMUX_DRAIN_ABS_V} V, SCDS404B 7.1; beyond it the switch row fails first), I <= {round(current_ua)} uA through R_LIMIT and '
                         f'BAT54S VF <= {BOOT_VF_MAX_V} V (0.1 mA row, 25 C). ZO {FOLLOWER_ZO_OHM} ohm is the typical open-loop output impedance at 1 MHz (no maximum)',
                'margin_V': round(0.5 - sense_over, 3),
                'verdict': 'PASS at 25 C (margin ' + str(round(0.5 - sense_over, 2)) + ' V); below 25 C the BAT54S VF has no curve or maximum, so it is PASS only if VF rises by less than the margin (a Schottky tempco of about -1 to -2 mV/K, a general figure and not a BAT54S datasheet value, would add about 0.05 V at 0 C): UNKNOWN as a guarantee',
                'negative_side': 'Symmetric: SENSE >= V- - ' + str(round(sense_over, 3)) + ' V'},
            'current_row': f'PASS: <= {round(current_ua)} uA, far below 10 mA; the follower output sinks or sources the same current',
            'verdict_bav199_without_bootstrap': 'PASS within the declared contract; beyond it UNKNOWN',
            'verdict_with_bootstrap': 'PASS within the declared contract; beyond it PASS at 25 C, UNKNOWN below 25 C (typical PASS)',
            'not_covered': 'Rail-missing and unpowered rows: with the follower unpowered D_BOOT clamps SENSE to the output pin, whose ESD diodes go to the dead rail; the BAV199 rail clamp is unchanged. Follower slewing: D_BOOT conducts while |SENSE - OUT| exceeds about 0.2 V during fast edges (transient only). NOT RUN'}}


def source_receipts():
    out = {}
    for key, (title, path, url) in SOURCES.items():
        out[key] = {'title': title, 'url': url, 'path': str(path.relative_to(ROOT)),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else 'NOT RETAINED',
                    'authority_class': 'MANUFACTURER_PRIMARY'}
    return out


def placements():
    pinmap = json.loads((ROOT / '.claude/skills/component-adi-adg5412fbruz/pin-map.json').read_text())['pin_maps'][0]['pins']
    names = {p['symbol_pin']: p['name'] for p in pinmap}
    families, instances = spec()
    copies = collections.Counter(i.family for i in instances)
    rows, errors = [], []
    for family in families:
        tips = {net for part in family.parts if part.prefix == 'J' for pin, net in part.pins.items() if pin == 'T' and net}
        for part in family.parts:
            if part.attributes.get('Role') != 'input_fault_switch:U' or part.unit != 1:
                continue
            # S2b candidate: TMUX7412FRRPR S1 pad 1, D1 pad 16 (SCDS404B Table 6-1); ADG5412FBRUZ S1 3, D1 2.
            tmux = part.symbol.endswith('TMUX7412FRRPR')
            source, drain = part.pins.get('1' if tmux else '3'), part.pins.get('16' if tmux else '2')
            jack_on_source = source in tips
            if not jack_on_source or drain in tips:
                errors.append(f'{family.name} {part.key}: jack not on S1')
            rows.append({'family': family.name, 'instances': copies[family.name], 'stem': part.key.rsplit('.', 1)[0],
                         'adg_source_pin': f"3 ({names['3']})", 'adg_drain_pin': f"2 ({names['2']})",
                         'jack_net': source, 'local_net': drain, 'jack_faces': 'SOURCE' if jack_on_source else 'DRAIN',
                         'tmux7412f_wqfn': {'jack': f"S1 pad {TMUX_WQFN['S1']}", 'local': f"D1 pad {TMUX_WQFN['D1']}",
                                            'enable': f"SEL1 pad {TMUX_WQFN['SEL1']}"},
                         'tmux_protected_side_faces_jack': jack_on_source})
    return rows, errors


def build():
    rows, errors = placements()
    total = sum(r['instances'] for r in rows)
    return {'schema_version': 1, 'status': 'Adopted S2b (decisions E13, E15); fault rows revised after the independent review',
            'sources': source_receipts(),
            'input_placements_per_unit': total, 'placement_groups': len(rows),
            'jack_on_protected_source_per_unit': sum(r['instances'] for r in rows if r['jack_faces'] == 'SOURCE'),
            'errors': errors, 'placements': rows,
            'fault_rows': [{'row': f['row'], 'adg5412f': {'verdict': f['adg'][0], 'basis': f['adg'][1]},
                            'tmux7412f': {'verdict': f['tmux'][0], 'basis': f['tmux'][1]},
                            'changes_with_tmux7412f': f['adg'][0] != f['tmux'][0]} for f in FAULTS],
            'fault_row_summary': {name: dict(collections.Counter(f[key][0] for f in FAULTS))
                                  for name, key in (('adg5412f', 'adg'), ('tmux7412f', 'tmux'))},
            'usable_signal_range': {**USABLE_RANGE, 'roles': USABLE_RANGE['roles'] + [pitch_role()]},
            'envelope_internal_tmux6112': [{'row': a, 'verdict': b, 'basis': c} for a, b, c in TMUX6112_ROWS],
            'precision_input_clamp': precision_clamp()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    missing = [k for k, (_, p, _) in SOURCES.items() if not p.exists()]
    if missing:
        print(f'NOT RUN: retained datasheets absent: {missing}')
        return 4
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            print(f'FAIL: {OUTPUT.relative_to(ROOT)} is stale; run without --check')
            return 1
        print('PASS: S2b protection map matches the specification and retained datasheets')
        return 0
    OUTPUT.write_text(text)
    print(f'wrote {OUTPUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
