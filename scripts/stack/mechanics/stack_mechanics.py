"""ST-03 stack mechanics calculator.

Reads design/stack/mechanics/stackups.json only and recomputes every number that
design/stack/mechanics/README.md shows. Tables in the README sit between
<!-- calc:NAME --> markers; `--write-readme` refreshes them and the tests require
the committed README to equal this output.

  python3 scripts/stack/mechanics/stack_mechanics.py               print all tables
  python3 scripts/stack/mechanics/stack_mechanics.py --write-readme
  python3 scripts/stack/mechanics/stack_mechanics.py --refresh-geometry
"""
from pathlib import Path
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'design/stack/mechanics/stackups.json'
README = ROOT / 'design/stack/mechanics/README.md'
MULTILAYER = {'JL', 'JR', 'P'}
FRONT_UNITS = ['JL', 'JR', 'P', 'O1', 'EL']
UNIT_LABEL = {'JL': 'JL to K', 'JR': 'JR to K', 'P': 'P unit to K', 'O1': 'O1/O3/O5 to K', 'EL': 'EL to P'}
SCHEMES = {
    'diag_precise': 'two corner pins, press-fit hole class',
    'diag_standard': 'two corner pins, ordinary hole class',
    'posts': 'two end posts as pilots, ordinary hole class',
}


def load(path=DATA):
    return json.loads(Path(path).read_text())


class Calc:
    def __init__(self, data):
        self.d = data
        self.t = data['terms']
        self.g = data['geometry']
        self.p = data['parameters']

    def v(self, name):
        return self.t[name]['value']

    # ---------- derived terms ----------
    def derived(self):
        t = self.t
        eps_test = 6 * self.v('murata_board') * self.v('murata_flexure') / self.v('murata_span') ** 2
        pin_minus = t['loc_pin_diameter']['minus']
        return {
            'strain_test_level': eps_test,
            'strain_design_limit': eps_test / self.v('strain_safety_factor'),
            'hole_position_radial': math.sqrt(2) * self.v('hole_position_tol_axis'),
            'routed_hole_position_radial': math.sqrt(2) * self.v('routed_hole_position_tol_axis'),
            'r_loc_precise': (self.v('loc_hole_clearance_precise') + self.v('press_fit_hole_tol') + pin_minus) / 2,
            'r_loc_standard': (0.10 + self.v('pth_hole_tol_plus') + pin_minus) / 2,
            'r_slot': (self.v('loc_slot_clearance') + self.v('pth_hole_tol_plus') + pin_minus) / 2,
            'el_cantilever': 227 - 218.5,
            'm25_pitch': 0.45,
        }

    def dv(self, name):
        return self.derived()[name]

    # ---------- XY ----------
    def scheme_available(self, unit, scheme):
        u = self.g['units'][unit]
        if scheme == 'posts':
            return u['posts'] >= 2 and unit != 'EL'
        if scheme == 'diag_precise':
            return unit in MULTILAYER
        return True

    def ratio(self, unit, scheme):
        u = self.g['units'][unit]
        if scheme == 'posts':
            return u['post_locator_r_max_mm'] / u['post_locator_span_mm']
        return u['diag_pins_r_max_mm'] / (self.v('diag_pin_span_factor') * u['diagonal_mm'])

    def locator_terms(self, unit, scheme):
        """Front board to its carrier board (K, or P for EL) at the farthest point from the primary feature."""
        hp = self.dv('hole_position_radial')
        axis = self.v('hole_position_tol_axis')
        r_loc = self.dv('r_loc_precise') if scheme == 'diag_precise' else self.dv('r_loc_standard')
        k = self.ratio(unit, scheme)
        return [
            ('primary hole position, front board', hp, 'DERIVED from SOURCED'),
            ('primary hole position, carrier board', hp, 'DERIVED from SOURCED'),
            ('primary pin-in-hole float', r_loc, 'DERIVED from SOURCED + ASSUMED'),
            ('rotation: secondary slot float x ratio', self.dv('r_slot') * k, 'DERIVED'),
            ('rotation: front hole pair spacing error x ratio', 2 * axis * k, 'DERIVED'),
            ('rotation: carrier hole pair spacing error x ratio', 2 * axis * k, 'DERIVED'),
        ]

    def connector_terms(self, unit):
        h = self.g['units'][unit]['mated_height_mm']
        return [
            ('SMT float, front half', self.v('smt_float_front'), 'ASSUMED'),
            ('SMT float, carrier half', self.v('smt_float_k'), 'ASSUMED'),
            ('stacker lean at the tip', h * math.tan(math.radians(self.v('pin_lean_deg'))), 'ASSUMED'),
        ]

    @staticmethod
    def combine(terms):
        vals = [x[1] for x in terms]
        return sum(vals), math.sqrt(sum(x * x for x in vals))

    def xy(self, unit, scheme):
        terms = self.connector_terms(unit) + self.locator_terms(unit, scheme)
        wc, rss = self.combine(terms)
        return {'terms': terms, 'wc': wc, 'rss': rss}

    def min_a(self, value):
        for a in self.p['a_mm']:
            if value <= a + 1e-12:
                return a
        return None

    # ---------- apertures ----------
    def aperture_clearance(self, ap):
        c_min = (ap['hole'] - ap['hole_minus'] - ap['part_max']) / 2 - ap['wobble']
        c_max = (ap['hole'] + ap['hole_plus'] - ap['part_min']) / 2
        return c_min, c_max

    def best_scheme(self, unit):
        return 'diag_precise' if unit in MULTILAYER else 'diag_standard'

    def hw_terms(self, ap):
        float_name = ap['hw_float_term']
        return [('hardware float on its board', self.v(float_name), 'ASSUMED'),
                ('hardware hole position on its board', self.dv('hole_position_radial'), 'DERIVED from SOURCED')]

    def panel_pos(self, ap):
        name = ap['panel_pos_term']
        return self.dv(name)

    def aperture_stack_first(self, cls):
        ap = self.d['apertures'][cls]
        rows = []
        for board in ap['board']:
            unit = 'O1' if board.startswith('O') else board
            if cls.startswith('el_passage'):
                carrier_unit = 'EL'
                terms = self.hw_terms(ap) + self.locator_terms(carrier_unit, 'diag_standard')
            elif cls == 'indicator' and board == 'EL':
                terms = self.hw_terms(ap) + self.locator_terms('EL', 'diag_standard') + self.locator_terms('P', 'diag_precise')
            else:
                terms = self.hw_terms(ap) + self.locator_terms(unit, self.best_scheme(unit))
            terms = terms + [('aperture position', self.panel_pos(ap), 'DERIVED from SOURCED')]
            wc, rss = self.combine(terms)
            rows.append((board, wc, rss, terms))
        worst = max(rows, key=lambda r: r[1])
        return worst

    def tightest_float(self, unit):
        best = None
        for cls, ap in self.d['apertures'].items():
            if ap.get('hole') is None or cls.startswith('el_passage'):
                continue
            boards = ['O1' if b.startswith('O') else b for b in ap['board']]
            if unit in boards:
                c_max = self.aperture_clearance(ap)[1]
                best = c_max if best is None else min(best, c_max)
        return best

    def panel_first_terms(self, unit):
        """Panel fitted first with hardware nuts tight; K mates last and is located on P by pins."""
        terms = self.connector_terms(unit)
        terms += [(t[0] + ' (K to P)', t[1], t[2]) for t in self.locator_terms('P', 'diag_precise')]
        if unit == 'P':
            return terms
        for b in ('P', unit):
            ap_float = self.tightest_float(b)
            terms += [
                (b + ' float in its tightest aperture', ap_float, 'DERIVED'),
                (b + ' hardware float on board', self.v('th_lead_float'), 'ASSUMED'),
                (b + ' hardware hole position', self.dv('hole_position_radial'), 'DERIVED from SOURCED'),
                (b + ' aperture position', self.dv('hole_position_radial'), 'DERIVED from SOURCED'),
            ]
        return terms

    def panel_first_floating_k_terms(self, unit):
        """Panel fitted first with nuts tight; K has no locating pins and floats onto the pairs (best fit near nominal)."""
        terms = self.connector_terms(unit)
        terms += [
            (unit + ' float in its tightest aperture', self.tightest_float(unit), 'DERIVED'),
            (unit + ' hardware float on board', self.v('th_lead_float'), 'ASSUMED'),
            (unit + ' hardware hole position', self.dv('hole_position_radial'), 'DERIVED from SOURCED'),
            (unit + ' aperture position', self.dv('hole_position_radial'), 'DERIVED from SOURCED'),
        ]
        return terms

    # ---------- Z ----------
    def bow(self, board_len, d):
        return 4 * self.v('bow_twist_ratio') * d * d / board_len

    def d_required(self, board_len):
        return math.sqrt(self.v('bow_allocation') * board_len / (4 * self.v('bow_twist_ratio')))

    def z_gap_terms(self, case, bow_mode):
        g = self.g
        alloc = self.v('bow_allocation')
        k_len = g['K']['longest_side_mm']

        def bow_term(name, length, d):
            if bow_mode == 'allocated':
                return (name + ' residual bow (allocation)', alloc, 'ASSUMED')
            return (name + ' bow, posts only', self.bow(length, d), 'DERIVED from SOURCED + ASSUMED model')

        base = [
            ('post length', self.v('post_length_tol'), 'ASSUMED'),
            ('post seat, front face', self.v('post_seat_tol'), 'ASSUMED'),
            ('post seat, carrier face', self.v('post_seat_tol'), 'ASSUMED'),
            ('connector standoff, front half', self.v('connector_standoff_tol'), 'ASSUMED'),
            ('connector standoff, carrier half', self.v('connector_standoff_tol'), 'ASSUMED'),
        ]
        if case in ('JL', 'JR', 'P'):
            u = g['units'][case]
            return base + [bow_term(case, u['longest_side_mm'], u['pair_to_nearest_post_max_mm']),
                           bow_term('K', k_len, u['pair_to_nearest_stack_post_on_K_max_mm'])]
        if case == 'EL':
            u = g['units']['EL']
            return base + [bow_term('EL', u['longest_side_mm'], u['pair_to_nearest_post_max_mm']),
                           ('P residual bow (allocation)', alloc, 'ASSUMED')]
        if case == 'O_on_K_standoffs':
            return base + [('O residual bow (allocation)', alloc, 'ASSUMED'), ('K residual bow (allocation)', alloc, 'ASSUMED')]
        if case == 'O_from_carrier':
            return [
                ('selector seat and carrier (O plane from panel)', self.v('selector_seat_tol'), 'ASSUMED'),
                ('O thickness', self.t['board_thickness_1p6']['tol'], 'SOURCED'),
                ('jack shoulder (K plane from panel)', self.t['jack_shoulder_to_board']['tol'], 'ASSUMED'),
                ('J thickness', self.t['board_thickness_1p6']['tol'], 'SOURCED'),
                ('J post length', self.v('post_length_tol'), 'ASSUMED'),
                ('J post seats (2)', 2 * self.v('post_seat_tol'), 'ASSUMED'),
                ('connector standoffs (2)', 2 * self.v('connector_standoff_tol'), 'ASSUMED'),
                ('K residual bow (allocation)', alloc, 'ASSUMED'),
            ]
        raise KeyError(case)

    def z_gap(self, case, bow_mode='allocated'):
        terms = self.z_gap_terms(case, bow_mode)
        wc, rss = self.combine(terms)
        return {'terms': terms, 'wc': wc, 'rss': rss}

    # ---------- K strain ----------
    def toggle_gap(self):
        """Nominal gap between the toggle body front and the panel rear face."""
        panel_rear = -self.v('panel_thickness')
        body_front = self.v('p_front_face_z') + self.v('toggle_body_height')
        return panel_rear - body_front

    def p_mismatch_terms(self):
        tb = self.t['board_thickness_1p6']['tol']
        return [
            ('jack shoulder (J plane)', self.t['jack_shoulder_to_board']['tol'], 'ASSUMED'),
            ('J thickness', tb, 'SOURCED'),
            ('J post length', self.v('post_length_tol'), 'ASSUMED'),
            ('J post seats (2)', 2 * self.v('post_seat_tol'), 'ASSUMED'),
            ('P post length', self.v('post_length_tol'), 'ASSUMED'),
            ('P post seats (2)', 2 * self.v('post_seat_tol'), 'ASSUMED'),
            ('P thickness', tb, 'SOURCED'),
            ('toggle body seat (P plane from panel)', self.t['toggle_body_height']['tol'], 'ASSUMED'),
        ]

    def seam_terms(self):
        tb = self.t['board_thickness_1p6']['tol']
        span = self.g['jl_jr_inner_post_span_mm']
        panel_bow = self.bow(318.0, span / 2)
        return [
            ('jack shoulder, JL', self.t['jack_shoulder_to_board']['tol'], 'ASSUMED'),
            ('jack shoulder, JR', self.t['jack_shoulder_to_board']['tol'], 'ASSUMED'),
            ('JL thickness', tb, 'SOURCED'),
            ('JR thickness', tb, 'SOURCED'),
            ('posts, JL and JR', 2 * self.v('post_length_tol'), 'ASSUMED'),
            ('post seats (4)', 4 * self.v('post_seat_tol'), 'ASSUMED'),
            ('panel local bow over half the span', panel_bow, 'DERIVED from SOURCED + ASSUMED model'),
        ]

    def strain(self, delta, span):
        return 3 * self.t['board_thickness_1p6']['value'] * delta / span ** 2

    def delta_allow(self, limit, span):
        return limit * span ** 2 / (3 * self.t['board_thickness_1p6']['value'])

    def strain_cases(self):
        spans = self.g['j_to_p_post_row_spacing_mm']
        seam_span = self.g['jl_jr_inner_post_span_mm']
        pm_wc, pm_rss = self.combine(self.p_mismatch_terms())
        sm_wc, sm_rss = self.combine(self.seam_terms())
        tg = self.toggle_gap()
        cases = []
        for s in spans:
            cases.append(('P pulled by toggle front nuts only (nominal gap closed)', s, tg + pm_wc, tg))
            cases.append(('P clamped to panel at a fixed stop and bolted to K', s, pm_wc, pm_rss))
            cases.append(('P free in Z, measured take-up at its panel fixings', s, self.v('shim_resolution'), self.v('shim_resolution')))
        cases.append(('JL and JR planes both from jack shoulders, K bolted to both', seam_span, sm_wc, sm_rss))
        return cases

    def bow_flatten_strain(self):
        kappa = 8 * self.v('bow_twist_ratio') / self.g['K']['longest_side_mm']
        return kappa * self.t['board_thickness_1p6']['value'] / 2

    # ---------- forces ----------
    def force_steps(self):
        u = self.g['units']
        return [
            ('Stack first, step 1: EL onto P (P unit)', u['EL']['positions'], u['EL']['posts']),
            ('Stack first, step 2: each adapter onto K', u['O1']['positions'], 0),
            ('Stack first, step 2: P unit onto K', u['P']['positions'], u['P']['posts']),
            ('Stack first, step 2: JL onto K', u['JL']['positions'], u['JL']['posts']),
            ('Stack first, step 2: JR onto K', u['JR']['positions'], u['JR']['posts']),
            ('Panel first: K onto all front boards at once', self.g['K']['positions'], 18),
            ('Rear service: K jacked off all front boards', self.g['K']['positions'], 18),
        ]

    # ---------- EL plate ----------
    def el_plate(self, f, thickness):
        e = self.v('fr4_modulus')
        b = self.v('el_site_pitch')
        span = self.v('el_post_pitch')
        c = self.dv('el_cantilever')
        force = self.v('el_positions_per_site') * f
        inertia = b * thickness ** 3 / 12
        mid_d = force * span ** 3 / (48 * e * inertia)
        mid_e = force * span * thickness / (8 * e * inertia)
        can_d = force * c ** 3 / (3 * e * inertia)
        can_e = force * c * thickness / (2 * e * inertia)
        return force, mid_d, mid_e, can_d, can_e


# ---------- rendering ----------
def mm(x):
    return f'{x:.3f}'


def ue(x):
    return f'{x * 1e6:.0f}'


def verdict_a(c, value):
    a = c.min_a(value)
    return f'closes for a >= {a}' if a is not None else 'fails at every a'


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(str(x) for x in r) + ' |' for r in rows]
    return '\n'.join(out)


def render_xy_summary(c):
    rows = []
    for unit in FRONT_UNITS:
        for scheme, label in SCHEMES.items():
            if not c.scheme_available(unit, scheme):
                continue
            r = c.xy(unit, scheme)
            rows.append([UNIT_LABEL[unit], label, mm(c.g['units'][unit]['mated_height_mm']), f'{c.ratio(unit, scheme):.2f}',
                         mm(r['wc']), verdict_a(c, r['wc']), mm(r['rss']), verdict_a(c, r['rss'])])
    return table(['Pair group', 'Locating scheme', 'H, mm', 'Ratio r/L', 'Worst case, mm', 'Worst case against a',
                  'RSS, mm', 'RSS against a'], rows)


def render_xy_terms(c):
    unit, scheme = 'P', 'diag_precise'
    r = c.xy(unit, scheme)
    rows = [[n, mm(v), s] for n, v, s in r['terms']]
    rows.append(['Sum (worst case)', mm(r['wc']), 'DERIVED'])
    rows.append(['Root sum of squares', mm(r['rss']), 'DERIVED'])
    return table(['Term at the farthest P-unit pair (recommended scheme)', 'mm, radial', 'Status'], rows)


def render_apertures(c):
    rows = []
    for cls, ap in c.d['apertures'].items():
        board, wc, rss, _ = c.aperture_stack_first(cls)
        if ap.get('hole') is None:
            rows.append([cls, board, 'window, no limit', mm(wc), mm(rss), 'no acceptance limit exists (#64)', 'n/a', 'n/a'])
            continue
        c_min, _ = c.aperture_clearance(ap)
        v_wc = 'closes' if wc <= c_min else f'fails by {mm(wc - c_min)}'
        v_rss = 'closes' if rss <= c_min else f'fails by {mm(rss - c_min)}'
        d_wc = ap['part_max'] + 2 * (wc + ap['wobble']) + ap['hole_minus']
        d_rss = ap['part_max'] + 2 * (rss + ap['wobble']) + ap['hole_minus']
        rows.append([cls, board, f"{ap['hole']} / {mm(c_min)}", mm(wc), mm(rss), f'WC {v_wc}; RSS {v_rss}',
                     f'{d_wc:.2f}', f'{d_rss:.2f}'])
    return table(['Class', 'Worst board', 'Hole / min radial clearance, mm', 'Stack-first error WC, mm',
                  'RSS, mm', 'Verdict', 'Hole for WC, mm', 'Hole for RSS, mm'], rows)


def render_panel_first(c):
    rows = []
    for unit in ['JL', 'JR', 'P', 'O1']:
        terms = c.panel_first_terms(unit)
        wc, rss = c.combine(terms)
        sf = c.xy(unit, c.best_scheme(unit))
        fw, fr = c.combine(c.panel_first_floating_k_terms(unit))
        rows.append([UNIT_LABEL[unit], mm(wc), verdict_a(c, wc), mm(rss), verdict_a(c, rss), mm(fw), mm(fr),
                     verdict_a(c, fr), mm(sf['rss'])])
    return table(['Pair group', 'K pinned to P: WC, mm', 'WC against a', 'RSS, mm', 'RSS against a',
                  'K floating: WC, mm', 'RSS, mm', 'RSS against a', 'Stack first RSS, mm'], rows)


def render_toggle(c):
    gap = c.toggle_gap()
    nut = c.v('toggle_nut_thickness')
    washer = c.v('toggle_washer_thickness')
    tol = c.t['toggle_body_height']['tol'] + c.t['jack_shoulder_to_board']['tol']
    rows = [
        ['Toggle body front z (P front face + body height)', mm(c.v('p_front_face_z') + c.v('toggle_body_height')), 'DERIVED from SOURCED + ASSUMED'],
        ['Panel rear face z', mm(-c.v('panel_thickness')), 'SOURCED'],
        ['Nominal gap body front to panel rear', mm(gap), 'DERIVED'],
        ['Rear jam nut thickness', mm(nut), 'SOURCED'],
        ['Rear nut plus washer', mm(nut + washer), 'SOURCED'],
        ['Nominal interference of a rear jam nut', mm(nut - gap), 'DERIVED'],
        ['Gap variation from body seat and J-chain, WC', mm(tol), 'ASSUMED'],
    ]
    return table(['Quantity', 'mm', 'Status'], rows)


def render_coupon(c):
    rows = [[b['id'], b['role'], f"{b['outline_mm'][0]} x {b['outline_mm'][1]}", b['thickness_mm'], b['contents']] for b in c.d['coupon']['boards']]
    t1 = table(['Board', 'Role', 'Outline, mm', 'Thickness, mm', 'Contents'], rows)
    rows = [[m['id'], m['what'], m['finishes']] for m in c.d['coupon']['measurements']]
    return t1 + '\n\n' + table(['Measurement', 'What it measures', 'Term it replaces'], rows)


def render_st01(c):
    return table(['Figure', 'Exact need from ST-01'], [[f['figure'], f['exact_need']] for f in c.d['st01_figures_needed']])


def render_z(c):
    rows = []
    cases = [('JL', 'JL to K, 12.9 mm'), ('JR', 'JR to K, 12.9 mm'), ('P', 'P to K, 11.1 mm'),
             ('EL', 'EL to P, 7.2 mm'), ('O_on_K_standoffs', 'O to K, 6.9 mm, adapters on K standoffs'),
             ('O_from_carrier', 'O to K, 6.9 mm, adapters held by the selector carrier')]
    for case, label in cases:
        for mode in (('allocated', 'posts only') if case in ('JL', 'JR', 'P') else ('allocated',)):
            r = c.z_gap(case, mode)
            wreq = [f"{2 * (t + r['wc']):.2f} / {2 * (t + r['rss']):.2f}" for t in c.p['t_mm']]
            bow_label = 'fasteners at d_req' if mode == 'allocated' else 'posts only'
            if case.startswith('O') or case == 'EL':
                bow_label = 'allocation'
            rows.append([label, bow_label, mm(r['wc']), mm(r['rss'])] + wreq)
    return table(['Pair', 'Bow basis', 'Gap error WC, mm', 'RSS, mm'] +
                 [f'Required usable wipe at t = {t}, WC / RSS, mm' for t in c.p['t_mm']], rows)


def render_bow(c):
    rows = []
    for unit in ['JL', 'JR', 'P', 'EL']:
        u = c.g['units'][unit]
        d = u['pair_to_nearest_post_max_mm']
        rows.append([unit, mm(u['longest_side_mm']), mm(d), mm(c.bow(u['longest_side_mm'], d)), mm(c.d_required(u['longest_side_mm']))])
    k = c.g['K']
    rows.append(['K', mm(k['longest_side_mm']), mm(k['pair_to_nearest_post_max_mm']),
                 mm(c.bow(k['longest_side_mm'], k['pair_to_nearest_post_max_mm'])), mm(c.d_required(k['longest_side_mm']))])
    return table(['Board', 'Longest side L, mm', 'Farthest pair from a post d, mm', 'Bow at d, mm',
                  'd_req for the bow allocation, mm'], rows)


def render_strain(c):
    lim_t = c.dv('strain_test_level')
    lim_d = c.dv('strain_design_limit')
    rows = []
    for name, span, d_wc, d_rss in c.strain_cases():
        e_wc, e_rss = c.strain(d_wc, span), c.strain(d_rss, span)
        verdict = 'within design limit' if e_wc <= lim_d else ('within test level only' if e_wc <= lim_t else 'exceeds test level')
        rows.append([name, mm(span), mm(d_wc), mm(d_rss), ue(e_wc), ue(e_rss), verdict])
    rows.append(['K pulled flat from 0.75% bow at fixings', 'n/a', 'n/a', 'n/a', ue(c.bow_flatten_strain()),
                 ue(c.bow_flatten_strain()), 'within design limit' if c.bow_flatten_strain() <= lim_d else 'exceeds'])
    return table(['Case', 'Span s, mm', 'Delta WC, mm', 'Delta RSS, mm', 'Strain WC, microstrain',
                  'Strain RSS, microstrain', 'Verdict (WC)'], rows)


def render_strain_allow(c):
    rows = []
    for s in c.g['j_to_p_post_row_spacing_mm'] + [c.g['jl_jr_inner_post_span_mm']]:
        rows.append([mm(s), mm(c.delta_allow(c.dv('strain_design_limit'), s)), mm(c.delta_allow(c.dv('strain_test_level'), s))])
    head = table(['Span s, mm', f"Allowed Delta at design limit {ue(c.dv('strain_design_limit'))} microstrain, mm",
                  f"Allowed Delta at test level {ue(c.dv('strain_test_level'))} microstrain, mm"], rows)
    return head


def render_forces(c):
    rows = []
    cap = c.v('screw_axial_capacity')
    ratio = c.v('unmate_to_mate_ratio')
    for name, n, posts in c.force_steps():
        k = ratio if 'jacked' in name else 1.0
        forces = [n * f * k for f in c.p['f_N']]
        per = [f'{x / posts:.0f}' if posts else 'n/a' for x in forces]
        rows.append([name, n] + [f'{x:.0f}' for x in forces] + [' / '.join(per),
                     'yes' if posts and max(forces) / posts <= cap else ('n/a' if not posts else 'no')])
    return table(['Step', 'Positions'] + [f'Force at f = {f} N, N' for f in c.p['f_N']] +
                 ['Per post or jacking point at each f, N', 'Within planning screw capacity'], rows)


def render_el(c):
    rows = []
    lim = c.dv('strain_design_limit')
    for thick in (c.t['el_thickness']['value'], c.t['el_thickness']['value'] - c.t['el_thickness']['tol']):
        for f in c.p['f_N']:
            force, md, me, cd, ce = c.el_plate(f, thick)
            rows.append([mm(thick), f, f'{force:.1f}', mm(md), ue(me), mm(cd), ue(ce),
                         'exceeds design limit' if max(me, ce) > lim else 'within design limit'])
    return table(['EL thickness, mm', 'f, N', 'Force per site, N', 'Mid-span deflection, mm', 'Mid-span strain, microstrain',
                  'Outer-site deflection, mm', 'Outer-site strain, microstrain', 'Unbacked EL'], rows)


def render_terms(c):
    rows = []
    for name, t in c.t.items():
        val = t['value']
        if isinstance(val, float):
            val = f'{val:g}'
        tol = ''
        if 'tol' in t:
            tol = f"+/-{t['tol']}"
        elif 'plus' in t:
            tol = f"+{t['plus']}/-{t['minus']}"
        basis = t.get('source', '') or ''
        if t['status'] == 'DERIVED':
            basis = t['formula']
        elif t['status'] == 'ASSUMED':
            basis = 'to source: ' + t['to_source']
        else:
            basis = basis + ': ' + t.get('locator', '')
        rows.append([f'`{name}`', val, tol, t['unit'], t['status'], basis.replace('|', '/')])
    return table(['Term', 'Value', 'Tolerance', 'Unit', 'Status', 'Source, formula or what would source it'], rows)


def render_supports(c):
    rows = [[s['items'], s['count'], s['disposition'], s['reason']] for s in c.d['supports_disposition']]
    total = sum(s['count'] for s in c.d['supports_disposition'] if s['counts_toward_87'])
    rows.append(['Total of the 87 partition supports', total, '', ''])
    return table(['Items', 'Count', 'Disposition', 'Reason'], rows)


RENDERERS = {
    'xy_summary': render_xy_summary,
    'xy_terms': render_xy_terms,
    'apertures': render_apertures,
    'panel_first': render_panel_first,
    'z_gap': render_z,
    'bow': render_bow,
    'strain': render_strain,
    'strain_allow': render_strain_allow,
    'forces': render_forces,
    'el_plate': render_el,
    'supports': render_supports,
    'terms': render_terms,
    'toggle': render_toggle,
    'coupon': render_coupon,
    'st01': render_st01,
}


def render_all(data=None):
    c = Calc(data or load())
    return {name: fn(c) for name, fn in RENDERERS.items()}


BLOCK = re.compile(r'(<!-- calc:(\w+) -->\n)(.*?)(\n<!-- /calc:\2 -->)', re.S)


def fill_readme(text, blocks):
    def sub(m):
        return m.group(1) + blocks[m.group(2)] + m.group(4)
    return BLOCK.sub(sub, text)


def main(argv):
    data = load()
    if '--refresh-geometry' in argv:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from stack_mechanics_geometry import derive
        geo = derive()
        geo['el_passage_diameters_mm'] = [list(x) for x in geo['el_passage_diameters_mm']]
        data['geometry'] = geo
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
