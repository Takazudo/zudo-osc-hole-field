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
    'AS3340D': ('none', 'AS3340D (ALFA RPAR): theta-JA, Tj max and operating range; the bundle keeps only the advice to supply VEE at -5 V against self-heating'),
    'OPA4197IPWR': ('none', 'OPA4197IPWR (TI): theta-JA (PW) and Tj max'),
    'OPA4197IDR': ('none', 'OPA4197IDR (TI): theta-JA (D) and Tj max'),
    'LF398M_NOPB': ('none', 'LF398M/NOPB (TI): theta-JA (D) and Tj max'),
    'LM13700M_NOPB': ('none', 'LM13700M/NOPB (TI): theta-JA (D) and Tj max'),
    'NOISE2': ('none', 'NOISE2 (Electric Druid, PDIP-8): theta-JA, Tj max and operating range'),
    'REF5050AIDR': ('none', 'REF5050AIDR (TI): theta-JA (D), Tj max and the drift curve over 25 to 85 degC'),
    'OPA4196IDR': ('none', 'OPA4196IDR (TI): theta-JA (D) and Tj max'),
    'TMUX7412FRRPR': ('none', 'TMUX7412FRRPR (TI): theta-JA (RRP) and Tj max; the thermal pad is tied to AGND'),
    'LM393BIDR': ('none', 'LM393BIDR (TI): theta-JA (D) and Tj max'),
}


def f(x, n=1):
    return '-' if x is None else f'{x:.{n}f}'


def rng(a, b, n=1):
    lo, hi = min(a, b), max(a, b)
    return f'{lo:.{n}f} to {hi:.{n}f}'


def facts():
    d = T.load()
    r = {'d': d}
    r['normal'] = T.power_map(d, 'normal')
    r['contract'] = T.power_map(d, 'contract')
    r['cases_W'] = T.ledger_case_W(d)
    r['outputs'] = T.output_count(d)
    r['areas'] = {k: T.outer_area_m2(d, k) for k in (40, 34, 120)}
    r['plan_h'] = T.plan_h_range(d)
    nets = {}
    for depth in (40, 120):
        for o in ('V', 'H'):
            for lv in ('high', 'low'):
                for case in ('normal', 'contract'):
                    nets[(depth, o, lv, case)] = T.network(d, depth, o, lv, case)
    r['nets'] = nets
    surf = {}
    for depth in (40, 34, 120):
        for o in ('V', 'H'):
            for lv in ('high', 'low'):
                for case in ('normal', 'contract'):
                    surf[(depth, o, lv, case)] = T.surface_rise(d, depth, o, lv, r[case]['internal_W'])
    r['surf'] = surf
    return r


def air_rise(net):
    gaps = net['gaps']
    area = sum(g['area_cm2'] for g in gaps)
    return sum(g['air_rise'] * g['area_cm2'] for g in gaps) / area - net['rise']['shell']


def item1(r):
    d = r['d']
    n, c = r['normal'], r['contract']
    planes = d['inputs']['planes_40']
    areas = T.board_areas_cm2(planes)
    k_share = n['boards']['K'] / n['internal_W']
    lines = [f"## 1. The ledger puts {f(n['internal_W'], 2)} W inside the instrument at the normal planning load "
             f"and {f(c['internal_W'], 2)} W at the continuous contract; K carries {f(100 * k_share, 0)} %; the residual is "
             f"{f(abs(n['residual_W']), 6)} W", '',
             f"Every ledger row and every one of the {len(d['inputs']['ic_packages'])} IC packages is assigned to the board "
             f"that carries it in the partition (rules in `row_rules`; only the IC, NOISE2, REF and LOGIC rules are bound to "
             f"packages, the rest are ASSUMED). {r['outputs']} outputs at 5 V into 10 kohm dissipate "
             f"{f(1000 * n['external_W'], 0)} mW outside. The bleeder residual of the ledger total, "
             f"{f(T.row_power_W(d, T.all_rows(d)[-1]['mA']), 3)} W, is the two inlet bleeders and sits on the ASSUMED inlet board. "
             f"The supply is outside (Q6) and not in the map. All LEDs are on. The contract case spreads the excess over the "
             f"planning map rail by rail (ASSUMED).", '',
             '| Board | Normal planning, W | Contract, W | Board area, cm2 | Normal density, mW/cm2 | Contract density, mW/cm2 |',
             '| --- | --- | --- | --- | --- | --- |']
    for b in ('K', 'JL', 'JR', 'P', 'EL', 'O1', 'O3', 'O5'):
        wn, wc = n['boards'].get(b, 0.0), c['boards'].get(b, 0.0)
        lines.append(f"| {b} | {f(wn, 3)} | {f(wc, 3)} | {f(areas[b], 1)} | {f(1000 * wn / areas[b], 2)} | {f(1000 * wc / areas[b], 2)} |")
    lines += [f"| Outside: output loads | {f(n['external_W'], 3)} | {f(c['external_W'], 3)} | - | - | - |",
              f"| Sum of the map | {f(n['internal_W'] + n['external_W'], 3)} | {f(c['internal_W'] + c['external_W'], 3)} | - | - | - |",
              f"| Ledger input power (12/12/5 V) | {f(n['input_W'], 3)} | {f(c['input_W'], 3)} | - | - | - |",
              f"| Residual | {f(n['residual_W'], 6)} | {f(c['residual_W'], 6)} | - | - | - |", '']
    by_rule = ', '.join(f"{k} {f(v, 2)} W" for k, v in sorted(n['rules_W'].items(), key=lambda x: -x[1]))
    lines += [f"Input power by rule at the normal load: {by_rule}. The ASSUMED rules carry "
              f"{f(sum(v for k, v in n['rules_W'].items() if k not in ('IC', 'NOISE2', 'REF', 'LOGIC')), 2)} W; moving all of it "
              f"between K and the front boards is the widest error of the map.", '',
              'Not in the ledger and not added: the SUB divider and gating on +5 V (UNSOURCED until ST-11 refreshes the ledger), '
              'the lower count of octave receivers without the OSC2 and OSC4 selectors (not credited, so the map stays high), '
              f"the I2R of the 18 posts (at most {f(1000 * T.post_i2r_bound_W(d), 1)} mW with every contract rail current through "
              'one 0.5 mOhm joint), and the flat links (at most 0.049 A on a ground, DS-62; conductor resistance UNSOURCED). '
              'The ledger charges magnitude LEDs and outputs on both analogue rails at once, which is high by up to a factor of two '
              'for those rows. The ledger names OPA4197IDR where the netlist has OPA4197IPWR in '
              f"{len({k[0][0] for k in T.symbol_mismatches(d)})} instances; same die and allowance, so the screen pools the two packages.", '']
    return lines


def plan_check(r):
    d = r['d']
    n = r['normal']
    cases = r['cases_W']
    a = r['areas']
    drop34 = 1 - a[34] / a[120]
    drop40 = 1 - a[40] / a[120]
    hlo, hhi = r['plan_h']
    lines = [f"## The plan page's 41.1 W is reproduced; its 35.4 W is corrected to {f(n['input_W'], 2)} W input "
             f"({f(n['internal_W'], 2)} W inside); its 31 % and its rise ranges are reproduced by its own method", '',
             f"35.4 W is not the normal planning load of the ledger: {f(cases['two_feed_total_mA'], 2)} W. It equals, to "
             f"{f(abs(cases['conditional_SH_short_resistor_case_mA'] - 35.4), 2)} W, the conditional S&H short-resistor case "
             f"({f(cases['conditional_SH_short_resistor_case_mA'], 2)} W), a fault case. 41.1 W is the contract at 12/12/5 V. "
             f"Both are input power: {f(1000 * n['external_W'], 0)} mW leaves through the outputs. The plan's rise ranges follow "
             f"from one uniform coefficient of {f(hlo, 2)} to {f(hhi, 2)} W/m2K over the whole outer surface (back-solved; the "
             'plan names none). That method has no orientation, no resting face and no inside; item 2 replaces it.', '',
             '| Figure | Plan page | This screen | Verdict |', '| --- | --- | --- | --- |',
             f"| Normal planning load | 35.4 W | {f(n['input_W'], 2)} W input, {f(n['internal_W'], 2)} W inside | corrected: 35.4 W is the S&H short case |",
             f"| Continuous contract | 41.1 W | {f(r['contract']['input_W'], 2)} W input, {f(r['contract']['internal_W'], 2)} W inside | reproduced |",
             f"| Outer surface, 34 mm against 120 mm | -31 % | {f(-100 * drop34, 1)} % (40 mm: {f(-100 * drop40, 1)} %) | reproduced at a 2 mm wall |",
             f"| Rise, 34 mm | 17 to 22 K | {rng(T.plan_method(d, 34, 35.4)[0], T.plan_method(d, 34, 41.1)[1])} K by the plan's method at 35.4 to 41.1 W | reproduced |",
             f"| Rise, 120 mm | 12 to 15 K | {rng(T.plan_method(d, 120, 35.4)[0], T.plan_method(d, 120, 41.1)[1])} K by the plan's method at 35.4 to 41.1 W | reproduced |",
             f"| Rise, 34 mm, this screen's surface model | - | {rng(r['surf'][(34, 'V', 'high', 'normal')], r['surf'][(34, 'H', 'low', 'contract')])} K | corrected: orientation and the resting face widen the range |",
             f"| Rise, 120 mm, this screen's surface model | - | {rng(r['surf'][(120, 'V', 'high', 'normal')], r['surf'][(120, 'H', 'low', 'contract')])} K | corrected, as above |", '']
    return lines


def item2(r):
    d = r['d']
    s, nets = r['surf'], r['nets']
    a = r['areas']
    k40 = (nets[(40, 'H', 'low', 'contract')]['rise']['K'], nets[(40, 'V', 'high', 'normal')]['rise']['K'])
    lines = [f"## 2. At 40 degC ambient the 40 mm case's surface rises {rng(s[(40, 'V', 'high', 'normal')], s[(40, 'H', 'low', 'contract')])} K "
             f"against {rng(s[(120, 'V', 'high', 'normal')], s[(120, 'H', 'low', 'contract')])} K for 120 mm; lying panel-up is the worst "
             f"orientation; K's mean reaches {f(40 + min(k40), 0)} to {f(40 + max(k40), 0)} degC closed", '',
             f"Outer box: the internal {d['inputs']['enclosure_internal_xy_mm']} mm plus a {T.term(d, 'wall_mm')} mm wall (ASSUMED, 1 to 3 mm) "
             f"at the sides and rear; the depth includes the {T.term(d, 'panel_thickness_mm')} mm panel. Coefficients (all ASSUMED): "
             f"vertical faces {T.term(d, 'h_conv_vertical')} W/m2K, upward faces {T.term(d, 'h_conv_up')} W/m2K, the face resting "
             f"on a table 0, finish emissivity {T.term(d, 'eps_case')}, radiation to surroundings at ambient. Each range pairs the "
             'high coefficients with the normal load and the low ones with the contract. Standing (V): panel vertical, base face '
             'resting. Lying (H): panel horizontal facing up, rear wall resting. Inside: the network of item 3. The 34 mm row is '
             f"surface only: the stack does not fit it ({f(d['inputs']['stack']['enclosure_depth_cases'][1]['rear_part_clearance_mm'], 1)} mm rear clearance).", '',
             '| Case | Outer area, m2 | Surface rise, normal, K | Surface rise, contract, K | Internal air above surface, K | K mean rise above ambient, K | Front board hottest (JR) above ambient, K |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for depth in (40, 34, 120):
        for o in ('V', 'H'):
            name = f"{depth} mm, {'standing' if o == 'V' else 'lying panel-up'}, closed, supply outside"
            sn = rng(s[(depth, o, 'high', 'normal')], s[(depth, o, 'low', 'normal')])
            sc = rng(s[(depth, o, 'high', 'contract')], s[(depth, o, 'low', 'contract')])
            if depth == 34:
                lines.append(f"| {name} | {f(a[depth], 4)} | {sn} | {sc} | not applicable: the stack does not fit | - | - |")
                continue
            hi, lo = nets[(depth, o, 'high', 'normal')], nets[(depth, o, 'low', 'contract')]
            lines.append(f"| {name} | {f(a[depth], 4)} | {sn} | {sc} | {rng(air_rise(hi), air_rise(lo))} | "
                         f"{rng(hi['rise']['K'], lo['rise']['K'])} | {rng(hi['rise']['JR'], lo['rise']['JR'])} |")
    for label, kw in sensitivity_rows(d):
        hi = T.network(d, 40, 'V', 'high', 'normal', **kw['hi'])
        lo = T.network(d, 40, 'V', 'low', 'contract', **kw['lo'])
        lines.append(f"| {label} | {f(a[40], 4)} | {f(hi['rise']['shell'])} (high coefficients) | "
                     f"{f(lo['rise']['shell'])} (low coefficients) | {rng(air_rise(hi), air_rise(lo))} | "
                     f"{rng(hi['rise']['K'], lo['rise']['K'])} | {rng(hi['rise']['JR'], lo['rise']['JR'])} |")
    w1, w3 = T.outer_area_m2(d, 40, 1.0), T.outer_area_m2(d, 40, 3.0)
    lines += ['', f"The wall allowance moves the 40 mm area from {f(w1, 4)} to {f(w3, 4)} m2 ({f(100 * (w3 / w1 - 1), 1)} %). "
              'A vented row is an upper bound of the benefit: the air is taken to leave at the area-mean board temperature. '
              'The supply-inside rows add the supply loss at the shell only; no pocket for a supply exists in the 40 mm stack '
              '(2.8 mm behind K), so a supply inside needs a deeper case or a side pocket (Q6, #57).', '']
    return lines


def sensitivity_rows(d):
    e_lo, e_hi = T.lo_hi(d, 'supply_efficiency')
    v_lo, v_hi = T.lo_hi(d, 'vent_area_cm2')
    bare = T.term(d, 'eps_bare_metal')
    return [
        (f"40 mm standing, supply inside, efficiency {e_hi} to {e_lo}",
         {'hi': {'supply': 'inside', 'eta': e_hi}, 'lo': {'supply': 'inside', 'eta': e_lo}}),
        (f"40 mm standing, vented, {v_hi} to {v_lo} cm2 per vent (upper bound of the benefit)",
         {'hi': {'vent_cm2': v_hi}, 'lo': {'vent_cm2': v_lo}}),
        (f"40 mm standing, bare metal inside and out (emissivity {bare})",
         {'hi': {'eps_override': bare}, 'lo': {'eps_override': bare}}),
    ]


def item3(r):
    d = r['d']
    pairs40 = T.facing_pairs(d, 40)
    n = r['normal']
    areas = T.board_areas_cm2(d['inputs']['planes_40'])
    hi = r['nets'][(40, 'V', 'high', 'contract')]
    hh = r['nets'][(40, 'H', 'high', 'contract')]
    lo = r['nets'][(40, 'V', 'low', 'contract')]
    rec = T.term(d, 'links_record')
    lines = []
    big = [p for p in pairs40 if p['area_mm2'] >= 1000]
    nu_max = max(g['Nu'] for g in hi['gaps'] + hh['gaps'])
    lines += [f"## 3. Every gap of the 40 mm stack is conduction-dominated (Nu 1.0 to {f(nu_max, 2)}); radiation carries most of the heat between facing boards, and the slots and loops change no bound", '',
              'Gaps from `candidate.planes` and `candidate.stack`: panel rear at -2.0 mm, EL -4.4/-4.8, JL and JR -10.0/-11.6, '
              'P -12.0/-13.6, adapters -16.0/-17.6, K -30.6/-32.2, rear wall -40. Densities are board totals at the normal load over '
              'the board area. Nu runs from 1 (conduction only, ASSUMED lower bound) to the ASSUMED enclosed-layer correlations at the '
              'contract temperatures; h adds the plate-to-plate radiation (emissivity 0.80 to 0.95).', '',
              '| Facing pair (front, rear) | Gap, mm | Facing area, cm2 | Density, front member, mW/cm2 | Density, rear member, mW/cm2 | Nu standing | Nu lying | h, W/m2K |',
              '| --- | --- | --- | --- | --- | --- | --- | --- |']

    def dens(b):
        return '0 (case)' if b == 'shell' else f(1000 * n['boards'].get(b, 0.0) / areas[b], 2)

    def find(net, p):
        return next(g for g in net['gaps'] if g['upper'] == p['upper'] and g['lower'] == p['lower'] and g['gap_mm'] == p['gap_mm'])
    for p in big:
        name = f"{'panel' if p['upper'] == 'shell' else p['upper']} / {'rear wall' if p['lower'] == 'shell' else p['lower']}"
        gv, gh, gl = find(hi, p), find(hh, p), find(lo, p)
        lines.append(f"| {name} | {f(p['gap_mm'], 1)} | {f(p['area_mm2'] / 100, 1)} | {dens(p['upper'])} | {dens(p['lower'])} | "
                     f"{f(gv['Nu'], 2)} | {f(gh['Nu'], 2)} | {rng(gl['h'], max(gv['h'], gh['h']))} |")
    small = sum(p['area_mm2'] for p in pairs40 if p['area_mm2'] < 1000) / 100
    k_fr = sum(p['area_mm2'] for p in pairs40 if p['lower'] == 'K' and p['upper'] != 'shell') / 100
    lines += ['', f"Pairs below 10 cm2 (adapters, P over the adapters, EL over K's edge) total {f(small, 1)} cm2 and are in the network. "
              f"As of the record of the room study the stack has {rec['placed']} of {rec['links']} links placed, {rec['slots']} slots "
              f"in K of {f(rec['slot_area_mm2'] / 100, 1)} cm2 in all, and cable loops of at most {f(rec['loop_plan_area_mm2'] / 100, 1)} cm2 "
              f"in plan. The slots are {f(100 * rec['slot_area_mm2'] / (100 * k_fr), 1)} % of the {f(k_fr, 0)} cm2 where front boards face K "
              'and are mostly filled by the cable; they add no credited air path. The loops are at most '
              f"{f(100 * rec['loop_plan_area_mm2'] / (100 * k_fr), 1)} % of that area: as a radiation shield they lower h by at most that "
              'fraction where they lie, and they cannot drive a gap below conduction except where cable replaces air. The screen '
              'carries them as this bound, not in the network. No airflow is claimed: the vented rows of item 2 are a bound.', '']
    return lines


def power_curve_W(curve, t):
    frac = (curve['T_zero_C'] - t) / (curve['T_zero_C'] - curve['T_full_C'])
    return curve['P70_W'] * min(1.0, max(0.0, frac))


def item4(r):
    d = r['d']
    top = T.top_ten(d, 'normal')
    lines = []
    rows = []
    worst_margin = None
    for i, c in enumerate(top, 1):
        sym = c['symbol']
        board = max(c['boards'], key=lambda b: (c['boards'][b], b))
        xy_list = [p['xy'] for p in d['inputs']['ic_packages'] if p['symbol'] == sym and p['board'] == 'K']
        if sym.startswith('RC0603FR-072K2L') or not xy_list:
            t_low, orient, lat = max(T.local_temperature(d, b, None, 'contract') for b in c['boards'])
            board = max(c['boards'], key=lambda b: T.local_temperature(d, b, None, 'contract')[0])
        else:
            best = max((T.local_temperature(d, 'K', xy, 'contract') for xy in xy_list), key=lambda x: x[0])
            t_low, orient, lat = best
        t_high = T.term(d, 'ambient_C') + T.network(d, 40, 'V', 'high', 'normal')['rise'].get(board, 0.0)
        p_mw = 1000 * c['max_W']
        if sym.startswith('RC0603FR-072K2L'):
            rth = T.term(d, 'bleeder_rth_K_per_W')
            tj = t_low + c['max_W'] * rth
            curve = T.term(d, 'resistor_power_curve')
            allowed = power_curve_W(curve, t_low)
            margin = T.term(d, 'solder_joint_limit_C') - tj
            worst_margin = margin if worst_margin is None else min(worst_margin, margin)
            evid = f"400 K/W generic mounting estimate (bundle), 110 degC solder joint, power curve 0.1 W at 70 degC to 0 at 155 degC"
            est = f"{f(tj, 0)} degC body ({f(t_high + c['max_W'] * rth, 0)} at the high coefficients)"
            marg = f"{f(margin, 0)} K to 110 degC; power curve allows {f(1000 * allowed, 0)} mW at {f(t_low, 0)} degC against {f(p_mw, 0)} mW"
            where = 'inlet, ASSUMED on K, position open (#57)'
        elif sym.startswith('magnitude sense'):
            curve = T.term(d, 'resistor_power_curve')
            allowed = power_curve_W(curve, t_low)
            evid = 'exact resistor UNSELECTED; series power curve only for the retained 0603 lines'
            est = f"{f(t_low, 0)} degC local; self-rise needs theta of the exact part"
            marg = f"power curve of the retained 0603 lines allows {f(1000 * allowed, 0)} mW against {f(p_mw, 1)} mW; exact part needed"
            where = 'JL and JR beside each magnitude LED'
        else:
            evid = 'none in the bundle'
            est = f"case >= {f(t_low, 0)} degC; Tj = case + {f(p_mw, 0)} mW x theta-JA (not retained)"
            marg = 'missing limit: Tj max not retained'
            where = ', '.join(f"{b} {n}" for b, n in sorted(c['boards'].items()))
        rows.append(f"| {i} | {sym} | {where} | {f(p_mw, 1)} | {f(c['density_mW_mm2'], 2)} | {evid} | {f(t_low, 0)} ({orient}, +{f(lat, 1)} K lateral) / {f(t_high, 0)} | {est} | {marg} |")
    k_lo = 40 + r['nets'][(40, 'H', 'low', 'contract')]['rise']['K']
    hc = T.term(d, 'hc_logic_ambient_max_C')
    cells, meta = T.k_cells(d, 'contract', 40, 'H', 'low')
    hottest = max(c['rise_smooth_K'] for c in cells.values())
    k_hot = k_lo + max(0.0, hottest)
    k_hi = 40 + r['nets'][(40, 'V', 'high', 'normal')]['rise']['K']
    bl_hi = T.term(d, 'solder_joint_limit_C') - (40 + r['nets'][(40, 'V', 'high', 'normal')]['rise']['K'] + T.term(d, 'bleeder_mW') / 1000 * T.term(d, 'bleeder_rth_K_per_W'))
    verdict = f"misses its 110 degC joint by {f(-worst_margin, 0)} K at the low corner and keeps {f(bl_hi, 0)} K at the high corner" if worst_margin < 0 else f"keeps {f(worst_margin, 0)} K to its 110 degC joint"
    lines += [f"## 4. No IC bundle holds a thermal resistance or a junction limit; the one part with a retained figure, the 2.2 kOhm bleeder, {verdict}, and K's mean at the low corner ({f(k_lo, 0)} degC) exceeds the 85 degC limit of the HC logic and X5R parts: NEEDS_DESIGN", '',
              'The ten classes are the union of the highest dissipation per package and the highest density (per courtyard area; '
              'body area for the 0603 parts). Dissipation is the ledger allowance per package at the normal load (full-temperature '
              'quiescent maxima). Local temperature: 40 degC plus the board mean rise at the contract load, low coefficients, worst '
              'orientation, plus the smoothed lateral rise of the package\'s 50 mm cell on K; the second figure is the standing '
              'case at the normal load with high coefficients. The AS3340D figure includes its VEE driver: '
              f"{f(1000 * T.as3340_split_W(d)['core_W'], 0)} mW in the core and {f(1000 * T.as3340_split_W(d)['vee_driver_W'], 0)} mW in the OPA4197 buffer.", '',
              '| Rank | Part class (exact) | Where | Dissipation, mW | Density, mW/mm2 | Retained thermal figure | Local, low corner / high corner, degC | Estimated case or junction | Margin or missing limit |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- |'] + rows
    lines += ['', f"Limits held by bundles for parts that dissipate little but sit on K: SN74HC14DR and SN74HC74DR recommended free-air "
              f"{hc:.0f} degC, CL10A105KB8NNNC (X5R) {T.term(d, 'x5r_max_C'):.0f} degC, BAT54S and BAV199 500 K/W and Tj 150 degC. "
              f"K's mean is {f(k_hi, 0)} degC at the high corner ({f(hc - k_hi, 0)} K margin) and {f(k_lo, 0)} degC at the low corner, "
              f"{f(k_hot, 0)} degC in its hottest cell; the screen cannot show the 85 degC limits met. This is a screen result, not a "
              'measured failure: the low corner stacks the contract load, conduction-only gaps, the lower emissivities and a resting '
              'rear wall. The decision on a limit or an option belongs to the design authority.', '']
    return lines


def item5(r):
    d = r['d']
    rows = T.sensitive_table(d)
    cells, meta = T.k_cells(d, 'contract', 40, 'V', 'low')
    cells120, meta120 = T.k_cells(d, 'contract', 120, 'V', 'low')
    n40, n120 = r['nets'][(40, 'V', 'low', 'contract')], r['nets'][(120, 'V', 'low', 'contract')]
    ks40, ks120 = n40['rise']['K'] - n40['rise']['shell'], n120['rise']['K'] - n120['rise']['shell']
    kf40, kf120 = n40['rise']['K'] - n40['rise']['JL'], n120['rise']['K'] - n120['rise']['JL']
    spread40 = max(c['rise_smooth_K'] for c in cells.values()) - min(c['rise_smooth_K'] for c in cells.values())
    spread120 = max(c['rise_smooth_K'] for c in cells120.values()) - min(c['rise_smooth_K'] for c in cells120.values())
    cores = [x for x in rows if x['function'].endswith('core')]
    hot_cores = sum(1 for x in cores if x['rise_40'] > 5.0)
    lines = [f"## 5. {hot_cores} of the 5 oscillator cores and the octave reference sit in K's hottest region (x 0 to 100, y 150 to 250, 7 to 11 K above K's mean); the thin case shrinks K's rise above the case ({f(ks120, 1)} to {f(ks40, 1)} K) and its lateral spread ({f(spread120, 1)} to {f(spread40, 1)} K) but couples the front boards closer to K", '',
             f"Regions are 50 mm cells of K in the partition frame. The lateral figure is the cell's density against K's mean over K's "
             f"coupling to its surroundings ({f(meta['h_K'], 1)} W/m2K at 40 mm), smoothed over the ASSUMED copper spreading length of "
             f"{f(meta['L_s_mm'], 0)} mm (the no-spreading bound is up to {f(max(c['rise_bound_K'] for c in cells.values()), 1)} K). "
             f"Contract load, standing, low coefficients. K stands {f(kf40, 1)} K above JL at 40 mm against {f(kf120, 1)} K at 120 mm. "
             'Pitch calibration stays at 25 degC; these are risks, not drift predictions. "Nearest hot" is the nearest of the 20 '
             'K packages with the highest dissipation; a 25 mm move of one part can change a distance verdict when the distance '
             'lies within 25 mm of the 50 mm cell size, and the sign of the lateral figure when a cell within 25 mm has the other sign.', '',
             '| Function | Part | Region on K | Lateral, 40 mm, K | Lateral, 120 mm, K | Nearest hot package, distance mm | Within 50 mm | A 25 mm move can change |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for x in rows:
        if x['function'].endswith('REF5050') and not x['function'].startswith(('OCTAVE', 'H1', 'H2', 'F')):
            continue
        change = []
        if x['move_changes_distance_verdict']:
            change.append('distance verdict')
        if x['move_changes_sign']:
            change.append('lateral sign')
        lines.append(f"| {x['function']} | {x['ref']} | {x['cell']} | {f(x['rise_40'], 1)} | {f(x['rise_120'], 1)} | "
                     f"{x['nearest_hot']} ({x['nearest_hot_symbol']}), {f(x['distance_mm'], 0)} | {'yes' if x['within_cell'] else 'no'} | "
                     f"{', '.join(change) or 'no'} |")
    others = [x for x in rows if x['function'].endswith('REF5050') and not x['function'].startswith(('OCTAVE', 'H1', 'H2', 'F'))]
    hot_refs = [x for x in others if x['rise_40'] > 2.0]
    lines += ['', f"The other {len(others)} local REF5050 references (E, W, A and M modules) are not listed row by row: "
              f"{len(hot_refs)} lie in cells more than 2 K above K's mean ({', '.join(x['ref'] for x in hot_refs)}). "
              f"{sum(1 for x in cores if x['within_cell'])} of the {len(cores)} cores stand within 50 mm of another hot package. "
              'The thin case changes which gradients grow: K-to-case and K-lateral shrink because K couples to the near rear wall; '
              'front-to-K shrinks too, so JL, JR and P run nearer to K and warmer against the case.', '',
              'Conclusions that a 25 mm move of a K part could change: '
              f"(a) the distance verdicts flagged in the table ({sum(1 for x in rows if x['move_changes_distance_verdict'])} of {len(rows)} sites); "
              f"(b) the sign of the lateral figure at {', '.join(x['function'] for x in rows if x['move_changes_sign'] and not x['function'].endswith('REF5050'))} "
              'and at the references flagged; (c) the hottest-cell term (up to '
              f"{f(max(c['rise_smooth_K'] for c in cells.values()), 1)} K) that item 4 adds to the parts in that cell. "
              'Conclusions that it cannot change: the board totals, the case rise, K\'s mean, the NEEDS_DESIGN verdict (K\'s mean alone '
              'passes 85 degC at the low corner), and the hot region itself, which spans about 100 mm, more than twice the move.', '']
    return lines


def item6(r):
    d = r['d']
    g_posts, area = T.post_conductance(d)
    net = r['nets'][(40, 'V', 'low', 'contract')]
    g_fk = sum(g['h'] * g['area_cm2'] * 1e-4 for g in net['gaps'] if g['lower'] == 'K' and g['upper'] != 'shell')
    base = net['rise']['K']
    v_lo, v_hi = T.lo_hi(d, 'vent_area_cm2')
    vent = T.network(d, 40, 'V', 'low', 'contract', vent_cm2=v_hi)
    deep = r['nets'][(120, 'V', 'low', 'contract')]
    red = T.network(d, 40, 'V', 'low', 'normal')
    per_w = (base - red['rise']['K']) / (r['contract']['internal_W'] - r['normal']['internal_W'])
    metal = T.network(d, 40, 'V', 'low', 'contract', eps_override=0.95)
    lines = [f"## 6. Five options are listed and none is selected; on paper the vent bounds K's rise down by {f(base - vent['rise']['K'], 1)} K at {v_hi} cm2 per vent, one watt less load by {f(per_w, 2)} K, and the posts' brass could add up to {f(g_posts[1], 2)} W/K between K and the front boards", '',
             f"Reference: 40 mm, standing, contract load, low coefficients: K at {f(base, 1)} K above ambient. The facing gaps couple "
             f"the front boards to K by {f(g_fk, 2)} W/K in that case.", '',
             '| Option | What it changes in the screen | What it conflicts with | Evidence it needs |', '| --- | --- | --- | --- |',
             f"| Vent slots in the side or rear walls | Upper bound: K -{f(base - vent['rise']['K'], 1)} K at {v_hi} cm2 per vent standing; lying panel-up the height between vents is {f(T.term(d, 'vent_height_m')['H_fraction_of_depth'] * 40 / 1000, 3)} m and the bound shrinks | Dust and EMC on an open case; the frame; the 191 retired K service apertures are retired, not a vent path, and the 2.8 mm behind K leaves no duct | A vent and case drawing; a flow estimate with the cable loops in the gaps; then the #64 measurement |",
             f"| Metal rear wall used as a spreader, high-emissivity inside | Holds the uniform-shell assumption the screen already makes; finish 0.95 inside and out moves K by {f(metal['rise']['K'] - base, 1)} K | K's rear parts are 2.8 mm from the wall: insulation and a shorting check are needed; supports and frame fixing; EMC grounding of the wall | Enclosure material, finish and emissivity; an insulation layer and its conductance |",
             f"| Conduction through the 18 brass posts and the 4 sleeves | Brass body alone {rng(*g_posts, 2)} W/K from K to the front boards ({f(1e6 * area, 1)} mm2 per post, ASSUMED bore); not credited. It couples K to JL, JR and P, not to the case: it lowers K only if the front boards have a path to the panel or case. The sleeves are printed plastic and carry nothing | The posts carry the supply current and are fixed by DS-33 and DS-75; no thermal path from a front board to the panel exists; ceramic-part strain rule of DS-42 near any added clamp | Thermal contact resistance of the nickel-brass face on the land (UNSOURCED); conductivity of CW614N; a front-board-to-case path |",
             f"| Larger case depth (120 mm row) | K {deep['rise']['K'] - base:+.1f} K at the same coefficients: the case runs {f(net['rise']['shell'] - deep['rise']['shell'], 1)} K cooler, but K's rear wall is {f(d['inputs']['enclosure_120_rear_clearance_from_K_B_face_mm'], 1)} mm away in place of {f(40 + d['inputs']['stack']['K_rear_z_mm'], 1)} mm, so depth alone does not cool K | The stack's depth target of about 40 mm (DS-13, DS-33); the inlet reservation (#57) | None beyond item 2 |",
             f"| Reduced load | {f(per_w, 2)} K per watt removed at K (40 mm standing low corner); the normal planning load is {f(r['contract']['internal_W'] - r['normal']['internal_W'], 2)} W below the contract | Circuit changes are out of scope; the ledger charges both rails for LEDs and outputs, so a refreshed ledger (ST-11) may already lower it | A measured supply current per rail (#64) and the ST-11 ledger refresh |", '']
    return lines


def item7(r):
    d = r['d']
    hi = r['nets'][(40, 'V', 'high', 'normal')]
    lo = r['nets'][(40, 'H', 'low', 'contract')]
    lines = ['## 7. Proposal for #64: soak at 40 degC in both orientations at the contract state, and pass when every part class stays inside its retained limit and the case and K rises stay inside the screen\'s bounds; #64 stays NOT RUN', '',
             'PROPOSAL only; nothing here is a test result. Limits marked "evidence first" cannot be set until the bundle holds the figure.', '',
             '| Element | Proposal |', '| --- | --- |',
             '| Ambient | Chamber or still room at 40 degC +/-1 K, measured at two points 100 mm from the case at mid-height, shielded; a 25 degC run as the reference |',
             f"| Soak | {T.term(d, 'soak_proposal')} |",
             f"| Operating state | Rails at nominal and at the upper tolerance; every LED lit; every output into 10 kOhm at 5 V; the measured rail currents recorded and compared with the ledger ({f(r['normal']['input_W'], 2)} W input) and the contract ({f(r['contract']['input_W'], 1)} W) |",
             '| Orientations | Standing with the base resting, and lying panel-up with the rear wall resting on a wooden board |',
             '| Case sensors | Panel centre, rear wall centre, each side wall centre, top face |',
             '| Internal sensors | Air in the JL/K and P/K gaps at their centres, air between K and the rear wall, K front and rear face at the five AS3340D cores, at U1601 (octave reference), at U115 and U215 (S&H) and in K\'s coolest region (upper edge) |',
             '| Part sensors | Case of the hottest AS3340D, OPA4197IPWR, OPA4197IDR, LF398M, LM13700M, NOISE2 and REF5050AIDR on K; the bleeder resistors at the inlet; one magnitude sense resistor on JL and on JR; one SN74HC14DR and one SN74HC74DR on K |',
             f"| Pass: screen consistency | Case rise inside {rng(hi['rise']['shell'], lo['rise']['shell'])} K and K mean rise inside {rng(hi['rise']['K'], lo['rise']['K'])} K; a reading outside invalidates the screen, not the design |",
             '| Pass: HC logic and X5R on K | Local air at the part at most 85 degC (SN74HC14DR, SN74HC74DR, CL10A105KB8NNNC) |',
             '| Pass: 0603 resistors | Dissipation under the series power curve at the measured local temperature; bleeder body at most 110 degC at its joint |',
             '| Pass: ICs | Tj from the measured case and the retained theta-JC or theta-JB at most the retained Tj max less 10 K: evidence first for every IC class of item 4 |',
             '| Pass: temperature-sensitive functions | Record each core\'s frequency, each reference and each S&H droop at 25 and 40 degC; no pass limit is proposed (calibration scope stays 25 degC) |', '']
    return lines


def evidence_needs(r):
    lines = ['## Evidence is needed for ten exact parts before any junction temperature can be stated', '',
             '| Exact part | Missing thermal evidence |', '| --- | --- |']
    for sym, (_, need) in LIMIT_FACTS.items():
        lines.append(f"| {sym} | {need.split(': ', 1)[1]} |")
    lines += ['| APHHS1005QWF/D and APG1005SEC/E-T (Kingbright) | Current derating with temperature and Tj max are not in the bundles |',
              '| The 5600 Ohm magnitude sense, 1200 Ohm stage and 22.1 kOhm clip resistors | Exact identity UNSELECTED; power curve and size |', '']
    return lines


def terms_table(r):
    d = r['d']
    lines = ['## 47 terms are ASSUMED or UNSOURCED; every other term is SOURCED with its pin or DERIVED', '',
             '| Term | Value | Unit | Status | Reason or source |', '| --- | --- | --- | --- | --- |']
    n = 0
    for name, t in d['terms'].items():
        if t['status'] in ('ASSUMED', 'UNSOURCED'):
            n += 1
            v = t['value']
            text = v if isinstance(v, str) else ('see JSON' if isinstance(v, list) and v and isinstance(v[0], list) else v)
            lines.append(f"| {name} | {text} | {t['unit']} | {t['status']} | {t['source']} |")
    lines[0] = f"## {n} terms are ASSUMED or UNSOURCED; every other term is SOURCED with its pin or DERIVED"
    return lines + ['']


def header(r):
    return ['# ST-05 thermal paper screen: NEEDS_DESIGN, because at the low corner K exceeds the 85 degC limits of its HC logic and X5R parts in either case depth', '',
            'Generated by `python3 scripts/stack/thermal/thermal_readme.py` from `thermal-screen.json`; do not edit by hand. '
            'A recomputable estimate on paper for the direct board stack at the 40 degC ambient corner of E19. Every board is an '
            'unvalidated draft; nothing is measured, nothing is selected, and #64 (the physical thermal test) stays NOT RUN. Sources are '
            'pinned by the object or row a term reads; the room study is read as of its record. Run `extract_inputs.py --check` to see '
            'whether a pinned source has changed.', '']


def checks_section():
    return ['## Checks run and NOT RUN', '',
            '| Check | State |', '| --- | --- |',
            '| Unit tests: `python3 scripts/checks/frozen_studies.py discover scripts/stack/thermal` | run by the executor; see the brief\'s result section |',
            '| `pnpm circuit:check` before and after | run by the executor; see the brief\'s result section |',
            '| CFD, airflow, vent or enclosure design | NOT RUN: out of scope (screen only) |',
            '| Physical thermal test #64 | NOT RUN: no assembled stack exists |',
            '| `regen-all.sh`, `pnpm check`, full Python suite | NOT RUN: excluded by the brief for time (CI near its limit) |', '']


def render():
    r = facts()
    lines = header(r) + plan_check(r) + item1(r) + item2(r) + item3(r) + item4(r) + item5(r) + item6(r) + item7(r) + \
        evidence_needs(r) + terms_table(r) + checks_section()
    return '\n'.join(lines).rstrip() + '\n'


def main(argv):
    text = render()
    if argv == ['--check']:
        same = README.exists() and README.read_text() == text
        print('README matches the rendering' if same else 'README differs from the rendering')
        return 0 if same else 1
    README.write_text(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
