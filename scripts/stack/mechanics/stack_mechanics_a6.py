"""Attempt a6 of the ST-03 calculator: K on the fixing list ruled in DA-03 c2 against the movement limit of DS-72,
and the compliance map for the room study (DS-72 to DS-76, DS-81).

Model: the torsion-free grillage of attempt a5 (stack_mechanics_a5.Grillage), on the 2 mm grid, which is the coarsest
grid that puts every vertex of K's outline on a node (review finding 1). Fixings are pinned nodes; each one's snap onto
the grid is reported and two fixings on one node fail (review finding 2). The compliance under a push is an upper bound
on the plate's; the curvature strain under the uniform load is no bound and is pessimistic at the pinned nodes.
"""
from functools import lru_cache
import hashlib
import json
import math

import numpy as np

import stack_mechanics as sm
import stack_mechanics_a5 as a5
import stack_mechanics_geometry as geo

MAP_FILE = sm.ROOT / 'design/stack/mechanics/k-compliance-map.json'
NUMBER_WORDS = {2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six'}
POINT_LABELS = {'lower_left_corner': 'lower left corner', 'left_edge': 'left edge', 'above_post_rows': 'above the post rows',
                'upper_edge_middle': 'middle of the upper edge'}


def outline_step(outline):
    """Largest grid step (multiple of 0.001 mm) that puts every vertex of the outline on a node."""
    x0, y0 = min(p[0] for p in outline), min(p[1] for p in outline)
    g = 0
    for x, y in outline:
        g = math.gcd(g, int(round((x - x0) * 1000)), int(round((y - y0) * 1000)))
    return g / 1000


@lru_cache(maxsize=32)
def movement_for(outline, step, fixings, bending, cover, q, t, points, rows_y):
    gr = a5.grillage_for(outline, step, fixings, bending, cover)
    u = gr.uniform(q)
    w = np.abs(u[0::3])
    kap = gr.curvatures(u)
    k = int(np.argmax(w))
    above = gr.nodes[:, 1] < rows_y[0]
    ka = int(np.argmax(np.where(above, w, -np.inf))) if above.any() else None
    ks = int(np.argmax(kap))
    return {
        'nodes': len(gr.nodes), 'covers': gr.covers, 'snap_mm': list(gr.snap_mm),
        'max': {'w': float(w[k]), 'at': [float(v) for v in gr.nodes[k]]},
        'above_rows_max': {'w': float(w[ka]), 'at': [float(v) for v in gr.nodes[ka]]} if ka is not None else None,
        'points': {name: float(abs(gr.w_at(u, xy))) for name, xy in points},
        'strain': {'eps': float(kap[ks]) * t / 2, 'at': [float(v) for v in gr.nodes[ks]]},
    }


class A6:
    def __init__(self, c):
        self.c = c
        self.a5 = a5.A5(c)
        self.a3 = self.a5.a3
        self.g = c.g['a6']
        self.p = {k: v['value'] for k, v in c.d['parameters']['a6'].items()}
        self.bending = self.a5.flex * self.a5.p['grillage_stiffness_factor']
        self.outline = tuple(tuple(v) for v in self.g['k_outline'])
        self.step = self.p['grid_step_mm']
        self.lim = c.dv('strain_design_limit')
        self.hg = self.a3.p['handling_g']

    def fixings_xy(self, key):
        if key == 'a1':
            return self.a5.fixings_xy('list')
        return tuple(tuple(map(float, f['xy'])) for f in self.g['sets'][key]['fixings'])

    def fixing_ids(self, key):
        if key == 'a1':
            return [f['id'] for f in self.a5.g['fixings']]
        return [f['id'] for f in self.g['sets'][key]['fixings']]

    def grillage(self, key, step=None, cover=True):
        return a5.grillage_for(self.outline, step or self.step, self.fixings_xy(key), self.bending, cover)

    def post_rows(self, key):
        reg = self.a5.g['regions']['list'] if key == 'a1' else self.g['sets'][key]['regions']
        return tuple(reg['post_rows_y_mm'])

    def comparison_sets(self):
        """(key, label, changed sleeve id) for the ruled list, each reserve and each alternative of the fixing file, and the a1 list."""
        ruled = self.g['sets']['ruled']['fixings']
        kinds = [f['kind'] for f in ruled]
        out = [('ruled', f"Ruled list ({kinds.count('post')} posts, {len(kinds) - kinds.count('post')} sleeves)", None)]
        for r in self.g['reserve']:
            out.append(('ruled_plus_' + r['id'], f"Ruled list + reserve {r['id']} at ({r['xy'][0]:g}, {r['xy'][1]:g})", r['id']))
        for alt in self.g['alternatives']:
            old = [f['xy'] for f in ruled if f['id'] == alt['replaces']][0]
            out.append((alt['id'], f"{alt['replaces']} at ({alt['xy'][0]:g}, {alt['xy'][1]:g}) instead of ({old[0]:g}, {old[1]:g})", alt['id']))
        out.append(('a1', 'ST-08 a1 list (the a5 record)', None))
        return out

    def corner_label(self, xy):
        """A name per outline vertex that differs between vertices (review a6 finding 1)."""
        return {tuple(v): n for n, v in self.corners()}[tuple(map(float, xy))]

    def movement(self, key, step=None, cover=True):
        points = tuple((n, tuple(xy)) for n, xy in self.p['check_points_xy'].items())
        rows = self.post_rows(key)
        return movement_for(self.outline, step or self.step, self.fixings_xy(key), self.bending, cover,
                            self.a3.weight_pressure(self.hg), self.a5.t, points, rows)

    def passes(self, m):
        return m['max']['w'] <= self.p['movement_limit_mm'] and m['strain']['eps'] < self.lim

    def push_at(self, key, xy, step=None):
        """Deflection per newton at xy under a 1 N push spread bilinearly over the nodes of its cell, read back with the
        same nodes and weights (review a6 finding 7); a point outside the grid raises ValueError."""
        gr = self.grillage(key, step)
        load = np.zeros(gr.size)
        for k, wt in gr.bilinear(xy):
            load[3 * k] += wt
        return gr.w_at(gr.solve(load), xy)

    def sleeve_rows(self, key):
        return self.g['sets'][key]['sleeves']

    def corners(self):
        """K's outline vertices with a name; the notch corner is the re-entrant vertex."""
        pts = list(self.outline)
        n = len(pts)
        x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
        x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
        area2 = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
        named = {(x0, y0): 'upper left corner', (x1, y0): 'upper right corner', (x0, y1): 'lower left corner', (x1, y1): 'lower right corner'}
        out = []
        for i, v in enumerate(pts):
            a, b = pts[i - 1], pts[(i + 1) % n]
            cross = (v[0] - a[0]) * (b[1] - v[1]) - (v[1] - a[1]) * (b[0] - v[0])
            if cross * area2 < 0:
                name = 'notch corner'
            elif tuple(v) in named:
                name = named[tuple(v)]
            else:
                side = 'right' if v[0] == x1 else 'left' if v[0] == x0 else 'lower' if v[1] == y1 else 'upper' if v[1] == y0 else None
                name = f'notch corner on the {side} edge' if side else f'corner at ({v[0]:g}, {v[1]:g})'
            out.append((name, [float(v[0]), float(v[1])]))
        return out

    def map_corner_names(self):
        """Names as the retained map file carries them: the two convex notch vertices share 'outer notch corner'
        there and are told apart by their coordinates. Kept so that a rewrite of the map stays byte-identical."""
        return [('outer notch corner' if n.startswith(('notch corner on', 'corner at')) else n, xy) for n, xy in self.corners()]

    # compliance map -------------------------------------------------------------------------------------------
    def map_inputs(self):
        return {'fixing_file': self.g['fixing_file'], 'fixings_array_sha256': self.g['fixings_array_sha256'],
                'fixings': [[i, xy[0], xy[1]] for i, xy in zip(self.fixing_ids('ruled'), self.fixings_xy('ruled'))],
                'k_outline': [list(v) for v in self.outline], 'grid_step_mm': self.step, 'map_pitch_mm': self.p['map_pitch_mm'],
                'bending_stiffness_N_mm': round(self.bending, 6),
                'grillage_stiffness_factor': self.a5.p['grillage_stiffness_factor']}

    def map_nodes(self, gr):
        ratio = self.p['map_pitch_mm'] / gr.h
        if ratio < 1 - 1e-9 or abs(ratio - round(ratio)) > 1e-9:
            raise ValueError(f"map pitch {self.p['map_pitch_mm']} mm is not a whole positive multiple of the {gr.h} mm grid (review a6 finding 9)")
        pitch = int(round(ratio))
        on_outline = geo.boundary_dist_many(gr.nodes[:, 0], gr.nodes[:, 1], [list(v) for v in self.outline]) < 1e-9
        return sorted(k for (i, j), k in gr.idx.items() if (i % pitch == 0 and j % pitch == 0) or on_outline[k])

    def build_map(self):
        gr = self.grillage('ruled')
        sel = self.map_nodes(gr)
        comp = gr.point_compliance(sel)
        nodes = [[round(float(gr.nodes[k][0]), 3), round(float(gr.nodes[k][1]), 3), round(float(c), 5)] for k, c in zip(sel, comp)]
        inputs = self.map_inputs()
        doc = {
            'schema_version': 1, 'task': 'ST-03', 'attempt': 'a6', 'status': 'DERIVED',
            'note': ("Compliance of K under a 1 N push on its rear face at each node, fixings of the ruled list (DS-73 to DS-76) "
                     "as pinned nodes, torsion-free grillage of stack_mechanics_a5.Grillage on the 2 mm grid: an upper bound on "
                     "the plate on the ASSUMED plate model of the same run as the movement (DS-72). Nodes at the map pitch plus "
                     "every outline node of the 2 mm grid. Written by `stack_mechanics.py --write-map`; nothing measured. "
                     "Not the gate file of ST-02: the connector places are not final"),
            'inputs': inputs,
            'inputs_sha256': inputs_sha256(inputs),
            'columns': ['x_mm', 'y_mm', 'mm_per_N'],
            'thresholds': map_regions(nodes, self.p['map_pitch_mm'], (gr.x0, gr.y0),
                                      [(self.p['compliance_hold_edge_mm_per_N'], 'DS-72: the other hand holds K\'s edge beside the connector'),
                                       (self.p['compliance_not_placed_mm_per_N'], 'DS-72: no K connector is placed')]),
            'corners': [{'name': n, 'xy': xy, 'mm_per_N': node_value(nodes, xy)} for n, xy in self.map_corner_names()],
            'nodes': nodes,
        }
        return doc


def node_value(nodes, xy):
    for x, y, c in nodes:
        if abs(x - xy[0]) < 1e-6 and abs(y - xy[1]) < 1e-6:
            return c
    return None


def inputs_sha256(inputs):
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def map_regions(nodes, pitch, origin, thresholds):
    """Connected regions of map nodes above each threshold (8-neighbours at the map pitch or closer), as boxes.
    The area counts the nodes on the map lattice through the grid origin, times pitch²."""
    ox, oy = origin
    out = []
    for limit, rule in thresholds:
        above = [(x, y, c) for x, y, c in nodes if c > limit]
        key = {(round(x * 2), round(y * 2)): n for n, (x, y, _) in enumerate(above)}
        parent = list(range(len(above)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        reach = [d for d in range(-int(2 * pitch), int(2 * pitch) + 1)]
        for n, (x, y, _) in enumerate(above):
            for dx in reach:
                for dy in reach:
                    m = key.get((round(x * 2) + dx, round(y * 2) + dy))
                    if m is not None:
                        parent[find(m)] = find(n)
        groups = {}
        for n in range(len(above)):
            groups.setdefault(find(n), []).append(above[n])
        regions = []
        for pts in groups.values():
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            peak = max(pts, key=lambda p: p[2])
            lattice = sum(1 for x, y, _ in pts if abs((x - ox) / pitch - round((x - ox) / pitch)) < 1e-9
                          and abs((y - oy) / pitch - round((y - oy) / pitch)) < 1e-9)
            regions.append({'box_mm': [min(xs), min(ys), max(xs), max(ys)], 'nodes': len(pts),
                            'area_mm2_approx': lattice * pitch * pitch, 'peak': {'xy': [peak[0], peak[1]], 'mm_per_N': peak[2]}})
        regions.sort(key=lambda r: (r['box_mm'][1], r['box_mm'][0]))
        out.append({'mm_per_N': limit, 'rule': rule, 'nodes': len(above),
                    'area_mm2_approx': sum(r['area_mm2_approx'] for r in regions), 'regions': regions})
    return out


def write_map(c, path=None):
    doc = A6(c).build_map()
    nodes = doc.pop('nodes')
    doc['nodes'] = '__NODES__'
    text = json.dumps(doc, indent=1, ensure_ascii=False)
    rows = ',\n'.join('  ' + json.dumps(n, separators=(',', ':')) for n in nodes)
    (path or MAP_FILE).write_text(text.replace('"__NODES__"', '[\n' + rows + '\n ]') + '\n')


def load_map():
    return json.loads(MAP_FILE.read_text())


def map_is_current(a, mp):
    """The retained map belongs to the current model when its recorded inputs hash to the current inputs (review a6 finding 5)."""
    current = inputs_sha256(a.map_inputs())
    return mp.get('inputs_sha256') == current and inputs_sha256(mp.get('inputs', {})) == current


def stale_note(a, mp):
    return (f"### The compliance map is stale: its inputs (SHA256 {str(mp.get('inputs_sha256'))[:12]}…) differ from the current model "
            f"({inputs_sha256(a.map_inputs())[:12]}…); no map figure is published until `stack_mechanics.py --write-map` rewrites it")


def dropped_strips(outline, step):
    """Strips of the outline between an off-grid axis-parallel edge and the last node line inside it."""
    pts = [tuple(map(float, v)) for v in outline]
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        if a[0] == b[0]:
            axis, other, c, orig, lo, hi = 'x', 'y', a[0], x0, min(a[1], b[1]), max(a[1], b[1])
        elif a[1] == b[1]:
            axis, other, c, orig, lo, hi = 'y', 'x', a[1], y0, min(a[0], b[0]), max(a[0], b[0])
        else:
            out.append(f'the edge ({a[0]:g}, {a[1]:g}) to ({b[0]:g}, {b[1]:g}) lies on no grid line')
            continue
        off = (c - orig) / step
        if abs(off - round(off)) < 1e-9:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        probe = (mid[0] - 1e-3, mid[1]) if axis == 'x' else (mid[0], mid[1] - 1e-3)
        line = orig + step * (math.floor(off) if geo.inside(probe, pts) else math.ceil(off))
        out.append(f'{axis} = {min(line, c):g} to {max(line, c):g} for {other} = {lo:g} to {hi:g}')
    return out


def cover_label(outline, step, covers):
    return 'yes' if covers else 'no: drops ' + '; '.join(dropped_strips(outline, step))


def f3(x):
    return f'{x:.3f}'


def f2(x):
    return f'{x:.2f}'


def verdict(ok):
    return 'within' if ok else 'exceeds'


def peak_cell(r):
    return f"{f3(r['w'])} at {r['at']}" if r else 'n/a (no node above the post rows)'


def peak_ok(r, lim):
    return r is None or r['w'] <= lim


# renderers -----------------------------------------------------------------------------------------------------
def render_a6_movement(c):
    a = A6(c)
    m = a.movement('ruled')
    auth = a.p['authority_figures']
    am = auth['movement_mm']
    lim_w = a.p['movement_limit_mm']
    pts = a.p['check_points_xy']
    rows = [['Largest anywhere on K', f"{f3(m['max']['w'])} at {m['max']['at']}", f"{am['max']:.2f} at the lower left corner", verdict(m['max']['w'] <= lim_w)]]
    for name in ('lower_left_corner', 'left_edge'):
        rows.append([f'At {tuple(pts[name])} ({POINT_LABELS[name]})', f3(m['points'][name]), f"{am[name]:.2f}", verdict(m['points'][name] <= lim_w)])
    rows.append(['Largest above the post rows', peak_cell(m['above_rows_max']), f"{am['above_post_rows_max']:.2f}",
                 verdict(peak_ok(m['above_rows_max'], lim_w))])
    for name in ('above_post_rows', 'upper_edge_middle'):
        rows.append([f'At {tuple(pts[name])} ({POINT_LABELS[name]})', f3(m['points'][name]), f"{am[name]:.2f}", verdict(m['points'][name] <= lim_w)])
    s4 = a.a5.p['grillage_step_mm']
    m4 = a.movement('ruled', step=s4, cover=False)
    four = [f"{f3(m4['max']['w'])} at {m4['max']['at']}", f3(m4['points']['lower_left_corner']), f3(m4['points']['left_edge']),
            peak_cell(m4['above_rows_max']), f3(m4['points']['above_post_rows']), f3(m4['points']['upper_edge_middle'])]
    for row, cell in zip(rows, four):
        row.insert(2, cell)
    rows.append([f'Strain, largest (grillage curvature, no bound)', f"{sm.ue(m['strain']['eps'])} microstrain at {m['strain']['at']}",
                 f"{sm.ue(m4['strain']['eps'])} microstrain at {m4['strain']['at']}", f"{auth['strain_microstrain_4mm_grid']} microstrain on the 4 mm grid",
                 'below' if m['strain']['eps'] < a.lim else 'not below'])
    ok = a.passes(m)
    head = (f"### DS-72 is met on the ruled list: K moves at most {f2(m['max']['w'])} mm under {a.hg:g} g at {tuple(m['max']['at'])} against "
            f"{lim_w} mm, and the strain figure is {sm.ue(m['strain']['eps'])} against {a.lim * 1e6:.0f} microstrain" if ok else
            f"### DS-72 is not met on the ruled list: {f2(m['max']['w'])} mm at {tuple(m['max']['at'])}, strain {sm.ue(m['strain']['eps'])} microstrain (NEEDS_DESIGN)")
    covers4 = 'covers K' if m4['covers'] else 'does not cover K'
    return head + '\n\n' + sm.table([f'Figure ({a.hg:g} g)', f'This run, {a.step:g} mm grid of record, mm', f'Same run on the {s4:g} mm grid ({covers4}), mm',
                                     "Authority's scratch figure, mm",
                                     f'Against {lim_w} mm / {a.lim * 1e6:.0f} microstrain'], rows)


def render_a6_grids(c):
    a = A6(c)
    lim_w = a.p['movement_limit_mm']
    rows = []
    out = {}
    s4, s1 = a.a5.p['grillage_step_mm'], a.p['snap_check_step_mm']
    for step, cover in ((s4, False), (a.step, True), (s1, True)):
        m = a.movement('ruled', step=step, cover=cover)
        out[step] = m
        rows.append([f'{step:g}', cover_label(a.outline, step, m['covers']), m['nodes'],
                     f"{max(m['snap_mm']):.3f}", f"{f3(m['max']['w'])} at {m['max']['at']}", f3(m['points']['left_edge']),
                     peak_cell(m['above_rows_max']), sm.ue(m['strain']['eps'])])
    m2, m1 = out[a.step], out[s1]
    within = [m['max']['w'] <= lim_w for m in (m1, m2)]
    word = 'both within' if all(within) else 'neither within' if not any(within) else (
        f'only the {s1:g} mm grid within' if within[0] else f'only the {a.step:g} mm grid within')
    head = (f"### The snap moves the largest movement by {f3(m1['max']['w'] - m2['max']['w'])} mm: {f3(m1['max']['w'])} mm on the {s1:g} mm grid against "
            f"{f3(m2['max']['w'])} mm on the {a.step:g} mm grid of record, {word} {lim_w} mm; the strain figure rises to "
            f"{sm.ue(m1['strain']['eps'])} microstrain at the pins")
    return head + '\n\n' + sm.table(['Grid step, mm', "Covers K's outline", 'Nodes', 'Largest fixing snap, mm', f'Largest movement {a.hg:g} g, mm',
                                     f"At {tuple(a.p['check_points_xy']['left_edge'])}, mm", 'Largest above the post rows, mm',
                                     'Strain figure, microstrain'], rows)


def render_a6_snaps(c):
    a = A6(c)
    m2, m1 = a.movement('ruled'), a.movement('ruled', step=a.p['snap_check_step_mm'])
    rows = [[i, f'({xy[0]:g}, {xy[1]:g})', f'{s2:.3f}', f'{s1:.3f}'] for i, xy, s2, s1 in
            zip(a.fixing_ids('ruled'), a.fixings_xy('ruled'), m2['snap_mm'], m1['snap_mm'])]
    moved = sum(1 for s in m2['snap_mm'] if s > 1e-9)
    s1 = a.p['snap_check_step_mm']
    head = (f"### {moved} of {len(rows)} fixings move onto the {a.step:g} mm grid, by at most {max(m2['snap_mm']):.3f} mm; no two share a node")
    return head + '\n\n' + sm.table(['Fixing', 'Site', f'Snap on the {a.step:g} mm grid, mm', f'Snap on the {s1:g} mm grid, mm'], rows)


def render_a6_sleeves(c):
    a = A6(c)
    err = a.a5.p['sleeve_error_mm']
    auth = a.p['authority_figures']['sleeve_strain_microstrain_worst_case']
    rows = []
    worst = 0.0
    for s in a.sleeve_rows('ruled'):
        e2, e5 = c.strain(err['printer'], s['span_mm']), c.strain(err['worst_case'], s['span_mm'])
        worst = max(worst, e5)
        rows.append([s['id'], f"{s['nearest_other_fixing']} {s['span_mm']:.1f}", sm.ue(e2), sm.ue(e5), auth.get(s['id'], ''), verdict(e5 <= a.lim)])
    head = (f"### The {NUMBER_WORDS.get(len(rows), str(len(rows)))} sleeves stay below {a.lim * 1e6:.0f} microstrain: at most {sm.ue(worst)} at the {err['worst_case']} mm worst case"
            if worst <= a.lim else f"### A sleeve exceeds {a.lim * 1e6:.0f} microstrain: {sm.ue(worst)} (NEEDS_DESIGN)")
    return head + '\n\n' + sm.table(['Sleeve', 'Nearest other fixing, span mm', f"Strain at ±{err['printer']} mm, microstrain",
                                     f"Strain at {err['worst_case']} mm (worst case), microstrain", "Authority's figure at the worst case",
                                     f'Against {a.lim * 1e6:.0f}'], rows)


def render_a6_compare(c):
    a = A6(c)
    err = a.a5.p['sleeve_error_mm']['worst_case']
    rule = a.a5.p['sleeve_clamp_rule_mm']
    pts = a.p['check_points_xy']
    sets = a.comparison_sets()
    rows = []
    for key, label, changed in sets:
        m = a.movement(key)
        sleeve = ''
        if changed:
            fx = a.g['sets'][key]['fixings']
            s = [r for r in a.sleeve_rows(key) if r['id'] == changed][0]
            site = [f['xy'] for f in fx if f['id'] == changed][0]
            close = sorted(geo_dist(f['xy'], site) for f in fx if f['id'] != changed and geo_dist(f['xy'], site) < rule)
            sleeve = (f"{s['id']}: {s['nearest_other_fixing']} {s['span_mm']:.2f} mm, {sm.ue(c.strain(err, s['span_mm']))} microstrain; "
                      + (f"inside the {rule:g} mm rule at {', '.join(f'{d:.2f}' for d in close)} mm" if close else f'no fixing within {rule:g} mm'))
        rows.append([label, f"{f3(m['max']['w'])} at {m['max']['at']}", f3(m['points']['lower_left_corner']), f3(m['points']['left_edge']),
                     peak_cell(m['above_rows_max']), f3(m['points']['above_post_rows']),
                     f3(m['points']['upper_edge_middle']), sm.ue(m['strain']['eps']), sleeve, verdict(a.passes(m))])
    ok = all(a.passes(a.movement(k)) for k, _, _ in sets)
    worst = max(sets, key=lambda kl: a.movement(kl[0])['max']['w'])
    broken = [r[0] for r in rows if 'inside the' in r[8]]
    head = (f"### {'Every comparison set meets' if ok else 'Not every comparison set meets'} DS-72 as well, at most "
            f"{f2(a.movement(worst[0])['max']['w'])} mm ({worst[1]}); none is selected"
            + (f", and {'; '.join(broken)} breaks the {rule:g} mm sleeve rule" if broken else ''))
    at = lambda name: f'At {tuple(pts[name])}, mm'
    return head + '\n\n' + sm.table([f'Fixings ({a.step:g} mm grid, {a.hg:g} g)', 'Largest, mm', at('lower_left_corner'), at('left_edge'),
                                     'Largest above the post rows, mm', at('above_post_rows'), at('upper_edge_middle'), 'Strain figure, microstrain',
                                     f'Changed sleeve: nearest fixing, strain at {err} mm, {rule:g} mm rule', 'DS-72'], rows)


def geo_dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def render_a6_compliance(c):
    a = A6(c)
    mp = load_map()
    if not map_is_current(a, mp):
        return stale_note(a, mp)
    auth = a.p['authority_figures']['compliance_mm_per_N']
    before = {tuple(xy): a.push_at('a1', xy) for _, xy in a.corners()}
    rows = []
    for k in mp['corners']:
        label = a.corner_label(k['xy'])
        note = ''
        if label.startswith('upper'):
            note = f"{auth['upper_corners']} (before: {auth['upper_corners_before']})"
        elif label == 'lower left corner':
            note = f"{auth['lower_left_corner_a5']} in a5 (ST-08 a1 list, {a.a5.p['grillage_step_mm']:g} mm grid)"
        rows.append([label, f"({k['xy'][0]:g}, {k['xy'][1]:g})", f3(k['mm_per_N']), f3(before[tuple(map(float, k['xy']))]), note])
    pts = a.p['compliance_points_xy']
    auth_pts = {'P-K-P-L06.02': auth['P-K-P-L06.02 (15.5, 234)'], 'link centre': auth['link centre (31.5, 283)']}
    for name, xy in pts.items():
        rows.append([name, f'({xy[0]:g}, {xy[1]:g})', f3(a.push_at('ruled', xy)), f3(a.push_at('a1', xy)), f'{auth_pts[name]}'])
    table1 = sm.table(['Place', 'Site', f'Ruled list, mm/N ({a.step:g} mm grid)', f'ST-08 a1 list, mm/N ({a.step:g} mm grid)', "Authority's figure, mm/N"], rows)
    rows2 = []
    for t in mp['thresholds']:
        boxes = '; '.join(f"x {r['box_mm'][0]:g}–{r['box_mm'][2]:g}, y {r['box_mm'][1]:g}–{r['box_mm'][3]:g} ({r['nodes']} nodes, peak {f3(r['peak']['mm_per_N'])} at "
                          f"({r['peak']['xy'][0]:g}, {r['peak']['xy'][1]:g}))" for r in t['regions'])
        rows2.append([f"above {t['mm_per_N']}", t['rule'], t['nodes'], f"{t['area_mm2_approx']:.0f}", len(t['regions']), boxes])
    table2 = sm.table(['Compliance, mm/N', 'Rule', 'Map nodes', 'Area, mm² (map-pitch nodes × pitch²)', 'Regions', 'Boxes'], rows2)
    top = max(k['mm_per_N'] for k in mp['corners'])
    t1 = [t for t in mp['thresholds'] if t['mm_per_N'] == a.p['compliance_not_placed_mm_per_N']][0]
    head = (f"### The corners are soft: up to {f2(top)} mm/N at a corner, and {len(t1['regions'])} regions of about {t1['area_mm2_approx']:.0f} mm² "
            f"lie above 1.0 mm/N, where DS-72 places no K connector")
    intro = (f"The map is retained in [`k-compliance-map.json`](k-compliance-map.json): {len(mp['nodes'])} nodes (x, y, mm/N) at a "
             f"{mp['inputs']['map_pitch_mm']:g} mm pitch on the {mp['inputs']['grid_step_mm']:g} mm grid, plus every outline node, with the regions and "
             f"corners below. It is an upper bound on the same model as the movement; ST-02's gate file is not pinned.")
    return head + '\n\n' + intro + '\n\n' + table1 + '\n\n' + table2


def render_a6_head(c):
    a = A6(c)
    m = a.movement('ruled')
    mp = load_map()
    if not map_is_current(a, mp):
        tail = 'and the compliance map is stale'
    else:
        t1 = [t for t in mp['thresholds'] if t['mm_per_N'] == a.p['compliance_not_placed_mm_per_N']][0]
        tail = f"and {len(t1['regions'])} corner regions lie above 1.0 mm/N"
    if a.passes(m):
        return (f"## Attempt a6 (DONE): on the ruled list K moves at most {f2(m['max']['w'])} mm under {a.hg:g} g against DS-72's "
                f"{a.p['movement_limit_mm']} mm, the strain figure is {sm.ue(m['strain']['eps'])} against {a.lim * 1e6:.0f} microstrain, {tail}")
    return (f"## Attempt a6 (NEEDS_DESIGN): on the ruled list K moves {f2(m['max']['w'])} mm at {tuple(m['max']['at'])} against "
            f"{a.p['movement_limit_mm']} mm, strain figure {sm.ue(m['strain']['eps'])} microstrain")


def render_a6_terms(c):
    rows = []
    for name, t in c.d['parameters']['a6'].items():
        basis = t.get('locator') or t.get('formula') or ('to source: ' + t.get('to_source', ''))
        src = t.get('source', '')
        rows.append([f'`a6.{name}`', json.dumps(t['value'], ensure_ascii=False).replace('|', '/'), t['status'], (f'{src}: ' if src else '') + basis.replace('|', '/')])
    return sm.table(['Parameter', 'Value', 'Status', 'Source, formula or what would source it'], rows)


RENDERERS = {
    'a6_head': render_a6_head, 'a6_movement': render_a6_movement, 'a6_grids': render_a6_grids, 'a6_snaps': render_a6_snaps, 'a6_sleeves': render_a6_sleeves,
    'a6_compare': render_a6_compare, 'a6_compliance': render_a6_compliance, 'a6_terms': render_a6_terms,
}
