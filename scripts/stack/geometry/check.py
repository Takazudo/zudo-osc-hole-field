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
        model = p['obstacle_model']
        retired_k = set()
        con = {c['id']: c for c in ci['partition']['connectors']}
        for h in ci['partition']['harnesses']:
            if any(b in p['retired_boards'] for b in h['boards']):
                for cid in h['header_ids']:
                    if con[cid]['board'] == 'K':
                        retired_k.add(con[cid]['pcb_reference'])
        self.retired_k = retired_k
        self.obstacles = {'K': sg.Obstacles(ci['boards']['K'], model, drop=frozenset(retired_k),
                                            skip_hole=lambda f: f['ref'].startswith('MH_K-SERVICE'))}
        for key in ('JL', 'JR', 'P', 'EL', 'O1', 'O3', 'O5'):
            self.obstacles[key] = sg.Obstacles(ci['boards'][key], model)
        self.reference = generate.build(ci)
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
    if st['K_rear_parts_z_mm'] - st['enclosure_inner_rear_z_mm'] < 0:
        errs.append('K rear parts at z=%s pass the enclosure inner rear at z=%s' % (st['K_rear_parts_z_mm'], st['enclosure_inner_rear_z_mm']))
    for p in cand['pairs']:
        gap = '/'.join(p['boards']) if p['family'] != 'EL/P' else 'EL/P'
        gap = {'K/O1': 'O1/K', 'K/O3': 'O3/K', 'K/O5': 'O5/K'}.get(gap, gap)
        if gap in st['mated_heights_mm'] and abs(p['mated_height_mm'] - st['mated_heights_mm'][gap]) > TOL:
            errs.append('pair %s mated height %s differs from gap %s %s' % (p['id'], p['mated_height_mm'], gap, st['mated_heights_mm'][gap]))
    res.check('planes_and_gaps', {'stack': ref}, errs)


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
    for p in cand['pairs']:
        for name, half in (('front', 'front'), ('back', 'K')):
            s = p['sites'][name]
            w, l = sg.envelope(ctx.land, p['positions'], half)
            rect = sg.env_rect(s['center'][0], s['center'][1], w, l, s['long_axis_x'])
            if any(abs(a - b) > TOL for a, b in zip(rect, s['envelope'])):
                errs.append('pair %s %s envelope %s is stale; land pattern gives %s' % (p['id'], name, s['envelope'], rect))
            if s['replaces']:
                gh = ctx.fps[s['board']][s['replaces']]['courtyard']
                counted += 1
                if not sg.inside(rect, gh):
                    errs.append('pair %s %s envelope %s lies outside the GH courtyard %s of %s on %s'
                                % (p['id'], name, rect, gh, s['replaces'], s['board']))
    res.check('replacement_inside_gh_courtyard', {'replaced_halves_checked': counted}, errs)


def check_blockers(cand, ctx, res):
    errs = []
    declared = []
    for p in cand['pairs']:
        for name in ('front', 'back'):
            s = p['sites'][name]
            skip = {s['replaces']} if s['replaces'] else set()
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


def adjacency_violations(pins):
    out = []
    for i, n in enumerate(pins):
        if n in ('AGND', 'NC') or n in RAILS:
            continue
        nb = [pins[j] for j in (i - 1, i + 1) if 0 <= j < len(pins)]
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
            for n in adjacency_violations(pins):
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
        if h['boards'] == ['EL', 'K']:
            pass
    rails_seen = {n for p in cand['pairs'] if p['family'] == 'EL/P' for n in p['pin_map'] if n in RAILS}
    for r in RAILS:
        if r not in rails_seen:
            errs.append('EL/P pairs do not carry rail %s to EL' % r)
    crossing = sum(len(harness[h]['signals']) for h, js in by_source.items() if len(js) == 2)
    totals['nets_counted_at_two_joints'] = crossing
    lone = {p['id']: adjacency_violations(p['pin_map']) for p in cand['pairs'] if adjacency_violations(p['pin_map'])}
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


def check_sub(cand, ctx, res):
    errs = []
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
        if not sg.inside(s['toggle_courtyard'][:1] + [t[1]] + s['toggle_courtyard'][2:3] + [t[3]], t):
            errs.append('SUB toggle %s courtyard %s is not inside control tab %s' % (s['block'], s['toggle_courtyard'], t))
        env = pair['sites']['front']['envelope']
        if not sg.inside(sg.grow(env, m)[:3] + [min(env[3] + m, t[3])], t):
            errs.append('SUB pair %s envelope %s is not inside control tab %s with %s mm margin' % (s['block'], env, t, m))
        if abs(pair['sites']['front']['center'][1] - y) > TOL:
            errs.append('SUB pair %s site differs from the recorded SUB site' % s['block'])
    res.check('sub_toggle_windows', {'windows': {s['block']: {'window_centre_y': s['window_centre_y'], 'window_mm': s['window_mm'],
                                                              'site_centre': s['site_centre']} for s in cand['sub_toggles']}}, errs)


def check_posts(cand, ctx, res):
    errs = []
    tabs = {t['id']: t for t in cand['tabs']}
    coax = 0
    for p in cand['posts']:
        land = p['proposed_front_land']
        if abs(land[0] - p['K_land'][0]) > TOL or abs(land[1] - p['K_land'][1]) > TOL:
            errs.append('post %s is not coaxial: front land %s, K land %s' % (p['id'], land, p['K_land']))
            continue
        if p['present_offset_mm'] <= TOL:
            coax += 1
            continue
        t = tabs.get(p['resolved_by'])
        w, h = p['land_courtyard_mm']
        court = [land[0] - w / 2, land[1] - h / 2, land[0] + w / 2, land[1] + h / 2]
        if t is None:
            errs.append('post %s moves its %s land to %s with no tab to carry it' % (p['id'], p['front_board'], land))
        elif not on_tab_or_body(court, t['rect'], ctx.boards['P']['outline']):
            errs.append('post %s moved land courtyard %s is outside %s %s' % (p['id'], court, t['id'], t['rect']))
    if len(cand['posts']) != len(ctx.ci['partition']['load_side_wires']):
        errs.append('expected %d posts, found %d' % (len(ctx.ci['partition']['load_side_wires']), len(cand['posts'])))
    res.check('post_coaxiality', {'posts': len(cand['posts']), 'coaxial_today': coax,
                                  'offset_resolved_by_power_tab': [p['id'] for p in cand['posts'] if p['resolved_by']]}, errs)


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
    pz = (p_board['face_z_mm'] - p_board['thickness_mm'], p_board['face_z_mm'])
    detail = {}
    carrier = ctx.ci['partition']['jack_seam_carrier']
    carriers = [('seam rear cradle', carrier['rear_rect_mm'], carrier['rear_z_mm']),
                ('seam front lip', carrier['front_lip_rect_mm'], carrier['front_lip_z_mm'])]
    carriers += [('seam cross-member %d' % i, c['rect_mm'], c['z_mm']) for i, c in enumerate(carrier['cross_members'], 1)]
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
    res.check('p_tabs', {'tabs': detail, 'NOT_RUN': 'P body-carrier envelope: no carrier geometry is recorded in the sources (text only in partition load paths)'}, errs)


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
    sel_tail = None
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


def check_facing_heights(cand, ctx, res):
    errs = []
    detail = {}
    replaced = {s['replaces'] for p in cand['pairs'] for s in p['sites'].values() if s['replaces']}
    posts = {p['front_ref'] for p in cand['posts']} | {p['K_ref'] for p in cand['posts']}
    exclude = replaced | posts | ctx.retired_k
    gaps = cand['stack']['mated_heights_mm']
    k_outline = ctx.boards['K']['outline']
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
        idx = {}
        for k, it in enumerate(b_items):
            r = it[2]
            for i in range(int(r[0] // 5), int(r[2] // 5) + 1):
                for j in range(int(r[1] // 5), int(r[3] // 5) + 1):
                    idx.setdefault((i, j), []).append(k)
        for it in a_items + b_items:
            if it[3] is not None and it[3] >= gap:
                single.append({'ref': it[0], 'height_mm': it[3], 'gap_mm': gap})
        for a in a_items:
            seen = set()
            r = a[2]
            for i in range(int(r[0] // 5), int(r[2] // 5) + 1):
                for j in range(int(r[1] // 5), int(r[3] // 5) + 1):
                    for k in idx.get((i, j), ()):
                        if k in seen:
                            continue
                        seen.add(k)
                        b = b_items[k]
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
            'collisions': collisions}
    res.check('facing_heights', {'gaps': detail, 'height_source': 'design/mechanical/ic-envelope-native-report.json native display-model z bounds (not seated heights), selector-assembly.json tails, partition bulk reserves; every other part height is unretained and counted as unknown'}, errs)


CHECKS = [check_planes, check_coaxial, check_containment, check_blockers, check_pins, check_pass_through,
          check_sub, check_posts, check_tabs, check_retired, check_facing_heights]


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


def main(argv):
    raw = sg.load_raw()
    boards = sg.load_boards(raw)
    ci = sg.canonical_inputs(raw, boards)
    ctx = Context(ci)
    doc = json.loads(sg.CANDIDATE.read_text())
    res = run_checks(doc, ctx)
    report = {
        'schema_version': 1,
        'status': 'COURTYARD-AND-PAD-LEVEL PLANNING SCREEN; not a copper clearance, tolerance result or physical fit; unvalidated draft',
        'verdict': 'FAIL' if res.errors else 'PASS',
        'candidate_sha256': sg.sha256_file(sg.CANDIDATE),
        'canonical_input_digest': sg.canonical_digest(ci),
        'errors': res.errors,
        'checks': res.checks,
        'not_run': [
            'Copper clearance, DRC and routing of the stack: no stack board exists',
            'Tolerance stack-up, mating misalignment and force: no exact connector (ST-01, ST-03)',
            'P body-carrier openings for the EL pairs: no carrier envelope is recorded in the sources',
            'Seated part heights: only native display-model envelopes and the listed reserves are retained; other heights are counted as unknown',
            'Native KiCad oracle query: not needed; boards parsed with plain Python and the extract matched the planning extract for K',
        ],
    }
    if '--no-measurements' not in argv:
        import measure
        report['measurements'] = measure.measure(ci, doc['candidate'], ctx)
    sg.REPORT.write_text(json.dumps(report, indent=1) + '\n')
    print('verdict', report['verdict'], 'errors', len(res.errors))
    for e in res.errors[:30]:
        print('  ', e)
    return 1 if res.errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
