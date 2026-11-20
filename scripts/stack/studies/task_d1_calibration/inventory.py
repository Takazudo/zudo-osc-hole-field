"""Task D step 1: a calibration-procedure inventory for all 104 K-board adjustments and probe pads.

Joins the ST-07 relocation plan (pinned by hash) with the io-partition unit/pin map. For every record it derives,
from source connectivity only: the adjusted nets, the one-hop parts on them, a topological class (how the trim
touches the circuit), the module procedure group, and the access state after the FFC projection. The per-role
procedure text (stimulus, observation, order) is a PROPOSAL for the design reviewer: the retained sources supply
only the electrical standard's calibration object, which this file cites; no other target is invented.
Paper only: no placement, routing, access or measurement claim."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PLAN = ROOT / 'design/stack/trimmers/relocation-plan.json'
PLAN_SHA = '56ce0dac92688e2a1d7a2844a8a56b1c122c04e92bd03a3db4463600d20075dd'
STD = ROOT / 'design/standard/electrical-standard.json'
RAILS = {'+12V', '-12V', '+5V', 'AGND'}

# Sourced targets: electrical-standard.json "calibration". Anything else is UNRESOLVED.
STD_PITCH = 'electrical-standard calibration.pitch_tracking_target_cents = 5 over 0..5 V at 25 C after 20 min warm-up'
STD_OCTAVE = 'electrical-standard calibration.octave_step_error_V = 0.002'

# role -> (group, order within group, proposed stimulus and observation, sourced target or None)
ROLES = {
    'octave_reference:RV_GAIN': ('octave reference', 1, 'Measure the octave reference steps with the instrument warm; set the ladder gain.', STD_OCTAVE),
    'oscillator:HF_TRIM': ('oscillator', 1, 'Drive high pitch CV; set high-frequency tracking against a counter at the oscillator output.', STD_PITCH),
    'oscillator:SCALE_TRIM': ('oscillator', 2, 'Step pitch CV 0 V to 5 V in 1 V steps; set the octave ratio at the oscillator output.', STD_PITCH),
    'oscillator:RZ_TRIM': ('oscillator', 3, 'Repeat the octave steps; set the scale-pin resistance element (RZ) as the circuit designer specifies.', STD_PITCH),
    'oscillator:BASE_TRIM': ('oscillator', 4, 'At 0 V pitch CV, set the base frequency at the oscillator output.', None),
    'oscillator:SINE_SYMMETRY': ('oscillator', 5, 'At a mid frequency, null sine asymmetry at the sine output.', None),
    'oscillator:SINE_LEVEL': ('oscillator', 6, 'Set the sine output peak level.', None),
    'filter:EXPO_BASE_TRIM': ('filter', 1, 'At 0 V frequency CV, set the cutoff reference.', None),
    'filter:EXPO_SCALE_TRIM': ('filter', 2, 'Step frequency CV; set the exponential scale (self-oscillation or a swept response).', None),
    'filter:LP_OFFSET': ('filter', 3, 'No input; null the LP output DC offset.', None),
    'filter:BP_OFFSET': ('filter', 3, 'No input; null the BP output DC offset.', None),
    'filter:RES_OFFSET': ('filter', 3, 'No input; null the resonance path offset.', None),
    'filter:DRY_OFFSET': ('filter', 3, 'No input; null the dry VCA path offset.', None),
    'filter:RESONANCE_MAX': ('filter', 4, 'At full resonance, set the onset of self-oscillation.', None),
    'envelope:RISE_OFFSET': ('envelope', 1, 'Null the rise exponential-converter offset.', None),
    'envelope:FALL_OFFSET': ('envelope', 1, 'Null the fall exponential-converter offset.', None),
    'envelope:RISE_BASE': ('envelope', 2, 'Set the rise time reference at a fixed control setting.', None),
    'envelope:FALL_BASE': ('envelope', 2, 'Set the fall time reference at a fixed control setting.', None),
    'envelope:RISE_SCALE': ('envelope', 3, 'Set the rise time-per-volt scale across two control settings.', None),
    'envelope:FALL_SCALE': ('envelope', 3, 'Set the fall time-per-volt scale across two control settings.', None),
    'wavefolder:OTA_OFFSET': ('wavefolder', 1, 'No input; null OTA control feedthrough at the output.', None),
    'wavefolder:PRE_GAIN_MAX': ('wavefolder', 2, 'At full drive, set the maximum pre-gain.', None),
    'mix4_vca:FEEDTHROUGH': ('mix4 VCA', 1, 'No input, command swept; null control feedthrough at the mix output.', None),
    'mix4_vca:TIA_CAL': ('mix4 VCA', 2, 'With a known input and full command, set the VCA gain at the mix output.', None),
    'noise:WHITE_LEVEL_TRIM': ('noise', 1, 'Set white noise output level (RMS meter).', None),
    'noise:PINK_LEVEL_TRIM': ('noise', 1, 'Set pink noise output level (RMS meter).', None),
    'noise:BLUE_LEVEL_TRIM': ('noise', 1, 'Set blue noise output level (RMS meter).', None),
    'noise:BROWN_LEVEL_TRIM': ('noise', 1, 'Set brown noise output level (RMS meter).', None),
    'power:Bare copper rail probe pad': ('power', 0, 'Probe the rail with the instrument powered, before any trim.', None),
}


def topology(ref, pins, netmap, roles):
    """How the part touches the circuit, from one-hop connectivity only."""
    hops = {n: [(r, p, roles[r]) for r, p, _ in netmap[n] if r != ref] for n in set(pins.values()) if n not in RAILS}
    on = [x for n in hops for x in hops[n]]
    if not hops:
        return 'rail probe', hops
    if any(r.startswith('Q') for r, _, _ in on):
        return 'exponential-pair reference node', hops
    if any('CORE' in role for _, _, role in on):
        return 'oscillator core pin', hops
    if any('REF5' in n for n in pins.values()) and any('REFN5' in n for n in pins.values()):
        return 'reference divider; wiper isolated by a feed resistor', hops
    amp_in = [x for x in on if x[0].startswith('U')]
    if amp_in:
        return 'rheostat at an amplifier input or feedback node', hops
    return 'rheostat to ground through a fixed resistor', hops


def run():
    raw = PLAN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PLAN_SHA:
        raise ValueError('relocation plan changed')
    plan = json.loads(raw)
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    std = json.loads(STD.read_text())['calibration']
    pp = {x['ref']: x for x in part['physical_packages']}
    netmap, pins_of, roles = collections.defaultdict(list), collections.defaultdict(dict), {}
    for u in part['package_units']:
        roles[u['ref']] = u['role'].split(':')[-1]
        for p, n in (u.get('pins') or {}).items():
            if n:
                netmap[n].append((u['ref'], p, u['role']))
                pins_of[u['ref']][p] = n
    rows = []
    for r in plan['records']:
        group, order, proc, target = ROLES[r['role']]
        cls, hops = topology(r['ref'], pins_of[r['ref']], netmap, roles)
        face = r['after_link_projection']['face']
        if r['proposal']:
            access = 'rear candidate %.2f mm from projected position (unreviewed)' % r['proposal']['distance_mm']
        elif face == 'B':
            access = 'rear, kept (tool access unmeasured)'
        else:
            access = 'front, blocked in the closed stack, no candidate'
        rows.append({'ref': r['ref'], 'module': r['module'], 'role': r['role'], 'mpn': pp[r['ref']]['mpn'],
                     'pins': pins_of[r['ref']], 'one_hop': {n: ['%s.%s %s' % x for x in v] for n, v in hops.items()},
                     'topology': cls, 'group': group, 'order': order, 'proposed_procedure': proc,
                     'sourced_target': target or 'UNRESOLVED', 'access_after_projection': access,
                     'plan_verdict': r['verdict']})
    rows.sort(key=lambda x: (x['group'], x['module'], x['order'], x['ref']))
    c = collections.Counter
    return {'status': 'TASK_D_STEP_1_CALIBRATION_INVENTORY', 'plan_sha256': PLAN_SHA,
            'standard_calibration': std, 'records': rows, 'count': len(rows),
            'by_topology': dict(c(x['topology'] for x in rows)),
            'by_access': dict(c(x['access_after_projection'].split(' (')[0].split(' %')[0] if not x['access_after_projection'].startswith('rear candidate') else 'rear candidate' for x in rows)),
            'with_sourced_target': sum(x['sourced_target'] != 'UNRESOLVED' for x in rows),
            'scope': 'Source connectivity and the electrical standard only. Procedure text and order are proposals for '
                     'the design reviewer; access is the unreviewed ST-07 courtyard screen; no tool access, loop, '
                     'guard, measurement or acceptance claim.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
