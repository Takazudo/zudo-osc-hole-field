"""Conservative courtyard containment and face checks, independent of KiCad."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def area(self):
        return max(0, self.x1-self.x0)*max(0, self.y1-self.y0)

    def shift(self, dx, dy):
        return Box(self.x0+dx, self.y0+dy, self.x1+dx, self.y1+dy)

    def intersects(self, other, gap=0):
        return (self.x0 < other.x1+gap and self.x1 > other.x0-gap
                and self.y0 < other.y1+gap and self.y1 > other.y0-gap)

    def overlap_area(self, other):
        return (max(0, min(self.x1, other.x1)-max(self.x0, other.x0))
                * max(0, min(self.y1, other.y1)-max(self.y0, other.y0)))


def point_in_polygon(x, y, poly):
    inside = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i+1) % len(poly)]
        if ((y1 > y) != (y2 > y)) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            inside = not inside
    return inside


def point_segment_distance(x, y, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx-ax, by-ay
    t = max(0, min(1, ((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
    return math.hypot(x-(ax+t*dx), y-(ay+t*dy))


def segment_intersects_box(a, b, box):
    """Closed segment/rectangle intersection, including contact and endpoints."""
    lo, hi = 0., 1.
    for start, end, lower, upper in ((a[0], b[0], box.x0, box.x1),
                                    (a[1], b[1], box.y0, box.y1)):
        delta = end-start
        if delta == 0:
            if start < lower or start > upper:
                return False
        else:
            enter, leave = sorted(((lower-start)/delta, (upper-start)/delta))
            lo, hi = max(lo, enter), min(hi, leave)
            if lo > hi:
                return False
    return True


def point_box_distance(point, box):
    x, y = point
    return math.hypot(max(box.x0-x, 0, x-box.x1), max(box.y0-y, 0, y-box.y1))


def inside_outline(box, outline, clearance):
    """Require an interior courtyard and clearance along its entire perimeter.

    Corners alone cannot exclude a concave notch. Check every outline segment
    against the closed rectangle, then its minimum distance to the rectangle.
    Retain the existing 1e-6 mm clearance comparison tolerance; boundary contact
    is rejected even when the requested clearance is zero.
    """
    numbers = (box.x0, box.y0, box.x1, box.y1, clearance)
    if (not all(math.isfinite(v) for v in numbers) or clearance < 0
            or box.x0 >= box.x1 or box.y0 >= box.y1 or len(outline) < 3
            or any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in outline)
            or len(set(map(tuple, outline))) != len(outline)):
        raise ValueError('invalid courtyard, outline or clearance')
    corners = ((box.x0, box.y0), (box.x1, box.y0),
               (box.x1, box.y1), (box.x0, box.y1))
    if not all(point_in_polygon(x, y, outline) for x, y in corners):
        return False
    for i, a in enumerate(outline):
        b = outline[(i+1) % len(outline)]
        if segment_intersects_box(a, b, box):
            return False
        distance = min(point_box_distance(a, box), point_box_distance(b, box),
                       *(point_segment_distance(x, y, a, b) for x, y in corners))
        if distance < clearance-1e-6:
            return False
    return True


def placement_side_matches(actual, requested, region_side):
    """An omitted source side adds no constraint; actual face must always agree."""
    return actual in ('F.Cu', 'B.Cu') and actual == region_side and (not requested or requested == actual)
