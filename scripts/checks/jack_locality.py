"""Locality-driven placement of free jack-board packages (owner decision 2026-10-03).

The earlier first-fit pass ignored connectivity, so free passives landed far
from the ICs and jacks they serve and the jack halves became unroutable on
their cut lines. Here every free package first gets an ideal position from
repeated median relaxation over its signal nets (fixed jacks, LEDs and
headers anchor the nets; rails and AGND are ignored). Packages are then
legalized one at a time onto the nearest free courtyard cells, IC/bypass
clusters first, reusing the floorplan grids, gaps and bypass alignment.
Panel hardware and headers never move. Geometry only; routing is separate.
"""
from __future__ import annotations
from collections import defaultdict
import copy
import math
import statistics

PLANE_NETS={'AGND','+12V','-12V','+5V'}
RELAX_PASSES=40
FACE_PENALTY_MM=4.0
# Nets longer than this pay a quadratic penalty in the swap pass; long spans, not total
# length, are what overload the routing channels.
SPAN_SOFT_MM=60.0
# Boards whose placement has been rebuilt and rerouted with the swap pass.
SWAP_BOARDS={'JL','K'}
SWAP_PASSES=8
# Core (#43): its ~1700 R0603s make all-pairs swaps too slow, so candidates are the
# same-footprint slots within this radius of a package's net median.
SWAP_RADIUS_MM={'K':25.0}
# Core only: keep-clear ring around each IC so its pins can escape (it lengthened JL nets).
IC_CHANNEL_MM={'K':0.5}
CHANNEL_DETOUR_MM=3.0
# Courtyard gap between legalized packages (mm); the core spreads wider for routing room.
GAP_MM={'K':.6}


def nearest(grid,masks,target):
    """Nearest free origin cell (envelope corner) to target cell for a list of (dx,dy,w,h) masks."""
    tx,ty=target;height=max(dy+h for dx,dy,w,h in masks);best=None
    rows=sorted(range(grid.height-height+1),key=lambda y:(abs(y-ty),y))
    for yy in rows:
        if best is not None and abs(yy-ty)>=best[0]:break
        available=grid.full
        for dx,dy,w,h in masks:
            rowfree=grid.full
            for row in grid.rows[yy+dy:yy+dy+h]:rowfree&=~(row>>dx)
            n=w;shift=1
            while n>1:
                step=min(shift,n-1);rowfree&=rowfree>>step;n-=step;shift*=2
            available&=rowfree
            if not available:break
        if not available:continue
        t=min(max(tx,0),grid.width-1)
        above=available>>t
        candidates=[]
        if above:candidates.append(t+((above&-above).bit_length()-1))
        below=available&((1<<t)-1)
        if below:candidates.append(below.bit_length()-1)
        for xx in candidates:
            d=math.hypot(xx-tx,yy-ty)
            if best is None or d<best[0]:best=(d,xx,yy)
    return best


def occupy(grid,masks,xx,yy):
    for dx,dy,w,h in masks:
        mask=((1<<w)-1)<<(xx+dx)
        for y in range(yy+dy,yy+dy+h):grid.rows[y]|=mask


def masks_for(boxes,scale,theta,oriented_box,gap=.35):
    rb=[oriented_box(b,'F.Cu',theta) for b in boxes]
    envelope=[min(b[0] for b in rb),min(b[1] for b in rb),max(b[2] for b in rb),max(b[3] for b in rb)]
    masks=[]
    for b in rb:
        dx=math.floor((b[0]-envelope[0])*scale+1e-8);dy=math.floor((b[1]-envelope[1])*scale+1e-8)
        w=math.ceil((b[2]-envelope[0]+gap)*scale-1e-8)-dx;h=math.ceil((b[3]-envelope[1]+gap)*scale-1e-8)-dy
        masks.append((dx,dy,w,h))
    return envelope,masks


def place_jack_locality(board,free,grids,shapes,pin_nets,anchors,cluster_cells,turn,oriented_box,instance_anchor=None,through_hole=lambda part:False,module_order=False):
    """Return floorplan rows for every free package of one jack board, or raise on overflow.

    anchors: {net: [(x_mm, y_mm), ...]} pad/contact positions of fixed parts and headers.
    cluster_cells(parent, caps, side): [(part, angle, (x, y))] rigid IC/bypass layout or None.
    """
    by_ref={p['ref']:p for p in free}
    caps=defaultdict(list)
    for p in free:
        if p['decouples_ref'] and p['decouples_ref'] in by_ref:caps[p['decouples_ref']].append(p)
    member_of={}
    for parent,children in caps.items():
        for c in children:member_of[c['ref']]=parent
    units=[r for r in sorted(by_ref) if r not in member_of]
    nets=defaultdict(set)
    for ref in by_ref:
        for net in pin_nets[ref].values():
            if net and net not in PLANE_NETS:nets[net].add(member_of.get(ref,ref))
    neighbours={u:[n for n in sorted({net for ref in [u,*(c['ref'] for c in caps.get(u,[]))] for net in pin_nets[ref].values() if net and net not in PLANE_NETS})] for u in units}
    grid=grids[board,'B.Cu']
    centre=(grid.width/grid.scale/2,grid.height/grid.scale/2)
    xs=[x for pts in anchors.values() for x,_ in pts];ys=[y for pts in anchors.values() for _,y in pts]
    if xs:centre=(statistics.median(xs),statistics.median(ys))
    pos={u:centre for u in units}

    home={u:(instance_anchor or {}).get(by_ref[u]['instance']) for u in units}

    def target(u,positions):
        pts=[]
        for net in neighbours[u]:
            pts+=anchors.get(net,[])
            pts+=[positions[v] for v in nets[net] if v!=u and v in positions]
        # Pure net medians collapse every module toward the board centre; weighting each
        # package toward its own module's fixed jacks/LEDs keeps modules spread like the panel.
        if home[u]:pts+=[home[u]]*max(1,len(pts))
        if not pts:return None
        return (statistics.median(x for x,_ in pts),statistics.median(y for _,y in pts))

    for _ in range(RELAX_PASSES):
        for u in units:
            t=target(u,pos)
            if t:pos[u]=t
    fixed_degree=lambda u:sum(len(anchors.get(n,[])) for n in neighbours[u])
    order=sorted(units,key=lambda u:(u not in caps,-fixed_degree(u),-len(neighbours[u]),u))
    if module_order:
        # Legalize one module at a time, largest first, so each fills contiguous space around its home.
        size=defaultdict(int)
        for u in units:size[by_ref[u]['instance']]+=1+len(caps.get(u,[]))
        rank={k:i for i,k in enumerate(sorted(size,key=lambda k:(-size[k],k)))}
        order=sorted(order,key=lambda u:rank[by_ref[u]['instance']])
    ic_channel=IC_CHANNEL_MM.get(board,0.0);gap=GAP_MM.get(board,.35)
    placed={};rows=[]
    for u in order:
        legal={**pos,**placed};t=target(u,{v:legal[v] for v in legal if v!=u}) or pos[u]
        tht=any(through_hole(p) for p in [by_ref[u],*caps.get(u,[])])
        def candidate(channel):
            best=None
            for side in ('B.Cu','F.Cu'):
                g=grids[board,side]
                if tht:
                    # Through-hole pads occupy both faces: search the union of both grids.
                    other=grids[board,'F.Cu' if side=='B.Cu' else 'B.Cu'];g=copy.copy(g);g.rows=[a|b for a,b in zip(g.rows,other.rows)]
                if u in caps:
                    variants=[(cluster_cells(by_ref[u],sorted(caps[u],key=lambda p:p['ref']),side,h),thetas) for h,thetas in ((False,(0,90,180,270)),(True,(0,90,180,270)))]
                else:
                    variants=[([(by_ref[u],0,(0,0))],(0,90))]
                for cells,thetas in variants:
                    if cells is None:continue
                    boxes=[]
                    for k,(part,angle,(x,y)) in enumerate(cells):
                        b=oriented_box(shapes[part['footprint']],side,angle);m=channel if k==0 else 0.0
                        boxes.append([b[0]+x-m,b[1]+y-m,b[2]+x+m,b[3]+y+m])
                    for theta in thetas:
                        envelope,masks=masks_for(boxes,g.scale,theta,oriented_box,gap)
                        # Parent (cell 0) origin sits at (0,0); aim the envelope so the parent lands on the target.
                        cell=(round((t[0]+envelope[0])*g.scale),round((t[1]+envelope[1])*g.scale))
                        found=nearest(g,masks,cell)
                        if found is None:continue
                        cost=found[0]/g.scale+(FACE_PENALTY_MM if side=='F.Cu' else 0)
                        if best is None or cost<best[0]:best=(cost,side,g,cells,theta,envelope,masks,found)
            return best
        best=candidate(0.0)
        if u in caps and ic_channel:
            # Reserve a routing channel around each IC so its pins can escape, unless
            # that would push the cluster much further from its target.
            roomy=candidate(ic_channel)
            if roomy is not None and (best is None or roomy[0]<=best[0]+CHANNEL_DETOUR_MM):best=roomy
        if best is None:raise ValueError(f'jack locality overflow {board} {u}')
        _,side,g,cells,theta,envelope,masks,(_,xx,yy)=best
        for face in (('B.Cu','F.Cu') if tht else (side,)):occupy(grids[board,face],masks,xx,yy)
        offset=(xx/g.scale-envelope[0],yy/g.scale-envelope[1])
        for part,angle,p in cells:
            x,y=turn(p,theta);x+=offset[0];y+=offset[1];rotation=(angle+theta)%360
            b=oriented_box(shapes[part['footprint']],side,rotation)
            row={'ref':part['ref'],'board':board,'fixed':False,'x_mm':x,'y_mm':y,'rotation_deg':rotation,'side':side,
                 'courtyard_mm':[b[0]+x,b[1]+y,b[2]+x,b[3]+y]}
            if u in caps:row['bypass_cluster']=u
            rows.append(row)
        placed[u]=offset
    swappable={u for u in units if u not in caps}
    if board not in SWAP_BOARDS:return rows
    return improve_by_swaps(rows,{r:by_ref[r]['footprint'] for r in swappable},pin_nets,anchors,SWAP_RADIUS_MM.get(board))


def net_cost(points):
    xs=[x for x,_ in points];ys=[y for _,y in points]
    dx,dy=max(xs)-min(xs),max(ys)-min(ys);excess=max(0.0,math.hypot(dx,dy)-SPAN_SOFT_MM)
    return dx+dy+excess*excess/10.0


def improve_by_swaps(rows,footprint,pin_nets,anchors,radius=None):
    """Swap legal slots between packages with the same footprint to shorten long nets.

    Two packages with one footprint have identical courtyards in each other's slot (side
    and rotation travel with the slot), so every swap stays legal. With a radius, candidates
    are the same-footprint slots within it of the package's net median.
    """
    at={r['ref']:r for r in rows}
    nets_of={ref:{n for n in pin_nets[ref].values() if n and n not in PLANE_NETS} for ref in at}
    members=defaultdict(set)
    for ref,ns in nets_of.items():
        for n in ns:members[n].add(ref)
    cost=lambda n:net_cost(anchors.get(n,[])+[(at[r]['x_mm'],at[r]['y_mm']) for r in members[n]]) if len(members[n])+len(anchors.get(n,[]))>1 else 0.0
    groups=defaultdict(list)
    for ref in sorted(footprint):
        if ref in at:groups[footprint[ref]].append(ref)
    slot=('x_mm','y_mm','rotation_deg','side','courtyard_mm')
    def swap(a,b):
        ra,rb=at[a],at[b]
        for k in slot:ra[k],rb[k]=rb[k],ra[k]
    def want(a):
        pts=[q for n in nets_of[a] for q in anchors.get(n,[])+[(at[r]['x_mm'],at[r]['y_mm']) for r in members[n] if r!=a]]
        return (statistics.median(x for x,_ in pts),statistics.median(y for _,y in pts)) if pts else None
    for _ in range(SWAP_PASSES):
        improved=False
        for group in groups.values():
            for a in sorted(group,key=lambda r:-max((cost(n) for n in nets_of[r]),default=0)):
                t=want(a) if radius else None
                if radius and t is None:continue
                best=(-1e-6,None)
                for b in group:
                    if b==a:continue
                    if radius and (abs(at[b]['x_mm']-t[0])>radius or abs(at[b]['y_mm']-t[1])>radius):continue
                    touched=nets_of[a]|nets_of[b]
                    before=sum(cost(n) for n in touched);swap(a,b)
                    delta=sum(cost(n) for n in touched)-before;swap(a,b)
                    if delta<best[0]:best=(delta,b)
                if best[1]:swap(a,best[1]);improved=True
        if not improved:break
    return rows


def prove_jack_locality_transition(old,new):
    """Whole-partition equality except the jack-half layer stack and jack package faces/bypass distances."""
    import copy
    expected=copy.deepcopy(old)
    jack_ids={b['id'] for b in old['boards'] if b.get('board_key') in ('JL','JR')}
    current_boards={b['id']:b for b in new['boards']}
    for board in expected['boards']:
        if board['id'] in jack_ids:
            board['layers']=6;board['layer_reason']=current_boards[board['id']]['layer_reason']
    old_rows={r['ref']:r for r in expected['assignment']['components']}
    for row in new['assignment']['components']:
        before=old_rows.get(row['ref'])
        if before is not None and before['board'] in ('JL','JR'):before['side']=row['side']
    expected['checks']['J_bypass_proximity']=new['checks']['J_bypass_proximity']
    if any(p['board'] not in ('JL','JR') for p in new['checks']['J_bypass_proximity']['pairs']):
        raise ValueError('bypass proximity rows outside the jack halves')
    if expected!=new:raise ValueError('Partition changed beyond the jack-half locality placement and six-layer stack')
