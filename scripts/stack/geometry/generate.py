"""Generate design/stack/geometry/stack-candidate.json from the sources.

    python3 scripts/stack/geometry/generate.py [--stdout]

Inputs are the partition, the placement lock, the retained mechanical heights, the
board files and the two planning-parameter files beside the output. Nothing is
copied from the plan page; the page is what check.py and the README reconcile.
"""
import json
import sys

import stackgeom as sg

RAIL_NETS = ('+12V', '-12V', '+5V')


def board_index(ci):
    return {b['board_key']: b for b in ci['partition']['boards']}


def fp_by_ref(ci, key):
    return {f['ref']: f for f in ci['boards'][key]}


def ordered_pins(pin_map):
    return [pin_map[k] for k in sorted(pin_map, key=lambda s: int(s))]


def long_axis_x(rect):
    return (rect[2] - rect[0]) >= (rect[3] - rect[1])


def fill_template(template, signals, rails=()):
    slots = [c for c in template]
    out = []
    sig = list(signals)
    rail = list(rails)
    for c in slots:
        if c == 'S':
            out.append(sig.pop(0) if sig else 'NC')
        elif c == 'G':
            out.append('AGND')
        elif c == 'R':
            out.append(rail.pop(0) if rail else 'NC')
    return out, sig, rail


def p_edge_y(outline, x):
    """Topmost y of the P outline at a given x (sampled at 0.05 mm)."""
    for i in range(0, 6001):
        y = i * 0.05
        if sg.point_in_poly(x, y + 0.025, outline):
            return round(y, 2)
    raise ValueError('x outside outline')


def make_site(board, side, center, replaces, gh_courtyard, axis_x):
    return {'board': board, 'side': side, 'center': [round(center[0], 4), round(center[1], 4)],
            'replaces': replaces, 'replaced_gh_courtyard': gh_courtyard, 'long_axis_x': axis_x}


def build(ci, obstacles=None):
    params = ci['parameters']
    land = ci['land_pattern']
    part = ci['partition']
    bidx = board_index(ci)
    retired = set(params['retired_boards'])
    con = {c['id']: c for c in part['connectors']}
    fps = {k: fp_by_ref(ci, k) for k in ci['boards']}
    templates = params['pin_templates']
    positions = params['positions']

    # ---------------------------------------------------------- planes
    adapters = [k for k in ('O1', 'O3', 'O5')]
    adapter_rear = min(bidx[k]['face_z_mm'] - bidx[k]['thickness_mm'] for k in adapters)
    k_face = round(adapter_rear - params['k_plane']['adapter_mated_height_mm'], 4)
    k_rear = round(k_face - bidx['K']['thickness_mm'], 4)
    k_parts = round(k_rear - ci['mechanical']['core_rear_ceiling_mm'], 4)
    sel_tail = round(min(bidx[k]['face_z_mm'] for k in adapters) + ci['mechanical']['selector_body_support_z_mm'][0], 4)
    enclosure = -params['enclosure_inside_depth_mm']
    planes = {}
    for key, b in sorted(bidx.items()):
        if key in retired:
            continue
        face = k_face if key == 'K' else b['face_z_mm']
        planes[key] = {'face_z_mm': face, 'rear_z_mm': round(face - b['thickness_mm'], 4),
                       'thickness_mm': b['thickness_mm'], 'outline': b['outline'],
                       'plane_source': 'derived: adapter rear face minus adapter mated height' if key == 'K'
                       else 'partition.json face_z_mm (unchanged)'}
    gaps = {}
    for front in ('JL', 'JR', 'P', 'O1', 'O3', 'O5'):
        gaps[front + '/K'] = round(planes[front]['rear_z_mm'] - k_face, 4)
    gaps['EL/P'] = round(planes['EL']['rear_z_mm'] - planes['P']['face_z_mm'], 4)
    stack = {
        'K_face_z_mm': k_face, 'K_rear_z_mm': k_rear, 'K_rear_parts_z_mm': k_parts,
        'selector_tail_z_mm': sel_tail, 'selector_tail_to_K_mm': round(sel_tail - k_face, 4),
        'enclosure_inner_rear_z_mm': enclosure, 'rear_part_clearance_mm': round(k_parts - enclosure, 4),
        'mated_heights_mm': gaps,
    }

    # ---------------------------------------------------------- pairs
    pairs = []
    retired_items = {'boards': sorted(retired), 'K_headers': [], 'front_headers': [], 'harnesses': []}

    def gh(key, ref):
        return fps[key][ref]['courtyard']

    def add_pair(pid, family, front, back, n, pins, mated, source_harness, note=''):
        pairs.append({'id': pid, 'family': family, 'boards': [front['board'], back['board']], 'positions': n,
                      'pin_map': pins, 'mated_height_mm': mated, 'source_harness': source_harness,
                      'sites': {'front': front, 'back': back}, 'note': note})

    el_harnesses = []
    jl_p = []
    for h in part['harnesses']:
        boards = h['boards']
        if any(b in retired for b in boards):
            retired_items['harnesses'].append(h['id'])
            for cid in h['header_ids']:
                c = con[cid]
                (retired_items['K_headers'] if c['board'] == 'K' else retired_items['front_headers']).append(c['pcb_reference'])
            continue
        a, b = [con[i] for i in h['header_ids']]
        if boards == ['EL', 'K']:
            el_harnesses.append((h, a, b))
            continue
        if boards == ['JL', 'P']:
            jl_p.append((h, a, b))
            continue
        k_con, f_con = (a, b) if a['board'] == 'K' else (b, a)
        fb = f_con['board']
        family = 'K/O' if fb.startswith('O') else ('K/P' if fb == 'P' else fb + '/K')
        n = positions[family]
        tkey = family
        if family == 'K/O':
            tkey = 'K/O first' if h['id'].endswith('-1') else 'K/O second'
        signals = [x for x in ordered_pins(f_con['pin_map']) if x not in ('AGND', 'NC') + RAIL_NETS]
        pins, left, _ = fill_template(templates[tkey], signals)
        fgh, kgh = gh(fb, f_con['pcb_reference']), gh('K', k_con['pcb_reference'])
        front = make_site(fb, f_con['side'], f_con['center_mm'], f_con['pcb_reference'], fgh, long_axis_x(fgh))
        back = make_site('K', k_con['side'], k_con['center_mm'], k_con['pcb_reference'], kgh, long_axis_x(kgh))
        add_pair(h['id'], tkey, front, back, n, pins, gaps[fb + '/K'], h['id'],
                 'unplaced signals: ' + ', '.join(left) if left else '')

    # JL-to-P nets pass through K at both existing header coordinates
    for i, (h, a, b) in enumerate(sorted(jl_p, key=lambda t: t[0]['id']), 1):
        jl_con, p_con = (a, b) if a['board'] == 'JL' else (b, a)
        tkey = 'JL/P pass-through'
        n = positions[tkey]
        signals = [x for x in ordered_pins(jl_con['pin_map']) if x not in ('AGND', 'NC') + RAIL_NETS]
        pins, _, _ = fill_template(templates[tkey], signals)
        for fcon, fb, pid, gap in ((jl_con, 'JL', 'JL-K-X%d' % i, gaps['JL/K']), (p_con, 'P', 'P-K-X%d' % i, gaps['P/K'])):
            fgh = gh(fb, fcon['pcb_reference'])
            front = make_site(fb, fcon['side'], fcon['center_mm'], fcon['pcb_reference'], fgh, long_axis_x(fgh))
            back = make_site('K', 'F.Cu', fcon['center_mm'], None, None, long_axis_x(fgh))
            add_pair(pid, tkey, front, back, n, list(pins), gap, h['id'],
                     'pass-through: %s carried JL to P through K' % h['id'])

    # EL plugs into a P tab; P passes the EL nets to K at K's existing sites
    rot = params['el_rail_rotation']
    for k, (h, a, b) in enumerate(sorted(el_harnesses, key=lambda t: t[1]['center_mm'][0] if t[1]['board'] == 'EL' else t[2]['center_mm'][0])):
        el_con, k_con = (a, b) if a['board'] == 'EL' else (b, a)
        signals = [x for x in ordered_pins(el_con['pin_map']) if x not in ('AGND', 'NC') + RAIL_NETS]
        egh, kgh = gh('EL', el_con['pcb_reference']), gh('K', k_con['pcb_reference'])
        pins, _, _ = fill_template(templates['EL/P'], signals, rot[k % len(rot)])
        front = make_site('EL', el_con['side'], el_con['center_mm'], el_con['pcb_reference'], egh, long_axis_x(egh))
        back = make_site('P', 'F.Cu', el_con['center_mm'], None, None, long_axis_x(egh))
        add_pair('EL-P-%s' % h['id'].split('-')[-1], 'EL/P', front, back, positions['EL/P'], pins, gaps['EL/P'],
                 h['id'], 'EL takes its rails from P; rails rotate over sites (planning assumption)')
        pins2, _, _ = fill_template(templates['P/K for EL'], signals)
        front2 = make_site('P', 'B.Cu', el_con['center_mm'], None, None, long_axis_x(egh))
        back2 = make_site('K', k_con['side'], k_con['center_mm'], k_con['pcb_reference'], kgh, long_axis_x(kgh))
        add_pair('P-K-%s' % h['id'].split('-')[-1], 'P/K for EL', front2, back2, positions['P/K for EL'], pins2,
                 gaps['P/K'], h['id'], 'pass-through: EL nets carried EL to K through P')

    # ---------------------------------------------------------- obstacles
    model = params['obstacle_model']
    if obstacles is None:
        obstacles = sg.stack_obstacles(ci)
    obs_k, obs_p = obstacles['K'], obstacles['P']

    # ---------------------------------------------------------- control tabs and SUB toggles
    sub = params['sub_toggle']
    toggle = next(f for f in sorted(ci['boards'][sub['reuse_board']], key=lambda f: f['ref'])
                  if f['value'] == sub['reuse_value'] and f['angle'] == 0)
    rows = {r['block']: r for r in ci['lock']['octave_rows']}
    selectors = []
    for blk, r in rows.items():
        if blk in retired:
            continue
        f = fps[blk][r['ref']]
        selectors.append({'block': blk, 'ref': r['ref'], 'courtyard': f['courtyard']})
    m = params['tab_edge_margin_mm']
    step = params['window_step_mm']
    pad_g = model['opposite_face_through_hole_pad_growth_mm']
    w_sub = max(sg.envelope(land, positions['SUB'], 'front')[0], sg.envelope(land, positions['SUB'], 'K')[0])
    l_sub = max(sg.envelope(land, positions['SUB'], 'front')[1], sg.envelope(land, positions['SUB'], 'K')[1])
    control_tabs = []
    sub_sites = []
    k_conn_centres = {c['pcb_reference']: c['center_mm'] for c in part['connectors'] if c['board'] == 'K'}
    for blk in sub['retired_selectors']:
        r = rows[blk]
        cx, cy = r['x_mm'], r['y_mm']
        dx, dy = cx - toggle['origin'][0], cy - toggle['origin'][1]
        t_cy = [round(toggle['courtyard'][0] + dx, 4), round(toggle['courtyard'][1] + dy, 4),
                round(toggle['courtyard'][2] + dx, 4), round(toggle['courtyard'][3] + dy, 4)]
        t_pads = [[round(p['bbox'][0] + dx, 4), round(p['bbox'][1] + dy, 4), round(p['bbox'][2] + dx, 4),
                   round(p['bbox'][3] + dy, 4)] for p in toggle['pads']]
        t_pads_g = [sg.grow(p, pad_g) for p in t_pads]
        left = max(s['courtyard'][2] for s in selectors if s['courtyard'][2] <= cx)
        right = min(s['courtyard'][0] for s in selectors if s['courtyard'][0] >= cx)
        p_edge = p_edge_y(bidx['P']['outline'], cx)
        tab_x = [round(left + m, 4), round(right - m, 4)]
        ys = sg.frange(cy - 15, cy + 15, step)
        both, p_only, k_only = [], [], []
        k_block = {}
        for y in ys:
            rect = sg.env_rect(cx, y, w_sub, l_sub, True)
            if rect[0] < tab_x[0] + m - 1e-9 or rect[2] > tab_x[1] - m + 1e-9:
                continue
            p_ok = not any(sg.inter(rect, t) for t in t_pads_g) and not obs_p.hits('B', rect)
            kh = obs_k.hits('F', rect)
            if p_ok:
                p_only.append(y)
            if not kh:
                k_only.append(y)
            else:
                k_block[y] = kh
            if p_ok and not kh:
                both.append(y)
        win = sg.runs(both, step)
        above = [w for w in win if w[1] < cy]
        if not above:
            raise ValueError('fit conflict: no SUB pair position above the toggle at %s for a %s x %s mm envelope; '
                             'windows found: %s' % (blk, w_sub, l_sub, win))
        wmin, wmax = above[-1]
        site_y = round(round(((wmin + wmax) / 2) / step) * step, 4)
        tab_top = round(site_y - w_sub / 2 - m, 4)
        below_p = [y for y in p_only if y > cy]
        below_k = [y for y in k_only if y > cy]
        first_p = below_p[0] if below_p else None
        nearest = None
        if first_p is not None and below_k:
            cand = [(abs(a - b), a, b) for a in below_p for b in below_k if abs(a - b) < 3]
            if cand:
                d, a, b = min(cand)
                nearest = {'miss_mm': round(d, 4), 'p_clear_centre_y': a, 'k_free_centre_y': b,
                           'k_blockers_at_p_centre': sorted({ref for ref, _ in k_block.get(a, [])})}
        retired_overlap = []
        for kref in sorted(x for x in retired_items['K_headers'] if x in k_conn_centres):
            kx, ky = k_conn_centres[kref]
            if abs(kx - cx) > sg.OFFSET_TOL_MM:
                continue
            rect = sg.env_rect(cx, ky, w_sub, l_sub, True)
            depth = max([sg.overlap_depth(rect, t) for t in t_pads_g if sg.inter(rect, t)] or [0])
            retired_overlap.append({'retired_K_header': kref, 'centre_y': ky, 'toggle_pad_clearance_overlap_mm': round(depth, 4)})
        tab = [tab_x[0], tab_top, tab_x[1], p_edge]
        control_tabs.append({'id': 'TAB-CONTROL-' + blk, 'block': blk, 'rect': tab, 'board': 'P',
                             'basis': 'x: neighbouring selector courtyards less the edge margin; top: SUB site less half the envelope and the edge margin; bottom: P edge'})
        sub_sites.append({'block': blk, 'uid': r['uid'], 'toggle_centre': [cx, cy], 'toggle_value': sub['reuse_value'], 'toggle_lib': toggle['lib'],
                          'toggle_courtyard': t_cy, 'toggle_pads': t_pads,
                          'corridor_x': [left, right], 'corridor_mm': round(right - left, 4),
                          'toggle_margins_mm': [round(t_cy[0] - left, 4), round(right - t_cy[2], 4)],
                          'window_centre_y': [wmin, wmax], 'window_mm': round(wmax - wmin, 4),
                          'all_windows': win, 'site_centre': [cx, site_y], 'below_toggle': nearest,
                          'retired_header_overlap': retired_overlap})
        pins, _, _ = fill_template(templates['SUB'], ['%s:%s' % (blk, n) for n in sub['select_nets']])
        front = make_site('P', 'B.Cu', [cx, site_y], None, None, True)
        back = make_site('K', 'F.Cu', [cx, site_y], None, None, True)
        add_pair('P-K-SUB-' + blk, 'SUB', front, back, positions['SUB'], pins, gaps['P/K'], None,
                 'new control; pin map is a planning assumption (ST-06)')

    # ---------------------------------------------------------- power posts and power tab
    terms = {t['reference']: t for t in part['load_side_terminals']}
    posts = []
    moved = []
    for w in part['load_side_wires']:
        ta, tb = [terms[r] for r in w['terminal_refs']]
        kt, ft = (ta, tb) if ta['board'] == 'K' else (tb, ta)
        off = round(((kt['center_mm'][0] - ft['center_mm'][0]) ** 2 + (kt['center_mm'][1] - ft['center_mm'][1]) ** 2) ** 0.5, 4)
        post = {'id': w['id'], 'net': w['net'], 'front_board': ft['board'], 'front_land': ft['center_mm'],
                'front_ref': ft['reference'], 'K_land': kt['center_mm'], 'K_ref': kt['reference'],
                'present_offset_mm': off, 'land_courtyard_mm': ft['maximum_courtyard_mm'],
                'proposed_front_land': ft['center_mm'], 'resolved_by': None}
        if off > sg.OFFSET_TOL_MM:
            post['proposed_front_land'] = kt['center_mm']
            post['resolved_by'] = 'TAB-POWER'
            moved.append(post)
        posts.append(post)
    tabs = list(control_tabs)
    if moved:
        xs = [p['K_land'][0] for p in moved]
        ys = [p['K_land'][1] for p in moved]
        cw, ch = moved[0]['land_courtyard_mm']
        x0 = round(min(xs) - cw / 2 - m, 4)
        x1 = round(max(xs) + cw / 2 + m, 4)
        top = round(min(ys) - ch / 2 - m, 4)
        tabs.append({'id': 'TAB-POWER', 'rect': [x0, top, x1, p_edge_y(bidx['P']['outline'], (x0 + x1) / 2)], 'board': 'P',
                     'basis': 'moved P land courtyards at the K land centres plus the edge margin, to the P edge'})

    # ---------------------------------------------------------- EL tab
    el_sites = [p for p in pairs if p['family'] == 'EL/P']
    rects = []
    for p in el_sites:
        cx, cy = p['sites']['front']['center']
        for half, fam in (('front', 'EL/P'), ('K', 'EL/P'), ('front', 'P/K for EL'), ('K', 'P/K for EL')):
            w, l = sg.envelope(land, positions[fam], half)
            rects.append(sg.env_rect(cx, cy, w, l, p['sites']['front']['long_axis_x']))
    x0 = round(min(r[0] for r in rects) - m, 4)
    x1 = round(max(r[2] for r in rects) + m, 4)
    top = round(min(r[1] for r in rects) - m, 4)
    el_tab = {'id': 'TAB-EL', 'rect': [x0, top, x1, p_edge_y(bidx['P']['outline'], (x0 + x1) / 2)], 'board': 'P',
              'basis': 'six EL site envelopes (both pairs, both halves) plus the edge margin, to the P edge'}
    tabs.insert(0, el_tab)
    pass_holes = []
    for s in part['supports']:
        x, y = s['position_mm']
        for t in tabs:
            r = t['rect']
            if r[0] < x < r[2] and r[1] < y < r[3]:
                pass_holes.append({'tab': t['id'], 'support': s['id'], 'board': s['board'], 'position': s['position_mm']})
    for t in tabs:
        t['pass_through_supports'] = [h['support'] for h in pass_holes if h['tab'] == t['id']]
        t['carried_posts'] = [p['id'] for p in posts if p['resolved_by'] == t['id']]

    # ---------------------------------------------------------- declared courtyard-level blockers
    for p in pairs:
        for half_name, half in (('front', 'front'), ('back', 'K')):
            s = p['sites'][half_name]
            w, l = sg.envelope(land, p['positions'], half)
            rect = sg.env_rect(s['center'][0], s['center'][1], w, l, s['long_axis_x'])
            s['envelope'] = rect
            skip = {s['replaces']} if s['replaces'] else set()
            s['blockers'] = [list(x) for x in obstacles[s['board']].hits(s['side'][0], rect, skip)]

    retired_items['K_service_apertures'] = len(part['K_service_apertures'])
    retired_items['K_service_aperture_footprints'] = sorted(f['ref'] for f in ci['boards']['K'] if f['ref'].startswith('MH_K-SERVICE'))
    retired_items['K_headers'] = sorted(retired_items['K_headers'])
    retired_items['front_headers'] = sorted(retired_items['front_headers'])
    retired_items['selectors'] = sorted(rows[b]['uid'] for b in sub['retired_selectors'])

    return {
        'schema_version': 1,
        'status': 'GENERATED PLANNING CANDIDATE; courtyard-and-pad level; unvalidated draft; not adopted',
        'stack': stack,
        'planes': planes,
        'pairs': sorted(pairs, key=lambda p: p['id']),
        'posts': posts,
        'tabs': tabs,
        'sub_toggles': sub_sites,
        'selectors_kept': selectors,
        'retired': retired_items,
        'land_pattern': {'source': land['source'], 'status': land['status'],
                         'envelopes_mm': {half: {str(n): list(sg.envelope(land, n, half)) for n in sorted(set(positions.values()))}
                                          for half in ('front', 'K')}},
    }


def generate(root=sg.ROOT):
    raw = sg.load_raw(root)
    boards = sg.load_boards(raw, root)
    ci = sg.canonical_inputs(raw, boards)
    candidate = build(ci)
    out = {
        'provenance': {
            'generator': 'scripts/stack/geometry/generate.py',
            'regenerate': sg.REGEN_COMMAND,
            'input_sha256': sg.input_hashes(root),
            'board_checkpoint_match': checkpoint_match(raw, root),
        },
        'canonical_input_digest': sg.canonical_digest(ci),
        'canonical_input_scope': 'footprint reference, library, side, origin, angle, courtyard box and pad geometry of every board; the partition, lock, mechanical and parameter fields listed in stackgeom.canonical_inputs. Tracks, vias, zones and nets are excluded',
        'candidate': candidate,
    }
    return out, ci


def checkpoint_match(raw, root):
    res = {}
    for key, b in raw['checkpoint']['boards'].items():
        path = b.get('board')
        if not path:
            continue
        actual = sg.sha256_file(sg.Path(root) / path)
        succ = b.get('metadata_successor', {}).get('successor_board_sha256')
        res[path] = ('checkpoint board_sha256' if actual == b.get('board_sha256') else
                     'checkpoint metadata successor' if actual == succ else 'DIFFERS from checkpoint')
    for key, path in sg.BOARD_FILES.items():
        res.setdefault(path, 'not covered by the checkpoint')
    return res


def render(out):
    """The tracked file text; it depends on the inputs only, never on the commit or the clock."""
    return json.dumps(out, indent=1, sort_keys=False) + '\n'


def main(argv):
    out, _ = generate()
    text = render(out)
    if '--stdout' in argv:
        sys.stdout.write(text)
    else:
        sg.CANDIDATE.write_text(text)
        print('wrote', sg.CANDIDATE.relative_to(sg.ROOT), 'digest', out['canonical_input_digest'][:16])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
