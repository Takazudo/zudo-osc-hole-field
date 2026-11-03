"""A01 J-SIG/J-PWR whole-arch retention (RG34) and wire/current evidence on the Stage33 R33 study baseline (design only; no native/physical claims)."""
import argparse
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import stage33_large_radius as s33

s32,s31,s28=s33.s32,s33.s31,s33.s28
ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage34'
S33=ROOT/REL/'stage33'
BASE='2c41e8cd93574c356ba375fafba47ba65a480217'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage34_arch_retention.py','test_stage34_arch_retention.py')}
need,read,dump,sha=s28.need,s28.read,s28.dump,s28.sha
r6,p6,val=s32.r6,s32.p6,s32.val
LINKS,ENDS=s33.LINKS,s33.ENDS
GENERATED=('model.json','analysis.json','ledger.json','report.json','summary.md','plan-rg34.svg','arch-sections.svg','service-sections.svg')
CLASSES=s33.CLASSES
SIDES=('local','middle')
# Carriers that hold the core: RG34 stands on crossmember:rear:0, so registration drops out against these.
# Screwdriver columns of the A01-jack mounts are used only to remove the front jack board, which starts by removing RG34.
SERVICE_ONLY=('tool:A01-jack:',)
REAR=('core-envelope','board:A01-core','rail:rear','crossmember:rear','tool:A01-core','head:A01-core','spacer:A01-core','handle:')


# ---------- inputs ----------
def load():
    return {'approval':read(OUT/'approval.json'),'input':read(OUT/'design-input.json'),'sources':read(OUT/'sources.json'),'s33':s33.load(),
        's33_analysis':read(S33/'analysis.json'),'s33_report':read(S33/'report.json')}


def merged(data):
    """Stage32 + Stage33 parameters, extended (never overridden) by the Stage34 additions."""
    P,T,rules,bows=s33.merged(data['s33'])
    for k,v in data['input']['parameters'].items():
        need(k not in P,'Stage34 may not override the inherited parameter '+k);P[k]=v
    return P,T,rules,bows


def all_sources(data):
    return s32.validate_sources({'sources':data['s33']['s32']['sources']['sources']+data['s33']['sources']['sources']+data['sources']['sources']})


def validate_inputs(data):
    a=data['approval'];inp=data['input']
    P33,T,rules=s33.validate_inputs(data['s33'])
    need(inp['inherits']==REL+'stage33/design-input.json' and data['sources']['inherits']==REL+'stage33/sources.json','Stage34 inherits the committed Stage33 inputs')
    need(a['status']=='DESIGN_STUDY_CHANGES_ALLOWED' and a['decided_by']=='OWNER','owner approval record')
    need(a['changeable']['header_changes']==[],'the R33 header positions are the fixed study baseline')
    need(set(a['provisional_baseline']['does_not_adopt'])>={'canonical CAD','manufacturing outputs','a wire selection','physical feasibility'},'the provisional baseline adopts nothing')
    need(inp['status']=='DESIGN_STUDY_INPUT_NOT_MEASURED','design input status')
    for x,n in ((inp,'design-input'),(a,'approval'),(data['sources'],'sources')):s28.no_claims(x,n)
    src=all_sources(data);P,_,_,_=merged(data)
    for k in inp['parameters']:s32.classed(k,P[k],src)
    need(val(P,'inter_carrier_registration_mm') is None,'carrier registration is not known; it stays UNCONFIRMED')
    need(val(P,'registration_allowance_mm')>val(P,'guide_clearance_mm'),'the registration allowance is a requirement larger than the guide play')
    for k in ('guide_clearance_mm','guide_wall_mm','cut_length_tolerance_mm','guide_fab_tolerance_mm','guide_mount_float_mm'):need(val(P,k)>0,k+' is positive')
    need(val(P,'former_clearance_mm')==0.0,'the former is a contact guide (any in-plane play adds slack)')
    need(val(P,'selected_wire_mpn') is None,'no wire is selected without complete evidence')
    need(val(P,'jst_current_rating_awg28_A') is None and val(P,'jst_current_rating_awg30_A') is None,'the JST AWG26 current rating is not transferred to AWG28/30')
    for w in inp['wire_candidates_added']:
        for sid in w['sources']:need(src[sid]['authority'] in s32.MAKER_AUTH and not str(src[sid].get('availability','')).startswith('NOT_'),'wire candidate values from an obtained maker document '+w['mpn'])
        need(w['od_min_mm']<w['od_max_mm'],'wire OD range '+w['mpn'])
    cb=inp['current_budget']
    for link,rows in cb['links'].items():
        need([r['pin'] for r in rows]==[str(i) for i in range(1,len(rows)+1)],'one budget row per pin, in order '+link)
        for r in rows:
            for sid in r['sources']+[x for t in r['terms'] for x in t.get('sources',[])]:need(sid in src,'unknown current source '+sid)
            for t in r['terms']:
                need(t['kind'] in ('V_over_R','current','unknown'),'current term kind '+t['term'])
                if t['kind']!='unknown':need(t.get('sources') and t.get('basis'),'a current term carries its sources and basis '+t['term'])
                if t['kind']=='V_over_R':need(all(x>0 for x in t['R_ohm']) and t['V'][0]<=t['V'][1]+1e-12 and t['R_ohm'][0]>=t['R_ohm'][1]-1e-9,'typical never exceeds the conditional maximum '+t['term'])
                if t['kind']=='current':need(t['A'][0] is None or t['A'][0]<=t['A'][1],'typical never exceeds the conditional maximum '+t['term'])
            if r['established_max_A'] is not None:need(any(src[sid]['authority'] in s32.MAKER_AUTH for sid in r['sources']),'an established maximum needs maker evidence '+link+' pin '+r['pin'])
            else:need(r['established_status'].startswith('UNKNOWN'),'no established maximum means UNKNOWN '+link+' pin '+r['pin'])
    need(set(cb['stage33_inputs_superseded']['parameters'])=={'j_pwr_conductor_current_max_A','j_pwr_agnd_return_bound_A'},'the Stage33 X1-derived current inputs are superseded, not reused')
    rg=inp['rg34'];need(rg['service_withdrawal_ends_at_once']==1,'one end at a time with RG34 closed')
    return P,T,rules


# ---------- plane frames and prisms ----------
def frame(cand,l):
    a=cand['geo'][ENDS[l][0]]['exit_mm'];b=cand['geo'][ENDS[l][1]]['exit_mm'];D=math.dist(a[:2],b[:2]);u=[(b[0]-a[0])/D,(b[1]-a[1])/D]
    return {'link':l,'a':a,'b':b,'D':D,'u':u,'n':[-u[1],u[0]]}


def world(f,s,nn,z):return [f['a'][0]+s*f['u'][0]+nn*f['n'][0],f['a'][1]+s*f['u'][1]+nn*f['n'][1],z]


def local(f,p):
    dx,dy=p[0]-f['a'][0],p[1]-f['a'][1];return (dx*f['u'][0]+dy*f['u'][1],dx*f['n'][0]+dy*f['n'][1],p[2])


def plane_prism(f,pid,kind,s,nn,z,removable_for=None):
    poly=[world(f,a,b,0)[:2] for a,b in ((s[0],nn[0]),(s[1],nn[0]),(s[1],nn[1]),(s[0],nn[1]))]
    return {'id':pid,'link':f['link'],'kind':kind,'carrier':'rear','poly':[p6(p) for p in poly],'z':[r6(z[0]),r6(z[1])],'plane':{'s':p6(s),'n':p6(nn),'z':p6(z)},'removable_for':removable_for}


def box_prism(o):
    lo,hi=o['lo'],o['hi'];return {'id':o['id'],'link':o.get('link'),'kind':o.get('kind'),'poly':[[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]],'z':[lo[2],hi[2]]}


def _axes(poly):
    out=[]
    for i in range(len(poly)):
        p,q=poly[i],poly[(i+1)%len(poly)];out.append([q[1]-p[1],p[0]-q[0]])
    return out


def poly_overlap(A,B):
    for ax in _axes(A)+_axes(B):
        pa=[p[0]*ax[0]+p[1]*ax[1] for p in A];pb=[p[0]*ax[0]+p[1]*ax[1] for p in B]
        if max(pa)<=min(pb)+1e-12 or max(pb)<=min(pa)+1e-12:return False
    return True


def poly_dist(A,B):
    if poly_overlap(A,B):return 0.0
    return min(s33.seg_dist2(A[i],A[(i+1)%len(A)],B[j],B[(j+1)%len(B)]) for i in range(len(A)) for j in range(len(B)))


def point_poly_dist(p,A):
    if all((q[0]-pp[0])*(p[1]-pp[1])-(q[1]-pp[1])*(p[0]-pp[0])>=-1e-12 for pp,q in zip(A,A[1:]+A[:1])) or all((q[0]-pp[0])*(p[1]-pp[1])-(q[1]-pp[1])*(p[0]-pp[0])<=1e-12 for pp,q in zip(A,A[1:]+A[:1])):return 0.0
    def seg(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];L=dx*dx+dy*dy;t=0 if L==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L));return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
    return min(seg(a,b) for a,b in zip(A,A[1:]+A[:1]))


def zgap(a,b):return max(0.0,b[0]-a[1],a[0]-b[1])


def prism_dist(A,B):
    """Exact distance between two vertical prisms (convex plan polygon x z interval): the plan and z gaps combine in quadrature."""
    return math.hypot(poly_dist(A['poly'],B['poly']),zgap(A['z'],B['z']))


# ---------- vertical spheroids (free-span reach) ----------
def spheroid(xy,z1,z2,length,inflate):
    """All points a free span of the given length can reach between two points on one vertical line: a prolate spheroid with those foci, then inflated."""
    A=length/2;f=abs(z2-z1)/2;need(A>=f-1e-9,'free span shorter than its chord')
    return {'xy':p6(xy),'zc':r6((z1+z2)/2),'A':r6(A),'B':r6(math.sqrt(max(A*A-f*f,0.0))),'chord_mm':r6(2*f),'length_mm':r6(length),'inflate_mm':r6(inflate)}


def _ellipse(sp,n=20000):
    return [(sp['B']*math.sin(math.pi*k/n),sp['zc']+sp['A']*math.cos(math.pi*k/n)) for k in range(n+1)]


def spheroid_prism_dist(sp,pr):
    """Distance between the solid spheroid and a prism, minus the inflation: in the meridian half-plane the prism is a vertical segment at its plan distance from the axis."""
    d0=point_poly_dist(sp['xy'],pr['poly']);z0,z1=pr['z'];best=None
    for rr,zz in _ellipse(sp,4000 if d0>sp['B']+5 else 20000):
        if z0<=zz<=z1 and rr>=d0:return -sp['inflate_mm']
        d=math.hypot(max(0.0,d0-rr),zgap([zz,zz],[z0,z1]))
        if best is None or d<best:best=d
    return best-sp['inflate_mm']


def spheroid_pair_dist(s1,s2):
    dax=math.dist(s1['xy'],s2['xy']);e1=_ellipse(s1,600);e2=_ellipse(s2,600)
    best=min(math.hypot(max(0.0,dax-r1-r2),z1-z2) for r1,z1 in e1 for r2,z2 in e2)
    return best-s1['inflate_mm']-s2['inflate_mm']


# ---------- RG34 geometry ----------
def awg_d(n):return 0.127*92**((36-n)/39)


def rg34(cand,P,T):
    """Per cable: plane frame, heights, slack, sleeves, channel prisms. The admissible centreline region is |n| <= c, -c <= s <= D + c, below the cap, outside the inflated former."""
    c=val(P,'guide_clearance_mm');t=val(P,'guide_wall_mm');R=val(P,'route_radius_mm');trav=val(P,'release_travel_mm');grip=val(P,'grip_length_design_mm')
    dcut=val(P,'cut_length_tolerance_mm');e=val(P,'registration_allowance_mm');mh=2*val(P,'gh_mated_height_mm')
    x0,y0,x1,y1=cand['mech']['boards']['A01-middle']['outline_mm'];beta=T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)
    out={}
    for l in LINKS:
        f=frame(cand,l);r=s33.bundle(P,l)['round_radius_mm'];fan=s33.fan_in(P,l)['length_mm'];Ld=cand['lengths'][l]['design_length_mm'];Z0=cand['installed'][l]['top_centreline_z_mm']
        Rreq=s33.required_radius(val(P,'wire_bend_rule_x_od'),val(P,'wire_od_max_mm'),P,l)['surface'];ep=e-c;ls=math.sqrt(4*Rreq*ep-ep*ep)
        # Tolerance corners of the arch relative to RG34: short cable + bow + RG34 high, or long cable + RG34 low (z registration).
        dz={'low':-(dcut/2+beta/2+e),'nominal':0.0,'high':dcut/2+e}
        ex={'local':f['a'][2],'middle':f['b'][2]};zsb={k:ex[k]+fan+ls+e for k in SIDES};zent={k:ex[k]+trav+fan+grip+e for k in SIDES}
        Zlow=Z0+dz['low'];Zcap=Z0+dz['high']+trav/2+r+c;Ztop=Zcap+t
        Lhug=s33.arch(cand['geo'],l,Zlow,0,0,P)['length_mm']+mh;fixed=Ld+dcut-Lhug;delta=2*val(P,'former_setting_resolution_mm')
        g={'frame':{k:(p6(v) if isinstance(v,list) else r6(v)) for k,v in f.items() if k!='link'},'f':f,'r':r,'c':c,'t':t,'R':R,'fan_in_mm':r6(fan),'s_bend_length_mm':r6(ls),'required_radius_mm':r6(Rreq),
            'exit_z_mm':ex,'sleeve_bottom_z_mm':{k:r6(v) for k,v in zsb.items()},'block_entry_z_mm':{k:r6(v) for k,v in zent.items()},'Z0':Z0,'Zlow':Zlow,'Zcap_inner':Zcap,'Ztop':Ztop,
            'corners_dz_mm':{k:r6(v) for k,v in dz.items()},'former_top_range_z_mm':[r6(Zlow-r),r6(Z0+dz['high']-r)],'former_bottom_z_mm':r6(Zlow-R),'hug_length_mm':r6(Lhug),'slack_mm':r6(delta),'slack_fixed_former_mm':r6(fixed),'bow_mm':r6(beta),'design_length_mm':Ld}
        out[l]=g
    for l,g in out.items():
        f=g['f'];g['s_off']={k:sleeve_offset(cand,g,l,k,P) for k in SIDES};a_out=g['r']+g['c']+g['t'];D=f['D']
        Ls=max(2.0,g['s_off']['local']+g['r']+g['c']+g['t']);Ms=max(2.0,g['s_off']['middle']+g['r']+g['c']+g['t'])
        g['parts']=[plane_prism(f,'RG34-'+l+'-sleeve-local','sleeve',[-a_out,Ls],[-a_out,a_out],[g['sleeve_bottom_z_mm']['local'],g['block_entry_z_mm']['local']],'local'),
            plane_prism(f,'RG34-'+l+'-sleeve-middle','sleeve',[D-Ms,D+a_out],[-a_out,a_out],[g['sleeve_bottom_z_mm']['middle'],g['block_entry_z_mm']['middle']],'middle'),
            plane_prism(f,'RG34-'+l+'-channel-local-leg','channel',[-a_out,a_out],[-a_out,a_out],[g['block_entry_z_mm']['local'],g['Ztop']]),
            plane_prism(f,'RG34-'+l+'-channel-corner-local','channel',[-a_out,g['R']],[-a_out,a_out],[g['former_bottom_z_mm']-g['t'],g['Ztop']]),
            plane_prism(f,'RG34-'+l+'-channel-top','channel',[g['R'],D-Ms],[-a_out,a_out],[g['Zlow']-g['r']-g['t'],g['Ztop']]),
            plane_prism(f,'RG34-'+l+'-channel-middle','channel',[D-Ms,D+a_out],[-a_out,a_out],[g['block_entry_z_mm']['middle'],g['Ztop']])]
        g['interior_hull']=plane_prism(f,'RG34-'+l+'-interior','interior',[-(g['r']+g['c']),D+g['r']+g['c']],[-(g['r']+g['c']),g['r']+g['c']],[min(g['sleeve_bottom_z_mm'].values()),g['Zcap_inner']])
    return out


def state_list(P):
    t=val(P,'release_travel_sensitivity_mm');return [('installed',0.0,0.0)]+[('local',x,0.0) for x in t]+[('middle',0.0,x) for x in t]


def route_at(cand,l,tl,tm,P):
    return s33.constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tl,tm,P)


def shifted(route,dz):return [[p[0],p[1],p[2]+dz] for p in route['dense']]


def sleeve_offset(cand,g,l,side,P):
    """Largest in-plane offset of the centreline toward the arch inside a sleeve zone, over the states in which that sleeve is fitted."""
    f=g['f'];z0,z1=g['sleeve_bottom_z_mm'][side],g['block_entry_z_mm'][side];best=0.0
    for n,tl,tm in state_list(P):
        if (side=='local' and tl) or (side=='middle' and tm):continue
        for p in (q for dz in g['corners_dz_mm'].values() for q in shifted(route_at(cand,l,tl,tm,P)['route'],dz)):
            s,_,z=local(f,p)
            if z0-1e-9<=z<=z1+1e-9 and in_leg_region(g,s,side):best=max(best,s if side=='local' else f['D']-s)
    return r6(best)


def in_former(g,s,z):
    """Inside the inflated former (centreline excluded): s in (0, D), z below Zlow, with corner arcs of radius R."""
    D=g['f']['D'];R=g['R'];Zl=g['Zlow']
    # Below its lowest corner point the former ends; the sleeve bores bound the legs there.
    if not(1e-6<s<D-1e-6 and Zl-R-1e-6<=z<Zl-1e-6):return False
    if z>Zl-R:
        if s<R:return math.hypot(s-R,z-(Zl-R))<R-1e-6
        if s>D-R:return math.hypot(s-(D-R),z-(Zl-R))<R-1e-6
    return True


def in_leg_region(g,s,side):
    """The leg and bend region of one end (within R of the leg in s): what a sleeve encloses below its block entry."""
    return s<=g['R']+1e-9 if side=='local' else s>=g['f']['D']-g['R']-1e-9


def admissible(g,p,withdrawn,f):
    """Centreline point admissible in RG34: inside the walls and end walls, under the cap, outside the inflated former; the withdrawn end's sleeve zone is open."""
    s,nn,z=local(f,p);side='local' if s<f['D']/2 else 'middle';leg=in_leg_region(g,s,side)
    if z<g['sleeve_bottom_z_mm'][side]-1e-9:return True,None
    if withdrawn==side and leg and z<g['block_entry_z_mm'][side]-1e-9:return True,None
    if abs(nn)>g['c']+1e-6:return False,'wall'
    if s<-g['c']-1e-6 or s>f['D']+g['c']+1e-6:return False,'end wall'
    if z>g['Zcap_inner']-g['r']+1e-6:return False,'cap'
    if in_former(g,s,z):return False,'former'
    if not leg and z<g['Zlow']-g['R']-1e-6:return False,'below the channel'
    if leg and z<g['block_entry_z_mm'][side]-1e-9:
        if side=='local' and s>g['s_off']['local']+g['c']+1e-6:return False,'sleeve bore'
        if side=='middle' and f['D']-s>g['s_off']['middle']+g['c']+1e-6:return False,'sleeve bore'
    return True,None


def states_in_rg34(cand,geo,P):
    """Every allowed state (installed, one end withdrawn 2.45-15 mm) keeps the design length and stays admissible; the both-ends state is checked to be blocked."""
    rows=[];e=val(P,'registration_allowance_mm');grip=val(P,'grip_length_design_mm')
    for l in LINKS:
        g=geo[l];f=g['f']
        for corner,dz in g['corners_dz_mm'].items():
            for n,tl,tm in state_list(P)+[('both',val(P,'release_travel_mm'),val(P,'release_travel_mm'))]:
                c=route_at(cand,l,tl,tm,P);bad=[]
                for p in shifted(c['route'],dz):
                    ok,why=admissible(g,p,n,f)
                    if not ok:bad.append(why)
                # exits may sit up to e higher than RG34 (registration): the withdrawn fan-in and the grip still stay below the block entry
                fan_ok=all(g['exit_z_mm'][k]+e+t_+g['fan_in_mm']+grip<=g['block_entry_z_mm'][k]+1e-9 for k,t_ in (('local',tl),('middle',tm)))
                rows.append({'link':l,'corner':corner,'dz_mm':dz,'state':n,'travel_mm':max(tl,tm),'top_centreline_z_mm':r6(c['top_centreline_z_mm']+dz),'admissible':not bad,'blocked_by':sorted(set(bad)),'fan_in_below_block':fan_ok})
    return rows


def obstacle_prisms(cand):
    obs=[box_prism(o) for o in cand['obs'] if o['kind'] in ('known','assumed_height','unknown_depth') and not o['id'].startswith('core-extraction')]
    env=s31.core_envelope(cand['mech']);obs.append(box_prism({'id':'core-envelope-40mm','link':'K-PWR','lo':env['lo'],'hi':env['hi'],'kind':'known'}))
    return obs


def own(pr,l,side=None):
    """Parts that belong to a cable's own end: its housing release sweep (the housing lives there)."""
    i=pr['id']
    return i.startswith('release:A01:'+l+':') and (side is None or i.endswith(':'+side))


def stack_for(oid,P,T,rules,ubow,cross):
    st=s32.tol_stack(oid,[0,0,0],P,T,rules,bow_mm=ubow if oid.startswith('board:A01-middle') else None)
    extra={'guide_fab_tolerance_mm':val(P,'guide_fab_tolerance_mm'),'guide_mount_float_mm':val(P,'guide_mount_float_mm')}
    if cross:extra['registration_allowance_mm']=val(P,'registration_allowance_mm')
    parts=dict(st['contributors'],**extra);return {'contributors':{k:r6(v) for k,v in parts.items()},'worst_case_mm':r6(sum(parts.values()))}


# ---------- analyses ----------
def post_prism(cand,geo,inp):
    x0,y0,z0,x1,y1=inp['rg34']['post_box_mm'];top=next(p for p in geo['J-PWR']['parts'] if p['id'].endswith('channel-top'))
    pr={'id':'RG34-post','link':None,'kind':'post','carrier':'rear','poly':[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],'z':[z0,top['z'][0]]}
    base=next(o for o in cand['obs'] if o['id']==inp['rg34']['post_base_on'])
    need(abs(z0-base['hi'][2])<1e-9 and poly_overlap(pr['poly'],box_prism(base)['poly']),'the RG34 post stands on '+inp['rg34']['post_base_on'])
    need(poly_overlap(pr['poly'],top['poly']),'the RG34 post supports the J-PWR channel')
    return pr


def part_clearances(cand,geo,post,P,T,rules):
    """Every RG34 part (and the post) against every designed part, the core envelope and tool columns: margin, the obstacle stack, guide tolerances and, across carriers, the registration allowance."""
    m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');x0,y0,x1,y1=cand['mech']['boards']['A01-middle']['outline_mm']
    ubow=T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0);obs=obstacle_prisms(cand);rows=[]
    parts=[p for l in LINKS for p in geo[l]['parts']]+[post];svc=[]
    for pr in parts:
        best=None
        for o in obs:
            # A sleeve is off while its own housing is withdrawn; channel parts stay and keep every own-end sweep.
            if pr.get('removable_for') and own(o,pr['link'],pr['removable_for']):continue
            if pr['kind']=='post' and o['id']=='crossmember:rear:0':continue
            d=prism_dist(pr,o)
            if d>m+6:continue
            cross=not o['id'].startswith(REAR);st=stack_for(o['id'],P,T,rules,ubow,cross);sp=d-m-st['worst_case_mm']
            row={'part':pr['id'],'obstacle':o['id'],'distance_mm':r6(d),'cross_carrier':cross,'stack':st,'robust_spare_mm':r6(sp),'meets_K4':sp>=k4-1e-12}
            if o['id'].startswith(SERVICE_ONLY):svc.append(dict(row,overlaps=d<=0,use='front jack board removal only; RG34 is removed first'));continue
            if best is None or sp<best['robust_spare_mm']:best=row
        rows.append(best or {'part':pr['id'],'obstacle':None,'distance_mm':None,'robust_spare_mm':None,'meets_K4':True,'note':'nothing within margin + 6 mm'})
    sig=[p for p in geo['J-SIG']['parts']];pwr=[p for p in geo['J-PWR']['parts']]
    outer=min(prism_dist(a,b) for a in sig for b in pwr)
    inner=poly_dist(geo['J-SIG']['interior_hull']['poly'],geo['J-PWR']['interior_hull']['poly']) if zgap(geo['J-SIG']['interior_hull']['z'],geo['J-PWR']['interior_hull']['z'])==0 else None
    return {'rows':sorted(rows,key=lambda r:(r['robust_spare_mm'] if r['robust_spare_mm'] is not None else 99,r['part'])),'service_only':sorted(svc,key=lambda r:r['robust_spare_mm']),
        'service_only_clear_of_overlap':not any(r['overlaps'] for r in svc),'outer_gap_between_channels_mm':r6(outer),
        'interior_hull_plan_gap_mm':r6(inner) if inner is not None else None,'walls_fit_between_cables':inner is None or inner>=2*val(P,'guide_wall_mm')-1e-9}


def free_spans(cand,geo,post,P,T,rules,slack_key='slack_mm'):
    """Reach of each unconfined span (exit to sleeve bottom) when all the RG34 slack enters it: a spheroid with foci at the exit and the sleeve bottom; the middle exit also at the largest bow."""
    m=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm');obs=obstacle_prisms(cand);out=[];sph={}
    x0,y0,x1,y1=cand['mech']['boards']['A01-middle']['outline_mm'];ubow=T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)
    infl_extra=val(P,'guide_clearance_mm')+val(P,'registration_allowance_mm')+val(P,'guide_fab_tolerance_mm')+val(P,'guide_mount_float_mm')
    for l in LINKS:
        g=geo[l];xy={'local':g['f']['a'][:2],'middle':g['f']['b'][:2]}
        for side in SIDES:
            z1=g['exit_z_mm'][side];z2=g['sleeve_bottom_z_mm'][side];L=z2-z1+g[slack_key];infl=infl_extra+g['r']
            cases=[spheroid(xy[side],z1,z2,L,infl)]
            # A set former absorbs the bow (set on the bowed board); with a fixed former the bow is already inside the fixed-former slack.
            if side=='middle':cases.append(spheroid(xy[side],z1-g['bow_mm'],z2,L+(g['bow_mm'] if slack_key=='slack_mm' else 0.0),infl))
            sph[(l,side)]=cases
    for (l,side),cases in sph.items():
        rows=[]
        for sp in cases:
            for o in obs+[post]+[p for l2 in LINKS if l2!=l for p in geo[l2]['parts']]:
                if own(o,l,side) or point_poly_dist(sp['xy'],o['poly'])>sp['B']+sp['inflate_mm']+m+6:continue
                d=spheroid_prism_dist(sp,o);st=s32.tol_stack(o['id'],[0,0,0],P,T,rules,bow_mm=ubow if o['id'].startswith('board:A01-middle') else None) if not o['id'].startswith('RG34') else {'worst_case_mm':0.0,'contributors':{}}
                sp_=d-m-st['worst_case_mm'];rows.append({'against':o['id'],'distance_mm':r6(d),'stack_mm':st['worst_case_mm'],'robust_spare_mm':r6(sp_),'meets_K4':sp_>=k4-1e-12})
            for (l2,side2),c2 in sph.items():
                if l2==l or l2<l:continue
                for sp2 in c2:
                    if math.dist(sp['xy'],sp2['xy'])>sp['B']+sp2['B']+sp['inflate_mm']+sp2['inflate_mm']+m+6:continue
                    d=spheroid_pair_dist(sp,sp2);st=s32.tol_stack('cable:',[0,0,0],P,T,rules);sp_=d-m-st['worst_case_mm']
                    rows.append({'against':f'{l2} {side2} free span','distance_mm':r6(d),'stack_mm':st['worst_case_mm'],'robust_spare_mm':r6(sp_),'meets_K4':sp_>=k4-1e-12})
        rows.sort(key=lambda r:r['robust_spare_mm'])
        out.append({'link':l,'side':side,'spheroids':cases,'semi_minor_mm':max(c['B'] for c in cases),'tightest':rows[:4],'meets_K4':all(r['meets_K4'] for r in rows)})
    return out


def negative_controls(cand,geo,s33res,fs,P):
    """Bounds that fail on purpose: a guide on the local leg alone, RG34 without its former, and a both-ends withdrawal with the lid closed."""
    mh=2*val(P,'gh_mated_height_mm');out={}
    for l in LINKS:
        g=geo[l];f=g['f'];route=cand['routes'][l];zl=g['block_entry_z_mm']['local']
        zmin=s33.arch_zmin(cand['geo'],l,0,0,P);free=g['design_length_mm']+val(P,'cut_length_tolerance_mm')-(s33.arch(cand['geo'],l,zmin,0,0,P)['length_mm']+mh)
        rem=route['length_mm']-(zl-f['a'][2]);A=[f['a'][0],f['a'][1],zl];B=f['b'];ch=math.dist(A,B)
        u=[(B[i]-A[i])/ch for i in range(3)]
        bucket=max(math.dist(p,[A[i]+u[i]*sum((p[k]-A[k])*u[k] for k in range(3)) for i in range(3)]) for p in route['dense'] if p[2]>=zl-1e-9 or local(f,p)[0]>1e-6)
        one_leg=0.5*math.sqrt((rem+free)**2-ch*ch);allow=s33res['retention'][l]['lateral_allowance_mm']
        loc=next(x for x in fs if x['link']==l and x['side']=='local');ch2=g['sleeve_bottom_z_mm']['local']-g['exit_z_mm']['local']
        nf=0.5*math.sqrt((ch2+free)**2-ch2*ch2);worst=min(r['robust_spare_mm'] for r in loc['tightest'])
        out[l]={'local_leg_guide_only':{'remainder_length_mm':r6(rem),'slack_without_former_mm':r6(free),'chord_mm':r6(ch),'reach_semi_minor_mm':r6(one_leg),'bucket_handle_radius_mm':r6(bucket),
                'stage33_allowance_mm':allow,'bounded_within_allowance':one_leg<=allow and bucket<=allow},
            'without_former':{'slack_mm':r6(free),'local_free_span_semi_minor_mm':r6(nf),'with_former_semi_minor_mm':loc['semi_minor_mm'],'growth_mm':r6(nf-loc['semi_minor_mm']),
                'tightest_spare_with_former_mm':worst,'bounded_within_spare':nf-loc['semi_minor_mm']<=worst}}
    return out


def strength(geo,post,P):
    """The post as the root of a rigid RG34 assembly: a load at the farthest RG34 point gives bending (full 3D lever, weak axis) and torsion (horizontal lever) at once; von Mises at the root. Joints and walls not evaluated."""
    xs=[p[0] for p in post['poly']];ys=[p[1] for p in post['poly']];b,h=max(xs)-min(xs),max(ys)-min(ys);root=[(max(xs)+min(xs))/2,(max(ys)+min(ys))/2,post['z'][0]]
    pts=[(q[0],q[1],z) for l in LINKS for p in geo[l]['parts'] for q in p['poly'] for z in p['z']];far=max(pts,key=lambda q:math.dist(q,root));lever=math.dist(far,root);arm=math.dist(far[:2],root[:2])
    I=min(b*h**3,h*b**3)/12;c=(min(b,h))/2;allow=val(P,'carrier_proof_MPa')/val(P,'strength_safety_factor')
    lo,hi=min(b,h),max(b,h);alpha=1/(3+1.8*lo/hi)  # rectangle torsion: tau_max = T / (alpha a b^2)
    per_N=math.sqrt((lever*c/I)**2+3*(arm/(alpha*hi*lo*lo))**2)
    grid=[{'load_N':F,'von_mises_MPa':r6(F*per_N),'meets':F*per_N<=allow} for F in val(P,'load_sensitivity_N')]
    return {'post_section_mm':[r6(b),r6(h)],'lever_mm':r6(lever),'torsion_arm_mm':r6(arm),'farthest_point_mm':p6(far),'I_min_mm4':r6(I),'torsion_alpha':r6(alpha),'allowable_load_N':r6(allow/per_N),'grid':grid,
        'planning_load_N':val(P,'planning_load_N'),'meets_at_planning_load':allow/per_N>=val(P,'planning_load_N'),
        'material':{'name':val(P,'carrier_material'),'proof_min_MPa':val(P,'carrier_proof_MPa'),'safety_factor':val(P,'strength_safety_factor')},
        'not_covered':['post root fixity: the post overhangs crossmember:rear:0 (y 167.5-170 off its 170-174 top face); root treated as fixed','post-to-crossmember fastening and the crossmember:rear:0 / rail:rear:0 joint','channel walls, lids and sleeves under a load','the J-SIG to J-PWR channel joint','fatigue, vibration, impact'],
        'status':'CALCULATED_CONDITIONALLY; not a physical strength result (M34-05)'}


def constructions(inp):
    c=dict(inp['stage33_wire_constructions']);c.update({w['mpn']:{'strands':w['strands'],'strand_awg':w['strand_awg']} for w in inp['wire_candidates_added']});return c


def friction(geo,inp,P):
    """Drag of the cable through RG34 (friction upper bound x cable weight upper bound) against the buckling load of each free span (strands-only stiffness of the most flexible identified wire)."""
    cons=constructions(inp);E=val(P,'copper_E_lower_MPa');mu=val(P,'friction_coefficient_upper');od=val(P,'wire_od_max_mm')
    heavy=max(cons.items(),key=lambda kv:kv[1]['strands']*awg_d(kv[1]['strand_awg'])**2);soft=min(cons.items(),key=lambda kv:kv[1]['strands']*awg_d(kv[1]['strand_awg'])**4)
    acu=heavy[1]['strands']*math.pi/4*awg_d(heavy[1]['strand_awg'])**2;q=(acu*val(P,'copper_density_g_cm3')+(math.pi/4*od*od-acu)*val(P,'insulation_density_upper_g_cm3'))*1e-3*9.81e-3
    ei1=soft[1]['strands']*E*math.pi*awg_d(soft[1]['strand_awg'])**4/64;out={}
    for l in LINKS:
        n=val(P,'conductors')[l];W=q*n*geo[l]['design_length_mm'];drag=mu*W;spans={}
        for side in SIDES:
            # With that end's sleeve removed the pushed span reaches the block entry (worst case for re-mating).
            Lf=geo[l]['block_entry_z_mm'][side]-geo[l]['exit_z_mm'][side];pcr=2.046*math.pi**2*n*ei1/Lf**2;spans[side]={'length_mm':r6(Lf),'buckling_load_N':r6(pcr),'ratio_to_drag':r6(pcr/drag)}
        out[l]={'weight_upper_N':r6(W),'drag_upper_N':r6(drag),'free_spans':spans,'slack_moves_without_buckling':all(v['ratio_to_drag']>=10 for v in spans.values())}
    return {'heaviest_construction':heavy[0],'most_flexible_construction':soft[0],'EI_per_conductor_Nmm2':r6(ei1),'weight_per_conductor_N_per_mm':q,'links':out,
        'note':'the retention bounds do not use stiffness; this only shows the slack can follow a withdrawal without buckling a free span. The drag bound (friction x weight) leaves out contact forces from bending stiffness and tension at the bends. Abrasion over repeated withdrawals is not calculated (M34-04).'}


def cover(geo,P):
    """RG34 top under the rear cover with the same rule as every RG34 clearance: margin, RG34 tolerances, registration (carrier to cover), K4."""
    top=val(P,'enclosure_rear_inner_z_mm');m=val(P,'placement_margin_mm');e=val(P,'registration_allowance_mm');k4=val(P,'robust_spare_mm')
    st=val(P,'guide_fab_tolerance_mm')+val(P,'guide_mount_float_mm')+e;out={}
    for l,g in geo.items():
        sp=top-g['Ztop']-m-st;need_z=g['Ztop']+m+st+k4
        out[l]={'rg34_top_z_mm':r6(g['Ztop']),'margin_mm':m,'stack_mm':r6(st),'cover_z_mm':top,'robust_spare_mm':r6(sp),'meets_K4':sp>=k4-1e-12,'cover_needed_z_mm':r6(need_z),
            'shortfall_mm':r6(max(0.0,need_z-top)),'design_length_cut_to_fit_mm':r6(max(0.0,2*(need_z-top)))}
    return out


def access(cand,geo,P):
    """With a sleeve removed: the housing column from the exit up to the block entry (latch press and the grip during 15 mm) against rigid parts and the other cable's RG34 parts."""
    obs=obstacle_prisms(cand);out={}
    for l in LINKS:
        for side,ref in zip(SIDES,ENDS[l]):
            g=cand['geo'][ref];bx=g['box_mm'];z0=geo[l]['exit_z_mm'][side];z1=geo[l]['block_entry_z_mm'][side]
            col={'poly':[[bx[0],bx[1]],[bx[2],bx[1]],[bx[2],bx[3]],[bx[0],bx[3]]],'z':[z0,z1]}
            others=[p for l2 in LINKS if l2!=l for p in geo[l2]['parts']]
            hits=sorted(o['id'] for o in obs+others if not o['id'].startswith('release:A01:'+l) and not o['id'].startswith('board:') and prism_dist(col,o)==0)
            out[ref]={'column_z_mm':[r6(z0),r6(z1)],'free_height_mm':r6(z1-z0),'rigid_hits':hits,'clear':not hits,'grip_zone_z_mm':[r6(z0+geo[l]['fan_in_mm']),r6(z1-val(P,'release_travel_mm'))],
                'finger_operation':'NOT_DETERMINED (M33-03)'}
    return out


def reservation_check(geo,s33res):
    """RG34 against the provisionally reserved volumes: wall protrusion beyond the RV-ARCH half-thickness and RV-ACCESS columns occupied above the grip zones."""
    rv={r['id']:r for r in s33res['reservations']};out=[]
    for l in LINKS:
        g=geo[l];w=rv['RV-ARCH-'+l]['slab']['half_thickness_mm'];a_out=g['r']+g['c']+g['t']
        zs=[z for q in rv['RV-ARCH-'+l]['slab']['parts'] for z in q['z_mm']]
        occ=[]
        for ref in ENDS[l]:
            r=rv['RV-ACCESS-'+ref.split(':',1)[1].replace(':','-')];colp={'poly':[[r['box_mm'][0],r['box_mm'][1]],[r['box_mm'][2],r['box_mm'][1]],[r['box_mm'][2],r['box_mm'][3]],[r['box_mm'][0],r['box_mm'][3]]],'z':r['z_mm']}
            occ+=[{'reservation':r['id'],'part':p['id']} for p in g['parts'] if prism_dist(colp,p)==0]
        lo=min(p['z'][0] for p in g['parts']);hi=max(p['z'][1] for p in g['parts'])
        out.append({'link':l,'rv_arch_half_thickness_mm':w,'rg34_half_thickness_mm':r6(a_out),'protrusion_mm':r6(a_out-w),'rv_arch_z_mm':[min(zs),max(zs)],'rg34_z_mm':[r6(lo),r6(hi)],
            'below_rv_arch_mm':r6(max(0.0,min(zs)-lo)),'rv_access_occupied':occ,'status':'PROPOSAL_REQUIRES_OWNER_DECISION'})
    return out


def r17_check(data,mech,P,T,geo):
    """Sensitivity: the same RG34 rule at R 17 (15x OD): the cap over the single-end raised arch against the rear cover."""
    Q=copy.deepcopy(P);Q['route_radius_mm']['value']=17.0;cand=s33.build_r33(data['s33']['input']['candidates']['R33'],data['s33'],mech,Q);out={}
    for l in LINKS:
        g=geo[l];Z0=cand['installed'][l]['top_centreline_z_mm'];top=Z0+g['corners_dz_mm']['high']+val(P,'release_travel_mm')/2+g['r']+g['c']+g['t']
        need_z=top+val(P,'placement_margin_mm')+val(P,'guide_fab_tolerance_mm')+val(P,'guide_mount_float_mm')+val(P,'registration_allowance_mm')+val(P,'robust_spare_mm')
        out[l]={'installed_top_centreline_z_mm':r6(Z0),'rg34_top_z_mm':r6(top),'needed_z_mm':r6(need_z),'fits_under_cover':need_z<=val(P,'enclosure_rear_inner_z_mm')}
    return out


# ---------- electrical and wire ledgers ----------
def current_ledger(inp,P,mech):
    cb=inp['current_budget'];lim=val(P,'gh_contact_current_limit_A');jst=val(P,'jst_current_rating_awg26_A');out={}
    for link,rows in cb['links'].items():
        pins=mech['headers']['A01:'+link+':local']['pins']
        for r in rows:need(pins[r['pin']]==r['net'],'current budget net matches the header pin map '+link+' pin '+r['pin'])
        rr=[]
        for r in rows:
            terms=[];typ=cond=fault=0.0
            for t in r['terms']:
                if t['kind']=='unknown':terms.append({'term':t['term'],'typical_A':None,'conditional_A':None,'status':'UNKNOWN','basis':t['basis']});continue
                if t['kind']=='V_over_R':a=[t['V'][i]/t['R_ohm'][i]*t['count'] for i in (0,1)]
                else:a=[None if t['A'][0] is None else t['A'][0]*t['count'],t['A'][1]*t['count']]
                fi=t.get('fault_A',0.0)*t['count'];typ+=a[0] or 0.0;cond+=a[1];fault+=fi
                terms.append({'term':t['term'],'typical_A':None if a[0] is None else r6(a[0]*1e3)/1e3,'conditional_A':r6(a[1]*1e3)/1e3,'fault_increment_A':r6(fi*1e3)/1e3 if fi else None,'basis':t['basis'],'sources':t['sources']})
            fault=cond+fault if fault else None;worst=fault or cond
            rr.append({'pin':r['pin'],'net':r['net'],'driver':r['driver'],'loads':r['loads'],'direction':r['direction'],'typical_A':typ,'conditional_max_A':cond,
                'conditional_fault_A':fault,'condition':r['condition'],'terms':terms,'unknown_terms':[t['term'] for t in terms if t.get('status')=='UNKNOWN'],'established_max_A':r['established_max_A'],'established_status':r['established_status'],
                'worst_conditional_A':worst,'within_project_limit_conditional':worst<=lim,'fraction_of_project_limit':r6(worst/lim),'fraction_of_jst_awg26_rating':r6(worst/jst),'sources':r['sources']})
        out[link]=rr
    s33p=inp['current_budget']['stage33_inputs_superseded']
    return {'links':out,'project_contact_limit_A':lim,'jst_rating_awg26_A':jst,'classes':cb['classes'],'conditions':cb['conditions'],'established_any':any(r['established_max_A'] is not None for v in out.values() for r in v),
        'stage33_superseded':dict(s33p,stage33_values={k:P[k]['value'] for k in s33p['parameters']}),
        'fault':'no fuse, PTC, series element or regulator limit exists upstream (R-POWER-SPEC); a short on a J-PWR or AGND conductor is limited only by an unselected source (requirement 2.1 A), above the JST 1.0 A rating: UNKNOWN'}


def wire_ledger(inp,data,P,cur):
    """Per wire: terminal compatibility, conductor and contact current, temperature rise, derating, installed bend and service flex kept separate; a wire meets the set only with no FAIL and no UNKNOWN."""
    jmin,jmax=val(P,'wire_od_min_mm'),val(P,'wire_od_max_mm');R=val(P,'route_radius_mm');amp={26:4.6,28:3.4,30:2.5}
    worst={l:max(r['worst_conditional_A'] for r in cur['links'][l]) for l in LINKS};rows=[]
    ws=[dict(w,od_min_mm=w['od_nominal_mm']-w['od_tolerance_mm'],od_max_mm=w['od_nominal_mm']+w['od_tolerance_mm'],stage=33) for w in data['s33']['input']['wire_candidates']]+[dict(w,stage=34) for w in inp['wire_candidates_added']]
    for w in ws:
        lo,hi=w['od_min_mm'],w['od_max_mm'];per={}
        for l in LINKS:
            env=hi*val(P,'round_bundle_factor')[l]/2+val(P,'bundle_dressing_allowance_mm');k=w['bend_rule_x_od']
            chk={'awg_in_jst_range':'PASS' if val(P,'wire_awg_range')[1]<=w['awg']<=val(P,'wire_awg_range')[0] else 'FAIL',
                'od_window_full_tolerance':'PASS' if lo>=jmin-1e-9 and hi<=jmax+1e-9 else 'FAIL',
                'tin_plated_stranded':'PASS' if w['plating']=='tin' and '/' in w['conductor'] else 'FAIL',
                'voltage':'PASS' if w['voltage_V']>=val(P,'gh_voltage_rating_V') else 'FAIL',
                'temperature':'PASS' if w['temperature_max_C']>=val(P,'gh_temperature_max_C') else 'FAIL',
                # Currents are conditional maxima with no established limit, so a rating comparison can only be CONDITIONAL.
                'contact_rating':('CONDITIONAL' if worst[l]<=val(P,'jst_current_rating_awg26_A') else 'FAIL') if w['awg']==26 else 'UNKNOWN',
                'temperature_rise':'CONDITIONAL' if w['awg']==26 and worst[l]<=val(P,'jst_current_rating_awg26_A') else 'UNKNOWN',
                'derating_to_project_limit':('CONDITIONAL' if worst[l]<=val(P,'gh_contact_current_limit_A') else 'FAIL') if w['awg']==26 else 'UNKNOWN',
                'bend_installed_R12':('PASS' if R>=k*hi+env-1e-9 else 'FAIL') if k is not None else 'UNKNOWN',
                'service_flex':'UNKNOWN'}
            failed=[x for x,v in chk.items() if v=='FAIL'];unk=[x for x,v in chk.items() if v=='UNKNOWN']
            cnd=[x for x,v in chk.items() if v=='CONDITIONAL']
            per[l]={'checks':chk,'failed':failed,'unknown':unk,'conditional':cnd,'status':'FAIL' if failed else 'UNKNOWN' if unk else 'CONDITIONAL' if cnd else 'MEETS_ALL',
                'conductor_ampacity_generic_A':amp.get(w['awg']),'worst_conditional_A':worst[l]}
        rows.append({'mpn':w['mpn'],'stage':w['stage'],'awg':w['awg'],'conductor':w['conductor'],'insulation':w['insulation'],'od_range_mm':[r6(lo),r6(hi)],'od_margin_to_window_mm':[r6(lo-jmin),r6(jmax-hi)],
            'voltage_V':w['voltage_V'],'temperature_max_C':w['temperature_max_C'],'bend_rule_x_od':w['bend_rule_x_od'],'per_cable':per,'sources':w['sources']})
    closest=[{'mpn':r['mpn'],'unknown':r['per_cable']['J-PWR']['unknown'],'conditional':r['per_cable']['J-PWR']['conditional']} for r in rows if not r['per_cable']['J-PWR']['failed'] and not r['per_cable']['J-SIG']['failed']]
    return {'wires':rows,'selection':None,'selection_status':'NULL: no identified wire meets every check; the closest fail nothing but leave UNKNOWN items, and their current checks are CONDITIONAL (no established current maximum)','closest':closest,
        'basis':{'contact_rating':'JST 1.0 A at AWG #26 only (S-JST-EGH); not transferred to AWG #28/#30','temperature_rise':'JST range -40 to +105 C includes temperature rise at the rated current (AWG #26)',
            'derating':'project limit 0.5 A per contact (R-STAGE10-CONTACT-LIMIT), half the JST AWG #26 rating','conductor_ampacity':'generic chart only (S-REMINGTON-AMPACITY, not a candidate maker); shown, not used as a check',
            'service_flex':'no candidate maker states a repeated-flex radius; RG34 also slides the cable through its guides at each withdrawal','crimp_process':'JST applicator and crimp height for every wire: NOT RUN (process item)'},
        'questions':['Amphenol CIT / Thermax: minimum bend radius (installation and repeated flexing) for M22759/18-26 and confirmation that the .030-.034 in OD range is current',
            'JST: SSHL-002T-P0.2 current rating or temperature-rise curve with AWG #28 and #30, and any insulation restriction for mPPE, PVC or ETFE',
            'Measurement: OD of an M22759/18-26 sample against the 0.76 mm floor (stated minimum 0.762 mm leaves 0.002 mm)',
            'Measurement: unpowered repeated-withdrawal flex and abrasion test of the chosen wire at R12 through RG34 (M34-04)']}


# ---------- evaluation ----------
MEASUREMENTS=[
    {'id':'M34-01','item':'Unpowered mock-up of R33 + RG34 (printed or machined channels on a carrier dummy): both arches at the design lengths, lids and sleeves closed; lateral position at the bend apexes and free spans in six enclosure orientations, before and after a defined handling push'},
    {'id':'M34-02','item':'Free-span excursion on the mock-up: largest lateral displacement of each exit-to-sleeve span with the arch top pushed onto the former (all slack driven into one span), against the computed spheroid semi-minor axes'},
    {'id':'M34-03','item':'Cut length after crimping of each harness (M-09) against +/- cut_length_tolerance_mm, and the arch top gap to the former when installed'},
    {'id':'M34-04','item':'Repeated single-end 15 mm withdrawals through RG34: pull and push force, sliding drag, insulation abrasion at the sleeve and channel entries, fan-in shape after cycling (M-12)'},
    {'id':'M34-05','item':'RG34 post, joint and wall stiffness/strength under a hand load; post fastening to crossmember:rear:0'},
    {'id':'M34-06','item':'Inter-carrier registration between the rear carrier and the jack/middle carriers on the enclosure cleats, against registration_allowance_mm'},
    {'id':'M34-07','item':'Latch press and bundle grip at each housing with only that sleeve removed (finger or tool), and lid/sleeve refit with no conductor in a parting line'},
    {'id':'M34-08','item':'Selected wire: OD sample, maker bend radius (installation and repeated flexing), JST contact rating at its gauge (M33-01 carried forward)'}]


def evaluate(data,mech,P,T,rules,bows):
    cand,res33,inst=s33.evaluate(data['s33'],mech,P,T,rules,bows)
    need(res33['status']=='CONDITIONAL_PENDING_RETENTION','the Stage33 ideal-plane criteria re-run unchanged: '+', '.join(res33['failed']))
    inp=data['input'];geo=rg34(cand,P,T);post=post_prism(cand,geo,inp)
    st=states_in_rg34(cand,geo,P);pc=part_clearances(cand,geo,post,P,T,rules);fs=free_spans(cand,geo,post,P,T,rules)
    nc=negative_controls(cand,geo,res33,fs,P);stren=strength(geo,post,P);fr=friction(geo,inp,P);cv=cover(geo,P);acc=access(cand,geo,P)
    rv=reservation_check(geo,res33);r17=r17_check(data,mech,P,T,geo);cur=current_ledger(inp,P,mech);wires=wire_ledger(inp,data,P,cur)
    gap=val(P,'guide_closure_gap_max_mm');odmin=min([val(P,'wire_od_min_mm')]+[w['od_min_mm'] for w in inp['wire_candidates_added']])
    grip=val(P,'grip_length_design_mm');trav=val(P,'release_travel_mm');e=val(P,'registration_allowance_mm')
    # Exits may sit up to e closer to RG34 than nominal: the S-bend room and the grip must survive that.
    t7=all(g['s_bend_length_mm']>0 and g['sleeve_bottom_z_mm'][k]-e-(g['exit_z_mm'][k]+g['fan_in_mm'])>=g['s_bend_length_mm']-1e-9 and g['sleeve_bottom_z_mm'][k]<g['block_entry_z_mm'][k]
        and g['block_entry_z_mm'][k]-e-(g['exit_z_mm'][k]+trav+g['fan_in_mm'])>=grip-1e-9 and g['block_entry_z_mm'][k]<=g['Zcap_inner']-g['r'] for g in geo.values() for k in SIDES)
    fixed=free_spans(cand,geo,post,P,T,rules,'slack_fixed_former_mm');nc['fixed_former']={'meets_K4':all(x['meets_K4'] for x in fixed),'tightest':{f"{x['link']} {x['side']}":x['tightest'][0] for x in fixed}}
    crit={'T1_declared_closed_parts_and_closure_gap':all(inp['rg34']['parts_closed'].values()) and gap<odmin/2,
        'T2_single_end_states_inside_RG34_all_corners':all(r['admissible'] and r['fan_in_below_block'] for r in st if r['state']!='both'),
        'T3_parts_clear_K4':all(r['meets_K4'] for r in pc['rows']) and pc['service_only_clear_of_overlap'],
        'T4_walls_fit_between_cable_interiors':pc['walls_fit_between_cables'],
        'T5_free_spans_bounded_and_clear':all(x['meets_K4'] for x in fs),
        'T6_rear_cover_K4':all(v['meets_K4'] for v in cv.values()),
        'T7_fan_in_grip_and_s_bend_with_registration':t7,
        'T8_strength_planning_load':stren['meets_at_planning_load'],
        'T9_slack_follows_without_buckling':all(v['slack_moves_without_buckling'] for v in fr['links'].values()),
        'T10_both_ends_withdrawal_blocked':all(r['blocked_by']==['cap'] or 'cap' in r['blocked_by'] for r in st if r['state']=='both'),
        'T11_access_columns_clear':all(a['clear'] for a in acc.values())}
    failed=[k for k,v in crit.items() if not v]
    status='BOUNDED_WITHIN_STATED_ASSUMPTIONS' if not failed else 'BOUNDED_EXCEPT_REAR_COVER' if failed==['T6_rear_cover_K4'] else 'NOT_BOUNDED'
    return cand,res33,{'geometry':geo,'post':post,'states':st,'parts':pc,'free_spans':fs,'negative_controls':nc,'strength':stren,'friction':fr,'cover':cv,'access':acc,'reservations':rv,'r17':r17,
        'current':cur,'wires':wires,'criteria':crit,'failed':failed,'status':status,'closure':{'gap_max_mm':gap,'smallest_wire_od_mm':odmin}}


def nc_fixed(rg):return rg['negative_controls']['fixed_former']['meets_K4']


def public_geo(geo):
    return {l:{k:v for k,v in g.items() if k!='f'} for l,g in geo.items()}


def build(data,preserve=True):
    P,T,rules=validate_inputs(data);bows=merged(data)[3];s29,_,_=s33.s30.stage29_current();mech=s29['mech']
    cand,res33,rg=evaluate(data,mech,P,T,rules,bows)
    # The retention bound must hold; the only accepted open criterion is the J-SIG cap against the rear cover (reported, with the smallest changes, as an owner decision).
    need(rg['status']=='BOUNDED_EXCEPT_REAR_COVER' and [l for l,v in rg['cover'].items() if not v['meets_K4']]==['J-SIG'],'RG34 must bound the whole arch under the stated assumptions: '+', '.join(rg['failed']))
    need(not nc_fixed(rg),'RG34 with a fixed former must lose the bound (negative control)')
    nc={l:v for l,v in rg['negative_controls'].items() if l in LINKS};need(not any(v['local_leg_guide_only']['bounded_within_allowance'] for v in nc.values()),'a local-leg guide alone must not bound the arch (negative control)')
    need(not all(v['without_former']['bounded_within_spare'] for v in nc.values()),'RG34 without its former must lose the bound (negative control)')
    need(not any(r['fits_under_cover'] for r in rg['r17'].values()),'R17 sensitivity: RG34 cap above the cover (expected)')
    s33a=data['s33_analysis']['R33'];need(s33a['failed']==['S3_lateral_retention'] and data['s33_report']['classification']['R33']=='CONDITIONAL','Stage33 committed results are preserved')
    rr=rg['geometry']
    ok=lambda k:'FEASIBLE_WITHIN_STATED_ASSUMPTIONS' if rg['criteria'][k] else 'INFEASIBLE';cv=rg['cover']
    results=[('R33 ideal-plane criteria S1-S12 (Stage33 re-run; S3 lateral retention still fails without RG34)','CONDITIONAL'),
        ('RG34 escape: closed lids and sleeves, closure gap below half the smallest OD',ok('T1_declared_closed_parts_and_closure_gap')),
        ('RG34 out-of-plane and rotation bound inside the channel (guide play)',ok('T2_single_end_states_inside_RG34_all_corners')),
        ('Free spans exit-to-sleeve with all slack (inextensible cable, set former, registration allowance)',ok('T5_free_spans_bounded_and_clear')),
        ('J-PWR to core: channel wall on the rear carrier (inter-carrier registration out of this chain)',ok('T3_parts_clear_K4')),
        ('J-SIG / J-PWR shared gap: walls between the channel interiors and free-span pairs',ok('T4_walls_fit_between_cable_interiors')),
        ('Every single-end 2.45-15 mm withdrawal at constant length inside RG34, at every corner (cut +/-, bow, registration in z)',ok('T2_single_end_states_inside_RG34_all_corners')),
        ('RG34 J-PWR cap under the rear cover (margin, RG34 tolerances, registration, K4)','FEASIBLE_WITHIN_STATED_ASSUMPTIONS' if cv['J-PWR']['meets_K4'] else 'INFEASIBLE'),
        ('RG34 J-SIG cap under the rear cover (margin, RG34 tolerances, registration, K4)','FEASIBLE_WITHIN_STATED_ASSUMPTIONS' if cv['J-SIG']['meets_K4'] else 'INFEASIBLE'),
        ('Both ends of one cable withdrawn with RG34 closed','INFEASIBLE'),
        ('Inter-carrier registration within the 1.0 mm requirement','UNKNOWN'),
        ('RG34 post strength (bending + torsion; 5-20 N meet, 50 N does not; root fixity and joints not evaluated)','CONDITIONAL'),
        ('Sliding friction vs free-span buckling','CONDITIONAL'),('Abrasion over repeated withdrawals','UNKNOWN'),('Finger/tool operability with one sleeve removed','UNKNOWN'),
        ('Front jack board removal with RG34 in place (J-PWR channel within K4 of the A01-jack M4 screwdriver column)','INFEASIBLE'),
        ('RG34 fit and removal path (post fastener access, lifting past neighbours)','UNKNOWN'),
        ('RG34 outside the reserved RV-ARCH/RV-ACCESS volumes (proposal)','CONDITIONAL'),
        ('Local-leg guide alone as whole-arch retention (negative control)','INFEASIBLE'),('RG34 without its former (negative control)','INFEASIBLE'),('RG34 with a fixed, not set, former (negative control)','INFEASIBLE'),
        ('R12 route radius vs 10x OD, inner-surface convention (Stage33)','FEASIBLE_WITHIN_STATED_ASSUMPTIONS'),
        ('R17 / 15x OD with RG34 (cap over the raised arch above the rear cover)','INFEASIBLE'),('R17 / 15x OD geometry without retention (Stage33 scan, preserved)','CONDITIONAL'),
        ('20x OD radius (Stage33 rear-cover failure, preserved)','INFEASIBLE'),
        ('J-SIG conductor currents (term-by-term budget; conditional maxima, no established maximum)','CONDITIONAL'),('J-PWR conductor currents (A01 term-by-term budget; conditional maxima, no established maximum)','CONDITIONAL'),
        ('Fault/short current on any conductor (no upstream limiting element)','UNKNOWN'),('Stage33 J-PWR current inputs as an A01 basis (Stage8 X1 values)','INFEASIBLE'),
        ('AWG26 contact rating, temperature rise and derating against conditional currents','CONDITIONAL'),
        ('AWG28/AWG30 GH contact current (no JST rating; not a demonstrated failure)','UNKNOWN'),('Wire selection','UNKNOWN'),
        ('F33 front-face large radius (Stage33, preserved)','UNKNOWN'),('B32 5 mm bends with every identified wire (Stage32/33, preserved)','INFEASIBLE'),('B32 uniform 1.282 mm bow (Stage32, preserved)','INFEASIBLE')]
    for _,v in results:need(v in CLASSES,'result class')
    lengths={l:{'design_length_proposal_mm':rr[l]['design_length_mm'],'cut_tolerance_mm':val(P,'cut_length_tolerance_mm'),'measured_or_cut_mm':None} for l in LINKS}
    model={'status':'DESIGN_STUDY_ONLY','approval':data['approval'],'parameters':{k:P[k] for k in data['input']['parameters']},'inherited_from':REL+'stage33/design-input.json',
        'rg34':{'spec':data['input']['rg34'],'geometry':public_geo(rr),'post':rg['post']},'design_lengths':lengths,'procedure':data['input']['procedure']}
    ana={'status':'DESIGN_STUDY_ONLY','R33_stage33_rerun':{k:res33[k] for k in ('criteria','failed','status','retention','core_40mm','cable_to_cable')},
        'RG34':{k:rg[k] for k in ('states','parts','free_spans','negative_controls','strength','friction','cover','access','reservations','r17','criteria','failed','status','closure')}}
    ledger={'status':'DESIGN_STUDY_ONLY','current':rg['current'],'wires':rg['wires']}
    sig=rg['cover']['J-SIG']
    report={'status':'DESIGN_STUDY_ONLY','recommendation':{'id':'R33+RG34','status':'CONDITIONAL_PENDING_COVER_REGISTRATION_AND_MEASUREMENT','rg34':rg['status'],'adopted':False,
            'requires':['an owner decision on the J-SIG cap vs rear cover conflict: a rear-cover inner face at z >= '+f"{sig['cover_needed_z_mm']:.2f}"+' (enclosure, proposal) or a J-SIG design length about '+f"{sig['design_length_cut_to_fit_mm']:.2f}"+' mm shorter (less than the inherited 10 mm service slack, proposal; its consequences are not evaluated)',
                'inter-carrier registration within registration_allowance_mm (UNKNOWN; enclosure cleats not designed)','owner decisions on the RG34 mount, RG34 outside the reserved volumes and removing RG34 before front jack board removal','the M34 mock-up measurements','a wire that meets every check (selection NULL)']},
        'classification':{'R33':'CONDITIONAL','RG34':'CONDITIONAL','F33':'UNKNOWN','B32':'INFEASIBLE'},
        'stage33_notes':['radius_headroom.largest_fitting_radius_mm (17) is the largest scanned radius that fits; radii between 17 and 22 were not scanned (review note on Stage33 round 2; Stage33 bytes unchanged)'],
        'results':[{'result':k,'class':v} for k,v in results],'design_lengths':lengths,'criteria':rg['criteria'],
        'assumptions':['the cable is inextensible and stays within its bundle envelope (JST maximum OD + 0.25 mm dressing)','cut length within +/- '+f"{val(P,'cut_length_tolerance_mm'):g}"+' mm of the design length',
            'A01-middle bow up to the uniform '+f"{rr['J-SIG']['bow_mm']:.3f}"+' mm case','inter-carrier registration within '+f"{val(P,'registration_allowance_mm'):g}"+' mm (requirement)',
            'RG34 profile and mounting tolerances '+f"{val(P,'guide_fab_tolerance_mm'):g}"+' / '+f"{val(P,'guide_mount_float_mm'):g}"+' mm','lids and sleeves closed on their stops; only one end of a cable withdrawn at a time',
            'each former set at assembly so the top leg rests on it (gap <= '+f"{val(P,'former_setting_resolution_mm'):g}"+' mm); both bend corners belong to that settable former, and the sleeves carry no inner arc','the legs below the former stay inside their sleeve bores; extra slack from in-bore leg offset is not added (about 0.06 mm by the independent review)'],
        'unresolved_degrees_of_freedom':['the J-SIG cap vs rear cover conflict (owner decision)','actual inter-carrier registration (enclosure cleats undesigned)','arch shape during service while a sleeve is removed (operator-held, not bounded)','actual free-span excursion under handling (bound computed, not measured)',
            'cable length after crimping','abrasion and drag over repeated withdrawals','finger access with one sleeve removed'],
        'measurements':[{'id':x['id'],'item':x['item'],'status':'NOT_RUN','value':None} for x in MEASUREMENTS],
        'decision_status':{'route':'STUDY_BASELINE (owner provisional); not adopted','header_moves':'PROVISIONAL_STUDY_BASELINE; not adopted','retention':'RG34 STUDY_DESIGN; not adopted','reservations':'PROVISIONAL (owner); RG34 extensions PROPOSAL_REQUIRES_OWNER_DECISION',
            'cable_lengths':'DESIGN_LENGTH_PROPOSAL; not measured, not cut','wire':'SELECTION_NULL; not selected','strength':'CALCULATED_CONDITIONALLY','currents':'CONDITIONAL; no established maximum',
            'stage33_jpwr_currents':'SUPERSEDED (X1 values); Stage33 bytes not changed','M-01':'NOT_RUN','M-09':'NOT_RUN','M-12':'NOT_RUN'},
        'two_sided_assembly_and_rerouting':two_sided(cand,res33),
        'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('approval.json','design-input.json','sources.json','README.md')]+[S33/n for n in ('design-input.json','sources.json','approval.json','analysis.json','report.json')]+[ROOT/'design/grid/placements.lock.json']
    files+=[Path(__file__).with_name(n) for n in ('test_stage34_arch_retention.py','stage33_large_radius.py','stage32_service_envelope.py','stage31_cable_entry_redesign.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return {'model':model,'analysis':ana,'ledger':ledger,'report':report,'rg':rg,'res33':res33,'cand':cand,'mech':mech,'P':P}


def two_sided(cand,res33):
    imp=res33['pcb_impact']
    return {'A01-middle':'gains GH header pads on its rear face: a second SMT side (or hand soldering) with its own stencil, placement and reflow pass; the GH headers would ride the second reflow on the first-side parts or the reverse order; process, fixture and cost UNCONFIRMED',
        'copper':'nets and pin identities unchanged; the pads move to the rear face (largest move '+', '.join(f"{k} {v['largest_plan_move_mm']:.1f} mm" for k,v in imp.items())+'); each net needs a via or a rear-side route to the new pads; routed copper is null in the draft and KiCad regeneration is NOT RUN',
        'courtyard':'rear-face courtyards must clear the rear-side obstacles (header sweeps already clear the DIN body and the mounts in Stage33); DRC NOT RUN',
        'carriers':'RG34 adds a post and fastening on crossmember:rear:0 (rear carrier change, proposal); the enclosure cleats must hold the inter-carrier registration within the allowance',
        'status':'IMPLICATIONS_ONLY; nothing changed in canonical CAD'}


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed: '+', '.join(sorted(set(changed)-MUTABLE)))
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage34/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


# ---------- rendering ----------
f2,esc,COLOR=s32.f2,s32.esc,s32.COLOR


def service_slack(b):
    """During a single-end withdrawal the arch top floats half the travel above the former: that slack can reach the opposite free span; the operator holds it (not bounded)."""
    P=b['P'];out={}
    for l,g in b['rg']['geometry'].items():
        ch=g['sleeve_bottom_z_mm']['local']-g['exit_z_mm']['local'];sl=val(P,'release_travel_mm')
        out[l]={'slack_mm':sl,'opposite_free_span_semi_minor_mm':r6(0.5*math.sqrt((ch+sl)**2-ch*ch))}
    return out


def render_md(b):
    rg=b['rg'];rep=b['report'];P=b['P'];yn=lambda x:'yes' if x else '**no**';geo=rg['geometry'];res33=b['res33']
    L=['# Stage34 whole-arch retention and wire/current evidence (generated)','','Design study only. Calculations on planning geometry and stated inputs; nothing is measured, and a clear envelope is not physical non-interference.','',
       '## Result','',f"R33 + RG34: **{rep['recommendation']['status']}**. RG34 bounds the whole arch under the stated assumptions at every tolerance corner, but its J-SIG cap does not fit under the rear cover ({rg['status']}). That conflict, inter-carrier registration, the mock-up measurements and the wire stay open. Nothing is adopted.",'',
       '| Criterion | Result |','|---|---|']+[f"| {k} | {yn(v)} |" for k,v in rg['criteria'].items()]
    L+=['','Stage33 ideal-plane criteria re-run: '+res33['status']+' (failed: '+', '.join(res33['failed'])+'); RG34 replaces the missing lateral retention.','','## Results by class','','| Result | Class |','|---|---|']+[f"| {r['result']} | {r['class']} |" for r in rep['results']]
    L+=['','## RG34 geometry','','One slot channel per arch, on the rear carrier (post on crossmember:rear:0). Coordinates in each arch plane: s along the arch from the local exit, n out of plane, z.','',
        '| Cable | Play c (mm) | Wall (mm) | Free span: exit → sleeve bottom z (local / middle) | Sleeve to block entry z | Former top (set range) | Cap / top z | Slack with set former / fixed former (mm) |','|---|---|---|---|---|---|---|---|']
    for l,g in geo.items():
        L.append(f"| {l} | {f2(g['c'])} | {f2(g['t'])} | {f2(g['exit_z_mm']['local'])} → {f2(g['sleeve_bottom_z_mm']['local'])} / {f2(g['exit_z_mm']['middle'])} → {f2(g['sleeve_bottom_z_mm']['middle'])} | {f2(g['block_entry_z_mm']['local'])} / {f2(g['block_entry_z_mm']['middle'])} | {f2(g['former_top_range_z_mm'][0])}–{f2(g['former_top_range_z_mm'][1])} | {f2(g['Zcap_inner'])} / {f2(g['Ztop'])} | {f2(g['slack_mm'])} / {f2(g['slack_fixed_former_mm'])} |")
    L+=['',f"- Sleeve bottoms and block entries include the {f2(val(P,'registration_allowance_mm'))} mm registration allowance in z; the cap includes the long-cable and registration corner.",f"- Each sleeve bottom leaves the fan-in plus an S-bend length ({f2(geo['J-SIG']['s_bend_length_mm'])} / {f2(geo['J-PWR']['s_bend_length_mm'])} mm) for a carrier registration error of {f2(val(P,'registration_allowance_mm'))} mm at the maker radius ({f2(geo['J-SIG']['required_radius_mm'])} / {f2(geo['J-PWR']['required_radius_mm'])} mm).",
        f"- Each block entry sits the 15 mm travel + fan-in + {f2(val(P,'grip_length_design_mm'))} mm grip above its exit, so a withdrawn housing's fan-in and the gripping fingers stay below RG34.",
        f"- Each middle sleeve encloses the whole of bend 2 and, at the low corner, the start of the top leg (up to {f2(geo['J-SIG']['s_off']['middle'])} mm in-plane). It has no inner arc: the bend-2 corner belongs to the settable former, which runs down through the sleeve zone.",
        f"- Outer gap between the J-SIG and J-PWR channels {f2(rg['parts']['outer_gap_between_channels_mm'])} mm (bridged by the channel joint); interior hulls {f2(rg['parts']['interior_hull_plan_gap_mm'])} mm apart in plan, enough for both walls.",
        f"- Closure gap ≤ {f2(rg['closure']['gap_max_mm'])} mm, below half of the smallest wire OD {f2(rg['closure']['smallest_wire_od_mm'])} mm: no conductor can enter or pass a parting line."]
    L+=['','## Movement budget','','Inside RG34 every point of a cable stays within the play c of its plane (walls), above the former and below the cap; rotation of the arch is bounded by the same walls. Between each housing exit and its sleeve the cable is free; the bound is the spheroid of every point a span of its length + all the slack can reach (inextensible cable), inflated by c + registration + RG34 tolerances + bundle radius.','',
        '| Cable | Span | Chord (mm) | Length with slack (mm) | Reach (semi-minor, mm) | Inflation (mm) | Tightest against | Robust spare (mm) |','|---|---|---|---|---|---|---|---|']
    for x in rg['free_spans']:
        sp=x['spheroids'][0];t=x['tightest'][0]
        L.append(f"| {x['link']} | {x['side']} | {f2(sp['chord_mm'])} | {f2(sp['length_mm'])} | {f2(x['semi_minor_mm'])} | {f2(sp['inflate_mm'])} | {t['against']} | {f2(t['robust_spare_mm'])} |")
    ss=service_slack(b);L.append('\nDuring a single-end withdrawal the arch top floats above the former, so up to '+'; '.join(f"{l} {f2(v['slack_mm'])} mm of slack (opposite free span reach {f2(v['opposite_free_span_semi_minor_mm'])} mm)" for l,v in ss.items())+' is held only by the operator: NOT bounded.')
    L+=['','## Clearances of RG34','','| Part | Nearest | Distance (mm) | Across carriers | Stack (mm) | Robust spare (mm) | K4 |','|---|---|---|---|---|---|---|']
    for r in rg['parts']['rows']:
        if r['obstacle']:L.append(f"| {r['part']} | {r['obstacle']} | {f2(r['distance_mm'])} | {'yes' if r['cross_carrier'] else 'no (rear carrier)'} | {f2(r['stack']['worst_case_mm'])} | {f2(r['robust_spare_mm'])} | {yn(r['meets_K4'])} |")
    for r in rg['parts']['service_only'][:2]:L.append(f"| {r['part']} | {r['obstacle']} (service only) | {f2(r['distance_mm'])} | yes | {f2(r['stack']['worst_case_mm'])} | {f2(r['robust_spare_mm'])} | {yn(r['meets_K4'])}: {r['use']} |")
    cv=rg['cover'];L+=['','Rear cover (margin + RG34 tolerances + registration, then K4):','','| Cable | RG34 top z | Margin + stack (mm) | Robust spare (mm) | K4 | Cover needed z | Or design length shorter by (mm) |','|---|---|---|---|---|---|---|']
    L+=[f"| {l} | {f2(v['rg34_top_z_mm'])} | {f2(v['margin_mm'])} + {f2(v['stack_mm'])} | {f2(v['robust_spare_mm'])} | {yn(v['meets_K4'])} | {f2(v['cover_needed_z_mm'])} | {f2(v['design_length_cut_to_fit_mm'])} |" for l,v in cv.items()]
    L+=['','## States inside RG34 (constant design length, every tolerance corner)','','Corners shift the arch against RG34: low = short cable + uniform bow + RG34 high by the registration allowance; high = long cable + RG34 low. The former is set at assembly for each.','',
        '| Cable | Corner | State | Travel (mm) | Top centreline z | Inside RG34 | Blocked by |','|---|---|---|---|---|---|---|']
    for r in rg['states']:
        if r['travel_mm'] in (0.0,15):L.append(f"| {r['link']} | {r['corner']} | {r['state']} | {r['travel_mm']:g} | {f2(r['top_centreline_z_mm'])} | {yn(r['admissible'])} | {', '.join(r['blocked_by']) or '–'} |")
    L+=['','## Negative controls','','| Cable | Control | Bound (mm) | Allowance (mm) | Bounded |','|---|---|---|---|---|']
    for l,v in rg['negative_controls'].items():
        if l not in LINKS:continue
        a=v['local_leg_guide_only'];w=v['without_former']
        L.append(f"| {l} | guide on the local leg only: reach of the rest of the arch / bucket-handle radius | {f2(a['reach_semi_minor_mm'])} / {f2(a['bucket_handle_radius_mm'])} | {f2(a['stage33_allowance_mm'])} | {yn(a['bounded_within_allowance'])} |")
        L.append(f"| {l} | RG34 without the former: local free span reach grows by | {f2(w['growth_mm'])} | {f2(w['tightest_spare_with_former_mm'])} | {yn(w['bounded_within_spare'])} |")
    fx=rg['negative_controls']['fixed_former']
    L.append('\nRG34 with a fixed (not set) former: free spans fail K4 ('+'; '.join(f"{k} {f2(v['robust_spare_mm'])} mm against {v['against']}" for k,v in fx['tightest'].items())+').')
    L.append('Both ends of one cable withdrawn with the lid closed: blocked by the cap at every corner (procedure: one end at a time).')
    s=rg['strength'];fr=rg['friction']
    L+=['','## Strength, friction, access','',f"- Post {s['post_section_mm'][0]:g} × {s['post_section_mm'][1]:g} mm; a load at the farthest RG34 point gives bending (lever {f2(s['lever_mm'])} mm) and torsion (arm {f2(s['torsion_arm_mm'])} mm) together: allowable {f2(s['allowable_load_N'])} N (von Mises); "+', '.join(f"{g['load_N']} N {'meets' if g['meets'] else 'fails'}" for g in s['grid'])+f". Not covered: {'; '.join(s['not_covered'])}.",
        f"- Drag upper bound "+', '.join(f"{l} {v['drag_upper_N']*1000:.1f} mN" for l,v in fr['links'].items())+f" against free-span buckling ≥ {min(x['buckling_load_N'] for v in fr['links'].values() for x in v['free_spans'].values()):.2f} N (strands-only {fr['most_flexible_construction']}); stiffness is not used for any bound. Abrasion NOT calculated (M34-04).",
        '- With one sleeve removed, the housing column up to the block entry is clear of rigid parts: '+'; '.join(f"{k} {f2(a['free_height_mm'])} mm, grip zone z {f2(a['grip_zone_z_mm'][0])}–{f2(a['grip_zone_z_mm'][1])}" for k,a in rg['access'].items())+'. Finger operation NOT DETERMINED.']
    L+=['','## Reserved volumes','']
    for r in rg['reservations']:L.append(f"- {r['link']}: RG34 half-thickness {f2(r['rg34_half_thickness_mm'])} mm vs RV-ARCH {f2(r['rv_arch_half_thickness_mm'])} mm (protrudes {f2(r['protrusion_mm'])} mm); occupies "+', '.join(sorted({x['reservation'] for x in r['rv_access_occupied']}))+' above the grip zones. '+r['status']+'.')
    r17=rg['r17'];L.append('\nR17 sensitivity: RG34 needs z '+' / '.join(f2(v['needed_z_mm']) for v in r17.values())+' (J-SIG / J-PWR) against the cover at 105: does not fit. The Stage33 R17 geometry without retention stays CONDITIONAL and 20× stays INFEASIBLE.')
    cur=b['ledger']['current']
    L+=['','## Current ledger (A01; replaces the Stage33 X1-derived J-PWR inputs)','','Each value is the generator\'s sum of recorded terms (V/R from the A01 specification, quiescent and bias currents from the evidence facts); ledger.json lists every term with its basis and sources. Classes: typical (5 V signals) / conditional maximum (stated conditions) / conditional fault case / established maximum (maker-backed limit). No conductor has an established maximum.','',
        '| Cable | Pin | Net | Typical (mA) | Conditional max (mA) | Fault case (mA) | Established | Of 0.5 A project limit |','|---|---|---|---|---|---|---|---|']
    for l,rows in cur['links'].items():
        for r in rows:L.append(f"| {l} | {r['pin']} | {r['net']} | {r['typical_A']*1000:.4g} | {r['conditional_max_A']*1000:.4g} | {f"{r['conditional_fault_A']*1000:.4g}" if r['conditional_fault_A'] else '–'} | {r['established_status'].split(':')[0]} | {r['fraction_of_project_limit']*100:.2f} % |")
    sp=cur['stage33_superseded'];v=sp['stage33_values']
    L+=['',f"Stage33 used +12V {v['j_pwr_conductor_current_max_A']['+12V']*1000:.2f} / -12V {v['j_pwr_conductor_current_max_A']['-12V']*1000:.2f} / +5V {v['j_pwr_conductor_current_max_A']['+5V']*1000:.3f} mA and an AGND bound of {v['j_pwr_agnd_return_bound_A']*1000:.2f} mA. {sp['reason']}",'',f"Fault: {cur['fault']}."]
    w=b['ledger']['wires'];L+=['','## Wire ledger','',f"Selection: {w['selection_status']}.",'','| Wire | AWG | OD (mm) | Fails | Unknown (J-PWR) | Conditional (J-PWR) |','|---|---|---|---|---|---|']
    for x in w['wires']:
        pc=x['per_cable'];fails=sorted(set(pc['J-SIG']['failed'])|set(pc['J-PWR']['failed']))
        L.append(f"| {x['mpn']} | {x['awg']} | {x['od_range_mm'][0]}–{x['od_range_mm'][1]} | {', '.join(fails) or 'none'} | {', '.join(pc['J-PWR']['unknown']) or 'none'} | {', '.join(pc['J-PWR']['conditional']) or 'none'} |")
    L+=['']+[f"- {k}: {v}" for k,v in w['basis'].items()]+['','Smallest questions or measurements:','']+[f"{i}. {q}" for i,q in enumerate(w['questions'],1)]
    ts=rep['two_sided_assembly_and_rerouting'];L+=['','## Two-sided assembly and re-routing (implications only)','']+[f"- **{k}**: {v}" for k,v in ts.items() if k!='status']
    L+=['','## Assumptions','']+[f"- {a}" for a in rep['assumptions']]+['','## Unresolved degrees of freedom','']+[f"- {a}" for a in rep['unresolved_degrees_of_freedom']]
    for k_,v in b['model']['procedure'].items():L+=['',f'**{k_}**','']+[f'{i}. {x}' for i,x in enumerate(v,1)]
    L+=['','## Measurements still NOT RUN (minimal unpowered mock-up plan)','']+[f"- **{m['id']}** {m['item']}." for m in rep['measurements']]
    return '\n'.join(L)+'\n'


def svg_open(title,W,H,legend):return s33.svg_frame(title,W,H,legend)


def render_plan(b):
    rg=b['rg'];cand=b['cand'];W,H=1010,620;out=svg_open('Stage34 R33 + RG34 plan (design study; modelled envelopes, not physical clearance)',W,H,
        ['Blue J-SIG, red J-PWR: arch centrelines (installed). Filled outlines: RG34 channels and sleeves (outer walls). Dark: post on crossmember:rear:0. Dashed black: core box with the 40 mm withdrawal.',
         'Circles: free-span reach (spheroid semi-minor + inflation) at each housing exit. Grey: designed parts above z 40; dotted: screwdriver columns.'])
    ox,oy,sc=20,70,6.4;x0,y0,x1,y1=195,138,300,190
    T=lambda p:(ox+(p[0]-x0)*sc,oy+(p[1]-y0)*sc)
    out.append(f'<rect x="{ox}" y="{oy}" width="{(x1-x0)*sc:.1f}" height="{(y1-y0)*sc:.1f}" fill="none" stroke="#999"/>')
    for v in range(200,301,20):out.append(f'<text x="{ox+(v-x0)*sc-8:.1f}" y="{oy+(y1-y0)*sc+12:.1f}" fill="#666">x {v}</text>')
    for v in range(140,191,10):out.append(f'<text x="{ox+(x1-x0)*sc+3:.1f}" y="{oy+(v-y0)*sc+3:.1f}" fill="#666">y {v}</text>')
    def poly(pts,st):out.append('<polygon points="'+' '.join(f"{x:.1f},{y:.1f}" for x,y in (T(p) for p in pts))+f'" {st}/>')
    for o in cand['obs']:
        if o['kind']=='unknown_depth' or o['hi'][2]<=40 or o['id'].startswith(('body:','core-extraction')):continue
        lo,hi=o['lo'],o['hi'];st=s33.style(o)
        if hi[0]<x0 or lo[0]>x1 or hi[1]<y0 or lo[1]>y1:continue
        poly([[max(lo[0],x0),max(lo[1],y0)],[min(hi[0],x1),max(lo[1],y0)],[min(hi[0],x1),min(hi[1],y1)],[max(lo[0],x0),min(hi[1],y1)]],st)
    env=s31.core_envelope(cand['mech']);poly([[env['lo'][0],env['lo'][1]],[x1,env['lo'][1]],[x1,y1],[env['lo'][0],y1]],'fill="none" stroke="#111" stroke-width="1" stroke-dasharray="6,3"')
    for l in LINKS:
        for p in rg['geometry'][l]['parts']:poly(p['poly'],f'fill="{COLOR[l]}" fill-opacity="{0.10 if p["kind"]=="channel" else 0.25}" stroke="{COLOR[l]}" stroke-width="0.8"')
        pts=[T(p) for p in cand['routes'][l]['dense'][::4]];out.append('<polyline points="'+' '.join(f"{x:.1f},{y:.1f}" for x,y in pts)+f'" fill="none" stroke="{COLOR[l]}" stroke-width="2"/>')
    poly(rg['post']['poly'],'fill="#333" fill-opacity="0.7" stroke="#000"')
    for txt,xy in (('core + 40 mm',[env['lo'][0]+20,env['lo'][1]+6]),('RG34 post',[rg['post']['poly'][0][0]-1,rg['post']['poly'][0][1]-1]),('crossmember:rear:0',[262,173.4]),('A01-middle (rear face z 50)',[262,143]),('A01-jack',[197,186]),
            ('tool col. jack M4',[230,184]),('tool col. middle M1',[226,141.5])):
        X,Y=T(xy);out.append(f'<text x="{X:.1f}" y="{Y:.1f}" fill="#333" font-size="8">{esc(txt)}</text>')
    for x in rg['free_spans']:
        sp=x['spheroids'][0];c=T(sp['xy']);out.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{(x["semi_minor_mm"]+sp["inflate_mm"])*sc:.1f}" fill="none" stroke="{COLOR[x["link"]]}" stroke-dasharray="2,2"/>')
    y=oy+(y1-y0)*sc+34
    for l,g in rg['geometry'].items():
        out.append(f'<text x="20" y="{y}" fill="{COLOR[l]}">{l}: channel play {g["c"]:g} mm, walls {g["t"]:g} mm, top z {g["Ztop"]:.1f}; sleeves z {g["sleeve_bottom_z_mm"]["local"]:.1f}–{g["block_entry_z_mm"]["local"]:.1f} (local) and {g["sleeve_bottom_z_mm"]["middle"]:.1f}–{g["block_entry_z_mm"]["middle"]:.1f} (middle); slack {g["slack_mm"]:g} mm with the former set at assembly</text>');y+=13
    out.append(f'<text x="20" y="{y}">Status {esc(b["report"]["recommendation"]["status"])}; RG34 {esc(rg["status"])}; physical NOT_RUN</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'


def section_panel(b,out,l,ox,oy,sc,states,title):
    """One arch plane, unfolded: s horizontal, z up. Former, cap, end walls, sleeves, free-span reach and the chosen states."""
    rg=b['rg'];g=rg['geometry'][l];f=frame(b['cand'],l);D=f['D'];P=b['P'];s0,s1,z0,z1=-8,D+8,38,112
    T=lambda s,z:(ox+(s-s0)*sc,oy+(z1-z)*sc)
    out.append(f'<text x="{ox}" y="{oy-6}" font-weight="bold" fill="{COLOR[l]}">{esc(title)}</text><rect x="{ox}" y="{oy}" width="{(s1-s0)*sc:.1f}" height="{(z1-z0)*sc:.1f}" fill="none" stroke="#999"/>')
    for z in range(40,111,10):X,Y=T(s1,z);out.append(f'<text x="{X+3:.1f}" y="{Y+3:.1f}" fill="#666">z {z}</text>')
    def rect(sa,sb,za,zb,st):
        A=T(sa,zb);B=T(sb,za);out.append(f'<rect x="{A[0]:.1f}" y="{A[1]:.1f}" width="{B[0]-A[0]:.1f}" height="{B[1]-A[1]:.1f}" {st}/>')
    a=g['r']+g['c']+g['t'];R=g['R'];Zl=g['Z0'];r=g['r']
    rect(-a,D+a,g['former_bottom_z_mm']-g['t'],g['Ztop'],'fill="#f3f3f3" stroke="#888" stroke-width="0.6"')
    for side,(sa,sb) in (('local',(-a,a)),('middle',(D-a-g['s_off']['middle'],D+a))):
        rect(sa,sb,g['block_entry_z_mm'][side],g['Ztop'],'fill="#f3f3f3" stroke="#888" stroke-width="0.6"')
        rect(sa,sb,g['sleeve_bottom_z_mm'][side],g['block_entry_z_mm'][side],'fill="none" stroke="#555" stroke-width="0.8" stroke-dasharray="4,2"')
    rect(-g['c']-r,D+g['c']+r,g['former_bottom_z_mm'],g['Zcap_inner'],'fill="#ffffff" stroke="none"')
    pts=[]
    for k in range(0,91,5):th=math.radians(k);pts.append((R-(R-r)*math.cos(th),Zl-R+(R-r)*math.sin(th)))
    for k in range(90,-1,-5):th=math.radians(k);pts.append((D-R+(R-r)*math.cos(th),Zl-R+(R-r)*math.sin(th)))
    pts+=[(D-r,g['former_bottom_z_mm']),(r,g['former_bottom_z_mm'])]
    out.append('<polygon points="'+' '.join(f"{x:.1f},{y:.1f}" for x,y in (T(*p) for p in pts))+'" fill="#9aa5b1" fill-opacity="0.6" stroke="#4a5562"/>')
    A=T(R,g['former_top_range_z_mm'][0]);B=T(D-R,g['former_top_range_z_mm'][0]);out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#4a5562" stroke-dasharray="1,2"/>')
    A=T(-g['c']-r,g['Zcap_inner']);B=T(D+g['c']+r,g['Zcap_inner']);out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#333" stroke-width="1.2"/>')
    A=T(s0,105);B=T(s1,105);out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#666" stroke-dasharray="1,2"/><text x="{A[0]+3:.1f}" y="{A[1]-2:.1f}" fill="#555">rear cover z 105</text>')
    for x in rg['free_spans']:
        if x['link']!=l:continue
        sp=x['spheroids'][0];s=0.0 if x['side']=='local' else D;C=T(s,sp['zc'])
        out.append(f'<ellipse cx="{C[0]:.1f}" cy="{C[1]:.1f}" rx="{(sp["B"]+sp["inflate_mm"])*sc:.1f}" ry="{(sp["A"]+sp["inflate_mm"])*sc:.1f}" fill="none" stroke="{COLOR[l]}" stroke-dasharray="2,2"/>')
    for name,tl,tm,dash,col in states:
        c=s33.constant_length(b['cand'].get('geo'),l,b['cand']['lengths'][l]['design_length_mm'],tl,tm,P)
        pp=[T(*local(f,p)[0::2]) for p in c['route']['dense'][::2]]
        out.append('<polyline points="'+' '.join(f"{x:.1f},{y:.1f}" for x,y in pp)+f'" fill="none" stroke="{col}" stroke-width="1.4" {dash}/>')
        for side,t in (('local',tl),('middle',tm)):
            if t:s=0.0 if side=='local' else D;e=g['exit_z_mm'][side];rect(s-4,s+4,e-7.3+t,e+t,f'fill="none" stroke="{col}" {dash}')


def render_sections(b):
    W,H=1010,860;out=svg_open('Stage34 arch-plane sections: RG34 channel, former, sleeves and free spans (installed)',W,H,
        ['Unfolded section in each arch plane (s along the arch, z up). Light grey: RG34 block outline; dashed boxes: removable sleeves; dark grey: former at its nominal set height (dotted: lowest setting); thick line: cap.',
         'Dashed ellipses: free-span reach (all slack in one span, inflated). The cable may touch the walls, former and cap; it cannot leave the channel.'])
    for i,l in enumerate(LINKS):section_panel(b,out,l,20+i*500,70,3.9 if l=='J-PWR' else 5.4,[('installed',0.0,0.0,'',COLOR[l])],l+' installed')
    cross_panel(b,out,20,560)
    out.append('</svg>');return '\n'.join(out)+'\n'


def cross_panel(b,out,ox,oy):
    """Cut normal to each arch through the middle of its top leg (n horizontal, z up): walls, play, former, cap; the cable may sit anywhere in the white slot."""
    sc=14.0;out.append(f'<text x="{ox}" y="{oy-6}" font-weight="bold">Cut normal to each arch at mid top leg (scale x{sc:g}; n across the arch plane, z up)</text>')
    for i,l in enumerate(LINKS):
        g=b['rg']['geometry'][l];r,c,t=g['r'],g['c'],g['t'];x0=ox+60+i*480;z0=g['former_top_range_z_mm'][0]-3;z1=g['Ztop']+1
        T=lambda n,z:(x0+n*sc,oy+(z1-z)*sc)
        def rect(na,nb,za,zb,st):
            A=T(na,zb);B=T(nb,za);out.append(f'<rect x="{A[0]:.1f}" y="{A[1]:.1f}" width="{B[0]-A[0]:.1f}" height="{B[1]-A[1]:.1f}" {st}/>')
        rect(-(r+c+t),-(r+c),z0,g['Ztop'],'fill="#9aa5b1" stroke="#4a5562"');rect(r+c,r+c+t,z0,g['Ztop'],'fill="#cfd6dd" stroke="#4a5562" stroke-dasharray="3,2"')
        rect(-(r+c),r+c,g['Zcap_inner'],g['Ztop'],'fill="#9aa5b1" stroke="#4a5562"');rect(-(r+c),r+c,z0,g['Z0']-r,'fill="#9aa5b1" fill-opacity="0.6" stroke="#4a5562"')
        C=T(0,g['Z0']);out.append(f'<circle cx="{C[0]:.1f}" cy="{C[1]:.1f}" r="{r*sc:.1f}" fill="{COLOR[l]}" fill-opacity="0.35" stroke="{COLOR[l]}"/>')
        C=T(0,g['Z0']+7.5);out.append(f'<circle cx="{C[0]:.1f}" cy="{C[1]:.1f}" r="{r*sc:.1f}" fill="none" stroke="{COLOR[l]}" stroke-dasharray="3,2"/>')
        X=T(r+c+t,z0)[0]+12
        for k,txt in enumerate((l,f'play {c:g} mm each side; walls {t:g} mm (lid dashed)',f'former top z {g["Z0"]-r:.1f} (set at assembly)',f'cap underside z {g["Zcap_inner"]:.1f}; dashed circle: raised 7.5 mm')):
            out.append(f'<text x="{X:.1f}" y="{oy+14+14*k:.1f}" fill="{COLOR[l] if k==0 else "#333"}">{esc(txt)}</text>')


def render_service(b):
    P=b['P'];t=val(P,'release_travel_mm');W,H=1010,1080
    out=svg_open('Stage34 service states inside RG34 (one end withdrawn 15 mm; that sleeve removed)',W,H,
        ['Solid: installed. Dashed: middle housing withdrawn 15 mm (middle sleeve removed). Dotted: local housing withdrawn 15 mm (local sleeve removed). Red dash-dot: both ends withdrawn: blocked by the cap (not allowed with the lid closed).',
         'Constant design length: the arch rises half the travel inside the channel. Withdrawn housings outlined.'])
    for i,l in enumerate(LINKS):
        section_panel(b,out,l,20+i*500,80,3.9 if l=='J-PWR' else 5.4,[('installed',0.0,0.0,'',COLOR[l]),('middle',0.0,t,'stroke-dasharray="5,3"',COLOR[l]),('local',t,0.0,'stroke-dasharray="1,2"',COLOR[l])],l+' single-end withdrawals')
        section_panel(b,out,l,20+i*500,580,3.9 if l=='J-PWR' else 5.4,[('both',t,t,'stroke-dasharray="6,2,1,2"','#c00')],l+' both ends (blocked by the cap)')
    out.append('</svg>');return '\n'.join(out)+'\n'


def outputs(b):
    return {'model.json':dump(b['model']),'analysis.json':dump(b['analysis']),'ledger.json':dump(b['ledger']),'report.json':dump(b['report']),'summary.md':render_md(b),
        'plan-rg34.svg':render_plan(b),'arch-sections.svg':render_sections(b),'service-sections.svg':render_service(b)}


def run(data,preserve=True):
    b=build(data,preserve);return b,outputs(b)


def check_outputs(bodies):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage34-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            # Stage33 bytes are immutable from BASE; its own replay of Stage32 runs there too.
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage33_large_radius.py','--check','--check-history','--check-review'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage33_large_radius.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage33 source checkpoint (generator, history, review binding, tests normal and -O)')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage34/'+n for n in GENERATED}
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
    print('PASS Stage34 source checks: R33 '+b['report']['recommendation']['status']+'; RG34 '+b['rg']['status']+'; wire selection NULL; physical/native NOT RUN')


if __name__=='__main__':main()
