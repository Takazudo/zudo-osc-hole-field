"""Conforming finite copper sheet elements with shared physical boundaries.

No cell is an equipotential copper island: each triangle retains its finite
sheet conductance. Refinement changes numerical resolution, not electrodes.
This is a numerical model; convergence and physical source conditions remain
explicit acceptance gates, rather than claims of manufactured performance.
"""
from __future__ import annotations

import bisect
import collections
import math

import numpy as np
import shapely
from shapely.geometry import GeometryCollection, LineString, Point, Polygon, box
from scipy.sparse import coo_matrix
from scripts.pcbgen.shared_interface import canonical_interfaces


def coordinate(value):
    return round(float(value), 9)


def make_cells(bounds, coarse, fine, features=None, origin=(0., 0.)):
    ratio = round(coarse/fine)
    if coarse <= 0 or fine <= 0 or not math.isclose(ratio*fine, coarse, abs_tol=1e-9):
        raise ValueError('fine pitch must divide coarse pitch')
    x0, y0, x1, y1 = bounds
    ox, oy = origin
    startx = ox+math.floor((x0-ox)/coarse)*coarse
    starty = oy+math.floor((y0-oy)/coarse)*coarse
    cells = []
    for iy in range(math.ceil((y1-starty)/coarse)):
        for ix in range(math.ceil((x1-startx)/coarse)):
            x, y = startx+ix*coarse, starty+iy*coarse
            n = ratio if features is not None and features.intersects(box(x, y, x+coarse, y+coarse)) else 1
            step = coarse/n
            cells.extend(tuple(coordinate(v) for v in (x+i*step, y+j*step, x+(i+1)*step, y+(j+1)*step))
                         for j in range(n) for i in range(n))
    return cells


def make_adaptive_cells(bounds,coarse,fine,features,origin=(0.,0.)):
    """Local quadtree subdivision; every final shared edge is noded by Sheet.

    A contact refines only its intersecting descendants, rather than all64 or
    256 fine cells of a broad coarse cell. Physical electrodes stay unchanged.
    """
    ratio=coarse/fine
    if ratio<1 or not math.isclose(math.log2(ratio),round(math.log2(ratio)),abs_tol=1e-12):
        raise ValueError('adaptive fine pitch must divide coarse by a power of two')
    result=[]
    def visit(cell):
        x0,y0,x1,y1=cell
        if x1-x0<=fine+1e-10 or not features.intersects(box(*cell)):
            result.append(cell);return
        xm=coordinate((x0+x1)/2);ym=coordinate((y0+y1)/2)
        for child in ((x0,y0,xm,ym),(xm,y0,x1,ym),(x0,ym,xm,y1),(xm,ym,x1,y1)):
            visit(child)
    for cell in make_cells(bounds,coarse,coarse,origin=origin):visit(cell)
    return result


def edge_vertices(cells):
    vertical = collections.defaultdict(set); horizontal = collections.defaultdict(set)
    for x0, y0, x1, y1 in cells:
        for x in (x0, x1):
            vertical[x].update((y0, y1))
        for y in (y0, y1):
            horizontal[y].update((x0, x1))
    return ({k: sorted(v) for k, v in vertical.items()},
            {k: sorted(v) for k, v in horizontal.items()})


def conforming_ring(ring, cell, vertical, horizontal):
    x0, y0, x1, y1 = cell
    result = []
    points = list(ring.coords)
    for a, b in zip(points, points[1:]):
        a = tuple(coordinate(v) for v in a); b = tuple(coordinate(v) for v in b)
        result.append(a)
        values = None
        if a[0] == b[0] and a[0] in (x0, x1):
            values = vertical[a[0]]; axis = 1
        elif a[1] == b[1] and a[1] in (y0, y1):
            values = horizontal[a[1]]; axis = 0
        if values is not None:
            lo, hi = sorted((a[axis], b[axis]))
            middle = values[bisect.bisect_right(values, lo):bisect.bisect_left(values, hi)]
            if b[axis] < a[axis]:
                middle = list(reversed(middle))
            result.extend((a[0], v) if axis == 1 else (v, a[1]) for v in middle)
    return result


class Sheet:
    def __init__(self, copper, cells, sheet_ohm, source_patches=(),interfaces=()):
        if not copper.is_valid or copper.is_empty or sheet_ohm <= 0:
            raise ValueError('invalid finite copper sheet')
        vertical, horizontal = edge_vertices(cells)
        # Native boundary vertices can lie partway along a shared cell face
        # even when one neighboring cell is completely covered by copper.
        # Include them on BOTH sides, rather than creating a hanging node.
        for x, y in shapely.get_coordinates(copper):
            x, y = coordinate(x), coordinate(y)
            if x in vertical:
                vertical[x].append(y)
            if y in horizontal:
                horizontal[y].append(x)
        vertical = {k: sorted(set(v)) for k, v in vertical.items()}
        horizontal = {k: sorted(set(v)) for k, v in horizontal.items()}
        spatial = shapely.box(*np.asarray(cells).T)
        # Whole-board copper contains many thousands of boundaries. Clip once
        # into spatial tiles before intersecting its boundary cells; intersecting
        # every fine cell with every board contour is unnecessarily quadratic.
        shapely.prepare(copper)
        inside = np.asarray(shapely.covers(copper, spatial))
        touching = np.asarray(shapely.intersects(copper, spatial))
        clipped = np.empty(len(cells), dtype=object)
        clipped[:] = GeometryCollection()
        clipped[inside] = spatial[inside]
        groups = collections.defaultdict(list)
        for index in np.flatnonzero(touching & ~inside):
            x0, y0, x1, y1 = cells[index]
            groups[(math.floor((x0+x1)/32), math.floor((y0+y1)/32))].append(index)
        for indices in groups.values():
            extent = shapely.union_all(spatial[indices]).envelope
            local_copper = copper.intersection(extent)
            clipped[indices] = shapely.intersection(spatial[indices], local_copper)
        # Physical area electrodes are material interfaces in the mesh. Splitting
        # their intersections changes numerical triangles, never the prescribed
        # source support or current density. RT0 volume divergence is constant
        # over each whole triangle, so clipped area totals alone are insufficient.
        for patch in source_patches:
            if not patch.is_valid or patch.is_empty or not copper.covers(patch):
                raise ValueError('source patch must be fully contained in copper')
            for index in np.flatnonzero(shapely.intersects(spatial, patch)):
                pieces = []
                for part in shapely.get_parts(clipped[index]):
                    pieces.extend(shapely.get_parts(part.intersection(patch)))
                    pieces.extend(shapely.get_parts(part.difference(patch)))
                clipped[index] = GeometryCollection(pieces)
        if source_patches:
            # Patch/cell crossings must be inserted into both neighboring cells.
            for shape in clipped:
                for x, y in shapely.get_coordinates(shape):
                    x, y = coordinate(x), coordinate(y)
                    if x in vertical:
                        vertical[x].append(y)
                    if y in horizontal:
                        horizontal[y].append(x)
            vertical = {k: sorted(set(v)) for k, v in vertical.items()}
            horizontal = {k: sorted(set(v)) for k, v in horizontal.items()}
        vertices = []; triangles = []; lookup = {}

        def vertex(point):
            point = tuple(coordinate(v) for v in point)
            if point not in lookup:
                lookup[point] = len(vertices); vertices.append(point)
            return lookup[point]

        for cell, shape in zip(cells, clipped):
            for part in shapely.get_parts(shape):
                if part.geom_type != 'Polygon' or part.area <= 1e-18:
                    continue
                polygon = Polygon(conforming_ring(part.exterior, cell, vertical, horizontal),
                    [conforming_ring(r, cell, vertical, horizontal) for r in part.interiors])
                if not polygon.is_valid:
                    raise ValueError('conforming boundary insertion broke native copper')
                if len(polygon.interiors) == 0 and math.isclose(polygon.area, (cell[2]-cell[0])*(cell[3]-cell[1]), abs_tol=1e-12):
                    ring = list(polygon.exterior.coords)
                    centre = ((cell[0]+cell[2])/2, (cell[1]+cell[3])/2)
                    local = [[centre, a, b] for a, b in zip(ring, ring[1:])]
                else:
                    local = [list(t.exterior.coords)[:3] for t in shapely.get_parts(shapely.constrained_delaunay_triangles(polygon))]
                for triangle in local:
                    ids = [vertex(p) for p in triangle]
                    if len(set(ids)) == 3:
                        triangles.append(ids)
        self.xy = np.asarray(vertices, dtype=float)
        self.triangles = np.asarray(triangles, dtype=np.int64)
        edges = np.sort(self.triangles[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True)
        self.metric_xy,self.interface_faces,self.maximum_interface_projection_mm=canonical_interfaces(
            self.xy,unique,np.flatnonzero(counts==1),interfaces,vertical,horizontal)
        original=self.xy[self.triangles]
        original_orientation=((original[:,1,0]-original[:,0,0])*(original[:,2,1]-original[:,0,1])-
                              (original[:,2,0]-original[:,0,0])*(original[:,1,1]-original[:,0,1]))
        self.xy=np.asarray(self.metric_xy,dtype=float)
        points = self.metric_xy[self.triangles]
        twice_area = ((points[:, 1, 0]-points[:, 0, 0])*(points[:, 2, 1]-points[:, 0, 1]) -
                      (points[:, 2, 0]-points[:, 0, 0])*(points[:, 1, 1]-points[:, 0, 1]))
        if np.any(np.abs(twice_area) <= 1e-20):
            raise ValueError('degenerate sheet element')
        if np.any(np.sign(twice_area)!=np.sign(original_orientation)):
            raise ValueError('canonical shared interface projection reversed a sheet element')
        self.areas = np.asarray(np.abs(twice_area)/2,dtype=float)
        self.area_error_mm2 = float(self.areas.sum()-copper.area)
        if abs(self.area_error_mm2) > max(1e-6, copper.area*1e-8):
            raise ValueError('sheet mesh omitted or duplicated copper area')
        # Gradients of the three linear nodal shape functions.
        dx = points[:, [1, 2, 0], 1]-points[:, [2, 0, 1], 1]
        dy = points[:, [2, 0, 1], 0]-points[:, [1, 2, 0], 0]
        stiffness = (dx[:, :, None]*dx[:, None, :]+dy[:, :, None]*dy[:, None, :]) / (2*np.abs(twice_area[:, None, None])*sheet_ohm)
        maximum_edge=np.sqrt(np.sum((points-np.roll(points,1,axis=1))**2,axis=2)).max(axis=1)
        coordinate_error=(64*np.finfo(np.longdouble).eps*np.maximum(1.,np.max(abs(points),axis=(1,2)))+
                          32*np.finfo(float).eps)
        relative=16*coordinate_error*maximum_edge/np.asarray(self.areas,dtype=np.longdouble)
        if np.any(relative>=.25):raise ValueError('sheet metric evaluation is too ill-conditioned to bound')
        self.metric_factors=np.asarray(((1+relative)/(1-relative))**2,dtype=float)
        stiffness=np.asarray(stiffness*self.metric_factors[:,None,None],dtype=float)
        rows = np.broadcast_to(self.triangles[:, :, None], stiffness.shape).ravel()
        columns = np.broadcast_to(self.triangles[:, None, :], stiffness.shape).ravel()
        self.matrix = coo_matrix((stiffness.ravel(), (rows, columns)), shape=(len(vertices), len(vertices))).tocsc()
        if np.any(counts > 2):
            raise ValueError('sheet elements overlap at a shared edge')
        self.boundary_edges = unique[counts == 1]
        material_boundary = copper.boundary.buffer(2e-9)
        shapely.prepare(material_boundary)
        if not np.all(shapely.covers(material_boundary, shapely.linestrings(self.xy[self.boundary_edges]))):
            raise ValueError('unmatched interior sheet faces: mesh is not conforming')
        self.polygons = shapely.polygons(np.asarray(points,dtype=float))
        self.tree = shapely.STRtree(self.polygons)

    def area_load(self, patch):
        """Unit current distributed over one fixed finite physical patch."""
        ids = self.tree.query(patch, predicate='intersects')
        rhs = np.zeros(len(self.xy)); represented = 0.
        for index in ids:
            intersection = self.polygons[index].intersection(patch)
            if intersection.area <= 0:
                continue
            point = np.asarray(intersection.centroid.coords[0])
            xy = self.xy[self.triangles[index]]
            weights = np.linalg.solve(np.vstack((xy.T, np.ones(3))), np.r_[point, 1.])
            rhs[self.triangles[index]] += weights*intersection.area
            represented += intersection.area
        if not math.isclose(represented, patch.area, rel_tol=1e-7, abs_tol=1e-9):
            raise ValueError('finite physical patch is not fully represented in copper')
        return rhs/represented

    def line_load(self, line):
        """Unit current on a finite sheet boundary, partitioned once by faces."""
        rhs = np.zeros(len(self.xy)); represented = 0.
        for a, b in self.boundary_edges:
            segment = LineString([self.xy[a], self.xy[b]])
            overlap = segment.intersection(line)
            if overlap.length <= 1e-12:
                continue
            t = segment.project(overlap.centroid)/segment.length
            rhs[a] += (1-t)*overlap.length; rhs[b] += t*overlap.length
            represented += overlap.length
        if not math.isclose(represented, line.length, rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError('finite boundary electrode is missing, duplicated or not conforming')
        return rhs/represented


def barrel_edges(sheets, offsets, bridges, rho, thickness, plating, sheet_ohm):
    """Distributed finite axial links; each physical sector appears once.

    The matching sheet-hole edges retain their own annular sheet resistance.
    Linear edge potentials couple through a consistent boundary mass matrix.
    Angular barrel conduction is omitted. Each adjacent active-layer span is
    charged the full board thickness because actual dielectric depths are open.
    """
    rows = []; columns = []; values = []; receipts = []
    for bridge in bridges:
        centre = np.array([bridge['x_mm'], bridge['y_mm']]); radius = bridge['drill_mm']/2
        matched = collections.defaultdict(dict)
        # Original 128-sided outside drill plus the conservative 2nm retreat.
        maximum = radius/math.cos(math.pi/128)+.00002
        for layer, sheet in enumerate(sheets):
            endpoints = sheet.xy[sheet.boundary_edges]
            distances = np.linalg.norm(endpoints-centre, axis=2)
            near = (np.min(distances, axis=1) >= radius-.000002) & (np.max(distances, axis=1) <= maximum)
            for a, b in sheet.boundary_edges[near]:
                pa, pb = tuple(sheet.xy[a]), tuple(sheet.xy[b])
                key = tuple(sorted((pa, pb)))
                matched[key][layer] = (int(a), int(b)) if pa <= pb else (int(b), int(a))
        total_angle = 0.; links = 0
        for (pa, pb), layers in matched.items():
            active = sorted(layers)
            if len(active) < 2:
                continue
            a, b = np.asarray(pa)-centre, np.asarray(pb)-centre
            delta = abs(math.atan2(a[0]*b[1]-a[1]*b[0], np.dot(a, b)))
            if not 0 < delta < math.pi:
                raise ValueError('invalid physical barrel sector')
            radial = sheet_ohm*max(0., math.log(max(np.linalg.norm(a), np.linalg.norm(b))/radius))/delta
            resistance = rho*thickness/(plating*radius*delta)+2*radial
            mass = np.array([[2., 1.], [1., 2.]])/(6*resistance)
            for la, lb in zip(active, active[1:]):
                aa = np.asarray(layers[la])+offsets[la]; bb = np.asarray(layers[lb])+offsets[lb]
                for i in range(2):
                    for j in range(2):
                        for row, col, sign in ((aa[i], aa[j], 1), (bb[i], bb[j], 1),
                                               (aa[i], bb[j], -1), (bb[i], aa[j], -1)):
                            rows.append(row); columns.append(col); values.append(sign*mass[i, j])
                links += 1
            total_angle += delta
        if total_angle > 2*math.pi+1e-6:
            raise ValueError('physical barrel circumference counted more than once')
        receipts.append({'uuid': bridge['uuid'], 'shared_sector_links': links,
            'represented_angle_rad': total_angle, 'axial_span_upper_mm': thickness,
            'barrel_angular_conductance': 'omitted', 'finite_radial_polygon_gap_charged': True})
    return rows, columns, values, receipts
