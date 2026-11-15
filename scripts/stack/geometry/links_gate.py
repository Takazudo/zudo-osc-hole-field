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
COMPLIANCE_FILE = 'design/stack/mechanics/k-compliance-map.json'
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
    gopts = json.loads((root / 'design/stack/geometry/links/link-gate-options.json').read_text())
    le = json.loads((root / 'design/stack/link-electrical/inputs.json').read_text())
    part = json.loads((root / sg.JSON_FILES['partition']).read_text())
    fl = json.loads((root / FIXING_FILE).read_text())
    cmap = json.loads((root / COMPLIANCE_FILE).read_text())
    return {'raw': raw, 'ci': ci, 'cand': cand, 'opts': opts, 'gopts': gopts, 'class_rules': le['classes'],
            'partition': part, 'root': root, 'fixing_list': fl, 'compliance': cmap}


def input_hashes(inp):
    root = inp['root']
    paths = ['design/stack/geometry/stack-candidate.json', 'design/stack/geometry/links/link-options.json',
             'design/stack/geometry/links/link-gate-options.json', 'design/stack/geometry/check-report.json',
             'design/stack/geometry/parameters.json', sg.JSON_FILES['partition'], sg.JSON_FILES['lock']]
    paths += [sg.BOARD_FILES[k] for k in ('K',) + FRONTS + ADAPTERS] + PROGRAM
    out = {p: sg.sha256_file(root / p) for p in sorted(paths)}
    # the class rules object only, so that the link-electrical results (which read this study) are not an input
    out['design/stack/link-electrical/inputs.json#classes'] = pinned_object(inp['class_rules'])
    # the fixing list and the compliance map by the objects read, not the files (DS-89 scope a8 items 1 and 3)
    out[FIXING_FILE + '#fixings'] = pinned_object(inp['fixing_list']['fixings'])
    out[FIXING_FILE + '#access_holes'] = pinned_object(inp['fixing_list']['access_holes'])
    out[COMPLIANCE_FILE + '#inputs_sha256'] = inp['compliance']['inputs_sha256']
    out[COMPLIANCE_FILE + '#nodes'] = pinned_object(inp['compliance']['nodes'])
    return out


FIXING_FILE = 'design/stack/fixings/fixing-sites.json'


def fixing_sites_a7(inp):
    """The fixings of attempt a7 (comparison run (a) only): the option study's 18 posts and 12 kept supports of
    stack-candidate.json, with its post lands and the radii of link-options.json."""
    cand, opts = inp['cand'], inp['opts']
    posts = {p['id']: p for p in cand['posts']}
    rk, rf = opts['fixing_keepout_radius_mm']['K'], opts['fixing_keepout_radius_mm']['front']
    out = []
    for f in cand['fixings']:
        if not f['declared']:
            continue
        out.append({'id': f['id'], 'kind': f['kind'], 'K': f['xy'], 'r_K': rk,
                    'front': posts[f['id']]['proposed_front_land'] if f['id'] in posts else f['xy'],
                    'front_board': f['front_board'], 'r_front': rf, 'boards': ['K', f['front_board']]})
    return out


def fixing_sites(inp, source='list'):
    """The fixings as keep-outs. 'list': the active entries of `fixings` in design/stack/fixings/fixing-sites.json
    (ST-08 a2; DS-75, DS-76: 18 posts and four sleeves), each with its centre on K (`xy`) and on its front board
    (`front_xy`) and its keep-out radius per board; the reserve and the alternatives are no keep-outs (DS-87).
    'a7': the option study's list of attempt a7."""
    if source == 'a7':
        return fixing_sites_a7(inp)
    out = []
    for f in inp['fixing_list']['fixings']:
        if not f['active']:
            continue
        r = f['keepout_radius_mm']
        out.append({'id': f['id'], 'kind': f['kind'], 'K': f['xy'], 'r_K': r['K'], 'front': f['front_xy'],
                    'front_board': f['front_board'], 'r_front': r[f['front_board']], 'boards': list(f['boards'])})
    return out


def access_holes(inp):
    """The access holes of the fixing list (the 7.0 mm hole in EL at SLV-L2, DS-76). No link geometry lies on EL in
    this model; the hole is recorded with the keep-out of its sleeve on P that contains it."""
    out = []
    for h in inp['fixing_list']['access_holes']:
        sleeve = next(f for f in inp['fixing_list']['fixings'] if f['id'] == h['for'])
        on_p = sleeve['keepout_radius_mm'].get('P')
        d = math.hypot(h['xy'][0] - sleeve['front_xy'][0], h['xy'][1] - sleeve['front_xy'][1])
        out.append({'id': h['id'], 'board': h['board'], 'xy': h['xy'], 'diameter_mm': h['diameter_mm'],
                    'for': h['for'], 'keepout_radius_mm': h['keepout_radius_mm'],
                    'inside_P_keepout_of_its_sleeve': on_p is not None and d + h['diameter_mm'] / 2 <= on_p + 1e-9})
    return out


def pinned_object(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


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


def gate_sites(inp, rule='a8'):
    """Every site of the gate: the 191 link sites of the study and the six adapter pairs, each signal with its class.
    The adapter lines are STATIC under 'a8' (DS-79, from the schematic specification) and ANALOGUE under 'a7'."""
    kinds = partition_kinds(inp['partition'])
    rules = inp['class_rules']['rules']
    sites = links.link_sites(inp['cand'])
    for s in sites:
        s['classes'] = [classify(n, kinds, rules) for n in s['signals']]
    ad_class = inp['gopts']['adapters']['class_of_signals'][rule]
    for key, pairs in adapter_sites(inp['cand']).items():
        for p in pairs:
            f, b = p['sites']['front'], p['sites']['back']
            sig = [n for n in p['pin_map'] if n not in links.NON_SIGNAL]
            sites.append({'id': p['id'], 'family': p['family'], 'joint': 'O-K', 'front_board': key,
                          'xy': [f['center'][0], f['center'][1]], 'K_xy': b['center'], 'positions': p['positions'],
                          'signals': sig, 'classes': [ad_class] * len(sig),
                          'front_replaces': f['replaces'], 'K_replaces': b['replaces']})
    return sites


def circuits_needed(classes, rule='a8'):
    """Circuits a link needs, or None when LOGIC and WIPER would share it. 'a7': DS-62. 'a8': DS-62 with DS-77 (a run
    of two or more LOGIC lines takes a ground on each side and no outer position) and DS-79 (static adapter lines
    side by side, one ground)."""
    if 'LOGIC' in classes and 'WIPER' in classes:
        return None
    if rule == 'a8' and classes and all(c == 'STATIC' for c in classes):
        return len(classes) + 1
    a = sum(1 for c in classes if c in LOUD)
    q = len(classes) - a
    units = a + (1 if q else 0)
    extra = 1 if rule == 'a8' and classes.count('LOGIC') >= 2 and units <= 2 else 0
    return a + q + max(units - 1, 1) + extra


# DS-78: preference for the outer signal positions; a run of two or more LOGIC lines is never outer by choice (DS-77)
OUTER_RANK = {'WIPER': 0, 'LOGIC': 1, 'ANALOGUE': 2, 'PRECISION': 3}
LOGIC_RUN_RANK = 4


def unit_rank(classes):
    if classes[0] == 'LOGIC' and len(classes) >= 2:
        return LOGIC_RUN_RANK
    return OUTER_RANK.get(classes[0], 2)


def adapter_order_key(net, order):
    return order.index(net.split('/')[-1])


def allocation(signals, n, rule='a8', adapter_order=None):
    """Positions 1..n: each a signal (net, class, site), a ground or unused. 'a7': DS-62 as in attempt a7. 'a8': DS-62
    with DS-77 to DS-79 (rule text in link-gate-options.json allocation)."""
    loud = [s for s in signals if s[1] in LOUD]
    quiet = [s for s in signals if s[1] in QUIET]
    if rule == 'a8' and signals and all(s[1] == 'STATIC' for s in signals):
        by = sorted(signals, key=lambda s: adapter_order_key(s[0], adapter_order))
        seq = []
        for name in adapter_order:
            if name == 'AGND':
                seq.append(None)
            else:
                seq += [s for s in by if s[0].split('/')[-1] == name]
    else:
        units = [[s] for s in loud] + ([quiet] if quiet else [])
        if rule == 'a8' and len(units) >= 2:
            order = sorted(range(len(units)), key=lambda i: (unit_rank([x[1] for x in units[i]]), i))
            first, last = order[0], order[1]
            units = [units[first]] + [units[i] for i in range(len(units)) if i not in (first, last)] + [units[last]]
        seq = []
        for i, u in enumerate(units):
            if i:
                seq.append(None)
            seq += u
        if rule == 'a8' and units:
            if unit_rank([x[1] for x in units[0]]) == LOGIC_RUN_RANK:
                seq.insert(0, None)
            if unit_rank([x[1] for x in units[-1]]) == LOGIC_RUN_RANK:
                seq.append(None)
        if not any(x is None for x in seq):
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


def signal_units(positions):
    """Maximal runs of signal positions between grounds or unused positions: [(first pos, last pos, classes)]."""
    out, cur = [], []
    for p in positions + [{'kind': 'end'}]:
        if p['kind'] == 'signal':
            cur.append(p)
        elif cur:
            out.append((cur[0]['pos'], cur[-1]['pos'], [x['class'] for x in cur]))
            cur = []
    return out


def allocation_errors(positions, rule='a8', adapter_order=None):
    """Rule violations of one link's recorded order. 'a7': DS-62, unused positions are not grounds. 'a8': DS-62 with
    DS-77 to DS-79; an unused position is tied to AGND on both boards and counts as a ground (DS-77)."""
    errs = []
    n = len(positions)
    sig = [p for p in positions if p['kind'] == 'signal']
    classes = {p['class'] for p in sig}
    gnd = ('ground', 'unused') if rule == 'a8' else ('ground',)
    if 'LOGIC' in classes and 'WIPER' in classes:
        errs.append('LOGIC and WIPER share the link')
    if not any(p['kind'] in gnd for p in positions):
        errs.append('no ground on the link')
    static = rule == 'a8' and bool(sig) and classes == {'STATIC'}
    if 'STATIC' in classes and not static:
        errs.append('a static adapter line shares a link with another class')
    prev = None
    for p in positions:
        if p['kind'] in gnd:
            prev = None
        elif p['kind'] == 'signal':
            if prev is not None and not (prev['class'] == p['class'] and p['class'] in QUIET + (('STATIC',) if static else ())):
                errs.append('%s (%s) beside %s (%s) without a ground' % (prev['net'], prev['class'], p['net'], p['class']))
            prev = p
    if rule != 'a8':
        return errs
    if static:
        want = [x for x in adapter_order]
        got = []
        for p in positions:
            if p['kind'] == 'signal':
                got.append(p['net'].split('/')[-1])
            elif p['kind'] == 'ground':
                got.append('AGND')
            else:
                got.append(None)
        if n != len(want) or got != want:
            errs.append('adapter order %s is not the ruled order %s (DS-79)' % (got, want))
        return errs
    units = signal_units(positions)
    for a, b, cl in units:
        if cl[0] == 'LOGIC' and len(cl) >= 2 and (a == 1 or b == n):
            errs.append('a run of %d LOGIC lines takes position %d, an outer position (DS-77)' % (len(cl), 1 if a == 1 else n))
    if len(units) >= 2:
        ranks = sorted(unit_rank(cl) for _, _, cl in units)
        ends = sorted((unit_rank(units[0][2]), unit_rank(units[-1][2])))
        if ends != ranks[:2]:
            errs.append('outer signal positions carry %s and %s, the preference of DS-78 asks for ranks %s'
                        % (units[0][2][0], units[-1][2][-1], ranks[:2]))
    return errs


def gate_cluster(sites, n, join_radius, prefix, rule='a8'):
    """The study's greedy clustering (links.cluster) with DS-62 feasibility in place of an additive capacity. A site
    that alone needs more than n circuits forms its own cluster marked `oversize` (it gets no place at n)."""
    rem = sorted(sites, key=lambda s: s['id'])
    out = []
    k = 0
    while rem:
        cx, cy = links._centroid(rem)
        seed = min(rem, key=lambda s: (-round(math.hypot(s['xy'][0] - cx, s['xy'][1] - cy), 6), s['id']))
        members = [seed]
        rem.remove(seed)
        need0 = circuits_needed(seed['classes'], rule)
        if need0 is None or need0 > n:
            k += 1
            out.append({'id': '%s%02d' % (prefix, k), 'centre': [r4(seed['xy'][0]), r4(seed['xy'][1])],
                        'members': [seed['id']], 'site_distances_mm': [0.0], 'oversize': need0})
            continue
        cls = list(seed['classes'])
        while True:
            mx, my = links._centroid(members)
            cands = []
            for s in rem:
                d = round(math.hypot(s['xy'][0] - mx, s['xy'][1] - my), 6)
                if d > join_radius:
                    continue
                need = circuits_needed(cls + s['classes'], rule)
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
    conn = next(z for z in gopts['sizes'] if z['circuits'] == n)['connector'] if any(
        z['circuits'] == n for z in gopts['sizes']) else 'FH12-%dS-0.5SH(55)' % n
    return {'id': 'FH12-N%d' % n, 'pitch_mm': 0.5, 'circuits': n, 'connector': conn,
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

    def __init__(self, inp, sites, adapters=True, fixings='list', compliance=True):
        super().__init__(inp, [s for s in sites if s['joint'] != 'O-K'])
        ci, opts = inp['ci'], inp['opts']
        self.compliance = ComplianceMap(inp['compliance'], inp['gopts']['compliance']) if compliance else None
        self.lib = {f['ref']: f['lib'] for f in ci['boards']['K']}
        self.memos, self.memo, self._polys = {}, {}, {}
        drop_labels = ('fixing keep-out',) + (('kept rigid pair',) if adapters else ())
        for key in list(self.forb):
            idx = sg.RectIndex()
            for rect, payload in self.forb[key].items:
                if not payload[2].startswith(drop_labels):
                    idx.add(rect, payload)
            self.forb[key] = idx
        self.fixings = fixing_sites(inp, fixings)
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

    # ---- exact fast paths (scope a8 item 7): the same results as stackgeom.rect_inside_poly and links.Model, with a
    # memo per link that the search, the refinement, the improvement pass and the analysis share

    def memo_for(self, lid):
        """Use the memo of link `lid` (None: a fresh one that is dropped after use)."""
        self.memo = self.memos.setdefault(lid, {}) if lid is not None else {}
        return self.memo

    def drop_memo(self, lid):
        self.memos.pop(lid, None)

    def _prep(self, key):
        poly = self.outline[key]
        edges, rect_ok = [], True
        n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if x1 == x2 and y1 != y2:
                edges.append((x1, min(y1, y2), max(y1, y2)))
            elif y1 != y2:
                rect_ok = False
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        self._polys[key] = (edges if rect_ok else None, (min(xs), min(ys), max(xs), max(ys)), poly)
        return self._polys[key]

    def _pip(self, x, y, prep):
        edges, bb, poly = prep
        if edges is None:
            return sg.point_in_poly(x, y, poly)
        if x < bb[0] or x > bb[2] or y < bb[1] or y > bb[3]:
            return False
        c = False
        for ex, lo, hi in edges:
            # a vertical edge: the crossing test of stackgeom.point_in_poly reduces to lo <= y < hi and x < ex
            if lo <= y < hi and x < ex:
                c = not c
        return c

    def inside(self, key, rect, margin=0.0):
        mk = ('in', key, rect[0], rect[1], rect[2], rect[3], margin)
        m = self.memo
        if mk in m:
            return m[mk]
        prep = self._polys.get(key) or self._prep(key)
        r = sg.grow(rect, margin)
        eps = 1e-6
        ok = True
        for x, y in ((r[0] + eps, r[1] + eps), (r[2] - eps, r[1] + eps), (r[2] - eps, r[3] - eps), (r[0] + eps, r[3] - eps)):
            if not self._pip(x, y, prep):
                ok = False
                break
        if ok:
            ok = not any(r[0] + eps < x < r[2] - eps and r[1] + eps < y < r[3] - eps for x, y in prep[2])
        m[mk] = ok
        return ok

    def forbidden(self, key, face, rect, tail=False):
        mk = ('fb', key, face, rect[0], rect[1], rect[2], rect[3], tail)
        m = self.memo
        if mk not in m:
            m[mk] = links.Model.forbidden(self, key, face, rect, tail)
        return m[mk]

    def between_hit_for(self, rect, own):
        mk = ('bw', rect[0], rect[1], rect[2], rect[3], own)
        m = self.memo
        if mk not in m:
            m[mk] = self._between_hit_for(rect, own)
        return m[mk]

    def _between_hit_for(self, rect, own):
        for r, label, key in self.between_owned:
            if key is not None and key == own:
                continue
            if sg.inter(rect, r):
                return (label, r4(sg.overlap_depth(rect, r)))
        return None


# ---------------------------------------------------------------- screens, split by the side they depend on

def check_slot(model, placed, front, geo, web, own):
    slot = geo['slot']
    if not model.inside('K', slot, web):
        return ('slot within %.1f mm of the K edge or outside K' % web, None)
    if not model.inside(front, slot, 0.0):
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


def check_front(model, placed, front, geo, own):
    fc, ft, first = geo['front_connector'], geo['front_tail'], geo['front_tail_first']
    if not model.inside(front, fc, model.margin):
        return ('front field outside the %s outline less %.2f mm' % (front, model.margin), None)
    if not model.inside(front, ft, 0.0):
        return ('front tail not under its own front board %s' % front, None)
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
    if not model.inside('K', kc, model.margin):
        return ('K field outside the K outline less %.2f mm' % model.margin, None)
    if model.compliance is not None:
        v = model.compliance.value(kc)
        if v > model.compliance.limit + 1e-12:
            return ('K field above %g mm/N on the compliance map (DS-87)' % model.compliance.limit, None)
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


def evaluate(model, placed, front, geo, web, own):
    """(reason, depth) or None for one complete candidate; the search and the checker share these screens."""
    return check_slot(model, placed, front, geo, web, own) or check_front(model, placed, front, geo, own) or \
        check_k(model, placed, geo)


def displaced(model, front, geo, latch=None):
    """Footprints a link displaces. `latch` (mm, DS-88): a K-rear footprint within that distance of the K connector
    field, not under the field and not of an exempt package, is displaced like one under the field."""
    field = model.displaced('K', 'B', geo['K_connector'])
    out = {'front B': sorted(model.displaced(front, 'B', geo['front_connector'])),
           'K F (slot)': sorted(model.displaced('K', 'F', geo['slot'])),
           'K B (slot)': sorted(model.displaced('K', 'B', geo['slot'])),
           'K B (field)': sorted(field)}
    if latch is not None:
        near = model.displaced('K', 'B', sg.grow(geo['K_connector'], latch)) - field
        out['K B (latch)'] = sorted(r for r in near if not latch_exempt(model.lib.get(r, '')))
    return out


CHIP = re.compile(r'^[RCL](\d{4,5})$')
CHIP_SIZES = ('01005', '0201', '0402', '0603')


def k_union(disp):
    return set().union(*(disp[k] for k in K_KEYS if k in disp))


K_KEYS = ('K F (slot)', 'K B (slot)', 'K B (field)', 'K B (latch)')


def latch_exempt(lib):
    """DS-88: a chip part of 0603 size or smaller, a SOD-123 or a SOT-23 (ASSUMED lower than the 2.0 mm connector
    body). The package is the footprint name of the board file (`lib`, e.g. R0603, SOT-23)."""
    m = CHIP.match(lib)
    return bool(m and m.group(1) in CHIP_SIZES) or lib in ('SOD-123', 'SOT-23')


class ComplianceMap:
    """The retained compliance map of K (ST-03 a6). The value of a K connector is the largest mm_per_N over the
    nodes inside its K field grown by the map pitch on every side (DS-87 reading set for a8)."""

    def __init__(self, cmap, copts):
        self.pitch = cmap['inputs']['map_pitch_mm']
        self.limit = val(copts['limit_mm_per_N'])
        self.list_above = val(copts['list_above_mm_per_N'])
        cols = cmap['columns']
        ix, iy, iv = cols.index('x_mm'), cols.index('y_mm'), cols.index('mm_per_N')
        self.cell = 8.0
        self.buckets = {}
        for n in cmap['nodes']:
            x, y, v = n[ix], n[iy], n[iv]
            self.buckets.setdefault((int(x // self.cell), int(y // self.cell)), []).append((x, y, v))
        self._memo = {}

    def value(self, rect):
        key = tuple(rect)
        if key in self._memo:
            return self._memo[key]
        g = sg.grow(rect, self.pitch)
        best = None
        for i in range(int(g[0] // self.cell), int(g[2] // self.cell) + 1):
            for j in range(int(g[1] // self.cell), int(g[3] // self.cell) + 1):
                for x, y, v in self.buckets.get((i, j), ()):
                    if g[0] - 1e-9 <= x <= g[2] + 1e-9 and g[1] - 1e-9 <= y <= g[3] + 1e-9 and (best is None or v > best):
                        best = v
        self._memo[key] = best if best is not None else 0.0
        return self._memo[key]


def trim_list(model, front, geo):
    """Panel-hardware pads under the front tail beyond its first 4.0 mm: leads to trim (DS-61)."""
    ft = geo['front_tail']
    return sorted({lab.split(' ')[-1] for _, (kind, g, lab) in model.forb[(front, 'B')].near(ft)
                   if kind == 'rect' and lab.startswith('panel hardware') and sg.inter(ft, g)})


add_placed = links.add_placed


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
        self.radius = val(self.opts['search']['radius_mm'])
        self._grids = {}
        self.rule = flags['allocation']
        self.cmap = model.compliance or ComplianceMap(inp['compliance'], self.gopts['compliance'])
        self.adapter_order = list(self.gopts['adapters']['order'])
        self.latch = val(self.opts['latch_access_margin_mm']) if flags['latch_rule'] else None
        # the field courtyard grows 0.25 mm per side over body and land; a run may grow it less against panel pads
        self.gaps = self.cand['stack']['mated_heights_mm']
        self.k_th = round(self.cand['stack']['K_face_z_mm'] - self.cand['stack']['K_rear_z_mm'], 4)
        self.hard = val(self.gopts['tail_rule']['hard_mm'])
        self.step = val(self.gopts['tail_lengthening']['step_mm'])
        self.a0 = val(self.opts['cable']['straight_stiffened_outside_mm']) + val(self.opts['cable']['bend_radius_mm'])

    def evaluate(self, placed, front, geo, own):
        return evaluate(self.model, placed, front, geo, self.web, own)

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
        why = check_front(model, placed, front, gm.front(sx, sy, d, e), own)
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
    disp = displaced(model, front, geo, ctx.latch)
    k_refs = k_union(disp)
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


# ---------------------------------------------------------------- placement of the gate option

def link_record(ctx, lid, joint, front, members, site_by, size):
    sig = [(n, c, m) for m in members for n, c in zip(site_by[m]['signals'], site_by[m]['classes'])]
    classes = [c for _, c, _ in sig]
    n = size['circuits']
    need = circuits_needed(classes, ctx.rule)
    pos = allocation(sig, n, ctx.rule, ctx.adapter_order) if need is not None and need <= n else []
    return {'id': lid, 'joint': joint, 'front_board': front, 'members': list(members),
            'signals': len(sig), 'grounds': sum(1 for p in pos if p['kind'] == 'ground'),
            'unused': sum(1 for p in pos if p['kind'] == 'unused'), 'circuits_needed': need,
            'size': size['id'], 'circuits': n, 'connector': size['connector'], 'cable': size['cable'],
            'cable_length_mm': size['cable_length_mm'], 'positions': pos}


def place(ctx, placed, rec, size, centre, own, offsets=None, grid=None, best=None):
    tally = {}
    ctx.model.memo_for(rec['id'])
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
    ctx.model.drop_memo(rec['id'])
    rec.update({'placed': True, 'centre': centre, 'slot_centre': [sx, sy], 'direction': DIR_NAMES[d],
                'slot_distance_from_centre_mm': r4(dist), 'geometry': geo, 'displaced': disp,
                'lengthened_tail': lengthened, 'placed_only_with_lengthened_tail': only,
                'trim_leads': trim_list(ctx.model, front, geo),
                'under_tails': links.under_tails(ctx.model, front, geo),
                'cable_needed_mm': need, 'loop_mm': r4(size['cable_length_mm'] - need),
                'grid_mm': grid or ctx.step0, 'cost': r4(best[0]),
                'compliance_mm_per_N': r4(ctx.cmap.value(geo['K_connector']))})
    return True, tally


def adapter_sizes(ctx):
    """Sizes tried per adapter link, in order: 'a8' (DS-79) 8 circuits on C81339 at 40 mm, then C29534 at 50 mm;
    'a7' one 14-circuit link."""
    if ctx.rule == 'a8':
        return [fh12_size(8, ctx.gopts, ctx.gopts['adapter_short_cable']), fh12_size(8, ctx.gopts)]
    return [fh12_size(ctx.gopts['adapters']['circuits_a7'], ctx.gopts)]


def place_gate(inp, sites, flags):
    """Place the gate option; `flags` select the inputs of a run (the record or a comparison of the chain)."""
    model = GateModel(inp, sites, fixings=flags['fixings'], compliance=flags['compliance'])
    ctx = Ctx(inp, model, flags)
    gopts, opts = inp['gopts'], inp['opts']
    site_by = {s['id']: s for s in sites}
    jr = val(opts['clustering']['join_radius_mm'])
    placed = links.Placed()
    out = []
    joint_sizes = {j: list(gopts['joints'][j]) for j in ('JL-K', 'JR-K', 'P-K', 'JL-P via K')}
    for key in gopts['adapters']['boards']:
        mem = sorted(s['id'] for s in sites if s['joint'] == 'O-K' and s['front_board'] == key)
        centre = [r4(c) for c in links._centroid([site_by[m] for m in mem])]
        tried = []
        for size in adapter_sizes(ctx):
            rec = link_record(ctx, 'O-K-%s' % key, 'O-K', key, mem, site_by, size)
            tried.append('%s %s %g mm' % (size['id'], size['cable'], size['cable_length_mm']))
            ok, _ = place(ctx, placed, rec, size, centre, key)
            if ok:
                break
        rec['cables_tried'] = tried
        if not ok:
            rec.update({'placed': False, 'centre': centre, 'no_place': 'no place on %s: the rigid pairs stay the named '
                        'exception of DS-64' % ' or '.join(tried)})
        out.append(rec)
    for joint in ('JL-K', 'JR-K', 'P-K', 'JL-P via K'):
        ladder = joint_sizes[joint]
        js = [s for s in sites if s['joint'] == joint]
        for front in sorted({s['front_board'] for s in js}):
            fs = [s for s in js if s['front_board'] == front]
            prefix = '%s-%s-L' % (joint.replace(' ', '').replace('via', '-'), front)
            for c in gate_cluster(fs, ladder[0], jr, prefix, ctx.rule):
                _place_ladder(ctx, placed, out, joint, front, c, ladder, 0, site_by, jr)
    refine(ctx, placed, out)
    placed = improve(ctx, out)
    for r in out:
        if not r['placed']:
            ctx.model.memo_for(r['id'])
            r['nearest_misses'], r['most_frequent_blockers'] = misses_and_blockers(ctx, placed, r)
            r['why_no_place'] = why_no_place(ctx, placed, r)
            ctx.model.drop_memo(r['id'])
    ctx.model.memos.clear()
    ctx.model.memo_for(None)
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
    """Every link without a place on the 2.0 mm grid is searched again on 0.5 mm, and on 0.25 mm where its smallest
    miss on 0.5 mm is below 0.5 mm; placed links fixed, rules, sizes, radius and cost unchanged."""
    rg = ctx.gopts['refinement']
    g1, g2 = val(rg['grids_mm'])
    thr = val(rg['quarter_grid_below_mm'])
    for r in out:
        if r['placed'] or r.get('oversize'):
            continue
        front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
        ctx.model.memo_for(r['id'])
        tried, miss, best = [], None, None
        for g in (g1, g2):
            if g == g2 and (miss is None or miss >= thr):
                break
            offs = ctx.grid(g, front, centre)
            best, tally = search(ctx, placed, front, centre, size, own, offsets=offs)
            tried.append(g)
            if best:
                place(ctx, placed, r, size, centre, own, offsets=offs, grid=g, best=best)
                r['refinement'] = {'found': True, 'by': 'finer grid', 'grid_mm': g, 'grids_tried_mm': tried}
                break
            miss = smallest_miss(tally)
        if not best:
            r['refinement'] = {'found': False, 'grids_tried_mm': tried, 'smallest_miss_mm': miss}


def _bbox(rects):
    rs = [x for x in rects if x]
    return [min(x[0] for x in rs), min(x[1] for x in rs), max(x[2] for x in rs), max(x[3] for x in rs)]


def geo_bbox(geo):
    return _bbox([geo[k] for k in ('slot', 'front_connector', 'front_tail', 'K_tail', 'K_connector')])


def improve(ctx, out):
    """The bounded improvement pass (rule in link-gate-options.json refinement.improvement). A legal candidate that no
    placed link blocks (freed by an earlier move) is taken at once (finding 12). A blocking link is moved only when
    its new cost stays within the allowance above its cost before the pass, and every move is recorded (finding 14)."""
    ip = ctx.gopts['refinement']['improvement']
    g1 = val(ctx.gopts['refinement']['grids_mm'])[0]
    cap = val(ip['candidates_per_link'])
    allowance = val(ip['allowance'])
    base = {r['id']: r['cost'] for r in out if r['placed']}
    reach = 2 * ctx.web + 1.0
    for rnd in range(1, val(ip['rounds']) + 1):
        changed = False
        for u in [r for r in out if not r['placed'] and not r.get('oversize')]:
            front, size, own, centre = u['front_board'], rec_size(ctx, u), rec_own(u), u['centre']
            ctx.model.memo_for(u['id'])
            offs = ctx.grid(g1, front, centre)
            cands, _ = search(ctx, links.Placed(), front, centre, size, own, offsets=offs, collect=cap)
            pl = [r for r in out if r['placed']]
            boxes = {b['id']: geo_bbox(b['geometry']) for b in pl}
            tried = set()
            for c in cands:
                geo = c[2]
                cb = sg.grow(geo_bbox(geo), reach)
                blockers = []
                for b in pl:
                    if not sg.inter(cb, boxes[b['id']]):
                        continue
                    one = links.Placed()
                    add_placed(one, b['front_board'], b['geometry'], b['id'])
                    if ctx.evaluate(one, front, geo, own):
                        blockers.append(b)
                        if len(blockers) > 1:
                            break
                if not blockers:
                    allp = placed_index(out)
                    if ctx.evaluate(allp, front, geo, own):
                        raise AssertionError('unblocked candidate of %s is illegal' % u['id'])
                    place(ctx, allp, u, size, centre, own, offsets=offs, grid=g1, best=c)
                    base[u['id']] = u['cost']
                    u['refinement'] = {'found': True, 'by': 'improvement pass (place freed by an earlier move)',
                                       'round': rnd, 'grid_mm': g1, 'moved': None}
                    changed = True
                    break
                if len(blockers) != 1 or blockers[0]['id'] in tried:
                    continue
                b = blockers[0]
                tried.add(b['id'])
                others = placed_index(out, skip={b['id']})
                add_placed(others, front, geo, u['id'])
                bsize = rec_size(ctx, b)
                boffs = ctx.grid(g1, b['front_board'], b['centre'])
                limit = r4(base[b['id']] + allowance)
                ctx.model.memo_for(None)
                nb, _ = search(ctx, others, b['front_board'], b['centre'], bsize, rec_own(b), offsets=boffs, limit=limit)
                ctx.model.memo_for(u['id'])
                if not nb:
                    continue
                old = {'slot_centre': b['slot_centre'], 'direction': b['direction'], 'cost': b['cost'], 'grid_mm': b['grid_mm']}
                moves = b.get('moves_by_improvement', [])
                place(ctx, others, b, bsize, b['centre'], rec_own(b), offsets=boffs, grid=g1, best=nb)
                b['moves_by_improvement'] = moves + [dict(old, round=rnd, to_free_a_place_for=u['id'], new_cost=b['cost'],
                                                          cost_before_the_pass=base[b['id']], limit=limit)]
                allp = placed_index(out, skip={u['id']})
                if ctx.evaluate(allp, front, geo, own):
                    raise AssertionError('improvement pass left %s illegal' % u['id'])
                place(ctx, allp, u, size, centre, own, offsets=offs, grid=g1, best=c)
                base[u['id']] = u['cost']
                u['refinement'] = {'found': True, 'by': 'improvement pass', 'round': rnd, 'grid_mm': g1, 'moved': b['id']}
                changed = True
                break
        if not changed:
            break
    return placed_index(out)


def corridor(model, front, rect, axis, reach=30.0):
    """Free span between panel-hardware pads through `rect` along `axis` (0: x, 1: y), within the band that the
    rect covers across it. Returns free, needed and the gap from each side of the rect to its bounding pad; a side
    with no pad within `reach` mm is open (its gap None), and free is then None (finding 18)."""
    lo_i, hi_i = (0, 2) if axis == 0 else (1, 3)
    blo, bhi = (1, 3) if axis == 0 else (0, 2)
    c = (rect[lo_i] + rect[hi_i]) / 2
    probe = list(rect)
    probe[lo_i], probe[hi_i] = c - reach, c + reach
    left, right = None, None
    for _, (kind, g, label) in model.forb[(front, 'B')].near(probe):
        if kind != 'rect' or not label.startswith('panel hardware'):
            continue
        if g[bhi] <= rect[blo] or g[blo] >= rect[bhi] or g[hi_i] < c - reach or g[lo_i] > c + reach:
            continue
        if (g[lo_i] + g[hi_i]) / 2 < c:
            left = g[hi_i] if left is None else max(left, g[hi_i])
        else:
            right = g[lo_i] if right is None else min(right, g[lo_i])
    return {'free': None if left is None or right is None else r4(right - left), 'needed': r4(rect[hi_i] - rect[lo_i]),
            'gap_low_mm': None if left is None else r4(rect[lo_i] - left),
            'gap_high_mm': None if right is None else r4(right - rect[hi_i])}


STAGES = ('the field', 'the first {hard} mm of the tail', 'the rest of the front tail', 'the slot on K', 'the K side')


def staged(ctx, placed, front, gm, sx, sy, d, e, spare, own):
    """(stage, reason, depth) of one candidate with front extension e: the first stage it fails, 5 when legal, None
    when its field leaves the front board's margins. Every rejection is kept, with or without a depth (finding 11)."""
    model = ctx.model
    fr = gm.front(sx, sy, d, e)
    fc, ft, first = fr['front_connector'], fr['front_tail'], fr['front_tail_first']
    if not model.inside(front, fc, model.margin):
        return None
    h = model.forbidden(front, 'B', fc) or model.between_hit_for(fc, own) or placed.hit(front, 'B', fc) or \
        placed.hit(front, 'S', fc)
    if h:
        return 0, h[0], h[1]
    h = model.forbidden(front, 'B', first) if first else None
    if h:
        return 1, h[0], h[1]
    h = check_front(model, placed, front, fr, own)
    if h:
        return 2, h[0], h[1]
    h = check_slot(model, placed, front, gm.slot(sx, sy, d), ctx.web, own)
    if h:
        return 3, h[0], h[1]
    first_k = None
    for k in ctx.extensions(r4(spare - e)):
        h = check_k(model, placed, gm.k(sx, sy, d, k))
        if h is None:
            return 5, 'legal', 0.0
        first_k = first_k or h
    return 4, (first_k or ('cable too short for the K tail', None))[0], (first_k or (None, None))[1]


def why_no_place(ctx, placed, r):
    """On the finest grid searched for the link, against the final placed set: the deepest stage any candidate
    reaches, the smallest penetration at that stage (None when no rejection there has a depth) with its screen, the
    count of candidates there, and the free corridors at that candidate."""
    if r.get('oversize'):
        return {'lacks': 'circuits: %s' % r['no_place']}
    model = ctx.model
    front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
    g = (r.get('refinement') or {}).get('grids_tried_mm', [ctx.step0])[-1]
    spare = ctx.spare(front, size)
    gm = GeoMaker(size, ctx.opts, ctx.hard)
    best, count = {}, {}
    for off in ctx.grid(g, front, centre):
        sx, sy = r4(centre[0] + off[0]), r4(centre[1] + off[1])
        for d in DIRS:
            for e in ctx.extensions(spare):
                res = staged(ctx, placed, front, gm, sx, sy, d, e, spare, own)
                if res is None:
                    continue
                stage, label, pen = res
                count[stage] = count.get(stage, 0) + 1
                cur = best.get(stage)
                key = (pen is None, pen if pen is not None else 0.0)
                if cur is None or key < cur[0]:
                    best[stage] = (key, pen, label, (sx, sy), d, e)
    if not best:
        return {'lacks': 'no candidate inside the board margins', 'grid_mm': g}
    stage = max(best)
    if stage == 5:
        raise AssertionError('%s has a legal candidate in why_no_place' % r['id'])
    _, pen, label, slot, d, e = best[stage]
    geo = gm.full(slot[0], slot[1], d, e, 0.0)
    fc = geo['front_connector']
    out = {'lacks': STAGES[stage].format(hard='%g' % ctx.hard), 'stage': stage, 'grid_mm': g,
           'smallest_penetration_mm': pen, 'blocker': label, 'candidates_at_stage': count[stage],
           'at': {'slot_centre': list(slot), 'direction': DIR_NAMES[d], 'front_extension_mm': e},
           'field_corridor_mm': {'x': corridor(model, front, fc, 0), 'y': corridor(model, front, fc, 1)}}
    if stage >= 1 and geo['front_tail_first']:
        ax = 0 if DIR_NAMES[d] in ('+x', '-x') else 1
        out['tail_corridor_mm'] = {'across': corridor(model, front, geo['front_tail_first'], 1 - ax),
                                   'first_length_needed': ctx.hard}
    return out


def _place_ladder(ctx, placed, out, joint, front, c, ladder, k, site_by, jr):
    size = fh12_size(ladder[k], ctx.gopts)
    rec = link_record(ctx, c['id'], joint, front, c['members'], site_by, size)
    if 'oversize' not in c:
        ok, _ = place(ctx, placed, rec, size, c['centre'], None)
        if ok:
            rec['sizes_tried'] = ladder[:k + 1]
            out.append(rec)
            return
        if k + 1 < len(ladder):
            for sub in gate_cluster([site_by[m] for m in c['members']], ladder[k + 1], jr, c['id'] + '.', ctx.rule):
                _place_ladder(ctx, placed, out, joint, front, sub, ladder, k + 1, site_by, jr)
            return
        why = 'no place as a stock link at %d circuits' % ladder[k]
    else:
        why = 'its site needs %s circuits, more than the %d of the size' % (c['oversize'], ladder[k])
    rec.update({'placed': False, 'centre': c['centre'], 'sizes_tried': ladder[:k + 1], 'no_place': why,
                'sites': [{'site': m, 'xy': site_by[m]['xy'], 'signals': site_by[m]['signals'],
                           'classes': site_by[m]['classes']} for m in c['members']]})
    if 'oversize' in c:
        rec['oversize'] = True
    out.append(rec)


def misses_and_blockers(ctx, placed, r, k=3):
    """For a link without a place, against the final placed set: the k candidates nearest its centre on the 2.0 mm
    grid with the screen that rejects each, and the three most frequent screens of its search. Outline, K-edge and
    own-front-board rejections are left out of both (findings 9 and 16)."""
    if r.get('oversize'):
        return [], []
    front, size, own, centre = r['front_board'], rec_size(ctx, r), rec_own(r), r['centre']
    best, tally = search(ctx, placed, front, centre, size, own)
    if best is not None:
        raise AssertionError('%s has a legal place against the final placed set' % r['id'])
    skip = ('outline', 'K edge', 'own front board')
    out = []
    for off in ctx.grid(ctx.step0, front, centre):
        sx, sy = r4(centre[0] + off[0]), r4(centre[1] + off[1])
        for d in DIRS:
            geo = gate_geometry(sx, sy, d, size, ctx.opts, hard=ctx.hard)
            why = ctx.evaluate(placed, front, geo, own)
            if why and not any(x in why[0] for x in skip):
                out.append({'slot_centre': [sx, sy], 'direction': DIR_NAMES[d], 'screen': why[0],
                            'penetration_mm': why[1], 'distance_mm': r4(math.hypot(*off))})
                if len(out) == k:
                    break
        if len(out) == k:
            break
    inside = {kk: v for kk, v in tally.items() if not any(x in kk for x in skip)}
    blk = [{'blocker': kk, 'candidates': v[0], 'smallest_penetration_mm': v[1]}
           for kk, v in sorted(inside.items(), key=lambda kv: (-kv[1][0], kv[0]))[:3]]
    return out, blk


def _latch(ctx, out):
    """Per placed link, the rear neighbours of its K latch: K-rear footprints within the latch margin of its K field and
    not under it. Verdict: open (none), open after the displacement (every one displaced by a link, the latch rule of
    DS-88 included), or NOT SHOWN with the reason (a neighbour of an exempt package, or any neighbour without the rule)."""
    margin = val(ctx.opts['latch_access_margin_mm'])
    all_disp = {x for r in out if r['placed'] for x in k_union(r['displaced'])}
    for r in out:
        if not r['placed']:
            continue
        kc = r['geometry']['K_connector']
        near = sorted(ctx.model.displaced('K', 'B', sg.grow(kc, margin)) - set(r['displaced']['K B (field)']))
        left = [x for x in near if x not in all_disp]
        if not near:
            verdict = 'open'
        elif not left:
            verdict = 'open after the displacement'
        elif all(latch_exempt(ctx.model.lib.get(x, '')) for x in left) and ctx.latch is not None:
            verdict = 'NOT SHOWN (exempt packages %s, ASSUMED lower than the 2.0 mm connector body; no height retained)' \
                % ', '.join(sorted({ctx.model.lib.get(x, '') for x in left}))
        else:
            verdict = 'NOT SHOWN (neighbour heights not retained)'
        r['latch_reach'] = {'neighbours_within_margin': near,
                            'packages': {x: ctx.model.lib.get(x, '') for x in near},
                            'displaced_by_latch_rule': r['displaced'].get('K B (latch)', []),
                            'remaining': left, 'verdict': verdict}


def split(refs):
    out = {'ICs': 0, 'resistors': 0, 'capacitors': 0, 'other': 0}
    for r in refs:
        p = re.match(r'[A-Z]+', r).group(0)
        out['ICs' if p == 'U' else 'resistors' if p == 'R' else 'capacitors' if p == 'C' else 'other'] += 1
    return out


def summarise(ctx, out, post_k):
    pl = [r for r in out if r['placed']]
    by = {k: sorted({x for r in pl for x in r['displaced'].get(k, [])}) for k in K_KEYS}
    k_all = sorted(set().union(*by.values()))
    latch_only = sorted(set(by['K B (latch)']) - set().union(*(set(v) for k, v in by.items() if k != 'K B (latch)')))
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
    verdicts = _count(r['latch_reach']['verdict'].split(' (')[0] for r in pl)
    near = sorted({x for r in pl for x in r['latch_reach']['neighbours_within_margin']})
    lib = ctx.model.lib
    cm = ctx.cmap
    return {
        'links': len(out), 'placed': len(pl), 'unplaced': len(out) - len(pl),
        'slots': len(pl), 'connectors': 2 * len(pl), 'latches': 2 * len(pl),
        'signals_on_links': sum(r['signals'] for r in out), 'signals_on_placed_links': sum(r['signals'] for r in pl),
        'grounds': sum(r['grounds'] for r in pl), 'unused_positions': sum(r['unused'] for r in pl),
        'per_joint_and_size': per,
        'K_displaced': {'F.Cu by slots': len(by['K F (slot)']), 'B.Cu by slots': len(by['K B (slot)']),
                        'B.Cu by fields': len(by['K B (field)']), 'B.Cu by the latch rule': len(by['K B (latch)']),
                        'B.Cu by the latch rule alone': len(latch_only),
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
        'latch_verdicts': verdicts,
        'latch_not_shown': sum(1 for r in pl if r['latch_reach']['verdict'].startswith('NOT SHOWN')),
        'latch_neighbour_packages': _count(lib.get(x, '') for x in near),
        'compliance': {'limit_mm_per_N': cm.limit, 'list_above_mm_per_N': cm.list_above,
                       'max_mm_per_N': max((r['compliance_mm_per_N'] for r in pl), default=None),
                       'links_above_list': sorted(r['id'] for r in pl if r['compliance_mm_per_N'] > cm.list_above + 1e-12),
                       'links_above_limit': sorted(r['id'] for r in pl if r['compliance_mm_per_N'] > cm.limit + 1e-12)},
    }, {'K_displaced_refs': {k.replace('K F', 'F.Cu').replace('K B', 'B.Cu'): v for k, v in by.items()},
        'K_displaced_by_the_latch_rule_alone': latch_only,
        'front_displaced_refs': fronts}


# The record of part 1 is run (e); runs (a) to (d) are comparisons of the chain (scope a8 item 6), each adding one input
RECORD = {'fixings': 'list', 'allocation': 'a8', 'compliance': True, 'latch_rule': True, 'lengthen': True}
CHAIN = [
    ('(a) corrected code on the inputs of a7 part 2 (30 fixings of DS-45, allocation of a7)',
     {'fixings': 'a7', 'allocation': 'a7', 'compliance': False, 'latch_rule': False}),
    ('(b) + the fixing list of ST-08 a2 (18 posts, four sleeves)',
     {'fixings': 'list', 'allocation': 'a7', 'compliance': False, 'latch_rule': False}),
    ('(c) + the allocation of DS-77 to DS-79',
     {'fixings': 'list', 'allocation': 'a8', 'compliance': False, 'latch_rule': False}),
    ('(d) + the compliance screen of DS-87',
     {'fixings': 'list', 'allocation': 'a8', 'compliance': True, 'latch_rule': False}),
    ('(e) + the latch rule of DS-88 (the record)', RECORD),
]
CHAIN_FILE = links.LINK_DIR / 'link-gate-chain.json'
CHAIN_REGEN = 'python3 scripts/stack/geometry/links_gate.py --chain'
A7_FILE = links.LINK_DIR / 'link-gate-a7-comparisons.json'


def gate_run(inp, flags, post_k):
    flags = dict(RECORD, **flags)
    sites = gate_sites(inp, flags['allocation'])
    model, ctx, out = place_gate(inp, sites, flags)
    s, refs = summarise(ctx, out, post_k)
    return sites, model, ctx, out, s, refs


def generate(root=sg.ROOT):
    """The record of part 1 (run (e)); the tests regenerate all of it."""
    inp = load_inputs(root)
    post_k = links.post_keepout_k(inp['root'])
    sites, model, ctx, out, s, refs = gate_run(inp, {}, post_k)
    rg = inp['gopts']['refinement']
    ref = [r for r in out if 'refinement' in r]
    return {'provenance': {'generator': 'scripts/stack/geometry/links_gate.py', 'regenerate': REGEN,
                           'input_sha256': input_hashes(inp)},
            'schema_version': 2,
            'status': 'RECORD OF ST-02 a8 part 1: the gate option of DS-67 on the ruled inputs (fixing list of ST-08 a2, '
                      'allocation of DS-77 to DS-79, compliance screen of DS-87, latch rule of DS-88); no way out of DS-84 '
                      'or DS-85 applied and no sleeve moved (part 2); courtyard level; unvalidated drafts; nothing selected',
            'flags': dict(RECORD),
            'signals': {'total': len(sum((x['signals'] for x in sites), [])),
                        'by_joint': {j: sum(len(x['signals']) for x in sites if x['joint'] == j) for j in JOINTS},
                        'by_class': _by_class(sites),
                        'classes': [{'site': x['id'], 'net': n, 'class': c} for x in sites
                                    for n, c in zip(x['signals'], x['classes'])]},
            'fixings': {'source': FIXING_FILE + ' (fixings with active true; reserve and alternatives are no keep-outs, '
                                  'DS-87)', 'count': len(model.fixings),
                        'by_kind': _count(f['kind'] for f in model.fixings),
                        'keepouts': model.fixings, 'access_holes': access_holes(inp)},
            'parameters': parameters(inp, ctx),
            'search': {'step_mm': ctx.step0, 'radius_mm': ctx.radius, 'tail_step_mm': ctx.step,
                       'tail_rule_hard_mm': ctx.hard,
                       'spare_mm': {'%s, %s' % (f, z['cable']): ctx.spare(f, fh12_size(z['circuits'], inp['gopts']))
                                    for f in FRONTS + ADAPTERS for z in inp['gopts']['sizes']},
                       'refinement': {'grids_mm': val(rg['grids_mm']), 'quarter_grid_below_mm': val(rg['quarter_grid_below_mm']),
                                      'rule': rg['rule'], 'improvement': {
                                          'rounds': val(rg['improvement']['rounds']),
                                          'allowance': val(rg['improvement']['allowance']),
                                          'candidates_per_link': val(rg['improvement']['candidates_per_link']),
                                          'rule': rg['improvement']['rule']},
                                      'links_without_a_place_on_the_2_mm_grid': len(ref),
                                      'found_on_finer_grid': {str(g): sum(1 for r in ref if r['refinement'].get('by') == 'finer grid'
                                                                          and r['refinement']['grid_mm'] == g) for g in val(rg['grids_mm'])},
                                      'found_by_improvement_pass': sum(1 for r in ref if r['refinement'].get('by', '').startswith('improvement pass')),
                                      'links_moved_by_improvement_pass': sum(1 for r in out if r.get('moves_by_improvement')),
                                      'remaining': sum(1 for r in out if not r['placed'])}},
            'summary': s,
            'part_2_of_a7': json.loads(A7_FILE.read_text())['record_totals'] if A7_FILE.exists() else None,
            'refs': refs,
            'links': out}


def parameters(inp, ctx):
    """Figures the README prints, read from the options files (findings 7 and 17)."""
    o, g = inp['opts'], inp['gopts']
    return {'latch_margin_mm': val(o['latch_access_margin_mm']), 'insertion_mm': val(o['cable']['insertion_depth_mm']),
            'bend_radius_mm': val(o['cable']['bend_radius_mm']), 'join_radius_mm': val(o['clustering']['join_radius_mm']),
            'distance_weight_per_mm': ctx.w, 'trim_to_mm': val(g['tail_rule']['trim_to_mm']),
            'field_growth_mm': val(g['field']['growth_mm']), 'field_depth_mm': val(g['field']['depth']),
            'adapter_sizes': [{'circuits': z['circuits'], 'cable': z['cable'], 'cable_length_mm': z['cable_length_mm'],
                               'connector': z['connector']} for z in adapter_sizes(ctx)],
            'adapter_order': ctx.adapter_order, 'joints': {k: v for k, v in g['joints'].items() if k != 'status'},
            'compliance': {'limit_mm_per_N': ctx.cmap.limit, 'list_above_mm_per_N': ctx.cmap.list_above,
                           'map_pitch_mm': ctx.cmap.pitch},
            'latch_exempt': g['latch_rule']['exempt']}


def chain_run(task):
    root, label, flags = task
    inp = load_inputs(root)
    post_k = links.post_keepout_k(inp['root'])
    _, _, _, out, s, _ = gate_run(inp, flags, post_k)
    return {'run': label, 'flags': dict(RECORD, **flags), 'links': s['links'], 'placed': s['placed'],
            'unplaced': s['unplaced'], 'unplaced_links': [r['id'] for r in out if not r['placed']],
            'signals_on_placed_links': s['signals_on_placed_links'], 'K_displaced': s['K_displaced']['total'],
            'trim_leads': s['trim_leads']}


def generate_chain(root=sg.ROOT, processes=4):
    import subprocess
    tasks = [(str(root), label, flags) for label, flags in CHAIN[:-1]]
    if processes > 1:
        import multiprocessing
        with multiprocessing.Pool(processes) as pool:
            rows = pool.map(chain_run, tasks, chunksize=1)
    else:
        rows = [chain_run(t) for t in tasks]
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=str(root), capture_output=True,
                            text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'scripts/stack/geometry'], cwd=str(root),
                           capture_output=True, text=True).stdout.strip()
    return {'note': 'Comparison runs (a) to (d) of the chain of ST-02 a8 part 1 (scope item 6); run (e) is the record in '
                    'link-gate.json. These rows are retained evidence and are regenerated only by `%s`; the tests do not '
                    'regenerate them.' % CHAIN_REGEN,
            'commit_of_run': commit + (' with uncommitted changes under scripts/stack/geometry' if dirty else ''),
            'runs': rows}


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

_MODELS = {}


def cached_model(inp, sites, flags):
    """One obstacle model per inputs, sites and run inputs (the model is not changed by a check)."""
    key = (id(inp), id(sites), flags['fixings'], flags['compliance'])
    if key not in _MODELS:
        _MODELS[key] = (inp, sites, GateModel(inp, sites, fixings=flags['fixings'], compliance=flags['compliance']))
    return _MODELS[key][2]


def check(doc, inp, sites=None):
    """Errors of the gate file. Nothing recorded is trusted: the run's inputs come from the recorded flags; joint, front
    board and size are checked against the sites and the ladder; tail extensions against the step and the spare;
    geometry is rebuilt from slot centre, direction, size and extensions; the allocation, cable length, displaced
    lists (latch rule included), compliance value and latch verdicts are recomputed; each placed link is re-screened
    against every other placed link with the screens of the search; and for each link without a place the nearest
    misses and blockers are recomputed against the final placed set. It proves legality, not that a larger size or
    another order would not have placed."""
    flags = dict(RECORD, **doc.get('flags', {}))
    sites = sites or gate_sites(inp, flags['allocation'])
    site_by = {s['id']: s for s in sites}
    model = cached_model(inp, sites, flags)
    ctx = Ctx(inp, model, flags)
    gopts = inp['gopts']
    errs = []
    seen_sites, seen_sig = [], {}
    pl = [r for r in doc['links'] if r['placed']]
    ladder = dict(gopts['joints'])
    ad_cables = {(z['cable'], z['cable_length_mm'], z['circuits']) for z in adapter_sizes(ctx)}
    for r in doc['links']:
        tag = r['id']
        n = r['circuits']
        mem = [site_by.get(m) for m in r['members']]
        if any(m is None for m in mem):
            errs.append('%s: unknown member site' % tag)
            continue
        if {m['joint'] for m in mem} != {r['joint']} or {m['front_board'] for m in mem} != {r['front_board']}:
            errs.append('%s: joint or front board %s / %s is not that of its sites' % (tag, r['joint'], r['front_board']))
        if r['joint'] == 'O-K':
            if (r['cable'], r['cable_length_mm'], n) not in ad_cables:
                errs.append('%s: %d circuits on %s %s mm is not an adapter size of the rule' % (tag, n, r['cable'], r['cable_length_mm']))
        else:
            if n not in ladder.get(r['joint'], []):
                errs.append('%s: %d circuits is not a size of joint %s' % (tag, n, r['joint']))
            if (r['cable'], r['cable_length_mm']) not in {(z['cable'], z['cable_length_mm']) for z in gopts['sizes'] if z['circuits'] == n}:
                errs.append('%s: cable %s %s mm is not the stock cable of %d circuits' % (tag, r['cable'], r['cable_length_mm'], n))
        size = rec_size(ctx, r)
        seen_sites += r['members']
        classes = [c for m in mem for c in m['classes']]
        need = circuits_needed(classes, ctx.rule)
        if need != r['circuits_needed']:
            errs.append('%s: records %s circuits needed, the rule gives %s' % (tag, r['circuits_needed'], need))
        want = sorted((nn, c, m['id']) for m in mem for nn, c in zip(m['signals'], m['classes']))
        if r.get('oversize'):
            if not r['placed'] and need is not None and need <= n:
                errs.append('%s: marked oversize but needs %s of %d circuits' % (tag, need, n))
            for x in want:
                seen_sig[(x[2], x[0])] = tag
            if r['placed']:
                errs.append('%s: an oversize link is placed' % tag)
            continue
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
        for e in allocation_errors(pos, ctx.rule, ctx.adapter_order):
            errs.append('%s: %s' % (tag, e))
        for k in ('signals', 'grounds', 'unused'):
            v = sum(1 for p in pos if p['kind'] == {'signals': 'signal', 'grounds': 'ground', 'unused': 'unused'}[k])
            if v != r[k]:
                errs.append('%s: records %d %s, the order has %d' % (tag, r[k], k, v))
        if not r['placed']:
            continue
        d = {v: k for k, v in DIR_NAMES.items()}[r['direction']]
        g0 = r['geometry']
        spare = ctx.spare(r['front_board'], size)
        ef, ek = g0['front_extension_mm'], g0['K_extension_mm']
        for nm, e in (('front', ef), ('K', ek)):
            if e < -1e-9 or abs(e / ctx.step - round(e / ctx.step)) > 1e-6:
                errs.append('%s: %s tail extension %s mm is not a non-negative multiple of %s mm' % (tag, nm, e, ctx.step))
        if ef + ek > spare + 1e-9:
            errs.append('%s: tail extensions %s + %s mm exceed the spare %s mm of the cable' % (tag, ef, ek, spare))
        geo = gate_geometry(r['slot_centre'][0], r['slot_centre'][1], d, size, inp['opts'], ef=ef, ek=ek, hard=ctx.hard)
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
        model.memo_for(None)
        why = ctx.evaluate(others, r['front_board'], geo, rec_own(r))
        if why:
            errs.append('%s: %s%s' % (tag, why[0], '' if why[1] is None else ' (%.4f mm)' % why[1]))
        elif displaced(model, r['front_board'], geo, ctx.latch) != r['displaced']:
            errs.append('%s: recorded displaced lists differ from the recomputed ones' % tag)
        if abs(r4(ctx.cmap.value(geo['K_connector'])) - r['compliance_mm_per_N']) > 1e-9:
            errs.append('%s: recorded compliance differs from the map' % tag)
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
    if errs:
        return errs
    # verdicts and the analysis of the links without a place, recomputed against the final placed set
    out = json.loads(json.dumps(doc['links']))
    _latch(ctx, out)
    for a, b in zip(out, doc['links']):
        if a.get('latch_reach') != b.get('latch_reach'):
            errs.append('%s: recorded latch verdict differs from the recomputed one' % a['id'])
    final = placed_index(doc['links'])
    for r in doc['links']:
        if not r['placed']:
            model.memo_for(None)
            nm, blk = misses_and_blockers(ctx, final, r)
            if nm != r.get('nearest_misses') or blk != r.get('most_frequent_blockers'):
                errs.append('%s: recorded nearest misses or blockers differ from the recomputed ones' % r['id'])
    return errs


# ---------------------------------------------------------------- main

def readme(doc):
    import links_gate_readme
    return links_gate_readme.render(doc)


def main(argv):
    if '--stdout' in argv:
        sys.stdout.write(render(generate()))
        return 0
    if '--chain' in argv:
        CHAIN_FILE.write_text(render(generate_chain()))
        print('wrote', CHAIN_FILE.relative_to(sg.ROOT))
        return 0
    doc = generate()
    LINK_GATE.write_text(render(doc))
    LINK_GATE_README.write_text(readme(doc))
    print('wrote', ', '.join(str(p.relative_to(sg.ROOT)) for p in (LINK_GATE, LINK_GATE_README)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
