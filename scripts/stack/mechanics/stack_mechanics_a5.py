"""Attempt a5 of the ST-03 calculator: K on the fixing list of ST-08 (DS-66, DS-67, DS-70).

Model: a torsion-free grillage of Euler-Bernoulli beams on a square grid over K's outline, each beam with the
stiffness D (1 - nu) of its tributary width. For every displacement field its strain energy is at most the plate's,
so its compliance bounds the plate's: the deflection under a single point load is an upper bound, and under the
uniform load the load-weighted mean deflection is. Fixings are pinned nodes (a clamped sleeve or post holds more).
The cantilever strip of attempt a4 is shown beside it as the screen it was.
"""
from functools import lru_cache
import json
import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

import stack_mechanics as sm
import stack_mechanics_a3 as a3
import stack_mechanics_geometry as geo

SETS = (('posts_only', '18 posts only'), ('list', 'ST-08 list (18 posts, 5 sleeves)'),
        ('list_plus_one', 'list + one hypothetical fixing at the left edge'))
REGIONS = (('y_low', 'from the post rows to the edge at y = 8'), ('band', 'between the post rows'),
           ('y_high', 'from the post rows to the edge at y = 292'))


class MergedFixings(ValueError):
    """Two fixings snap to the same grid node (review finding 2)."""


def nested_dissection(ij, ids, leaf=64):
    """Grid nested-dissection order: halves first, the separating grid line last (keeps the factor sparse)."""
    if len(ids) <= leaf:
        return list(ids)
    sub = ij[ids]
    ax = 0 if np.ptp(sub[:, 0]) >= np.ptp(sub[:, 1]) else 1
    mid = int(np.median(sub[:, ax]))
    return (nested_dissection(ij, ids[sub[:, ax] < mid], leaf) + nested_dissection(ij, ids[sub[:, ax] > mid], leaf)
            + list(ids[sub[:, ax] == mid]))


class Grillage:
    def __init__(self, outline, step, fixings_xy, bending, require_cover=True):
        self.outline, self.h = outline, step
        self.fixings_xy, self.bending = tuple(tuple(map(float, p)) for p in fixings_xy), bending
        x0, y0, x1, y1 = geo.bbox(outline)
        self.x0, self.y0 = x0, y0
        nx, ny = int(round((x1 - x0) / step)), int(round((y1 - y0) / step))
        self.covers = all(abs((vx - x0) / step - round((vx - x0) / step)) < 1e-9 and abs((vy - y0) / step - round((vy - y0) / step)) < 1e-9
                          for vx, vy in outline)
        if require_cover and not self.covers:
            raise ValueError(f'a {step} mm grid does not cover the outline exactly (review finding 1)')
        px, py, _ = geo.grid(outline, step)
        ii = np.rint((px - x0) / step).astype(int)
        jj = np.rint((py - y0) / step).astype(int)
        order = np.lexsort((ii, jj))
        ii, jj = ii[order], jj[order]
        grid_idx = -np.ones((ny + 3, nx + 3), dtype=int)
        grid_idx[jj + 1, ii + 1] = np.arange(len(ii))
        self.grid_idx = grid_idx
        self.idx = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(ii, jj))}
        n = len(ii)
        self.nodes = np.column_stack((x0 + ii * step, y0 + jj * step)).astype(float)
        h = step
        ok = grid_idx >= 0
        beams_a, beams_b, beams_rot, widths = [], [], [], []
        for rot, (di, dj) in ((1, (1, 0)), (2, (0, 1))):
            a = grid_idx[1:-1, 1:-1]
            b = np.roll(np.roll(grid_idx, -dj, axis=0), -di, axis=1)[1:-1, 1:-1]
            if rot == 1:
                side1 = ok & np.roll(ok, -1, axis=1)
                up = np.roll(side1, -1, axis=0)[1:-1, 1:-1]
                down = np.roll(side1, 1, axis=0)[1:-1, 1:-1]
            else:
                side1 = ok & np.roll(ok, -1, axis=0)
                up = np.roll(side1, -1, axis=1)[1:-1, 1:-1]
                down = np.roll(side1, 1, axis=1)[1:-1, 1:-1]
            width = h / 2 * (up.astype(float) + down.astype(float))
            sel = (a >= 0) & (b >= 0) & (width > 0)
            beams_a.append(a[sel]); beams_b.append(b[sel]); beams_rot.append(np.full(sel.sum(), rot)); widths.append(width[sel])
        a = np.concatenate(beams_a); b = np.concatenate(beams_b); rot = np.concatenate(beams_rot); width = np.concatenate(widths)
        order = np.lexsort((rot, a))
        a, b, rot, width = a[order], b[order], rot[order], width[order]
        self.beams = np.column_stack((a, b, rot))
        kel = np.array([[12, 6 * h, -12, 6 * h], [6 * h, 4 * h * h, -6 * h, 2 * h * h],
                        [-12, -6 * h, 12, -6 * h], [6 * h, 2 * h * h, -6 * h, 4 * h * h]]) / h ** 3
        dofs = np.column_stack((3 * a, 3 * a + rot, 3 * b, 3 * b + rot))
        rows = np.repeat(dofs, 4, axis=1).ravel()
        cols = np.tile(dofs, (1, 4)).ravel()
        vals = (bending * width)[:, None] * kel.ravel()[None, :]
        size = 3 * n
        kmat = coo_matrix((vals.ravel(), (rows, cols)), shape=(size, size)).tocsc()
        kmat = kmat + coo_matrix((np.full(size, 1e-9 * bending), (np.arange(size), np.arange(size))), shape=(size, size)).tocsc()
        cell = ok & np.roll(ok, -1, axis=0) & np.roll(ok, -1, axis=1) & np.roll(np.roll(ok, -1, axis=0), -1, axis=1)
        area = np.zeros(n)
        for dj, di in ((0, 0), (1, 0), (0, 1), (1, 1)):
            c = np.roll(np.roll(cell, dj, axis=0), di, axis=1)[1:-1, 1:-1]
            g = grid_idx[1:-1, 1:-1]
            m = c & (g >= 0)
            np.add.at(area, g[m], h * h / 4)
        self.area = area
        for xy in fixings_xy:
            if not geo.inside(xy, outline):
                raise ValueError(f'fixing at {tuple(xy)} lies outside the outline (review a6 finding 6)')
        self.fixed_nodes = [self.nearest(xy) for xy in fixings_xy]
        self.snap_mm = [float(np.hypot(*(self.nodes[k] - np.array(xy, float)))) for k, xy in zip(self.fixed_nodes, fixings_xy)]
        self.snap_bound_mm = step / math.sqrt(2)
        for xy, snap in zip(fixings_xy, self.snap_mm):
            if snap > self.snap_bound_mm + 1e-9:
                raise ValueError(f'fixing at {tuple(xy)} snaps {snap:.3f} mm, more than half a cell diagonal ({self.snap_bound_mm:.3f} mm)')
        if len(set(self.fixed_nodes)) != len(self.fixed_nodes):
            raise MergedFixings('two fixings share a grid node')
        fixed = sorted(3 * k for k in self.fixed_nodes)
        free = np.setdiff1d(np.arange(size), fixed)
        order = np.array(nested_dissection(np.column_stack((ii, jj)), np.arange(n)), dtype=int)
        dof = (3 * order[:, None] + np.arange(3)[None, :]).ravel()
        is_free = np.zeros(size, bool); is_free[free] = True
        self.free = dof[is_free[dof]]
        self.size = size
        self.lu = splu(kmat[self.free][:, self.free].tocsc(), permc_spec='NATURAL', diag_pivot_thresh=0.0,
                       options=dict(SymmetricMode=True))

    def point_compliance(self, nodes, chunk=100):
        """Deflection per newton at each node under a unit push at that node (one column per node)."""
        pos = -np.ones(self.size, dtype=int)
        pos[self.free] = np.arange(len(self.free))
        nodes = np.asarray(nodes, dtype=int)
        out = np.zeros(len(nodes))
        for s in range(0, len(nodes), chunk):
            part = nodes[s:s + chunk]
            rows = pos[3 * part]
            live = np.flatnonzero(rows >= 0)
            if not len(live):
                continue
            rhs = np.zeros((len(self.free), len(live)))
            rhs[rows[live], np.arange(len(live))] = 1.0
            x = self.lu.solve(rhs)
            out[s + live] = x[rows[live], np.arange(len(live))]
        return out

    def nearest(self, xy):
        return int(np.argmin(np.hypot(self.nodes[:, 0] - xy[0], self.nodes[:, 1] - xy[1])))

    def solve(self, load):
        u = np.zeros(self.size)
        u[self.free] = self.lu.solve(load[self.free])
        return u

    def uniform(self, q):
        load = np.zeros(self.size)
        load[0::3] = q * self.area
        return self.solve(load)

    def point(self, node, force):
        load = np.zeros(self.size)
        load[3 * node] = force
        return self.solve(load)

    def bilinear(self, xy):
        """Nodes and bilinear weights of the cell around xy; every node with a non-zero weight must exist."""
        fi, fj = (xy[0] - self.x0) / self.h, (xy[1] - self.y0) / self.h
        i0, j0 = int(math.floor(fi + 1e-9)), int(math.floor(fj + 1e-9))
        tx, ty = max(0.0, fi - i0), max(0.0, fj - j0)
        out = []
        for (di, dj), wt in (((0, 0), (1 - tx) * (1 - ty)), ((0, 1), (1 - tx) * ty), ((1, 0), tx * (1 - ty)), ((1, 1), tx * ty)):
            if wt > 1e-12:
                k = self.idx.get((i0 + di, j0 + dj))
                if k is None:
                    raise ValueError(f'{tuple(xy)} is not inside a cell of the grid: node {tuple(self.nodes_xy(i0 + di, j0 + dj))} is missing')
                out.append((k, wt))
        return out

    def nodes_xy(self, i, j):
        return [self.x0 + i * self.h, self.y0 + j * self.h]

    def w_at(self, u, xy):
        """Bilinear deflection at xy from the same nodes and weights that bilinear() gives a load."""
        return float(sum(wt * u[3 * k] for k, wt in self.bilinear(xy)))

    def curvatures(self, u):
        """Largest end curvature of the beams at each node (numpy, one value per node)."""
        h = self.h
        a, b, rot = self.beams[:, 0], self.beams[:, 1], self.beams[:, 2]
        w1, t1, w2, t2 = u[3 * a], u[3 * a + rot], u[3 * b], u[3 * b + rot]
        k1 = np.abs(-6 * w1 - 4 * h * t1 + 6 * w2 - 2 * h * t2) / h ** 2
        k2 = np.abs(6 * w1 + 2 * h * t1 - 6 * w2 + 4 * h * t2) / h ** 2
        out = np.zeros(len(self.nodes))
        np.maximum.at(out, a, k1)
        np.maximum.at(out, b, k2)
        return out

    def boundary_nodes(self):
        out = []
        for (i, j), a in self.idx.items():
            if not all((i + di, j + dj) in self.idx for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.append(a)
        return out


class A5:
    def __init__(self, c):
        self.c = c
        self.a3 = a3.A3(c)
        self.g = c.g['a5']
        self.p = {k: v['value'] for k, v in c.d['parameters']['a5'].items()}
        e, nu, self.t, self.flex = self.a3.plate()

    def fixings_xy(self, key):
        fx = self.g['fixings']
        if key == 'posts_only':
            return tuple(tuple(f['xy']) for f in fx if f['kind'] == 'post')
        pts = tuple(tuple(f['xy']) for f in fx)
        if key == 'list_plus_one':
            pts += (tuple(self.p['hypothetical_fixing_xy']),)
        return pts

    def grillage(self, key, step=None):
        step = step or self.p['grillage_step_mm']
        # the a5 record ran on a 4 mm grid that drops a 2 mm strip at x 312-314 and at the notch (review finding 1)
        return grillage_for(tuple(map(tuple, self.g['k_outline'])), step, self.fixings_xy(key),
                            self.flex * self.p['grillage_stiffness_factor'], False)

    def region_of(self, y):
        rows = self.g['regions']['posts_only']['post_rows_y_mm']
        return 'y_low' if y < rows[0] else ('y_high' if y > rows[-1] else 'band')

    def uniform_summary(self, key, g_level, step=None):
        gr = self.grillage(key, step)
        u = gr.uniform(self.a3.weight_pressure(g_level))
        w = u[0::3]
        out = {}
        for reg, _ in REGIONS:
            mask = np.array([self.region_of(y) == reg for y in gr.nodes[:, 1]])
            n = int(np.argmax(np.where(mask, np.abs(w), -1)))
            kap = gr.curvatures(u)
            out[reg] = {'w': float(abs(w[n])), 'at': [float(v) for v in gr.nodes[n]], 'eps': float(np.max(kap[mask])) * self.t / 2}
        n = int(np.argmax(np.abs(w)))
        out['max'] = {'w': float(abs(w[n])), 'at': [float(v) for v in gr.nodes[n]]}
        out['points'] = [float(abs(gr.w_at(u, xy))) for xy in self.p['far_points_xy']]
        return out

    def strip_w(self, g_level, span):
        return self.a3.edge_uniform(self.a3.weight_pressure(g_level), span)

    def compliance(self, key, node_xy=None, node=None):
        """Deflection per newton at the load point under a unit push (grillage: an upper bound)."""
        gr = self.grillage(key)
        n = gr.nearest(node_xy) if node is None else node
        return float(gr.point(n, 1.0)[3 * n]), [float(v) for v in gr.nodes[n]]

    def compliance_scan(self, key):
        gr = self.grillage(key)
        return compliance_scan_for(self, key, tuple(gr.boundary_nodes()))

    def cut_lower_bound(self, key, load_xy):
        """Equilibrium bound: across any straight cut that leaves every fixing on one side, the mean moment per
        width is P d / l; the peak is at least that. Returns (strain per newton, d, l, angle)."""
        fx = np.array(self.fixings_xy(key), dtype=float)
        outline = self.g['k_outline']
        best = (0.0, None, None, None)
        for deg in range(0, 360, CUT_ANGLE_STEP_DEG):
            n = np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])
            offset = float(np.max(fx @ n))
            d = float(np.dot(load_xy, n)) - offset
            if d <= 0:
                continue
            length = chord_length(outline, n, offset)
            if length <= 0:
                continue
            m = d / length
            if m > best[0]:
                best = (m, d, length, deg)
        m, d, length, deg = best
        if deg is None:
            return None, None, None, None   # no straight cut leaves every fixing on one side: the bound does not apply
        return self.a3.strain_cylindrical(m), d, length, deg

    def a4_push_strain(self):
        """a4 free-edge push model: the strain per newton does not depend on the span."""
        return self.a3.edge_point(1.0, self.g['regions']['list']['farthest']['span_mm'])[1]


CUT_ANGLE_STEP_DEG = 1  # angle step of the straight-cut search


def chord_length(poly, n, offset):
    """Length of the line {p : p . n = offset} inside the polygon."""
    t = np.array([-n[1], n[0]])
    params = []
    for i in range(len(poly)):
        a, b = np.array(poly[i], float), np.array(poly[(i + 1) % len(poly)], float)
        da, db = a @ n - offset, b @ n - offset
        if (da > 0) != (db > 0) and da != db:
            q = a + (b - a) * (da / (da - db))
            params.append(float(q @ t))
    params.sort()
    return sum(params[i + 1] - params[i] for i in range(0, len(params) - 1, 2))


GRILLAGE_CACHE_SIZE = 6   # a 2 mm factor of K holds about 9 million non-zeros; keep only the latest few models


@lru_cache(maxsize=GRILLAGE_CACHE_SIZE)
def _grillage(outline, step, fixings_xy, bending):
    return Grillage([list(p) for p in outline], step, fixings_xy, bending, require_cover=False)


def grillage_for(outline, step, fixings_xy, bending, require_cover=True):
    """One cached model per (outline, step, fixings, bending); the cover check is applied to it, not part of its key."""
    gr = _grillage(outline, step, tuple(tuple(map(float, p)) for p in fixings_xy), bending)
    if require_cover and not gr.covers:
        raise ValueError(f'a {step} mm grid does not cover the outline exactly (review finding 1)')
    return gr


def clear_grillages():
    _grillage.cache_clear()


_SCAN = {}


def compliance_scan_for(a, key, nodes):
    """Largest compliance over the given nodes. Keyed by the whole grillage identity (outline, step, fixings, bending)
    and the nodes, so that a change of any model input recomputes (review finding 4)."""
    gr = a.grillage(key)
    cache_key = (tuple(map(tuple, gr.outline)), gr.h, tuple(gr.fixings_xy), gr.bending, nodes)
    if cache_key not in _SCAN:
        comp = gr.point_compliance(list(nodes))
        k = int(np.argmax(comp))
        _SCAN[cache_key] = (float(comp[k]), [float(v) for v in gr.nodes[nodes[k]]])
    return _SCAN[cache_key]


def f3(x):
    return f'{x:.3f}'


def render_a5_regions(c):
    a = A5(c)
    rows = []
    for key, label in SETS:
        reg = a.g['regions'][key]
        rows.append([label, f"{reg['farthest']['span_mm']:.1f} at {reg['farthest']['point_xy']}",
                     f"{reg['edge_region_low_y']['span_mm']:.1f} at {reg['edge_region_low_y']['point_xy']}",
                     f"{reg['edge_region_high_y']['span_mm']:.1f} at {reg['edge_region_high_y']['point_xy']}",
                     f"{reg['interior_bay']['radius_mm']:.1f} at {reg['interior_bay']['centre_xy']}"])
    return sm.table(['Fixings', 'Farthest point of K from a fixing, mm', 'Region y < post rows: farthest, mm',
                     'Region y > post rows: farthest, mm', 'Largest circle inside K holding no fixing, radius, mm'], rows)


def render_a5_k(c):
    a = A5(c)
    lim = c.dv('strain_design_limit')
    hg = a.a3.p['handling_g']
    rows = []
    for key, label in SETS:
        s1, s5 = a.uniform_summary(key, 1.0), a.uniform_summary(key, hg)
        spans = {'y_low': a.g['regions'][key]['edge_region_low_y']['span_mm'], 'y_high': a.g['regions'][key]['edge_region_high_y']['span_mm']}
        for reg, reg_label in REGIONS:
            strip = (f"{spans[reg]:.1f}: {f3(a.strip_w(hg, spans[reg])[0])} / {sm.ue(a.strip_w(hg, spans[reg])[1])}"
                     if reg in spans else 'n/a (held on both sides)')
            rows.append([label, reg_label, f3(s1[reg]['w']), f3(s5[reg]['w']), str(s5[reg]['at']), sm.ue(s1[reg]['eps']),
                         sm.ue(s5[reg]['eps']), 'within' if s5[reg]['eps'] <= lim else 'exceeds', strip])
    return sm.table(['Fixings', 'Region', 'Grillage deflection 1 g, mm', f'Grillage deflection {hg:g} g, mm', f'Where ({hg:g} g)',
                     'Grillage strain 1 g, microstrain', f'Grillage strain {hg:g} g, microstrain', f'Strain against {lim * 1e6:.0f}',
                     f'a4 strip screen at {hg:g} g: span, deflection mm / strain'], rows)


def render_a5_points(c):
    a = A5(c)
    hg = a.a3.p['handling_g']
    clear = a.p['rear_clearance_mm']
    rows = []
    for key, label in SETS:
        s = a.uniform_summary(key, hg)
        cells = [label] + [f3(w) for w in s['points']] + [f"{f3(s['max']['w'])} at {s['max']['at']}",
                                                         'within' if s['max']['w'] <= clear else 'exceeds']
        rows.append(cells)
    pts = [f'Grillage at ({x:g}, {y:g}), {hg:g} g, mm' for x, y in a.p['far_points_xy']]
    table1 = sm.table(['Fixings'] + pts + [f'Largest anywhere on K, {hg:g} g, mm', f'Against {clear} mm rear clearance (DS-33)'], rows)
    spans = [a.g['regions']['list']['farthest']['span_mm'], None, a.p['fixing_distance_rule_mm']]
    corner = a.p['far_points_xy'][1]
    spans[1] = min(geo.dist(corner, f['xy']) for f in a.g['fixings'])
    rows2 = [[f'{s:.1f}', f3(a.strip_w(hg, s)[0]), sm.ue(a.strip_w(hg, s)[1])] for s in spans]
    table2 = sm.table([f'a4 strip screen: span, mm', f'Deflection at {hg:g} g, mm', 'Strain, microstrain'], rows2)
    return table1 + '\n\n' + table2


def render_a5_mesh(c):
    a = A5(c)
    hg = a.a3.p['handling_g']
    rows = []
    for step in (a.p['grillage_step_mm'], a.p['grillage_step_mm'] / 2):
        s = a.uniform_summary('list', hg, step)
        rows.append([f'{step:g}', f3(s['max']['w']), str(s['max']['at']), f3(s['points'][0]), f3(s['points'][1])])
    return sm.table(['Grid step, mm', f'Largest deflection on the list, {hg:g} g, mm', 'Where', 'At the first far point, mm',
                     'At the second far point, mm'], rows)


def render_a5_sleeves(c):
    a = A5(c)
    lim = c.dv('strain_design_limit')
    err = a.p['sleeve_error_mm']
    rows = []
    for s in a.g['sleeves']:
        cells = [s['id'], s['kind'], f"{s['gap_mm']:.1f}", f"{s['nearest_other_fixing']} {s['span_mm']:.1f}"]
        worst = 0.0
        for key in ('printer', 'too_long', 'worst_case'):
            e = c.strain(err[key], s['span_mm'])
            worst = max(worst, e)
            cells.append(sm.ue(e))
        cells.append('within' if worst <= lim else 'exceeds')
        rows.append(cells)
    return sm.table(['Sleeve', 'Kind', 'Gap, mm', 'Nearest other fixing, span mm', f"Strain at {err['printer']} mm error",
                     f"Strain at {err['too_long']} mm too long", f"Strain at {err['worst_case']} mm (worst case)",
                     f'Against {lim * 1e6:.0f} microstrain'], rows)


def render_a5_push(c):
    a = A5(c)
    lim = c.dv('strain_design_limit')
    est = a.a4_push_strain()
    rows = []
    for key, label in SETS:
        for xy in a.p['far_points_xy']:
            comp, at = a.compliance(key, node_xy=xy)
            lb = a.cut_lower_bound(key, at)[0]
            rows.append([label, f'push at {at}', f3(comp)] + cut_cells(lb, lim) + [sm.ue(est), f'{lim / est:.1f}'])
        comp, at = a.compliance_scan(key)
        lb = a.cut_lower_bound(key, at)[0]
        rows.append([label, f'largest compliance on the edge, push at {at}', f3(comp)] + cut_cells(lb, lim) + [sm.ue(est), f'{lim / est:.1f}'])
    return sm.table(['Fixings', "Push on K's rear face", 'Compliance, mm/N (grillage, upper bound)',
                     'Strain per newton, lower bound (straight cut), microstrain', f'Force at {lim * 1e6:.0f} microstrain, at most, N',
                     'Strain per newton, a4 estimate (45° spread), microstrain', f'Force at {lim * 1e6:.0f} microstrain, a4 estimate, N'], rows)


def cut_cells(lb, lim):
    if lb is None:
        return ['no straight cut (bound does not apply)', 'n/a']
    return [sm.ue(lb), f'{lim / lb:.1f}']


def annulus_area(outer, inner, centre, edges, shift=0.0, n=400):
    """Area of the sleeve annulus around centre that lies on the centre's side of every edge line (grid integration).
    edges are board-edge segments ((x1, y1), (x2, y2)) at any angle; shift moves each line that far away from the centre."""
    xs = np.linspace(-outer, outer, n)
    gx, gy = np.meshgrid(xs, xs)
    rr = np.hypot(gx, gy)
    keep = (rr <= outer) & (rr >= inner)
    cx, cy = centre
    for (ax, ay), (bx, by) in edges:
        tx, ty = bx - ax, by - ay
        length = math.hypot(tx, ty)
        nx, ny = -ty / length, tx / length
        side = (cx - ax) * nx + (cy - ay) * ny
        if side < 0:
            nx, ny, side = -nx, -ny, -side
        keep &= gx * nx + gy * ny >= -(side + shift)
    cell = (xs[1] - xs[0]) ** 2
    return float(keep.sum() * cell)


def render_a5_corners(c):
    a = A5(c)
    sleeve = load_spacer(c)
    outer, inner = sleeve['outer_diameter_mm'] / 2, sleeve['bore_diameter_mm'] / 2
    opts = a.p['corner_sleeve_options']
    rows = []
    for sid, boards in a.g['corner_sleeves'].items():
        for board, f in boards.items():
            site = [s['xy'] for s in a.g['sleeves'] if s['id'] == sid][0]
            edges = [e for e, d in zip(f['nearest_edges_mm'], f['edge_distances_mm']) if d < outer]
            area = annulus_area(outer, inner, site, edges)
            small = annulus_area(opts['smaller_outer_diameter_mm'] / 2, inner, site, edges)
            moved = annulus_area(outer, inner, site, edges, shift=opts['inward_move_mm'])
            parts = '; '.join(f"{p['ref']} ({p['lib']}) origin {p['origin_distance_mm']:.2f} mm"
                              + (f", drill {p['drills_mm']}" if p['drills_mm'] else '') for p in f['footprints_within_8_mm']) or 'none'
            rows.append([sid, board, ', '.join(f'{d:.2f}' for d in f['edge_distances_mm']), f'{max(0.0, outer - min(f["edge_distances_mm"])):.2f}',
                         holes_here(f, outer), f'{area:.1f} of {math.pi * (outer ** 2 - inner ** 2):.1f}', f'{small:.1f}', f'{moved:.1f}', parts])
    return sm.table(['Sleeve', 'Board', 'Two nearest board edges, mm', 'Overhang, mm', 'Hole or land today', 'Bearing area left, mm²',
                     f"Area with a {opts['smaller_outer_diameter_mm']} mm sleeve, mm²", f"Area moved {opts['inward_move_mm']} mm inward, mm²",
                     'Footprints within 8 mm (origin distance from the site)'], rows)


def holes_here(facts, radius):
    """Footprints whose origin lies inside the sleeve's outer radius on this board."""
    inside = [p for p in facts['footprints_within_8_mm'] if p['origin_distance_mm'] < radius]
    return '; '.join(f"{p['ref']} drill {p['drills_mm']}" for p in inside) if inside else 'no footprint within the sleeve radius'


def load_spacer(c):
    return json.loads((sm.ROOT / c.d['sources']['S-SPACER']['path']).read_text())['sleeve']


def render_a5_terms(c):
    rows = []
    for name, t in c.d['parameters']['a5'].items():
        basis = t.get('locator') or t.get('formula') or ('to source: ' + t.get('to_source', ''))
        src = t.get('source', '')
        rows.append([f'`a5.{name}`', str(t['value']).replace('|', '/'), t['status'], (f'{src}: ' if src else '') + basis.replace('|', '/')])
    return sm.table(['Parameter', 'Value', 'Status', 'Source, formula or what would source it'], rows)


RENDERERS = {
    'a5_regions': render_a5_regions, 'a5_k': render_a5_k, 'a5_points': render_a5_points, 'a5_mesh': render_a5_mesh,
    'a5_sleeves': render_a5_sleeves, 'a5_push': render_a5_push, 'a5_corners': render_a5_corners, 'a5_terms': render_a5_terms,
}
