"""ST-04 attempt a2: coupling and ground-current bounds for a flat link (paper; DS-41 checks 3 and 4).

  python3 scripts/stack/link_electrical/link_electrical.py           write results.json and README.md
  python3 scripts/stack/link_electrical/link_electrical.py --check   exit 1 if the retained files differ

Everything is a quasi-static paper bound from design/stack/link-electrical/inputs.json. Nothing here is a
measured coupling, current share or resistance.
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stack/power_posts'))
sys.path.insert(0, str(HERE))
import power_posts as pp  # noqa: E402

OUT = ROOT / 'design/stack/link-electrical'
INPUTS = OUT / 'inputs.json'
MU0 = 4e-7 * math.pi
EPS0 = 8.8541878128e-12
PITCHES = ('pitch_1_0', 'pitch_0_5')
PITCH_LABEL = {'pitch_1_0': '1.00 mm', 'pitch_0_5': '0.5 mm'}
AGGRESSORS = ('LOGIC', 'ANALOGUE')
VICTIMS = ('PRECISION', 'WIPER', 'ANALOGUE', 'LOGIC')
NON_SIGNAL = ('AGND', 'NC', '+12V', '-12V', '+5V')


def load_inputs(path=INPUTS):
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------- signals and classes

def is_link_pair(pr):
    return 'K' in pr['boards'] and not pr['family'].startswith('K/O')


def link_signals(root=ROOT):
    """Every signal of a K pair that goes to a link (all K pairs except the six adapter pairs). NC, rail and AGND
    positions are not signals, as in ST-02's room study (scripts/stack/geometry/links.py, NON_SIGNAL)."""
    cand = json.loads((root / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    out = []
    for pr in cand['pairs']:
        if not is_link_pair(pr):
            continue
        front = [b for b in pr['boards'] if b != 'K'][0]
        for net in pr['pin_map']:
            if net not in NON_SIGNAL:
                out.append({'pair': pr['id'], 'family': pr['family'], 'front_board': front, 'net': net})
    return out


def signal_census(root=ROOT):
    """Counts for the README text: K-pair signals, adapter signals and NC positions on link pairs."""
    cand = json.loads((root / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    k = [pr for pr in cand['pairs'] if 'K' in pr['boards']]
    sig = lambda prs: sum(n not in NON_SIGNAL for pr in prs for n in pr['pin_map'])  # noqa: E731
    return {'K_pair_signals': sig(k), 'adapter_signals': sig([pr for pr in k if not is_link_pair(pr)]),
            'link_nc_positions': sum(n == 'NC' for pr in k if is_link_pair(pr) for n in pr['pin_map'])}


def partition_kinds(root=ROOT):
    part = json.loads((root / 'design/partition/partition.json').read_text())
    kinds = {}
    for h in part['harnesses']:
        for s in h['signals']:
            kinds.setdefault(s['net'], set()).add(s['kind'])
    return kinds


def classify(net, kinds, rules):
    ks = kinds.get(net, set())
    for r in rules:
        if 'kind' in r and r['kind'] != '*' and r['kind'] not in ks:
            continue
        if 'net_regex' in r and not re.search(r['net_regex'], net):
            continue
        return r['class']
    raise ValueError('unclassified net ' + net)


def classified_signals(inp, root=ROOT):
    kinds = partition_kinds(root)
    rows = []
    for s in link_signals(root):
        s = dict(s)
        s['kind'] = ' / '.join(sorted(kinds.get(s['net'], {'(not in partition harnesses)'})))
        s['class'] = classify(s['net'], kinds, inp['classes']['rules'])
        rows.append(s)
    return rows


def joint_of(s):
    f = s['family']
    if f == 'JL/P pass-through':
        return 'JL to P through K'
    if f in ('K/P', 'SUB', 'P/K for EL'):
        return 'P to K (with SUB and EL pass-through)'
    return s['front_board'] + ' to K'


def ground_branch(s):
    """The AGND post branch that the link ground parallels."""
    return 'JL' if s['family'] == 'JL/P pass-through' else s['front_board']


# ---------------------------------------------------------------- capacitance (2-D MoM)

def _g(u):
    au = np.abs(u)
    return np.where(au > 0, u * np.log(np.where(au > 0, au, 1.0)) - u, 0.0)


def strip_segments(centers, width, nseg):
    """Cosine-graded segments (dense at the strip edges, where the charge peaks)."""
    edges, owner = [], []
    t = 0.5 * (1 - np.cos(np.linspace(0, math.pi, nseg + 1)))
    for k, c in enumerate(centers):
        e = c - width / 2 + width * t
        for i in range(nseg):
            edges.append((e[i], e[i + 1]))
            owner.append(k)
    return np.array(edges), np.array(owner)


def capacitance_matrix(centers, width, eps_r, nseg=24):
    """Short-circuit capacitance matrix per unit length (F/m) of coplanar zero-thickness strips in a homogeneous
    medium, with total charge zero (open 2-D boundary). Columns sum to zero; -C[i, j] is the mutual capacitance."""
    seg, owner = strip_segments(centers, width, nseg)
    n, m = len(seg), len(centers)
    mid = seg.mean(axis=1)
    h = seg[:, 1] - seg[:, 0]
    u1 = mid[:, None] - seg[None, :, 0]
    u2 = mid[:, None] - seg[None, :, 1]
    P = -(_g(u1) - _g(u2)) / h[None, :] / (2 * math.pi * EPS0 * eps_r)
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = P
    A[:n, n] = 1.0
    A[n, :n] = 1.0
    C = np.zeros((m, m))
    for j in range(m):
        rhs = np.zeros(n + 1)
        rhs[:n] = (owner == j).astype(float)
        sol = np.linalg.solve(A, rhs)
        q = sol[:n]
        for i in range(m):
            C[i, j] = q[owner == i].sum()
    return C


def coplanar_pair_c(width, gap, eps_r):
    """Conformal-map capacitance per unit length of two coplanar strips (test reference): eps K(k') / K(k)."""
    from scipy.special import ellipk
    k = gap / (gap + 2 * width)
    return EPS0 * eps_r * ellipk(1 - k * k) / ellipk(k * k)


# ---------------------------------------------------------------- partial inductance

def lp_self(l, w, t):
    return MU0 * l / (2 * math.pi) * (math.log(2 * l / (w + t)) + 0.5 + 0.2235 * (w + t) / l)


def lp_mutual(l, d):
    x = l / d
    return MU0 * l / (2 * math.pi) * (math.log(x + math.sqrt(1 + x * x)) - math.sqrt(1 + 1 / (x * x)) + 1 / x)


def lp_matrix(centers, l, w, t):
    m = len(centers)
    L = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            L[i, j] = lp_self(l, w, t) if i == j else lp_mutual(l, abs(centers[i] - centers[j]))
    return L


def effective_mutual(L, window, a, v):
    """Aggressor current +1 on a returns through the window's grounds, split by least inductance; the victim sees
    its own induced voltage less the common ground voltage (grounds tied at both ends)."""
    g = [i for i, c in enumerate(window) if c == 'G']
    ng = len(g)
    A = np.zeros((ng + 1, ng + 1))
    rhs = np.zeros(ng + 1)
    for r, gi in enumerate(g):
        A[r, :ng] = L[gi, g]
        A[r, ng] = -1.0
        rhs[r] = -L[gi, a]
    A[ng, :ng] = 1.0
    rhs[ng] = -1.0
    x = np.linalg.solve(A, rhs)
    current = np.zeros(len(window))
    current[a] = 1.0
    current[g] = x[:ng]
    return float(L[v] @ current - L[g[0]] @ current), {window_index: float(c) for window_index, c in zip(g, x[:ng])}


# ---------------------------------------------------------------- coupling

def pair_parameters(inp, pitch_key, length_mm, eps_r, rule, pair):
    cab = inp['cable'][pitch_key]
    p, w, t = cab['pitch_mm'] * 1e-3, cab['conductor_width_mm'] * 1e-3, cab['conductor_thickness_mm'] * 1e-3
    l = (length_mm + 2 * inp['cable']['end_equivalent_mm']['value']) * 1e-3
    window = inp['ground_rules'][rule]['window']
    a, v = inp['ground_rules'][rule]['pairs'][pair]
    centers = [i * p for i in range(len(window))]
    C = capacitance_matrix(centers, w, eps_r) * l
    L = lp_matrix(centers, l, w, t)
    m_eff, split = effective_mutual(L, window, a, v)
    return {'Cm_F': float(-C[a, v]), 'Cv_total_F': float(C[v, v]), 'M_eff_H': m_eff, 'Lp_av_H': float(L[a, v]),
            'return_split': split, 'length_m': l}


def victim_peak(par, agg, vic, inp, edge_index=None, r_index=None):
    a = inp['aggressors'][agg]
    vv = inp['victims'][vic]
    r = vv['source_ohm'][vv['nominal_index'] if r_index is None else r_index]
    ctot = par['Cv_total_F'] + vv['input_F']
    if agg == 'LOGIC':
        tr = a['edge_s'][a['nominal_index'] if edge_index is None else edge_index]
        va = a['swing_V']
        didt = 2 * a['load_F'] * va / tr ** 2
    else:
        slew = a['slew_V_per_s'][a['nominal_index'] if edge_index is None else edge_index]
        va = a['swing_V']
        tr = va / slew
        i = va / a['load_ohm'] + a['load_F'] * slew
        didt = 2 * i / tr
    tau = r * ctot
    v_c = va * r * par['Cm_F'] / tr * (1 - math.exp(-tr / tau))
    v_l = abs(par['M_eff_H']) * didt
    out = {'edge_V': v_c + v_l, 'capacitive_V': v_c, 'inductive_V': v_l, 'swing_V': va}
    if agg == 'ANALOGUE':
        wr = 2 * math.pi * a['sine_Hz'] * r
        out['sine_V'] = a['sine_peak_V'] * wr * par['Cm_F'] / math.hypot(1, wr * ctot)
    out['dB'] = 20 * math.log10(out['edge_V'] / va)
    return out


def coupling_table(inp):
    rows = []
    eps = inp['cable']['eps_eff']['value']
    for pk in PITCHES:
        for length in inp['cable']['lengths_mm']['value']:
            for rule, pair in (('A', 'adjacent'), ('A', 'across_ground'), ('B', 'across_ground')):
                for ie, e in enumerate(eps):
                    par = pair_parameters(inp, pk, length, e, rule, pair)
                    for agg in AGGRESSORS:
                        for vic in VICTIMS:
                            pk_v = victim_peak(par, agg, vic, inp)
                            rows.append({'pitch': pk, 'length_mm': length, 'rule': rule, 'pair': pair, 'eps_eff': e,
                                         'aggressor': agg, 'victim': vic, 'Cm_pF': par['Cm_F'] * 1e12,
                                         'Cv_total_pF': par['Cv_total_F'] * 1e12, 'M_eff_nH': par['M_eff_H'] * 1e9,
                                         'Lp_av_nH': par['Lp_av_H'] * 1e9, **pk_v,
                                         'limit_V': inp['victims'][vic]['limit_V'],
                                         'meets': max(pk_v['edge_V'], pk_v.get('sine_V', 0)) <= inp['victims'][vic]['limit_V']})
    return rows


SENSITIVITY_CASE = ('pitch_0_5', -1)


def sensitivity(inp, pitch=SENSITIVITY_CASE[0], length=None):
    """Worst configuration (upper eps) across the impedance and edge sweeps: the verdict's dependence on ASSUMED terms."""
    e = inp['cable']['eps_eff']['value'][-1]
    length = inp['cable']['lengths_mm']['value'][SENSITIVITY_CASE[1]] if length is None else length
    rows = []
    for rule, pair in (('A', 'adjacent'), ('A', 'across_ground'), ('B', 'across_ground')):
        par = pair_parameters(inp, pitch, length, e, rule, pair)
        for agg in AGGRESSORS:
            n_e = len(inp['aggressors'][agg]['edge_s' if agg == 'LOGIC' else 'slew_V_per_s'])
            for vic in VICTIMS:
                n_r = len(inp['victims'][vic]['source_ohm'])
                grid = [[victim_peak(par, agg, vic, inp, ie, ir)['edge_V'] for ir in range(n_r)] for ie in range(n_e)]
                rows.append({'rule': rule, 'pair': pair, 'aggressor': agg, 'victim': vic, 'grid_V': grid})
    return rows


def verdict_rows(inp, table):
    """Per pitch, aggressor and victim: the worst bound over lengths at the upper eps, per configuration."""
    e = inp['cable']['eps_eff']['value'][-1]
    out = []
    for pk in PITCHES:
        for agg in AGGRESSORS:
            for vic in VICTIMS:
                cfg = {}
                for rule, pair in (('A', 'adjacent'), ('A', 'across_ground'), ('B', 'across_ground')):
                    sel = [r for r in table if r['pitch'] == pk and r['eps_eff'] == e and r['rule'] == rule and r['pair'] == pair
                           and r['aggressor'] == agg and r['victim'] == vic]
                    cfg[rule + ':' + pair] = {L: max(sel, key=lambda r: r['edge_V'] if r['length_mm'] == L else -1) for L in inp['cable']['lengths_mm']['value']}
                limit = inp['victims'][vic]['limit_V']
                worst = lambda key: max(max(x['edge_V'], x.get('sine_V', 0)) for x in cfg[key].values())  # noqa: E731
                if worst('A:adjacent') <= limit:
                    need = 'side by side'
                elif worst('B:across_ground') <= limit and worst('A:across_ground') <= limit:
                    need = 'grounded neighbour between'
                elif worst('B:across_ground') <= limit:
                    need = 'grounded neighbours on both sides (rule B pattern)'
                else:
                    need = 'not in the same flat cable (separate link or ground layer)'
                out.append({'pitch': pk, 'aggressor': agg, 'victim': vic, 'limit_V': limit, 'cfg': cfg, 'need': need})
    return out


# ---------------------------------------------------------------- ground count under the rule

SEP_RANK = {'side by side': 0, 'grounded neighbour between': 1, 'grounded neighbours on both sides (rule B pattern)': 1,
            'not in the same flat cable (separate link or ground layer)': 2}


def need_between(verdicts, pk, c1, c2):
    """Separation needed between two adjacent signals of classes c1 and c2 (both directions; STATIC aggressors exert none)."""
    rank = 0
    for agg, vic in ((c1, c2), (c2, c1)):
        a = 'ANALOGUE' if agg in ('ANALOGUE', 'PRECISION') else ('LOGIC' if agg == 'LOGIC' else None)
        if a is None:
            continue
        v = [r for r in verdicts if r['pitch'] == pk and r['aggressor'] == a and r['victim'] == vic][0]
        rank = max(rank, SEP_RANK[v['need']])
    return rank


def _links(n_sig, g_fixed, circuits):
    """Fixed point: one ground per link (cable edge and return) on top of the rule's fixed grounds."""
    links = 1
    while math.ceil((n_sig + g_fixed + links) / circuits) > links:
        links += 1
    return links


def ground_count(signals, verdicts, pk, circuits):
    """Grounds and links per joint under the computed rule with free ordering inside a joint: classes in blocks, a
    ground between same-class neighbours only where the class pair needs one, one ground between blocks in a cable,
    one ground per link, and classes that may not share a cable put into cables of their own. Rule A and rule B of
    DS-51 are counted the same way for comparison. A lower bound: the class mix per link follows ST-02 a4's clusters."""
    order = ('LOGIC', 'ANALOGUE', 'PRECISION', 'WIPER')
    joints = {}
    for s in signals:
        if s['class'] == 'NC':
            continue
        joints.setdefault(joint_of(s), {}).setdefault(s['class'], 0)
        joints[joint_of(s)][s['class']] += 1
    out = {}
    for j, counts in sorted(joints.items()):
        present = [c for c in order if counts.get(c)]
        groups = []
        for c in present:
            for g in groups:
                if not any(need_between(verdicts, pk, c, o) == 2 for o in g):
                    g.append(c)
                    break
            else:
                groups.append([c])
        grounds = links = 0
        for g in groups:
            n = sum(counts[c] for c in g)
            fixed = sum(counts[c] - 1 for c in g if need_between(verdicts, pk, c, c) >= 1) + len(g) - 1
            k = _links(n, fixed, circuits)
            grounds += fixed + k
            links += k
        n_sig = sum(counts.values())
        out[j] = {'signals': n_sig, 'classes': {c: counts[c] for c in present}, 'cables': [' + '.join(g) for g in groups],
                  'grounds_rule': grounds, 'links_rule': links, **ds51_counts(n_sig, circuits)}
    return out


def ds51_capacity(n, rule):
    """Signals per link, as ST-02's room study (scripts/stack/geometry/links.py, capacity()) for A and B_inner."""
    s = 0
    if rule == 'A':
        while (s + 1) + math.ceil((s + 1) / 2) <= n:
            s += 1
    elif rule == 'B_inner':
        while 2 * (s + 1) - 1 <= n:
            s += 1
    elif rule == 'B_outer':
        while 2 * (s + 1) + 1 <= n:
            s += 1
    return s


def ds51_grounds(s, rule):
    return {'A': math.ceil(s / 2), 'B_inner': max(s - 1, 0), 'B_outer': s + 1}[rule]


def ds51_counts(n_sig, circuits):
    """Per link, links filled to capacity: rule A (one ground per two signals), rule B read without outer grounds
    (s - 1 per link, the room study's reading and the present harness pattern) and with them (s + 1)."""
    out = {}
    for rule in ('A', 'B_inner', 'B_outer'):
        cap = ds51_capacity(circuits, rule)
        full, rem = divmod(n_sig, cap)
        out['rule_' + rule] = {'signals_per_link': cap, 'links': full + (rem > 0),
                               'grounds': full * ds51_grounds(cap, rule) + ds51_grounds(rem, rule)}
    return out


# ---------------------------------------------------------------- ground current

def link_ground_paths(inp, pk):
    c = inp['conductor_resistance_mohm'][pk]
    rc = inp['contact'][pk]['resistance_max_ohm']['value']
    rmin = c['min'] / 1000 + 2 * inp['contact']['resistance_min_ohm']['value']
    rmax = c['max'] / 1000 + 2 * rc
    return rmin, rmax


def worst_ground_contact(inp, pk, branch, n, posts, d=None):
    d = d or pp.load()
    rmin, rmax = link_ground_paths(inp, pk)
    rj = pp.joint_ohm(d, pp.branch_gap(branch, d))
    g = (n - 1) / rmax + posts / rj
    alt = pp.v(d, 'return_plane_ohm') + (1 / g if g > 0 else math.inf)
    i_total = pp.v(d, 'single_return_A')
    if math.isinf(alt):
        return i_total
    return i_total * alt / (rmin + alt)


def min_grounds(inp, pk, branch, posts, limit, d=None, n_max=2000):
    for n in range(1, n_max + 1):
        if worst_ground_contact(inp, pk, branch, n, posts, d) <= limit:
            return n
    return None


def current_table(inp, signals):
    d = pp.load()
    rows = []
    branch_signals = {}
    for s in signals:
        branch_signals[ground_branch(s)] = branch_signals.get(ground_branch(s), 0) + 1
    for pk in PITCHES:
        ratings = inp['contact'][pk]['ratings_A']
        for b in inp['ground_current']['branches']:
            nA = ds51_counts(branch_signals[b], inp['link_options'][pk][0])['rule_A']['grounds']
            for case, posts in inp['ground_current']['posts_cases'].items():
                row = {'pitch': pk, 'branch': b, 'case': case, 'posts': posts,
                       'I_n1_A': worst_ground_contact(inp, pk, b, 1, posts, d),
                       'I_ruleA_A': worst_ground_contact(inp, pk, b, nA, posts, d), 'n_ruleA': nA,
                       'n_min': {str(r['value']): min_grounds(inp, pk, b, posts, r['value'], d) for r in ratings}}
                rows.append(row)
    return rows, branch_signals


# ---------------------------------------------------------------- outputs

def room_site_counts(root=ROOT):
    """ST-02 a4's signal count (design/stack/geometry/links/link-candidate.json, site_counts), read only."""
    return json.loads((root / 'design/stack/geometry/links/link-candidate.json').read_text())['site_counts']


def results(inp):
    sig = classified_signals(inp)
    table = coupling_table(inp)
    verd = verdict_rows(inp, table)
    cur, branch_signals = current_table(inp, sig)
    by_class = {}
    for s in sig:
        by_class[s['class']] = by_class.get(s['class'], 0) + 1
    rmin_max = {pk: link_ground_paths(inp, pk) for pk in PITCHES}
    return {'signals': sig, 'by_class': by_class, 'coupling': table, 'verdicts': verd,
            'sensitivity': sensitivity(inp), 'census': signal_census(), 'site_counts': room_site_counts(),
            'ground_counts': {pk: {str(c): ground_count(sig, verd, pk, c) for c in inp['link_options'][pk]} for pk in PITCHES},
            'ground_current': cur, 'branch_signals': branch_signals,
            'link_ground_path_ohm': {pk: {'min': a, 'max': b} for pk, (a, b) in rmin_max.items()}}


def rnd(x):
    if isinstance(x, float):
        return float(f'{x:.6g}')
    if isinstance(x, dict):
        return {str(k): rnd(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v) for v in x]
    return x


def results_json(inp, r):
    keep = {k: v for k, v in r.items() if k != 'verdicts'}
    keep['verdicts'] = [{k: v for k, v in x.items() if k != 'cfg'} for x in r['verdicts']]
    doc = {'schema_version': 1, 'task': inp['task'], 'status': inp['status'],
           'written_by': 'scripts/stack/link_electrical/link_electrical.py', 'inputs': 'inputs.json', **rnd(keep)}
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def mv(x):
    return f'{x * 1000:.3g}'


def db(x, va):
    return f'{20 * math.log10(x / va):.0f}'


def sweep(xs, scale, unit):
    return ' / '.join(f'{x * scale:g}' for x in xs) + ' ' + unit


def pitch_heading(rows):
    side = [x for x in rows if x['need'] == 'side by side']
    gnd = [x for x in rows if SEP_RANK[x['need']] == 1]
    sep = [x for x in rows if SEP_RANK[x['need']] == 2]
    return (f'{len(side)} of {len(rows)} class pairs side by side, {len(gnd)} with a grounded neighbour, {len(sep)} not in one cable'
            + (' (' + ', '.join(f'{x["aggressor"]} onto {x["victim"]}' for x in sep) + ')' if sep else ''))


def readme(inp, r):
    L = inp['cable']['lengths_mm']['value']
    eps = inp['cable']['eps_eff']['value']
    e_hi = eps[-1]
    la = inp['aggressors']['LOGIC']
    an = inp['aggressors']['ANALOGUE']
    nsig = len(r['signals'])
    cen = r['census']
    joints = {}
    for s in r['signals']:
        joints[joint_of(s)] = joints.get(joint_of(s), 0) + 1
    by_pitch = {pk: [x for x in r['verdicts'] if x['pitch'] == pk] for pk in PITCHES}
    gc = r['ground_current']
    worst_normal = max(x['I_n1_A'] for x in gc if x['case'] == 'normal')
    worst_open = max(x['I_n1_A'] for x in gc if x['case'] == 'one_post_open')
    lines = []
    w = lines.append
    w('# Flat-link electrical bounds: ST-04 attempts a2 to a4 (paper; DS-41 checks 3 and 4 without positions, harness baseline DS-54, DS-62 table; gate checks 3 and 4 on the record of the room study)')
    w('')
    w(f'Task `{inp["task"]}`, launch commit `{inp["launch_commit"]}`. **Status: unvalidated paper bound.** Coupling, current share '
      'and resistance are NOT RUN as measurements; nothing is selected, adopted or bought. Every class, impedance, edge rate and '
      'limit below is ASSUMED unless a row says otherwise, and the limits are criteria for the design ruling (NEEDS_DESIGN).')
    w('')
    w('This file, `results.json`, `harness-baseline.json` and `ds62-table.json` are written by `python3 scripts/stack/link_electrical/link_electrical.py` from '
      '[`inputs.json`](inputs.json); the tests fail if any differs from a fresh run. Status words: SOURCED (file and locator in '
      '`inputs.json`), DERIVED (formula below), ASSUMED (reason in `inputs.json`), NOT RUN (reason given).')
    w('')
    # ---- signals
    w(f'## {nsig} link signals in four coupling classes, the count of ST-02\'s room study ({r["site_counts"]["signals"]})')
    w('')
    w(f'Every K pair of the retained candidate except the six adapter pairs, with rail, AGND and NC positions removed (as '
      f'`NON_SIGNAL` in `scripts/stack/geometry/links.py`): {cen["K_pair_signals"]} K-pair signals less {cen["adapter_signals"]} '
      f'on the adapter pairs = {nsig}; {cen["link_nc_positions"]} NC positions on link pairs are not signals. The class comes from the '
      'partition\'s signal kind and the net name (`inputs.json` → `classes`, ASSUMED). Four planning nets of the SUB pairs '
      '(`O2:SUB_SEL_A` etc.) are not in the partition harnesses and are taken as LOGIC.')
    w('')
    w('| Joint | ' + ' | '.join(VICTIMS) + ' | Total |')
    w('| --- | ' + '--- | ' * len(VICTIMS) + '--- |')
    for j in sorted(joints):
        cnt = {}
        for s in r['signals']:
            if joint_of(s) == j:
                cnt[s['class']] = cnt.get(s['class'], 0) + 1
        w(f'| {j} | ' + ' | '.join(str(cnt.get(c, 0)) for c in VICTIMS) + f' | {joints[j]} |')
    w('| **Total** | ' + ' | '.join(str(r['by_class'].get(c, 0)) for c in VICTIMS) + f' | {nsig} |')
    w('')
    w('| Class | Victim source impedance (sweep, nominal) | Victim limit | As aggressor |')
    w('| --- | --- | --- | --- |')
    for c in VICTIMS:
        vv = inp['victims'][c]
        agg = {'PRECISION': 'ANALOGUE row (op-amp slew)', 'WIPER': 'none (hand-turned; STATIC)',
               'ANALOGUE': f'{an["swing_V"]:g} V at {an["slew_V_per_s"][an["nominal_index"]] / 1e6:g} V/µs (sweep {sweep(an["slew_V_per_s"], 1e-6, "V/µs")}), '
                           f'and a {an["sine_peak_V"]:g} V peak {an["sine_Hz"] / 1000:g} kHz sine',
               'LOGIC': f'{la["swing_V"]:g} V in {la["edge_s"][la["nominal_index"]] * 1e9:g} ns (sweep {sweep(la["edge_s"], 1e9, "ns")}), load {la["load_F"] * 1e12:g} pF'}[c]
        w(f'| {c} | {", ".join(f"{x:g}" for x in vv["source_ohm"])} Ω, nominal {vv["source_ohm"][vv["nominal_index"]]:g} Ω | {vv["limit_V"] * 1000:g} mV | {agg} |')
    w('')
    # ---- coupling
    heads = {pk: pitch_heading(rows) for pk, rows in by_pitch.items()}
    if len(set(heads.values())) == 1:
        head = 'at both pitches ' + heads[PITCHES[0]]
    else:
        head = '; '.join(f'at {PITCH_LABEL[pk]} {h}' for pk, h in heads.items())
    w(f'## Coupling under the ASSUMED absolute limits: {head}')
    w('')
    w(f'Upper permittivity {e_hi}, nominal impedance and edge. The table gives the worst bound over {" and ".join(f"{x:g}" for x in L)} mm '
      f'per pitch; voltage in mV, dB relative to the aggressor swing; "sine" is the steady {an["sine_Hz"] / 1000:g} kHz bleed. Rule A '
      'adjacent is two signals side by side; A across ground and B are one grounded conductor between them (B also has grounds on '
      'the outer sides).')
    w('')
    for pk in PITCHES:
        w(f'### {PITCH_LABEL[pk]} pitch: worst crosstalk per class pair, {" / ".join(f"{x:g}" for x in L)} mm')
        w('')
        w(f'| Aggressor → victim | Limit, mV | Side by side, mV (dB) | Ground between (A), mV (dB) | Ground between (B), mV (dB) | {an["sine_Hz"] / 1000:g} kHz sine side by side, mV | Rule that follows |')
        w('| --- | --- | --- | --- | --- | --- | --- |')
        for x in by_pitch[pk]:
            cells = []
            for key in ('A:adjacent', 'A:across_ground', 'B:across_ground'):
                c = x['cfg'][key]
                cells.append(' / '.join(f'{mv(c[l]["edge_V"])} ({db(c[l]["edge_V"], c[l]["swing_V"])})' for l in L))
            sine = ' / '.join(mv(x['cfg']['A:adjacent'][l]['sine_V']) if 'sine_V' in x['cfg']['A:adjacent'][l] else '—' for l in L)
            w(f'| {x["aggressor"]} → {x["victim"]} | {x["limit_V"] * 1000:g} | {cells[0]} | {cells[1]} | {cells[2]} | {sine} | {x["need"]} |')
        w('')
    wv = inp['victims']['WIPER']
    r_w = wv['source_ohm'][wv['nominal_index']]
    limits = ', '.join(f'{c} {inp["victims"][c]["limit_V"] * 1000:g} mV' for c in VICTIMS)
    w('Three ASSUMED terms carry these verdicts, and each is a design input. (1) The wiper victim has no receiver filter '
      f'capacitor credited: at {r_w / 1000:g} kΩ the coupled edge decays over R·C_tot, and any filter capacitor at the '
      'receiver divides it by C_filter/C_tot. (2) PRECISION nets are counted as aggressors at full analogue slew; most are DC '
      'references or slow CVs. (3) The victim limits '
      f'({limits}) are peak criteria for nanosecond to microsecond spikes; a pitch error depends on the area that the receiving '
      'stage integrates, which no retained source states. No 2-layer flex with a ground layer is computed (DS-41 check 4): NOT RUN.')
    w('')
    w('### Per-unit-length terms behind the table (DERIVED)')
    w('')
    w(f'| Pitch | Configuration | ε_eff | Cm at {L[0]:g} mm + ends, pF | Victim total C, pF | Partial mutual a–v, nH | Loop mutual with ground return, nH |')
    w('| --- | --- | --- | --- | --- | --- | --- |')
    seen = set()
    for x in r['coupling']:
        k = (x['pitch'], x['rule'], x['pair'], x['eps_eff'])
        if x['length_mm'] != L[0] or k in seen:
            continue
        seen.add(k)
        w(f'| {PITCH_LABEL[x["pitch"]]} | {x["rule"]} {x["pair"].replace("_", " ")} | {x["eps_eff"]} | {x["Cm_pF"]:.3f} | {x["Cv_total_pF"]:.3f} | {x["Lp_av_nH"]:.1f} | {x["M_eff_nH"]:.2f} |')
    w('')
    w(f'Formulas. Capacitance: 2-D method of moments for coplanar strips in a homogeneous medium (ε_eff swept {" / ".join(f"{x:g}" for x in eps)}), '
      "zero total charge, the other conductors of the window held at AC ground; checked against ε K(k')/K(k) for two strips "
      'in the tests. Inductance: Grover\'s parallel-filament mutual and Ruehli\'s bar self term, valid for length ≫ spacing; '
      'the aggressor return divides among the window\'s grounds by least inductance. Victim bound = capacitive term '
      'V·R·Cm/t_r·(1 − e^(−t_r/(R·C_tot))) plus the full loop term M·di/dt, di/dt = 2·I/t_r (both ASSUMED same sign). '
      f'Each end adds {inp["cable"]["end_equivalent_mm"]["value"]:g} mm of parallel run for the connector and fan-in (ASSUMED).')
    w('')
    # ---- sensitivity
    s_len = L[SENSITIVITY_CASE[1]]
    w(f'### The verdicts turn on the victim impedance and the logic edge: sensitivity at {PITCH_LABEL[SENSITIVITY_CASE[0]]}, {s_len:g} mm, ε_eff {e_hi}')
    w('')
    w('| Configuration | Aggressor → victim | Edge or slew sweep (rows) × victim impedance sweep (columns), mV |')
    w('| --- | --- | --- |')
    for x in r['sensitivity']:
        if x['victim'] in ('PRECISION', 'WIPER') or x['aggressor'] == 'LOGIC':
            grid = '; '.join(' / '.join(f'{v * 1000:.3g}' for v in row) for row in x['grid_V'])
            w(f'| {x["rule"]} {x["pair"].replace("_", " ")} | {x["aggressor"]} → {x["victim"]} | {grid} |')
    w('')
    # ---- ground count
    tot = {}
    for pk in PITCHES:
        for c, rows in r['ground_counts'][pk].items():
            tot[(pk, c)] = {k: [sum(x[k][q] for x in rows.values()) for q in ('grounds', 'links')] for k in ('rule_A', 'rule_B_inner', 'rule_B_outer')}
            tot[(pk, c)]['own'] = [sum(x[q] for x in rows.values()) for q in ('grounds_rule', 'links_rule')]
            tot[(pk, c)]['cap'] = {k: next(iter(rows.values()))[k]['signals_per_link'] for k in ('rule_A', 'rule_B_inner', 'rule_B_outer')}
    lo = min(v['own'][0] for v in tot.values())
    hi = max(v['own'][0] for v in tot.values())
    ds = {k: (min(v[k][0] for v in tot.values()), max(v[k][0] for v in tot.values())) for k in ('rule_A', 'rule_B_inner', 'rule_B_outer')}
    w(f'## The a2 class rule needs {lo} to {hi} grounds for the {nsig} signals; counted per link, rule A needs {ds["rule_A"][0]} to '
      f'{ds["rule_A"][1]}, rule B {ds["rule_B_inner"][0]} to {ds["rule_B_inner"][1]} without outer grounds and '
      f'{ds["rule_B_outer"][0]} to {ds["rule_B_outer"][1]} with them')
    w('')
    w('Own class rule, per joint and option, with free ordering inside a joint: classes in blocks, a ground between same-class '
      'neighbours only where the class pair needs one, one ground between blocks that share a cable, one ground per link (at a '
      'cable edge; no other outer grounds), and class pairs that may not share a cable put in cables of their own. A lower bound: '
      'the class mix per link follows the clustering of ST-02 a4. DS-51 rules are counted per link with the capacities of the room '
      'study (links filled to capacity per joint): rule A one ground per two signals; rule B read without outer grounds (s − 1 '
      'grounds per link, the room study\'s reading and the present harness pattern) and with them (s + 1). Filling every link '
      'to capacity per joint gives fewer links than the room study\'s clustering, which also respects site distances.')
    w('')
    w('| Pitch | Circuits | Own rule, grounds / links | Rule A, signals per link: grounds / links | Rule B inner only, signals per link: grounds / links | Rule B with outer grounds, signals per link: grounds / links |')
    w('| --- | --- | --- | --- | --- | --- |')
    for (pk, c), v in tot.items():
        w(f'| {PITCH_LABEL[pk]} | {c} | {v["own"][0]} / {v["own"][1]} | ' + ' | '.join(
            f'{v["cap"][k]}: {v[k][0]} / {v[k][1]}' for k in ('rule_A', 'rule_B_inner', 'rule_B_outer')) + ' |')
    w('')
    pk0 = PITCHES[0]
    c0 = str(inp['link_options'][pk0][0])
    w(f'Per joint at {PITCH_LABEL[pk0]}, {c0} circuits (the other options in `results.json`):')
    w('')
    w('| Joint | Signals | Cable groups | Own rule | Rule A | Rule B inner | Rule B outer |')
    w('| --- | --- | --- | --- | --- | --- | --- |')
    for j, x in r['ground_counts'][pk0][c0].items():
        w(f'| {j} | {x["signals"]} | {"; ".join(x["cables"])} | {x["grounds_rule"]} / {x["links_rule"]} | ' +
          ' | '.join(f'{x[k]["grounds"]} / {x[k]["links"]}' for k in ('rule_A', 'rule_B_inner', 'rule_B_outer')) + ' |')
    w('')
    # ---- ground current
    rmin_all = min(x['value'] for pk in PITCHES for x in inp['contact'][pk]['ratings_A'])
    word = 'inside' if worst_open <= rmin_all else 'over'
    w(f'## Ground current: the worst link ground contact carries at most {worst_normal:.3f} A normally and {worst_open:.3f} A with one post open, {word} the lowest rating swept ({rmin_all:g} A) at both pitches')
    w('')
    rp = r['link_ground_path_ohm']
    d = pp.load()
    w('One link ground path is two contacts and one conductor. The bound gives the candidate path its minimum resistance (conductor '
      f'minimum, contacts {inp["contact"]["resistance_min_ohm"]["value"]:g} Ω ASSUMED) and no PCB term, and every alternative its '
      f'maximum and the whole {pp.v(d, "return_plane_ohm") * 1000:g} mΩ common neck (the partition35 method of the power-post README). '
      f'Branch current {pp.v(d, "single_return_A"):g} A (SOURCED, `single_return_A`). Post joints from `power_posts.py` ('
      + ' / '.join(f'{b} {pp.joint_ohm(d, pp.branch_gap(b, d)) * 1000:.4f}' for b in inp['ground_current']['branches']) + ' mΩ).')
    w('')
    w('| Pitch | Link ground path, min / max, mΩ |')
    w('| --- | --- |')
    for pk in PITCHES:
        w(f'| {PITCH_LABEL[pk]} | {rp[pk]["min"] * 1000:.1f} / {rp[pk]["max"] * 1000:.1f} (conductor DERIVED, contact max SOURCED) |')
    w('')
    w('| Pitch | Branch | AGND posts in place | Worst contact, one ground in the branch, A | Worst contact, rule A grounds per link at the first option (n), A | Smallest grounds per board meeting each rating |')
    w('| --- | --- | --- | --- | --- | --- |')
    for x in gc:
        nm = ', '.join(f'{k} A: {v if v is not None else "none ≤ 2000"}' for k, v in x['n_min'].items())
        w(f'| {PITCH_LABEL[x["pitch"]]} | {x["branch"]} | {x["posts"]} ({x["case"].replace("_", " ")}) | {x["I_n1_A"]:.3f} | {x["I_ruleA_A"]:.4f} ({x["n_ruleA"]}) | {nm} |')
    w('')
    w('With any post of the branch in place a single link ground stays far inside every rating, because one link ground path '
      '(tens of mΩ) is about a hundred times the post path (under 1 mΩ). So current sets no minimum beyond one ground per link; '
      'the coupling rule sets the count. With every AGND post of a branch open (not a design case) the link grounds carry the '
      'whole return, and the count in the last column applies.')
    w('')
    w('### The final share at the field positions needs four inputs from the geometry task')
    w('')
    w('- the K-side and front-side field centre of every link and its branch (ST-02 a4 `link-candidate.json`);')
    w('- the ground positions of each link after the ruling (count and pin numbers);')
    w('- the AGND plane spreading on K and on each front board from each field to the three post lands of its branch (routed planes, or the ASSUMED sheet model of the power-post README);')
    w('- the cable length per link (a shorter link lowers its path resistance and raises its share).')
    w('')
    # ---- checks
    w('## Checks: calculator and tests run; every measurement and native check NOT RUN')
    w('')
    w('- **Run:** this calculator twice with a clean `git status`; `python3 scripts/checks/frozen_studies.py discover scripts/stack/link_electrical`; `pnpm circuit:check` before and after.')
    w('- **NOT RUN, crosstalk, current share and resistance measurements:** no cable, connector or board exists.')
    w('- **NOT RUN, field solver for the real laminate:** the permittivity of the LX cable is not on its drawing; the homogeneous model is bracketed by the ε_eff sweep.')
    w('- **NOT RUN, connector contact coupling:** no connector coupling data is retained; covered only by the ASSUMED end length.')
    w('- **NOT RUN, ground share with board terms at the field positions:** the model keeps its stated terms (no board term on the link path); the record enters only through the contact count and the cable length.')
    w('- **NOT RUN, `bash scripts/checks/regen-all.sh`, `pnpm check` and the full Python suite:** native KiCad steps run in the pull request\'s CI; the suite outside this folder is run by the manager on the integrated tree.')
    w('- **NOT RUN, KiCad, DRC and `regen-all.sh`:** no board is changed.')
    w('- **NOT RUN, harness coupling measurement and a field solver for the insulated wire bundle:** no harness is built; the wire permittivity is not on the Alpha sheet.')
    w('')
    return '\n'.join(lines)


def generate():
    import harness_baseline as hb
    import ds62_table
    inp = load_inputs()
    r = results(inp)
    b = hb.build(inp, r['signals'])
    import link_ratios
    d62 = ds62_table.build(inp)
    r['signals_all'] = d62['signals_all']
    lr = link_ratios.build(inp, d62['baseline'])
    text = readme(inp, r)
    marker = '## Checks: calculator and tests run'
    text = text.replace(marker, '\n'.join(hb.readme_lines(inp, b, r['ground_counts'])) + '\n' +
                        '\n'.join(ds62_table.readme_lines(inp, d62)) + '\n' +
                        '\n'.join(link_ratios.readme_lines(inp, lr)) + '\n' + marker)
    return results_json(inp, r), text, hb.to_json(inp, b), ds62_table.to_json(inp, d62), link_ratios.to_json(inp, lr)


def main(argv):
    rj, rm, hj, dj, lj = generate()
    if '--check' in argv:
        ok = (OUT / 'results.json').read_text() == rj and (OUT / 'README.md').read_text() == rm and \
            (OUT / 'harness-baseline.json').read_text() == hj and (OUT / 'ds62-table.json').read_text() == dj and \
            (OUT / 'link-ratios.json').read_text() == lj
        print('current' if ok else 'stale')
        return 0 if ok else 1
    (OUT / 'results.json').write_text(rj)
    (OUT / 'README.md').write_text(rm)
    (OUT / 'harness-baseline.json').write_text(hj)
    (OUT / 'ds62-table.json').write_text(dj)
    (OUT / 'link-ratios.json').write_text(lj)
    print('wrote results.json, harness-baseline.json, ds62-table.json, link-ratios.json and README.md in', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
