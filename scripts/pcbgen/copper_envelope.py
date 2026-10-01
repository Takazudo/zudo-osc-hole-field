"""Analytic envelopes of the actual supported native copper primitives.

Circle vertices lie on the exact radius for the contained polygon. Dividing
radius by cos(pi/N) makes every circumscribed edge tangent to that circle.
Capsules and rounded rectangles are Minkowski sums with that same disk, so
set inclusion is preserved. Integer native half-sizes/radii and effective
centres are exported before any polygon approximation. Quarter-turns use
exact signed coordinate permutations. Unsupported shapes fail explicitly.

The2nm guard covers native integer polygon-coordinate rounding and floating
coordinate arithmetic separately from circle chord approximation. Coordinates
are restricted to +/-1000mm; exported integers are exact and all primitive
construction operations use double precision, with no general-angle rotation.
This is a nominal CAD envelope, not a manufacturing etch/registration envelope.
"""
import math

import shapely
from shapely import affinity
from shapely.geometry import LineString,Point,box

FLOAT_GUARD_MM=2e-6
QUADRANT_SEGMENTS=32


def core_rectangle(x,y):
    if x==0 and y==0:return Point(0,0)
    if x==0:return LineString([(0,-y),(0,y)])
    if y==0:return LineString([(-x,0),(x,0)])
    return box(-x,-y,x,y)


def primitive_envelopes(primitive):
    kind=primitive['kind'];radius=None
    if kind=='segment':
        a=primitive['start_nm'];b=primitive['end_nm']
        if any(abs(v)>1_000_000_000 for v in a+b):raise ValueError('native primitive exceeds coordinate proof range')
        core=Point([v/1e6 for v in a]) if a==b else LineString([[v/1e6 for v in a],[v/1e6 for v in b]])
        radius=primitive['radius_nm']/1e6
        centre=None
    else:
        centre=primitive['centre_nm']
        if any(abs(v)>1_000_000_000 for v in centre):raise ValueError('native primitive exceeds coordinate proof range')
        hx,hy=[v/1e6 for v in primitive['half_size_nm']]
        if min(hx,hy)<=0:raise ValueError('nonpositive native copper primitive')
        if kind=='circle':core=Point(0,0);radius=hx
        elif kind=='oval':
            radius=min(hx,hy);core=core_rectangle(hx-radius,hy-radius)
        elif kind=='rectangle':core=core_rectangle(hx,hy);radius=0.
        elif kind=='roundrect':
            radius=primitive['corner_radius_nm']/1e6
            if not 0<=radius<=min(hx,hy):raise ValueError('invalid native rounded corner')
            core=core_rectangle(hx-radius,hy-radius)
        else:raise ValueError('unsupported native copper primitive: '+kind)
    if radius<0:raise ValueError('negative native copper radius')
    if radius:
        inner=core.buffer(radius,quad_segs=QUADRANT_SEGMENTS)
        outer=core.buffer(radius/math.cos(math.pi/(4*QUADRANT_SEGMENTS)),quad_segs=QUADRANT_SEGMENTS)
    else:inner=outer=core
    if centre is not None:
        quarter=primitive['quarter_turns']
        if quarter not in (0,1,2,3):raise ValueError('unsupported nonorthogonal native pad')
        transforms=((1,0,0,1,0,0),(0,-1,1,0,0,0),(-1,0,0,-1,0,0),(0,1,-1,0,0,0))
        inner=affinity.translate(affinity.affine_transform(inner,transforms[quarter]),centre[0]/1e6,centre[1]/1e6)
        outer=affinity.translate(affinity.affine_transform(outer,transforms[quarter]),centre[0]/1e6,centre[1]/1e6)
    inner=inner.buffer(-FLOAT_GUARD_MM,quad_segs=QUADRANT_SEGMENTS)
    outer=outer.buffer(FLOAT_GUARD_MM,quad_segs=QUADRANT_SEGMENTS)
    if not inner.is_valid or not outer.is_valid or not outer.covers(inner):
        raise ValueError('analytic copper envelopes lost set inclusion')
    return inner,outer
