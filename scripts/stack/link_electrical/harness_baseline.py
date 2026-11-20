"""ST-04 attempt a3: the present cable harness as the baseline for the flat-link coupling criteria (DS-54).

Imported by link_electrical.py, which writes design/stack/link-electrical/harness-baseline.json and the README
sections. Paper bounds only; the harness coupling was never measured either.
"""
import json
import math
import statistics

import numpy as np

import link_electrical as le

RAILS = ('+12V', '-12V', '+5V')
CONFIGS = (('flat side by side', 'A', 'adjacent', 0), ('flat one ground between (rule A)', 'A', 'across_ground', 1),
           ('flat ground on every side (rule B)', 'B', 'across_ground', 1), ('flat two grounds between', 'C', 'across_two_grounds', 2))


def aggressor_of(cls):
    return {'LOGIC': 'LOGIC', 'ANALOGUE': 'ANALOGUE', 'PRECISION': 'ANALOGUE'}.get(cls)


# ---------------------------------------------------------------- present pattern

def harness_patterns(inp, root=le.ROOT):
    part = json.loads((root / 'design/partition/partition.json').read_text())
    loom = {r['id']: r for r in json.loads((root / 'design/partition/loom-candidate.json').read_text())['routes']}
    hdr = {c['id']: c for c in part['connectors']}
    kinds = le.partition_kinds(root)
    rules = inp['classes']['rules']
    out = []
    for h in part['harnesses']:
        c = hdr[h['header_ids'][0]]
        seq = [c['pin_map'][str(i)] for i in range(1, c['contacts'] + 1)]
        cls = ['G' if n == 'AGND' else 'R' if n in RAILS else le.classify(n, kinds, rules) for n in seq]
        out.append({'id': h['id'], 'nets': seq, 'classes': cls, 'cut_length_mm': loom[h['id']]['cut_length_max_mm'],
                    'wire_mpn': loom[h['id']]['wire_mpn'],
                    'same_order_both_ends': c['pin_map'] == hdr[h['header_ids'][1]]['pin_map']})
    return out


def is_signal(c):
    return c not in ('G', 'R', 'NC')


def pattern_counts(pats):
    sizes, triples, harn, adjacent, beside_rail = {}, {}, {}, [], []
    outer_ground = 0
    for p in pats:
        c = p['classes']
        sizes[len(c)] = sizes.get(len(c), 0) + 1
        outer_ground += (c[0] == 'G') + (c[-1] == 'G')
        for i in range(len(c) - 1):
            if is_signal(c[i]) and is_signal(c[i + 1]):
                adjacent.append((p['id'], i + 1, i + 2))
            for x, y in ((c[i], c[i + 1]), (c[i + 1], c[i])):
                if is_signal(x) and y == 'R':
                    beside_rail.append((p['id'], x))
        for i in range(len(c) - 2):
            if c[i + 1] == 'G' and is_signal(c[i]) and is_signal(c[i + 2]):
                k = '/'.join(sorted((c[i], c[i + 2])))
                triples.setdefault(k, []).append({'harness': p['id'], 'a': i, 'v': i + 2})
                harn.setdefault(k, set()).add(p['id'])
    return {'sizes': sizes, 'triples': triples, 'harness_count': {k: len(v) for k, v in harn.items()},
            'adjacent_signals': adjacent, 'signal_beside_rail': beside_rail, 'outer_grounds': outer_ground,
            'outer_ground_harnesses': [p['id'] for p in pats if p['classes'][-1] == 'G']}


# ---------------------------------------------------------------- round-wire geometry

def wire_capacitance_matrix(centers, radius, eps_r, n=16, shrink=0.6):
    """Charge simulation: n line charges on a circle of shrink*radius in each wire, potential matched at n surface
    points, total charge zero. Short-circuit matrix per unit length (F/m), as capacitance_matrix in link_electrical."""
    m = len(centers)
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    src = np.array([(cx + shrink * radius * math.cos(t), shrink * radius * math.sin(t)) for cx in centers for t in ang])
    pts = np.array([(cx + radius * math.cos(t), radius * math.sin(t)) for cx in centers for t in ang])
    owner = np.repeat(np.arange(m), n)
    dist = np.hypot(pts[:, None, 0] - src[None, :, 0], pts[:, None, 1] - src[None, :, 1])
    P = -np.log(dist) / (2 * math.pi * le.EPS0 * eps_r)
    N = m * n
    A = np.zeros((N + 1, N + 1))
    A[:N, :N] = P
    A[:N, N] = 1.0
    A[N, :N] = 1.0
    C = np.zeros((m, m))
    for j in range(m):
        rhs = np.zeros(N + 1)
        rhs[:N] = (owner == j).astype(float)
        q = np.linalg.solve(A, rhs)[:N]
        for i in range(m):
            C[i, j] = q[owner == i].sum()
    return C


def two_wire_c(d_center, radius, eps_r):
    """Test reference: two parallel round wires, C = pi eps / acosh(D / 2r)."""
    return math.pi * le.EPS0 * eps_r / math.acosh(d_center / (2 * radius))


def lp_self_round(l, r):
    return le.MU0 * l / (2 * math.pi) * (math.log(2 * l / r) - 0.75)


def harness_pair_parameters(inp, classes, a, v, length_mm, eps_r):
    w = inp['harness']
    pitch = w['pitch_mm']['value'] * 1e-3
    r = w['conductor_diameter_mm']['value'] / 2 * 1e-3
    l = (length_mm + 2 * inp['cable']['end_equivalent_mm']['value']) * 1e-3
    centers = [i * pitch for i in range(len(classes))]
    C = wire_capacitance_matrix(centers, r, eps_r) * l
    m = len(classes)
    L = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            L[i, j] = lp_self_round(l, r) if i == j else le.lp_mutual(l, abs(centers[i] - centers[j]))
    window = ['G' if c == 'G' else 'S' for c in classes]
    m_eff, split = le.effective_mutual(L, window, a, v)
    return {'Cm_F': float(-C[a, v]), 'Cv_total_F': float(C[v, v]), 'M_eff_H': m_eff, 'return_split': split, 'length_m': l}


def level(par, agg, vic, inp):
    x = le.victim_peak(par, agg, vic, inp)
    return max(x['edge_V'], x.get('sine_V', 0.0)), x['swing_V']


# ---------------------------------------------------------------- baseline and comparison

def baseline(inp, pats=None):
    """Per directed class pair across one ground: the bound for every triple at the upper eps; shortest, median and
    longest harness length; and the smallest bound over all triples (the harness's quietest instance)."""
    pats = pats or harness_patterns(inp)
    byid = {p['id']: p for p in pats}
    eps = inp['cable']['eps_eff']['value'][-1]
    counts = pattern_counts(pats)
    rows = {}
    for key, tris in counts['triples'].items():
        c1, c2 = key.split('/')
        for ag_cls, vic in ((c1, c2), (c2, c1)):
            agg = aggressor_of(ag_cls)
            if agg is None or (ag_cls, vic) in [(r['aggressor_class'], r['victim']) for r in rows.values()]:
                continue
            vals = []
            for t in tris:
                p = byid[t['harness']]
                a, v = (t['a'], t['v']) if p['classes'][t['a']] == ag_cls else (t['v'], t['a'])
                if p['classes'][a] != ag_cls or p['classes'][v] != vic:
                    continue
                par = harness_pair_parameters(inp, p['classes'], a, v, p['cut_length_mm'], eps)
                lv, sw = level(par, agg, vic, inp)
                vals.append({'harness': p['id'], 'length_mm': p['cut_length_mm'], 'V': lv, 'swing_V': sw,
                             'Cm_pF': par['Cm_F'] * 1e12, 'M_eff_nH': par['M_eff_H'] * 1e9})
            vals.sort(key=lambda x: (x['length_mm'], x['harness']))
            med = vals[len(vals) // 2]
            rows[ag_cls + '>' + vic] = {'aggressor_class': ag_cls, 'aggressor': agg, 'victim': vic, 'triples': len(vals),
                                        'shortest': vals[0], 'median': med, 'longest': vals[-1],
                                        'min_V': min(x['V'] for x in vals), 'max_V': max(x['V'] for x in vals),
                                        'median_length_mm': statistics.median(x['length_mm'] for x in vals)}
    return rows, counts


def flat_levels(inp, pk, length_mm, ag_cls, vic):
    eps = inp['cable']['eps_eff']['value'][-1]
    out = {}
    for name, rule, pair, _ in CONFIGS:
        par = le.pair_parameters(inp, pk, length_mm, eps, rule, pair)
        out[name] = level(par, aggressor_of(ag_cls), vic, inp)[0]
    return out


def comparison(inp, base):
    rows = []
    for key, b in sorted(base.items()):
        for pk in le.PITCHES:
            fl = flat_levels(inp, pk, inp['cable']['lengths_mm']['value'][0], b['aggressor_class'], b['victim'])
            rows.append({'pair': key, 'pitch': pk, 'harness_min_V': b['min_V'], 'harness_median_V': b['median']['V'],
                         'flat_V': fl, 'ratio_to_min': {k: v / b['min_V'] for k, v in fl.items()},
                         'ratio_to_median': {k: v / b['median']['V'] for k, v in fl.items()}})
    return rows


def harness_rule(comp, base, pk):
    """Grounds needed between two neighbours of each class pair on a flat link so that every direction stays at or
    below the quietest harness instance of that pair; None = never share a flat cable (also when the pair never
    shares a harness across one ground)."""
    classes = ('LOGIC', 'ANALOGUE', 'PRECISION', 'WIPER')
    rule = {}
    for c1 in classes:
        for c2 in classes:
            dirs = [r for r in comp if r['pitch'] == pk and r['pair'] in (c1 + '>' + c2, c2 + '>' + c1)]
            present = '/'.join(sorted((c1, c2))) in {'/'.join(sorted((b['aggressor_class'], b['victim']))) for b in base.values()}
            if not present:
                rule[c1 + '/' + c2] = None if (aggressor_of(c1) or aggressor_of(c2)) else 0
                continue
            need = None
            for name, _, _, grounds in CONFIGS:
                if all(r['ratio_to_min'][name] <= 1.0 for r in dirs):
                    need = grounds
                    break
            rule[c1 + '/' + c2] = need
    return rule


def count_under(signals, rule, circuits):
    order = ('LOGIC', 'ANALOGUE', 'PRECISION', 'WIPER')
    joints = {}
    for s in signals:
        if s['class'] != 'NC':
            joints.setdefault(le.joint_of(s), {}).setdefault(s['class'], 0)
            joints[le.joint_of(s)][s['class']] += 1
    out = {}
    for j, counts in sorted(joints.items()):
        present = [c for c in order if counts.get(c)]
        groups = []
        for c in present:
            if rule[c + '/' + c] is None:
                groups.append([c])
                continue
            for g in groups:
                if all(rule[c + '/' + o] is not None for o in g):
                    g.append(c)
                    break
            else:
                groups.append([c])
        grounds = links = 0
        for g in groups:
            n = sum(counts[c] for c in g)
            within = sum((counts[c] - 1) * (rule[c + '/' + c] or 0) for c in g if rule[c + '/' + c] is not None)
            between = sum(max(1, rule[g[i] + '/' + g[i + 1]]) for i in range(len(g) - 1))
            k = le._links(n, within + between, circuits)
            grounds += within + between + k
            links += k
        out[j] = {'signals': sum(counts.values()), 'cables': [' + '.join(g) for g in groups], 'grounds': grounds, 'links': links}
    return out


# ---------------------------------------------------------------- outputs

def build(inp, signals):
    pats = harness_patterns(inp)
    base, counts = baseline(inp, pats)
    comp = comparison(inp, base)
    rules = {pk: harness_rule(comp, base, pk) for pk in le.PITCHES}
    tallies = {pk: {str(c): count_under(signals, rules[pk], c) for c in inp['link_options'][pk]} for pk in le.PITCHES}
    return {'patterns': pats, 'counts': counts, 'baseline': base, 'comparison': comp, 'rules': rules, 'tallies': tallies}


def to_json(inp, b):
    c = b['counts']
    doc = {'schema_version': 1, 'task': 'osc-stack-20261114/ST-04 attempt a3 (DS-54)', 'status': inp['status'],
           'written_by': 'scripts/stack/link_electrical/link_electrical.py', 'inputs': 'inputs.json',
           'pattern_counts': {'sizes': c['sizes'], 'triples': {k: len(v) for k, v in c['triples'].items()},
                              'harnesses': c['harness_count'], 'adjacent_signals': c['adjacent_signals'],
                              'signal_beside_rail': c['signal_beside_rail'],
                              'harnesses_ending_on_ground': len(c['outer_ground_harnesses']),
                              'harnesses_starting_on_ground': sum(p['classes'][0] == 'G' for p in b['patterns'])},
           'patterns': [{'id': p['id'], 'classes': p['classes'], 'cut_length_mm': p['cut_length_mm']} for p in b['patterns']],
           'baseline': b['baseline'], 'comparison': b['comparison'],
           'rules': {pk: {k: v for k, v in r.items()} for pk, r in b['rules'].items()}, 'tallies': b['tallies']}
    return json.dumps(le.rnd(doc), indent=1, ensure_ascii=False) + '\n'


def readme_lines(inp, b, a2_counts):
    c = b['counts']
    out = []
    w = out.append
    sizes = ', '.join(f'{v} of {k} contacts' for k, v in sorted(c['sizes'].items()))
    w(f'## The present harness puts a ground between every two signals in all {sum(c["sizes"].values())} harnesses and shares {len(c["triples"])} class pairs across that one ground (attempt a3, DS-54)')
    w('')
    w(f'From `partition.json` (harness header pin maps, both ends in the same order: '
      f'{all(p["same_order_both_ends"] for p in b["patterns"])}) with the class rules of `inputs.json`: {sizes}. '
      f'Signals side by side with no ground between: {len(c["adjacent_signals"])}. Signals beside a rail conductor: '
      f'{len(c["signal_beside_rail"])} ({", ".join(sorted({h for h, _ in c["signal_beside_rail"]}))}, all ANALOGUE). '
      f'Harnesses that start on a ground: {sum(p["classes"][0] == "G" for p in b["patterns"])}; that end on one: '
      f'{len(c["outer_ground_harnesses"])} (the 8-contact pattern S G S G S G S G ends on its fourth ground). DERIVED.')
    w('')
    w('| Class pair across one ground | Triples | Harnesses |')
    w('| --- | --- | --- |')
    for k in sorted(c['triples']):
        w(f'| {k} | {len(c["triples"][k])} | {c["harness_count"][k]} |')
    w('')
    w('The manager\'s count (DS-54) has ANALOGUE/ANALOGUE at 147 triples in 70 harnesses. The difference, 25 triples in 10 '
      'harnesses, is the ten K-to-adapter harnesses K-O1-1 to K-O5-2, whose local nets `OSC_OCT0` to `OSC_OCT5` (kind '
      '"buffered signal/reference") fall to ANALOGUE under the fallback rule. NC positions (two on JR-K-27) are not '
      'signals here. Every other count matches.')
    w('')
    h = inp['harness']
    L0 = inp['cable']['lengths_mm']['value'][0]
    e_hi = inp['cable']['eps_eff']['value'][-1]
    end = inp['cable']['end_equivalent_mm']['value']
    one = 'flat one ground between (rule A)'
    ok = all(x['ratio_to_min'][one] <= 1.0 for x in b['comparison'])
    worst_one = max(x['ratio_to_min'][one] for x in b['comparison'])
    w(f'## Against the quietest present harness, a {L0:g} mm flat link with one ground between {"stays at or below" if ok else "exceeds"} '
      f'it for {"every" if ok else "some"} class pair the harness shares (largest ratio {worst_one:.2f})')
    w('')
    w(f'Harness geometry: round conductors of {h["conductor_diameter_mm"]["value"]} mm (SOURCED, Alpha 6821; stranding taken as '
      f'solid, ASSUMED) at {h["pitch_mm"]["value"]} mm pitch in a flat lay (SOURCED pitch; spacing along the run ASSUMED), '
      f'insulation {h["insulation_diameter_mm"]["value"]} mm (SOURCED) with unknown permittivity (ASSUMED sweep), each harness at '
      f'its own cut length from the loom candidate plus {end:g} mm per end, the whole length in parallel (ASSUMED upper bound). '
      f'Same aggressors, victim impedances and equations as attempt a2, both at ε_eff {e_hi:g}. Capacitance by charge simulation '
      'for round wires (checked against π·ε/acosh(D/2r) in the tests). Every figure is a paper bound (DERIVED from '
      'ASSUMED terms); no harness coupling was ever measured.')
    w('')
    w(f'| Aggressor > victim | Triples | Harness bound, mV: shortest / median / longest cut (mm) | Quietest harness, mV | Flat {le.PITCH_LABEL[le.PITCHES[0]]}, {L0:g} mm: side by side / one ground / two grounds, ratio (dB) | Flat {le.PITCH_LABEL[le.PITCHES[1]]}, {L0:g} mm: same |')
    w('| --- | --- | --- | --- | --- | --- |')
    for key, bb in sorted(b['baseline'].items()):
        cells = []
        for pk in le.PITCHES:
            r = [x for x in b['comparison'] if x['pair'] == key and x['pitch'] == pk][0]
            cells.append(' / '.join(f'{r["ratio_to_min"][n]:.2f} ({20 * math.log10(r["ratio_to_min"][n]):+.1f})'
                                    for n in ('flat side by side', 'flat one ground between (rule A)', 'flat two grounds between')))
        hs = ' / '.join(f'{bb[k]["V"] * 1000:.3g} ({bb[k]["length_mm"]:g})' for k in ('shortest', 'median', 'longest'))
        w(f'| {key} | {bb["triples"]} | {hs} | {bb["min_V"] * 1000:.3g} | {cells[0]} | {cells[1]} |')
    w('')
    w('Ratio = flat-link bound over the quietest harness instance of the same directed pair (ratio ≤ 1 keeps the flat link at or '
      'below every present harness). Rule B (grounds on every side) is in `harness-baseline.json`; it is within a few per cent '
      'of rule A here. The ratio barely depends on ε_eff because both sides use the same value, and the logic rows are '
      'dominated by the inductive term, which ε does not touch.')
    w('')
    rule = b['rules']['pitch_1_0']
    same = all(b['rules'][pk] == rule for pk in le.PITCHES)
    never = sorted({k for k, v in rule.items() if v is None and k.split('/')[0] <= k.split('/')[1]})
    side = sorted({k for k, v in rule.items() if v == 0 and k.split('/')[0] <= k.split('/')[1]})
    w(f'### The harness rule: one ground between every two signals, except {", ".join(side)} side by side; {", ".join(never)} never in one cable')
    w('')
    w(f'Same rule at both pitches: {same}. A class pair the harness never places across one ground ({", ".join(never)}) has no '
      'harness level to match, so it stays in separate cables, as in the harness. WIPER/WIPER is side by side because wipers '
      'are STATIC aggressors; LOGIC/LOGIC because the flat side-by-side bound is below the quietest LOGIC/LOGIC harness.')
    w('')
    w('| Pitch | Circuits | Harness rule, grounds / links | Attempt a2 rule (absolute limits) | Rule A | Rule B inner only (as the harness) | Rule B with outer grounds |')
    w('| --- | --- | --- | --- | --- | --- | --- |')
    for pk in le.PITCHES:
        for cc, rows in b['tallies'][pk].items():
            a2 = a2_counts[pk][cc]
            g2 = sum(x['grounds_rule'] for x in a2.values())
            l2 = sum(x['links_rule'] for x in a2.values())
            ds = ' | '.join(f'{sum(x[k]["grounds"] for x in a2.values())} / {sum(x[k]["links"] for x in a2.values())}'
                            for k in ('rule_A', 'rule_B_inner', 'rule_B_outer'))
            w(f'| {le.PITCH_LABEL[pk]} | {cc} | {sum(x["grounds"] for x in rows.values())} / {sum(x["links"] for x in rows.values())} | {g2} / {l2} | {ds} |')
    w('')
    w('Cable groups per joint under the harness rule: ' + '; '.join(f'{j}: {" | ".join(x["cables"])}' for j, x in b['tallies']['pitch_1_0'][str(inp['link_options']['pitch_1_0'][0])].items()) + '. Same counting method and lower-bound caveat as attempt a2.')
    w('')
    w('### What the comparison shows, and what it does not')
    w('')
    w(f'It shows that, on the same equations and ASSUMED drive and impedance terms, a {L0:g} mm flat link with one ground conductor '
      f'between two signals couples less than the {min(p["cut_length_mm"] for p in b["patterns"]):g} to {max(p["cut_length_mm"] for p in b["patterns"]):g} mm GH harnesses that carry the same class pairs today, mainly because '
      'it is shorter and its return sits closer. It does not show that either is good enough: the present harness is an '
      'unvalidated draft too, its coupling was never computed before nor measured, and the absolute limits of attempt a2 '
      '(' + ', '.join(f'{c} {inp["victims"][c]["limit_V"] * 1000:g} mV' for c in le.VICTIMS) + ' peak) would fail many harness instances as well. Those limits stay ASSUMED criteria for the ruling; '
      'no verdict on them is given here (NEEDS_DESIGN).')
    w('')
    return out
