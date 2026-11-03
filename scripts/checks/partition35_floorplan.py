#!/usr/bin/env python3
"""Source-derived courtyard capacity proposal. Produces no KiCad board or fit pass."""
from __future__ import annotations
import argparse
from functools import lru_cache
from collections import Counter, defaultdict
import json
import copy
import math
import statistics
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import JACK_BOARDS
from scripts.checks.connector_packing35 import board_for,pads
from scripts.checks.partition35_diagnostic import footprint_geometry
from scripts.pcbgen.netlist import TOKEN, parse, many, one
from scripts.checks.jack_locality import place_jack_locality,stable_sum,FACE_PENALTY_MM,GAP_MM,masks_for,nearest
from scripts.checks.core_locality import spread_module_homes
OUT=ROOT/'design/partition/floorplan-candidate.json'
PINS=ROOT/'design/partition/adopted-placement-pins.json'
RELEASE_ROUNDS=400
RELEASE_STEP_MM=1.5
WHOLE_MODULE_AFTER=4
WHOLE_BOARD_AFTER=8
CLUSTER_RADIUS_MM=24.0
CLUSTER_STEP_MM=0.5
GROWTH_DISTANCE_WEIGHT=0.1
EVICT_COST_MM=3.0
EVICT_MAX_AREA_MM2=15.0
# Phase 32 locality: S2b rail-clamp and bootstrap diodes never leave their slot by eviction, and an
# added one is placed within CLUSTER_RADIUS_MM of the pinned parts on its own input nets.
PROTECTION_DIODES=('BAV199,215','BAT54S,215')
# Phase 33: boards whose evicted passives are re-placed near their own slot. JL keeps the accepted
# d867e53e placement (locality placer for evicted parts); JR evicts nothing.
EVICTED_LOCAL_BOARDS=('K',)
BUCKET_MM=5.0
BYPASS_LIMIT_MM=json.loads((ROOT/'design/partition/bypass-placement-evidence.json').read_text())['proposal']['maximum_supply_pad_to_capacitor_rail_pad_mm']
SCALE=4


class Grid:
    """Conservative 0.25 mm occupancy cells, using bit rows for rectangle search."""
    def __init__(self,board,side,outline):
        self.scale=10 if board in JACK_BOARDS else SCALE
        self.board=board;self.side=side;self.width=318*self.scale;self.height=298*self.scale
        self.full=(1<<self.width)-1;self.rows=[0]*self.height
        def inside(x,y):
            # Rectangular source outlines with one orthogonal notch each.
            if board in JACK_BOARDS:
                xs=[p[0] for p in outline];return min(xs)+.30<=x<=max(xs)-.30 and 20.30<=y<=163.70
            if board=='P':return 1.30<=x<=316.70 and 176.30<=y<=291.70 and (x>=94.30 or y>=194.30)
            return 4.30<=x<=313.70 and 8.30<=y<=291.70 and (x<=257.70 or y<=245.70)
        for y in range(self.height):
            for x in range(self.width):
                if not inside(x/self.scale,y/self.scale):self.rows[y]|=1<<x
    def fill(self,b,gap=.35):
        SCALE=self.scale
        x0,y0,x1,y1=b;x0=max(0,math.floor((x0-gap)*SCALE));x1=min(self.width,math.ceil((x1+gap)*SCALE));y0=max(0,math.floor((y0-gap)*SCALE));y1=min(self.height,math.ceil((y1+gap)*SCALE));mask=((1<<(x1-x0))-1)<<x0
        for y in range(y0,y1):self.rows[y]|=mask
    def place(self,box):
        SCALE=self.scale
        if self.side=='B.Cu':box=[-box[2],box[1],-box[0],box[3]]
        for angle in (0,90):
            b=box if angle==0 else [-box[3],box[0],-box[1],box[2]]
            w=math.ceil((b[2]-b[0]+.35)*SCALE);h=math.ceil((b[3]-b[1]+.35)*SCALE)
            for y in range(self.height-h+1):
                available=self.full
                for row in self.rows[y:y+h]:available &= ~row
                n=w;shift=1
                while n>1:
                    step=min(shift,n-1);available &= available>>step;n-=step;shift*=2
                if not available:continue
                x=(available&-available).bit_length()-1
                self.fill([x/SCALE,y/SCALE,(x+w)/SCALE,(y+h)/SCALE],0)
                return {'x_mm':x/SCALE-b[0],'y_mm':y/SCALE-b[1],'rotation_deg':angle,'side':self.side,
                        'courtyard_mm':[x/SCALE,y/SCALE,x/SCALE+b[2]-b[0],y/SCALE+b[3]-b[1]]}
        return None


def transformed(box,p):
    angle=math.radians(p['rot_deg']);co,si=math.cos(angle),math.sin(angle)
    points=[(p['x_mm']+x*co-y*si,p['y_mm']+x*si+y*co) for x in (box[0],box[2]) for y in (box[1],box[3])]
    return [min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]


def turn(point, angle):
    x,y=point
    for _ in range((angle%360)//90):x,y=-y,x
    return x,y


def oriented_box(box, side, angle):
    pts=[turn((-x if side=='B.Cu' else x,y),angle) for x in (box[0],box[2]) for y in (box[1],box[3])]
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]


@lru_cache(maxsize=None)
def footprint_pads(footprint):
    tree,_=parse(TOKEN.findall((ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(footprint.split(':')[1]+'.kicad_mod')).read_text()))
    return {p[1]:tuple(map(float,one(p,'at')[1:3])) for p in many(tree,'pad')}


@lru_cache(maxsize=None)
def through_hole(footprint):
    return 'thru_hole' in (ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(footprint.split(':')[1]+'.kicad_mod')).read_text()


def bypass_cells(parent,caps,side,shapes,pin_nets,horizontal=False):
    """Rigid IC plus capacitors, each capacitor aligned to its actual supply pad."""
    icbox=oriented_box(shapes[parent['footprint']],side,0)
    ipads=footprint_pads(parent['footprint']);cells=[(parent,0,(0,0))]
    for cap in caps:
        # A local supply such as a regulated VEE also counts as the decoupled rail.
        rail=next(n for n in pin_nets[cap['ref']].values() if n!='AGND' and n in pin_nets[parent['ref']].values())
        supply=next(pin for pin,n in pin_nets[parent['ref']].items() if n==rail)
        sx,sy=ipads[supply];sx=-sx if side=='B.Cu' else sx
        cpads=footprint_pads(cap['footprint']);cpin=next(pin for pin,n in pin_nets[cap['ref']].items() if n==rail)
        cx,cy=cpads[cpin];cx=-cx if side=='B.Cu' else cx
        angle=(180 if cx*sx>0 else 0) if horizontal else 90
        cx,cy=turn((cx,cy),angle)
        box=oriented_box(shapes[cap['footprint']],side,angle)
        x=icbox[2]+.35-box[0] if sx>0 else icbox[0]-.35-box[2]
        cells.append((cap,angle,(x,sy-cy)))
    return cells


def check_bypasses(parts,placements,pin_nets):
    errors=[]
    limit=json.loads((ROOT/'design/partition/bypass-placement-evidence.json').read_text())['proposal']['maximum_supply_pad_to_capacitor_rail_pad_mm']
    byref={p['ref']:p for p in placements};bypass=[]
    for p in parts:
        if not p['decouples_ref'] or board_for(p) not in JACK_BOARDS:continue
        if p['ref'] not in byref or p['decouples_ref'] not in byref:continue
        c=byref[p['ref']];u=byref[p['decouples_ref']]
        rail=next(n for n in pin_nets[p['ref']].values() if n in ('+12V','-12V','+5V'))
        def point(ref,net):
            item=byref[ref];part=next(q for q in parts if q['ref']==ref);pin=next(k for k,n in pin_nets[ref].items() if n==net);x,y=footprint_pads(part['footprint'])[pin]
            x,y=turn((-x if item['side']=='B.Cu' else x,y),item['rotation_deg'])
            return [x+item['x_mm'],y+item['y_mm']]
        distance=math.dist(point(p['ref'],rail),point(p['decouples_ref'],rail))
        if c['side']!=u['side'] or distance>limit:errors.append('bypass supply-pad proximity failed '+p['ref'])
        bypass.append({'capacitor':p['ref'],'IC':p['decouples_ref'],'rail':rail,'board':c['board'],'same_face':c['side']==u['side'],'supply_pad_centre_distance_mm':distance})
    return bypass,errors



def grid_free(grid,b,gap=.35):
    x0,y0,x1,y1=b;s=grid.scale
    x0=math.floor((x0-gap)*s);x1=math.ceil((x1+gap)*s);y0=math.floor((y0-gap)*s);y1=math.ceil((y1+gap)*s)
    if x0<0 or y0<0 or x1>grid.width or y1>grid.height:return False
    mask=((1<<(x1-x0))-1)<<x0
    return not any(grid.rows[y]&mask for y in range(y0,y1))


def pad_point(footprint,pin,side,rotation,x,y):
    px,py=footprint_pads(footprint)[pin]
    px,py=turn((-px if side=='B.Cu' else px,py),rotation)
    return (px+x,py+y)


def apply_adopted_pins(board,free,grids,shapes,pin_nets,anchors,pin_rows,swapped_slots,reservations,extra,report):
    """Decision E15 minimal-move reflow: pin unchanged packages on their pre-adoption slots. Each swapped IC
    moves as one rigid cluster with its bypass capacitors to the cheapest legal pose near its old slot,
    evicting the fewest small pinned passives; when nothing near fits, the nearest board-wide pose that only
    evicts small passives is used. Evicted packages join the added ones in the locality placer."""
    rows=pin_rows.get(board,{})
    if not rows and not any(r['board']==board for r in swapped_slots.values()):return free,[]
    by_ref={p['ref']:p for p in free}
    gap=GAP_MM.get(board,.35)
    swapped=sorted(r for r,s in swapped_slots.items() if s['board']==board)
    members={ic:sorted((p for p in free if p['decouples_ref']==ic),key=lambda p:p['ref']) for ic in swapped}
    in_cluster={c['ref'] for cs in members.values() for c in cs}
    net_refs=defaultdict(set)
    for ref,nets in pin_nets.items():
        for n in nets.values():
            if n:net_refs[n].add(ref)
    boxes={}
    for ref,row in rows.items():
        part=by_ref.get(ref)
        if part is None or part['footprint']!=row['footprint']:raise ValueError('stale adopted placement pin '+ref)
        c=row['courtyard_mm'];dx,dy=reservations.get(ref,(0,0))
        boxes[ref]=[min(c[0],c[0]+dx),min(c[1],c[1]+dy),max(c[2],c[2]+dx),max(c[3],c[3]+dy)]
    tht={ref:through_hole(rows[ref]['footprint']) for ref in rows}
    faces=lambda ref:('F.Cu','B.Cu') if tht[ref] else (rows[ref]['side'],)
    released=set(extra)|in_cluster
    # Same spacing convention as the locality placer's occupancy masks: the courtyard gap on the
    # right/bottom edge only, so pins keep their original spacing instead of doubling it.
    def occupy_box(g,b):g.fill([b[0],b[1],b[2]+gap,b[3]+gap],0)
    def box_free(g,b):return grid_free(g,[b[0],b[1],b[2]+gap,b[3]+gap],0)
    def evictable(ref):
        # A capacitor of a pinned IC stays with that IC so its bypass loop is not broken.
        if ref in reservations or tht[ref] or ref[:1] in ('U','J'):return False
        if by_ref[ref]['mpn'] in PROTECTION_DIODES:return False
        if by_ref[ref]['decouples_ref'] in rows and by_ref[ref]['decouples_ref'] not in released:return False
        b=shapes[rows[ref]['footprint']]
        return (b[2]-b[0])*(b[3]-b[1])<=EVICT_MAX_AREA_MM2
    def buckets(b):
        return [(i,j) for i in range(int(b[0]//BUCKET_MM),int(b[2]//BUCKET_MM)+1) for j in range(int(b[1]//BUCKET_MM),int(b[3]//BUCKET_MM)+1)]
    index=defaultdict(set)
    for ref in rows:
        if ref in released:continue
        for face in faces(ref):
            for k in buckets(boxes[ref]):index[face,k].add(ref)
    def hits(face,b):
        e=[b[0]-gap,b[1]-gap,b[2]+gap,b[3]+gap];out=set()
        for k in buckets(e):
            for ref in index.get((face,k),()):
                if ref in released:continue
                c=boxes[ref]
                if c[0]<e[2] and e[0]<c[2] and c[1]<e[3] and e[1]<c[3]:out.add(ref)
        return out
    occ={}
    for side in ('F.Cu','B.Cu'):
        occ[side]=copy.copy(grids[board,side]);occ[side].rows=list(grids[board,side].rows)
    n=int(round(CLUSTER_RADIUS_MM/CLUSTER_STEP_MM));steps=[k*CLUSTER_STEP_MM for k in range(-n,n+1)]
    offsets=sorted(((dx,dy) for dx in steps for dy in steps if math.hypot(dx,dy)<=CLUSTER_RADIUS_MM),key=lambda d:(math.hypot(*d),d))
    def poses(part,side,thetas):
        for horizontal in (False,True):
            cells=bypass_cells(part,members[part['ref']],side,shapes,pin_nets,horizontal)
            for theta in thetas:
                yield theta,cells,[(cpart,*turn(p,theta),(angle+theta)%360,oriented_box(shapes[cpart['footprint']],side,(angle+theta)%360)) for cpart,angle,p in cells]
    placed_at={ref:(row['x_mm'],row['y_mm'],row['side']) for ref,row in rows.items()}
    def growth_cost(part,slot,baseline):
        # Phase 32: score a pose by the worst half-perimeter growth it causes on the part's own signal
        # nets (other members at their current slots), then by distance; baseline False = added part.
        nets=[n for n in set(pin_nets[part['ref']].values()) if n and n not in ('AGND','+12V','-12V','+5V')]
        mine={part['ref']}|{c['ref'] for c in members.get(part['ref'],())}
        groups=[]
        for n in nets:
            pts=[placed_at[r][:2] for r in net_refs[n] if r not in mine and r in placed_at and (r not in released or r in clusters)]
            if pts:
                xs=[x for x,_ in pts];ys=[y for _,y in pts]
                hp=lambda x,y,xs=xs,ys=ys:max(*xs,x)-min(*xs,x)+max(*ys,y)-min(*ys,y)
                groups.append((hp,hp(slot['x_mm'],slot['y_mm']) if baseline else max(xs)-min(xs)+max(ys)-min(ys)))
        def cost(cx,cy):
            g=max((hp(cx,cy)-base for hp,base in groups),default=0.0)
            return max(g,0.0)+GROWTH_DISTANCE_WEIGHT*math.hypot(cx-slot['x_mm'],cy-slot['y_mm'])
        return cost
    def local_pose(part,slot,baseline=True,evict=True):
        best=None;thetas=(slot['rotation_deg'],*(t for t in (0,90,180,270) if t!=slot['rotation_deg']))
        score=growth_cost(part,slot,baseline)
        ranked=sorted(((score(slot['x_mm']+dx,slot['y_mm']+dy),dx,dy) for dx,dy in offsets))
        for side in (slot['side'],'B.Cu' if slot['side']=='F.Cu' else 'F.Cu'):
            penalty=0.0 if side==slot['side'] else FACE_PENALTY_MM
            shapes_side=[local for _,_,local in poses(part,side,thetas)]
            for s,dx,dy in ranked:
                d=s+penalty
                if best is not None and d>=best[0]:break
                cx,cy=slot['x_mm']+dx,slot['y_mm']+dy
                for local in shapes_side:
                    placed=[(cpart,x+cx,y+cy,rotation,[b[0]+x+cx,b[1]+y+cy,b[2]+x+cx,b[3]+y+cy]) for cpart,x,y,rotation,b in local]
                    if not all(box_free(occ[side],b) for *_,b in placed):continue
                    hit=set().union(*(hits(side,b) for *_,b in placed))
                    if not all(evictable(r) for r in hit) or hit and not evict:continue
                    cost=d+EVICT_COST_MM*len(hit)
                    if best is None or cost<best[0]:best=(cost,side,placed,hit)
        return best
    def wide_pose(part,slot,evict=True):
        # Board-wide nearest fit on a grid holding hardware, placed clusters and every non-evictable pin.
        best=None
        for side in (slot['side'],'B.Cu' if slot['side']=='F.Cu' else 'F.Cu'):
            g=copy.copy(occ[side]);g.rows=list(occ[side].rows)
            for ref in rows:
                if ref not in released and side in faces(ref) and (not evict or not evictable(ref)):occupy_box(g,boxes[ref])
            penalty=0.0 if side==slot['side'] else FACE_PENALTY_MM
            for theta,cells,_ in poses(part,side,(0,90,180,270)):
                local=[]
                for cpart,angle,(x,y) in cells:
                    b=oriented_box(shapes[cpart['footprint']],side,angle);local.append([b[0]+x,b[1]+y,b[2]+x,b[3]+y])
                envelope,masks=masks_for(local,g.scale,theta,oriented_box,gap)
                found=nearest(g,masks,(round((slot['x_mm']+envelope[0])*g.scale),round((slot['y_mm']+envelope[1])*g.scale)))
                if found is None:continue
                d,xx,yy=found;cost=d/g.scale+penalty
                if best is not None and cost>=best[0]:continue
                ox,oy=xx/g.scale-envelope[0],yy/g.scale-envelope[1];placed=[]
                for cpart,angle,p in cells:
                    x,y=turn(p,theta);x+=ox;y+=oy;rotation=(angle+theta)%360
                    b=oriented_box(shapes[cpart['footprint']],side,rotation);placed.append((cpart,x,y,rotation,[b[0]+x,b[1]+y,b[2]+x,b[3]+y]))
                hit=set().union(*(hits(side,b) for *_,b in placed))
                if all(evictable(r) for r in hit) and (evict or not hit):best=(cost,side,placed,hit)
        return best
    clusters={};evicted=set();moves=[];wide=[];unplaced=[]
    for ic in swapped:
        part=by_ref.get(ic)
        if part is None:raise ValueError('swapped slot without a free package '+ic)
        slot=swapped_slots[ic];best=local_pose(part,slot)
        if best is None:
            best=wide_pose(part,slot)
            if best is not None:wide.append(ic)
        if best is None:
            unplaced.append(ic);continue
        cost,side,placed,hit=best
        released|=hit;evicted|=hit
        for cpart,x,y,rotation,b in placed:
            for face in (('F.Cu','B.Cu') if through_hole(cpart['footprint']) else (side,)):occupy_box(occ[face],b)
            clusters[cpart['ref']]={'ref':cpart['ref'],'board':board,'fixed':False,'x_mm':x,'y_mm':y,'rotation_deg':rotation,
                                    'side':side,'courtyard_mm':b,'bypass_cluster':ic}
            placed_at[cpart['ref']]=(x,y,side)
        moves.append(math.dist((placed[0][1],placed[0][2]),(slot['x_mm'],slot['y_mm'])))
    boots={};boot_far=[]
    added=sorted((p for p in free if p['ref'] not in rows and p['ref'] not in clusters and p['ref'] not in in_cluster
                  and p['mpn'] in PROTECTION_DIODES),key=lambda p:p['ref'])
    for part in added:
        nets={n for n in pin_nets[part['ref']].values() if n and n not in ('AGND','+12V','-12V','+5V')}
        near=sorted(ref for ref in placed_at if ref not in released or ref in clusters if nets & set(pin_nets[ref].values()))
        if not near:
            boot_far.append(part['ref']);continue
        # Anchor on its amplifiers when any (for an S2b bootstrap diode, the amplifier it bootstraps, so the
        # diode adds no output-net length), else on one non-logic IC sharing most of its nets.
        ics=[ref for ref in near if ref[:1]=='U']
        most=max((len(nets & set(pin_nets[ref].values())) for ref in ics),default=0)
        top=[ref for ref in ics if len(nets & set(pin_nets[ref].values()))==most]
        amps=[ref for ref in ics if by_ref.get(ref,{}).get('mpn','').startswith('OPA')]
        diodes=(amps or ([min(top,key=lambda ref:(by_ref.get(ref,{}).get('mpn','').startswith('SN74'),ref))] if top else [])
                or [ref for ref in near if by_ref.get(ref,{}).get('mpn') in PROTECTION_DIODES] or near)
        x=statistics.median(placed_at[r][0] for r in diodes);y=statistics.median(placed_at[r][1] for r in diodes)
        side=Counter(placed_at[r][2] for r in diodes).most_common(1)[0][0]
        members[part['ref']]=[]
        best=local_pose(part,{'x_mm':x,'y_mm':y,'rotation_deg':0,'side':side},baseline=False)
        if best is None:
            boot_far.append(part['ref']);continue
        cost,side,placed,hit=best
        released|=hit;evicted|=hit
        for cpart,px,py,rotation,b in placed:
            occupy_box(occ[side],b)
            boots[cpart['ref']]={'ref':cpart['ref'],'board':board,'fixed':False,'x_mm':px,'y_mm':py,'rotation_deg':rotation,
                                 'side':side,'courtyard_mm':b,'protection_locality':diodes[0]}
            placed_at[cpart['ref']]=(px,py,side)
    clusters.update(boots)
    relocated={};far=[]
    if board in EVICTED_LOCAL_BOARDS:
        # An evicted passive is re-placed near its own slot (least growth on its nets) without evicting
        # anything, instead of joining the board-wide locality placer.
        for ref in sorted(evicted):
            part=by_ref[ref];row=rows[ref];members[ref]=[]
            slot={'x_mm':row['x_mm'],'y_mm':row['y_mm'],'rotation_deg':row['rotation_deg'],'side':row['side']}
            best=local_pose(part,slot,evict=False) or wide_pose(part,slot,evict=False)
            if best is None:
                far.append(ref);continue
            _,side,placed,_=best
            for cpart,px,py,rotation,b in placed:
                occupy_box(occ[side],b)
                relocated[cpart['ref']]={'ref':cpart['ref'],'board':board,'fixed':False,'x_mm':px,'y_mm':py,'rotation_deg':rotation,
                                         'side':side,'courtyard_mm':b,'evicted_near_slot':True}
                placed_at[cpart['ref']]=(px,py,side)
    clusters.update(relocated)
    pinned={}
    for ref,row in rows.items():
        if ref in released:continue
        for face in faces(ref):occupy_box(grids[board,face],boxes[ref])
        pinned[ref]={k:v for k,v in row.items() if k!='footprint'}
    for row in clusters.values():
        for face in (('F.Cu','B.Cu') if through_hole(by_ref[row['ref']]['footprint']) else (row['side'],)):occupy_box(grids[board,face],row['courtyard_mm'])
    out=[*pinned.values(),*clusters.values()]
    for row in out:
        for net in pin_nets[row['ref']].values():
            if net and net not in ('AGND','+12V','-12V','+5V'):anchors[net].append((row['x_mm'],row['y_mm']))
    report[board]={'pinned':len(pinned),'swapped_clusters':len(swapped),'cluster_capacitors':len(in_cluster),
                   'clusters_board_wide':wide,'clusters_to_locality':unplaced,
                   'cluster_move_mm':{'max':round(max(moves,default=0),3),'median':round(statistics.median(moves),3) if moves else 0},
                   'evicted':sorted(evicted),'protection_diodes_placed':len(boots),'protection_diodes_beyond_radius':boot_far,
                   'evicted_replaced_near_slot':len(relocated),'evicted_to_locality':far}
    taken=set(pinned)|set(clusters)
    return [p for p in free if p['ref'] not in taken],out


def release_window(board,unit,count,pin_rows,swapped_slots,pin_nets,extra,instance_of):
    """Unpin packages around one that found no legal slot: a growing window first, then its whole module,
    then the whole board (the full locality reflow, which is known to fit)."""
    rows=pin_rows.get(board,{})
    if count>=WHOLE_BOARD_AFTER:return set(rows)-extra
    if count>=WHOLE_MODULE_AFTER:return {ref for ref in rows if instance_of[ref]==instance_of[unit]}-extra
    if unit in swapped_slots:c=swapped_slots[unit]['courtyard_mm']
    elif unit in rows:c=rows[unit]['courtyard_mm']
    else:
        nets={n for n in pin_nets[unit].values() if n and n not in ('AGND','+12V','-12V','+5V')}
        pts=[(r['x_mm'],r['y_mm']) for ref,r in rows.items() if nets & set(pin_nets[ref].values())]
        if not pts:raise ValueError('no pinned neighbour to release for '+unit)
        x=statistics.median(p[0] for p in pts);y=statistics.median(p[1] for p in pts);c=[x,y,x,y]
    r=RELEASE_STEP_MM*count
    window=[c[0]-r,c[1]-r,c[2]+r,c[3]+r]
    hit={ref for ref,row in rows.items() if ref not in extra and row['courtyard_mm'][0]<window[2] and window[0]<row['courtyard_mm'][2] and row['courtyard_mm'][1]<window[3] and window[1]<row['courtyard_mm'][3]}
    return hit


def build():
    source=json.loads((ROOT/'design/partition/partition-input.json').read_text())
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text());lock={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    connector=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    parts=io['physical_packages'];shapes={};pin_nets=defaultdict(dict)
    for unit in io['package_units']:pin_nets[unit['ref']].update(unit['pins'])
    for p in parts:
        if p['footprint'] not in shapes:shapes[p['footprint']]=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm']
    placements=[];errors=[];grids={};available={}
    adopted=json.loads(PINS.read_text()) if PINS.exists() else {'pins':[],'swapped_slots':[],'reservations':[]}
    pin_rows=defaultdict(dict)
    for row in adopted['pins']:pin_rows[row['board']][row['ref']]=row
    swapped_slots={row['ref']:row for row in adopted['swapped_slots']}
    reservations={row['ref']:row['delta_mm'] for row in adopted['reservations']}
    adopted_report={}
    for board in (*JACK_BOARDS,'P','K'):
        spec=source['boards'][board]
        for side in ('F.Cu','B.Cu'):
            g=Grid(board,side,spec['outline']);grids[board,side]=g
            for p in parts:
                if board_for(p)!=board or not p['panel_uid']:continue
                for _,box in pads(p,lock):g.fill(box)
                if side=='F.Cu':g.fill(transformed(shapes[p['footprint']],lock[p['panel_uid']]))
            for h in connector['headers']:
                if h['board']==board and h['side']==side:g.fill(h['land_courtyard_mm'])
            if board=='K':
                for aperture in connector['K_service_apertures']:g.fill(aperture['box_mm'])
            for h in spec['supports_mm']:
                x,y=h;g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
            if board=='P':
                optical=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())['support']
                for x in optical['x_mm']:
                    for y in optical['y_mm']:
                        if y>=176:g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
            for reserve in spec.get('reserves',[]):
                if side in reserve['sides']:g.fill(reserve['rect'])
            available[board+' '+side]=sum(g.width-row.bit_count() for row in g.rows)/(g.scale*g.scale)
        free=sorted((p for p in parts if board_for(p)==board and not p['panel_uid']),key=lambda p:(-p['courtyard']['area_mm2'],p['ref']))
        def place_board(free,extra):
            if board in JACK_BOARDS:
                anchors=defaultdict(list)
                for p in parts:
                    if board_for(p)!=board or not p['panel_uid']:continue
                    point=lock[p['panel_uid']];angle=math.radians(point['rot_deg']);co,si=math.cos(angle),math.sin(angle)
                    for pin,(x,y) in footprint_pads(p['footprint']).items():
                        net=pin_nets[p['ref']].get(pin)
                        if net:anchors[net].append((point['x_mm']+x*co-y*si,point['y_mm']+x*si+y*co))
                for h in connector['headers']:
                    if h['board']==board:
                        for net in h['pin_map'].values():
                            if net not in (None,'NC'):anchors[net].append(tuple(h['center_mm']))
                free,rows=apply_adopted_pins(board,free,grids,shapes,pin_nets,anchors,pin_rows,swapped_slots,reservations,extra,adopted_report)
                homes=defaultdict(list)
                for p in parts:
                    if board_for(p)==board and p['panel_uid']:homes[p['instance']].append((lock[p['panel_uid']]['x_mm'],lock[p['panel_uid']]['y_mm']))
                instance_anchor={k:(stable_sum(x for x,_ in v)/len(v),stable_sum(y for _,y in v)/len(v)) for k,v in homes.items()}
                return rows+(place_jack_locality(board,free,grids,shapes,pin_nets,anchors,
                    lambda parent,caps,side,horizontal:bypass_cells(parent,caps,side,shapes,pin_nets,horizontal),turn,oriented_box,instance_anchor))
            if board=='K':
                # Core locality (#43): the core has no panel hardware, so its headers anchor
                # each net and each module is pulled toward the headers that carry its nets.
                anchors=defaultdict(list);net_instances=defaultdict(set);homes=defaultdict(list)
                for p in free:
                    for net in pin_nets[p['ref']].values():net_instances[net].add(p['instance'])
                for h in connector['headers']:
                    if h['board']!=board:continue
                    for net in h['pin_map'].values():
                        if net in (None,'NC'):continue
                        anchors[net].append(tuple(h['center_mm']))
                        if net not in ('AGND','+12V','-12V','+5V'):
                            for instance in net_instances[net]:homes[instance].append(h['center_mm'])
                free,rows=apply_adopted_pins(board,free,grids,shapes,pin_nets,anchors,pin_rows,swapped_slots,reservations,extra,adopted_report)
                homes={k:v for k,v in homes.items() if k in {p['instance'] for p in free}}
                instance_anchor={k:(stable_sum(x for x,_ in v)/len(v),stable_sum(y for _,y in v)/len(v)) for k,v in homes.items()}
                # Header homes crowd ~1300 packages into one corner; spread the module homes so each
                # module gets contiguous room, then legalize module by module (#43 congestion review).
                areas=defaultdict(float)
                for p in free:
                    b=shapes[p['footprint']];areas[p['instance']]+=(b[2]-b[0]+.35)*(b[3]-b[1]+.35)
                notch=[spec['outline'][3][0],spec['outline'][3][1],spec['outline'][2][0],spec['outline'][4][1]]
                instance_anchor=spread_module_homes(instance_anchor,areas,(4.3,8.3,313.7,291.7),holes=[notch],fill=.45)
                return rows+(place_jack_locality(board,free,grids,shapes,pin_nets,anchors,
                    lambda parent,caps,side,horizontal:bypass_cells(parent,caps,side,shapes,pin_nets,horizontal),turn,oriented_box,instance_anchor,
                    lambda part:through_hole(part['footprint']),module_order=True))

        if board in JACK_BOARDS or board=='K':
            base={side:list(grids[board,side].rows) for side in ('F.Cu','B.Cu')};extra=set();failures=Counter()
            for _ in range(RELEASE_ROUNDS):
                for side in ('F.Cu','B.Cu'):grids[board,side].rows=list(base[side])
                try:
                    rows=place_board(free,extra);break
                except ValueError as exc:
                    if not str(exc).startswith('jack locality overflow '):raise
                    unit=str(exc).split()[-1];failures[unit]+=1
                    extra|=release_window(board,unit,failures[unit],pin_rows,swapped_slots,pin_nets,extra,{p['ref']:p['instance'] for p in parts})
            else:raise ValueError('adopted placement release rounds exhausted '+board)
            adopted_report[board]['release_rounds']=sum(failures.values());adopted_report[board]['window_released']=sorted(extra)
            placements.extend(rows);free=[]
        for p in free:
            location=grids[board,'B.Cu'].place(shapes[p['footprint']])
            if location is None and board in JACK_BOARDS:location=grids[board,'F.Cu'].place(shapes[p['footprint']])
            if location is None:errors.append('courtyard first-fit overflow '+board+' '+p['ref']);continue
            placements.append({'ref':p['ref'],'board':board,'fixed':False,**location})
    optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text())
    placements.extend({**p,'board':'EL','side':'F.Cu'} for p in optical['placement_proposal'])
    for p in parts:
        if not p['panel_uid'] or board_for(p)=='EL':continue
        point=lock[p['panel_uid']]
        placements.append({'ref':p['ref'],'board':board_for(p),'fixed':True,'x_mm':point['x_mm'],'y_mm':point['y_mm'],'rotation_deg':point['rot_deg'],'side':'F.Cu','courtyard_mm':transformed(shapes[p['footprint']],point)})
    from scripts.checks.control_locality import apply_locality
    locality_source=json.loads((ROOT/'design/partition/control-locality.json').read_text())
    optical_source=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())
    placements,locality=apply_locality(placements,io,source,connector,lock,shapes,locality_source,optical_source)
    from scripts.checks.control_bypass_locality import apply_bypass_locality
    bypass_source=json.loads((ROOT/'design/partition/control-bypass-locality.json').read_text())
    placements,control_bypasses=apply_bypass_locality(placements,io,source,connector,lock,shapes,bypass_source,optical_source,locality_source)
    from scripts.checks.control_debounce_locality import apply_debounce_locality
    debounce_source=json.loads((ROOT/'design/partition/control-debounce-locality.json').read_text())
    placements,control_debounce=apply_debounce_locality(placements,io,source,connector,lock,shapes,debounce_source,optical_source)
    for row in placements:row['kicad_orientation_deg']=((180 if row['side']=='B.Cu' else 0)-row['rotation_deg'])%360
    from scripts.checks.routing_placement_translations import apply_translations
    placements=apply_translations(placements,source,json.loads((ROOT/'design/partition/routing-placement-translations.json').read_text()),headers=connector['headers'])
    if Counter(p['ref'] for p in placements)!=Counter(p['ref'] for p in parts):errors.append('package roster mismatch')
    bypass,bypass_errors=check_bypasses(parts,placements,pin_nets);errors.extend(bypass_errors)
    return {'schema_version':1,'status':'FAIL' if errors else 'PASS - conservative courtyard capacity proposal only',
            'errors':errors,'control_slew_locality':{'source':'design/partition/control-locality.json','status':'SOURCE GEOMETRY ONLY; native/routed/physical checks required','groups':locality},'grid_mm_by_board':{b:(.1 if b in JACK_BOARDS else .25) for b in source['boards']},'courtyard_gap_mm':.35,'drawn_edge_margin_mm':.30,'native_cached_inflation_ceiling_mm':.05,'native_free_clearance_lower_bound_mm':.25,'placements':placements,
            'control_bypass_locality':{'source':'design/partition/control-bypass-locality.json',**control_bypasses},
            'control_debounce_locality':{'source':'design/partition/control-debounce-locality.json',**control_debounce},
            'bypass_proximity':{'status':'DERIVED geometry only; routed loop #38 NOT RUN','evidence':'design/partition/bypass-placement-evidence.json','project_pad_distance_limit_mm':json.loads((ROOT/'design/partition/bypass-placement-evidence.json').read_text())['proposal']['maximum_supply_pad_to_capacitor_rail_pad_mm'],'pairs':bypass,'maximum_supply_pad_distance_mm':max((r['supply_pad_centre_distance_mm'] for r in bypass),default=0)},
            'adopted_placement_pins':{'source':'design/partition/adopted-placement-pins.json','status':'Decision E15 minimal-move reflow; source geometry only','boards':adopted_report},
            'usable_grid_area_after_exclusions_mm2':available,
            'counts':{b:dict(Counter(p['side'] for p in placements if p['board']==b)) for b in source['boards']},
            'limits':['No PCB generated, routed, soldered or physically fitted.','First-fit failure is not an infeasibility proof; every reported successful footprint has its full courtyard.',
                      'J mixed-face local passive connections need vias, continuous inner AGND and actual loop/decoupling review under #38.',
                      'Source #59 unselected protection geometry remains reserved/conditional, not fictitious zero-area components.',
                      'Main board service slots and loom/support solids must be checked separately.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report=build();text=dumps(report)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('floorplan drift')
    else:OUT.write_text(text)
    print(report['status'],report['counts'])
    if report['errors']:raise SystemExit('\n'.join(report['errors']))

if __name__=='__main__':main()
