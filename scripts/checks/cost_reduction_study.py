#!/usr/bin/env python3
"""Phase-14 cost-reduction study: priced, UNADOPTED alternatives for the top BOM lines.

Inputs: the instrument specification, design/readiness/bom-cost-evidence.json and
retained read-only catalog bytes in .circuit-cache/sources/readiness-20261031/
(jlc/<keyword>.json search responses and ds/<part>.pdf manufacturer datasheets,
all retrieved 2026-10-31; git-ignored).

Every alternative is a PROPOSAL. Nothing here changes the standard, the inventory,
the schematic, the PCB or an order file. Distributor rows give price tier and stock
only; electrical rows come from the cited manufacturer datasheet sections.
"""
import argparse
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification  # noqa: E402
from scripts.checks.passive_candidates import CACHE, LOT, RETRIEVED, jlc_row, tier_price  # noqa: E402

OUTPUT = ROOT / 'design/readiness/cost-reduction-study.json'
COST = ROOT / 'design/readiness/bom-cost-evidence.json'
# Ledger planning unit per ADG5412F quad (fact-fault-switch-normal-idd, +-15 V table),
# as used by the P59-B worksheets in design/power/proposals-59/README.md.
ADG_IDD_MA = {'+12V': 1.3, '-12V': 0.7}
# Normal-load headroom before the next PD continuous step at HEAD (phase 11 ledger).
HEADROOM_MA = {'+12V': 10.6, '-12V': 19.0}

# Manufacturer datasheet rows read from ds/<file>.pdf (section and printed page).
DATASHEETS = {
    'OPA4196IDR': ('opa4196.pdf', 'TI SBOS869 electrical characteristics, VS = +/-18 V; IQ is the '
                   'design/standard/source-receipts.json maximum over temperature',
                   {'iq_max_mA': 0.25, 'vos_max_uV_25C': 100, 'package': 'SOIC-14'}),
    'OPA4197IPWR': ('opa4197.pdf', 'TI SBOS737C Section 6.7 (VOS row printed page 7; IQ row printed page 8)',
                    {'iq_max_mA': 1.5, 'vos_max_uV_25C': 100, 'ib_max_full_temp_nA': 15, 'gbw_MHz': 10,
                     'package': 'TSSOP-14'}),
    'OPA4197IDR': ('opa4197.pdf', 'TI SBOS737C Section 6.7; the 15 nA full-temperature IB subrow is PW only, '
                   'the device row is +/-5 nA', {'iq_max_mA': 1.5, 'vos_max_uV_25C': 100,
                                                'ib_max_full_temp_nA': 5, 'gbw_MHz': 10, 'package': 'SOIC-14'}),
    'OPA4192IDR': ('opa4192.pdf', 'TI SBOS620E Section 6.x electrical characteristics, VS = +/-18 V',
                   {'iq_max_mA': 1.5, 'vos_max_uV_25C': 25, 'vos_max_uV_full_temp': 75, 'gbw_MHz': 10,
                    'package': 'SOIC-14'}),
    'OPA4991IPWR': ('opa4991.pdf', 'TI SBOS969F Section 6.7', {'iq_max_mA': 0.75, 'vos_max_uV_25C': 830,
                                                             'vos_max_uV_full_temp': 850, 'gbw_MHz': 4.5,
                                                             'package': 'TSSOP-14'}),
    'OPA4171AIPWR': ('opa4171.pdf', 'TI SBOS516H Section 5.7, printed page 8', {
        'iq_max_mA': 0.65, 'vos_max_uV_25C': 1800, 'vos_max_uV_full_temp': 2000, 'gbw_MHz': 3,
        'vcm_upper': '(V+) - 2 V', 'package': 'TSSOP-14'}),
    'OPA4171AIDR': ('opa4171.pdf', 'TI SBOS516H Section 5.7, printed page 8', {
        'iq_max_mA': 0.65, 'vos_max_uV_25C': 1800, 'vos_max_uV_full_temp': 2000, 'gbw_MHz': 3,
        'vcm_upper': '(V+) - 2 V', 'package': 'SOIC-14'}),
    'TL074HIDR': ('tl074h.pdf', 'TI SLOS080W Section 5.7, printed page 13', {
        'iq_max_mA': 1.13, 'vos_max_uV_25C': 4000, 'vos_max_uV_full_temp': 5000, 'package': 'SOIC-14'}),
    'LM324DR': ('lm324.pdf', 'TI SLOS066AE Section 6.7 (LM324 columns): VIO, VICR, ICC four amplifiers', {
        'iq_max_mA': 0.75, 'vos_max_uV_25C': 7000, 'vos_max_uV_full_temp': 9000,
        'vcm_upper': 'VCC - 2 V full range', 'package': 'SOIC-14'}),
    'TMUX7412FRRPR': ('tmux7412f.pdf', 'TI SCDS404B (also design/power/protection59-sources.json)', {
        'package': 'WQFN-16 4x4', 'idd_max_mA': 0.6, 'iss_max_mA': 0.5, 'ron_max_ohm': 16.5,
        'drain_overvoltage_protected': False, 'powered_off_protection_needs_gnd': True,
        'floating_rail_leakage': 'typical only'}),
}


def _lcsc_by_mpn():
    lines = json.loads(COST.read_text())['exact_lines']
    return {x['mpn']: x['jlc']['lcsc'] for x in lines if x.get('jlc')}


def price(mpn, qty):
    # Phase-13 baseline lines were retrieved by their LCSC code, not by MPN.
    row, receipt = jlc_row(mpn)
    if not row and mpn in LCSC_BY_MPN:
        row, receipt = jlc_row(LCSC_BY_MPN[mpn])
    if not row or not row['tiers']:
        return {'mpn': mpn, 'status': 'UNKNOWN: no exact JLC row', 'receipt': receipt}
    unit, lot = tier_price(row['tiers'], qty), tier_price(row['tiers'], qty * LOT)
    return {'mpn': mpn, 'lcsc': row['lcsc'],
            'stock': row['stock'], 'stock_covers_lot': row['stock'] >= qty * LOT, 'qty_per_unit': qty,
            'unit_price_usd': unit, 'lot_unit_price_usd': lot, 'per_unit_usd': round(qty * unit, 2),
            'per_lot_usd': round(qty * LOT * lot, 2), 'receipt': receipt}


LCSC_BY_MPN = _lcsc_by_mpn()


def datasheet(mpn):
    if mpn not in DATASHEETS:
        return None
    name, locator, rows = DATASHEETS[mpn]
    path = CACHE / 'ds' / name
    return {'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else 'NOT RETAINED',
            'locator': locator, 'rows': rows}


def inventory():
    families, instances = specification()
    copies = collections.Counter(i.family for i in instances)
    adg_inputs = collections.Counter()
    adg_internal = collections.Counter()
    opamps = collections.Counter()
    for family in families:
        seen = set()
        for part in family.parts:
            stem = part.key.rsplit('.', 1)[0]
            mpn = part.attributes.get('MPN')
            if part.prefix != 'U' or stem in seen or part.abstract or part.dnp or not part.in_bom:
                continue
            seen.add(stem)
            if mpn == 'ADG5412FBRUZ':
                if part.attributes.get('Role') == 'input_fault_switch:U':
                    group = stem.split('input_fault_switch')[0].rstrip('_') or 'MAIN'
                    adg_inputs[(family.name, group)] += 1
                else:
                    adg_internal[(family.name, part.attributes.get('Role'))] += 1
            elif mpn in ('OPA4196IDR', 'OPA4197IPWR'):
                indicator = any(t in stem for t in ('LED_PACK', 'IND_PACK', 'magnitude_indicator'))
                opamps[(mpn, 'indicator' if indicator and mpn == 'OPA4196IDR' else
                        'audio/cv' if mpn == 'OPA4196IDR' else 'precision')] += copies[family.name]
    return copies, adg_inputs, adg_internal, opamps


def iq_delta(packages, base_mpn, alt_mpn):
    base = DATASHEETS[base_mpn][2]['iq_max_mA']
    alt = DATASHEETS[alt_mpn][2]['iq_max_mA']
    delta = round(packages * 4 * (alt - base), 1)
    return {'per_rail_mA': delta, 'fits_headroom': {r: delta <= h for r, h in HEADROOM_MA.items()}}


def adg_study(copies, adg_inputs, adg_internal, baseline):
    inputs = sum(n * copies[f] for (f, _), n in adg_inputs.items())
    internal = sum(n * copies[f] for (f, _), n in adg_internal.items())
    by_family = collections.Counter()
    for (f, _), n in adg_inputs.items():
        by_family[f] += n
    packed_family = sum(math.ceil(n / 4) * copies[f] for f, n in by_family.items())
    packed_group = sum(math.ceil(n / 4) * copies[f] for (f, _), n in adg_inputs.items())
    def tmux_saving(removed, added):
        # Mixed conditions: ADG planning unit (+-15 V table) vs TMUX7412F maximum at +-16.5 V.
        tmux = {'+12V': 0.6, '-12V': 0.5}
        return {r: round(removed * ADG_IDD_MA[r] - added * tmux[r], 1) for r in ADG_IDD_MA}

    def saving(n_removed):
        return {r: round(n_removed * v, 1) for r, v in ADG_IDD_MA.items()}
    options = [
        {'id': 'ADG-0', 'name': 'HEAD: one ADG5412FBRUZ per input jack plus 12 envelope switches',
         'packages': inputs + internal, 'cost': price('ADG5412FBRUZ', inputs + internal),
         'rows_changed': [], 'classification': 'baseline'},
        {'id': 'ADG-1', 'name': 'Quad-pack input channels per module group (ADG5412FBRUZ kept)',
         'packages': packed_group + internal, 'cost': price('ADG5412FBRUZ', packed_group + internal),
         'ledger_reduction_mA': saving(inputs - packed_group),
         'rows_changed': ['Input fault switch row keeps its identity, but one package serves up to four jacks',
                          'UNKNOWN: no retained fact covers how a fault on one channel affects the other channels '
                          '(the same gap P59-B recorded for output sharing)',
                          'NOT RUN: partition35_floorplan jack-locality fit with shared packages',
                          'Stock 0 at JLC remains an availability blocker'],
         'classification': 'engineering, after the cross-channel fault evidence gap is closed'},
        {'id': 'ADG-2', 'name': 'TMUX7412FRRPR one per input (S toward jack), 12 envelope switches unchanged',
         'packages': inputs, 'cost': price('TMUX7412FRRPR', inputs),
         'ledger_reduction_mA': tmux_saving(inputs, inputs),
         'rows_changed': ['Input fault switch identity changes (standard decision record)',
                          'Footprint TSSOP-16 -> WQFN-16 4x4 (thermal pad and assembly land review)',
                          'Drain pins are not overvoltage protected; S must face the jack, as now',
                          'Powered-off protection needs GND; floating-rail leakage is typical only',
                          'protection58 acceptance and P59-A rev2 clamp interaction must be re-run'],
         'classification': 'user decision (protected-switch identity in the standard)'},
        {'id': 'ADG-3', 'name': 'TMUX7412FRRPR quad-packed (ADG-1 packing) plus envelope switches on ADG5412F',
         'packages': packed_group, 'cost': price('TMUX7412FRRPR', packed_group),
         'ledger_reduction_mA': tmux_saving(inputs, packed_group),
         'rows_changed': ['All ADG-1 and ADG-2 rows'],
         'classification': 'user decision'},
        {'id': 'ADG-4', 'name': 'Discrete series resistor plus BAT54S rail clamp, no switch',
         'packages': 0, 'cost': {'status': 'Clamp line BAT54S,215 already priced at 0.0283 USD; '
                                           'per-input resistor cost is below 0.03 USD'},
         'rows_changed': ['FAIL: the standard rejects a bare clamp to a supply rail because an incoming patch '
                          'can energize an unpowered rail', 'Changes the R-INJ and powered-off behaviour rows'],
         'classification': 'user decision (reverses a recorded architecture rejection)'},
    ]
    internal_opts = []
    for mpn in ('TMUX6112PWR', 'DG412DY', 'ADG1412YRUZ'):
        internal_opts.append({'mpn': mpn, 'cost': price(mpn, internal),
                              'rows_changed': ['Envelope SLOPE_SELECT / STORAGE_CLAMP switch identity',
                                               'UNKNOWN: on-resistance, leakage on the hold node and +/-12 V '
                                               'rating are not read from a retained manufacturer datasheet',
                                               'Pin map compatibility with the ADG5412F TSSOP-16 land is UNKNOWN'],
                              'classification': 'engineering after evidence retrieval'})
    return {'baseline_line': baseline,
            'placements': {'input_fault_switch': inputs, 'envelope_internal': internal,
                           'input_groups': [{'family': f, 'group': g, 'per_instance': n, 'instances': copies[f]}
                                            for (f, g), n in sorted(adg_inputs.items())],
                           'packed_inputs_per_group': packed_group, 'packed_inputs_per_instance': packed_family,
                           'internal': [{'family': f, 'role': r, 'per_instance': n, 'instances': copies[f]}
                                        for (f, r), n in sorted(adg_internal.items())]},
            'options': options, 'envelope_internal_alternatives': internal_opts,
            'datasheet': datasheet('TMUX7412FRRPR')}


def opamp_study(opamps):
    precision = opamps[('OPA4197IPWR', 'precision')]
    audio = opamps[('OPA4196IDR', 'audio/cv')]
    indicator = opamps[('OPA4196IDR', 'indicator')]
    prec = []
    for mpn, rows, cls in [
        ('OPA4197IDR', ['Role package TSSOP-14 -> SOIC-14 (explicit footprint migration per swap_policy)',
                        'Same die and datasheet; IB full-temperature limit improves from 15 to 5 nA',
                        'NOT RUN: board fit of the larger SOIC-14 land'], 'engineering (package migration)'),
        ('OPA4192IDR', ['Role package TSSOP-14 -> SOIC-14', 'Different die: renewed loop, stability and '
                        'input-protection checks', 'VOS max 25 uV at 25 C improves the static budget'],
         'engineering (package migration plus renewed checks)'),
        ('OPA4991IPWR', ['Same TSSOP-14 package; exact pin map must be retained',
                         'VOS max 830 uV uses 42 % of the 2 mV static and octave-step rows per amplifier; '
                         'paths with two or more untrimmed stages need a per-path stack',
                         'GBW 4.5 MHz vs 10 MHz: renewed loop checks'],
         'user decision (relaxes precision margin)'),
        ('OPA4171AIPWR', ['Same TSSOP-14 package', 'FAIL: VOS max 1.8 mV (2.0 mV over temperature) consumes the '
                          '2 mV static_precision_error_V and octave_step_error_V rows with one amplifier',
                          'Input range ends at (V+) - 2 V; GBW 3 MHz, SR 1.5 V/us'],
         'user decision (fails precision rows)'),
    ]:
        prec.append({'mpn': mpn, 'packages': precision, 'cost': price(mpn, precision),
                     'iq_change': iq_delta(precision, 'OPA4197IPWR', mpn), 'datasheet': datasheet(mpn),
                     'rows_changed': rows, 'classification': cls})
    general = []
    for scope, n in (('all audio/cv/indicator packages', audio + indicator), ('indicator packages only', indicator)):
        for mpn in ('TL074HIDR', 'LM324DR', 'OPA4171AIDR'):
            rows = ['Iq rises above the OPA4196 0.25 mA per amplifier', 'Renewed loop and headroom checks']
            if mpn == 'LM324DR':
                rows.append('VIO 7 mV max; input range ends at VCC - 2 V; not rail-to-rail')
            general.append({'scope': scope, 'mpn': mpn, 'packages': n, 'cost': price(mpn, n),
                            'iq_change': iq_delta(n, 'OPA4196IDR', mpn), 'datasheet': datasheet(mpn),
                            'rows_changed': rows,
                            'classification': 'user decision (PD contract change with PD agreement)'})
    return {'packages': {'precision OPA4197IPWR': precision, 'audio/cv OPA4196IDR': audio,
                         'indicator OPA4196IDR': indicator},
            'baseline': {'OPA4197IPWR': price('OPA4197IPWR', precision),
                         'OPA4196IDR': price('OPA4196IDR', audio + indicator)},
            'baseline_datasheets': {m: datasheet(m) for m in ('OPA4197IPWR', 'OPA4196IDR')},
            'precision_alternatives': prec, 'general_alternatives': general}


# Each role: function used to judge the change, current values, and proposals.
# kind 'ratio' keeps an amplifier gain or divider; 'abs' sets a current or a span.
RESISTOR_ROLES = [
    ('80k', 'envelope:R_REF9_FB', 'REF9 = REF5 * (1 + RF/RG), RG = 100 k', 6,
     [('series', ['RT0603BRD0740KL', 'RT0603BRD0740KL'], 80e3), ('rescale RF 40 k, RG 50 k', ['RT0603BRD0740KL'], 80e3),
      ('nearest', ['RT0603BRD0780K6L'], 80.6e3)], lambda r: 5 * (1 + r / 100e3), 'V'),
    ('80k', 'envelope:R_BIP_PLUS_BOTTOM', 'BIP_PLUS = ENV * 80k/(64k+80k); BIP gain 1.25', 6,
     [('rescale TOP 40 k, BOTTOM 50 k', ['RT0603BRD0750KL'], 80e3), ('series', ['RT0603BRD0740KL'] * 2, 80e3),
      ('nearest', ['RT0603BRD0780K6L'], 80.6e3)], lambda r: 2.25 * r / (64e3 + r), 'gain'),
    ('80k', 'oscillator:R_SAW_IN', 'SAW gain = 100k / R_SAW_IN', 5,
     [('series', ['RT0603BRD0740KL'] * 2, 80e3), ('nearest', ['RT0603BRD0780K6L'], 80.6e3)],
     lambda r: 100e3 / r, 'gain'),
    ('899k', 'envelope:R_RISE_DRIVE_TOP / R_FALL_DRIVE_TOP', 'OTA drive attenuation 1k / (R + 1k)', 12,
     [('series', ['RT0603BRD07820KL', 'RT0603BRD0778K7L'], 898.7e3), ('nearest', ['RT0603BRD07887KL'], 887e3)],
     lambda r: 1e3 / (r + 1e3), 'ratio'),
    ('250k', 'oscillator:R_PITCH_TUNE', 'TUNE span = 5 V * 100k / R (manual knob)', 5,
     [('nearest', ['RT0603BRD07249KL'], 249e3), ('series', ['RT0603BRD07200KL', 'RT0603BRD0750KL'], 250e3)],
     lambda r: 5 * 100e3 / r, 'V'),
    ('250k', 'oscillator:R_TRI_BIAS_TOP', 'TRI_BIAS = REF5 * 100k / (R + 100k)', 5,
     [('rescale TOP 50 k, BOTTOM 20 k', ['RT0603BRD0750KL', 'RT0603BRD0720KL'], 250e3),
      ('series', ['RT0603BRD07200KL', 'RT0603BRD0750KL'], 250e3),
      ('nearest', ['RT0603BRD07249KL'], 249e3)], lambda r: 5 * 100e3 / (r + 100e3), 'V'),
    ('64k', 'envelope:R_BIP_PLUS_TOP', 'BIP_PLUS divider top; see R_BIP_PLUS_BOTTOM', 6,
     [('rescale TOP 40 k, BOTTOM 50 k', ['RT0603BRD0740KL'], 64e3), ('series', ['RT0603BRD0732KL'] * 2, 64e3),
      ('nearest', ['RT0603BRD0764K9L'], 64.9e3)], lambda r: 2.25 * 80e3 / (r + 80e3), 'gain'),
    ('79k', 'envelope:R_FLOOR_TOP', 'FLOOR_REF = REF5 * 22k / (R + 22k)', 6,
     [('series', ['RT0603BRD0747KL', 'RT0603BRD0732KL'], 79e3), ('nearest', ['RT0603BRD0778K7L'], 78.7e3)],
     lambda r: 5 * 22e3 / (r + 22e3), 'V'),
    ('400k', 'envelope:R_BIP_GROUND', 'BIP gain 1 + 100k/(100k || R); offset -REF5', 6,
     [('rescale REF/FB/GROUND 50 k/50 k/200 k', ['RT0603BRD0750KL', 'RT0603BRD07200KL'], 400e3),
      ('series', ['RT0603BRD07200KL'] * 2, 400e3), ('nearest', ['RT0603BRD07402KL'], 402e3)],
     lambda r: (1 + 100e3 / (100e3 * r / (100e3 + r))) * 80 / 144, 'gain'),
    ('5.72k', 'oscillator:R_RT', 'AS3340 scale resistor inside the trimmed scale network', 5,
     [('series', ['RT0603BRD075K1L', 'RT0603BRD07620RL'], 5.72e3), ('nearest', ['RT0603BRD075K76L'], 5.76e3)],
     lambda r: r, 'ohm'),
    ('25k', 'oscillator:R_REF4_TOP', 'REF4 = REF5 * 100k / (R + 100k), PWM clamp reference', 5,
     [('nearest', ['RT0603BRD0724K9L'], 24.9e3), ('rescale TOP 10 k, BOTTOM 40 k', ['RT0603BRD0710KL'], 25e3)],
     lambda r: 5 * 100e3 / (r + 100e3), 'V'),
    ('72k', 'oscillator:R_PWM_FB', 'PWM command = (0.2 + 0.72 man + 0.36 depth) scale', 5,
     [('series', ['RT0603BRD0740KL', 'RT0603BRD0732KL'], 72e3), ('nearest', ['RT0603BRD0771K5L'], 71.5e3)],
     lambda r: r / 100e3, 'gain'),
    ('125k', 'oscillator:R_SAW_BIAS_TOP', 'SAW_BIAS = REF5 * 100k / (R + 100k)', 5,
     [('rescale TOP 50 k, BOTTOM 40 k', ['RT0603BRD0750KL', 'RT0603BRD0740KL'], 125e3),
      ('series', ['RT0603BRD0775KL', 'RT0603BRD0750KL'], 125e3), ('nearest', ['RT0603BRD07124KL'], 124e3)],
     lambda r: 5 * 100e3 / (r + 100e3), 'V'),
    ('1.2M', 'oscillator:R_LINEAR_REFERENCE', 'AS3340 linear reference current from +12 V', 5,
     [('series', ['RT0603BRD071ML', 'RT0603BRD07200KL'], 1.2e6), ('r_general', ['RC0603FR-071M2L'], 1.2e6)],
     lambda r: 12 / r * 1e6, 'uA'),
    ('1.8M', 'oscillator:R_PWM_OFFSET', 'PWM offset = REF5 * 72k / R', 5,
     [('series', ['RT0603BRD071ML', 'RT0603BRD07820KL'], 1.82e6), ('r_general', ['RC0603FR-071M8L'], 1.8e6)],
     lambda r: 5 * 72e3 / r, 'V'),
    ('5M', 'oscillator:R_PITCH_FINE', 'FINE span = 5 V * 100k / R (manual knob)', 5,
     [('series', ['RT0603BRD071ML'] * 5, 5e6), ('r_general', ['RC0603FR-075M1L'], 5.1e6)],
     lambda r: 5 * 100e3 / r, 'V'),
    ('70k', 'wavefolder:R_OUTPUT_RF', 'Output gain 1 + R / 10k', 2,
     [('series', ['RT0603BRD0720KL', 'RT0603BRD0750KL'], 70e3), ('nearest', ['RT0603BRD0769K8L'], 69.8e3)],
     lambda r: 1 + r / 10e3, 'gain'),
]
NOMINAL = {'80k': 80e3, '899k': 899e3, '250k': 250e3, '64k': 64e3, '79k': 79e3, '400k': 400e3, '5.72k': 5.72e3,
           '25k': 25e3, '72k': 72e3, '125k': 125e3, '1.2M': 1.2e6, '1.8M': 1.8e6, '5M': 5e6, '70k': 70e3}


def resistor_study():
    out = []
    for value, role, function, qty, proposals, fn, unit in RESISTOR_ROLES:
        nominal = fn(NOMINAL[value])
        rows = []
        for kind, parts, effective in proposals:
            if kind.startswith('rescale'):
                result = nominal
            else:
                result = fn(effective)
            lines = []
            for mpn in parts:
                row, _ = jlc_row(mpn)
                lines.append({'mpn': mpn, 'lcsc': row['lcsc'] if row else None,
                              'stock': row['stock'] if row else 'UNKNOWN',
                              'unit_price_usd': tier_price(row['tiers'], qty) if row else 'UNKNOWN'})
            known = all(isinstance(x['unit_price_usd'], float) for x in lines)
            rows.append({'proposal': kind, 'parts_per_placement': lines,
                         'added_placements_per_unit': (len(parts) - 1) * qty if kind in ('series',) else 0,
                         'nominal_result': round(result, 6), 'unit': unit,
                         'nominal_error_percent': round((result / nominal - 1) * 100, 3),
                         'tolerance_class': '1 % thick film (r_general)' if kind == 'r_general' else '0.1 % thin film',
                         'all_stock_covers_lot': all(isinstance(x['stock'], int) and x['stock'] >= qty * LOT * len(parts)
                                                     for x in lines),
                         'per_unit_usd': round(sum(x['unit_price_usd'] for x in lines) * qty, 4) if known else 'UNKNOWN'})
        out.append({'value': value, 'role': role, 'qty_per_unit': qty, 'function': function,
                    'nominal_result': round(nominal, 6), 'unit': unit, 'proposals': rows})
    return out


# Plan selection rule for R-exact: an exact rescale only where the changed partner is
# not on a shared reference node, otherwise the nominal if within the 0.1 % class,
# otherwise an exact series pair. R-min never adds a placement.
RESISTOR_PLANS = {
    'R-exact': {'envelope:R_REF9_FB': 'rescale', 'envelope:R_BIP_PLUS_BOTTOM': 'rescale',
                'envelope:R_BIP_PLUS_TOP': None, 'envelope:R_BIP_GROUND': 'nearest',
                'oscillator:R_SAW_IN': 'series', 'envelope:R_RISE_DRIVE_TOP / R_FALL_DRIVE_TOP': 'series',
                'oscillator:R_PITCH_TUNE': 'series', 'oscillator:R_TRI_BIAS_TOP': 'series',
                'envelope:R_FLOOR_TOP': 'series', 'oscillator:R_RT': 'series', 'oscillator:R_REF4_TOP': 'nearest',
                'oscillator:R_PWM_FB': 'series', 'oscillator:R_SAW_BIAS_TOP': 'series',
                'oscillator:R_LINEAR_REFERENCE': 'series', 'oscillator:R_PWM_OFFSET': 'series',
                'oscillator:R_PITCH_FINE': 'series', 'wavefolder:R_OUTPUT_RF': 'series'},
    'R-min': {'envelope:R_REF9_FB': 'rescale', 'envelope:R_BIP_PLUS_BOTTOM': 'rescale',
              'envelope:R_BIP_PLUS_TOP': None, 'envelope:R_BIP_GROUND': 'nearest',
              'oscillator:R_SAW_IN': 'nearest', 'envelope:R_RISE_DRIVE_TOP / R_FALL_DRIVE_TOP': 'nearest',
              'oscillator:R_PITCH_TUNE': 'nearest', 'oscillator:R_TRI_BIAS_TOP': 'nearest',
              'envelope:R_FLOOR_TOP': 'nearest', 'oscillator:R_RT': 'nearest', 'oscillator:R_REF4_TOP': 'nearest',
              'oscillator:R_PWM_FB': 'nearest', 'oscillator:R_SAW_BIAS_TOP': 'nearest',
              'oscillator:R_LINEAR_REFERENCE': 'r_general', 'oscillator:R_PWM_OFFSET': 'r_general',
              'oscillator:R_PITCH_FINE': 'r_general', 'wavefolder:R_OUTPUT_RF': 'nearest'},
}


def resistor_plans(roles):
    out = {}
    for name, pick in RESISTOR_PLANS.items():
        cost, added, worst, blocked, rows = 0.0, 0, 0.0, [], []
        for role in roles:
            choice = pick[role['role']]
            if choice is None:
                rows.append({'role': role['role'], 'proposal': 'covered by the BIP_PLUS rescale'})
                continue
            prop = next(x for x in role['proposals'] if x['proposal'].startswith(choice))
            cost += prop['per_unit_usd'] if isinstance(prop['per_unit_usd'], float) else 0
            added += prop['added_placements_per_unit']
            worst = max(worst, abs(prop['nominal_error_percent']))
            if not prop['all_stock_covers_lot']:
                blocked.append(role['role'])
            rows.append({'role': role['role'], 'proposal': prop['proposal'],
                         'nominal_error_percent': prop['nominal_error_percent'],
                         'added_placements_per_unit': prop['added_placements_per_unit']})
        out[name] = {'per_unit_usd': round(cost, 2), 'added_placements_per_unit': added,
                     'worst_nominal_error_percent': worst, 'stock_short_of_lot': blocked, 'selection': rows}
    return out


def build():
    cost = json.loads(COST.read_text())
    baseline = next(x for x in cost['exact_lines'] if x['mpn'] == 'ADG5412FBRUZ')['cost']
    copies, adg_inputs, adg_internal, opamps = inventory()
    return {'schema_version': 1,
            'status': 'UNADOPTED PROPOSALS; not a fabrication BOM, quote or order file',
            'retrieved': RETRIEVED, 'lot_units': LOT, 'currency': 'USD',
            'tier_rule': 'Unit cost uses the JLC tier containing the per-unit quantity; lot cost uses the tier '
                         'containing five times that quantity.',
            'headroom_mA': HEADROOM_MA, 'adg_planning_idd_mA': ADG_IDD_MA,
            'phase13_totals': {'exact': cost['exact_total'], 'candidates': cost['candidate_total']},
            'adg5412f': adg_study(copies, adg_inputs, adg_internal, baseline),
            'opamps': opamp_study(opamps),
            'resistors': (res := resistor_study()),
            'resistor_plans': resistor_plans(res)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not (CACHE / 'jlc').exists():
        print(f'NOT RUN: retained catalog cache {CACHE.relative_to(ROOT)} is absent')
        return 4
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            print(f'FAIL: {OUTPUT.relative_to(ROOT)} is stale; run without --check')
            return 1
        print('PASS: cost-reduction study matches the retained evidence')
        return 0
    OUTPUT.write_text(text)
    print(f'wrote {OUTPUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
