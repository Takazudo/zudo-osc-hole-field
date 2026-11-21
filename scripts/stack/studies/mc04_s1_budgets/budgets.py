"""Stage 1a of the accepted remedy (option D): draft electrical limits for every net the block move puts on a cable.

For each newly crossing net of the step 4 default boundary and the step 5b keep-front boundary (both classifications
pinned by hash), this finds the node type from the netlist (OPA419x output, inverting input, non-inverting input,
or a passive-only node), the resistances on the node from the generated board netlists, and the added cable
capacitance from the retained flat-link model (0.5 mm stock FFC, 80 mm long case, upper permittivity, one ground
per two signals). It then evaluates three DRAFT criteria built from sourced OPA4196 facts (SBOS869, sha256
c68223d5..., GBW 2.5 MHz, input capacitance 6.4 pF common-mode, unity-gain ringing below 100 pF when lightly loaded)
and the retained ANALOGUE coupling limit:

- output node: added capacitance at most 100 pF;
- inverting (feedback) node: the pole of the node resistance and the added capacitance at or above the 2.5 MHz GBW;
- non-inverting or passive node: the RC corner at or above 200 kHz (10 x the retained 20 kHz sine), and the
  side-by-side ANALOGUE edge crosstalk at the node's own source resistance within the 10 mV ANALOGUE limit.

The criteria are proposals for the independent reviewer, not accepted budgets. Paper only."""
import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/link_electrical'))
import link_electrical as le  # noqa: E402

S = ROOT / 'scripts/stack/studies'
NETS = {'default_one_hop': (S / 'mc04_c5_crossing_nets/result.json',
                            '29879937886fb3c15ed0ac379bd557a285b43eb8747b0c6ff34467be27576a5d'),
        'keep_protection_and_isolation_front': (S / 'mc04_c5b_keep_front_pairs/nets-protect-iso.json',
                                                '62b178e9f94c2fa5a4ef869d46a2d8a750a04744382d39d32f63910c0a26e675')}
NETLISTS = ('osc-jack-left', 'osc-jack-right', 'osc-core')
OPA = {'OPA4196IDR', 'OPA4197IDR', 'OPA4197IPWR'}
OUT_PINS, INV_PINS, NONINV_PINS = {'1', '7', '8', '14'}, {'2', '6', '9', '13'}, {'3', '5', '10', '12'}
SOURCED = {'datasheet': 'TI SBOS869 (July 2017, addendum 15-Oct-2026), sha256 c68223d51715ef65baa6a8f549278f2f451365ccc3b95864c0d815c8797d5fde',
           'gbw_Hz': 2.5e6, 'input_cm_F': 6.4e-12, 'ringing_note_F': 100e-12}
LIMIT_OUT_F = 100e-12
LIMIT_POLE_HZ = 2.5e6
LIMIT_CORNER_HZ = 200e3
CABLE = ('pitch_0_5', 80, 'A', 'adjacent')


def values():
    out = {}
    for b in NETLISTS:
        text = (ROOT / ('schematic/boards/%s.net' % b)).read_text()
        for ref, val in re.findall(r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', text):
            out[ref] = val
    return out


def ohms(v):
    m = re.match(r'\s*([\d.]+)\s*([kKM]?)\s*Ω', v or '')
    if not m:
        return None
    return float(m.group(1)) * {'': 1, 'k': 1e3, 'K': 1e3, 'M': 1e6}[m.group(2)]


def run():
    nets = {}
    for k, (p, h) in NETS.items():
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() != h:
            raise ValueError('%s changed' % p)
        nets[k] = json.loads(b)['nets']
    inp = le.load_inputs()
    pk, length, rule, pair = CABLE
    eps = max(inp['cable']['eps_eff']['value'])
    par = le.pair_parameters(inp, pk, length, eps, rule, pair)
    c_cable = par['Cv_total_F']
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    mpn = {x['ref']: x['mpn'] for x in part['physical_packages']}
    pins = collections.defaultdict(list)
    for u in part['package_units']:
        for p, n in (u.get('pins') or {}).items():
            if n:
                pins[n].append((u['ref'], p))
    val = values()
    out = {}
    for case, rows in nets.items():
        res = []
        for r in rows:
            n = r['net']
            on = pins[n]
            ic = [(ref, p) for ref, p in on if mpn.get(ref) in OPA]
            rs = [ohms(val.get(ref)) for ref, _ in on if ref[0] == 'R' and not ref.startswith('RV')]
            rs = [x for x in rs if x]
            c_add = c_cable + SOURCED['input_cm_F'] * sum(1 for _, p in ic if p in INV_PINS | NONINV_PINS)
            row = {'net': n, 'kind': r['kind'], 'from': r['from'], 'opa_pins': ['%s.%s' % x for x in ic],
                   'resistors_ohm': sorted(rs), 'added_C_pF': round(c_add * 1e12, 2)}
            if any(p in OUT_PINS for _, p in ic):
                row['node'] = 'op-amp output'
                row['criterion'] = 'added C <= 100 pF'
                row['pass'] = c_add <= LIMIT_OUT_F
            elif any(p in INV_PINS for _, p in ic):
                req = 1 / sum(1 / x for x in rs) if rs else None
                row['node'] = 'inverting (feedback) input'
                if req is None:
                    row.update(criterion='pole >= 2.5 MHz', note='no resistor on node', **{'pass': None})
                else:
                    f = 1 / (2 * math.pi * req * c_add)
                    row.update(node_R_ohm=round(req, 1), pole_Hz=round(f), criterion='pole >= 2.5 MHz', **{'pass': f >= LIMIT_POLE_HZ})
            else:
                row['node'] = 'non-inverting input' if ic else 'passive-only node'
                src = min(rs) if rs else None
                if src is None:
                    row.update(criterion='corner >= 200 kHz and crosstalk <= 10 mV', note='no resistor on node', **{'pass': None})
                else:
                    corner = 1 / (2 * math.pi * src * c_add)
                    vic = {'ANALOGUE': dict(inp['victims']['ANALOGUE'], source_ohm=[src], nominal_index=0)}
                    xt = le.victim_peak(par, 'ANALOGUE', 'ANALOGUE', dict(inp, victims=vic))
                    shielded = {}
                    for g, gp in (('A', 'across_ground'), ('B', 'across_ground'), ('C', 'across_two_grounds')):
                        gpar = le.pair_parameters(inp, pk, length, eps, g, gp)
                        shielded[g] = round(le.victim_peak(gpar, 'ANALOGUE', 'ANALOGUE', dict(inp, victims=vic))['edge_V'] * 1e3, 2)
                    row.update(source_R_ohm=src, corner_Hz=round(corner), crosstalk_edge_mV=round(xt['edge_V'] * 1e3, 2),
                               crosstalk_edge_mV_with_grounds=shielded,
                               crosstalk_20kHz_mV=round(xt['sine_V'] * 1e3, 3),
                               criterion='corner >= 200 kHz and crosstalk <= 10 mV',
                               **{'pass': corner >= LIMIT_CORNER_HZ and xt['edge_V'] <= inp['victims']['ANALOGUE']['limit_V']})
            res.append(row)
        tally = collections.Counter((x['node'], {True: 'pass', False: 'FAIL', None: 'undetermined'}[x.get('pass')]) for x in res)
        mit = collections.Counter()
        for x in res:
            if x.get('pass') is False and 'crosstalk_edge_mV_with_grounds' in x:
                ok = [g for g, v in x['crosstalk_edge_mV_with_grounds'].items() if v <= inp['victims']['ANALOGUE']['limit_V'] * 1e3]
                mit[ok[0] if ok else 'none'] += 1
        blocks = {n['net']: n['blocks'] for n in nets[case]}
        per_ic = collections.defaultdict(collections.Counter)
        for x in res:
            v = x.get('pass')
            if v is False and x.get('crosstalk_edge_mV_with_grounds', {}).get('A', 1e9) <= inp['victims']['ANALOGUE']['limit_V'] * 1e3:
                v = 'meets with rule A ground between'
            for ic in blocks[x['net']]:
                per_ic[ic][{True: 'pass', False: 'FAIL', None: 'undetermined'}.get(v, v)] += 1
        out[case] = {'per_ic': {k: dict(v) for k, v in sorted(per_ic.items())}, 'nets': res, 'first_ground_rule_meeting_10mV': dict(mit), 'tally': {'%s %s' % k: v for k, v in sorted(tally.items())},
                     'fail': sorted(x['net'] for x in res if x.get('pass') is False)}
    return {'status': 'STAGE_1A_DRAFT_LIMITS', 'sourced': SOURCED,
            'cable_case': {'pitch': pk, 'length_mm': length, 'eps_eff': eps, 'ground_rule': rule,
                           'victim_C_total_pF': round(c_cable * 1e12, 2)},
            'draft_criteria': {'output_added_C_F': LIMIT_OUT_F, 'feedback_pole_Hz': LIMIT_POLE_HZ,
                               'input_corner_Hz': LIMIT_CORNER_HZ, 'crosstalk_V': inp['victims']['ANALOGUE']['limit_V']},
            'cases': out,
            'scope': 'DRAFT criteria for independent review; first-order RC and the retained quasi-static cable model only; '
                     'no loop-gain simulation, no measured cable data; not an acceptance.'}


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
