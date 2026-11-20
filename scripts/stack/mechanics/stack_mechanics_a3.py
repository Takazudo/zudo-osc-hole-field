"""Attempt a3 of the ST-03 calculator: what remains after 191 K pairs became flat links (DS-39 to DS-46).

Reads `parameters.a3` and `geometry.a3` of stackups.json. The rigid-pair budgets of attempt a2 stay in
stack_mechanics.py on their a2 inputs (`parameters.da01`) as the record of the way back.
"""
from functools import lru_cache
import math

import numpy as np

import stack_mechanics as sm

GRAVITY_MM_S2 = 9810.0      # standard gravity in mm/s^2
DENSITY_UNIT = 1e-9         # g/cm^3 to t/mm^3, so that t/mm^3 x mm/s^2 x mm gives N/mm^2
COARSE = 10                 # board-level distributions resampled to 10 x GRID_STEP for the common-K order statistic
FIXING_SETS = (('posts_only', '18 posts only'), ('posts_and_sleeves', '18 posts and 12 sleeves'))


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
        if block == 'a3':
            return self.c.heights(joint, gap_mm=self.p['gap_mm'], stacker_a_in=self.p['stacker_A_in'])
        return self.c.heights(joint)

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
        """Terms drawn once per adapter; K's play on its post screws is drawn once for all adapters (item 3)."""
        c_min, c_max = self.selector_aperture()
        base = [('selector hole position on the adapter', self.v('hole_position_tol_axis')),
                ('routed selector aperture position', self.v('routed_hole_position_tol_axis')),
                ('selector leg float', self.v('selector_leg_float'))]
        if phase == 'capture':
            return base + [('rest offset within the selector aperture clearance', c_max)], 0.0
        return base, c_min

    def adapter_xy(self, phase):
        limits, shrink_by = self.adapter_board_limits(phase)
        pairs = self.g['adapter_pairs']
        boards = sorted({p['board'] for p in pairs})
        per = tuple(x[1] for x in self.c.per_pair_limits('O'))
        cdf = common_k_worst_cdf(self.p['k_post_hole_radial_play_mm'], tuple(x[1] for x in limits), shrink_by, per,
                                 len(boards), len(pairs) // len(boards), tuple(self.c._xs))
        wc = max(0.0, self.p['k_post_hole_radial_play_mm'] + sum(x[1] for x in limits) - shrink_by) + sum(per)
        xs = self.c._xs
        return {'n': len(pairs), 'median': sm.quantile(xs, cdf, 0.5), 'p95': sm.quantile(xs, cdf, 0.95), 'wc': wc}

    def selector_misfit(self):
        terms = [('K against the panel on its post screws', self.p['k_post_hole_radial_play_mm']),
                 ('SMT float, socket half', self.v('smt_float_front')), ('SMT float, stacker half', self.v('smt_float_k')),
                 ('selector leg float', self.v('selector_leg_float')),
                 ('selector hole position on the adapter', self.c.dv('hole_position_radial')),
                 ('routed aperture position', self.c.dv('routed_hole_position_radial'))]
        vals = [x[1] for x in terms]
        return terms, sum(vals), math.sqrt(sum(x * x for x in vals))

    def adapter_z_terms(self, pair, fixing_set='posts_only'):
        t = self.d['terms']
        k_len = self.c.g['outlines']['K']['longest_side_mm']
        return [('jack shoulder to JL front face', t['jack_shoulder_to_board']['tol']),
                ('JL thickness', t['board_thickness_1p6']['tol']),
                ('J post length', self.p['post_length_tol_mm']), ('J post seats', 2 * self.v('post_seat_tol')),
                ('K bow at the pair (screen model)', self.c.bow(k_len, pair['d_post_mm' if fixing_set == 'posts_only' else 'd_fixing_mm'])),
                ('selector seat on the panel', self.v('selector_seat_tol')),
                ('selector carrier to the panel', self.p['carrier_to_panel_mm']),
                ('adapter thickness', t['board_thickness_1p6']['tol']),
                ('standoff, socket half', self.v('connector_standoff_tol')),
                ('standoff, stacker half', self.v('connector_standoff_tol')),
                ('stacker pin length t', self.c.p['t_mm'])]

    def adapter_z(self, fixing_set='posts_only'):
        rows = []
        for pair in self.g['adapter_pairs']:
            vals = [x[1] for x in self.adapter_z_terms(pair, fixing_set)]
            rows.append((pair['id'], sum(vals), math.sqrt(sum(x * x for x in vals))))
        return max(rows, key=lambda r: r[1]), max(rows, key=lambda r: r[2])

    # ---------- item 4: K on 30 fixings ----------
    def plate(self):
        e, nu = self.v('fr4_modulus'), self.v('poisson_fr4')
        t = self.d['terms']['board_thickness_1p6']['value']
        return e, nu, t, e * t ** 3 / (12 * (1 - nu * nu))

    def strain_cylindrical(self, m):
        e, nu, t, _ = self.plate()
        return 6 * m * (1 - nu * nu) / (e * t * t)

    def bay_uniform(self, q, radius):
        """Circular bay: the larger of the clamped and simply supported plate (deflection and strain)."""
        e, nu, t, flex = self.plate()
        w_clamped = q * radius ** 4 / (64 * flex)
        w_simple = (5 + nu) / (1 + nu) * w_clamped
        eps_clamped_edge = self.strain_cylindrical(q * radius * radius / 8)
        eps_simple_centre = 6 * (3 + nu) * q * radius * radius / 16 * (1 - nu) / (e * t * t)
        return max(w_clamped, w_simple), max(eps_clamped_edge, eps_simple_centre)

    def bay_point(self, force, radius):
        """Circular bay, load on a patch at the centre: simply supported deflection; the larger strain at the fixings or under the load."""
        e, nu, t, flex = self.plate()
        b = self.p['latch_patch_radius_mm']
        w_simple = (3 + nu) / (1 + nu) * force * radius * radius / (16 * math.pi * flex)
        eps_fixing = self.strain_cylindrical(force / (4 * math.pi))
        eps_load = 6 * force * (1 + nu) / (4 * math.pi) * math.log(radius / b) * (1 - nu) / (e * t * t)
        return w_simple, max(eps_fixing, eps_load)

    def edge_uniform(self, q, span):
        """Region reaching a free edge: a strip cantilevered from its nearest fixing, cylindrical bending."""
        _, _, _, flex = self.plate()
        return q * span ** 4 / (8 * flex), self.strain_cylindrical(q * span * span / 2)

    def edge_point(self, force, span):
        """Push at the free edge: root moment spread over an effective width of 2 x span (45 degree spread, ASSUMED)."""
        _, _, _, flex = self.plate()
        width = self.p['edge_spread_width_factor'] * span
        return force * span ** 3 / (3 * flex * width), self.strain_cylindrical(force * span / width)

    def k_models(self, fixing_set, load):
        """Rows (region, span, deflection, strain) for one fixing set and one load ('g', level) or ('push', N)."""
        reg = self.g['k_regions'][fixing_set]
        kind, size = load
        rows = []
        q = self.weight_pressure(size) if kind == 'g' else None
        bay = reg['interior_bay']['radius_mm']
        w, e = self.bay_uniform(q, bay) if q is not None else self.bay_point(size, bay)
        rows.append(('interior bay (circular plate)', bay, w, e))
        for key, label in (('edge_region_low_y', 'free-edge region, low y'), ('edge_region_high_y', 'free-edge region, high y')):
            span = reg[key]['span_mm']
            w, e = self.edge_uniform(q, span) if q is not None else self.edge_point(size, span)
            rows.append((label + ' (cantilever strip)', span, w, e))
        return rows

    def k_governing(self, fixing_set, load):
        return max(self.k_models(fixing_set, load), key=lambda r: r[3])

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

    def loads(self):
        lo, hi = self.p['latch_force_N']
        return [('own weight (1 g)', ('g', 1.0)), (f"handling ({self.p['handling_g']:g} g on the weight)", ('g', self.p['handling_g'])),
                ('push per newton (rescale)', ('push', 1.0)), (f'latch or cable push {lo:g} N', ('push', float(lo))),
                (f'latch or cable push {hi:g} N', ('push', float(hi)))]

    def strain_pull(self, delta, span):
        return self.c.strain(delta, span)

    def turn_travel(self, fraction):
        return self.p['m3_pitch_mm'] * fraction


def coarse(pdf, half):
    vals = np.arange(-half, half + 1) * sm.GRID_STEP
    idx = np.round(vals / (sm.GRID_STEP * COARSE)).astype(int)
    keys, inv = np.unique(idx, return_inverse=True)
    return keys * sm.GRID_STEP * COARSE, np.bincount(inv, weights=pdf)


@lru_cache(maxsize=8)
def common_k_worst_cdf(k_limit, adapter_limits, shrink_by, per_pair_limits, n_adapters, n_each, xs):
    """P(max over all pairs of |S(K + A_i) + X_ij| <= x): K once, A_i once per adapter, X_ij once per pair.

    S shrinks the misfit by the selector's minimum clearance in the final state (the adapter follows its pairs
    until the shaft meets the aperture wall).
    """
    k_vals, k_w = coarse(*sm.uniform_pdf(k_limit))
    a_vals, a_w = coarse(*sm.convolve(list(adapter_limits)))
    xpdf, xh = sm.convolve(list(per_pair_limits))
    xcdf = np.cumsum(xpdf)
    grid = np.arange(-xh, xh + 1) * sm.GRID_STEP
    x = np.array(xs)[:, None]
    out = np.zeros(len(xs))
    for k, wk in zip(k_vals, k_w):
        s = k + a_vals
        if shrink_by > 0:
            s = np.sign(s) * np.maximum(0.0, np.abs(s) - shrink_by)
        g = np.clip(np.interp(x - s, grid, xcdf, left=0.0, right=1.0) - np.interp(-x - s, grid, xcdf, left=0.0, right=1.0), 0.0, 1.0)
        out += wk * ((g ** n_each) @ a_w) ** n_adapters
    return out


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
    w2 = c.p['toggle_takeup_window_mm']
    fx2 = {k: len(v) for k, v in c.g['fixings'].items()}
    fx3 = {}
    for key, n in a.g['fixing_counts'].items():
        kind = key.rsplit(' ', 1)[0]
        fx3[kind] = fx3.get(kind, 0) + n
    rows = [['K F.Cu z, mm', f3(c.p['K_face_z_mm']), f3(a.p['K_face_z_mm']), 'DS-33'],
            ['K rear face z, mm', f3(c.p['K_face_z_mm'] - c.d['terms']['board_thickness_1p6']['value']), f3(a.p['K_rear_z_mm']), 'DS-33'],
            ['P F.Cu z, mm', f3(c.v('p_front_face_z')), f3(a.p['P_front_face_z_mm']), 'DS-33'],
            ['Post length tolerance, mm', f"+/-{c.v('post_length_tol'):.2f} (ASSUMED)", f"+/-{a.p['post_length_tol_mm']:.2f} (SOURCED)", 'DS-33'],
            ['Toggle gap, nominal, mm', f3(t2), f3(tog['nominal']), 'DERIVED'],
            ['Toggle gap, worst case, mm', f'{t2 - sum(a2_vals):.2f} to {t2 + sum(a2_vals):.2f}',
             f"{tog['nominal'] - tog['wc']:.2f} to {tog['nominal'] + tog['wc']:.2f}", 'DERIVED'],
            ['Toggle take-up window, mm', f"{w2[0]} to {w2[1]} (DA-01 D4)", f"{a.p['toggle_window_mm'][0]} to {a.p['toggle_window_mm'][1]}", 'DS-27'],
            ['Fixings on K', f"{fx2['posts']} posts + {fx2['kept_supports']} kept supports (+{fx2['provisional']} provisional)",
             f"{fx3['post']} posts + {fx3['kept support']} printed sleeves", 'DS-43'],
            ['Rigid K pairs', str(sum(1 for p in c.g['pairs'] if p['joint'] != 'EL')), str(len(a.g['adapter_pairs'])), 'DS-39']]
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
            text += f'; the sum with K, less the minimum selector clearance {f3(shrink_by)}'
        rows.append([phase, f"K against the panel on its post screws {f3(a.p['k_post_hole_radial_play_mm'])}", text,
                     '; '.join(f'{n} {f3(v)}' for n, v in c.per_pair_limits('O'))])
    return sm.table(['Phase', 'Drawn once for all six pairs (uniform per axis, mm)', 'Drawn once per adapter (uniform per axis, mm)',
                     'Drawn once per pair (uniform per axis, mm)'], rows)


def render_a3_selector(c):
    a = A3(c)
    terms, wc, rss = a.selector_misfit()
    c_min, _ = a.selector_aperture()
    grown = c_min + (a.p['selector_aperture_grown_mm'] - c.d['apertures']['selector']['hole']) / 2
    rows = [[n, f3(v)] for n, v in terms]
    rows += [['Worst case', f3(wc)], ['Root sum of squares', f3(rss)],
             [f"Selector clearance at {c.d['apertures']['selector']['hole']} mm (budget)", f3(c_min)], ['Over the budget (RSS)', f3(rss - c_min)],
             [f"Selector clearance at {a.p['selector_aperture_grown_mm']} mm (DA-01 D4 remedy)", f3(grown)],
             ['Over that clearance (RSS)', f3(rss - grown)]]
    return sm.table(['Selector misfit: K-located pairs against the panel-located shaft', 'mm, radial'], rows)


def adapter_z_verdict(a, fixing_set):
    """Worst case and RSS against both sides of the adapter window (item 4)."""
    (wid, wc, _), (rid, _, rss) = a.adapter_z(fixing_set)
    h = a.heights('O', 'a3')

    def side(x):
        return {'open': x - h['open'], 'close': x - h['close']}
    return {'wc_pair': wid, 'wc': wc, 'rss_pair': rid, 'rss': rss, 'open': h['open'], 'close': h['close'],
            'wc_miss': side(wc), 'rss_miss': side(rss)}


def miss_text(miss):
    parts = [f"{'misses' if v > 0 else 'meets'} the {k}ing side" + (f' by {v:.3f}' if v > 0 else f' with {-v:.3f} to spare')
             for k, v in miss.items()]
    return '; '.join(parts).replace('closeing', 'closing')


def render_a3_adapter_z(c):
    a = A3(c)
    v = adapter_z_verdict(a, 'posts_only')
    pair = [p for p in a.g['adapter_pairs'] if p['id'] == v['wc_pair']][0]
    rows = [[n, f3(x)] for n, x in a.adapter_z_terms(pair, 'posts_only')]
    rows += [[f"Worst case ({v['wc_pair']})", f3(v['wc'])], [f"Root sum of squares ({v['rss_pair']})", f3(v['rss'])],
             ['Gap may open by (window)', f3(v['open'])], ['Gap may close by (body clearance governs)', f3(v['close'])],
             ['Verdict, worst case', miss_text(v['wc_miss'])], ['Verdict, root sum of squares', miss_text(v['rss_miss'])]]
    gap = a.p['gap_mm']['O']
    return sm.table([f'Adapter Z term (carrier is the datum, DS-31; {gap} mm gap; K bow from the 18 posts only)', 'mm'], rows)


def render_a3_adapter_z_sets(c):
    a = A3(c)
    rows = []
    for key, label in FIXING_SETS:
        v = adapter_z_verdict(a, key)
        bow = max(c.bow(c.g['outlines']['K']['longest_side_mm'], p['d_post_mm' if key == 'posts_only' else 'd_fixing_mm'])
                  for p in a.g['adapter_pairs'])
        rows.append([label, f3(bow), f3(v['wc']), f3(v['rss']), miss_text(v['wc_miss']), miss_text(v['rss_miss'])])
    return sm.table(['Fixings holding K in Z', 'Largest K bow at an adapter pair, mm', 'Worst case, mm', 'RSS, mm',
                     'Worst case verdict', 'RSS verdict'], rows)


def render_a3_k(c):
    a = A3(c)
    lim = c.dv('strain_design_limit')
    rows = []
    for key, label in FIXING_SETS:
        for load_label, load in a.loads():
            for region, span, w, e in a.k_models(key, load):
                rows.append([label, load_label, region, f'{span:.1f}', f3(w), sm.ue(e), 'within' if e <= lim else 'exceeds'])
    return sm.table(['Fixings', 'Load', 'Region and model', 'Span or radius, mm', 'Deflection, mm', 'Strain, microstrain',
                     f'Against {lim * 1e6:.0f} microstrain'], rows)


def render_a3_k_governing(c):
    a = A3(c)
    lim = c.dv('strain_design_limit')
    rows = []
    for load_label, load in a.loads():
        cells = [load_label]
        for key, _ in FIXING_SETS:
            region, span, w, e = a.k_governing(key, load)
            cells += [f'{region}, {span:.1f} mm', f3(w), sm.ue(e)]
        e_posts = a.k_governing('posts_only', load)[3]
        cells.append('within' if e_posts <= lim else 'exceeds')
        rows.append(cells)
    return sm.table(['Load', 'Governing region, 18 posts only', 'Deflection, mm', 'Strain, microstrain',
                     'Governing region, posts and sleeves', 'Deflection, mm', 'Strain, microstrain',
                     f'Verdict on the posts alone, against {lim * 1e6:.0f} microstrain'], rows)


def render_a3_k_regions(c):
    a = A3(c)
    rows = []
    for key, label in FIXING_SETS:
        reg = a.g['k_regions'][key]
        rows.append([label, f"radius {reg['interior_bay']['radius_mm']:.1f} at {reg['interior_bay']['centre_xy']}",
                     f"{reg['edge_region_low_y']['span_mm']:.1f} from {reg['edge_region_low_y']['point_xy']}",
                     f"{reg['edge_region_high_y']['span_mm']:.1f} from {reg['edge_region_high_y']['point_xy']}"])
    rows_y = a.g['k_regions']['posts_only']['post_rows_y_mm']
    return sm.table(['Fixings', 'Largest circle inside the outline holding no fixing, mm',
                     f'Free-edge region y < {rows_y[0]:g}: farthest point from a fixing, mm',
                     f'Free-edge region y > {rows_y[-1]:g}: farthest point from a fixing, mm'], rows)


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
    'a3_selector': render_a3_selector, 'a3_adapter_z': render_a3_adapter_z, 'a3_adapter_z_sets': render_a3_adapter_z_sets,
    'a3_k_regions': render_a3_k_regions, 'a3_k_governing': render_a3_k_governing, 'a3_k': render_a3_k,
    'a3_sleeve_chain': render_a3_sleeve_chain, 'a3_sleeves': render_a3_sleeves, 'a3_terms': render_a3_terms,
}
