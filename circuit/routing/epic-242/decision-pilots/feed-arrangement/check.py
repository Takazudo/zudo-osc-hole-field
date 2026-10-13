#!/usr/bin/env python3
"""Reversible feed construction and rejection evidence. No CAD/native writes."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)

def box(poly):
    need(len(poly)==1,'multiple courtyard rings')
    points={tuple(p) for p in poly[0]};xs=sorted({x for x,y in points});ys=sorted({y for x,y in points})
    need(len(xs)==len(ys)==2 and points=={(x,y) for x in xs for y in ys},'nonrectangular courtyard')
    return [xs[0],ys[0],xs[-1],ys[-1]]

def rectgap(a,b):
    return math.hypot(max(0,a[0]-b[2],b[0]-a[2]),max(0,a[1]-b[3],b[1]-a[3]))

def min_chord(length,radius):
    need(0<=length<=math.pi*radius,'short-curve theorem domain')
    return 2*radius*math.sin(length/(2*radius))

def minimum_service_length(gap,travel,radius):
    need(gap>0 and travel>=0 and radius>0,'positive geometry required')
    rhs=2*gap*travel+travel*travel
    lo=0.;hi=math.pi*radius
    need(hi*hi-min_chord(hi,radius)**2>=rhs,'outside bounded theorem domain')
    for _ in range(90):
        mid=(lo+hi)/2
        if mid*mid-min_chord(mid,radius)**2<rhs:lo=mid
        else:hi=mid
    return hi

def path_drop(amps,ret,main,new,d,rail_copper=None,return_copper=None):
    rr=d['hot_resistance_requirement_ohm_per_m']*(main+new)/1000+2*d['combined_termination_resistance_ohm']
    return 1000*(amps*(rr+(d['rail_plane_resistance_ceiling_ohm'] if rail_copper is None else rail_copper))+ret*(rr+(d['return_plane_resistance_ceiling_ohm'] if return_copper is None else return_copper)))

def obstacles(candidate,side,mech,partition):
    result=[{'id':p['ref'],'box':box(p['courtyard_polygons_mm']),'kind':'courtyard'} for p in candidate['placements'] if p['side']==side]
    result += [{'id':'support','box':[x-1.6,y-1.6,x+1.6,y+1.6],'kind':'support'} for x,y in candidate['supports_mm']]
    result += [{'id':p['header_id'],'box':p['box_mm'],'kind':'tool-column'} for p in partition['K_service_apertures']]
    result += [{'id':p['id'],'box':p['box_mm'],'kind':'loom'} for p in mech['through_loom_passages'] if p['board']==candidate['provisional_board_key']]
    if candidate['provisional_board_key']=='KA':result += [{'id':'protection','box':[180,220,256,290],'kind':'reserve'}]
    return result

def build():
    lock=read(HERE/'source-lock.json')
    for name,digest in lock['files'].items():need(sha(ROOT/name)==digest,'input drift: '+name)
    c=read(ROOT/'design/partition/core-split/candidates/two.json')['boards']
    s=read(ROOT/'design/partition/partition-input.json');d=s['load_distribution']
    partition=read(ROOT/'design/partition/partition.json')
    mech=next(a for a in read(ROOT/'design/partition/core-split/mechanical/generated/comparison.json')['alternatives'] if a['id']=='two-deep')
    config=read(ROOT/'design/partition/core-split/mechanical/candidates.json')
    power=read(ROOT/'design/partition/core-split/power/contract.json')['options']['two']
    feed=power['new_feeds'][0]
    need([e['side'] for e in feed['endpoint_envelopes']]==['F.Cu','F.Cu'],'current face contract changed')
    need([w['net'] for w in feed['wires']]==d['net_order'],'wire identity/order drift')
    R=d['minimum_bend_radius_mm'];od=d['diameter_max_mm'];allowance=config['cut_allowance_mm'];travel=config['service_geometry']['proposed_unmating_travel_mm']
    z={b['id']:b for b in mech['boards']};gap=z['KA']['back_z_mm']-z['KB']['front_z_mm']
    # Exact two-row construction; current face contract is NOT silently changed.
    coords=[(23+17*(i%3),15+12*(i//3)) for i in range(6)]
    terminals=[]
    for board,side,face,source in [('KA','B.Cu',z['KA']['back_z_mm'],'two-A'),('KB','F.Cu',z['KB']['front_z_mm'],'two-B')]:
        obs=obstacles(c[source],side,mech,partition)
        for i,(x,y) in enumerate(coords):
            q=[x-3,y-3,x+3,y+3]
            closest=min(obs,key=lambda o:rectgap(q,o['box']))
            margin=rectgap(q,closest['box'])
            need(margin>=.5,'terminal reserve gap below positive .5 mm construction margin')
            need(q[0]>=4.3 and q[1]>=8.3 and q[2]<=313.7 and q[3]<=245.7,'terminal outside retained top rectangle')
            terminals.append({'id':feed['wires'][i]['terminal_ids'][0 if board=='KA' else 1],
                'wire_id':feed['wires'][i]['id'],'net':feed['wires'][i]['net'],'board':board,'side':side,
                'center_xyz_mm':[x,y,face],'reserve_xy_mm':q,'land_mm':[4,4],'courtyard_mm':[5,5],
                'minimum_reserve_to_source_obstacle_mm':margin,'nearest_source_obstacle':closest['id'],
                'side_contract':'UNACCEPTED ALTERNATIVE to KA F.Cu' if board=='KA' else 'RETAINED'})
    # Concrete central split-guide envelope with enclosure-side load path.
    # It demonstrates static packaging only: no retention/insulation qualification.
    clamps=[{'id':f'GUIDE-{i+1}','box_xyz_mm':[18,y-4,-116,62,y+4,-112],
             'bores': [{'center_xy_mm':[x,y],'diameter_mm':2.8} for x in (23,40,57)],
             'construction':'custom split guide, unselected insulating material; bore clearance is not compression/retention evidence'} for i,y in enumerate((15,27))]
    beams=[{'id':f'ARM-{i+1}','box_xyz_mm':[-1.5,y-1,-116,18,y+1,-112]} for i,y in enumerate((15,27))]
    clamp_margin=min(-116-z['KB']['front_body_limit_z_mm'], z['KA']['rear_body_limit_z_mm']-(-112))
    need(clamp_margin>0,'clamp body-allowance collision')
    wire_clear=min(math.dist(a,b)-od for i,a in enumerate(coords) for b in coords[i+1:])
    # Straight installed cylinders; solder-end intersections are explicit joints.
    wires=[{**w,'centerline_xyz_mm':[[x,y,z['KB']['front_z_mm']],[x,y,z['KA']['back_z_mm']]],
        'installed_cylinder_diameter_mm':od,'installed_centerline_mm':gap,'bend_radius_mm':None,
        'bend_status':'STRAIGHT; curvature zero','cut_necessary_lower_bound_mm':math.ceil(gap+allowance),
        'service_status':'REJECTED: fixed length cannot execute required independent axial withdrawal'} for w,(x,y) in zip(feed['wires'],coords)]
    # All terminal XY offsets: relaxed obstacle-free service necessary condition.
    minimum=minimum_service_length(gap,travel,R)
    budgets=read(ROOT/'design/partition/core-split/power/joined/budget.json')['voltage_budget']
    electrical=[]
    for prefix in ('POWER-JL-','POWER-JR-','POWER-P-'):
        # Lower bound is deliberately optimistic, not a realized main route.
        main=max(r['cut_lower_bound_mm'] for r in mech['power_bounds'] if r['id'] in (prefix+'+12V',prefix+'AGND1'))
        cap=budgets['+12V']['two_section_total_cut_limit_for_both_rail_and_return_mm']-main
        L=cap-allowance;f=L*L-min_chord(L,R)**2
        electrical.append({'main_branch':prefix[:-1],'existing_main_cut_lower_bound_mm':main,
            'equal_aggregate_new_cut_ceiling_mm':cap,'static_35mm_cut_drop_mV':path_drop(2.1,4.6,main,math.ceil(gap+allowance),d),
            'conditional_flexible_length_ceiling_mm':L,'max_any_xy_axial_travel_with_10_reserved_mm':math.sqrt(gap*gap+f)-gap,
            'minimum_service_cut_mm':minimum+allowance,'service_drop_at_full_copper_allocations_mV':path_drop(2.1,4.6,main,minimum+allowance,d),
            'remaining_nonflexible_allowance_at_ideal_minimum_mm':cap-minimum,
            'required_rail_copper_ceiling_if_return_stays_0p5mohm':d['rail_plane_resistance_ceiling_ohm']-(path_drop(2.1,4.6,main,minimum+allowance,d)-20)/2100})
    bulk=[]
    for b in ('KA','KB'):
        for i,rail in enumerate(('+12V','-12V','+5V')):
            q=[20+i*17,34,25+i*17,37]
            obs=obstacles(c['two-A' if b=='KA' else 'two-B'],'B.Cu',mech,partition)
            need(min(rectgap(q,o['box']) for o in obs)>=.5,'bulk reserve conflict')
            bulk.append({'id':f'CS247-BULK-{b}-{i+1}','net':rail,'board':b,'side':'B.Cu','box_xy_mm':q,'height_mm':5,'mpn':None})
    monitor={'id':'CS247-MON-KB','board':'KB','side':'B.Cu','box_xy_mm':[80,12,100,32],'height_mm':5,'mpn':None}
    need(min(rectgap(monitor['box_xy_mm'],o['box']) for o in obstacles(c['two-B'],'B.Cu',mech,partition))>=.5,'monitor reserve conflict')
    return {'status':'REJECTED SERVICE CONSTRUCTION; conditional installed geometry only; NOT ACCEPTED / NOT APPLIED',
        'source_commit':lock['source_commit'],'input_sha256':lock['files'],'tool_sha256':sha(Path(__file__)),
        'current_face_contract':['KA F.Cu','KB F.Cu'],'alternative_faces':['KA B.Cu','KB F.Cu'],
        'face_change_adopted':False,'reversible_face_proposal_permitted':True,'face_requires_user_permission':False,'geometry_is_conditional_research':True,
        'terminals':terminals,'wire_identity_source':feed['id'],'wires':wires,'clamp_envelopes':clamps,'enclosure_side_arms':beams,
        'clamp_load_path':'Two releasable split-guide bars through arms to enclosure side-frame; no new PCB holes and no solder structural load. Material/retention/insulation and fastening geometry NOT QUALIFIED; this construction is rejected before service adoption.',
        'bulk_reserves':bulk,'monitor_reserve':monitor,
        'static_screen':{'minimum_terminal_reserve_gap_mm':min(t['minimum_reserve_to_source_obstacle_mm'] for t in terminals),
            'wire_to_wire_clearance_mm':wire_clear,'clamp_to_conservative_body_allowance_mm':clamp_margin,
            'bore_diametral_clearance_mm':2.8-od,'scope':'Installed primitive envelope only; exact solder transition/clamp force, all existing cable sweeps and physical solids not proven.'},
        'service_rejection':{'bend_radius_mm':R,'actual_anchor_convention':'Material anchors on PCB land face datum; raised solder/strain-relief anchors require a separately bound model.','face_datum_gap_mm':gap,
            'required_axial_travel_mm':travel,'half_turn_length_mm':math.pi*R,
            'shared_xy_max_short_centerline_mm':2*R*math.asin(gap/(2*R)),
            'shared_xy_max_axial_travel_mm':2*R*math.asin(gap/(2*R))-gap,
            'any_xy_minimum_flexible_length_mm':minimum,'reserved_outside_flexible_centerline_mm':allowance,
            'any_xy_minimum_cut_under_reserved_allowance_mm':minimum+allowance,
            'theorem':'For L<=pi R, endpoint chord d>=2R sin(L/(2R)); fixed-offset axial travel requires L^2-[2R sin(L/(2R))]^2>=2g delta+delta^2. Proof and scope in README.',
            'scope':'Shared-XY rejection needs no cut-allowance allocation. Any-XY cut rejection assumes the 10 mm allowance remains outside modeled flexible centerline. These are not a proof against every service lifecycle or lower realized copper resistance.'},
        'electrical':electrical,'copper_policy':'All existing copper preserved; zero native terminals or new copper applied. Lower copper targets are requirements for future extraction, never measured values.',
        'next_decision':'Current F/F contract remains. Face revision alone cannot cure this shared-XY service failure. An offset-wire/lifecycle redesign needs explicit preparation allocation and either demonstrated lower copper resistance or revised route lengths within existing electrical ceilings; no blanket architecture impossibility established.',
        'native':'NOT RUN / NOT ADMITTED','all_100_trim_access':'NOT ESTABLISHED; co-extraction alone is not access evidence','accepted':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=json.dumps(build(),indent=2,sort_keys=True)+'\n';path=HERE/'proposal.json'
    if args.check:need(path.read_text()==text,'proposal drift')
    else:path.write_text(text)
    print('PASS deterministic construction/rejection evidence; service BLOCKED, geometry NOT ADOPTED, native NOT RUN')

if __name__=='__main__':main()
