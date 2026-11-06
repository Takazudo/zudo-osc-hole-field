"""Stage35 interval screens and fail-closed service audit; no hardware qualification."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import stage34_arch_retention as s34

s33, s32, s31 = s34.s33, s34.s32, s34.s31
ROOT = Path(__file__).resolve().parents[3]
REL = 'design/architecture-278/implementation/'
OUT = ROOT / REL / 'stage35'
BASE = '9d9aa404a27dc7e5b8476e0d9f826fc44c517fbe'
MUTABLE = {REL+'README.md', REL+'WORK.md', 'scripts/architecture278/implementation/check_source.py'}
SCRIPTS = {'scripts/architecture278/implementation/'+n for n in ('stage35_cover_service.py', 'test_stage35_cover_service.py')}
GENERATED = ('analysis.json', 'summary.md')
need, val = s34.need, s34.val


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n'


def context():
    data = s34.load()
    P, T, rules = s34.validate_inputs(data)
    mech = s33.s30.stage29_current()[0]['mech']
    cand = s33.build_r33(data['s33']['input']['candidates']['R33'], data['s33'], mech, P)
    return data, P, T, rules, cand


def exact_top(length, distance, a, b, radius, housings):
    # Two quarter circles replace four R of rectilinear length by pi R.
    return (length-housings-distance+a+b+(4-math.pi)*radius)/2


def minimum_length(distance, a, b, radius, fan, housings):
    return distance+abs(a-b)+2*fan+(math.pi-2)*radius+housings


def interval(cand, P, T, link, mode):
    """Continuous necessary interval for the two-quarter-circle parallel-exit arch family.

    Datum modes are deliberately separate. The endpoint box is a sensitivity,
    not a measured tolerance allocation or a proof for a guided S-bend route.
    """
    a, b = [cand['geo'][ref]['exit_mm'] for ref in s34.ENDS[link]]
    D = math.dist(a[:2], b[:2]); R = val(P, 'route_radius_mm')
    f = s33.fan_in(P, link)['length_mm']; r = s33.bundle(P, link)['round_radius_mm']
    travel = val(P, 'release_travel_mm'); cut = val(P, 'cut_length_tolerance_mm')
    e = val(P, 'registration_allowance_mm'); h = 2*val(P, 'gh_mated_height_mm')
    x0,y0,x1,y1 = cand['mech']['boards']['A01-middle']['outline_mm']
    bow = T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)
    extra = r+val(P,'guide_clearance_mm')+val(P,'guide_wall_mm')
    cover_budget = (val(P,'placement_margin_mm')+val(P,'guide_fab_tolerance_mm')+
                    val(P,'guide_mount_float_mm')+e+val(P,'robust_spare_mm'))
    cover = val(P,'enclosure_rear_inner_z_mm')
    if mode == 'inherited_height_screen':
        # Replicates Stage34's translating arch corners; no endpoint registration proof.
        low_dz = cut/2+bow/2+e
        lower = minimum_length(D,a[2],b[2]+travel,R,f,h)+2*low_dz
        top_extra = cut/2+e
        upper = 2*(cover-extra-cover_budget-top_extra)-(-h-D+a[2]+b[2]+travel+(4-math.pi)*R)
        assumptions = 'Stage34 whole-arch height shifts; shifted exits are NOT re-solved. Necessary height/lead screen only.'
    elif mode in ('endpoint_box_downward_bow', 'endpoint_box_signed_bow'):
        # A subset of errors: each exit +/- e along its nominal arch and z, n=0.
        # Unknown rotations and out-of-plane errors cannot improve certification.
        positive_bow = bow if mode.endswith('signed_bow') else 0.0
        lower = minimum_length(D+2*e,a[2]-e,b[2]+e+positive_bow+travel,R,f,h)+cut
        upper = 2*(cover-extra-cover_budget)-(-h-(D-2*e)+a[2]+b[2]+2*e+positive_bow+travel+(4-math.pi)*R)-cut
        assumptions = ('Independent endpoint +/-1 mm s,z box, n=0; relative to rear carrier, NOT a measured/pairwise radial bound. '
                       + ('Middle bow +/- diagonal allowance.' if positive_bow else 'Middle bow only toward carrier as historical source model.'))
    else:
        raise ValueError('unknown datum mode')
    return {'mode':mode,'link':link,'lower_design_length_mm':lower,'upper_design_length_mm':upper,
            'interval_nonempty':lower<=upper,'width_mm':upper-lower,'assumptions':assumptions,
            'cover_inner_z_mm':cover,'minimum_deeper_cover_in_this_family_mm':max(0,(lower-upper)/2),
            'D_mm':D,'radius_mm':R,'fan_in_mm':f,'bow_mm':bow,'cut_tolerance_mm':cut,
            'physical_or_cut_length_mm':None,'full_service_solution':False}


def candidate_at(cand, P, sig_length):
    out = copy.deepcopy(cand)
    out['lengths']['J-SIG']['design_length_mm'] = sig_length
    for l in s34.LINKS:
        route = s33.constant_length(out['geo'],l,out['lengths'][l]['design_length_mm'],0,0,P)
        need(route['route'] is not None, 'installed route has insufficient length')
        out['installed'][l] = route
        out['routes'][l] = route['route']
    return out


def continuous_states(cand, P, T):
    """Extrema are at corners: Z and straight lengths are affine in length, z and travel."""
    out=[]
    for l in s34.LINKS:
        a,b=[cand['geo'][ref]['exit_mm'] for ref in s34.ENDS[l]]
        D=math.dist(a[:2],b[:2]);R=val(P,'route_radius_mm');h=2*val(P,'gh_mated_height_mm')
        fan=s33.fan_in(P,l)['length_mm'];r=s33.bundle(P,l)['round_radius_mm']
        L=cand['lengths'][l]['design_length_mm'];cut=val(P,'cut_length_tolerance_mm')
        x0,y0,x1,y1=cand['mech']['boards']['A01-middle']['outline_mm'];bow=T['pcb_bow_fraction']['value']*math.hypot(x1-x0,y1-y0)
        for side in ('installed','local','middle'):
            rows=[]
            for dl in (-cut,cut):
                for beta in (-bow,0.0,bow):
                    for t in ((0.0,) if side=='installed' else (0.0,15.0)):
                        za=a[2]+(t if side=='local' else 0);zb=b[2]+beta+(t if side=='middle' else 0)
                        z=exact_top(L+dl,D,za,zb,R,h)
                        rows.append({'cut_delta_mm':dl,'middle_bow_mm':beta,'travel_mm':t,'top_z_mm':z,
                                     'local_straight_mm':z-R-za,'middle_straight_mm':z-R-zb})
            out.append({'link':l,'state':side,'length_mm':L,'corners':rows,
                        'top_z_interval_mm':[min(x['top_z_mm'] for x in rows),max(x['top_z_mm'] for x in rows)],
                        'bottom_envelope_z_mm':min(a[2],b[2]-bow)-r,
                        'minimum_straight_mm':min(min(x['local_straight_mm'],x['middle_straight_mm']) for x in rows),
                        'required_fan_in_mm':fan,'radius_mm':R,'required_bundle_radius_mm':s33.required_radius(10,1,P,l)['surface'],
                        'straight_pass':all(min(x['local_straight_mm'],x['middle_straight_mm'])>=fan for x in rows),
                        'scope':'continuous axial 0..15 travel, cut +/-0.5 and signed bow; endpoint/carrier error handled separately, not a guided shape proof'})
    return out


def occupied_obstacles(cand, ceiling):
    out=copy.deepcopy(s34.obstacle_prisms(cand))
    for o in out:
        if o['kind'] in ('unknown_depth','assumed_height'):
            o['z'][1]=max(o['z'][1],ceiling+100)
    return out


def gap_status(o, spare, k4):
    if spare>=k4:return 'CLEAR_OF_THIS_BOUND'
    return 'UNKNOWN_OCCUPANCY' if o['kind'] in ('unknown_depth','assumed_height') else 'NOT_CERTIFIED'


def access_screen(cand, geo, post, P, T, rules):
    out=[];margin=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm')
    for l in s34.LINKS:
        for side,ref in zip(s34.SIDES,s34.ENDS[l]):
            bx=cand['geo'][ref]['box_mm'];g=geo[l]
            col={'poly':[[bx[0],bx[1]],[bx[2],bx[1]],[bx[2],bx[3]],[bx[0],bx[3]]],
                 'z':[g['exit_z_mm'][side],g['block_entry_z_mm'][side]]}
            obs=occupied_obstacles(cand,col['z'][1])+[post]+[p for ll in s34.LINKS for p in geo[ll]['parts']
                if not(ll==l and p.get('removable_for')==side)]
            rows=[]
            for o in obs:
                if s34.own(o,l,side):continue
                st=s34.stack_for(o['id'],P,T,rules,g['bow_mm'],not o['id'].startswith(s34.REAR))
                spare=s34.prism_dist(col,o)-margin-st['worst_case_mm']
                rows.append({'obstacle':o['id'],'robust_spare_mm':spare,'status':gap_status(o,spare,k4)})
            out.append({'end':ref,'column':col,'examined':len(rows),'tightest':sorted(rows,key=lambda x:x['robust_spare_mm'])[:5],
                        'blockers':[r for r in rows if r['status']!='CLEAR_OF_THIS_BOUND'],
                        'status':'NOT_CERTIFIED','finger_and_tool_shapes':'UNKNOWN; housing projection is a necessary minimum column only'})
    return out


def conservative_free_spans(cand, geo, post, P, T, rules):
    # Stage34 constructs the spheroids; Stage35 independently audits their entire occupancy.
    inherited=s34.free_spans(cand,geo,post,P,T,rules)
    out=[];margin=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm')
    for item in inherited:
        l,side=item['link'],item['side'];g=geo[l];rows=[]
        for sp in item['spheroids']:
            ceiling=sp['zc']+sp['A']+sp['inflate_mm']
            obs=occupied_obstacles(cand,ceiling)+[post]+[p for ll in s34.LINKS if ll!=l for p in geo[ll]['parts']]
            for o in obs:
                if s34.own(o,l,side):continue
                st=s34.stack_for(o['id'],P,T,rules,g['bow_mm'],False)['worst_case_mm']
                # Inflation already includes registration and guide tolerances; do not double count them.
                st-=val(P,'guide_fab_tolerance_mm')+val(P,'guide_mount_float_mm')
                dxy=s34.point_poly_dist(sp['xy'],o['poly'])
                planar_lower=max(0,dxy-sp['B'])-sp['inflate_mm']
                if planar_lower-margin-st>=k4:
                    distance=planar_lower;method='conservative planar lower bound'
                else:
                    n=4000 if dxy>sp['B']+5 else 20000
                    error=math.pi*max(sp['A'],sp['B'])/(2*n)
                    distance=s34.spheroid_prism_dist(sp,o)-error
                    method='meridian sample minus Lipschitz discretization bound'
                spare=distance-margin-st
                rows.append({'obstacle':o['id'],'robust_spare_lower_bound_mm':spare,
                             'status':gap_status(o,spare,k4),'method':method})
        out.append({'link':l,'side':side,'spheroids':item['spheroids'],'examined':len(rows),
                    'tightest':sorted(rows,key=lambda x:x['robust_spare_lower_bound_mm'])[:5],
                    'blockers':[r for r in rows if r['status']!='CLEAR_OF_THIS_BOUND'],
                    'status':'NOT_CERTIFIED' if any(r['status']!='CLEAR_OF_THIS_BOUND' for r in rows) else 'CLEAR_OF_LISTED_OBSTACLE_BOUNDS',
                    'inherited_cable_pair_screen':{'scope':'historical pair distances only; no hardware qualification',
                        'tightest':item['tightest'],'all_reported_bounds_meet_K4':item['meets_K4']}})
    return out


def all_obstacle_rows(cand, geo, post, P, T, rules, lift=False):
    """No proximity cull; unknown-depth solids extend to the sweep ceiling, not a free default plane."""
    obs=occupied_obstacles(cand,300)
    ubow=geo['J-SIG']['bow_mm'];margin=val(P,'placement_margin_mm');k4=val(P,'robust_spare_mm')
    parts=[p for l in s34.LINKS for p in geo[l]['parts']]+[post]
    rows=[]
    for part in parts:
        pr=copy.deepcopy(part)
        if lift:
            # Full vertical extraction prism until the lowest point is above the cover.
            pr['z'][1]+=max(0,105+margin-pr['z'][0])
        for ob in obs:
            o=copy.deepcopy(ob)
            if o['kind']=='unknown_depth':o['z'][1]=max(o['z'][1],pr['z'][1]+100)
            exclusion=None
            if part['kind']=='post' and o['id']=='crossmember:rear:0':exclusion='intentional root contact; fastening/removal geometry UNKNOWN'
            elif part.get('removable_for') and s34.own(o,part['link'],part['removable_for']):exclusion='own connector sweep: sleeve removed before withdrawal'
            d=s34.prism_dist(pr,o)
            st=s34.stack_for(o['id'],P,T,rules,ubow,not o['id'].startswith(s34.REAR))
            spare=d-margin-st['worst_case_mm']
            kind='UNKNOWN_OCCUPANCY' if o['kind'] in ('unknown_depth','assumed_height') else 'KNOWN_MODEL'
            rows.append({'part':part['id'],'obstacle':o['id'],'kind':kind,'distance_mm':d,'robust_spare_mm':spare,
                         'meets_K4_geometry':spare>=k4,'exclusion':exclusion,
                         'service_reservation':o['id'].startswith(('tool:','release:'))})
    by_obstacle={}
    for row in rows:
        key=row['obstacle']
        if key not in by_obstacle or row['robust_spare_mm']<by_obstacle[key]['robust_spare_mm']:
            by_obstacle[key]=row
    return {'examined_pair_count':len(rows),'minimum_by_obstacle':list(by_obstacle.values()),
            'unexcluded_below_K4':[r for r in rows if not r['meets_K4_geometry'] and not r['exclusion']],
            'scope':'13 retention prisms against every inherited obstacle; union of vertical translation when removal=true; joints/lid lateral opening and enclosure aperture UNKNOWN'}


def support_screen(cand, geo, post, P, T, rules):
    out={}
    for mode in ('fixed_former_withdrawal','tracking_former_proposal'):
        g=copy.deepcopy(geo)
        for l in s34.LINKS:
            # Envelope superset: any one open sleeve, all residual slack at either span.
            g[l]['slack_mm']=15.5 if mode=='fixed_former_withdrawal' else .5
            g[l]['sleeve_bottom_z_mm']=dict(g[l]['block_entry_z_mm'])
        spans=conservative_free_spans(cand,g,post,P,T,rules)
        out[mode]={'span_bounds':spans,'all_reported_bounds_meet_K4':all(x['status']=='CLEAR_OF_LISTED_OBSTACLE_BOUNDS' for x in spans),
                   'status':'NOT_CERTIFIED','reason':'Bounding-volume screen only; open sleeve, tracking mechanism, joints and moving guide geometry are not established.'}
    return out


def sources():
    paths=[str(p.relative_to(ROOT)) for p in (ROOT/REL/'stage34').iterdir() if p.is_file()]
    paths += [str(p.relative_to(ROOT)) for p in OUT.iterdir() if p.name in ('README.md','design-input.json','mock-up.md')]
    paths += sorted(SCRIPTS|MUTABLE)
    return {p:digest(ROOT/p) for p in sorted(paths)}


def build():
    inp=json.loads((OUT/'design-input.json').read_text())
    need(inp['status']=='DESIGN_STUDY_ONLY' and not inp['adopted'],'study is not adopted')
    need(inp['wire_selection'] is None,'wire stays unresolved')
    need(inp['trial_interval_mm']==[129.0,130.5],'fixed reviewable diagnostic interval')
    data,P,T,rules,base=context()
    need(val(P,'release_travel_mm')==15 and val(P,'robust_spare_mm')==.15 and val(P,'placement_margin_mm')==.5,'thresholds preserved')
    intervals=[interval(base,P,T,l,mode) for l in s34.LINKS for mode in ('inherited_height_screen','endpoint_box_downward_bow','endpoint_box_signed_bow')]
    evaluations=[]
    for L in (129.0,130.0,130.5,130.58,133.0):
        c=candidate_at(base,P,L);g=s34.rg34(c,P,T);p=s34.post_prism(c,g,data['input'])
        evaluations.append({'sig_length_mm':L,'geometry':s34.public_geo(g),'cover':s34.cover(g,P),
                            'states':s34.states_in_rg34(c,g,P),'parts':s34.part_clearances(c,g,p,P,T,rules),
                            'historical_access_only':{'scope':'Stage34 assumptions only; not Stage35 certification','result':s34.access(c,g,P)},'strength':s34.strength(g,p,P),
                            'continuous_axial_states':continuous_states(c,P,T)})
    c=candidate_at(base,P,130.0);g=s34.rg34(c,P,T);post=s34.post_prism(c,g,data['input'])
    fixed=conservative_free_spans(c,g,post,P,T,rules)
    obstacles=all_obstacle_rows(c,g,post,P,T,rules)
    removal=all_obstacle_rows(c,g,post,P,T,rules,True)
    # Historical covers use polyline arc lengths. Keep the exact circular correction visible.
    exact=exact_top(133,math.dist(g['J-SIG']['f']['a'][:2],g['J-SIG']['f']['b'][:2]),43.9,57.3,12,14.6)
    old=s34.read(ROOT/REL/'stage34/model.json')['rg34']['geometry']['J-SIG']['Z0']
    return {'status':'DESIGN_STUDY_ONLY','verdict':'NO_ROBUST_SERVICE_SOLUTION_ESTABLISHED','adopted':False,
            'baseline':BASE,'source_sha256':sources(),'wire_selection':None,'native':'NOT_RUN','physical':'NOT_RUN',
            'intervals':intervals,'evaluations':evaluations,'installed_free_spans_130mm':fixed,
            'access_130mm':access_screen(c,g,post,P,T,rules),'all_obstacles_130mm':obstacles,'vertical_removal_130mm':removal,'support':support_screen(c,g,post,P,T,rules),
            'exact_minus_stage34_polyline_top_mm':exact-old,
            'deeper_cover_proposals':{
                'historical_133mm_height_only_z_mm':s34.cover(s34.rg34(base,P,T),P)['J-SIG']['cover_needed_z_mm'],
                'signed_box_minimum_z_mm':105+next(x['minimum_deeper_cover_in_this_family_mm'] for x in intervals if x['link']=='J-SIG' and x['mode']=='endpoint_box_signed_bow'),
                'signed_box_at_133mm_z_mm':105+(133-next(x['upper_design_length_mm'] for x in intervals if x['link']=='J-SIG' and x['mode']=='endpoint_box_signed_bow'))/2,
                'status':'HEIGHT_LOWER_BOUNDS_ONLY; no release/adoption; aperture, thickness, joints, fasteners, reservations and full service unresolved'},
            'length_definition':{'design':'bundle centreline between housing exits plus two 7.3 mm mated-height accounting terms; inherited convention',
                                 'raw_wire_cut_mm':None,'cut_conversion':'UNKNOWN: contact insertion, stripping, crimp take-up and individual fan-in paths not established',
                                 'tolerance':'Assumed +/-0.5 mm on finished design-length surrogate, NOT an established raw-cut process capability'},
            'slack':{'original_rule_mm':10,'nominal_130mm_remainder_mm':130-(base['lengths']['J-SIG']['minimum_installed_mm']+15),
                     'original_133mm_remainder_mm':133-(base['lengths']['J-SIG']['minimum_installed_mm']+15),
                     'former_residual_mm':.5,'withdrawal_uncontrolled_extra_mm':15,'tracking_stroke_mm':7.5,'tracking_gap_limit_mm':.25},
            'reservation_status':'RG34 plan thickness unchanged: 0.875 mm exact excess, rounded 0.9 historically; RV-ACCESS occupation and jack M4 conflict remain proposals',
            'remaining':['carrier translations and rotations / bow sign and local shape not measured',
                         'guide fit, fasteners, fastening-tool corridors and enclosure aperture undefined',
                         'no constrained support during withdrawal or sleeve removal',
                         'unknown foreign geometry treated occupied/unknown, not admitted as free',
                         '50 N post failure, root fixity/joints, R17 failure preserved',
                         'wire bend/flex/current data unresolved; Stage34 A01 conditional budgets unchanged']}


def summary(a):
    lines=['# Stage35: shortening alone does not establish a serviceable assembly','',
           'Source-only design study. No hardware, wire or canonical geometry is adopted.','',
           '| Arch / datum screen | Lower length mm | Upper length mm | Nonempty |','|---|---:|---:|---|']
    for x in a['intervals']:
        lines.append(f"| {x['link']} / {x['mode']} | {x['lower_design_length_mm']:.6f} | {x['upper_design_length_mm']:.6f} | {x['interval_nonempty']} |")
    lines+=['','These are continuous necessary intervals for the specified arch family, not complete feasible hardware intervals. See README for the distinct datum assumptions.',
            '', '| J-SIG length mm | Historical-shape cover spare mm | Cover K4 | All single-end samples inside |','|---:|---:|---|---|']
    for x in a['evaluations']:
        cv=x['cover']['J-SIG'];ok=all(r['admissible'] for r in x['states'] if r['state']!='both')
        lines.append(f"| {x['sig_length_mm']:.3f} | {cv['robust_spare_mm']:.6f} | {cv['meets_K4']} | {ok} |")
    lines+=['','## Complete service feasibility remains unestablished','',
            '- Shortening lowers the cap; it does not constrain the extra 15 mm released during withdrawal.',
            '- A tracking former needs 7.5 mm travel and <=0.25 mm contact gap; this is a mechanism requirement, not designed hardware.',
            '- The entire obstacle and vertical-removal ledgers include every modeled obstacle; unknown heights are extended through the sweep.',
            '- The post still fails 50 N. Raw cut lengths, repeated-flex radius and wire selection remain unknown.',
            '- A deeper-cover comparison closes only a stated height inequality, not access, guide removal, registration, flex or strength.',
            '', 'See [mock-up.md](mock-up.md) for required unpowered measurements and stop criteria.']
    return '\n'.join(lines)+'\n'


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical bytes changed: '+str(set(changed)-MUTABLE))
    added=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    added+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage35/') or p in SCRIPTS for p in added),'new file outside Stage35 scope')


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage35-history-') as temp:
        path=Path(temp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(path),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage34_arch_retention.py','--check','--check-history','--check-review'],cwd=path,check=True,timeout=600)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage34_arch_retention.py'],cwd=path,check=True,timeout=600)
        finally:
            subprocess.run(['git','worktree','remove','--force',str(path)],cwd=ROOT,check=True)


def review():
    r=json.loads((OUT/'independent-review.json').read_text())
    need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent review missing')
    required=set(sources())|{REL+'stage35/'+n for n in GENERATED}
    need(required<=set(r['reviewed_sha256']),'incomplete review bindings')
    for p,h in r['reviewed_sha256'].items():need(digest(ROOT/p)==h,'review drift '+p)


def main():
    parser=argparse.ArgumentParser()
    for n in ('check','check-history','check-review'):parser.add_argument('--'+n,action='store_true')
    args=parser.parse_args();protected()
    if args.check_history:history()
    a=build();bodies={'analysis.json':dump(a),'summary.md':summary(a)}
    for name,body in bodies.items():
        if args.check:need((OUT/name).read_text()==body,'deterministic drift '+name)
        else:(OUT/name).write_text(body)
    if args.check_review:review()
    print('PASS Stage35 source checks; NO_ROBUST_SERVICE_SOLUTION_ESTABLISHED; native/physical NOT_RUN')


if __name__=='__main__':main()
