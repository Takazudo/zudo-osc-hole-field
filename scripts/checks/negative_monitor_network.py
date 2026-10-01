"""Exact passive-network screening; no complete monitor or permit admission."""
import argparse
import hashlib
import itertools
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.checks.rail_monitor_candidate import number, display

SPEC = ROOT / 'design/power/negative-monitor-network.json'
SOURCES = ROOT / 'design/power/negative-monitor-network-sources.json'
REPORT = ROOT / 'design/power/negative-monitor-network-report.json'
NODES = ('REF', 'SENSE', 'UV', 'OV')


def solve(matrix, rhs):
    """Fraction Gaussian elimination; singular networks fail explicitly."""
    a = [list(row) + [value] for row, value in zip(matrix, rhs)]
    for i in range(len(a)):
        pivot = next((j for j in range(i, len(a)) if a[j][i]), None)
        if pivot is None:
            raise ValueError('singular passive network')
        a[i], a[pivot] = a[pivot], a[i]
        scale = a[i][i]
        a[i] = [v / scale for v in a[i]]
        for j in range(len(a)):
            if j != i:
                scale = a[j][i]
                a[j] = [v - scale * w for v, w in zip(a[j], a[i])]
    return [row[-1] for row in a]


def nodal(spec, resistance, fixed, injections=None):
    """Positive injections enter a node; input sink currents are negative."""
    unknown = [n for n in NODES if n not in fixed]
    indices = {n: i for i, n in enumerate(unknown)}
    matrix = [[F() for _ in unknown] for _ in unknown]
    rhs = [F((injections or {}).get(n, 0)) for n in unknown]
    for part in spec['resistors']:
        g = 1 / resistance[part['ref']]
        a, b = part['nodes']
        for node, other in ((a, b), (b, a)):
            if node not in indices:
                continue
            i = indices[node]
            matrix[i][i] += g
            if other in indices:
                matrix[i][indices[other]] -= g
            else:
                rhs[i] += g * fixed[other]
    return {**fixed, **dict(zip(unknown, solve(matrix, rhs)))}, matrix, unknown


def resistor_corners(spec):
    c = spec['conditions']
    delta = max(abs(number(t) - number(c['resistor_reference_C']))
                for t in c['resistor_temperature_C'])
    tol = number(c['resistor_tolerance_fraction'])
    drift = delta * number(c['resistor_tcr_per_C'])
    if not 0 <= tol < 1 or not 0 <= drift < 1:
        raise ValueError('invalid resistor condition')
    factors = ((1 - tol) * (1 - drift), (1 + tol) * (1 + drift))
    for choices in itertools.product(factors, repeat=len(spec['resistors'])):
        yield {p['ref']: number(p['ohm']) * factor
               for p, factor in zip(spec['resistors'], choices)}


def validate(spec, retained=False):
    if spec['protection_implemented'] or len(spec['resistors']) != 8:
        raise ValueError('not an admitted protection circuit')
    records = json.loads(SOURCES.read_text())['sources']
    sources = {r['mpn']: r for r in records}
    if len(sources) != len(records) or len({r['id'] for r in records}) != len(records):
        raise ValueError('duplicate source')
    required = {p['mpn'] for p in spec['resistors']} | {
        spec['comparator']['mpn'], spec['reference']['mpn']}
    if not required <= sources.keys():
        raise ValueError('required device/source evidence missing or mismatched')
    expected = {
        'RN': ('VN', 'SENSE'), 'RR': ('REF', 'SENSE'), 'RG': ('SENSE', 'AGND'),
        'RB': ('REF', 'AGND'), 'RU': ('REF', 'UV'), 'RUG': ('UV', 'AGND'),
        'RO': ('REF', 'OV'), 'ROG': ('OV', 'AGND')}
    if {p['ref']: tuple(p['nodes']) for p in spec['resistors']} != expected:
        raise ValueError('captured topology changed; review equations first')
    for p in spec['resistors']:
        r = sources[p['mpn']]
        if (number(p['ohm']) <= 0 or p['ohm'] != r['resistance_ohm']
                or r['tolerance_fraction'] != spec['conditions']['resistor_tolerance_fraction']
                or r['tcr_abs_per_C'] != spec['conditions']['resistor_tcr_per_C']):
            raise ValueError('exact resistor evidence mismatch')
    d = spec['comparator']; r = spec['reference']
    if (d['mpn'] != 'TLV9022DR' or r['mpn'] != 'REF3433TIDBVR'
            or d['input_absolute_V'] != [-.3, 6]
            or r['output_absolute_V'] != [-.3, 5.5]
            or d['internal_hysteresis'] is not False
            or d['power_on_reset_guarantee'] is not False
            or any(v is not None for v in (d['propagation_max_s'], d['input_bias_max_A'],
                       r['startup_max_s'], r['unpowered_output_leakage_max_A']))):
        raise ValueError('unsupported source promotion')
    if (d['pins'] != {'1':'FAULT_N','2':'SENSE','3':'UV','4':'AGND',
                     '5':'SENSE','6':'OV','7':'FAULT_N','8':'+5V'}
            or r['pins'] != {'1':'NC','2':'AGND','3':'NC','4':'+5V','5':'NC','6':'REF'}):
        raise ValueError('exact pin map changed')
    for record in records:
        if (record['authority'] != 'MANUFACTURER_PRIMARY' or record['availability'] != 'AVAILABLE'
                or not re.fullmatch('[0-9a-f]{64}', record['sha256'])
                or set(record['sha256']) == {'0'}
                or type(record['bytes']) is not int or record['bytes'] <= 0):
            raise ValueError('primary evidence required')
        if retained:
            data = (ROOT / record['file']).read_bytes()
            if (not data.startswith(b'%PDF-') or len(data) != record['bytes']
                    or hashlib.sha256(data).hexdigest() != record['sha256']):
                raise ValueError('retained source mismatch: ' + record['mpn'])


def calculate(spec):
    c = spec['conditions']
    cold = {n: [None, None] for n in NODES}
    impedance = {n: F() for n in NODES}
    forced = {n: [None, None] for n in NODES}
    trips = {n: [None, None] for n in ('UV', 'OV')}
    reference_current = F()
    def extend(target, key, value):
        lo, hi = target[key]
        target[key] = [value if lo is None else min(lo, value),
                       value if hi is None else max(hi, value)]
    bias = number(c['powered_input_bias_per_pin_A'])
    error = number(c['powered_comparator_error_V'])
    leakage = number(c['cold_uniform_leakage_per_pin_A'])
    if min(bias, error, leakage) < 0:
        raise ValueError('negative error envelope')
    count = 0
    for resistance in resistor_corners(spec):
        count += 1
        # A passive conductance matrix has a nonnegative inverse. This RHS
        # sums absolute per-pin responses, counting both SENSE input pins.
        fixed = {'AGND': F(), 'VN': F()}
        z, _, _ = nodal(spec, resistance, fixed,
                        {'REF': F(1), 'SENSE': F(2), 'UV': F(1), 'OV': F(1)})
        for n in NODES:
            if z[n] < 0:
                raise ValueError('nonpassive response')
            impedance[n] = max(impedance[n], z[n])
        for vn in map(number, c['forced_VN_V']):
            v, _, _ = nodal(spec, resistance, {'AGND': F(), 'VN': vn})
            for n in NODES:
                extend(cold, n, v[n])
            for ref in (number(spec['reference']['output_absolute_V'][0]),
                        number(spec['reference']['normal_target_V'][1])):
                v, _, _ = nodal(spec, resistance, {'AGND': F(), 'VN': vn, 'REF': ref})
                for n in NODES:
                    extend(forced, n, v[n])
                if ref > 0:
                    demand = sum((v['REF']-v[p['nodes'][1]]) / resistance[p['ref']]
                                 for p in spec['resistors'] if p['nodes'][0] == 'REF')
                    reference_current = max(reference_current, demand)
        # Solve SENSE == threshold with independent comparator and input-current
        # error envelopes, retaining the SAME reference voltage in both legs.
        rn, rr, rg = (resistance[n] for n in ('RN', 'RR', 'RG'))
        total = 1/rn + 1/rr + 1/rg
        for ref in map(number, spec['reference']['normal_target_V']):
            for name, top, bottom in (('UV','RU','RUG'), ('OV','RO','ROG')):
                rt, rb = resistance[top], resistance[bottom]
                threshold = ref * rb/(rt+rb)
                vn = rn * (total*threshold - ref/rr)
                spread = rn * (total*(error+bias*rt*rb/(rt+rb)) + 2*bias)
                extend(trips, name, -vn-spread)
                extend(trips, name, -vn+spread)
    pins = {}
    budgets = []
    for n in NODES:
        limits = spec['reference']['output_absolute_V'] if n == 'REF' else spec['comparator']['input_absolute_V']
        lo, hi = map(number, limits)
        lower, upper = cold[n]
        budget = min(lower-lo, hi-upper)/impedance[n]
        budgets.append(budget)
        pins[n] = {
            'open_reference_zero_leakage_V': [display(lower, False), display(upper, True)],
            'uniform_per_pin_leakage_sensitivity_ohm_upper': display(impedance[n], True),
            'conditional_cold_V': [display(lower-leakage*impedance[n], False),
                                   display(upper+leakage*impedance[n], True)],
            'conditional_cold_within_absolute_rating': lower-leakage*impedance[n] >= lo and upper+leakage*impedance[n] <= hi,
            'forced_reference_zero_leakage_V': [display(v, i == 1) for i, v in enumerate(forced[n])],
            'forced_reference_zero_leakage_within_absolute_rating': forced[n][0] >= lo and forced[n][1] <= hi}
    bands = json.loads((ROOT/spec['normal_voltage_source']).read_text())['source_requirement']['required_load_voltage_magnitude_V']['-12V']
    nominal = {p['ref']: number(p['ohm']) for p in spec['resistors']}
    collapsed, _, _ = nodal(spec, nominal, {'AGND': F(), 'VN': F(-8), 'REF': F(22,10)})
    uv_margin = collapsed['UV']-collapsed['SENSE']
    ov_margin = collapsed['SENSE']-collapsed['OV']
    return {
        'status': 'UNSELECTED conditional passive network; protection unimplemented',
        'protection_implemented': False, 'resistor_corner_count': count,
        'pin_screen': pins,
        'sufficient_uniform_per_pin_cold_leakage_budget_A': display(min(budgets), False),
        'conditional_trip_magnitude_V': {n: [display(a, False), display(b, True)] for n, (a,b) in trips.items()},
        'normal_magnitude_V': bands,
        'conditional_static_normal_band_accepted': number(bands[0]) > trips['UV'][1] and number(bands[1]) < trips['OV'][0],
        'normal_UV_margin_V': display(number(bands[0])-trips['UV'][1], False),
        'normal_OV_margin_V': display(trips['OV'][0]-number(bands[1]), False),
        'zero_input_leakage_reference_resistor_demand_A_upper': display(reference_current, True),
        'maximum_detection_delay_s': None,
        'permit_accepted': False,
        'permit_scope': 'Output pullup, receiver and startup gating are uncaptured; the current datasheet removed the POR feature. No complete permit is implemented.',
        'reference_collapse_counterexample': {
            'VN_V': -8, 'REF_V': 2.2, 'comparator_supply_V': 5,
            'sense_nodes_V': {n: float(collapsed[n]) for n in ('SENSE','UV','OV')},
            'ideal_UV_healthy_margin_V': display(uv_margin, False),
            'ideal_OV_healthy_margin_V': display(ov_margin, False),
            'ideal_both_outputs_released': uv_margin > 0 and ov_margin > 0,
            'negative_rail_in_normal_band': number(bands[0]) <= 8 <= number(bands[1]),
            'scope': 'Forced nominal DC topology counterexample, not a claimed reachable trajectory. Independent reference validity is required even with valid comparator supply.'},
        'dynamic_native_bench': 'NOT RUN: incomplete monitor assembly and control circuit',
        'conditions': c, 'open_obligations': spec['open_obligations']}


def run(check=False, retained=False):
    spec = json.loads(SPEC.read_text()); validate(spec, retained)
    report = calculate(spec)
    paths = (SPEC, SOURCES, ROOT/spec['normal_voltage_source'], Path(__file__).resolve(),
             ROOT/'scripts/checks/rail_monitor_candidate.py')
    report['input_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    text = json.dumps(report, indent=2, allow_nan=False)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text() != text:
            raise ValueError('negative-monitor report drift')
    else:
        REPORT.write_text(text)
    print('PASS: conditional passive-network calculation only; permit NOT ACCEPTED')
    print('Retained PDFs: ' + ('PASS' if retained else 'NOT RUN (use --verify-retained)'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify-retained', action='store_true')
    args = parser.parse_args(); run(args.check, args.verify_retained)
