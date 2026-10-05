"""Bounded partition transition for the core locality placement (#43).

The core packages are placed by scripts/checks/jack_locality.py, anchored on the
core GH headers instead of panel hardware (see partition35_floorplan.py).
"""
from __future__ import annotations
import copy


def prove_core_locality_transition(old,new):
    """Whole-partition equality except core package faces and the core layer stack."""
    expected=copy.deepcopy(old)
    current={b['id']:b for b in new['boards']}
    for board in expected['boards']:
        if board.get('board_key')=='K':
            board['layers']=current[board['id']]['layers'];board['layer_reason']=current[board['id']]['layer_reason']
    old_rows={r['ref']:r for r in expected['assignment']['components']}
    for row in new['assignment']['components']:
        before=old_rows.get(row['ref'])
        if before is not None and before['board']=='K':before['side']=row['side']
    if expected!=new:raise ValueError('Partition changed beyond the core locality placement and core layer stack')


def without_core_locality(partition,base):
    """The partition with core package faces and the core layer stack restored from base.

    Later jack-half changes stay, so the jack transition is proved on this
    intermediate and the core transition from it to the current partition.
    """
    result=copy.deepcopy(partition)
    before={b['id']:b for b in base['boards']}
    for board in result['boards']:
        if board.get('board_key')=='K':
            board['layers']=before[board['id']]['layers'];board['layer_reason']=before[board['id']]['layer_reason']
    sides={r['ref']:r['side'] for r in base['assignment']['components'] if r['board']=='K'}
    for row in result['assignment']['components']:
        if row['board']=='K':row['side']=sides[row['ref']]
    return result


def spread_module_homes(homes,areas,bounds,holes=(),fill=0.55,passes=600):
    """Push module home discs apart so each module has room near its headers.

    homes: {instance: (x, y)}; areas: {instance: courtyard mm2 over both faces}.
    Each disc holds its module at `fill` density on two faces; discs repel until
    they stop overlapping, stay inside bounds and outside `holes` rectangles, and
    are weakly pulled back toward their header homes.
    """
    import math
    r={k:math.sqrt(areas[k]/(2*fill)/math.pi) for k in homes}
    p={k:list(v) for k,v in homes.items()};keys=sorted(p)
    for _ in range(passes):
        moved=0.0
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                dx=p[b][0]-p[a][0];dy=p[b][1]-p[a][1];d=math.hypot(dx,dy) or 1e-6;over=r[a]+r[b]-d
                if over>0:
                    ux,uy=dx/d,dy/d;wa=r[b]**2/(r[a]**2+r[b]**2);wb=1-wa
                    p[a][0]-=ux*over*wa;p[a][1]-=uy*over*wa;p[b][0]+=ux*over*wb;p[b][1]+=uy*over*wb;moved+=over
        for k in keys:
            p[k][0]+=0.02*(homes[k][0]-p[k][0]);p[k][1]+=0.02*(homes[k][1]-p[k][1])
            x0,y0,x1,y1=bounds;rr=min(r[k],(x1-x0)/2,(y1-y0)/2)
            p[k][0]=min(max(p[k][0],x0+rr),x1-rr);p[k][1]=min(max(p[k][1],y0+rr),y1-rr)
            for hx0,hy0,hx1,hy1 in holes:
                if hx0<p[k][0]<hx1 and hy0<p[k][1]<hy1:
                    # Leave the hole through its nearest side.
                    exits=[(p[k][0]-hx0,(hx0,p[k][1])),(hx1-p[k][0],(hx1,p[k][1])),(p[k][1]-hy0,(p[k][0],hy0)),(hy1-p[k][1],(p[k][0],hy1))]
                    p[k]=list(min(exits)[1])
        if moved<1e-3:break
    return {k:tuple(v) for k,v in p.items()}
