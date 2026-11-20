"""Render design/stack/thermal/README.md from thermal-screen.json through the calculator.

  thermal_readme.py          write the README
  thermal_readme.py --check  exit 1 when the README on disk differs from the rendering
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thermal as T

README = T.ROOT / 'design/stack/thermal/README.md'
LIMIT_FACTS = {
    'AS3340D': 'AS3340D (ALFA RPAR): theta-JA, Tj max and operating range; the bundle keeps only the advice to supply VEE at -5 V against self-heating',
    'OPA4197IPWR': 'OPA4197IPWR (TI): theta-JA (PW) and Tj max',
    'OPA4197IDR': 'OPA4197IDR (TI): theta-JA (D) and Tj max',
    'LF398M_NOPB': 'LF398M/NOPB (TI): theta-JA (D) and Tj max',
    'LM13700M_NOPB': 'LM13700M/NOPB (TI): theta-JA (D) and Tj max',
    'NOISE2': 'NOISE2 (Electric Druid, PDIP-8): theta-JA and Tj max',
    'REF5050AIDR': 'REF5050AIDR (TI): theta-JA (D), Tj max and the drift curve over 25 to 85 °C',
    'OPA4196IDR': 'OPA4196IDR (TI): theta-JA (D) and Tj max',
    'TMUX7412FRRPR': 'TMUX7412FRRPR (TI): theta-JA (RRP) and Tj max; the thermal pad is tied to AGND',
    'LM393BIDR': 'LM393BIDR (TI): theta-JA (D) and Tj max',
    'SN74HC00DR': 'SN74HC00DR (TI): theta-JA (D) and Tj max',
    'CD74HC221M96': 'CD74HC221M96 (TI): theta-JA (D) and Tj max',
    'TMUX6112PWR': 'TMUX6112PWR (TI): theta-JA (PW) and Tj max',
    'BCM847BS': 'BCM847BS,115 (Nexperia): Rth(j-a) and Tj max',
    'SN74HC14DR': 'SN74HC14DR (TI): theta-JA (D) and Tj max',
    'SN74HC74DR': 'SN74HC74DR (TI): theta-JA (D) and Tj max',
    'CL10A105KB8NNNC': 'CL10A105KB8NNNC (Samsung): none beyond the range for a capacitor of this duty',
}
ORIENT_NAME = {'V': 'standing', 'H': 'lying panel-up'}


def f(x, n=1):
    return '-' if x is None else f'{x:.{n}f}'


def rng(*xs, n=1):
    return f'{min(xs):.{n}f} to {max(xs):.{n}f}'


def srng(*xs, n=1):
    return f'{min(xs):+.{n}f} to {max(xs):+.{n}f}'


def deg(x, n=0):
    return f'{x:.{n}f} °C'


def facts(d=None):
    d = T.load() if d is None else d
    r = {'d': d, 'amb': T.term(d, 'ambient_C')}
    for case in T.CASES:
        r[case] = T.power_map(d, case)
    r['cases_W'] = T.ledger_case_W(d)
    r['outputs'] = T.output_count(d)
    r['areas'] = {k: T.outer_area_m2(d, k) for k in (40, 34, 120)}
    nets, surf = {}, {}
    for depth in (40, 34, 120):
        for o in T.ORIENTS:
            for lv in ('high', 'low'):
                for case in T.CASES:
                    surf[(depth, o, lv, case)] = T.surface_rise(d, depth, o, lv, r[case]['internal_W'])
                    if depth != 34:
                        nets[(depth, o, lv, case)] = T.network(d, depth, o, lv, case)
    r['nets'], r['surf'] = nets, surf
    r['cmp'] = T.comparison(d)
    r['panel'] = T.panel_rows(d)
    r['boards'] = T.board_table(d)
    r['limit_classes'] = T.limit_classes(d)
    return r


def end(r, depth, o, which, key='nets'):
    case, level = T.ENDS[which]
    return r[key][(depth, o, level, case)]


def air_rise(net):
    gaps = net['gaps']
    area = sum(g['area_cm2'] for g in gaps)
    return sum(g['air_rise'] * g['area_cm2'] for g in gaps) / area - net['rise']['shell']


def headline(r):
    lim = r['limit_classes']
    cmp_ = r['cmp']
    spans = {}
    for o in T.ORIENTS:
        worst = max(cmp_[(s, 40)]['orients'][o]['worst']['T_C'] for s in lim)
        best = max(cmp_[(s, 40)]['orients'][o]['best']['T_C'] for s in lim)
        spans[o] = (best, worst)
    shift = T.depth_shift_K(r['d'], lim)
    limits = sorted({cmp_[(s, 40)]['limit']['limit_C'] for s in lim})
    return depth_state({depth: [cmp_[(s, depth)]['word'] for s in lim] for depth in T.DEPTHS}), spans, shift, limits


def depth_state(words):
    per = {depth: T.worst_word(ws) for depth, ws in words.items() if ws}
    if not per:
        return 'has no plane in either case depth'
    if set(per.values()) == {'NOT SHOWN'} and len(per) == len(words):
        return 'is NOT SHOWN met in either case depth'
    if len(set(per.values())) == 1 and len(per) == len(words):
        return f"is {next(iter(per.values()))} in both case depths"
    return 'reads ' + ' and '.join(f"{w} at {k} mm" for k, w in per.items())


def limit_kind(cls):
    return {'ABSOLUTE_MAXIMUM': 'absolute maximum', 'RECOMMENDED_OPERATION': 'operating range'}.get(cls, 'range')


def temps_at(comparisons):
    return [c['orients'][o][e]['T_C'] for c in comparisons for o in T.ORIENTS if c['orients'][o] for e in T.ENDS]


def pot_clause(r):
    d = r['d']
    syms = pot_symbols(d)
    rows = [x for x in r['panel'] if x['symbol'] in syms]
    if not rows:
        return None
    lims = {(T.retained_limit(d, s) or {}).get('limit_C') for s in syms}
    kinds = {limit_kind((T.retained_limit(d, s) or {}).get('class')) for s in syms}
    if None in lims or len(lims) != 1 or len(kinds) != 1:
        return None
    boards = sorted({x['board'] for x in rows})
    state = depth_state({depth: [x['depths'][depth]['word'] for x in rows if x['depths'][depth]['word']] for depth in T.DEPTHS})
    spans = ', '.join(f"{rng(*temps_at([x['depths'][depth] for x in rows]))} °C at {depth} mm" for depth in T.DEPTHS)
    return (f"the {next(iter(lims)):+.0f} °C {next(iter(kinds))} printed for the panel pots {state} "
            f"({join_names(boards)} {spans})")


def k_clause(r):
    lim = r['limit_classes']
    if not lim:
        return None
    state, _, _, limits = headline(r)
    spans = ', '.join(f"{rng(*temps_at([r['cmp'][(s, depth)] for s in lim]))} °C at {depth} mm" for depth in T.DEPTHS)
    return (f"the {' and '.join(f'{x:.0f} °C' for x in limits)} limit of {join_names(lim)} on K {state} "
            f"(board at the part {spans})")


def header(r):
    lying = lying_front_shift(r)
    clauses = [x for x in (pot_clause(r), k_clause(r)) if x]
    if lying:
        clauses.append(f"lying flat, the 40 mm stack reads the front boards {rng(*lying)} K above the 120 mm case"
                       if min(lying) >= 0 else f"lying flat, the 40 mm stack reads the front boards {srng(*lying)} K against the 120 mm case")
    return [f"# ST-05 thermal paper screen: at {r['amb']:g} °C ambient in a closed case {'; '.join(clauses)}; #64 measures it", '',
            f"State: **{r['d']['status']}**. Generated by `python3 scripts/stack/thermal/thermal_readme.py` from `thermal-screen.json`; "
            f"do not edit by hand. A recomputable estimate on paper for the direct board stack at the {r['amb']:g} °C ambient corner "
            'of E19. Every board is an unvalidated draft; nothing is measured, nothing is selected, and #64 (the physical thermal '
            'test) stays NOT RUN. The result is a recorded risk of the instrument in a closed case and no check of the gate (DS-94). '
            'Sources are pinned by the object or row a term reads. Run `extract_inputs.py --check` to see whether a pinned source '
            'has changed.', '']


def same(text, b, minimum_places):
    places = max(len(text.split('.')[1]) if '.' in text else 0, minimum_places)
    return round(b, places) == round(float(text), places)


def plan_check(r):
    d = r['d']
    plan = T.term(d, 'plan_heat_W')
    n, c = r['normal'], r['contract']
    texts = d['inputs']['plan_heat_row_text']
    places = T.term(d, 'plan_compare_decimals')
    verdict = ['reproduced' if same(p, x['input_W'], places) else 'differs' for p, x in zip(texts, (n, c))]
    head = 'the screen reproduces both' if verdict == ['reproduced', 'reproduced'] else \
        'the screen reads ' + ' and '.join(f"{f(x['input_W'], 2)} W" for x in (n, c))
    return [f"## The plan page's heat row reads {plan[0]:g} W and {plan[1]:g} W; {head}", '',
            'Attempt a1 reproduced the 31 % and the two rise ranges of the earlier row by the plan\'s own method and corrected '
            'its 35.4 W, which is the ledger\'s fault case with a shorted S&H resistor, to the normal planning load (DS-92); the '
            'corrected row states neither, and this screen no longer reads them.', '',
            '| Figure | Plan page | This screen | Reading |', '| --- | --- | --- | --- |',
            f"| Normal planning load | {plan[0]:g} W | {f(n['input_W'], 3)} W input, {f(n['internal_W'], 2)} W inside | {verdict[0]} |",
            f"| Supply contract | {plan[1]:g} W | {f(c['input_W'], 3)} W input, {f(c['internal_W'], 2)} W inside | {verdict[1]} |", '']


def item1(r):
    d = r['d']
    n, c, lw = r['normal'], r['contract'], r['low']
    areas = T.board_areas_cm2(d['inputs']['planes_40'])
    k_share = n['boards']['K'] / n['internal_W']
    lows = T.low_heat_rows(d)
    by_fact = {}
    rows = {x['id']: x for x in T.term(d, 'ledger_rows')}
    for rid, x in lows.items():
        w = T.row_power_W(d, rows[rid]['mA']) - T.row_power_W(d, x['mA'])
        k = (x['symbol'], x['fact'])
        by_fact[k] = by_fact.get(k, 0.0) + w
    low_text = '; '.join(f"{sym} by {f(w, 2)} W (`{fact}`)" for (sym, fact), w in sorted(by_fact.items()))
    lines = [f"## 1. The ledger puts {f(n['internal_W'], 2)} W inside the instrument at the normal planning load and "
             f"{f(lw['internal_W'], 2)} W at the low-heat load; the contract's {f(c['internal_W'], 2)} W is an outer row; "
             f"K carries {f(100 * k_share, 0)} %; the residual is {f(abs(n['residual_W']), 6)} W", '',
             f"Every ledger row and every one of the {len(d['inputs']['ic_packages'])} IC packages is assigned to the board "
             'that carries it in the partition (rules in `row_rules`; only the IC, NOISE2, REF and LOGIC rules are bound to '
             f"packages, the rest are ASSUMED). {r['outputs']} outputs at 5 V into 10 kohm dissipate "
             f"{f(1000 * n['external_W'], 0)} mW outside. The bleeder residual of the ledger total, "
             f"{f(T.row_power_W(d, T.all_rows(d)[-1]['mA']), 3)} W, is the two inlet bleeders and sits on the ASSUMED inlet board. "
             'The supply is outside (Q6) and not in the map. All LEDs are on. The contract case spreads the excess over the '
             'planning map rail by rail (ASSUMED) and enters no verdict.', '',
             f"The low-heat load (DS-95) takes the typical quiescent current at 25 °C of each part whose bundle holds one, "
             f"row by row, and lowers the two-feed total by the same current: {low_text}. It is "
             f"{f(lw['input_W'], 2)} W input, a lower end and no prediction; no ledger file is changed. The AS3340D typical "
             'table is at 20 °C and +15 V and is not taken.', '',
             '| Board | Normal planning, W | Low-heat, W | Contract (outer row), W | Board area, cm2 | Normal density, mW/cm2 |',
             '| --- | --- | --- | --- | --- | --- |']
    for b in sorted(n['boards'], key=lambda b: (-n['boards'][b], b)):
        wn, wl, wc = n['boards'][b], lw['boards'].get(b, 0.0), c['boards'].get(b, 0.0)
        lines.append(f"| {b} | {f(wn, 3)} | {f(wl, 3)} | {f(wc, 3)} | {f(areas[b], 1)} | {f(1000 * wn / areas[b], 2)} |")
    lines += [f"| Outside: output loads | {f(n['external_W'], 3)} | {f(lw['external_W'], 3)} | {f(c['external_W'], 3)} | - | - |",
              f"| Ledger input power (12/12/5 V) | {f(n['input_W'], 3)} | {f(lw['input_W'], 3)} | {f(c['input_W'], 3)} | - | - |",
              f"| Residual | {f(n['residual_W'], 6)} | {f(lw['residual_W'], 6)} | {f(c['residual_W'], 6)} | - | - |", '']
    by_rule = ', '.join(f"{k} {f(v, 2)} W" for k, v in sorted(n['rules_W'].items(), key=lambda x: -x[1]))
    lines += [f"Input power by rule at the normal load: {by_rule}. The ASSUMED rules carry "
              f"{f(sum(v for k, v in n['rules_W'].items() if k not in ('IC', 'NOISE2', 'REF', 'LOGIC')), 2)} W; moving all of it "
              'between K and the front boards is the widest error of the map.', '',
              'Not in the ledger and not added: the SUB divider and gating on +5 V (UNSOURCED until ST-11 refreshes the ledger), '
              'the lower count of octave receivers without the OSC2 and OSC4 selectors (not credited, so the map stays high), '
              f"the I2R of the {T.term(d, 'post_count')} posts (at most {f(1000 * T.post_i2r_bound_W(d), 1)} mW with every contract rail current through "
              f"one {1000 * T.term(d, 'post_joint_ohm'):g} mOhm joint), and the flat links (at most {T.term(d, 'link_ground_current_A'):g} A "
              'on a ground, DS-62; conductor resistance UNSOURCED). '
              'The ledger charges magnitude LEDs and outputs on both analogue rails at once, which is high by up to a factor of two '
              'for those rows. The ledger names OPA4197IDR where the netlist has OPA4197IPWR in '
              f"{len({k[0][0] for k in T.symbol_mismatches(d)})} instances; same die and allowance, so the map pools the two packages.", '']
    return lines


def item2(r):
    d = r['d']
    s, nets, a, amb = r['surf'], r['nets'], r['areas'], r['amb']

    def span(depth, o, key='surf'):
        return end(r, depth, o, 'best', key), end(r, depth, o, 'worst', key)
    worse = max(T.ORIENTS, key=lambda o: (s[(40, o, 'low', 'normal')], o))
    k40 = [amb + end(r, 40, o, w)['rise']['K'] for o in T.ORIENTS for w in T.ENDS]
    lines = [f"## 2. At {amb:g} °C ambient the 40 mm case's surface rises {rng(*[x for o in T.ORIENTS for x in span(40, o)])} K "
             f"against {rng(*[x for o in T.ORIENTS for x in span(120, o)])} K for 120 mm; {ORIENT_NAME[worse]} is the worse "
             f"orientation; K's mean reads {rng(min(k40), max(k40), n=0)} °C closed at 40 mm", '',
             f"Outer box: the internal {d['inputs']['enclosure_internal_xy_mm']} mm plus a {T.term(d, 'wall_mm')} mm wall (ASSUMED, 1 to 3 mm) "
             f"at the sides and rear; the depth includes the {T.term(d, 'panel_thickness_mm')} mm panel. Coefficients (all ASSUMED): "
             f"vertical faces {T.term(d, 'h_conv_vertical')} W/m2K, upward faces {T.term(d, 'h_conv_up')} W/m2K, the face resting "
             f"on a table {T.term(d, 'h_conv_resting'):g}, finish emissivity {T.term(d, 'eps_case')}, radiation to surroundings at ambient. Each range runs from "
             'the best end (low-heat load, high coefficients) to the worst end (planning load, low coefficients); the contract '
             'column is the outer row at the low coefficients. Standing: panel vertical, base face resting. Lying: panel horizontal '
             'facing up, rear wall resting. Inside: the network of item 3. The 34 mm row is surface only: the stack does not fit it '
             f"({f(d['inputs']['stack']['enclosure_depth_cases'][1]['rear_part_clearance_mm'], 1)} mm rear clearance; DS-17).", '',
             '| Case | Outer area, m2 | Surface rise, K | Surface rise, contract, K | Internal air above surface, K | K mean rise above ambient, K | JR rise above ambient, K |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for depth in (40, 34, 120):
        for o in T.ORIENTS:
            name = f"{depth} mm, {ORIENT_NAME[o]}, closed, supply outside"
            sc = f(s[(depth, o, 'low', 'contract')])
            if depth == 34:
                lines.append(f"| {name} | {f(a[depth], 4)} | {rng(*span(depth, o))} | {sc} | not applicable: the stack does not fit | - | - |")
                continue
            b, w = end(r, depth, o, 'best'), end(r, depth, o, 'worst')
            lines.append(f"| {name} | {f(a[depth], 4)} | {rng(*span(depth, o))} | {sc} | {rng(air_rise(b), air_rise(w))} | "
                         f"{rng(b['rise']['K'], w['rise']['K'])} | {rng(b['rise']['JR'], w['rise']['JR'])} |")
    for label, kw in sensitivity_rows(d):
        b = T.network(d, 40, 'V', T.ENDS['best'][1], T.ENDS['best'][0], **kw['best'])
        w = T.network(d, 40, 'V', T.ENDS['worst'][1], T.ENDS['worst'][0], **kw['worst'])
        lines.append(f"| {label} | {f(a[40], 4)} | {rng(b['rise']['shell'], w['rise']['shell'])} | - | "
                     f"{rng(air_rise(b), air_rise(w))} | {rng(b['rise']['K'], w['rise']['K'])} | {rng(b['rise']['JR'], w['rise']['JR'])} |")
    w1, w3 = T.outer_area_m2(d, 40, 1.0), T.outer_area_m2(d, 40, 3.0)
    lines += ['', f"The wall allowance moves the 40 mm area from {f(w1, 4)} to {f(w3, 4)} m2 ({f(100 * (w3 / w1 - 1), 1)} %). "
              'The supply-inside rows add the supply loss at the shell only; no pocket for a supply exists in the 40 mm stack '
              f"({f(rear_gap_mm(d), 1)} mm behind K's rear parts), so a supply inside needs a deeper case or a side "
              'pocket (Q6, #57).', '']
    return lines


def rear_gap_mm(d):
    return T.term(d, 'depth_cases_mm')[0] + d['inputs']['stack']['K_rear_parts_z_mm']


def sensitivity_rows(d):
    e_lo, e_hi = T.lo_hi(d, 'supply_efficiency')
    bare = T.term(d, 'eps_bare_metal')
    return [
        (f"40 mm standing, supply inside, efficiency {e_hi} to {e_lo}",
         {'best': {'supply': 'inside', 'eta': e_hi}, 'worst': {'supply': 'inside', 'eta': e_lo}}),
        (f"40 mm standing, bare metal inside and out (emissivity {bare})",
         {'best': {'eps_override': bare}, 'worst': {'eps_override': bare}}),
    ]


def plane_text(d):
    groups = {}
    for b, v in d['inputs']['planes_40'].items():
        key = (v['face_z_mm'], v['face_z_mm'] - v['thickness_mm'])
        groups.setdefault(key, []).append(b)
    parts = [f"panel rear at {-T.term(d, 'panel_thickness_mm'):g} mm"]
    for (face, rear), bs in sorted(groups.items(), key=lambda x: -x[0][0]):
        parts.append(f"{' and '.join(sorted(bs))} {face:g}/{rear:g}")
    return ', '.join(parts) + f", rear wall {-T.term(d, 'depth_cases_mm')[0]:g}"


def join_names(names):
    names = list(names)
    if not names:
        return 'no class'
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ' and ' + names[-1]


def radiation_shares(d, net, pairs):
    k_air = T.term(d, 'air')['k']
    out = []
    for g in net['gaps']:
        if not any(p['upper'] == g['upper'] and p['lower'] == g['lower'] and p['gap_mm'] == g['gap_mm'] for p in pairs):
            continue
        conv = g['Nu'] * k_air / (g['gap_mm'] / 1000.0)
        out.append((g['h'] - conv) / g['h'])
    return out


def item3(r):
    d = r['d']
    pairs40 = T.facing_pairs(d, 40)
    n = r['normal']
    areas = T.board_areas_cm2(d['inputs']['planes_40'])
    rec = T.term(d, 'link_figures')
    big = [p for p in pairs40 if p['area_mm2'] >= 1000]
    ends = [end(r, 40, o, w) for o in T.ORIENTS for w in T.ENDS]
    nus = [g['Nu'] for net in ends for g in net['gaps']]
    shares = [x for net in ends for x in radiation_shares(d, net, big)]
    k_fr = sum(p['area_mm2'] for p in pairs40 if p['lower'] == 'K' and p['upper'] != 'shell') / 100
    slot_pct = 100 * rec['slot_area_mm2'] / (100 * k_fr)
    loop_pct = 100 * rec['loop_plan_area_mm2'] / (100 * k_fr)
    lines = [f"## 3. Every gap of the 40 mm stack has Nu {f(min(nus), 2)} to {f(max(nus), 2)}; radiation carries "
             f"{rng(100 * min(shares), 100 * max(shares), n=0)} % of the heat across the facing pairs of 10 cm2 or more; the slots cover "
             f"{f(slot_pct, 1)} % and the cable loops at most {f(loop_pct, 1)} % of where front boards face K", '',
             f"Gaps from `candidate.planes`: {plane_text(d)}. Densities are board totals at the normal load over "
             'the board area. Nu runs from 1 (conduction only, ASSUMED lower bound) to the ASSUMED enclosed-layer correlations at the '
             f"best end; h adds the plate-to-plate radiation (board emissivity {rng(*T.lo_hi(d, 'eps_board'), n=2)}).", '',
             '| Facing pair (front, rear) | Gap, mm | Facing area, cm2 | Density, front member, mW/cm2 | Density, rear member, mW/cm2 | Nu standing, best end | Nu lying, best end | h, W/m2K |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']

    def dens(b):
        return '0 (case)' if b == 'shell' else f(1000 * n['boards'].get(b, 0.0) / areas[b], 2)

    def find(net, p):
        return next(g for g in net['gaps'] if g['upper'] == p['upper'] and g['lower'] == p['lower'] and g['gap_mm'] == p['gap_mm'])
    bv, bh = end(r, 40, 'V', 'best'), end(r, 40, 'H', 'best')
    wv = end(r, 40, 'V', 'worst')
    for p in big:
        name = f"{'panel' if p['upper'] == 'shell' else p['upper']} / {'rear wall' if p['lower'] == 'shell' else p['lower']}"
        gv, gh, gl = find(bv, p), find(bh, p), find(wv, p)
        lines.append(f"| {name} | {f(p['gap_mm'], 1)} | {f(p['area_mm2'] / 100, 1)} | {dens(p['upper'])} | {dens(p['lower'])} | "
                     f"{f(gv['Nu'], 2)} | {f(gh['Nu'], 2)} | {rng(gl['h'], max(gv['h'], gh['h']))} |")
    small = sum(p['area_mm2'] for p in pairs40 if p['area_mm2'] < 1000) / 100
    lines += ['', f"Pairs below 10 cm2 (adapters, P over the adapters, EL over K's edge) total {f(small, 1)} cm2 and are in the network. "
              f"The gate record of the room study holds {rec['placed']} of {rec['links']} links placed, {rec['slots']} slots in K of "
              f"{f(rec['slot_area_mm2'] / 100, 1)} cm2 in all, cable loops of at most {f(rec['loop_plan_area_mm2'] / 100, 1)} cm2 and "
              f"cable of {f(rec['cable_plan_area_mm2'] / 100, 1)} cm2 in plan (read by extraction, pin `link-gate-figures`). The slots "
              f"are mostly filled by the cable and add no credited air path. The loops are at most {f(loop_pct, 1)} % of the "
              f"{f(k_fr, 0)} cm2 where front boards face K: as a radiation shield they lower h by at most that fraction where they "
              'lie, and they cannot drive a gap below conduction except where cable replaces air. The screen carries them as this '
              'bound, not in the network. No airflow is claimed: the vented rows of item 6 are a bound.', '']
    return lines


def place_text(d, x):
    where = x['board'] if x['cell'] is None else f"K {T.cell_name(d, x['cell'])}"
    lat = '' if x['lateral_K'] is None else f" ({x['lateral_K'] + 0.0 if abs(x['lateral_K']) >= 0.05 else 0.0:+.1f} K lateral)"
    return f"{x['ref']}, {where}{lat}"


def class_shifts(a, b):
    out = {}
    for o in T.ORIENTS:
        if a['orients'].get(o) is None or b['orients'].get(o) is None:
            out[o] = None
            continue
        out[o] = {e: a['orients'][o][e]['T_C'] - b['orients'][o][e]['T_C'] for e in T.ENDS}
    return out


def share_text(shifts, limit):
    parts = []
    for o in T.ORIENTS:
        x = shifts.get(o)
        if x is None:
            parts.append(f"{ORIENT_NAME[o]} -")
            continue
        mark = ', share of the 40 mm stack' if any(v > limit for v in x.values()) else ''
        parts.append(f"{ORIENT_NAME[o]} {x['best']:+.1f} / {x['worst']:+.1f}{mark}")
    return '; '.join(parts)


def comparison_rows(r, symbols):
    d = r['d']
    rows = []
    for s in symbols:
        for depth in T.DEPTHS:
            c = r['cmp'][(s, depth)]
            lim = 'NO LIMIT RETAINED' if c['limit'] is None else f"{c['limit']['limit_C']:.0f} °C (`{c['limit']['fact_id']}`)"
            o = c['orients']
            share = share_text(class_shifts(r['cmp'][(s, 40)], r['cmp'][(s, 120)]), T.term(d, 'stack_share_K')) if depth == 40 else '-'
            rows.append(f"| {s} | {c['places']} | {depth} mm | {lim} | "
                        f"{f(o['V']['best']['T_C'])} to {f(o['V']['worst']['T_C'])} | {o['V']['word']} | "
                        f"{f(o['H']['best']['T_C'])} to {f(o['H']['worst']['T_C'])} | {o['H']['word']} | "
                        f"{place_text(d, o[c['worse']]['worst'])} | **{c['word']}** | {share} |")
    return rows


def bleeder_lines(r):
    d = r['d']
    rth = T.term(d, 'bleeder_rth_K_per_W')
    mw = T.term(d, 'bleeder_mW')
    lim = T.term(d, 'solder_joint_limit_C')
    region = T.term(d, 'ds96_bleeder_region_mm')
    notes = {(depth, o): T.bleeder_note(d, depth, o) for depth in T.DEPTHS for o in T.ORIENTS}
    allb = [x for v in notes.values() for x in v]
    worst = max(allb, key=lambda x: x['body_C'])
    lines = [f"### Bleeder note for #57: at the worst end the bleeder body reads {rng(min(x['body_C'] for x in allb), max(x['body_C'] for x in allb), n=0)} °C, "
             f"against the {lim:.0f} °C solder joint; the board at its places allows {rng(min(x['allowed_mW'] for x in allb), max(x['allowed_mW'] for x in allb), n=0)} mW per body against {f(mw, 1)} mW", '',
             f"A conditional note and no verdict (DS-95, DS-96): the board at the place plus {f(mw, 1)} mW × {rth:.0f} K/W, the bundle's generic "
             f"mounting estimate, against {lim:.0f} °C at the joint, at the planning load with the low coefficients. The places are the floorplan's "
             f"{', '.join(x['ref'] for x in notes[(40, 'V')])} (`io-partition-exact-refs`); the part and its place are the inlet's (#57). "
             f"DS-96: two bodies that share the current and a place outside x {region[0]:g} to {region[2]:g}, y {region[1]:g} to "
             f"{region[3]:g} of K close this on paper; {sum(1 for x in notes[(40, 'V')] if not x['in_region'])} of "
             f"{len(notes[(40, 'V')])} present places lie outside that box.", '',
             '| Place | Depth, orientation | Board at the place, °C | Body, °C | Margin to the joint, K | Allowed per body, mW |',
             '| --- | --- | --- | --- | --- | --- |']
    for (depth, o), xs in notes.items():
        for x in xs:
            lines.append(f"| {x['ref']} ({x['xy'][0]:g}, {x['xy'][1]:g}) | {depth} mm, {ORIENT_NAME[o]} | {f(x['board_C'])} | "
                         f"{f(x['body_C'])} | {x['margin_K']:+.1f} | {f(x['allowed_mW'], 0)} |")
    return lines + ['']


def item4(r):
    d = r['d']
    amb = r['amb']
    lim = r['limit_classes']
    nolim = T.no_limit_classes(d)
    state, spans, shift, limits = headline(r)
    contract = {(depth, o): amb + r['nets'][(depth, o, 'low', 'contract')]['rise']['K'] for depth in T.DEPTHS for o in T.ORIENTS}
    split = T.as3340_split_W(d)
    shift_all = T.depth_shift_K(d, lim + nolim)
    big = largest_shift(r, lim + nolim)
    limits_text = ' and '.join(f'{x:.0f} °C' for x in limits) or 'no'
    lines = [f"## 4. The {limits_text} limit of {join_names(lim)} {state}; {len(nolim)} IC classes read NO LIMIT RETAINED "
             f"and NOT SHOWN; on the classes with a limit the 40 mm case moves the board at the part by {srng(*shift, n=1)} K against 120 mm", '',
             f"The comparison of DS-95: one temperature, the board at the part (K's mean plus the smoothed lateral rise of the hottest "
             f"{T.term(d, 'cell_mm'):g} mm cell of K that holds a part of the class; the board's mean off K), against the limit of the "
             'exact part. Worst end: planning load, low coefficients. Best end: low-heat load, high coefficients, read on the board '
             'of the worst end. The class word is the worst word of the two orientations. MET ON PAPER: worst end at or '
             'below the limit; EXCEEDED ON PAPER: best end above it; NOT SHOWN otherwise and wherever no limit is retained. '
             f"No limit is borrowed from a part of the same family and no junction temperature is stated. Places: {place_source(d)}. "
             'The CL10A105KB8NNNC places are the floorplan places of the references that the partition report gives the exact part '
             '(`io-partition-exact-refs`). DS-94 reads the 40 mm case more than 5 K above the 120 mm case on this comparison as a '
             f"cost of the stack: the classes with a limit read {srng(*shift, n=1)} K. Across every class the shift is "
             f"{srng(*shift_all, n=1)} K; the largest in size is {big['symbol']} on {big['board']} ({big['shift']:+.1f} K, "
             f"{ORIENT_NAME[big['orient']]}, {big['end']} end).", '',
             '| Exact part class | Places | Case | Limit | Standing, best to worst, °C | Standing | Lying, best to worst, °C | Lying | Hottest place, worse orientation, worst end | Word | Shift 40 against 120 mm, best / worst end, K |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |'] + comparison_rows(r, lim + nolim)
    lines += ['', f"Outer row, no verdict: at the contract ({f(r['contract']['input_W'], 1)} W) with the low coefficients K's mean reads "
              + ', '.join(f"{f(v)} °C {ORIENT_NAME[o]} at {depth} mm" for (depth, o), v in contract.items()) + '. '
              f"The AS3340D row includes its VEE driver: {f(1000 * split['core_W'], 0)} mW in the core and "
              f"{f(1000 * split['vee_driver_W'], 0)} mW in the OPA4197 buffer. The packages of the classes with a limit take at most "
              f"{f(1000 * max_limit_package_W(d), 0)} mW each in the ledger, "
              'and the gaps carry heat by conduction, so the air at the part has the temperature of the board (DS-95).', '']
    return lines + bleeder_lines(r)


def largest_shift(r, symbols):
    best = None
    for s in symbols:
        a, b = r['cmp'][(s, 40)], r['cmp'][(s, 120)]
        for o in T.ORIENTS:
            for e in T.ENDS:
                x = a['orients'][o][e]['T_C'] - b['orients'][o][e]['T_C']
                if best is None or abs(x) > abs(best['shift']):
                    best = {'symbol': s, 'board': a['orients'][o][e]['board'], 'orient': o, 'end': e, 'shift': x}
    return best


def max_limit_package_W(d):
    syms = set(T.limit_classes(d))
    per = T.package_powers(d)
    return max([per[p['ref']] for p in d['inputs']['ic_packages'] if p['symbol'] in syms and p['ref'] in per] or [0.0])


def place_source(d):
    ps = d['inputs']['place_source']
    if ps['read'] == 'floorplan':
        return 'the floorplan (the gate record holds no `displaced_k_ic_packages`; no package moved)'
    return (f"the gate record's `displaced_k_ic_packages`: {ps['moved']} of the {ps['listed']} listed packages are read at their "
            f"new place; the {ps['kept']} listed packages whose `new` is null have no position and are read at their floorplan place, "
            "as is every package not listed")


def item5(r):
    d = r['d']
    rows = T.sensitive_table(d)
    cells, meta = T.k_cells_cached(d, 'normal', 40, 'V', 'low')
    cells120, meta120 = T.k_cells_cached(d, 'normal', 120, 'V', 'low')
    region = T.warm_region(d, cells)
    box = region['box_mm']
    hot = T.hot_packages(d)
    near = T.term(d, 'hot_within_mm')
    n40, n120 = r['nets'][(40, 'V', 'low', 'normal')], r['nets'][(120, 'V', 'low', 'normal')]
    ks40, ks120 = n40['rise']['K'] - n40['rise']['shell'], n120['rise']['K'] - n120['rise']['shell']
    lat40 = [c['rise_smooth_K'] for c in cells.values()]
    lat120 = [c['rise_smooth_K'] for c in cells120.values()]
    spread40, spread120 = max(lat40) - min(lat40), max(lat120) - min(lat120)
    cores = [x for x in rows if x['function'].endswith('core')]
    in_cores = sum(1 for x in cores if T.in_box(box, x['xy']))
    octave = next(x for x in rows if x['function'].startswith('OCTAVE'))
    oct_text = 'and the octave reference' if T.in_box(box, octave['xy']) else 'but not the octave reference'
    with_hot = sum(1 for x in rows if x['hot_near'])
    region_text = f"x {box[0]:g} to {box[2]:g}, y {box[1]:g} to {box[3]:g}, {rng(*region['lateral_K'])} K above K's mean"
    lines = [f"## 5. {in_cores} of the {len(cores)} oscillator cores {oct_text} lie in K's warm region ({region_text}); "
             f"{with_hot} of the {len(rows)} sensitive sites have a package of {1000 * T.term(d, 'hot_package_W'):.0f} mW or more within "
             f"{near:g} mm", '',
             f"Regions are {T.term(d, 'cell_mm'):g} mm cells of K in the partition frame, the grid taken from K's outline. The lateral "
             f"figure is the cell's density against K's mean over K's coupling to its surroundings ({f(meta['h_K'], 1)} W/m2K at 40 mm), "
             f"smoothed over the ASSUMED copper spreading length of {f(meta['L_s_mm'], 0)} mm (the no-spreading bound is up to "
             f"{f(max(c['rise_bound_K'] for c in cells.values()), 1)} K). Planning load, standing, low coefficients. The warm region is "
             f"the bounding box of the cells at {100 * T.term(d, 'hot_region_fraction'):.0f} % or more of the hottest cell "
             f"({T.cell_name(d, region['hottest'])}; ASSUMED reporting rule). K stands {f(ks40, 1)} K above the case at 40 mm against "
             f"{f(ks120, 1)} K at 120 mm, and its lateral spread is {f(spread40, 1)} K against {f(spread120, 1)} K. The hot set is "
             f"every K package of {1000 * T.term(d, 'hot_package_W'):.0f} mW or more at the planning load: {len(hot)} packages with "
             f"{f(sum(h['W'] for h in hot), 2)} W. Pitch calibration stays at 25 °C; these are risks, not drift predictions.", '',
             f"| Function | Part | Region on K | Lateral, 40 mm, K | Lateral, 120 mm, K | Hot packages within {near:g} mm | Their power, W |",
             '| --- | --- | --- | --- | --- | --- | --- |']
    listed = [x for x in rows if not (x['function'].endswith('REF5050') and not x['function'].startswith(('OCTAVE', 'H1', 'H2', 'F')))]
    for x in listed:
        lines.append(f"| {x['function']} | {x['ref']} | {x['cell'] or 'outside the cells of K'} | {f(x['rise_40'], 1)} | "
                     f"{f(x['rise_120'], 1)} | {x['hot_near']} | {f(x['hot_near_W'], 2)} |")
    others = [x for x in rows if x not in listed]
    warm_refs = [x for x in others if T.in_box(box, x['xy'])]
    lines += ['', f"The other {len(others)} local REF5050 references (E, W, A and M modules) are not listed row by row: "
              f"{len(warm_refs)} lie in the warm region ({', '.join(x['ref'] for x in warm_refs) or 'none'}), and "
              f"{sum(1 for x in others if x['hot_near'])} have a hot package within {near:g} mm. A move of {T.term(d, 'move_mm'):g} mm "
              f"shifts heat between neighbouring cells at most and cannot leave a warm region {box[2] - box[0]:g} by "
              f"{box[3] - box[1]:g} mm (DS-98).", '']
    return lines


def k_mean(d, depth, o, which, **kw):
    case, level = T.ENDS[which]
    return T.network(d, depth, o, level, case, **kw)['rise']['K']


def item6(r):
    d = r['d']
    g_posts, area = T.post_conductance(d)
    v_lo, v_hi = T.lo_hi(d, 'vent_area_cm2')
    f_lo, f_hi = T.lo_hi(d, 'h_conv_feet')
    base = {(o, w): k_mean(d, 40, o, w) for o in T.ORIENTS for w in T.ENDS}
    vents = {(v, o, w): base[(o, w)] - k_mean(d, 40, o, w, vent_cm2=v) for v in (v_lo, v_hi) for o in T.ORIENTS for w in T.ENDS}
    feet = {w: base[('H', w)] - k_mean(d, 40, 'H', w, h_resting=(f_lo if w == 'worst' else f_hi)) for w in T.ENDS}
    net = end(r, 40, 'V', 'worst')
    g_fk = sum(g['h'] * g['area_cm2'] * 1e-4 for g in net['gaps'] if g['lower'] == 'K' and g['upper'] != 'shell')
    deep = k_mean(d, 120, 'V', 'worst')
    red = (r['normal']['internal_W'] - r['low']['internal_W'])
    per_w = (base[('V', 'worst')] - T.network(d, 40, 'V', 'low', 'low')['rise']['K']) / red
    bare = T.term(d, 'eps_bare_metal')
    metal = [k_mean(d, 40, 'V', w, eps_override=bare) for w in T.ENDS]
    vent_text = '; '.join(f"{v:g} cm2 {ORIENT_NAME[o]}: {rng(vents[(v, o, 'best')], vents[(v, o, 'worst')])} K"
                          for v in (v_lo, v_hi) for o in T.ORIENTS)
    rows = [
        ('Vent slots in the side or rear walls', 'listed (DS-96: enclosure, to the owner)',
         f"Upper bound of the fall of K's mean, best to worst end: {vent_text}; the air is taken to leave at the area-mean board temperature",
         f"Dust and EMC on an open case; the frame; the {T.term(d, 'service_apertures')} K service apertures are retired, not a vent path; the gaps must stay open along the upper and lower edges of K (DS-96, ST-12)",
         'A vent and case drawing; a flow estimate with the cable loops in the gaps; then #64'),
        ('Case on feet, lying', 'listed (DS-96: enclosure, to the owner)',
         f"The resting rear wall carries {f_lo:g} to {f_hi:g} W/m2K (ASSUMED) in place of nothing: K's mean falls by "
         f"{f(feet['worst'])} K at the worst end ({f_lo:g} W/m2K) and {f(feet['best'])} K at the best end ({f_hi:g} W/m2K)",
         'The feet and the clearance under the case are the enclosure\'s', 'An enclosure drawing; then #64'),
        ('Metal rear wall used as a spreader, high-emissivity inside', 'not followed (DS-96)',
         f"A bare metal case (emissivity {bare}) reads K at {rng(*metal)} K above ambient, standing, best to worst end",
         f"K's rear parts are {f(rear_gap_mm(d), 1)} mm from the wall: insulation and a shorting check; EMC grounding of the wall",
         'Enclosure material, finish and emissivity; an insulation layer and its conductance'),
        (f"Conduction through the {T.term(d, 'post_count')} brass posts and the {T.term(d, 'sleeve_count')} sleeves", 'not followed (DS-96)',
         f"Brass body alone {rng(*g_posts, n=2)} W/K from K to the front boards ({f(1e6 * area, 1)} mm2 per post, ASSUMED bore), "
         f"beside the {f(g_fk, 2)} W/K of the facing gaps; not credited, because the front boards have no path to the case",
         'The posts carry the supply current and are fixed by DS-33 and DS-75; the ceramic-part strain rule of DS-42',
         'Thermal contact resistance of the nickel-brass face on the land (UNSOURCED); a front-board-to-case path'),
        ('Larger case depth (120 mm row)', 'not followed (DS-96)',
         f"K's mean {deep - base[('V', 'worst')]:+.1f} K against 40 mm, standing, worst end: the case runs cooler but K's rear wall is "
         f"{f(d['inputs']['enclosure_120_rear_clearance_from_K_B_face_mm'], 1)} mm away in place of {f(40 + d['inputs']['stack']['K_rear_z_mm'], 1)} mm",
         'The depth target of about 40 mm (DS-13, DS-33); the inlet reservation (#57)', 'None beyond item 2'),
        ('Less load', 'not followed (DS-96: a circuit change outside this campaign)',
         f"{f(per_w, 2)} K per watt removed at K's mean (40 mm standing, low coefficients); the low-heat load is "
         f"{f(red, 2)} W below the planning load",
         'Circuit changes are out of scope; the ST-11 ledger refresh may lower the planning load', 'A measured supply current per rail (#64)'),
    ]
    listed = sum(1 for x in rows if x[1].startswith('listed'))
    vmax = max(vents.values())
    vmin = min(vents.values())
    lines = [f"## 6. {len(rows)} options are listed and none is selected; {listed} go to the owner as enclosure items: on paper vents bound K's mean "
             f"down by {rng(vmin, vmax)} K and feet lower it by {rng(feet['best'], feet['worst'])} K lying", '',
             f"Reference: 40 mm, closed, K's mean at {rng(base[('V', 'best')], base[('V', 'worst')])} K above ambient standing and "
             f"{rng(base[('H', 'best')], base[('H', 'worst')])} K lying, best to worst end. The campaign follows no thermal option on a "
             'board (DS-96).', '',
             '| Option | State | What it changes in the screen | What it conflicts with | Evidence it needs |',
             '| --- | --- | --- | --- | --- |']
    lines += [f"| {a} | {b} | {c} | {e} | {g} |" for a, b, c, e, g in rows]
    return lines + [''] + option_board_lines(r)


OPTION_BOARDS = ('P', 'JR', 'K')


def option_rows(d):
    v_lo, v_hi = T.lo_hi(d, 'vent_area_cm2')
    rows = [('Case on feet', 'H', lambda w: {'h_resting': feet_h(d, w)})]
    for v in (v_lo, v_hi):
        for o in T.ORIENTS:
            rows.append((f"Vents {v:g} cm2", o, lambda w, v=v: {'vent_cm2': v}))
    for v in (v_lo, v_hi):
        rows.append((f"Feet and vents {v:g} cm2", 'H', lambda w, v=v: {'vent_cm2': v, 'h_resting': feet_h(d, w)}))
    return rows


def option_falls(d, depth, o, kw_of):
    out = {}
    for w, (case, level) in T.ENDS.items():
        base = T.network(d, depth, o, level, case)['rise']
        opt = T.network(d, depth, o, level, case, **kw_of(w))['rise']
        out[w] = {b: base[b] - opt[b] for b in OPTION_BOARDS if b in base}
    return out


def option_board_lines(r):
    d = r['d']
    lines = ['Fall of the board mean of P, JR and K under each option row, 40 mm, against the closed case in the same orientation; '
             f"best end / worst end, K. The feet carry {feet_h(d, 'worst'):g} W/m2K at the worst end and {feet_h(d, 'best'):g} W/m2K at the "
             'best end (ASSUMED); vents are the upper bound of item 6.', '',
             f"| Option | Orientation | {' | '.join(OPTION_BOARDS)} |", '| --- | --- |' + ' --- |' * len(OPTION_BOARDS)]
    for name, o, kw_of in option_rows(d):
        falls = option_falls(d, 40, o, kw_of)
        cells = [f"{falls['best'][b]:.1f} / {falls['worst'][b]:.1f}" if b in falls['best'] else 'no plane' for b in OPTION_BOARDS]
        lines.append(f"| {name} | {ORIENT_NAME[o]} | {' | '.join(cells)} |")
    return lines + ['']


def item7(r):
    d = r['d']
    amb = r['amb']
    lim = r['limit_classes']
    within = T.term(d, 'sensor_within_mm')
    cmp_ = r['cmp']
    places = ', '.join(f"{s} at {cmp_[(s, 40)]['orients'][cmp_[(s, 40)]['worse']]['worst']['ref']}" for s in lim)
    lines = [f"## 7. Proposal for #64: soak at {amb:g} °C in both orientations at the planning state, with a sensor on the body of each part "
             f"of a retained limit or on the board within {within:g} mm of it; #64 stays NOT RUN", '',
             'PROPOSAL only; nothing here is a test result. Limits marked "evidence first" cannot be set until the bundle holds the figure.', '',
             '| Element | Proposal |', '| --- | --- |',
             f"| Ambient | Chamber or still room at {amb:g} °C +/-1 K, measured at two points 100 mm from the case at mid-height, shielded; a 25 °C run as the reference |",
             f"| Soak | {T.term(d, 'soak_proposal')} |",
             f"| Operating state | Rails at nominal and at the upper tolerance; every LED lit; every output into 10 kOhm at 5 V; the measured rail currents recorded and compared with the planning load ({f(r['normal']['input_W'], 2)} W input) and the low-heat load ({f(r['low']['input_W'], 2)} W) |",
             '| Orientations | Standing with the base resting, and lying panel-up with the rear wall resting on a wooden board |',
             '| Case sensors | Panel centre, rear wall centre, each side wall centre, top face |',
             f"| Part sensors | On the body of the part, or on the board within {within:g} mm of it (DS-95): the hottest place of each class of item 4 ({places}); the bleeder bodies at the inlet; the five AS3340D cores, U1601 (octave reference) and the two S&H |",
             f"| Panel part sensors | {panel_sensor_text(r)} |",
             f"| Reading: parts with a retained limit | The board at the part against the limit of the exact part ({', '.join(lim)}: {'/'.join(f'{x:.0f}' for x in headline(r)[3])} °C) |",
             f"| Reading: 0603 resistors | Dissipation under the series power curve at the measured board temperature; bleeder body against {T.term(d, 'solder_joint_limit_C'):g} °C at its joint |",
             '| Reading: ICs | NO LIMIT RETAINED: evidence first (operating range, then thermal resistance and junction maximum) for every IC class of item 4 |',
             f"| Reading: screen consistency | Case rise inside {rng(end(r, 40, 'V', 'best')['rise']['shell'], end(r, 40, 'H', 'worst')['rise']['shell'])} K at 40 mm; a reading outside invalidates the screen, not the design |",
             '| Reading: temperature-sensitive functions | Each core\'s frequency, each reference and each S&H droop at 25 °C and at the soak ambient; no limit is proposed (calibration scope stays 25 °C) |', '']
    return lines


def nearest(places, xy):
    return min(places, key=lambda p: ((p['xy'][0] - xy[0]) ** 2 + (p['xy'][1] - xy[1]) ** 2, p['ref']))


def panel_sensors(d):
    cells, _ = T.k_cells_cached(d, 'normal', 40, 'V', 'low')
    region = T.warm_region(d, cells)
    size = T.term(d, 'cell_mm')
    centre = ((region['hottest'][0] + 0.5) * size, (region['hottest'][1] + 0.5) * size)
    pots = [p for s in pot_symbols(d) for p in T.class_places(d, s) if p['board'] == 'P']
    over = [p for p in pots if T.in_box(region['box_mm'], p['xy'])]
    out = {'region': region, 'centre': centre, 'over': len(over)}
    out['pot'] = nearest(over or pots, centre) if pots else None
    switches = [p for s in T.panel_parts(d) if s.startswith('B3F') for p in T.class_places(d, s)]
    out['switch'] = nearest(switches, centre) if switches else None
    leds = [p for row in (x for x in T.panel_parts(d) if x.startswith('APHHS')) for p in T.class_places(d, row) if p['board'] == 'JR']
    out['led'] = nearest(leds, centre) if leds else None
    return out


def panel_sensor_text(r):
    x = panel_sensors(r['d'])
    box = x['region']['box_mm']
    pick = lambda p, what: f"{what} {p['ref']} ({p['symbol']}, {p['board']}, x {p['xy'][0]:g}, y {p['xy'][1]:g} mm)" if p else f"no {what} placed"
    return (f"Three more bodies, each the one nearest the centre of K's hottest cell (x {x['centre'][0]:g}, y {x['centre'][1]:g} mm, "
            f"40 mm standing, planning state), with the x, y of `floorplan-placements` read as one frame for every board: "
            f"{pick(x['pot'], 'the pot')}, one of the {x['over']} pots on P inside K's warm region (x {box[0]:g} to {box[2]:g}, "
            f"y {box[1]:g} to {box[3]:g} mm); {pick(x['switch'], 'the tact switch')}; {pick(x['led'], 'the LED')}. Each is read against "
            'the row of item 9, and the pot also against the curve of its second row')


BOARD_ORDER = ('K', 'P', 'JL', 'JR', 'EL', 'O1', 'O2', 'O3', 'O4', 'O5', 'shell')


def board_label(b):
    return 'case (panel and walls)' if b == 'shell' else b


def front_boards(d):
    return sorted(b for b in d['inputs']['planes_40'] if b != 'K')


def lying_front_shift(r):
    xs = [T.board_shift(r['boards'], b, 'H', e) for b in front_boards(r['d']) for e in T.ENDS]
    return [x for x in xs if x is not None]


def item_boards(r):
    d = r['d']
    bt = r['boards']
    limit = T.term(d, 'stack_share_K')
    lying = lying_front_shift(r)
    standing = [x for x in (T.board_shift(bt, b, 'V', e) for b in front_boards(d) for e in T.ENDS) if x is not None]
    lines = [f"## 8. Lying flat, the 40 mm stack reads the front boards {srng(*lying)} K above the 120 mm case; standing "
             f"{srng(*standing)} K", '',
             f"Mean of every board and of the case (the shell node: panel and walls) at {r['amb']:g} °C ambient, closed, supply "
             'outside; each cell is best end to worst end. The shift is the 40 mm stack less the 120 mm case on the same board, '
             f"orientation and end; above {limit:g} K it is marked "
             '"share of the 40 mm stack" (DS-94, DS-102). O2 and O4 are no planes of the 40 mm stack.', '',
             '| Board | 40 mm standing, °C | 40 mm lying, °C | 120 mm standing, °C | 120 mm lying, °C | Shift standing, best / worst, K | Shift lying, best / worst, K |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for b in [x for x in BOARD_ORDER if x in bt] + sorted(set(bt) - set(BOARD_ORDER)):
        row = bt[b]
        cells = []
        for depth in T.DEPTHS:
            for o in T.ORIENTS:
                cells.append(rng(row[(depth, o, 'best')], row[(depth, o, 'worst')]) if (depth, o, 'best') in row else 'no plane')
        shifts = []
        for o in T.ORIENTS:
            x = [T.board_shift(bt, b, o, e) for e in T.ENDS]
            if None in x:
                shifts.append('-')
                continue
            mark = ', share of the 40 mm stack' if any(v > limit for v in x) else ''
            shifts.append(f"{x[0]:+.1f} / {x[1]:+.1f}{mark}")
        lines.append(f"| {board_label(b)} | {' | '.join(cells)} | {' | '.join(shifts)} |")
    f_lo, f_hi = T.lo_hi(d, 'h_conv_feet')
    lines += ['', f"Case on feet (option row of item 6; the resting rear wall carries {f_lo:g} W/m2K at the worst end and {f_hi:g} W/m2K "
              'at the best end, ASSUMED), lying, the same shift of the 40 mm stack against the 120 mm case:', '',
              '| Board | Shift lying closed, best / worst, K | Shift lying on feet, best / worst, K |', '| --- | --- | --- |']
    for b in [x for x in BOARD_ORDER if x in bt and (40, 'H', 'best') in bt[x]]:
        closed = [T.board_shift(bt, b, 'H', e) for e in T.ENDS]
        feet = [feet_board(d, 40, b, e) - feet_board(d, 120, b, e) for e in T.ENDS]
        mark = lambda x: ', share of the 40 mm stack' if any(v > limit for v in x) else ''
        lines.append(f"| {board_label(b)} | {closed[0]:+.1f} / {closed[1]:+.1f}{mark(closed)} | {feet[0]:+.1f} / {feet[1]:+.1f}{mark(feet)} |")
    return lines + ['']


def feet_h(d, which):
    f_lo, f_hi = T.lo_hi(d, 'h_conv_feet')
    return f_lo if which == 'worst' else f_hi


def feet_board(d, depth, board, which, **kw):
    case, level = T.ENDS[which]
    net = T.network(d, depth, 'H', level, case, h_resting=feet_h(d, which), **kw)
    return T.term(d, 'ambient_C') + net['rise'][board]


def limit_text(d, symbol):
    lim = T.retained_limit(d, symbol)
    info = T.information_ranges(d, symbol)
    parts = []
    if lim is None:
        parts.append('NO LIMIT RETAINED')
    else:
        kind = limit_kind(lim['class'])
        cond = next((x['printed_condition'] for x in d['inputs']['operating_ranges'][symbol] if x['fact_id'] == lim['fact_id']), None)
        parts.append(f"{lim['limit_C']:+.0f} °C, {kind} (`{lim['fact_id']}`{', ' + cond if cond else ''})")
    for x in info:
        src = 'third-party copy' if x['third_party_copy'] else 'source not confirmed'
        parts.append(f"for information {x['minimum']} to {x['maximum']} °C (`{x['fact_id']}`, {x['verdict']}, {src})")
    for fid, v in d['inputs']['panel_facts'].items():
        if v['symbol'] == symbol and 'junction' in fid:
            parts.append(f"junction maximum {v['value']} °C listed, not compared (`{fid}`)")
    return '; '.join(parts)


def info_word(d, symbol, c):
    info = T.information_ranges(d, symbol)
    if not info:
        return None
    limit = min(x['maximum'] for x in info)
    words = [T.word(limit, c['orients'][o]['worst']['T_C'], c['orients'][o]['best']['T_C']) for o in T.ORIENTS if c['orients'][o]]
    return T.worst_word(words) if words else None


def item_panel(r):
    d = r['d']
    rows = r['panel']
    limit = T.term(d, 'stack_share_K')
    syms = T.panel_parts(d)
    words = {(s, depth): T.panel_class_word(d, s, depth) for s in syms for depth in T.DEPTHS}
    exceeded = [s for s in syms if all(words[(s, dep)] == 'EXCEEDED ON PAPER' for dep in T.DEPTHS)]
    changed = [s for s in syms if any(row['symbol'] == s and row['depths'][40]['orients']['V'] and row['depths'][40]['orients']['H']
                                      and row['depths'][40]['orients']['V']['word'] == 'MET ON PAPER'
                                      and row['depths'][40]['orients']['H']['word'] != 'MET ON PAPER' for row in rows)]
    lines = [f"## 9. Panel classes and trimmers: {join_names(exceeded) if exceeded else 'no class'} read EXCEEDED ON PAPER in both case depths; "
             f"at 40 mm {join_names(changed) if changed else 'no class'} change from MET ON PAPER standing to another word lying", '',
             'One row per class of an exact part and board, from the retained facts (DS-104, DS-111). Only a fact whose verdict '
             'confirms its primary source makes a limit of record; an UNSOURCED range is printed for information, and its class reads NO LIMIT RETAINED and '
             'NOT SHOWN. The temperature is the board at the part: on a front board its mean (lateral rise NOT COMPUTED: the screen '
             'has no cell model of a front board); on K the mean plus the lateral rise of the hottest cell that holds a part of the '
             'class. The panel beside it is the case node, printed without a word. Best end to worst end; the row word is the worst '
             'word of the two orientations; the class word is the worst word of its rows. Counts and boards: '
             '`io-partition-exact-refs` and the partition assignment.', '',
             '| Exact part | Board | Count | Limit | Case | Standing, °C | Standing | Lying, °C | Lying | Panel beside it, °C | Lateral rise | Row word | Shift 40 against 120 mm, best / worst end, K |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in rows:
        s, b = row['symbol'], row['board']
        shifts = class_shifts(row['depths'][40], row['depths'][120])
        for depth in T.DEPTHS:
            c = row['depths'][depth]
            if c['word'] is None:
                lines.append(f"| {s} | {b} | {row['count']} | {limit_text(d, s)} | {depth} mm | no plane of the {depth} mm stack | - | - | - | - | - | - | - |")
                continue
            o = c['orients']
            shell = [T.term(d, 'ambient_C') + r['nets'][(depth, x, T.ENDS[e][1], T.ENDS[e][0])]['rise']['shell'] for x in T.ORIENTS for e in T.ENDS]
            lat = 'NOT COMPUTED' if b != 'K' else f"{o[c['worse']]['worst']['lateral_K']:+.1f} K, {o[c['worse']]['worst']['ref']}"
            note = info_word(d, s, c)
            wtxt = f"**{c['word']}**" + (f" (for information against the UNSOURCED range: {note})" if note else '')
            share = share_text(shifts, limit) if depth == 40 else '-'
            lines.append(f"| {s} | {b} | {row['count']} | {limit_text(d, s)} | {depth} mm | "
                         f"{f(o['V']['best']['T_C'])} to {f(o['V']['worst']['T_C'])} | {o['V']['word']} | "
                         f"{f(o['H']['best']['T_C'])} to {f(o['H']['worst']['T_C'])} | {o['H']['word']} | {rng(*shell)} | {lat} | {wtxt} | {share} |")
    lines += ['', '| Exact part | Class word, 40 mm | Class word, 120 mm |', '| --- | --- | --- |']
    lines += [f"| {s} | {words[(s, 40)] or '-'} | {words[(s, 120)] or '-'} |" for s in syms]
    return lines + [''] + pot_curve_lines(r)


def pot_symbols(d):
    return [s for s in T.panel_parts(d) if any(v['symbol'] == s and 'derating' in fid for fid, v in d['inputs']['panel_facts'].items())]


def curve_reading(worst, best, end_C, power_holds):
    if best > end_C:
        return 'beyond the curve'
    if worst <= end_C and power_holds:
        return 'inside the curve'
    return 'not shown'


def pot_curve_lines(r):
    d = r['d']
    syms = pot_symbols(d)
    powers = T.pot_powers(d)
    computed = [x for x in powers if x['W'] is not None]
    missing = len(powers) - len(computed)
    top = max(computed, key=lambda x: x['W']) if computed else None
    fid = next(fid for fid, v in d['inputs']['panel_facts'].items() if v['symbol'] == syms[0] and 'derating' in fid)
    rating_id = next(fid for fid, v in d['inputs']['panel_facts'].items() if v['symbol'] == syms[0] and 'power-rating' in fid)
    rating = d['inputs']['panel_facts'][rating_id]['value']
    end_C = d['inputs']['panel_facts'][fid]['value']['curve_end_ambient_C']
    rows = [x for x in r['panel'] if x['symbol'] in syms]
    lines = [f"### Second row of the pots: derating curve, outside the printed operating range; the power condition reads not shown, "
             f"because {missing} of {len(powers)} pots are NOT COMPUTED", '',
             f"No word of record (DS-103). The board at the part against {end_C:g} °C, the end of the curve (`{fid}`), with the power "
             f"condition: the largest dissipation of a pot against {rating:g} W (`{rating_id}`) times the ratio of the curve at that "
             'temperature (1.0 up to its full-power ambient, a straight line to its end, no figure beyond). The power of a pot is '
             'taken from the control netlist (`control-netlist-pot-ends`): the voltage between the two end pins where both nets '
             'carry a retained voltage (a rail of `ledger-case-envelope` or ground), squared, over the resistance less '
             f"{100 * T.term(d, 'pot_resistance_tolerance'):.0f} %. A pot with a signal net at an end is NOT COMPUTED. "
             + (f"Largest computed: {top['ref']} ({top['value']}), {1000 * top['W']:.2f} mW. " if top else 'Largest computed: none. ')
             + f"{missing} NOT COMPUTED: {sum(1 for e in d['inputs']['pot_ends'] if e['pin1'] in T.term(d, 'ground_nets') or e['pin3'] in T.term(d, 'ground_nets'))} "
             'have ground at one end and a signal net at the other, the rest a signal net at both ends; no end pin of a pot is on a rail.', '',
             '| Pots | Case | Orientation | Board at the part, best to worst, °C | Curve ratio at the worst end | Allowed per pot at the worst end, mW | Reading |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    holds = missing == 0 and top is not None
    for depth in T.DEPTHS:
        for o in T.ORIENTS:
            temps = [(row['depths'][depth]['orients'][o]['best']['T_C'], row['depths'][depth]['orients'][o]['worst']['T_C']) for row in rows]
            best, worst = max(t[0] for t in temps), max(t[1] for t in temps)
            ratio = T.derating_ratio(d, fid, worst)
            ok = holds and ratio is not None and top['W'] <= rating * ratio
            lines.append(f"| {join_names(syms)} on P | {depth} mm | {ORIENT_NAME[o]} | {rng(best, worst)} | "
                         f"{'no figure beyond the curve' if ratio is None else f'{ratio:.2f}'} | "
                         f"{'-' if ratio is None else f'{1000 * rating * ratio:.1f}'} | {curve_reading(worst, best, end_C, ok)} |")
    return lines + ['']


def item_ambient(r):
    d = r['d']
    lo, hi = T.term(d, 'ambient_search_C')
    targets = [(s, None) for s in r['limit_classes']] + [(row['symbol'], row['board']) for row in r['panel']
                                                          if T.retained_limit(d, row['symbol']) is not None]
    memo = {}
    rows = []
    for s, b in targets:
        limit = T.retained_limit(d, s)['limit_C']
        key_place = b if b not in (None, 'K') else s
        cells = []
        for depth in T.DEPTHS:
            for o in T.ORIENTS:
                pair = []
                for e in ('best', 'worst'):
                    k = (key_place, depth, o, e, limit)
                    if k not in memo:
                        memo[k] = T.ambient_at(d, s, depth, o, e, limit, board=b, lo=lo, hi=hi)
                    pair.append(memo[k])
                cells.append(' / '.join('outside the search' if x is None else f'{x:.1f}' for x in pair))
        rows.append((s, b or 'K', limit, cells))
    pots = [x for x in rows if x[0] in pot_symbols(d)]
    pot_worst = min(float(c.split(' / ')[1]) for x in pots for c in x[3] if 'outside' not in c) if pots else None
    lines = [f"## 10. Ambient at the limit: the pots read their {pots[0][2]:+.0f} °C at an ambient down to {pot_worst:.1f} °C at the worst end"
             if pots else '## 10. Ambient at the limit per class with a limit of record', '',
             'Per class with a limit of record, the ambient at which the best end and the worst end read the limit, found by '
             f"running the network at each trial ambient (search {lo:g} to {hi:g} °C; DS-106 point 7), not by a linear shift. Each "
             'cell: best end / worst end, °C.', '',
             '| Exact part | Board | Limit, °C | 40 mm standing | 40 mm lying | 120 mm standing | 120 mm lying |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    lines += [f"| {s} | {b} | {limit:g} | {' | '.join(cells)} |" for s, b, limit, cells in rows]
    return lines + ['']


def evidence_needs(r):
    d = r['d']
    ranges = d['inputs']['operating_ranges']
    syms = list(LIMIT_FACTS)
    missing = sum(1 for s in syms if not ranges.get(s))
    lines = [f"## Evidence is needed for {len(syms)} exact parts before any junction temperature can be stated; {missing} of them have no retained operating range", '',
             'The thermal evidence of the exact parts is a task of the component evidence workflow outside this campaign (DS-98): '
             'the operating temperature range first, then thermal resistance and junction maximum.', '',
             '| Exact part | Operating temperature range | Other retained thermal facts of the bundle | Missing thermal evidence |', '| --- | --- | --- | --- |']
    for sym in syms:
        rr = ranges.get(sym, [])
        rtxt = '; '.join(f"{x['minimum']} to {x['maximum']} °C (`{x['fact_id']}`)" for x in rr) or 'not retained'
        figs = ', '.join(f'`{x}`' for x in T.thermal_figures(d, sym)) if sym in d['inputs']['class_bundles'] else '-'
        lines.append(f"| {sym} | {rtxt} | {figs or 'none'} | {LIMIT_FACTS[sym].split(': ', 1)[1]} |")
    lines += ['| The 5600 Ohm magnitude sense, 1200 Ohm stage and 22.1 kOhm clip resistors | exact identity UNSELECTED | - | Power curve and size |', '']
    return lines


def terms_table(r):
    d = r['d']
    body = []
    for name, t in d['terms'].items():
        if t['status'] in ('ASSUMED', 'UNSOURCED'):
            v = t['value']
            text = v if isinstance(v, str) else ('see JSON' if isinstance(v, list) and v and isinstance(v[0], (list, dict)) else v)
            body.append(f"| {name} | {text} | {t['unit']} | {t['status']} | {t['source']} |")
    return [f"## {len(body)} terms are ASSUMED or UNSOURCED; every other term is SOURCED with its pin or DERIVED", '',
            '| Term | Value | Unit | Status | Reason or source |', '| --- | --- | --- | --- | --- |'] + body + ['']


def checks_section():
    return ['## Checks run and NOT RUN', '',
            '| Check | State |', '| --- | --- |',
            '| Unit tests: `python3 scripts/checks/frozen_studies.py discover scripts/stack/thermal` | run by the executor; see the brief\'s result section |',
            '| `pnpm circuit:check` before and after | run by the executor; see the brief\'s result section |',
            '| CFD, airflow, vent or enclosure design | NOT RUN: out of scope (screen only) |',
            '| Physical thermal test #64 | NOT RUN: no assembled stack exists |',
            '| `regen-all.sh`, `pnpm check`, full Python suite | NOT RUN: excluded by the brief for time (CI near its limit) |', '']


def render(d=None):
    r = facts(d)
    lines = header(r) + plan_check(r) + item1(r) + item2(r) + item3(r) + item4(r) + item5(r) + item6(r) + item7(r) + \
        item_boards(r) + item_panel(r) + item_ambient(r) + evidence_needs(r) + terms_table(r) + checks_section()
    return '\n'.join(lines).rstrip() + '\n'


def main(argv):
    if argv not in ([], ['--check']):
        print('usage: thermal_readme.py [--check]', file=sys.stderr)
        return 2
    text = render()
    if argv == ['--check']:
        ok = README.exists() and README.read_text() == text
        print('README matches the rendering' if ok else 'README differs from the rendering')
        return 0 if ok else 1
    README.write_text(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
