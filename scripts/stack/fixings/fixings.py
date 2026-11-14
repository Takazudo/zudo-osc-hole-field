"""Fixing list of the flat-link stack (ST-08 attempt a1, part 1; ruling DS-66).

Applies the two rules of DS-66 to the fixings of the core board K: a printed sleeve stays only where no other
fixing of K lies within 70 mm, and no point of K is farther than 90 mm from a fixing. Writes
`design/stack/fixings/fixing-sites.json` and `design/stack/fixings/README.md`.

A courtyard-level paper screen on unvalidated drafts: not a copper clearance, a DRC, a fit or a strength result.
No KiCad: the boards are parsed with the plain-Python reader of `scripts/stack/geometry/` (imported, not changed).

  python3 scripts/stack/fixings/fixings.py           # write the JSON and the README
  python3 scripts/stack/fixings/fixings.py --check   # fail if a retained file differs or the checker fails
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, milp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
sys.path.insert(0, str(HERE))
import stackgeom as sg  # noqa: E402

OUT_DIR = ROOT / 'design/stack/fixings'
SITES_JSON = OUT_DIR / 'fixing-sites.json'
README = OUT_DIR / 'README.md'
REGEN = 'python3 scripts/stack/fixings/fixings.py'
CAMPAIGN = 'circuit/orchestration/campaigns/osc-stack-20261114'

CANDIDATE = 'design/stack/geometry/stack-candidate.json'
JOINTS = 'design/stack/power-posts/joint-design.json'
LINK_OPTIONS = 'design/stack/geometry/links/link-options.json'
SPACERS = 'design/stack/spacers/spacer-set.json'
INPUT_FILES = [CANDIDATE, JOINTS, LINK_OPTIONS, SPACERS, sg.JSON_FILES['lock'], sg.JSON_FILES['partition'],
               CAMPAIGN + '/decisions.md', CAMPAIGN + '/reviews/da-03.md', 'design/stack/mechanics/README.md',
               'design/stack/power-posts/README.md']
BOARDS = ('K', 'JL', 'JR', 'P', 'EL')
PROGRAM = ['scripts/stack/fixings/fixings.py', 'scripts/stack/fixings/fixings_check.py',
           'scripts/stack/fixings/fixings_readme.py', 'scripts/stack/geometry/stackgeom.py',
           'scripts/stack/geometry/kicad_extract.py']
FRONTS = ('JL', 'JR', 'P')
PANEL_KINDS = ('jack', 'led', 'pot', 'switch', 'button')
PAIRED = (('JL-SUP-1', 'JL-SUP-2'), ('JR-SUP-1', 'JR-SUP-2'), ('K-SUP-5', 'K-SUP-7'))
NAMED_DROPS = ('JL-SUP-3', 'JR-SUP-3', 'K-SUP-3', 'K-SUP-4')
BEST_COVER_STEP_MM = 0.5
TIER2 = {'grid_mm': 1.0, 'thin_mm': 4.0}
PROVISIONAL = ((227, 38), (227, 80), (108, 80), (202, 255), (252, 241))


def r3(v):
    return round(float(v) + 0.0, 3)


def term(value, status, source):
    return {'value': value, 'status': status, 'source': source}


def val(t):
    return t['value'] if isinstance(t, dict) else t


# ---------------------------------------------------------------- inputs

def load_inputs(root=ROOT):
    root = Path(root)
    raw = sg.load_raw(root)
    boards = sg.load_boards(raw, root, files={k: sg.BOARD_FILES[k] for k in BOARDS})
    rd = lambda p: json.loads((root / p).read_text())  # noqa: E731
    return {'raw': raw, 'boards': boards, 'cand': rd(CANDIDATE)['candidate'], 'joints': rd(JOINTS),
            'opts': rd(LINK_OPTIONS), 'spacers': rd(SPACERS), 'root': root}


def input_hashes(root=ROOT):
    paths = INPUT_FILES + [sg.BOARD_FILES[k] for k in BOARDS] + PROGRAM
    return {p: sg.sha256_file(Path(root) / p) for p in sorted(paths)}


def parameters(inp):
    opts, sp, cand = inp['opts'], inp['spacers'], inp['cand']
    long_m = next(m for m in sp['members'] if m['id'] == 'gap-19')
    short_m = next(m for m in sp['members'] if m['id'] == 'gap-17')
    return {
        'sleeve_min_spacing_mm': term(70.0, 'SOURCED', 'DS-66 (reviews/da-03.md c1 G8): a printed sleeve only where no other fixing of K lies within 70 mm'),
        'coverage_max_mm': term(90.0, 'SOURCED', 'DS-66: no point of K farther than 90 mm from a fixing'),
        'grid_mm': term(1.0, 'STATED', 'ST-08 grid over K\'s outline; the outline has integer corners, so a point between nodes lies at most 0.71 mm farther than its nearest node'),
        'keepout_radius_K_mm': term(val(opts['fixing_keepout_radius_mm']['K']), 'ASSUMED',
                                    'link-options.json fixing_keepout_radius_mm.K (SOURCED for posts, ASSUMED equal for sleeves; washer and nut on K\'s rear face)'),
        'keepout_radius_front_mm': term(val(opts['fixing_keepout_radius_mm']['front']), 'ASSUMED',
                                        'link-options.json fixing_keepout_radius_mm.front (7.0 mm sleeve inside 3.75 mm, DS-45); applied on both faces and on EL where a site lies under EL'),
        'sleeve_outer_diameter_mm': term(sp['sleeve']['outer_diameter_mm'], 'SOURCED', 'spacer-set.json sleeve.outer_diameter_mm (DS-45)'),
        'sleeve_bore_mm': term(sp['sleeve']['bore_diameter_mm'], 'SOURCED', 'spacer-set.json sleeve.bore_diameter_mm (DS-45)'),
        'panel_head_radius_mm': term(3.0, 'SOURCED', 'design/stack/power-posts/README.md item 4 and DS-44: 3.0 mm keep-out of a 5.5 mm M3 head without washer against locked panel hardware; DS-45: the sleeve screw has its washer on K, not on the panel side'),
        'board_edge_margin_mm': term(val(opts['board_edge_margin_mm']), 'SOURCED', 'link-options.json board_edge_margin_mm'),
        'ceramic_radius_mm': term(5.0, 'SOURCED', 'DS-42: no ceramic part of 0805 or larger within 5 mm of a fixing'),
        'ceramic_min_case': term('0805', 'SOURCED', 'DS-42'),
        'move_search': term({'step_mm': 0.25, 'directions': 24, 'max_mm': 12.0, 'outline_margin_mm': 0.3}, 'SOURCED',
                            'the method of ST-04 (design/stack/power-posts/envelopes.json "method")'),
        'gap_mm': term({'JL': 19.0, 'JR': 19.0, 'P': 17.0}, 'SOURCED',
                       'DS-33 and DS-45: gaps 19.0 mm (JL, JR) and 17.0 mm (P)'),
        'board_thickness_mm': term(cand['planes']['K']['thickness_mm'], 'SOURCED', 'stack-candidate.json planes.*.thickness_mm (K, JL, JR, P 1.6 mm)'),
        'sleeve_length_mm': term({'19.0': r3(19.0 + sp['length_allowance_mm']), '17.0': r3(17.0 + sp['length_allowance_mm'])},
                                 'SOURCED', 'spacer-set.json length_allowance_mm (modelled 0.2 mm short)'),
        'plate': term({'long': long_m['quantity'] + long_m['spares'], 'short': short_m['quantity'] + short_m['spares']}, 'SOURCED',
                      'spacer-set.json members quantity + spares (one plate)'),
        'washer_thickness_mm': term(None, 'UNSOURCED', 'no M3 washer drawing retained (joint-design.json washer_od_mm is ASSUMED, no thickness)'),
        'nut_height_mm': term(None, 'UNSOURCED', 'no M3 nut drawing retained'),
        'thread_protrusion_mm': term(None, 'UNSOURCED', 'no retained rule for the thread length beyond the nut'),
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
        if not (d < r - 1e-9 or (cer and d <= rc + 1e-9)):
            continue
        h = {'board': board, 'ref': f['ref'], 'lib': f['lib'], 'value': f['value'], 'class': cls,
             'faces': list(faces(f)), 'distance_mm': r3(d), 'in_keepout': d < r - 1e-9,
             'ceramic_0805_or_larger_within_5mm': bool(cer and d <= rc + 1e-9)}
        if cls.startswith('panel hardware'):
            dp = min((box_dist(p['bbox'], xy) for p in f['pads'] if any(l in ('B.Cu', '*.Cu') for l in p['layers'])),
                     default=None)
            h['panel_face_courtyard_mm'] = r3(d)
            h['rear_face_pad_mm'] = None if dp is None else r3(dp)
            h['in_keepout'] = d < rh - 1e-9 or (dp is not None and dp < r - 1e-9)
        hits.append(h)
    return sorted(hits, key=lambda h: h['ref'])


def _rect_dist(pts, rects):
    r = np.asarray(rects, dtype=float)
    dx = np.maximum(np.maximum(r[None, :, 0] - pts[:, None, 0], 0), pts[:, None, 0] - r[None, :, 2])
    dy = np.maximum(np.maximum(r[None, :, 1] - pts[:, None, 1], 0), pts[:, None, 1] - r[None, :, 3])
    return np.hypot(dx, dy).min(1)


def fixed_clear_mask(pts, board, fcls, prm):
    """Vectorised pre-screen of grid nodes: False where locked panel hardware or a fixed hole on `board` blocks a
    site by the same rule as keepout_hits. A True node is screened in full afterwards."""
    r = radius_on(board, prm)
    rh = val(prm['panel_head_radius_mm'])
    court, pads, holes = [], [], []
    for f, cls in fcls[board]:
        if cls.startswith('panel hardware'):
            court.append(box(f))
            pads += [p['bbox'] for p in f['pads'] if any(l in ('B.Cu', '*.Cu') for l in p['layers'])]
        elif cls == 'hole':
            holes.append(box(f))
    ok = np.ones(len(pts), dtype=bool)
    for rects, rad in ((court, rh), (pads, r), (holes, r)):
        for i in range(0, len(pts), 20000):
            if rects:
                ok[i:i + 20000] &= _rect_dist(pts[i:i + 20000], rects) >= rad - 1e-9
    return ok


def obstacle_reasons(xy, front, ol, cand, prm, edge=None):
    """Why a point cannot carry a sleeve: board edges, tabs, adapters, selectors, sub toggles. `edge` is the radius
    that must stay inside every pierced outline: the sleeve plus margin for an added site, the bore plus margin for
    one of the twelve given sites."""
    why = []
    rf = val(prm['keepout_radius_front_mm'])
    if edge is None:
        edge = val(prm['sleeve_outer_diameter_mm']) / 2 + val(prm['board_edge_margin_mm'])
    for b in pierced(xy, front, ol):
        if not sg.point_in_poly(xy[0], xy[1], ol[b]) or sg.distance_to_outline(xy[0], xy[1], ol[b]) < edge - 1e-9:
            why.append('board edge of %s within %.2f mm' % (b, edge))
    if front == 'P':
        el = ol['EL']
        if not sg.point_in_poly(xy[0], xy[1], el) and sg.distance_to_outline(xy[0], xy[1], el) < rf - 1e-9:
            why.append('straddles the EL edge')
    for t in cand['tabs']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, t['rect']) > 1e-9:
            why.append('tab ' + t['id'])
    for a in ('O1', 'O3', 'O5'):
        o = cand['planes'][a]['outline']
        if sg.point_in_poly(xy[0], xy[1], o) or sg.distance_to_outline(xy[0], xy[1], o) < rf - 1e-9:
            why.append('adapter ' + a)
    for s in cand['selectors_kept']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, s['courtyard']) > 1e-9:
            why.append('kept selector ' + s['ref'])
    for s in cand['sub_toggles']:
        if sg.circle_rect_depth(xy[0], xy[1], rf, s['toggle_courtyard']) > 1e-9:
            why.append('sub toggle ' + s['block'])
    return why


# ---------------------------------------------------------------- nearest free position (ST-04's method)

class FreeSearch:
    def __init__(self, fcls, ol, prm):
        self.fcls, self.ol, self.prm = fcls, ol, prm
        self.index = {}
        for b in BOARDS:
            idx = {'F': sg.RectIndex(), 'B': sg.RectIndex()}
            for f, _ in fcls[b]:
                for s in faces(f):
                    idx[s].add(box(f), f['ref'])
            self.index[b] = idx

    def search(self, board, f, circles):
        """Smallest shift whose box clears every fixing circle on the board (5 mm for a ceramic of 0805 or larger),
        every other footprint box on its faces and stays inside the outline; None when none within the limit."""
        ms = val(self.prm['move_search'])
        cer = ceramic_at_least(f, val(self.prm['ceramic_min_case']))
        rc = val(self.prm['ceramic_radius_mm'])
        b0 = box(f)
        fs = faces(f)
        for k in range(1, int(ms['max_mm'] / ms['step_mm']) + 1):
            d = k * ms['step_mm']
            for i in range(ms['directions']):
                a = math.radians(i * 360 / ms['directions'])
                dx, dy = d * math.cos(a), d * math.sin(a)
                nb = [b0[0] + dx, b0[1] + dy, b0[2] + dx, b0[3] + dy]
                if any(box_dist(nb, c) < (max(r, rc) if cer else r) - 1e-9 for c, r in circles):
                    continue
                if any(ref != f['ref'] for s in fs for rect, ref in self.index[board][s].near(nb) if sg.inter(nb, rect)):
                    continue
                if not sg.rect_inside_poly(nb, self.ol[board], ms['outline_margin_mm']):
                    continue
                return r3(d), [r3(f['origin'][0] + dx), r3(f['origin'][1] + dy)]
        return None, None


def fixing_circles(fixings, board, prm):
    """(centre, radius) of every fixing that pierces `board`."""
    out = []
    for fx in fixings:
        if fx['kind'] == 'sleeve dropped' or board not in fx['boards']:
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
    gx = np.arange(min(xs), max(xs) + 1e-9, step)
    gy = np.arange(min(ys), max(ys) + 1e-9, step)
    pts = [(x, y) for y in gy for x in gx
           if sg.point_in_poly(x, y, ol) or sg.distance_to_outline(x, y, ol) < 1e-9]
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
    pts = grid[d > cover + 1e-9]
    dd = d[d > cover + 1e-9]
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


# ---------------------------------------------------------------- selection

def solve(grid, fixed_xy, cands, paired, prm, forced=None, relax=None):
    """Smallest set of added sites, with one member of each sleeve pair kept, meeting both rules on the grid.

    Variables: one per candidate site, one per paired sleeve. Minimises 1000 x the count of added sites plus their
    part moves (a tie-break), so the count is minimal for the candidate set on this grid. `forced` fixes a paired
    sleeve's choice. Returns (chosen candidate indices, kept paired ids) or None when infeasible."""
    spacing = val(prm['sleeve_min_spacing_mm'])
    cover = val(prm['coverage_max_mm'])
    items = [('cand', c['id'], c['xy']) for c in cands] + [('pair', sid, xy) for pr in paired for sid, xy in pr]
    n = len(items)
    xy = np.array([it[2] for it in items], dtype=float)
    fixed = np.array(fixed_xy, dtype=float)
    dfix = np.sqrt(((grid[:, None, :] - fixed[None]) ** 2).sum(-1)).min(1)
    need = grid[dfix > cover + 1e-9]
    rows, lo, hi = [], [], []
    if len(need):
        dn = np.sqrt(((need[:, None, :] - xy[None]) ** 2).sum(-1))
        for row in np.unique(dn <= cover + 1e-9, axis=0):
            if not row.any():
                if relax is None:
                    return None
                continue
            rows.append(row.astype(float))
            lo.append(1)
            hi.append(np.inf)
        far_rows = (dn.min(1) > cover + 1e-9) & (dfix[dfix > cover + 1e-9] > (relax or 0) + 1e-9)
        if relax is not None and far_rows.any():
            for row in np.unique(dn[far_rows] <= relax + 1e-9, axis=0):
                if not row.any():
                    return None
                rows.append(row.astype(float))
                lo.append(1)
                hi.append(np.inf)
    for i in range(n):
        for j in range(i + 1, n):
            if math.dist(items[i][2], items[j][2]) < spacing - 1e-9:
                r = np.zeros(n)
                r[i] = r[j] = 1
                rows.append(r)
                lo.append(0)
                hi.append(1)
    for pr in paired:
        if not pr:
            continue
        r = np.zeros(n)
        for sid, _ in pr:
            r[next(k for k, it in enumerate(items) if it[1] == sid)] = 1
        rows.append(r)
        lo.append(1)
        hi.append(1)
    lb, ub = np.zeros(n), np.ones(n)
    for k, it in enumerate(items):
        if len(fixed) and np.sqrt(((fixed - np.array(it[2])) ** 2).sum(-1)).min() < spacing - 1e-9:
            ub[k] = 0
    for sid, keep in (forced or {}).items():
        k = next(k for k, it in enumerate(items) if it[1] == sid)
        lb[k] = ub[k] = 1 if keep else 0
    cost = np.array([1000.0 + c['move_count'] + 1e-3 * i for i, c in enumerate(cands)] + [0.0] * (n - len(cands)))
    res = milp(cost, constraints=LinearConstraint(sparse.csr_array(np.array(rows)), lo, hi), integrality=np.ones(n),
               bounds=Bounds(lb, ub), options={'mip_rel_gap': 0, 'presolve': True})
    if res.status != 0:
        return None
    x = np.round(res.x).astype(int)
    chosen = [items[k][1] for k in range(n) if x[k] and items[k][0] == 'cand']
    kept = [items[k][1] for k in range(n) if x[k] and items[k][0] == 'pair']
    return chosen, kept


# ---------------------------------------------------------------- build

def build(inp):
    cand, prm = inp['cand'], parameters(inp)
    ol = outlines(cand)
    fcls = footprint_classes(inp)
    free = FreeSearch(fcls, ol, prm)
    rk, rf = val(prm['keepout_radius_K_mm']), val(prm['keepout_radius_front_mm'])
    spacing, cover = val(prm['sleeve_min_spacing_mm']), val(prm['coverage_max_mm'])

    posts = []
    for j in inp['joints']['joints']:
        kr = {'K': rk, j['front_board']: rf}
        posts.append({'id': j['id'], 'kind': 'post', 'xy': list(j['K_xy']), 'front_xy': list(j['front_xy']),
                      'front_board': j['front_board'], 'boards': ['K', j['front_board']], 'gap_mm': j['gap_mm'],
                      'keepout_radius_mm': kr,
                      'panel_side_keepout_radius_mm': j.get('panel_side_keepout_radius_mm', rf),
                      'source': JOINTS + ' joints (DS-44 lands govern over stack-candidate.json)'})
    sleeves = []
    for f in cand['fixings']:
        if f['kind'] != 'kept support':
            continue
        fb = f['front_board']
        bs = pierced(f['xy'], fb, ol)
        sleeves.append({'id': f['id'], 'xy': list(f['xy']), 'front_board': fb, 'boards': bs,
                        'gap_mm': val(prm['gap_mm'])[fb], 'keepout_radius_mm': {b: radius_on(b, prm) for b in bs}})
    by_id = {s['id']: s for s in sleeves}
    post_xy = [p['xy'] for p in posts]

    grid = k_grid(cand, val(prm['grid_mm']))

    # inventory: nearest other fixing among the 30 present fixings
    present = [(p['id'], p['xy']) for p in posts] + [(s['id'], s['xy']) for s in sleeves]
    inventory = []
    for fx in posts + sleeves:
        others = [(i, xy) for i, xy in present if i != fx['id']]
        inventory.append({'id': fx['id'], 'kind': 'post' if fx in posts else 'sleeve', 'xy': fx['xy'],
                          'front_board': fx['front_board'], 'gap_mm': fx['gap_mm'],
                          'nearest_other_fixing': nearest_other(fx['xy'], others)})

    # the twelve given sites: a site on locked panel hardware or on a fixed hole cannot be kept (no locked part moves)
    hole_edge = val(prm['sleeve_bore_mm']) / 2 + val(prm['board_edge_margin_mm'])
    for s in sleeves:
        why = obstacle_reasons(s['xy'], s['front_board'], ol, cand, prm, edge=hole_edge)
        for b in s['boards']:
            for h in keepout_hits(s['xy'], b, fcls, prm):
                if h['in_keepout'] and h['class'] != 'movable':
                    why.append('%s %s on %s at %.2f mm' % (h['class'], h['ref'], h['board'], h['distance_mm']))
        s['site_conflicts'] = sorted(set(why))
    eligible = {s['id'] for s in sleeves if not s['site_conflicts']}

    # rule of 70 mm, step 1: sleeves that conflict with a post or with a sleeve that has no partner choice
    paired_ids = {i for pr in PAIRED for i in pr}
    always = [s['id'] for s in sleeves if s['id'] not in paired_ids and s['id'] not in NAMED_DROPS
              and s['id'] in eligible]
    fixed_xy = post_xy + [by_id[i]['xy'] for i in always]

    # candidates: the five provisional sites and the clear sites of the geometry candidate
    raw_c = [('PROV-%d' % (k + 1), list(xy), 'provisional tie site (reviews/da-01.md D4)') for k, xy in enumerate(PROVISIONAL)]
    for b, lst in sorted(cand['interior_candidate_sites']['sites'].items()):
        raw_c += [('CS-%s-%d' % (b, k + 1), list(xy), 'clear candidate site of stack-candidate.json (%s)' % b)
                  for k, xy in enumerate(lst)]
    def screen(cid, xy, origin, quick=False):
        front = front_board_at(xy, ol)
        rec = {'id': cid, 'xy': [r3(v) for v in xy], 'origin': origin, 'front_board': front}
        if quick and (front is None or min(math.dist(xy, q) for q in fixed_xy) < spacing - 1e-9):
            rec['rejected'] = ['quick reject']
            return rec
        why = []
        if front is None:
            why.append('no facing front board')
        else:
            why += obstacle_reasons(xy, front, ol, cand, prm)
        near = nearest_other(xy, [(f['id'], f['xy']) for f in posts] + [(i, by_id[i]['xy']) for i in always])
        if near['distance_mm'] < spacing - 1e-9:
            why.append('within %.0f mm of %s (%.1f mm)' % (spacing, near['id'], near['distance_mm']))
        hits = []
        if front is not None:
            for b in pierced(xy, front, ol):
                hits += keepout_hits(xy, b, fcls, prm)
            for h in hits:
                if h['in_keepout'] and h['class'] != 'movable':
                    why.append('%s %s on %s at %.2f mm' % (h['class'], h['ref'], h['board'], h['distance_mm']))
        rec['rejected'] = sorted(set(why))
        rec['move_count'] = len(hits)
        return rec

    screened = [screen(*c) for c in raw_c]
    usable = [c for c in screened if not c['rejected']]
    paired_xy = [[(i, by_id[i]['xy']) for i in pr if i in eligible] for pr in PAIRED]
    sol = solve(grid, fixed_xy, usable, paired_xy, prm)
    tier1 = {'candidates': len(raw_c), 'usable': len(usable), 'feasible': sol is not None}

    # second tier, used only when the stated set cannot meet both rules: a screen of K on a stated grid
    tier2 = None
    pool = usable
    clear_nodes = []
    if sol is None:
        step, thin = TIER2['grid_mm'], TIER2['thin_mm']
        ok = []
        xs = [p[0] for p in ol['K']]
        ys = [p[1] for p in ol['K']]
        pts = np.array([(x, y) for y in np.arange(min(ys), max(ys) + 1e-9, step)
                        for x in np.arange(min(xs), max(xs) + 1e-9, step)], dtype=float)
        dpost = np.sqrt(((pts[:, None, :] - np.array(fixed_xy)[None]) ** 2).sum(-1)).min(1)
        pts = pts[dpost >= spacing - 1e-9]
        mask = np.ones(len(pts), dtype=bool)
        for b in ('JL', 'JR', 'P', 'EL'):
            mask &= fixed_clear_mask(pts, b, fcls, prm)
        for x, y in pts[mask]:
            rec = screen('G', [float(x), float(y)], 'grid screen of ST-08', quick=True)
            if not rec['rejected']:
                ok.append(rec)
        kept = []
        for rec in sorted(ok, key=lambda c: (c['move_count'], c['xy'][1], c['xy'][0])):
            if all(math.dist(rec['xy'], k['xy']) >= thin - 1e-9 for k in kept):
                kept.append(rec)
        kept.sort(key=lambda c: (c['xy'][1], c['xy'][0]))
        for k, rec in enumerate(kept):
            rec['id'] = 'GS-%d' % (k + 1)
        pool = usable + kept
        clear_nodes = ok
        sol = solve(grid, fixed_xy, pool, paired_xy, prm)
        tier2 = {'grid_mm': step, 'thin_mm': thin, 'clear_nodes': len(ok), 'candidates': len(kept),
                 'feasible': sol is not None, 'sites': [{'id': c['id'], 'xy': c['xy'], 'front_board': c['front_board'],
                                                         'move_count': c['move_count']} for c in kept]}
    # when both rules cannot be met: the smallest farthest distance reachable with the 70 mm rule kept
    best_cover = cover
    lower_bound = farthest(grid, fixed_xy + [c['xy'] for c in pool + clear_nodes] + [xy for pr in paired_xy for _, xy in pr])
    if sol is None:
        best_cover = math.ceil(lower_bound[0] / BEST_COVER_STEP_MM - 1e-9) * BEST_COVER_STEP_MM
        while solve(grid, fixed_xy, pool, paired_xy, prm, relax=best_cover) is None and best_cover < 2 * cover:
            best_cover += BEST_COVER_STEP_MM
        sol = solve(grid, fixed_xy, pool, paired_xy, prm, relax=best_cover)
    alternatives = []
    for pr in PAIRED:
        for sid in [i for i in pr if i in eligible]:
            s_ = solve(grid, fixed_xy, pool, paired_xy, prm, forced={sid: True}, relax=best_cover if best_cover > cover else None)
            alternatives.append({'pair': list(pr), 'kept': sid, 'added_sites': None if s_ is None else len(s_[0]),
                                 'farthest_mm': None if s_ is None else farthest(
                                     grid, fixed_xy + [c['xy'] for c in pool if c['id'] in s_[0]] +
                                     [by_id[i]['xy'] for i in s_[1]])[0]})
    if sol is None:
        return {'feasible': False, 'parameters': prm, 'screened': screened, 'inventory': inventory,
                'tier1': tier1, 'tier2': tier2, 'alternatives': alternatives}
    usable = pool
    chosen, kept_pairs = sol
    chosen_recs = sorted([c for c in usable if c['id'] in chosen], key=lambda c: (c['xy'][1], c['xy'][0]))

    # final fixing list
    fixings = []
    for p in posts:
        fixings.append(dict(p, status='post (DS-43, DS-44)'))
    kept_ids = set(always) | set(kept_pairs)
    for s in sleeves:
        if s['id'] in kept_ids:
            kind, status = 'sleeve kept', 'kept under DS-66: no other fixing within 70 mm'
        else:
            kind = 'sleeve dropped'
            status = ('dropped by DS-66 (named)' if s['id'] in NAMED_DROPS else
                      'dropped: site conflicts (%s)' % '; '.join(s['site_conflicts']) if s['id'] not in eligible else
                      'dropped by DS-66 (pair choice of ST-08)' if s['id'] in paired_ids else
                      'dropped by DS-66 (within 70 mm of another fixing)')
        fixings.append(dict(s, kind=kind, front_xy=s['xy'], status=status,
                            length_class=str(s['gap_mm'])))
    for k, c in enumerate(chosen_recs):
        bs = pierced(c['xy'], c['front_board'], ol)
        fixings.append({'id': 'SLV-%s-%d' % ('U' if c['front_board'] in ('JL', 'JR') else 'L', k + 1),
                        'kind': 'sleeve added', 'xy': c['xy'], 'front_xy': c['xy'], 'front_board': c['front_board'],
                        'boards': bs, 'gap_mm': val(prm['gap_mm'])[c['front_board']],
                        'keepout_radius_mm': {b: radius_on(b, prm) for b in bs},
                        'length_class': str(val(prm['gap_mm'])[c['front_board']]),
                        'candidate': c['id'], 'origin': c['origin'],
                        'status': 'added under DS-66 (ST-08 a1 part 1 proposal)'})
    for fx in fixings:
        if fx['kind'] == 'post':
            fx['length_class'] = None
    # renumber added ids per edge in order
    up = [f for f in fixings if f['kind'] == 'sleeve added' and f['front_board'] in ('JL', 'JR')]
    lo = [f for f in fixings if f['kind'] == 'sleeve added' and f['front_board'] == 'P']
    for pre, grp in (('SLV-U', sorted(up, key=lambda f: f['xy'][0])), ('SLV-L', sorted(lo, key=lambda f: f['xy'][0]))):
        for k, f in enumerate(grp):
            f['id'] = '%s%d' % (pre, k + 1)

    active = [f for f in fixings if f['kind'] != 'sleeve dropped']
    for fx in fixings:
        others = [(o['id'], o['xy']) for o in active if o['id'] != fx['id']]
        fx['nearest_other_fixing'] = nearest_other(fx['xy'], others)
        fx['K_kicad_xy'] = kicad_xy(fx['xy'], inp)
        fx['front_kicad_xy'] = kicad_xy(fx['front_xy'], inp)

    # part moves and ceramics for kept and added sleeves (and ceramics for posts)
    for fx in fixings:
        if fx['kind'] == 'sleeve dropped':
            continue
        hits = []
        for b in fx['boards']:
            hits += keepout_hits(fx['xy'], b, fcls, prm)
        moves = []
        for h in hits:
            if fx['kind'] == 'post' and not h['ceramic_0805_or_larger_within_5mm']:
                continue  # post keep-outs belong to ST-04 (design/stack/power-posts/envelopes.json)
            f = next(f for f, _ in fcls[h['board']] if f['ref'] == h['ref'])
            if h['class'] == 'movable':
                shift, pos = free.search(h['board'], f, fixing_circles(active, h['board'], prm))
            else:
                shift, pos = None, None
            moves.append(dict(h, origin=[r3(v) for v in f['origin']], nearest_free_shift_mm=shift,
                              nearest_free_origin=pos))
        fx['part_moves'] = sorted(moves, key=lambda m: (m['board'], m['ref']))
        if fx['kind'] == 'sleeve added':
            fx['site_conflicts'] = obstacle_reasons(fx['xy'], fx['front_board'], ol, cand, prm)
        if fx['kind'] != 'post':
            edge = min(sg.distance_to_outline(fx['xy'][0], fx['xy'][1], ol[b]) for b in fx['boards'])
            fx['edge_distance_mm'] = r3(edge)

    cover_before_posts = farthest(grid, post_xy)
    cover_before_all = farthest(grid, [f['xy'] for f in posts + sleeves])
    cover_after = farthest(grid, [f['xy'] for f in active])
    long_n = sum(1 for f in active if f['kind'] != 'post' and f['gap_mm'] == 19.0)
    short_n = sum(1 for f in active if f['kind'] != 'post' and f['gap_mm'] == 17.0)
    plate = val(prm['plate'])
    return {
        'feasible': True,
        'parameters': prm,
        'grid': {'step_mm': val(prm['grid_mm']), 'nodes': int(len(grid)),
                 'outline': cand['planes']['K']['outline']},
        'inventory': inventory,
        'screened': screened,
        'selection': {
            'method': ('integer program (scipy.optimize.milp, HiGHS, relative gap 0) over the screened candidate set: '
                       'binary choice per usable candidate and per paired sleeve; every grid node beyond 90 mm of the '
                       'fixed fixings must lie within 90 mm of a chosen site; any two chosen sleeves at least 70 mm '
                       'apart; exactly one sleeve of each named pair; objective 1000 per added site plus its keep-out '
                       'part count, so the site count is the minimum for this candidate set and grid'),
            'tier1_stated_set': tier1, 'tier2_grid_screen': tier2,
            'chosen': [c['id'] for c in chosen_recs], 'kept_from_pairs': sorted(kept_pairs),
            'pair_alternatives': alternatives,
        },
        'coverage': {'posts_only': cover_before_posts, 'present_30': cover_before_all, 'after': cover_after,
                     'rule_mm': cover, 'rule_met': cover_after[0] <= cover + 1e-9,
                     'best_reachable_mm': best_cover if best_cover > cover else None,
                     'lower_bound_any_selection': lower_bound,
                     'beyond_rule': beyond_rule(grid, [f['xy'] for f in active], cover)},
        'verdict': 'DONE' if cover_after[0] <= cover + 1e-9 else 'NEEDS_DESIGN',
        'counts': {'posts': len(posts), 'sleeves_kept': sum(1 for f in fixings if f['kind'] == 'sleeve kept'),
                   'sleeves_added': sum(1 for f in fixings if f['kind'] == 'sleeve added'),
                   'sleeves_dropped': sum(1 for f in fixings if f['kind'] == 'sleeve dropped'),
                   'long_19': long_n, 'short_17': short_n, 'plate': plate,
                   'plate_covers': long_n <= plate['long'] and short_n <= plate['short']},
        'fixings': fixings,
        'screws': screws(prm, inp),
    }


def kicad_xy(xy, inp):
    t = inp['raw']['lock']['frame']['kicad_translation_mm']
    return [r3(xy[0] + t['x']), r3(xy[1] + t['y'])]


def screws(prm, inp):
    """Grip per site class from retained heights; the washer, nut and protrusion are UNSOURCED, so no length is
    stated."""
    t = val(prm['board_thickness_mm'])
    planes = inp['cand']['planes']
    out = []
    for cls, fb, gap in (('sleeve, JL or JR to K', 'JL', 19.0), ('sleeve, P to K', 'P', 17.0)):
        grip = planes[fb]['face_z_mm'] - planes['K']['rear_z_mm']
        out.append({'class': cls, 'front_board_mm': t, 'gap_mm': gap, 'K_mm': t,
                    'grip_mm': r3(grip), 'grip_check_mm': r3(2 * t + gap),
                    'grip_source': 'stack-candidate.json planes: %s face z %.1f to K rear z %.1f' % (
                        fb, planes[fb]['face_z_mm'], planes['K']['rear_z_mm']),
                    'washer_mm': 'UNSOURCED', 'nut_mm': 'UNSOURCED', 'protrusion_mm': 'UNSOURCED',
                    'length': 'UNSOURCED: %.1f mm grip + washer + nut + protrusion' % (2 * t + gap)})
    el = planes['EL']
    out.append({'class': 'sleeve, P to K under EL', 'front_board_mm': t, 'gap_mm': 17.0, 'K_mm': t,
                'grip_mm': r3(planes['P']['face_z_mm'] - planes['K']['rear_z_mm']), 'grip_check_mm': r3(2 * t + 17.0),
                'grip_source': 'head on P\'s front face through a clearance hole in EL; head on EL\'s face (z %.1f) would '
                               'add %.1f mm and bridge the %.1f mm EL gap' % (
                                   el['face_z_mm'], el['face_z_mm'] - planes['P']['face_z_mm'],
                                   el['rear_z_mm'] - planes['P']['face_z_mm']),
                'washer_mm': 'UNSOURCED', 'nut_mm': 'UNSOURCED', 'protrusion_mm': 'UNSOURCED',
                'length': 'UNSOURCED: 20.2 mm grip + washer + nut + protrusion; how the screw passes EL is open'})
    return out


def generate(root=ROOT):
    inp = load_inputs(root)
    body = build(inp)
    doc = {'schema_version': 1, 'task': 'osc-stack-20261114/ST-08 a1 part 1',
           'status': ('GENERATED PAPER FIXING LIST on unvalidated drafts; courtyard-level screen; no fit, strength or '
                      'strain claim; not adopted'),
           'provenance': {'generator': 'scripts/stack/fixings/fixings.py', 'regenerate': REGEN,
                          'input_sha256': input_hashes(root)}}
    doc.update(body)
    import fixings_check
    doc['checker_findings'] = [list(e) for e in fixings_check.check(doc, inp)]
    return doc, inp


def render(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def main(argv):
    import fixings_readme
    doc, inp = generate()
    text, md = render(doc), fixings_readme.render(doc)
    if '--check' in argv:
        bad = []
        if SITES_JSON.read_text() != text:
            bad.append('fixing-sites.json is stale; regenerate with: ' + REGEN)
        if README.read_text() != md:
            bad.append('README.md is stale; regenerate with: ' + REGEN)
        for e in bad:
            print('FAIL', e)
        return 1 if bad else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SITES_JSON.write_text(text)
    README.write_text(md)
    print('wrote', SITES_JSON.relative_to(ROOT), README.relative_to(ROOT), '; verdict', doc['verdict'],
          '; checker findings', len(doc['checker_findings']))
    for e in doc['checker_findings']:
        print('  ', e)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
