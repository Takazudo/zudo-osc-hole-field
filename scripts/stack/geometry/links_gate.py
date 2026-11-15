"""The gate option of DS-67 on the FH12 field (ST-02 attempt a7).

    python3 scripts/stack/geometry/links_gate.py [--stdout]

Hirose FH12 links on stock same-side 0.5 mm cables: 40 circuits on JL and JR, on the P joint the largest of 40, 26,
14 and 8 that places, one link per adapter; the ground rule of DS-62 by signal class; the tail rule of DS-61 as a hard
screen; lengthened tails. Reads the option study's model and parameters (links.py, link-options.json) and
link-gate-options.json; writes link-gate.json and link-gate.md beside them. The option study's retained files are
not touched. Courtyard level only: nothing here is a copper clearance, a tolerance result or a fit, and nothing is
selected.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import stackgeom as sg
import links
from links import r4, val, oriented_rect, DIRS, DIR_NAMES, FRONTS

GATE_OPTIONS = links.LINK_DIR / 'link-gate-options.json'
LINK_GATE = links.LINK_DIR / 'link-gate.json'
LINK_GATE_README = links.LINK_DIR / 'link-gate.md'
REGEN = 'python3 scripts/stack/geometry/links_gate.py'
PROGRAM = ['scripts/stack/geometry/links_gate.py', 'scripts/stack/geometry/links_gate_readme.py'] + links.PROGRAM
ADAPTERS = ('O1', 'O3', 'O5')
JOINTS = ('O-K', 'JL-K', 'JR-K', 'P-K', 'JL-P via K')
QUIET = ('LOGIC', 'WIPER')
LOUD = ('ANALOGUE', 'PRECISION')


# ---------------------------------------------------------------- inputs

def load_inputs(root=sg.ROOT):
    raw = sg.load_raw(root)
    boards = sg.load_boards(raw, root, files={k: sg.BOARD_FILES[k] for k in ('K',) + FRONTS + ADAPTERS})
    ci = sg.canonical_inputs(raw, boards)
    root = Path(root)
    cand = json.loads((root / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    opts = json.loads((root / 'design/stack/geometry/links/link-options.json').read_text())
    gopts = json.loads(GATE_OPTIONS.read_text()) if root == sg.ROOT else \
        json.loads((root / 'design/stack/geometry/links/link-gate-options.json').read_text())
    le = json.loads((root / 'design/stack/link-electrical/inputs.json').read_text())
    part = json.loads((root / sg.JSON_FILES['partition']).read_text())
    return {'raw': raw, 'ci': ci, 'cand': cand, 'opts': opts, 'gopts': gopts, 'class_rules': le['classes'],
            'partition': part, 'root': root}


def input_hashes(inp):
    root = inp['root']
    paths = ['design/stack/geometry/stack-candidate.json', 'design/stack/geometry/links/link-options.json',
             'design/stack/geometry/links/link-gate-options.json', 'design/stack/geometry/check-report.json',
             'design/stack/geometry/parameters.json', sg.JSON_FILES['partition'], sg.JSON_FILES['lock']]
    paths += [sg.BOARD_FILES[k] for k in ('K',) + FRONTS + ADAPTERS] + PROGRAM
    out = {p: sg.sha256_file(root / p) for p in sorted(paths)}
    # the class rules object only, so that the link-electrical results (which read this study) are not an input
    out['design/stack/link-electrical/inputs.json#classes'] = hashlib.sha256(
        json.dumps(inp['class_rules'], sort_keys=True).encode()).hexdigest()
    return out


def fixing_sites(inp):
    """The fixings as keep-outs. Attempt a7 keeps the option study's list (18 posts and 12 kept supports of
    stack-candidate.json); attempt a8 replaces this source with design/stack/fixings/fixing-sites.json (ST-08)."""
    cand, opts = inp['cand'], inp['opts']
    posts = {p['id']: p for p in cand['posts']}
    rk, rf = opts['fixing_keepout_radius_mm']['K'], opts['fixing_keepout_radius_mm']['front']
    out = []
    for f in cand['fixings']:
        if not f['declared']:
            continue
        out.append({'id': f['id'], 'kind': f['kind'], 'K': f['xy'], 'r_K': rk,
                    'front': posts[f['id']]['proposed_front_land'] if f['id'] in posts else f['xy'],
                    'front_board': f['front_board'], 'r_front': rf})
    return out


# ---------------------------------------------------------------- classes and the ground rule of DS-62

def partition_kinds(part):
    kinds = {}
    for h in part['harnesses']:
        for s in h['signals']:
            kinds.setdefault(s['net'], set()).add(s['kind'])
    return kinds


def classify(net, kinds, rules):
    """The class rules of design/stack/link-electrical/inputs.json, first match wins (same reading as that study)."""
    ks = kinds.get(net, set())
    for r in rules:
        if 'kind' in r and r['kind'] != '*' and r['kind'] not in ks:
            continue
        if 'net_regex' in r and not re.search(r['net_regex'], net):
            continue
        return r['class']
    raise ValueError('unclassified net ' + net)


def adapter_sites(cand):
    """One link per adapter (DS-64): the two K/O pairs of each adapter, their seven signals."""
    out = {}
    for p in sorted(cand['pairs'], key=lambda q: q['id']):
        if not p['family'].startswith('K/O'):
            continue
        key = p['sites']['front']['board']
        out.setdefault(key, []).append(p)
    return out


def gate_sites(inp):
    """Every site of the gate: the 191 link sites of the study and the six adapter pairs, each signal with its class."""
    kinds = partition_kinds(inp['partition'])
    rules = inp['class_rules']['rules']
    sites = links.link_sites(inp['cand'])
    for s in sites:
        s['classes'] = [classify(n, kinds, rules) for n in s['signals']]
    ad_class = inp['gopts']['adapters']['class_of_signals']
    for key, pairs in adapter_sites(inp['cand']).items():
        for p in pairs:
            f, b = p['sites']['front'], p['sites']['back']
            sig = [n for n in p['pin_map'] if n not in links.NON_SIGNAL]
            sites.append({'id': p['id'], 'family': p['family'], 'joint': 'O-K', 'front_board': key,
                          'xy': [f['center'][0], f['center'][1]], 'K_xy': b['center'], 'positions': p['positions'],
                          'signals': sig, 'classes': [ad_class] * len(sig),
                          'front_replaces': f['replaces'], 'K_replaces': b['replaces']})
    return sites


def circuits_needed(classes):
    """Circuits a link needs under DS-62, or None when LOGIC and WIPER would share it."""
    if 'LOGIC' in classes and 'WIPER' in classes:
        return None
    a = sum(1 for c in classes if c in LOUD)
    q = len(classes) - a
    units = a + (1 if q else 0)
    return a + q + max(units - 1, 1)


def allocation(signals, n):
    """Positions 1..n: each a signal (net, class, site), a ground or unused, under DS-62 (see link-gate-options)."""
    loud = [s for s in signals if s[1] in LOUD]
    quiet = [s for s in signals if s[1] in QUIET]
    units = [[s] for s in loud] + ([quiet] if quiet else [])
    seq = []
    for i, u in enumerate(units):
        if i:
            seq.append(None)
        seq += u
    if len(units) <= 1:
        seq.append(None)
    if len(seq) > n:
        raise ValueError('allocation needs %d positions, link has %d' % (len(seq), n))
    out = []
    for i in range(n):
        if i < len(seq):
            x = seq[i]
            out.append({'pos': i + 1, 'kind': 'ground'} if x is None else
                       {'pos': i + 1, 'kind': 'signal', 'net': x[0], 'class': x[1], 'site': x[2]})
        else:
            out.append({'pos': i + 1, 'kind': 'unused'})
    return out


def allocation_errors(positions):
    """Rule violations of one link's recorded order under DS-62 (unused positions are not grounds)."""
    errs = []
    sig = [p for p in positions if p['kind'] == 'signal']
    classes = {p['class'] for p in sig}
    if 'LOGIC' in classes and 'WIPER' in classes:
        errs.append('LOGIC and WIPER share the link')
    if not any(p['kind'] == 'ground' for p in positions):
        errs.append('no ground on the link')
    prev = None
    for p in positions:
        if p['kind'] == 'ground':
            prev = None
        elif p['kind'] == 'signal':
            if prev is not None and not (prev['class'] == p['class'] and p['class'] in QUIET):
                errs.append('%s (%s) beside %s (%s) without a ground' % (prev['net'], prev['class'], p['net'], p['class']))
            prev = p
    return errs


def gate_cluster(sites, n, join_radius, prefix):
    """The study's greedy clustering (links.cluster) with DS-62 feasibility in place of an additive capacity."""
    rem = sorted(sites, key=lambda s: s['id'])
    out = []
    k = 0
    while rem:
        cx, cy = links._centroid(rem)
        seed = min(rem, key=lambda s: (-round(math.hypot(s['xy'][0] - cx, s['xy'][1] - cy), 6), s['id']))
        if (circuits_needed(seed['classes']) or n + 1) > n:
            raise ValueError('site %s does not fit %d circuits' % (seed['id'], n))
        members = [seed]
        rem.remove(seed)
        cls = list(seed['classes'])
        while True:
            mx, my = links._centroid(members)
            cands = []
            for s in rem:
                d = round(math.hypot(s['xy'][0] - mx, s['xy'][1] - my), 6)
                if d > join_radius:
                    continue
                need = circuits_needed(cls + s['classes'])
                if need is not None and need <= n:
                    cands.append((d, s['id'], s))
            if not cands:
                break
            _, _, s = min(cands, key=lambda c: (c[0], c[1]))
            members.append(s)
            rem.remove(s)
            cls += s['classes']
        k += 1
        mx, my = links._centroid(members)
        out.append({'id': '%s%02d' % (prefix, k), 'centre': [r4(mx), r4(my)], 'members': sorted(s['id'] for s in members),
                    'site_distances_mm': sorted(r4(math.hypot(s['xy'][0] - mx, s['xy'][1] - my)) for s in members)})
    return out


# ---------------------------------------------------------------- sizes and geometry

def fh12_size(n, gopts, cable=None):
    row = cable or next(z for z in gopts['sizes'] if z['circuits'] == n)
    return {'id': 'FH12-N%d' % n, 'pitch_mm': 0.5, 'circuits': n,
            'field_length_mm': {'value': r4(0.5 * n + 5.6)}, 'field_depth_mm': {'value': val(gopts['field']['depth'])},
            'tail_width_mm': {'value': r4(0.5 * (n + 1))}, 'cable': row['cable'], 'cable_length_mm': row['cable_length_mm']}


class GeoMaker:
    """The rectangles of one size, built part by part so that the search screens the slot before it builds the rest."""

    def __init__(self, size, opts, hard):
        self.L, self.D, self.W = val(size['field_length_mm']), val(size['field_depth_mm']), val(size['tail_width_mm'])
        sl = opts['slot']
        self.hs = val(sl['length_mm']) / 2
        self.sw = (self.W + val(sl['width_extra_mm'])) / 2
        self.a0 = val(opts['cable']['straight_stiffened_outside_mm']) + val(opts['cable']['bend_radius_mm'])
        self.hard = hard

    def slot(self, sx, sy, d):
        return {'slot': oriented_rect(sx, sy, d, -self.hs, self.hs, self.sw)}

    def front(self, sx, sy, d, ef):
        af = self.a0 + ef
        return {'front_connector': oriented_rect(sx, sy, d, -(af + self.D), -af, self.L / 2),
                'front_tail': oriented_rect(sx, sy, d, -af, -self.hs, self.W / 2),
                'front_tail_first': oriented_rect(sx, sy, d, -af, -(af - self.hard), self.W / 2) if self.hard > 0 else None,
                'tail_rule_hard_mm': r4(self.hard)}

    def k(self, sx, sy, d, ek):
        ak = self.a0 + ek
        return {'K_tail': oriented_rect(sx, sy, d, self.hs, ak, self.W / 2),
                'K_connector': oriented_rect(sx, sy, d, ak, ak + self.D, self.L / 2)}

    def full(self, sx, sy, d, ef=0.0, ek=0.0):
        g = self.slot(sx, sy, d)
        g.update(self.front(sx, sy, d, ef))
        g.update(self.k(sx, sy, d, ek))
        g.update({'a_mm': r4(self.a0 + ef), 'b_mm': r4(self.a0 + ek), 'front_extension_mm': r4(ef),
                  'K_extension_mm': r4(ek)})
        return {k: g[k] for k in ('slot', 'front_connector', 'front_tail', 'front_tail_first', 'K_tail', 'K_connector',
                                  'a_mm', 'b_mm', 'front_extension_mm', 'K_extension_mm', 'tail_rule_hard_mm')}


def gate_geometry(sx, sy, d, size, opts, ef=0.0, ek=0.0, hard=4.0):
    """The Z path with tails lengthened by ef (front) and ek (K) beyond the minimum run of the study."""
    return GeoMaker(size, opts, hard).full(sx, sy, d, ef, ek)


# ---------------------------------------------------------------- obstacle model of the gate

class GateModel(links.Model):
    """The option study's model with the gate's changes: fixings from fixing_sites(), the adapter boards, and with
    adapter links the six rigid K/O pairs, their K-side headers and their envelopes on K's front face removed."""

    def __init__(self, inp, sites, adapters=True):
        super().__init__(inp, [s for s in sites if s['joint'] != 'O-K'])
        ci, opts = inp['ci'], inp['opts']
        drop_labels = ('fixing keep-out',) + (('kept rigid pair',) if adapters else ())
        for key in list(self.forb):
            idx = sg.RectIndex()
            for rect, payload in self.forb[key].items:
                if not payload[2].startswith(drop_labels):
                    idx.add(rect, payload)
            self.forb[key] = idx
        self.fixings = fixing_sites(inp)
        for f in self.fixings:
            for face in 'FB':
                self._circle('K', face, f['K'], f['r_K'], 'fixing keep-out %s' % f['id'])
                if f['front_board'] in FRONTS:
                    self._circle(f['front_board'], face, f['front'], f['r_front'], 'fixing keep-out %s' % f['id'])
        model = ci['parameters']['obstacle_model']
        ad = [s for s in sites if s['joint'] == 'O-K']
        if adapters:
            k_drop = {s['K_replaces'] for s in ad}
            for face in 'FB':
                idx = sg.RectIndex()
                for rect, payload in self.disp[('K', face)].items:
                    if payload[0] not in k_drop:
                        idx.add(rect, payload)
                self.disp[('K', face)] = idx
            self.dropped['K'] = sorted(set(self.dropped['K']) | k_drop)
        lock = inp['raw']['lock']['placements']
        for key in ADAPTERS:
            refs = {f['ref'] for f in ci['boards'][key]}
            self.panel[key] = {r['ref'] for r in lock if r.get('domain') == 'O' and r['ref'] in refs}
            drop = {s['front_replaces'] for s in ad if s['front_board'] == key} if adapters else set()
            self.dropped[key] = sorted(drop)
            obs = sg.Obstacles(ci['boards'][key], model, drop=frozenset(drop))
            for face in 'FB':
                d, fb = sg.RectIndex(), sg.RectIndex()
                for rect, (ref, kind) in obs.index[face].items:
                    if kind == 'hole' or ref in self.panel[key]:
                        fb.add(rect, ('rect', rect, '%s %s' % ('panel hardware' if kind != 'hole' else 'hole', ref)))
                    else:
                        d.add(rect, (ref, kind))
                self.disp[(key, face)] = d
                self.forb[(key, face)] = fb
        # between the boards: each adapter outline and its selector, owned by the adapter (its own link passes)
        owner = {s['ref']: s['block'] for s in inp['cand']['selectors_kept']}
        self.between_owned = []
        for r, label in self.between:
            m = re.match(r'adapter (O\d) outline', label) or re.match(r'kept selector (\S+) envelope', label)
            key = m.group(1) if m and m.group(1) in ADAPTERS else owner.get(m.group(1)) if m else None
            self.between_owned.append((r, label, key if adapters else None))

    def between_hit_for(self, rect, own):
        for r, label, key in self.between_owned:
            if key is not None and key == own:
                continue
            if sg.inter(rect, r):
                return (label, r4(sg.overlap_depth(rect, r)))
        return None


# ---------------------------------------------------------------- screens, split by the side they depend on

def check_slot(model, placed, front, geo, web, own):
    slot = geo['slot']
    if not sg.rect_inside_poly(slot, model.outline['K'], web):
        return ('slot within %.1f mm of the K edge or outside K' % web, None)
    if not sg.rect_inside_poly(slot, model.outline[front], 0.0):
        return ('slot not under its own front board %s' % front, None)
    for face in 'FB':
        h = model.forbidden('K', face, sg.grow(slot, web))
        if h:
            return ('slot web on %s' % h[0], h[1])
    h = model.between_hit_for(slot, own)
    if h:
        return ('slot under %s' % h[0], h[1])
    h = placed.hit('K', 'S', slot, web) or placed.hit('K', 'B', slot)
    if h:
        return ('slot on %s' % h[0], h[1])
    h = placed.hit(front, 'B', slot)
    if h:
        return ('slot on %s (front board %s)' % (h[0], front), h[1])
    return None


def panel_hit(model, key, rect):
    """The deepest panel-hardware pad on the rear face that `rect` enters, or None."""
    worst = None
    for _, (kind, g, label) in model.forb[(key, 'B')].near(rect):
        if kind == 'rect' and label.startswith('panel hardware') and sg.inter(rect, g):
            d = sg.overlap_depth(rect, g)
            if worst is None or d > worst[1]:
                worst = (label, r4(d))
    return worst


def check_front(model, placed, front, geo, own, shrink=0.0):
    """`shrink` > 0 screens the field against panel-hardware pads with less courtyard growth (a comparison run)."""
    fc, ft, first = geo['front_connector'], geo['front_tail'], geo['front_tail_first']
    if not sg.rect_inside_poly(fc, model.outline[front], model.margin):
        return ('front field outside the %s outline less %.2f mm' % (front, model.margin), None)
    if not sg.rect_inside_poly(ft, model.outline[front], 0.0):
        return ('front tail not under its own front board %s' % front, None)
    if shrink > 0:
        h = model.forbidden(front, 'B', fc, tail=True) or panel_hit(model, front, sg.grow(fc, -shrink))
    else:
        h = model.forbidden(front, 'B', fc)
    if h:
        return ('front field on %s' % h[0], h[1])
    h = model.forbidden(front, 'B', first) if first else None
    if h:
        return ('first %.1f mm of the front tail on %s' % (geo['tail_rule_hard_mm'], h[0]), h[1])
    h = model.forbidden(front, 'B', ft, tail=True)
    if h:
        return ('front tail on %s' % h[0], h[1])
    for rect, what in ((fc, 'front field'), (ft, 'front tail')):
        h = model.between_hit_for(rect, own)
        if h:
            return ('%s under %s' % (what, h[0]), h[1])
        h = placed.hit(front, 'B', rect)
        if h:
            return ('%s on %s' % (what, h[0]), h[1])
        h = placed.hit(front, 'S', rect)
        if h:
            return ('%s on %s (front board %s)' % (what, h[0], front), h[1])
    return None


def check_k(model, placed, geo):
    kc, kt = geo['K_connector'], geo['K_tail']
    if not sg.rect_inside_poly(kc, model.outline['K'], model.margin):
        return ('K field outside the K outline less %.2f mm' % model.margin, None)
    h = model.forbidden('K', 'B', kc)
    if h:
        return ('K field on %s' % h[0], h[1])
    h = model.forbidden('K', 'B', kt, tail=True)
    if h:
        return ('K tail on %s' % h[0], h[1])
    for rect, what in ((kc, 'K field'), (kt, 'K tail')):
        h = placed.hit('K', 'B', rect) or placed.hit('K', 'S', rect)
        if h:
            return ('%s on %s' % (what, h[0]), h[1])
    return None


def evaluate(model, placed, front, geo, web, own, shrink=0.0):
    """(reason, depth) or None for one complete candidate; the search and the checker share these screens."""
    return check_slot(model, placed, front, geo, web, own) or check_front(model, placed, front, geo, own, shrink) or \
        check_k(model, placed, geo)


def displaced(model, front, geo):
    return {'front B': sorted(model.displaced(front, 'B', geo['front_connector'])),
            'K F (slot)': sorted(model.displaced('K', 'F', geo['slot'])),
            'K B (slot)': sorted(model.displaced('K', 'B', geo['slot'])),
            'K B (field)': sorted(model.displaced('K', 'B', geo['K_connector']))}


def trim_list(model, front, geo):
    """Panel-hardware pads under the front tail beyond its first 4.0 mm: leads to trim (DS-61)."""
    ft = geo['front_tail']
    return sorted({lab.split(' ')[-1] for _, (kind, g, lab) in model.forb[(front, 'B')].near(ft)
                   if kind == 'rect' and lab.startswith('panel hardware') and sg.inter(ft, g)})


def add_placed(placed, front, geo, lid):
    links.add_placed(placed, front, geo, lid)


# ---------------------------------------------------------------- search

def grid_offsets(step, radius, bbox=None, centre=None):
    """Slot offsets on a square grid within `radius` (None: unbounded, limited to `bbox` around `centre`),
    nearest first, as links.search_offsets orders them."""
    if radius is None:
        cx, cy = centre
        xs = range(int(math.floor((bbox[0] - cx) / step)), int(math.ceil((bbox[2] - cx) / step)) + 1)
        ys = range(int(math.floor((bbox[1] - cy) / step)), int(math.ceil((bbox[3] - cy) / step)) + 1)
        pts = [(i * step, j * step) for i in xs for j in ys]
    else:
        n = int(round(radius / step))
        pts = [(i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)
               if math.hypot(i * step, j * step) <= radius + 1e-9]
    return sorted(pts, key=lambda o: (round(math.hypot(*o), 6), o))


class Ctx:
    def __init__(self, inp, model, flags):
        self.inp, self.model, self.flags = inp, model, flags
        self.opts, self.gopts, self.cand = inp['opts'], inp['gopts'], inp['cand']
        self.web = val(self.opts['slot']['web_mm'])
        self.w = val(self.opts['search']['distance_weight_per_mm'])
        self.step0 = val(self.opts['search']['step_mm'])
        self.radius = val(self.opts['search']['radius_mm']) if flags['radius'] == 'study' else flags['radius']
        self.offsets = grid_offsets(self.step0, self.radius) if self.radius is not None else None
        self._grids = {}
        # the field courtyard grows 0.25 mm per side over body and land; a run may grow it less against panel pads
        self.panel_shrink = r4(val(self.gopts['field']['growth_mm']) - flags['panel_growth'])
        self.gaps = self.cand['stack']['mated_heights_mm']
        self.k_th = round(self.cand['stack']['K_face_z_mm'] - self.cand['stack']['K_rear_z_mm'], 4)
        self.hard = flags['hard'] if flags['tail_rule'] else 0.0
        self.step = val(self.gopts['tail_lengthening']['step_mm'])
        self.a0 = val(self.opts['cable']['straight_stiffened_outside_mm']) + val(self.opts['cable']['bend_radius_mm'])

    def grid(self, step, front, centre, radius='default'):
        """Offsets of one search: the run's radius, or unbounded over the link's front board."""
        radius = self.radius if radius == 'default' else radius
        if radius is not None:
            key = (step, radius)
            if key not in self._grids:
                self._grids[key] = grid_offsets(step, radius)
            return self._grids[key]
        ol = self.model.outline[front]
        bbox = [min(p[0] for p in ol), min(p[1] for p in ol), max(p[0] for p in ol), max(p[1] for p in ol)]
        return grid_offsets(step, None, bbox, centre)

    def need(self, front, a, b):
        return links.cable_needed(a, b, self.gaps[front + '/K'], self.k_th, self.opts)

    def spare(self, front, size):
        return r4(size['cable_length_mm'] - self.need(front, self.a0, self.a0))

    def extensions(self, limit):
        if not self.flags['lengthen'] or limit < 0:
            return [0.0] if limit >= -1e-9 else []
        n = int(math.floor(limit / self.step + 1e-9))
        return [r4(i * self.step) for i in range(n + 1)]


def candidate(ctx, placed, front, size, own, sx, sy, d, dist, spare, lengthen=True, gm=None):
    """One slot centre and direction: (reason, None) when illegal, else (None, (cost, geo, disp)) with the shortest
    legal front extension and then the shortest legal K extension."""
    model = ctx.model
    gm = gm or GeoMaker(size, ctx.opts, ctx.hard)
    why = check_slot(model, placed, front, gm.slot(sx, sy, d), ctx.web, own)
    if why:
        return why, None
    ef, first_why = None, None
    for e in (ctx.extensions(spare) if lengthen else [0.0]):
        why = check_front(model, placed, front, gm.front(sx, sy, d, e), own, ctx.panel_shrink)
        if not why:
            ef = e
            break
        first_why = first_why or why
    if ef is None:
        return first_why or ('cable too short for the minimum tails', None), None
    ek, first_why = None, None
    for e in (ctx.extensions(r4(spare - ef)) if lengthen else [0.0]):
        why = check_k(model, placed, gm.k(sx, sy, d, e))
        if not why:
            ek = e
            break
        first_why = first_why or why
    if ek is None:
        return first_why or ('cable too short for the minimum tails', None), None
    geo = gm.full(sx, sy, d, ef, ek)
    disp = displaced(model, front, geo)
    k_refs = set(disp['K F (slot)']) | set(disp['K B (slot)']) | set(disp['K B (field)'])
    return None, (len(disp['front B']) + len(k_refs) + ctx.w * (dist + ef + ek), geo, disp)


def search(ctx, placed, front, centre, size, own, lengthen=True, offsets=None, limit=None, collect=None):
    """The cheapest legal candidate (cost, key, geo, disp, d, slot, dist) or None, and the rejection tally.
    `limit`: a candidate costing more is not legal (the improvement pass). `collect`: return up to that many legal
    candidates, cheapest first, instead (no early stop)."""
    offsets = offsets or ctx.grid(ctx.step0, front, centre)
    spare = ctx.spare(front, size)
    gm = GeoMaker(size, ctx.opts, ctx.hard)
    cx, cy = centre
    best, tally, found = None, {}, []
    for off in offsets:
        dist = math.hypot(*off)
        if collect is None and best is not None and ctx.w * dist > best[0] + 1e-9:
            break
        if limit is not None and ctx.w * dist > limit + 1e-9:
            break
        sx, sy = r4(cx + off[0]), r4(cy + off[1])
        for di, d in enumerate(DIRS):
            why, c = candidate(ctx, placed, front, size, own, sx, sy, d, dist, spare, lengthen, gm)
            if why:
                if best is None:
                    t = tally.setdefault(why[0], [0, None])
                    t[0] += 1
                    if why[1] is not None and (t[1] is None or why[1] < t[1]):
                        t[1] = why[1]
                continue
            cost, geo, disp = c
            if limit is not None and cost > limit + 1e-9:
                continue
            key = (round(cost, 6), round(dist, 6), di, geo['front_extension_mm'], geo['K_extension_mm'], sx, sy)
            cand = (cost, key, geo, disp, d, (sx, sy), dist)
            if collect is not None:
                found.append(cand)
            if best is None or key < best[1]:
                best = cand
    if collect is not None:
        return sorted(found, key=lambda c: c[1])[:collect], tally
    return best, tally


def smallest_miss(tally):
    v = [x[1] for k, x in tally.items() if x[1] is not None]
    return min(v) if v else None


def nearest_misses(ctx, placed, front, centre, size, own, k=3):
    """The candidates nearest the link centre and the screen that rejects each (for links without a place)."""
    out = []
    cx, cy = centre
    for off in ctx.grid(ctx.step0, front, centre):
        sx, sy = r4(cx + off[0]), r4(cy + off[1])
        for d in DIRS:
            geo = gate_geometry(sx, sy, d, size, ctx.opts, hard=ctx.hard)
            why = evaluate(ctx.model, placed, front, geo, ctx.web, own, ctx.panel_shrink)
            if why and 'outline' not in why[0] and 'K edge' not in why[0] and 'own front board' not in why[0]:
                out.append({'slot_centre': [sx, sy], 'direction': DIR_NAMES[d], 'screen': why[0],
                            'penetration_mm': why[1], 'distance_mm': r4(math.hypot(*off))})
                if len(out) == k:
                    return out
    return out


# ---------------------------------------------------------------- placement of the gate option

def link_record(ctx, lid, joint, front, members, site_by, size):
    sig = [(n, c, m) for m in members for n, c in zip(site_by[m]['signals'], site_by[m]['classes'])]
    classes = [c for _, c, _ in sig]
    n = size['circuits']
    pos = allocation(sig, n)
    return {'id': lid, 'joint': joint, 'front_board': front, 'members': list(members),
            'signals': len(sig), 'grounds': sum(1 for p in pos if p['kind'] == 'ground'),
            'unused': sum(1 for p in pos if p['kind'] == 'unused'), 'circuits_needed': circuits_needed(classes),
            'size': size['id'], 'circuits': n, 'cable': size['cable'], 'cable_length_mm': size['cable_length_mm'],
            'positions': pos}


def place(ctx, placed, rec, size, centre, own, offsets=None, grid=None, best=None):
    tally = {}
    if best is None:
        best, tally = search(ctx, placed, rec['front_board'], centre, size, own, offsets=offsets)
    if best is None:
        return False, tally
    _, _, geo, disp, d, (sx, sy), dist = best
    lengthened = geo['front_extension_mm'] > 0 or geo['K_extension_mm'] > 0
    only = False
    if lengthened:
        b0, _ = search(ctx, placed, rec['front_board'], centre, size, own, lengthen=False, offsets=offsets)
        only = b0 is None
    for k in ('no_place', 'sites', 'nearest_misses', 'most_frequent_blockers', 'why_no_place'):
        rec.pop(k, None)
    front = rec['front_board']
    add_placed(placed, front, geo, rec['id'])
    need = ctx.need(front, geo['a_mm'], geo['b_mm'])
    rec.update({'placed': True, 'centre': centre, 'slot_centre': [sx, sy], 'direction': DIR_NAMES[d],
                'slot_distance_from_centre_mm': r4(dist), 'geometry': geo, 'displaced': disp,
                'lengthened_tail': lengthened, 'placed_only_with_lengthened_tail': only,
                'trim_leads': trim_list(ctx.model, front, geo),
                'under_tails': links.under_tails(ctx.model, front, geo),
                'cable_needed_mm': need, 'loop_mm': r4(size['cable_length_mm'] - need),
                'grid_mm': grid or ctx.step0, 'cost': r4(best[0])})
    return True, tally


def place_gate(inp, sites, flags):
    """Place the gate option; `flags` switch the causes off for the comparison runs."""
    model = GateModel(inp, sites, adapters=flags['adapters'])
    ctx = Ctx(inp, model, flags)
    gopts, opts = inp['gopts'], inp['opts']
    site_by = {s['id']: s for s in sites}
    jr = val(opts['clustering']['join_radius_mm'])
    placed = links.Placed()
    out = []
    unplaced = []
    joint_sizes = {j: list(gopts['joints'][j]) for j in ('JL-K', 'JR-K', 'P-K', 'JL-P via K')}
    if not flags['ladder']:
        joint_sizes['P-K'] = joint_sizes['JL-P via K'] = [flags['p_fixed']]
    if flags['adapters']:
        ad = gopts['adapters']
        for key in gopts['adapters']['boards']:
            mem = sorted(s['id'] for s in sites if s['joint'] == 'O-K' and s['front_board'] == key)
            size = fh12_size(ad['circuits'], gopts)
            rec = link_record(ctx, 'O-K-%s' % key, 'O-K', key, mem, site_by, size)
            centre = [r4(c) for c in links._centroid([site_by[m] for m in mem])]
            ok, tally = place(ctx, placed, rec, size, centre, key)
            if not ok:
                rec.update({'placed': False, 'centre': centre, 'no_place': 'no place at 14 circuits: the rigid pairs '
                            'stay as the named exception of DS-64', 'nearest_misses':
                            nearest_misses(ctx, placed, key, centre, size, key)})
                unplaced.append(rec['id'])
            out.append(rec)
    for joint in ('JL-K', 'JR-K', 'P-K', 'JL-P via K'):
        ladder = joint_sizes[joint]
        js = [s for s in sites if s['joint'] == joint]
        for front in sorted({s['front_board'] for s in js}):
            fs = [s for s in js if s['front_board'] == front]
            prefix = '%s-%s-L' % (joint.replace(' ', '').replace('via', '-'), front)
            for c in gate_cluster(fs, ladder[0], jr, prefix):
                _place_ladder(ctx, placed, out, unplaced, joint, front, c, ladder, 0, site_by, jr)
    if flags['refine']:
        refine(ctx, placed, out)
        placed = improve(ctx, out)
        if flags['analyse']:
            for r in out:
                if not r['placed']:
                    r['why_no_place'] = why_no_place(ctx, placed, r)
    _latch(ctx, out)
    return model, ctx, out


def rec_size(ctx, r):
    return fh12_size(r['circuits'], ctx.gopts, {'cable': r['cable'], 'cable_length_mm': r['cable_length_mm']})


def rec_own(r):
    return r['front_board'] if r['joint'] == 'O-K' else None


def placed_index(out, skip=()):
    placed = links.Placed()
    for r in out:
        if r['placed'] and r['id'] not in skip:
            add_placed(placed, r['front_board'], r['geometry'], r['id'])
    return placed


def refine(ctx, placed, out):
    """Item 1 of part 2: every link without a place on the 2.0 mm grid is searched again on 0.5 mm, and on 0.25 mm
    where its smallest miss on 0.5 mm is below 0.5 mm; placed links fixed, rules, sizes, radius and cost unchanged."""
    rg = ctx.gopts['refinement']
    g1, g2 = val(rg['grids_mm'])
    thr = val(rg['quarter_grid_below_mm'])
    rr = ctx.flags['refine_radius']
    for r in out:
        if r['placed']:
            continue
        front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
        tried, miss, best = [], None, None
        for g in (g1, g2):
            if g == g2 and (miss is None or miss >= thr):
                break
            offs = ctx.grid(g, front, centre, rr)
            best, tally = search(ctx, placed, front, centre, size, own, offsets=offs)
            tried.append(g)
            if best:
                place(ctx, placed, r, size, centre, own, offsets=offs, grid=g, best=best)
                r['refinement'] = {'found': True, 'by': 'finer grid', 'grid_mm': g, 'grids_tried_mm': tried}
                break
            miss = smallest_miss(tally)
        if not best:
            r['refinement'] = {'found': False, 'grids_tried_mm': tried, 'smallest_miss_mm': miss}


def improve(ctx, out):
    """The bounded improvement pass of part 2 item 1 (rule in link-gate-options.json refinement.improvement)."""
    ip = ctx.gopts['refinement']['improvement']
    g1 = val(ctx.gopts['refinement']['grids_mm'])[0]
    rr = ctx.flags['refine_radius']
    cap = val(ip['candidates_per_link'])
    for rnd in range(1, val(ip['rounds']) + 1):
        changed = False
        for u in [r for r in out if not r['placed']]:
            front, size, own, centre = u['front_board'], rec_size(ctx, u), rec_own(u), u['centre']
            offs = ctx.grid(g1, front, centre, rr)
            cands, _ = search(ctx, links.Placed(), front, centre, size, own, offsets=offs, collect=cap)
            pl = [r for r in out if r['placed']]
            tried = set()
            for c in cands:
                geo = c[2]
                blockers = []
                for b in pl:
                    if math.hypot(b['slot_centre'][0] - c[5][0], b['slot_centre'][1] - c[5][1]) > 80:
                        continue
                    one = links.Placed()
                    add_placed(one, b['front_board'], b['geometry'], b['id'])
                    if evaluate(ctx.model, one, front, geo, ctx.web, own, ctx.panel_shrink):
                        blockers.append(b)
                        if len(blockers) > 1:
                            break
                if len(blockers) != 1 or blockers[0]['id'] in tried:
                    continue
                b = blockers[0]
                tried.add(b['id'])
                others = placed_index(out, skip={b['id']})
                add_placed(others, front, geo, u['id'])
                bsize = rec_size(ctx, b)
                boffs = ctx.grid(g1, b['front_board'], b['centre'], rr)
                limit = r4(b['cost'] + val(ip['allowance']))
                nb, _ = search(ctx, others, b['front_board'], b['centre'], bsize, rec_own(b), offsets=boffs, limit=limit)
                if not nb:
                    continue
                old = {'slot_centre': b['slot_centre'], 'direction': b['direction'], 'cost': b['cost'], 'grid_mm': b['grid_mm']}
                place(ctx, others, b, bsize, b['centre'], rec_own(b), offsets=boffs, grid=g1, best=nb)
                b['moved_by_improvement'] = dict(old, round=rnd, to_free_a_place_for=u['id'], new_cost=b['cost'])
                allp = placed_index(out, skip={u['id']})
                if evaluate(ctx.model, allp, front, geo, ctx.web, own, ctx.panel_shrink):
                    raise AssertionError('improvement pass left %s illegal' % u['id'])
                place(ctx, allp, u, size, centre, own, offsets=offs, grid=g1, best=c)
                u['refinement'] = {'found': True, 'by': 'improvement pass', 'round': rnd, 'grid_mm': g1, 'moved': b['id']}
                changed = True
                break
        if not changed:
            break
    return placed_index(out)


def field_screen(model, placed, front, fc, own, shrink):
    if not sg.rect_inside_poly(fc, model.outline[front], model.margin):
        return ('outline', None)
    h = (model.forbidden(front, 'B', fc, tail=True) or panel_hit(model, front, sg.grow(fc, -shrink))) if shrink > 0 \
        else model.forbidden(front, 'B', fc)
    h = h or model.between_hit_for(fc, own) or placed.hit(front, 'B', fc) or placed.hit(front, 'S', fc)
    return h


def corridor(model, front, rect, axis):
    """Free span between panel-hardware pads through `rect` along `axis` (0: x, 1: y), within the band that the
    rect covers across it; (free, needed), free None where no pad bounds a side within 30 mm."""
    lo_i, hi_i = (0, 2) if axis == 0 else (1, 3)
    blo, bhi = (1, 3) if axis == 0 else (0, 2)
    c = (rect[lo_i] + rect[hi_i]) / 2
    probe = list(rect)
    probe[lo_i], probe[hi_i] = c - 30, c + 30
    left, right = None, None
    for _, (kind, g, label) in model.forb[(front, 'B')].near(probe):
        if kind != 'rect' or not label.startswith('panel hardware'):
            continue
        if g[bhi] <= rect[blo] or g[blo] >= rect[bhi] or g[hi_i] < c - 30 or g[lo_i] > c + 30:
            continue
        if (g[lo_i] + g[hi_i]) / 2 < c:
            left = g[hi_i] if left is None else max(left, g[hi_i])
        else:
            right = g[lo_i] if right is None else min(right, g[lo_i])
    free = None if left is None or right is None else r4(right - left)
    return free, r4(rect[hi_i] - rect[lo_i])


def why_no_place(ctx, placed, r):
    """Item 2 of part 2: the deepest stage any candidate reaches (field, first 4.0 mm of the tail, slot on K), the
    smallest penetration there and the free corridor between panel pads at that candidate."""
    model = ctx.model
    front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
    g = (r.get('refinement') or {}).get('grids_tried_mm', [ctx.step0])[-1]
    spare = ctx.spare(front, size)
    best = {}
    for off in ctx.grid(g, front, centre, ctx.flags['refine_radius']):
        sx, sy = r4(centre[0] + off[0]), r4(centre[1] + off[1])
        for d in DIRS:
            for e in ctx.extensions(spare):
                geo = gate_geometry(sx, sy, d, size, ctx.opts, ef=e, hard=ctx.hard)
                fc = geo['front_connector']
                h = field_screen(model, placed, front, fc, own, ctx.panel_shrink)
                if h:
                    stage, why = 0, h
                else:
                    first = geo['front_tail_first']
                    h = model.forbidden(front, 'B', first) if first else None
                    if h:
                        stage, why = 1, h
                    else:
                        w2 = check_front(model, placed, front, geo, own, ctx.panel_shrink) or \
                            check_slot(model, placed, front, geo, ctx.web, own)
                        if w2 is None:
                            k_ok = any(check_k(model, placed, gate_geometry(sx, sy, d, size, ctx.opts, ef=e, ek=k, hard=ctx.hard)) is None
                                       for k in ctx.extensions(r4(spare - e)))
                            w2 = None if k_ok else ('K side', None)
                        stage, why = 2, w2 or ('legal', 0.0)
                if why[1] is None:
                    continue
                cur = best.get(stage)
                if cur is None or why[1] < cur[0]:
                    best[stage] = (why[1], why[0], geo, (sx, sy), DIR_NAMES[d], e)
    if not best:
        return {'lacks': 'no candidate inside the board margins', 'grid_mm': g}
    stage = max(best)
    pen, label, geo, slot, dname, e = best[stage]
    fc = geo['front_connector']
    fx, fy = corridor(model, front, fc, 0), corridor(model, front, fc, 1)
    out = {'lacks': ('the field', 'the first %.1f mm of the tail' % ctx.hard, 'the slot on K or the K side')[stage],
           'grid_mm': g, 'smallest_penetration_mm': pen, 'blocker': label,
           'at': {'slot_centre': list(slot), 'direction': dname, 'front_extension_mm': e},
           'field_corridor_mm': {'x': {'free': fx[0], 'needed': fx[1]}, 'y': {'free': fy[0], 'needed': fy[1]}}}
    if stage >= 1 and geo['front_tail_first']:
        ax = 0 if dname in ('+x', '-x') else 1
        first = geo['front_tail_first']
        across, w = corridor(model, front, first, 1 - ax)
        out['tail_corridor_mm'] = {'across': {'free': across, 'needed': w}, 'first_length_needed': ctx.hard}
    return out


def _place_ladder(ctx, placed, out, unplaced, joint, front, c, ladder, k, site_by, jr):
    size = fh12_size(ladder[k], ctx.gopts)
    rec = link_record(ctx, c['id'], joint, front, c['members'], site_by, size)
    ok, tally = place(ctx, placed, rec, size, c['centre'], None)
    if ok:
        rec['sizes_tried'] = ladder[:k + 1]
        out.append(rec)
        return
    if k + 1 < len(ladder):
        for sub in gate_cluster([site_by[m] for m in c['members']], ladder[k + 1], jr, c['id'] + '.'):
            _place_ladder(ctx, placed, out, unplaced, joint, front, sub, ladder, k + 1, site_by, jr)
        return
    inside = {kk: v for kk, v in tally.items() if 'outline' not in kk and 'K edge' not in kk}
    rec.update({'placed': False, 'centre': c['centre'], 'sizes_tried': ladder[:k + 1],
                'no_place': 'no place as a stock link at %d circuits' % ladder[k],
                'sites': [{'site': m, 'xy': site_by[m]['xy'], 'signals': site_by[m]['signals']} for m in c['members']],
                'nearest_misses': nearest_misses(ctx, placed, front, c['centre'], size, None),
                'most_frequent_blockers': [{'blocker': kk, 'candidates': v[0], 'smallest_penetration_mm': v[1]}
                                           for kk, v in sorted(inside.items(), key=lambda kv: (-kv[1][0], kv[0]))[:3]]})
    unplaced.append(rec['id'])
    out.append(rec)


def _latch(ctx, out):
    margin = val(ctx.opts['latch_access_margin_mm'])
    all_disp = {x for r in out if r['placed'] for k in links.K_DISPLACED for x in r['displaced'][k]}
    for r in out:
        if r['placed']:
            zone = sg.grow(r['geometry']['K_connector'], margin)
            near = sorted(ctx.model.displaced('K', 'B', zone) - all_disp)
            r['latch_reach'] = {'neighbours_within_margin': near,
                                'verdict': 'open' if not near else 'NOT SHOWN (neighbour heights not retained)'}


def adapter_small_check(ctx, out, sites):
    """Per adapter: would 8 circuits place, with every other link fixed (its own 14-circuit link removed)."""
    site_by = {s['id']: s for s in sites}
    res = []
    for key in ctx.gopts['adapters']['boards']:
        own = next(r for r in out if r['id'] == 'O-K-%s' % key)
        placed = links.Placed()
        for r in out:
            if r['placed'] and r is not own:
                add_placed(placed, r['front_board'], r['geometry'], r['id'])
        row = {'adapter': key}
        for cable in (next(z for z in ctx.gopts['sizes'] if z['circuits'] == 8), ctx.gopts['adapter_short_cable']):
            size = fh12_size(8, ctx.gopts, cable)
            best, _ = search(ctx, placed, key, own['centre'], size, key)
            if best is None:
                row[cable['cable']] = {'places': False}
                continue
            geo = best[2]
            need = ctx.need(key, geo['a_mm'], geo['b_mm'])
            row[cable['cable']] = {'places': True, 'slot_centre': list(best[5]), 'direction': DIR_NAMES[best[4]],
                                   'cable_length_mm': cable['cable_length_mm'], 'cable_needed_mm': need,
                                   'loop_mm': r4(cable['cable_length_mm'] - need),
                                   'K_displaced': sorted(set(best[3]['K F (slot)']) | set(best[3]['K B (slot)'])
                                                         | set(best[3]['K B (field)']))}
        res.append(row)
    return res


# ---------------------------------------------------------------- results

def split(refs):
    out = {'ICs': 0, 'resistors': 0, 'capacitors': 0, 'other': 0}
    for r in refs:
        p = re.match(r'[A-Z]+', r).group(0)
        out['ICs' if p == 'U' else 'resistors' if p == 'R' else 'capacitors' if p == 'C' else 'other'] += 1
    return out


def summarise(ctx, out, post_k):
    pl = [r for r in out if r['placed']]
    k_f = sorted({x for r in pl for x in r['displaced']['K F (slot)']})
    k_bs = sorted({x for r in pl for x in r['displaced']['K B (slot)']})
    k_bf = sorted({x for r in pl for x in r['displaced']['K B (field)']})
    k_all = sorted(set(k_f) | set(k_bs) | set(k_bf))
    fronts = {b: sorted({x for r in pl if r['front_board'] == b for x in r['displaced']['front B']})
              for b in FRONTS + ADAPTERS}
    per = {}
    for r in out:
        e = per.setdefault(r['joint'], {}).setdefault(r['size'], {'links': 0, 'placed': 0, 'unplaced': 0, 'signals': 0,
                                                                 'grounds': 0, 'unused': 0})
        e['links'] += 1
        e['placed' if r['placed'] else 'unplaced'] += 1
        for k in ('signals', 'grounds', 'unused'):
            e[k] += r[k]
    need = [r['cable_needed_mm'] for r in pl]
    loops = [r['loop_mm'] for r in pl]
    allocated = sum(r['signals'] for r in pl)
    return {
        'links': len(out), 'placed': len(pl), 'unplaced': len(out) - len(pl),
        'slots': len(pl), 'connectors': 2 * len(pl), 'latches': 2 * len(pl),
        'signals_on_links': sum(r['signals'] for r in out), 'signals_on_placed_links': allocated,
        'grounds': sum(r['grounds'] for r in pl), 'unused_positions': sum(r['unused'] for r in pl),
        'per_joint_and_size': per,
        'K_displaced': {'F.Cu by slots': len(k_f), 'B.Cu by slots': len(k_bs), 'B.Cu by fields': len(k_bf),
                        'total': len(k_all), 'outside_post_keepouts': len(set(k_all) - post_k),
                        'split': split(k_all)},
        'front_displaced': {b: len(v) for b, v in fronts.items()},
        'front_displaced_split': split(sorted({x for v in fronts.values() for x in v})),
        'front_tails_over_panel_hardware': sum(1 for r in pl if r['trim_leads']),
        'trim_leads': sum(len(r['trim_leads']) for r in pl),
        'lengthened_tails': sum(1 for r in pl if r['lengthened_tail']),
        'placed_only_with_lengthened_tail': sum(1 for r in pl if r['placed_only_with_lengthened_tail']),
        'cable_needed_mm': [min(need), max(need)] if need else None,
        'loop_mm': [min(loops), max(loops)] if loops else None,
        'links_over_cable_length': sum(1 for r in pl if r['loop_mm'] < -1e-9),
        'latch_not_shown': sum(1 for r in pl if r['latch_reach']['verdict'] != 'open'),
    }, {'K_displaced_refs': {'F.Cu by slots': k_f, 'B.Cu by slots': k_bs, 'B.Cu by fields': k_bf},
        'front_displaced_refs': fronts}


FULL = {'ladder': True, 'tail_rule': True, 'lengthen': True, 'adapters': True, 'p_fixed': 8, 'refine': True,
        'radius': 'study', 'hard': 4.0, 'panel_growth': 0.25, 'refine_radius': 'default', 'analyse': True}
CAUSES = [
    ('class rule, fixed sizes (JL/JR 40, P 8)', {'ladder': False, 'tail_rule': False, 'lengthen': False, 'adapters': False, 'refine': False}),
    ('+ mixed sizes on P', {'ladder': True, 'tail_rule': False, 'lengthen': False, 'adapters': False, 'refine': False}),
    ('+ tail rule', {'ladder': True, 'tail_rule': True, 'lengthen': False, 'adapters': False, 'refine': False}),
    ('+ lengthened tails', {'ladder': True, 'tail_rule': True, 'lengthen': True, 'adapters': False, 'refine': False}),
    ('+ adapter links (the gate option of part 1)', {'ladder': True, 'tail_rule': True, 'lengthen': True, 'adapters': True,
                                                     'refine': False}),
]
# not a step of the chain: the trade that DS-61 names if links lose their place under the 4.0 mm rule
TRADE = ('comparison: the gate option without the 4.0 mm rule (every lead under a front tail trimmed)',
         {'ladder': True, 'tail_rule': False, 'lengthen': True, 'adapters': True, 'refine': False})


def gate_run(inp, sites, flags, post_k):
    flags = dict(FULL, **flags)
    model, ctx, out = place_gate(inp, sites, flags)
    s, refs = summarise(ctx, out, post_k)
    return model, ctx, out, s, refs


def study_field_runs(inp, gopts):
    """Item 1: the option study's rule, clustering and model with the FH12 field in place of the old one."""
    sinp = links.load_inputs(inp['root'])
    ssites = links.link_sites(sinp['cand'])
    smodel = links.Model(sinp, ssites)
    post_k = links.post_keepout_k(inp['root'])
    old = {z['id']: z for z in sinp['opts']['sizes'] + sinp['opts']['p_small']['sizes']}
    pj = tuple(sinp['opts']['p_small']['joints'])
    rows = []
    for label, size, joints in (('P joint, 8 circuits', '8', pj), ('JL and JR, 40 circuits', '40', ('JL-K', 'JR-K'))):
        for rule in ('G-PER-2S', 'G-BETWEEN'):
            for which, z in (('option study field', old['P050-N%s' % size]), ('FH12 field', fh12_size(int(size), gopts))):
                s, _ = links.option_result(smodel, ssites, z, rule, sinp['opts'], sinp['cand'], post_k, 0, joints=joints,
                                           label='%s %s %s' % (label, rule, which))
                rows.append({'run': label, 'ground_rule': rule, 'field': which,
                             'field_mm': [val(z['field_length_mm']), val(z['field_depth_mm'])],
                             'links': s['links'], 'placed': s['placed'], 'unplaced': s['unplaced'],
                             'K_displaced': s['K_displaced']['total'], 'front_displaced': s['front_displaced']})
    for label, base, small, rule in (('JL/JR 40 + P 8 (the 88-link row)', 'P050-N40', 'P050-N8', 'G-BETWEEN'),
                                      ('JL/JR 40 + P 8, one ground per two signals', 'P050-N40', 'P050-N8', 'G-PER-2S')):
        for which, zb, zs in (('option study field', old[base], old[small]),
                              ('FH12 field', fh12_size(40, gopts), fh12_size(8, gopts))):
            s, _ = links.option_result(smodel, ssites, zb, rule, sinp['opts'], sinp['cand'], post_k, 0,
                                       by_joint={j: zs for j in pj}, label='%s %s' % (label, which))
            rows.append({'run': label, 'ground_rule': rule, 'field': which,
                         'field_mm': [val(zs['field_length_mm']), val(zs['field_depth_mm'])],
                         'links': s['links'], 'placed': s['placed'], 'unplaced': s['unplaced'],
                         'K_displaced': s['K_displaced']['total'], 'front_displaced': s['front_displaced']})
    return rows


# item 3 of part 2: one ASSUMED term per run, each a comparison and not a result
SENSITIVITY = [
    ('tail rule hard length 3.0 mm', {'hard': 3.0}),
    ('tail rule hard length 2.0 mm', {'hard': 2.0}),
    ('tail rule hard length 1.0 mm', {'hard': 1.0}),
    ('field growth against panel pads 0.10 mm', {'panel_growth': 0.10}),
    ('field growth against panel pads 0 mm', {'panel_growth': 0.0}),
    ('search radius 36 mm', {'radius': 36.0}),
    ('search radius unbounded over the front board (2.0 mm grid; refined within 36 mm)', {'radius': None, 'refine_radius': 36.0}),
]

_WORKER = {}


def _worker_inputs(root):
    if root not in _WORKER:
        inp = load_inputs(root)
        _WORKER[root] = (inp, gate_sites(inp), links.post_keepout_k(inp['root']))
    return _WORKER[root]


def _task(task):
    kind, root, label, flags, extra = task
    inp, sites, post_k = _worker_inputs(root)
    if kind == 'field':
        return kind, label, study_field_runs(inp, inp['gopts'])
    _, ctx, out, s, _ = gate_run(inp, sites, dict(flags, analyse=False), post_k)
    if kind == 'cause':
        st = _step(label, s)
        if extra:
            st['trim_leads'] = s['trim_leads']
        return kind, label, st
    # sensitivity: how many of the links without a place on the 2.0 mm grid of the record still have none
    site_of = {m: r for r in out for m in r['members']}
    rows = []
    for lid, members in extra:
        hold = {site_of[m]['id']: site_of[m] for m in members}
        ok = all(h['placed'] for h in hold.values())
        rows.append({'link': lid, 'placed': ok,
                     'slot_distance_from_centre_mm': max(h['slot_distance_from_centre_mm'] for h in hold.values()) if ok else None})
    return kind, label, dict(_step(label, s), trim_leads=s['trim_leads'], links_of_part1=rows,
                             remaining_of_part1=sum(1 for r in rows if not r['placed']))


def nearest_legal(ctx, placed, r, step):
    """Distance from the link centre of the nearest legal place, unbounded over its front board (refined grid)."""
    front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
    spare = ctx.spare(front, size)
    gm = GeoMaker(size, ctx.opts, ctx.hard)
    for off in ctx.grid(step, front, centre, None):
        dist = math.hypot(*off)
        sx, sy = r4(centre[0] + off[0]), r4(centre[1] + off[1])
        for d in DIRS:
            why, c = candidate(ctx, placed, front, size, own, sx, sy, d, dist, spare, True, gm)
            if not why:
                return {'distance_mm': r4(dist), 'slot_centre': [sx, sy], 'direction': DIR_NAMES[d], 'grid_mm': step}
    return None


def generate(root=sg.ROOT, causes=True, processes=4):
    inp = load_inputs(root)
    sites = gate_sites(inp)
    post_k = links.post_keepout_k(inp['root'])
    model, ctx, out, s, refs = gate_run(inp, sites, {}, post_k)
    part1 = [(r['id'], r['members']) for r in out if 'refinement' in r]
    rg = inp['gopts']['refinement']
    doc = {'provenance': {'generator': 'scripts/stack/geometry/links_gate.py', 'regenerate': REGEN,
                          'input_sha256': input_hashes(inp)},
           'schema_version': 1,
           'status': 'GATE OPTION of DS-67, attempt a7 with the refinement of part 2 (without the fixing list of ST-08, '
                     'the DS-44 JR lands and the re-placement search: attempt a8); courtyard level; unvalidated drafts; '
                     'nothing selected',
           'signals': {'total': len(sum((x['signals'] for x in sites), [])),
                       'by_joint': {j: sum(len(x['signals']) for x in sites if x['joint'] == j) for j in JOINTS},
                       'by_class': _by_class(sites),
                       'classes': [{'site': x['id'], 'net': n, 'class': c} for x in sites
                                   for n, c in zip(x['signals'], x['classes'])]},
           'fixings': {'source': 'stack-candidate.json (option study list; attempt a8 reads design/stack/fixings/'
                                 'fixing-sites.json)', 'count': len(model.fixings),
                       'by_kind': _count(f['kind'] for f in model.fixings)},
           'search': {'step_mm': val(inp['opts']['search']['step_mm']), 'radius_mm': val(inp['opts']['search']['radius_mm']),
                      'tail_step_mm': ctx.step, 'tail_rule_hard_mm': ctx.hard,
                      'spare_mm': {'%s, %s' % (f, z['cable']): ctx.spare(f, fh12_size(z['circuits'], inp['gopts']))
                                   for f in FRONTS + ADAPTERS for z in inp['gopts']['sizes']},
                      'refinement': {'grids_mm': val(rg['grids_mm']), 'quarter_grid_below_mm': val(rg['quarter_grid_below_mm']),
                                     'rule': rg['rule'], 'improvement': {
                                         'rounds': val(rg['improvement']['rounds']),
                                         'allowance': val(rg['improvement']['allowance']),
                                         'candidates_per_link': val(rg['improvement']['candidates_per_link']),
                                         'rule': rg['improvement']['rule']},
                                     'links_without_a_place_on_the_2_mm_grid': len(part1),
                                     'found_on_finer_grid': {str(g): sum(1 for r in out if (r.get('refinement') or {}).get('by') == 'finer grid'
                                                                         and r['refinement']['grid_mm'] == g) for g in val(rg['grids_mm'])},
                                     'found_by_improvement_pass': sum(1 for r in out if (r.get('refinement') or {}).get('by') == 'improvement pass'),
                                     'links_moved_by_improvement_pass': sum(1 for r in out if 'moved_by_improvement' in r),
                                     'remaining': sum(1 for r in out if not r['placed'])}},
           'summary': s,
           'adapters_at_8': adapter_small_check(ctx, out, sites),
           'nearest_legal_unbounded': {r['id']: nearest_legal(ctx, placed_index(out), r, val(rg['grids_mm'])[0])
                                       for r in out if not r['placed']},
           'refs': refs,
           'links': out}
    if causes:
        root = str(inp['root'])
        # the longest runs first, so that the pool finishes together
        tasks = [('sens', root, label, flags, part1) for label, flags in SENSITIVITY[::-1]]
        tasks += [('field', root, 'field', None, None)]
        tasks += [('cause', root, label, flags, False) for label, flags in CAUSES]
        tasks += [('cause', root, TRADE[0], TRADE[1], True)]
        if processes > 1:
            import multiprocessing
            with multiprocessing.Pool(processes) as pool:
                res = pool.map(_task, tasks, chunksize=1)
        else:
            res = [_task(x) for x in tasks]
        doc['field_change'] = next(r for k, _, r in res if k == 'field')
        doc['causes'] = [r for k, _, r in res if k == 'cause']
        doc['sensitivity'] = [r for k, _, r in res if k == 'sens'][::-1]
    return doc


def _step(label, s):
    return {'step': label, 'links': s['links'], 'placed': s['placed'], 'unplaced': s['unplaced'],
            'K_displaced': s['K_displaced']['total'], 'front_displaced': s['front_displaced'],
            'lengthened_tails': s['lengthened_tails'], 'tails_over_panel_hardware': s['front_tails_over_panel_hardware']}


def _count(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def _by_class(sites):
    return _count(c for s in sites for c in s['classes'])


def render(doc):
    return json.dumps(doc, indent=1) + '\n'


# ---------------------------------------------------------------- checker

def check(doc, inp, sites=None):
    """Errors of the gate file. Nothing recorded is trusted: geometry is rebuilt from slot centre, direction, size and
    tail extensions; the allocation, cable length and displaced lists are recomputed; each placed link is re-screened
    against every other placed link. It proves legality, not that a larger size would not have placed."""
    sites = sites or gate_sites(inp)
    site_by = {s['id']: s for s in sites}
    flags = dict(FULL)
    model = GateModel(inp, sites, adapters=True)
    ctx = Ctx(inp, model, flags)
    errs = []
    seen_sites, seen_sig = [], {}
    pl = [r for r in doc['links'] if r['placed']]
    for r in doc['links']:
        tag = r['id']
        n = r['circuits']
        size = fh12_size(n, inp['gopts'], {'cable': r['cable'], 'cable_length_mm': r['cable_length_mm']})
        ok_cables = {(z['cable'], z['cable_length_mm']) for z in inp['gopts']['sizes'] if z['circuits'] == n}
        if n == 8:
            ok_cables.add((inp['gopts']['adapter_short_cable']['cable'], inp['gopts']['adapter_short_cable']['cable_length_mm']))
        if (r['cable'], r['cable_length_mm']) not in ok_cables:
            errs.append('%s: cable %s %s mm is not the stock cable of %d circuits' % (tag, r['cable'], r['cable_length_mm'], n))
        seen_sites += r['members']
        want = sorted((nn, c, m) for m in r['members'] for nn, c in zip(site_by[m]['signals'], site_by[m]['classes']))
        pos = r['positions']
        got = sorted((p['net'], p['class'], p['site']) for p in pos if p['kind'] == 'signal')
        if got != want:
            errs.append('%s: the order does not carry exactly the signals of its sites with their classes' % tag)
        for p in pos:
            if p['kind'] == 'signal':
                k = (p['site'], p['net'])
                if k in seen_sig:
                    errs.append('%s: signal %s of %s also on %s' % (tag, p['net'], p['site'], seen_sig[k]))
                seen_sig[k] = tag
        if len(pos) != n or [p['pos'] for p in pos] != list(range(1, n + 1)):
            errs.append('%s: %d positions recorded for %d circuits' % (tag, len(pos), n))
        for e in allocation_errors(pos):
            errs.append('%s: %s' % (tag, e))
        for k in ('signals', 'grounds', 'unused'):
            v = sum(1 for p in pos if p['kind'] == {'signals': 'signal', 'grounds': 'ground', 'unused': 'unused'}[k])
            if v != r[k]:
                errs.append('%s: records %d %s, the order has %d' % (tag, r[k], k, v))
        if not r['placed']:
            continue
        d = {v: k for k, v in DIR_NAMES.items()}[r['direction']]
        g0 = r['geometry']
        geo = gate_geometry(r['slot_centre'][0], r['slot_centre'][1], d, size, inp['opts'], ef=g0['front_extension_mm'],
                            ek=g0['K_extension_mm'], hard=ctx.hard)
        for k, v in geo.items():
            rv = g0.get(k)
            if v is None and rv is None:
                continue
            if rv is None or v is None or (isinstance(v, list) and any(abs(x - y) > 1e-6 for x, y in zip(v, rv))) or \
                    (not isinstance(v, list) and abs(v - rv) > 1e-6):
                errs.append('%s: recorded %s %s differs from the rebuilt %s' % (tag, k, rv, v))
        others = links.Placed()
        for o in pl:
            if o is not r:
                add_placed(others, o['front_board'], o['geometry'], o['id'])
        own = r['front_board'] if r['joint'] == 'O-K' else None
        why = evaluate(model, others, r['front_board'], geo, ctx.web, own)
        if why:
            errs.append('%s: %s%s' % (tag, why[0], '' if why[1] is None else ' (%.4f mm)' % why[1]))
        elif displaced(model, r['front_board'], geo) != r['displaced']:
            errs.append('%s: recorded displaced lists differ from the recomputed ones' % tag)
        if trim_list(model, r['front_board'], geo) != r['trim_leads']:
            errs.append('%s: recorded trim list differs from the recomputed one' % tag)
        need = ctx.need(r['front_board'], geo['a_mm'], geo['b_mm'])
        if abs(need - r['cable_needed_mm']) > 1e-6 or abs(r4(r['cable_length_mm'] - need) - r['loop_mm']) > 1e-6:
            errs.append('%s: recorded cable length or loop differs from the recomputed %.4f mm' % (tag, need))
        if need > r['cable_length_mm'] + 1e-9:
            errs.append('%s: tails longer than the cable allows, needs %.2f mm against %.2f mm'
                        % (tag, need, r['cable_length_mm']))
    if sorted(seen_sites) != sorted(site_by):
        errs.append('sites not covered exactly once')
    if len(seen_sig) != sum(len(s['signals']) for s in sites):
        errs.append('%d signals on links, %d expected' % (len(seen_sig), sum(len(s['signals']) for s in sites)))
    return errs


# ---------------------------------------------------------------- main

def readme(doc):
    import links_gate_readme
    return links_gate_readme.render(doc)


def main(argv):
    if '--stdout' in argv:
        sys.stdout.write(render(generate(causes=False)))
        return 0
    doc = generate()
    LINK_GATE.write_text(render(doc))
    LINK_GATE_README.write_text(readme(doc))
    print('wrote', ', '.join(str(p.relative_to(sg.ROOT)) for p in (LINK_GATE, LINK_GATE_README)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
