"""ST-03 stack mechanics calculator, attempt a2 (DA-01 decisions).

Reads design/stack/mechanics/stackups.json only and recomputes every number that
design/stack/mechanics/README.md shows. Tables in the README sit between
<!-- calc:NAME --> markers; `--write-readme` refreshes them, and the tests require
the committed README to equal this output. The order statistics are computed on a
fixed grid (no random numbers), so a second run writes the same bytes.

  python3 scripts/stack/mechanics/stack_mechanics.py               print all tables
  python3 scripts/stack/mechanics/stack_mechanics.py --refresh-geometry --write-readme
"""
from pathlib import Path
import json
import math
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'design/stack/mechanics/stackups.json'
README = ROOT / 'design/stack/mechanics/README.md'
GRID_STEP = 0.0005          # mm; numerical grid of the per-axis distributions
X_MAX = 1.5                 # mm; upper end of the worst-pair search
JOINTS = ['JL', 'JR', 'P', 'O', 'EL']
JOINT_LABEL = {'JL': 'JL to K', 'JR': 'JR to K', 'P': 'P unit to K', 'O': 'O1/O3/O5 to K', 'EL': 'EL to P'}
FRONT_FIXED = {'JL', 'JR', 'P'}
# DA-01 D2: O1, O3 and O5 each join K through two new standoffs.
ADAPTER_STANDOFFS = 2 * 3


def load(path=DATA):
    return json.loads(Path(path).read_text())


# ---------- numerical distributions (per axis) ----------
def uniform_pdf(limit):
    n = int(round(limit / GRID_STEP))
    if n == 0:
        return np.array([1.0]), 0
    w = np.ones(2 * n + 1)
    return w / w.sum(), n


def convolve(limits):
    pdf, half = np.array([1.0]), 0
    for lim in limits:
        u, n = uniform_pdf(lim)
        pdf = np.convolve(pdf, u)
        half += n
    return pdf, half


def shrink(pdf, half, by):
    """Distribution of sign(B) * max(0, |B| - by): the board moves within its clearance."""
    n = int(round(by / GRID_STEP))
    x = np.arange(-half, half + 1)
    out_half = max(half - n, 0)
    out = np.zeros(2 * out_half + 1)
    for i, p in zip(x, pdf):
        j = 0 if abs(i) <= n else (i - n if i > 0 else i + n)
        out[j + out_half] += p
    return out, out_half


def worst_of_n_cdf(board, per_pair, n_pairs, xs):
    """P(max over N pairs of |B + X_i| <= x), B drawn once per board, X_i per pair."""
    bpdf, bh = board
    xpdf, xh = per_pair
    xcdf = np.cumsum(xpdf)
    grid = np.arange(-xh, xh + 1) * GRID_STEP
    bvals = np.arange(-bh, bh + 1) * GRID_STEP
    keep = bpdf > 1e-12
    bvals, bp = bvals[keep], bpdf[keep]
    out = []
    for x in xs:
        hi = np.interp(x - bvals, grid, xcdf, left=0.0, right=1.0)
        lo = np.interp(-x - bvals, grid, xcdf, left=0.0, right=1.0)
        out.append(float(np.sum(bp * np.clip(hi - lo, 0.0, 1.0) ** n_pairs)))
    return np.array(out)


def quantile(xs, cdf, q):
    idx = int(np.searchsorted(cdf, q))
    return float(xs[min(idx, len(xs) - 1)])


class Calc:
    def __init__(self, data):
        self.d = data
        self.t = data['terms']
        self.g = data['geometry']
        self.p = {k: v['value'] for k, v in data['parameters']['da01'].items()}
        self._xs = np.round(np.arange(0.0, X_MAX + GRID_STEP / 2, 0.001), 3)

    def v(self, name):
        return self.t[name]['value']

    # ---------- derived terms ----------
    def derived(self):
        eps_test = 6 * self.v('murata_board') * self.v('murata_flexure') / self.v('murata_span') ** 2
        pin_minus = self.t['loc_pin_diameter']['minus']
        return {
            'strain_test_level': eps_test,
            'strain_design_limit': eps_test / self.v('strain_safety_factor'),
            'hole_position_radial': math.sqrt(2) * self.v('hole_position_tol_axis'),
            'routed_hole_position_radial': math.sqrt(2) * self.v('routed_hole_position_tol_axis'),
            'r_loc_standard': (self.v('loc_hole_clearance_standard') + self.v('pth_hole_tol_plus') + pin_minus) / 2,
            'r_slot': (self.v('loc_slot_clearance') + self.v('pth_hole_tol_plus') + pin_minus) / 2,
            'm25_pitch': 0.45,
        }

    def dv(self, name):
        return self.derived()[name]

    # ---------- pairs ----------
    def pairs(self, joint):
        return [p for p in self.g['pairs'] if p['joint'] == joint]

    def positions(self, pair):
        if pair['joint'] == 'EL':
            return self.p['el_positions_per_pair']
        return pair['positions_candidate']

    # ---------- heights (D3) ----------
    def heights(self, joint):
        gap = self.p['gap_mm'][joint]
        tip = self.p['stacker_tip_mm'][joint]
        a_mm = self.p['stacker_A_in'][joint] * 25.4
        if joint == 'EL':
            sock = self.p['socket_height_mm']['EL']
            ins = tip + sock - gap
            win_min, win_max = self.p['insertion_window_mm']['EL_min'], None
        else:
            sock = self.p['socket_height_mm']['single']
            ins = tip + sock - gap
            win_min, win_max = self.p['insertion_window_mm']['single']
        body = gap - sock - a_mm
        open_margin = ins - win_min
        close_window = (win_max - ins) if win_max is not None else None
        close_margin = body if close_window is None else min(close_window, body)
        return {'gap': gap, 'tip': tip, 'A': a_mm, 'socket': sock, 'insertion': ins, 'open': open_margin,
                'close_window': close_window, 'body': body, 'close': close_margin}

    # ---------- XY (M1, M2) ----------
    def tightest(self, board):
        best = None
        for ap in self.d['apertures'].values():
            if ap.get('hole') is None or board not in ap['board'] or 'carrier' in ap:
                continue
            c_min = (ap['hole'] - ap['hole_minus'] - ap['part_max']) / 2 - ap['wobble']
            c_max = (ap['hole'] + ap['hole_plus'] - ap['part_min']) / 2
            if best is None or c_min < best[0]:
                best = (c_min, c_max)
        return best

    def per_pair_limits(self, joint):
        lean = self.p['stacker_tip_mm'][joint] * math.tan(math.radians(self.v('pin_lean_deg')))
        return [('SMT float, socket half', self.v('smt_float_front')), ('SMT float, stacker half', self.v('smt_float_k')),
                ('stacker lean at the tip', lean)]

    def board_limits(self, joint, phase):
        """Per-axis limits of the terms drawn once per board, D2 order."""
        axis = self.v('hole_position_tol_axis')
        if joint == 'O':
            return [], 0.0
        if joint == 'EL':
            k = self.v('el_locator_ratio')
            return [('EL hole registration', axis), ('P hole registration', axis), ('collar float', self.dv('r_loc_standard')),
                    ('rotation: slot float x ratio', self.dv('r_slot') * k), ('rotation: hole pair spacing, both boards', 4 * axis * k)], 0.0
        c_min, c_max = self.tightest(joint if joint != 'JR' else 'JR')
        base = [('hardware float on board', self.v('th_lead_float')), ('hardware hole registration', axis),
                ('aperture position', axis)]
        if phase == 'capture':
            return base + [('rest offset within the aperture clearance', c_max)], 0.0
        return base, c_min

    def board_dist(self, joint, phase):
        limits, shrink_by = self.board_limits(joint, phase)
        pdf, half = convolve([x[1] for x in limits])
        if shrink_by > 0:
            pdf, half = shrink(pdf, half, shrink_by)
        return pdf, half

    def worst_pair(self, joint, phase, lean_deg=None):
        saved = self.t['pin_lean_deg']['value']
        if lean_deg is not None:
            self.t['pin_lean_deg']['value'] = lean_deg
        try:
            n = len(self.pairs(joint))
            groups = 3 if joint == 'O' else 1
            n_each = n // groups
            per = convolve([x[1] for x in self.per_pair_limits(joint)])
            cdf = worst_of_n_cdf(self.board_dist(joint, phase), per, n_each, self._xs) ** groups
        finally:
            self.t['pin_lean_deg']['value'] = saved
        return cdf

    def xy_row(self, joint, phase):
        cdf = self.worst_pair(joint, phase)
        limits, shrink_by = self.board_limits(joint, phase)
        wc_board = max(0.0, sum(x[1] for x in limits) - shrink_by)
        wc = wc_board + sum(x[1] for x in self.per_pair_limits(joint))
        return {'n': len(self.pairs(joint)), 'median': quantile(self._xs, cdf, 0.5), 'p95': quantile(self._xs, cdf, 0.95),
                'wc': wc, 'cdf': cdf}

    def xy_all(self, phase):
        cdf = np.ones_like(self._xs, dtype=float)
        for joint in ('JL', 'JR', 'P', 'O'):
            cdf = cdf * self.worst_pair(joint, phase)
        return {'n': sum(len(self.pairs(j)) for j in ('JL', 'JR', 'P', 'O')), 'median': quantile(self._xs, cdf, 0.5),
                'p95': quantile(self._xs, cdf, 0.95)}

    # ---------- selector chain (D4) ----------
    def selector_chain(self):
        terms = [('K against the panel', self.p['k_vs_panel_selector_mm']), ('SMT float, socket half', self.v('smt_float_front')),
                 ('SMT float, stacker half', self.v('smt_float_k')), ('selector leg float', self.v('selector_leg_float')),
                 ('selector hole position on the adapter', self.dv('hole_position_radial')),
                 ('routed aperture position', self.dv('routed_hole_position_radial'))]
        vals = [x[1] for x in terms]
        return terms, sum(vals), math.sqrt(sum(x * x for x in vals))

    # ---------- apertures (M3) ----------
    def aperture_baseline(self, ap):
        terms = [self.v(ap['hw_float_term']), self.dv('hole_position_radial'), self.dv(ap['panel_pos_term'])]
        return sum(terms), math.sqrt(sum(x * x for x in terms))

    def aperture_clearance(self, ap):
        return ((ap['hole'] - ap['hole_minus'] - ap['part_max']) / 2 - ap['wobble'],
                (ap['hole'] + ap['hole_plus'] - ap['part_min']) / 2)

    # ---------- Z (M5, M6) ----------
    def bow(self, length, d):
        return 4 * self.v('bow_twist_ratio') * d * d / length

    def z_terms(self, pair, tag):
        o = self.g['outlines']
        panel_len = max(self.g['panel_size_mm'])
        k_len = o['K']['longest_side_mm']
        terms = [('post length', self.v('post_length_tol')), ('post seat, front', self.v('post_seat_tol')),
                 ('post seat, K', self.v('post_seat_tol')), ('standoff, socket half', self.v('connector_standoff_tol')),
                 ('standoff, stacker half', self.v('connector_standoff_tol'))]
        j = pair['joint']
        if j in ('JL', 'JR'):
            terms += [('panel bow at the J fixing distance', self.bow(panel_len, pair['d_front_' + tag])),
                      ('local jack seat', self.v('jack_shoulder_local')),
                      ('K bow', self.bow(k_len, pair['d_K_' + tag]))]
        elif j == 'P':
            terms += [('P bow', self.bow(o['P']['longest_side_mm'], pair['d_front_' + tag])),
                      ('K bow', self.bow(k_len, pair['d_K_' + tag]))]
        elif j == 'O':
            side = o['O1']['longest_side_mm']
            terms += [('adapter bow within its outline', self.bow(side, side)), ('K bow within one adapter outline', self.bow(k_len, side))]
        else:
            d = self.g['el_outer_site_overhang_mm']
            terms += [('EL bow at the outer site', self.bow(o['EL']['longest_side_mm'], d)),
                      ('P tab bow at the outer site', self.bow(o['P']['longest_side_mm'], d))]
        return terms

    def z_joint(self, joint, tag):
        rows = []
        for pair in self.pairs(joint):
            terms = self.z_terms(pair, tag)
            vals = [x[1] for x in terms]
            rows.append((pair['id'], sum(vals), math.sqrt(sum(x * x for x in vals))))
        wc = max(rows, key=lambda r: r[1])
        rss = max(rows, key=lambda r: r[2])
        return wc, rss

    # ---------- coverage (D4 40 mm rule) ----------
    def coverage(self, tag):
        rule = self.p['fixing_distance_rule_mm']
        miss = {}
        for pair in self.g['pairs']:
            if pair['joint'] not in FRONT_FIXED:
                continue
            if pair['d_front_' + tag] > rule or pair['d_K_' + tag] > rule:
                miss.setdefault(pair['joint'], []).append(pair['id'])
        return miss

    # ---------- dish (M7) ----------
    def dish(self, tag, f):
        bay = self.g['largest_bay'][tag]
        r = bay['radius_mm']
        ids = set(bay['pairs_inside'])
        n = sum(self.positions(p) for p in self.g['pairs'] if p['id'] in ids)
        force = n * f
        q = force / (math.pi * r * r)
        e, nu, t = self.v('fr4_modulus'), self.v('poisson_fr4'), self.t['board_thickness_1p6']['value']
        flex = e * t ** 3 / (12 * (1 - nu * nu))
        clamped = q * r ** 4 / (64 * flex)
        simple = (5 + nu) / (1 + nu) * clamped
        return {'radius': r, 'positions': n, 'force': force, 'clamped': clamped, 'simple': simple, 'centre': bay['centre_pair']}

    # ---------- K strain (M8, F1) ----------
    def toggle_gap(self):
        return -self.v('panel_thickness') - (self.v('p_front_face_z') + self.v('toggle_body_height'))

    def p_mismatch_terms(self):
        tb = self.t['board_thickness_1p6']['tol']
        return [self.t['jack_shoulder_to_board']['tol'], tb, self.v('post_length_tol'), 2 * self.v('post_seat_tol'),
                self.v('post_length_tol'), 2 * self.v('post_seat_tol'), tb, self.t['toggle_body_height']['tol']]

    def seam_terms(self):
        tb = self.t['board_thickness_1p6']['tol']
        span = self.g['jl_jr_inner_post_span_mm']
        panel_len = max(self.g['panel_size_mm'])
        return [self.t['jack_shoulder_to_board']['tol']] * 2 + [tb, tb, 2 * self.v('post_length_tol'),
                                                                 4 * self.v('post_seat_tol'), self.bow(panel_len, span / 2)]

    @staticmethod
    def wc_rss(vals):
        return sum(vals), math.sqrt(sum(x * x for x in vals))

    def strain(self, delta, span):
        return 3 * self.t['board_thickness_1p6']['value'] * delta / span ** 2

    def delta_allow(self, limit, span):
        return limit * span ** 2 / (3 * self.t['board_thickness_1p6']['value'])

    def strain_cases(self):
        spans = self.g['j_to_p_post_row_spacing_mm']
        pm_wc, pm_rss = self.wc_rss(self.p_mismatch_terms())
        sm_wc, sm_rss = self.wc_rss(self.seam_terms())
        tg = self.toggle_gap()
        cases = []
        for s in spans:
            cases.append(('P pulled by toggle front nuts only (nominal gap closed)', s, tg + pm_wc, tg + pm_rss))
            cases.append(('P clamped to the panel at a fixed stop and bolted to K', s, pm_wc, pm_rss))
        cases.append(('JL and JR planes both from jack shoulders, K bolted to both', self.g['jl_jr_inner_post_span_mm'], sm_wc, sm_rss))
        return cases

    def bow_flatten_strain(self):
        return 8 * self.v('bow_twist_ratio') / self.g['outlines']['K']['longest_side_mm'] * self.t['board_thickness_1p6']['value'] / 2

    # ---------- forces (M9) ----------
    def board_fixings(self, board, tag):
        sets = ['posts', 'kept_supports'] + (['provisional'] if tag == 'plus' else [])
        return sum(1 for s in sets for f in self.g['fixings'][s] if f['board'] == board)

    def force_rows(self):
        rows = []
        for joint in ('JL', 'JR', 'P', 'O', 'EL'):
            n = sum(self.positions(p) for p in self.pairs(joint))
            if joint == 'O':
                fix = (ADAPTER_STANDOFFS, ADAPTER_STANDOFFS)
            elif joint == 'EL':
                fix = (None, None)
            else:
                fix = (self.board_fixings(joint, 'base'), self.board_fixings(joint, 'plus'))
            rows.append((JOINT_LABEL[joint], n, fix))
        return rows

    def k_positions(self):
        return sum(self.positions(p) for p in self.g['pairs'] if p['joint'] != 'EL')

    # ---------- EL plate ----------
    def el_plate(self, f, thickness):
        e = self.v('fr4_modulus')
        b = span = self.g['el_tab_post_pitch_mm']
        c = self.g['el_outer_site_overhang_mm']
        force = self.p['el_positions_per_pair'] * f
        inertia = b * thickness ** 3 / 12
        return (force, force * span ** 3 / (48 * e * inertia), force * span * thickness / (8 * e * inertia),
                force * c ** 3 / (3 * e * inertia), force * c * thickness / (2 * e * inertia))


# ---------- rendering ----------
def mm(x):
    return f'{x:.3f}'


def ue(x):
    return f'{x * 1e6:.0f}'


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(str(x) for x in r) + ' |' for r in rows]
    return '\n'.join(out)


def render_heights(c):
    rows = []
    cand = c.g['candidate_heights_mm']
    cand_key = {'JL': 'JL/K', 'JR': 'JR/K', 'P': 'P/K', 'O': 'O1/K', 'EL': 'EL/P'}
    for j in JOINTS:
        h = c.heights(j)
        rows.append([JOINT_LABEL[j], mm(h['gap']), mm(h['tip']), mm(h['A']), mm(h['socket']), mm(h['insertion']),
                     mm(h['open']), mm(h['close_window']) if h['close_window'] is not None else 'open (pins pass through)',
                     mm(h['body']), mm(h['close']), mm(cand[cand_key[j]])])
    return table(['Joint', 'Gap, mm', 'Pin tip, mm', 'Stacker A, mm', 'Socket, mm', 'Insertion, mm',
                  'Gap may open by, mm', 'Gap may close by (window), mm', 'Body clearance, mm',
                  'Gap may close by (governing), mm', 'Height in the geometry candidate, mm (note only)'], rows)


def render_xy(c):
    lim = c.p['misalignment_mm']
    rows = []
    for phase, key in (('capture', 'initial'), ('final', 'final')):
        along = lim[key]['along']
        across = lim[key]['across_single']
        for j in JOINTS:
            r = c.xy_row(j, phase)
            if j == 'EL':
                verdict = 'UNSOURCED limit (CLT); MMS double-row reference ' + str(lim[key]['across_double_MMS'])
            else:
                verdict = ('along ' + ('meets' if r['p95'] <= along else 'misses') + f' {along}; across ' +
                           ('meets' if r['p95'] <= across else 'misses') + f' {across}')
            rows.append([phase, JOINT_LABEL[j], r['n'], mm(r['median']), mm(r['p95']), mm(r['wc']), verdict])
        a = c.xy_all(phase)
        rows.append([phase, 'all K pairs', a['n'], mm(a['median']), mm(a['p95']), 'n/a',
                     ('along ' + ('meets' if a['p95'] <= along else 'misses') + f' {along}; across ' +
                      ('meets' if a['p95'] <= across else 'misses') + f' {across}')])
    return table(['Phase', 'Pairs', 'N', 'Worst pair, median, mm per axis', 'Worst pair, 95th percentile, mm',
                  'Worst case, mm', 'p95 against the sourced limits'], rows)


def render_xy_terms(c):
    rows = []
    for j in JOINTS:
        for phase in ('capture', 'final'):
            limits, shrink_by = c.board_limits(j, phase)
            board = '; '.join(f'{n} {mm(v)}' for n, v in limits) or 'none (the adapter floats onto K)'
            if shrink_by:
                board += f'; less the minimum clearance {mm(shrink_by)}'
            per = '; '.join(f'{n} {mm(v)}' for n, v in c.per_pair_limits(j))
            rows.append([JOINT_LABEL[j], phase, board, per])
    return table(['Pairs', 'Phase', 'Drawn once per board (uniform per axis, limits in mm)', 'Drawn once per pair (uniform per axis, mm)'], rows)


def render_lean(c):
    rows = []
    for deg in (c.v('pin_lean_deg'), c.p['pin_sway_max_deg']):
        cdf = c.worst_pair('P', 'final', lean_deg=deg)
        rows.append([f'{deg:g}', mm(quantile(c._xs, cdf, 0.5)), mm(quantile(c._xs, cdf, 0.95))])
    return table(['Lean, degrees', 'P unit final worst pair, median, mm', '95th percentile, mm'], rows)


def render_selector(c):
    terms, wc, rss = c.selector_chain()
    rows = [[n, mm(v)] for n, v in terms] + [['Worst case', mm(wc)], ['Root sum of squares', mm(rss)],
                                             ['Budget (S-SEL, kept by DA-01 D4)', mm(c.p['selector_budget_mm'])],
                                             ['Over the budget (RSS)', mm(rss - c.p['selector_budget_mm'])]]
    return table(['Selector-row term (adapters on K, D4)', 'mm, radial'], rows)


def render_apertures(c):
    rows = []
    for cls, ap in c.d['apertures'].items():
        if ap.get('hole') is None or 'carrier' in ap:
            continue
        wc, rss = c.aperture_baseline(ap)
        c_min, c_max = c.aperture_clearance(ap)
        rows.append([cls, f"{ap['hole']}", mm(c_min), mm(c_max), mm(wc), mm(rss),
                     'closes' if rss <= c_min else f'fails by {mm(rss - c_min)}'])
    return table(['Class', 'Hole, mm', 'Min radial clearance, mm', 'Max radial clearance, mm',
                  'Baseline WC, mm (hardware-on-board only)', 'Baseline RSS, mm', 'Baseline RSS verdict'], rows)


def render_el_passages(c):
    rows = []
    for cls, ap in c.d['apertures'].items():
        if 'carrier' not in ap:
            continue
        c_min, _ = c.aperture_clearance(ap)
        limits, _ = c.board_limits('EL', 'final')
        vals = [c.v(ap['hw_float_term']), c.dv('hole_position_radial'), c.dv('hole_position_radial')] + [x[1] for x in limits]
        wc, rss = c.wc_rss(vals)
        rows.append([cls, f"{ap['hole']}", mm(c_min), mm(wc), mm(rss), 'closes' if rss <= c_min else f'fails by {mm(rss - c_min)}'])
    return table(['EL passage', 'Hole, mm (a1 values)', 'Min radial clearance, mm', 'WC, mm', 'RSS, mm', 'RSS verdict'], rows)


def render_z(c):
    rows = []
    t = c.p['t_mm']
    for j in JOINTS:
        h = c.heights(j)
        for tag in (('base', 'plus') if j in FRONT_FIXED else ('base',)):
            (wid, wc, _), (rid, _, rss) = c.z_joint(j, tag)
            basis = {'base': '18 posts + 12 kept supports', 'plus': '+ 5 provisional sites'}[tag] if j in FRONT_FIXED else (
                'adapter standoffs (not placed)' if j == 'O' else 'EL collar posts')
            need_wc, need_rss = wc + t, rss + t
            v_open = 'meets' if need_rss <= h['open'] else 'misses'
            v_close = 'meets' if need_rss <= h['close'] else 'misses'
            rows.append([JOINT_LABEL[j], basis, f'{wid} {mm(wc)}', f'{rid} {mm(rss)}', mm(need_wc), mm(need_rss),
                         mm(h['open']), mm(h['close']), f'RSS: open {v_open}, close {v_close}; WC: ' +
                         ('meets both' if need_wc <= min(h['open'], h['close']) else 'misses')])
    return table(['Joint', 'Fixings', 'Worst pair WC: id, mm', 'Worst pair RSS: id, mm', 'Need WC (+ t), mm',
                  'Need RSS (+ t), mm', 'Margin open, mm', 'Margin close, mm', 'Verdict'], rows)


def render_coverage(c):
    rows = []
    for tag, label in (('base', '18 posts + 12 kept supports'), ('plus', 'with the 5 provisional sites')):
        miss = c.coverage(tag)
        for j in ('JL', 'JR', 'P'):
            ids = miss.get(j, [])
            rows.append([label, j, len(ids), ', '.join(ids) if ids else 'none'])
    return table(['Fixings', 'Board', 'Pairs beyond 40 mm', 'References'], rows)


def render_coverage_worst(c):
    rows = []
    for j in ('JL', 'JR', 'P'):
        ps = c.pairs(j)
        rows.append([j] + [mm(max(p['d_front_' + tag] for p in ps)) + ' / ' + mm(max(p['d_K_' + tag] for p in ps))
                           for tag in ('base', 'plus')])
    return table(['Board', 'Farthest pair, front-board / K fixing, mm (base)', 'Same with the 5 provisional sites, mm'], rows)


def render_dish(c):
    rows = []
    for tag, label in (('base', '18 posts + 12 kept supports'), ('plus', 'with the 5 provisional sites')):
        for f in c.p['mating_force_N']:
            r = c.dish(tag, f)
            rows.append([label, r['centre'], mm(r['radius']), r['positions'], f, f"{r['force']:.0f}", mm(r['clamped']), mm(r['simple'])])
    return table(['Fixings', 'Bay centre (pair)', 'Bay radius, mm', 'Positions in the bay', 'f, N', 'Force, N',
                  'Dish, clamped edge, mm', 'Dish, simply supported edge, mm'], rows)


def render_strain(c):
    lim_t = c.dv('strain_test_level')
    lim_d = c.dv('strain_design_limit')
    rows = []
    for name, span, d_wc, d_rss in c.strain_cases():
        e_wc, e_rss = c.strain(d_wc, span), c.strain(d_rss, span)
        verdict = 'within design limit' if e_wc <= lim_d else ('within test level only' if e_wc <= lim_t else 'exceeds test level')
        rows.append([name, mm(span), mm(d_wc), mm(d_rss), ue(e_wc), ue(e_rss), verdict])
    rows.append([f"K pulled flat from {c.v('bow_twist_ratio') * 100:g}% bow at fixings", 'n/a', 'n/a', 'n/a', ue(c.bow_flatten_strain()),
                 ue(c.bow_flatten_strain()), 'within design limit' if c.bow_flatten_strain() <= lim_d else 'exceeds'])
    return table(['Case (upper bound: K alone bends)', 'Span s, mm', 'Delta WC, mm', 'Delta RSS, mm', 'Strain WC, microstrain',
                  'Strain RSS, microstrain', 'Verdict (WC)'], rows)


def render_strain_allow(c):
    rows = []
    for s in c.g['j_to_p_post_row_spacing_mm'] + [c.g['jl_jr_inner_post_span_mm']]:
        rows.append([mm(s), mm(c.delta_allow(c.dv('strain_design_limit'), s)), mm(c.delta_allow(c.dv('strain_test_level'), s))])
    return table(['Span s, mm', f"Lower bound of the allowed Delta at {ue(c.dv('strain_design_limit'))} microstrain, mm",
                  f"Lower bound at the test level {ue(c.dv('strain_test_level'))} microstrain, mm"], rows)


def render_toggle(c):
    gap = c.toggle_gap()
    wc, _ = c.wc_rss(c.p_mismatch_terms())
    lo, hi = c.p['toggle_takeup_window_mm']
    rows = [['Nominal gap, toggle body front to panel rear', mm(gap), 'DERIVED'],
            ['Gap range, worst case (P follows K)', f'{mm(gap - wc)} to {mm(gap + wc)}', 'DERIVED'],
            ['D4 washer working range', f'{lo} to {hi}', 'SOURCED (DA-01 D4)'],
            ['Range inside the D4 window', 'yes' if gap - wc >= lo - 1e-9 and gap + wc <= hi + 1e-9 else 'no', 'DERIVED'],
            ['Rear jam nut thickness against the nominal gap', f"{mm(c.v('toggle_nut_thickness'))} vs {mm(gap)}", 'SOURCED / DERIVED']]
    return table(['Quantity', 'mm', 'Status'], rows)


def render_forces(c):
    mate = c.p['mating_force_N']
    unm = c.p['unmating_force_N']
    rows = []
    for label, n, fix in c.force_rows():
        per = 'n/a (platen)' if fix[0] is None else ' / '.join(f'{n * f / fix[0]:.0f}' for f in mate) + f' over {fix[0]}'
        per_plus = 'n/a' if fix[1] is None else f'{n * max(mate) / fix[1]:.0f} over {fix[1]}'
        rows.append([label, n] + [f'{n * f:.0f}' for f in mate] + [f'{n * unm[0]:.0f} to {n * unm[1]:.0f}', per, per_plus])
    k = c.k_positions()
    rows.append(['K, all joints (count: K positions)', k] + [f'{k * f:.0f}' for f in mate] + [f'{k * unm[0]:.0f} to {k * unm[1]:.0f}', '', ''])
    tot = c.p['positions_per_side_total']
    rows.append(['All joints per side incl. EL (count: DA-01 D6)', tot] + [f'{tot * f:.0f}' for f in mate] + [f'{tot * unm[0]:.0f} to {tot * unm[1]:.0f}', '', ''])
    return table(['Joint', 'Positions'] + [f'Mating at {f} N, N' for f in mate] + [f'Unmating at {unm[0]} to {unm[1]} N, N',
                  'Draw-down load per fixing at each f, N (posts + kept supports)', f'At {max(mate)} N with the {len(c.g["fixings"]["provisional"])} provisional sites, N'], rows)


def render_el(c):
    rows = []
    lim = c.dv('strain_design_limit')
    for thick in (c.t['el_thickness']['value'], c.t['el_thickness']['value'] - c.t['el_thickness']['tol']):
        for f in c.p['mating_force_N']:
            force, md, me, cd, ce = c.el_plate(f, thick)
            rows.append([mm(thick), f, f'{force:.1f}', mm(md), ue(me), mm(cd), ue(ce),
                         'exceeds design limit' if max(me, ce) > lim else 'within design limit'])
    return table(['EL thickness, mm', 'f, N', 'Force per site, N', 'Mid-span deflection, mm', 'Mid-span strain, microstrain',
                  'Outer-site deflection, mm', 'Outer-site strain, microstrain', 'Unbacked EL'], rows)


def render_closing(c):
    rows = []
    for s in c.d['closing_order']:
        xy = '; '.join(f'{k}: {v}' for k, v in s['XY'].items())
        z = '; '.join(f'{k}: {v}' for k, v in s['Z'].items())
        rows.append([s['step'], s['action'], xy, z, s['joint_chain']])
    return table(['Step', 'Action (DA-01 D2)', 'XY set by', 'Z set by', 'Chain at this step'], rows)


def render_terms(c):
    rows = []
    for name, t in c.t.items():
        val = t['value']
        if isinstance(val, float):
            val = f'{val:g}'
        tol = f"+/-{t['tol']}" if 'tol' in t else (f"+{t['plus']}/-{t['minus']}" if 'plus' in t else '')
        if t['status'] == 'DERIVED':
            basis = t['formula']
        elif t['status'] == 'ASSUMED':
            basis = 'to source: ' + t['to_source']
        else:
            basis = t.get('source', '') + ': ' + t.get('locator', '')
        rows.append([f'`{name}`', val, tol, t['unit'], t['status'], basis.replace('|', '/')])
    for name, t in c.d['parameters']['da01'].items():
        val = json.dumps(t['value']).replace('|', '/')
        basis = t.get('formula') or ('to source: ' + t['to_source'] if 'to_source' in t else t.get('source', '') + ': ' + t.get('locator', ''))
        rows.append([f'`da01.{name}`', val, '', '', t['status'], basis.replace('|', '/')])
    return table(['Term', 'Value', 'Tolerance', 'Unit', 'Status', 'Source, formula or what would source it'], rows)


def render_supports(c):
    rows = [[s['items'], s['count'], s['disposition'], s['reason']] for s in c.d['supports_disposition']]
    total = sum(s['count'] for s in c.d['supports_disposition'] if s['counts_toward_87'])
    rows.append(['Total of the 87 partition supports', total, '', ''])
    return table(['Items', 'Count', 'Disposition', 'Reason'], rows)


def render_coupon(c):
    cp = c.d['coupon']
    t1 = table(['Board', 'Role', 'Outline', 'Thickness, mm', 'Contents'],
               [[b['id'], b['role'], b['outline_mm'], b['thickness_mm'], b['contents']] for b in cp['boards']])
    t2 = table(['Measurement', 'What it measures', 'Pass number (DA-01 D5)'], [[m['id'], m['what'], m['pass']] for m in cp['measurements']])
    return t1 + '\n\n' + t2


def render_open(c):
    return table(['Figure', 'Exact need'], [[f['figure'], f['exact_need']] for f in c.d['open_figures']])


def render_notes(c):
    cand = c.g['candidate_heights_mm']
    rows = [['K F.Cu z', mm(c.g['candidate_K_face_z_mm']), mm(c.p['K_face_z_mm'])]]
    for key, j in (('JL/K', 'JL'), ('JR/K', 'JR'), ('P/K', 'P'), ('O1/K', 'O'), ('EL/P', 'EL')):
        rows.append([f'{key} gap', mm(cand[key]), mm(c.p['gap_mm'][j])])
    return table(['Height (note, not an error)', 'Geometry candidate, mm', 'Used here (DA-01), mm'], rows)


RENDERERS = {
    'notes': render_notes, 'closing': render_closing, 'heights': render_heights, 'xy': render_xy,
    'xy_terms': render_xy_terms, 'lean': render_lean, 'selector': render_selector, 'apertures': render_apertures,
    'el_passages': render_el_passages, 'z_gap': render_z, 'coverage': render_coverage, 'coverage_worst': render_coverage_worst,
    'dish': render_dish, 'strain_allow': render_strain_allow, 'strain': render_strain, 'toggle': render_toggle,
    'forces': render_forces, 'el_plate': render_el, 'supports': render_supports, 'coupon': render_coupon,
    'open': render_open, 'terms': render_terms,
}


def render_all(data=None):
    c = Calc(data or load())
    return {name: fn(c) for name, fn in RENDERERS.items()}


BLOCK = re.compile(r'(<!-- calc:(\w+) -->\n)(?:(.*?)\n)?(<!-- /calc:\2 -->)', re.S)


def fill_readme(text, blocks):
    return BLOCK.sub(lambda m: m.group(1) + blocks[m.group(2)] + '\n' + m.group(4), text)


def main(argv):
    data = load()
    if '--refresh-geometry' in argv:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from stack_mechanics_geometry import derive
        data['geometry'] = derive(data)
        DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    blocks = render_all(data)
    if '--write-readme' in argv:
        README.write_text(fill_readme(README.read_text(), blocks))
    elif '--refresh-geometry' not in argv:
        for name, text in blocks.items():
            print(f'## {name}\n\n{text}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
