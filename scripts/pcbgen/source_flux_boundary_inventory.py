"""Map actual fitted own-load copper boundary families; no model acceptance.

Native exports may be historical. Every input epoch is retained separately;
this inventory never changes a prerequisite receipt or certifies continuity.
"""
import hashlib
import math
from fractions import Fraction as F
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native
from scripts.pcbgen.convex_source_flux import domain_bounds


def circle_drill_separation(primitive,hole):
    """Exact squared separation from a guarded circular drill to convex pad.

    Rounded rectangle = axis-aligned core rectangle + radius disk. Rectangle
    and circle are its zero-radius and zero-core special cases. Positive
    squared margin proves disjointness; no polygon chord approximation.
    """
    sx,sy=(F(str(v))*1000000 for v in hole['size_mm'])
    if sx!=sy or sx<=0:
        return {'status':'unsupported drill shape; not admitted'}
    x,y=(F(str(v))*1000000 for v in hole['xy_mm'])
    cx,cy=primitive['centre_nm'];x-=cx;y-=cy
    turn=primitive['quarter_turns']
    x,y=((x,y),(y,-x),(-x,-y),(-y,x))[turn]
    hx,hy=map(F,primitive['half_size_nm']);kind=primitive['kind']
    r=F(primitive.get('corner_radius_nm',0)) if kind=='roundrect' else F(0)
    if kind=='circle':
        if hx!=hy:raise ValueError('invalid circle')
        r=hx
    elif kind not in ('rectangle','roundrect'):
        raise ValueError('unsupported source primitive')
    dx=max(abs(x)-(hx-r),F(0));dy=max(abs(y)-(hy-r),F(0))
    radius=r+sx/2+2  # retained analytic/native coordinate guard, in nm
    margin=dx*dx+dy*dy-radius*radius
    return {'status':'proved disjoint' if margin>0 else 'actual guarded drill overlap',
            'guard_nm':2,'squared_margin_nm2':[margin.numerator,margin.denominator]}


def inventory(native,partition,io):
    expected=expected_contacts(native['board_id'],partition,io,{'AGND'})
    boards=[b for b in partition['boards'] if b['id']==native['board_id']]
    if len(boards)!=1:raise ValueError('native board lacks one exact source board identity')
    refs={row['ref'] for row in partition['assignment']['components']
          if row['board']==boards[0]['board_key'] and row['fitted']}
    source_fitted={row['ref'] for row in io['physical_packages'] if not row['dnp']}
    if not refs<=source_fitted:raise ValueError('assigned fitted package is absent from source physical packages')
    pads=reconcile_native(native,expected,refs,{'AGND'})
    holes={r['uuid']:r for r in native['holes']}
    hole_ids=set(holes)
    drill_boxes=[]
    for hole in native['holes']:
        x,y=(F(str(v))*1000000 for v in hole['xy_mm'])
        dx,dy=(F(str(v))*500000 for v in hole['size_mm'])
        radius=max(dx,dy) if dx==dy else dx+dy
        drill_boxes.append((math.floor(x-radius-2),math.floor(y-radius-2),
                            math.ceil(x+radius+2),math.ceil(y+radius+2),hole['uuid']))
    rows=[]
    for (ref,pad,net),item in sorted(pads.items()):
        row={'ref':ref,'pad':pad,'uuid':item['uuid'],'native_layers':sorted(item['copper']),
             'net':net,'physical_support_qualified':False}
        if item['uuid'] in hole_ids:
            row.update(family='PTH',status='REQUIRES annular exterior and inner barrel-wall flux family; no top-face substitution')
        else:
            faces=[f for f in ('F.Cu','B.Cu') if f in item['copper']]
            if len(faces)!=1:raise ValueError('SMD source lacks one actual external foil')
            face=faces[0];primitive=item['analytic_primitives'][face]
            lo,hi,d2=domain_bounds(primitive)
            cx,cy=primitive['centre_nm'];hx,hy=primitive['half_size_nm']
            if primitive['quarter_turns']%2:hx,hy=hy,hx
            nearby=[]
            for x0,y0,x1,y1,uuid in drill_boxes:
                if cx-hx<=x1 and x0<=cx+hx and cy-hy<=y1 and y0<=cy+hy:
                    nearby.append(uuid)
            separation={uid:circle_drill_separation(primitive,holes[uid]) for uid in nearby}
            overlaps=[uid for uid in nearby if separation[uid]['status']!='proved disjoint']
            row.update(family='convex_SMD' if not overlaps else 'SMD_drill_overlap_unresolved',
                       face=face,primitive=primitive,nearby_drill_uuids=nearby,
                       actual_or_unproved_drill_uuids=overlaps,drill_separation=separation,
                       area_mm2_rational_bounds=[[lo.numerator,lo.denominator],[hi.numerator,hi.denominator]],
                       diameter_squared_mm2_rational_upper=[d2.numerator,d2.denominator],
                       status='Nominal analytic pad is convex and conservatively drill-free; physical etch/material/support admission required' if not overlaps else 'Actual guarded circular drill or unsupported shape intersects source slab; explicit actual domain/lift required')
        rows.append(row)
    return {'board_id':native['board_id'],'board_sha256':native['board_sha256'],'own_source_contacts':rows,
            'scope':'Complete fitted external own-load boundary inventory only. No full-pad wetting assumption, no zero-current omission, no current/source/material/model acceptance.'}
