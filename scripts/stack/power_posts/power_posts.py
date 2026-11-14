"""ST-04 power-post calculator: every README figure from design/stack/power-posts/joint-design.json.

  python3 scripts/stack/power_posts/power_posts.py                 print the results
  python3 scripts/stack/power_posts/power_posts.py --write-readme  refresh the calc: tables

Paper screen only. Nothing here is a measured resistance, a current rating or a fit.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / 'design/stack/power-posts/joint-design.json'
ENVELOPES = ROOT / 'design/stack/power-posts/envelopes.json'
README = ROOT / 'design/stack/power-posts/README.md'
RAILS = ('+12V', '-12V', '+5V')
BRANCHES = ('JL', 'JR', 'P')


def load(path=DESIGN):
    return json.loads(Path(path).read_text())


def v(d, key):
    return d['terms'][key]['value']


# ---------------------------------------------------------------- present figures

def present_drop_mV(d):
    """partition35.py: rwire = hot ohm/m x length + termination; drop = I x (rwire + rail plane) + 4.6 A x (rwire + return plane)."""
    rwire = v(d, 'wire_hot_ohm_per_m') * v(d, 'wire_length_mm') / 1000 + v(d, 'wire_termination_ohm')
    return {r: (a * (rwire + v(d, 'rail_plane_ohm')) + v(d, 'single_return_A') * (rwire + v(d, 'return_plane_ohm'))) * 1000
            for r, a in v(d, 'rail_max_A').items()}, rwire


def share_A(i_total, neck, r_min, n, r_other, n_main, r_main):
    """partition35.py GH bound: the candidate path has its minimum resistance and no PCB term; every alternative
    has its maximum resistance and the whole common neck; the main returns are parallel before the neck."""
    alt = neck + 1 / ((n - 1) / r_other + n_main / r_main)
    return i_total * alt / (r_min + alt), alt


def present_shares(d):
    out = {}
    for b, t in v(d, 'present_gh_bounds').items():
        out[b] = share_A(v(d, 'single_return_A'), v(d, 'return_plane_ohm'), t['minimum_single_path_ohm'],
                         t['return_contact_count'], t['maximum_other_path_ohm'], t['dedicated_ground_wire_count'],
                         t['dedicated_ground_wire_max_ohm'])[0]
    return out


def present_budget_V(d):
    c = v(d, 'conductor_path_ohm')
    return {r: a * c + v(d, 'single_return_A') * c + v(d, 'protection_drop_V') + v(d, 'distribution_limit_V')
            for r, a in v(d, 'rail_max_A').items()}


# ---------------------------------------------------------------- joint terms

def rho_cu_hot(d):
    return v(d, 'cu_rho_20C_ohm_mm') * (1 + v(d, 'cu_alpha_per_C') * (v(d, 'hot_C') - 20))


def barrel_ohm(d, drill):
    t = v(d, 'barrel_cu_mm')
    area = math.pi / 4 * (drill ** 2 - (drill - 2 * t) ** 2)
    return rho_cu_hot(d) * v(d, 'board_mm') / area


def land_transfer_ohm(d, side):
    lp = d['land_pattern'][side]
    ring = lp['via_ring']
    g = ring['count'] / barrel_ohm(d, ring['drill_mm'])
    if lp['hole_plated']:
        g += 1 / barrel_ohm(d, lp['hole_finished_mm'])
    return 1 / g


def post_section_mm2(d):
    s = v(d, 'post_af_min_mm')
    return math.sqrt(3) / 2 * s * s - math.pi / 4 * v(d, 'post_thread_major_mm') ** 2


def body_ohm(d, length):
    return v(d, 'brass_rho_hot_ohm_mm') * length / post_section_mm2(d)


def joint_terms(d, length):
    return {'K face': v(d, 'face_ohm'), 'front face': v(d, 'face_ohm'), 'post body': body_ohm(d, length),
            'K land and vias': land_transfer_ohm(d, 'K'), 'front land and vias': land_transfer_ohm(d, 'front')}


def joint_ohm(d, length):
    return sum(joint_terms(d, length).values())


def branch_gap(b):
    return 17.0 if b == 'P' else 18.8


# ---------------------------------------------------------------- stack screens

def stack_drop_mV(d, rj):
    return {r: (a * (rj + v(d, 'rail_plane_ohm')) + v(d, 'single_return_A') * (rj + v(d, 'return_plane_ohm'))) * 1000
            for r, a in v(d, 'rail_max_A').items()}


def joint_requirement_ohm(d):
    """Largest joint resistance that keeps each rail's distribution drop at the 20 mV limit."""
    lim, i_r = v(d, 'distribution_limit_V'), v(d, 'single_return_A')
    return {r: (lim - a * v(d, 'rail_plane_ohm') - i_r * v(d, 'return_plane_ohm')) / (a + i_r)
            for r, a in v(d, 'rail_max_A').items()}


def contact_paths(d, branch):
    pin = v(d, 'tw_pin_rho_ohm_mm') * v(d, 'tw_pin_length_mm')[branch] / v(d, 'tw_pin_section_mm2')
    r_min = v(d, 'llcr_min_ohm')
    r_max = v(d, 'llcr_initial_max_ohm') + v(d, 'llcr_change_max_ohm') + pin
    return r_min, r_max, pin


def stack_shares(d):
    out = {}
    for b in BRANCHES:
        r_min, r_max, _ = contact_paths(d, b)
        n = v(d, 'header_agnd_positions')[b]
        out[b] = share_A(v(d, 'single_return_A'), v(d, 'return_plane_ohm'), r_min, n, r_max, 3, joint_ohm(d, branch_gap(b)))
    return out


def fault_shares(d):
    """SI-2 inputs: worst single header contact with 3, 2, 1 or 0 AGND posts of the branch in place."""
    out = {}
    for b in BRANCHES:
        r_min, r_max, _ = contact_paths(d, b)
        n = v(d, 'header_agnd_positions')[b]
        rj = joint_ohm(d, branch_gap(b))
        row = {}
        for posts in (3, 2, 1, 0):
            alt = v(d, 'return_plane_ohm') + 1 / ((n - 1) / r_max + posts / rj)
            row[posts] = v(d, 'single_return_A') * alt / (r_min + alt)
        out[b] = row
    return out


def el_drop_mV(d):
    """EL fed from P: P-branch distribution drop (whole-domain bound) plus EL's own contact term (partition EL formula
    with the header pair in place of the harness path)."""
    _, r_max, _ = contact_paths(d, 'EL')
    n_rail, n_ret = v(d, 'el_rail_positions_per_rail'), v(d, 'el_agnd_positions')
    ret = v(d, 'el_return_mA') / 1000
    own = {r: ((i / 1000) * (r_max / n_rail + v(d, 'rail_plane_ohm')) + ret * (r_max / n_ret + v(d, 'return_plane_ohm'))) * 1000
           for r, i in v(d, 'el_current_mA').items()}
    p = stack_drop_mV(d, joint_ohm(d, 17.0))
    return own, {r: own[r] + p[r] for r in RAILS}


def stack_budget_V(d, drop_mV):
    c = v(d, 'conductor_path_ohm')
    return {r: a * c + v(d, 'single_return_A') * c + v(d, 'protection_drop_V') + drop_mV[r] / 1000
            for r, a in v(d, 'rail_max_A').items()}


def e23(d, length):
    rj = joint_ohm(d, length)
    energy = v(d, 'e23_i2t_A2s') * rj
    body_e = v(d, 'e23_i2t_A2s') * body_ohm(d, length)
    heat_cap = post_section_mm2(d) * length * v(d, 'brass_density_g_mm3') * v(d, 'brass_c_J_gK')
    return {'joint_energy_uJ': energy * 1e6, 'body_energy_uJ': body_e * 1e6, 'body_rise_K': body_e / heat_cap}


def single_post_4p6(d, length):
    rj = joint_ohm(d, length)
    i = v(d, 'single_return_A')
    return {'drop_mV': i * rj * 1000, 'loss_mW': i * i * rj * 1000}


def results(d):
    drop0, rwire = present_drop_mV(d)
    rj = {b: joint_ohm(d, branch_gap(b)) for b in BRANCHES}
    worst_b = max(BRANCHES, key=lambda b: rj[b])
    drops = {b: stack_drop_mV(d, rj[b]) for b in BRANCHES}
    worst_drop = {r: max(drops[b][r] for b in BRANCHES) for r in RAILS}
    el_own, el_total = el_drop_mV(d)
    return {'present_drop_mV': drop0, 'present_wire_ohm': rwire, 'present_shares_A': present_shares(d),
            'present_budget_V': present_budget_V(d), 'joint_ohm': rj, 'worst_joint_branch': worst_b,
            'joint_terms': {b: joint_terms(d, branch_gap(b)) for b in BRANCHES},
            'requirement_ohm': joint_requirement_ohm(d), 'drop_mV': drops, 'worst_drop_mV': worst_drop,
            'shares': {b: s[0] for b, s in stack_shares(d).items()}, 'alt_ohm': {b: s[1] for b, s in stack_shares(d).items()},
            'el_own_mV': el_own, 'el_total_mV': el_total, 'budget_V': stack_budget_V(d, worst_drop),
            'e23': {b: e23(d, branch_gap(b)) for b in ('JL', 'P')}, 'single_post': {b: single_post_4p6(d, branch_gap(b)) for b in ('JL', 'P')}}


# ---------------------------------------------------------------- README tables

def f(x, n=3):
    return f'{x:.{n}f}'


def tables(d, env=None):
    r = results(d)
    t = {}
    rows = ['| Rail | Rail current, A | Partition figure, mV | Recomputed, mV |', '| --- | --- | --- | --- |']
    for k in RAILS:
        rows.append(f'| {k} | {v(d, "rail_max_A")[k]} | {v(d, "present_drop_mV")[k]} | {f(r["present_drop_mV"][k])} |')
    rows.append(f'| Wire term (hot wire plus terminations) | | 1.63 mΩ | {f(r["present_wire_ohm"] * 1000)} mΩ |')
    for b in BRANCHES:
        rows.append(f'| GH worst single contact, {b} | | {f(v(d, "present_gh_bounds")[b]["worst_single_contact_A"])} A | {f(r["present_shares_A"][b])} A |')
    for k in RAILS:
        rows.append(f'| Rail-plus-return budget, {k} | | {v(d, "present_budget_V")[k]} V | {f(r["present_budget_V"][k])} V |')
    t['reproduce'] = rows
    rows = ['| Term | JL, JR (18.8 mm), mΩ | P (17.0 mm), mΩ | Status |', '| --- | --- | --- | --- |']
    st = {'K face': 'ASSUMED (`face_ohm`)', 'front face': 'ASSUMED (`face_ohm`)', 'post body': 'DERIVED from ASSUMED brass resistivity',
          'K land and vias': 'DERIVED (copper SOURCED)', 'front land and vias': 'DERIVED (copper SOURCED)'}
    for k in r['joint_terms']['JL']:
        rows.append(f'| {k} | {f(r["joint_terms"]["JL"][k] * 1000, 4)} | {f(r["joint_terms"]["P"][k] * 1000, 4)} | {st[k]} |')
    rows.append(f'| **Joint** | **{f(r["joint_ohm"]["JL"] * 1000)}** | **{f(r["joint_ohm"]["P"] * 1000)}** | DERIVED |')
    rows.append(f'| Planning requirement from the 20 mV limit (+12 V governs) | {f(min(r["requirement_ohm"].values()) * 1000)} | same | DERIVED |')
    rows.append('| Plan-page planning figure | 0.500 | 0.500 | plan page, not derived |')
    t['joint'] = rows
    rows = ['| Rail | JL / JR, mV | P, mV | Limit, mV | Margin at the worst branch, mV | Requirement on the joint, mΩ |', '| --- | --- | --- | --- | --- | --- |']
    for k in RAILS:
        rows.append(f'| {k} | {f(r["drop_mV"]["JL"][k])} | {f(r["drop_mV"]["P"][k])} | 20 | {f(20 - r["worst_drop_mV"][k])} | {f(r["requirement_ohm"][k] * 1000)} |')
    t['drop'] = rows
    rows = ['| Branch | AGND header positions | Minimum contact path, mΩ | Maximum other path, mΩ | All alternatives, mΩ | Worst single contact, A | Against 0.5 A (GH) | Against 1.6 A (MMS CCC) |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for b in BRANCHES:
        rmin, rmax, _ = contact_paths(d, b)
        s = r['shares'][b]
        rows.append(f'| {b} | {v(d, "header_agnd_positions")[b]} | {f(rmin * 1000, 2)} | {f(rmax * 1000, 2)} | {f(r["alt_ohm"][b] * 1000)} | {f(s)} | '
                    f'{"exceeds" if s > v(d, "gh_contact_limit_A") else "meets"} | {"meets" if s <= v(d, "header_contact_limit_A") else "exceeds"} |')
    t['share'] = rows
    rows = ['| Rail | EL own contact term, mV | Plus the P-branch drop, mV | Limit, mV |', '| --- | --- | --- | --- |']
    for k in RAILS:
        rows.append(f'| {k} | {f(r["el_own_mV"][k])} | {f(r["el_total_mV"][k])} | 20 |')
    t['el'] = rows
    rows = ['| Rail | Rail conductor, V | Return conductor at 4.6 A, V | Protection, V | Distribution (worst branch), V | Total, V | Limit, V |', '| --- | --- | --- | --- | --- | --- | --- |']
    for k in RAILS:
        c = v(d, 'conductor_path_ohm')
        rows.append(f'| {k} | {f(v(d, "rail_max_A")[k] * c)} | {f(v(d, "single_return_A") * c)} | {v(d, "protection_drop_V")} | {f(r["worst_drop_mV"][k] / 1000, 4)} | {f(r["budget_V"][k], 4)} | 0.20 |')
    t['budget'] = rows
    rows = ['| Joint | 4.6 A drop, mV | 4.6 A loss, mW | E23 energy in the joint, µJ | in the post body, µJ | Adiabatic body rise, K |', '| --- | --- | --- | --- | --- | --- |']
    for b, lab in (('JL', 'JL / JR 18.8 mm'), ('P', 'P 17.0 mm')):
        s, e = r['single_post'][b], r['e23'][b]
        rows.append(f'| {lab} | {f(s["drop_mV"])} | {f(s["loss_mW"], 2)} | {f(e["joint_energy_uJ"], 1)} | {f(e["body_energy_uJ"], 1)} | {e["body_rise_K"]:.1e} |')
    t['single'] = rows
    rows = ['| Branch | 3 AGND posts, A | 2 posts (one loose or missing), A | 1 post, A | 0 posts (all open), A | Header limit, A |', '| --- | --- | --- | --- | --- | --- |']
    for b, row in fault_shares(d).items():
        rows.append(f'| {b} | {f(row[3])} | {f(row[2])} | {f(row[1])} | {f(row[0])} | {v(d, "header_contact_limit_A")} |')
    t['faults'] = rows
    if env is not None:
        rows = ['| Board | Face | Footprints in the keep-out | References | No free position within 12 mm |', '| --- | --- | --- | --- | --- |']
        for b in ('K', 'JL', 'JR', 'P'):
            e = env['boards'][b]
            for face, lab in (('F', 'F.Cu'), ('B', 'B.Cu')):
                refs = e['refs_by_face'][face]
                stuck = sorted({m['ref'] for m in e['hits'] if face in m['faces'] and m['nearest_free_shift_mm'] is None})
                rows.append(f'| {b} | {lab} | {len(refs)} | {", ".join(refs) if refs else "none"} | {", ".join(stuck) if stuck else "none"} |')
        t['moves'] = rows
    return t


def write_readme(d, env, path=README):
    text = Path(path).read_text()
    for key, rows in tables(d, env).items():
        block = '\n'.join(rows)
        text, n = re.subn(rf'(<!-- calc:{key} -->\n)(?:.*?\n)?(<!-- /calc:{key} -->)', lambda m: m.group(1) + block + '\n' + m.group(2), text, flags=re.S)
        if n != 1:
            raise SystemExit('README marker missing: ' + key)
    Path(path).write_text(text)


def main(argv):
    d = load()
    env = json.loads(ENVELOPES.read_text()) if ENVELOPES.exists() else None
    if '--write-readme' in argv:
        write_readme(d, env)
    for key, rows in tables(d, env).items():
        print('##', key)
        print('\n'.join(rows))


if __name__ == '__main__':
    main(sys.argv[1:])
