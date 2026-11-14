"""Courtyard-level measurements that reconcile the plan page's counts and dimensions.

Called by check.py (section `measurements` of the check report). Each value is a
planning screen at courtyard-and-pad level, not a copper clearance or a fit.
"""
import math
import statistics

import stackgeom as sg

RAILS = ('+12V', '-12V', '+5V')


def _con(ci):
    return {c['id']: c for c in ci['partition']['connectors']}


def _fps(ci):
    return {k: {f['ref']: f for f in v} for k, v in ci['boards'].items()}


def interface_census(ci):
    con = _con(ci)
    by_mate = {}
    noncoax = []
    for h in ci['partition']['harnesses']:
        a, b = [con[i] for i in h['header_ids']]
        if 'K' not in h['boards']:
            if a['center_mm'] != b['center_mm']:
                noncoax.append(h['id'])
            continue
        k, f = (a, b) if a['board'] == 'K' else (b, a)
        mate = 'O1-O5' if f['board'].startswith('O') else f['board']
        e = by_mate.setdefault(mate, {'K_headers': 0, 'coaxial': 0, 'front_side': set(), 'K_side': set()})
        e['K_headers'] += 1
        e['coaxial'] += int(k['center_mm'] == f['center_mm'])
        e['front_side'].add(f['side'])
        e['K_side'].add(k['side'])
    for e in by_mate.values():
        e['front_side'] = sorted(e['front_side'])
        e['K_side'] = sorted(e['K_side'])
    return {'by_mate': by_mate, 'K_headers': sum(e['K_headers'] for e in by_mate.values()),
            'non_coaxial_harnesses': noncoax}


def gh_courtyards(ci):
    out = {}
    for key, fps in ci['boards'].items():
        for f in fps:
            if f['lib'].startswith('JST_GH') and f['courtyard']:
                c = f['courtyard']
                w, h = sorted((round(c[2] - c[0], 4), round(c[3] - c[1], 4)))
                out.setdefault(f['lib'], set()).add((w, h))
    return {k: sorted(v) for k, v in sorted(out.items())}


def _harness_sites(ci, fps, contacts=None, pairs=None):
    con = _con(ci)
    for h in ci['partition']['harnesses']:
        key = '/'.join(h['boards'])
        if pairs and key not in pairs:
            continue
        a, b = [con[i] for i in h['header_ids']]
        if contacts and a['contacts'] != contacts:
            continue
        yield h, [(c['board'], fps[c['board']][c['pcb_reference']]) for c in (a, b)]


def _fit(obs, board, f, w, l, axis, dx=0.0, dy=0.0):
    c = sg.centre(f['courtyard'])
    rect = sg.env_rect(c[0] + dx, c[1] + dy, w, l, axis)
    return not obs[board].hits(f['side'], rect, {f['ref']})


def envelope_fits(ci, obs, land, positions):
    fps = _fps(ci)
    out = {}
    for contacts, n, label in ((3, positions['K/P'], 'GH3'), (7, positions['K/O'], 'GH7'), (8, positions['JL/K'], 'GH8')):
        w, l = sg.envelope(land, n, 'front')
        ok = total = 0
        fails = []
        for h, ends in _harness_sites(ci, fps, contacts):
            good = all(_fit(obs, bk, f, w, l, (f['courtyard'][2] - f['courtyard'][0]) >= (f['courtyard'][3] - f['courtyard'][1]))
                       for bk, f in ends)
            total += 1
            ok += int(good)
            if not good:
                fails.append(h['id'])
        out[label] = {'positions': n, 'envelope_mm': [w, l], 'sites': total, 'fit_in_place_both_boards': ok, 'fails': fails}
    return out


def sweep(ci, obs, params):
    fps = _fps(ci)
    out = []
    groups = (('3', 3, ('K/P', 'JL/P')), ('6', 8, ('JL/K', 'JR/K', 'EL/K')), ('5', 7, ('K/O1', 'K/O2', 'K/O3', 'K/O4', 'K/O5')))
    for key, contacts, mates in groups:
        for w, l in params['envelope_sweep_mm'][key]:
            counts = {}
            for h, ends in _harness_sites(ci, fps, contacts, mates):
                mate = '/'.join(h['boards'])
                good = any(all(_fit(obs, bk, f, w, l, ax) for bk, f in ends) for ax in (True, False))
                e = counts.setdefault(mate, [0, 0])
                e[0] += int(not good)
                e[1] += 1
            out.append({'envelope_mm': [w, l], 'fail_of_sites': {m: '%d of %d' % tuple(v) for m, v in sorted(counts.items())}})
    return out


def longer_rows(ci, obs, params):
    fps = _fps(ci)
    st = params['shift_search']
    k = int(round(st['max_mm'] / st['step_mm']))
    shifts = sorted([(i * st['step_mm'], j * st['step_mm']) for i in range(-k, k + 1) for j in range(-k, k + 1)],
                    key=lambda s: abs(s[0]) + abs(s[1]))
    out = {}
    for name, (w, l) in params['longer_single_row_mm'].items():
        counts = {}
        for h, ends in _harness_sites(ci, fps, 8, ('JL/K', 'JR/K', 'EL/K')):
            mate = '/'.join(h['boards'])
            found = False
            for dx, dy in shifts:
                for ax in (True, False):
                    if all(_fit(obs, bk, f, w, l, ax, dx, dy) for bk, f in ends):
                        found = True
                        break
                if found:
                    break
            e = counts.setdefault(mate, [0, 0])
            e[0] += int(not found)
            e[1] += 1
        out[name] = {'envelope_mm': [w, l], 'no_position_within_shift': {m: '%d of %d' % tuple(v) for m, v in sorted(counts.items())}}
    return out


def opposite_face(ci, obs):
    fps = _fps(ci)
    con = _con(ci)
    res = {}
    for c in con.values():
        if c['board'] not in obs:
            continue
        f = fps[c['board']][c['pcb_reference']]
        other = 'F' if f['side'] == 'B' else 'B'
        occupied = bool(obs[c['board']].hits(other, f['courtyard'], {f['ref']}))
        grp = 'J' if c['board'] in ('JL', 'JR') else c['board']
        e = res.setdefault(grp, [0, 0])
        e[0] += int(occupied)
        e[1] += 1
    return {k: '%d of %d' % tuple(v) for k, v in sorted(res.items())}


def _near(fps, cx, cy, rad, side, skip_lib=('LoadWire',)):
    """Footprints on `side` (courtyard or pad) or with a drilled pad, within `rad` of a point (planning helper)."""
    out = set()
    for f in fps:
        if any(s in f['lib'] for s in skip_lib):
            continue
        cy_ = f['courtyard']
        if cy_ and f['side'] == side:
            dx = max(cy_[0] - cx, 0, cx - cy_[2])
            dy = max(cy_[1] - cy, 0, cy - cy_[3])
            if dx * dx + dy * dy < rad * rad:
                out.add(f['ref'] or 'HOLE')
                continue
        for p in f['pads']:
            if p['drill'] or f['side'] == side:
                r = max(p['bbox'][2] - p['bbox'][0], p['bbox'][3] - p['bbox'][1]) / 2
                if (p['center'][0] - cx) ** 2 + (p['center'][1] - cy) ** 2 < (rad + r) ** 2:
                    out.add(f['ref'] or 'HOLE')
                    break
    return sorted(out)


def power_lands(ci, cand, rad):
    k = ci['boards']['K']
    per = []
    for p in cand['posts']:
        x, y = p['K_land']
        per.append({'post': p['id'], 'K_land': p['K_land'], 'K_B': _near(k, x, y, rad, 'B'), 'K_F': _near(k, x, y, rad, 'F')})
    moved = [p for p in cand['posts'] if p['present_offset_mm'] > 0]
    alt = {'F': set(), 'B': set()}
    for p in moved:
        x, y = p['front_land']
        for s in 'FB':
            alt[s] |= set(_near(k, x, y, rad, s))
    front = {}
    for p in cand['posts']:
        fb = ci['boards'][p['front_board']]
        x, y = p['front_land']
        e = front.setdefault(p['front_board'], {'lands': 0, 'clear_both_faces': 0, 'clear_F': 0})
        nf, nb = _near(fb, x, y, rad, 'F'), _near(fb, x, y, rad, 'B')
        e['lands'] += 1
        e['clear_both_faces'] += int(not nf and not nb)
        e['clear_F'] += int(not nf)
    return {
        'radius_mm': rad,
        'K_lands_with_B_neighbour': sum(1 for e in per if e['K_B']),
        'K_B_neighbours_total': sum(len(e['K_B']) for e in per),
        'K_lands_with_F_neighbour': sum(1 for e in per if e['K_F']),
        'per_land': per,
        'K_lands_moved_to_front_land_y': {'F': len(alt['F']), 'B': len(alt['B'])},
        'front_lands': front,
        'coaxial_pairs': sum(1 for p in cand['posts'] if p['present_offset_mm'] == 0),
        'offset_pairs': [{'post': p['id'], 'front_land': p['front_land'], 'K_land': p['K_land']} for p in moved],
    }


def tab_occupants(ci, cand):
    out = {}
    for t in cand['tabs']:
        r = t['rect']
        occ = {}
        for key in ('EL', 'JL', 'JR', 'O1', 'O3', 'O5'):
            for f in ci['boards'][key]:
                hit = (f['courtyard'] and sg.inter(f['courtyard'], r)) or any(sg.inter(p['bbox'], r) for p in f['pads'])
                if hit:
                    occ.setdefault(key, []).append(f['ref'])
        out[t['id']] = {k: sorted(v) for k, v in occ.items()}
    return out


def k_area(ci, obs_all):
    tot = ff = fb = 0
    ol = ci['partition']['boards']
    for x in range(5, 313):
        for y in range(9, 291):
            if x > 258 and y > 246:
                continue
            tot += 1
            r = [x, y, x + 1, y + 1]
            ff += not obs_all.hits('F', r)
            fb += not obs_all.hits('B', r)
    return {'cells_mm2': tot, 'free_F_percent': round(100 * ff / tot, 1), 'free_B_percent': round(100 * fb / tot, 1),
            'scope': '1 mm cells, x 5..312, y 9..290 outside the notch; obstacle model with every K hole retained'}


def k_fragmentation(obs):
    slots = 0
    x = 182.0
    while x <= 312.0:
        y = 160.0
        while y <= 180.0:
            for lx, ly in ((13.0, 5.0), (5.0, 13.0)):
                r = [x - lx / 2, y - ly / 2, x + lx / 2, y + ly / 2]
                if r[2] > 313.0:
                    continue
                if not obs.hits('F', r) and not obs.hits('B', r):
                    slots += 1
                    break
            y += 0.5
        x += 0.5
    gh8 = 0
    x = 182.0
    while x <= 312.0:
        y = 150.0
        while y <= 200.0:
            for lx, ly in ((13.94, 6.1), (6.1, 13.94)):
                r = [x - lx / 2, y - ly / 2, x + lx / 2, y + ly / 2]
                if r[2] > 313.5:
                    continue
                if not obs.hits('B', r):
                    gh8 += 1
                    break
            y += 0.5
        x += 0.5
    return {'through_slot_13x5_positions_x182_312_y160_180': slots, 'GH8_B_positions_x182_312_y150_200': gh8}


def trimmers(ci, obs_all, growth):
    k = ci['boards']['K']
    tr = [f for f in k if 'TC33X' in f['lib']]
    front = sorted([f for f in tr if f['side'] == 'F'], key=lambda f: f['ref'])
    taken = []
    dist = []
    cands = sorted([(dx * 0.5, dy * 0.5) for dx in range(-60, 61) for dy in range(-60, 61)], key=lambda s: s[0] ** 2 + s[1] ** 2)
    for f in front:
        c = f['courtyard']
        w, h = c[2] - c[0], c[3] - c[1]
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        best = None
        for dx, dy in cands:
            for ww, hh in ((w, h), (h, w)):
                r = [cx + dx - ww / 2, cy + dy - hh / 2, cx + dx + ww / 2, cy + dy + hh / 2]
                if not (4.5 < r[0] and r[2] < 313.5 and 8.5 < r[1] and r[3] < 291.5):
                    continue
                if r[2] > 257.5 and r[3] > 245.5:
                    continue
                if not obs_all.hits('B', r) and all(not sg.inter(sg.grow(r, growth), t) for t in taken):
                    best = (dx, dy, r)
                    break
            if best:
                break
        if best:
            dist.append(math.hypot(best[0], best[1]))
            taken.append(best[2])
    return {'F': len(front), 'B': sum(1 for f in tr if f['side'] == 'B'), 'relocatable_within_30mm': len(dist),
            'median_move_mm': round(statistics.median(dist), 1) if dist else None,
            'longest_move_mm': round(max(dist), 1) if dist else None,
            'test_pads_F': sorted(f['ref'] for f in k if f['lib'].startswith('TestPad') and f['side'] == 'F')}


def supports(ci):
    sup = ci['partition']['supports']
    k_sup = [s for s in sup if s['board'] == 'K']
    k_ol = [b for b in ci['partition']['boards'] if b['board_key'] == 'K'][0]['outline']
    j = []
    for s in sup:
        if s['board'] in ('JL', 'JR'):
            d = min(math.dist(s['position_mm'], t['position_mm']) for t in k_sup)
            if d < 3:
                j.append({'support': s['id'], 'distance_to_K_support_mm': round(d, 3)})
    p = []
    for s in sup:
        if s['id'].startswith('P-SUP'):
            x, y = s['position_mm']
            r = s['collar_diameter_mm'] / 2
            inside_k = sg.point_in_poly(x + r - 0.001, y, k_ol) or sg.point_in_poly(x - r + 0.001, y, k_ol)
            edges = [q[0] for q in k_ol]
            depth = None
            if inside_k:
                depth = round(min(abs((x + r) - e) if x < e else abs(e - (x - r)) for e in edges if abs(e - x) <= r), 3)
            p.append({'support': s['id'], 'collar_over_K_outline': inside_k, 'overlap_mm': depth})
    return {'J_near_K': j, 'P_collars': p, 'P_collars_over_K': sum(1 for e in p if e['collar_over_K_outline'])}


def selector_envelopes(ci):
    z = ci['mechanical']['selector_body_support_z_mm']
    out = {}
    for i in ci['mechanical']['selector_instances']:
        out[i['uid']] = [round(i['pcb_z_mm'] + z[0], 3), round(i['pcb_z_mm'] + z[1], 3)]
    return out


def today(ci):
    part = ci['partition']
    c = part['counts']
    con = _con(ci)
    libs = {}
    for h in part['harnesses']:
        n = con[h['header_ids'][0]]['contacts']
        libs['GH%d' % n] = libs.get('GH%d' % n, 0) + 1
    receivers = {}
    for cc in part['connectors']:
        if cc['board'].startswith('O'):
            receivers[cc['board']] = receivers.get(cc['board'], 0) + sum(1 for n in cc['pin_map'].values() if n.startswith('OSC_OCT'))
    return {'harnesses': c['harnesses'], 'by_type': libs, 'header_contacts': c['header_contacts'],
            'positions_per_side': c['header_contacts'] // 2,
            'fitted_crimps': c['header_contacts'] - 2 * c['unwired_positions_across_all_harnesses_per_end'],
            'signal': c['wired_signal_conductors'], 'return': c['wired_return_conductors'], 'rail': c['rail_conductors_GH'],
            'load_side_wires': c['factory_load_side_wires'], 'load_side_lands': c['load_side_copper_terminals'],
            'K_service_apertures': len(part['K_service_apertures']), 'boards': c['boards'],
            'octave_receivers': receivers, 'K_plane_today_z_mm': [b['face_z_mm'] for b in part['boards'] if b['board_key'] == 'K'][0],
            'enclosure_depth_today_mm': part['enclosure']['inside_depth_mm'],
            'K_rear_clearance_today_mm': round(part['enclosure']['inside_depth_mm'] - (-[b['face_z_mm'] for b in part['boards'] if b['board_key'] == 'K'][0] + 1.6) - ci['mechanical']['core_rear_ceiling_mm'], 3)}


def standoffs(ci, edge=3.0, step=0.5):
    def build(key):
        idx = {'F': {}, 'B': {}}

        def add(side, r):
            for i in range(int(r[0] // 5), int(r[2] // 5) + 1):
                for j in range(int(r[1] // 5), int(r[3] // 5) + 1):
                    idx[side].setdefault((i, j), []).append(r)
        for f in ci['boards'][key]:
            if 'LoadWire' in f['lib']:
                continue
            if f['courtyard']:
                add(f['side'], f['courtyard'])
            for p in f['pads']:
                if p['drill']:
                    add('F', p['bbox'])
                    add('B', p['bbox'])
                else:
                    add(f['side'], p['bbox'])
        return idx

    def free(idx, side, cx, cy, rad):
        for i in range(int((cx - rad) // 5), int((cx + rad) // 5) + 1):
            for j in range(int((cy - rad) // 5), int((cy + rad) // 5) + 1):
                for r in idx[side].get((i, j), ()):
                    dx = max(r[0] - cx, 0, cx - r[2])
                    dy = max(r[1] - cy, 0, cy - r[3])
                    if dx * dx + dy * dy < rad * rad:
                        return False
        return True
    ol = {b['board_key']: b['outline'] for b in ci['partition']['boards']}
    kidx = build('K')
    out = {}
    for front in ('JL', 'JR', 'P'):
        fidx = build(front)
        poly = ol[front]
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        pts = []
        x = min(xs) + edge
        while x <= max(xs) - edge:
            y = min(ys) + edge
            while y <= max(ys) - edge:
                if all(sg.point_in_poly(x + dx, y + dy, poly) and sg.point_in_poly(x + dx, y + dy, ol['K'])
                       for dx, dy in ((0, 0), (edge, 0), (-edge, 0), (0, edge), (0, -edge))):
                    if free(fidx, 'B', x, y, 3.0) and free(kidx, 'F', x, y, 3.0) and free(kidx, 'B', x, y, 2.6):
                        pts.append((x, y))
                y += step
            x += step
        kept = []
        for p in pts:
            if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= 64 for q in kept):
                kept.append(p)
        out[front] = len(kept)
    return {'sites_8mm_apart': out, 'rule': 'front B.Cu and K F.Cu clear within 3.0 mm, K B.Cu within 2.6 mm, 3 mm inside both outlines, 0.5 mm grid, greedy 8 mm thinning'}


def measure(ci, cand, ctx):
    params = ci['parameters']
    land = ci['land_pattern']
    model = params['obstacle_model']
    obs = dict(ctx.obstacles)
    for key in ('O2', 'O4'):
        obs[key] = sg.Obstacles(ci['boards'][key], model)
    k_all = sg.Obstacles(ci['boards']['K'], model)
    sub = []
    for s in cand['sub_toggles']:
        w, l = sg.envelope(land, params['positions']['SUB'], 'front')
        probe = params.get('probe_tab_top_mm')
        e = {'block': s['block'], 'window_mm': s['window_mm']}
        if probe is not None:
            e['tab_top_probe_mm'] = probe
            e['shortfall_mm'] = round(probe + params['tab_edge_margin_mm'] + w / 2 - s['window_centre_y'][1], 4)
        sub.append(e)
    return {
        'interface_census': interface_census(ci),
        'gh_courtyards_mm': gh_courtyards(ci),
        'planning_envelope_fit_in_place': envelope_fits(ci, obs, land, params['positions']),
        'envelope_sweep': sweep(ci, obs, params),
        'longer_single_rows': longer_rows(ci, obs, params),
        'opposite_face_occupied_behind_sites': opposite_face(ci, obs),
        'power_lands': power_lands(ci, cand, params['power_land_neighbour_radius_mm']),
        'tab_occupants_on_other_boards': tab_occupants(ci, cand),
        'K_footprints': len(ci['boards']['K']),
        'K_free_area': k_area(ci, k_all),
        'K_fragmentation': k_fragmentation(ctx.obstacles['K']),
        'K_trimmers': trimmers(ci, k_all, model['own_face_courtyard_growth_mm']),
        'interior_fastener_sites': standoffs(ci),
        'supports': supports(ci),
        'selector_rear_envelopes_z_mm': selector_envelopes(ci),
        'today': today(ci),
        'sub_tab_probe': sub,
    }
