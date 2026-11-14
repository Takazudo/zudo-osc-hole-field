"""Flat-link option study (ST-02 attempt a4): clusters, connector fields and slots in K per link size and ground rule.

    python3 scripts/stack/geometry/links.py [--stdout]

Reads the retained rigid candidate (design/stack/geometry/stack-candidate.json), the board files through the
existing extract, and design/stack/geometry/links/link-options.json. Writes link-candidate.json and README.md
beside the options. Courtyard level only: nothing here is a copper clearance, a tolerance result or a fit, and
nothing is selected.
"""
import json
import math
import sys
from pathlib import Path

import stackgeom as sg

LINK_DIR = sg.OUT_DIR / 'links'
OPTIONS = LINK_DIR / 'link-options.json'
LINK_CANDIDATE = LINK_DIR / 'link-candidate.json'
LINK_README = LINK_DIR / 'README.md'
LINK_P_SMALL = LINK_DIR / 'link-candidate-p-small.json'
REGEN = 'python3 scripts/stack/geometry/links.py'
PROGRAM = ['scripts/stack/geometry/links.py', 'scripts/stack/geometry/links_readme.py', 'scripts/stack/geometry/stackgeom.py',
           'scripts/stack/geometry/kicad_extract.py']
FRONTS = ('JL', 'JR', 'P')
LINK_FAMILIES = {'JL/K': 'JL-K', 'JR/K': 'JR-K', 'K/P': 'P-K', 'P/K for EL': 'P-K', 'SUB': 'P-K',
                 'JL/P pass-through': 'JL-P via K'}
JOINTS = ('JL-K', 'JR-K', 'P-K', 'JL-P via K')
NON_SIGNAL = ('AGND', 'NC', '+12V', '-12V', '+5V')
PANEL_KINDS = ('jack', 'led', 'pot', 'switch', 'button')
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIR_NAMES = {(1, 0): '+x', (-1, 0): '-x', (0, 1): '+y', (0, -1): '-y'}


def r4(v):
    return round(v + 0.0, 4)


def val(entry):
    return entry['value'] if isinstance(entry, dict) else entry


# ---------------------------------------------------------------- inputs

def load_inputs(root=sg.ROOT):
    raw = sg.load_raw(root)
    boards = sg.load_boards(raw, root)
    ci = sg.canonical_inputs(raw, boards)
    cand = json.loads((Path(root) / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    opts = json.loads((Path(root) / 'design/stack/geometry/links/link-options.json').read_text())
    return {'raw': raw, 'ci': ci, 'cand': cand, 'opts': opts, 'root': Path(root)}


def input_hashes(root):
    paths = ['design/stack/geometry/stack-candidate.json', 'design/stack/geometry/links/link-options.json',
             'design/stack/geometry/check-report.json',
             'design/stack/geometry/parameters.json', sg.JSON_FILES['partition'], sg.JSON_FILES['lock']]
    paths += [sg.BOARD_FILES[k] for k in ('K', 'JL', 'JR', 'P')] + PROGRAM
    return {p: sg.sha256_file(Path(root) / p) for p in sorted(paths)}


def link_sites(cand):
    """The 191 K pairs that go to links (every K pair except the six adapter pairs)."""
    out = []
    for p in sorted(cand['pairs'], key=lambda q: q['id']):
        if p['family'] not in LINK_FAMILIES:
            continue
        f, b = p['sites']['front'], p['sites']['back']
        out.append({'id': p['id'], 'family': p['family'], 'joint': LINK_FAMILIES[p['family']],
                    'front_board': f['board'], 'xy': [f['center'][0], f['center'][1]], 'K_xy': b['center'],
                    'positions': p['positions'], 'signals': [s for s in p['pin_map'] if s not in NON_SIGNAL],
                    'front_replaces': f['replaces'], 'K_replaces': b['replaces']})
    return out


def site_counts(sites):
    fam = {}
    for s in sites:
        e = fam.setdefault(s['family'], {'pairs': 0, 'positions': 0, 'signals': 0})
        e['pairs'] += 1
        e['positions'] += s['positions']
        e['signals'] += len(s['signals'])
    top = {}
    for s in sites:
        top[s['family']] = max(top.get(s['family'], 0), len(s['signals']))
    short = [{'site': s['id'], 'family': s['family'], 'signals': s['signals'], 'family_maximum': top[s['family']]}
             for s in sites if len(s['signals']) < top[s['family']]]
    return {'pairs': len(sites), 'positions': sum(s['positions'] for s in sites),
            'signals': sum(len(s['signals']) for s in sites), 'by_family': dict(sorted(fam.items())),
            'sites_below_family_maximum': short}


# ---------------------------------------------------------------- capacity and clustering

def capacity(n, rule):
    s = 0
    if rule == 'G-PER-2S':
        while (s + 1) + math.ceil((s + 1) / 2) <= n:
            s += 1
    elif rule == 'G-BETWEEN':
        while 2 * (s + 1) - 1 <= n:
            s += 1
    else:
        raise ValueError('unknown ground rule ' + rule)
    return s


def grounds_for(s, rule):
    return math.ceil(s / 2) if rule == 'G-PER-2S' else max(s - 1, 0)


def _centroid(items):
    return (sum(i['xy'][0] for i in items) / len(items), sum(i['xy'][1] for i in items) / len(items))


def cluster(sites, cap, weight, join_radius):
    """Deterministic greedy clustering of sites per (joint, front board) under a capacity in `weight` units."""
    groups = {}
    for s in sites:
        groups.setdefault((s['joint'], s['front_board']), []).append(s)
    out = []
    for (joint, front) in sorted(groups, key=lambda k: (JOINTS.index(k[0]), k[1])):
        rem = sorted(groups[(joint, front)], key=lambda s: s['id'])
        k = 0
        while rem:
            cx, cy = _centroid(rem)
            seed = min(rem, key=lambda s: (-round(math.hypot(s['xy'][0] - cx, s['xy'][1] - cy), 6), s['id']))
            if weight(seed) > cap:
                raise ValueError('site %s exceeds the link capacity %s' % (seed['id'], cap))
            members = [seed]
            rem.remove(seed)
            load = weight(seed)
            while True:
                mx, my = _centroid(members)
                cands = [(round(math.hypot(s['xy'][0] - mx, s['xy'][1] - my), 6), s['id'], s) for s in rem
                         if load + weight(s) <= cap]
                cands = [c for c in cands if c[0] <= join_radius]
                if not cands:
                    break
                _, _, s = min(cands, key=lambda c: (c[0], c[1]))
                members.append(s)
                rem.remove(s)
                load += weight(s)
            k += 1
            mx, my = _centroid(members)
            out.append({'id': '%s-%s-L%02d' % (joint.replace(' ', '').replace('via', '-'), front, k), 'joint': joint,
                        'front_board': front, 'centre': [r4(mx), r4(my)], 'load': load,
                        'members': sorted(s['id'] for s in members),
                        'site_distances_mm': sorted(r4(math.hypot(s['xy'][0] - mx, s['xy'][1] - my)) for s in members)})
    return out


def cluster_summary(links, sites, cap, weight):
    out = {}
    for joint in JOINTS:
        ls = [l for l in links if l['joint'] == joint]
        ss = [s for s in sites if s['joint'] == joint]
        d = [x for l in ls for x in l['site_distances_mm']]
        by_front = {}
        for s in ss:
            by_front[s['front_board']] = by_front.get(s['front_board'], 0) + weight(s)
        out[joint] = {'sites': len(ss), 'links': len(ls),
                      'lower_bound': sum(math.ceil(v / cap) for v in by_front.values()),
                      'lower_bound_whole_joint': math.ceil(sum(by_front.values()) / cap),
                      'mean_site_distance_mm': r4(sum(d) / len(d)) if d else None,
                      'max_site_distance_mm': max(d) if d else None}
    return out


# ---------------------------------------------------------------- obstacle model

class Model:
    """Per board face: displacement obstacles (counted) and forbidden items (never entered)."""

    def __init__(self, inp, sites):
        ci, cand = inp['ci'], inp['cand']
        params = ci['parameters']
        opts = inp['opts']
        self.margin = val(opts['board_edge_margin_mm'])
        self.outline = {b['board_key']: b['outline'] for b in ci['partition']['boards']}
        lock = inp['raw']['lock']['placements']
        self.panel = {k: {r['ref'] for r in lock if r['kind'] in PANEL_KINDS and r.get('domain') == k} for k in FRONTS}
        drop = {'K': set(sg.retired_k_headers(ci)) | {s['K_replaces'] for s in sites if s['K_replaces']}}
        retired_front = set(cand['retired']['front_headers'])
        for k in FRONTS:
            drop[k] = retired_front | {s['front_replaces'] for s in sites if s['front_replaces'] and s['front_board'] == k}
        self.dropped = {k: sorted(v) for k, v in drop.items()}
        model = params['obstacle_model']
        self.post_refs = {p['K_ref'] for p in cand['posts']} | {p['front_ref'] for p in cand['posts']}
        self.disp = {}
        self.forb = {}
        for key in ('K',) + FRONTS:
            obs = sg.Obstacles(ci['boards'][key], model, drop=frozenset(drop[key]),
                               skip_hole=lambda f: f['ref'].startswith('MH_K-SERVICE'))
            for face in 'FB':
                d, fb = sg.RectIndex(), sg.RectIndex()
                for rect, (ref, kind) in obs.index[face].items:
                    if kind == 'hole' or ref in self.panel.get(key, ()):
                        fb.add(rect, ('rect', rect, '%s %s' % ('panel hardware' if kind != 'hole' else 'hole', ref)))
                    elif ref in self.post_refs:
                        continue  # covered by the post keep-out circle
                    else:
                        d.add(rect, (ref, kind))
                self.disp[(key, face)] = d
                self.forb[(key, face)] = fb
        kr = opts['fixing_keepout_radius_mm']['K']
        fr = opts['fixing_keepout_radius_mm']['front']
        self.fixings = []
        posts = {p['id']: p for p in cand['posts']}
        for f in cand['fixings']:
            if not f['declared']:
                continue
            k_xy = f['xy']
            front_xy = posts[f['id']]['proposed_front_land'] if f['id'] in posts else f['xy']
            self.fixings.append({'id': f['id'], 'K': k_xy, 'front': front_xy, 'front_board': f['front_board']})
            for face in 'FB':
                self._circle('K', face, k_xy, kr, 'fixing keep-out %s' % f['id'])
            if f['front_board'] in FRONTS:
                for face in 'FB':
                    self._circle(f['front_board'], face, front_xy, fr, 'fixing keep-out %s' % f['id'])
        for t in cand['tabs']:
            for face in 'FB':
                self.forb[('P', face)].add(t['rect'], ('rect', t['rect'], 'tab %s' % t['id']))
        g = model['opposite_face_through_hole_pad_growth_mm']
        for s in cand['sub_toggles']:
            self.forb[('P', 'F')].add(s['toggle_courtyard'], ('rect', s['toggle_courtyard'], 'SUB toggle %s' % s['block']))
            for pad in s['toggle_pads']:
                r = sg.grow(pad, g)
                self.forb[('P', 'B')].add(r, ('rect', r, 'SUB toggle %s pins' % s['block']))
        # items between the front boards and K that a cable or slot may not pass: adapters and kept selectors
        self.between = []
        for key in ('O1', 'O3', 'O5'):
            ol = self.outline[key]
            r = sg.grow([min(p[0] for p in ol), min(p[1] for p in ol), max(p[0] for p in ol), max(p[1] for p in ol)], self.margin)
            self.between.append((r, 'adapter %s outline (kept rigid pairs)' % key))
        for s in cand['selectors_kept']:
            self.between.append((s['courtyard'], 'kept selector %s envelope' % s['ref']))
        for p in cand['pairs']:
            if p['family'].startswith('K/O'):
                env = p['sites']['back']['envelope']
                self.forb[('K', 'F')].add(env, ('rect', env, 'kept rigid pair %s' % p['id']))

    def _circle(self, key, face, xy, r, label):
        self.forb[(key, face)].add(sg.circle_rect(xy[0], xy[1], 2 * r), ('circle', (xy[0], xy[1], r), label))

    def forbidden(self, key, face, rect, tail=False):
        """(label, penetration) of the deepest forbidden item the rectangle enters, or None.

        With tail=True panel-hardware pins are left out: whether a pin stands higher than the cable is a height
        question with no retained protrusion, so those crossings are listed, not screened."""
        worst = None
        for _, (kind, geo, label) in self.forb[(key, face)].near(rect):
            if tail and label.startswith('panel hardware'):
                continue
            if kind == 'rect':
                if not sg.inter(rect, geo):
                    continue
                d = sg.overlap_depth(rect, geo)
            else:
                d = sg.circle_rect_depth(geo[0], geo[1], geo[2], rect)
                if d <= 1e-9:
                    continue
            if worst is None or d > worst[1]:
                worst = (label, r4(d))
        return worst

    def between_hit(self, rect):
        for r, label in self.between:
            if sg.inter(rect, r):
                return (label, r4(sg.overlap_depth(rect, r)))
        return None

    def displaced(self, key, face, rect):
        return {payload[0] for r, payload in self.disp[(key, face)].near(rect) if sg.inter(rect, r)}


# ---------------------------------------------------------------- geometry of one link

def oriented_rect(sx, sy, d, t0, t1, half):
    """Axis-aligned rectangle spanning t0..t1 along direction d from (sx, sy) and +-half across."""
    if d[0]:
        xs = sorted((sx + d[0] * t0, sx + d[0] * t1))
        return [r4(xs[0]), r4(sy - half), r4(xs[1]), r4(sy + half)]
    ys = sorted((sy + d[1] * t0, sy + d[1] * t1))
    return [r4(sx - half), r4(ys[0]), r4(sx + half), r4(ys[1])]


def link_geometry(sx, sy, d, size, opts):
    L = val(size['field_length_mm'])
    D = val(size['field_depth_mm'])
    W = val(size['tail_width_mm'])
    sl = opts['slot']
    half_slot = val(sl['length_mm']) / 2
    a = val(opts['cable']['straight_stiffened_outside_mm']) + val(opts['cable']['bend_radius_mm'])
    return {
        'slot': oriented_rect(sx, sy, d, -half_slot, half_slot, (W + val(sl['width_extra_mm'])) / 2),
        'front_connector': oriented_rect(sx, sy, d, -(a + D), -a, L / 2),
        'front_tail': oriented_rect(sx, sy, d, -a, -half_slot, W / 2),
        'K_tail': oriented_rect(sx, sy, d, half_slot, a, W / 2),
        'K_connector': oriented_rect(sx, sy, d, a, a + D, L / 2),
        'a_mm': r4(a), 'b_mm': r4(a),
    }


def cable_needed(a, b, gap, k_thickness, opts):
    c = opts['cable']
    R = val(c['bend_radius_mm'])
    return r4(2 * val(c['insertion_depth_mm']) + a + b + gap + k_thickness + (math.pi - 4) * R)


# ---------------------------------------------------------------- placement

class Placed:
    def __init__(self):
        self.idx = {}

    def add(self, key, face, rect, label):
        self.idx.setdefault((key, face), sg.RectIndex()).add(rect, label)

    def hit(self, key, face, rect, grow_by=0.0):
        idx = self.idx.get((key, face))
        if not idx:
            return None
        g = sg.grow(rect, grow_by)
        for r, label in idx.near(g):
            if sg.inter(g, r):
                return (label, r4(sg.overlap_depth(g, r)))
        return None


def add_placed(placed, front, geo, lid):
    placed.add(front, 'B', geo['front_connector'], 'front field of ' + lid)
    placed.add(front, 'B', geo['front_tail'], 'front tail of ' + lid)
    placed.add('K', 'B', geo['K_connector'], 'K field of ' + lid)
    placed.add('K', 'B', geo['K_tail'], 'K tail of ' + lid)
    placed.add('K', 'S', geo['slot'], 'slot of ' + lid)
    placed.add('K', 'B', geo['slot'], 'slot of ' + lid)


def evaluate(model, placed, front, geo, web):
    """(reason, depth) when illegal, else None; and the displaced refs per board face.

    Connector courtyards, the slot with its web and both stiffened tails are screened against the forbidden items
    (a tail: holes, fixing keep-outs, tabs, SUB toggles and kept rigid pairs on its face; the front tail also against
    the adapters and kept selectors between the boards). Panel pins and other parts under a tail are only listed."""
    mg = model.margin
    fc, kc, slot = geo['front_connector'], geo['K_connector'], geo['slot']
    if not sg.rect_inside_poly(fc, model.outline[front], mg):
        return ('front field outside the %s outline less %.2f mm' % (front, mg), None), None
    if not sg.rect_inside_poly(slot, model.outline['K'], web):
        return ('slot within %.1f mm of the K edge or outside K' % web, None), None
    if not sg.rect_inside_poly(kc, model.outline['K'], mg):
        return ('K field outside the K outline less %.2f mm' % mg, None), None
    for rect, key, face, what in ((fc, front, 'B', 'front field'), (kc, 'K', 'B', 'K field'),
                                  (sg.grow(slot, web), 'K', 'F', 'slot web'),
                                  (sg.grow(slot, web), 'K', 'B', 'slot web')):
        h = model.forbidden(key, face, rect)
        if h:
            return ('%s on %s' % (what, h[0]), h[1]), None
    for rect, key, what in ((geo['front_tail'], front, 'front tail'), (geo['K_tail'], 'K', 'K tail')):
        h = model.forbidden(key, 'B', rect, tail=True)
        if h:
            return ('%s on %s' % (what, h[0]), h[1]), None
    for rect, what in ((slot, 'slot'), (fc, 'front field'), (geo['front_tail'], 'front tail')):
        h = model.between_hit(rect)
        if h:
            return ('%s under %s' % (what, h[0]), h[1]), None
    for rect, key, face, g, what in ((fc, front, 'B', 0.0, 'front field'), (geo['front_tail'], front, 'B', 0.0, 'front tail'),
                                     (kc, 'K', 'B', 0.0, 'K field'), (geo['K_tail'], 'K', 'B', 0.0, 'K tail'),
                                     (slot, 'K', 'S', web, 'slot web'), (slot, 'K', 'B', 0.0, 'slot')):
        h = placed.hit(key, face, rect, g)
        if h:
            return ('%s on %s' % (what, h[0]), h[1]), None
    if placed.hit('K', 'S', kc) or placed.hit('K', 'S', geo['K_tail']):
        return ('K field or tail on another slot', None), None
    disp = {'front B': sorted(model.displaced(front, 'B', fc)),
            'K F (slot)': sorted(model.displaced('K', 'F', slot)),
            'K B (slot)': sorted(model.displaced('K', 'B', slot)),
            'K B (field)': sorted(model.displaced('K', 'B', kc))}
    return None, disp


def under_tails(model, front, geo):
    """Footprints and panel pins under the two tail runs (listed only; heights NOT RUN)."""
    out = {}
    for key, rect, name in ((front, geo['front_tail'], 'front tail'), ('K', geo['K_tail'], 'K tail')):
        refs = set(model.displaced(key, 'B', rect))
        refs |= {lab.split(' ')[-1] for _, (kind, g, lab) in model.forb[(key, 'B')].near(rect)
                 if kind == 'rect' and lab.startswith('panel hardware') and sg.inter(rect, g)}
        out[name] = sorted(refs)
    return out


def search_offsets(opts):
    srch = opts['search']
    step, rad = val(srch['step_mm']), val(srch['radius_mm'])
    n = int(round(rad / step))
    return sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)
                   if math.hypot(i * step, j * step) <= rad + 1e-9),
                  key=lambda o: (round(math.hypot(*o), 6), o))


def search_link(model, placed, link, size, opts, offsets):
    """The cheapest legal candidate of one link against the placed set, or None; and the rejection tally."""
    w = val(opts['search']['distance_weight_per_mm'])
    web = val(opts['slot']['web_mm'])
    cx, cy = link['centre']
    best = None
    why_tally = {}
    for off in offsets:
        dist = math.hypot(*off)
        if best is not None and w * dist > best[0] + 1e-9:
            break
        sx, sy = r4(cx + off[0]), r4(cy + off[1])
        for di, d in enumerate(DIRS):
            geo = link_geometry(sx, sy, d, size, opts)
            why, disp = evaluate(model, placed, link['front_board'], geo, web)
            if why:
                if best is None:
                    t = why_tally.setdefault(why[0], [0, None])
                    t[0] += 1
                    if why[1] is not None and (t[1] is None or why[1] < t[1]):
                        t[1] = why[1]
                continue
            k_refs = set(disp['K F (slot)']) | set(disp['K B (slot)']) | set(disp['K B (field)'])
            cost = len(disp['front B']) + len(k_refs) + w * dist
            key = (round(cost, 6), round(dist, 6), di, sx, sy)
            if best is None or key < best[1]:
                best = (cost, key, geo, disp, d, (sx, sy), dist)
    return best, why_tally


def place_links(model, links, sizes, opts, cand):
    """`sizes` maps each joint to its link size."""
    web = val(opts['slot']['web_mm'])
    offsets = search_offsets(opts)
    gaps = cand['stack']['mated_heights_mm']
    k_th = round(cand['stack']['K_face_z_mm'] - cand['stack']['K_rear_z_mm'], 4)
    placed = Placed()
    access_margin = val(opts['latch_access_margin_mm'])
    out = []
    for link in links:
        size = sizes[link['joint']]
        best, why_tally = search_link(model, placed, link, size, opts, offsets)
        rec = dict(link)
        if best is None:
            rec['placed'] = False
            rec['blocked_at_centre'] = blocked_reasons(model, placed, link, size, opts, web)
            inside = {k: v for k, v in why_tally.items() if 'outline' not in k and 'K edge' not in k}
            top = sorted(inside.items(), key=lambda kv: (-kv[1][0], kv[0]))[:3]
            rec['blocked_in_search'] = {'candidates': len(offsets) * len(DIRS),
                                        'outside_a_board_or_edge_web': sum(v[0] for k, v in why_tally.items() if k not in inside),
                                        'most_frequent': [{'blocker': k, 'candidates': v[0], 'smallest_penetration_mm': v[1]}
                                                          for k, v in top]}
            out.append(rec)
            continue
        _, _, geo, disp, d, (sx, sy), dist = best
        front = link['front_board']
        add_placed(placed, front, geo, link['id'])
        gap = gaps[front + '/K']
        rec.update({'placed': True, 'slot_centre': [sx, sy], 'direction': DIR_NAMES[d],
                    'slot_distance_from_centre_mm': r4(dist), 'geometry': geo, 'displaced': disp,
                    'under_tails': under_tails(model, front, geo),
                    'cable_needed_mm': cable_needed(geo['a_mm'], geo['b_mm'], gap, k_th, opts)})
        out.append(rec)
    # latch reach after all links are placed: K-rear footprints next to a K connector that no link displaces
    all_disp = {x for r in out if r['placed'] for v in r['displaced'].values() for x in v}
    for r in out:
        if not r['placed']:
            continue
        zone = sg.grow(r['geometry']['K_connector'], access_margin)
        near = sorted(model.displaced('K', 'B', zone) - all_disp)
        r['latch_reach'] = {'neighbours_within_margin': near,
                            'verdict': 'open' if not near else 'NOT SHOWN (neighbour heights not retained)'}
    return out


def blocked_reasons(model, placed, link, size, opts, web):
    """Why the link has no legal place: the shallowest blocker at the link centre, per direction."""
    cx, cy = link['centre']
    out = []
    for d in DIRS:
        geo = link_geometry(r4(cx), r4(cy), d, size, opts)
        why, _ = evaluate(model, placed, link['front_board'], geo, web)
        out.append({'direction': DIR_NAMES[d], 'blocker': why[0] if why else 'none at the centre (blocked elsewhere)',
                    'penetration_mm': why[1] if why else None})
    return out


# ---------------------------------------------------------------- results

def option_result(model, sites, size, rule, opts, cand, post_k, rigid_criterion, by_joint=None, joints=JOINTS, label=None):
    """One option: `size` for every joint unless `by_joint` names another size for a joint; only `joints` are run."""
    n = size['circuits']
    cap = capacity(n, rule)
    sizes = {j: (by_joint or {}).get(j, size) for j in joints}
    sites = [s for s in sites if s['joint'] in joints]
    weight = lambda s: len(s['signals'])  # noqa: E731
    links = []
    lower = {}
    for j in joints:
        jc = capacity(sizes[j]['circuits'], rule)
        js = [s for s in sites if s['joint'] == j]
        jl = cluster(js, jc, weight, val(opts['clustering']['join_radius_mm']))
        for l in jl:
            l['signals'] = l.pop('load')
            l['grounds'] = grounds_for(l['signals'], rule)
            l['circuits_used'] = l['signals'] + l['grounds']
            l['size'] = sizes[j]['id']
            l['capacity_signals'] = jc
            l['circuits'] = sizes[j]['circuits']
        links += jl
        lower[j] = cluster_summary(jl, js, jc, weight)[j]
    placed = place_links(model, links, sizes, opts, cand)
    site_by = {s['id']: s for s in sites}
    k_area = poly_area(model.outline['K'])
    per_joint = {}
    for joint in joints:
        ls = [l for l in placed if l['joint'] == joint]
        pl = [l for l in ls if l['placed']]
        dist_field = [math.hypot(site_by[m]['xy'][0] - sg.centre(l['geometry']['front_connector'])[0],
                                 site_by[m]['xy'][1] - sg.centre(l['geometry']['front_connector'])[1])
                      for l in pl for m in l['members']]
        per_joint[joint] = {'links': len(ls), 'placed': len(pl), 'slots': len(pl),
                            'mean_site_to_field_mm': r4(sum(dist_field) / len(dist_field)) if dist_field else None,
                            'max_site_to_field_mm': r4(max(dist_field)) if dist_field else None}
    pl = [l for l in placed if l['placed']]
    slot_area = sum((l['geometry']['slot'][2] - l['geometry']['slot'][0]) * (l['geometry']['slot'][3] - l['geometry']['slot'][1]) for l in pl)
    k_slot = sorted({x for l in pl for x in l['displaced']['K F (slot)'] + l['displaced']['K B (slot)']})
    k_field = sorted({x for l in pl for x in l['displaced']['K B (field)']} - set(k_slot))
    k_f = sorted({x for l in pl for x in l['displaced']['K F (slot)']})
    k_b = sorted({x for l in pl for x in l['displaced']['K B (slot)'] + l['displaced']['K B (field)']})
    k_all = sorted(set(k_slot) | set(k_field))
    front = {b: sorted({x for l in pl if l['front_board'] == b for x in l['displaced']['front B']}) for b in FRONTS}
    nets = {b: 0 for b in FRONTS + ('K',)}
    for l in placed:
        nets[l['front_board']] += l['signals']
        nets['K'] += l['signals']
    cable = val(opts['cable']['length_mm'])
    need = [l['cable_needed_mm'] for l in pl]
    summary = {
        'option': label or '%s %s' % (size['id'], rule), 'size': size['id'], 'ground_rule': rule, 'pitch_mm': size['pitch_mm'],
        'circuits': n, 'signals_per_link': cap,
        'sizes_by_joint': {j: sizes[j]['id'] for j in joints},
        'links': len(placed), 'links_per_joint': {j: per_joint[j]['links'] for j in joints},
        'unplaced_per_joint': {j: per_joint[j]['links'] - per_joint[j]['placed'] for j in joints},
        'lower_bound_per_joint': lower,
        'placed': len(pl), 'unplaced': len(placed) - len(pl),
        'slots': len(pl), 'slot_area_mm2': r4(slot_area), 'slot_area_share_of_K_pct': r4(100 * slot_area / k_area),
        'K_displaced': {'by_slots': len(k_slot), 'by_fields_only': len(k_field), 'F.Cu': len(k_f), 'B.Cu': len(k_b),
                        'total': len(k_all), 'outside_post_keepouts': len(set(k_all) - post_k),
                        'rigid_return_criterion': rigid_criterion},
        'front_displaced': {b: len(v) for b, v in front.items()},
        'nets_rerouted': nets,
        'site_to_field_mm': {j: [per_joint[j]['mean_site_to_field_mm'], per_joint[j]['max_site_to_field_mm']] for j in joints},
        'cable_needed_mm': [min(need), max(need)] if need else None,
        'links_served_by_cable': sum(1 for x in need if x <= cable + 1e-9), 'cable_length_mm': cable,
        'latch_not_shown': sum(1 for l in pl if l['latch_reach']['verdict'] != 'open'),
    }
    detail = {'K_displaced_refs': {'by_slots': k_slot, 'by_fields_only': k_field},
              'front_displaced_refs': front, 'links': placed}
    return summary, detail


def poly_area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def post_keepout_k(root):
    rep = json.loads((Path(root) / 'design/stack/geometry/check-report.json').read_text())
    rows = rep['checks']['post_land_keepout_screen']['detail']['posts']
    return {x for r in rows for x in r['K F.Cu'] + r['K B.Cu']}


def build(inp, sizes=None, rules=None, with_p_small=True):
    cand, opts = inp['cand'], inp['opts']
    sites = link_sites(cand)
    counts = site_counts(sites)
    f4cap = opts['f4_reproduction']['capacity_positions']
    f4_links = cluster(sites, f4cap, lambda s: s['positions'], val(opts['clustering']['join_radius_mm']))
    f4 = cluster_summary(f4_links, sites, f4cap, lambda s: s['positions'])
    model = Model(inp, sites)
    post_k = post_keepout_k(inp['root'])
    st08 = sorted({x for m in cand['st08_K_part_moves_at_pass_through_sites'] for x in m['K_parts_to_move']})
    rigid = {'post_keepout_K_footprints': len(post_k), 'st08_part_moves': len(st08),
             'total': len(post_k) + len(st08),
             'basis': 'DS-41: 115 K footprints in the post keep-outs (check-report.json, union of F.Cu and B.Cu: %d) plus '
                      'the %d ST-08 part moves of attempt a3' % (len(post_k), len(st08))}
    options, details = [], {}
    for size in opts['sizes']:
        if sizes and size['id'] not in sizes:
            continue
        for rule in [g['id'] for g in opts['ground_rules']]:
            if rules and rule not in rules:
                continue
            s, d = option_result(model, sites, size, rule, opts, cand, post_k, rigid['total'])
            options.append(s)
            details[s['option']] = d
    p_small = build_p_small(model, sites, opts, cand, post_k, rigid['total'], details) \
        if with_p_small and not sizes and not rules else None
    return {
        'schema_version': 1,
        'status': 'OPTION STUDY; courtyard level; unvalidated drafts; nothing selected, adopted or bought',
        'site_counts': counts,
        'f4_reproduction': {'capacity_positions': f4cap, 'per_joint': f4,
                            'total_links': sum(v['links'] for v in f4.values()),
                            'da03_f4': DA03_F4},
        'search_parameters': search_parameters(opts, cand),
        'option_sizes': [{'id': z['id'], 'envelope': z.get('envelope'), 'stock_cable': z['stock_cable'],
                          'field_length': z['field_length_mm'], 'field_depth': z['field_depth_mm']} for z in opts['sizes']],
        'cable_contacts': val(opts['cable']['contacts']),
        'da03_f4_signals': DA03_F4_SIGNALS,
        'rigid_return_criterion': rigid,
        'dropped_retired_headers': {k: len(v) for k, v in model.dropped.items()},
        'summary': options,
        'options': details,
        'p_small': p_small,
    }


def build_p_small(model, sites, opts, cand, post_k, criterion, details):
    """Item 5 of attempt a5: smaller stock links on the P joint, combinations with JL and JR, and a field-length scan."""
    ps = opts['p_small']
    joints = tuple(ps['joints'])
    rules = [g['id'] for g in opts['ground_rules']]
    summ, det = [], {}
    for size in ps['sizes']:
        for rule in rules:
            s, d = p_small_option(model, sites, opts, cand, post_k, criterion, size, rule)
            summ.append(s)
            det[s['option']] = d
    best = min(summ, key=lambda s: (s['unplaced'], s['K_displaced']['total'], summ.index(s)))
    best_size = next(z for z in ps['sizes'] if z['id'] == best['size'])
    combos, cdet = [], {}
    for jid in ps['combine_jl_jr_with']:
        s, d = p_small_combo(model, sites, opts, cand, post_k, criterion, jid, best_size, best['ground_rule'])
        combos.append(s)
        cdet[s['option']] = d
    return {'status': ps['status'], 'joints': list(joints), 'summary': summ, 'options': det, 'best': best['option'],
            'best_rule': ps['best_rule'], 'combined': {'summary': combos, 'options': cdet},
            'field_scan': field_scan(model, opts, cand, details, ps['field_scan'], joints)}


def p_small_combo(model, sites, opts, cand, post_k, criterion, jid, small, rule):
    base = next(z for z in opts['sizes'] if z['id'] == jid)
    return option_result(model, sites, base, rule, opts, cand, post_k, criterion,
                         by_joint={j: small for j in opts['p_small']['joints']},
                         label='JL/JR %s + P %s %s' % (jid, small['id'], rule))


def p_small_option(model, sites, opts, cand, post_k, criterion, size, rule):
    s, d = option_result(model, sites, size, rule, opts, cand, post_k, criterion, joints=tuple(opts['p_small']['joints']),
                         label='P only %s %s' % (size['id'], rule))
    sc = size['stock_cable']
    need = [l['cable_needed_mm'] for l in d['links'] if l['placed']]
    s['stock_cable'] = {'value': sc['value'], 'contacts': sc['contacts'], 'length_mm': sc['length_mm'],
                        'opposite_side_only': sc['contacts'] == 'opposite',
                        'served': sum(1 for x in need if x <= sc['length_mm'] + 1e-9),
                        'slack_mm': [r4(sc['length_mm'] - max(need)), r4(sc['length_mm'] - min(need))] if need else None}
    return s, d


def field_scan(model, opts, cand, details, fs, joints):
    base = next(z for z in opts['sizes'] if z['id'] == fs['option'].split(' ')[0])
    links = details[fs['option']]['links']
    placed = Placed()
    for l in links:
        if l['placed']:
            add_placed(placed, l['front_board'], l['geometry'], l['id'])
    offsets = search_offsets(opts)
    rows = []
    for l in links:
        if l['placed'] or l['joint'] not in joints:
            continue
        lo, hi, found = fs['circuits_min'] - 1, base['circuits'], None
        while hi - lo > 1:
            mid = (lo + hi) // 2
            best, _ = search_link(model, placed, l, scaled_size(base, mid), opts, offsets)
            if best:
                lo, found = mid, best
            else:
                hi = mid
        rows.append({'link': l['id'], 'centre': l['centre'], 'signals': l['signals'],
                     'largest_circuits_placed': lo if found else None,
                     'field_length_mm': val(scaled_size(base, lo)['field_length_mm']) if found else None,
                     'slot_centre': list(found[5]) if found else None})
    return {'option': fs['option'], 'envelope': fs['envelope'], 'rule': fs['rule'], 'links': rows}


def scaled_size(base, n):
    """The base envelope at n circuits: field length and tail width move with n at the base pitch."""
    dn = (n - base['circuits']) * base['pitch_mm']
    out = dict(base, circuits=n, id='%s-n%d' % (base['id'], n))
    out['field_length_mm'] = {'value': r4(val(base['field_length_mm']) + dn)}
    out['tail_width_mm'] = {'value': r4(val(base['tail_width_mm']) + dn)}
    return out


# reviews/da-03.md section F4 (the figures this study reproduces): links, lower bound, mean and largest site distance,
# and signals per family
DA03_F4 = {'JL-K': [9, 7, 10.9, 17.0], 'JR-K': [10, 8, 12.6, 28.6], 'P-K': [28, 19, 12.9, 24.9], 'JL-P via K': [2, 2, 17.0, 25.5]}
DA03_F4_SIGNALS = {'K/P': 246, 'JR/K': 108, 'JL/K': 100, 'JL/P pass-through': 16, 'P/K for EL': 18, 'SUB': 4}


def search_parameters(opts, cand):
    c = opts['cable']
    fx = [f for f in cand['fixings'] if f['declared']]
    return {'step_mm': val(opts['search']['step_mm']), 'radius_mm': val(opts['search']['radius_mm']),
            'distance_weight_per_mm': val(opts['search']['distance_weight_per_mm']),
            'join_radius_mm': val(opts['clustering']['join_radius_mm']),
            'slot_web_mm': val(opts['slot']['web_mm']), 'slot_width_extra_mm': val(opts['slot']['width_extra_mm']),
            'slot_length_mm': val(opts['slot']['length_mm']),
            'insertion_mm': val(c['insertion_depth_mm']), 'straight_mm': val(c['straight_stiffened_outside_mm']),
            'bend_radius_mm': val(c['bend_radius_mm']),
            'tail_run_mm': r4(val(c['straight_stiffened_outside_mm']) + val(c['bend_radius_mm'])),
            'latch_margin_mm': val(opts['latch_access_margin_mm']),
            'fixings': {'posts': sum(1 for f in fx if f['kind'] == 'post'),
                        'kept_supports': sum(1 for f in fx if f['kind'] == 'kept support'),
                        'other_declared': sum(1 for f in fx if f['kind'] not in ('post', 'kept support'))}}


def generate(root=sg.ROOT, with_p_small=True):
    """(main candidate, P-joint addition or None); both carry the same provenance."""
    inp = load_inputs(root)
    prov = {'generator': 'scripts/stack/geometry/links.py', 'regenerate': REGEN, 'input_sha256': input_hashes(root)}
    body = build(inp, with_p_small=with_p_small)
    small = body.pop('p_small')
    out = {'provenance': prov}
    out.update(body)
    return out, ({'provenance': prov, **small} if small else None)


def render(out):
    return json.dumps(out, indent=1) + '\n'


# ---------------------------------------------------------------- checker

def check(out, model, opts, sites):
    """Errors of a link candidate under the legality rules of the search (evaluate) plus capacity, coverage and cable.

    Each placed link is re-evaluated against every other placed link of its option, so a candidate the search would
    reject (outline, slot web, forbidden items on fields, slot and tails, items between the boards, overlap between
    links) fails here with the search's own reason."""
    errs = []
    by_id = {s['id']: s for s in sites}
    cable = val(opts['cable']['length_mm'])
    web = val(opts['slot']['web_mm'])
    for s in out['summary']:
        cap, n = s['signals_per_link'], s['circuits']
        seen = []
        ls = out['options'][s['option']]['links']
        pl = [l for l in ls if l['placed']]
        for l in ls:
            sig = sum(len(by_id[m]['signals']) for m in l['members'])
            if sig != l['signals']:
                errs.append('%s %s: members carry %d signals, the link records %d' % (s['option'], l['id'], sig, l['signals']))
            lcap, ln = l.get('capacity_signals', cap), l.get('circuits', n)
            if sig > lcap or l['signals'] + l['grounds'] > ln:
                errs.append('%s %s: overfull, %d signals and %d grounds on %d circuits (capacity %d signals)'
                            % (s['option'], l['id'], sig, l['grounds'], ln, lcap))
            seen += l['members']
            if not l['placed']:
                continue
            others = Placed()
            for o in pl:
                if o is not l:
                    add_placed(others, o['front_board'], o['geometry'], o['id'])
            why, _ = evaluate(model, others, l['front_board'], l['geometry'], web)
            if why:
                errs.append('%s %s: %s%s' % (s['option'], l['id'], why[0], '' if why[1] is None else ' (%.4f mm)' % why[1]))
            if l['cable_needed_mm'] > cable + 1e-9:
                errs.append('%s %s: cable too short, needs %.2f mm against %.2f mm' % (s['option'], l['id'], l['cable_needed_mm'], cable))
        if sorted(seen) != sorted(i for i, x in by_id.items() if x['joint'] in s['sizes_by_joint']):
            errs.append('%s: sites not covered exactly once' % s['option'])
    return errs


# ---------------------------------------------------------------- README

def readme(out, small):
    import links_readme
    return links_readme.render(out, small)


def main(argv):
    out, small = generate()
    if '--stdout' in argv:
        sys.stdout.write(render(out))
        return 0
    LINK_CANDIDATE.write_text(render(out))
    LINK_P_SMALL.write_text(render(small))
    LINK_README.write_text(readme(out, small))
    print('wrote', ', '.join(str(p.relative_to(sg.ROOT)) for p in (LINK_CANDIDATE, LINK_P_SMALL, LINK_README)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
