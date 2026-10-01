"""Exact rectangular process support placement in actual native pad frames.

Passing this gate proves PCB-pad containment only. The process must separately
qualify actual metal/solder coverage; a native pad is not a component foot.
"""
from fractions import Fraction as F
import math


def _nm(value):
    value=float(value)
    if not math.isfinite(value):raise ValueError('finite dimension required')
    return F.from_float(value)*1000000


def admit_rectangle(item, *, face, width_mm, length_mm, registration_mm,
                    local_offset_mm=(0.,0.)):
    if face not in ('F.Cu','B.Cu') or not item.get('ref') or not item.get('pad') or not item.get('uuid'):
        raise ValueError('exact physical pad identity and external face required')
    p=item.get('analytic_primitives',{}).get(face)
    if not p or p['kind']!='rectangle':
        raise ValueError('only explicit rectangular native copper is supported')
    w,l,r=map(_nm,(width_mm,length_mm,registration_mm))
    if min(w,l)<=0 or r<0:raise ValueError('positive support and nonnegative registration required')
    dx,dy=map(_nm,local_offset_mm)
    hx,hy=map(F,p['half_size_nm'])
    if abs(dx)+w/2+r>hx or abs(dy)+l/2+r>hy:
        raise ValueError('registered support exceeds actual native pad copper')
    turn=p['quarter_turns']
    if not isinstance(turn,int) or not 0<=turn<4:
        raise ValueError('explicit quarter-turn frame required')
    cx,cy=map(F,p['centre_nm'])
    def rotate(x,y):return ((x,y),(-y,x),(-x,-y),(y,-x))[turn]
    corners=[]
    for x,y in ((dx-w/2,dy-l/2),(dx+w/2,dy-l/2),(dx+w/2,dy+l/2),(dx-w/2,dy+l/2)):
        x,y=rotate(x,y)
        corners.append([[v.numerator,v.denominator] for v in (cx+x,cy+y)])
    return {'ref':item['ref'],'pad':item['pad'],'uuid':item['uuid'],'face':face,
            'quarter_turns':turn,'support_corners_nm_rational':corners,
            'local_z_outward_global_depth_sign':-1 if face=='F.Cu' else 1,
            'scope':'PCB containment under supplied registration only; actual conductive support qualification remains required.'}


def push_current(local_current, *, quarter_turns, face):
    """Global depth grows from F toward B; local z grows away from PCB."""
    if face not in ('F.Cu','B.Cu') or quarter_turns not in range(4):
        raise ValueError('invalid physical face/frame')
    x,y,z=map(float,local_current)
    x,y=((x,y),(-y,x),(-x,-y),(y,-x))[quarter_turns]
    return x,y,(-z if face=='F.Cu' else z)
