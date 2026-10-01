"""Exact, conditional partial-P1-cell energy witnesses; no solver or geometry edits.

Coordinates are millimetres. The inherited current-inner-domain admission is
an explicit premise, not established by clipping or a floating spatial index.
"""
from dataclasses import dataclass, field
from fractions import Fraction as F
import math


def exact(value):
    if isinstance(value, bool):
        raise ValueError('finite real value required')
    try:
        return F(*value.as_integer_ratio()) if hasattr(value, 'as_integer_ratio') else F(value)
    except (ValueError, OverflowError, TypeError) as exc:
        raise ValueError('finite real value required') from exc


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def signed_twice_area(poly):
    return sum((cross(a, b) for a, b in zip(poly, poly[1:]+poly[:1])), F())


def area(poly):
    return abs(signed_twice_area(poly))/2


def triangle(points):
    points = tuple(tuple(map(exact, p)) for p in points)
    if len(points) != 3 or any(len(p) != 2 for p in points):
        raise ValueError('three two-dimensional vertices required')
    determinant = signed_twice_area(points)
    if not determinant:
        raise ValueError('degenerate triangle')
    return points if determinant > 0 else (points[0], points[2], points[1])


def halfplanes(poly):
    if signed_twice_area(poly) < 0:
        poly = tuple(reversed(poly))
    for p, q in zip(poly, poly[1:]+poly[:1]):
        dx, dy = sub(q, p)
        yield dy, -dx, dy*p[0]-dx*p[1]


def clip_halfplane(poly, a, b, c):
    if not poly:
        return ()
    out = []
    for p, q in zip(poly, poly[1:]+poly[:1]):
        fp, fq = a*p[0]+b*p[1]-c, a*q[0]+b*q[1]-c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp/(fp-fq)
            out.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
    return tuple(out)


def intersect(poly, other):
    if not poly or not other or not area(poly) or not area(other):
        return ()
    for a, b, c in halfplanes(other):
        poly = clip_halfplane(poly, a, b, c)
    return poly


def erode(points, epsilon):
    """Subset of every triangle with matching vertices in L-infinity boxes."""
    original = triangle(points)
    epsilon = exact(epsilon)
    if epsilon < 0:
        raise ValueError('negative coordinate uncertainty')
    poly = original
    for a, b, c in halfplanes(original):
        poly = clip_halfplane(poly, a, b, c-epsilon*(abs(a)+abs(b)))
    return poly


def area_upper(points, epsilon):
    a, b, c = triangle(points)
    epsilon = exact(epsilon)
    if epsilon < 0:
        raise ValueError('negative coordinate uncertainty')
    d, e = sub(b, a), sub(c, a)
    determinant = cross(d, e)
    error = 2*epsilon*(sum(map(abs, d))+sum(map(abs, e)))+8*epsilon**2
    if determinant-error <= 0:
        raise ValueError('uncertain triangle orientation')
    return (determinant+error)/2


class WorkCap(Exception):
    """No contribution from the incomplete target; its overhead stays paid."""


@dataclass
class Budget:
    limits: dict
    used: dict = field(default_factory=dict)

    def charge(self, kind, amount=1):
        if kind not in self.limits or amount < 0:
            raise ValueError('unknown work budget')
        value = self.used.get(kind, 0)+amount
        if value > self.limits[kind]:
            raise WorkCap(kind)
        self.used[kind] = value


def covered_fraction(nominal, epsilon, canonical, current, nearby, budget):
    """Exact nonoverlap checks before accepting any area for one target.

    current: (unique ID, nominal triangle, epsilon) witnesses.
    nearby: (unique ID, exact canonical triangle) OTHER potential cells,
    including already counted cells. Caller supplies conservative census.
    """
    patch = erode(nominal, epsilon)
    upper = area_upper(nominal, epsilon)
    if area(canonical) > upper or area(intersect(patch, canonical)) != area(patch):
        raise ValueError('canonical area or erosion escapes its enclosure')
    seen = set()
    for ident, other in nearby:
        if ident in seen:
            raise ValueError('duplicate nearby potential ID')
        seen.add(ident)
        budget.charge('overlap_checks')
        # Check the entire exact target, not just its eroded witness. This
        # also protects additions against previously counted whole cells.
        if area(intersect(canonical, other)):
            raise ValueError('positive-area potential overlap')
    pieces = []
    seen = set()
    for ident, points, error in current:
        if ident in seen:
            raise ValueError('duplicate current witness ID')
        seen.add(ident)
        budget.charge('clips')
        piece = intersect(patch, erode(points, error))
        if area(piece):
            for previous in pieces:
                budget.charge('overlap_checks')
                if area(intersect(piece, previous)):
                    raise ValueError('positive-area current witness overlap')
            pieces.append(piece)
    covered = sum(map(area, pieces), F())
    fraction = covered/upper
    if not 0 <= fraction <= 1:
        raise ValueError('invalid area fraction; never clamp overlapping witnesses')
    return fraction, covered, upper, len(pieces)


def p1_energy_interval(points, values, errors, sheet_ohm, metric_factor=1):
    """Exact full-cell energy enclosure, including BOTH nodal endpoint errors.

    P1 gradients are constant. Exact arithmetic pays no unrecorded float
    contraction error. Existing metric inflation is retained conservatively.
    """
    points = tuple(tuple(map(exact, p)) for p in points)
    determinant = abs(signed_twice_area(points))
    if len(points) != 3 or not determinant:
        raise ValueError('nondegenerate P1 triangle required')
    values, errors = tuple(map(exact, values)), tuple(map(exact, errors))
    resistance, factor = exact(sheet_ohm), exact(metric_factor)
    if len(values) != 3 or len(errors) != 3 or min(errors) < 0 or resistance <= 0 or factor < 1:
        raise ValueError('invalid P1 coefficient/material/metric enclosure')
    # The common anchor cancels exactly; its uncertainty is still included
    # in both differences. No error upper is scaled by a lower area fraction.
    differences = (F(), values[1]-values[0], values[2]-values[0])
    delta = (F(), errors[1]+errors[0], errors[2]+errors[0])
    lower = upper = F()
    for axis in (0, 1):
        weights = [points[(i+1)%3][axis]-points[(i+2)%3][axis] for i in range(3)]
        centre = sum((a*b for a, b in zip(weights, differences)), F())
        radius = sum((abs(a)*b for a, b in zip(weights, delta)), F())
        lower += max(F(), abs(centre)-radius)**2
        upper += (abs(centre)+radius)**2
    denominator = 2*determinant*resistance
    return lower/denominator/factor, upper/denominator*factor


class CanonicalChart:
    """Reconstruct the frozen grid/affine-interface chart; check cached eta.

    No trig or barrel geometry is invented here: caller provides endpoints
    from the hash-bound frozen interface_polygon API and retained parameters.
    """
    def __init__(self, sheet, interfaces):
        import numpy as np
        self.sheet = sheet
        self.eps_long = exact(np.finfo(np.longdouble).eps)
        self.eps_float = exact(np.finfo(float).eps)
        xy = sheet.metric_xy
        if xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all() or np.max(abs(xy)) > 1000:
            raise ValueError('finite millimetre chart within native range required')
        tri = sheet.triangles
        if tri.ndim != 2 or tri.shape[1] != 3 or not np.issubdtype(tri.dtype, np.integer) or np.min(tri) < 0 or np.max(tri) >= len(xy):
            raise ValueError('valid retained triangle vertex indices required')
        if np.shape(sheet.metric_factors) != (len(tri),):
            raise ValueError('one metric factor per retained triangle required')
        if not np.isfinite(sheet.metric_factors).all() or np.min(sheet.metric_factors) < 1:
            raise ValueError('invalid retained metric factors')
        self.interface = {}
        self.cache = {}
        self.max_residual = F()
        self.max_residual_eta_ratio = F()
        expected = {(ib, s) for ib, item in enumerate(interfaces) for s in range(len(item['relative']))}
        if set(sheet.interface_faces) != expected:
            raise ValueError('missing or foreign interface sector')
        for (ib, sector), pieces in sheet.interface_faces.items():
            interface = interfaces[ib]
            centre = tuple(F(round(exact(v)*10**6), 10**6) for v in interface['centre'])
            relative = interface['relative']
            a = tuple(centre[j]+exact(relative[sector][j]) for j in range(2))
            b = tuple(centre[j]+exact(relative[(sector+1)%len(relative)][j]) for j in range(2))
            spans = []
            for piece in pieces:
                ts = tuple(map(exact, piece['parameters']))
                if len(ts) != 2 or len(piece['vertices']) != 2 or not 0 <= min(ts) < max(ts) <= 1:
                    raise ValueError('invalid retained interface parameters')
                spans.append(tuple(sorted(ts)))
                for index, t in zip(piece['vertices'], ts):
                    index = int(index)
                    if not 0 <= index < len(xy):
                        raise ValueError('invalid interface vertex')
                    point = tuple(a[j]+t*(b[j]-a[j]) for j in range(2))
                    if index in self.interface and self.interface[index] != point:
                        raise ValueError('conflicting exact canonical vertex')
                    self.interface[index] = point
            spans.sort()
            if not spans or spans[0][0] != 0 or spans[-1][1] != 1 or any(a[1] != b[0] for a, b in zip(spans, spans[1:])):
                raise ValueError('interface parameters do not telescope')

    def vertex(self, index):
        index = int(index)
        if index not in self.cache:
            nominal = tuple(map(exact, self.sheet.metric_xy[index]))
            eta = 64*self.eps_long*max(F(1), *map(abs, nominal))+32*self.eps_float
            canonical = self.interface.get(index)
            if canonical is None:
                canonical = tuple(F(round(x*10**9), 10**9) for x in nominal)
                if eta >= F(1, 2*10**9):
                    raise ValueError('ordinary grid recovery is not unique')
            residual = max(abs(a-b) for a, b in zip(canonical, nominal))
            if residual > eta:
                raise ValueError('canonical coordinate exceeds arithmetic eta')
            self.max_residual = max(self.max_residual, residual)
            self.max_residual_eta_ratio = max(self.max_residual_eta_ratio, residual/eta)
            self.cache[index] = nominal, canonical, eta
        return self.cache[index]

    def cell(self, index):
        records = [self.vertex(i) for i in self.sheet.triangles[index]]
        nominal = tuple(r[0] for r in records)
        canonical = tuple(r[1] for r in records)
        epsilon = max(r[2] for r in records)
        if signed_twice_area(nominal)*signed_twice_area(canonical) <= 0:
            raise ValueError('canonical orientation changed')
        upper = area_upper(nominal, epsilon)
        if area(canonical) > upper:
            raise ValueError('canonical area exceeds enclosure')
        return nominal, canonical, epsilon

    def audit(self):
        return {'checked_vertices': len(self.cache), 'interface_vertices': len(self.interface),
                'maximum_coordinate_residual_mm_exact': str(self.max_residual),
                'maximum_residual_eta_ratio_exact': str(self.max_residual_eta_ratio)}

    def validate_all_vertices(self):
        """Required before a spatial index may exclude an unseen vertex."""
        for index in range(len(self.sheet.metric_xy)):
            self.vertex(index)
        return self.audit()


class ConservativeIndex:
    """Only outward bounding boxes; never floating area/intersects filtering."""
    def __init__(self, sheet):
        import numpy as np
        import shapely
        # Cached coordinates -> adjacent floats encloses conversion. Next,
        # outward-expand by a global eta upper enclosing every vertex eta.
        xy = np.asarray(sheet.metric_xy, dtype=float)
        maximum = max(F(1), *(exact(x) for x in np.max(abs(sheet.metric_xy), axis=0)))
        epsilon = 64*exact(np.finfo(np.longdouble).eps)*maximum+32*exact(np.finfo(float).eps)
        error = float(epsilon)
        if exact(error) < epsilon:
            error = math.nextafter(error, math.inf)
        low = np.nextafter(np.nextafter(xy, -np.inf)-error, -np.inf)
        high = np.nextafter(np.nextafter(xy, np.inf)+error, np.inf)
        self.bounds = np.column_stack((low[sheet.triangles].min(axis=1), high[sheet.triangles].max(axis=1)))
        self.boxes = shapely.box(*self.bounds.T)
        self.tree = shapely.STRtree(self.boxes)

    def query_box(self, box):
        return sorted(map(int, self.tree.query(box)))
