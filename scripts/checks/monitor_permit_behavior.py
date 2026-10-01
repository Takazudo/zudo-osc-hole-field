#!/usr/bin/env python3
"""Conditional behavioral diagnostics, never a device or qualification model."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'design/power/monitor-permit-draft.json'
REPORT = ROOT / 'design/power/monitor-permit-behavior-report.json'


EXPECTED_TOPOLOGY = {'U101': {'kind': 'ic',
          'pins': {'1': '+5V',
                   '2': 'REF_SENSE',
                   '3': None,
                   '4': 'AGND',
                   '5': 'P12_SENSE',
                   '6': 'P5_SENSE',
                   '7': 'FAULT_N',
                   '8': 'FAULT_N'}},
 'U102': {'kind': 'ic',
          'pins': {'1': 'REF_SENSE',
                   '2': 'SENSE',
                   '3': 'UV',
                   '4': 'AGND',
                   '5': 'SENSE',
                   '6': 'OV',
                   '7': 'REF_SENSE',
                   '8': '+5V'}},
 'U103': {'kind': 'ic',
          'pins': {'1': None, '2': 'AGND', '3': None, '4': '+5V', '5': None, '6': 'REF'}},
 'U104': {'kind': 'ic',
          'pins': {'1': 'FAULT_N',
                   '2': 'BAD_FAST',
                   '3': 'BAD_FAST',
                   '4': 'GOOD_FAST',
                   '5': 'DELAY_IN',
                   '6': 'DELAY_INV',
                   '7': 'AGND',
                   '8': 'PERMIT_CLK',
                   '9': 'DELAY_INV',
                   '10': None,
                   '11': 'AGND',
                   '12': None,
                   '13': 'AGND',
                   '14': '+5V'}},
 'U105': {'kind': 'ic',
          'pins': {'1': 'GOOD_FAST',
                   '2': '+5V',
                   '3': 'PERMIT_CLK',
                   '4': '+5V',
                   '5': 'PERMIT_Q',
                   '6': None,
                   '7': 'AGND',
                   '8': None,
                   '9': None,
                   '10': '+5V',
                   '11': 'AGND',
                   '12': 'AGND',
                   '13': 'AGND',
                   '14': '+5V'}},
 'Q101': {'kind': 'npn', 'pins': {'1': 'BASE', '2': 'AGND', '3': 'PERMIT_SINK'}},
 'R101': {'kind': 'resistor', 'pins': {'1': 'VN', '2': 'SENSE'}},
 'R102': {'kind': 'resistor', 'pins': {'1': 'REF', '2': 'SENSE'}},
 'R103': {'kind': 'resistor', 'pins': {'1': 'SENSE', '2': 'AGND'}},
 'R104': {'kind': 'resistor', 'pins': {'1': 'REF', '2': 'AGND'}},
 'R105': {'kind': 'resistor', 'pins': {'1': 'REF', '2': 'UV'}},
 'R106': {'kind': 'resistor', 'pins': {'1': 'UV', '2': 'AGND'}},
 'R107': {'kind': 'resistor', 'pins': {'1': 'REF', '2': 'OV'}},
 'R108': {'kind': 'resistor', 'pins': {'1': 'OV', '2': 'AGND'}},
 'R109': {'kind': 'resistor', 'pins': {'1': 'REF', '2': 'REF_D1'}},
 'R110': {'kind': 'resistor', 'pins': {'1': 'REF_D1', '2': 'REF_D2'}},
 'R111': {'kind': 'resistor', 'pins': {'1': 'REF_D2', '2': 'REF_D3'}},
 'R112': {'kind': 'resistor', 'pins': {'1': 'REF_D3', '2': 'REF_SENSE'}},
 'R113': {'kind': 'resistor', 'pins': {'1': 'REF_SENSE', '2': 'AGND'}},
 'R114': {'kind': 'resistor', 'pins': {'1': '+12V', '2': 'P12_SENSE'}},
 'R115': {'kind': 'resistor', 'pins': {'1': 'P12_SENSE', '2': 'AGND'}},
 'R116': {'kind': 'resistor', 'pins': {'1': '+5V', '2': 'P5_TOP'}},
 'R117': {'kind': 'resistor', 'pins': {'1': 'P5_TOP', '2': 'P5_SENSE'}},
 'R118': {'kind': 'resistor', 'pins': {'1': 'P5_SENSE', '2': 'AGND'}},
 'R119': {'kind': 'resistor', 'pins': {'1': '+5V', '2': 'FAULT_N'}},
 'R120': {'kind': 'resistor', 'pins': {'1': 'GOOD_FAST', '2': 'DELAY_CAP'}},
 'R121': {'kind': 'resistor', 'pins': {'1': 'DELAY_CAP', '2': 'DELAY_IN'}},
 'R122': {'kind': 'resistor', 'pins': {'1': 'PERMIT_Q', '2': 'BASE'}},
 'R123': {'kind': 'resistor', 'pins': {'1': 'BASE', '2': 'AGND'}},
 'R124': {'kind': 'resistor', 'pins': {'1': '+12V', '2': 'PERMIT_SINK'}},
 'C101': {'kind': 'capacitor', 'pins': {'1': '+5V', '2': 'AGND'}},
 'C102': {'kind': 'capacitor', 'pins': {'1': '+5V', '2': 'AGND'}},
 'C103': {'kind': 'capacitor', 'pins': {'1': '+5V', '2': 'AGND'}},
 'C104': {'kind': 'capacitor', 'pins': {'1': 'REF', '2': 'AGND'}},
 'C105': {'kind': 'capacitor', 'pins': {'1': 'REF', '2': 'AGND'}},
 'C106': {'kind': 'capacitor', 'pins': {'1': 'REF', '2': 'AGND'}},
 'C107': {'kind': 'capacitor', 'pins': {'1': '+5V', '2': 'AGND'}},
 'C108': {'kind': 'capacitor', 'pins': {'1': '+5V', '2': 'AGND'}},
 'C109': {'kind': 'capacitor', 'pins': {'1': 'DELAY_CAP', '2': 'AGND'}}}


def latch_trace(segments, tau, high, low):
    """Exact single-pole RC between piecewise constant ideal GOOD_FAST levels.

    Input capacitance, gate propagation, reset pulse restrictions and device
    power dynamics are excluded. None of this bounds actual turn-off time.
    None means control power undefined; no powered-off LOW is invented.
    """
    cap, clock, q = 0.0, False, None
    result = []
    for duration, good in segments:
        if duration <= 0:
            raise ValueError('positive segment duration required')
        if good is None:
            q = None
            result.append({'duration_s': duration, 'good': None, 'q': None,
                           'capacitor_fraction': None, 'clock': None})
            # Retained state after undefined power cannot be predicted.
            cap, clock = None, None
            continue
        if cap is None:
            result.append({'duration_s': duration, 'good': good, 'q': None,
                           'capacitor_fraction': None, 'clock': None})
            continue
        if not good:
            q = False
        end = float(good) + (cap - float(good)) * math.exp(-duration / tau)
        if good and not clock and end >= high:
            clock, q = True, True
        elif not good and clock and end <= low:
            clock = False
        cap = end
        result.append({'duration_s': duration, 'good': good, 'q': q,
                       'capacitor_fraction': cap, 'clock': clock})
    return result


def build(spec):
    if spec['qualification_accepted'] or spec['canonical_protection_implemented']:
        raise ValueError('unselected study cannot promote qualification')
    parts = {p['ref']: p for p in spec['components']}
    actual = {p['ref']:{'kind':p['kind'],'pins':p['pins']} for p in spec['components']}
    if len(parts) != len(spec['components']) or actual != EXPECTED_TOPOLOGY:
        raise ValueError('captured topology differs from behavioral equations')
    def r(ref):
        value = parts[ref]['value']
        if value <= 0 or not math.isfinite(value):
            raise ValueError('invalid component value')
        return value
    m = spec['model_conditions']
    high, low = m['schmitt_high_fraction'], m['schmitt_low_fraction']
    if not 0 < low < high < 1:
        raise ValueError('invalid Schmitt thresholds')
    tau = r('R120') * r('C109')
    cases = {}
    rails = ('+12V','VN','+5V')
    for order in itertools.permutations(rails):
        for direction in ('arrival','failure'):
            state = {rail:direction=='failure' for rail in rails}
            states = [dict(state)]
            for rail in order:
                state[rail] = direction=='arrival'
                states.append(dict(state))
            # Failure begins with a reset and successful arm, then each
            # recorded rail transition drives the ideal powered monitor.
            seq = ([(0.02,False)] if direction=='failure' else [])
            seq += [(0.02,all(state.values())) for state in states]
            cases[direction+':'+','.join(order)] = {
                'rail_order':list(order), 'rail_states':states,
                'ideal_powered_trace':latch_trace(seq,tau,high,low),
                'actual_control_power_absent':'UNKNOWN',
                'scope':'Boolean sequencing only; no rail ramp or monitor propagation simulation'}
    for name, duration in [('short_good_fast_low',tau/100),('long_good_fast_low',tau*10)]:
        cases[name] = latch_trace([(0.02,False),(0.02,True),(duration,False),(0.02,True)],tau,high,low)
    cases['control_power_loss'] = latch_trace([(0.02,False),(0.02,True),(0.02,None),(0.02,True)],tau,high,low)
    # Nominal resistor-only nodal calculation; no tolerance/leakage claim.
    ref, vn, p5, p12 = 3.3, -12.0, 5.0, 12.0
    sense = (vn/r('R101') + ref/r('R102')) / (1/r('R101')+1/r('R102')+1/r('R103'))
    ref_load = ((ref-sense)/r('R102') + ref/r('R104')
                + ref/(r('R105')+r('R106')) + ref/(r('R107')+r('R108'))
                + ref/sum(r('R'+str(i)) for i in range(109,114)))
    ledger = {
        'scope': 'Nominal resistor currents with both TLV drains released; not a maximum or total supply-current budget',
        'reference_output_A': ref_load,
        'negative_rail_sink_A': (sense-vn)/r('R101'),
        'positive_12_divider_A': p12/(r('R114')+r('R115')),
        'positive_5_divider_A': p5/sum(r('R'+str(i)) for i in range(116,119)),
        'fault_pullup_low_A': p5/r('R119'),
        'base_drive_zero_junction_drop_A': p5/r('R122'),
        'dummy_load_zero_saturation_drop_A': p12/r('R124'),
        'timing_charge_C': r('C109')*p5,
        'nominal_5V_bypass_charge_C': sum(p['value']*p5 for p in parts.values()
             if p['kind']=='capacitor' and p['pins']['1']=='+5V'),
        'nominal_reference_bypass_charge_C': sum(p['value']*ref for p in parts.values()
             if p['kind']=='capacitor' and p['pins']['1']=='REF'),
        'unaccounted': ['All active-device quiescent and dynamic supply currents',
                        'Reference input current includes its output load plus regulator quiescent current; no free reference supply',
                        'HC slow-input dynamic current, reference startup and both retained RC clamp-return paths',
                        'Tolerance, temperature, effective capacitance and leakage',
                        'Actual isolation population and driver loads'],
        'total_supply_current_A': None,
        'original_auxiliary_allowances_removed': False,
        'original_current_limits_changed': False,
    }
    return {
        'status':'CONDITIONAL IDEAL BEHAVIOR DIAGNOSTICS; NOT QUALIFICATION',
        'qualification_accepted':False,
        'evaluated_input_sha256':hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'model_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'model_limits':['Ideal monitor truth values, no comparator/reference/supervisor dynamics',
            'GOOD_FAST low pulse durations are forced after the monitor; they are not external negative-fault durations',
            'Single-pole RC excludes R121/input capacitance and all device propagation',
            'No transistor model or guaranteed physical output release',
            'Actual partial-power and retained-charge behavior remain UNKNOWN'],
        'nominal_rc_s':tau,
        'ideal_charge_to_clock_s':-tau*math.log(1-high),
        'ideal_discharge_to_clock_low_s':-tau*math.log(low),
        'cases':cases,'nominal_partial_current_ledger':ledger,
        'physical_release_bound_s':None,
    }


def run(check=False):
    text=json.dumps(build(json.loads(SPEC.read_text())),indent=2)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:
            raise ValueError('behavior report drift')
    else:
        REPORT.write_text(text)
    print('PASS: conditional behavioral report reproduced; physical qualification OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
