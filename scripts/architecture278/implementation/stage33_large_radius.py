"""A01 J-SIG/J-PWR maker-compliant large-radius routing and service-envelope study on top of Stage32 (design only; no native/physical claims)."""
import argparse
import copy
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import stage32_service_envelope as s32

s31,s30,s28=s32.s31,s32.s30,s32.s28
ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage33'
S32=ROOT/REL/'stage32'
BASE='9a3b91169658569eb5702ef24f336b73b84c70ff'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage33_large_radius.py','test_stage33_large_radius.py')}
need,read,dump,sha=s28.need,s28.read,s28.dump,s28.sha
LINKS,ENDS,STEP=s31.LINKS,s31.ENDS,s31.STEP_MM
GENERATED=('model.json','states.json','analysis.json','reservations.json','report.json','summary.md','plan-elevation.svg','service-states.svg')
STATES=(('middle',(0,1)),('local',(1,0)),('both',(1,1)))
MIDDLE={ENDS[l][1] for l in LINKS}
CLASSES=('FEASIBLE_WITHIN_STATED_ASSUMPTIONS','CONDITIONAL','INFEASIBLE','UNKNOWN')
r6,p6,val=s32.r6,s32.p6,s32.val


# ---------- inputs ----------
def load():
    return {'approval':read(OUT/'approval.json'),'input':read(OUT/'design-input.json'),'sources':read(OUT/'sources.json'),'s32':s32.load(),
        's32_analysis':read(S32/'analysis.json'),'s32_report':read(S32/'report.json')}


def merged(data):
    """Stage32 parameters, tolerances, rules and bow cases, extended (never overridden) by the Stage33 additions."""
    i32=data['s32']['input'];i33=data['input'];P=copy.deepcopy(i32['parameters'])
    for k,v in i33['parameters'].items():
        need(k not in P,'Stage33 may not override the inherited Stage32 parameter '+k);P[k]=v
    rules=list(i32['tolerance_rules']);need(rules[-1]['match']=='','catch-all tolerance rule stays last')
    rules=rules[:-1]+list(i33['tolerance_rules_added'])+rules[-1:]
    return P,i32['tolerances'],rules,i32['bow_cases']


def validate_inputs(data):
    a=data['approval'];inp=data['input']
    s32.validate_inputs(data['s32'])
    need(inp['inherits']==REL+'stage32/design-input.json' and data['sources']['inherits']==REL+'stage32/sources.json','Stage33 inherits the committed Stage32 inputs')
    need(a['status']=='DESIGN_STUDY_CHANGES_ALLOWED' and a['decided_by']=='OWNER','owner approval record')
    need(set(a['changeable']['header_refs'])<=MIDDLE,'only the middle J-SIG/J-PWR headers may move')
    need(a['changeable']['carrier_local_shape']==['rail:middle:0'],'approved carrier change limited to rail:middle:0')
    need(inp['status']=='DESIGN_STUDY_INPUT_NOT_MEASURED','design input status')
    for x,n in ((inp,'design-input'),(a,'approval'),(data['sources'],'sources')):s28.no_claims(x,n)
    src=s32.validate_sources({'sources':data['s32']['sources']['sources']+data['sources']['sources']})
    P,T,rules,_=merged(data)
    for k in inp['parameters']:s32.classed(k,P[k],src)
    for w in inp['wire_candidates']:
        for sid in w['sources']:need(src[sid]['authority'] in s32.MAKER_AUTH and not str(src[sid].get('availability','')).startswith('NOT_'),'wire candidate values from an obtained maker document '+w['mpn'])
    for w in inp['wire_candidates_not_obtained']:need(w['values'] is None,'a wire whose maker document was not obtained carries no values '+w['mpn'])
    need(val(P,'selected_wire_mpn') is None,'no wire is selected without complete evidence')
    need(val(P,'jst_current_rating_awg28_A') is None and val(P,'jst_current_rating_awg30_A') is None,'the JST AWG26 current rating is not transferred to AWG28/30')
    need(val(P,'service_flex_rule_x_od') is None,'no maker flex rule exists; it stays UNCONFIRMED')
    need(val(P,'bundle_dressing_allowance_mm')>=0,'dressing allowance is not negative')
    need(val(P,'release_travel_mm')==15,'release travel stays the 15 mm basis')
    c=inp['candidates']['R33']
    for ref,mv in c['header_moves'].items():
        need(ref in a['changeable']['header_refs'],'header move outside the approval '+ref)
        need(mv['face'] in ('front','rear'),'header face')
        if mv['face']=='rear':need('header_mounting_face' in a['broader_change_proposals'],'a header face change must be listed as a broader change proposal '+ref)
    need('keeper' not in c and 'retention' not in c,'R33 carries no retention part; lateral retention stays an open condition')
    return P,T,rules


# ---------- geometry ----------
def header_geometry(mech,moves):
    """Stage31 header geometry after the XY move; a rear-face header is mirrored onto the opposite board face (pins and MPN unchanged) and points +z."""
    geo=s31.header_geometry(mech,{r:{'origin_mm':m['origin_mm'],'rotation_deg':m['rotation_deg']} for r,m in moves.items()})
    for ref,mv in moves.items():
        g=geo[ref];g['face']=mv['face'];g['face_changed']=mv['face']=='rear'
        if mv['face']!='rear':continue
        z0,z1=mech['boards'][g['board']]['z_mm'];need(g['face_z_mm']==z0,'rear move starts from a front-face header '+ref)
        span=g['sweep']['z_mm'][1]-g['sweep']['z_mm'][0];ox,oy=g['origin_mm'];q=g['rotation_deg']
        mir=(lambda xy:[r6(2*ox-xy[0]),xy[1]]) if q in (0,180) else (lambda xy:[xy[0],r6(2*oy-xy[1])])
        g['pads_xyz_mm']={p:[mir(xy[:2])+[z1] for xy in v] for p,v in g['pads_xyz_mm'].items()}
        sig=[p for p in g['pins'] if g['pins'][p] is not None];cx,cy=(r6(sum(g['pads_xyz_mm'][p][0][i] for p in sig)/len(sig)) for i in (0,1))
        g.update(face_z_mm=z1,axis=1,exit_mm=[cx,cy,r6(z1+s31.MATED_MM)],pad_centroid_mm=[cx,cy,z1])
        g['sweep']['z_mm']=[z1,r6(z1+span)]
    return geo


def moved_mech(mech,geo):
    m=s31.moved_mech(mech,geo)
    for ref,g in geo.items():
        if not g.get('face_changed'):continue
        next(x for x in m['connector_release_sweeps'] if x['ref']==ref)['z_mm']=g['sweep']['z_mm'];m['headers'][ref]['pad_depth_mm']=g['face_z_mm']
    return m


def check_moves(mech,geo,moves):
    """A moved header keeps its board, MPN and pin/net map, sits on the board clear of the edge notch and mount washers, and its sweep clears the DIN body and every header sweep on the same face."""
    rows=[]
    for ref in sorted(moves):
        g=geo[ref];h=mech['headers'][ref];b=mech['boards'][g['board']]['outline_mm']
        need(g['pins']==h['pins'] and g['header_mpn']==h['header_mpn'] and g['housing_mpn']==h['housing_mpn'] and g['board']==h['board'],'moved header identity '+ref)
        need(g['face_z_mm'] in mech['boards'][g['board']]['z_mm'],'moved header on a board face '+ref)
        need(b[0]<=g['box_mm'][0] and b[1]<=g['box_mm'][1] and g['box_mm'][2]<=b[2] and g['box_mm'][3]<=b[3],'moved header body on its board '+ref)
        need(not s31.overlap2(g['box_mm'],mech['middle_access_edge_notches_mm'][0]),'moved header clear of the board notch '+ref)
        others=[]
        for r2,h2 in mech['headers'].items():
            if r2==ref or h2['board']!=g['board']:continue
            face2=geo[r2]['face_z_mm'] if r2 in geo else h2['pad_depth_mm']
            if face2!=g['face_z_mm']:continue
            sw2=geo[r2]['sweep']['box_mm'] if r2 in geo else next(x for x in mech['connector_release_sweeps'] if x['ref']==r2)['box_mm']
            need(not s31.overlap2(g['sweep']['box_mm'],sw2),'moved header release sweep overlaps '+r2);others.append({'ref':r2,'gap_mm':r6(s31.gap2(g['sweep']['box_mm'],sw2))})
        din=mech['din_connectors']['middle']
        if din['mount_surface_z_mm']==g['face_z_mm']:need(not s31.overlap2(g['sweep']['box_mm'],din['box_mm']),'moved header clear of the DIN body')
        mounts=[]
        for mt in mech['mounts']:
            if mt['board']!=g['board']:continue
            x,y=mt['xy_mm'];r=mt['washer_diameter_mm']/2;d=s31.gap2(g['box_mm'],[x-r,y-r,x+r,y+r]);need(d>0,'moved header clear of mount washer '+mt['id']);mounts.append({'mount':mt['id'],'gap_mm':r6(d)})
        rows.append({'ref':ref,'from_origin_mm':h['origin_mm'],'to_origin_mm':g['origin_mm'],'rotation_deg':g['rotation_deg'],'face':g['face'],'face_changed':g['face_changed'],
            'face_z_mm':g['face_z_mm'],'exit_mm':g['exit_mm'],'box_mm':g['box_mm'],'sweep':g['sweep'],'pins_unchanged':True,'mpn_unchanged':True,'board_plane_unchanged':True,
            'sweep_gap_to_same_face_headers':min(others,key=lambda x:x['gap_mm']) if others else None,'nearest_mount':min(mounts,key=lambda x:x['gap_mm']),
            'status':'BROADER_CHANGE_PROPOSAL (mounting face)' if g['face_changed'] else 'PROPOSAL_NOT_ADOPTED'})
    return rows


def bundle(P,link):
    """Round bundle at the JST maximum OD plus the dressing allowance (envelope radius)."""
    rb=val(P,'wire_od_max_mm')*val(P,'round_bundle_factor')[link]/2
    return {'kind':'ROUND_BUNDLE','conductors':val(P,'conductors')[link],'wire_od_mm':val(P,'wire_od_max_mm'),'round_radius_mm':r6(rb+val(P,'bundle_dressing_allowance_mm'))}


def fan_in(P,link):
    """Straight length an S-bend needs to bring the outermost pin-row conductor onto the bundle ring at the maker single-conductor radius (inner-surface convention), worst case over the JST OD window."""
    n=val(P,'conductors')[link];pitch=val(P,'gh_pitch_mm');k=val(P,'wire_bend_rule_x_od');rows=[]
    for od in (val(P,'wire_od_min_mm'),val(P,'wire_od_max_mm')):
        ring=od if n==7 else od/math.sqrt(2);d=(n-1)/2*pitch-ring;rho=k*od+od/2
        need(n in (4,7) and d>0,'fan-in offset model covers 4- and 7-conductor bundles');c=1-d/(2*rho)
        rows.append({'od_mm':od,'offset_mm':r6(d),'rho_mm':r6(rho),'length_mm':r6(2*rho*math.sqrt(1-c*c))})
    return {'length_mm':max(max(r['length_mm'] for r in rows),val(P,'straight_lead_mm')),'cases':rows}


def leads(P,link):
    f=fan_in(P,link)['length_mm'];return (f,f)


def arch(geo,link,Z,tl,tm,P):
    """Vertical-plane arch: up from the local exit, one straight horizontal leg at Z, down into the rear-face middle exit."""
    a,b=(geo[r] for r in ENDS[link]);need(a['axis']==1 and b['axis']==1,'arch needs both housings pointing +z '+link)
    ea=[a['exit_mm'][0],a['exit_mm'][1],a['exit_mm'][2]+tl];eb=[b['exit_mm'][0],b['exit_mm'][1],b['exit_mm'][2]+tm]
    return s31.fillet_route([ea,[ea[0],ea[1],Z],[eb[0],eb[1],Z],eb],val(P,'route_radius_mm'),leads(P,link))


def arch_zmin(geo,link,tl,tm,P):
    a,b=(geo[r] for r in ENDS[link])
    return max(a['exit_mm'][2]+tl,b['exit_mm'][2]+tm)+fan_in(P,link)['length_mm']+val(P,'route_radius_mm')


def design_length(geo,link,P):
    """Stage32 rule: minimum installed + largest release extra at the 15 mm travel + 10 mm service slack, rounded up to 1 mm; mated housings counted at both ends."""
    mh=2*val(P,'gh_mated_height_mm');t=val(P,'release_travel_mm')
    L0=arch(geo,link,arch_zmin(geo,link,0,0,P),0,0,P)['length_mm']+mh
    ext={n:arch(geo,link,arch_zmin(geo,link,t*w[0],t*w[1],P),t*w[0],t*w[1],P)['length_mm']+mh-L0 for n,w in STATES}
    return {'minimum_installed_mm':L0,'release_extra_by_case_mm':{k:r6(v) for k,v in ext.items()},'release_extra_mm':max(ext.values()),'design_length_mm':math.ceil(L0+max(ext.values())+val(P,'service_slack_mm'))}


def constant_length(geo,link,Ld,tl,tm,P):
    """Arch top that keeps the design length: both legs are vertical, so the top moves by half the length difference."""
    mh=2*val(P,'gh_mated_height_mm');zr=arch_zmin(geo,link,tl,tm,P);Lr=arch(geo,link,zr,tl,tm,P)['length_mm']+mh
    Z=zr+(Ld-Lr)/2;short=Z<zr-1e-9;r=None if short else arch(geo,link,Z,tl,tm,P)
    if r is not None:need(abs(r['length_mm']+mh-Ld)<1e-6,'constant-length state keeps the design length '+link)
    return {'route':r,'top_centreline_z_mm':r6(Z),'z_min_for_bends_mm':r6(zr),'slack_short':short}


def build_r33(c,data,mech,P):
    moves=c['header_moves'];geo=header_geometry(mech,moves);moved=check_moves(mech,geo,moves);mm=moved_mech(mech,geo)
    obs=s31.obstacles(mm,data['s32']['s31']['lock'],data['s32']['s31']['input']['parameters'],[])
    lengths={l:design_length(geo,l,P) for l in LINKS}
    inst={l:constant_length(geo,l,lengths[l]['design_length_mm'],0,0,P) for l in LINKS}
    for l in LINKS:need(inst[l]['route'] is not None,'installed arch fits '+l)
    return {'id':'R33','geo':geo,'moved':moved,'obs':obs,'guides':[],'reliefs':[],'lengths':lengths,'installed':inst,'routes':{l:inst[l]['route'] for l in LINKS},'spec':c,'mech':mm}


# ---------- analyses ----------
def seg_dist2(a,b,c,d):
    """Shortest distance between two plan segments (endpoints xy)."""
    def pt(p,u,v):
        dx,dy=v[0]-u[0],v[1]-u[1];L=dx*dx+dy*dy;t=0.0 if L==0 else max(0.0,min(1.0,((p[0]-u[0])*dx+(p[1]-u[1])*dy)/L));return math.hypot(p[0]-u[0]-t*dx,p[1]-u[1]-t*dy)
    def cross(o,p,q):return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0.0
    return min(pt(a,c,d),pt(b,c,d),pt(c,a,b),pt(d,a,b))


def state_rows(cand,P):
    """Installed and every release case at constant design length: arch top, straight leads, keep-outs, lowest envelope, front-volume entry."""
    m=val(P,'placement_margin_mm');out={};cb=val(P,'carrier_bottom_z_mm')
    for l in LINKS:
        bund=bundle(P,l);rb=bund['round_radius_mm'];Ld=cand['lengths'][l]['design_length_mm'];rows=[]
        cases=[('installed',(0,0),0.0)]+[(n,w,t) for t in val(P,'release_travel_sensitivity_mm') for n,w in STATES]
        for n,w,t in cases:
            c=constant_length(cand['geo'],l,Ld,t*w[0],t*w[1],P);row={'travel_mm':t,'withdrawn':n,'slack_short':c['slack_short'],'top_centreline_z_mm':c['top_centreline_z_mm'],'z_min_for_bends_mm':c['z_min_for_bends_mm']}
            if c['route'] is not None:
                r=c['route'];smp=s31.samples(r,bund);known,depth=s31.evaluate_route(smp,cand['obs'],m,l)
                low=min(p[2]-rr for p,rr in smp)
                row.update({'envelope_top_z_mm':r6(c['top_centreline_z_mm']+rb),'envelope_bottom_z_mm':r6(low),'below_carrier_bottom':low<cb,'straight_from_exit_mm':r['straight_from_exit_mm'],
                    'bend_radii_mm':sorted({b['radius_mm'] for b in r['bends']}),'length_mm':r6(r['length_mm']+2*val(P,'gh_mated_height_mm')),'min_clearance_mm':min(known.values()) if known else None,
                    'nearest':list(known.items())[:3],'keep_outs_below_margin':sorted(k for k,v in known.items() if v<m),'foreign_depth_bounds':depth})
            rows.append(row)
        out[l]={'design_length_mm':Ld,'rows':rows}
    return out


def robust(cand,P,T,rules,bow_cases,mech):
    """K4 after the worst-case stack for the installed state and every 15 mm release state, under each bow case (base half sine and the Stage32 bow cases)."""
    t=val(P,'release_travel_mm');sets={}
    for n,w in (('installed',(0,0)),)+STATES:
        tt=0 if n=='installed' else t
        sets[n]={l:s31.samples(constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tt*w[0],tt*w[1],P)['route'],bundle(P,l)) for l in LINKS}
    x0,y0,x1,y1=mech['boards']['A01-middle']['outline_mm'];out=[]
    for case in [None]+list(bow_cases):
        c=case
        if c and c.get('uniform_of_outline_diagonal'):c=dict(c,uniform_mm=r6(T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)))
        for n,smp in sets.items():
            rows=s32.robust_rows(cand,smp,P,T,rules,c)
            out.append({'bow_case':c['id'] if c else 'base (half sine 142-292)','bow_mm':c.get('uniform_mm') if c else None,'state':n,
                'tightest':{k:rows[0][k] for k in ('link','obstacle','sampled_clearance_mm','robust_spare_mm')} if rows else None,'meets_K4':all(r['meets_K4'] for r in rows),'rows':rows[:4]})
    return out


def cable_pairs(cand,P,T,rules):
    """Cable-to-cable gap: a state-independent plan bound (the plan projection of an arch is its exit-to-exit segment) and the sampled 3D gap for every 15 mm state pair."""
    seg={l:[cand['geo'][ENDS[l][0]]['exit_mm'][:2],cand['geo'][ENDS[l][1]]['exit_mm'][:2]] for l in LINKS}
    rad={l:bundle(P,l)['round_radius_mm'] for l in LINKS}
    plan=seg_dist2(seg['J-SIG'][0],seg['J-SIG'][1],seg['J-PWR'][0],seg['J-PWR'][1])-rad['J-SIG']-rad['J-PWR']
    t=val(P,'release_travel_mm');sm={}
    for l in LINKS:
        for n,w in (('installed',(0,0)),)+STATES:
            tt=0 if n=='installed' else t;sm[(l,n)]=s31.samples(constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tt*w[0],tt*w[1],P)['route'],bundle(P,l))[::3]
    pairs=[]
    for a in ('installed',)+tuple(n for n,_ in STATES):
        for b in ('installed',)+tuple(n for n,_ in STATES):
            g,_=s31.cable_gap(sm[('J-SIG',a)],sm[('J-PWR',b)]);pairs.append({'J-SIG':a,'J-PWR':b,'gap_mm':g})
    stack=s32.tol_stack('cable:',seg['J-SIG'][0]+[0],P,T,rules)
    return {'plan_bound_mm':r6(plan),'plan_segments_mm':seg,'pairs':pairs,'min_sampled_mm':min(p['gap_mm'] for p in pairs),'tolerance':stack,
        'robust_spare_mm':r6(plan-val(P,'placement_margin_mm')-stack['worst_case_mm']),'note':'3D distance is never below the plan distance, so the plan bound holds in every state'}


def rear_access(cand,P,inst_smp):
    """Latch faces and the +z corridor above each rear-face middle housing and each local housing: rigid hits, other-cable crossings, own bundle above the housing."""
    m=val(P,'placement_margin_mm');tool=val(P,'flat_tool_mm');top=val(P,'enclosure_rear_inner_z_mm');out={}
    route_straight={ENDS[l][i]:cand['routes'][l]['straight_from_exit_mm'][i] for l in LINKS for i in (0,1)}
    for l in LINKS:
        for end,ref in (('middle',ENDS[l][1]),('local',ENDS[l][0])):
            g=cand['geo'][ref];bx=g['box_mm'];z0,z1=sorted((g['face_z_mm'],g['exit_mm'][2]));axis=0 if g['pin_row_axis']=='y' else 1;other=1-axis;faces={}
            for sgn in (-1,1):
                face=bx[axis+(2 if sgn>0 else 0)];best=None;cab=None
                for o in cand['obs']:
                    if o['link']==l or o['kind']=='unknown_depth':continue
                    lo,hi=o['lo'],o['hi']
                    if not(lo[other]<bx[other+2] and hi[other]>bx[other] and lo[2]<z1 and hi[2]>z0):continue
                    d=(lo[axis]-face) if sgn>0 else (face-hi[axis])
                    if d>=-1e-9 and (best is None or d<best[0]):best=(d,o['id'])
                for l2 in LINKS:
                    for p,r in inst_smp[l2]:
                        if bx[0]-1e-9<=p[0]<=bx[2]+1e-9 and bx[1]-1e-9<=p[1]<=bx[3]+1e-9:continue
                        if not(bx[other]-r<p[other]<bx[other+2]+r and z0-r<p[2]<z1+r):continue
                        d=((p[axis]-r)-face) if sgn>0 else (face-(p[axis]+r))
                        if d>=-1e-9 and (cab is None or d<cab[0]):cab=(d,l2)
                free=min([x[0] for x in (best,cab) if x],default=None)
                faces[('+' if sgn>0 else '-')+'xy'[axis]]={'free_to_rigid_mm':r6(best[0]) if best else None,'nearest_rigid':best[1] if best else None,'free_to_cable_mm':r6(cab[0]) if cab else None,
                    'nearest_cable':cab[1] if cab else None,'flat_tool_fits':free is None or free>=tool[0]+m}
            col_lo=[bx[0],bx[1],z1];col_hi=[bx[2],bx[3],top]
            hits=sorted(o['id'] for o in cand['obs'] if o['link']!=l and o['kind']!='unknown_depth' and all(o['lo'][i]<col_hi[i] and o['hi'][i]>col_lo[i] for i in range(3)))
            over=sorted({l2 for l2 in LINKS if l2!=l for p,r in inst_smp[l2] if bx[0]-r-m<p[0]<bx[2]+r+m and bx[1]-r-m<p[1]<bx[3]+r+m and p[2]>z1})
            out[ref]={'end':end,'housing_box_mm':bx,'housing_z_mm':[z0,z1],'latch_faces':faces,'latch_side':'UNCONFIRMED (both long faces evaluated)',
                'rear_corridor':{'box_mm':bx,'z_mm':[z1,top],'rigid_hits':hits,'other_cable_above':over,'clear':not hits and not over},
                'own_straight_bundle_above_housing_mm':route_straight[ref],'grip_length_needed_mm':None,
                'finger_operation':'NOT_DETERMINED; a CAD gap is not finger operability (M33-03)'}
    return out


def catch_all_stack(P,T,rules,point):
    return s32.tol_stack('',point,P,T,[r for r in rules if r['match']==''])


def core_check(cand,P,T,rules,inst_smp):
    """Installed arches against the core envelope (core moved only in the installed state) with the board-chain stack; inter-carrier registration is UNCONFIRMED."""
    env=s31.core_envelope(cand['mech']);best=None
    for l in LINKS:
        for p,r in inst_smp[l]:
            d=s31.box_distance(p,env['lo'],env['hi'])-r-STEP/2
            if best is None or d<best[0]:best=(d,l,p)
    st=catch_all_stack(P,T,rules,best[2]);spare=best[0]-val(P,'placement_margin_mm')-st['worst_case_mm']
    return {'envelope':env,'arch_min_clearance_mm':r6(best[0]),'nearest':{'link':best[1],'at_mm':p6(best[2])},'tolerance':st,'robust_spare_mm':r6(spare),'clear':spare>=val(P,'robust_spare_mm')-1e-12,
        'registration':'core carrier to middle/jack carrier registration UNCONFIRMED (panel_to_carrier_registration_mm null in Stage32); not in the stack',
        'procedure':'K-PWR first, then 40 mm along +z; J-SIG/J-PWR are not touched'}


def required_radius(k,od,P,link):
    """Centreline radius for a maker rule of k x OD: inner surface of the dressed round bundle (used) and the innermost-conductor centreline reading (comparison)."""
    env=od*val(P,'round_bundle_factor')[link]/2+val(P,'bundle_dressing_allowance_mm')
    return {'surface':r6(k*od+env),'innermost_conductor_centreline':r6(k*od+env-od/2)}


def wire_table(P,route_R,wires):
    """Per wire and per cable: termination window, ratings, plating, current basis and the required radius under the maker rule; flex sensitivity at the JST maximum OD."""
    jmin,jmax=val(P,'wire_od_min_mm'),val(P,'wire_od_max_mm')
    loads=val(P,'j_pwr_conductor_current_max_A');ret=val(P,'j_pwr_agnd_return_bound_A');lim=val(P,'gh_contact_current_limit_A');rows=[]
    for w in wires:
        lo,hi=w['od_nominal_mm']-w['od_tolerance_mm'],w['od_nominal_mm']+w['od_tolerance_mm'];inwin=lo>=jmin-1e-9 and hi<=jmax+1e-9
        rating=val(P,'jst_current_rating_awg26_A') if w['awg']==26 else None
        rq={l:required_radius(w['bend_rule_x_od'],hi,P,l) for l in LINKS}
        common={'od_window':inwin,'voltage':w['voltage_V']>=val(P,'gh_voltage_rating_V'),'temperature':w['temperature_max_C']>=val(P,'gh_temperature_max_C'),
            'tin_plated':w['plating']=='tin','awg_in_jst_range':val(P,'wire_awg_range')[1]<=w['awg']<=val(P,'wire_awg_range')[0]}
        per={}
        for l in LINKS:
            cur=(rating is not None and rating>=lim) if l=='J-PWR' else False
            chk=dict(common,bend_rule_at_route_R=route_R>=rq[l]['surface']-1e-9,current=cur)
            per[l]={'checks':chk,'failed':[k for k,v in chk.items() if not v],'current_basis':('S-JST-EGH 1.0 A at AWG #26 >= Stage10 0.5 A contact limit' if cur else ('UNCONFIRMED: JST states no rating at AWG #'+str(w['awg'])) if l=='J-PWR' else 'UNCONFIRMED: J-SIG conductor current is not budgeted')}
            per[l]['qualified']=not per[l]['failed']
        rows.append({'mpn':w['mpn'],'awg':w['awg'],'conductor':w['conductor'],'insulation':w['insulation'],'od_range_mm':[r6(lo),r6(hi)],'voltage_V':w['voltage_V'],'temperature_max_C':w['temperature_max_C'],
            'maker_rule_x_od':w['bend_rule_x_od'],'rule_kind':'single stated bend radius; static or dynamic not stated','required_radius_mm':rq,'per_cable':per,'sources':w['sources']})
    generic={l:required_radius(val(P,'wire_bend_rule_x_od'),jmax,P,l) for l in LINKS}
    flex=[{'x_od':k,'required_radius_mm':{l:required_radius(k,jmax,P,l)['surface'] for l in LINKS},'route_R_meets':all(route_R>=required_radius(k,jmax,P,l)['surface']-1e-9 for l in LINKS)} for k in val(P,'flex_rule_sensitivity_x_od')]
    q={l:[r['mpn'] for r in rows if r['per_cable'][l]['qualified']] for l in LINKS}
    return {'route_radius_mm':route_R,'convention':val(P,'bend_radius_convention'),'radius_definitions':{'route_R':'centreline radius of the bundle axis (every bend)','required (used)':'k x OD + bundle envelope radius (inner surface of the bent bundle)','comparison':'k x OD + envelope radius - OD/2 (innermost conductor centreline)'},
        'wires':rows,'required_at_jst_max_od_10x_mm':generic,'route_meets_10x_for_any_window_wire':all(route_R>=generic[l]['surface']-1e-9 for l in LINKS),'flex_sensitivity':flex,
        'fan_in':{l:fan_in(P,l) for l in LINKS},'qualified_wires':q,'selection':None,'selection_status':'NULL: no identified wire passes every check for either cable (see per_cable failed)',
        'signal_power':{'J-SIG':{'conductors':val(P,'conductors')['J-SIG'],'current_A':val(P,'j_sig_conductor_current_A'),'requirement':'bend, OD window, tin plating, >= 50 V, >= 105 C; current UNCONFIRMED (not budgeted), so no wire qualifies for J-SIG on current'},
            'J-PWR':{'conductors':val(P,'conductors')['J-PWR'],'rail_current_max_conditional_A':loads,'agnd_return_bound_A':ret,'contact_limit_A':lim,'requirement':'as J-SIG, plus a current basis at the selected gauge: JST rates AWG #26 only'}}}


def strength(mech,P):
    """rail:middle:0 without notches (same cantilever model as Stage32); load sensitivity. R33 adds no retention part, so no guide strength exists to calculate."""
    f=mech['carrier_frames']['middle'];z0,z1=f['z_mm'];rail=f['rails_boxes_mm'][0];width=rail[2]-rail[0];Sy=val(P,'carrier_proof_MPa');SF=val(P,'strength_safety_factor')
    need([rail[1],rail[3]]==[s32.RAIL_ROOT_Y,s32.RAIL_TIP_Y],'rail:middle:0 spans y 142-274 (Stage10)')
    sec=s32.section(width,z1-z0,[]);lever=s32.RAIL_TIP_Y-s32.RAIL_ROOT_Y;allow=Sy/SF
    dirs=(('vertical',sec['I_vertical_mm4'],sec['c_vertical_mm']),('lateral',sec['I_lateral_mm4'],sec['c_lateral_mm']))
    rail={'notches':'none (R33 crosses no carrier rail)','net_section':{k:r6(v) for k,v in sec.items()},'lever_mm':lever,'allowable_tip_load_N':{d:r6(allow*I/(c*lever)) for d,I,c in dirs},
        'grid':[{'load_N':L,'direction':d,'peak_MPa':r6(L*lever*c/I),'meets':L*lever*c/I<=allow} for L in val(P,'load_sensitivity_N') for d,I,c in dirs]}
    return {'material':{'name':val(P,'carrier_material'),'E_MPa':val(P,'carrier_E_MPa'),'proof_min_MPa':Sy,'safety_factor':SF},'rail_middle_0':rail,'retention_parts':'none in R33 (lateral retention UNCONFIRMED)',
        'meets_at_planning_load':min(rail['allowable_tip_load_N'].values())>=val(P,'planning_load_N'),'b32_notched_rail_from_stage32':None,
        'not_covered':['rail root joint to the crossmember','fatigue and vibration','impact/handling loads (unknown)','certified machined material'],
        'status':'CALCULATED_CONDITIONALLY; not a physical strength result (M33-06)'}


def largest_clear_radius(region,boxes,step=0.25):
    """Largest circle (centre on a grid) inside the plan region that stays clear of every box."""
    x0,y0,x1,y1=region;best=(0.0,None);x=x0
    while x<=x1+1e-9:
        y=y0
        while y<=y1+1e-9:
            d=min([x-x0,x1-x,y-y0,y1-y]+[math.hypot(max(b[0]-x,0,x-b[2]),max(b[1]-y,0,y-b[3])) for b in boxes])
            if d>best[0]:best=(d,[r6(x),r6(y)])
            y+=step
        x+=step
    return best


def f33_screen(data,mech,P,T):
    """Front-face middle headers with every bend at the route radius: hook lower bound, release dip, the crossmember-slot path and the descent beyond the jack board's +y edge."""
    R=val(P,'route_radius_mm');m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');t=val(P,'release_travel_mm')
    geo=s31.header_geometry(mech,{});jz=val(P,'jack_carrier_z_mm');cb=val(P,'carrier_bottom_z_mm');plane=val(P,'foreign_pcb_plane_z_mm')
    jx=mech['carrier_frames']['jack']['crossmembers_boxes_mm'];need(mech['carrier_frames']['jack']['z_mm']==jz and mech['carrier_frames']['middle']['z_mm'][0]==cb,'carrier z from Stage10')
    jb=mech['boards']['A01-jack']['outline_mm'];mb=mech['boards']['A01-middle']['outline_mm'];rail=mech['carrier_frames']['middle']['rails_boxes_mm'][0];cb_out=mech['boards']['A01-control']['outline_mm']
    obs=s31.obstacles(mech,data['s32']['s31']['lock'],data['s32']['s31']['input']['parameters'],[])
    band=[jb[0],jx[1][3],mb[0],cb_out[1]]
    cols=[o['lo'][:2]+o['hi'][:2] for o in obs if o['kind']=='unknown_depth' and o['lo'][0]<band[2] and o['hi'][0]>band[0] and o['lo'][1]<band[3] and o['hi'][1]>band[1]]
    free,at=largest_clear_radius(band,cols);rows={}
    for l in LINKS:
        rb=bundle(P,l)['round_radius_mm'];ez=geo[ENDS[l][1]]['exit_mm'][2];low=ez-fan_in(P,l)['length_mm']-R
        slot=cb-jz[1];spare=(slot-2*rb)/2-m-T['carrier_face_mm']['value'];tmax=low-rb-m-plane[1]
        rows[l]={'hook_low_centreline_z_max_mm':r6(low),'installed_envelope_bottom_z_max_mm':r6(low-rb),'release_15mm_envelope_bottom_z_max_mm':r6(low-t-rb),
            'enters_front_unknown_volume_installed':low-rb<cb,'release_15mm_below_code_default_plane':low-t-rb-m<plane[1],'largest_travel_clear_of_plane_mm':r6(tmax),
            'slot_mm':r6(slot),'slot_robust_spare_per_side_mm':r6(spare),'slot_meets_K4':spare>=k4-1e-12,
            'descent_needs_clear_radius_mm':r6(rb+m),'descent_clear_of_foreign_columns':free>=rb+m,'installed_below_code_default_plane':low-rb-m<plane[1]}
    paths={'slot':{'status':'INFEASIBLE' if not any(r['slot_meets_K4'] for r in rows.values()) else 'UNKNOWN','basis':'slot z 30-34 between the jack and middle carriers fails K4 for both cables'},
        'plus_y_descent':{'band_xy_mm':band,'foreign_columns':len(cols),'largest_clear_radius_mm':r6(free),'at_mm':at,'status':'UNKNOWN',
            'basis':('a descent clear of the foreign XY columns exists in plan (largest clear radius '+f'{free:.2f}'+' mm)' if all(r['descent_clear_of_foreign_columns'] for r in rows.values()) else 'no descent position clears the foreign XY columns of unknown depth')
                +'; the run to the hook then lies at z <= '+' / '.join(f"{rows[l]['installed_envelope_bottom_z_max_mm']:.2f}" for l in LINKS)+' (J-SIG / J-PWR) installed'+(', below the code-default foreign PCB plane z 20-21.6' if any(r['installed_below_code_default_plane'] for r in rows.values()) else '')
                +', inside the undesigned front volume; the middle headers would have to move to y > 185'}}
    return {'route_radius_mm':R,'links':rows,'paths':paths,
        'descent':{'jack_board_xy_mm':jb,'middle_board_xy_mm':mb,'gap_between_jack_board_edge_and_rail_mm':r6(rail[0]-jb[2]),'jack_crossmembers_xy_mm':jx},
        'status':'UNKNOWN','classification':'UNKNOWN',
        'reason':'the slot path fails K4; the remaining path depends entirely on the undesigned front volume (a foreign PCB plane below the hook, foreign hardware depth limits and a reservation down to the release dip); R33 needs none of this',
        'smallest_change':'foreign depth limits and a front-volume reservation down to z '+f"{min(r['release_15mm_envelope_bottom_z_max_mm'] for r in rows.values()):.2f}"+('; the hook is below the code-default plane z 20-21.6 already installed, so no release travel avoids it' if any(r['installed_below_code_default_plane'] for r in rows.values()) else '; the 15 mm release stays above the code-default plane only for a travel of at most '+f"{min(r['largest_travel_clear_of_plane_mm'] for r in rows.values()):.2f}"+' mm (no maker basis for a shorter travel)')}


def slab(cand,P,l,tops):
    """In-plane swept volume of one arch: the vertical plane through both exits, thickened by the envelope radius + margin; two leg columns and a top band in (s, z)."""
    a=cand['geo'][ENDS[l][0]]['exit_mm'];b=cand['geo'][ENDS[l][1]]['exit_mm'];D=math.dist(a[:2],b[:2]);u=[(b[0]-a[0])/D,(b[1]-a[1])/D];n=[-u[1],u[0]]
    w=bundle(P,l)['round_radius_mm']+val(P,'placement_margin_mm')+STEP/2;R=val(P,'route_radius_mm');zmax=max(tops)+w
    rects=[{'part':'local leg','s':[-w,w],'z':[a[2],zmax]},{'part':'middle leg','s':[D-w,D+w],'z':[b[2],zmax]},{'part':'top band','s':[-w,D+w],'z':[min(tops)-R-w,zmax]}]
    return {'origin_xy_mm':p6(a[:2]),'direction_xy':p6(u),'normal_xy':p6(n),'half_thickness_mm':r6(w),'length_mm':r6(D),'parts':[{'part':x['part'],'s_mm':p6(x['s']),'z_mm':p6(x['z'])} for x in rects]}


def slab_overlaps_box(sl,lo,hi):
    """Separating-axis test of each slab part (oriented rectangle in plan x z range) against an axis-aligned box."""
    o=sl['origin_xy_mm'];u=sl['direction_xy'];n=sl['normal_xy'];w=sl['half_thickness_mm']
    for part in sl['parts']:
        if not(part['z_mm'][0]<hi[2] and lo[2]<part['z_mm'][1]):continue
        cs=[[o[0]+s*u[0]+t*n[0],o[1]+s*u[1]+t*n[1]] for s in part['s_mm'] for t in (-w,w)];bs=[[lo[0],lo[1]],[hi[0],lo[1]],[lo[0],hi[1]],[hi[0],hi[1]]]
        sep=False
        for ax in ([1,0],[0,1],u,n):
            p1=[c[0]*ax[0]+c[1]*ax[1] for c in cs];p2=[c[0]*ax[0]+c[1]*ax[1] for c in bs]
            if max(p1)<=min(p2)+1e-9 or max(p2)<=min(p1)+1e-9:sep=True;break
        if not sep:return True
    return False


def reservations(cand,P,st):
    """Volumes R33 needs that no designed part uses: the in-plane arch slab over every state, and +z access columns above all four housings. Proposals only; each is tested against every designed part."""
    m=val(P,'placement_margin_mm');top=val(P,'enclosure_rear_inner_z_mm');out=[]
    designed=[o for o in cand['obs'] if o['kind'] in ('known','assumed_height') and not o['id'].startswith('core-extraction')]
    env=s31.core_envelope(cand['mech']);designed.append({'id':'core-envelope-40mm','link':'K-PWR','lo':env['lo'],'hi':env['hi'],'kind':'known'})
    for l in LINKS:
        tops=[r['top_centreline_z_mm'] for r in st[l]['rows']];sl=slab(cand,P,l,tops)
        hits=sorted(o['id'] for o in designed if o['link']!=l and slab_overlaps_box(sl,o['lo'],o['hi']))
        out.append({'id':'RV-ARCH-'+l,'for':l+' arch in the installed state and every release case (2.45-15 mm, constant length)','slab':sl,'designed_part_overlaps':hits,
            'reason':'the arch occupies this in-plane volume above the A01 boards','status':'PROPOSAL_REQUIRES_OWNER_DECISION'})
        for ref in ENDS[l]:
            g=cand['geo'][ref];sw=g['sweep']['box_mm'];lo=[r6(sw[0]-m),r6(sw[1]-m),g['exit_mm'][2]];hi=[r6(sw[2]+m),r6(sw[3]+m),top]
            hits=sorted(o['id'] for o in designed if o['link']!=l and all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3)))
            out.append({'id':'RV-ACCESS-'+ref.split(':',1)[1].replace(':','-'),'for':ref+' latch press and pull from the rear','box_mm':lo[:2]+hi[:2],'z_mm':[lo[2],top],'designed_part_overlaps':hits,
                'reason':'+z access above the housing with the rear cover off','status':'PROPOSAL_REQUIRES_OWNER_DECISION'})
    return out


def retention(cand,P,T,rules,st):
    """No part holds the arches laterally. Report how far each arch may leave its plane before margin and stack are used up, and the z band on each leg that stays straight in every state (where a sliding guide could sit)."""
    m=val(P,'placement_margin_mm');R=val(P,'route_radius_mm');t15=val(P,'release_travel_mm');out={}
    ends={'board:'+cand['geo'][r]['board'] for l in LINKS for r in ENDS[l]}
    for l in LINKS:
        stack=catch_all_stack(P,T,rules,[0,0,0])['worst_case_mm'];worst=None
        for n,w in (('installed',(0,0)),)+STATES:
            tt=0 if n=='installed' else t15;smp=s31.samples(constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tt*w[0],tt*w[1],P)['route'],bundle(P,l))
            known,_=s31.evaluate_route(smp,[o for o in cand['obs'] if not o['id'].startswith(tuple(ends))],m,l)
            for k,v in known.items():
                if worst is None or v<worst[0]:worst=(v,k,n,tt)
        f=fan_in(P,l)['length_mm'];zones={}
        for i,end in ((0,'local'),(1,'middle')):
            e=cand['geo'][ENDS[l][i]]['exit_mm'][2];lo=[];hi=[]
            for r in st[l]['rows']:
                t=r['travel_mm'] if r['withdrawn'] in (('local','both') if end=='local' else ('middle','both')) else 0.0
                lo.append(e+t+f);hi.append(r['top_centreline_z_mm']-R)
            zones[end]={'z_mm':[r6(max(lo)),r6(min(hi))],'length_mm':r6(min(hi)-max(lo)),'exists':min(hi)>max(lo)}
        if worst is None:worst=(m+5,'none within '+f'{m+5:g}'+' mm (allowance is a lower bound)','every state',0)
        out[l]={'retention_part':None,'lateral_allowance_mm':r6(worst[0]-m-stack),'nearest':worst[1],'state':f"{worst[2]} {worst[3]:g}" if worst[2]!='every state' else worst[2],'excludes':'the boards carrying the cable ends (their clearance is the housing height, not a lateral gap)',
            'straight_zone_every_state':zones,'status':'UNCONFIRMED (M33-04)'}
    return out


def pcb_impact(cand,mech):
    """Pad moves of the two rear-face headers: every pin keeps its net; the front-face pads are removed and rear-face pads added (copper routing is a draft and is not recomputed)."""
    out={}
    for ref in sorted(MIDDLE):
        g=cand['geo'][ref];h=mech['headers'][ref];rows=[]
        for p,net in sorted(h['pins'].items()):
            a=h['pads_xyz_mm'][p][0];b=g['pads_xyz_mm'][p][0];rows.append({'pin':p,'net':net,'from_mm':p6(a),'to_mm':p6(b),'plan_move_mm':r6(math.dist(a[:2],b[:2]))})
        out[ref]={'pins':rows,'face':'front z 48.4 -> rear z 50','largest_plan_move_mm':max(r['plan_move_mm'] for r in rows),
            'consequences':['A01-middle gains SMT pads on its rear face (second SMT side); process UNCONFIRMED','nets and pin identities unchanged; connecting copper must be re-routed (routed copper is null in this candidate)']}
    return out


def evaluate(data,mech,P,T,rules,bow_cases):
    c=data['input']['candidates']['R33'];cand=build_r33(c,data,mech,P);m=val(P,'placement_margin_mm')
    inst={l:s31.samples(cand['routes'][l],bundle(P,l)) for l in LINKS};static={}
    for l in LINKS:
        known,depth=s31.evaluate_route(inst[l],cand['obs'],m,l)
        static[l]={'design_length_mm':cand['lengths'][l]['design_length_mm'],'top_centreline_z_mm':cand['installed'][l]['top_centreline_z_mm'],'min_surface_clearance_mm':min(known.values()) if known else None,
            'nearest':list(known.items())[:6],'foreign_depth_bounds':depth,'bends':cand['routes'][l]['bends'],'straight_from_exit_mm':cand['routes'][l]['straight_from_exit_mm'],'fan_in_mm':fan_in(P,l)['length_mm']}
    st=state_rows(cand,P);rob=robust(cand,P,T,rules,bow_cases,mech);cc=cable_pairs(cand,P,T,rules);acc=rear_access(cand,P,inst);core=core_check(cand,P,T,rules,inst)
    wires=wire_table(P,val(P,'route_radius_mm'),data['input']['wire_candidates']);stren=strength(mech,P);rv=reservations(cand,P,st);ret=retention(cand,P,T,rules,st)
    sw={}
    for ref in MIDDLE:
        g=cand['geo'][ref];lo=[g['sweep']['box_mm'][0],g['sweep']['box_mm'][1],g['sweep']['z_mm'][0]];hi=[g['sweep']['box_mm'][2],g['sweep']['box_mm'][3],g['sweep']['z_mm'][1]]
        sw[ref]={'box_mm':g['sweep']['box_mm'],'z_mm':g['sweep']['z_mm'],'known_overlaps':sorted(o['id'] for o in cand['obs'] if o['link']!=g['link'] and o['kind']!='unknown_depth' and all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3)))}
    rows=[r for l in LINKS for r in st[l]['rows']];top=val(P,'enclosure_rear_inner_z_mm')
    x0,y0,x1,y1=mech['boards']['A01-middle']['outline_mm'];ubow=T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)
    inst_top=max(r['envelope_top_z_mm'] for r in rows if r['withdrawn']=='installed')
    crit={'S1_static_clear':all(static[l]['min_surface_clearance_mm'] is None or static[l]['min_surface_clearance_mm']>=m for l in LINKS) and cc['plan_bound_mm']>=m,
        'S2_robust_K4':all(r['meets_K4'] for r in rob) and cc['robust_spare_mm']>=val(P,'robust_spare_mm')-1e-12,
        'S3_lateral_retention':bool(c.get('retention')),
        'S4_sweeps_and_access_clear':all(not v['known_overlaps'] for v in sw.values()) and all(a['rear_corridor']['clear'] for a in acc.values()),
        'S5_core_clear':core['clear'],'S6_strength_planning_load':stren['meets_at_planning_load'],
        'S7_release_15mm_clear_and_outside_front_volume':all(not r['slack_short'] and not r['keep_outs_below_margin'] and not r['below_carrier_bottom'] for r in rows),
        'S8_no_foreign_requirement':all(not r.get('foreign_depth_bounds') for r in rows),
        'S9_bend_maker_rule':wires['route_meets_10x_for_any_window_wire'] and all(r['bend_radii_mm']==[val(P,'route_radius_mm')] for r in rows if 'bend_radii_mm' in r),
        'S10_fan_in_every_state':all(min(r['straight_from_exit_mm'])>=fan_in(P,l)['length_mm']-1e-9 for l in LINKS for r in st[l]['rows'] if 'straight_from_exit_mm' in r),
        'S11_constant_length_and_cover':all(abs(r['length_mm']-st[l]['design_length_mm'])<1e-6 for l in LINKS for r in st[l]['rows'] if 'length_mm' in r) and inst_top+ubow+m<=top,
        'S12_reservations_clear_of_designed_parts':all(not r['designed_part_overlaps'] for r in rv)}
    failed=[k for k,v in crit.items() if not v]
    status='CONDITIONAL' if not failed else 'CONDITIONAL_PENDING_RETENTION' if failed==['S3_lateral_retention'] else 'INFEASIBLE'
    return cand,{'header_moves':cand['moved'],'pcb_impact':pcb_impact(cand,mech),'static':static,'states':st,'robust':rob,'cable_to_cable':cc,'sweeps':sw,'access':acc,'core_40mm':core,'wires':wires,'strength':stren,
        'reservations':rv,'retention':ret,'criteria':crit,'failed':failed,'installed_envelope_top_z_mm':inst_top,'cover_check':{'installed_top_z_mm':inst_top,'uniform_bow_mm':r6(ubow),'margin_mm':m,'cover_z_mm':top},
        'status':status,'physical':'NOT_RUN'},inst


def radius_headroom(data,mech,P,T,rules,flex):
    """Route radius scan at the design value, the flex-sensitivity radii and the horizontal-leg limit: clearance with the catch-all stack against K4, slack, the core envelope and the rear cover. Access and strength are not re-evaluated."""
    m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');top=val(P,'enclosure_rear_inner_z_mm');best=None;rows=[]
    geo=header_geometry(mech,data['input']['candidates']['R33']['header_moves'])
    leg=min(math.dist(geo[ENDS[l][0]]['exit_mm'][:2],geo[ENDS[l][1]]['exit_mm'][:2]) for l in LINKS)
    up=lambda v:math.ceil(v*2-1e-9)/2
    radii=sorted({val(P,'route_radius_mm')}|{up(max(f['required_radius_mm'].values())) for f in flex}|{math.floor(leg)/2,math.floor(leg)/2+0.5})
    for R in radii:
        Q=copy.deepcopy(P);Q['route_radius_mm']['value']=R;ok=True;why=None;row={'radius_mm':R}
        try:cand=build_r33(data['input']['candidates']['R33'],data,mech,Q)
        except ValueError as e:ok,why=False,str(e)
        if ok:
            st=state_rows(cand,Q);rr=[r for l in LINKS for r in st[l]['rows']]
            spare=min(r['min_clearance_mm'] for r in rr if r.get('min_clearance_mm') is not None)-m-catch_all_stack(Q,T,rules,[0,0,0])['worst_case_mm']
            inst={l:s31.samples(cand['routes'][l],bundle(Q,l)) for l in LINKS};core=core_check(cand,Q,T,rules,inst)
            itop=max(r['envelope_top_z_mm'] for r in rr if r['withdrawn']=='installed')
            row.update({'design_lengths_mm':{l:cand['lengths'][l]['design_length_mm'] for l in LINKS},'installed_top_z_mm':r6(itop),'service_top_z_mm':r6(max(r['envelope_top_z_mm'] for r in rr if 'envelope_top_z_mm' in r)),
                'robust_spare_conservative_mm':r6(spare),'core_robust_spare_mm':core['robust_spare_mm']})
            if any(r['slack_short'] or r.get('keep_outs_below_margin') for r in rr):ok,why=False,'keep-out or slack'
            elif spare<k4-1e-12:ok,why=False,'K4 with the catch-all stack'
            elif not core['clear']:ok,why=False,'core envelope'
            elif itop+m>top:ok,why=False,'installed arch above the rear cover'
        row.update({'fits':ok,'reason':why});rows.append(row)
        if not ok:break
        best=R
    return {'largest_fitting_radius_mm':best,'horizontal_leg_min_mm':r6(leg),'scan':rows,'checks':'clearance with the catch-all stack (K4), slack, core envelope with stack, rear cover; access, bow cases and strength not re-evaluated',
        'note':'a larger radius needs longer cables; the rear cover is off in every service state'}


def b32_summary(data):
    """Stage32 B32 results as committed (not recomputed): the maker bend failure and the uniform-bow K4 failure are preserved next to the half-sine pass."""
    a=data['s32_analysis']['candidates']['B32'];bow={c['case']:c for c in a['bow_sensitivity']}
    st=a['strength'];grid20=[r for n in st['notches'] for r in n['grid'] if r['load_N']==20 and not r['meets']]
    return {'status_stage32':a['status'],'failed_stage32':a['failed'],'tightest_robust_mm':a['robust'][0]['robust_spare_mm'],'bow_sensitivity':{k:{'robust_spare_mm':v['tightest']['robust_spare_mm'],'meets_K4':v['meets_K4']} for k,v in bow.items()},
        'route_radius_mm':a['bend']['route_radius_mm'],'required_at_jst_max_od_mm':a['bend']['required_centreline_radius_at_jst_max_od_mm'],'any_identified_wire_met':a['bend']['any_identified_wire_met'],
        'notched_rail_allowable_min_N':st['smallest_allowable_tip_load_N'],'notched_rail_20N_failures':len(grid20),
        'classification':'INFEASIBLE','reason':'infeasible for every identified wire (5 mm bends are below each maker rule; the bounded search found no smaller rule inside the JST window); for an unidentified wire it is UNKNOWN. K4 holds for the half-sine bow (0.199 mm) and fails for the uniform 1.282 mm bow (-0.382 mm)',
        'source_sha256':sha(S32/'analysis.json')}


def build(data,preserve=True):
    P,T,rules=validate_inputs(data);bow_cases=merged(data)[3];s29,_,_=s30.stage29_current();mech=s29['mech']
    cand,res,inst=evaluate(data,mech,P,T,rules,bow_cases)
    need(res['status']=='CONDITIONAL_PENDING_RETENTION','R33 must meet every Stage33 criterion except lateral retention under the stated assumptions: '+', '.join(res['failed']))
    res['radius_headroom']=radius_headroom(data,mech,P,T,rules,res['wires']['flex_sensitivity'])
    f33=f33_screen(data,mech,P,T);need(f33['paths']['slot']['status']=='INFEASIBLE' and f33['status']=='UNKNOWN','F33: slot path infeasible, the rest depends on the undesigned front volume')
    b32=b32_summary(data);need(not b32['any_identified_wire_met'] and not b32['bow_sensitivity']['uniform-diagonal']['meets_K4'],'Stage32 failures are preserved')
    res['strength']['b32_notched_rail_from_stage32']={'allowable_min_N':b32['notched_rail_allowable_min_N'],'failures_at_20N':b32['notched_rail_20N_failures']}
    cls={'B32':b32['classification'],'F33':f33['classification'],'R33':'CONDITIONAL'}
    lengths={l:{'design_length_proposal_mm':cand['lengths'][l]['design_length_mm'],'minimum_installed_mm':r6(cand['lengths'][l]['minimum_installed_mm']),'release_extra_15mm_mm':r6(cand['lengths'][l]['release_extra_mm']),
        'service_slack_mm':val(P,'service_slack_mm'),'measured_or_cut_mm':None} for l in LINKS}
    hr=res['radius_headroom'];flex_fit=all(any(x['fits'] and x['radius_mm']>=max(f['required_radius_mm'].values()) for x in hr['scan']) for f in res['wires']['flex_sensitivity'])
    results=[('R33 static and robust clearance, all bow cases (arch in its ideal plane)','CONDITIONAL'),('R33 15 mm release and core 40 mm (arch in its ideal plane)','CONDITIONAL'),
        ('R33 bend radius 12 mm vs 10x OD (inner-surface convention) and the fan-in at every exit','FEASIBLE_WITHIN_STATED_ASSUMPTIONS'),
        ('R33 at R 12 under the 15x/20x flex-rule sensitivity','INFEASIBLE' if not any(f['route_R_meets'] for f in res['wires']['flex_sensitivity']) else 'CONDITIONAL'),
        ('R33 geometry at the 15x/20x radii (scan: clearance, K4 with the catch-all stack, core, cover; longer cables)','CONDITIONAL' if flex_fit else 'INFEASIBLE'),
        ('R33 rear-face header move','CONDITIONAL'),('R33 lateral retention (no part; position not measured)','UNKNOWN'),
        ('Wire selection','UNKNOWN'),('AWG28 current qualification','UNKNOWN'),('J-SIG conductor current','UNKNOWN'),('Finger/tool operability at the latches','UNKNOWN'),
        ('F33 slot path (front-face headers)','INFEASIBLE'),('F33 descent beyond the jack board +y edge','UNKNOWN'),('B32 5 mm bends with every identified wire','INFEASIBLE'),('B32 uniform 1.282 mm bow','INFEASIBLE')]
    for _,v in results:need(v in CLASSES,'result class')
    model={'status':'DESIGN_STUDY_ONLY','approval':data['approval'],'parameters':{k:P[k] for k in data['input']['parameters']},'inherited_from':REL+'stage32/design-input.json',
        'R33':{'header_moves':res['header_moves'],'pcb_impact':res['pcb_impact'],'route_shape':cand['spec']['route_shape'],'fan_in':{l:fan_in(P,l) for l in LINKS},
            'routes':{l:{'vertices_mm':[p6(v) for v in [cand['geo'][ENDS[l][0]]['exit_mm'],[*cand['geo'][ENDS[l][0]]['exit_mm'][:2],cand['installed'][l]['top_centreline_z_mm']],[*cand['geo'][ENDS[l][1]]['exit_mm'][:2],cand['installed'][l]['top_centreline_z_mm']],cand['geo'][ENDS[l][1]]['exit_mm']]],
                'bends':cand['routes'][l]['bends'],'legs_mm':cand['routes'][l]['legs_mm'],'straight_from_exit_mm':cand['routes'][l]['straight_from_exit_mm']} for l in LINKS},
            'design_lengths':lengths,'retention':res['retention']},'procedure':data['input']['procedure']}
    states={'status':'DESIGN_STUDY_ONLY','R33':res['states'],'core_40mm':res['core_40mm'],'access':res['access'],
        'note':'every state keeps the design length; the arch top moves by half the length change; the rear cover is off for every service state; the arch is taken in its ideal vertical plane (lateral position UNCONFIRMED)'}
    ana={'status':'DESIGN_STUDY_ONLY','R33':{k:res[k] for k in ('static','robust','cable_to_cable','sweeps','wires','strength','retention','criteria','failed','status','installed_envelope_top_z_mm','cover_check','radius_headroom')},'F33':f33,'B32':b32}
    rvs={'status':'DESIGN_STUDY_ONLY','reservations':res['reservations'],'front_unknown_volume':{'entered_by_R33':any(r.get('below_carrier_bottom') for l in LINKS for r in res['states'][l]['rows']),
        'lowest_R33_envelope_z_mm':min(r['envelope_bottom_z_mm'] for l in LINKS for r in res['states'][l]['rows'] if 'envelope_bottom_z_mm' in r),'status':'UNKNOWN_NOT_FREE (unchanged from Stage32)'},
        'stage32_front_reservations':'RV-DIP and RV-ACCESS (front) are not needed by R33; they stay Stage32 proposals for B32'}
    report={'status':'DESIGN_STUDY_ONLY','recommendation':{'id':'R33','status':res['status'],'adopted':False,'requires':['owner decision on the rear-face header move (broader change)',
            'a lateral retention design, or a measured arch position (M33-04) within the allowance','owner decision on the RV-ARCH / RV-ACCESS reservations','a wire that passes every check (selection NULL)']},
        'classification':cls,'results':[{'result':k,'class':v} for k,v in results],'design_lengths':lengths,'failed':res['failed'],
        'open_conditions':{'retention':'S3 fails: no part holds the arches laterally; allowance '+', '.join(f"{l} {res['retention'][l]['lateral_allowance_mm']:.2f} mm" for l in LINKS),
            'wire':res['wires']['selection_status'],'awg28_current':'UNCONFIRMED','j_sig_current':'UNCONFIRMED','flex_rule':'UNCONFIRMED (15x needs R >= '+str(res['wires']['flex_sensitivity'][0]['required_radius_mm']['J-SIG'])+')',
            'latch_side':'UNCONFIRMED','finger_operation':'NOT_DETERMINED','rear_face_smt':'UNCONFIRMED','carrier_registration':'UNCONFIRMED',
            'gh_mating_force':'UNCONFIRMED (the board deflects toward rail:middle:0 when a rear-face housing is pushed on)'},
        'reservations':[r['id'] for r in res['reservations']],'measurements':[{'id':m_['id'],'item':m_['item'],'status':'NOT_RUN','value':None} for m_ in MEASUREMENTS],
        'decision_status':{'route':'STUDY_CANDIDATE_CONDITIONAL; not adopted','header_moves':'BROADER_CHANGE_PROPOSAL; not adopted','retention':'NOT_DESIGNED; open condition','reservations':'PROPOSAL_REQUIRES_OWNER_DECISION',
            'cable_lengths':'DESIGN_LENGTH_PROPOSAL; not measured, not cut','wire':'SELECTION_NULL; not selected','strength':'CALCULATED_CONDITIONALLY','M-01':'NOT_RUN','M-09':'NOT_RUN','M-12':'NOT_RUN'},
        'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('approval.json','design-input.json','sources.json','README.md')]+[S32/n for n in ('design-input.json','sources.json','approval.json','analysis.json','report.json')]+[ROOT/'design/grid/placements.lock.json']
    files+=[Path(__file__).with_name(n) for n in ('test_stage33_large_radius.py','stage32_service_envelope.py','stage31_cable_entry_redesign.py','stage30_din_design_integration.py','stage28_din_harness.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return {'model':model,'states':states,'analysis':ana,'reservations':rvs,'report':report,'res':res,'cand':cand,'f33':f33,'b32':b32,'mech':mech,'P':P,'inst':inst}


MEASUREMENTS=[
    {'id':'M33-01','item':'Selected wire MPN: OD with tolerance, strand count, plating, maker bend rule (installation and repeated flexing) and a current basis at its gauge with the GH contact'},
    {'id':'M33-02','item':'GH unmating on a bench coupon: stroke to free, force, latch side, conductor fan-in length at the housing; mating force on a rear-face header and the A01-middle deflection under it'},
    {'id':'M33-03','item':'Latch press and pull at all four housings from the rear, with the core and both arches in place (finger or tool)'},
    {'id':'M33-04','item':'Mock-up of both arches at the design lengths: installed shape, lateral position in each enclosure orientation against the allowance, rise during each release case'},
    {'id':'M33-05','item':'Enclosure rear inner face and rear-cover features over the RV-ARCH volumes'},
    {'id':'M33-06','item':'rail:middle:0 root joint and stiffness; any retention part added later'},
    {'id':'M33-07','item':'Cut lengths for the design lengths (M-09) and repeated-release abrasion at the housing exits (M-12)'},
    {'id':'M33-08','item':'A01-middle bow (M32-04), rear-face header position after assembly and core-to-middle carrier registration'}]


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed: '+', '.join(sorted(set(changed)-MUTABLE)))
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage33/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


# ---------- rendering ----------
f2,esc=s32.f2,s32.esc
COLOR=s32.COLOR


def render_md(b):
    res=b['res'];rep=b['report'];P=b['P'];f33=b['f33'];b32=b['b32'];yn=lambda x:'yes' if x else '**no**';n=len(res['criteria'])
    L=['# Stage33 large-radius study (generated)','','Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.','',
       '## Candidates','','| Candidate | What it is | Class | Why |','|---|---|---|---|',
       f"| B32 | Stage32 recommendation, front-face headers, 5 mm bends | {b32['classification']} | {b32['reason']} |",
       f"| F33 | Front-face headers, every bend at R {f2(f33['route_radius_mm'])} | {f33['classification']} | slot path fails K4 (J-SIG {f2(f33['links']['J-SIG']['slot_robust_spare_per_side_mm'])} mm, J-PWR {f2(f33['links']['J-PWR']['slot_robust_spare_per_side_mm'])} mm); the +y descent meets foreign columns of unknown depth (largest clear radius {f2(f33['paths']['plus_y_descent']['largest_clear_radius_mm'])} mm); 15 mm release envelope down to z {f2(f33['links']['J-SIG']['release_15mm_envelope_bottom_z_max_mm'])} |",
       f"| R33 | Rear-face headers, one arch per cable at R {f2(val(P,'route_radius_mm'))} | CONDITIONAL ({res['status']}) | meets {n-len(res['failed'])} of {n} criteria; fails {', '.join(res['failed'])}; needs owner decisions and a wire |",'',
       '## R33 criteria','','| Criterion | Result |','|---|---|']+[f"| {k} | {yn(v)} |" for k,v in res['criteria'].items()]
    L+=['','## Results by class','','| Result | Class |','|---|---|']+[f"| {r['result']} | {r['class']} |" for r in rep['results']]
    L+=['','## R33 geometry','']
    for h in res['header_moves']:L.append(f"- {h['ref']}: {h['from_origin_mm']} front → {h['to_origin_mm']} {h['face']} face (z {h['face_z_mm']}), {h['rotation_deg']}°, exit {h['exit_mm']}, sweep {h['sweep']['box_mm']} z {h['sweep']['z_mm']}; largest pad move {f2(res['pcb_impact'][h['ref']]['largest_plan_move_mm'])} mm; {h['status']}")
    for l in LINKS:
        s=res['static'][l];lg=rep['design_lengths'][l]
        L.append(f"- {l}: design length {lg['design_length_proposal_mm']} mm (minimum installed {f2(lg['minimum_installed_mm'])} + 15 mm release extra {f2(lg['release_extra_15mm_mm'])} + {lg['service_slack_mm']} slack; not a cut length); fan-in {f2(s['fan_in_mm'])} mm at each exit; installed arch top centreline z {f2(s['top_centreline_z_mm'])}; straight from the exits {' / '.join(f2(v) for v in s['straight_from_exit_mm'])} mm; nearest {', '.join(f'{a} {f2(v)}' for a,v in s['nearest'][:3]) or 'none within 5 mm'}")
    L+=['','## Lateral retention (S3 fails)','','No part holds the arches laterally. Allowance = smallest clearance over every state − 0.5 margin − catch-all stack.','','| Cable | Allowance (mm) | Nearest | Straight zone on the local leg in every state | Straight zone on the middle leg |','|---|---|---|---|---|']
    for l in LINKS:
        r=res['retention'][l];z=r['straight_zone_every_state']
        L.append(f"| {l} | {f2(r['lateral_allowance_mm'])} | {r['nearest']} ({r['state']}) | {'z '+f2(z['local']['z_mm'][0])+'–'+f2(z['local']['z_mm'][1]) if z['local']['exists'] else 'none'} | {'z '+f2(z['middle']['z_mm'][0])+'–'+f2(z['middle']['z_mm'][1]) if z['middle']['exists'] else 'none'} |")
    L+=['','## Service states (constant design length)','','| Cable | State | Travel (mm) | Arch top centreline z | Envelope top / bottom z | Straight from exits (mm) | Min clearance (mm) | Below carrier |','|---|---|---|---|---|---|---|---|']
    for l in LINKS:
        for r in res['states'][l]['rows']:
            if r['withdrawn']!='installed' and r['travel_mm'] not in (7.5,15):continue
            L.append(f"| {l} | {r['withdrawn']} | {r['travel_mm']} | {f2(r['top_centreline_z_mm'])} | {f2(r.get('envelope_top_z_mm'))} / {f2(r.get('envelope_bottom_z_mm'))} | {' / '.join(f2(v) for v in r['straight_from_exit_mm'])} | {f2(r.get('min_clearance_mm'))} | {'yes' if r.get('below_carrier_bottom') else 'no'} |")
    cc=res['cable_to_cable'];c=res['core_40mm']
    L+=['',f"Cable to cable: plan bound {f2(cc['plan_bound_mm'])} mm in every state (robust {f2(cc['robust_spare_mm'])}); sampled minimum over the 16 state pairs at 15 mm {f2(cc['min_sampled_mm'])} mm.",
        f"Core 40 mm (installed arches): {f2(c['arch_min_clearance_mm'])} mm, robust {f2(c['robust_spare_mm'])} mm after the {f2(c['tolerance']['worst_case_mm'])} mm stack; {c['registration']}.",'',
        '## K4 after the tolerance stack (R33)','','| Bow case | State | Tightest | Robust spare (mm) | K4 |','|---|---|---|---|---|']
    for r in res['robust']:t=r['tightest'];L.append(f"| {r['bow_case']} | {r['state']} | {t['link']} {t['obstacle']} | {f2(t['robust_spare_mm'])} | {yn(r['meets_K4'])} |")
    cv=res['cover_check'];L.append(f"\nThe bow also shifts the rear-face exits in z; the rear-cover check adds the uniform bow: installed top {f2(cv['installed_top_z_mm'])} + {f2(cv['uniform_bow_mm'])} + {cv['margin_mm']} ≤ {cv['cover_z_mm']}.")
    w=res['wires'];L+=['','## Wire qualification','',f"Route R {f2(w['route_radius_mm'])} mm (bundle centreline). Required R = k × OD + bundle envelope radius (inner surface); the innermost-conductor reading is listed for comparison. Selection: {w['selection_status']}.",'',
        '| Wire | AWG | OD (mm) | Rule | Required R J-SIG / J-PWR (mm) | Conductor-centreline reading (mm) | J-SIG fails | J-PWR fails |','|---|---|---|---|---|---|---|---|']
    for x in w['wires']:
        rq=x['required_radius_mm'];pc=x['per_cable']
        L.append(f"| {x['mpn']} | {x['awg']} | {x['od_range_mm'][0]}–{x['od_range_mm'][1]} | {x['maker_rule_x_od']}× OD | {f2(rq['J-SIG']['surface'])} / {f2(rq['J-PWR']['surface'])} | {f2(rq['J-SIG']['innermost_conductor_centreline'])} / {f2(rq['J-PWR']['innermost_conductor_centreline'])} | {', '.join(pc['J-SIG']['failed']) or 'none'} | {', '.join(pc['J-PWR']['failed']) or 'none'} |")
    g=w['required_at_jst_max_od_10x_mm'];L.append(f"\nAny wire in the JST window under 10× OD needs {f2(g['J-SIG']['surface'])} / {f2(g['J-PWR']['surface'])} mm. Flex sensitivity: "+'; '.join(f"{f['x_od']}× needs {f2(f['required_radius_mm']['J-SIG'])} / {f2(f['required_radius_mm']['J-PWR'])} mm ({'met' if f['route_R_meets'] else 'not met'} at R {f2(w['route_radius_mm'])})" for f in w['flex_sensitivity'])+'.')
    L.append('Fan-in at each housing exit (outermost pin to the bundle ring, S-bend at 10× OD + OD/2): '+'; '.join(f"{l} {f2(w['fan_in'][l]['length_mm'])} mm" for l in LINKS)+'.')
    sp=w['signal_power']['J-PWR'];L.append(f"J-PWR conditional rail maxima {', '.join(f'{k} {v*1000:.2f} mA' for k,v in sp['rail_current_max_conditional_A'].items())}; AGND return bound {sp['agnd_return_bound_A']*1000:.2f} mA; Stage10 contact limit {sp['contact_limit_A']} A. J-SIG current UNCONFIRMED.")
    hr=res['radius_headroom'];L+=['','## Radius scan','',f"Checks: {hr['checks']}.",'','| R (mm) | Fits | Design lengths J-SIG / J-PWR | Installed top z | Service top z | Robust spare (mm) | Reason |','|---|---|---|---|---|---|---|']
    for x in hr['scan']:L.append(f"| {x['radius_mm']} | {yn(x['fits'])} | {' / '.join(str(v) for v in x['design_lengths_mm'].values()) if 'design_lengths_mm' in x else '–'} | {f2(x.get('installed_top_z_mm'))} | {f2(x.get('service_top_z_mm'))} | {f2(x.get('robust_spare_conservative_mm'))} | {x['reason'] or ''} |")
    s=res['strength'];L+=['','## Strength (conditional)','',f"- rail:middle:0 has no notch in R33: allowable tip load {f2(s['rail_middle_0']['allowable_tip_load_N']['vertical'])} N vertical / {f2(s['rail_middle_0']['allowable_tip_load_N']['lateral'])} N lateral; it meets 20 N and 50 N (root joint not evaluated).",
        '- R33 adds no retention part, so no guide strength exists to calculate.',
        f"- B32 (Stage32, preserved): notched rail allowable {f2(s['b32_notched_rail_from_stage32']['allowable_min_N'])} N; {s['b32_notched_rail_from_stage32']['failures_at_20N']} notch cases fail at 20 N."]
    L+=['','## Access (R33, rear cover off)','']
    for ref,a in res['access'].items():L.append(f"- {ref} ({a['end']}): faces {'; '.join(k+' rigid '+f2(v['free_to_rigid_mm'])+' / cable '+f2(v['free_to_cable_mm']) for k,v in a['latch_faces'].items())} mm; +z corridor {'clear' if a['rear_corridor']['clear'] else 'BLOCKED '+str(a['rear_corridor']['rigid_hits']+a['rear_corridor']['other_cable_above'])}; straight bundle above the housing {f2(a['own_straight_bundle_above_housing_mm'])} mm; finger operation {a['finger_operation']}.")
    L+=['','## Reservations proposed (not adopted)','']
    for r in res['reservations']:
        if 'slab' in r:sl=r['slab'];L.append(f"- **{r['id']}**: vertical slab through {sl['origin_xy_mm']} along {sl['direction_xy']}, half thickness {f2(sl['half_thickness_mm'])} mm, length {f2(sl['length_mm'])} mm; parts "+'; '.join(f"{p['part']} s {p['s_mm']} z {p['z_mm']}" for p in sl['parts'])+f". Designed parts inside: {', '.join(r['designed_part_overlaps']) or 'none'}.")
        else:L.append(f"- **{r['id']}**: XY {r['box_mm']}, z {r['z_mm']}. {r['reason']}. Designed parts inside: {', '.join(r['designed_part_overlaps']) or 'none'}.")
    for k_,v in b['model']['procedure'].items():L+=['',f'**{k_}**','']+[f'{i}. {x}' for i,x in enumerate(v,1)]
    L+=['','## Measurements still NOT RUN','']+[f"- **{m_['id']}** {m_['item']}." for m_ in rep['measurements']]
    return '\n'.join(L)+'\n'


def svg_frame(title,W,H,legend):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif" font-size="9">',
        '<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#d6d6d6" stroke-width="2"/></pattern></defs>',
        '<rect width="100%" height="100%" fill="#fff"/>',f'<text x="10" y="16" font-size="12" font-weight="bold">{esc(title)}</text>']+[f'<text x="10" y="{30+12*i}">{esc(t)}</text>' for i,t in enumerate(legend)]


def style(o):
    i=o['id']
    if i.startswith('board:'):return 'fill="#e8f5e9" fill-opacity="0.6" stroke="#2e7d32" stroke-width="0.8"'
    if i.startswith('foreign'):return 'fill="#eeeeee" stroke="#bbb" stroke-width="0.3"'
    if i.startswith(('tool:','head:','spacer:','release:')):return 'fill="none" stroke="#9aa5b1" stroke-width="0.4" stroke-dasharray="1,1"'
    return 'fill="#9aa5b1" fill-opacity="0.5" stroke="#4a5562" stroke-width="0.4"'


LABELS=(('core-extraction-40mm','core + 40 mm'),('crossmember:rear:0','crossmember:rear:0'),('rail:middle:0','rail:middle:0'),('board:A01-jack','A01-jack'),('board:A01-core','A01-core'),('tool:A01-jack:M4','tool col. M4'))


def panel(out,ox,oy,sc,ax,ay,lim,title):
    (a0,a1),(b0,b1)=lim
    out.append(f'<text x="{ox}" y="{oy-6}" font-weight="bold">{esc(title)}</text><rect x="{ox}" y="{oy}" width="{(a1-a0)*sc:.1f}" height="{(b1-b0)*sc:.1f}" fill="none" stroke="#999"/>')
    flip=ay==2
    T=lambda p:(ox+(p[ax]-a0)*sc,oy+((b1-p[ay]) if flip else (p[ay]-b0))*sc)
    for v in range(int(math.ceil(a0/20))*20,int(a1)+1,20):
        x=ox+(v-a0)*sc;out.append(f'<line x1="{x:.1f}" y1="{oy+(b1-b0)*sc:.1f}" x2="{x:.1f}" y2="{oy+(b1-b0)*sc+3:.1f}" stroke="#666"/><text x="{x-6:.1f}" y="{oy+(b1-b0)*sc+12:.1f}" fill="#666">{"xyz"[ax]} {v}</text>')
    for v in range(int(math.ceil(b0/20))*20,int(b1)+1,20):
        y=oy+((b1-v) if flip else (v-b0))*sc;out.append(f'<line x1="{ox-3}" y1="{y:.1f}" x2="{ox}" y2="{y:.1f}" stroke="#666"/><text x="{ox+(a1-a0)*sc+3:.1f}" y="{y+3:.1f}" fill="#666">{"xyz"[ay]} {v}</text>')
    def rect(lo,hi,st,label=None):
        l=[max(lo[ax],a0),max(lo[ay],b0)];h=[min(hi[ax],a1),min(hi[ay],b1)]
        if l[0]>=h[0] or l[1]>=h[1]:return
        p=[0,0,0];q=[0,0,0];p[ax],p[ay]=l;q[ax],q[ay]=h;P_=T(p);Q=T(q)
        out.append(f'<rect x="{min(P_[0],Q[0]):.1f}" y="{min(P_[1],Q[1]):.1f}" width="{abs(Q[0]-P_[0]):.1f}" height="{abs(Q[1]-P_[1]):.1f}" {st}/>')
        if label:out.append(f'<text x="{min(P_[0],Q[0])+2:.1f}" y="{min(P_[1],Q[1])+9:.1f}" fill="#333" font-size="8">{esc(label)}</text>')
    def line(pts,st):out.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in (T(p) for p in pts))}" fill="none" stroke-linejoin="round" {st}/>')
    return T,rect,line


def draw_static(b,out,ox,oy,sc,ax,ay,lim,title,slab_,states):
    cand=b['cand'];P=b['P'];T,rect,line=panel(out,ox,oy,sc,ax,ay,lim,title);lab=dict(LABELS)
    if ay==2:rect([195,94,0],[318,300,34],'fill="url(#h)" stroke="none"')
    for o in cand['obs']:
        if o['kind']=='unknown_depth' or o['id'].startswith(('body:','core-extraction')) or (o['id'].startswith('release:') and o['link'] not in LINKS):continue
        k=1 if ax==0 else 0
        if ay==2 and not(o['hi'][k]>slab_[0] and o['lo'][k]<slab_[1]):continue
        if ay==1 and (o['id'].startswith('foreign') or o['hi'][2]<=40):continue
        rect(o['lo'],o['hi'],style(o),lab.get(o['id']))
    env=b['res']['core_40mm']['envelope'];rect(env['lo'],env['hi'],'fill="none" stroke="#111" stroke-width="0.8" stroke-dasharray="6,3"',lab['core-extraction-40mm'])
    for l in LINKS:
        for ref in ENDS[l]:
            g=cand['geo'][ref];bx=g['box_mm'];z=sorted((g['face_z_mm'],g['exit_mm'][2]))
            rect([bx[0],bx[1],z[0]],[bx[2],bx[3],z[1]],f'fill="{COLOR[l]}" fill-opacity="0.3" stroke="{COLOR[l]}" stroke-width="0.6"')
    if ay==2:
        for z,lb in ((105,'rear cover inner face z 105'),(50,'A01-middle rear face z 50'),(34,'middle carrier bottom z 34; below: front volume UNKNOWN')):
            p=[0,0,0];q=[0,0,0];p[ax]=lim[0][0];q[ax]=lim[0][1];p[2]=q[2]=z;A=T(p);B=T(q)
            out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#666" stroke-width="0.5" stroke-dasharray="1,2"/><text x="{A[0]+3:.1f}" y="{A[1]-2:.1f}" fill="#555">{esc(lb)}</text>')
    for l in LINKS:
        wpx=2*bundle(P,l)['round_radius_mm']*sc
        for n,tl,tm,dash in states:
            c=constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tl,tm,P);pts=c['route']['dense'][::2]+[c['route']['dense'][-1]]
            if not tl and not tm:line(pts,f'stroke="{COLOR[l]}" stroke-opacity="0.18" stroke-width="{wpx:.1f}"')
            line(pts,f'stroke="{COLOR[l]}" stroke-width="1.2" {dash}')
            for ref,t in ((ENDS[l][0],tl),(ENDS[l][1],tm)):
                if not t:continue
                g=cand['geo'][ref];bx=g['box_mm'];z=sorted((g['face_z_mm']+t,g['exit_mm'][2]+t))
                rect([bx[0],bx[1],z[0]],[bx[2],bx[3],z[1]],f'fill="none" stroke="{COLOR[l]}" stroke-width="0.8" {dash}')
    return T


def render_plan(b):
    P=b['P'];res=b['res'];W,H=1010,940
    out=svg_frame('Stage33 R33 plan and elevations (design study; modelled envelopes, not physical clearance)',W,H,
        ['Blue J-SIG, red J-PWR: installed arches at the design length (pale band = bundle envelope width). Black dashed: core box incl. the 40 mm withdrawal. Hatched: front volume z 0-34 (UNKNOWN, not free).',
         'Elevations are projections: an arch drawn over the core box or a part lies beside it in the hidden axis (see the plan). Dotted grey: release sweeps, tool columns, screw heads. No retention part exists.'])
    inst=[('installed',0,0,'')]
    draw_static(b,out,20,80,6.0,0,1,((195,320),(140,190)),'Plan XY (+y down; parts above z 40 only)',None,inst)
    draw_static(b,out,20,430,4.0,0,2,((195,320),(0,110)),'Elevation XZ (y 145-176 projected; +z up = toward the rear)',(145,176),inst)
    draw_static(b,out,580,430,4.0,1,2,((140,240),(0,110)),'Elevation YZ (x 200-300 projected)',(200,300),inst)
    y=H-48
    for l in LINKS:
        s=res['static'][l];out.append(f'<text x="20" y="{y}" fill="{COLOR[l]}">{l}: design length {s["design_length_mm"]} mm (not a cut length); arch top centreline z {s["top_centreline_z_mm"]:.1f}; every bend R {val(P,"route_radius_mm"):g}; fan-in {s["fan_in_mm"]:.1f} mm; straight from the exits {" / ".join(f"{v:.1f}" for v in s["straight_from_exit_mm"])} mm</text>');y+=13
    out.append(f'<text x="20" y="{y}">Status {esc(res["status"])}: the rear-face header move is a broader-change proposal; lateral retention is not designed; physical NOT_RUN</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'


def render_states(b):
    P=b['P'];W,H=1010,600;t=val(P,'release_travel_mm')
    out=svg_frame('Stage33 R33 service states at constant design length (design study)',W,H,
        ['Solid: installed. Dashed: middle housing withdrawn 15 mm. Dotted: local housing withdrawn 15 mm. Dash-dot: both withdrawn (withdrawn housings outlined). The arch top rises by half the length change.',
         'Projections: arches drawn over the core box lie beside it in the hidden axis. No state goes below the middle carrier bottom z 34. The core is moved only with every housing installed.'])
    st=[('installed',0,0,''),('middle',0,t,'stroke-dasharray="5,3"'),('local',t,0,'stroke-dasharray="1,2"'),('both',t,t,'stroke-dasharray="6,2,1,2"')]
    draw_static(b,out,20,70,4.0,0,2,((195,320),(30,120)),'Elevation XZ, all states',(145,176),st)
    draw_static(b,out,580,70,4.0,1,2,((140,240),(30,120)),'Elevation YZ, all states',(200,300),st)
    y=455
    for l in LINKS:
        for r in b['res']['states'][l]['rows']:
            if r['travel_mm']!=t and r['withdrawn']!='installed':continue
            out.append(f'<text x="20" y="{y}" fill="{COLOR[l]}">{l} {r["withdrawn"]} {r["travel_mm"]:g} mm: top centreline z {r["top_centreline_z_mm"]:.1f}, straight from the exits {" / ".join(f"{v:.1f}" for v in r["straight_from_exit_mm"])} mm, min clearance {f2(r["min_clearance_mm"])} mm</text>');y+=13
    out.append('</svg>');return '\n'.join(out)+'\n'


def outputs(b):
    return {'model.json':dump(b['model']),'states.json':dump(b['states']),'analysis.json':dump(b['analysis']),'reservations.json':dump(b['reservations']),'report.json':dump(b['report']),
        'summary.md':render_md(b),'plan-elevation.svg':render_plan(b),'service-states.svg':render_states(b)}


def run(data,preserve=True):
    b=build(data,preserve);return b,outputs(b)


def check_outputs(bodies):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage33-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            # Stage32 bytes are immutable from BASE; its own history replay (Stage31) already passed there.
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage32_service_envelope.py','--check','--check-review'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage32_service_envelope.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage32 source checkpoint (generator, review binding, tests normal and -O)')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage33/'+n for n in GENERATED}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-history','check-review'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.check_history:history()
    b,bodies=run(load())
    need(set(bodies)==set(GENERATED),'generated file set')
    if a.check:check_outputs(bodies)
    else:
        for name,body in bodies.items():(OUT/name).write_text(body)
    if a.check_review:review()
    print('PASS Stage33 source checks: '+'; '.join(f"{k} {v}" for k,v in b['report']['classification'].items())+'; physical/native NOT RUN')


if __name__=='__main__':main()
