"""Task C step 5c: function-boundary comparison for the 26 unplaced ICs, with the unresolved electrical budgets.

For each IC, joins the retained step 4 combined packing (default one-hop boundary) and the step 5b variant that
keeps protection and isolation parts on the front board (both pinned by hash) with the step 5a / 5b crossing-net
classifications: the IC shift, the farthest block member, the nets each boundary would put on the cable, the
front-board endpoints those nets reach, the module test file that guards the function and the briefs that own it.
Every electrical budget is listed as UNRESOLVED: none is sourced, and none may be invented here (MC02 analog brief).
Paper only: no allocation, no electrical acceptance, no canonical write."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S = ROOT / 'scripts/stack/studies'
INPUTS = {
    'default_blocks': (S / 'mc04_c4_blocks/result.json', 'be96eff6fb4a5fc4e047b2c4d109fa8dd87b0bf7a4b3927fc3069233cb8fcab3'),
    'default_nets': (S / 'mc04_c5_crossing_nets/result.json', '29879937886fb3c15ed0ac379bd557a285b43eb8747b0c6ff34467be27576a5d'),
    'keep_blocks': (S / 'mc04_c5b_keep_front_pairs/result-protect-iso.json', '9197e4e7b7e433c7762f47e7060627c1f2134f268deb307b3ab160c93f3403d6'),
    'keep_nets': (S / 'mc04_c5b_keep_front_pairs/nets-protect-iso.json', '62b178e9f94c2fa5a4ef869d46a2d8a750a04744382d39d32f63910c0a26e675'),
}
BRIEFS = 'circuit/orchestration/campaigns/osc-stack-20261114/'
TESTS = (('oscillator', 'design/spec/modules/test_oscillator.py'), ('filter', 'design/spec/modules/test_filter.py'),
         ('envelope', 'design/spec/modules/test_envelope.py'), ('wavefolder', 'design/spec/modules/test_wavefolder.py'),
         ('mix4', 'design/spec/modules/test_mixers.py'))
ANALOG_BUDGETS = ('added trace length', 'via count', 'added R/L/C', 'feedback phase margin', 'summed error and noise',
                  'output-load envelope', 'thermal margin', 'mounted service envelope')
LOGIC_BUDGETS = ('added trace and via', 'propagation delay', 'clock skew', 'setup and hold', 'synchronizer reliability')
PRECISION_BUDGETS = ('share of the 4.166667 mV tracking budget', 'added feedback R/C', 'storage leakage and droop',
                     'injection and contamination limits')


def load():
    out = {}
    for k, (p, h) in INPUTS.items():
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() != h:
            raise ValueError('%s changed' % p)
        out[k] = json.loads(b)
    return out


def rows_by_ic(blocks, nets):
    by = {}
    for c in blocks['all_on_K_together']:
        for b in c['blocks']:
            by[b['ic']] = {'from': c['from'], 'members': b['members'], 'ic_shift_mm': b['ic_shift_mm'],
                           'max_member_distance_mm': b['max_member_distance_mm'], 'crossing': []}
    for n in nets['nets']:
        for ic in n['blocks']:
            by[ic]['crossing'].append({'net': n['net'], 'kind': n['kind'], 'front_endpoints': n['staying_refs']})
    return by


def run():
    d = load()
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    pp = {x['ref']: x for x in part['physical_packages']}
    a, b = rows_by_ic(d['default_blocks'], d['default_nets']), rows_by_ic(d['keep_blocks'], d['keep_nets'])
    rows = []
    for ic in sorted(a, key=lambda r: (a[r]['from'], r)):
        x = pp[ic]
        mpn = x['mpn']
        if mpn == 'OPA4196IDR':
            budgets, brief = ANALOG_BUDGETS, 'mc02-analog-function-remedy-brief-20261117.md'
        elif ic in ('U1518', 'U4341'):
            budgets, brief = PRECISION_BUDGETS, 'mc02-%s-remedy-brief-20261117.md' % ic.lower()
        else:
            budgets, brief = LOGIC_BUDGETS, 'mc02-logic-function-remedy-brief-20261117.md'
        tests = [t for f, t in TESTS if x['family'].startswith(f)]
        rows.append({'ic': ic, 'board': a[ic]['from'], 'instance': x['instance'], 'family': x['family'], 'mpn': mpn,
                     'moves_to': 'K', 'ic_shift_mm': a[ic]['ic_shift_mm'], 'beyond_25mm': a[ic]['ic_shift_mm'] > 25,
                     'boundaries': {
                         'default_one_hop': {'members': a[ic]['members'], 'max_member_distance_mm': a[ic]['max_member_distance_mm'],
                                             'new_crossing_nets': a[ic]['crossing']},
                         'keep_protection_and_isolation_front': {
                             'members': b[ic]['members'], 'max_member_distance_mm': b[ic]['max_member_distance_mm'],
                             'new_crossing_nets': b[ic]['crossing']}},
                     'guarding_tests': tests, 'owning_brief': BRIEFS + brief,
                     'unresolved_budgets': list(budgets)})
    return {'status': 'TASK_C_STEP_5C_FUNCTION_BOUNDARIES', 'inputs': {k: v[1] for k, v in INPUTS.items()},
            'ics': rows, 'count': len(rows), 'beyond_25mm': [r['ic'] for r in rows if r['beyond_25mm']],
            'budgets_resolved': 0,
            'scope': 'Paper comparison only. Every budget is UNRESOLVED: no source assigns one and none is invented. '
                     'Crossing nets are per block on the cable, before any allocation; K-internal moves add no crossing '
                     'but lengthen runs. Not a stability model, not an approved relocation set.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    o = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if o.output:
        with o.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
