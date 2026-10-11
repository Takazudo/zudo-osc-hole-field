#!/usr/bin/env python3
"""Conditional fixed-tangent split-row sweep; source geometry, never native CAD."""
import argparse
import json
import math
import sys
from pathlib import Path
from importlib.metadata import version
import check as base
from clamps import assembly, exit_proof
import numpy as np
from scipy.optimize import brentq
from scipy.spatial import cKDTree
from numpy.polynomial.legendre import leggauss

HERE=Path(__file__).resolve().parent
V0=np.array([0.4717697145308489,0.6926204804756201,-0.5456282676669185])
V1=V0*np.array([1,-1,1])
TAIL=2.;LENGTH=64.;OFFSET=52.;HEIGHT=1.5;RADIUS=25.908
SIGNS=[1,-1,1,1,-1,1]
BRIDGE=HEIGHT/(-V0[2])
NODES,WEIGHTS=leggauss(96);T=(NODES+1)/2

def control(g,h):
    a=np.zeros(3);b=np.array([OFFSET,0,-g])
    return np.array([a+TAIL*V0,a+(TAIL+h)*V0,b-(TAIL+h)*V1,b-TAIL*V1])

def position(p,t):
    t=np.asarray(t)[:,None]
    return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]

def first(p,t):
    t=np.asarray(t)[:,None]
    return 3*((1-t)**2*(p[1]-p[0])+2*(1-t)*t*(p[2]-p[1])+t*t*(p[3]-p[2]))

def second(p,t):
    t=np.asarray(t)[:,None]
    return 6*((1-t)*(p[2]-2*p[1]+p[0])+t*(p[3]-2*p[2]+p[1]))

def arclength(p,n=96):
    if n==96:ts,ws=T,WEIGHTS
    else:xs,ws=leggauss(n);ts=(xs+1)/2
    return float(np.sum(ws*np.linalg.norm(first(p,ts),axis=1))/2)

def handle(g):
    return brentq(lambda h:arclength(control(g,h))-LENGTH,1,60,xtol=1e-12)

def product(a,b,c,d):
    z=np.array([a*c,a*d,b*c,b*d]);return z.min(axis=0),z.max(axis=0)

def radius_bound(lo,hi,ddlo,ddhi):
    speed=np.linalg.norm(np.maximum(0,np.maximum(lo,-hi)),axis=1)
    crosses=[]
    for i,j in ((1,2),(2,0),(0,1)):
        a,b=product(lo[:,i],hi[:,i],ddlo[:,j],ddhi[:,j]);c,d=product(lo[:,j],hi[:,j],ddlo[:,i],ddhi[:,i])
        crosses.append(np.maximum(abs(a-d),abs(b-c)))
    cross=np.linalg.norm(np.array(crosses).T,axis=1)
    return speed**3/np.maximum(cross,1e-30)

def sweep_cells(g0,g1,h0,h1,n=512):
    # h is bracketed by endpoint roots: length increases with g while P'_z<0,
    # and is convex in h, with chord length < LENGTH on the rising root branch.
    # Roots get a 1e-7 mm engineering arithmetic pad; numerical audit remains explicit.
    ts=(np.arange(n)+.5)/n;dt=.5/n
    corners=[control(g,h) for g in (g0,g1) for h in (h1-1e-7,h0+1e-7)]
    ps=np.array([position(p,ts) for p in corners]);dp=np.array([first(p,ts) for p in corners]);dd=np.array([second(p,ts) for p in corners])
    d3=np.max(np.abs([6*(p[3]-3*p[2]+3*p[1]-p[0]) for p in corners]),axis=0)
    ddlo=dd.min(axis=0)-d3*dt-1e-9;ddhi=dd.max(axis=0)+d3*dt+1e-9
    dmax=np.maximum(abs(ddlo),abs(ddhi));lo=dp.min(axis=0)-dmax*dt-1e-9;hi=dp.max(axis=0)+dmax*dt+1e-9
    pmax=np.maximum(abs(lo),abs(hi));plo=ps.min(axis=0)-pmax*dt-1e-9;phi=ps.max(axis=0)+pmax*dt+1e-9
    return plo,phi,lo,hi,radius_bound(lo,hi,ddlo,ddhi)

def distances(lo,hi,boxes):
    b=np.array(boxes)
    delta=np.maximum(0,np.maximum(lo[:,None,:]-b[None,:,3:],b[None,:,:3]-hi[:,None,:]))
    return np.linalg.norm(delta,axis=2)

def build():
    for package,required in [('numpy','2.2.6'),('scipy','1.15.3')]:base.need(version(package)==required,'numerical environment drift')
    historical=base.build() # validates all frozen producer bytes
    root=base.ROOT
    source=base.read(root/'design/partition/partition-input.json');d=source['load_distribution']
    candidate=base.read(root/'design/partition/core-split/candidates/two.json')['boards']
    comparison=base.read(root/'design/partition/core-split/mechanical/generated/comparison.json')
    mech=next(a for a in comparison['alternatives'] if a['id']=='two-deep')
    partition=base.read(root/'design/partition/partition.json')
    coords=[(23+17*(i%3),15.5+9*(i//3)) for i in range(6)]
    faces={'KA':-101.6,'KB':-126.};anchors={'KA':-103.1,'KB':-124.5};od=d['diameter_max_mm'];r=od/2
    terminals=[];obstacles=[]
    for board,key,side in [('KA','two-A','B.Cu'),('KB','two-B','F.Cu')]:
        rows=base.obstacles(candidate[key],side,mech,partition)
        for i,(x,y) in enumerate(coords):
            if board=='KB':x+=OFFSET
            land=np.array([x,y,anchors[board]])+((-BRIDGE*V0) if board=='KA' else (BRIDGE*V1))*np.array([1,SIGNS[i],1])
            q=[land[0]-3,land[1]-3,land[0]+3,land[1]+3];gap=min(base.rectgap(q,o['box']) for o in rows)
            base.need(gap>=.5,'terminal source clearance failure')
            terminals.append({'id':historical['wires'][i]['terminal_ids'][0 if board=='KA' else 1],
                'net':historical['wires'][i]['net'],'board':board,'side':side,'land_center_xyz_mm':land.tolist(),'reserve_xy_mm':q,
                'free_tail_start_xyz_mm':[x,y,anchors[board]],'source_reserve_gap_mm':gap})
        for row in rows:
            if row['kind'] in ('tool-column','support','loom'):
                zz=[-150,-90] # conservative full swept-depth reservation
            else:zz=[-106.6,-101.6] if board=='KA' else [-126,-118.7]
            q=row['box'];obstacles.append({'id':board+'/'+row['id'],'box':[q[0],q[1],zz[0],q[2],q[3],zz[1]],'board':board,'kind':row['kind']})
    # Jointly place the required new bulk/monitor reservations as well as terminals.
    reserves=[]
    for board,key in [('KA','two-A'),('KB','two-B')]:
        rows=base.obstacles(candidate[key],'B.Cu',mech,partition)
        boxes=[(f'{board}-bulk-{i+1}',[20+17*i,34,25+17*i,37]) for i in range(3)]
        if board=='KB':boxes.append(('KB-monitor',[80,12,100,32]))
        for name,q in boxes:
            clearance=min(base.rectgap(q,o['box']) for o in rows)
            base.need(clearance>=.5,'new bulk/monitor source reserve clearance')
            zz=[-106.6,-101.6] if board=='KA' else [-132.6,-127.6]
            obj={'id':name,'box':[q[0],q[1],zz[0],q[2],q[3],zz[1]],'board':board,'kind':'new-reserve','source_clearance_mm':clearance}
            reserves.append(obj);obstacles.append(obj)
    # Complete broad phase includes negative bows, land bridges and side carriers.

    obstacles=[o for o in obstacles if o['box'][0]<120 and o['box'][1]<50 and o['box'][3]>-2 and o['box'][4]>-2]
    clamps=assembly(coords,SIGNS,anchors,V0,r)
    clamps['enclosure_XY_margin_mm']=min(min(q['box'][0]+2,q['box'][1]+2,320-q['box'][3],300-q['box'][4]) for q in clamps['solids'])
    clamps['own_collet_exit_halfspace_check']=True
    base.need(all(q['box'][0]>-2 and q['box'][1]>-2 and q['box'][3]<120 and q['box'][4]<50 for q in clamps['solids']),'clamp outside complete obstacle broad phase')
    clamp_wire=math.inf;clamp_source=math.inf;clamp_nearest=None
    gs=np.linspace(21.4,31.4,201);hs=[handle(g) for g in gs]
    for g,h in [(g,h) for g in (gs[0],gs[-1]) for h in (min(hs),max(hs))]:
        p=control(g,h)
        # All free-curve control points lie outside each flat collet end plane;
        # convex hull containment ensures the curve never re-enters its own shell.
        base.need(np.all((p-p[0])@V0>=-1e-10) and np.all((p-p[3])@(-V1)>=-1e-10),'own collet end re-entry')
    clamps['finite_wire_collet_exit_proof']=exit_proof([control(g,h) for g in (gs[0],gs[-1]) for h in (min(hs)-1e-7,max(hs)+1e-7)],V0,V1,r)
    base.need(all(a>b for a,b in zip(hs,hs[1:])),'handle monotonicity failure')
    lengths=[arclength(control(g,h),192) for g,h in zip(gs,hs)]
    base.need(max(abs(v-LENGTH) for v in lengths)<1e-8,'independent quadrature disagreement')
    radius_min=math.inf;minimum_clearance=math.inf;nearest=None;sx=sy=0.;gates=[]
    pair_clearance=math.inf;enclosure_clearance=math.inf;signs=SIGNS
    for j in range(len(gs)-1):
        lo,hi,dl,dh,rb=sweep_cells(gs[j],gs[j+1],hs[j],hs[j+1])
        radius_min=min(radius_min,float(rb.min()))
        base.need(np.all(dh[:,2]<0),'nonmonotone Z invalidates derivative/collision proof')
        sx=max(sx,float((np.maximum(abs(dl[:,0]),abs(dh[:,0]))/(-dh[:,2])).max()))
        sy=max(sy,float((np.maximum(abs(dl[:,1]),abs(dh[:,1]))/(-dh[:,2])).max()))
        # Include both rigid straight tails in source/wire envelope checks.
        tail_lo=[];tail_hi=[]
        for start,end0,end1 in [(-BRIDGE*V0,np.zeros(3),np.zeros(3)),(np.array([OFFSET,0,-gs[j]]),np.array([OFFSET,0,-gs[j]])+BRIDGE*V1,np.array([OFFSET,0,-gs[j+1]])+BRIDGE*V1),(np.zeros(3),TAIL*V0,TAIL*V0), (np.array([OFFSET,0,-gs[j]]),np.array([OFFSET,0,-gs[j]])-TAIL*V1,np.array([OFFSET,0,-gs[j+1]])-TAIL*V1)]:
            for q in range(32):
                a0=start+(end0-start)*(q/32);a1=start+(end0-start)*((q+1)/32)
                if start[0]==OFFSET:
                    cloud=np.array([a0,a1,a0+[0,0,-(gs[j+1]-gs[j])],a1+[0,0,-(gs[j+1]-gs[j])]])
                else:cloud=np.array([a0,a1])
                tail_lo.append(cloud.min(axis=0));tail_hi.append(cloud.max(axis=0))
        lo=np.vstack([lo,tail_lo]);hi=np.vstack([hi,tail_hi])
        clamp_boxes=[]
        for obj in clamps['solids']:
            q=obj['box'].copy()
            if obj['board']=='KB':q[2]-=gs[j+1]-21.4;q[5]-=gs[j]-21.4
            clamp_boxes.append(q)
        source_boxes=[]
        for obj in obstacles:
            q=obj['box'].copy()
            if obj['board']=='KB' and obj['kind'] in ('courtyard','new-reserve'):
                q[2]-=gs[j+1]-21.4;q[5]-=gs[j]-21.4
            source_boxes.append(q)
        cb=np.array(clamp_boxes)
        clamp_source=min(clamp_source,float(distances(cb[:,:3],cb[:,3:],source_boxes).min()))
        center_sets=[];radii=[]
        for i,(x,y) in enumerate(coords):
            shift=np.array([x,y,anchors['KA']]);a=lo.copy();b=hi.copy()
            if signs[i]<0:a[:,1],b[:,1]=-hi[:,1],-lo[:,1]
            a+=shift;b+=shift
            base.need(a[:,0].min()-r>-2 and a[:,1].min()-r>-2 and b[:,0].max()+r<120 and b[:,1].max()+r<50,'wire outside complete obstacle broad phase')
            center_sets.append((a+b)/2);radii.append(float(np.linalg.norm((b-a)/2,axis=1).max()))
            enclosure_clearance=min(enclosure_clearance,float(a[:,1].min()+2-r),float(300-b[:,1].max()-r),float(a[:,0].min()+2-r),float(320-b[:,0].max()-r))
            # Only the own collet's bore is an intended wire/material contact.
            permitted=[k for k,obj in enumerate(clamps['solids']) if not (obj['kind']=='collet-capsule-bound' and obj['wire']==i)]
            cd=distances(a,b,[clamp_boxes[k] for k in permitted])-r
            ck=np.unravel_index(int(cd.argmin()),cd.shape)
            if cd[ck]<clamp_wire:
                clamp_wire=float(cd[ck]);clamp_nearest={'wire':i+1,'solid':clamps['solids'][permitted[ck[1]]]['id'],'travel_cell_mm':[float(gs[j]-21.4),float(gs[j+1]-21.4)]}
            boxes=[]
            for o in obstacles:
                q=o['box'].copy()
                if o['board']=='KB' and o['kind'] in ('courtyard','new-reserve'):
                    q[2]-=gs[j+1]-21.4;q[5]-=gs[j]-21.4
                boxes.append(q)
            dd=distances(a,b,boxes)-r
            k=np.unravel_index(int(dd.argmin()),dd.shape)
            if dd[k]<minimum_clearance:minimum_clearance=float(dd[k]);nearest={'wire':i+1,'travel_cell_mm':[float(gs[j]-21.4),float(gs[j+1]-21.4)],'obstacle':obstacles[k[1]]['id']}
        for i in range(6):
            tree=cKDTree(center_sets[i])
            for k in range(i+1,6):
                lower=float(tree.query(center_sets[k])[0].min())-radii[i]-radii[k]-od
                pair_clearance=min(pair_clearance,lower)
        if j in (0,99,199):gates.append({'travel_mm':float(gs[j]-21.4),'handle_mm':hs[j],'control_points_relative_mm':control(gs[j],hs[j]).tolist()})
    wire_sep=pair_clearance
    # Frozen registered main-wire source includes fan, solder and adapter lengths.
    sys.path.insert(0,str(root))
    from scripts.geometry.power_wire import registered_route
    fan=base.read(root/'design/partition/contact-transfer-proposal.json')['main_strand_class']
    wire=base.read(root/'design/partition/wire-transfer-proposal.json')
    main=[]
    for board in ('JL','JR','P'):
        for i in range(6):
            route=registered_route(source,board,i,fan,wire['endpoint_adapter_class'],metal_radius=wire['bulk_potential_class']['maximum_metal_radius_from_bundle_axis_mm'])
            main.append({'id':'POWER-'+board+'-'+d['wire_labels'][i], 'continuous_axis_upper_mm':route['continuous_centreline_length_upper_mm'],
                'cut_with_10mm_allowance_upper_mm':route['continuous_centreline_length_upper_mm']+10,'radius_lower_mm':route['bulk_curve_bounds']['curvature_radius_lower_mm']})
    main_cut=math.ceil(max(v['cut_with_10mm_allowance_upper_mm'] for v in main));new_cut=math.ceil(LENGTH+2*TAIL+10)
    allocated={'rail_ohm':.00015,'return_ohm':.0002}
    drops={rail:base.path_drop(amps,4.6,main_cut,new_cut,d,allocated['rail_ohm'],allocated['return_ohm']) for rail,amps in d['rail_max_A'].items()}
    return {'status':'CONDITIONAL SOURCE PROPOSAL; provisional face contract unreconciled; NOT APPLIED / NOT PHYSICAL FIT',
        'source_commit':historical['source_commit'],'tool_sha256':base.sha(Path(__file__)),'clamps_tool_sha256':base.sha(HERE/'clamps.py'),'accepted':False,'face_change_adopted':False,'reversible_face_proposal_permitted':True,'face_requires_user_permission':False,
        'construction':{'row_count':2,'wires_per_row':3,'KA_side':'B.Cu','KB_side':'F.Cu','fixed_panel_or_canonical_edits':0,
            'terminals':terminals,'bulk_and_monitor_reserves':reserves,'anchor_height_from_face_mm':HEIGHT,'straight_land_bridge_each_mm':BRIDGE,'allowance_remaining_after_two_bridges_mm':10-2*BRIDGE,'termination_scope':'Straight tangent continuations end at recentered land centers. Reserve is checked; stripping, solder and insulation termination remain unqualified. Bare-PCB tube bound covers raised flexible section only.','offset_xy_mm':[OFFSET,0],'free_bezier_length_mm':LENGTH,
            'straight_clamping_tail_each_mm':TAIL,'Y_bow_sign_by_W1_to_W6':signs,'fixed_tail_direction_KA_to_KB_before_Y_sign':V0.tolist(),'fixed_end_direction':V1.tolist(),
            'handle_root_definition':'Unique positive rising root of integral_0^1 |BezierDerivative(control(g,h),t)| dt = 64 mm; root h decreases with g.'},
        'sweep':{'axial_withdrawal_mm':[0,10],'interval_travel_cells':200,'interval_curve_cells':512,
            'minimum_curvature_radius_lower_bound_mm':radius_min,'bend_margin_mm':radius_min-RADIUS,
            'source_obstacle_tube_clearance_lower_bound_mm':minimum_clearance,'nearest_source_obstacle':nearest,
            'wire_wire_clearance_lower_bound_mm':wire_sep,'enclosure_xy_tube_clearance_lower_bound_mm':enclosure_clearance,'bare_pcb_tube_clearance_mm':HEIGHT-r,
            'quadrature_max_disagreement_mm':max(abs(v-LENGTH) for v in lengths),
            'method':'Interval boxes bound derivatives and tube centerline over every parameter/travel cell using convex hull in g,h and Taylor bounds in t. Floating results use 1e-7 handle and 1e-9 arithmetic padding; not a formal interval library certificate.',
            'pose_examples':gates},
        'clamps':{**clamps,'wire_clearance_lower_bound_mm':clamp_wire,'nearest_wire_solid':clamp_nearest,'foreign_collet_separation_lower_bound_mm':wire_sep-1.0,'source_clearance_lower_bound_mm':clamp_source},
        'joined_budget':{'actual_main_source_curves':main,'required_qualified_main_cut_ceiling_mm':main_cut,'new_wire_cut_ceiling_mm':new_cut,
            'proposed_global_copper_targets':allocated,'drops_mV_if_all_targets_and_cut_classes_realized':drops,
            'minimum_margin_mV':20-max(drops.values()),'drops_at_existing_full_copper_ceilings_mV':{rail:base.path_drop(amps,4.6,main_cut,new_cut,d) for rail,amps in d['rail_max_A'].items()},'drops_if_main_cut_is_110mm_mV':{rail:base.path_drop(amps,4.6,110,new_cut,d,allocated['rail_ohm'],allocated['return_ohm']) for rail,amps in d['rail_max_A'].items()},'scope':'Stronger performance targets within existing 1mohm/0.5mohm ceilings; actual copper extraction and manufactured cuts NOT PROVEN. Main source geometry is recomputed, not a straight-line lower bound.'},
        'manufacturing_tolerance_status':'UNQUALIFIED: no selected dimensional/position/warp/deflection/assembly/shape budget; positive nominal geometry is not positive physical margin',
        'gates':{'wire_geometry':radius_min>RADIUS and minimum_clearance>0 and wire_sep>0 and enclosure_clearance>0,
            'arithmetic_allocation':max(drops.values())<20,'face_contract':False,'clamp_assembly':False,'nominal_clamp_collision_envelopes':clamp_wire>0 and clamp_source>0 and clamps['enclosure_XY_margin_mm']>0,'actual_copper':False,'all_100_trim_access':False,'native':False}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();result=build()
    text=json.dumps(result,indent=2,sort_keys=True)+'\n';out=HERE/'offset-proposal.json'
    if args.check:base.need(out.read_text()==text,'offset proposal drift')
    else:out.write_text(text)
    print(json.dumps({'status':result['status'],'sweep':{k:v for k,v in result['sweep'].items() if k not in ('pose_examples','method')},'gates':result['gates']}))

if __name__=='__main__':main()
