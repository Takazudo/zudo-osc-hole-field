"""Check design/stack/geometry/stack-candidate.json against the sources.

    python3 scripts/stack/geometry/check.py [--no-measurements]

Writes design/stack/geometry/check-report.json. Exit 0 when the candidate is a
consistent derivation of the sources with every courtyard-level conflict
declared, 1 otherwise. All results are courtyard-and-pad-level planning
screens; none is a copper clearance, a tolerance result or a physical fit.
"""
import copy
import json
import sys

import generate
import stackgeom as sg

TOL = 1e-3
RAILS = ('+12V', '-12V', '+5V')
FRONT_LAYER = ('JL', 'JR', 'O1', 'O3', 'O5')


class Context:
    """Source-derived objects shared by the checks (built once per canonical input)."""

    def __init__(self, ci):
        self.ci = ci
        p = ci['parameters']
        self.params = p
        self.land = ci['land_pattern']
        self.boards = {b['board_key']: b for b in ci['partition']['boards']}
        self.fps = {k: {f['ref']: f for f in v} for k, v in ci['boards'].items()}
        self.retired_k = sg.retired_k_headers(ci)
        self.obstacles = sg.stack_obstacles(ci)
        self.reference = generate.build(ci, self.obstacles)
        self.cache = {}
        self.heights = {}
        for env in ci['mechanical']['model_envelopes']:
            if env['side'] != 'F.Cu':
                continue
            zmin, zmax = env['z']
            self.heights.setdefault(env['footprint'], (round(zmax - 0.8, 3), round(max(0.0, -0.8 - zmin), 3)))


class Result:
    def __init__(self):
        self.errors = []
        self.checks = {}

    def check(self, name, ok_detail, errors):
        self.errors += ['%s: %s' % (name, e) for e in errors]
        self.checks[name] = {'status': 'FAIL' if errors else 'PASS', 'errors': errors, 'detail': ok_detail}


# ---------------------------------------------------------------- individual checks

def check_planes(cand, ctx, res):
    ref = ctx.reference['stack']
    st = cand['stack']
    errs = []
    for key in ('K_face_z_mm', 'K_rear_z_mm', 'K_rear_parts_z_mm', 'selector_tail_z_mm', 'enclosure_inner_rear_z_mm'):
        if abs(st[key] - ref[key]) > TOL:
            errs.append('stale %s %s, sources give %s' % (key, st[key], ref[key]))
    for gap, value in ref['mated_heights_mm'].items():
        if abs(st['mated_heights_mm'].get(gap, 1e9) - value) > TOL:
            errs.append('stale mated height %s %s, sources give %s' % (gap, st['mated_heights_mm'].get(gap), value))
        if value <= 0:
            errs.append('non-positive mated height %s %s' % (gap, value))
    if st['selector_tail_z_mm'] - st['K_face_z_mm'] <= 0:
        errs.append('selector tail at z=%s reaches K F.Cu at z=%s' % (st['selector_tail_z_mm'], st['K_face_z_mm']))
    for key in ('enclosure_depth_cases', 'stacker_height_by_gap'):
        if json.dumps(st.get(key), sort_keys=True) != json.dumps(ref[key], sort_keys=True):
            errs.append('stale %s; sources give %s' % (key, ref[key]))
    for p in cand['pairs']:
        gap = '/'.join(p['boards']) if p['family'] != 'EL/P' else 'EL/P'
        if gap in st['mated_heights_mm'] and abs(p['mated_height_mm'] - st['mated_heights_mm'][gap]) > TOL:
            errs.append('pair %s mated height %s differs from gap %s %s' % (p['id'], p['mated_height_mm'], gap, st['mated_heights_mm'][gap]))
    res.check('planes_and_gaps', {'stack': ref}, errs)


def check_rear_envelope(cand, ctx, res):
    """K's rear parts against the decided enclosure depth; the other depth cases are reported rows."""
    st = cand['stack']
    errs = []
    rows = []
    for c in st['enclosure_depth_cases']:
        clear = round(st['K_rear_parts_z_mm'] - c['inner_rear_z_mm'], 4)
        rows.append({'inside_depth_mm': c['inside_depth_mm'], 'inner_rear_z_mm': c['inner_rear_z_mm'],
                     'K_rear_parts_z_mm': st['K_rear_parts_z_mm'], 'clearance_mm': clear,
                     'role': 'decided depth (checked)' if c['decided'] else 'reported row (not a check)'})
        if c['decided'] and clear < 0:
            errs.append('K rear parts at z=%s pass the enclosure inner rear at z=%s by %s mm'
                        % (st['K_rear_parts_z_mm'], c['inner_rear_z_mm'], -clear))
    res.check('rear_envelope', {'cases': rows, 'K_rear_z_mm': st['K_rear_z_mm'],
                                'core_rear_ceiling_mm': ctx.ci['mechanical']['core_rear_ceiling_mm']}, errs)


def check_stacker_heights(cand, ctx, res):
    """DA-01 D3 rule per gap to K: A + socket + body clearance <= gap, with A on the 0.005 in step."""
    errs = []
    rule = ctx.params['stacker_rule']
    for g, row in cand['stack']['stacker_height_by_gap'].items():
        gap = cand['stack']['mated_heights_mm'][g]
        a = row['stacker_A_mm']
        steps = a / rule['height_step_mm']
        if abs(steps - round(steps)) > 1e-6:
            errs.append('gap %s stacker A %s mm is not a multiple of %s mm' % (g, a, rule['height_step_mm']))
        if a + rule['socket_seated_height_mm'] + rule['body_clearance_mm'] > gap + TOL:
            errs.append('gap %s (%s mm): stacker A %s + socket %s + clearance %s mm exceeds it' % (
                g, gap, a, rule['socket_seated_height_mm'], rule['body_clearance_mm']))
        if a <= 0:
            errs.append('gap %s (%s mm) leaves no stacker height' % (g, gap))
    el = ctx.params['el_pair_heights_mm']
    gap_el = cand['stack']['mated_heights_mm']['EL/P']
    bodies = round(el['stacker_body'] + el['socket'], 3)
    if bodies >= gap_el:
        errs.append('EL/P bodies %s + %s mm reach the %s mm gap' % (el['stacker_body'], el['socket'], gap_el))
    el_t = ctx.boards['EL']['thickness_mm']
    proud = round(el['pin_tip'] - gap_el - el_t, 3)
    if proud > el['el_front_height']:
        errs.append('EL/P stacker tips stand %s mm proud of EL F.Cu, above the %s mm front height' % (proud, el['el_front_height']))
    res.check('stacker_heights', {'by_gap': cand['stack']['stacker_height_by_gap'],
                                  'EL/P': {'gap_mm': gap_el, 'bodies_mm': bodies, 'body_gap_mm': round(gap_el - bodies, 3),
                                           'tip_proud_of_EL_front_mm': proud, 'EL_front_height_mm': el['el_front_height']}}, errs)


def check_coaxial(cand, ctx, res):
    errs = []
    n = 0
    for p in cand['pairs']:
        f, b = p['sites']['front'], p['sites']['back']
        if abs(f['center'][0] - b['center'][0]) > TOL or abs(f['center'][1] - b['center'][1]) > TOL:
            errs.append('pair %s is not coaxial: %s on %s, %s on %s' % (p['id'], f['center'], f['board'], b['center'], b['board']))
        for s in (f, b):
            if s['replaces']:
                fp = ctx.fps[s['board']].get(s['replaces'])
                if fp is None:
                    errs.append('pair %s replaces %s, absent from board %s' % (p['id'], s['replaces'], s['board']))
                    continue
                c = sg.centre(fp['courtyard'])
                if abs(c[0] - s['center'][0]) > TOL or abs(c[1] - s['center'][1]) > TOL:
                    errs.append('pair %s site %s is not at the replaced %s courtyard centre %s' % (p['id'], s['center'], s['replaces'], c))
                want = 'F' if s['side'] == 'F.Cu' else 'B'
                if fp['side'] != want:
                    errs.append('pair %s site side %s differs from %s on %s' % (p['id'], s['side'], s['replaces'], fp['side']))
        n += 1
    res.check('coaxial_sites', {'pairs': n}, errs)


def check_containment(cand, ctx, res):
    errs = []
    counted = 0
    drop_in = set(ctx.params['drop_in_families'])
    for p in cand['pairs']:
        for name, half in (('front', 'front'), ('back', 'K')):
            s = p['sites'][name]
            w, l = sg.envelope(ctx.land, p['positions'], half, p.get('rows', 1))
            rect = sg.env_rect(s['center'][0], s['center'][1], w, l, s['long_axis_x'])
            if any(abs(a - b) > TOL for a, b in zip(rect, s['envelope'])):
                errs.append('pair %s %s envelope %s is stale; land pattern gives %s' % (p['id'], name, s['envelope'], rect))
            if s['replaces'] and p['family'] in drop_in:
                gh = ctx.fps[s['board']][s['replaces']]['courtyard']
                counted += 1
                if not sg.inside(rect, gh):
                    errs.append('pair %s %s envelope %s lies outside the GH courtyard %s of %s on %s'
                                % (p['id'], name, rect, gh, s['replaces'], s['board']))
    res.check('replacement_inside_gh_courtyard', {'replaced_halves_checked': counted,
                                                  'families': sorted(drop_in)}, errs)


def check_blockers(cand, ctx, res):
    errs = []
    declared = []
    clear = set(ctx.params['must_be_clear_families'])
    margin = ctx.params['board_edge_margin_mm']
    for p in cand['pairs']:
        for name in ('front', 'back'):
            s = p['sites'][name]
            skip = {s['replaces']} if s['replaces'] else set()
            if p['family'] in clear:
                for ref, kind, depth in ctx.obstacles[s['board']].hits_depth(s['side'][0], s['envelope'], skip):
                    errs.append('pair %s %s %s envelope %s on %s %s overlaps %s (%s) by %s mm (must be clear)'
                                % (p['id'], name, sg.envelope_info(ctx.land, p['positions'], 'front' if name == 'front' else 'K',
                                                                   p.get('rows', 1))['key'],
                                   s['envelope'], s['board'], s['side'], ref, kind, depth))
                if s['board'] != 'P' and not sg.rect_inside_poly(s['envelope'], ctx.boards[s['board']]['outline'], margin):
                    errs.append('pair %s %s envelope %s is not inside the %s outline with %s mm margin'
                                % (p['id'], name, s['envelope'], s['board'], margin))
            got = [list(x) for x in ctx.obstacles[s['board']].hits(s['side'][0], s['envelope'], skip)]
            decl = [list(x) for x in s.get('blockers', [])]
            for x in got:
                if x not in decl:
                    errs.append('pair %s %s site on %s %s has undeclared blocker %s (%s)' % (p['id'], name, s['board'], s['side'], x[0], x[1]))
            for x in decl:
                if x not in got:
                    errs.append('pair %s %s declares blocker %s that the sources do not give' % (p['id'], name, x[0]))
            if decl:
                declared.append({'pair': p['id'], 'half': name, 'board': s['board'], 'blockers': sorted({x[0] for x in decl})})
    res.check('courtyard_blockers_declared', {'declared_conflicts': declared}, errs)


def neighbours(i, n, rows):
    """Adjacent indices: single row along the row; two rows (index i = column i // rows, row i % rows)
    in the same column or the same row of the next column."""
    if rows == 1:
        return [j for j in (i - 1, i + 1) if 0 <= j < n]
    col, row = divmod(i, rows)
    cand = [(col, r) for r in range(rows) if r != row] + [(col - 1, row), (col + 1, row)]
    return [c * rows + r for c, r in cand if 0 <= c < n // rows]


def adjacency_violations(pins, rows=1):
    out = []
    for i, n in enumerate(pins):
        if n in ('AGND', 'NC') or n in RAILS:
            continue
        nb = [pins[j] for j in neighbours(i, len(pins), rows)]
        if 'AGND' not in nb:
            out.append(n)
    return out


def check_pins(cand, ctx, res):
    errs = []
    p_cfg = ctx.params
    harness = {h['id']: h for h in ctx.ci['partition']['harnesses']}
    con = {c['id']: c for c in ctx.ci['partition']['connectors']}
    by_source = {}
    totals = {'pairs': 0, 'positions': 0, 'signal_positions': 0, 'used_signal': 0, 'unused': 0, 'AGND': 0, 'rail': 0,
              'K_pairs': 0, 'K_positions': 0, 'K_AGND': 0}
    for p in cand['pairs']:
        pins = p['pin_map']
        fam_key = 'K/O' if p['family'].startswith('K/O') else p['family']
        if p['positions'] != p_cfg['positions'][fam_key]:
            errs.append('pair %s has %s positions; parameters give %s for %s' % (p['id'], p['positions'], p_cfg['positions'][fam_key], fam_key))
        if len(pins) != p['positions']:
            errs.append('pair %s has %d pin entries for %d positions' % (p['id'], len(pins), p['positions']))
        template = p_cfg['pin_templates'][p['family']]
        for c, n in zip(template, pins):
            if c == 'G' and n != 'AGND':
                errs.append('pair %s puts %s on an AGND position of template %s' % (p['id'], n, template))
        if p['family'] in p_cfg['pin_templates']['signal_beside_return_required']:
            for n in adjacency_violations(pins, p.get('rows', 1)):
                errs.append('pair %s: signal %s has no adjacent AGND (signal beside a return required)' % (p['id'], n))
        if p['source_harness']:
            by_source.setdefault(p['source_harness'], []).append(p)
        totals['pairs'] += 1
        totals['positions'] += len(pins)
        sig = sum(1 for n in pins if n not in RAILS and n != 'AGND')
        totals['signal_positions'] += sig
        totals['unused'] += sum(1 for n in pins if n == 'NC')
        totals['used_signal'] += sum(1 for n in pins if n not in RAILS + ('AGND', 'NC'))
        totals['AGND'] += pins.count('AGND')
        totals['rail'] += sum(1 for n in pins if n in RAILS)
        if 'K' in p['boards']:
            totals['K_pairs'] += 1
            totals['K_positions'] += len(pins)
            totals['K_AGND'] += pins.count('AGND')
    for hid, h in harness.items():
        if any(b in p_cfg['retired_boards'] for b in h['boards']):
            if hid in by_source:
                errs.append('retired harness %s is still carried by %s' % (hid, [p['id'] for p in by_source[hid]]))
            continue
        joints = by_source.get(hid, [])
        if not joints:
            errs.append('harness %s is not replaced by any pair' % hid)
            continue
        for j in joints:
            carried = set(j['pin_map'])
            for net in h['signals']:
                if net not in carried:
                    errs.append('pair %s does not carry %s of %s' % (j['id'], net, hid))
    for p in cand['pairs']:
        if p['family'] == 'EL/P':
            for r in ctx.params['el_rails']:
                if r not in p['pin_map']:
                    errs.append('EL/P pair %s does not carry rail %s to EL' % (p['id'], r))
    crossing = sum(len(harness[h]['signals']) for h, js in by_source.items() if len(js) == 2)
    totals['nets_counted_at_two_joints'] = crossing
    lone = {p['id']: adjacency_violations(p['pin_map'], p.get('rows', 1)) for p in cand['pairs']
            if adjacency_violations(p['pin_map'], p.get('rows', 1))}
    res.check('pin_budget', {'totals': totals, 'signals_without_adjacent_AGND_where_not_required': lone}, errs)


def check_pass_through(cand, ctx, res):
    errs = []
    jl = [p for p in cand['pairs'] if p['family'] == 'JL/P pass-through']
    el = [p for p in cand['pairs'] if p['family'] == 'P/K for EL']
    n_jlp = sum(1 for h in ctx.ci['partition']['harnesses'] if h['boards'] == ['JL', 'P'])
    n_el = sum(1 for h in ctx.ci['partition']['harnesses'] if h['boards'] == ['EL', 'K'])
    if len(jl) != 2 * n_jlp:
        errs.append('expected %d JL-to-P pass-through pairs, found %d' % (2 * n_jlp, len(jl)))
    if len(el) != n_el:
        errs.append('expected %d P-to-K pass-through pairs for EL, found %d' % (n_el, len(el)))
    sites = []
    for p in jl + el:
        new = [s for s in (p['sites']['front'], p['sites']['back']) if not s['replaces']]
        for s in new:
            sites.append({'pair': p['id'], 'board': s['board'], 'side': s['side'], 'center': s['center'],
                          'clear_in_place': not s['blockers'], 'blockers': sorted({b[0] for b in s['blockers']})})
    res.check('pass_through_sites', {'new_sites': sites,
                                     'K_new_sites_clear': sum(1 for s in sites if s['board'] == 'K' and s['clear_in_place']),
                                     'K_new_sites': sum(1 for s in sites if s['board'] == 'K')}, errs)


def rect_in_tab_or_outline(rect, tab, outline, step=0.25):
    """Every sample point of the rectangle lies in the tab or inside P's existing outline."""
    nx = max(2, int((rect[2] - rect[0]) / step) + 1)
    ny = max(2, int((rect[3] - rect[1]) / step) + 1)
    for i in range(nx + 1):
        x = rect[0] + (rect[2] - rect[0]) * i / nx
        for j in range(ny + 1):
            y = rect[1] + (rect[3] - rect[1]) * j / ny
            in_tab = tab[0] - TOL <= x <= tab[2] + TOL and tab[1] - TOL <= y <= tab[3] + TOL
            if not in_tab and not sg.point_in_poly(x, y, outline):
                return False
    return True


def toggle_tail_screen(s, cand, ctx, errs):
    """Toggle through-hole tails below P B.Cu against K F.Cu parts in the P/K gap."""
    lib = s['toggle_lib']
    tail = ctx.heights.get(lib, (None, 0.0))[1]
    gap = cand['stack']['mated_heights_mm']['P/K']
    under = sorted({ref for pad in s['toggle_pads'] for ref, _ in ctx.obstacles['K'].hits('F', pad)})
    if not tail:
        return {'status': 'NOT CHECKABLE', 'K_F_parts_under_toggle_pads': under,
                'missing_source': 'toggle tail protrusion below P B.Cu: the retained native envelope of %s starts at the board face' % lib}
    k_fps = ctx.fps['K']
    unknown = []
    for ref in under:
        h = ctx.heights.get(k_fps[ref]['lib'], (None,))[0] if ref in k_fps else None
        if h is None:
            unknown.append(ref)
        elif tail + h >= gap:
            errs.append('SUB toggle %s tail %s mm and K part %s %s mm reach the %s mm P/K gap' % (s['block'], tail, ref, h, gap))
    return {'status': 'NOT CHECKABLE' if unknown else 'PASS', 'tail_mm': tail, 'K_F_parts_under_toggle_pads': under,
            'K_parts_without_retained_height': unknown}


def check_sub(cand, ctx, res):
    errs = []
    tails = {}
    ref = {s['block']: s for s in ctx.reference['sub_toggles']}
    tabs = {t['id']: t for t in cand['tabs']}
    pairs = {p['id']: p for p in cand['pairs']}
    m = ctx.params['tab_edge_margin_mm']
    for s in cand['sub_toggles']:
        r = ref.get(s['block'])
        if r is None:
            errs.append('SUB toggle at %s has no source selector' % s['block'])
            continue
        if s['toggle_centre'] != r['toggle_centre']:
            errs.append('SUB toggle %s centre %s differs from the placement lock %s' % (s['block'], s['toggle_centre'], r['toggle_centre']))
        y = s['site_centre'][1]
        lo, hi = r['window_centre_y']
        if not (lo - TOL <= y <= hi + TOL) or abs(s['site_centre'][0] - r['site_centre'][0]) > TOL:
            errs.append('SUB pair at %s centre %s is outside the placement window y=%s..%s' % (s['block'], s['site_centre'], lo, hi))
        if r['corridor_mm'] - (s['toggle_courtyard'][2] - s['toggle_courtyard'][0]) <= 0 or min(r['toggle_margins_mm']) <= 0:
            errs.append('SUB toggle %s courtyard crosses a selector courtyard' % s['block'])
        tab = tabs.get('TAB-CONTROL-' + s['block'])
        pair = pairs.get('P-K-SUB-' + s['block'])
        if tab is None or pair is None:
            errs.append('SUB toggle %s lacks its control tab or pair' % s['block'])
            continue
        t = tab['rect']
        tc = s['toggle_courtyard']
        if not rect_in_tab_or_outline(tc, t, ctx.boards['P']['outline']):
            errs.append('SUB toggle %s courtyard %s is not inside control tab %s or P outline' % (s['block'], tc, t))
        for ref, kind in ctx.obstacles['P'].hits('F', tc):
            errs.append('SUB toggle %s courtyard %s overlaps P F.Cu obstacle %s (%s)' % (s['block'], tc, ref, kind))
        pad_g = ctx.params['obstacle_model']['opposite_face_through_hole_pad_growth_mm']
        for pad in s['toggle_pads']:
            for ref, kind in ctx.obstacles['P'].hits('B', sg.grow(pad, pad_g)):
                errs.append('SUB toggle %s pad %s overlaps P B.Cu obstacle %s (%s)' % (s['block'], pad, ref, kind))
        tails[s['block']] = toggle_tail_screen(s, cand, ctx, errs)
        env = pair['sites']['front']['envelope']
        if not sg.inside(sg.grow(env, m)[:3] + [min(env[3] + m, t[3])], t):
            errs.append('SUB pair %s envelope %s is not inside control tab %s with %s mm margin' % (s['block'], env, t, m))
        if abs(pair['sites']['front']['center'][1] - y) > TOL:
            errs.append('SUB pair %s site differs from the recorded SUB site' % s['block'])
    res.check('sub_toggle_windows', {'windows': {s['block']: {'window_centre_y': s['window_centre_y'], 'window_mm': s['window_mm'],
                                                              'site_centre': s['site_centre']} for s in cand['sub_toggles']},
                                   'toggle_tail_against_K': tails}, errs)


def check_posts(cand, ctx, res):
    errs = []
    tabs = {t['id']: t for t in cand['tabs']}
    ref = {p['id']: p for p in ctx.reference['posts']}
    d = ctx.params['post_resites']['front_land_diameter_mm']
    coax = 0
    for p in cand['posts']:
        land = p['proposed_front_land']
        k_land = p['proposed_K_land']
        if abs(land[0] - k_land[0]) > TOL or abs(land[1] - k_land[1]) > TOL:
            errs.append('post %s is not coaxial: front land %s, K land %s' % (p['id'], land, k_land))
            continue
        r = ref.get(p['id'])
        if r is None or r['proposed_K_land'] != k_land or r['proposed_front_land'] != land:
            errs.append('post %s lands %s differ from the sources and re-sites' % (p['id'], land))
        if p['present_offset_mm'] <= sg.OFFSET_TOL_MM and 'resite' not in p:
            coax += 1
            continue
        court = [land[0] - d / 2, land[1] - d / 2, land[0] + d / 2, land[1] + d / 2]
        if p['resolved_by']:
            t = tabs.get(p['resolved_by'])
            if t is None:
                errs.append('post %s moves its %s land to %s with no tab to carry it' % (p['id'], p['front_board'], land))
            elif not on_tab_or_body(court, t['rect'], ctx.boards['P']['outline']):
                errs.append('post %s moved land %s (Ø%s mm) is outside %s %s' % (p['id'], land, d, t['id'], t['rect']))
        elif not sg.rect_inside_poly(court, ctx.boards[p['front_board']]['outline']):
            errs.append('post %s re-sited land %s (Ø%s mm) is not inside the %s outline' % (p['id'], land, d, p['front_board']))
    if len(cand['posts']) != len(ctx.ci['partition']['load_side_wires']):
        errs.append('expected %d posts, found %d' % (len(ctx.ci['partition']['load_side_wires']), len(cand['posts'])))
    res.check('post_coaxiality', {'posts': len(cand['posts']), 'coaxial_today_unmoved': coax,
                                  'carried_by_a_tab': {p['id']: p['resolved_by'] for p in cand['posts'] if p['resolved_by']},
                                  're_sited': {p['id']: p['proposed_front_land'] for p in cand['posts'] if 'resite' in p}}, errs)


def on_tab_or_body(rect, tab, outline):
    """The rectangle lies inside the tab, or inside the tab x-span and continues onto P's body."""
    if sg.inside(rect, tab):
        return True
    if not sg.inside([rect[0], rect[1], rect[2], tab[3]], tab):
        return False
    below = [rect[0], tab[3], rect[2], rect[3]]
    return all(sg.point_in_poly(x, y, outline) for x in (below[0] + 0.01, below[2] - 0.01) for y in (below[1] + 0.01, below[3] - 0.01))


def check_tabs(cand, ctx, res):
    errs = []
    p_board = ctx.boards['P']
    pz = (cand['planes']['P']['rear_z_mm'], cand['planes']['P']['face_z_mm'])
    detail = {}
    carrier = ctx.ci['partition']['jack_seam_carrier']
    carriers = [('seam rear cradle', carrier['rear_rect_mm'], carrier['rear_z_mm']),
                ('seam front lip', carrier['front_lip_rect_mm'], carrier['front_lip_z_mm'])]
    carriers += [('seam cross-member %d' % i, c['rect_mm'], c['z_mm']) for i, c in enumerate(carrier['cross_members'], 1)]
    removed = set(ctx.params['removed_carriers'])
    carriers = [c for c in carriers if c[0] not in removed]
    pairs = {p['id']: p for p in cand['pairs']}
    m = ctx.params['tab_edge_margin_mm']
    for t in cand['tabs']:
        r = t['rect']
        d = {'rect': r, 'min_distance_mm': {}}
        if sg.rect_poly_overlap([r[0], r[1], r[2], r[3] - 0.01], p_board['outline']):
            errs.append('tab %s %s overlaps P itself; a tab must add outline' % (t['id'], r))
        if not sg.point_in_poly((r[0] + r[2]) / 2, r[3] + 0.05, p_board['outline']):
            errs.append('tab %s %s is not attached to the P edge' % (t['id'], r))
        for key in FRONT_LAYER:
            ol = ctx.boards[key]['outline']
            if sg.rect_poly_overlap(r, ol):
                errs.append('tab %s %s overlaps board outline %s' % (t['id'], r, key))
            xs = [q[0] for q in ol]
            ys = [q[1] for q in ol]
            bb = [min(xs), min(ys), max(xs), max(ys)]
            d['min_distance_mm'][key] = round(rect_distance(r, bb), 4)
        for name, cr, cz in carriers:
            if cz[0] < pz[1] and pz[0] < cz[1] and sg.inter(r, cr):
                errs.append('tab %s %s overlaps the %s carrier envelope %s z=%s' % (t['id'], r, name, cr, cz))
            if cz[0] < pz[1] and pz[0] < cz[1]:
                d['min_distance_mm'][name] = round(rect_distance(r, cr), 4)
        for s in ctx.ci['partition']['supports']:
            if s['board'] == 'K':
                continue
            c = sg.circle_rect(s['position_mm'][0], s['position_mm'][1], s['collar_diameter_mm'])
            if sg.inter(r, c) and s['id'] not in t.get('pass_through_supports', []):
                errs.append('tab %s %s overlaps support %s collar at %s' % (t['id'], r, s['id'], s['position_mm']))
        for sel in cand['selectors_kept']:
            if sg.inter(r, sel['courtyard']):
                errs.append('tab %s %s overlaps selector %s courtyard %s' % (t['id'], r, sel['ref'], sel['courtyard']))
            d['min_distance_mm'][sel['ref']] = round(rect_distance(r, sel['courtyard']), 4)
        for post in cand['posts']:
            x, y = post['proposed_front_land']
            if r[0] < x < r[2] and r[1] < y < r[3] and post['id'] not in t.get('carried_posts', []):
                errs.append('tab %s %s holds post land %s that it does not carry' % (t['id'], r, post['id']))
        if t['id'] == 'TAB-EL':
            for p in cand['pairs']:
                if p['family'] in ('EL/P', 'P/K for EL'):
                    for name in ('front', 'back'):
                        s = p['sites'][name]
                        if s['board'] == 'P' and not sg.inside(sg.grow(s['envelope'], m)[:3] + [min(s['envelope'][3] + m, r[3])], r):
                            errs.append('pair %s envelope %s is not inside tab %s %s' % (p['id'], s['envelope'], t['id'], r))
        detail[t['id']] = d
    res.check('p_tabs', {'tabs': detail, 'removed_carriers': sorted(removed), 'NOT_RUN': 'P body-carrier envelope: no carrier geometry is recorded in the sources (text only in partition load paths)'}, errs)


def rect_distance(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    if dx == 0 and dy == 0:
        return -min(a[2] - b[0], b[2] - a[0], a[3] - b[1], b[3] - a[1])
    return (dx * dx + dy * dy) ** 0.5


def check_retired(cand, ctx, res):
    errs = []
    retired = set(ctx.params['retired_boards'])
    for p in cand['pairs']:
        for b in p['boards']:
            if b in retired:
                errs.append('pair %s uses retired board %s' % (p['id'], b))
        for s in p['sites'].values():
            if s['replaces'] in ctx.retired_k:
                errs.append('pair %s reuses retired K header %s' % (p['id'], s['replaces']))
    for b in retired:
        if b in cand['planes']:
            errs.append('retired board %s still has a plane' % b)
    n_ap = len(ctx.ci['partition']['K_service_apertures'])
    n_fp = sum(1 for f in ctx.ci['boards']['K'] if f['ref'].startswith('MH_K-SERVICE'))
    if cand['retired']['K_service_apertures'] != n_ap or len(cand['retired']['K_service_aperture_footprints']) != n_fp:
        errs.append('retired K service aperture count %s/%s differs from sources %s/%s'
                    % (cand['retired']['K_service_apertures'], len(cand['retired']['K_service_aperture_footprints']), n_ap, n_fp))
    if sorted(cand['retired']['K_headers']) != sorted(ctx.retired_k):
        errs.append('retired K headers %s differ from the sources %s' % (cand['retired']['K_headers'], sorted(ctx.retired_k)))
    res.check('retired_items', {'boards': sorted(retired), 'K_headers': sorted(ctx.retired_k), 'K_service_apertures': n_ap}, errs)


def facing_items(ctx, cand, key, face, region_poly, exclude):
    """Items of board `key` that face the gap from `face` ('F' or 'B'), with known heights or None."""
    out = []
    for f in ctx.ci['boards'][key]:
        if f['ref'] in exclude or f['lib'] == '' or not f['courtyard']:
            continue
        c = sg.centre(f['courtyard'])
        if region_poly is not None and not sg.point_in_poly(c[0], c[1], region_poly):
            continue
        h = ctx.heights.get(f['lib'])
        tht = any(p['type'] == 'thru_hole' for p in f['pads'])
        if f['side'] == face:
            out.append((f['ref'], f['lib'], f['courtyard'], h[0] if h else None, 'body'))
        elif tht:
            if f['lib'] == 'SRBV160803':
                b = ctx.boards[key]
                tail = (b['face_z_mm'] - cand['stack']['selector_tail_z_mm']) - b['thickness_mm']
                out.append((f['ref'], f['lib'], f['courtyard'], round(tail, 3), 'selector tail'))
            else:
                out.append((f['ref'], f['lib'], f['courtyard'], h[1] if h and h[1] > 0 else None, 'through-hole tail'))
    for res_ in ctx.boards[key].get('board_bulk_reserve', []):
        if res_['side'][0] == face:
            out.append(('%s bulk reserve %s' % (key, res_['net']), 'reserve', res_['rect'], res_['maximum_height_mm'], 'reserve'))
    return out


def tallest(items, n=3):
    return [{'ref': it[0], 'class': it[1], 'height_mm': it[3], 'kind': it[4]} for it in sorted(items, key=lambda it: (-it[3], it[0]))[:n]]


def tallest_class(items):
    """The part class (footprint library, reserve or selector tail) with the tallest retained height on one face."""
    known = [it for it in items if it[3] is not None]
    if not known:
        return None
    it = sorted(known, key=lambda it: (-it[3], it[1], it[0]))[0]
    return {'class': it[1], 'height_mm': it[3], 'kind': it[4],
            'members_on_face': sum(1 for x in known if x[1] == it[1])}


def check_facing_heights(cand, ctx, res):
    errs = []
    detail = {}
    replaced = {s['replaces'] for p in cand['pairs'] for s in p['sites'].values() if s['replaces']}
    posts = {p['front_ref'] for p in cand['posts']} | {p['K_ref'] for p in cand['posts']}
    exclude = replaced | posts | ctx.retired_k
    gaps = cand['stack']['mated_heights_mm']
    for front in ('JL', 'JR', 'P', 'O1', 'O3', 'O5', 'EL'):
        back = 'P' if front == 'EL' else 'K'
        gap = gaps['EL/P' if front == 'EL' else front + '/K']
        fo = ctx.boards[front]['outline']
        bo = ctx.boards[back]['outline']
        a_items = facing_items(ctx, cand, front, 'B', bo, exclude)
        b_items = facing_items(ctx, cand, back, 'F', fo, exclude)
        known = unknown = 0
        collisions = []
        single = []
        idx = sg.RectIndex()
        for it in b_items:
            idx.add(it[2], it)
        for it in a_items + b_items:
            if it[3] is not None and it[3] >= gap:
                single.append({'ref': it[0], 'height_mm': it[3], 'gap_mm': gap})
        for a in a_items:
            for _, b in idx.near(a[2]):
                if not sg.inter(a[2], b[2]):
                    continue
                if a[3] is None or b[3] is None:
                    unknown += 1
                else:
                    known += 1
                    if a[3] + b[3] >= gap:
                        collisions.append({'front': a[0], 'front_height_mm': a[3], 'back': b[0],
                                           'back_height_mm': b[3], 'gap_mm': gap})
        for c in collisions:
            errs.append('facing-height collision in gap %s/%s (%s mm): %s %s mm + %s %s mm'
                        % (front, back, gap, c['front'], c['front_height_mm'], c['back'], c['back_height_mm']))
        for s in single:
            errs.append('facing-height collision in gap %s/%s: %s is %s mm tall against a %s mm gap' % (front, back, s['ref'], s['height_mm'], gap))
        a_known = [it for it in a_items if it[3] is not None]
        b_known = [it for it in b_items if it[3] is not None]
        detail[front + '/' + back] = {
            'gap_mm': gap, 'overlapping_pairs_with_known_heights': known,
            'overlapping_pairs_with_an_unretained_height': unknown,
            'front_items': len(a_items), 'front_items_with_height': len(a_known),
            'back_items': len(b_items), 'back_items_with_height': len(b_known),
            'tallest_front_mm': max([it[3] for it in a_known] or [0]),
            'tallest_back_mm': max([it[3] for it in b_known] or [0]),
            'tallest_front_parts': tallest(a_known), 'tallest_back_parts': tallest(b_known),
            'tallest_class_front_face': tallest_class(a_items), 'tallest_class_back_face': tallest_class(b_items),
            'front_items_without_height': len(a_items) - len(a_known), 'back_items_without_height': len(b_items) - len(b_known),
            'stacker': cand['stack']['stacker_height_by_gap'].get(front + '/' + back),
            'collisions': collisions}
    res.check('facing_heights', {'gaps': detail,
                                 'facing_pairs_without_a_retained_height': sum(d['overlapping_pairs_with_an_unretained_height'] for d in detail.values()), 'height_source': 'design/mechanical/ic-envelope-native-report.json native display-model z bounds (not seated heights), selector-assembly.json tails, partition bulk reserves; every other part height is unretained and counted as unknown'}, errs)


def nearest_clearance(obs, side, cx, cy, r, skip, reach=6.0):
    """Distance from a circle of radius r to the nearest grown obstacle on one face (negative = overlap)."""
    best = None
    for rect, payload in obs.index[side].near(sg.circle_rect(cx, cy, 2 * (r + reach))):
        if payload[0] in skip:
            continue
        d = -sg.circle_rect_depth(cx, cy, r, rect)
        if best is None or d < best[0]:
            best = (round(d, 4), payload[0])
    return best


def check_el_relief_holes(cand, ctx, res):
    """Eight relief holes per EL site against EL parts, holes, reserves and outline on both faces."""
    errs = []
    obs = ctx.obstacles['EL']
    margin = ctx.params['board_edge_margin_mm']
    outline = ctx.boards['EL']['outline']
    ref = {p['id']: p.get('relief_holes') for p in ctx.reference['pairs'] if p['family'] == 'EL/P'}
    rows = []
    for p in cand['pairs']:
        if p['family'] != 'EL/P':
            continue
        holes = p.get('relief_holes') or []
        if holes != ref.get(p['id']):
            errs.append('pair %s relief holes differ from the sources' % p['id'])
        if len(holes) != p['positions']:
            errs.append('pair %s has %d relief holes for %d positions' % (p['id'], len(holes), p['positions']))
        skip = {p['sites']['front']['replaces']}
        site_hits = []
        for h in holes:
            cx, cy = h['center']
            r = h['diameter_mm'] / 2
            for side in 'FB':
                for oref, kind, depth in obs.circle_hits(side, cx, cy, r, skip):
                    site_hits.append([h['pin'], side, oref, depth])
                    errs.append('pair %s relief hole pin %d at %s (d %s mm) overlaps EL %s.Cu %s (%s) by %s mm'
                                % (p['id'], h['pin'], h['center'], h['diameter_mm'], side, oref, kind, depth))
            edge = sg.distance_to_outline(cx, cy, outline)
            if not sg.point_in_poly(cx, cy, outline) or edge < r + margin:
                errs.append('pair %s relief hole pin %d at %s is %s mm from the EL edge (needs %s)'
                            % (p['id'], h['pin'], h['center'], round(edge, 4), r + margin))
        rows.append({'pair': p['id'], 'holes': len(holes), 'conflicts': site_hits,
                     'clear_holes': len(holes) - len({c[0] for c in site_hits})})
    res.check('el_relief_holes', {'sites': rows, 'diameter_status': ctx.params['el_relief_holes']['status'],
                                  'EL_windows': 'NOT CHECKABLE: no window geometry is recorded for EL in the sources'}, errs)


def check_el_pot_passages(cand, ctx, res):
    """The 18 EL pot passages at the decided diameter against EL parts, holes, reserves and outline."""
    errs = []
    obs = ctx.obstacles['EL']
    margin = ctx.params['board_edge_margin_mm']
    outline = ctx.boards['EL']['outline']
    if cand['el_pot_passages'] != ctx.reference['el_pot_passages']:
        errs.append('EL pot passages differ from the sources')
    rows = []
    for ps in cand['el_pot_passages']:
        cx, cy = ps['center']
        r = ps['diameter_mm'] / 2
        if ps['el_footprint'] is None:
            errs.append('pot passage %s at %s has no EL passage footprint' % (ps['uid'], ps['center']))
        skip = {ps['el_footprint']}
        hits = []
        for side in 'FB':
            for oref, kind, depth in obs.circle_hits(side, cx, cy, r, skip):
                hits.append([side, oref, depth])
                errs.append('pot passage %s at %s (d %s mm) overlaps EL %s.Cu %s (%s) by %s mm'
                            % (ps['uid'], ps['center'], ps['diameter_mm'], side, oref, kind, depth))
        edge = sg.distance_to_outline(cx, cy, outline)
        if edge < r + margin:
            errs.append('pot passage %s at %s is %s mm from the EL edge (needs %s)' % (ps['uid'], ps['center'], round(edge, 4), r + margin))
        near = [nearest_clearance(obs, side, cx, cy, r, skip) for side in 'FB']
        near = min((n for n in near if n), default=None)
        rows.append({'uid': ps['uid'], 'center': ps['center'], 'diameter_mm': ps['diameter_mm'], 'conflicts': hits,
                     'nearest_grown_obstacle': {'clearance_mm': near[0], 'ref': near[1]} if near else None})
    res.check('el_pot_passages', {'passages': rows,
                                  'EL_windows': 'NOT CHECKABLE: no window geometry is recorded for EL in the sources',
                                  'EL_copper': 'NOT RUN: tracks and zones are outside the courtyard model'}, errs)


def nearest_fixing(xy, fixings):
    best = None
    if not fixings:
        return None
    for f in fixings:
        d = ((xy[0] - f['xy'][0]) ** 2 + (xy[1] - f['xy'][1]) ** 2) ** 0.5
        if best is None or d < best[0]:
            best = (round(d, 3), f['id'])
    return best


def reach_misses(cand, fixings, reach):
    """Per-side misses under reviews/da-02.md E2: K side, any fixing; front side, a fixing of the pair's own side."""
    out = []
    for p in cand['pairs']:
        if 'K' not in p['boards']:
            continue
        front = p['boards'][0]
        xy = p['sites']['back']['center']
        k = nearest_fixing(xy, fixings)
        if front in ('JL', 'JR'):
            own = [f for f in fixings if f['front_board'] in ('JL', 'JR')]
        elif front == 'P':
            own = [f for f in fixings if f['front_board'] == 'P']
        else:
            own = None
        fr = nearest_fixing(xy, own) if own is not None else None
        sides = []
        if k is None or k[0] > reach:
            sides.append('K')
        if own is not None and (fr is None or fr[0] > reach):
            sides.append('front')
        if sides:
            dists = [k[0] if k else 1e9] + ([fr[0] if fr else 1e9] if own is not None else [])
            out.append({'pair': p['id'], 'front_board': front, 'xy': xy, 'sides': sides,
                        'K_side_nearest': list(k) if k else None, 'front_side_nearest': list(fr) if fr else None,
                        'worst_mm': max(dists)})
    return sorted(out, key=lambda m: (-m['worst_mm'], m['pair']))


def check_fixing_reach(cand, ctx, res):
    """reviews/da-02.md E2: every pair to K within 40 mm of a declared fixing on the K side and on its own front side.
    Only declared fixings count (finding G4); the PROVISIONAL tie sites are a reported second run."""
    errs = []
    fx = ctx.params['fixings']
    reach, ex = fx['reach_mm'], fx['exception_reach_mm']
    if cand['fixings'] != ctx.reference['fixings']:
        errs.append('fixing list differs from the sources')
    declared = [f for f in cand['fixings'] if f['declared']]
    runs = {}
    for name, fl in (('declared', declared), ('declared_and_provisional_tie_sites', cand['fixings'])):
        misses = reach_misses(cand, fl, reach)
        by = {}
        for m in misses:
            by[m['front_board']] = by.get(m['front_board'], 0) + 1
        runs[name] = {'fixings': len(fl), 'misses': len(misses), 'by_front_board': dict(sorted(by.items())),
                      'K_side_misses': sum(1 for m in misses if 'K' in m['sides']),
                      'front_side_misses': sum(1 for m in misses if 'front' in m['sides']),
                      'between_reach_and_exception': [m['pair'] for m in misses if m['worst_mm'] <= ex],
                      'beyond_exception': sum(1 for m in misses if m['worst_mm'] > ex),
                      'missed_pairs': misses}
    posts = {p['id']: p for p in cand['posts']}
    before = [dict(f, xy=posts[f['id']]['K_land']) if f['kind'] == 'post' else f for f in cand['fixings']]
    runs['at_partition_post_positions'] = {
        'declared': len(reach_misses(cand, [f for f in before if f['declared']], reach)),
        'declared_and_provisional_tie_sites': len(reach_misses(cand, before, reach)),
        'note': 'the same rule with the 18 posts at their partition K lands (before the ST-04 re-sites); DA-02 E2 gives 107 and 67'}
    for m in runs['declared']['missed_pairs']:
        errs.append('pair %s at %s misses the %s mm reach on the %s side (K side %s, front side %s)'
                    % (m['pair'], m['xy'], reach, ' and '.join(m['sides']), m['K_side_nearest'], m['front_side_nearest']))
    collars = [{'id': s['id'], 'xy': s['position_mm']} for s in ctx.ci['partition']['supports'] if s['board'] == 'EL']
    el = []
    for p in cand['pairs']:
        if p['family'] == 'EL/P':
            d, fid = nearest_fixing(p['sites']['front']['center'], collars)
            el.append({'pair': p['id'], 'nearest_EL_collar_post': fid, 'distance_mm': d})
    res.check('fixing_reach', {'reach_mm': reach, 'exception_reach_mm': ex, 'rule': fx['front_board_rule'],
                               'K_pairs': sum(1 for p in cand['pairs'] if 'K' in p['boards']), 'runs': runs,
                               'tie_site_status': fx['provisional_tie_status'],
                               'EL_P_pairs_to_EL_collar_posts': el}, errs)


def post_land_screen(cand, ctx, res):
    """ST-04's keep-out screen at the candidate post lands: K footprints (courtyard on its face, through-hole parts on
    both) inside r 4.05 mm, front-board footprints inside r 3.75 mm. Reported for ST-08; not a pass criterion."""
    rr = ctx.params['post_resites']['screen_keepout_radius_mm']
    key = ('post_screen', json.dumps([cand['posts'], rr], sort_keys=True))
    if key not in ctx.cache:
        ctx.cache[key] = _post_screen_rows(cand, ctx, rr)
    rows = copy.deepcopy(ctx.cache[key])
    total = {k: sorted({x for r in rows for x in r[k]}) for k in ('K F.Cu', 'K B.Cu')}
    res.check('post_land_keepout_screen', {'radius_mm': rr, 'posts': rows,
                                           'K_footprints_in_keepouts': {k: len(v) for k, v in total.items()},
                                           're_sited_K_hits': {r['post']: r['K F.Cu'] + r['K B.Cu'] for r in rows if r['re_sited']},
                                           'role': 'reported for ST-08 and Gate A-paper; not a pass criterion'}, [])


def _post_screen_rows(cand, ctx, rr):
    rows = []
    for p in cand['posts']:
        row = {'post': p['id'], 'land': p['proposed_K_land'], 're_sited': 'resite' in p}
        for key, xy, r in (('K', p['proposed_K_land'], rr['K']), (p['front_board'], p['proposed_front_land'], rr['front'])):
            for face in 'FB':
                hit = set()
                for f in ctx.ci['boards'][key]:
                    if f['lib'] == '' or not f['courtyard'] or f['ref'] in (p['K_ref'], p['front_ref']):
                        continue
                    tht = any(q['type'] == 'thru_hole' for q in f['pads'])
                    if f['side'] != face and not tht:
                        continue
                    if sg.circle_rect_depth(xy[0], xy[1], r, f['courtyard']) > 1e-9:
                        hit.add(f['ref'])
                row['%s %s.Cu' % ('K' if key == 'K' else 'front', face)] = sorted(hit)
        rows.append(row)
    return rows


CHECKS = [check_planes, check_rear_envelope, check_stacker_heights, check_coaxial, check_containment, check_blockers, check_pins, check_pass_through,
          check_sub, check_posts, check_tabs, check_retired, check_facing_heights, check_el_relief_holes,
          check_el_pot_passages, check_fixing_reach, post_land_screen]


def run_checks(doc, ctx):
    res = Result()
    cand = doc['candidate']
    for fn in CHECKS:
        try:
            fn(cand, ctx, res)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            res.check(fn.__name__.replace('check_', ''), {}, ['malformed candidate: %r' % (exc,)])
    if doc.get('canonical_input_digest') != sg.canonical_digest(ctx.ci):
        res.check('staleness', {}, ['candidate digest %s differs from the sources %s; regenerate with: %s'
                                    % (str(doc.get('canonical_input_digest'))[:16], sg.canonical_digest(ctx.ci)[:16], sg.REGEN_COMMAND)])
    elif json.dumps(cand, sort_keys=True) != json.dumps(ctx.reference, sort_keys=True):
        res.check('staleness', {}, ['candidate content differs from a fresh generation; regenerate with: ' + sg.REGEN_COMMAND])
    else:
        res.check('staleness', {'digest': doc['canonical_input_digest']}, [])
    return res


NOT_RUN = [
    'Copper clearance, DRC and routing of the stack: no stack board exists',
    'Tolerance stack-up, mating misalignment and force: no exact connector (ST-01, ST-03)',
    'P body-carrier openings for the EL pairs: no carrier envelope is recorded in the sources',
    'Seated part heights: only native display-model envelopes and the listed reserves are retained; other heights are counted as unknown',
    'SUB toggle tails against K F.Cu: no retained tail protrusion for the toggle (see sub_toggle_windows detail)',
    'Native KiCad oracle query: not needed; boards parsed with plain Python and the extract matched the planning extract for K',
    'EL copper around the relief holes and the 6.8 mm pot passages: tracks and zones are outside the courtyard model',
    'EL windows around the relief holes and passages: NOT CHECKABLE, no EL window geometry is recorded in the sources',
    'CLT-104-02-L-D-BE-K-TR body outline: not retained; the -D courtyard envelope of design/stack/connectors/land-patterns.json stands in for it',
]


def build_report(doc, ctx, candidate_sha256, measurements=True):
    """The check report; a measurement that raises becomes an error entry instead of a traceback."""
    res = run_checks(doc, ctx)
    errors = list(res.errors)
    report = {
        'schema_version': 1,
        'status': 'COURTYARD-AND-PAD-LEVEL PLANNING SCREEN; not a copper clearance, tolerance result or physical fit; unvalidated draft',
        'verdict': None,
        'candidate_sha256': candidate_sha256,
        'canonical_input_digest': sg.canonical_digest(ctx.ci),
        'errors': errors,
        'checks': res.checks,
        'not_run': NOT_RUN,
    }
    if measurements:
        import measure
        try:
            report['measurements'] = measure.measure(ctx.ci, doc['candidate'], ctx)
        except Exception as exc:  # noqa: BLE001 - any measurement failure must still leave a report
            errors.append('measurements: %s: %s' % (type(exc).__name__, exc))
            report['measurements'] = None
    report['verdict'] = 'FAIL' if errors else 'PASS'
    return report


def main(argv):
    raw = sg.load_raw()
    boards = sg.load_boards(raw)
    ci = sg.canonical_inputs(raw, boards)
    ctx = Context(ci)
    doc = json.loads(sg.CANDIDATE.read_text())
    report = build_report(doc, ctx, sg.sha256_file(sg.CANDIDATE), '--no-measurements' not in argv)
    sg.REPORT.write_text(json.dumps(report, indent=1) + '\n')
    print('verdict', report['verdict'], 'errors', len(report['errors']))
    for e in report['errors'][:30]:
        print('  ', e)
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
