"""MC04-S15 (DS-192): the no-growth rule NG of Rulings N1 to N3, on plain data (study only, nothing adopted).

Brief: circuit/orchestration/campaigns/osc-stack-20261114/mc04-s15-no-growth-moves-brief-20261128.md (Revision 3).
Pad-centre and connector-centre geometry only. The figures are lower-bound style estimates; they are not routed
lengths, areas or capacitances.

A model holds, per footprint key (board, ref): its paper record (`origin`, `side`, `pads` as
[(index, number, (x, y))] at the paper pose), its pins {number: net}, whether it has a pin record, whether it is
protected, and the open-IC set. A scene holds poses {key: (origin or None, face or None)}, turns {key: deg},
live links {lid: geometry} and, for NG5, link rectangles and courtyards.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # no bytecode is written into the S8, S9, S10 or S12 directories

import math  # noqa: E402

EPS = 1e-9
RAILS = frozenset({'AGND', 'GND', '+12V', '-12V', '+5V'})
LARGE = 8
TESTS = ('NG1', 'NG2', 'NG3', 'NG4', 'NG5', 'NG6', 'NG7')


def rot_pt(pt, origin, k):
    """replacement_a2.rot_pt (the turn used by overlay.ancillary_geometry.current_pad)."""
    x, y = pt
    for _ in range(int(k) // 90):
        x, y = origin[0] - (y - origin[1]), origin[1] + (x - origin[0])
    return x, y


def centre(rect):
    return ((rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0)


def pad_xy(fp, pad_xy0, pose, turn):
    """overlay.ancillary_geometry.current_pad: mirror on a face change, rotate by the effective turn, translate."""
    pos, face = pose
    dx, dy = pad_xy0[0] - fp['origin'][0], pad_xy0[1] - fp['origin'][1]
    if face != fp['side']:
        dx = -dx
    dx, dy = rot_pt((dx, dy), (0, 0), turn or 0)
    return pos[0] + dx, pos[1] + dy


def hpwl(pts):
    if len(pts) < 2:
        return 0.0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def rmst(pts):
    """Length of the rectilinear (Manhattan) minimum spanning tree (Prim, O(n^2)), unrounded."""
    n = len(pts)
    if n < 2:
        return 0.0
    inf = float('inf')
    best = [inf] * n
    used = [False] * n
    best[0] = 0.0
    total = 0.0
    for _ in range(n):
        i = min((j for j in range(n) if not used[j]), key=lambda j: best[j])
        used[i] = True
        total += best[i]
        xi, yi = pts[i]
        for j in range(n):
            if not used[j]:
                d = abs(pts[j][0] - xi) + abs(pts[j][1] - yi)
                if d < best[j]:
                    best[j] = d
    return total


class Scene:
    def __init__(self, poses, turns, links, rects=None, courtyards=None, name='scene'):
        self.poses = poses            # key -> (origin or None, face or None)
        self.turns = turns            # key -> deg
        self.links = links            # lid -> geometry (live links only)
        self.rects = rects or {}      # lid -> [(board, face, rect, what)]
        self.courtyards = courtyards or {}  # key -> rect (only needed for moved protected footprints)
        self.name = name

    def pose(self, key):
        return self.poses.get(key, (None, None))


class Model:
    def __init__(self, fps, link_nets, link_front, open_ics=(), protected_ics=None, gap=0.35):
        self.fps = fps                # key -> {'origin', 'side', 'pads', 'pins', 'pin_record', 'protected'}
        self.link_nets = link_nets    # lid -> set of nets
        self.link_front = link_front  # lid -> front board
        self.open_ics = set(open_ics)
        self.gap = gap
        self.net_fps = {}
        for key, fp in fps.items():
            for _, num, _ in fp['pads']:
                n = fp['pins'].get(num)
                if n:
                    self.net_fps.setdefault(n, set()).add(key)
        self.protected_nets = set()
        for n, keys in self.net_fps.items():
            if n not in RAILS and any(fps[k]['protected'] for k in keys):
                self.protected_nets.add(n)
        self.protected_ic = {k for k, fp in fps.items() if fp['protected'] and k[1].startswith('U')} \
            if protected_ics is None else set(protected_ics)
        self.nets_of = {}
        for n, keys in self.net_fps.items():
            for k in keys:
                self.nets_of.setdefault(k, set()).add(n)
        self.link_of_net = {}
        for lid, nets in link_nets.items():
            for n in nets:
                self.link_of_net.setdefault(n, set()).add(lid)
        self._fig = {}

    # ------------------------------------------------------------ poses
    def eff(self, scene, key):
        """(origin, face, turn) with the open-IC convention: a positionless open IC enters at its paper pose."""
        pos, face = scene.pose(key)
        if key in self.open_ics and pos is None:
            fp = self.fps[key]
            return tuple(fp['origin']), fp['side'], 0
        return (tuple(pos) if pos is not None else None), face, scene.turns.get(key, 0)

    def moved(self, base, scene, key):
        a, b = self.eff(base, key), self.eff(scene, key)
        if a[0] is None and b[0] is None:
            return False
        if a[0] is None or b[0] is None:
            return True
        return math.dist(a[0], b[0]) >= EPS or a[1] != b[1] or (a[2] or 0) != (b[2] or 0)

    # ------------------------------------------------------------ point sets and figures
    def points(self, scene, net, board):
        """({point id: (x, y)}, pin ids, computable) for P(net, board, scene) of Ruling N1."""
        pts, pins, ok = {}, [], True
        for key in sorted(self.net_fps.get(net, ())):
            if key[0] != board:
                continue
            fp = self.fps[key]
            pos, face, turn = self.eff(scene, key)
            for idx, num, xy in fp['pads']:
                if fp['pins'].get(num) != net:
                    continue
                if pos is None:
                    ok = False
                    continue
                pid = ('pad', key[0], key[1], idx)
                pts[pid] = pad_xy(fp, xy, (pos, face), turn)
                if key in self.protected_ic:
                    pins.append(pid)
        for lid in sorted(self.link_of_net.get(net, ())):
            geo = scene.links.get(lid)
            if geo is None:
                continue
            if board == 'K':
                pts[('link', lid, 'K')] = centre(geo['K_connector'])
            if board == self.link_front.get(lid):
                pts[('link', lid, 'front')] = centre(geo['front_connector'])
        return pts, pins, ok

    def boards(self, net, scenes):
        out = {k[0] for k in self.net_fps.get(net, ())}
        for sc in scenes:
            for lid in self.link_of_net.get(net, ()):
                if lid in sc.links:
                    out.add('K')
                    out.add(self.link_front[lid])
        return sorted(out)

    def figures(self, scene, net, board, cache=True):
        cache = cache and scene.name in ('paper', 'base')
        ck = (id(scene), net, board)
        if cache and ck in self._fig and self._fig[ck][0] is scene:
            return self._fig[ck][1]
        pts, pins, ok = self.points(scene, net, board)
        coords = list(pts.values())
        pairs = {}
        for q in pins:
            for x, xy in pts.items():
                if x != q:
                    pairs[(q, x)] = math.dist(pts[q], xy)
        f = {'extent': hpwl(coords), 'tree': rmst(coords), 'pairs': pairs, 'n': len(pts), 'computable': ok}
        if cache:
            self._fig[ck] = (scene, f)
        return f

    # ------------------------------------------------------------ NG
    def evaluate(self, paper, base, scene, max_limit=False):
        """NG1 to NG7 on `scene` (Ruling N2) with the limits of Ruling N3. Returns the full record."""
        keys = sorted(set(self.fps))
        moved = [k for k in keys if self.moved(base, scene, k)]
        mset = set(moved)
        changed_links = sorted(l for l in set(base.links) | set(scene.links) if base.links.get(l) != scene.links.get(l))
        evaluated = {}
        for n in sorted(self.protected_nets):
            movers = sorted(k for k in self.net_fps[n] if k in mset)
            lk = sorted(l for l in self.link_of_net.get(n, ()) if l in changed_links)
            if not movers and not lk:
                continue
            pm = any(self.fps[k]['protected'] for k in movers)
            evaluated[n] = {'class': 'P-moved' if pm else 'Other', 'movers': ['%s %s' % k for k in movers],
                            'links_changed': lk}
        fails = {t: [] for t in TESTS}
        strict_only = True   # every NG1-NG3 failure disappears with max(paper, base)
        for n, rec in evaluated.items():
            pm = rec['class'] == 'P-moved'
            rec['boards'] = {}
            inherited = False
            for b in self.boards(n, (paper, base, scene)):
                fp_, fb, fs = (self.figures(x, n, b) for x in (paper, base, scene))
                r = {'points': fs['n'], 'paper': _brief(fp_), 'base': _brief(fb), 'scene': _brief(fs), 'fails': []}
                if pm and (fb['extent'] > fp_['extent'] + EPS or fb['tree'] > fp_['tree'] + EPS or
                           any(v > fp_['pairs'].get(k, float('inf')) + EPS for k, v in fb['pairs'].items())):
                    inherited = True
                for lim_mode in (('max',) if max_limit else ('min', 'max')):
                    bad = self._board_tests(pm, fp_, fb, fs, lim_mode)
                    if lim_mode == 'min' or max_limit:
                        r['fails'] = bad
                    else:
                        r['fails_with_max_limit'] = bad
                        if bad:
                            strict_only = False
                for t in r['fails']:
                    fails[t].append('%s on %s' % (n, b))
                rec['boards'][b] = r
            rec['inherited_excess'] = inherited
            rec['fails'] = sorted({t for r in rec['boards'].values() for t in r['fails']})
        ev_moved = [k for k in moved if self.nets_of.get(k, set()) & set(evaluated)]
        for k in ev_moved:
            a, b = self.eff(base, k), self.eff(scene, k)
            if a[0] is not None and b[0] is not None and a[1] != b[1]:
                fails['NG4'].append('%s %s: face %s -> %s' % (k[0], k[1], a[1], b[1]))
        for k in moved:
            if not self.fps[k]['protected']:
                continue
            cy = scene.courtyards.get(k)
            if self.eff(scene, k)[0] is None:
                continue
            if cy is None:
                fails['NG5'].append('%s %s: no scene courtyard' % k)
                continue
            face = self.eff(scene, k)[1]
            g = grow(cy, self.gap)
            bcy = base.courtyards.get(k)
            bface = self.eff(base, k)[1]
            for lid, rects in sorted(scene.rects.items()):
                for rb, rf, rect, what in rects:
                    if rb != k[0] or rf != face or not inter(g, rect):
                        continue
                    exempt = False
                    if bcy is not None:
                        gb = grow(bcy, self.gap)
                        exempt = any(b2 == k[0] and f2 == bface and w2 == what and inter(gb, r2)
                                     for b2, f2, r2, w2 in base.rects.get(lid, []))
                    if not exempt:
                        fails['NG5'].append('%s %s under %s %s' % (k[0], k[1], lid, what))
        for k in keys:
            a, b = self.eff(base, k), self.eff(scene, k)
            if a[0] is not None and b[0] is None:
                fails['NG6'].append('%s %s: loses its base position' % k)
            elif b[0] is None and self.nets_of.get(k, set()) & set(evaluated):
                fails['NG6'].append('%s %s: positionless on an evaluated net' % k)
        for k in moved:
            if self.fps[k]['pads'] and not self.fps[k]['pin_record']:
                fails['NG7'].append('%s %s: moved, no pin record' % k)
        vec = []
        for t in TESTS:
            if t in ('NG1', 'NG2', 'NG3') and not evaluated:
                vec.append('–')
            else:
                vec.append('F' if fails[t] else 'P')
        failing = sorted(n for n, r in evaluated.items() if r['fails'])
        rest_ok = all(v == 'P' for v in vec[3:])
        nets_fail = bool(failing)
        tallies = {
            'stricter_limit_alone': nets_fail and rest_ok and strict_only and not max_limit,
            'inherited_excess_alone': nets_fail and rest_ok and all(evaluated[n]['inherited_excess'] for n in failing),
            'link_end_alone': nets_fail and rest_ok and all(not evaluated[n]['movers'] for n in failing),
            'large_net_alone': nets_fail and rest_ok and all(
                max(r['points'] for r in evaluated[n]['boards'].values()) > LARGE for n in failing),
        }
        first = next((t for t, v in zip(TESTS, vec) if v == 'F'), None)
        return {'vector': vec, 'pass': 'F' not in vec, 'first_failure': first, 'moved': ['%s %s' % k for k in moved],
                'links_changed': changed_links, 'evaluated': evaluated, 'failing_nets': failing,
                'fails': {t: v for t, v in fails.items() if v}, 'tallies': tallies}

    @staticmethod
    def _board_tests(pm, fp_, fb, fs, mode):
        pick = (min if mode == 'min' else max)
        bad = []
        if not (fs['computable'] and fb['computable'] and (fp_['computable'] or not pm)):
            return ['NG1', 'NG2', 'NG3']
        for t, f in (('NG1', 'extent'), ('NG2', 'tree')):
            lim = pick(fp_[f], fb[f]) if pm else fb[f]
            if fs[f] > lim + EPS:
                bad.append(t)
        for k, v in fs['pairs'].items():
            if pm:
                have = [x['pairs'][k] for x in (fp_, fb) if k in x['pairs']]
                if mode == 'min' and len(have) < 2:
                    bad.append('NG3')
                    break
                if not have:
                    bad.append('NG3')
                    break
                lim = pick(have)
            else:
                if k not in fb['pairs']:
                    bad.append('NG3')
                    break
                lim = fb['pairs'][k]
            if v > lim + EPS:
                bad.append('NG3')
                break
        return bad


def _brief(f):
    return {'extent': f['extent'], 'tree': f['tree'], 'pairs': len(f['pairs']),
            'max_pin_distance': max(f['pairs'].values()) if f['pairs'] else None, 'computable': f['computable']}


def grow(r, g):
    return [r[0] - g, r[1] - g, r[2] + g, r[3] + g]


def inter(a, b):
    """stackgeom.inter: open-interval overlap of two [x0, y0, x1, y1] rectangles."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def brute_rmst(pts):
    """C6: the rectilinear spanning tree by brute force over every spanning tree (Prüfer sequences), 2 to 7 points."""
    import itertools
    n = len(pts)
    if n < 2:
        return 0.0
    if n == 2:
        return abs(pts[0][0] - pts[1][0]) + abs(pts[0][1] - pts[1][1])
    best = float('inf')
    for seq in itertools.product(range(n), repeat=n - 2):
        degree = [1] * n
        for x in seq:
            degree[x] += 1
        total = 0.0
        s = list(seq)
        for x in s:
            leaf = min(i for i in range(n) if degree[i] == 1)
            total += abs(pts[leaf][0] - pts[x][0]) + abs(pts[leaf][1] - pts[x][1])
            degree[leaf] -= 1
            degree[x] -= 1
        u, v = [i for i in range(n) if degree[i] == 1]
        total += abs(pts[u][0] - pts[v][0]) + abs(pts[u][1] - pts[v][1])
        best = min(best, total)
    return best


def canon(obj):
    import json
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def scene_digest(slots, rows):
    """The digest of a written scene file (S12 convention: SHA-256 of the canonical slots and rows)."""
    import hashlib
    return hashlib.sha256(canon({'slots': slots, 'rows': rows}).encode()).hexdigest()


# C7 hand values for P-K-P-L03.01 at the base, from its record geometry, written before the run
C7_K = (214.6667, 182.8833)
C7_FRONT = (214.6667, 207.7833)


# ================================================================ the S12 machinery (imported unchanged)

import copy  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
S12DIR = HERE.parent / 'mc04_s12_five_ic_joint'
if str(S12DIR) not in sys.path:
    sys.path.insert(0, str(S12DIR))
import s12  # noqa: E402
import joint_search as js  # noqa: E402
from s12 import lg, p2, sg, sm, ov, rp, mfc, sa2  # noqa: E402,F401

ROOT = s12.ROOT
SEARCHED15 = ('P-K-P-L12.02.01.02', 'P-K-P-L03.01', 'P-K-P-L13.01.01.01', 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01',
              'P-K-P-L15.02.01.01')
ICS4 = ('U5110', 'U8409', 'U5209', 'U5210')
NEEDS = {'U5110': 'P-K-P-L12.02.01.02', 'U8409': 'P-K-P-L03.01', 'U5209': 'P-K-P-L13.01.01.02',
         'U5210': 'P-K-P-L13.01.01.01'}
CLUSTERS15 = (('South', ('P-K-P-L12.02.01.02',), ('U5110',)),
              ('East', ('P-K-P-L03.01', 'P-K-P-L15.02.01.01', 'P-K-P-L13.01.01.01', 'P-K-P-L13.01.02.01',
                        'P-K-P-L13.01.01.02'), ('U8409', 'U5210', 'U5209')))
STATUS = 'CANDIDATE SCENE, GEOMETRIC ONLY, NOT ADOPTED'


def link_signal_nets(rec):
    """The link's signal list: the nets of its allocated signal positions."""
    return {p['net'] for p in rec.get('positions', []) if p.get('kind') == 'signal' and p.get('net')}


def rowmap(rows):
    return {(r['board'], r['ref']): r for r in rows}


class G15:
    """The S12 World seen through Ruling N1: pads, pins, link ends, and the paper and base scenes."""

    def __init__(self, w):
        self.w = w
        s = w.s
        fps = {}
        for k, fp in s.fps.items():
            pins = s.pins.get(k[1])
            fps[k] = {'origin': tuple(fp['origin']), 'side': fp['side'],
                      'pads': [(i, p['number'], tuple(p['center'])) for i, p in enumerate(fp['pads'])],
                      'pins': dict(pins or {}), 'pin_record': pins is not None, 'protected': k in w.protected}
        self.link_nets = {r['id']: link_signal_nets(r) for r in w.base_out}
        self.link_front = {r['id']: r['front_board'] for r in w.base_out}
        self.model = Model(fps, self.link_nets, self.link_front, open_ics={('K', ic) for ic in s12.FIVE}, gap=w.gap)
        live = p2.live(w.base_out)
        self.base_links = {r['id']: r['geometry'] for r in live if r['placed']}
        self.paper = Scene({k: (tuple(fp['origin']), fp['side']) for k, fp in s.fps.items()}, {}, dict(self.base_links),
                           name='paper')
        before, bt = s12.base_effective(w)
        self.base = self._scene(before, bt, live, w.base_rows, w.retained, 'base')

    def _scene(self, eff, turns, live, rb, placements, name):
        poses = {k: (tuple(v[0]) if v[0] is not None else None, v[1] if v[0] is not None else None)
                 for k, v in eff.items()}
        links = {r['id']: r['geometry'] for r in live if r['placed']}
        rects = {r['id']: sm.link_rects(r['geometry'], r['front_board'], self.w.latch_field) for r in live if r['placed']}
        return Scene(poses, dict(turns), links, rects, LazyCourtyards(self.w, eff, rb, placements), name)

    def scene_from_rows(self, rows, scene_out, blocks=()):
        """The effective scene of a rows-only replay (paper, then gate rows, then retained block poses whose IC row
        is positionless, then `blocks`), as s12.judge / overlay_part build it."""
        s = self.w.s
        rb = rows if isinstance(rows, dict) else rowmap(rows)
        old_rows, old_out = s.rows, s.out
        s.rows, s.out = rb, scene_out
        try:
            cur = [e for e in self.w.retained if (e['board'], e['ic']) in rb and rb[e['board'], e['ic']]['new'] is None]
            pl = cur + list(blocks)
            eff = ov.effective_scene(s, rb, pl)
            turns = ov.effective_turns(rb, pl)
        finally:
            s.rows, s.out = old_rows, old_out
        return self._scene(eff, turns, p2.live(scene_out), rb, pl, 'scene')

    def evaluate(self, scene, max_limit=False):
        return self.model.evaluate(self.paper, self.base, scene, max_limit=max_limit)


class LazyCourtyards:
    """The courtyard of a footprint at its effective pose (gate row: its new courtyard; paper: the board record;
    block member: member_faces.block_rects; displaced passive: member_faces.part_rect)."""

    def __init__(self, w, eff, rb, placements):
        self.w, self.eff, self.rb, self.pl = w, eff, rb, placements
        self.cache = {}

    def get(self, key, default=None):
        if key not in self.cache:
            self.cache[key] = self._one(key)
        return self.cache[key] if self.cache[key] is not None else default

    def _one(self, key):
        s = self.w.s
        pos, face, src = self.eff[key]
        if pos is None:
            return None
        fp = s.fps[key]
        if src == 'paper':
            return list(fp['courtyard'] or p2.fp_bbox(fp))
        if src == 'gate row':
            return list(self.rb[key]['new_courtyard'])
        b, ref = key
        for e in self.pl:
            if e['board'] != b:
                continue
            for m in e.get('passives_moved', []):
                if m['ref'] == ref and src.endswith('displaced passive'):
                    return mfc.part_rect(s, b, m)
            blocks = [(e['ic'], e.get('members') or e['block'], e['pose'])] + \
                [(x['ic'], x['members'], x) for x in e.get('blocks_moved', [])]
            for ic, members, pose in blocks:
                if pose and ref in members and src == '%s block' % ic:
                    for r, _, rect in mfc.block_rects(s, b, ic, members, s.fps[(b, ic)]['side'], pose):
                        if r == ref:
                            return rect
        raise LookupError('STOP 4: no scene courtyard for %s %s (%s)' % (key[0], key[1], src))


# ================================================================ derived S12 functions (switch `rules`: 's12' or 'ng')

def check_rules_ng(w, lid, geo, dist, size, rules):
    """World.check_rules with rules='s12'; with rules='ng' rules 2 to 4 only (T1 and T2 are replaced by NG)."""
    if rules == 's12':
        return w.check_rules(lid, geo, dist, size)
    why = w.rule2(lid, geo, size)
    if why:
        return 2, why, None
    if dist > s12.RADIUS + 1e-9:
        return 3, 'slot centre %.4f mm from the search centre, beyond %.1f mm' % (dist, s12.RADIUS), None
    why = w.rule4(lid, geo, size)
    if why:
        return 4, why, None
    bad, anch = w.t1(lid, geo, size)
    return None, None, (anch, bad)


def census_ng(w, lid, grid, size=None, memo_every=4000, deadline=None, rules='ng'):
    """Every candidate of one link on one grid within 35 mm (rule 1 as links_gate.search evaluates it, every other
    searched link out of `placed`), then rules 2 to 6 in order. Returns (counts, accepted candidates)."""
    ctx = w.ctx
    rec = w.rec(lid, size)
    front, centre, own = rec['front_board'], rec['centre'], lg.rec_own(rec)
    z = w.size_of(rec)
    placed = w.placed_index({}, skip=s12.SEARCHED)
    spare = ctx.spare(front, z)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    offsets = ctx.grid(grid, radius=s12.RADIUS)
    counts = {'offsets': len(offsets), 'evaluated': 0,
              'legal_rule1': {'≤ 24 mm': 0, '24–35 mm': 0},
              'after_rule': {str(n): {'≤ 24 mm': 0, '24–35 mm': 0} for n in (2, 3, 4, 5, 6)},
              'rejections_rule1': {}, 'rejections_by_rule': {str(n): {} for n in (2, 3, 4, 5, 6)},
              't1_by_class': {'N': 0, 'S': 0}, 't1_by_footprint': {}, 'rejected_for_class_S_alone': 0,
              'complete': True}
    acc = []
    ctx.model.memo_for(None)
    for i, off in enumerate(offsets):
        if deadline is not None and time.time() > deadline:
            counts['complete'] = False
            break
        if i % memo_every == 0:
            ctx.model.memo_for(None)
        dist = math.hypot(*off)
        ring = s12.ring_of(dist)
        sx, sy = lg.r4(centre[0] + off[0]), lg.r4(centre[1] + off[1])
        for di, d in enumerate(lg.DIRS):
            counts['evaluated'] += 1
            why, c = lg.candidate(ctx, placed, front, z, own, sx, sy, d, dist, spare, True, gm)
            if why:
                k = why[0]
                counts['rejections_rule1'][k] = counts['rejections_rule1'].get(k, 0) + 1
                continue
            counts['legal_rule1'][ring] += 1
            cost, geo, disp = c
            rule, reason, extra = check_rules_ng(w, lid, geo, dist, size, rules)
            unanchored = None
            if rules == 'ng' and rule is None:
                extra, unanchored = extra
            if rule is not None:
                t = counts['rejections_by_rule'][str(rule)]
                key = reason if rule in (2, 3, 4) else 'T1' if rule == 5 else 'T2'
                t[key] = t.get(key, 0) + 1
                if rule == 5:
                    classes = {c2 for _, c2 in extra}
                    for cl in classes:
                        counts['t1_by_class'][cl] += 1
                    if classes == {'S'}:
                        counts['rejected_for_class_S_alone'] += 1
                    for ref, cl in extra:
                        e = counts['t1_by_footprint'].setdefault(ref, {'class': cl, 'candidates': 0})
                        e['candidates'] += 1
                if rule == 6:
                    for b, ref, what in extra:
                        k2 = 'T2 ' + ref
                        t[k2] = t.get(k2, 0) + 1
            for n in (2, 3, 4, 5, 6):
                if rule is None or rule > n:
                    counts['after_rule'][str(n)][ring] += 1
            if rule is None:
                key = (round(cost, 6), round(dist, 6), di, geo['front_extension_mm'], geo['K_extension_mm'], sx, sy)
                acc.append({'cost': cost, 'key': list(key), 'geometry': geo, 'direction': lg.DIR_NAMES[d],
                            'slot_centre': [sx, sy], 'dist': dist, 'ring': ring, 'grid_mm': grid, 'size': rec['circuits'],
                            'spot': list(s12.spot_of(sx, sy, lg.DIR_NAMES[d])), 'anchored_covered': [list(x) for x in extra],
                            'tails': [list(x) for x in w.tails(lid, geo)]})
                if rules == 'ng':
                    acc[-1]['displaced'] = {k: sorted(v) for k, v in disp.items()}
                    acc[-1]['unanchored_protected'] = [list(x) for x in unanchored]
    ctx.model.memo_for(None)
    acc.sort(key=lambda c: c['key'])
    return counts, acc


def legal_entry_ng(w, lid, e, chosen, later, size, rules='ng'):
    """(moves entry or None, reason): the pool entry at its slot with fixed and earlier chosen links placed."""
    ctx = w.ctx
    rec = w.rec(lid, size)
    front, own = rec['front_board'], lg.rec_own(rec)
    placed = w.placed_index(chosen, skip=(lid,) + tuple(later))
    if e['stay']:
        why = ctx.evaluate(placed, front, rec['geometry'], own)
        if why:
            return None, 'stay illegal: %s' % why[0]
        return {'stay': True}, None
    z = w.size_of(rec)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == e['direction']][0]
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, front, z, own, e['slot_centre'][0], e['slot_centre'][1], d, e['dist'],
                          ctx.spare(front, z), True, gm)
    if why:
        return None, why[0]
    cost, geo, disp = c
    rule, reason, _ = check_rules_ng(w, lid, geo, e['dist'], size, rules)
    if rule is not None:
        return None, 'rule %d: %s' % (rule, reason)
    return {'geometry': geo, 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'size': size, 'cost': cost,
            'dist': e['dist'], 'ring': e['ring'], 'grid_mm': e.get('grid_mm')}, None


def check_rows_ng(w, rows, claim_ok=True, rules='ng', g=None, scene_out=None):
    """A1 to A4 and A6 on one scene's rows. Returns ({item: [failures]}, info). With rules='ng' A2 is replaced by NG
    on the effective scene of `rows` and `scene_out` (info['NG'] holds the record)."""
    ra, rb = w.base_rows, rowmap(rows)
    removed, new, shifted = s12.row_changes(ra, rb)
    fails = defaultdict(list)
    s = w.s
    claimed = [ic for ic in s12.FIVE if ('K', ic) not in rb]
    for ic in s12.FIVE:
        k = ('K', ic)
        if k in rb and rb[k] != ra.get(k):
            fails['A1'].append('%s is not claimed and its row differs from the base row' % ic)
    prot = {'new': [], 'shifted': [], 'returned': [], 'lost_position': []}
    for k in sorted(w.protected):
        a, b = ra.get(k), rb.get(k)
        if b is None:
            if a is not None:
                prot['returned'].append(k)
            continue
        if a is None:
            prot['new'].append(k)
            if rules == 's12':
                fails['A2'].append('%s %s: new protected row (%s)' % (k[0], k[1], 'no position' if b['new'] is None else b['step']))
        elif s12.rowsig(a) != s12.rowsig(b):
            if b['new'] is None:
                prot['lost_position'].append(k)
                if rules == 's12':
                    fails['A2'].append('%s %s: protected footprint loses its base position' % k)
            else:
                prot['shifted'].append(k)
                if rules == 's12':
                    fails['A2'].append('%s %s: shifted or turned protected row' % k)
    for k, b in rb.items():
        a = ra.get(k)
        if b['new'] is None and (a is None or a['new'] is not None):
            fails['A3'].append('%s %s: %s without a position' % (k[0], k[1], 'new row' if a is None else 'row'))
    for k in new + shifted:
        ref = k[1]
        if not ref.startswith('RV'):
            continue
        b = rb[k]
        paper_face = s.fps[k]['side']
        before_face = ra[k]['new_face'] if k in ra and ra[k]['new'] is not None else paper_face
        if b['new_face'] is not None and b['new_face'] != paper_face:
            fails['A4'].append('%s %s: trimmer row changes face from paper %s to %s' % (k[0], ref, paper_face, b['new_face']))
        if k[0] == 'K' and b['new_face'] == 'F' and before_face != 'F':
            fails['A4'].append('%s %s: trimmer newly lands on K front face' % k)
    for board in s12.UNTOUCHED:
        a = sorted((s12.canon(r) for kk, r in ra.items() if kk[0] == board))
        b = sorted((s12.canon(r) for kk, r in rb.items() if kk[0] == board))
        if a != b:
            fails['A6'].append('rows on %s differ from the base' % board)
    info = {'claimed': claimed, 'counts': {'removed': len(removed), 'new': len(new), 'shifted': len(shifted)},
            'protected': {k: ['%s %s' % x for x in v] for k, v in prot.items()},
            'removed': removed, 'new': new, 'shifted': shifted}
    if rules == 'ng':
        res = g.evaluate(g.scene_from_rows(rb, scene_out))
        info['NG'] = res
        if not res['pass']:
            fails['NG'] = ['%s: %s' % (t, '; '.join(v[:4])) for t, v in sorted(res['fails'].items())]
    return dict(fails), info


def cluster_search_ng(w, links, targets, pools, budget, size07=None, rules='ng', g=None):
    """Best-first enumeration over the pools in the fixed link order. Returns (clean scenes, log)."""
    need = s12.must_move(w, targets) & set(links)
    pl = []
    for lid in links:
        tag = '%s@%d' % (lid, size07) if (lid == 'P-K-P-L07' and size07) else lid
        es = [e for e in pools[tag] if not (e['stay'] and lid in need)]
        if size07 and lid == 'P-K-P-L07':
            pass
        if rules == 's12':
            es = sorted(es, key=lambda e: (not (e['screen'] or {}).get('clean', False), e['cost'], e['key']))
        else:
            es = sorted(es, key=lambda e: e['pool_order'])
        pl.append((lid, es, size07 if lid == 'P-K-P-L07' else None))
    logd = {'targets': list(targets), 'must_move': sorted(need), 'pool_sizes': {lid: len(es) for lid, es, _ in pl},
            'replays': 0, 'legality_calls': 0, 'complete_scenes': 0, 'rejected_scenes': [], 'bound': None, 'illegal': {}}
    empty = [lid for lid, es, _ in pl if not es]
    if empty:
        logd['bound'] = 'none: no pool entry for %s (census zero after rules 1 to 6)' % ', '.join(empty) if rules == 's12' \
            else 'none: no pool entry for %s' % ', '.join(empty)
        logd['exhausted'] = True
        return [], logd
    hmin = []
    for lid, es, _ in pl:
        hmin.append((min(int(not (e['screen'] or {}).get('clean', False)) for e in es), min(e['cost'] for e in es)))
    rest = [(sum(h[0] for h in hmin[i:]), sum(h[1] for h in hmin[i:])) for i in range(len(pl) + 1)]
    heap = [(rest[0][0], rest[0][1], 0, ())]
    seq = js.itertools.count()
    clean = []
    while heap:
        if budget.out():
            logd['bound'] = budget.reason
            break
        un, cost, _, choice = js.heapq.heappop(heap)
        depth = len(choice)
        chosen = {}
        for (lid, es, sz), (i, m) in zip(pl, choice):
            chosen[lid] = m
        if depth == len(pl):
            logd['complete_scenes'] += 1
            moves = {l: m for l, m in chosen.items()}
            bad = js.reverify(w, moves)
            if bad:
                logd['rejected_scenes'].append({'choice': [i for i, _ in choice], 'reverify': bad})
                continue
            budget.replays += 1
            logd['replays'] += 1
            scene_out = w.scene_links(moves)
            rows = w.rows_only(scene_out)
            fails, info = check_rows_ng(w, rows, rules=rules, g=g, scene_out=scene_out)
            for lid, m in moves.items():
                _, bad5 = s12.link_figures(w, lid, m)
                if bad5:
                    fails.setdefault('A5', []).extend(bad5)
            miss = [ic for ic in targets if ic not in info['claimed']]
            if fails or miss:
                rej = {'choice': [i for i, _ in choice], 'fails': {k: v[:6] for k, v in fails.items()},
                       'targets_not_claimed': miss}
                if rules == 'ng':
                    rej['ng'] = ng_summary(info['NG'])
                logd['rejected_scenes'].append(rej)
                continue
            allt, newt = js.tails_of(w, moves)
            clean.append({'moves': moves, 'rows_digest': s12.digest(rows), 'claimed': info['claimed'], 'row_info': info,
                          'tails_all': allt, 'tails_new': newt, 'rank': js.scene_rank(w, moves, info, newt)})
            if len(clean) >= js.CLEAN_CAP:
                logd['bound'] = 'three clean scenes'
                break
            continue
        lid, es, sz = pl[depth]
        later = [x[0] for x in pl[depth + 1:]]
        for i, e in enumerate(es):
            if budget.out():
                break
            budget.legal += 1
            logd['legality_calls'] += 1
            m, why = legal_entry_ng(w, lid, e, chosen, later, sz, rules=rules)
            if m is None:
                k = '%s: %s' % (lid, why)
                logd['illegal'][k] = logd['illegal'].get(k, 0) + 1
                continue
            if not m.get('stay'):
                m['screen_clean'] = bool((e['screen'] or {}).get('clean'))
            un2 = sum(0 if (mm.get('stay') or mm.get('screen_clean')) else 1 for mm in list(chosen.values()) + [m]) + rest[depth + 1][0]
            c2 = sum((w.byid[l]['cost'] if mm.get('stay') else mm['cost']) for l, mm in list(chosen.items()) + [(lid, m)]) + rest[depth + 1][1]
            js.heapq.heappush(heap, (un2, round(c2, 6), next(seq), choice + ((i, m),)))
    else:
        logd['exhausted'] = True
    logd.setdefault('exhausted', False)
    logd['rejected_scenes'] = logd['rejected_scenes'][:40]
    return sorted(clean, key=lambda c: c['rank']), logd


def judge_ng(w, moves, rows, overlay_blocks=None, run_overlay_search=True, rules='ng', g=None):
    """A1 to A11 on one scene (rows from the rows-only replay). `overlay_blocks`: fixed overlay placements (P6) instead
    of the A8 search. Returns a dict with per-item failures and the ledgers. With rules='ng', A2 and the protected
    clause of A10 are replaced by NG on the effective scene after the overlay."""
    s = w.s
    fails, info = check_rows_ng(w, rows, rules='s12' if rules == 's12' else 'ng-rows')
    fails = defaultdict(list, fails)
    figs = {}
    for lid, m in sorted(moves.items()):
        f, bad = s12.link_figures(w, lid, m)
        figs[lid] = f
        fails['A5'] += bad
    ra, rb = w.base_rows, rowmap(rows)
    scene_out = w.scene_links(moves)
    old_rows, old_out = s.rows, s.out
    s.rows, s.out = rb, scene_out
    try:
        res = overlay_part_ng(w, ra, rb, info, fails, overlay_blocks, run_overlay_search, rules=rules, g=g,
                              scene_out=scene_out)
    finally:
        s.rows, s.out = old_rows, old_out
    res.update({'fails': {k: v for k, v in sorted(fails.items()) if v}, 'rows': info, 'link_figures': figs})
    items = ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11') if rules == 's12' else \
        ('A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A11', 'NG')
    res['passes'] = {a: not fails.get(a) for a in items}
    return res


def overlay_part_ng(w, ra, rb, info, fails, overlay_blocks, run_search, rules='ng', g=None, scene_out=None):
    """A7 to A11 with s.rows / s.out set to the scene (the DS-148 overlay rules of overlay.py)."""
    s = w.s
    before, before_turns = s12.base_effective(w)
    new, shifted = info['new'], info['shifted']
    dec_of = defaultdict(list)
    for ref, p in s.pk.items():
        if p.get('decouples_ref'):
            dec_of[p['decouples_ref']].append(ref)
    current_retained = [e for e in w.retained if (e['board'], e['ic']) in rb and rb[e['board'], e['ic']]['new'] is None]
    mid = ov.effective_scene(s, rb, current_retained)
    touched = sorted({k for k in new + shifted if k[1].startswith('U')} |
                     {(k[0], s.pk[k[1]]['decouples_ref']) for k in new + shifted if s.pk.get(k[1], {}).get('decouples_ref')})
    rule, need = [], []
    for key in touched:
        if key not in s.fps:
            continue
        b, ic = key
        io0, if0, _ = before[key]
        io1, if1, _ = mid[key]
        decs = []
        for d in sorted(dec_of.get(ic, [])):
            dk = (b, d)
            if dk not in s.fps:
                continue
            o0, f0, _ = before[dk]
            o1, f1, _ = mid[dk]
            if None in (o0, o1, io0, io1):
                decs.append({'ref': d, 'unavailable': 'no position'})
                continue
            d0, d1 = math.dist(o0, io0), math.dist(o1, io1)
            decs.append({'ref': d, 'face_before': f0, 'face_after': f1, 'distance_before_mm': d0, 'distance_after_mm': d1,
                         'other_face_after': f1 != if1, 'farther': d1 > d0 + 1e-9})
        breaks = [d for d in decs if d.get('unavailable') or d['other_face_after'] or d['farther']]
        own = key in set(new) | set(shifted)
        kind = 'holds' if not breaks else ('overlay pose (searched)' if own and rb[key]['new'] is not None else 'knock-on break')
        rule.append({'board': b, 'ic': ic, 'ic_row': 'new' if key in new else 'shifted' if key in shifted else 'unchanged',
                     'decouplers': decs, 'block_rule': kind})
        if kind == 'knock-on break':
            fails['A8'].append('%s %s: a decoupler row breaks the block rule while the IC row is unchanged '
                               '(stricter reading: no knock-on exemption)' % key)
        elif kind.startswith('overlay'):
            need.append(key)
    blocks = []
    if overlay_blocks is not None:
        blocks = copy.deepcopy(overlay_blocks)
    elif need and run_search:
        members = {}
        for key in need:
            dec, local, _ = s.block(*key)
            members[key] = [key[1]] + dec + local
        lifted = {(b, m) for (b, ic), ms in members.items() for m in ms}
        for key in need:
            b, ic = key
            f = s.build_field(extra=lifted)
            for e in blocks:
                s.place(f, e['board'], e['ic'], e['members'], s.fps[(e['board'], e['ic'])]['side'], e['pose'])
                for m in e['passives_moved']:
                    s.add_part(f, e['board'], m)
            s.members[key] = members[key]
            try:
                legal, disp, _ = s.search(f, b, ic)
            finally:
                if key not in {(i['board'], i['ref']) for i in s.items}:
                    s.members.pop(key, None)
            best = legal[0] if legal else None
            e = {'board': b, 'ic': ic, 'members': members[key]}
            if best and best['moved_mm'] <= rp.LIMIT_MM:
                e.update({'pose': {k: best[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')}, 'passives_moved': []})
            elif disp:
                e.update({'pose': {k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')},
                          'passives_moved': disp['displaced_moves']})
            else:
                fails['A8'].append('%s %s: no S8 block pose within 24 mm (nearest %s mm)' % (b, ic, best and best['moved_mm']))
                e.update({'pose': None, 'passives_moved': []})
            blocks.append(e)
    elif need:
        fails['A8'].append('overlay search not run for %s' % need)
    stop = []
    if blocks:
        ov.candidate_clearance(s, blocks, stop)
        for x in stop:
            fails['A8'].append(x)
    after = ov.effective_scene(s, rb, current_retained + blocks)
    rotations = ov.effective_turns(rb, current_retained + blocks)
    ledger = ov.movement(s, before, after, before_turns, rotations)
    # A10: protected footprints in the effective scene
    overlay_refs = {(e['board'], m) for e in blocks for m in e['members']} | \
        {(e['board'], m['ref']) for e in blocks for m in e['passives_moved']}
    prot_ledger = {'returned_to_paper': [], 'overlay_moved': [], 'differs': []}
    for k in sorted(w.protected):
        a, b = before[k], after[k]
        ta, tb = before_turns.get(k, 0), rotations.get(k, 0)
        same = (a[0] == b[0] or (a[0] is not None and b[0] is not None and math.dist(a[0], b[0]) < 1e-9)) and a[1] == b[1] and ta == tb
        if same:
            continue
        paper = s.fps[k]
        if b[2] == 'paper' and b[1] == paper['side'] and tb == 0:
            prot_ledger['returned_to_paper'].append('%s %s' % k)
            continue
        tag = 'overlay_moved' if k in overlay_refs else 'differs'
        prot_ledger[tag].append('%s %s' % k)
        if rules == 's12':
            fails['A10'].append('%s %s: effective pose differs from its base effective pose (%s)' % (k[0], k[1], tag))
    ng_rec = None
    if rules != 's12':
        sc = g._scene(after, rotations, p2.live(scene_out), rb, current_retained + blocks, 'scene')
        ng_rec = g.evaluate(sc)
        if not ng_rec['pass']:
            fails['NG'] = ['%s: %s' % (t, '; '.join(v[:4])) for t, v in sorted(ng_rec['fails'].items())]
    # A7: the ten link-era poses in the Field built from the scene rows
    a7 = []
    for board, ic, members, face0, pose in s.confirmed_blocks():
        a7.append(s12.check_block(s, board, ic, members, face0, pose, []))
    for board, ic, members, face0, pose, passives, _ in s.done:
        a7.append(s12.check_block(s, board, ic, members, face0, pose, passives))
    for x in a7:
        if not x['all_clear']:
            fails['A7'].append('link-era pose of %s %s is not legal in the scene Field' % (x['board'], x['ic']))
    # A9: placed ICs' blocks
    a9 = []
    for ic in info['claimed']:
        key = ('K', ic)
        ms = s.members.get(key) or ([ic] + s.block('K', ic)[0] + s.block('K', ic)[1])
        io = s.fps[key]['origin']
        for m in ms[1:]:
            mk = ('K', m)
            pos, face, src = after[mk]
            if src == 'paper':
                continue
            isdec = s.pk.get(m, {}).get('decouples_ref') == ic
            ok = isdec and pos is not None and face == s.fps[key]['side'] and \
                math.dist(pos, io) <= math.dist(s.fps[mk]['origin'], io) + 1e-9
            a9.append({'ic': ic, 'ref': m, 'source': src, 'ok': ok})
            if not ok:
                fails['A9'].append('%s block member %s is not at paper (%s)' % (ic, m, src))
    for k in sorted(set(new) | set(shifted)):
        kind = sa2.buffer_kind(s, k)
        if kind and kind[0] == 'r_iso':
            amps = sorted(r for r in s.net_refs[kind[1]] if r.startswith('U') and (k[0], r) in s.fps)
            ak = (k[0], amps[0])
            if None in (after[k][0], after[ak][0], before[k][0], before[ak][0]):
                fails['A9'].append('R_ISO %s: no position' % k[1])
                continue
            d0, d1 = math.dist(before[k][0], before[ak][0]), math.dist(after[k][0], after[ak][0])
            a9.append({'r_iso': k[1], 'op_amp': amps[0], 'before_mm': d0, 'after_mm': d1, 'ok': d1 <= d0 + 1e-9})
            if d1 > d0 + 1e-9:
                fails['A9'].append('R_ISO %s farther from %s than at the base' % (k[1], amps[0]))
    loc = s12.locality_table(w, after, rotations)
    for x in loc['figures']:
        if x['verdict'] == 'ABOVE LIMIT':
            fails['A11'].append('%s %s: %s above its limit %s' % (x['entry'], x['figure'], x['scene'], x['limit']))
    out = {'block_rule': rule, 'overlay_blocks': blocks, 'effective_movements': ledger,
           'face_changes': [r for r in ledger if r['from'] and r['to'] and r['from'] != r['to']],
           'protected_effective': prot_ledger, 'link_era_poses': a7, 'placed_ic_blocks': a9, 'locality': loc}
    if ng_rec is not None:
        out['NG'] = ng_rec
    return out


def ng_summary(r):
    """A compact NG record: vector, moved footprints, evaluated nets with class and per-board figures, failures."""
    return {'vector': ''.join(r['vector']), 'pass': r['pass'], 'first_failure': r['first_failure'], 'moved': r['moved'],
            'links_changed': r['links_changed'], 'failing_nets': r['failing_nets'], 'tallies': r['tallies'],
            'fails': {t: v[:12] for t, v in r['fails'].items()},
            'evaluated': {n: {'class': e['class'], 'movers': e['movers'], 'links_changed': e['links_changed'],
                              'inherited_excess': e['inherited_excess'], 'fails': e['fails'],
                              'boards': e['boards']} for n, e in r['evaluated'].items()}}


# ================================================================ run bounds: pins, clock, checkpoints

OUTDIR = Path(os.environ['S15_DEV_OUT']) if os.environ.get('S15_DEV_OUT') else HERE  # development dry runs only
CK = OUTDIR / 'checkpoints'
CAND = OUTDIR / 'candidates'
# Bulky intermediates live in an ignored cache, not in git (owner rule: no large intermediate dumps, no Git LFS);
# their SHA-256 and sizes are pinned in the tracked BULK_MANIFEST.
BULK = OUTDIR / 'cache' if os.environ.get('S15_DEV_OUT') else ROOT / '.circuit-cache' / 'mc04-s15'
BULK_MANIFEST = OUTDIR / 'bulk-manifest.json'
DURABLE = '/mnt/project-files/osc-s15-cache/'  # project file storage (network mount) holding a verified copy of the cache
SCREEN = BULK / 'screen.json'
STAGE1 = BULK / 'checkpoints' / 'stage1.json'
CENSUS_NG = BULK / 'checkpoints' / 'census_ng.json'
STAGE2_DIR = BULK / 'checkpoints' / 'stage2'
RESULT = OUTDIR / 'result.json'
PY = sys.executable
CAMPAIGN = 'circuit/orchestration/campaigns/osc-stack-20261114/'
BRIEF = CAMPAIGN + 'mc04-s15-no-growth-moves-brief-20261128.md'
BRIEF_SHA = '8283667186ae355ac0b18c94cdd21f30fbc0ea8fd02286633aef1e338ad2c378'
PINS15 = {
    CAMPAIGN + 'mc04-s12-five-ic-joint-search-brief-20261127.md': '1ecf7da618924bf1a21b825ad1ce682ffa057b66cc950b0285f110e9e2069a2a',
    CAMPAIGN + 'mc04-s12-report-20261127.md': 'd3b9a33026089d24aa4d8e4c591b1cb16545fb617e01800d3993e38a23470a19',
    CAMPAIGN + 'mc04-s12-disposition-20261127.md': '6c21cb39354f12f091472c1dd33c56ec53b4ea0bf1196489737f7bc1e8516f0b',
    CAMPAIGN + 'mc04-s14-disposition-20261128.md': '347e016cf86ecf82b7898416aa6fe4d670490a12533cdcbbe856f6afb1e40b3f',
    'scripts/stack/studies/mc04_s12_five_ic_joint/s12.py': 'b1e993583c541dc28c3574dfe7b789804937697466e2404b09d5a1a64c7aadcd',
    'scripts/stack/studies/mc04_s12_five_ic_joint/joint_search.py': '97697c009b3282807191dad7180ca77c0810fc81f33a165b3d505defe60b6d28',
    'scripts/stack/studies/mc04_s12_five_ic_joint/guard.py': '941c9130ba056e552564cf95b8990141f8e8ded0aba22cc20d695fe7fa88284a',
    'scripts/stack/studies/mc04_s12_five_ic_joint/census.json': '92f6fdede21948d10ed49236889f1853b77c1e803445a945a15a92e7dbda095e',
    'scripts/stack/studies/mc04_s12_five_ic_joint/result.json': '32532262d6a98dbdef8e73fee4951487f417c8361cc2f008ea801be099da02ed',
    BRIEF: BRIEF_SHA,
}
CLOCK_S = 5 * 3600
STEP_CEIL = {'arm0': 35 * 60, 'stage1': 15 * 60, 'stage2': 125 * 60, 'stage3': 55 * 60, 'stage4': 30 * 60}
STAGE2_CAP = 1000
POOL_CAP = 60
REPLAY_CAP3 = 400
LEGAL_CAP3 = 100000
CLEAN_CAP = 3
JOINT_CAP = 9
OVERLAY_CAP = 6
FULL_CAP = 8
WORKERS = 3
RESUME_CAP = 4
SETS3 = ((('U5110',), 'South', 6), (('U8409', 'U5210', 'U5209'), 'East', 14), (('U5209', 'U5210'), 'East', 8),
         (('U8409', 'U5210'), 'East', 5), (('U8409', 'U5209'), 'East', 5), (('U8409',), 'East', 4),
         (('U5210',), 'East', 4), (('U5209',), 'East', 4))
SET_MAX_S = 20 * 60


class Stop(Exception):
    pass


def now():
    return time.time()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, file=sys.stderr, flush=True)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=_jdefault) + '\n')
    os.replace(tmp, path)


def _jdefault(o):
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(type(o))


def read_json(path):
    return json.loads(Path(path).read_text())


def pins15():
    """(record, problems): the S15 input pins, plus the S12 input, tree and code pins."""
    rec, bad = {}, []
    for p, want in PINS15.items():
        got = s12.sha_file(ROOT / p)
        rec[p] = got
        if got != want:
            bad.append('pin %s: %s != %s' % (p, got, want))
    s12pins, s12bad = s12.input_pins()
    return {'s15': rec, 's12': s12pins}, bad + s12bad


class Clock:
    """The cumulative wall clock in checkpoints/run.json (never restarted on a resume)."""

    def __init__(self, path):
        self.path = path
        self.rec = read_json(path) if path.exists() else {'clock_s': 0.0, 'steps': {}, 'segments': [], 'resumes': [],
                                                          'executor_timed': {}}
        self.mark = now()
        self.step = None
        self.rec['segments'].append({'start': self.mark, 'pid': os.getpid()})

    def tick(self, step=None, save=True):
        t = now()
        dt = t - self.mark
        self.mark = t
        self.rec['clock_s'] += dt
        st = step or self.step
        if st:
            self.rec['steps'][st] = self.rec['steps'].get(st, 0.0) + dt
        self.rec['segments'][-1]['end'] = t
        if save:
            write_json(self.path, self.rec)
        total = self.rec['clock_s'] + sum(self.rec['executor_timed'].values())
        if total > CLOCK_S:
            raise Stop('STOP 6: the cumulative 5-hour clock is spent (%.0f s)' % total)
        if st in STEP_CEIL and self.rec['steps'][st] > STEP_CEIL[st]:
            raise Stop('STOP 6: the %s ceiling (%d min) is passed (%.0f s)' % (st, STEP_CEIL[st] // 60, self.rec['steps'][st]))

    def begin(self, step):
        self.tick(self.step)
        self.step = step


def ck(name):
    return CK / name


# ================================================================ arm 0: controls C1 to C18

def env_nobytecode():
    e = dict(os.environ)
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    return e


def c1(w, g):
    t = now()
    p = js.subprocess.run([PY, str(S12DIR / 'joint_search.py'), '--check'], capture_output=True, text=True,
                          cwd=str(ROOT), env=env_nobytecode())
    ok = p.returncode == 0 and 'input pins, P3, P4, P11, 0 scenes and 6 checkpoint digests verified' in p.stdout
    return ok, {'returncode': p.returncode, 'stdout': p.stdout.strip()[-400:], 'stderr_tail': p.stderr[-400:],
                'wall_s': round(now() - t, 1)}


def full_replay_child(holds_json, out_json):
    holds = None if holds_json == '-' else read_json(holds_json)
    t = now()
    doc, reads = s12.full_replay(holds)
    write_json(out_json, {'doc': doc, 'working_tree_reads': reads, 'wall_s': round(now() - t, 1)})


def run_full(holds, tag):
    """One full gate replay (s12.full_replay) in a child process; its hold file is kept in this study's checkpoints."""
    hp = CK / 'holds' / ('holds-%s.json' % tag)
    op = CK / 'holds' / ('full-%s.json' % tag)
    if holds is not None:
        write_json(hp, holds)
    p = js.subprocess.run([PY, __file__, '--full-replay', str(hp) if holds is not None else '-', str(op)],
                          capture_output=True, text=True, timeout=1800, env=env_nobytecode())
    if p.returncode:
        raise RuntimeError('full replay %s failed: %s' % (tag, p.stderr[-2000:]))
    d = read_json(op)
    op.unlink()
    return d


def c2(w, g):
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    d = run_full(None, 'C2')
    doc = d['doc']
    diffs = s12.compare_links(doc['links'], base_doc['links'])
    rows_eq = json.dumps(doc['replacement']) == json.dumps(base_doc['replacement']['footprints'])
    ways = doc['ways_out'] == base_doc['ways_out']
    cons = doc['consolidation'] == base_doc['consolidation']
    ok = not diffs and rows_eq and ways and cons and not doc['hold_errors']
    return ok, {'link_differences': diffs, 'rows_equal': rows_eq, 'ways_out_equal': ways, 'consolidation_equal': cons,
                'hold_errors': doc['hold_errors'], 'working_tree_reads': d['working_tree_reads'], 'wall_s': d['wall_s']}


def c3(w, g):
    n, bad = 0, []
    for k, fp in g.model.fps.items():
        if k[0] not in ('K', 'JL', 'JR', 'P'):
            continue
        for _, num, xy in fp['pads']:
            n += 1
            got = pad_xy(fp, xy, (fp['origin'], fp['side']), 0)
            if got != xy:
                bad.append('%s %s pad %s: %s != %s' % (k[0], k[1], num, got, xy))
    return not bad, {'pads': n, 'differences': bad[:20], 'count_differing': len(bad)}


def c4(w, g):
    """C4 runs the test file's three R8356 poses on the real record."""
    fp = g.model.fps[('K', 'R8356')]
    rec = {'origin': fp['origin'], 'side': fp['side'], 'pads': [(n, xy) for _, n, xy in fp['pads']]}
    want = {'shift': {'1': (207.66, 207.89), '2': (207.66, 206.39)}, 'turn90': {'1': (204.91, 208.14), '2': (206.41, 208.14)},
            'flip': {'1': (205.66, 208.89), '2': (205.66, 207.39)}}
    poses = {'shift': (((207.66, 207.14), 'B'), 0), 'turn90': (((205.66, 208.14), 'B'), 90), 'flip': (((205.66, 208.14), 'F'), 0)}
    got, ok = {}, rec['origin'] == (205.66, 208.14) and rec['side'] == 'B'
    for name, (pose, turn) in poses.items():
        got[name] = {}
        for _, num, xy in fp['pads']:
            v = pad_xy(fp, xy, pose, turn)
            got[name][num] = v
            ok = ok and abs(v[0] - want[name][num][0]) < 1e-9 and abs(v[1] - want[name][num][1]) < 1e-9
    return ok, {'record': rec, 'computed': got, 'hand_values': want}


def c5(w, g):
    """Pads only: 1.5 x the base extent and each pin distance against ancillary_geometry, at one decimal."""
    s = w.s
    if not hasattr(w, 'original'):
        s12.locality_table(w, *s12.base_effective(w))
    before, bt = s12.base_effective(w)
    rows, bad, n, skipped = [], [], 0, []
    for x in w.locality_doc['acceptances']:
        if 'ref' not in x or not x.get('input_runs'):
            continue
        rec, _ = ov.ancillary_geometry(s, x, before, w.original, bt, s.fps)
        b, ic = x['board'], x['ref']
        for run in x['input_runs']:
            net = run['net']
            if 'input_passives_to_buffer_mm' not in run:
                # this run's routed_estimate_mm is the S8 origin-based figure, not a pad figure (reading R1)
                skipped.append('%s %s %s' % (b, ic, net))
                continue
            pts, pins, okc = g.model.points(g.base, net, b)
            pads = {k: v for k, v in pts.items() if k[0] == 'pad'}
            key = net + '.routed_estimate_mm'
            if key in rec and 'routed_estimate_mm' in run:
                n += 1
                mine = round(1.5 * hpwl(list(pads.values())), 1)
                r = {'net': net, 'figure': 'routed_estimate_mm', 'recomputed': rec[key]['recomputed'], 'study': mine}
                rows.append(r)
                if mine != rec[key]['recomputed']:
                    bad.append(r)
            key = net + '.input_passives_to_buffer_mm'
            if key in rec and 'input_passives_to_buffer_mm' in run:
                icpins = [p for p in pads if p[2] == ic]
                for ref, dv in rec[key]['recomputed'].items():
                    n += 1
                    cands = [round(math.dist(pads[q], pads[p]), 1) for q in icpins for p in pads if p[2] == ref]
                    r = {'net': net, 'figure': 'input_passives_to_buffer_mm.' + ref, 'recomputed': dv, 'study': cands}
                    rows.append(r)
                    if dv not in cands:
                        bad.append(r)
    return not bad and n > 0, {'compared': n, 'rows': rows, 'differences': bad, 'runs_without_a_pad_figure': skipped}


def c6(w, g):
    nb, bad, ge = 0, [], []
    t = now()
    for n in sorted(g.model.net_fps):
        for b in g.model.boards(n, (g.base,)):
            pts, _, okc = g.model.points(g.base, n, b)
            v = list(pts.values())
            tr, ex = rmst(v), hpwl(v)
            if tr + 1e-9 < ex:
                ge.append('%s on %s' % (n, b))
            if 2 <= len(v) <= 7:
                nb += 1
                br = brute_rmst(v)
                if abs(br - tr) > 1e-9:
                    bad.append({'net': n, 'board': b, 'prim': tr, 'brute': br})
    return not bad and not ge, {'nets_2_to_7_points': nb, 'tree_differences': bad[:20], 'tree_below_extent': ge[:20],
                                'wall_s': round(now() - t, 1)}


def c7(w, g):
    lid = 'P-K-P-L03.01'
    pts, _, _ = g.model.points(g.base, next(iter(sorted(g.link_nets[lid]))), 'K')
    kp = pts[('link', lid, 'K')]
    ptsf, _, _ = g.model.points(g.base, next(iter(sorted(g.link_nets[lid]))), g.link_front[lid])
    fpnt = ptsf[('link', lid, 'front')]
    geo = w.byid[lid]['geometry']
    ok = abs(kp[0] - C7_K[0]) < 1e-4 and abs(kp[1] - C7_K[1]) < 1e-4 and abs(fpnt[0] - C7_FRONT[0]) < 1e-4 and \
        abs(fpnt[1] - C7_FRONT[1]) < 1e-4 and 179.83 <= kp[1] <= 185.94 and 204.73 <= fpnt[1] <= 210.84
    rec = w.rec(lid)
    z = w.size_of(rec)
    gm = lg.GeoMaker(z, w.ctx.opts, w.ctx.hard)
    sx, sy = rec['slot_centre']
    d0 = [k for k, v in lg.DIR_NAMES.items() if v == rec['direction']][0]
    dflip = (-d0[0], -d0[1])
    flipped = gm.full(sx, sy, dflip, geo['front_extension_mm'], geo['K_extension_mm'])
    kf = centre(flipped['K_connector'])
    shift = math.dist(kf, kp)
    ok = ok and shift > 15.0
    return ok, {'K_point': kp, 'front_point': fpnt, 'hand_K': C7_K, 'hand_front': C7_FRONT,
                'flipped_direction': lg.DIR_NAMES[dflip], 'flipped_K_point': kf, 'K_point_shift_mm': shift}


def c8(w, g):
    rows = w.base_rows_list
    j = judge_ng(w, {}, rows, rules='ng', g=g)
    r = j['NG']
    ok_ng = r['pass'] and r['moved'] == [] and r['evaluated'] == {}
    ok_a = not j['fails']
    j12 = judge_ng(w, {}, rows, rules='s12')
    p11 = read_json(S12DIR / 'checkpoints/arm0.json')['controls']['P11']['detail']
    same = j12['fails'] == p11['fails'] and j12['rows']['claimed'] == p11['claimed'] and \
        j12['rows']['counts'] == p11['row_changes'] and j12['locality']['above_limit'] == p11['locality_above_limit'] and \
        [list(x) for x in j12['locality']['inherited_excess']] == p11['inherited_excess']
    orig = s12.judge(w, {}, rows)
    same_orig = s12.canon(orig) == s12.canon(j12)
    return ok_ng and ok_a and same and same_orig, {
        'ng': ng_summary(r), 'fails_ng_rules': j['fails'], 'passes_ng_rules': j['passes'],
        's12_rules_equal_P11': same, 's12_rules_equal_s12_judge': same_orig, 's12_rules_fails': j12['fails']}


def c9(w, g):
    rows = [r for r in w.base_rows_list if (r['board'], r['ref']) != ('K', 'U5110')]
    sc = g.scene_from_rows(rows, w.base_out)
    r = g.evaluate(sc)
    return r['pass'] and r['moved'] == [] and r['evaluated'] == {}, {'ng': ng_summary(r), 'rows': len(rows)}


def census_s12_record():
    return read_json(S12DIR / 'census.json')


def c10(w, g):
    """census_ng with rules='s12' and rules='ng' for the six links on the three grids, against census.json."""
    rec = census_s12_record()
    out, bad, ngc = {}, [], {}
    for lid in SEARCHED15:
        acc12, accng = [], []
        out[lid] = {}
        ngc[lid] = {}
        for grid in s12.GRIDS:
            t = now()
            c, acc = census_ng(w, lid, grid, rules='s12')
            ta = round(now() - t, 1)
            want = rec['links'][lid]['%g' % grid]
            cw = {k: v for k, v in want.items() if k != 'wall_s'}
            if c != cw:
                bad.append('%s %g: s12 counts differ' % (lid, grid))
            acc12 += acc
            t = now()
            c2_, acc2 = census_ng(w, lid, grid, rules='ng')
            tb = round(now() - t, 1)
            for k in ('offsets', 'evaluated', 'legal_rule1', 'rejections_rule1'):
                if c2_[k] != want[k]:
                    bad.append('%s %g: ng %s differs' % (lid, grid, k))
            for n in ('2', '3', '4'):
                if c2_['after_rule'][n] != want['after_rule'][n]:
                    bad.append('%s %g: ng after rule %s differs' % (lid, grid, n))
            accng += acc2
            ngc[lid]['%g' % grid] = {'counts': c2_, 'accepted': acc2, 'wall_s': tb}
            out[lid]['%g' % grid] = {'s12_wall_s': ta, 'ng_wall_s': tb, 'legal_rule1': sum(c['legal_rule1'].values()),
                                     'after_4': sum(c2_['after_rule']['4'].values()),
                                     'after_6_s12': sum(c['after_rule']['6'].values())}
        if s12.canon(acc12) != s12.canon(rec['accepted'][lid]):
            bad.append('%s: s12 accepted list differs' % lid)
        out[lid]['survivors_s12'] = len(acc12)
        out[lid]['after_4_ng'] = len(accng)
    want_surv = {'P-K-P-L12.02.01.02': 0, 'P-K-P-L03.01': 0, 'P-K-P-L13.01.01.01': 27, 'P-K-P-L13.01.01.02': 0,
                 'P-K-P-L13.01.02.01': 0, 'P-K-P-L15.02.01.01': 73}
    if {l: out[l]['survivors_s12'] for l in SEARCHED15} != want_surv:
        bad.append('survivor counts differ from the brief')
    write_json(CENSUS_NG, ngc)
    return not bad, {'per_link': out, 'differences': bad, 'ng_census': 'checkpoints/census_ng.json'}


class Budget15:
    """js.Budget with the stage 3 caps shared across all target sets (stricter reading)."""

    def __init__(self, seconds, shared):
        self.end = now() + seconds
        self.shared = shared
        self.reason = None

    @property
    def replays(self):
        return self.shared['replays']

    @replays.setter
    def replays(self, v):
        self.shared['replays'] = v

    @property
    def legal(self):
        return self.shared['legal']

    @legal.setter
    def legal(self, v):
        self.shared['legal'] = v

    def out(self):
        if self.reason:
            return True
        if now() > self.end:
            self.reason = 'time slice'
        elif self.shared['replays'] >= REPLAY_CAP3:
            self.reason = '400 rows-only replays'
        elif self.shared['legal'] >= LEGAL_CAP3:
            self.reason = '100 000 legality calls'
        return self.reason is not None


def c11(w, g):
    """S12 stage 3 (South and the seven East sets) with rules='s12', on the S12 stage 2 pools."""
    pools = read_json(S12DIR / 'checkpoints/stage2.json')['pools']
    want = read_json(S12DIR / 'checkpoints/stage3.json')
    keys = ('pool_sizes', 'legality_calls', 'replays', 'complete_scenes', 'bound', 'exhausted', 'must_move')
    got, bad = {}, []
    b = js.Budget(js.CEIL['South'])
    sc, lgs = cluster_search_ng(w, s12.CLUSTERS[1][1], ('U5110',), pools, b, rules='s12')
    got['South'] = {k: lgs.get(k) for k in keys}
    if got['South'] != {k: want['South']['log'].get(k) for k in keys} or sc:
        bad.append('South differs')
    for (targets, minutes), ws in zip(js.EAST_SLICES, want['East']['sets']):
        b = js.Budget(minutes * 60)
        sc, lge = cluster_search_ng(w, s12.CLUSTERS[2][1], targets, pools, b, rules='s12')
        tag = '+'.join(targets)
        got[tag] = {k: lge.get(k) for k in keys}
        if got[tag] != {k: ws['log'].get(k) for k in keys} or sc:
            bad.append('%s differs' % tag)
    u = got['U5210']
    if u['legality_calls'] != 13 or u['complete_scenes'] != 0:
        bad.append('{U5210}: %s legality calls, %s complete scenes' % (u['legality_calls'], u['complete_scenes']))
    return not bad, {'sets': got, 'differences': bad}


def c12(w, g):
    moves, rdoc = js.returned_moves(w)
    out = w.scene_links(moves)
    rows = w.rows_only(out)
    f, info = check_rows_ng(w, rows, rules='ng', g=g, scene_out=out)
    pr = info['protected']
    newp = sorted(x.split(' ')[1] for x in pr['new'])
    shp = sorted(x.split(' ')[1] for x in pr['shifted'])
    moved = {x.split(' ')[1] for x in info['NG']['moved']}
    ok = set(js.EXPECT_P5_N) <= set(newp) and 'R5253' in shp and set(js.EXPECT_P5_N) | {'R5253'} <= moved
    return ok, {'new_protected_rows': newp, 'shifted_protected_rows': shp, 'ng': ng_summary(info['NG']),
                'observation': 'no expected NG verdict (Ruling N7)'}


def c13(w, g):
    n = sorted(x for b, x in w.base_tail if b == 'K' and ('K', x) in w.protected)
    return len(n) == 71, {'protected_under_a_K_tail': len(n), 'refs': n}


def c14(w, g):
    bad = []
    for r in p2.live(w.base_out):
        geo = r.get('geometry') or {}
        if not link_signal_nets(r) or 'K_connector' not in geo or 'front_connector' not in geo:
            bad.append(r['id'])
    span, nolink = 0, []
    for n in sorted(g.model.protected_nets):
        boards = {k[0] for k in g.model.net_fps[n]}
        if len(boards) > 1:
            span += 1
            if not g.model.link_of_net.get(n):
                nolink.append(n)
    return not bad and not nolink, {'links_without_signals_or_connectors': bad, 'protected_nets_on_two_boards': span,
                                    'without_a_link': nolink, 'live_links': len(p2.live(w.base_out))}


def c15(w, g):
    import re
    by = defaultdict(int)
    for k, fp in g.model.fps.items():
        if fp['pads'] and not fp['pin_record']:
            by['%s %s' % (k[0], re.match(r'[A-Z]+', k[1]).group(0))] += 1
    k_ok = by.get('K J') == 196 and by.get('K MH') == 204 and by.get('K TP') == 18 and \
        sum(v for x, v in by.items() if x.startswith('K ')) == 418
    tp = sorted(k for k, fp in g.model.fps.items() if k[0] == 'K' and k[1].startswith('TP') and not fp['pin_record'])[0]
    poses = dict(g.base.poses)
    o, f = poses[tp]
    poses[tp] = ((o[0] + 1.0, o[1]), f)
    sc = Scene(poses, g.base.turns, g.base.links, g.base.rects, g.base.courtyards, 'scene')
    r = g.evaluate(sc)
    return k_ok and r['vector'][6] == 'F', {'by_board_and_prefix': dict(sorted(by.items())), 'moved_for_NG7': '%s %s' % tp,
                                            'vector': ''.join(r['vector'])}


def c18(w, g):
    """Forced evaluation on the all-stay scene: every non-rail net with a protected pad, against the base limit."""
    sc = g.scene_from_rows(w.base_rows_list, w.base_out)
    m = g.model
    n, bad, above = 0, [], 0
    for net in sorted(m.protected_nets):
        n += 1
        up = False
        for b in m.boards(net, (g.paper, g.base, sc)):
            fb, fs, fp_ = m.figures(g.base, net, b), m.figures(sc, net, b), m.figures(g.paper, net, b)
            if fs['extent'] != fb['extent'] or fs['tree'] != fb['tree'] or fs['pairs'] != fb['pairs'] or \
                    not fs['computable'] or not fb['computable']:
                bad.append('%s on %s' % (net, b))
            if fb['extent'] > fp_['extent'] + EPS or fb['tree'] > fp_['tree'] + EPS or \
                    any(v > fp_['pairs'].get(k, float('inf')) + EPS for k, v in fb['pairs'].items()):
                up = True
        above += up
    return not bad, {'nets_forced': n, 'differences': bad[:20], 'nets_with_base_above_paper': above}


CONTROLS = (('C1', c1), ('C2', c2), ('C3', c3), ('C4', c4), ('C5', c5), ('C6', c6), ('C7', c7), ('C8', c8), ('C9', c9),
            ('C10', c10), ('C11', c11), ('C12', c12), ('C13', c13), ('C14', c14), ('C15', c15), ('C18', c18))


# ================================================================ stage 1: census to rule 4 and legality at record

def stage1(w, g, clock):
    ngc = read_json(CENSUS_NG)
    out = {'links': {}, 'candidates': {}}
    for lid in SEARCHED15:
        cand = {}
        n_acc = 0
        for grid in s12.GRIDS:  # 2.0, 0.5, 0.25: a later (finer) grid's record replaces an earlier one
            for e in ngc[lid]['%g' % grid]['accepted']:
                n_acc += 1
                cand[(e['slot_centre'][0], e['slot_centre'][1], e['direction'], e['size'])] = e
        distinct = sorted(cand.values(), key=lambda e: e['key'])
        others = [l for l in SEARCHED15 if l != lid]
        cls = {'legal at record': 0, 'joint-only': 0, 'dropped': 0}
        why_drop, recs = {}, []
        for e in distinct:
            e = dict(e, stay=False)
            m, why = legal_entry_ng(w, lid, e, {}, (), None, rules='ng')
            if m is not None:
                c = 'legal at record'
                e['at_record'] = m
            else:
                m2, why2 = legal_entry_ng(w, lid, e, {}, others, None, rules='ng')
                c = 'joint-only' if m2 is not None else 'dropped'
                e['illegal_at_record'] = why
                if m2 is None:
                    why_drop[why2] = why_drop.get(why2, 0) + 1
            e['class'] = c
            cls[c] += 1
            recs.append(e)
        out['links'][lid] = {'after_rule_4': n_acc, 'distinct': len(distinct), **cls,
                             'dropped_reasons': dict(sorted(why_drop.items(), key=lambda x: -x[1])[:10])}
        out['candidates'][lid] = recs
        log('stage1', lid, out['links'][lid])
        clock.tick()
    return out


# ================================================================ stage 2: single-move screen under NG

_W = {}


def screen_entry(w, g, lid, e):
    t = now()
    m = e['at_record']
    moves = {lid: {'geometry': m['geometry'], 'slot_centre': m['slot_centre'], 'direction': m['direction'], 'size': None}}
    scene_out = w.scene_links(moves)
    rows = w.rows_only(scene_out)
    fails, info = check_rows_ng(w, rows, rules='ng', g=g, scene_out=scene_out)
    items = {a: not fails.get(a) for a in ('A1', 'A3', 'A4', 'A6')}
    r = info['NG']
    return {'link': lid, 'slot_centre': m['slot_centre'], 'direction': m['direction'], 'grid_mm': e['grid_mm'],
            'cost': m['cost'], 'key': e['key'], 'spot': e['spot'], 'dist': e['dist'], 'ring': e['ring'],
            'unanchored_protected': len(e['unanchored_protected']), 'rows_digest': s12.digest(rows),
            'claimed': info['claimed'], 'row_counts': info['counts'], 'acceptance': items,
            'acceptance_fails': {k: v[:6] for k, v in fails.items() if k != 'NG'},
            'ng': ng_summary(r), 'pass': all(items.values()) and r['pass'], 'wall_s': round(now() - t, 2)}


def _screen_task(i):
    lid, e = _W['tasks'][i]
    return i, screen_entry(_W['w'], _W['g'], lid, e)


def stage2_tasks(st1):
    """The replay order of stage 2 and the cap check (STOP 5)."""
    tasks = []
    for lid in ('P-K-P-L12.02.01.02', 'P-K-P-L03.01', 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01', 'P-K-P-L13.01.01.01'):
        tasks += [(lid, e) for e in st1['candidates'][lid] if e['class'] == 'legal at record']
    if len(tasks) > STAGE2_CAP:
        raise Stop('STOP 5: the stage 2 replay cap would cut a link other than P-K-P-L15.02.01.01 (%d)' % len(tasks))
    lid = 'P-K-P-L15.02.01.01'
    s12acc = {(tuple(x['slot_centre']), x['direction']) for x in census_s12_record()['accepted'][lid]}
    l15 = [e for e in st1['candidates'][lid] if e['class'] == 'legal at record']
    first = sorted([e for e in l15 if (tuple(e['slot_centre']), e['direction']) in s12acc], key=lambda e: e['key'])
    rest = sorted([e for e in l15 if (tuple(e['slot_centre']), e['direction']) not in s12acc],
                  key=lambda e: (len(e['unanchored_protected']), e['key']))
    room = STAGE2_CAP - len(tasks)
    l15_order = first + rest
    tasks += [(lid, e) for e in l15_order[:room]]
    pooled = l15_order[room:]
    return tasks, {'L15_legal_at_record': len(l15), 'L15_s12_survivors_first': len(first),
                   'L15_replayed': min(room, len(l15)), 'L15_not_replayed': len(pooled),
                   'L15_pooled': bool(pooled), 'total': len(tasks)}, pooled


def c16(w, g, tasks):
    import multiprocessing as mp
    sub = tasks[:12]
    seq = [screen_entry(w, g, lid, e)['rows_digest'] for lid, e in sub]
    _W.update({'w': w, 'g': g, 'tasks': sub})
    with mp.get_context('fork').Pool(WORKERS) as pool:
        par = [r['rows_digest'] for _, r in sorted(pool.imap_unordered(_screen_task, range(len(sub))))]
    return seq == par, {'candidates': len(sub), 'sequence_digests': seq, 'pool_digests': par, 'workers': WORKERS}


def stage2(w, g, st1, clock):
    import multiprocessing as mp
    tasks, info, pooled = stage2_tasks(st1)
    d = STAGE2_DIR
    d.mkdir(parents=True, exist_ok=True)
    done = {}
    for f in sorted(d.glob('part-*.json')):
        for r in read_json(f):
            done[r['index']] = r
    todo = [i for i in range(len(tasks)) if i not in done]
    log('stage2', len(tasks), 'tasks', len(done), 'done')
    _W.update({'w': w, 'g': g, 'tasks': tasks})
    buf = []
    part = len(list(d.glob('part-*.json')))
    if todo:
        with mp.get_context('fork').Pool(WORKERS) as pool:
            for i, r in pool.imap(_screen_task, todo):
                r['index'] = i
                done[i] = r
                buf.append(r)
                if len(buf) >= 25:
                    write_json(d / ('part-%03d.json' % part), buf)
                    part += 1
                    buf = []
                    clock.tick()
                    log('stage2', len(done), '/', len(tasks))
        if buf:
            write_json(d / ('part-%03d.json' % part), buf)
            clock.tick()
    recs = [done[i] for i in range(len(tasks))]
    return recs, info, pooled


# ================================================================ stage 3: scenes per cluster

def build_pools(w, st1, screen, pooled):
    """Per link: the record plus at most 60 entries, one per spot: stage 2 passers by the S12 cost key, then
    joint-only candidates by unanchored protected count, then cost (and, for a pooled L15.02.01.01, its unreplayed
    legal-at-record candidates after them)."""
    passers = defaultdict(list)
    for r in screen:
        if r['pass']:
            passers[r['link']].append(r)
    pooled_keys = {(tuple(e['slot_centre']), e['direction']) for e in pooled}
    pools, info = {}, {}
    for lid in SEARCHED15:
        recs = st1['candidates'][lid]
        byslot = {(tuple(e['slot_centre']), e['direction']): e for e in recs}
        order = []
        for r in sorted(passers[lid], key=lambda r: r['key']):
            e = byslot[(tuple(r['slot_centre']), r['direction'])]
            order.append(('stage 2 passer', e, True, e['at_record']))
        for e in sorted((e for e in recs if e['class'] == 'joint-only'), key=lambda e: (len(e['unanchored_protected']), e['cost'], e['key'])):
            order.append(('joint-only', e, False, None))
        for e in sorted((e for e in recs if (tuple(e['slot_centre']), e['direction']) in pooled_keys), key=lambda e: e['key']):
            order.append(('legal at record, not replayed (cap)', e, False, e['at_record']))
        seen, entries = set(), []
        for kind, e, clean, m in order:
            sp = tuple(e['spot'])
            if sp in seen:
                continue
            seen.add(sp)
            src = m or e
            entries.append({'stay': False, 'cost': src['cost'], 'key': e['key'], 'geometry': src['geometry'],
                            'slot_centre': e['slot_centre'], 'direction': e['direction'], 'dist': e['dist'],
                            'ring': e['ring'], 'grid_mm': e['grid_mm'], 'size': None, 'kind': kind,
                            'screen': {'clean': clean}, 'unanchored_protected': len(e['unanchored_protected'])})
        spots = len(entries)
        entries = entries[:POOL_CAP]
        for i, x in enumerate(entries):
            x['pool_order'] = i
        st = js.stay_entry(w, lid)
        st['pool_order'] = -1
        pools[lid] = [st] + entries
        info[lid] = {'spots': spots, 'entries': len(entries), 'cut_at_60': spots > POOL_CAP,
                     'by_kind': {k: sum(1 for x in entries if x['kind'] == k) for k in
                                 ('stage 2 passer', 'joint-only', 'legal at record, not replayed (cap)')}}
    return pools, info


def rank15(w, sc):
    prot = sum(1 for x in sc['row_info']['NG']['moved'] if tuple(x.split(' ', 1)) in w.protected)
    return [-len(sc['claimed']), prot, len(sc['tails_new']), list(sc['rank'])]


def stage3(w, g, pools, clock):
    d = ck('stage3')
    d.mkdir(parents=True, exist_ok=True)
    shared = {'replays': 0, 'legal': 0}
    carry = 0.0
    placed = set()
    sets = []
    stage_end_s = STEP_CEIL['stage3']
    for n, (targets, cluster, minutes) in enumerate(SETS3, 1):
        f = d / ('set-%d.json' % n)
        if f.exists():
            rec = read_json(f)
            sets.append(rec)
            shared = rec['shared_after']
            carry = rec['carry_after_s']
            if rec.get('scenes'):
                placed |= set(targets)
            continue
        links = dict((c[0], c[1]) for c in CLUSTERS15)[cluster]
        rec = {'set': n, 'cluster': cluster, 'targets': list(targets), 'minutes': minutes}
        used_stage = clock.rec['steps'].get('stage3', 0.0)
        if all(ic in placed for ic in targets):
            rec['skipped'] = 'every IC of the set already has a clean scene'
        elif used_stage >= stage_end_s:
            rec['not_searched'] = 'stage 3 ceiling reached'
        else:
            slot = min(minutes * 60 + carry, SET_MAX_S, stage_end_s - used_stage - 60)
            ts = now()
            b = Budget15(max(slot, 0.0), shared)
            sc, lg_ = cluster_search_ng(w, links, targets, pools, b, rules='ng', g=g)
            used = now() - ts
            carry = max(0.0, minutes * 60 + carry - used)
            for x in sc:
                x['rank15'] = rank15(w, x)
            sc = sorted(sc, key=lambda x: x['rank15'])
            rec.update({'scenes': sc, 'log': lg_, 'wall_s': round(used, 1), 'slot_s': round(slot, 1)})
            if sc:
                placed |= set(targets)
        rec['shared_after'] = dict(shared)
        rec['carry_after_s'] = carry
        write_json(f, rec)
        sets.append(rec)
        clock.tick()
        log('stage3 set', n, targets, rec.get('log', {}).get('bound'), len(rec.get('scenes', [])))
    return sets


# ================================================================ stage 4: joint scene, overlay rules, full replay

def stage4(w, g, sets, clock):
    d = ck('stage4')
    d.mkdir(parents=True, exist_ok=True)
    by = {'South': [], 'East': []}
    for s_ in sets:
        by[s_['cluster']] += s_.get('scenes', [])
    opts = []
    for c in ('South', 'East'):
        sc = sorted(by[c], key=lambda x: x['rank15'])[:CLEAN_CAP]
        opts.append(sc + [None])
    combos = []
    for cs, ce in js.itertools.product(*opts):
        if cs is None and ce is None:
            continue
        moves = {}
        for c in (cs, ce):
            if c:
                moves.update(c['moves'])
        claimed = sum(len(c['claimed']) for c in (cs, ce) if c)
        combos.append((-claimed, sum(c['rank15'][1] for c in (cs, ce) if c), moves))
    combos.sort(key=lambda x: (x[0], x[1], s12.canon({k: (v.get('slot_centre'), v.get('direction')) for k, v in x[2].items()})))
    capped = len(combos) > JOINT_CAP
    combos = combos[:JOINT_CAP]
    log_ = {'combinations': len(combos), 'combination_cap_reached': capped, 'overlay_searches': 0, 'full_replays': 0,
            'records': []}
    overlay_used, full_used = 0, 0
    survivors = []
    for i, (neg, _, moves) in enumerate(combos):
        f = d / ('combo-%d.json' % i)
        if f.exists():
            rec = read_json(f)
        else:
            rec = {'combo': i, 'links': sorted(moves), 'moves': moves}
            bad = js.reverify(w, moves)
            if bad:
                rec['verdict'] = 'reverify fails'
                rec['reverify'] = bad
            else:
                scene_out = w.scene_links(moves)
                rows = w.rows_only(scene_out)
                fails, info = check_rows_ng(w, rows, rules='ng', g=g, scene_out=scene_out)
                rec['rows_digest'] = s12.digest(rows)
                if fails:
                    rec['verdict'] = 'fails %s at rows level' % ', '.join(sorted(fails))
                    rec['fails'] = {k: v[:6] for k, v in fails.items()}
                    rec['ng'] = ng_summary(info['NG'])
                elif overlay_used >= OVERLAY_CAP:
                    rec['verdict'] = 'rows clean, overlay NOT RUN (cap 6)'
                else:
                    overlay_used += 1
                    j = judge_ng(w, moves, rows, rules='ng', g=g)
                    rec['judge'] = _judge_record(j)
                    rec['rows'] = rows
                    if j['fails']:
                        rec['verdict'] = 'fails %s' % ', '.join(sorted(j['fails']))
                    elif full_used >= FULL_CAP:
                        rec['verdict'] = 'rows clean, A12 NOT RUN (cap 8)'
                    else:
                        a12, used = gate_check15(w, moves, rows, FULL_CAP - full_used)
                        full_used += used
                        rec['A12'] = a12
                        rec['verdict'] = 'candidate' if a12['pass'] else 'rows clean, gate replay differs'
            rec['overlay_used_after'], rec['full_used_after'] = overlay_used, full_used
            write_json(f, rec)
            clock.tick()
        overlay_used, full_used = rec['overlay_used_after'], rec['full_used_after']
        log_['records'].append({k: rec.get(k) for k in ('combo', 'links', 'verdict')})
        if rec.get('verdict') in ('candidate', 'rows clean, gate replay differs'):
            survivors.append(rec)
    log_['overlay_searches'], log_['full_replays'] = overlay_used, full_used
    return survivors, log_


def _judge_record(j):
    out = {k: j[k] for k in ('fails', 'passes', 'block_rule', 'overlay_blocks', 'effective_movements', 'face_changes',
                             'protected_effective', 'link_figures')}
    out['rows_info'] = {k: v for k, v in j['rows'].items() if k != 'NG'}
    out['NG'] = ng_summary(j['NG'])
    out['locality_above_limit'] = j['locality']['above_limit']
    return out


def gate_check15(w, moves, rows, allowance):
    """A12 as joint_search.gate_check, with the full replays run by this study (holds kept in its checkpoints)."""
    holds0 = [h for h in s12.gjson(s12.BASE, s12.GOPTS)['slot_holds']['value']]
    holds = holds0 + [s12.hold_entry(w, lid, moves.get(lid, {'stay': True}), 'S15 scene slot') for lid in s12.SEARCHED]
    extra, used, history = [], 0, []
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    B = {r['id']: r for r in base_doc['links']}
    while used < allowance:
        used += 1
        d = run_full(holds + extra, 'A12-%d' % int(now()))
        doc = d['doc']
        L = {r['id']: r for r in doc['links']}
        errs = list(doc['hold_errors'])
        at = {}
        for lid in s12.SEARCHED:
            m = moves.get(lid, {'stay': True})
            want = (B[lid]['slot_centre'], B[lid]['direction']) if m.get('stay') else (m['slot_centre'], m['direction'])
            at[lid] = L.get(lid) is not None and (L[lid]['slot_centre'], L[lid]['direction']) == (want[0], want[1])
        held_ids = {h['link'] for h in holds + extra}
        moved_unheld = sorted(i for i, r in B.items() if not r.get('gone') and i not in held_ids and
                              s12.compare_links([L[i]] if i in L else [], [r], ('centre', 'slot_centre', 'direction', 'geometry')))
        live = sum(1 for r in doc['links'] if not r.get('gone'))
        gone_eq = sorted(i for i, r in L.items() if r.get('gone')) == sorted(i for i, r in B.items() if r.get('gone'))
        rows_eq = json.dumps(doc['replacement']) == json.dumps(rows)
        ways_eq = doc['ways_out'] == base_doc['ways_out']
        history.append({'holds_extra': [h['link'] for h in extra], 'hold_errors': errs, 'at_scene_slot': at,
                        'moved_unheld_links': moved_unheld, 'live': live, 'dissolved_equal': gone_eq,
                        'ways_out_equal': ways_eq, 'rows_equal_rows_only': rows_eq, 'wall_s': d['wall_s']})
        if moved_unheld and len(extra) < js.EXTRA_HOLD_CAP and used < allowance:
            for i in moved_unheld[:js.EXTRA_HOLD_CAP - len(extra)]:
                extra.append(s12.hold_entry(w, i, {'stay': True}, 'S15 retry: unheld live link moved in the replay'))
            continue
        ok = not errs and all(at.values()) and not moved_unheld and live == 62 and gone_eq and ways_eq and rows_eq
        return {'pass': ok, 'attempts': history, 'extra_holds': extra}, used
    return {'pass': False, 'attempts': history, 'extra_holds': extra, 'note': 'full replay allowance exhausted'}, used


# ================================================================ outputs

def tallies(recs):
    """First-failure and strictness tallies over stage 2 records."""
    first_test, by_net, by_fp, strict = defaultdict(int), defaultdict(int), {'ICs': defaultdict(int), 'passives': defaultdict(int)}, \
        defaultdict(int)
    order = ('A1', 'A3', 'A4', 'A6')
    for r in recs:
        if r['pass']:
            continue
        ft = next((a for a in order if not r['acceptance'][a]), None) or r['ng']['first_failure']
        first_test[ft] += 1
        ngr = r['ng']
        for n in ngr['failing_nets']:
            by_net[n] += 1
        movers = set()
        for n in ngr['failing_nets']:
            movers |= set(ngr['evaluated'][n]['movers'])
        for m in movers:
            ref = m.split(' ', 1)[1]
            by_fp['ICs' if ref.startswith('U') else 'passives'][m] += 1
        a_ok = all(r['acceptance'].values())
        for k, v in ngr['tallies'].items():
            if v and a_ok:
                strict[k] += 1
    top = lambda d, n=25: dict(sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n])  # noqa: E731
    return {'first_failure_by_test': dict(first_test), 'failing_nets_top': top(by_net), 'failing_nets_distinct': len(by_net),
            'moved_footprints_on_failing_nets': {k: top(v) for k, v in by_fp.items()},
            'moved_footprints_distinct': {k: len(v) for k, v in by_fp.items()}, 'strictness_alone': dict(strict)}


def after_each_test(recs):
    out, alive = {}, list(recs)
    for a in ('A1', 'A3', 'A4', 'A6'):
        alive = [r for r in alive if r['acceptance'][a]]
        out[a] = len(alive)
    for i, t in enumerate(TESTS):
        alive = [r for r in alive if r['ng']['vector'][i] != 'F']
        out[t] = len(alive)
    return out


def ic_verdicts(st1, screen, s2info, sets, st4, written):
    out = {}
    for ic in ICS4:
        lid = NEEDS[ic]
        recs = [r for r in screen if r['link'] == lid]
        legal = st1['links'][lid]['legal at record']
        complete = len(recs) == legal
        claim_pass = [r for r in recs if r['pass'] and ic in r['claimed']]
        dep = {}
        for k in ('link_end_alone', 'stricter_limit_alone'):
            dep[k] = sum(1 for r in recs if not r['pass'] and all(r['acceptance'].values()) and r['ng']['tallies'][k]
                         and ic in r['claimed'])
            dep[k + '_any_claim'] = sum(1 for r in recs if not r['pass'] and all(r['acceptance'].values()) and r['ng']['tallies'][k])
        illegal = st1['links'][lid]['joint-only'] + st1['links'][lid]['dropped']
        bounds = []
        for s_ in sets:
            if ic in s_['targets']:
                lg_ = s_.get('log') or {}
                if s_.get('not_searched'):
                    bounds.append('set %s: %s' % ('+'.join(s_['targets']), s_['not_searched']))
                elif lg_.get('bound') and not lg_.get('exhausted'):
                    bounds.append('set %s: %s' % ('+'.join(s_['targets']), lg_['bound']))
                elif lg_.get('exhausted'):
                    bounds.append('set %s: pools exhausted (%s)' % ('+'.join(s_['targets']), lg_.get('bound') or 'no clean scene'))
        rec = {'link_needed': lid, 'stage2_records': len(recs), 'legal_at_record': legal, 'complete_screen': complete,
               'single_move_passers_claiming': len(claim_pass), 'illegal_at_record': illegal, 'dependence': dep,
               'stage3_bounds': bounds}
        if any(ic in x['claimed'] for x in written):
            rec['verdict'] = STATUS
        elif complete and not claim_pass:
            line = 'NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD)'
            rec['verdict'] = line
            rec['verdict_line'] = '%s: %d legal-at-record survivors of %s replayed and failed; %d rule-4 survivors ' \
                                  'illegal at record (%d joint-only, %d dropped)' % (
                                      line, len(recs), lid, illegal, st1['links'][lid]['joint-only'], st1['links'][lid]['dropped'])
        else:
            why = []
            if not complete:
                why.append('stage 2 screen of %s incomplete' % lid)
            why += bounds or ['the stage 3 pool reduction (at most 60 entries per link)']
            rec['verdict'] = 'NO SCENE FOUND (BOUNDED)'
            rec['verdict_line'] = 'NO SCENE FOUND (BOUNDED): %s' % '; '.join(why)
        if rec['verdict'] != STATUS:
            notes = []
            if dep['link_end_alone']:
                notes.append('%d candidate(s) of %s fail only through a link-end change ("link end alone")' % (dep['link_end_alone'], lid))
            if dep['stricter_limit_alone']:
                notes.append('%d candidate(s) of %s fail only the stricter limit ("stricter limit alone")' % (dep['stricter_limit_alone'], lid))
            rec['dependence_line'] = '; '.join(notes) if notes else 'no dependence: setting aside the "link end alone" and ' \
                '"stricter limit alone" failures leaves no passing single move that places %s' % ic
            if notes:
                rec['verdict_line'] += ' — depends on: ' + '; '.join(notes)
        out[ic] = rec
    return out


def scene_body(w, n, rec):
    moves = rec['moves']
    slots = []
    for lid in s12.SEARCHED:
        m = moves.get(lid, {'stay': True})
        h = s12.hold_entry(w, lid, m, 'S15 candidate slot')
        h.update({'stay': bool(m.get('stay')), 'size': w.byid[lid]['circuits'] if m.get('stay') else w.rec(lid, m.get('size'))['circuits']})
        slots.append(h)
    ngr = rec['judge']['NG']
    moved = []
    for x in ngr['moved']:
        b, ref = x.split(' ', 1)
        nets = sorted(n_ for n_, e in ngr['evaluated'].items() if x in e['movers'])
        moved.append({'board': b, 'ref': ref, 'protected': (b, ref) in w.protected,
                      'nets': {n_: {'class': ngr['evaluated'][n_]['class'], 'boards': ngr['evaluated'][n_]['boards']} for n_ in nets}})
    body = {'status': STATUS + ', UNVALIDATED DRAFT', 'scene': n, 'slots': slots, 'moved_footprints': moved,
            'ng': ngr, 'acceptance': {**rec['judge']['passes'], 'A12': rec['A12']['pass']}, 'A12': rec['A12'],
            'claimed': rec['judge']['rows_info']['claimed']}
    body['digest'] = scene_digest(slots, rec['rows'])
    return body


def fingerprint():
    def sh(cmd):
        try:
            return js.subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
        except Exception as e:  # noqa: BLE001
            return 'unavailable: %s' % e
    import platform
    mem = {l.split(':')[0]: l.split(':')[1].strip() for l in open('/proc/meminfo') if l.startswith(('MemTotal', 'MemAvailable', 'SwapTotal'))}
    return {'os': platform.platform(), 'nproc': os.cpu_count(), 'cpu_affinity': sorted(os.sched_getaffinity(0)), 'meminfo': mem,
            'cgroup_memory_max': Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else 'absent',
            'disk': sh(['df', '-h', str(ROOT)]).splitlines()[-1:], 'python': platform.python_version(), 'interpreter': sys.executable,
            'commit': s12.git('rev-parse', 'HEAD', text=True).strip(), 'brief_sha256': s12.sha_file(ROOT / BRIEF)}


def bulk_files():
    """The bulky intermediates present in the cache, by their path relative to the study directory."""
    if not BULK.exists():
        return []
    return sorted(str(f.relative_to(BULK)) for f in BULK.rglob('*.json'))


def bulk_state():
    """(present, problems) of the cache against the tracked manifest."""
    if not BULK_MANIFEST.exists():
        return False, ['bulk-manifest.json missing']
    man = read_json(BULK_MANIFEST)['files']
    missing = [r for r in man if not (BULK / r).exists()]
    if len(missing) == len(man):
        return False, []
    bad = ['%s absent from the cache' % r for r in missing]
    for r, v in man.items():
        f = BULK / r
        if f.exists() and (f.stat().st_size != v['bytes'] or s12.sha_file(f) != v['sha256']):
            bad.append('%s differs from the manifest' % r)
    extra = sorted(set(bulk_files()) - set(man))
    bad += ['%s in the cache but not in the manifest' % r for r in extra]
    return True, bad


def write_manifest():
    files = {r: {'sha256': s12.sha_file(BULK / r), 'bytes': (BULK / r).stat().st_size} for r in bulk_files()}
    write_json(BULK_MANIFEST, {
        'why': 'The owner rule forbids Git LFS and committed large intermediate dumps, so the bulky stage 1 and stage 2 '
               'intermediates are kept out of git in the ignored cache below; their hashes and sizes are pinned here.',
        'cache': str(BULK.relative_to(ROOT)) if BULK.is_relative_to(ROOT) else str(BULK),
        'durable_copy': {'location': DURABLE, 'layout': 'same relative paths, with a copy of this manifest',
                         'verified': 'every SHA-256 and size re-read and compared after a 10 s settle'},
        'reproducibility': 'a re-run does not reproduce these hashes: every record carries its wall_s',
        'files': files, 'total_bytes': sum(v['bytes'] for v in files.values())})


def finish(stop=None, rewrite_manifest=False):
    """Rebuild result.json. The driver rewrites the bulk manifest; a later --finish only verifies against it."""
    if rewrite_manifest or not BULK_MANIFEST.exists():
        write_manifest()
    present, bad = bulk_state()
    if bad or (read_json(BULK_MANIFEST)['files'] and not present):
        raise SystemExit('finish needs the bulky intermediates in %s, matching the manifest: %s' % (BULK, bad or 'absent'))
    run = read_json(ck('run.json'))
    res = {'status': 'GEOMETRIC EVIDENCE ONLY, STUDY, NOTHING ADOPTED, UNVALIDATED DRAFTS', 'brief': BRIEF,
           'brief_sha256': BRIEF_SHA, 'snapshot': s12.BASE, 'fingerprint': run.get('fingerprint'),
           'pins': read_json(ck('pins.json')) if ck('pins.json').exists() else None, 'run': run, 'stop': stop or run.get('stop')}
    controls = {}
    for f in sorted((CK / 'arm0').glob('C*.json'), key=lambda p: int(p.stem[1:])):
        c = read_json(f)
        controls[f.stem] = c['pass']
    res['controls'] = controls
    guards = {}
    for f in sorted((CK / 'guard').glob('*.json')):
        gd = read_json(f)
        guards[f.stem] = {k: gd.get(k) for k in ('command', 'returncode', 'finished', 'wall_s', 'samples', 'peak_tree_rss_mib',
                                                 'min_mem_available_mib', 'peak_docker_container_mem_mib', 'watchdog_fired')}
    res['guards'] = guards
    if STAGE1.exists():
        st1 = read_json(STAGE1)
        res['stage1'] = st1['links']
    if SCREEN.exists():
        sc = read_json(SCREEN)
        recs = sc['records']
        res['stage2'] = {'info': sc['info'], 'c16': sc.get('c16'),
                         'per_link': {lid: {'replayed': sum(1 for r in recs if r['link'] == lid),
                                            'pass': sum(1 for r in recs if r['link'] == lid and r['pass']),
                                            'after_each_test': after_each_test([r for r in recs if r['link'] == lid])}
                                      for lid in SEARCHED15},
                         'tallies': tallies(recs)}
    if ck('stage3/pools.json').exists():
        res['stage3_pools'] = read_json(ck('stage3/pools.json'))['info']
    sets = [read_json(f) for f in sorted((CK / 'stage3').glob('set-*.json'), key=lambda p: int(p.stem.split('-')[1]))] \
        if (CK / 'stage3').exists() else []
    res['stage3'] = [{k: (v if k != 'scenes' else len(v)) for k, v in s_.items() if k != 'log'} |
                     {'log': {k: v for k, v in (s_.get('log') or {}).items() if k != 'rejected_scenes'}} for s_ in sets]
    st4 = read_json(ck('stage4/log.json')) if ck('stage4/log.json').exists() else None
    res['stage4'] = st4
    written = []
    CAND.mkdir(exist_ok=True)
    for f in CAND.glob('scene-*.json'):
        written.append({'scene': int(f.stem.split('-')[1]), 'digest': read_json(f)['digest'], 'claimed': read_json(f)['claimed']})
    res['candidates'] = sorted(written, key=lambda x: x['scene'])
    if STAGE1.exists() and SCREEN.exists() and st4 is not None:
        res['verdicts'] = ic_verdicts(read_json(STAGE1), read_json(SCREEN)['records'], read_json(SCREEN)['info'],
                                      sets, st4, written)
    cks = {}
    for f in sorted(CK.rglob('*.json')):
        if 'guard' in f.parts or f.name == 'run.json' or f.parent.name == 'holds' or f.parent.name == 'c17':
            continue
        cks[str(f.relative_to(OUTDIR))] = s12.sha_file(f)
    for r in bulk_files():
        cks[r] = s12.sha_file(BULK / r)
    res['digests'] = dict(sorted(cks.items()))
    res['bulk_intermediates'] = {'cache': str(BULK.relative_to(ROOT)) if BULK.is_relative_to(ROOT) else str(BULK),
                                 'manifest': BULK_MANIFEST.name, 'files': len(bulk_files())}
    write_json(RESULT, res)
    return res


# ================================================================ the driver

def control_record(name, ok, detail, t0):
    rec = {'control': name, 'pass': bool(ok), 'detail': detail, 'wall_s': round(now() - t0, 1)}
    write_json(CK / 'arm0' / ('%s.json' % name), rec)
    log(name, 'PASS' if ok else 'FAIL', rec['wall_s'])
    return rec


def drive(resume=False):
    CK.mkdir(parents=True, exist_ok=True)
    run_path = ck('run.json')
    if run_path.exists() and not resume:
        raise SystemExit('run.json exists: use --resume')
    clock = Clock(run_path)
    rec = clock.rec
    if resume:
        rec['resumes'].append({'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                               'reason': os.environ.get('S15_RESUME_REASON', 'interrupted')})
        if len(rec['resumes']) > RESUME_CAP:
            rec['stop'] = 'STOP 6: a fifth resume'
            write_json(run_path, rec)
            finish(rewrite_manifest=True)
            return
    else:
        rec['fingerprint'] = fingerprint()
        rec['started'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        gd = CK / 'guard'
        for f in sorted(gd.glob('*start-*.json')) if gd.exists() else ():
            rec['executor_timed'][f.stem] = read_json(f)['wall_s']
        if (CK / 'c17' / 'guard.json').exists():
            rec['executor_timed']['c17-detachment-test'] = read_json(CK / 'c17' / 'guard.json')['wall_s']
    rec['stop'] = None
    write_json(run_path, rec)
    try:
        clock.begin('arm0')
        pins, bad = pins15()
        if resume:
            old = read_json(ck('pins.json'))
            if old['pins'] != pins:
                raise Stop('STOP 1: input pins changed since the start: %s' % bad)
        write_json(ck('pins.json'), {'pins': pins, 'problems': bad})
        if bad:
            raise Stop('STOP 1: input pins differ: %s' % bad)
        w = s12.World()
        g = G15(w)
        clock.tick()
        for name, fn in CONTROLS:
            f = CK / 'arm0' / ('%s.json' % name)
            if f.exists() and read_json(f)['pass']:
                continue
            t0 = now()
            ok, detail = fn(w, g)
            control_record(name, ok, detail, t0)
            clock.tick()
            if not ok:
                raise Stop('STOP 1: control %s fails' % name)
        c17 = read_json(CK / 'c17' / 'result.json')
        control_record('C17', c17['pass'], c17, now())
        if not c17['pass']:
            raise Stop('STOP 1: control C17 fails')
        clock.begin('stage1')
        if not STAGE1.exists():
            st1 = stage1(w, g, clock)
            write_json(STAGE1, st1)
        st1 = read_json(STAGE1)
        c10 = read_json(CK / 'arm0' / 'C10.json')['detail']['per_link']
        diff = [l for l in SEARCHED15 if st1['links'][l]['after_rule_4'] != c10[l]['after_4_ng']]
        if diff:
            raise Stop('STOP 5: stage 1 counts differ from C10 for %s' % diff)
        clock.tick()
        clock.begin('stage2')
        if not SCREEN.exists():
            tasks, info, pooled = stage2_tasks(st1)
            f16 = CK / 'arm0' / 'C16.json'
            if not (f16.exists() and read_json(f16)['pass']):
                t0 = now()
                ok, detail = c16(w, g, tasks)
                control_record('C16', ok, detail, t0)
                clock.tick()
                if not ok:
                    raise Stop('STOP 1: control C16 fails')
            recs, info, pooled = stage2(w, g, st1, clock)
            write_json(SCREEN, {'status': 'GEOMETRIC EVIDENCE ONLY, STUDY, UNVALIDATED DRAFTS', 'info': info,
                                'pooled_L15': [{'slot_centre': e['slot_centre'], 'direction': e['direction']} for e in pooled],
                                'c16': read_json(CK / 'arm0' / 'C16.json')['pass'], 'records': recs})
            clock.tick()
        sc = read_json(SCREEN)
        clock.begin('stage3')
        pooled = [e for e in st1['candidates']['P-K-P-L15.02.01.01']
                  if {'slot_centre': e['slot_centre'], 'direction': e['direction']} in sc['pooled_L15']]
        if ck('stage3/pools.json').exists():
            pdoc = read_json(ck('stage3/pools.json'))
            pools = pdoc['pools']
        else:
            pools, pinfo = build_pools(w, st1, sc['records'], pooled)
            write_json(ck('stage3/pools.json'), {'pools': pools, 'info': pinfo})
        sets = stage3(w, g, pools, clock)
        clock.begin('stage4')
        surv, log4 = stage4(w, g, sets, clock)
        write_json(ck('stage4/log.json'), log4)
        CAND.mkdir(exist_ok=True)
        cands = sorted([x for x in surv if x['verdict'] == 'candidate'],
                       key=lambda x: (-len(x['judge']['rows_info']['claimed']),
                                      sum(1 for m in x['judge']['NG']['moved'] if tuple(m.split(' ', 1)) in w.protected)))
        for n, x in enumerate(cands, 1):
            write_json(CAND / ('scene-%d.json' % n), scene_body(w, n, x))
        clock.begin(None)
        clock.tick()
        rec['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    except Stop as e:
        rec['stop'] = str(e)
        log(str(e))
    try:
        clock.tick(save=False)
    except Stop:
        pass
    write_json(run_path, rec)
    finish(rewrite_manifest=True)
    log('driver end', rec.get('stop'))


# ================================================================ check and verify

def moves_from_scene(w, body):
    moves = {}
    for name, links, _ in CLUSTERS15:
        chosen = {}
        for lid in links:
            h = next(x for x in body['slots'] if x['link'] == lid)
            if h['stay']:
                chosen[lid] = {'stay': True}
                continue
            c = w.byid[lid]['centre']
            dist = math.hypot(h['slot_centre'][0] - c[0], h['slot_centre'][1] - c[1])
            e = {'stay': False, 'slot_centre': h['slot_centre'], 'direction': h['direction'], 'dist': dist,
                 'ring': s12.ring_of(dist)}
            later = links[links.index(lid) + 1:]
            m, why = legal_entry_ng(w, lid, e, dict(chosen), later, None, rules='ng')
            if m is None:
                raise ValueError('scene slot of %s not legal: %s' % (lid, why))
            chosen[lid] = m
        moves.update({k: v for k, v in chosen.items() if not v.get('stay')})
    return moves


def verify_scene(w, g, n, full=True):
    errs = []
    body = read_json(CAND / ('scene-%d.json' % n))
    moves = moves_from_scene(w, body)
    rows = w.rows_only(w.scene_links(moves))
    if scene_digest(body['slots'], rows) != body['digest']:
        errs.append('scene %d: digest differs' % n)
    j = judge_ng(w, moves, rows, rules='ng', g=g)
    if j['fails']:
        errs.append('scene %d fails %s' % (n, sorted(j['fails'])))
    if full:
        a12, _ = gate_check15(w, moves, rows, 1 + min(len(body['A12'].get('extra_holds', [])), js.EXTRA_HOLD_CAP))
        if not a12['pass']:
            errs.append('scene %d: A12 fails' % n)
    return errs


CHECK_CONTROLS = ('C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C13', 'C14', 'C15', 'C18')


def check():
    """Input pins; the offline controls re-run against their records; every checkpoint and screen digest; the result
    summaries and verdicts rebuilt from the checkpoints; three stage 2 replays re-run; every written scene verified."""
    res = read_json(RESULT)
    errs = []
    pins, bad = pins15()
    errs += bad
    if pins != read_json(ck('pins.json'))['pins']:
        errs.append('input pins differ from the run')
    w = s12.World()
    g = G15(w)
    fns = dict(CONTROLS)
    for name in CHECK_CONTROLS:
        ok, detail = fns[name](w, g)
        want = read_json(CK / 'arm0' / ('%s.json' % name))
        if not ok or s12.canon(json.loads(json.dumps(detail, default=_jdefault))) != s12.canon(want['detail']):
            if name == 'C6':
                d1 = dict(detail)
                d2 = dict(want['detail'])
                d1.pop('wall_s', None)
                d2.pop('wall_s', None)
                if ok and s12.canon(d1) == s12.canon(d2):
                    continue
            errs.append('%s differs from its record' % name)
    present, bad = bulk_state()
    if bad:
        raise SystemExit('CHECK FAILED: the bulky intermediates in %s are partly present or differ from the '
                         'manifest: %s' % (BULK, bad))
    man = read_json(BULK_MANIFEST)['files'] if BULK_MANIFEST.exists() else {}
    not_run = []
    checked = 0
    for path, want in res.get('digests', {}).items():
        if path in man:
            if man[path]['sha256'] != want:
                errs.append('manifest and result.json disagree on %s' % path)
            if not present:
                continue
        f = BULK / path if path in man else OUTDIR / path
        checked += 1
        if s12.sha_file(f) != want:
            errs.append('digest of %s differs' % path)
    if not present:
        not_run.append('bulky intermediates absent from %s: their %d digests, the 3 stage 2 replays against '
                       'screen.json and the rebuild of the stage 1, stage 2 and verdict summaries are NOT RUN '
                       '(the manifest and result.json digests were compared instead)' % (BULK, len(man)))
        again = finish_preview_light()
        for k in ('stage3', 'stage4', 'candidates'):
            if s12.canon(again.get(k)) != s12.canon(res.get(k)):
                errs.append('result %s differs when rebuilt' % k)
        for c in res.get('candidates', []):
            errs += verify_scene(w, g, c['scene'], full=False)
        if errs:
            raise SystemExit('CHECK FAILED: %s' % errs)
        print('PARTIAL CHECK (bulky intermediates absent; the copy is at %s): only the tracked part was checked' % DURABLE)
        print('PASS for what is tracked: input pins, %d offline controls, %d digests, stage 3 and 4 '
              'summaries rebuilt equal, %d scenes verified' % (len(CHECK_CONTROLS), checked, len(res.get('candidates', []))))
        for n in not_run:
            print('NOT RUN:', n)
        return
    sc = read_json(SCREEN)
    st1 = read_json(STAGE1)
    tasks, info, _ = stage2_tasks(st1)
    for i in range(min(3, len(tasks))):
        lid, e = tasks[i]
        r = screen_entry(w, g, lid, e)
        r['index'] = i
        a, b = dict(r), dict(sc['records'][i])
        a.pop('wall_s')
        b.pop('wall_s')
        if s12.canon(json.loads(json.dumps(a, default=_jdefault))) != s12.canon(b):
            errs.append('stage 2 record %d differs on replay' % i)
    again = finish_preview()
    for k in ('stage2', 'verdicts', 'stage3', 'stage4', 'candidates'):
        if s12.canon(again.get(k)) != s12.canon(res.get(k)):
            errs.append('result %s differs when rebuilt' % k)
    for c in res.get('candidates', []):
        errs += verify_scene(w, g, c['scene'], full=False)
    if errs:
        raise SystemExit('CHECK FAILED: %s' % errs)
    print('result.json current: input pins, %d offline controls, %d digests (%d bulky, verified against the manifest), '
          '3 stage 2 replays, %d scenes verified; summaries and verdicts rebuilt equal'
          % (len(CHECK_CONTROLS), checked, len(man), len(res.get('candidates', []))))


def finish_preview_light():
    """The stage 3, stage 4 and candidate summaries of finish(), which need no bulky intermediate."""
    sets = [read_json(f) for f in sorted((CK / 'stage3').glob('set-*.json'), key=lambda p: int(p.stem.split('-')[1]))] \
        if (CK / 'stage3').exists() else []
    out = {'stage3': [{k: (v if k != 'scenes' else len(v)) for k, v in s_.items() if k != 'log'} |
                      {'log': {k: v for k, v in (s_.get('log') or {}).items() if k != 'rejected_scenes'}} for s_ in sets],
           'stage4': read_json(ck('stage4/log.json')) if ck('stage4/log.json').exists() else None}
    written = []
    for f in CAND.glob('scene-*.json') if CAND.exists() else ():
        written.append({'scene': int(f.stem.split('-')[1]), 'digest': read_json(f)['digest'], 'claimed': read_json(f)['claimed']})
    out['candidates'] = sorted(written, key=lambda x: x['scene'])
    return json.loads(json.dumps(out, default=_jdefault))


def finish_preview():
    """finish() without writing result.json."""
    global RESULT
    keep = RESULT
    tmp = CK / '.preview-result.json'
    RESULT = tmp
    try:
        out = finish()
    finally:
        RESULT = keep
        if tmp.exists():
            tmp.unlink()
    return json.loads(json.dumps(out, default=_jdefault))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--finish', action='store_true')
    ap.add_argument('--verify-scene', type=int)
    ap.add_argument('--full-replay', nargs=2)
    a = ap.parse_args()
    if a.full_replay:
        full_replay_child(*a.full_replay)
    elif a.run:
        drive()
    elif a.resume:
        drive(resume=True)
    elif a.finish:
        finish()
    elif a.check:
        check()
    elif a.verify_scene:
        w = s12.World()
        e = verify_scene(w, G15(w), a.verify_scene)
        print('scene %d: %s' % (a.verify_scene, 'verified' if not e else e))
        sys.exit(1 if e else 0)


if __name__ == '__main__':
    main()
