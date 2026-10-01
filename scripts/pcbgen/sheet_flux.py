"""Conserved RT0 sheet-current trials and exact triangle Joule energy.

Each shared face has one normal-current variable. A divergence correction
enforces current conservation in every triangle. Integrating the resulting
piecewise Raviart--Thomas field gives a Thomson upper energy for the modeled
conductor and specified finite current electrodes; primal P1 energy alone
is not an upper bound. Physical transfer claims require their separate proof.
"""
from __future__ import annotations

import numpy as np
import shapely
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu


def grid_area_twice(polygon):
    """Exact integer twice-area on the declared 1 pm coordinate grid."""
    def ring_area(ring):
        points=[tuple(round(float(v)*1e9) for v in p) for p in ring.coords]
        return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:])))
    return sum(ring_area(part.exterior)-sum(ring_area(h) for h in part.interiors)
               for part in shapely.get_parts(polygon))


class FluxSheet:
    """One sheet, insulating outer boundary except specified finite faces.

    Native multilayer assembly adds shared barrel-sector flow variables at
    the same boundary faces; it must not substitute separate independent vias.
    """
    def __init__(self, sheet, sheet_ohm, standalone=True):
        self.sheet = sheet
        self.sheet_ohm = sheet_ohm
        triangles = sheet.triangles
        xy = sheet.metric_xy[triangles]
        # Face i is opposite vertex i; its unit outward-flux basis is
        # (x-vertex_i)/(2*area). This is a true finite current field.
        local_edges = np.sort(triangles[:, [[1, 2], [2, 0], [0, 1]]], axis=2)
        self.edges, inverse, counts = np.unique(local_edges.reshape(-1, 2), axis=0,
                                               return_inverse=True, return_counts=True)
        self.edge_ids = inverse.reshape(-1, 3)
        self.counts = counts
        signs = np.ones(len(inverse))
        order = np.argsort(inverse, kind='stable')
        previous = np.r_[-1, inverse[order][:-1]]
        signs[order[inverse[order] == previous]] = -1
        self.signs = signs.reshape(-1, 3)
        centroid = xy.mean(axis=1)
        mean_square = (np.sum(xy*xy, axis=(1, 2))+np.sum(np.sum(xy, axis=1)**2, axis=1))/12
        dot = np.einsum('nik,njk->nij', xy, xy)
        cv = np.einsum('nk,nik->ni', centroid, xy)
        self.mass = sheet_ohm*(mean_square[:, None, None]-cv[:, :, None]-cv[:, None, :]+dot)/(4*sheet.areas[:, None, None])
        # Translation cancellation is avoided in later large-coordinate use
        # by computing the same expression in centroid coordinates.
        relative = xy-centroid[:, None, :]
        mean_relative_square = np.sum(relative*relative, axis=(1, 2))/12
        self.mass = np.asarray(sheet_ohm*(mean_relative_square[:, None, None]+np.einsum('nik,njk->nij', relative, relative))/(4*sheet.areas[:, None, None])*sheet.metric_factors[:,None,None],dtype=float)
        self.internal = np.flatnonzero(counts == 2)
        variable = np.full(len(self.edges), -1, dtype=int)
        variable[self.internal] = np.arange(len(self.internal))
        local_variables = variable[self.edge_ids]
        valid = local_variables >= 0
        rows = np.broadcast_to(np.arange(len(triangles))[:, None], local_variables.shape)[valid]
        self.divergence = coo_matrix((self.signs[valid], (rows, local_variables[valid])),
            shape=(len(triangles), len(self.internal))).tocsc()
        edge_weight = np.zeros(len(self.edges))
        np.add.at(edge_weight, self.edge_ids.ravel(), np.diagonal(self.mass, axis1=1, axis2=2).ravel())
        self.weights = edge_weight[self.internal]
        if np.any(self.weights <= 0):
            raise ValueError('nonpositive finite face energy')
        self.laplacian = self.divergence@diags(1/self.weights)@self.divergence.T
        if standalone and connected_components(self.laplacian, directed=False, return_labels=False) != 1:
            raise ValueError('disconnected flux sheet; components need explicit electrode accounting')
        self.factor = splu(self.laplacian[1:, 1:].tocsc()) if standalone else None

    def boundary_current(self, line, current):
        """Prescribed outward current, partitioned over exact boundary faces."""
        flux = np.zeros(len(self.edges)); represented = 0.
        for edge in np.flatnonzero(self.counts == 1):
            a, b = self.edges[edge]
            segment = shapely.LineString([self.sheet.xy[a], self.sheet.xy[b]])
            length = segment.intersection(line).length
            if length <= 1e-12:
                continue
            if abs(length-segment.length) > 1e-8:
                raise ValueError('RT current electrode must align with whole mesh faces')
            flux[edge] = current*length/line.length
            represented += length
        if abs(represented-line.length) > 1e-8:
            raise ValueError('RT electrode is missing or duplicated')
        return flux

    def area_current(self, patch, current):
        """Exact uniform patch source; reject every partially covered triangle."""
        indices = self.sheet.tree.query(patch, predicate='intersects')
        sources = np.zeros(len(self.sheet.triangles))
        denominator=grid_area_twice(patch);represented=0
        if denominator<=0:raise ValueError('finite source profile has nonpositive exact area')
        for index in indices:
            area = self.sheet.polygons[index].intersection(patch).area
            if area <= 1e-18:
                continue
            full = self.sheet.areas[index]
            if abs(area-full) > max(1e-14, full*1e-7):
                raise ValueError('RT area electrode must align with whole triangles')
            points=[tuple(round(float(v)*1e9) for v in p) for p in self.sheet.xy[self.sheet.triangles[index]]]
            a,b,c=points
            numerator=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            sources[index] = current*numerator/denominator
            represented+=numerator
        if represented!=denominator:
            raise ValueError('RT area electrode is missing or duplicated on the exact coordinate grid')
        return sources

    def nodal_area_current(self,patch,current):
        """Exact P1 functional on whole source triangles, rounded only at sums."""
        source=self.area_current(patch,current)
        nodal=np.zeros(len(self.sheet.xy))
        np.add.at(nodal,self.sheet.triangles.ravel(),np.repeat(source/3,3))
        return nodal

    @staticmethod
    def one_face_source_lift_ohm(patch, rho_ohm_mm, foil_mm):
        """Extruded foil lift for a uniform one-face unit-current patch.

        Jz varies linearly from zero at the opposite foil face to 1/A at
        the physical electrode. Its divergence cancels the 2D sheet source.
        Orthogonality makes its Joule charge additive to the sheet trial.
        """
        if patch.area <= 0 or rho_ohm_mm <= 0 or foil_mm <= 0:
            raise ValueError('nonpositive physical source lift geometry')
        return rho_ohm_mm*foil_mm/(3*patch.area)

    def reconstruct(self, fixed, voltage=None, element_sources=None):
        if self.factor is None:
            raise ValueError('multilayer flux requires assembled physical component constraints')
        if np.any(abs(fixed[self.internal]) > 1e-14):
            raise ValueError('fixed boundary current assigned to an interior face')
        q0 = np.zeros(len(self.internal))
        if voltage is not None:
            xy = self.sheet.xy[self.sheet.triangles]
            v = voltage[self.sheet.triangles]
            determinant = ((xy[:, 1, 0]-xy[:, 0, 0])*(xy[:, 2, 1]-xy[:, 0, 1])-
                           (xy[:, 2, 0]-xy[:, 0, 0])*(xy[:, 1, 1]-xy[:, 0, 1]))
            dx = xy[:, [1, 2, 0], 1]-xy[:, [2, 0, 1], 1]
            dy = xy[:, [2, 0, 1], 0]-xy[:, [1, 2, 0], 0]
            gradient = np.column_stack((np.sum(v*dx, axis=1), np.sum(v*dy, axis=1)))/determinant[:, None]
            tangents = xy[:, [2, 0, 1], :]-xy[:, [1, 2, 0], :]
            normal_length = np.stack((tangents[:, :, 1], -tangents[:, :, 0]), axis=2)*np.sign(determinant[:, None, None])
            out = -np.einsum('nk,nik->ni', gradient, normal_length)/self.sheet_ohm
            average = np.zeros(len(self.edges))
            np.add.at(average, self.edge_ids.ravel(), (out*self.signs).ravel())
            average /= self.counts
            q0 = average[self.internal]
        source = np.zeros(len(self.sheet.triangles)) if element_sources is None else np.asarray(element_sources)
        boundary_divergence = np.sum(self.signs*fixed[self.edge_ids], axis=1)
        required = source-boundary_divergence
        if abs(required.sum()) > 1e-9:
            raise ValueError('physical current source and return do not balance')
        error = required-self.divergence@q0
        potential = np.zeros(len(required)); potential[1:] = self.factor.solve(error[1:])
        flux = fixed.copy()
        flux[self.internal] = q0+(self.divergence.T@potential)/self.weights
        local = self.signs*flux[self.edge_ids]
        residual = np.sum(local, axis=1)-source
        if np.max(abs(residual)) > 1e-8:
            raise ValueError('RT field fails exact interelement current conservation')
        energy = float(np.einsum('ni,nij,nj->', local, self.mass, local))
        return {'joule_upper_ohm': energy, 'maximum_triangle_divergence_residual_A': float(np.max(abs(residual))),
                'shared_face_normal_current_is_single_variable': True,
                'bound_scope': 'Thomson current trial on the exact meshed sheet and prescribed finite flux electrodes'}, flux
