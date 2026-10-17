"""A01 J-PWR/J-SIG common cable-entry redesign study (design only): filleted 3D routes, envelopes, rail reliefs, header moves; no native/physical claims."""
import argparse
import copy
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import stage10_interfaces as interfaces
import stage28_din_harness as s28
import stage30_din_design_integration as s30

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage31'
BASE='698d91398db411d94117a4298810b1bd58f38d61'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage31_cable_entry_redesign.py','test_stage31_cable_entry_redesign.py')}
need,read,dump,sha=s28.need,s28.read,s28.dump,s28.sha
LINKS=('J-SIG','J-PWR')
ENDS={'J-SIG':('A01:J-SIG:local','A01:J-SIG:middle'),'J-PWR':('A01:J-PWR:local','A01:J-PWR:middle')}
MATED_MM=s30.MATED_MM
# Stage10 sweep scope: "Mated7.3mm+15mm axial release;2mm latch/tool XY margin proposal".
SWEEP_XY_MARGIN_MM=2.0
STEP_MM=0.2
GENERATED=('common-input.json','candidates.json','comparison.md','copper-impact.json','report.json')+tuple(f'candidate-{c}.svg' for c in 'ABC')
NO_CLAIM_SCOPE=('physical non-interference','manufacturing or assembly qualification','rail strength','canonical CAD change','measured or cut cable length','native KiCad, ERC/DRC or simulation')


# ---------- vector helpers ----------
def sub(a,b):return [a[i]-b[i] for i in range(3)]
def add(a,b):return [a[i]+b[i] for i in range(3)]
def mul(a,k):return [a[i]*k for i in range(3)]
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a);need(n>1e-12,'zero-length route segment');return [v/n for v in a]
def r6(v):return round(v,6)
def p6(p):return [r6(v) for v in p]


# ---------- headers ----------
def turn(d,deg):
    need(deg in (0,90,180,270),'header rotation must be a quarter turn')
    c,sn={0:(1,0),90:(0,1),180:(-1,0),270:(0,-1)}[deg];return [c*d[0]-sn*d[1],sn*d[0]+c*d[1]]


def header_geometry(mech,moves):
    """Header pads, body box, release sweep and housing exit after the candidate moves; pin identity is carried unchanged."""
    out={}
    for link in LINKS:
        for ref in ENDS[link]:
            h=mech['headers'][ref];board=mech['boards'][h['board']];face=h['pad_depth_mm'];zb=board['z_mm']
            need(face in zb,'header on a board face '+ref);axis=1 if face==zb[1] else -1
            sw=next(s for s in mech['connector_release_sweeps'] if s['ref']==ref)
            need([round(v,6) for v in sw['box_mm']]==[round(h['box_mm'][0]-SWEEP_XY_MARGIN_MM,6),round(h['box_mm'][1]-SWEEP_XY_MARGIN_MM,6),round(h['box_mm'][2]+SWEEP_XY_MARGIN_MM,6),round(h['box_mm'][3]+SWEEP_XY_MARGIN_MM,6)],'Stage10 sweep is the body box plus 2 mm '+ref)
            need(h['quarter_turn']==0,'Stage10 header orientation '+ref)
            mv=moves.get(ref,{'origin_mm':h['origin_mm'],'rotation_deg':0});o0=h['origin_mm'];o1=mv['origin_mm'];q=mv['rotation_deg']
            f=lambda xy:[r6(o1[0]+turn([xy[0]-o0[0],xy[1]-o0[1]],q)[0]),r6(o1[1]+turn([xy[0]-o0[0],xy[1]-o0[1]],q)[1])]
            pads={p:[f(xy)+[face] for xy in v] for p,v in h['pads_mm'].items()}
            c=[f([h['box_mm'][0],h['box_mm'][1]]),f([h['box_mm'][2],h['box_mm'][3]])]
            box=[min(c[0][0],c[1][0]),min(c[0][1],c[1][1]),max(c[0][0],c[1][0]),max(c[0][1],c[1][1])]
            sig=[p for p in h['pins'] if h['pins'][p] is not None]
            centre=[sum(pads[p][0][k] for p in sig)/len(sig) for k in range(2)]
            exit_=[r6(centre[0]),r6(centre[1]),r6(face+axis*MATED_MM)]
            zr=sorted((face,face+axis*(MATED_MM+(sw['z_mm'][1]-sw['z_mm'][0]-MATED_MM))))
            out[ref]={'ref':ref,'link':link,'board':h['board'],'face_z_mm':face,'axis':axis,'moved':ref in moves,'origin_mm':o1,'rotation_deg':q,'pin_row_axis':'x' if q in (0,180) else 'y',
                'pins':h['pins'],'pads_xyz_mm':pads,'box_mm':[r6(v) for v in box],'pad_centroid_mm':[r6(centre[0]),r6(centre[1]),face],'exit_mm':exit_,
                'sweep':{'box_mm':[r6(box[0]-SWEEP_XY_MARGIN_MM),r6(box[1]-SWEEP_XY_MARGIN_MM),r6(box[2]+SWEEP_XY_MARGIN_MM),r6(box[3]+SWEEP_XY_MARGIN_MM)],'z_mm':[r6(zr[0]),r6(zr[1])]},
                'header_mpn':h['header_mpn'],'housing_mpn':h['housing_mpn'],'end':h['end']}
    return out


def moved_mech(mech,geo):
    m=copy.deepcopy(mech)
    for ref,g in geo.items():
        if not g['moved']:continue
        h=m['headers'][ref];h['origin_mm']=g['origin_mm'];h['box_mm']=g['box_mm']
        h['pads_xyz_mm']=g['pads_xyz_mm'];h['pads_mm']={p:[xy[:2] for xy in v] for p,v in g['pads_xyz_mm'].items()}
        sw=next(s for s in m['connector_release_sweeps'] if s['ref']==ref);sw['box_mm']=g['sweep']['box_mm']
    return m


def check_header_moves(mech,geo,moves,approval):
    """A moved header stays on its board face with its MPN and pin/net map, inside the allowed regions, and clear of other headers, DIN and mounts."""
    rows=[]
    for ref,mv in sorted(moves.items()):
        need(ref in approval['changeable']['header_refs'],'header move outside the approval '+ref)
        g=geo[ref];h=mech['headers'][ref];b=mech['boards'][g['board']]['outline_mm']
        need(g['pins']==h['pins'] and g['header_mpn']==h['header_mpn'] and g['board']==h['board'] and g['face_z_mm']==h['pad_depth_mm'],'moved header identity '+ref)
        need(b[0]<=g['box_mm'][0] and b[1]<=g['box_mm'][1] and g['box_mm'][2]<=b[2] and g['box_mm'][3]<=b[3],'moved header body on its board '+ref)
        x0,y0,x1,y1=mech['middle_access_edge_notches_mm'][0]
        need(not overlap2(g['box_mm'],[x0,y0,x1,y1]),'moved header clear of the board notch '+ref)
        others=[]
        for r2,h2 in mech['headers'].items():
            if r2==ref or h2['board']!=g['board'] or h2['pad_depth_mm']!=g['face_z_mm']:continue
            box2=geo[r2]['box_mm'] if r2 in geo else h2['box_mm']
            sweep2=geo[r2]['sweep']['box_mm'] if r2 in geo else next(s for s in mech['connector_release_sweeps'] if s['ref']==r2)['box_mm']
            need(not overlap2(g['sweep']['box_mm'],sweep2),'moved header release sweep overlaps '+r2)
            others.append({'ref':r2,'gap_mm':r6(gap2(g['sweep']['box_mm'],sweep2))})
        din=mech['din_connectors']['middle']['box_mm']
        need(not overlap2(g['sweep']['box_mm'],din),'moved header clear of the DIN body')
        mounts=[]
        for mt in mech['mounts']:
            if mt['board']!=g['board']:continue
            x,y=mt['xy_mm'];r=mt['washer_diameter_mm']/2;d=gap2(g['box_mm'],[x-r,y-r,x+r,y+r])
            need(d>0,'moved header clear of mount washer '+mt['id']);mounts.append({'mount':mt['id'],'gap_mm':r6(d)})
        rows.append({'ref':ref,'from_origin_mm':h['origin_mm'],'to_origin_mm':g['origin_mm'],'rotation_deg':g['rotation_deg'],'pin_row_axis':g['pin_row_axis'],'box_mm':g['box_mm'],'sweep':g['sweep'],
            'pins_unchanged':True,'mpn_unchanged':True,'board_face_unchanged':True,'sweep_gap_to_other_headers':min(others,key=lambda x:x['gap_mm']) if others else None,
            'nearest_mount':min(mounts,key=lambda x:x['gap_mm']) if mounts else None})
    return rows


def overlap2(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]


def gap2(a,b):
    dx=max(b[0]-a[2],a[0]-b[2],0.0);dy=max(b[1]-a[3],a[1]-b[3],0.0);return math.hypot(dx,dy)


# ---------- obstacles ----------
def obstacles(mech,lock,params,reliefs):
    """Stage30 keep-out classes plus mount spacers and screw heads; foreign depth stays unbounded (reported as a requirement)."""
    assume={'component_body_height_mm':{'value':params['component_body_height_mm']['value']},'foreign_unknown_depth_top_z_mm':{'status':'ASSUMPTION','value':mech['carrier_frames']['middle']['z_mm'][0]}}
    obs=s30.obstacles(mech,lock,assume,cap=params['foreign_depth_search_top_z_mm']['value'])
    for mt in mech['mounts']:
        x,y=mt['xy_mm'];r=mt['washer_diameter_mm']/2
        obs.append(s30.box('spacer:'+mt['id'],[x-r,y-r,mt['spacer_z_mm'][0]],[x+r,y+r,mt['spacer_z_mm'][1]]))
        obs.append(s30.box('head:'+mt['id'],[x-r,y-r,mt['rear_head_z_mm'][0]],[x+r,y+r,mt['rear_head_z_mm'][1]]))
    for rf in reliefs:obs=relieve(obs,rf)
    return obs


def relieve(obs,rf):
    out=[];found=False
    for o in obs:
        (y0,y1),zr=rf['y_mm'],rf['relieved_top_z_mm'];lo,hi=o['lo'],o['hi'];base=o.get('base',o['id'])
        if base!=rf['obstacle'] or o['id'].endswith(':floor') or not lo[1]<y0<y1<hi[1]:out.append(o);continue
        found=True;need(lo[2]<zr<hi[2],'relief inside the rail '+rf['id'])
        out+=[dict(o,id=base+':'+rf['id']+':floor',base=base,lo=[lo[0],y0,lo[2]],hi=[hi[0],y1,zr]),dict(o,id=f'{base}:y{lo[1]:g}-{y0:g}',base=base,hi=[hi[0],y0,hi[2]]),dict(o,id=f'{base}:y{y1:g}-{hi[1]:g}',base=base,lo=[lo[0],y1,lo[2]])]
    need(found,'relief obstacle exists '+rf['id'])
    return out


def shielded(rect,z,obs):
    """True when an A01 board lies between a foreign-depth XY region and height z over the whole region (the foreign part cannot pass the PCB)."""
    for o in obs:
        if o['kind']!='known' or not o['id'].startswith('board:'):continue
        if o['lo'][0]<=rect[0] and o['lo'][1]<=rect[1] and rect[2]<=o['hi'][0] and rect[3]<=o['hi'][1] and o['hi'][2]<=z:return True
    return False


def box_distance_boxes(a0,a1,b0,b1):
    return math.sqrt(sum(max(b0[i]-a1[i],a0[i]-b1[i],0.0)**2 for i in range(3)))


def box_distance(p,lo,hi):
    return math.sqrt(sum(max(lo[i]-p[i],0.0,p[i]-hi[i])**2 for i in range(3)))


# ---------- filleted routes ----------
def fillet_route(vertices,radius,leads):
    """Replace every interior corner by a circular arc; the first/last legs keep a straight lead from the housing exit."""
    need(len(vertices)>=3,'route needs at least one bend vertex')
    n=len(vertices);tl=[0.0]*n;arcs=[None]*n
    for i in range(1,n-1):
        u=unit(sub(vertices[i],vertices[i-1]));v=unit(sub(vertices[i+1],vertices[i]));th=math.acos(max(-1.0,min(1.0,dot(u,v))))
        if th<1e-6:continue
        need(th<math.pi-1e-6,'route reverses on itself at vertex '+str(i))
        tl[i]=radius*math.tan(th/2);arcs[i]=(u,v,th)
    legs=[]
    for i in range(n-1):
        L=norm(sub(vertices[i+1],vertices[i]));use=tl[i]+tl[i+1]+(leads[0] if i==0 else 0.0)+(leads[1] if i==n-2 else 0.0)
        need(use<=L+1e-9,f'bend radius {radius} mm does not fit leg {i} ({round(use,3)} > {round(L,3)} mm)')
        legs.append(L)
    pieces=[];bends=[];start=list(vertices[0])
    for i in range(1,n):
        if i<n-1 and arcs[i] is not None:
            u,v,th=arcs[i];t1=sub(vertices[i],mul(u,tl[i]));t2=add(vertices[i],mul(v,tl[i]))
            pieces.append((('leg',i-1),[start,t1]))
            centre=add(vertices[i],mul(unit(sub(v,u)),radius/math.cos(th/2)));ca=sub(t1,centre);cb=sub(t2,centre)
            steps=max(2,int(math.ceil(radius*th/STEP_MM)))
            pieces.append((('arc',i),[add(centre,add(mul(ca,math.sin((1-k/steps)*th)/math.sin(th)),mul(cb,math.sin(k/steps*th)/math.sin(th)))) for k in range(steps+1)]))
            bends.append({'vertex_index':i,'vertex_mm':p6(vertices[i]),'turn_deg':r6(math.degrees(th)),'radius_mm':radius,'arc_length_mm':r6(radius*th),'centre_mm':p6(centre)})
            start=t2
        else:
            pieces.append((('leg',i-1),[start,list(vertices[i])]));start=list(vertices[i])
    dense=[];tags=[]
    for tag,pts in pieces:
        for p,q in zip(pts,pts[1:]):
            L=norm(sub(q,p));k=max(1,int(math.ceil(L/STEP_MM)))
            for j in range(0 if not dense else 1,k+1):dense.append(add(p,mul(sub(q,p),j/k)));tags.append(tag)
    length=sum(norm(sub(b,a)) for a,b in zip(dense,dense[1:]))
    return {'dense':dense,'tags':tags,'bends':bends,'length_mm':length,'legs_mm':[r6(x) for x in legs],
        'straight_from_exit_mm':[r6(legs[0]-tl[1]),r6(legs[-1]-tl[n-2])]}


def route_vertices(geo,link,spec,shift=(0.0,0.0)):
    a,b=(geo[r] for r in ENDS[link])
    ea=add(a['exit_mm'],[0,0,a['axis']*shift[0]]);eb=add(b['exit_mm'],[0,0,b['axis']*shift[1]])
    return [ea]+[list(map(float,w)) for w in spec['waypoints_mm']]+[eb]


def bundle(params,link,dressing):
    od=params['wire_od_mm']['value'];n=params['conductors'][link];r=od*params['round_bundle_factor'][link]/2
    need(dressing in ('ROUND_BUNDLE','FLAT_SINGLE_LAYER'),'dressing kind')
    return {'kind':dressing,'conductors':n,'wire_od_mm':od,'round_radius_mm':r6(r),'flat_width_mm':r6(n*od) if dressing=='FLAT_SINGLE_LAYER' else None,'flat_thickness_mm':od if dressing=='FLAT_SINGLE_LAYER' else None}


def flat_tags(flat):
    i0,i1=flat['legs'];return {('leg',k) for k in range(i0,i1+1)}|{('arc',k) for k in range(i0+1,i1+1)}


def samples(route,bund,flat=None):
    """(point, physical radius) samples: a round bundle, or n side-by-side conductors on the declared flat legs."""
    tags=flat_tags(flat) if flat else set();out=[]
    if flat:
        ax=unit(flat['axis']);need(abs(ax[2])<1e-12,'flat ribbon width axis is horizontal');n=bund['conductors'];od=bund['wire_od_mm']
    for p,t in zip(route['dense'],route['tags']):
        if t in tags:out+=[(add(p,mul(ax,(k-(n-1)/2)*od)),od/2) for k in range(n)]
        else:out.append((p,bund['round_radius_mm']))
    return out


def evaluate_route(smp,obs,margin,link,kinds=('known','assumed_height')):
    """Surface clearance to each modelled obstacle near the route (sampling error subtracted), and the foreign-depth top each foreign part must stay below."""
    lo=[min(p[i] for p,_ in smp)-30 for i in range(3)];hi=[max(p[i] for p,_ in smp)+30 for i in range(3)]
    near=[o for o in obs if o['link']!=link and all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3))]
    known={};depth={};boards=[o for o in obs if o['id'].startswith('board:')]
    for o in near:
        if o['kind'] in kinds:
            d=min(box_distance(p,o['lo'],o['hi'])-r for p,r in smp)-STEP_MM/2
            if d<margin+5:known[o['id']]=r6(d)
        elif o['kind']=='unknown_depth':
            best=None
            for p,r in smp:
                e=r+margin+STEP_MM/2;dxy=math.hypot(max(o['lo'][0]-p[0],0.0,p[0]-o['hi'][0]),max(o['lo'][1]-p[1],0.0,p[1]-o['hi'][1]))
                if dxy>=e or p[2]<=o['lo'][2]:continue
                rect=[max(o['lo'][0],p[0]-e),max(o['lo'][1],p[1]-e),min(o['hi'][0],p[0]+e),min(o['hi'][1],p[1]+e)]
                if shielded(rect,p[2]-r,boards):continue
                top=p[2]-math.sqrt(e*e-dxy*dxy);best=top if best is None else min(best,top)
            if best is not None:depth[o['id'].split(':',1)[1]]={'block':o.get('block'),'pcb_rear_z_mm':o['lo'][2],'max_foreign_top_z_mm':r6(best),'max_rear_side_height_mm':r6(best-o['lo'][2])}
    return dict(sorted(known.items(),key=lambda kv:(kv[1],kv[0]))),dict(sorted(depth.items()))


def cable_gap(s1,s2):
    best=None;at=None
    for p,r in s1:
        for q,t in s2:
            d=math.dist(p,q)-r-t
            if best is None or d<best:best,at=d,(p6(p),p6(q))
    return r6(best-STEP_MM),at


# ---------- candidate evaluation ----------
def release_cases(geo,link,spec,params):
    """Bend-feasible release surrogate: a withdrawn housing moves 15 mm along its axis and the nearest pair of waypoints (loop top or hook) moves just far enough to keep the straight lead and an r 5 bend."""
    t=params['release_travel_mm']['value'];rad=params['design_bend_radius_mm']['value'];lead=params['straight_lead_mm']['value'];out=[]
    for dl,dm,name in ((0,0,'installed'),(0,1,'middle withdrawn 15 mm'),(1,0,'local withdrawn 15 mm'),(1,1,'both withdrawn 15 mm')):
        w=[list(map(float,x)) for x in spec['waypoints_mm']]
        for flag,idx,ref in ((dl,(0,1),ENDS[link][0]),(dm,(-1,-2),ENDS[link][1])):
            if not flag:continue
            g=geo[ref];ax=g['axis'];e=g['exit_mm'][2]+ax*t;need(all(w[i][2]==w[idx[0]][2] for i in idx),'release group shares one z '+link)
            move=max(0.0,ax*(e+ax*(lead+rad)-w[idx[0]][2]))
            for i in idx:w[i][2]+=ax*move
        v=route_vertices(geo,link,{'waypoints_mm':w},(t*dl,t*dm));r=fillet_route(v,rad,(lead,lead))
        out.append({'case':name,'route':r,'length_mm':r['length_mm']+2*MATED_MM,'lowest_centreline_z_mm':r6(min(p[2] for p in r['dense'])),'highest_centreline_z_mm':r6(max(p[2] for p in r['dense']))})
    return out


def release_row(c,d,bund,spec,obs,margin,link):
    known,depth=evaluate_route(samples(c['route'],bund,spec.get('flat')),obs,margin,link)
    hit=sorted(k for k,v in known.items() if v<margin)
    return {'case':c['case'],'length_mm':r6(c['length_mm']),'extra_mm':r6(d),'lowest_centreline_z_mm':c['lowest_centreline_z_mm'],'highest_centreline_z_mm':c['highest_centreline_z_mm'],
        'keep_outs_below_margin':hit,'foreign_depth_bounds':{k:v['max_foreign_top_z_mm'] for k,v in depth.items()},
        'note':'surrogate shape during release; own sweep excluded; the foreign PCB outline is not modelled'}


def core_envelope(mech):
    """Conservative box swept by the core, its parts, handles and DIN male half during the 40 mm withdrawal."""
    x0,y0,x1,y1=mech['boards']['A01-core']['outline_mm'];z1=mech['boards']['A01-core']['z_mm'][1]
    lo=mech['din_connectors']['middle']['mount_surface_z_mm'];travel=mech['service']['extraction_mm']
    top=max([z1]+[h['rear_projection_z_mm'][1] for h in mech['service']['core_handles']])
    return {'lo':[x0,y0,lo],'hi':[x1,y1,top+travel],'basis':'core outline XY from the mated DIN plane to the handle tops plus the 40 mm withdrawal'}


def max_radius(geo,link,spec,obs,params,bund,limit=15.0):
    """Largest uniform bend radius (0.25 mm steps from the design radius) at which every fillet fits and every clearance holds."""
    r=params['design_bend_radius_mm']['value'];best=None;lead=params['straight_lead_mm']['value'];m=params['placement_margin_mm']['value']
    while r<=limit+1e-9:
        try:route=fillet_route(route_vertices(geo,link,spec),r,(lead,lead))
        except ValueError:break
        known,_=evaluate_route(samples(route,bund,spec.get('flat')),obs,m,link)
        if known and min(known.values())<m:break
        best=r;r+=0.25
    return best


def sweep_screen(geo,obs,margin):
    """Release sweeps expanded by the placement margin against known obstacles (3D) and foreign XY; also the smallest gaps."""
    out={}
    for ref,g in sorted(geo.items()):
        s0=[g['sweep']['box_mm'][0],g['sweep']['box_mm'][1],g['sweep']['z_mm'][0]];s1=[g['sweep']['box_mm'][2],g['sweep']['box_mm'][3],g['sweep']['z_mm'][1]]
        lo=[v-margin for v in s0];hi=[v+margin for v in s1]
        known=[];foreign=[];gaps=[]
        for o in obs:
            if o['link']==g['link'] or o['id'].startswith('board:'+g['board']):continue
            if o['kind']=='unknown_depth' or all(o['lo'][i]<s1[i]+5 and o['hi'][i]>s0[i]-5 for i in range(3)):
                d=gap2([s0[0],s0[1],s1[0],s1[1]],[o['lo'][0],o['lo'][1],o['hi'][0],o['hi'][1]]) if o['kind']=='unknown_depth' else box_distance_boxes(s0,s1,o['lo'],o['hi'])
                if d<5 and not (o['kind']=='unknown_depth' and shielded([max(o['lo'][0],lo[0]),max(o['lo'][1],lo[1]),min(o['hi'][0],hi[0]),min(o['hi'][1],hi[1])],s0[2],obs)):gaps.append((r6(d),o['id']))
            if not all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(2)):continue
            if o['kind']=='unknown_depth':
                rect=[max(o['lo'][0],lo[0]),max(o['lo'][1],lo[1]),min(o['hi'][0],hi[0]),min(o['hi'][1],hi[1])]
                if lo[2]<o['hi'][2] and not shielded(rect,s0[2],obs):foreign.append({'ref':o['id'].split(':',1)[1],'max_foreign_top_z_mm':r6(lo[2]),'max_rear_side_height_mm':r6(lo[2]-o['lo'][2])})
            elif all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3)):known.append(o['id'])
        out[ref]={'moved':g['moved'],'sweep':g['sweep'],'margin_mm':margin,'known_overlaps':sorted(known),'foreign_xy_overlaps':sorted(foreign,key=lambda x:x['ref']),
            'nearest_gaps_mm':[{'id':i,'gap_mm':d} for d,i in sorted(gaps)[:4]]}
    return out


def notch_need(rf,smp,obs,margin,rail_top,allow):
    """Smallest top notch the route's samples need where they pass over the rail, against the proposal."""
    rail=next(o for o in obs if o.get('base')==rf['obstacle'] and o['id'].endswith(rf['id']+':floor'))
    pts=[(p,r) for p,r in smp if rail['lo'][0]-r-margin<p[0]<rail['hi'][0]+r+margin and p[2]-r-margin<rail_top+1e-9]
    need(pts,'route passes the notch '+rf['id'])
    window=[r6(min(p[1]-r-margin for p,r in pts)),r6(max(p[1]+r+margin for p,r in pts))];top=r6(min(p[2]-r-margin for p,r in pts))
    need(rf['y_mm'][0]<=window[0] and rf['y_mm'][1]>=window[1] and rf['relieved_top_z_mm']<=top,'proposed notch smaller than the route needs '+rf['id'])
    lo_=math.floor((window[0]-allow)*10+1e-6)/10;hi_=math.ceil((window[1]+allow)*10-1e-6)/10;zt=math.floor((top-allow)*10+1e-6)/10
    need([rf['y_mm'][0],rf['y_mm'][1],rf['relieved_top_z_mm']]==[lo_,hi_,zt],f"proposed notch {rf['id']} is not the minimum plus allowance: expected y {lo_}-{hi_}, top {zt}")
    return window,top


def rail_impact(mech,reliefs,needs,params):
    f=mech['carrier_frames']['middle'];depth=f['z_mm'][1]-f['z_mm'][0];width=params['rail_section_mm']['width'];out=[]
    need(depth==params['rail_section_mm']['depth'],'rail depth from Stage10')
    tabs=[t for t in f['mount_tabs']['boxes_mm']];rail=f['rails_boxes_mm'][0]
    for rf in reliefs:
        h=rf['relieved_top_z_mm']-f['z_mm'][0];win,top=needs[rf['id']]
        near=min(min(abs(rf['y_mm'][0]-t[3]),abs(t[1]-rf['y_mm'][1])) for t in tabs)
        out.append({'id':rf['id'],'obstacle':rf['obstacle'],'link':rf['link'],'y_mm':rf['y_mm'],'length_mm':r6(rf['y_mm'][1]-rf['y_mm'][0]),'relieved_top_z_mm':rf['relieved_top_z_mm'],
            'notch_depth_mm':r6(f['z_mm'][1]-rf['relieved_top_z_mm']),'remaining_depth_mm':r6(h),'remaining_fraction':r6(h/depth),
            'local_section_inertia_ratio':r6((h/depth)**3),'local_section_modulus_ratio':r6((h/depth)**2),'section_mm':[width,r6(h)],
            'route_needs':{'y_window_mm':win,'max_top_z_mm':top},'distance_to_nearest_mount_tab_mm':r6(near),
            'rail_span_y_mm':[rail[1],rail[3]],'strength':'NOT_CALCULATED; the Stage10 planning model covers only the straight crossmember surrogate',
            'status':rf['status']})
    return out


def evaluate(c,mech,lock,params,approval):
    moves=c['header_moves'];geo=header_geometry(mech,moves);moved=check_header_moves(mech,geo,moves,approval)
    for rf in c['rail_reliefs']:need(rf['obstacle'] in approval['changeable']['carrier_local_shape'],'carrier change outside the approval '+rf['id'])
    obs=obstacles(moved_mech(mech,geo),lock,params,c['rail_reliefs']);m=params['placement_margin_mm']['value'];lead=params['straight_lead_mm']['value']
    rad=params['design_bend_radius_mm']['value'];cutv,cutt=params['stage10_cut_mm']['value'];env=core_envelope(mech);routes={};smp={};needs={};centre={}
    for link in LINKS:
        spec=c['routes'][link];bund=bundle(params,link,spec['dressing']);v=route_vertices(geo,link,spec)
        for end,(p,q) in (('local',(v[0],v[1])),('middle',(v[-1],v[-2]))):
            g=geo[ENDS[link][0 if end=='local' else 1]];d=unit(sub(q,p))
            need(abs(d[2]-g['axis'])<1e-9,f'{link} {end} route must leave the housing along its axis')
        route=fillet_route(v,rad,(lead,lead));smp[link]=samples(route,bund,spec.get('flat'));centre[link]=route['dense']
        known,depth=evaluate_route(smp[link],obs,m,link)
        cases=release_cases(geo,link,spec,params);installed=route['length_mm']+2*MATED_MM;need(abs(cases[0]['length_mm']-installed)<1e-9,'release base case')
        delta=[c['length_mm']-installed for c in cases];req=installed+max(delta)+params['service_slack_mm']['value']
        core=min(box_distance(p,env['lo'],env['hi'])-r for p,r in smp[link])-STEP_MM/2
        a,b=(geo[r] for r in ENDS[link])
        routes[link]={'dressing':bund,'flat_legs':spec.get('flat'),'vertices_mm':[p6(x) for x in v],'bends':route['bends'],'legs_mm':route['legs_mm'],
            'exit_axis':{'local':'+z' if a['axis']>0 else '-z','middle':'+z' if b['axis']>0 else '-z'},'straight_from_exit_mm':dict(zip(('local','middle'),route['straight_from_exit_mm'])),
            'design_bend_radius_mm':rad,'max_uniform_radius_mm':max_radius(geo,link,spec,obs,params,bund),
            'installed_pad_to_pad_design_length_mm':r6(installed),
            'release_cases':[release_row(c,d,bund,spec,obs,m,link) for c,d in zip(cases,delta)],'release_extra_length_mm':[r6(x) for x in delta],'required_length_rule_mm':r6(req),
            'required_length_rule':'installed filleted length + largest bend-feasible release extra + Stage10 service slack',
            'release_dip_envelope_bottom_z_mm':r6(min(c['lowest_centreline_z_mm'] for c in cases)-bund['round_radius_mm']),
            'design_length_proposal_mm':math.ceil(req),'design_length_excess_over_installed_mm':r6(math.ceil(req)-installed),
            'slack_storage':'the free loop at the local end must take the excess; NOT_RUN (M-12)',
            'stage10_cut_mm':f'{cutv}±{cutt}','stage10_cut_covers_rule':cutv-cutt>=req,
            'min_surface_clearance_mm':r6(min(known.values())) if known else None,'required_surface_clearance_mm':m,
            'nearest_keep_outs_mm':[{'id':k,'surface_clearance_mm':v} for k,v in list(known.items())[:8]],'clear_of_known_keep_outs':(not known) or min(known.values())>=m,
            'foreign_depth_bounds':depth,'core_motion_clearance_mm':r6(core),'length_status':'DESIGN_LENGTH_PROPOSAL; not measured, not a cut length'}
        for rf in c['rail_reliefs']:
            if rf['link']==link:needs[rf['id']]=notch_need(rf,smp[link],obs,m,mech['carrier_frames']['middle']['z_mm'][1],params['notch_allowance_mm']['value'])
    gap,at=cable_gap(smp['J-SIG'],smp['J-PWR'])
    sweeps=sweep_screen(geo,obs,m)
    for ref in moves:need(not sweeps[ref]['known_overlaps'],'moved header sweep overlaps a known obstacle '+ref)
    rails=rail_impact(mech,c['rail_reliefs'],needs,params)
    spare=min([routes[k]['min_surface_clearance_mm']-m for k in LINKS]+[gap-m])
    k1=all(routes[k]['clear_of_known_keep_outs'] for k in LINKS) and gap>=m
    k2=all(not s['foreign_xy_overlaps'] for s in sweeps.values())
    allow=params['foreign_depth_cap_reference_mm']['value']-params['foreign_pcb_rear_z_mm']['value']
    worst=min([b['max_rear_side_height_mm'] for k in LINKS for b in routes[k]['foreign_depth_bounds'].values()],default=None)
    k3=worst is None or worst>=allow-1e-9;k4=spare>=params['robust_spare_mm']['value']-1e-9
    failed=[k for k,v in (('K1',k1),('K2',k2),('K3',k3),('K4',k4)) if not v]
    status='REJECTED' if not k1 else 'REJECTED_BY_CRITERIA' if failed else 'RECOMMENDABLE_UNDER_MODEL_CONDITIONS'
    return {'id':c['id'],'title':c['title'],'comparison_axes':c['comparison_axes'],'header_moves':moved,'rail_reliefs':rails,'routes':routes,
        'cable_to_cable':{'min_surface_gap_mm':gap,'required_mm':m,'clear':gap>=m,'closest_points_mm':at},
        'release_sweeps':sweeps,'retention':c['retention'],'assembly':c['assembly'],
        'service':{'K-PWR_first_then_core_40mm':'unchanged; neither cable attaches to the core','core_motion_envelope':env,
            'min_core_motion_clearance_mm':min(routes[k]['core_motion_clearance_mm'] for k in LINKS)},
        'criteria':{'K1':k1,'K2':k2,'K3':k3,'K4':k4},'tightest_spare_beyond_margin_mm':r6(spare),
        'tightest_spare_note':'sampled clearance minus the 0.1 mm sampling deduction (0.2 mm for cable to cable); the exact geometric spare is up to that much larger',
        'tightest_sweep_gap_mm':min(x['gap_mm'] for v in sweeps.values() for x in v['nearest_gaps_mm']),
        'smallest_foreign_rear_side_allowance_mm':worst,'status':status,'failed_criteria':failed,
        'physical':'NOT_RUN; centreline and envelope clearance is not physical non-interference'},obs,geo,{'samples':smp,'centre':centre}


def stage30_screen(mech,lock,params,route30):
    """Re-run the Stage30 J-PWR waypoint candidates through the Stage31 checks; all must be rejected."""
    geo=header_geometry(mech,{});m=params['placement_margin_mm']['value'];lead=params['straight_lead_mm']['value'];rad=params['design_bend_radius_mm']['value']
    bund=bundle(params,'J-PWR','ROUND_BUNDLE');allow=params['foreign_depth_cap_reference_mm']['value']-params['foreign_pcb_rear_z_mm']['value'];out=[]
    for c in route30['candidates']:
        mod=c.get('modification');obs=obstacles(mech,lock,params,[] if not mod else [{'id':'W4','obstacle':mod['obstacle'],'y_mm':mod['y_mm'],'relieved_top_z_mm':mod['relieved_top_z_mm']}])
        reasons=['no J-SIG route: Stage30 studied J-PWR only and the J-SIG proxies still cross rail:middle:0']
        v=route_vertices(geo,'J-PWR',{'waypoints_mm':c['waypoints_mm']})
        try:route=fillet_route(v,rad,(lead,lead))
        except ValueError as e:reasons.append('bend: '+str(e));route=fillet_route(v,1e-6,(0.0,0.0))
        known,depth=evaluate_route(samples(route,bund),obs,m,'J-PWR')
        hit=[k for k,d in known.items() if d<m]
        if hit:reasons.append('keep-out clearance below the margin: '+', '.join(hit[:6]))
        low=[k for k,b in depth.items() if b['max_rear_side_height_mm']<allow]
        if low:reasons.append('needs foreign rear-side height below 12.4 mm at '+', '.join(low))
        need(len(reasons)>1,'Stage30 candidate unexpectedly passes '+c['id'])
        out.append({'id':c['id'],'title':c['title'],'stage30_status':None,'stage31_status':'REJECTED','reasons':reasons})
    return out


def straight_proxy_crossings(mech,ledger28):
    rail=next(b for b in [mech['carrier_frames']['middle']['rails_boxes_mm'][0]]);z0,z1=mech['carrier_frames']['middle']['z_mm']
    out={}
    for r in ledger28['conductors']:
        if r['link'] not in LINKS:continue
        a,b=r['end_a']['pad_xyz_mm'],r['end_b']['pad_xyz_mm']
        out[r['id']]=s28.segment_box(a,b,[rail[0],rail[1],z0],[rail[2],rail[3],z1])
    return out


def copper_impact(graph,paths,stage16,design,mech,geo):
    """Stage10 trace-length allocations for copper edges that end on a moved header pin, over the Stage30 design DIN XY; routed copper NOT RUN."""
    base=s30.impact(graph,paths,stage16,design,mech);alloc={i:e['allocated_developed_mm'] for i,e in enumerate(graph['edges'])}
    for e in base['edges']:alloc[e['edge_index']]=e['design_allocation_mm']
    nodes=copy.deepcopy(graph['nodes'])
    for s_,pads in design.items():
        for p,v in pads.items():nodes['DIN:'+s30.NODE_SIDE[s_]+':'+p]['pad_xyz_mm']=v[0]
    moved={ref for ref,g in geo.items() if g['moved']}
    for ref in moved:
        for pin,v in geo[ref]['pads_xyz_mm'].items():
            key=ref+':'+pin
            if key in nodes:need(nodes[key]['ref']==ref and nodes[key]['pin']==pin,'graph node identity '+key);nodes[key]['pad_xyz_mm']=v[0]
    edges=[];new=dict(alloc)
    for i,e in enumerate(graph['edges']):
        if not {graph['nodes'][e['from']].get('ref'),graph['nodes'][e['to']].get('ref')}&moved:continue
        need(e['net']==nodes[e['from']]['net']==nodes[e['to']]['net'],'edge net identity '+str(i))
        if e['kind']=='GH_harness':
            edges.append({'edge_index':i,'kind':e['kind'],'net':e['net'],'from':e['from'],'to':e['to'],'stage30_allocation_mm':r6(alloc[i]),'stage31_allocation_mm':r6(alloc[i]),
                'delta_mm':0.0,'model':'GH harness allocation kept (history); the Stage31 design length is reported per route'});continue
        a,b=nodes[e['from']]['pad_xyz_mm'],nodes[e['to']]['pad_xyz_mm'];new[i]=interfaces.trace_length(a,b)
        edges.append({'edge_index':i,'kind':e['kind'],'net':e['net'],'from':e['from'],'to':e['to'],'stage31_straight_mm':r6(math.dist(a,b)),
            'stage30_allocation_mm':r6(alloc[i]),'stage31_allocation_mm':r6(new[i]),'delta_mm':r6(new[i]-alloc[i]),'routed_copper_mm':None,
            'model':'Stage10 trace_length: 1.15 octile XY + 7 mm + |dz|'})
    rows={}
    for name,metric in (('signal_net_paths','complete_net_pad_path_allocation_mm'),('power_and_return_endpoint_paths','allocated_developed_mm'),('local_endpoint_paths','complete_net_pad_path_allocation_mm')):
        rows[name]=[]
        for r in paths[name]:
            a=sum(alloc[j] for j in r['edge_indices']);b=sum(new[j] for j in r['edge_indices'])
            if abs(b-a)<1e-9:continue
            rows[name].append({'net':r['net'],'from':r.get('from',r.get('source_boundary')),'to':r['to'],'stage30_design_allocation_mm':r6(a),'stage31_allocation_mm':r6(b),'delta_mm':r6(b-a),'routed_mm':None})
    return {'moved_headers':sorted(moved),'edges':edges,'paths':rows,'status':'ALLOCATION_MODEL_ONLY; routed copper NOT RUN; production copper NOT BOUND'}


def identity(data,geo_all,ledger28,report28,policy28,inventory,graph):
    harness=s30.harness_preserved(ledger28,report28,inventory,policy28)
    gh=[e for e in graph['edges'] if e['kind']=='GH_harness' and graph['nodes'][e['from']]['ref'] in (ENDS['J-SIG'][0],ENDS['J-PWR'][0])]
    need(len(gh)==11 and all(graph['nodes'][e['from']]['pin']==graph['nodes'][e['to']]['pin'] for e in gh),'11 J-SIG/J-PWR harness conductors pin-to-pin')
    for cid,geo in geo_all.items():
        for ref,g in geo.items():need(g['pins']==data['mech']['headers'][ref]['pins'] and g['header_mpn']==data['mech']['headers'][ref]['header_mpn'],'header identity '+cid+' '+ref)
    return {'harness':harness,'J_SIG_J_PWR_conductors':[{'from':e['from'],'to':e['to'],'net':e['net']} for e in gh],'stage15_edges':len(graph['edges']),
        'panel_lock_sha256':sha(ROOT/'design/grid/placements.lock.json'),'stage30_design_contact_map_sha256':sha(ROOT/REL/'stage30/design-contact-map.json'),
        'header_pins_and_mpns':'unchanged for all four J-SIG/J-PWR headers in every candidate','DIN_mapping':'Stage30 DESIGN_ONLY_PROVISIONAL positions, unchanged'}


# ---------- build ----------
PARAM_CLASSES={'MAKER_SPEC_RANGE','MAKER_SPEC_REFERENCE','UNKNOWN','PROJECT_DATA','DESIGN_MODEL','STAGE30_ASSUMPTION','DESIGN_CHOICE','STAGE10_PROPOSAL','STAGE10_CONDITIONAL'}


def load():
    return {'approval':read(OUT/'approval.json'),'input':read(OUT/'design-input.json'),'route30':read(ROOT/REL/'stage30/route-input.json'),'report30':read(ROOT/REL/'stage30/report.json'),
        'graph':read(ROOT/REL/'stage15/interfaces-report.json'),'paths':read(ROOT/REL/'stage15/paths-report.json'),'stage16':read(ROOT/REL/'stage16/inputs-report.json'),
        'ledger28':read(ROOT/REL/'stage28/harness-ledger.json'),'report28':read(ROOT/REL/'stage28/report.json'),'policy28':read(ROOT/REL/'stage28/harness-policy.json'),
        'lock':read(ROOT/'design/grid/placements.lock.json')}


def validate_inputs(data):
    a=data['approval'];inp=data['input']
    need(a['status']=='DESIGN_STUDY_CHANGES_ALLOWED' and a['decided_by']=='OWNER','owner approval record')
    need(set(a['changeable']['header_refs'])=={r for l in LINKS for r in ENDS[l]} and a['changeable']['carrier_local_shape']==['rail:middle:0'],'approval scope')
    need(inp['status']=='DESIGN_STUDY_INPUT_NOT_MEASURED','design input status');s28.no_claims(inp,'design-input');s28.no_claims(a,'approval')
    for k,v in inp['parameters'].items():need(v['class'] in PARAM_CLASSES,'parameter class '+k)
    need(inp['parameters']['wire_od_mm']['value']==max(inp['parameters']['wire_od_mm']['range']),'envelopes use the maximum JST insulation OD')
    need(inp['parameters']['foreign_depth']['value'] is None and inp['parameters']['bend_radius_maker_value']['value'] is None,'unknowns stay null')
    need(data['report30']['status']=='DESIGN_ONLY_PROVISIONAL','Stage30 DIN positions are the provisional design data')
    need([c['id'] for c in inp['candidates']]==['A','B','C'],'at most three candidates A/B/C')


def build(data,preserve=True):
    validate_inputs(data)
    s29data,cmap,_=s30.stage29_current();mech=s29data['mech'];design=s30.design_positions(cmap);data=dict(data,mech=mech)
    committed={r['graph_node']:r['design_xy_mm'] for r in read(ROOT/REL/'stage30/design-contact-map.json')['contacts']}
    need(committed=={'DIN:'+s30.NODE_SIDE[side]+':'+p:v[0][:2] for side,pads in design.items() for p,v in pads.items()},'Stage30 committed design positions')
    params=data['input']['parameters'];results=[];geos={};samples_={};obs_={}
    for c in data['input']['candidates']:
        r,obs,geo,smp=evaluate(c,mech,data['lock'],params,data['approval']);results.append(r);geos[c['id']]=geo;samples_[c['id']]=smp;obs_[c['id']]=obs
    passing=[r['id'] for r in results if all(r['criteria'].values())]
    need(passing==[data['input']['recommendation']['id']],'recommendation must be the only candidate meeting K1-K4: '+str(passing))
    screen=stage30_screen(mech,data['lock'],params,data['route30'])
    for w in screen:w['stage30_status']=data['report30']['route_study']['results'][w['id']]
    proxies=straight_proxy_crossings(mech,data['ledger28']);need(all(proxies.values()) and len(proxies)==11,'straight J-SIG/J-PWR proxies cross the middle rail (Stage30 finding)')
    copper={cid:copper_impact(data['graph'],data['paths'],data['stage16'],design,mech,geos[cid]) for cid in geos if any(g['moved'] for g in geos[cid].values())}
    ident=identity(data,geos,data['ledger28'],data['report28'],data['policy28'],s29data['inventory'],data['graph'])
    rec=next(r for r in results if r['id']==data['input']['recommendation']['id'])
    meas=[]
    for m in data['input']['pre_prototype_measurements']:
        row=dict(m,status='NOT_RUN',value=None)
        if m['id']=='M31-05':row['bounds']={k:{f:b['max_foreign_top_z_mm'] for f,b in rec['routes'][k]['foreign_depth_bounds'].items()} for k in LINKS}
        if m['id']=='M31-02':row['route_max_uniform_radius_mm']={k:rec['routes'][k]['max_uniform_radius_mm'] for k in LINKS}
        if m['id']=='M31-08':row['design_length_proposal_mm']={k:rec['routes'][k]['design_length_proposal_mm'] for k in LINKS}
        meas.append(row)
    common={'status':'DESIGN_STUDY_INPUT_NOT_MEASURED','parameters':params,'headers_stage10':{ref:{k:g[k] for k in ('board','face_z_mm','axis','origin_mm','box_mm','exit_mm','sweep','header_mpn','housing_mpn','pins')} for ref,g in geos['A'].items()},
        'obstacle_classes':{k:sum(1 for o in obs_['A'] if o['id'].split(':')[0]==k) for k in sorted({o['id'].split(':')[0] for o in obs_['A']})},
        'not_modelled':['other harness cables (C-SIG, K-PWR, tails) as routed bodies','GHR housing latch geometry beyond the Stage10 sweep','fan-out and gather transitions of flat legs','twist of the conductors',
            'foreign PCB outlines (only per-part XY projections are known); the release dips and the panel-side reach to the middle headers pass the foreign PCB plane z 20-21.6',
            'the real GH unmating travel; the Stage10 15 mm axial release is used for every release case'],
        'straight_proxies_cross_rail_middle_0':proxies}
    report={'status':'DESIGN_STUDY_ONLY','approval':{k:data['approval'][k] for k in ('date','decided_by','status','scope_excludes')},
        'candidates':{r['id']:{'title':r['title'],'status':r['status'],'criteria':r['criteria'],'tightest_spare_beyond_margin_mm':r['tightest_spare_beyond_margin_mm'],
            'smallest_foreign_rear_side_allowance_mm':r['smallest_foreign_rear_side_allowance_mm'],
            'design_length_proposal_mm':{k:r['routes'][k]['design_length_proposal_mm'] for k in LINKS},'notches':[{k:n[k] for k in ('id','y_mm','notch_depth_mm','remaining_depth_mm')} for n in r['rail_reliefs']],
            'moved_headers':[{k:h[k] for k in ('ref','from_origin_mm','to_origin_mm','rotation_deg')} for h in r['header_moves']]} for r in results},
        'recommendation':dict(data['input']['recommendation'],verified_unique=True),'stage30_screen':{w['id']:w['stage31_status'] for w in screen},
        'measurements':meas,'identity':ident,
        'decision_status':{'route':'RECOMMENDED_FOR_NEXT_PROTOTYPE_STUDY (B); not adopted','rail_change':'PROPOSAL_NOT_ADOPTED','header_moves':'PROPOSAL_NOT_ADOPTED; canonical CAD unchanged',
            'D02':'CONFLICT_REQUIRES_DECISION (unchanged)','M-01':'NOT_RUN','M-09':'NOT_RUN','M-12':'NOT_RUN','rail_strength':'NOT_CALCULATED','cable_lengths':'DESIGN_LENGTH_PROPOSAL; not measured, not cut'},
        'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,
        'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('approval.json','design-input.json','README.md')]+[ROOT/REL/p for p in ('stage30/route-input.json','stage30/report.json','stage30/design-contact-map.json','stage29/contact-map.json',
        'stage15/interfaces-report.json','stage15/paths-report.json','stage16/inputs-report.json','stage28/harness-ledger.json','stage28/report.json','stage28/harness-policy.json',
        'stage10/mechanical-report.json','stage10/mechanical-input.json')]+[ROOT/'design/grid/placements.lock.json']
    files+=[ROOT/p for p in ('.claude/skills/component-jst-gh/facts.json','.claude/skills/component-qingpu-wqp518ma/facts.json','.claude/skills/component-dailywell-2ms1t1b1m2qes-5/facts.json','.claude/skills/component-passives-family/facts.json')]
    files+=[Path(__file__).with_name(n) for n in ('test_stage31_cable_entry_redesign.py','stage30_din_design_integration.py','stage29_din_column_reversal.py','stage28_din_harness.py','stage10_interfaces.py','assembly.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return {'common':common,'candidates':results,'screen':screen,'copper':copper,'report':report,'geo':geos,'samples':samples_,'obs':obs_,'mech':mech}


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed: '+', '.join(sorted(set(changed)-MUTABLE)))
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage31/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


# ---------- rendering ----------
def esc(v):return html.escape(str(v),quote=True)
def f2(v):return '–' if v is None else f'{v:.2f}'
COLOR={'J-SIG':'#1f5fbf','J-PWR':'#c0392b'}


def render_md(b,inp):
    rs=b['candidates'];rep=b['report']
    L=['# Stage31 cable-entry comparison (generated)','','Design study only. All values come from planning geometry and stated assumptions; nothing here is measured, and a clear envelope is not physical non-interference. Design lengths are not cut lengths.','',
       '## Criteria','']
    for k,v in inp['recommendation']['criteria'].items():L.append(f'- **{k}:** {v}')
    L+=['','| Candidate | Headers | Rail | Dressing | K1 | K2 | K3 | K4 | Tightest spare (mm) | Smallest foreign rear-side allowance (mm) | Design length J-SIG / J-PWR (mm) |','|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rs:
        a=r['comparison_axes'];c=r['criteria'];yn=lambda x:'yes' if x else '**no**'
        L.append(f"| {r['id']} | {a['headers']} | {a['rail']} | {a['dressing']} | {yn(c['K1'])} | {yn(c['K2'])} | {yn(c['K3'])} | {yn(c['K4'])} | {f2(r['tightest_spare_beyond_margin_mm'])} | {f2(r['smallest_foreign_rear_side_allowance_mm'])} | {r['routes']['J-SIG']['design_length_proposal_mm']} / {r['routes']['J-PWR']['design_length_proposal_mm']} |")
    L+=['',f"Recommended: **{inp['recommendation']['id']}** (the only candidate that meets K1-K4).",'']
    for t in inp['recommendation']['rationale']:L.append('- '+t)
    for r in rs:
        L+=['',f"## {r['id']}: {r['title']}",'']
        for h in r['header_moves']:L.append(f"- Header move: {h['ref']} {h['from_origin_mm']} → {h['to_origin_mm']}, rotation {h['rotation_deg']}°, pin row along {h['pin_row_axis']}; nearest other sweep gap {h['sweep_gap_to_other_headers']['gap_mm'] if h['sweep_gap_to_other_headers'] else '–'} mm")
        for n in r['rail_reliefs']:
            L.append(f"- Notch {n['id']} ({n['link']}): y {n['y_mm'][0]}–{n['y_mm'][1]} ({n['length_mm']} mm), top z {n['relieved_top_z_mm']} → {n['notch_depth_mm']} mm deep, {n['remaining_depth_mm']} mm of 12 left (local I ratio {n['local_section_inertia_ratio']:.3f}); route needs y {n['route_needs']['y_window_mm'][0]:.2f}–{n['route_needs']['y_window_mm'][1]:.2f} and top ≤ {n['route_needs']['max_top_z_mm']:.2f}. Strength NOT_CALCULATED.")
        if not r['rail_reliefs']:L.append('- Rail unchanged.')
        L+=['','| Cable | Dressing | Installed pad-to-pad (mm) | Release extra (mm) | Design length proposal (mm) | Straight lead local / middle (mm) | Bends (r 5) | Max uniform r (mm) | Min surface clearance (mm) | Nearest keep-outs | Foreign bounds (max top z) | Core motion clearance (mm) |','|---|---|---|---|---|---|---|---|---|---|---|---|']
        for k in LINKS:
            R=r['routes'][k];near=', '.join(f"{x['id']} {f2(x['surface_clearance_mm'])}" for x in R['nearest_keep_outs_mm'][:3]);fb=', '.join(f"{a} ≤ {f2(v['max_foreign_top_z_mm'])}" for a,v in R['foreign_depth_bounds'].items()) or 'none'
            L.append(f"| {k} | {R['dressing']['kind']} | {f2(R['installed_pad_to_pad_design_length_mm'])} | {max(R['release_extra_length_mm']):.2f} | {R['design_length_proposal_mm']} | {R['straight_from_exit_mm']['local']} / {R['straight_from_exit_mm']['middle']} | {len(R['bends'])} | {f2(R['max_uniform_radius_mm'])} | {f2(R['min_surface_clearance_mm'])} | {near} | {fb} | {f2(R['core_motion_clearance_mm'])} |")
        cc=r['cable_to_cable'];L+=['',f"- Cable to cable: minimum surface gap {f2(cc['min_surface_gap_mm'])} mm (required {cc['required_mm']}). Tightest spare {f2(r['tightest_spare_beyond_margin_mm'])} mm after the sampling deduction.",
            f"- Release sweeps: smallest gap {f2(r['tightest_sweep_gap_mm'])} mm to any known obstacle or foreign XY (required {cc['required_mm']}).",
            '- Release cases (bend-feasible surrogate, 15 mm travel): '+'; '.join(f"{k} extra {', '.join(f'{x:.1f}' for x in r['routes'][k]['release_extra_length_mm'][1:])} mm, envelope dips to z {r['routes'][k]['release_dip_envelope_bottom_z_mm']:.1f}" for k in LINKS)+'.',
            '- Release sweeps over foreign XY: '+('; '.join(f"{ref.split(':',1)[1]}: "+', '.join(x['ref'] for x in v['foreign_xy_overlaps']) for ref,v in r['release_sweeps'].items() if v['foreign_xy_overlaps']) or 'none')+'.',
            f"- Core withdrawal: minimum clearance {f2(r['service']['min_core_motion_clearance_mm'])} mm to the core motion box; K-PWR first, then 40 mm, unchanged.",'- Retention:']
        for t in r['retention']:L.append(f"  - {t['id']} ({t['link']}) at {t['at']}: {t['kind']}; dimensions null.")
        L.append('- Assembly (NOT RUN):')
        for i,t in enumerate(r['assembly'],1):L.append(f'  {i}. {t}')
    L+=['','## Stage30 candidates rejected again','','| Stage30 | Stage30 status | Stage31 reasons |','|---|---|---|']
    for w in b['screen']:L.append(f"| {w['id']} | {w['stage30_status']} | {'; '.join(w['reasons'])} |")
    for cid,c in b['copper'].items():
        L+=['',f'## Copper allocations for the moved headers ({cid})','','Stage10 trace-length model over the Stage30 design DIN XY; routed copper NOT RUN.','','| Edge | Kind | Net | From → To | Stage30 (mm) | Stage31 (mm) | Δ (mm) |','|---|---|---|---|---|---|---|']
        for e in c['edges']:
            if e['kind']!='GH_harness':L.append(f"| {e['edge_index']} | {e['kind']} | {e['net']} | {e['from']} → {e['to']} | {f2(e['stage30_allocation_mm'])} | {f2(e['stage31_allocation_mm'])} | {e['delta_mm']:+.2f} |")
        L.append(f"\nPaths changed: {', '.join(f'{k} {len(v)}' for k,v in c['paths'].items())}.")
    L+=['','## Measurements before a prototype (all NOT RUN)','']
    for m in rep['measurements']:L.append(f"- **{m['id']}** {m['item']}. {m['why']}.")
    return '\n'.join(L)+'\n'


def render_svg(r,obs,geo,sm,mech):
    """Plan (XY), side (XZ, service) and rail-entry section (YZ) of one candidate; stroke widths show the modelled envelope."""
    smp=sm['samples'];W,H=760,700;out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif" font-size="9">','<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="10" y="16" font-size="12" font-weight="bold">Stage31 candidate {esc(r["id"])}: {esc(r["title"])}</text>',
        '<text x="10" y="30">Design study only: modelled envelopes are not physical clearance. Blue J-SIG, red J-PWR; the wide stroke is the modelled bundle diameter. Dashed boxes are release sweeps.</text>',
        '<text x="10" y="42">Steel = carrier rails/crossmembers/tabs; orange = rail left under a proposed notch, dashed orange = material removed; green outline = A01 boards; tan = A01 parts (3 mm assumed);</text>',
        '<text x="10" y="54">light grey = foreign part XY (plan) or the foreign PCB rear (side/section); the depth behind it is unknown and is reported as a bound.</text>']
    win={'plan':(195,300,138,200),'side':(195,300,18,118),'sec':(150,195,28,54)}
    def panel(ox,oy,sc,ux,uy,a,b_,c,d,title,axes):
        out.append(f'<text x="{ox}" y="{oy-6}" font-weight="bold">{esc(title)}</text><rect x="{ox}" y="{oy}" width="{(b_-a)*sc}" height="{(d-c)*sc}" fill="none" stroke="#999"/>')
        out.append(f'<text x="{ox}" y="{oy+(d-c)*sc+12}">{esc(axes)}</text>')
        return lambda p:(ox+(p[ux]-a)*sc,oy+((d-p[uy]) if uy==2 else (p[uy]-c))*sc)
    views=[('plan',panel(20,74,3.0,0,1,*win['plan'],'Plan (board XY; +x right, +y down)','x 195–300 mm, y 138–200 mm'),{0:win['plan'][:2],1:win['plan'][2:]},3.0),
           ('side',panel(370,74,2.6,0,2,*win['side'],'Side (XZ, y 140–192 projected): release and core service','x 195–300 mm, z 18–118 mm (+z up, toward the rear)'),{0:win['side'][:2],2:win['side'][2:]},2.6),
           ('sec',panel(20,342,7.0,1,2,*win['sec'],'Rail entry section through rail:middle:0 (x 242–248)','y 150–195 mm, z 28–54 mm; circles = envelope at x 245'),{1:win['sec'][:2],2:win['sec'][2:]},7.0)]
    def style(o):
        i=o['id']
        if i.startswith(('rail:','crossmember:','tab:')):return 'fill="#f0a85a" stroke="#a0581a" stroke-width="0.5"' if i.endswith(':floor') else 'fill="#9aa5b1" stroke="#4a5562" stroke-width="0.5"'
        if i.startswith('board:'):return 'fill="none" stroke="#2e7d32" stroke-width="0.8"'
        if o['kind']=='assumed_height':return 'fill="#f3e6c8" stroke="#b9a36b" stroke-width="0.3"'
        if o['kind']=='unknown_depth':return 'fill="#e6e6e6" stroke="#aaa" stroke-width="0.3"'
        return 'fill="#d0d0d0" fill-opacity="0.6" stroke="#888" stroke-width="0.3"'
    for name,T,ax,sc in views:
        for o in obs:
            if o['id'].startswith(('release:','foreign:')) or o['link']=='K-PWR' and o['id'].startswith('core'):continue
            lo=list(o['lo']);hi=list(o['hi'])
            if o['kind']=='unknown_depth':hi[2]=lo[2]+1.2
            if not all(hi[k]>v[0] and lo[k]<v[1] for k,v in ax.items()):continue
            if name=='sec' and not (hi[0]>242 and lo[0]<248):continue
            if name=='side' and not (hi[1]>140 and lo[1]<192):continue
            lo=[max(lo[k],ax[k][0]) if k in ax else lo[k] for k in range(3)];hi=[min(hi[k],ax[k][1]) if k in ax else hi[k] for k in range(3)]
            x0,y0=T(lo);x1,y1=T(hi);out.append(f'<rect x="{min(x0,x1):.2f}" y="{min(y0,y1):.2f}" width="{abs(x1-x0):.2f}" height="{abs(y1-y0):.2f}" {style(o)}/>')
        for o in obs:
            if not o['id'].endswith(':floor'):continue
            rail=mech['carrier_frames']['middle']['z_mm'][1];lo=[o['lo'][0],o['lo'][1],o['hi'][2]];hi=[o['hi'][0],o['hi'][1],rail]
            if name=='side' and not (hi[1]>140 and lo[1]<192):continue
            x0,y0=T(lo);x1,y1=T(hi);out.append(f'<rect x="{min(x0,x1):.2f}" y="{min(y0,y1):.2f}" width="{abs(x1-x0):.2f}" height="{abs(y1-y0):.2f}" fill="none" stroke="#d2691e" stroke-dasharray="2,1.5" stroke-width="0.8"/>')
        if name!='sec':
            for ref,g in sorted(geo.items()):
                lo=[g['sweep']['box_mm'][0],g['sweep']['box_mm'][1],g['sweep']['z_mm'][0]];hi=[g['sweep']['box_mm'][2],g['sweep']['box_mm'][3],g['sweep']['z_mm'][1]]
                x0,y0=T(lo);x1,y1=T(hi);out.append(f'<rect x="{min(x0,x1):.2f}" y="{min(y0,y1):.2f}" width="{abs(x1-x0):.2f}" height="{abs(y1-y0):.2f}" fill="none" stroke="{COLOR[g["link"]]}" stroke-dasharray="3,2" stroke-width="0.8"/>')
                if name=='plan':
                    bx=g['box_mm'];x0,y0=T([bx[0],bx[1],0]);x1,y1=T([bx[2],bx[3],0])
                    out.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" fill="{COLOR[g["link"]]}" fill-opacity="0.25" stroke="{COLOR[g["link"]]}" stroke-width="0.6"/>')
                    tx,ty=T(g['exit_mm']);out.append(f'<text x="{tx-14:.1f}" y="{ty+(-9 if g["end"]=="local" else 14):.1f}" fill="{COLOR[g["link"]]}">{esc(ref.split(":",1)[1])}{" (moved)" if g["moved"] else ""}</text>')
        if name=='side':
            co=mech['boards']['A01-core'];x0,y0=T([co['outline_mm'][0],0,co['z_mm'][0]+40]);x1,y1=T([co['outline_mm'][2],0,co['z_mm'][1]+40])
            out.append(f'<rect x="{x0:.2f}" y="{y1:.2f}" width="{x1-x0:.2f}" height="{y0-y1:.2f}" fill="none" stroke="#333" stroke-dasharray="4,2"/><text x="{x0-60:.1f}" y="{y1-4:.1f}">A01-core withdrawn 40 mm (after K-PWR is disconnected)</text>')
        for link in LINKS:
            if name=='sec':
                for p,rr in smp[link]:
                    if 242<=p[0]<=248 and abs(p[0]-245)<0.11:
                        x,y=T(p);out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rr*sc:.2f}" fill="{COLOR[link]}" fill-opacity="0.45" stroke="{COLOR[link]}" stroke-width="0.4"/>')
                continue
            pts=sm['centre'][link];rad=max(rr for _,rr in smp[link])
            path=' '.join(f'{x:.2f},{y:.2f}' for x,y in (T(p) for p in pts[::3]+[pts[-1]]))
            out.append(f'<polyline points="{path}" fill="none" stroke="{COLOR[link]}" stroke-opacity="0.4" stroke-width="{2*rad*sc:.2f}" stroke-linejoin="round" stroke-linecap="round"/>')
            out.append(f'<polyline points="{path}" fill="none" stroke="{COLOR[link]}" stroke-width="0.6"/>')
    y=572
    for k in LINKS:
        R=r['routes'][k];fb=', '.join(f"{a} ≤ z {v['max_foreign_top_z_mm']:.1f}" for a,v in R['foreign_depth_bounds'].items()) or 'none'
        out.append(f'<text x="20" y="{y}" fill="{COLOR[k]}">{esc(k)}: installed {R["installed_pad_to_pad_design_length_mm"]:.1f} mm; design length proposal {R["design_length_proposal_mm"]} mm (not a cut length); min surface clearance {R["min_surface_clearance_mm"]:.2f} mm (required 0.5)</text>')
        out.append(f'<text x="32" y="{y+12}" fill="{COLOR[k]}">{len(R["bends"])} bends at r 5; straight lead local {R["straight_from_exit_mm"]["local"]} / middle {R["straight_from_exit_mm"]["middle"]} mm; foreign parts must stay below: {esc(fb)}</text>');y+=28
    for n in r['rail_reliefs']:
        out.append(f'<text x="20" y="{y}">Notch {esc(n["id"])} ({esc(n["link"])}): y {n["y_mm"][0]}–{n["y_mm"][1]}, {n["notch_depth_mm"]} mm deep, {n["remaining_depth_mm"]} of 12 mm rail left; strength NOT_CALCULATED</text>');y+=12
    out.append(f'<text x="20" y="{y}">Criteria {esc(" ".join(k+(" yes" if v else " no") for k,v in r["criteria"].items()))}; status {esc(r["status"])}; physical NOT_RUN</text>')
    out.append('</svg>')
    return '\n'.join(out)+'\n'


def outputs(b,inp):
    cands=[{k:v for k,v in r.items()} for r in b['candidates']]
    o={'common-input.json':dump(b['common']),'candidates.json':dump({'status':'DESIGN_STUDY_ONLY','candidates':cands,'stage30_screen':b['screen']}),
       'comparison.md':render_md(b,inp),'copper-impact.json':dump(b['copper']),'report.json':dump(b['report'])}
    for r in b['candidates']:o[f'candidate-{r["id"]}.svg']=render_svg(r,b['obs'][r['id']],b['geo'][r['id']],b['samples'][r['id']],b['mech'])
    return o


def check_outputs(bodies):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage31-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            # Stage30 bytes are immutable from BASE; its deeper chain already passed there, so replay the Stage30 checks only.
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage30_din_design_integration.py','--check','--check-review'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage30_din_design_integration.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage30 source checkpoint (generator, review binding, tests normal and -O)')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage31/'+n for n in GENERATED}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-history','check-review'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.check_history:history()
    data=load();b=build(data);bodies=outputs(b,data['input'])
    need(set(bodies)==set(GENERATED),'generated file set')
    if a.check:check_outputs(bodies)
    else:
        for name,body in bodies.items():(OUT/name).write_text(body)
    if a.check_review:review()
    c=b['report']['candidates']
    print('PASS Stage31 source checks: '+'; '.join(f"{k} {v['status']} {''.join(x for x,y in v['criteria'].items() if y)}" for k,v in c.items())+f"; recommended {b['report']['recommendation']['id']}; Stage30 W1-W4 REJECTED; physical/native NOT RUN")


if __name__=='__main__':main()
