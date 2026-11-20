"""Fixing list of the flat-link stack as ruled in DA-03 c2 (ST-08 attempt a2, part 1; DS-72 to DS-76).

The list is an input (`design/stack/fixings/ruled-list.json`); this study checks it with its screens, lists the
displaced parts with their nearest free position, reproduces the site scans behind DS-73 and DS-74 and reports the
distance screen of DS-72. Writes `design/stack/fixings/fixing-sites.json` and `design/stack/fixings/README.md`.

A courtyard-level paper screen on unvalidated drafts: not a copper clearance, a DRC, a fit or a strength result.
No KiCad: the boards are parsed with the plain-Python reader of `scripts/stack/geometry/` (imported, not changed).

  python3 scripts/stack/fixings/fixings.py           # write the JSON and the README
  python3 scripts/stack/fixings/fixings.py --check   # fail if a retained file differs or the checker finds anything
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
sys.path.insert(0, str(HERE))
import stackgeom as sg  # noqa: E402

OUT_DIR = ROOT / 'design/stack/fixings'
SITES_JSON = OUT_DIR / 'fixing-sites.json'
README = OUT_DIR / 'README.md'
RULED = 'design/stack/fixings/ruled-list.json'
REGEN = 'python3 scripts/stack/fixings/fixings.py'
CAMPAIGN = 'circuit/orchestration/campaigns/osc-stack-20261114'
DECISIONS = CAMPAIGN + '/decisions.md'
REVIEW = CAMPAIGN + '/reviews/da-03.md'

CANDIDATE = 'design/stack/geometry/stack-candidate.json'
JOINTS = 'design/stack/power-posts/joint-design.json'
LINK_OPTIONS = 'design/stack/geometry/links/link-options.json'
SPACERS = 'design/stack/spacers/spacer-set.json'
BOARDS = ('K', 'JL', 'JR', 'P', 'EL')
WHOLE_FILES = [RULED, sg.JSON_FILES['lock'], sg.JSON_FILES['partition']] + [sg.BOARD_FILES[k] for k in BOARDS]
PROGRAM = ['scripts/stack/fixings/fixings.py', 'scripts/stack/fixings/fixings_check.py',
           'scripts/stack/fixings/fixings_readme.py', 'scripts/stack/geometry/stackgeom.py',
           'scripts/stack/geometry/kicad_extract.py']
PINNED_ROWS = ('DS-43', 'DS-44', 'DS-45', 'DS-66', 'DS-70', 'DS-72', 'DS-73', 'DS-74', 'DS-75', 'DS-76')
# (label, first heading, heading that ends the section)
PINNED_SECTIONS = (('da-03 c2: scratch runs and H1 to H5', '### Three scratch runs', '### E1'),)
FRONTS = ('JL', 'JR', 'P')
PANEL_KINDS = ('jack', 'led', 'pot', 'switch', 'button')
# one comparison tolerance for every geometric test of the generator and the checker; retained positions are
# rounded to 0.001 mm before they are tested, so no rounding allowance is needed on top
EPS = 1e-9
COVER_SCREEN_MM = 90.0
POST_ROWS_Y = (160.0, 175.0)


def r3(v):
    return round(float(v) + 0.0, 3)


def term(value, status, source):
    return {'value': value, 'status': status, 'source': source}


def val(t):
    return t['value'] if isinstance(t, dict) else t


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


# ---------------------------------------------------------------- inputs and pins

def load_inputs(root=ROOT):
    root = Path(root)
    raw = sg.load_raw(root)
    boards = sg.load_boards(raw, root, files={k: sg.BOARD_FILES[k] for k in BOARDS})
    rd = lambda p: json.loads((root / p).read_text())  # noqa: E731
    return {'raw': raw, 'boards': boards, 'cand': rd(CANDIDATE)['candidate'], 'joints': rd(JOINTS),
            'opts': rd(LINK_OPTIONS), 'spacers': rd(SPACERS), 'ruled': rd(RULED), 'root': root}


def read_objects(root):
    """The objects this study reads from other studies, by label."""
    rd = lambda p: json.loads((Path(root) / p).read_text())  # noqa: E731
    cand = rd(CANDIDATE)['candidate']
    jd, lo, sp = rd(JOINTS), rd(LINK_OPTIONS), rd(SPACERS)
    return {
        CANDIDATE + ' candidate.planes': cand['planes'],
        CANDIDATE + ' candidate.tabs': cand['tabs'],
        CANDIDATE + ' candidate.selectors_kept': cand['selectors_kept'],
        CANDIDATE + ' candidate.sub_toggles': cand['sub_toggles'],
        CANDIDATE + ' candidate.retired (K_headers, front_headers)': [cand['retired']['K_headers'], cand['retired']['front_headers']],
        CANDIDATE + ' candidate.pairs[].sites.*.replaces': sorted(s.get('replaces') or '' for p in cand['pairs'] for s in p['sites'].values()),
        CANDIDATE + ' candidate.fixings (kept supports)': [f for f in cand['fixings'] if f['kind'] == 'kept support'],
        CANDIDATE + ' candidate.stack (K_rear_z_mm, K_rear_parts_z_mm)': [cand['stack']['K_rear_z_mm'], cand['stack']['K_rear_parts_z_mm']],
        JOINTS + ' joints': jd['joints'],
        LINK_OPTIONS + ' fixing_keepout_radius_mm, board_edge_margin_mm': [lo['fixing_keepout_radius_mm'], lo['board_edge_margin_mm']],
        SPACERS + ' sleeve, length_allowance_mm, members': [sp['sleeve'], sp['length_allowance_mm'], sp['members']],
    }


def decision_rows(root):
    text = (Path(root) / DECISIONS).read_text()
    out = {}
    for rid in PINNED_ROWS:
        rows = [line for line in text.splitlines() if re.match(r'^\| ?%s \|' % re.escape(rid), line)]
        out[rid] = rows[0] if len(rows) == 1 else None
    return out


def review_sections(root):
    text = (Path(root) / REVIEW).read_text()
    out = {}
    for label, start, end in PINNED_SECTIONS:
        a = text.find(start)
        b = text.find(end, a)
        out[label] = text[a:b] if a >= 0 and b > a else None
    return out


def pins(root=ROOT):
    root = Path(root)
    rows = decision_rows(root)
    secs = review_sections(root)
    return {
        'files_sha256': {p: sg.sha256_file(root / p) for p in sorted(WHOLE_FILES + PROGRAM)},
        'objects_sha256': {k: digest(v) for k, v in sorted(read_objects(root).items())},
        'decision_rows_sha256': {k: (hashlib.sha256(v.encode()).hexdigest() if v else 'MISSING') for k, v in rows.items()},
        'review_sections_sha256': {k: (hashlib.sha256(v.encode()).hexdigest() if v else 'MISSING') for k, v in secs.items()},
    }


def parameters(inp):
    opts, sp, cand = inp['opts'], inp['spacers'], inp['cand']
    long_m = next(m for m in sp['members'] if m['id'] == 'gap-19')
    short_m = next(m for m in sp['members'] if m['id'] == 'gap-17')
    head = sorted({j['panel_side_keepout_radius_mm'] for j in inp['joints']['joints'] if 'panel_side_keepout_radius_mm' in j})
    return {
        'sleeve_min_spacing_mm': term(70.0, 'SOURCED', 'DS-66, unchanged by DS-72: a printed sleeve only where no other fixing of K lies within 70 mm'),
        'cover_screen_mm': term(COVER_SCREEN_MM, 'SOURCED', 'DS-72: 90 mm stays a search screen and is no pass or fail'),
        'grid_mm': term(1.0, 'STATED', 'ST-08 grid over K\'s outline; the outline has integer corners, so a point between nodes lies at most 0.71 mm farther than its nearest node'),
        'keepout_radius_K_mm': term(val(opts['fixing_keepout_radius_mm']['K']), 'ASSUMED',
                                    'link-options.json fixing_keepout_radius_mm.K (SOURCED for posts, ASSUMED equal for sleeves)'),
        'keepout_radius_front_mm': term(val(opts['fixing_keepout_radius_mm']['front']), 'ASSUMED',
                                        'link-options.json fixing_keepout_radius_mm.front, applied on both faces and on EL where a site lies under EL (DS-76)'),
        'sleeve_outer_diameter_mm': term(sp['sleeve']['outer_diameter_mm'], 'SOURCED', 'spacer-set.json sleeve.outer_diameter_mm (DS-45)'),
        'sleeve_bore_mm': term(sp['sleeve']['bore_diameter_mm'], 'SOURCED', 'spacer-set.json sleeve.bore_diameter_mm (DS-45)'),
        'panel_head_radius_mm': term(head[0] if len(head) == 1 else None, 'SOURCED',
                                     'joint-design.json joints[].panel_side_keepout_radius_mm (DS-44: 5.5 mm M3 head without washer); DS-76: the sleeve screw head is at most 5.5 mm'),
        'board_edge_margin_mm': term(val(opts['board_edge_margin_mm']), 'SOURCED', 'link-options.json board_edge_margin_mm'),
        'ceramic_radius_mm': term(5.0, 'SOURCED', 'DS-42: no ceramic part of 0805 or larger within 5 mm of a fixing'),
        'ceramic_min_case': term('0805', 'SOURCED', 'DS-42'),
        'move_search': term({'step_mm': 0.25, 'directions': 24, 'max_mm': 12.0, 'outline_margin_mm': 0.3}, 'SOURCED',
                            'the method of ST-04 (design/stack/power-posts/envelopes.json "method")'),
        'gap_mm': term({'JL': 19.0, 'JR': 19.0, 'P': 17.0}, 'SOURCED', 'DS-33 and DS-45: gaps 19.0 mm (JL, JR) and 17.0 mm (P)'),
        'board_thickness_mm': term(cand['planes']['K']['thickness_mm'], 'SOURCED', 'stack-candidate.json planes.*.thickness_mm'),
        'rear_envelope_mm': term(r3(cand['stack']['K_rear_z_mm'] - cand['stack']['K_rear_parts_z_mm']), 'SOURCED',
                                 'stack-candidate.json stack: K_rear_z_mm minus K_rear_parts_z_mm (envelope of K\'s rear parts)'),
        'plate': term({'long': long_m['quantity'] + long_m['spares'], 'short': short_m['quantity'] + short_m['spares']}, 'SOURCED',
                      'spacer-set.json members quantity + spares (one plate)'),
        'washer_thickness_mm': term(None, 'UNSOURCED', 'no M3 washer drawing retained'),
        'nut_height_mm': term(None, 'UNSOURCED', 'no M3 nut drawing retained'),
    }


# ---------------------------------------------------------------- footprint classes

def box(fp):
    if fp['courtyard']:
        return fp['courtyard']
    bxs = [p['bbox'] for p in fp['pads']]
    if not bxs:
        return None
    return [min(b[0] for b in bxs), min(b[1] for b in bxs), max(b[2] for b in bxs), max(b[3] for b in bxs)]


def box_dist(rect, c):
    dx = max(rect[0] - c[0], 0, c[0] - rect[2])
    dy = max(rect[1] - c[1], 0, c[1] - rect[3])
    return math.hypot(dx, dy)


def is_tht(fp):
    return any(p['type'] in ('thru_hole', 'np_thru_hole') for p in fp['pads'])


def faces(fp):
    return ('F', 'B') if is_tht(fp) else (fp['side'],)


def case_of(fp):
    lib = fp['lib']
    for code, metric in (('0402', '1005'), ('0603', '1608'), ('0805', '2012'), ('1206', '3216'), ('1210', '3225'),
                         ('1812', '4532'), ('2220', '5750')):
        if code in lib or metric + 'Metric' in lib:
            return code
    return None


CASE_ORDER = ('0402', '0603', '0805', '1206', '1210', '1812', '2220')


def is_ceramic(fp):
    """A capacitor reference on an MLCC chip footprint (ASSUMED ceramic from the footprint class)."""
    return fp['ref'].startswith('C') and not fp['ref'].startswith('CN') and case_of(fp) is not None


def ceramic_at_least(fp, case):
    return is_ceramic(fp) and CASE_ORDER.index(case_of(fp)) >= CASE_ORDER.index(case)


def footprint_classes(inp):
    """Per board: (footprint, class) for every footprint the screen considers (cached on the inputs)."""
    if '_fcls' not in inp:
        inp['_fcls'] = _footprint_classes(inp)
    return inp['_fcls']


def _footprint_classes(inp):
    cand, lock = inp['cand'], inp['raw']['lock']
    locked = {r['ref']: r['kind'] for r in lock['placements'] if r['kind'] in PANEL_KINDS}
    replaced = set(cand['retired']['K_headers']) | set(cand['retired']['front_headers'])
    for p in cand['pairs']:
        for s in p['sites'].values():
            if s.get('replaces'):
                replaced.add(s['replaces'])
    sleeve_ids = {f['id'] for f in cand['fixings'] if f['kind'] == 'kept support'}
    out = {}
    for b in BOARDS:
        fps = []
        for f in inp['boards'][b]:
            ref = f['ref']
            if box(f) is None:
                continue
            if ref.startswith('TP9900'):
                continue  # the 18 power-post lands themselves
            if ref.startswith('MH_K-SERVICE'):
                continue  # retired K service apertures (stack-candidate retired.K_service_aperture_footprints)
            if ref.startswith('MH_') and ref[3:] in sleeve_ids:
                continue  # the hole of one of the twelve DS-45 sleeve sites
            if ref in replaced:
                continue  # GH harness header replaced by a stack pair, now by a flat link (DS-61)
            if ref in locked:
                cls = 'panel hardware (' + locked[ref] + ')'
            elif f['lib'] == '':
                cls = 'hole'
            else:
                cls = 'movable'
            fps.append((f, cls))
        out[b] = fps
    return out


# ---------------------------------------------------------------- geometry of a site

def outlines(cand):
    return {b: cand['planes'][b]['outline'] for b in BOARDS}


def front_board_at(xy, ol):
    for b in FRONTS:
        if sg.point_in_poly(xy[0], xy[1], ol[b]):
            return b
    return None


def pierced(xy, front, ol):
    out = ['K', front]
    if front == 'P' and sg.point_in_poly(xy[0], xy[1], ol['EL']):
        out.append('EL')
    return out


def radius_on(board, prm):
    return val(prm['keepout_radius_K_mm']) if board == 'K' else val(prm['keepout_radius_front_mm'])


_INDEX = {}


def board_index(fcls, board):
    key = (id(fcls), board)
    if key not in _INDEX:
        idx = sg.RectIndex()
        for f, cls in fcls[board]:
            idx.add(box(f), (f, cls))
        _INDEX[key] = (fcls, idx)
    return _INDEX[key][1]


def keepout_hits(xy, board, fcls, prm):
    """Footprints whose courtyard box enters the keep-out circle on `board`, and ceramics of 0805 or larger within
    5 mm (DS-42). Both faces count for a movable part: sleeve and washer cover both faces of K, sleeve and screw head
    both faces of a front board. Locked panel hardware is screened as ST-04 screened it at the DS-44 lands: its
    courtyard against the screw head on the panel face, its pads against the keep-out on the rear face."""
    r = radius_on(board, prm)
    rc = val(prm['ceramic_radius_mm'])
    rh = val(prm['panel_head_radius_mm'])
    reach = max(r, rc)
    hits = []
    for _, (f, cls) in board_index(fcls, board).near([xy[0] - reach, xy[1] - reach, xy[0] + reach, xy[1] + reach]):
        d = box_dist(box(f), xy)
        cer = ceramic_at_least(f, val(prm['ceramic_min_case']))
        if not (d < r - EPS or (cer and d <= rc + EPS)):
            continue
        h = {'board': board, 'ref': f['ref'], 'lib': f['lib'], 'value': f['value'], 'class': cls,
             'faces': list(faces(f)), 'distance_mm': r3(d), 'in_keepout': d < r - EPS,
             'ceramic_0805_or_larger_within_5mm': bool(cer and d <= rc + EPS)}
        if cls.startswith('panel hardware'):
            dp = min((box_dist(p['bbox'], xy) for p in f['pads'] if any(l in ('B.Cu', '*.Cu') for l in p['layers'])),
                     default=None)
            h['panel_face_courtyard_mm'] = r3(d)
            h['rear_face_pad_mm'] = None if dp is None else r3(dp)
            h['in_keepout'] = d < rh - EPS or (dp is not None and dp < r - EPS)
        hits.append(h)
    return sorted(hits, key=lambda h: h['ref'])


def obstacle_reasons(xy, front, ol, cand, prm, edge=None):
    """Why a point cannot carry a sleeve: board edges, tabs, adapters, selectors, sub toggles. `edge` is the radius
    that must stay inside every pierced outline: the sleeve plus margin for an added site, the bore plus margin for
    one of the twelve given sites."""
    why = []
    rf = val(prm['keepout_radius_front_mm'])
    if edge is None:
        edge = val(prm['sleeve_outer_diameter_mm']) / 2 + val(prm['board_edge_margin_mm'])
    for b in pierced(xy, front, ol):
        if not sg.point_in_poly(xy[0], xy[1], ol[b]) or sg.distance_to_outline(xy[0], xy[1], ol[b]) < edge - EPS:
            why.append('board edge of %s within %.2f mm' % (b, edge))
    if front == 'P':
        el = ol['EL']
        if not sg.point_in_poly(xy[0], xy[1], el) and sg.distance_to_outline(xy[0], xy[1], el) < rf - EPS:
            why.append('straddles the EL edge')
    for t in cand['tabs']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, t['rect']) > EPS:
            why.append('tab ' + t['id'])
    for a in ('O1', 'O3', 'O5'):
        o = cand['planes'][a]['outline']
        if sg.point_in_poly(xy[0], xy[1], o) or sg.distance_to_outline(xy[0], xy[1], o) < rf - EPS:
            why.append('adapter ' + a)
    for s in cand['selectors_kept']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, s['courtyard']) > EPS:
            why.append('kept selector ' + s['ref'])
    for s in cand['sub_toggles']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, s['toggle_courtyard']) > EPS:
            why.append('sub toggle ' + s['block'])
    return why


# ---------------------------------------------------------------- nearest free position (ST-04's method)

class FreeSearch:
    """Nearest free position by ST-04's method, with every candidate position rounded to 0.001 mm before it is
    tested, so that the retained position is the one that was checked."""

    def __init__(self, fcls, ol, prm):
        self.fcls, self.ol, self.prm = fcls, ol, prm
        self.index = {}
        self.cache = {}
        for b in BOARDS:
            idx = {'F': sg.RectIndex(), 'B': sg.RectIndex()}
            for f, _ in fcls[b]:
                for s in faces(f):
                    idx[s].add(box(f), f['ref'])
            self.index[b] = idx

    def radius(self, f, r):
        if ceramic_at_least(f, val(self.prm['ceramic_min_case'])):
            return max(r, val(self.prm['ceramic_radius_mm']))
        return r

    def _shifts(self, board, f):
        ms = val(self.prm['move_search'])
        for k in range(1, int(ms['max_mm'] / ms['step_mm']) + 1):
            d = k * ms['step_mm']
            for i in range(ms['directions']):
                a = math.radians(i * 360 / ms['directions'])
                pos = [r3(f['origin'][0] + d * math.cos(a)), r3(f['origin'][1] + d * math.sin(a))]
                yield r3(d), pos

    def moved_box(self, f, pos):
        b0 = box(f)
        dx, dy = pos[0] - f['origin'][0], pos[1] - f['origin'][1]
        return [b0[0] + dx, b0[1] + dy, b0[2] + dx, b0[3] + dy]

    def _base_ok(self, board, f, pos, base):
        ms = val(self.prm['move_search'])
        nb = self.moved_box(f, pos)
        if any(box_dist(nb, c) < self.radius(f, r) - EPS for c, r in base):
            return False
        if any(ref != f['ref'] for s in faces(f) for rect, ref in self.index[board][s].near(nb) if sg.inter(nb, rect)):
            return False
        return sg.rect_inside_poly(nb, self.ol[board], ms['outline_margin_mm'])

    def search(self, board, f, base, extra=()):
        """(shift, origin) of the smallest shift whose box clears every circle of `base` and `extra` (5 mm for a
        ceramic of 0805 or larger), every other footprint box on its faces and the outline; (None, None) when none
        lies within the limit. Positions passing `base` are cached per footprint, so scans that share the posts
        reuse them."""
        key = (board, f['ref'], tuple((tuple(c), r) for c, r in base))
        if key not in self.cache:
            self.cache[key] = {'gen': self._shifts(board, f), 'ok': [], 'done': False}
        ent = self.cache[key]
        i = 0
        while True:
            while i >= len(ent['ok']):
                if ent['done']:
                    return None, None
                try:
                    d, pos = next(ent['gen'])
                except StopIteration:
                    ent['done'] = True
                    continue
                if self._base_ok(board, f, pos, base):
                    ent['ok'].append((d, pos))
            d, pos = ent['ok'][i]
            nb = self.moved_box(f, pos)
            if not any(box_dist(nb, c) < self.radius(f, r) - EPS for c, r in extra):
                return d, pos
            i += 1


def fixing_circles(fixings, board, prm):
    """(centre, radius) of every fixing that pierces `board`."""
    out = []
    for fx in fixings:
        if not fx['active'] or board not in fx['boards']:
            continue
        out.append((fx['xy'], fx['keepout_radius_mm'][board]))
    return out


# ---------------------------------------------------------------- coverage

_GRID = {}


def k_grid(cand, step):
    ol = cand['planes']['K']['outline']
    key = (json.dumps(ol), step)
    if key not in _GRID:
        _GRID[key] = _k_grid(ol, step)
    return _GRID[key]


def _k_grid(ol, step):
    xs = [p[0] for p in ol]
    ys = [p[1] for p in ol]
    gx = np.arange(min(xs), max(xs) + EPS, step)
    gy = np.arange(min(ys), max(ys) + EPS, step)
    pts = [(x, y) for y in gy for x in gx
           if sg.point_in_poly(x, y, ol) or sg.distance_to_outline(x, y, ol) < EPS]
    return np.array(pts, dtype=float)


def farthest(grid, xys):
    f = np.array(xys, dtype=float)
    d = np.sqrt(((grid[:, None, :] - f[None, :, :]) ** 2).sum(-1)).min(1)
    i = int(d.argmax())
    return r3(d[i]), [r3(grid[i][0]), r3(grid[i][1])]


def beyond_rule(grid, xys, cover):
    """Grid nodes farther than `cover` from every fixing: count and bounding boxes of their 10 mm clusters."""
    f = np.array(xys, dtype=float)
    d = np.sqrt(((grid[:, None, :] - f[None, :, :]) ** 2).sum(-1)).min(1)
    pts = grid[d > cover + EPS]
    dd = d[d > cover + EPS]
    clusters = []
    for p, v in sorted(zip(pts.tolist(), dd.tolist()), key=lambda t: (t[0][1], t[0][0])):
        for c in clusters:
            if c['box'][0] - 10 <= p[0] <= c['box'][2] + 10 and c['box'][1] - 10 <= p[1] <= c['box'][3] + 10:
                c['box'] = [min(c['box'][0], p[0]), min(c['box'][1], p[1]), max(c['box'][2], p[0]), max(c['box'][3], p[1])]
                c['nodes'] += 1
                if v > c['farthest_mm']:
                    c['farthest_mm'], c['at'] = r3(v), p
                break
        else:
            clusters.append({'box': [p[0], p[1], p[0], p[1]], 'nodes': 1, 'farthest_mm': r3(v), 'at': p})
    return {'nodes': int(len(pts)), 'clusters': clusters}


def nearest_other(xy, others):
    best = None
    for oid, oxy in others:
        d = math.dist(xy, oxy)
        if best is None or d < best[1]:
            best = (oid, d)
    return {'id': best[0], 'distance_mm': r3(best[1])}




# ---------------------------------------------------------------- one site against a list

def site_record(site, kind, inp, prm, fcls, ol, free, others, edge=None, replacement=()):
    """Screens of one sleeve site against the other active fixings `others`: the hard findings and the displaced
    parts with their nearest free position (clearing every fixing of the list and the site itself)."""
    cand = inp['cand']
    xy = [float(v) for v in site['xy']]
    front = front_board_at(xy, ol)
    findings = []
    if front != site['front_board']:
        findings.append('facing board %s, ruled %s' % (front, site['front_board']))
        front = site['front_board']
    bs = pierced(xy, front, ol)
    findings += obstacle_reasons(xy, front, ol, cand, prm, edge=edge)
    hits = []
    for b in bs:
        hits += keepout_hits(xy, b, fcls, prm)
    for h in hits:
        if h['in_keepout'] and h['class'] != 'movable':
            findings.append('%s %s on %s (courtyard %.2f mm%s)' % (
                h['class'], h['ref'], h['board'], h['distance_mm'],
                '' if h.get('rear_face_pad_mm') is None else ', rear pad %.2f mm' % h['rear_face_pad_mm']))
    spacing = val(prm['sleeve_min_spacing_mm'])
    near = nearest_other(xy, [(o['id'], o['xy']) for o in others])
    for o in others:
        d = math.dist(xy, o['xy'])
        if d < spacing - EPS:
            findings.append('%s within %.0f mm (%.2f mm)' % (o['id'], spacing, d))
    rec = {'id': site['id'], 'kind': kind, 'xy': xy, 'front_xy': xy, 'front_board': front, 'boards': bs,
           'gap_mm': val(prm['gap_mm'])[front], 'keepout_radius_mm': {b: radius_on(b, prm) for b in bs},
           'length_class': str(val(prm['gap_mm'])[front]), 'nearest_other_fixing': near,
           'edge_distance_mm': r3(min(sg.distance_to_outline(xy[0], xy[1], ol[b]) for b in bs)),
           'findings': sorted(set(findings))}
    me = dict(rec, active=True)
    repl = {(r['board'], r['ref']) for r in replacement}
    moves = []
    for h in hits:
        if h['class'] != 'movable' or not (h['in_keepout'] or h['ceramic_0805_or_larger_within_5mm']):
            continue
        f = next(f for f, _ in fcls[h['board']] if f['ref'] == h['ref'])
        shift, pos = free.search(h['board'], f, fixing_circles(others + [me], h['board'], prm))
        m = dict(h, origin=[r3(v) for v in f['origin']], nearest_free_shift_mm=shift, nearest_free_origin=pos)
        if (h['board'], h['ref']) in repl:
            m['decided_by'] = 'the re-placement search of the room study at 25 mm (DS-74)'
        moves.append(m)
    rec['part_moves'] = sorted(moves, key=lambda m: (m['board'], m['ref']))
    return rec


# ---------------------------------------------------------------- region scans (DS-73, DS-74)

SCANS = (
    ('JL', 'JL, y 22 to 70', ('JL',), (4, 176.5), (22, 70)),
    ('JR', 'JR, y 22 to 70', ('JR',), (177.5, 314), (22, 70)),
    ('lower_right', 'lower right of K, x 200 to 314, y 176 to 292', ('P',), (200, 314), (176, 292)),
)
UPPER_MIDDLE_X = (120, 200)


def scan_region(region, inp, prm, fcls, ol, free, posts):
    """Clear sleeve nodes on the integer 1 mm grid of a region and, per node, the displaced parts that have no free
    position within 12 mm when the node and the posts are the only fixings."""
    _, _, boards, (x0, x1), (y0, y1) = region
    spacing = val(prm['sleeve_min_spacing_mm'])
    nodes = []
    for y in range(math.ceil(y0), math.floor(y1) + 1):
        for x in range(math.ceil(x0), math.floor(x1) + 1):
            xy = [float(x), float(y)]
            front = front_board_at(xy, ol)
            if front not in boards or obstacle_reasons(xy, front, ol, inp['cand'], prm):
                continue
            bs = pierced(xy, front, ol)
            hits = [h for b in bs for h in keepout_hits(xy, b, fcls, prm)]
            if any(h['in_keepout'] and h['class'] != 'movable' for h in hits):
                continue
            nofree = []
            for h in hits:
                if h['class'] != 'movable' or not (h['in_keepout'] or h['ceramic_0805_or_larger_within_5mm']):
                    continue
                f = next(f for f, _ in fcls[h['board']] if f['ref'] == h['ref'])
                base = fixing_circles(posts, h['board'], prm)
                if free.search(h['board'], f, base, extra=[(xy, radius_on(h['board'], prm))])[0] is None:
                    nofree.append({'board': h['board'], 'ref': h['ref'], 'lib': h['lib']})
            nodes.append({'xy': xy, 'front_board': front, 'parts_without_free_position': nofree,
                          'nearest_post_mm': r3(min(math.dist(xy, p['xy']) for p in posts)),
                          'outside_70_mm_of_every_post': min(math.dist(xy, p['xy']) for p in posts) >= spacing - EPS})
    return nodes


def scan_summary(nodes):
    free_nodes = [n['xy'] for n in nodes if not n['parts_without_free_position']]
    return {'clear': len(nodes), 'all_parts_free': len(free_nodes),
            'clear_outside_70_mm_of_every_post': sum(1 for n in nodes if n['outside_70_mm_of_every_post']),
            'columns_x_of_all_parts_free': sorted({n[0] for n in free_nodes}),
            'all_parts_free_nodes': free_nodes if len(free_nodes) <= 10 else None,
            'y_range': [min(n['xy'][1] for n in nodes), max(n['xy'][1] for n in nodes)] if nodes else None}


def is_ic(part):
    return part['ref'].startswith('U')


def region_scans(inp, prm, fcls, ol, free, posts):
    out = {}
    nodes_by = {}
    for region in SCANS:
        nodes = scan_region(region, inp, prm, fcls, ol, free, posts)
        nodes_by[region[0]] = nodes
        y_last = math.floor(region[4][1])
        out[region[0]] = dict(scan_summary(nodes), region=region[1], grid='integer nodes, 1 mm',
                              clear_without_last_row=sum(1 for n in nodes if n['xy'][1] < y_last),
                              nodes=[[n['xy'][0], n['xy'][1], len(n['parts_without_free_position'])] for n in nodes])
    mid = [n for k in ('JL', 'JR') for n in nodes_by[k] if UPPER_MIDDLE_X[0] <= n['xy'][0] <= UPPER_MIDDLE_X[1]]
    out['upper_middle'] = dict(scan_summary(mid), region='JL and JR nodes at x 120 to 200, y 22 to 70',
                               without_an_ic_lacking_a_free_position=sum(
                                   1 for n in mid if not any(is_ic(p) for p in n['parts_without_free_position'])))
    lr = nodes_by['lower_right']
    soic = [sum(1 for p in n['parts_without_free_position'] if p['lib'].startswith('SOIC-14')) for n in lr]
    out['lower_right']['soic14_without_free_position'] = [min(soic), max(soic)] if soic else None
    out['lower_right']['every_node_has_a_soic14_without_free_position'] = bool(soic) and min(soic) >= 1
    return out


def corner_tests(inp, prm, fcls, ol):
    out = []
    for xy, fb in (([7.5, 23.5], 'JL'), ([310.5, 23.5], 'JR')):
        hits = [h for b in pierced(xy, fb, ol) for h in keepout_hits(xy, b, fcls, prm)]
        fails = [{'ref': h['ref'], 'class': h['class'], 'panel_face_courtyard_mm': h.get('panel_face_courtyard_mm'),
                  'rear_face_pad_mm': h.get('rear_face_pad_mm')}
                 for h in hits if h['in_keepout'] and h['class'] != 'movable']
        out.append({'xy': xy, 'front_board': fb, 'fails': fails,
                    'test': 'panel-side test: locked courtyard against the %.1f mm head radius' % val(prm['panel_head_radius_mm'])})
    return out


# ---------------------------------------------------------------- coverage screen (DS-72)

def coverage(grid, active, cover):
    xys = [f['xy'] for f in active]
    above = grid[grid[:, 1] <= POST_ROWS_Y[0]]
    below = grid[grid[:, 1] >= POST_ROWS_Y[1]]
    out = {'screen_mm': cover, 'overall': farthest(grid, xys)}
    for name, g in (('above_post_rows', above), ('below_post_rows', below)):
        far = farthest(g, xys)
        b = beyond_rule(g, xys, cover)
        out[name] = {'farthest_mm': far[0], 'at': far[1], 'nodes_beyond_screen': b['nodes'], 'clusters': b['clusters']}
    return out


# ---------------------------------------------------------------- build

def build(inp):
    cand, prm, ruled = inp['cand'], parameters(inp), inp['ruled']
    ol = outlines(cand)
    fcls = footprint_classes(inp)
    free = FreeSearch(fcls, ol, prm)
    rk, rf = val(prm['keepout_radius_K_mm']), val(prm['keepout_radius_front_mm'])

    posts = []
    for j in inp['joints']['joints']:
        posts.append({'id': j['id'], 'kind': 'post', 'active': True, 'xy': list(j['K_xy']), 'front_xy': list(j['front_xy']),
                      'front_board': j['front_board'], 'boards': ['K', j['front_board']], 'gap_mm': j['gap_mm'],
                      'keepout_radius_mm': {'K': rk, j['front_board']: rf}, 'length_class': None,
                      'panel_side_keepout_radius_mm': j.get('panel_side_keepout_radius_mm', rf),
                      'status': 'post (DS-43, DS-44, DS-75)', 'decision': 'DS-43, DS-44, DS-75'})
    sleeves = []
    for s in ruled['sleeves']:
        xy = [float(v) for v in s['xy']]
        bs = pierced(xy, s['front_board'], ol)
        sleeves.append({'id': s['id'], 'xy': xy, 'active': True, 'boards': bs,
                        'keepout_radius_mm': {b: radius_on(b, prm) for b in bs}})
    fixings = list(posts)
    for s in ruled['sleeves']:
        others = posts + [o for o in sleeves if o['id'] != s['id']]
        rec = site_record(s, 'sleeve added', inp, prm, fcls, ol, free, others,
                          replacement=s.get('replacement_search', ()))
        rec.update(active=True, decision=s['decision'],
                   status='ruled sleeve (%s); screens %s' % (s['decision'], 'pass' if not rec['findings'] else 'FAIL'))
        if rec['length_class'] != s['length_class']:
            rec['findings'].append('length class %s, ruled %s' % (rec['length_class'], s['length_class']))
        fixings.append(rec)
    active = [f for f in fixings if f['active']]
    hole_edge = val(prm['sleeve_bore_mm']) / 2 + val(prm['board_edge_margin_mm'])
    for f in cand['fixings']:
        if f['kind'] != 'kept support':
            continue
        rec = site_record({'id': f['id'], 'xy': f['xy'], 'front_board': f['front_board']}, 'sleeve dropped', inp, prm,
                          fcls, ol, free, active, edge=hole_edge)
        rec['site_conflicts'] = rec.pop('findings')
        rec.pop('part_moves')
        rec.update(active=False, decision=ruled['dropped']['decision'],
                   status='dropped (%s)' % ruled['dropped']['decision'])
        fixings.append(rec)
    for fx in fixings:
        if fx['kind'] == 'post':
            fx['nearest_other_fixing'] = nearest_other(fx['xy'], [(o['id'], o['xy']) for o in active if o['id'] != fx['id']])
            hits = [h for b in fx['boards'] for h in keepout_hits(fx['xy'], b, fcls, prm) if h['ceramic_0805_or_larger_within_5mm']
                    and h['class'] == 'movable']
            moves = []
            for h in hits:
                f = next(f for f, _ in fcls[h['board']] if f['ref'] == h['ref'])
                shift, pos = free.search(h['board'], f, fixing_circles(active, h['board'], prm))
                moves.append(dict(h, origin=[r3(v) for v in f['origin']], nearest_free_shift_mm=shift, nearest_free_origin=pos))
            fx['part_moves'] = moves
        fx['K_kicad_xy'] = kicad_xy(fx['xy'], inp)
        fx['front_kicad_xy'] = kicad_xy(fx['front_xy'], inp)

    # reserve and alternatives, each against the list (the alternative in place of the sleeve it replaces)
    reserve = []
    for s in ruled['reserve']:
        rec = site_record(s, 'reserve', inp, prm, fcls, ol, free, active)
        rec.update(decision=s['decision'], use=s['use'])
        reserve.append(rec)
    alternatives = []
    for s in ruled['alternatives']:
        others = [o for o in active if o['id'] != s['replaces']]
        rec = site_record(s, 'alternative', inp, prm, fcls, ol, free, others)
        rec.update(decision=s['decision'], replaces=s['replaces'])
        alternatives.append(rec)

    holes = []
    for h in ruled['access_holes']:
        s = next(f for f in fixings if f['id'] == h['for'])
        r_hole = h['diameter_mm'] / 2
        inside = s['active'] and h['board'] in s['boards'] and math.dist(h['xy'], s['xy']) + r_hole <= s['keepout_radius_mm'][h['board']] + EPS
        holes.append(dict(h, keepout_radius_mm=s['keepout_radius_mm'].get(h['board']),
                          centre_offset_mm=r3(math.dist(h['xy'], s['xy'])), inside_applied_keepout=inside))

    scans = region_scans(inp, prm, fcls, ol, free, [p for p in posts])
    scans['corners'] = corner_tests(inp, prm, fcls, ol)

    grid = k_grid(cand, val(prm['grid_mm']))
    cov = coverage(grid, active, COVER_SCREEN_MM)
    cov['posts_only'] = farthest(grid, [p['xy'] for p in posts])
    cov['nearest_post_mm'] = {s['id']: r3(min(math.dist(s['xy'], p['xy']) for p in posts))
                              for s in fixings if s['kind'] == 'sleeve added'}

    act_sleeves = [f for f in active if f['kind'] != 'post']
    long_n = sum(1 for f in act_sleeves if f['gap_mm'] == 19.0)
    short_n = sum(1 for f in act_sleeves if f['gap_mm'] == 17.0)
    plate = val(prm['plate'])
    counts = {'fixings': len(active), 'posts': len(posts), 'sleeves': len(act_sleeves), 'long_19': long_n,
              'short_17': short_n, 'dropped': sum(1 for f in fixings if not f['active']),
              'fastener_operations': {'post_screws': 2 * len(posts), 'sleeve_screws': len(act_sleeves),
                                      'sleeve_nuts': len(act_sleeves),
                                      'total': 2 * len(posts) + 2 * len(act_sleeves),
                                      'basis': 'DERIVED: a post takes a screw from each board; a sleeve one screw and one nut'},
              'plate': plate, 'plate_covers': long_n <= plate['long'] and short_n <= plate['short']}
    moves = [m for f in act_sleeves for m in f['part_moves'] if m['class'] == 'movable']
    parts = {'movable_in_sleeve_keepouts': len(moves),
             'without_free_position': sum(1 for m in moves if m['nearest_free_origin'] is None),
             'without_free_position_not_decided': sum(1 for m in moves if m['nearest_free_origin'] is None and 'decided_by' not in m)}
    ruled_findings = [(f['id'], x) for f in act_sleeves for x in f['findings']]
    return {
        'verdict': 'DONE' if not ruled_findings else 'NEEDS_DESIGN',
        'ruled_findings': [list(x) for x in ruled_findings],
        'parameters': prm,
        'fixings': fixings,
        'reserve': reserve,
        'alternatives': alternatives,
        'access_holes': holes,
        'screw': screw_figures(prm, inp),
        'counts': counts,
        'parts': parts,
        'coverage': cov,
        'region_scans': scans,
        'authority': {'scans': ruled['authority_scans'], 'coverage': ruled['manager_coverage'], 'parts': ruled['authority_parts']},
        'movement_limit': {'rule': 'DS-72: K moves at most 1.4 mm under 5 g anywhere, by the grillage of ST-03',
                           'status': 'NOT RUN on this list until ST-03 attempt a6 reports'},
    }


def kicad_xy(xy, inp):
    t = inp['raw']['lock']['frame']['kicad_translation_mm']
    return [r3(xy[0] + t['x']), r3(xy[1] + t['y'])]


def screw_figures(prm, inp):
    planes = inp['cand']['planes']
    s = inp['ruled']['screw']
    env = val(prm['rear_envelope_mm'])
    rows = []
    for cls, fb in (('long sleeve, JL or JR to K', 'JL'), ('short sleeve, P to K', 'P')):
        grip = r3(planes[fb]['face_z_mm'] - planes['K']['rear_z_mm'])
        stand = r3(s['length_mm'] - grip)
        rows.append({'class': cls, 'grip_mm': grip, 'thread_behind_K_rear_mm': stand, 'rear_envelope_mm': env,
                     'inside_envelope': stand <= env + EPS,
                     'grip_source': 'stack-candidate.json planes: %s face z %.1f to K rear z %.1f' % (
                         fb, planes[fb]['face_z_mm'], planes['K']['rear_z_mm'])})
    return {'working_figure': s, 'classes': rows, 'nut_height_mm': 'UNSOURCED', 'washer_thickness_mm': 'UNSOURCED',
            'head_against_panel_test_mm': val(prm['panel_head_radius_mm']),
            'head_fits_panel_test': s['head_max_mm'] / 2 <= val(prm['panel_head_radius_mm']) + EPS}


def generate(root=ROOT):
    inp = load_inputs(root)
    body = build(inp)
    doc = {'schema_version': 2, 'task': 'osc-stack-20261114/ST-08 a2 part 1',
           'status': ('GENERATED PAPER CHECK of the ruled fixing list (DS-72 to DS-76) on unvalidated drafts; '
                      'courtyard-level screen; no fit, strength or strain claim; not adopted'),
           'provenance': {'generator': 'scripts/stack/fixings/fixings.py', 'regenerate': REGEN, 'pins': pins(root)}}
    doc.update(body)
    return doc, inp


def render(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def main(argv):
    import fixings_check
    import fixings_readme
    doc, inp = generate()
    text, md = render(doc), fixings_readme.render(doc)
    if '--check' in argv:
        bad = []
        if SITES_JSON.read_text() != text:
            bad.append('fixing-sites.json is stale; regenerate with: ' + REGEN)
        if README.read_text() != md:
            bad.append('README.md is stale; regenerate with: ' + REGEN)
        bad += ['[%s] %s' % e for e in fixings_check.check(json.loads(SITES_JSON.read_text()), inp)]
        for e in bad:
            print('FAIL', e)
        return 1 if bad else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SITES_JSON.write_text(text)
    README.write_text(md)
    errs = fixings_check.check(doc, inp)
    print('wrote', SITES_JSON.relative_to(ROOT), README.relative_to(ROOT), '; verdict', doc['verdict'],
          '; checker findings', len(errs))
    for e in errs:
        print('  ', e)
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
