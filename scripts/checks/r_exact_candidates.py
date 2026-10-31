#!/usr/bin/env python3
"""R-exact candidate identities and per-role error table for the 14 non-stocked precision values.

Inputs: retained read-only bytes in .circuit-cache/sources/readiness-20261031/ (git-ignored):
jlc/<MPN>.json JLC search responses and spec/<MPN>.pdf Yageo spec sheets, retrieved
2026-10-31. Spec sheets are read with pdftotext.

UNADOPTED. Nothing here changes the schematic, inventory, PCB or an order file.
"""
import argparse
import hashlib
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.checks.passive_candidates import CACHE, LOT, RETRIEVED, SPEC_URL, jlc_row, tier_price  # noqa: E402

OUTPUT = ROOT / 'design/readiness/r-exact-candidates.json'
TOL = 0.001
POLICY = json.loads((ROOT / 'design/standard/electrical-standard.json').read_text())['passive_policy']['resistors']['r_precision']


def mpn(value):
    return f'RT0603BRD07{value}L'


# role: (function, head values, R-exact values, instances per unit, unit)
# Values are lists of series elements in ohms; the key names the resistor in the function.
ROLES = {
    'envelope:R_REF9_FB (with R_REF9_RG)': (
        lambda v: 5 * (1 + v['RF'] / v['RG']), {'RF': [80e3], 'RG': [100e3]},
        {'RF': [('40K', 40e3)], 'RG': [('50K', 50e3)]}, 6, 'V', 'rescale'),
    'envelope:R_BIP_PLUS_TOP / R_BIP_PLUS_BOTTOM / R_BIP_GROUND': (
        lambda v: (1 + v['FB'] / (v['REF'] * v['GND'] / (v['REF'] + v['GND']))) * v['BOT'] / (v['TOP'] + v['BOT']),
        {'FB': [100e3], 'REF': [100e3], 'GND': [400e3], 'TOP': [64e3], 'BOT': [80e3]},
        {'FB': [('100K', 100e3)], 'REF': [('100K', 100e3)], 'GND': [('402K', 402e3)],
         'TOP': [('40K', 40e3)], 'BOT': [('50K', 50e3)]}, 6, 'gain', 'rescale + nearest'),
    'oscillator:R_SAW_IN': (
        lambda v: v['FB'] / v['IN'], {'FB': [100e3], 'IN': [80e3]},
        {'FB': [('100K', 100e3)], 'IN': [('40K', 40e3), ('40K', 40e3)]}, 5, 'gain', 'series'),
    'envelope:R_RISE_DRIVE_TOP / R_FALL_DRIVE_TOP': (
        lambda v: v['BOT'] / (v['TOP'] + v['BOT']), {'TOP': [899e3], 'BOT': [1e3]},
        {'TOP': [('820K', 820e3), ('78K7', 78.7e3)], 'BOT': [('1K', 1e3)]}, 12, 'ratio', 'series'),
    'oscillator:R_PITCH_TUNE': (
        lambda v: 5 * v['PITCH'] / v['TUNE'], {'PITCH': [100e3], 'TUNE': [250e3]},
        {'PITCH': [('100K', 100e3)], 'TUNE': [('200K', 200e3), ('50K', 50e3)]}, 5, 'V', 'series'),
    'oscillator:R_TRI_BIAS_TOP': (
        lambda v: 5 * v['BOT'] / (v['TOP'] + v['BOT']), {'TOP': [250e3], 'BOT': [100e3]},
        {'TOP': [('200K', 200e3), ('50K', 50e3)], 'BOT': [('100K', 100e3)]}, 5, 'V', 'series'),
    'envelope:R_FLOOR_TOP': (
        lambda v: 5 * v['BOT'] / (v['TOP'] + v['BOT']), {'TOP': [79e3], 'BOT': [22e3]},
        {'TOP': [('47K', 47e3), ('32K', 32e3)], 'BOT': [('22K', 22e3)]}, 6, 'V', 'series'),
    'oscillator:R_RT': (
        lambda v: v['R'], {'R': [5.72e3]}, {'R': [('5K1', 5.1e3), ('620R', 620)]}, 5, 'ohm', 'series'),
    'oscillator:R_REF4_TOP': (
        lambda v: 5 * v['BOT'] / (v['TOP'] + v['BOT']), {'TOP': [25e3], 'BOT': [100e3]},
        {'TOP': [('24K9', 24.9e3)], 'BOT': [('100K', 100e3)]}, 5, 'V', 'nearest'),
    'oscillator:R_PWM_FB': (
        lambda v: v['FB'] / v['MAN'], {'FB': [72e3], 'MAN': [100e3]},
        {'FB': [('40K', 40e3), ('32K', 32e3)], 'MAN': [('100K', 100e3)]}, 5, 'gain', 'series'),
    'oscillator:R_SAW_BIAS_TOP': (
        lambda v: 5 * v['BOT'] / (v['TOP'] + v['BOT']), {'TOP': [125e3], 'BOT': [100e3]},
        {'TOP': [('75K', 75e3), ('50K', 50e3)], 'BOT': [('100K', 100e3)]}, 5, 'V', 'series'),
    'oscillator:R_LINEAR_REFERENCE': (
        lambda v: 12 / v['R'] * 1e6, {'R': [1.2e6]}, {'R': [('1M', 1e6), ('200K', 200e3)]}, 5, 'uA', 'series'),
    'oscillator:R_PWM_OFFSET': (
        lambda v: 5 * v['FB'] / v['OFF'], {'FB': [72e3], 'OFF': [1.8e6]},
        {'FB': [('40K', 40e3), ('32K', 32e3)], 'OFF': [('1M', 1e6), ('820K', 820e3)]}, 5, 'V', 'series'),
    'oscillator:R_PITCH_FINE': (
        lambda v: 5 * v['PITCH'] / v['FINE'], {'PITCH': [100e3], 'FINE': [5e6]},
        {'PITCH': [('100K', 100e3)], 'FINE': [('1M', 1e6)] * 5}, 5, 'V', 'series'),
    'wavefolder:R_OUTPUT_RF': (
        lambda v: 1 + v['RF'] / v['RG'], {'RF': [70e3], 'RG': [10e3]},
        {'RF': [('20K', 20e3), ('50K', 50e3)], 'RG': [('10K', 10e3)]}, 2, 'gain', 'series'),
}


def evaluate(fn, values):
    """Nominal and worst-case (each element at +/-0.1 %) result."""
    nominal = fn({k: sum(v) for k, v in values.items()})
    elements = [(k, i) for k, v in values.items() for i in range(len(v))]
    lo, hi = nominal, nominal
    for signs in itertools.product((-1, 1), repeat=len(elements)):
        trial = {k: list(v) for k, v in values.items()}
        for (k, i), s in zip(elements, signs):
            trial[k][i] *= 1 + s * TOL
        r = fn({k: sum(v) for k, v in trial.items()})
        lo, hi = min(lo, r), max(hi, r)
    return nominal, lo, hi


def spec(m):
    path = CACHE / 'spec' / f'{m}.pdf'
    if not path.exists():
        return None
    raw = path.read_bytes()
    text = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True).stdout
    text = text.replace('​', '')

    def field(label):
        hit = re.search(label + r'\s{2,}(.+?)\s*$', text, re.M)
        return hit[1].strip() if hit else None
    row = {'url': SPEC_URL + m, 'retrieved': RETRIEVED, 'sha256': hashlib.sha256(raw).hexdigest(),
           'authority_class': 'MANUFACTURER_PRIMARY', 'mpn_printed': m in text,
           'resistance': field('Resistance'), 'tolerance': field('Resistance Tolerance'),
           'power': field('Power'), 'tcr': field('Temp. Coefficient'), 'voltage_dc': field('Voltage DC')}
    tol = re.search(r'([0-9.]+)\s*%', row['tolerance'] or '')
    tcr = re.search(r'([0-9]+)\s*ppm', row['tcr'] or '')
    pw = re.search(r'([0-9.]+)\s*W', row['power'] or '')
    vdc = re.search(r'([0-9]+)\s*V', row['voltage_dc'] or '')
    row['r_precision_class'] = ('PASS' if tol and tcr and pw and vdc and row['mpn_printed']
                                and float(tol[1]) <= POLICY['tolerance_percent']
                                and int(tcr[1]) <= POLICY['target_tempco_ppm_per_K']
                                and float(pw[1]) >= POLICY['minimum_power_W']
                                and int(vdc[1]) >= POLICY['minimum_working_voltage_V'] else 'UNKNOWN')
    return row


def identity(code, qty):
    m = mpn(code)
    row, receipt = jlc_row(m)
    return {'mpn': m, 'jlc': None if not row else {
        'lcsc': row['lcsc'], 'brand': row['brand'], 'stock': row['stock'], 'stock_covers_lot': row['stock'] >= qty * LOT,
        'unit_price_usd': tier_price(row['tiers'], qty), 'lot_unit_price_usd': tier_price(row['tiers'], qty * LOT)},
        'jlc_receipt': receipt, 'manufacturer_spec': spec(m)}


def build():
    roles, parts = [], {}
    for role, (fn, head, new, inst, unit, kind) in ROLES.items():
        h = evaluate(fn, head)
        values = {k: [x[1] for x in v] for k, v in new.items()}
        n = evaluate(fn, values)
        unchanged = {k for k in new if [x[1] for x in new[k]] == head[k]}
        # R_PWM_FB is the same physical resistor in both PWM rows; count it once.
        shared = {'FB'} if role == 'oscillator:R_PWM_OFFSET' else set()
        changed = {k: [x[0] for x in v] for k, v in new.items() if k not in unchanged}
        added = sum(len(v) - 1 for k, v in new.items() if k not in shared) * inst
        for k, v in changed.items():
            if k in shared:
                continue
            for code in v:
                parts[code] = parts.get(code, 0) + inst
        roles.append({'role': role, 'proposal': kind, 'instances_per_unit': inst, 'unit': unit,
                      'head_values_ohm': head, 'r_exact_elements': changed, 'shared_with_other_row': sorted(shared),
                      'added_placements_per_unit': added, 'head_nominal': round(h[0], 6),
                      'r_exact_nominal': round(n[0], 6),
                      'nominal_shift_percent': round((n[0] / h[0] - 1) * 100, 4),
                      'head_tolerance_band_percent': [round((h[1] / h[0] - 1) * 100, 4), round((h[2] / h[0] - 1) * 100, 4)],
                      'r_exact_band_vs_head_nominal_percent': [round((n[1] / h[0] - 1) * 100, 4),
                                                               round((n[2] / h[0] - 1) * 100, 4)]})
    lines = [identity(code, qty) | {'qty_per_unit_added_or_changed': qty} for code, qty in sorted(parts.items())]
    return {'schema_version': 1, 'status': 'UNADOPTED candidates; not an order file', 'retrieved': RETRIEVED,
            'tolerance_model': 'Every element at +/-0.1 % independently (all sign corners); TCR, ageing and '
                               'solder drift are not included',
            'r_precision_policy': POLICY, 'roles': roles,
            'added_placements_per_unit': sum(r['added_placements_per_unit'] for r in roles),
            'lines': lines,
            'lines_r_precision_pass': sum(1 for x in lines if x['manufacturer_spec'] and
                                          x['manufacturer_spec']['r_precision_class'] == 'PASS'),
            'board_impact': {'board': 'K (osc-core)', 'basis': 'design/partition/partition.json assignment of every '
                             'affected role reference',
                             'implied_reruns': ['schematic regeneration and master audit (designator locks)',
                                                'partition35 floorplan chain', 'osc-core placement and routing',
                                                '#293 zone fill (input changed)', 'osc-core DRC']}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not (CACHE / 'spec').exists():
        print(f'NOT RUN: retained catalog cache {CACHE.relative_to(ROOT)} is absent')
        return 4
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            print(f'FAIL: {OUTPUT.relative_to(ROOT)} is stale; run without --check')
            return 1
        print('PASS: R-exact candidates match the retained evidence')
        return 0
    OUTPUT.write_text(text)
    print(f'wrote {OUTPUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
