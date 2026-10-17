"""A01 J-SIG/J-PWR service envelope, retention, tolerance and carrier-strength study on the Stage31 B working option (design only; no native/physical claims)."""
import argparse
import copy
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import stage28_din_harness as s28
import stage30_din_design_integration as s30
import stage31_cable_entry_redesign as s31

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage32'
BASE='66533ba69b03c1ad7b43bf41baf69c0b3d258673'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage32_service_envelope.py','test_stage32_service_envelope.py')}
need,read,dump,sha=s28.need,s28.read,s28.dump,s28.sha
LINKS=s31.LINKS
ENDS=s31.ENDS
STEP=s31.STEP_MM
CLASSES={'MAKER_DOC','EXISTING_DESIGN','DESIGN_ASSUMPTION','UNCONFIRMED'}
MAKER_AUTH={'MAKER_PRIMARY','MAKER_MIRROR','FABRICATOR_PRIMARY','SUPPLIER_PRIMARY'}
GENERATED=('model.json','envelope.json','analysis.json','neighbour.json','report.json','summary.md','envelope.svg')
RAIL_TIP_Y=274.0
RAIL_ROOT_Y=142.0


def r6(v):return round(v,6)
def p6(p):return [r6(v) for v in p]
def val(params,k):return params[k]['value']


# ---------- inputs ----------
def load():
    return {'approval':read(OUT/'approval.json'),'input':read(OUT/'design-input.json'),'sources':read(OUT/'sources.json'),'s31':s31.load()}


def validate_sources(src):
    ids=[s['id'] for s in src['sources']];need(len(ids)==len(set(ids)),'unique source ids')
    for s in src['sources']:
        if s['authority']=='REPO_DESIGN':need((ROOT/s['path']).exists(),'repository source exists '+s['id'])
        elif s['authority'] in MAKER_AUTH:need(s.get('url') and s.get('revision') and s.get('locators'),'maker source carries url, revision and locator '+s['id'])
    return {s['id']:s for s in src['sources']}


def classed(name,p,src):
    need(p.get('class') in CLASSES,'value class must be one of '+'/'.join(sorted(CLASSES))+': '+name)
    for sid in p.get('sources',[]):need(sid in src,'unknown source '+sid+' for '+name)
    c=p['class'];auth={src[s]['authority'] for s in p.get('sources',[])}
    if c=='MAKER_DOC':need({src[s]['authority'] for s in p.get('sources',[]) if not str(src[s].get('availability','')).startswith('NOT_')}&MAKER_AUTH,'MAKER_DOC value without an obtained maker document: '+name)
    if c=='EXISTING_DESIGN':need('REPO_DESIGN' in auth,'EXISTING_DESIGN value without a repository source: '+name)
    if c=='UNCONFIRMED':need(p.get('value') is None,'UNCONFIRMED value must stay null: '+name)
    if c=='DESIGN_ASSUMPTION':need(p.get('note') or p.get('derivation') or name.endswith('_sensitivity_mm') or name.endswith('_sensitivity_N'),'DESIGN_ASSUMPTION needs a stated basis: '+name)


def validate_inputs(data):
    a=data['approval'];inp=data['input'];src=validate_sources(data['sources'])
    need(a['status']=='DESIGN_STUDY_CHANGES_ALLOWED' and a['decided_by']=='OWNER','owner approval record')
    need(set(a['changeable']['header_refs'])<={ENDS[l][1] for l in LINKS},'only the middle J-SIG/J-PWR headers may move')
    need(a['changeable']['carrier_local_shape']==['rail:middle:0'],'carrier change limited to rail:middle:0')
    need(inp['status']=='DESIGN_STUDY_INPUT_NOT_MEASURED','design input status')
    s28.no_claims(inp,'design-input');s28.no_claims(a,'approval');s28.no_claims(data['sources'],'sources')
    P=inp['parameters']
    for k,p in P.items():classed(k,p,src)
    for k,p in inp['tolerances'].items():classed(k,p,src)
    for w in inp['wire_candidates']:
        for sid in w['sources']:need(src[sid]['authority'] in MAKER_AUTH,'wire candidate values from a maker document '+w['mpn'])
    for sc in inp['neighbour_scenarios']:classed(sc['id'],dict(sc,value=sc['solids']),src)
    g=P['geometric_separation_mm'];need(abs(g['value']-(val(P,'gh_header_height_mm')-(val(P,'gh_mated_height_mm')-val(P,'gh_housing_height_mm'))))<1e-9,'geometric separation is derived from the JST reference dimensions')
    p31=data['s31']['input']['parameters']
    need(val(P,'release_travel_mm')==p31['release_travel_mm']['value']==15,'release travel stays the Stage10 15 mm design basis; a shorter travel needs a maker stroke')
    need(val(P,'placement_margin_mm')==p31['placement_margin_mm']['value'],'placement margin is not relaxed')
    need(val(P,'robust_spare_mm')==p31['robust_spare_mm']['value'],'K4 threshold is not relaxed')
    need(val(P,'wire_od_max_mm')==p31['wire_od_mm']['value'],'envelopes use the JST maximum OD')
    need({k:val(P,'round_bundle_factor')[k] for k in LINKS}=={k:p31['round_bundle_factor'][k] for k in LINKS},'bundle factors match Stage31')
    need(val(P,'design_bend_radius_mm')==p31['design_bend_radius_mm']['value'],'design bend radius carried from Stage31')
    need(val(P,'straight_lead_mm')==p31['straight_lead_mm']['value'],'straight lead carried from Stage31')
    T=inp['tolerances'];need(T['pcb_bow_fraction']['value']>=0.0075,'PCB bow allowance is not reduced below the 0.75 % limit')
    need(val(P,'strength_safety_factor')>=1.5,'strength safety factor is not reduced')
    need(val(P,'panel_rear_z_mm')==0.0 and val(P,'panel_front_z_mm')==-2.0,'panel datum follows Stage10 (rear z 0, front z -2)')
    c=inp['candidates']['B32']
    for ref in c['header_moves']:need(ref in a['changeable']['header_refs'],'header move outside the approval '+ref)
    for gd in c['guides']:need(gd['obstacle'] in a['changeable']['carrier_local_shape'],'guide outside the approved carrier shape '+gd['id'])
    need(sorted(gd['link'] for gd in c['guides'])==sorted(LINKS),'one guide per cable')


# ---------- geometry ----------
def bundle_r(P,link):return val(P,'wire_od_max_mm')*val(P,'round_bundle_factor')[link]/2


def bow(P,T,y,case=None):
    """A01-middle bow toward the carrier: half sine of 0.75 % over a y span, or a uniform value (sensitivity case)."""
    if case and 'uniform_mm' in case:return case['uniform_mm']
    y0,y1=case['span_y_mm'] if case else T['bow_span_y_mm']['value'];L=y1-y0
    if not y0<y<y1:return 0.0
    return T['pcb_bow_fraction']['value']*L*math.sin(math.pi*(y-y0)/L)


def guide_geometry(gd,route,P,rules,link):
    """Derive the captive guide (saddle, strap, latch tab, snap legs) and its notch from the straight route segment over the rail."""
    x0,x1=gd['rail_x_mm'];oh=rules['overhang_mm'];sb=rules['straight_beyond_guide_mm']
    pts=[(p,t) for p,t in zip(route['dense'],route['tags']) if x0-oh-sb<=p[0]<=x1+oh+sb]
    need(pts,'route crosses the guide '+gd['id'])
    need(all(t[0]=='leg' for _,t in pts),'route must be straight through guide '+gd['id']+' and '+str(sb)+' mm beyond it')
    ys={r6(p[1]) for p,_ in pts};zs={r6(p[2]) for p,_ in pts}
    need(len(ys)==1 and len(zs)==1,'route must run along x at constant y and z through guide '+gd['id'])
    yc=ys.pop();zc=zs.pop();rb=bundle_r(P,link);Rs=rb+rules['seat_radial_clearance_mm'];wh=Rs+rules['wall_thickness_mm']
    fit=rules['notch_fit_per_side_mm'];ny=[math.floor((yc-wh-fit)*10+1e-6)/10,math.ceil((yc+wh+fit)*10-1e-6)/10]
    floor=math.floor((zc-Rs-rules['seat_thickness_mm'])*10+1e-6)/10;st=rules['strap_thickness_mm'];xa,xb=x0-oh,x1+oh
    xc=(x0+x1)/2;sw=rules['strap_width_mm'];lt=rules['latch_tab_mm'];leg=rules['snap_leg_mm']
    sgn=-1 if gd['latch_side']=='-y' else 1;ty=yc+sgn*(wh-lt[1]/2)
    b=lambda n,lo,hi:{'id':f"guide:{gd['id']}:{n}",'lo':p6(lo),'hi':p6(hi),'kind':'known','link':link,'base':'guide:'+gd['id']}
    bodies=[b('base',[xa,yc-wh,floor],[xb,yc+wh,zc-Rs]),b('wall-',[xa,yc-wh,zc-Rs],[xb,yc-Rs,zc]),b('wall+',[xa,yc+Rs,zc-Rs],[xb,yc+wh,zc]),
        b('strap',[xc-sw/2,yc-wh,zc+Rs],[xc+sw/2,yc+wh,zc+Rs+st]),b('strap-',[xc-sw/2,yc-wh,zc],[xc+sw/2,yc-Rs,zc+Rs]),b('strap+',[xc-sw/2,yc+Rs,zc],[xc+sw/2,yc+wh,zc+Rs]),
        b('latch',[xc+sw/2,ty-lt[1]/2,zc+Rs+st-lt[2]],[xb+lt[0],ty+lt[1]/2,zc+Rs+st]),
        b('leg-',[x0-leg['thickness'],yc-wh,floor-leg['depth_below_floor']],[x0,yc+wh,zc-Rs]),b('leg+',[x1,yc-wh,floor-leg['depth_below_floor']],[x1+leg['thickness'],yc+wh,zc-Rs])]
    return {'id':gd['id'],'link':link,'obstacle':gd['obstacle'],'centre_mm':[r6(xc),yc,zc],'bundle_radius_mm':r6(rb),'seat_radius_mm':r6(Rs),'radial_clearance_mm':r6(Rs-rb),
        'notch':{'id':'N'+gd['id'][1:],'obstacle':gd['obstacle'],'y_mm':ny,'relieved_top_z_mm':floor,'link':link,'status':'PROPOSAL_NOT_ADOPTED'},
        'saddle_mm':{'length_x':r6(xb-xa),'width_y':r6(2*wh),'seat_thickness':r6(zc-Rs-floor),'wall':rules['wall_thickness_mm'],'end_flare_radius':rules['end_flare_radius_mm'],'x':[xa,xb]},
        'strap_mm':{'width':sw,'thickness':st,'inner_radius':r6(Rs),'top_z':r6(zc+Rs+st),'latch_side':gd['latch_side'],'latch_tab_box':bodies[6]['lo'][:2]+bodies[6]['hi'][:2]},
        'snap_legs_mm':dict(leg,x=[[r6(x0-leg['thickness']),x0],[x1,r6(x1+leg['thickness'])]],z=[r6(floor-leg['depth_below_floor']),r6(zc-Rs)]),
        'material':rules['material'],'bodies':bodies,'status':'PROPOSAL_NOT_ADOPTED'}


def build_candidate(cid,c,data,mech,P,T):
    """Header geometry, notches, guides, filleted routes and the obstacle field of one candidate."""
    p31=data['s31']['input']['parameters'];a=data['approval'];rules=data['input']['retention_rules']
    moves=c['header_moves'];geo=s31.header_geometry(mech,moves)
    moved=s31.check_header_moves(mech,geo,moves,{'changeable':{'header_refs':[r for r in moves]}}) if moves else []
    rad=val(P,'design_bend_radius_mm');lead=val(P,'straight_lead_mm');routes={};guides=[]
    for link in LINKS:
        v=s31.route_vertices(geo,link,c['routes'][link])
        for end,(p,q) in (('local',(v[0],v[1])),('middle',(v[-1],v[-2]))):
            g=geo[ENDS[link][0 if end=='local' else 1]];d=s31.unit(s31.sub(q,p))
            need(abs(d[2]-g['axis'])<1e-9,f'{link} {end} route must leave the housing along its axis')
        routes[link]=s31.fillet_route(v,rad,(lead,lead))
    if 'guides' in c:
        for gd in c['guides']:guides.append(guide_geometry(gd,routes[gd['link']],P,rules,gd['link']))
        reliefs=[gg['notch'] for gg in guides]
    else:
        reliefs=c['rail_reliefs']
    obs=s31.obstacles(s31.moved_mech(mech,geo),data['lock'],p31,reliefs)
    for gg in guides:obs+=gg['bodies']
    lengths={l:design_length(geo,l,c['routes'][l],P) for l in LINKS}
    installed={l:constant_length(geo,l,c['routes'][l],P,lengths[l]['design_length_mm'],0,(0,0)) for l in LINKS}
    for l in LINKS:need(installed[l]['route'] is not None,'installed slack loop fits '+l)
    return {'id':cid,'geo':geo,'moved':moved,'routes':{l:installed[l]['route'] for l in LINKS},'routes_minimum':routes,'lengths':lengths,'installed':installed,
        'guides':guides,'reliefs':reliefs,'obs':obs,'spec':c}


# ---------- clearance and tolerance ----------
def nearest(smp,obs,link,kinds=('known','assumed_height')):
    lo=[min(p[i] for p,_ in smp)-30 for i in range(3)];hi=[max(p[i] for p,_ in smp)+30 for i in range(3)];out=[]
    for o in obs:
        if o['link']==link or o['kind'] not in kinds or not all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3)):continue
        out.append((o,[(s31.box_distance(p,o['lo'],o['hi'])-r-STEP/2,p) for p,r in smp]))
    return out


def tol_stack(oid,point,P,T,rules,extra=(),case=None,bow_mm=None):
    rule=next(r for r in rules if oid.startswith(r['match']))
    parts=[]
    for k in list(rule['contributors'])+list(extra):
        if k=='pcb_bow':parts.append((k,bow(P,T,point[1],case) if bow_mm is None else bow_mm))
        else:parts.append((k,T[k]['value']))
    return {'contributors':{k:r6(v) for k,v in parts},'worst_case_mm':r6(sum(v for _,v in parts)),'rss_mm':r6(math.sqrt(sum(v*v for _,v in parts)))}


def robust_rows(cand,smp,P,T,rules,case=None):
    """Per obstacle, the sample that minimises clearance - margin - worst-case tolerance at that sample; strap tops take the largest bow over the strap and latch-tab footprint."""
    m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');rows=[]
    def row(link,oid,p,d,ts,frm=None):
        r={'link':link,'obstacle':oid,'at_mm':p6(p),'sampled_clearance_mm':r6(d),'tolerance':ts,'spare_after_margin_mm':r6(d-m),
            'robust_spare_mm':r6(d-m-ts['worst_case_mm']),'robust_spare_rss_mm':r6(d-m-ts['rss_mm']),'meets_K4':d-m-ts['worst_case_mm']>=k4-1e-12}
        if frm:r['from']=frm
        return r
    for link in LINKS:
        for o,ds in nearest(smp[link],cand['obs'],link):
            if min(d for d,_ in ds)>m+3:continue
            best=min(((d-tol_stack(o['id'],p,P,T,rules,case=case)['worst_case_mm'],d,p) for d,p in ds),key=lambda x:x[0])
            rows.append(row(link,o['id'],best[2],best[1],tol_stack(o['id'],best[2],P,T,rules,case=case)))
    for gg in cand['guides']:
        strap=next(b for b in gg['bodies'] if b['id'].endswith(':strap'));tab=next(b for b in gg['bodies'] if b['id'].endswith(':latch'))
        y0=min(strap['lo'][1],tab['lo'][1]);y1=max(strap['hi'][1],tab['hi'][1]);n=int(round((y1-y0)/0.05))
        bw=max(bow(P,T,y0+i*(y1-y0)/n,case) for i in range(n+1))
        for b in (strap,tab):
            for o in cand['obs']:
                if not o['id'].startswith('board:A01-middle') or not all(o['lo'][i]<b['hi'][i]+5 and o['hi'][i]>b['lo'][i]-5 for i in range(3)):continue
                d=s31.box_distance_boxes(b['lo'],b['hi'],o['lo'],o['hi'])
                rows.append(row(gg['link'],o['id'],gg['centre_mm'],d,tol_stack(o['id'],gg['centre_mm'],P,T,rules,('saddle_seat_mm','saddle_seating_mm','strap_bore_mm','strap_thickness_mm'),case,bw),b['id']))
    return sorted(rows,key=lambda r:(r['robust_spare_mm'],r['link'],r['obstacle'],r.get('from','')))


# ---------- states ----------
def release_shape(geo,link,spec,P,t,which):
    """Bend-feasible release surrogate (Stage31 rule) for a travel t: the nearest loop-top/hook waypoint pair moves just enough to keep the lead and an r bend. Used only to size the design length."""
    rad=val(P,'design_bend_radius_mm');lead=val(P,'straight_lead_mm');w=[list(map(float,x)) for x in spec['waypoints_mm']];dl,dm=which
    for flag,idx,ref in ((dl,(0,1),ENDS[link][0]),(dm,(-1,-2),ENDS[link][1])):
        if not flag:continue
        g=geo[ref];ax=g['axis'];e=g['exit_mm'][2]+ax*t;need(all(w[i][2]==w[idx[0]][2] for i in idx),'release group shares one z '+link)
        move=max(0.0,ax*(e+ax*(lead+rad)-w[idx[0]][2]))
        for i in idx:w[i][2]+=ax*move
    return s31.fillet_route(s31.route_vertices(geo,link,{'waypoints_mm':w},(t*dl,t*dm)),rad,(lead,lead))


def design_length(geo,link,spec,P):
    """Design length = minimum installed length + largest Stage31-rule release extra at the Stage10 travel + Stage10 service slack, rounded up to 1 mm."""
    mh=2*val(P,'gh_mated_height_mm');t=val(P,'release_travel_mm');L0=release_shape(geo,link,spec,P,0,(0,0))['length_mm']+mh
    extra=max(release_shape(geo,link,spec,P,t,w)['length_mm']+mh-L0 for w in ((0,1),(1,0),(1,1)))
    return {'minimum_installed_mm':L0,'release_extra_mm':extra,'design_length_mm':math.ceil(L0+extra+val(P,'service_slack_mm'))}


def constant_length(geo,link,spec,P,Ld,t,which):
    """Route that keeps the design length: the hook follows the withdrawn middle housing (Stage31 rule) and the local slack loop (waypoints 0-1, both legs vertical) rises or falls by half the length difference."""
    rad=val(P,'design_bend_radius_mm');lead=val(P,'straight_lead_mm');mh=2*val(P,'gh_mated_height_mm');dl,dm=which
    w=[list(map(float,x)) for x in spec['waypoints_mm']];need(w[0][2]==w[1][2] and w[1][:2]==w[2][:2],'local slack loop has two vertical legs '+link)
    g=geo[ENDS[link][1]]
    if dm:
        e=g['exit_mm'][2]+g['axis']*t;move=max(0.0,g['axis']*(e+g['axis']*(lead+rad)-w[-1][2]))
        for i in (-1,-2):w[i][2]+=g['axis']*move
    gl=geo[ENDS[link][0]];zmin=gl['exit_mm'][2]+gl['axis']*t*dl+lead+rad;z0=w[0][2];pre=max(0.0,zmin-z0);w[0][2]+=pre;w[1][2]+=pre
    base=s31.fillet_route(s31.route_vertices(geo,link,{'waypoints_mm':w},(t*dl,t*dm)),rad,(lead,lead))['length_mm']+mh
    d=(Ld-base)/2;w[0][2]+=d;w[1][2]+=d;h=w[0][2]-z0;short=w[0][2]<zmin-1e-9
    r=None if short else s31.fillet_route(s31.route_vertices(geo,link,{'waypoints_mm':w},(t*dl,t*dm)),rad,(lead,lead))
    if r is not None:need(abs(r['length_mm']+mh-Ld)<1e-6,'constant-length release keeps the design length '+link)
    return {'route':r,'loop_top_z_mm':r6(w[0][2]),'loop_rise_mm':r6(h),'slack_short':short,'loop_min_z_mm':r6(zmin)}


def middle_side_length(route,x_guide):
    """Arc length of the route beyond the guide centre (x > x_guide); its change between states is the slide through the closed guide."""
    d=route['dense'];return sum(s31.norm(s31.sub(b,a)) for a,b in zip(d,d[1:]) if a[0]>x_guide and b[0]>x_guide)


def solid_gaps(smp,solids):
    out={}
    for s in solids:
        lo=list(s['box_mm'][:2])+[s['z_mm'][0]];hi=list(s['box_mm'][2:])+[s['z_mm'][1]]
        out[s['id']]=min(s31.box_distance(p,lo,hi)-r for p,r in smp)-STEP/2
    return out


def solids_hit(smp,solids,margin):
    ext={s['id']:s['extent'] for s in solids}
    return [{'solid':k,'extent':ext[k],'clearance_mm':r6(d)} for k,d in solid_gaps(smp,solids).items() if d<margin]


def states(cand,data,mech,P):
    """Installed at design length, then every release case at constant length; the guide slide equals the change of the local loop."""
    m=val(P,'placement_margin_mm');scen=data['input']['neighbour_scenarios'];p31=data['s31']['input']['parameters'];out={}
    for link in LINKS:
        spec=cand['spec']['routes'][link];bund=s31.bundle(p31,link,'ROUND_BUNDLE');rb=bund['round_radius_mm'];Ld=cand['lengths'][link]['design_length_mm']
        inst=cand['installed'][link];rows=[]
        for t in val(P,'release_travel_sensitivity_mm'):
            for name,which in (('middle',(0,1)),('local',(1,0)),('both',(1,1))):
                c=constant_length(cand['geo'],link,spec,P,Ld,t,which);ref=release_shape(cand['geo'],link,spec,P,t,which)['length_mm']-cand['lengths'][link]['minimum_installed_mm']+2*val(P,'gh_mated_height_mm')
                xg=next((g['centre_mm'][0] for g in cand['guides'] if g['link']==link),245.0)
                row={'travel_mm':t,'withdrawn':name,'stage31_rule_extra_mm':r6(ref),'loop_top_z_mm':c['loop_top_z_mm'],'loop_min_z_mm':c['loop_min_z_mm'],'slack_short':c['slack_short'],
                    'slide_through_guide_mm':r6(middle_side_length(c['route'],xg)-middle_side_length(inst['route'],xg)) if c['route'] is not None else None}
                if c['route'] is not None:
                    r=c['route'];smp=s31.samples(r,bund);known,depth=s31.evaluate_route(smp,cand['obs'],m,link);low=min(p[2] for p in r['dense'])
                    row.update({'lowest_centreline_z_mm':r6(low),'envelope_bottom_z_mm':r6(low-rb),'keep_outs_below_margin':sorted(k for k,v in known.items() if v<m),
                        'foreign_depth_bounds':{k:{'max_foreign_top_z_mm':v['max_foreign_top_z_mm'],'max_rear_side_height_mm':v['max_rear_side_height_mm']} for k,v in depth.items()},
                        'neighbour_conflicts':{sc['id']:solids_hit(smp,sc['solids'],m) for sc in scen},
                        'neighbour_min_gap_mm':{sc['id']:r6(min(solid_gaps(smp,sc['solids']).values())) for sc in scen}})
                rows.append(row)
        mid=[x for x in rows if x['withdrawn']=='middle' and not x['slack_short']]
        out[link]={'design_length_mm':Ld,'minimum_installed_mm':r6(cand['lengths'][link]['minimum_installed_mm']),'installed_loop_top_z_mm':inst['loop_top_z_mm'],'release':rows,
            'max_travel_clear_of':{sc['id']:max([x['travel_mm'] for x in mid if not x['neighbour_conflicts'][sc['id']]],default=None) for sc in scen},
            'release_15mm_known_clear':all(not x['slack_short'] and not x['keep_outs_below_margin'] for x in rows if x['travel_mm']==15)}
    env=s31.core_envelope(mech);core=[]
    for link in LINKS:
        smp=s31.samples(cand['routes'][link],s31.bundle(p31,link,'ROUND_BUNDLE'))
        core.append(min(s31.box_distance(p,env['lo'],env['hi'])-r for p,r in smp)-STEP/2)
    for gg in cand['guides']:
        for b in gg['bodies']:core.append(s31.box_distance_boxes(b['lo'],b['hi'],env['lo'],env['hi']))
    out['core_40mm']={'envelope':env,'min_clearance_mm':r6(min(core)),'clear':min(core)>=m,'procedure':'K-PWR first, then 40 mm along +z; J-SIG/J-PWR and R1/R2 are not touched'}
    return out


def latch_access(cand,data,P,smp):
    """Free distance from each long face of the moved middle housings to rigid obstacles (incl. all guides) and, separately, to cable envelopes; and the panel-side tool corridor below each housing."""
    m=val(P,'placement_margin_mm');tool=val(P,'flat_tool_mm');zpanel=val(P,'panel_rear_z_mm');out={}
    for link in LINKS:
        g=cand['geo'][ENDS[link][1]];bx=g['box_mm'];z0,z1=g['exit_mm'][2],g['face_z_mm'];axis=0 if g['pin_row_axis']=='y' else 1;other=1-axis;faces={}
        for sgn in (-1,1):
            face=[bx[0],bx[1],bx[2],bx[3]][axis+(2 if sgn>0 else 0)]
            best=None
            for o in cand['obs']:
                if (o['link']==link and not o['id'].startswith('guide:')) or o['kind']=='unknown_depth':continue
                lo,hi=o['lo'],o['hi']
                if not(lo[other]<bx[other+2] and hi[other]>bx[other] and lo[2]<z1 and hi[2]>z0):continue
                d=(lo[axis]-face) if sgn>0 else (face-hi[axis])
                if d>=-1e-9 and (best is None or d<best[0]):best=(d,o['id'])
            cab=None
            for l2 in LINKS:
                for p,r in smp[l2]:
                    if bx[0]-1e-9<=p[0]<=bx[2]+1e-9 and bx[1]-1e-9<=p[1]<=bx[3]+1e-9:continue
                    if not(bx[other]-r<p[other]<bx[other+2]+r and z0-r<p[2]<z1+r):continue
                    d=((p[axis]-r)-face) if sgn>0 else (face-(p[axis]+r))
                    if d>=-1e-9 and (cab is None or d<cab[0]):cab=(d,l2)
            fd=[o['id'].split(':',1)[1] for o in cand['obs'] if o['kind']=='unknown_depth' and 0<=((o['lo'][axis]-face) if sgn>0 else (face-o['hi'][axis]))<10 and o['lo'][other]<bx[other+2] and o['hi'][other]>bx[other]]
            free=min([x[0] for x in (best,cab) if x],default=None)
            faces[('+' if sgn>0 else '-')+'xy'[axis]]={'free_to_rigid_mm':r6(best[0]) if best else None,'nearest_rigid':best[1] if best else None,
                'free_to_cable_mm':r6(cab[0]) if cab else None,'nearest_cable':cab[1] if cab else None,'foreign_depth_within_10mm':sorted(fd),
                'flat_tool_fits':free is None or free>=tool[0]+m}
        col_lo=[bx[0],bx[1],zpanel];col_hi=[bx[2],bx[3],z0];hits=[o['id'] for o in cand['obs'] if o['link']!=link and o['kind']!='unknown_depth' and all(o['lo'][i]<col_hi[i] and o['hi'][i]>col_lo[i] for i in range(3))]
        fdc=[o['id'].split(':',1)[1] for o in cand['obs'] if o['kind']=='unknown_depth' and o['lo'][0]<col_hi[0] and o['hi'][0]>col_lo[0] and o['lo'][1]<col_hi[1] and o['hi'][1]>col_lo[1]]
        out[link]={'housing_box_mm':bx,'housing_z_mm':[z0,z1],'latch_faces':faces,'latch_side':'UNCONFIRMED (both long faces evaluated)',
            'panel_side_corridor':{'box_mm':[bx[0],bx[1],bx[2],bx[3]],'z_mm':[zpanel,z0],'known_hits':sorted(hits),'foreign_xy_overlaps':sorted(fdc),
                'crosses':f'the neighbouring volume z {zpanel:g}-34, whose boards and parts are not designed (UNKNOWN)'},
            'straight_bundle_below_housing_mm':val(P,'straight_lead_mm'),'grip_length_needed_mm':None,
            'finger_operation':'NOT_DETERMINED; a CAD gap is not finger operability (M32-03)'}
    for gg in cand['guides']:
        tab=next(b for b in gg['bodies'] if b['id'].endswith(':latch'))
        lo=[tab['lo'][0],tab['lo'][1],val(P,'panel_rear_z_mm')];hi=[tab['hi'][0],tab['hi'][1],tab['lo'][2]]
        hits=[o['id'] for o in cand['obs'] if o['kind']!='unknown_depth' and not o['id'].startswith('guide:'+gg['id']) and all(o['lo'][i]<hi[i] and o['hi'][i]>lo[i] for i in range(3))]
        fd=[o['id'].split(':',1)[1] for o in cand['obs'] if o['kind']=='unknown_depth' and o['lo'][0]<hi[0] and o['hi'][0]>lo[0] and o['lo'][1]<hi[1] and o['hi'][1]>lo[1]]
        out['strap:'+gg['id']]={'tab_box_mm':tab['lo'][:2]+tab['hi'][:2],'panel_side_corridor_z_mm':[lo[2],r6(hi[2])],'known_hits':sorted(hits),'foreign_xy_overlaps':sorted(fd),
            'front_access':'BLOCKED' if hits or fd else 'CLEAR_OF_KNOWN','reopen':'with A01-middle removed (+z), rail top exposed',
            'note':'opened only for harness replacement; normal middle unmating slides the bundle through the closed guide'}
    return out


# ---------- analyses ----------
def bend_analysis(cand,data,P):
    """Route bend radius against the maker rule for each identified wire (inner conductor of a round bundle), and the geometric lower bound it forces at the middle hook."""
    k=val(P,'wire_bend_rule_x_od');lead=val(P,'straight_lead_mm');jmin,jmax=val(P,'wire_od_min_mm'),val(P,'wire_od_max_mm');rows=[]
    used=val(P,'design_bend_radius_mm')
    for w in data['input']['wire_candidates']:
        lo,hi=w['od_nominal_mm']-w['od_tolerance_mm'],w['od_nominal_mm']+w['od_tolerance_mm'];req={}
        for link in LINKS:
            rb=hi*val(P,'round_bundle_factor')[link]/2;req[link]=r6(w['bend_rule_x_od']*hi+rb-hi/2)
        rows.append({'mpn':w['mpn'],'awg':w['awg'],'od_range_mm':[r6(lo),r6(hi)],'inside_jst_od_window':lo>=jmin-1e-9 and hi<=jmax+1e-9,'voltage_V':w['voltage_V'],'temperature_max_C':w['temperature_max_C'],
            'meets_gh_ratings':w['voltage_V']>=val(P,'gh_voltage_rating_V') and w['temperature_max_C']>=val(P,'gh_temperature_max_C'),
            'required_centreline_radius_mm':req,'route_radius_mm':used,'route_meets_maker_rule':all(used>=req[l]-1e-9 for l in LINKS),'sources':w['sources']})
    generic={l:r6(k*jmax+jmax*val(P,'round_bundle_factor')[l]/2-jmax/2) for l in LINKS}
    hook=[];p31=data['s31']['input']['parameters'];top=max(val(P,'bend_radius_sensitivity_mm'))
    mr={l:s31.max_radius(cand['geo'],l,cand['spec']['routes'][l],cand['obs'],p31,s31.bundle(p31,l,'ROUND_BUNDLE'),limit=top) for l in LINKS}
    for R in val(P,'bend_radius_sensitivity_mm'):
        for link in LINKS:
            g=cand['geo'][ENDS[link][1]];rb=bundle_r(P,link);ez=g['exit_mm'][2];low=ez-lead-R
            hook.append({'link':link,'radius_mm':R,'installed_lowest_centreline_z_max_mm':r6(low),'installed_envelope_bottom_z_max_mm':r6(low-rb),
                'release_15mm_envelope_bottom_z_max_mm':r6(low-val(P,'release_travel_mm')-rb),'route_admits':mr[link] is not None and mr[link]>=R-1e-9})
    return {'route_radius_mm':used,'maker_rule':f'{k} x wire OD (S-AW-1852/1853/2843-7); applied to the inner conductor of the round bundle','wire_candidates':rows,
        'required_centreline_radius_at_jst_max_od_mm':generic,'max_uniform_radius_mm':mr,'any_identified_wire_met':any(r['route_meets_maker_rule'] and r['inside_jst_od_window'] and r['meets_gh_ratings'] for r in rows),
        'hook_lower_bound':hook,'lower_bound_rule':'a route of bend radius >= R that leaves the middle housing along -z after the straight lead must fall at least R before it can turn back up (z_low <= exit z - lead - R)'}


def section(width,h,grooves):
    """Second moments and extreme-fibre distances of the net rail section (rectangle minus flank grooves), by 0.01 mm strips."""
    n=int(round(h/0.01));dz=h/n;A=0.0;Sz=0.0;strips=[]
    for i in range(n):
        z=(i+0.5)*dz;w=width-sum(2*g['depth'] for g in grooves if g['z'][0]<=z<=g['z'][1]);strips.append((z,w));A+=w*dz;Sz+=w*dz*z
    zc=Sz/A;Iv=sum(w*dz*(z-zc)**2+w*dz**3/12 for z,w in strips);Il=sum(dz*w**3/12 for z,w in strips)
    return {'area_mm2':A,'I_vertical_mm4':Iv,'I_lateral_mm4':Il,'c_vertical_mm':max(zc,h-zc),'c_lateral_mm':width/2,'centroid_from_bottom_mm':zc}


def strength(cand,data,mech,P):
    """Notched rail:middle:0 as a cantilever from the top crossmember (y 142) with a free end at y 274; conservative Inglis Kt; sensitivity over load and corner radius."""
    f=mech['carrier_frames']['middle'];z0,z1=f['z_mm'];rail=f['rails_boxes_mm'][0];width=rail[2]-rail[0];E=val(P,'carrier_E_MPa');Sy=val(P,'carrier_proof_MPa');SF=val(P,'strength_safety_factor')
    need([rail[1],rail[3]]==[RAIL_ROOT_Y,RAIL_TIP_Y],'rail:middle:0 spans y 142-274 (Stage10)')
    leg=data['input']['retention_rules']['snap_leg_mm'];full=section(width,z1-z0,[]);notches=[]
    for nt in cand['reliefs']:
        h=nt['relieved_top_z_mm']-z0;depth=z1-nt['relieved_top_z_mm']
        grooves=[] if not cand['guides'] else [{'depth':leg['flank_groove_depth'],'z':[h-leg['depth_below_floor']+leg['barb'],h-leg['depth_below_floor']+leg['barb']+leg['flank_groove_height']]}]
        sec=section(width,h,grooves);lever=RAIL_TIP_Y-nt['y_mm'][0];rows=[]
        for rho in val(P,'notch_corner_radius_sensitivity_mm'):
            kt=1+2*math.sqrt(depth/rho)
            for load in val(P,'load_sensitivity_N'):
                for d,I,c in (('vertical',sec['I_vertical_mm4'],sec['c_vertical_mm']),('lateral',sec['I_lateral_mm4'],sec['c_lateral_mm'])):
                    sn=load*lever*c/I;rows.append({'corner_radius_mm':rho,'load_N':load,'direction':d,'Kt_inglis':r6(kt),'nominal_MPa':r6(sn),'peak_MPa':r6(kt*sn),'allowable_MPa':r6(Sy/SF),'meets':kt*sn<=Sy/SF})
        rho=val(P,'notch_corner_radius_mm');kt=1+2*math.sqrt(depth/rho)
        allow={d:r6(Sy/SF*I/(c*kt*lever)) for d,I,c in (('vertical',sec['I_vertical_mm4'],sec['c_vertical_mm']),('lateral',sec['I_lateral_mm4'],sec['c_lateral_mm']))}
        notches.append({'id':nt['id'],'y_mm':nt['y_mm'],'depth_mm':r6(depth),'remaining_mm':r6(h),'net_section':{k:r6(v) for k,v in sec.items()},'lever_mm':r6(lever),
            'Kt_inglis_at_design_radius':r6(kt),'allowable_tip_load_N':allow,'grid':rows})
    P0=val(P,'planning_load_N');need(P0==f['planning_model']['load_N'],'planning load equals the Stage10 carrier planning load')
    def tip(withn):
        n=int((RAIL_TIP_Y-RAIL_ROOT_Y)/0.05);dy=(RAIL_TIP_Y-RAIL_ROOT_Y)/n;dd=0.0
        for i in range(n):
            y=RAIL_ROOT_Y+(i+0.5)*dy;I=full['I_vertical_mm4']
            for nt in (cand['reliefs'] if withn else []):
                if nt['y_mm'][0]<=y<=nt['y_mm'][1]:I=next(n['net_section']['I_vertical_mm4'] for n in notches if n['id']==nt['id'])
            dd+=P0*(RAIL_TIP_Y-y)**2/(E*I)*dy
        return dd
    worst=min(min(a for a in n['allowable_tip_load_N'].values()) for n in notches) if notches else None
    return {'model':'cantilever rail:middle:0 fixed at the top crossmember (y 142, joint stiffness not evaluated), free end y 274, tip load P; moment at the notch edge nearest the root',
        'material':{'name':val(P,'carrier_material'),'E_MPa':E,'proof_min_MPa':Sy,'safety_factor':SF,'manufacture':'machined; notch internal corners end-milled'},
        'Kt':'Inglis upper estimate 1 + 2 sqrt(depth / corner radius); conservative for a flat-bottomed groove, not a chart or FEA value',
        'full_section':{k:r6(v) for k,v in full.items()},'notches':notches,'planning_load_N':P0,
        'tip_deflection_mm':{'without_notches':r6(tip(False)),'with_notches':r6(tip(True))},
        'smallest_allowable_tip_load_N':r6(worst) if worst is not None else None,'meets_at_planning_load':worst is None or worst>=P0,
        'not_covered':['joint to the crossmember','fatigue and vibration','assembly or service impact loads (unknown)','DIN insertion load path (enters the right rail and tabs, not beyond the notches)','certified machined-part material'],
        'status':'CALCULATED_CONDITIONALLY; not a physical strength result (M32-06)'}


def guide_foreign_bounds(cand,m):
    """Retention bodies over a foreign XY column: the highest top that foreign part may reach."""
    out=[]
    for gg in cand['guides']:
        for b in gg['bodies']:
            for o in cand['obs']:
                if o['kind']!='unknown_depth':continue
                if not(o['lo'][0]<b['hi'][0]+m and o['hi'][0]>b['lo'][0]-m and o['lo'][1]<b['hi'][1]+m and o['hi'][1]>b['lo'][1]-m):continue
                top=b['lo'][2]-m;out.append({'body':b['id'],'foreign':o['id'].split(':',1)[1],'max_foreign_top_z_mm':r6(top),'max_rear_side_height_mm':r6(top-o['lo'][2])})
    return sorted(out,key=lambda x:(x['max_foreign_top_z_mm'],x['body']))


def sweeps(cand,P,T):
    m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');scr=s31.sweep_screen(cand['geo'],cand['obs'],m);rows={}
    known=T['pcb_hole_position_mm']['value']+T['mount_hole_float_mm']['value']+T['carrier_face_mm']['value']
    for ref,s in scr.items():
        if not s['moved']:continue
        gaps=[x for x in s['nearest_gaps_mm'] if x['id'].startswith(('foreign','crossmember','rail','DIN','board'))];tight=min(gaps,key=lambda x:x['gap_mm']) if gaps else None
        foreign=tight is not None and tight['id'].startswith('foreign')
        rows[ref]={'known_overlaps':s['known_overlaps'],'foreign_xy_overlaps':[x['ref'] for x in s['foreign_xy_overlaps']],'tightest':tight,
            'known_tolerance_mm':r6(known),'robust_spare_known_only_mm':r6(tight['gap_mm']-m-known) if tight else None,
            'allowed_panel_registration_mm':r6(tight['gap_mm']-m-known-k4) if tight and foreign else None,
            'registration_class':'UNCONFIRMED (panel_to_carrier_registration_mm)' if foreign else 'not in this chain'}
    return rows


# ---------- evaluation ----------
def evaluate(cid,c,data,mech,P,T):
    cand=build_candidate(cid,c,data,mech,P,T);p31=data['s31']['input']['parameters'];m=val(P,'placement_margin_mm');rules=data['input']['tolerance_rules']
    smp={l:s31.samples(cand['routes'][l],s31.bundle(p31,l,'ROUND_BUNDLE')) for l in LINKS}
    static={}
    for l in LINKS:
        known,depth=s31.evaluate_route(smp[l],cand['obs'],m,l)
        static[l]={'installed_length_mm':r6(cand['routes'][l]['length_mm']+2*val(P,'gh_mated_height_mm')),'installed_state':'at design length, slack stored in the local loop (top z '+str(cand['installed'][l]['loop_top_z_mm'])+')',
            'bends':len(cand['routes'][l]['bends']),'min_surface_clearance_mm':min(known.values()) if known else None,
            'nearest':list(known.items())[:6],'foreign_depth_bounds':depth}
    gap,_=s31.cable_gap(smp['J-SIG'],smp['J-PWR'])
    rob=robust_rows(cand,smp,P,T,rules)
    ccg={'gap_mm':gap,'tolerance_mm':r6(2*T['carrier_face_mm']['value']),'robust_spare_mm':r6(gap-m-2*T['carrier_face_mm']['value'])}
    st=states(cand,data,mech,P);acc=latch_access(cand,data,P,smp);sw=sweeps(cand,P,T);bend=bend_analysis(cand,data,P);stren=strength(cand,data,mech,P)
    allow=p31['foreign_depth_cap_reference_mm']['value']-p31['foreign_pcb_rear_z_mm']['value']
    gfb=guide_foreign_bounds(cand,m)
    relb=[b['max_rear_side_height_mm'] for l in LINKS for x in st[l]['release'] if x['travel_mm']==val(P,'release_travel_mm') for b in x.get('foreign_depth_bounds',{}).values()]
    worst=min([b['max_rear_side_height_mm'] for l in LINKS for b in static[l]['foreign_depth_bounds'].values()]+[b['max_rear_side_height_mm'] for b in gfb]+relb,default=None)
    bows=bow_sensitivity(cand,smp,P,T,rules,data['input']['bow_cases'],mech)
    crit={'S1_static_clear':all(static[l]['min_surface_clearance_mm'] is None or static[l]['min_surface_clearance_mm']>=m for l in LINKS) and gap>=m,
        'S2_robust_K4':all(r['meets_K4'] for r in rob) and ccg['robust_spare_mm']>=val(P,'robust_spare_mm')-1e-12,
        'S3_retention_modelled':bool(cand['guides']),
        'S4_sweeps_clear':all(not v['known_overlaps'] and not v['foreign_xy_overlaps'] and (v['robust_spare_known_only_mm'] is None or v['robust_spare_known_only_mm']>=val(P,'robust_spare_mm')-1e-12) for v in sw.values()),
        'S5_core_clear':st['core_40mm']['clear'],
        'S6_strength_planning_load':stren['meets_at_planning_load'],
        'S7_release_15mm_known_clear':all(st[l]['release_15mm_known_clear'] for l in LINKS),
        'S8_foreign_allowance':worst is None or worst>=allow-1e-9,
        'S9_bend_maker_rule':bend['any_identified_wire_met']}
    open_={'bend_radius':'maker rule not met by the 5 mm route for any identified wire' if not bend['any_identified_wire_met'] else 'met',
        'release_dip':{l:st[l]['max_travel_clear_of'] for l in LINKS},'latch_side':'UNCONFIRMED','finger_operation':'NOT_DETERMINED','foreign_volume':'UNKNOWN (no board outline)'}
    failed=[k for k,v in crit.items() if not v]
    status='CONDITIONAL_WORKING_DESIGN' if not failed else 'CONDITIONAL_PENDING_WIRE_SELECTION' if failed==['S9_bend_maker_rule'] else 'NOT_ROBUST_UNDER_STAGE32_CHECKS'
    return cand,{'id':cid,'title':c.get('title',c.get('role')),'role':c.get('role'),'header_moves':cand['moved'],'notches':cand['reliefs'],'guides':[{k:v for k,v in g.items() if k!='bodies'} for g in cand['guides']],
        'static':static,'guide_foreign_bounds':gfb,'cable_to_cable':ccg,'robust':rob,'tightest_robust':rob[0] if rob else None,'sweeps':sw,'states':st,'access':acc,'bend':bend,'strength':stren,
        'criteria':crit,'failed':failed,'bow_sensitivity':bows,'open_conditions':open_,'status':status,'physical':'NOT_RUN'},smp


def bow_sensitivity(cand,smp,P,T,rules,cases,mech):
    out=[];x0,y0,x1,y1=mech['boards']['A01-middle']['outline_mm']
    for c in cases:
        if c.get('uniform_of_outline_diagonal'):c=dict(c,uniform_mm=r6(T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)))
        rows=robust_rows(cand,smp,P,T,rules,c);t=rows[0]
        out.append({'case':c['id'],'note':c['note'],'bow_mm':c.get('uniform_mm'),'tightest':{k:t[k] for k in ('link','obstacle','robust_spare_mm')},'meets_K4':all(r['meets_K4'] for r in rows)})
    return out


MIDDLE_SIDE_X=249.0  # beyond rail:middle:0 (x 242-248) and the 1 mm guide overhang: the middle-end hook region
CARRIER_BOTTOM_Z=34.0  # Stage10 middle carrier z 34-46; below it the neighbouring volume is undesigned


def middle_envelopes(cand,P,link):
    """(point, radius) samples of the middle-end hook for the installed state and every release case at constant length."""
    rb=bundle_r(P,link);Ld=cand['lengths'][link]['design_length_mm'];sp=cand['spec']['routes'][link];out=[]
    routes=[cand['routes'][link]]
    for t in val(P,'release_travel_sensitivity_mm'):
        for w in ((0,1),(1,1)):
            c=constant_length(cand['geo'],link,sp,P,Ld,t,w)
            if c['route'] is not None:routes.append(c['route'])
    for r in routes:out+=[(p,rb) for p in r['dense'] if p[0]>MIDDLE_SIDE_X and p[2]-rb<CARRIER_BOTTOM_Z]
    return out


def reservations(cand,res,P):
    """Dimensioned volumes this design needs from the undesigned neighbouring volume: the union of the installed and release hook envelopes and the housing sweep, plus the margin. Proposals for the owner, not adopted."""
    m=val(P,'placement_margin_mm');out=[]
    for link in LINKS:
        ref=ENDS[link][1];g=cand['geo'][ref];sw=g['sweep']['box_mm'];env=middle_envelopes(cand,P,link)
        lo=[min([p[0]-r for p,r in env]+[sw[0]])-m,min([p[1]-r for p,r in env]+[sw[1]])-m];hi=[max([p[0]+r for p,r in env]+[sw[2]])+m,max([p[1]+r for p,r in env]+[sw[3]])+m]
        zl=min(p[2]-r for p,r in env)-m-STEP/2
        out.append({'id':'RV-DIP-'+link,'for':ref+' hook below the carrier bottom, installed and released (2.45-15 mm, constant length), and the housing sweep','box_mm':[r6(lo[0]),r6(lo[1]),r6(hi[0]),r6(hi[1])],'z_mm':[r6(zl),48.4],
            'reason':f'the hook envelope reaches z {zl+m+STEP/2:.2f} at the 15 mm Stage10 travel; installed it already reaches z {min(p[2] for p in cand["routes"][link]["dense"])-bundle_r(P,link):.2f}, below the carrier bottom z 34. No neighbouring board, part or wiring may occupy this volume',
            'status':'PROPOSAL_REQUIRES_OWNER_DECISION'})
        out.append({'id':'RV-ACCESS-'+link,'for':ref+' latch press and pull from the panel side','box_mm':[r6(sw[0]-m),r6(sw[1]-m),r6(sw[2]+m),r6(sw[3]+m)],'z_mm':[val(P,'panel_rear_z_mm'),48.4],
            'reason':'only needed if the middle connectors are serviced with the neighbouring front boards in place; otherwise those boards must come out with the front panel','status':'PROPOSAL_REQUIRES_OWNER_DECISION'})
    seen=set()
    for g in res['guide_foreign_bounds']:
        key=(g['body'].split(':')[1],g['foreign'])
        if key in seen:continue
        seen.add(key);out.append({'id':'RV-GUIDE-'+key[0]+'-'+key[1],'for':g['body'],'foreign_part':g['foreign'],'max_top_z_mm':g['max_foreign_top_z_mm'],'max_rear_side_height_mm':g['max_rear_side_height_mm'],'status':'REQUIREMENT_ON_FOREIGN_DESIGN'})
    for link in LINKS:
        for ref,b in res['static'][link]['foreign_depth_bounds'].items():
            out.append({'id':'RV-RUN-'+ref,'for':link+' run under A01-middle','foreign_part':ref,'max_top_z_mm':b['max_foreign_top_z_mm'],'max_rear_side_height_mm':b['max_rear_side_height_mm'],'status':'REQUIREMENT_ON_FOREIGN_DESIGN'})
    return out


def toggle_rear_bound(P):
    """Rear-most z of a panel-mounted 2MS3 from the -5 drawing: front nut and washer at their thinnest (-0.25) on the panel front, every body dimension at +0.25."""
    t=val(P,'toggle_body_and_terminal_mm');tol=t['tolerance_2_decimal']
    tip=val(P,'panel_front_z_mm')-(t['nut']-tol)-(t['washer']-tol);shoulder=tip+t['bushing']+tol
    return {'panel_front_z_mm':val(P,'panel_front_z_mm'),'bushing_tip_z_max_mm':r6(tip),'shoulder_z_max_mm':r6(shoulder),'terminal_tip_z_max_mm':r6(shoulder+t['body']+tol+t['terminal_beyond_body']+tol),
        'conditions':['exact MPN gate OPEN (-5 drawing vs unsuffixed lock MPN)','panel-bushing mounting with the front nut fully engaged','no foreign wiring, PCB or connector behind the terminals (UNKNOWN)'],'class':'DESIGN_ASSUMPTION derived from S-DW2-2MS3'}


def build(data,preserve=True):
    validate_inputs(data);s29,cmap,_=s30.stage29_current();mech=s29['mech'];data=dict(data,lock=data['s31']['lock'])
    P=data['input']['parameters'];T=data['input']['tolerances'];b31=next(c for c in data['s31']['input']['candidates'] if c['id']=='B')
    cands={'B31':dict(b31,role='COMPARISON (Stage31 B as committed)'),'B32':data['input']['candidates']['B32']}
    res={};built={};smp={}
    for cid,c in cands.items():built[cid],res[cid],smp[cid]=evaluate(cid,c,data,mech,P,T)
    need(res['B32']['status'] in ('CONDITIONAL_WORKING_DESIGN','CONDITIONAL_PENDING_WIRE_SELECTION'),'B32 must meet S1-S8 under the stated conditions: '+', '.join(res['B32']['failed']))
    need(res['B31']['status']=='NOT_ROBUST_UNDER_STAGE32_CHECKS','B31 is expected to fail the Stage32 checks (no retention, K4 under tolerances)')
    rv=reservations(built['B32'],res['B32'],P);tog=toggle_rear_bound(P)
    nb={'unknown_regions':[{'id':'U-FRONT','box_mm':[195,94,318,300],'z_mm':[val(P,'panel_rear_z_mm'),34.0],'basis':'below the A01 carriers no foreign board, plane, outline or part height is designed; z 20-21.6 is only a code default (R-ASSEMBLY-DEFAULT)','status':'UNKNOWN_NOT_FREE'},
            {'id':'U-FOREIGN-DEPTH','basis':'per-part XY columns of A02-A06 / E2-E5 hardware above z 21.6, depth unknown (Stage30/31 foreign-depth)','status':'UNKNOWN_NOT_FREE'}],
        'scenarios':data['input']['neighbour_scenarios'],'reservations':rv,'toggle_rear_bound':tog,
        'toggle_vs_requirement':{k:{'required_max_top_z_mm':v['max_foreign_top_z_mm'],'drawing_bound_z_mm':tog['terminal_tip_z_max_mm'],'satisfied_if_conditions_hold':tog['terminal_tip_z_max_mm']<=v['max_foreign_top_z_mm']} for k,v in res['B32']['static']['J-PWR']['foreign_depth_bounds'].items()},
        'not_extended':'only the volume A01 J-SIG/J-PWR and their service motions cross is modelled; no other instrument is designed here'}
    model={'status':'DESIGN_STUDY_ONLY','approval':data['approval'],'parameters':P,'tolerances':T,'retention_rules':data['input']['retention_rules'],
        'candidates':{cid:{'header_moves':res[cid]['header_moves'],'notches':res[cid]['notches'],'guides':res[cid]['guides'],
            'routes':{l:{'vertices_mm':[p6(x) for x in s31.route_vertices(built[cid]['geo'],l,cands[cid]['routes'][l])],'bends':built[cid]['routes'][l]['bends'],'legs_mm':built[cid]['routes'][l]['legs_mm'],
                'straight_from_exit_mm':built[cid]['routes'][l]['straight_from_exit_mm']} for l in LINKS}} for cid in cands}}
    env={'status':'DESIGN_STUDY_ONLY','states':{cid:dict(res[cid]['states'],access=res[cid]['access']) for cid in cands},
        'note':'installed at design length with the slack in the local loop; release cases keep that length (the hook follows the Stage31 bend rule, the loop gives up the difference); the neighbouring volume is not free space'}
    ana={'status':'DESIGN_STUDY_ONLY','candidates':{cid:{k:res[cid][k] for k in ('static','guide_foreign_bounds','cable_to_cable','robust','bow_sensitivity','sweeps','bend','strength','criteria','failed','open_conditions','status')} for cid in cands}}
    lengths={l:{'minimum_installed_mm':r6(built['B32']['lengths'][l]['minimum_installed_mm']),'release_extra_15mm_mm':r6(built['B32']['lengths'][l]['release_extra_mm']),
        'design_length_proposal_mm':built['B32']['lengths'][l]['design_length_mm'],'installed_loop_top_z_mm':built['B32']['installed'][l]['loop_top_z_mm']} for l in LINKS}
    report={'status':'DESIGN_STUDY_ONLY','recommendation':{'id':'B32','status':res['B32']['status'],'adopted':False},'comparison':{cid:{'status':res[cid]['status'],'failed':res[cid]['failed'],
        'tightest_robust':{k:res[cid]['tightest_robust'][k] for k in ('link','obstacle','sampled_clearance_mm','robust_spare_mm')} if res[cid]['tightest_robust'] else None} for cid in cands},
        'design_lengths':lengths,'open_conditions':res['B32']['open_conditions'],'reservations':[r['id'] for r in rv if r['status']=='PROPOSAL_REQUIRES_OWNER_DECISION'],
        'measurements':[{'id':m_['id'],'item':m_['item'],'status':'NOT_RUN','value':None} for m_ in MEASUREMENTS],
        'decision_status':{'route':'WORKING_DESIGN_CONDITIONAL; not adopted','rail_change':'PROPOSAL_NOT_ADOPTED','header_moves':'PROPOSAL_NOT_ADOPTED','retention':'PROPOSAL_NOT_ADOPTED','reservations':'PROPOSAL_REQUIRES_OWNER_DECISION',
            'cable_lengths':'DESIGN_LENGTH_PROPOSAL; not measured, not cut','strength':'CALCULATED_CONDITIONALLY','D02':'CONFLICT_REQUIRES_DECISION (unchanged)','M-01':'NOT_RUN','M-09':'NOT_RUN','M-12':'NOT_RUN'},
        'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('approval.json','design-input.json','sources.json','README.md')]+[ROOT/REL/'stage31'/n for n in ('design-input.json','approval.json')]+[ROOT/'design/grid/placements.lock.json']
    files+=[Path(__file__).with_name(n) for n in ('test_stage32_service_envelope.py','stage31_cable_entry_redesign.py','stage30_din_design_integration.py','stage28_din_harness.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return {'model':model,'envelope':env,'analysis':ana,'neighbour':nb,'report':report,'res':res,'built':built,'samples':smp,'mech':mech,'P':P}


MEASUREMENTS=[
    {'id':'M32-01','item':'Selected wire MPN with the maker minimum bend radius, OD and the dressed 4/7-conductor bundle diameter'},
    {'id':'M32-02','item':'GH unmating on a bench coupon: stroke to free, force, latch side, bundle grip length within 15 degrees'},
    {'id':'M32-03','item':'Latch press and pull at the moved middle headers with the real neighbours fitted (finger or tool)'},
    {'id':'M32-04','item':'A01-middle bow at the notch positions after assembly, spacer length, tab and notch-floor heights'},
    {'id':'M32-05','item':'Neighbouring board planes, outlines and rear-side heights in RV-DIP / RV-ACCESS / RV-RUN'},
    {'id':'M32-06','item':'Notched rail coupon: stiffness and strength at the notches with the real corner radius'},
    {'id':'M32-07','item':'R1/R2 saddle fit, strap latch, axial slide force, abrasion after repeated release (M-12)'},
    {'id':'M32-08','item':'Mock-up path and cut lengths for installed and release states (M-09)'},
    {'id':'M32-09','item':'Panel-to-carrier registration (sweep gap to SW1701 / J1610)'}]


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed: '+', '.join(sorted(set(changed)-MUTABLE)))
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage32/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


# ---------- rendering ----------
def f2(v):return '–' if v is None else f'{v:.2f}'
def esc(v):return html.escape(str(v),quote=True)
COLOR={'J-SIG':'#1f5fbf','J-PWR':'#c0392b'}


def render_md(b):
    rs=b['res'];rep=b['report'];nb=b['neighbour'];P=b['P'];B=rs['B32']
    L=['# Stage32 service envelope (generated)','','Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.','',
       '## Criteria per candidate','','| Candidate | S1 static | S2 robust K4 | S3 retention | S4 sweeps | S5 core | S6 strength | S7 release | S8 foreign allowance | S9 bend maker rule | Status |','|---|---|---|---|---|---|---|---|---|---|---|']
    yn=lambda x:'yes' if x else '**no**'
    for cid,r in rs.items():
        c=r['criteria'];L.append(f"| {cid} | {yn(c['S1_static_clear'])} | {yn(c['S2_robust_K4'])} | {yn(c['S3_retention_modelled'])} | {yn(c['S4_sweeps_clear'])} | {yn(c['S5_core_clear'])} | {yn(c['S6_strength_planning_load'])} | {yn(c['S7_release_15mm_known_clear'])} | {yn(c['S8_foreign_allowance'])} | {yn(c['S9_bend_maker_rule'])} | {r['status']} |")
    L+=['','## Tightest clearances after the tolerance stack','','| Candidate | Cable | Obstacle | Sampled (mm) | Margin | Tolerance WC / RSS (mm) | Robust spare (mm) | K4 0.15 |','|---|---|---|---|---|---|---|---|']
    for cid,r in rs.items():
        for x in r['robust'][:5]:L.append(f"| {cid} | {x['link']} | {x['obstacle']} | {f2(x['sampled_clearance_mm'])} | 0.50 | {f2(x['tolerance']['worst_case_mm'])} / {f2(x['tolerance']['rss_mm'])} | {f2(x['robust_spare_mm'])} | {yn(x['meets_K4'])} |")
    L+=['','## K4 sensitivity to the bow model (B32)','','| Bow case | Tightest | Robust spare (mm) | K4 |','|---|---|---|---|']
    for c in B['bow_sensitivity']:L.append(f"| {c['case']} ({c['note']}) | {c['tightest']['link']} {c['tightest']['obstacle']} | {f2(c['tightest']['robust_spare_mm'])} | {yn(c['meets_K4'])} |")
    L+=['','## B32 geometry','']
    for l in LINKS:
        lg=rep['design_lengths'][l];L.append(f"- {l}: design length {lg['design_length_proposal_mm']} mm (minimum installed {f2(lg['minimum_installed_mm'])} + 15 mm release extra {f2(lg['release_extra_15mm_mm'])} + 10 slack); installed with the slack in the local loop, top z {f2(lg['installed_loop_top_z_mm'])}")
    for h in B['header_moves']:L.append(f"- {h['ref']}: {h['from_origin_mm']} → {h['to_origin_mm']}, {h['rotation_deg']}°, sweep {h['sweep']['box_mm']} z {h['sweep']['z_mm']}")
    for g in B['guides']:
        n=g['notch'];s=g['saddle_mm'];st=g['strap_mm']
        L.append(f"- {g['id']} ({g['link']}): notch y {n['y_mm'][0]}–{n['y_mm'][1]}, floor z {n['relieved_top_z_mm']} ({r6(46-n['relieved_top_z_mm'])} mm deep); bundle centre {g['centre_mm']}, seat R {g['seat_radius_mm']} (radial clearance {g['radial_clearance_mm']}); saddle {s['length_x']} x {s['width_y']} mm, seat {s['seat_thickness']} mm, end flare R {s['end_flare_radius']}; strap {st['width']} x {st['thickness']} mm, top z {st['top_z']}, latch {st['latch_side']}")
    L+=['','## Release travel sensitivity (middle withdrawn)','','NB-CAN gap is to recorded solids only; the rear-side parts of those boards have no recorded height, so the gap is the height they may have.','','| Cable | Travel (mm) | Slide through guide (mm) | Local loop top z (mm) | Envelope bottom z (mm) | NB-278 plane | NB-CAN gap to recorded solids (mm) |','|---|---|---|---|---|---|---|']
    for l in LINKS:
        for x in B['states'][l]['release']:
            if x['withdrawn']!='middle':continue
            nc=x['neighbour_conflicts'];L.append(f"| {l} | {x['travel_mm']} | {f2(x['slide_through_guide_mm'])} | {f2(x['loop_top_z_mm'])} | {f2(x['envelope_bottom_z_mm'])} | {'conflict' if nc['NB-278'] else 'clear'} | {f2(x['neighbour_min_gap_mm']['NB-CAN'])} |")
    L+=['','## Bend radius against the maker rule','','| Wire | AWG | OD range (mm) | In JST window | Meets 50 V / 105 °C | Required centreline R J-SIG / J-PWR (mm) | Route R (mm) |','|---|---|---|---|---|---|---|']
    for w in B['bend']['wire_candidates']:L.append(f"| {w['mpn']} | {w['awg']} | {w['od_range_mm'][0]}–{w['od_range_mm'][1]} | {yn(w['inside_jst_od_window'])} | {yn(w['meets_gh_ratings'])} | {w['required_centreline_radius_mm']['J-SIG']} / {w['required_centreline_radius_mm']['J-PWR']} | {w['route_radius_mm']} |")
    L+=['','| Cable | R (mm) | Installed hook envelope bottom ≤ z (mm) | 15 mm release ≤ z (mm) | Route waypoints admit R |','|---|---|---|---|---|']
    for h in B['bend']['hook_lower_bound']:L.append(f"| {h['link']} | {h['radius_mm']} | {f2(h['installed_envelope_bottom_z_max_mm'])} | {f2(h['release_15mm_envelope_bottom_z_max_mm'])} | {yn(h['route_admits'])} |")
    s=B['strength'];L+=['','## Notched rail strength (conditional)','',f"Model: {s['model']}. Kt: {s['Kt']}.",'','| Notch | Depth (mm) | Remaining (mm) | Lever (mm) | Kt | Allowable tip load vertical / lateral (N) |','|---|---|---|---|---|---|']
    for n in s['notches']:L.append(f"| {n['id']} | {n['depth_mm']} | {n['remaining_mm']} | {n['lever_mm']} | {f2(n['Kt_inglis_at_design_radius'])} | {f2(n['allowable_tip_load_N']['vertical'])} / {f2(n['allowable_tip_load_N']['lateral'])} |")
    L.append(f"\nTip deflection at {s['planning_load_N']} N: {s['tip_deflection_mm']['without_notches']:.4f} mm without, {s['tip_deflection_mm']['with_notches']:.4f} mm with the notches.")
    L+=['','## Reservations proposed to the owner (not adopted)','']
    for r in nb['reservations']:
        if r['status']=='PROPOSAL_REQUIRES_OWNER_DECISION':L.append(f"- **{r['id']}** ({r['for']}): XY {r['box_mm']}, z {r['z_mm']}. {r['reason']}.")
        else:L.append(f"- **{r['id']}** ({r['for']}): {r['foreign_part']} top ≤ z {f2(r['max_top_z_mm'])} ({f2(r['max_rear_side_height_mm'])} mm above z 21.6).")
    t=nb['toggle_rear_bound'];L.append(f"- 2MS3 drawing bound: terminal tips at z ≤ {t['terminal_tip_z_max_mm']} if {'; '.join(t['conditions'])}.")
    L+=['','## Access and procedure','']
    for l in LINKS:
        a=B['access'][l];L.append(f"- {l} middle housing: long faces {'; '.join(k+' free '+f2(v['free_to_rigid_mm'])+' mm to '+str(v['nearest_rigid'])+' and '+f2(v['free_to_cable_mm'])+' mm to the '+str(v['nearest_cable'])+' bundle' for k,v in a['latch_faces'].items())}; panel-side corridor known hits {a['panel_side_corridor']['known_hits'] or 'none'}, foreign XY {a['panel_side_corridor']['foreign_xy_overlaps'] or 'none'}; straight bundle below the housing {a['straight_bundle_below_housing_mm']} mm; finger operation {a['finger_operation']}.")
    for g in B['guides']:
        a=B['access']['strap:'+g['id']];L.append(f"- {g['id']} strap latch: front access {a['front_access']} (hits {', '.join(a['known_hits']+a['foreign_xy_overlaps']) or 'none'}); reopen {a['reopen']}.")
    for k,v in data_procedure(b).items():
        L+=['',f'**{k}**','']+[f'{i}. {x}' for i,x in enumerate(v,1)]
    L+=['','## Measurements still NOT RUN','']+[f"- **{m['id']}** {m['item']}." for m in rep['measurements']]
    return '\n'.join(L)+'\n'


def data_procedure(b):return b['model'].get('procedure',{})


def render_svg(b):
    """Side (XZ) and plan (XY) views of B32 with the four states: installed, latch/tool corridor, middle release 15 mm, core 40 mm."""
    built=b['built']['B32'];res=b['res']['B32'];P=b['P'];W,H=900,1010
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif" font-size="9">',
        '<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#d6d6d6" stroke-width="2"/></pattern></defs>',
        '<rect width="100%" height="100%" fill="#fff"/>','<text x="10" y="16" font-size="12" font-weight="bold">Stage32 B32 service envelope (design study; modelled envelopes, not physical clearance)</text>',
        '<text x="10" y="30">Blue J-SIG, red J-PWR. Solid: installed. Dashed: middle housing withdrawn 15 mm (Stage10 travel). Purple dashed: proposed reservations RV-DIP (owner decision).</text>',
        '<text x="10" y="42">Orange: R1/R2 guides in notches. Hatched: neighbouring volume z 2-34, not designed (UNKNOWN, not free). Black dashed: core box incl. 40 mm withdrawal after K-PWR is disconnected.</text>']
    sc=7.0;x0,x1=195,300
    def view(ox,oy,ax2,lo2,hi2,title,flip):
        out.append(f'<text x="{ox}" y="{oy-6}" font-weight="bold">{esc(title)}</text><rect x="{ox}" y="{oy}" width="{(x1-x0)*sc}" height="{(hi2-lo2)*sc}" fill="none" stroke="#999"/>')
        return lambda p:(ox+(p[0]-x0)*sc,oy+((hi2-p[ax2]) if flip else (p[ax2]-lo2))*sc)
    side=view(20,70,2,0,75,'Side view XZ (y 160-190 projected; +z up = toward the rear)',True)
    plan=view(20,620,1,140,190,'Plan view XY (+y down)',False)
    def rect(T,lo,hi,st,clip):
        (a0,a1)=clip[0];lo=[max(lo[0],x0),max(lo[1],a0)];hi=[min(hi[0],x1),min(hi[1],a1)]
        if lo[0]>=hi[0] or lo[1]>=hi[1]:return
        p=T([lo[0],lo[1],lo[1]]);q=T([hi[0],hi[1],hi[1]]);out.append(f'<rect x="{min(p[0],q[0]):.1f}" y="{min(p[1],q[1]):.1f}" width="{abs(q[0]-p[0]):.1f}" height="{abs(q[1]-p[1]):.1f}" {st}/>')
    def style(o):
        i=o['id']
        if i.startswith('guide:'):return 'fill="#f0a85a" stroke="#a0581a" stroke-width="0.4"'
        if i.startswith('board:'):return 'fill="#e8f5e9" fill-opacity="0.6" stroke="#2e7d32" stroke-width="0.8"'
        if i.startswith('foreign'):return 'fill="#eeeeee" stroke="#bbb" stroke-width="0.3"'
        if i.startswith(('tool:','head:','spacer:')):return 'fill="none" stroke="#9aa5b1" stroke-width="0.4" stroke-dasharray="1,1"'
        return 'fill="#9aa5b1" fill-opacity="0.55" stroke="#4a5562" stroke-width="0.4"'
    for T,kind in ((side,'side'),(plan,'plan')):
        if kind=='side':rect(T,[x0,2],[x1,34],'fill="url(#h)" stroke="none"',((0,75),None))
        for o in built['obs']:
            if o['kind']=='unknown_depth' or o['id'].startswith(('release:','core-extraction','body:')):continue
            if kind=='side' and not(o['hi'][1]>160 and o['lo'][1]<190):continue
            if kind=='side':rect(T,[o['lo'][0],o['lo'][2]],[o['hi'][0],o['hi'][2]],style(o),((0,75),None))
            elif o['hi'][2]>26 and o['lo'][2]<49 or o['id'].startswith('foreign'):rect(T,[o['lo'][0],o['lo'][1]],[o['hi'][0],o['hi'][1]],style(o),((140,190),None))
        env=res['states']['core_40mm']['envelope']
        if kind=='side':rect(T,[env['lo'][0],env['lo'][2]],[env['hi'][0],env['hi'][2]],'fill="none" stroke="#111" stroke-dasharray="5,3"',((0,75),None))
        for r in b['neighbour']['reservations']:
            if not r['id'].startswith('RV-DIP'):continue
            if kind=='side':rect(T,[r['box_mm'][0],r['z_mm'][0]],[r['box_mm'][2],r['z_mm'][1]],'fill="none" stroke="#7b1fa2" stroke-dasharray="3,2"',((0,75),None))
            else:rect(T,[r['box_mm'][0],r['box_mm'][1]],[r['box_mm'][2],r['box_mm'][3]],'fill="none" stroke="#7b1fa2" stroke-dasharray="3,2"',((140,190),None))
        for l in LINKS:
            sp=built['spec']['routes'][l]
            for route,dash in ((built['routes'][l],''),(constant_length(built['geo'],l,sp,P,built['lengths'][l]['design_length_mm'],15,(0,1))['route'],'stroke-dasharray="4,3"')):
                pts=' '.join(f'{x:.1f},{y:.1f}' for x,y in (T(p) for p in route['dense'][::3]+[route['dense'][-1]]))
                out.append(f'<polyline points="{pts}" fill="none" stroke="{COLOR[l]}" stroke-width="1.4" {dash}/>')
            g=built['geo'][ENDS[l][1]]
            if kind=='plan':
                bx=g['box_mm'];rect(T,[bx[0],bx[1]],[bx[2],bx[3]],f'fill="{COLOR[l]}" fill-opacity="0.25" stroke="{COLOR[l]}"',((140,190),None))
                sw=g['sweep']['box_mm'];rect(T,[sw[0],sw[1]],[sw[2],sw[3]],f'fill="none" stroke="{COLOR[l]}" stroke-dasharray="2,2"',((140,190),None))
    for z,lab in ((48.4,'A01-middle front z 48.4'),(34,'carrier bottom z 34; below: neighbouring volume, UNKNOWN'),(21.6,'code-default foreign PCB rear z 21.6 (no outline)'),(13.4,'incumbent canonical P rear z 13.4 (other architecture)'),(2,'panel rear z 2')):
        a=side([x0,0,z]);c=side([x1,0,z]);out.append(f'<line x1="{a[0]:.0f}" y1="{a[1]:.1f}" x2="{c[0]:.0f}" y2="{c[1]:.1f}" stroke="#888" stroke-width="0.5" stroke-dasharray="1,2"/><text x="{c[0]+4:.0f}" y="{a[1]+3:.1f}" fill="#555">z {z}</text><text x="{a[0]+3:.0f}" y="{a[1]-2:.1f}" fill="#777">{esc(lab)}</text>')
    y=985-28
    for l in LINKS:
        rel=[x for x in res['states'][l]['release'] if x['travel_mm']==15 and x['withdrawn']=='middle'][0]
        out.append(f'<text x="20" y="{y}" fill="{COLOR[l]}">{l}: design length {res["states"][l]["design_length_mm"]} mm (local loop top z {res["states"][l]["installed_loop_top_z_mm"]:.1f}); the 15 mm middle release slides {rel["slide_through_guide_mm"]:.1f} mm through the guide and drops the envelope to z {rel["envelope_bottom_z_mm"]:.1f}; r 5 is below the maker 10 x OD rule (open)</text>');y+=13
    out.append(f'<text x="20" y="{y}">Criteria {esc(" ".join(k.split("_")[0]+(" yes" if v else " no") for k,v in res["criteria"].items()))}; status {esc(res["status"])}; physical NOT_RUN</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'


def outputs(b):
    b['model']['procedure']=b['_procedure']
    return {'model.json':dump(b['model']),'envelope.json':dump(b['envelope']),'analysis.json':dump(b['analysis']),'neighbour.json':dump(b['neighbour']),'report.json':dump(b['report']),
        'summary.md':render_md(b),'envelope.svg':render_svg(b)}


def run(data,preserve=True):
    b=build(data,preserve);b['_procedure']=data['input']['procedure'];return b,outputs(b)


def check_outputs(bodies):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage32-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            # Stage31 bytes are immutable from BASE; its own history replay already passed there.
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage31_cable_entry_redesign.py','--check','--check-review'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage31_cable_entry_redesign.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage31 source checkpoint (generator, review binding, tests normal and -O)')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage32/'+n for n in GENERATED}
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
    c=b['report']['comparison']
    print('PASS Stage32 source checks: '+'; '.join(f"{k} {v['status']}" for k,v in c.items())+'; physical/native NOT RUN')


if __name__=='__main__':main()
