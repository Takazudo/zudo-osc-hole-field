"""Stage 1a of the accepted remedy (option D): draft electrical limits for every net the block move puts on a cable.

For each newly crossing net of the step 4 default boundary and the step 5b keep-front boundary (both classifications
pinned by hash), this finds the node type from the io-partition pin map, the node's source impedance, and the added
cable capacitance from the retained flat-link model (0.5 mm stock FFC, 80 mm long case, upper permittivity), and
evaluates DRAFT criteria built from retained OPA4196 facts and the retained coupling classes:

- op-amp output: total node capacitance (cable plus the follower's own input) at most an ASSUMED 100 pF; the
  datasheet guidance (fact-op-audio-capacitive-load-guidance) gives no safe threshold;
- input-side node: RC corner at or above 200 kHz (ASSUMED, 10 x the retained 20 kHz sine) and edge crosstalk at
  the node's source impedance within the victim class limit (ANALOGUE 10 mV, PRECISION 1 mV where the receiving
  op-amp unit carries a PRECISION net), with the shielding the cable would need;
- indicator LED bridge nets: inside the op-amp feedback loop, so they need a loop-stability criterion and an
  aggressor class, which are not drafted here (undetermined).

Input-side source impedance: a node driven by a protection switch drain (TMUX7412) is evaluated patched (an
ASSUMED 1 kΩ jack source plus the 15 Ω R_ON bound of fact-fault-switch-t-ron-12v-single) and unpatched (its
resistors to AGND), and the worse case is used; other nodes use the smallest resistor on the node, a lower bound.
The criteria are proposals for the independent reviewer, not accepted budgets. Paper only.

--source NAME=PATH (repeatable, MC04-S7 Revision 1) evaluates other crossing-net classifications instead of the two
pinned ones; each is recorded by its sha256 in the result. With no --source the pins are enforced as before."""
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
OPA4196 = 'OPA4196IDR'
OPA = {OPA4196, 'OPA4197IDR', 'OPA4197IPWR'}
SWITCH_PREFIX = ('TMUX', 'ADG')
RAILS = {'+12V', '-12V', '+5V', 'AGND'}
OUT_PINS, INV_PINS, NONINV_PINS = {'1', '7', '8', '14'}, {'2', '6', '9', '13'}, {'3', '5', '10', '12'}
FACTS = ROOT / '.claude/skills/component-ti-opa4196idr/facts.json'
JACK_SOURCE_OHM = 1000.0   # ASSUMED patched source impedance; no retained source states one
R_ON_OHM = 15.0            # fact-fault-switch-t-ron-12v-single bound (12 V single supply; extrapolated to +/-12 V)
LIMIT_OUT_F = 100e-12      # ASSUMED
LIMIT_CORNER_HZ = 200e3    # ASSUMED
CABLE = ('pitch_0_5', 80, 'A', 'adjacent')
SHIELDS = (('B', 'across_ground', 'ground on both sides'), ('C', 'across_two_grounds', 'two grounds on both sides'))


def facts():
    f = {x['fact_id']: x for x in json.loads(FACTS.read_text())['facts']}
    return {'input_cm_F': f['fact-op-audio-input-impedance']['value']['common_mode_pF'] * 1e-12,
            'gbw_Hz': f['fact-op-audio-gbw']['value']['typical'] * 1e6,
            'capacitive_load_guidance': f['fact-op-audio-capacitive-load-guidance']['value']}


def ohms(v):
    m = re.match(r'\s*([\d.]+(?:e[+-]?\d+)?)\s*(k|K|M|kohm|Mohm)?\s*(Ω|ohm)?\s*$', v or '')
    if not m:
        return None
    return float(m.group(1)) * {None: 1, 'k': 1e3, 'K': 1e3, 'kohm': 1e3, 'M': 1e6, 'Mohm': 1e6}[m.group(2)]


def values():
    out = {}
    for b in NETLISTS:
        text = (ROOT / ('schematic/boards/%s.net' % b)).read_text()
        for ref, val in re.findall(r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', text):
            out[ref] = val
    return out


def nets_sources(sources=None):
    """{case: (path, sha256, nets)}: the pinned classifications (hash enforced), or the given {case: path}."""
    out = {}
    if sources is None:
        for k, (p, h) in NETS.items():
            b = p.read_bytes()
            if hashlib.sha256(b).hexdigest() != h:
                raise ValueError('%s changed' % p)
            out[k] = (p, h, json.loads(b)['nets'])
    else:
        for k, p in sources.items():
            b = Path(p).read_bytes()
            out[k] = (Path(p), hashlib.sha256(b).hexdigest(), json.loads(b)['nets'])
    return out


def parse_sources(specs):
    if not specs:
        return None
    out = {}
    for x in specs:
        k, sep, p = x.partition('=')
        if not sep or not k or not p or k in out:
            raise ValueError('bad --source: ' + x)
        out[k] = Path(p)
    return out


def display(p):
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def run(sources=None):
    srcs = nets_sources(sources)
    nets = {k: v[2] for k, v in srcs.items()}
    fx = facts()
    inp = le.load_inputs()
    kinds = le.partition_kinds()
    rules = inp['classes']['rules']
    pk, length, rule, pair = CABLE
    eps = max(inp['cable']['eps_eff']['value'])
    par = le.pair_parameters(inp, pk, length, eps, rule, pair)
    shield_par = {g: le.pair_parameters(inp, pk, length, eps, g, gp) for g, gp, _ in SHIELDS}
    c_cable = par['Cv_total_F']
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    mpn = {x['ref']: x['mpn'] for x in part['physical_packages']}
    pins = collections.defaultdict(list)
    ref_pins = collections.defaultdict(dict)
    unit_nets = collections.defaultdict(set)
    unit_of = {}
    for u in part['package_units']:
        for p, n in (u.get('pins') or {}).items():
            if n:
                pins[n].append((u['ref'], p))
                ref_pins[u['ref']][p] = n
                unit_nets[(u['ref'], u['unit'])].add(n)
                unit_of[(u['ref'], p)] = (u['ref'], u['unit'])
    val = values()

    def r_of(ref):
        x = ohms(val.get(ref))
        if not x:
            raise ValueError('unparsed or zero-ohm resistor value %s %r' % (ref, val.get(ref)))
        return x

    def victim_class(n):
        reach = {n} | {m for ref, _ in pins[n] if ref[0] == 'R' and not ref.startswith('RV') for m in ref_pins[ref].values()} - RAILS
        cls = set()
        for m in reach:
            for ref, p in pins[m]:
                if mpn.get(ref) in OPA and (ref, p) in unit_of:
                    for un in unit_nets[unit_of[(ref, p)]]:
                        if un not in RAILS:
                            cls.add(le.classify(un, kinds, rules))
        return 'PRECISION' if 'PRECISION' in cls else 'ANALOGUE'

    def xtalk(src, cls):
        vic = {cls: dict(inp['victims'][cls], source_ohm=[src], nominal_index=0)}
        i2 = dict(inp, victims=vic)
        side = le.victim_peak(par, 'ANALOGUE', cls, i2)
        return side, {g: le.victim_peak(shield_par[g], 'ANALOGUE', cls, i2) for g, _, _ in SHIELDS}

    out = {}
    for case, rows in nets.items():
        res = []
        for r in rows:
            n = r['net']
            on = pins[n]
            ic = [(ref, p) for ref, p in on if mpn.get(ref) in OPA]
            sw = [(ref, p) for ref, p in on if mpn.get(ref, '').startswith(SWITCH_PREFIX)]
            rs = [(ref, r_of(ref)) for ref, _ in on if ref[0] == 'R' and not ref.startswith('RV')]
            own_c = sum(fx['input_cm_F'] for ref, p in ic if p in INV_PINS | NONINV_PINS and mpn[ref] == OPA4196)
            no_c = [('%s.%s' % x) for x in ic if x[1] in INV_PINS | NONINV_PINS and mpn[x[0]] != OPA4196]
            row = {'net': n, 'kind': r['kind'], 'from': r['from'], 'opa_pins': ['%s.%s' % x for x in ic],
                   'switch_pins': ['%s.%s' % x for x in sw], 'resistors_ohm': {a: b for a, b in rs},
                   'added_C_pF': round(c_cable * 1e12, 2), 'node_own_input_C_pF': round(own_c * 1e12, 2)}
            if no_c:
                row['input_C_not_retained_for'] = no_c
            if r['kind'] == 'indicator LED drive':
                row.update(node='indicator LED bridge net inside an op-amp feedback loop',
                           criterion='loop-stability criterion and aggressor class: not drafted', **{'pass': None})
            elif any(p in OUT_PINS for _, p in ic):
                tot = c_cable + own_c
                row.update(node='op-amp output (unity-gain follower)', node_total_C_pF=round(tot * 1e12, 2),
                           criterion='node total C <= 100 pF (ASSUMED)', **{'pass': tot <= LIMIT_OUT_F})
            else:
                cls = victim_class(n)
                if sw:
                    to_gnd = [x for ref, x in rs if 'AGND' in ref_pins[ref].values()]
                    unpatched = 1 / sum(1 / x for x in to_gnd) if to_gnd else None
                    cases = {'patched': JACK_SOURCE_OHM + R_ON_OHM}
                    if unpatched:
                        cases['unpatched'] = unpatched
                    row['node'] = 'protection-switch drain (input node)'
                else:
                    if not rs:
                        row.update(node='input-side node', criterion='source impedance unknown', **{'pass': None})
                        res.append(row)
                        continue
                    label = 'isolation-resistor source' if r['kind'] == 'isolation midpoint' else 'series-resistor lower bound'
                    cases = {label: min(x for _, x in rs)}
                    row['node'] = 'non-inverting input' if ic else 'passive-only node'
                evals = {}
                for name, src in cases.items():
                    side, sh = xtalk(src, cls)
                    corner = 1 / (2 * math.pi * src * (c_cable + own_c))
                    evals[name] = {'source_R_ohm': round(src, 1), 'corner_Hz': round(corner),
                                   'crosstalk_side_by_side_mV': round(side['edge_V'] * 1e3, 2),
                                   'crosstalk_20kHz_mV': round(side['sine_V'] * 1e3, 3),
                                   'crosstalk_shielded_mV': {g: round(v['edge_V'] * 1e3, 2) for g, v in sh.items()},
                                   'crosstalk_20kHz_shielded_mV': {g: round(v['sine_V'] * 1e3, 3) for g, v in sh.items()}}
                worst = max(evals, key=lambda k: evals[k]['crosstalk_side_by_side_mV'])
                lim = inp['victims'][cls]['limit_V'] * 1e3
                w = evals[worst]
                ok_bw = w['corner_Hz'] >= LIMIT_CORNER_HZ
                need = 'none' if w['crosstalk_side_by_side_mV'] <= lim and w['crosstalk_20kHz_mV'] <= lim else next(
                    (label for g, _, label in SHIELDS if w['crosstalk_shielded_mV'][g] <= lim and w['crosstalk_20kHz_shielded_mV'][g] <= lim),
                    'not met by any retained rule')
                row.update(victim_class=cls, limit_mV=lim, cases=evals, worst_case=worst, shielding_needed=need,
                           criterion='corner >= 200 kHz (ASSUMED) and edge crosstalk <= class limit',
                           **{'pass': ok_bw and need == 'none'})
            res.append(row)
        blocks = {x['net']: x['blocks'] for x in rows}
        per_ic = collections.defaultdict(collections.Counter)
        for x in res:
            v = x.get('pass')
            label = 'pass' if v else ('undetermined' if v is None else (
                'needs ' + x['shielding_needed'] if x.get('shielding_needed', '').startswith(('ground', 'two')) else 'FAIL'))
            for ic in blocks[x['net']]:
                per_ic[ic][label] += 1
        verdict = {}
        for ic, c in per_ic.items():
            shield = any(k.startswith('needs') for k in c)
            verdict[ic] = ('cannot move' if c.get('FAIL') else
                           'conditional: undetermined nets' + (', and shielding' if shield else '') if c.get('undetermined') else
                           'can move with shielding' if any(k.startswith('needs') for k in c) else 'can move')
        def outcome(x):
            if x.get('pass') is None:
                return 'undetermined'
            if x['pass']:
                return 'pass'
            return 'needs ' + x['shielding_needed'] if x.get('shielding_needed', '').startswith(('ground', 'two')) else 'FAIL'
        tally = collections.Counter((x['node'], outcome(x)) for x in res)
        out[case] = {'per_ic': {k: dict(v) for k, v in sorted(per_ic.items())},
                     'block_verdict': dict(sorted(verdict.items())),
                     'tally': {'%s %s' % k: v for k, v in sorted(tally.items())}, 'nets': res}
    return {'status': 'STAGE_1A_DRAFT_LIMITS', 'facts': {k: v for k, v in fx.items()},
            'fact_ids': ['fact-op-audio-gbw', 'fact-op-audio-input-impedance', 'fact-op-audio-capacitive-load-guidance',
                         'component-ti-tmux7412frrpr: fact-fault-switch-t-ron-12v-single'],
            'assumed': {'jack_source_ohm': JACK_SOURCE_OHM, 'r_on_ohm': R_ON_OHM, 'output_total_C_F': LIMIT_OUT_F,
                        'input_corner_Hz': LIMIT_CORNER_HZ,
                        'aggressor': 'retained ANALOGUE aggressor, 20 V at 20 V/us (OPA4196 slews 7.5/5.5 V/us typ)'},
            'cable_case': {'pitch': pk, 'length_mm': length, 'eps_eff': eps, 'ground_rule': rule,
                           'victim_C_total_pF': round(c_cable * 1e12, 2)},
            **({'sources': {k: {'path': display(v[0]), 'sha256': v[1]} for k, v in srcs.items()}}
               if sources is not None else {}),
            'cases': out,
            'scope': 'DRAFT criteria for independent review; first-order RC and the retained quasi-static cable model; '
                     'no inverting (feedback) node is among the crossings; no loop-gain simulation, no measured cable data; '
                     'not an acceptance.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--source', action='append', default=[], help='NAME=PATH of a crossing-net classification')
    a = ap.parse_args()
    text = json.dumps(run(parse_sources(a.source)), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
