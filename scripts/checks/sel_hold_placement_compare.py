#!/usr/bin/env python3
"""Compare the K TMUX6112 SEL hold-network placement with a proposed re-placement near each SEL pin.

Read only and host only: the accepted core board is parsed as text with
scripts/checks/board_text_geometry.py; no board, spec or placement file is
written, and nothing is routed, refilled or DRC-checked. For every SEL hold
network (100 kOhm pull-up, BAT54S clamp, BAT54S pull-down) it searches free
poses near the switch's SEL pad on a finite grid, against the courtyards of every
part that stays put, through-hole pads, footprint keepouts, the board outline and
the locked R21 panel hardware, and counts the existing copper each move would
invalidate. The result is a proposal for an owner decision, not an adopted
placement; centre distance is not trace length.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/checks'))
import board_text_geometry as g

SEL_PINS=('1','16','9','8')
RADIUS_MM=24.0               # CLUSTER_RADIUS_MM in scripts/checks/partition35_floorplan.py (centre to anchor)
SEARCH_MM=24.0               # search disc around the SEL pad (also capped by RADIUS_MM around the switch)
FALLBACK_MM=40.0             # diagnostic disc for parts with no pose inside the radius
STEP_MM=0.5
ANGLES=(0.0,90.0,180.0,270.0)
PAD_CLEARANCE_MM=0.2         # signal clearance used by the router stages (scripts/pcbgen/route_jack_grid.py)
EDGE_MM=0.5                  # router edge_clearance default (scripts/pcbgen/grid_router.py route())
GAP_MM=0.6                   # K courtyard spacing of the floorplan generator (scripts/checks/jack_locality.py GAP_MM['K'])
SIDE_PENALTY_MM=3.0
COPPER_PENALTY_MM=4.0        # per foreign copper object a new pad would collide with


def role(fp,sel_net):
    if fp.value.startswith('BAT54S'):
        p2=next((p['net'] for p in fp.pads if p['num']=='2'),'')
        return 'clamp' if p2=='+12V' else 'pull-down'
    return 'pull-up'


def networks(board,names):
    by_net=collections.defaultdict(list)
    for ref,f in board.footprints.items():
        for p in f.pads:
            if p['net']:by_net[p['net']].append((ref,p['num']))
    rows=[]
    for ref,f in sorted(board.footprints.items()):
        if not f.value.startswith('TMUX6112'):continue
        shapes={p['num']:p for p in f.pad_shapes()}
        for pin in SEL_PINS:
            net=shapes[pin]['net']
            if not net or net=='AGND':continue
            members=sorted({o for o,_ in by_net[net] if o!=ref})
            logic=[]
            for m in members:
                if role(board.footprints[m],net)=='pull-down':
                    logic.append(next(p['net'] for p in board.footprints[m].pads if p['num']=='2'))
            drivers=sorted(f'{o}.{n}' for ln in logic for o,n in by_net[ln] if not board.footprints[o].value.startswith('BAT54S'))
            rows.append({'switch':ref,'sel_pin':pin,'net_token':net,'net':names.get(net,net),'sel_pad_xy':(shapes[pin]['x'],shapes[pin]['y']),
                         'members':members,'logic_net_tokens':logic,'logic_drivers':drivers})
    return rows


class Obstacles:
    def __init__(self):self.grid={'F.Cu':g.Grid(2.0),'B.Cu':g.Grid(2.0)};self.polys=collections.defaultdict(list)

    def add(self,side,bb,tag):
        h=GAP_MM/2;bb=(bb[0]-h,bb[1]-h,bb[2]+h,bb[3]+h);self.grid[side].add(bb,(bb,tag))

    def hits(self,side,bb):
        h=GAP_MM/2;bb=(bb[0]-h,bb[1]-h,bb[2]+h,bb[3]+h)
        out=[t for b,t in self.grid[side].query(bb) if g.bbox_overlap(b,bb)]
        for poly,pbb,tag in self.polys[side]:
            if g.bbox_overlap(pbb,bb):
                corners=((bb[0],bb[1]),(bb[2],bb[1]),(bb[2],bb[3]),(bb[0],bb[3]),((bb[0]+bb[2])/2,(bb[1]+bb[3])/2))
                if any(g.point_in_poly(x,y,poly) for x,y in corners) or any(bb[0]<x<bb[2] and bb[1]<y<bb[3] for x,y in poly):out.append(tag)
        return out


def through(fp):return any(p['kind'] in ('thru_hole','np_thru_hole') for p in fp.pads)


def build_obstacles(board,movable,hardware):
    obs=Obstacles()
    for ref,f in board.footprints.items():
        if ref in movable:continue
        tag=('hardware:' if ref in hardware else 'locked:' if f.locked else 'part:')+ref
        bb=f.courtyard_bbox()
        if bb:
            obs.add(f.side,bb,tag)
            if through(f):obs.add('B.Cu' if f.side=='F.Cu' else 'F.Cu',bb if ref in hardware else bb,tag)
        for p in f.pad_shapes():
            if p['kind'] in ('thru_hole','np_thru_hole'):
                b=p['bbox'];c=PAD_CLEARANCE_MM;bb2=(b[0]-c,b[1]-c,b[2]+c,b[3]+c)
                for side in ('F.Cu','B.Cu'):obs.add(side,bb2,tag+'.'+p['num'])
    for z in board.zones:
        if z['keepout'] and z['keepout'].get('footprints')=='not_allowed':
            pts=z['outline'];pbb=(min(x for x,_ in pts),min(y for _,y in pts),max(x for x,_ in pts),max(y for _,y in pts))
            for l in z['layers']:
                if l in ('F.Cu','B.Cu'):obs.polys[l].append((pts,pbb,'keepout:'+z['name']))
    return obs


class Copper:
    def __init__(self,board):
        self.seg={l:g.Grid(2.0) for l in board.copper_layers};self.via=g.Grid(2.0);self.board=board
        for s in board.segments:self.seg[s['layer']].add(g.seg_bbox(s),s)
        for v in board.vias:r=v['size']/2;self.via.add((v['xy'][0]-r,v['xy'][1]-r,v['xy'][0]+r,v['xy'][1]+r),v)

    def conflicts(self,pads):
        """Foreign tracks/vias within pad clearance of the given SMD pads (same-net copper is not a conflict)."""
        out={}
        for p in pads:
            layer=next((l for l in p['layers'] if l in ('F.Cu','B.Cu')),None)
            if layer is None:continue
            c=PAD_CLEARANCE_MM;bb=(p['bbox'][0]-c-0.5,p['bbox'][1]-c-0.5,p['bbox'][2]+c+0.5,p['bbox'][3]+c+0.5)
            for s in self.seg[layer].query(bb):
                if s['net']!=p['net'] and g.seg_rect_dist(s,p['bbox'])<s['w']/2+c:out[s['uuid']]={'kind':'track','net':s['net'],'layer':layer}
            for v in self.via.query(bb):
                x0,y0,x1,y1=p['bbox'];d=math.hypot(max(x0-v['xy'][0],0,v['xy'][0]-x1),max(y0-v['xy'][1],0,v['xy'][1]-y1))
                if v['net']!=p['net'] and d<v['size']/2+c:out[v['uuid']]={'kind':'via','net':v['net']}
        return out

    def attached(self,fp):
        """Same-net tracks/vias touching the part's pads at its current pose: invalidated by any move."""
        out={}
        for p in fp.pad_shapes():
            layer=next((l for l in p['layers'] if l in ('F.Cu','B.Cu')),None)
            if layer is None or not p['net']:continue
            for s in self.seg[layer].query(p['bbox']):
                if s['net']==p['net'] and g.seg_rect_dist(s,p['bbox'])<=s['w']/2+1e-4:out[s['uuid']]={'kind':'track','net':s['net'],'layer':layer}
            for v in self.via.query(p['bbox']):
                x0,y0,x1,y1=p['bbox'];d=math.hypot(max(x0-v['xy'][0],0,v['xy'][0]-x1),max(y0-v['xy'][1],0,v['xy'][1]-y1))
                if v['net']==p['net'] and d<=v['size']/2:out[v['uuid']]={'kind':'via','net':v['net']}
        return out


def fills_under(board,bb,side):
    return sorted({z['name'] for z in board.zones if z['keepout'] is None for lay,pts in z['fills'] if lay==side
                   and any(g.point_in_poly(x,y,pts) for x,y in ((bb[0],bb[1]),(bb[2],bb[1]),(bb[2],bb[3]),(bb[0],bb[3])))})


def outline_polygon(board):
    """Chain the straight Edge.Cuts lines into one closed polygon (K is a rectangle with one notch)."""
    segs=[tuple(map(tuple,pts)) for kind,pts in board.edges if kind=='gr_line']
    poly=[segs[0][0],segs[0][1]];rest=segs[1:]
    while rest:
        for i,(a,b) in enumerate(rest):
            if a==poly[-1]:poly.append(b);break
            if b==poly[-1]:poly.append(a);break
        else:raise ValueError('Edge.Cuts lines do not chain into one outline')
        rest.pop(i)
    if poly[-1]!=poly[0]:raise ValueError('Edge.Cuts outline is not closed')
    return poly[:-1]


def inside_outline(poly,bb,margin=EDGE_MM):
    e=(bb[0]-margin,bb[1]-margin,bb[2]+margin,bb[3]+margin)
    if not all(g.point_in_poly(x,y,poly) for x,y in ((e[0],e[1]),(e[2],e[1]),(e[2],e[3]),(e[0],e[3]))):return False
    return not any(e[0]<x<e[2] and e[1]<y<e[3] for x,y in poly)


def flipped_side(side):return 'B.Cu' if side=='F.Cu' else 'F.Cu'


def search(board,fp,anchor_xy,switch_xy,obs,copper,outline,sides,disc=SEARCH_MM,radius=RADIUS_MM):
    """Lowest-cost free pose; cost = distance to the SEL pad + side change + new-copper conflicts."""
    best=None;cands=[]
    n=int(disc/STEP_MM)
    for i in range(-n,n+1):
        for j in range(-n,n+1):
            x=round(anchor_xy[0]+i*STEP_MM,3);y=round(anchor_xy[1]+j*STEP_MM,3)
            d=math.hypot(x-anchor_xy[0],y-anchor_xy[1])
            if d>disc or (radius is not None and math.dist((x,y),switch_xy)>radius):continue
            for side in sides:
                for a in ANGLES:
                    cands.append((d+(0 if side==fp.side else SIDE_PENALTY_MM),x,y,a,side))
    cands.sort()
    checked=0
    for base,x,y,a,side in cands:
        if best and base>=best[0]:break
        if side!=fp.side:continue  # mirrored geometry is not modelled; a side change is reported, not searched
        bb=fp.courtyard_bbox(x,y,a)
        if not inside_outline(outline,bb):continue
        if obs.hits(side,bb):continue
        pads=fp.pad_shapes(x,y,a);conf=copper.conflicts(pads);checked+=1
        cost=base+COPPER_PENALTY_MM*len(conf)
        if best is None or cost<best[0]:best=(cost,x,y,a,side,bb,conf)
    return best,checked


ROLE_ORDERS={'pull-down-first':('pull-down','clamp','pull-up'),'pull-up-first':('pull-up','pull-down','clamp')}


def plan(board,rows,move,obs,copper,outline,hardware,roles=ROLE_ORDERS['pull-down-first']):
    out=[];placed=[]
    for r in rows:
        sw=board.footprints[r['switch']];sw_xy=(sw.x,sw.y)
        for m in sorted(r['members'],key=lambda m:roles.index(role(board.footprints[m],r['net_token']))):
            fp=board.footprints[m]
            old=math.dist((fp.x,fp.y),sw_xy)
            row={'ref':m,'role':role(fp,r['net_token']),'footprint':fp.lib,'side':fp.side,
                 'courtyard_mm':[round(v,3) for v in (lambda b:(b[2]-b[0],b[3]-b[1]))(fp.courtyard_bbox(fp.x,fp.y,0))],
                 'status_quo':{'xy':[fp.x,fp.y],'angle':fp.angle,'centre_to_switch_mm':round(old,3),
                               'centre_to_sel_pad_mm':round(math.dist((fp.x,fp.y),r['sel_pad_xy']),3)}}
            if m not in move:
                row['proposal']='stays';out.append(row);continue
            best,checked=search(board,fp,r['sel_pad_xy'],sw_xy,obs,copper,outline,(fp.side,))
            row['poses_checked']=checked
            if best is None:
                cur=fp.courtyard_bbox()
                if not obs.hits(fp.side,cur):
                    far,_=search(board,fp,r['sel_pad_xy'],sw_xy,obs,copper,outline,(fp.side,),disc=FALLBACK_MM,radius=None)
                    row['nearest_free_pose_beyond_radius']=None if far is None else {
                        'xy':[far[1],far[2]],'angle':far[3],'centre_to_switch_mm':round(math.dist((far[1],far[2]),sw_xy),3),
                        'centre_to_sel_pad_mm':round(math.dist((far[1],far[2]),r['sel_pad_xy']),3)}
                    obs.add(fp.side,cur,'kept:'+m)
                    row['proposal']='stays';row['fallback']=f'no free pose within {RADIUS_MM} mm of the switch; the current pose is still free, so it is kept'
                else:
                    far,_=search(board,fp,r['sel_pad_xy'],sw_xy,obs,copper,outline,(fp.side,),disc=FALLBACK_MM,radius=None)
                    if far is None:
                        row['proposal']=f'NO FREE POSE within {FALLBACK_MM} mm of the SEL pad';out.append(row);continue
                    best=far;row['beyond_radius']=f'no free pose within {RADIUS_MM} mm and the current pose was taken; nearest free pose used'
            if best is None:out.append(row);continue
            cost,x,y,a,side,bb,conf=best
            obs.add(side,bb,'proposed:'+m);placed.append(m)
            near_hw=[]
            for b,tag in obs.grid[side].query((bb[0]-1,bb[1]-1,bb[2]+1,bb[3]+1)):
                if tag.startswith(('hardware:','locked:')) and '.' not in tag:
                    h=GAP_MM/2;gap=max(b[0]+h-bb[2],bb[0]-b[2]+h,b[1]+h-bb[3],bb[1]-b[3]+h)
                    near_hw.append({'ref':tag.split(':',1)[1],'kind':tag.split(':',1)[0],'courtyard_gap_mm':round(gap,3)})
            row['proposal']={'xy':[x,y],'angle':a,'side':side,'courtyard_bbox':[round(v,3) for v in bb],
                             'centre_to_switch_mm':round(math.dist((x,y),sw_xy),3),
                             'centre_to_sel_pad_mm':round(math.dist((x,y),r['sel_pad_xy']),3),
                             'new_pad_conflicts':[{'uuid':u,**v} for u,v in sorted(conf.items())],
                             'zone_fills_under_courtyard':fills_under(board,bb,side),
                             'locked_footprints_within_1mm':near_hw}
            row['invalidated_at_old_pose']=[{'uuid':u,**v} for u,v in sorted(copper.attached(fp).items())]
            out.append(row)
    return out


def summarise(rows,members):
    def dist(m,key):
        p=m['proposal'];return m['status_quo'][key] if p=='stays' or isinstance(p,str) else p[key]
    sq=[max(m['status_quo']['centre_to_switch_mm'] for m in r) for r in rows]
    pr=[max(dist(m,'centre_to_switch_mm') for m in r) for r in rows]
    moved=[m for r in rows for m in r if isinstance(m['proposal'],dict)]
    failed=[m['ref'] for r in rows for m in r if isinstance(m['proposal'],str) and m['proposal']!='stays']
    beyond=[{'ref':m['ref'],'role':m['role'],'centre_to_switch_mm':m['proposal']['centre_to_switch_mm']} for r in rows for m in r if 'beyond_radius' in m]
    inval=set();conf=set();fills=collections.Counter();hw=[]
    for m in moved:
        inval|={c['uuid'] for c in m['invalidated_at_old_pose']};conf|={c['uuid'] for c in m['proposal']['new_pad_conflicts']}
        fills.update(m['proposal']['zone_fills_under_courtyard']);hw+=[{'part':m['ref'],**h} for h in m['proposal']['locked_footprints_within_1mm']]
    nets_inval=collections.Counter(c['net'] for m in moved for c in m['invalidated_at_old_pose'])
    nets_conf=collections.Counter(c['net'] for m in moved for c in m['proposal']['new_pad_conflicts'])
    kept=[{'ref':m['ref'],'role':m['role'],'centre_to_switch_mm':m['status_quo']['centre_to_switch_mm'],
           'nearest_free_pose_beyond_radius':m.get('nearest_free_pose_beyond_radius')} for r in rows for m in r if 'fallback' in m]
    return {'sel_nets':len(rows),'parts_moved':len(moved),'parts_without_free_pose':failed,'parts_kept_by_fallback':kept,'parts_placed_beyond_radius':beyond,
            'sel_nets_with_a_member_beyond_24mm':sum(d>RADIUS_MM for d in pr),
            'status_quo_sel_nets_with_a_member_beyond_24mm':sum(d>RADIUS_MM for d in sq),
            'max_member_centre_to_switch_mm':round(max(pr),3),'status_quo_max_member_centre_to_switch_mm':round(max(sq),3),
            'copper_invalidated_at_old_poses':{'objects':len(inval),'by_net':dict(nets_inval)},
            'foreign_copper_under_new_pads':{'objects':len(conf),'by_net':dict(sorted(nets_conf.items(),key=lambda kv:-kv[1])[:12]),
                                             'distinct_nets':len(nets_conf)},
            'moved_parts_over_zone_fills':dict(fills),'locked_footprints_within_1mm':hw,
            'panel_hardware_conflicts':[h for h in hw if h['kind']=='hardware']}


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--board',type=Path,default=ROOT/'boards/osc-core/osc-core.kicad_pcb');p.add_argument('-o','--output',type=Path,required=True)
    a=p.parse_args();board=g.Board(a.board.resolve())
    names=json.loads((ROOT/'design/reports/board-net-tokens.json').read_text())
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())
    hardware={r['ref'] for r in lock['placements'] if r.get('ref') in board.footprints}
    rows=networks(board,names);members={m for r in rows for m in r['members']}
    copper=Copper(board);outline=outline_polygon(board)
    variants={};trials=[]
    beyond_set={m for r in rows for m in r['members']
                if math.dist((board.footprints[m].x,board.footprints[m].y),(board.footprints[r['switch']].x,board.footprints[r['switch']].y))>RADIUS_MM}
    for name,move in (('together',members),('beyond-24mm-only',beyond_set)):
        best=None
        for order_name,ordered in (('switch-pin',rows),('reverse',rows[::-1]),('farthest-first',sorted(rows,key=lambda r:-max(
                math.dist((board.footprints[m].x,board.footprints[m].y),(board.footprints[r['switch']].x,board.footprints[r['switch']].y)) for m in r['members'])))):
            for roles_name,roles in ROLE_ORDERS.items():
                obs=build_obstacles(board,move,hardware)
                out=[plan(board,[r],move,obs,copper,outline,hardware,roles) for r in ordered]
                if any(len(o)!=len(r['members']) for r,o in zip(ordered,out)):raise RuntimeError('a SEL hold member is missing from the plan')
                summ=summarise(out,members)
                key=(len(summ['parts_without_free_pose']),summ['sel_nets_with_a_member_beyond_24mm'],len(summ['parts_placed_beyond_radius']),summ['parts_moved'])
                trials.append({'variant':name,'network_order':order_name,'role_order':roles_name,'unplaced':key[0],'nets_beyond_24mm':key[1],
                               'placed_beyond_radius':key[2],'parts_moved':key[3]})
                if best is None or key<best[0]:best=(key,order_name,roles_name,ordered,out,summ)
        _,order_name,roles_name,ordered,out,summ=best
        variants[name]={'moved_set':'all 108 SEL hold parts' if move==members else 'only members whose centre is beyond 24 mm of the switch',
                        'chosen_order':{'networks':order_name,'roles':roles_name},'summary':summ,
                        'networks':[{**{k:v for k,v in r.items() if k!='sel_pad_xy'},'sel_pad_xy':[round(v,3) for v in r['sel_pad_xy']],'members':o}
                                    for r,o in zip(ordered,out)]}
        print(name,order_name,roles_name,json.dumps({k:summ[k] for k in ('parts_moved','parts_without_free_pose','sel_nets_with_a_member_beyond_24mm')}),flush=True)
    result={'schema':'osc-sel-hold-placement-compare-1',
            'status':'PROPOSAL FOR OWNER DECISION; host text geometry only; no board, spec or placement changed; not routed, refilled or DRC-checked; D4233 exception stays PROVISIONAL',
            'board':str(a.board.resolve().relative_to(ROOT)),'board_sha256':board.sha256,
            'placements_lock_sha256':hashlib.sha256((ROOT/'design/grid/placements.lock.json').read_bytes()).hexdigest(),
            'panel_hardware_from_lock_on_this_board':sorted(hardware),
            'locked_footprints_on_board':sum(f.locked for f in board.footprints.values()),
            'method':{'search':f'{STEP_MM} mm grid, disc of {SEARCH_MM} mm around the SEL pad, centre within {RADIUS_MM} mm of the switch, angles {list(ANGLES)}, current side only',
                      'free':f'courtyard bbox inside the Edge.Cuts polygon less {EDGE_MM} mm, at least {GAP_MM} mm from every staying courtyard, through-hole pad (+0.2 mm), footprint keepout and earlier proposal',
                      'order':'greedy, first come first served; three network orders x two role orders are tried and the one with fewest unplaced parts, then fewest nets beyond 24 mm, is kept (order_trials)',
                      'cost':f'distance to SEL pad + {COPPER_PENALTY_MM} mm per foreign copper object within 0.2 mm of a new pad',
                      'limits':'axis-aligned courtyard bounds; no silkscreen, assembly, thermal or electrical check; a side change is not searched'},
            'order_trials':trials,'variants':variants}
    a.output.write_text(json.dumps(result,indent=1,sort_keys=True)+'\n')


if __name__=='__main__':sys.exit(main())
