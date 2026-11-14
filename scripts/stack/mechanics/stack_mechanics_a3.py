"""Attempt a3 of the ST-03 calculator: what remains after 191 K pairs became flat links (DS-39 to DS-46).

Reads `parameters.a3` and `geometry.a3` of stackups.json. The rigid-pair budgets of attempt a2 stay in
stack_mechanics.py on their a2 inputs (`parameters.da01`) as the record of the way back.
"""
import math

import stack_mechanics as sm

GRAVITY_MM_S2 = 9810.0      # standard gravity in mm/s^2
DENSITY_UNIT = 1e-9         # g/cm^3 to t/mm^3, so that t/mm^3 x mm/s^2 x mm gives N/mm^2


class A3:
    def __init__(self, c):
        self.c = c
        self.d = c.d
        self.g = c.g['a3']
        self.p = {k: v['value'] for k, v in c.d['parameters']['a3'].items()}

    def v(self, name):
        return self.c.v(name)

    # ---------- item 1: heights ----------
    def heights(self, joint, block):
        saved = self.c.p
        merged = dict(saved)
        if block == 'a3':
            merged['gap_mm'] = self.p['gap_mm']
            merged['stacker_A_in'] = self.p['stacker_A_in']
        self.c.p = merged
        try:
            return self.c.heights(joint)
        finally:
            self.c.p = saved

    # ---------- item 2: toggle window ----------
    def toggle_nominal(self, p_front_z):
        return -self.v('panel_thickness') - (p_front_z + self.v('toggle_body_height'))

    def toggle_terms(self, post_tol):
        t = self.d['terms']
        seat = self.v('post_seat_tol')
        return [('jack shoulder to JL/JR front face', t['jack_shoulder_to_board']['tol']),
                ('JL/JR thickness', t['board_thickness_1p6']['tol']),
                ('J post length', post_tol), ('J post seats, both ends', 2 * seat),
                ('P post length', post_tol), ('P post seats, both ends', 2 * seat),
                ('P thickness', t['board_thickness_1p6']['tol']),
                ('toggle body height', t['toggle_body_height']['tol'])]

    def toggle_cases(self):
        nominal = self.toggle_nominal(self.p['P_front_face_z_mm'])
        tol = self.p['post_length_tol_mm']
        match = self.p['post_match_mm']
        rows = []
        for label, post_tol, spread in (('unmatched (each post +/-0.15 mm)', tol, 2 * tol),
                                        ('matched within 0.05 mm per unit (lot mean still +/-0.15 mm)', tol, match)):
            vals = [x[1] for x in self.toggle_terms(post_tol)]
            wc, rss = sum(vals), math.sqrt(sum(x * x for x in vals))
            rows.append({'label': label, 'nominal': nominal, 'wc': wc, 'rss': rss, 'post_spread_between_toggles': 2 * spread})
        return rows

    # ---------- item 3: six adapter pairs ----------
    def selector_aperture(self):
        return self.c.aperture_clearance(self.d['apertures']['selector'])

    def adapter_board_limits(self, phase):
        c_min, c_max = self.selector_aperture()
        base = [('K against the panel on its post screws', self.p['k_post_hole_radial_play_mm']),
                ('selector hole position on the adapter', self.v('hole_position_tol_axis')),
                ('routed selector aperture position', self.v('routed_hole_position_tol_axis')),
                ('selector leg float', self.v('selector_leg_float'))]
        if phase == 'capture':
            return base + [('rest offset within the selector aperture clearance', c_max)], 0.0
        return base, c_min

    def adapter_xy(self, phase):
        c = self.c
        limits, shrink_by = self.adapter_board_limits(phase)
        pdf, half = sm.convolve([x[1] for x in limits])
        if shrink_by > 0:
            pdf, half = sm.shrink(pdf, half, shrink_by)
        per = sm.convolve([x[1] for x in c.per_pair_limits('O')])
        pairs = self.g['adapter_pairs']
        boards = sorted({p['board'] for p in pairs})
        n_each = len(pairs) // len(boards)
        cdf = sm.worst_of_n_cdf((pdf, half), per, n_each, c._xs) ** len(boards)
        wc = max(0.0, sum(x[1] for x in limits) - shrink_by) + sum(x[1] for x in c.per_pair_limits('O'))
        return {'n': len(pairs), 'median': sm.quantile(c._xs, cdf, 0.5), 'p95': sm.quantile(c._xs, cdf, 0.95), 'wc': wc}

    def selector_misfit(self):
        terms = [('K against the panel on its post screws', self.p['k_post_hole_radial_play_mm']),
                 ('SMT float, socket half', self.v('smt_float_front')), ('SMT float, stacker half', self.v('smt_float_k')),
                 ('selector leg float', self.v('selector_leg_float')),
                 ('selector hole position on the adapter', self.c.dv('hole_position_radial')),
                 ('routed aperture position', self.c.dv('routed_hole_position_radial'))]
        vals = [x[1] for x in terms]
        return terms, sum(vals), math.sqrt(sum(x * x for x in vals))

    def adapter_z_terms(self, pair):
        t = self.d['terms']
        k_len = self.c.g['outlines']['K']['longest_side_mm']
        return [('jack shoulder to JL front face', t['jack_shoulder_to_board']['tol']),
                ('JL thickness', t['board_thickness_1p6']['tol']),
                ('J post length', self.p['post_length_tol_mm']), ('J post seats', 2 * self.v('post_seat_tol')),
                ('K bow at the pair (screen model)', self.c.bow(k_len, pair['d_fixing_mm'])),
                ('selector seat on the panel', self.v('selector_seat_tol')),
                ('selector carrier to the panel', self.p['carrier_to_panel_mm']),
                ('adapter thickness', t['board_thickness_1p6']['tol']),
                ('standoff, socket half', self.v('connector_standoff_tol')),
                ('standoff, stacker half', self.v('connector_standoff_tol')),
                ('stacker pin length t', self.c.p['t_mm'])]

    def adapter_z(self):
        rows = []
        for pair in self.g['adapter_pairs']:
            vals = [x[1] for x in self.adapter_z_terms(pair)]
            rows.append((pair['id'], sum(vals), math.sqrt(sum(x * x for x in vals))))
        return max(rows, key=lambda r: r[1]), max(rows, key=lambda r: r[2])

    # ---------- item 4: K on 30 fixings ----------
    def plate(self):
        e, nu = self.v('fr4_modulus'), self.v('poisson_fr4')
        t = self.d['terms']['board_thickness_1p6']['value']
        return e, nu, t, e * t ** 3 / (12 * (1 - nu * nu))

    def uniform_case(self, q):
        e, nu, t, flex = self.plate()
        r = self.g['k_largest_bay']['radius_mm']
        w_clamped = q * r ** 4 / (64 * flex)
        w_simple = (5 + nu) / (1 + nu) * w_clamped
        m_edge = q * r * r / 8
        eps = 6 * m_edge * (1 - nu * nu) / (e * t * t)
        return w_clamped, w_simple, eps

    def point_case(self, force):
        e, nu, t, flex = self.plate()
        r = self.g['k_largest_bay']['radius_mm']
        b = self.p['latch_patch_radius_mm']
        w_clamped = force * r * r / (16 * math.pi * flex)
        w_simple = (3 + nu) / (1 + nu) * w_clamped
        eps_fixing = 6 * force / (4 * math.pi) * (1 - nu * nu) / (e * t * t)
        m_load = force * (1 + nu) / (4 * math.pi) * math.log(r / b)
        eps_load = 6 * m_load * (1 - nu) / (e * t * t)
        return w_clamped, w_simple, eps_fixing, eps_load

    def weight_pressure(self, g_level):
        t = self.d['terms']['board_thickness_1p6']['value']
        return self.p['fr4_density_g_cm3'] * DENSITY_UNIT * t * GRAVITY_MM_S2 * self.p['parts_mass_factor'] * g_level

    # ---------- item 5: printed sleeve chain ----------
    def sleeve_clearance(self, sorted_rule):
        allowance = -self.p['sleeve_length_allowance_mm']
        if sorted_rule:
            lo, hi = self.p['sleeve_sort_window_mm']
            err = self.p['caliper_error_mm']
            return lo - err, hi + err
        post, prt = self.p['post_length_tol_mm'], self.p['sleeve_print_tol_mm']
        return allowance - post - prt, allowance + post + prt

    def strain_pull(self, delta, span):
        return self.c.strain(delta, span)

    def turn_travel(self, fraction):
        return self.p['m3_pitch_mm'] * fraction


def f3(x):
    return f'{x:.3f}'


def render_a3_heights(c):
    a = A3(c)
    rows = []
    status = {'JL': 'closed record (flat links, DS-39)', 'JR': 'closed record (flat links, DS-39)',
              'P': 'closed record (flat links, DS-39)', 'O': 'live: six rigid 1x5 pairs', 'EL': 'live: six rigid 2x4 pairs, unchanged'}
    for j in ('JL', 'JR', 'P', 'O', 'EL'):
        h2, h3 = a.heights(j, 'a2'), a.heights(j, 'a3')
        rows.append([sm.JOINT_LABEL[j], f"{h2['gap']:.1f} / {h3['gap']:.1f}", f"{h2['A']:.3f} / {h3['A']:.3f}",
                     f"{h2['insertion']:.2f} / {h3['insertion']:.2f}", f"{h2['open']:.2f} / {h3['open']:.2f}",
                     ('open' if h3['close_window'] is None else f"{h2['close_window']:.2f} / {h3['close_window']:.2f}"),
                     f"{h2['body']:.3f} / {h3['body']:.3f}", status[j]])
    return sm.table(['Joint', 'Gap a2 / a3, mm', "Stacker 'A' a2 / a3, mm", 'Insertion a2 / a3, mm', 'Gap may open by a2 / a3, mm',
                     'Window closing margin a2 / a3, mm', 'Body clearance a2 / a3, mm', 'State'], rows)


def render_a3_changes(c):
    a = A3(c)
    t2 = a.toggle_nominal(c.v('p_front_face_z'))
    tog = a.toggle_cases()[0]
    a2_vals = c.p_mismatch_terms()
    rows = [['K F.Cu z, mm', f3(c.p['K_face_z_mm']), f3(a.p['K_face_z_mm']), 'DS-33'],
            ['K rear face z, mm', f3(c.p['K_face_z_mm'] - c.d['terms']['board_thickness_1p6']['value']), f3(a.p['K_rear_z_mm']), 'DS-33'],
            ['P F.Cu z, mm', f3(c.v('p_front_face_z')), f3(a.p['P_front_face_z_mm']), 'DS-33'],
            ['Post length tolerance, mm', f"+/-{c.v('post_length_tol'):.2f} (ASSUMED)", f"+/-{a.p['post_length_tol_mm']:.2f} (SOURCED)", 'DS-33'],
            ['Toggle gap, nominal, mm', f3(t2), f3(tog['nominal']), 'DERIVED'],
            ['Toggle gap, worst case, mm', f'{t2 - sum(a2_vals):.2f} to {t2 + sum(a2_vals):.2f}',
             f"{tog['nominal'] - tog['wc']:.2f} to {tog['nominal'] + tog['wc']:.2f}", 'DERIVED'],
            ['Toggle take-up window, mm', '0.3 to 2.1 (D4)', f"{a.p['toggle_window_mm'][0]} to {a.p['toggle_window_mm'][1]}", 'DS-27'],
            ['Fixings on K', '18 posts + 12 kept supports (+5 provisional)', '18 posts + 12 printed sleeves', 'DS-43'],
            ['Rigid K pairs', '197', str(len(a.g['adapter_pairs'])), 'DS-39']]
    return sm.table(['Figure', 'Attempt a2', 'Attempt a3', 'Basis'], rows)


def render_a3_toggle(c):
    a = A3(c)
    lo, hi = a.p['toggle_window_mm']
    rows = []
    for r in a.toggle_cases():
        for kind in ('wc', 'rss'):
            low, high = r['nominal'] - r[kind], r['nominal'] + r[kind]
            miss = []
            if low < lo:
                miss.append(f'{lo - low:.2f} below')
            if high > hi:
                miss.append(f'{high - hi:.2f} above')
            rows.append([r['label'], 'worst case' if kind == 'wc' else 'root sum of squares', f3(r['nominal']), f'{low:.2f} to {high:.2f}',
                         f'{lo} to {hi}', 'inside' if not miss else 'misses: ' + ', '.join(miss), f"{r['post_spread_between_toggles']:.2f}"])
    return sm.table(['Posts', 'Method', 'Nominal gap, mm', 'Gap range, mm', 'DS-27 window, mm', 'Verdict',
                     'Post part of the gap difference between two toggles of one P, mm (worst case)'], rows)


def render_a3_toggle_terms(c):
    a = A3(c)
    rows = [[name, f3(val)] for name, val in a.toggle_terms(a.p['post_length_tol_mm'])]
    return sm.table(['Toggle-gap term (panel thickness cancels: jacks and toggles both seat on the panel rear)', '+/- mm'], rows)


def render_a3_adapters(c):
    a = A3(c)
    lim = c.p['misalignment_mm']
    rows = []
    for phase, limits in (('capture', lim['initial']), ('final', lim['final'])):
        r = a.adapter_xy(phase)

        def word(x):
            return f"along {'meets' if x <= limits['along'] else 'misses'} {limits['along']}; across {'meets' if x <= limits['across_single'] else 'misses'} {limits['across_single']}"
        rows.append([phase, r['n'], f3(r['median']), f3(r['p95']), f3(r['wc']), 'median: ' + word(r['median']) + ' / p95: ' + word(r['p95'])])
    return sm.table(['Phase', 'Pairs', 'Worst pair, median, mm per axis', '95th percentile, mm', 'Worst case, mm',
                     'Against the sourced MMS limits (V-MMS-SPEC 5.1.1, 5.1.2)'], rows)


def render_a3_adapter_terms(c):
    a = A3(c)
    rows = []
    for phase in ('capture', 'final'):
        limits, shrink_by = a.adapter_board_limits(phase)
        text = '; '.join(f'{n} {f3(v)}' for n, v in limits)
        if shrink_by:
            text += f'; less the minimum selector clearance {f3(shrink_by)}'
        rows.append([phase, text, '; '.join(f'{n} {f3(v)}' for n, v in c.per_pair_limits('O'))])
    return sm.table(['Phase', 'Drawn once per adapter (uniform per axis, mm)', 'Drawn once per pair (uniform per axis, mm)'], rows)


def render_a3_selector(c):
    a = A3(c)
    terms, wc, rss = a.selector_misfit()
    c_min, _ = a.selector_aperture()
    grown = c_min + (a.p['selector_aperture_grown_mm'] - c.d['apertures']['selector']['hole']) / 2
    rows = [[n, f3(v)] for n, v in terms]
    rows += [['Worst case', f3(wc)], ['Root sum of squares', f3(rss)],
             ['Selector clearance at 7.0 mm (budget)', f3(c_min)], ['Over the budget (RSS)', f3(rss - c_min)],
             [f"Selector clearance at {a.p['selector_aperture_grown_mm']} mm (DA-01 D4 remedy)", f3(grown)],
             ['Over that clearance (RSS)', f3(rss - grown)]]
    return sm.table(['Selector misfit: K-located pairs against the panel-located shaft', 'mm, radial'], rows)


def render_a3_adapter_z(c):
    a = A3(c)
    (wid, wc, _), (rid, _, rss) = a.adapter_z()
    h = a.heights('O', 'a3')
    rows = [[n, f3(v)] for n, v in a.adapter_z_terms([p for p in a.g['adapter_pairs'] if p['id'] == wid][0])]
    rows += [[f'Worst case ({wid})', f3(wc)], [f'Root sum of squares ({rid})', f3(rss)],
             ['Gap may open by (window)', f3(h['open'])], ['Gap may close by (body clearance governs)', f3(h['close'])],
             ['Verdict', f"RSS {'meets' if rss <= min(h['open'], h['close']) else 'misses'} both sides; worst case "
                         f"{'meets' if wc <= min(h['open'], h['close']) else 'misses'} the closing side by {max(0.0, wc - h['close']):.3f}"]]
    return sm.table(['Adapter Z term (carrier is the datum, DS-31; 13.0 mm gap)', 'mm'], rows)


def render_a3_k(c):
    a = A3(c)
    lim = c.dv('strain_design_limit')
    bay = a.g['k_largest_bay']
    rows = []
    for label, g_level in (('own weight (1 g)', 1.0), (f"handling ({a.p['handling_g']:g} g on the weight)", a.p['handling_g'])):
        w_c, w_s, eps = a.uniform_case(a.weight_pressure(g_level))
        rows.append([label, 'uniform', f3(w_c), f3(w_s), sm.ue(eps), 'n/a', 'within' if eps <= lim else 'exceeds'])
    lo, hi = a.p['latch_force_N']
    for force in (1.0, lo, hi):
        w_c, w_s, e_fix, e_load = a.point_case(force)
        label = 'per newton (rescale)' if force == 1.0 else f'latch or cable push {force:g} N, one at a time'
        worst = max(e_fix, e_load)
        rows.append([label, f'point, {a.p["latch_patch_radius_mm"]:g} mm patch', f3(w_c), f3(w_s), sm.ue(e_fix), sm.ue(e_load),
                     'within' if worst <= lim else 'exceeds'])
    head = f"Largest bay without a fixing: radius {bay['radius_mm']:.1f} mm, centre {bay['centre_xy']}"
    return sm.table([head, 'Load', 'Deflection, clamped edge, mm', 'Deflection, simply supported edge, mm',
                     'Strain at the fixings (clamped edge), microstrain', 'Strain under the load, microstrain',
                     f'Against {lim * 1e6:.0f} microstrain'], rows)


def render_a3_sleeves(c):
    a = A3(c)
    lim = c.dv('strain_design_limit')
    gaps = {'JL': a.p['gap_mm']['JL'], 'JR': a.p['gap_mm']['JR'], 'P': a.p['gap_mm']['P']}
    free_lo, free_hi = a.sleeve_clearance(False)
    rule_lo, rule_hi = a.sleeve_clearance(True)
    eighth = a.turn_travel(1 / 8)
    rows = []
    for s in a.g['sleeves']:
        span = s['d_fixing_mm']
        allow = c.delta_allow(lim, span)
        rows.append([s['id'], s['board'], f"{gaps[s['board']]:.1f}", f"{s['nearest_fixing']} {span:.1f}", f3(allow),
                     sm.ue(a.strain_pull(eighth, span)), sm.ue(a.strain_pull(-free_lo, span)), sm.ue(a.strain_pull(free_hi, span)),
                     sm.ue(a.strain_pull(rule_hi, span))])
    return sm.table(['Sleeve', 'Board', 'Gap, mm', 'Nearest fixing, span s, mm', f'K pull allowed at {lim * 1e6:.0f} microstrain, mm',
                     f'Strain from 1/8 turn past contact ({eighth:.4f} mm), microstrain',
                     f'Strain, sleeve {-free_lo:.2f} mm too long, no sorting, microstrain',
                     f'Strain, nut drawn down {free_hi:.2f} mm, no sorting, microstrain',
                     f'Strain, nut drawn down {rule_hi:.2f} mm, sorted, microstrain'], rows)


def render_a3_sleeve_chain(c):
    a = A3(c)
    free_lo, free_hi = a.sleeve_clearance(False)
    rule_lo, rule_hi = a.sleeve_clearance(True)
    rows = [['Sleeve modelled short by', f3(-a.p['sleeve_length_allowance_mm']), 'SOURCED (S-SPACER, DS-45)'],
            ['Print length tolerance', f"+/-{a.p['sleeve_print_tol_mm']:.2f}", 'ASSUMED (DS-45)'],
            ['Post length tolerance (sets the local gap)', f"+/-{a.p['post_length_tol_mm']:.2f}", 'SOURCED (DS-33)'],
            ['Clearance sleeve end to K, no sorting', f'{free_lo:.2f} to {free_hi:.2f}', 'DERIVED (negative = sleeve longer than the gap)'],
            ['Clearance with the sorting rule (caliper error included)', f'{rule_lo:.2f} to {rule_hi:.2f}', 'DERIVED from the ASSUMED rule'],
            ['Nut travel per turn (M3 coarse)', f3(a.p['m3_pitch_mm']), 'DERIVED']]
    return sm.table(['Sleeve chain term', 'mm', 'Status'], rows)


def render_a3_terms(c):
    rows = []
    for name, t in c.d['parameters']['a3'].items():
        basis = t.get('locator') or t.get('formula') or ('to source: ' + t.get('to_source', ''))
        src = t.get('source', '')
        rows.append([f'`a3.{name}`', str(t['value']).replace('|', '/'), t['status'], (f'{src}: ' if src else '') + basis.replace('|', '/')])
    return sm.table(['Parameter', 'Value', 'Status', 'Source, formula or what would source it'], rows)


RENDERERS = {
    'a3_changes': render_a3_changes, 'a3_heights': render_a3_heights, 'a3_toggle': render_a3_toggle,
    'a3_toggle_terms': render_a3_toggle_terms, 'a3_adapters': render_a3_adapters, 'a3_adapter_terms': render_a3_adapter_terms,
    'a3_selector': render_a3_selector, 'a3_adapter_z': render_a3_adapter_z, 'a3_k': render_a3_k,
    'a3_sleeve_chain': render_a3_sleeve_chain, 'a3_sleeves': render_a3_sleeves, 'a3_terms': render_a3_terms,
}
