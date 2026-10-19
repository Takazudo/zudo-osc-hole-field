"""One bounded cassette concept; proposed interfaces never become measured/free hardware."""
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
import stage35_cover_service as s35
s34,s33=s35.s34,s35.s33
ROOT=s35.ROOT
REL=s35.REL
OUT=ROOT/REL/'stage36'
BASE='8fd10c4a4841daf4d8e1e92346ce7d7282227764'
MUTABLE=s35.MUTABLE
SCRIPTS={'scripts/architecture278/implementation/'+x for x in ('stage36_interface_cassette.py','test_stage36_interface_cassette.py')}
GENERATED=('analysis.json','summary.md','c36-plan.svg','c36-service.svg')
need=s35.need

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n'
def box(i,xy,z,kind='proposal',**kw):return dict(id=i,poly=[[xy[0],xy[1]],[xy[2],xy[1]],[xy[2],xy[3]],[xy[0],xy[3]]],z=z,kind=kind,**kw)
def square(i,xy,d,z,**kw):return box(i,[xy[0]-d/2,xy[1]-d/2,xy[0]+d/2,xy[1]+d/2],z,**kw)
def sweep(p,t):
    q=copy.deepcopy(p);q['z'][1]+=t;return q

def validate(I):
    need(I['status']=='PROPOSED_INTERFACE_CONTRACT_NOT_ADOPTED','no adoption')
    need(I['baseline']==BASE,'baseline')
    need(I['design_lengths_mm']=={'J-SIG':133,'J-PWR':149},'no length sweep')
    for k,v in [('radius_mm',12),('withdrawal_mm',15),('core_extraction_mm',40),('margin_mm',.5),('K4_mm',.15)]:need(I[k]==v,'locked '+k)
    need(I['wire_selection'] is None,'wire unresolved')
    need(I['datum']['bow_fraction_signed']==.0075,'signed bow allowance retained')
    need(I['service_stud_shaft_z_mm'][1]-I['roof_z_mm'][1]>=I['withdrawal_mm'],'guide engagement')
    need(I['service_stud_diameter_mm']<I['bushing_bore_mm'],'guide clearance')
    need(I['keeper_capture_clearance_mm'] is None and I['latch_displacement_mm'] is None,'missing GH interface not invented')

def source_paths():
    paths=list(SCRIPTS|MUTABLE)
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/REL/'stage35').iterdir() if p.is_file()]
    paths += [REL+'stage36/'+n for n in ('interface-input.json','README.md','sources.md','mock-up.md','diagram-note.md')]
    paths += [REL+'stage36/diagram-history/c36-service-r01.svg']
    paths += ['design/connectors/sources/jst-gh.pdf','design/grid/placements.lock.json',REL+'stage10/mechanical-input.json',REL+'stage10/mechanical-report.json',REL+'stage10/overview.svg',REL+'stage31/common-input.json',REL+'stage33/reservations.json',REL+'stage34/plan-rg34.svg','scripts/architecture278/implementation/stage10_mechanical.py']
    return sorted(set(paths))

def geometry(I,c,P,T):
    g=s34.rg34(c,P,T);moving=[];fixed=[];tools=[];studs=[]
    # Transport corridors encompass closed sleeves/fan-ins and end keepers. They
    # are occupancy reservations, not invented solid keeper or shell detail.
    for l in s34.LINKS:
        f=g[l]['f'];R=I['radius_mm'];r=g[l]['r'];a=r+.3+1.2
        top=g[l]['Z0']+.25+1+g[l]['bow_mm']/2+r+.3+1.2
        moving.append(s34.plane_prism(f,'C36-'+l+'-closed-corridor','corridor',[-a,f['D']+a],[-a,a],[min(g[l]['exit_z_mm'].values()),top]))
        for side,ref in zip(s34.SIDES,s34.ENDS[l]):
            h=c['geo'][ref];b=h['sweep']['box_mm']
            moving.append(box('keeper:'+ref,b,[h['face_z_mm'],h['exit_mm'][2]+g[l]['fan_in_mm']],link=l,end=ref,detail='KEEPER INTERFACE UNDEFINED; occupied reservation only'))
    for i,xy in enumerate(I['roof_rectangles_xy_mm']):moving.append(box('roof:'+str(i),xy,I['roof_z_mm']))
    for i,xy in enumerate(I['root_centres_mm']):
        fixed += [square('root-boss:'+str(i),xy,6,I['root_boss_z_mm']),square('post:'+str(i),xy,6,I['post_z_mm'])]
        moving.append(square('bushing:'+str(i),xy,I['bushing_outer_diameter_mm'],[I['roof_z_mm'][1]-I['bushing_length_mm'],I['roof_z_mm'][1]]))
        studs.append(square('guide-stud:'+str(i),xy,I['service_stud_hex_diameter_mm'],[I['service_stud_thread_z_mm'][0],I['service_stud_top_z_mm']]))
        tools.append(square('root-tool:'+str(i),xy,I['tool_diameter_mm'],[100,I['tool_access_top_z_mm']]))
    return g,moving,fixed,studs,tools

def alignment(I,c):
    clearance=I['bushing_bore_mm']-I['service_stud_diameter_mm']
    rad=clearance/2;angle=math.atan(clearance/I['bushing_length_mm'])
    lever=I['roof_z_mm'][1]-I['bushing_length_mm']-min(v['exit_mm'][2] for v in c['geo'].values())
    path=rad+lever*math.tan(angle)
    x0,y0,x1,y1=c['mech']['boards']['A01-middle']['outline_mm'];bow=I['datum']['bow_fraction_signed']*math.hypot(x1-x0,y1-y0)
    return {'diametral_play_mm':clearance,'pitch_roll_bound_deg':math.degrees(angle),'scope':'Nominal clearance-only single-bushing screen; no shaft straightness, bore tolerance or stiffness credited; not a complete assembly bound','exit_lever_mm':lever,'guide_path_bound_mm':path,
            'proposed_path_target_mm':I['guide_path_error_target_mm'],'path_contract_met':path<=I['guide_path_error_target_mm'],
            'independent_pair_translation_span_each_axis_mm':2*I['datum']['endpoint_translation_each_axis_mm'],
            'middle_signed_bow_mm':bow,'possible_bow_change_between_fits_mm':2*bow,
            'common_translation_cannot_remove_relative_error':True,'manufacturer_capture_window_mm':None,
            'status':'FAILED_PROPOSED_GUIDE_PATH_CONTRACT_AND_UNRESOLVED_GH_CAPTURE'}

def obstacle_audit(I,c,P,T,rules,parts):
    obs=s35.occupied_obstacles(c,250);rows=[];alloc={};mins={};count=0
    byid={o['id']:o for o in c['obs']}
    bow=I['datum']['bow_fraction_signed']*math.hypot(82,150)
    for p in parts:
        for o in obs:
            count+=1
            cross=not o['id'].startswith(s34.REAR)
            inherited=s34.stack_for(o['id'],P,T,rules,bow,cross)
            registration_box_norm=math.sqrt(3)*I['datum']['endpoint_translation_each_axis_mm'] if cross else 0
            st=inherited['worst_case_mm']-inherited['contributors'].get('registration_allowance_mm',0)+registration_box_norm
            # Preserve inherited stack and add newly explicit rotation sweep.
            radius=max(math.dist([x,y,z],h['exit_mm']) for x,y in p['poly'] for z in p['z'] for h in c['geo'].values())
            rot=6*math.sin(math.radians(I['datum']['endpoint_rotation_each_axis_deg'])/2)*radius
            req=I['margin_mm']+st+I['K4_mm']+rot
            d=s34.prism_dist(p,o);spare=d-I['margin_mm']-st-rot
            exempt=None
            if p['id'].startswith(('root-boss:','post:')) and o['id']=='crossmember:rear:0':exempt='intentional integral replacement crossmember/boss/post union; strength NOT established'
            if p.get('end') and o['id']=='release:'+p['end']:exempt='own housing release occupancy; keeper/latch interface still undefined'
            if o['id'].startswith('tool:') and ('jack' in o['id'] or 'middle' in o['id']):exempt='deferred board tool use only AFTER entire cassette removed; removal audit still includes physical boards'
            row={'part':p['id'],'obstacle':o['id'],'distance_mm':d,'robust_spare_mm':spare,'required_K4_mm':I['K4_mm'],'exclusion':exempt,'kind':o['kind'],'registration_box_norm_mm':registration_box_norm,'rotation_bound_mm':rot,'stack_mm':st}
            if o['id'] not in mins or spare<mins[o['id']]['robust_spare_mm']:mins[o['id']]=row
            if spare<I['K4_mm'] and not exempt:
                rows.append(row)
                if o['kind'] in ('unknown_depth','assumed_height'):
                    # Sufficient vertical separation proposal over expanded XY only;
                    # the obstacle is NEVER shortened in the actual audit.
                    cap=p['z'][0]-req
                    old=alloc.get(o['id'])
                    if old is None or cap<old['proposed_max_z_mm']:
                        src=byid.get(o['id'],{})
                        alloc[o['id']]={'obstacle':o['id'],'owner':src.get('block','A01 component owner'),'class':o['kind'],'xy_polygon':o['poly'],
                            'proposed_max_z_mm':cap,'inherited_proxy_top_mm':src.get('hi',[None]*3)[2],
                            'inherited_lower_z_mm':src.get('lo',[None]*3)[2],'driving_part':p['id'],
                            'accepted':False,'cap_below_source_lower_surface':cap<o['z'][0],'effect':'Board, rear components, tails and harness must stay below this cap inside clearance-expanded footprint; no panel hardware move; reroute/repartition costs unresolved.'}
    return {'examined_pairs':count,'all_obstacles_count':len(obs),'blocking_rows':rows,'minimum_by_obstacle':list(mins.values()),'proposed_neighbor_obligations':list(alloc.values()),'unknown_space_treated_free':False}

def build():
    I=json.loads((OUT/'interface-input.json').read_text());validate(I)
    D,P,T,r,c=s35.context();g,moving,fixed,studs,tools=geometry(I,c,P,T)
    audits={name:obstacle_audit(I,c,P,T,r,parts) for name,parts in [
        ('installed',moving+fixed),('withdrawal_and_reverse', [sweep(p,15) for p in moving]+fixed+studs),
        ('hypothetical_75mm_removal_NOT_ACHIEVABLE',[sweep(p,I['removal_translation_mm']) for p in moving]+fixed+studs),
        ('root_tool_access',tools),('stud_installation_and_reverse',[sweep(p,I['service_stud_installation_translation_mm']) for p in studs])]}
    # Both-housing translation preserves every inter-point distance and bend;
    # this identity does not assert any real keeper or actuator realizes it.
    kinematics=[]
    for l in s34.LINKS:
        route=c['installed'][l]['route']['dense']
        moved=[[x,y,z+15] for x,y,z in route]
        error=max(abs(math.dist(a,b)-math.dist(x,y)) for a,b,x,y in zip(route,route[1:],moved,moved[1:]))
        kinematics.append({'link':l,'length_mm':c['lengths'][l]['design_length_mm'],'radius_mm':12,'common_translation_mm':15,'segment_length_invariance_error_mm':error,'fan_in_mm':g[l]['fan_in_mm'],'actual_supported_housing_capture':'UNRESOLVED'})
    footprint=I['root_footprint_mm'][1];beam=4;pilot=I['root_pilot_diameter_proposal_mm']
    return {'status':'FAILED_INTERFACE_CONCEPT_NOT_SOURCE_FEASIBLE','adopted':False,'baseline':BASE,'source_sha256':{p:digest(ROOT/p) for p in source_paths()},
      'concept':I['concept'],'input':I,'alignment':alignment(I,c),'kinematics':kinematics,'moving_parts':moving,'fixed_parts':fixed,'service_studs':studs,'tool_columns':tools,'audits':audits,
      'internal_interfaces':{'status':'UNRESOLVED_OCCUPANCY_ONLY_NOT_SOLID_CAD','bushing_post_seat_z_mm':90,'post_thread_z_mm':[84,90],'short_screw_engagement_mm':5,'shaft_bore_radial_gap_mm':0.2,'roof_bushing_join':'intentional union, strength unspecified','corridor_roof_keeper_joins':'solid shell, wire void and mounting detail missing; no internal clearance pass claimed','tool_stud_coaxial_access':'intended tool-to-hex contact; opposite root 40mm away; corridor/roof latch and grip access unresolved'},
      'root_obligations':{'rear_crossmember_source_xy_mm':[237,170,318,174],'root_front_extension_mm':4,'overlap_with_old_beam_y_mm':2,'pilot_diameter_proposal_mm':pilot,'boss_edge_ligament_mm':(footprint-pilot)/2,'old_beam_centred_pilot_ligament_mm':(beam-pilot)/2,'strength_50N':'NOT_ESTABLISHED; no material or thread/pullout rating adopted; Stage34 39.836642 N failure retained, not transferred to this root'},
      'cover':{'source_inner_z_mm':105,'roof_top_mm':100,'nominal_gap_mm':5,'opening_xy_mm':I['cover_opening_xy_mm'],'opening_area_mm2':(313-199)*(184-142),'minimum_lift_to_clear_opening_plane_mm':105+.5-min(p['z'][0] for p in moving),'requested_lift_mm':75,'removal_achievable':False,'head_bore_failure':{'head_diameter_mm':6,'bore_diameter_mm':4.4,'lift_to_head_contact_mm':32,'reason':'Closed bushing cannot pass service-stud hex; requested +75 sweep is NOT a realizable path'},'studs_installed_only_with_cover_removed':True,'rib_aperture_fastener_detail':'PROPOSED; not confirmed by a cover drawing'},
      'failed_interfaces':['D6 service-stud head cannot pass closed D4.4 bushing: contact at +32mm prevents required +75mm removal. No alternative disassembly sequence adopted.','Rigid four-end capture cannot be qualified from GH catalog dimensions: latch stroke, keeper bearing surfaces, axial force and mating capture tolerance unavailable.', 'Proposed plain two-stud guide exceeds its 0.25 mm path-error contract; signed bow and independent carrier errors cannot be removed by a common rigid translation.', 'All known and unknown geometric blockers remain in audits; neighbor caps are unaccepted interface obligations, not cleared volumes.'],
      'native':'NOT_RUN','physical':'NOT_RUN','wire_selection':None,'no_follow_on_mechanism':'STOP after C36 for parent review'}

def summary(a):
    al=a['alignment'];L=['# C36: one cassette concept stops at its interfaces','','**FAILED_INTERFACE_CONCEPT_NOT_SOURCE_FEASIBLE** — no hardware adopted.','',f"Nominal bore/shaft play alone permits a path-error screen of {al['guide_path_bound_mm']:.6f} mm against proposed 0.25 mm. Signed middle bow is +/-{al['middle_signed_bow_mm']:.6f} mm; a repeat fit can differ by {al['possible_bow_change_between_fits_mm']:.6f} mm. GH capture/latch/keeper dimensions are unavailable.",'','| Audit | Pairs | Unexcluded below K4 | Proposed neighbor caps |','|---|---:|---:|---:|']
    for k,v in a['audits'].items():L.append(f"| {k} | {v['examined_pairs']} | {len(v['blocking_rows'])} | {len(v['proposed_neighbor_obligations'])} |")
    L+=['','**Removal also fails:** D6 stud hex cannot pass the closed D4.4 bushing. Contact begins at +32 mm; the +75 mm sweep is hypothetical and unreachable. No alternate disassembly sequence is adopted.','','These counts include unknown-occupancy and conservative corridor bounds, not observed collisions. No cap is applied to erase an obstacle. Roof/aperture/roots and simultaneous four-end removal are new interface proposals.','', 'See README, sources.md, mock-up.md and the two diagrams. No new mechanism or Stage37 is selected.']
    return '\n'.join(L)+'\n'

# Original fine-outline diagrams: literal colors, no external assets or fonts.
def svg_start(title,desc):return ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img"><title>'+html.escape(title)+'</title><desc>'+html.escape(desc)+'</desc><rect width="1200" height="760" fill="#FCFCFA"/><g font-family="DejaVu Sans, sans-serif" fill="#253235" stroke-width="1.6">']
def text(x,y,t,size=18,color='#253235'):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(t)}</text>'
def rect(x,y,w,h,color='#B7C0C0',fill='none',dash=False):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{color}" fill="{fill}"'+(' stroke-dasharray="6 4"' if dash else '')+'/>'
def drawings(a):
    L=svg_start('C36 plan: proposed cassette and interface obligations','Rear view, source study; no qualified hardware. Existing core keepout is preserved.')
    L += [text(30,40,'C36 / removable cassette — proposed, NOT source-feasible',26),text(30,70,'Cover off • K-PWR first • core 40 mm • all four ends rise together 15 mm',19)]
    X=lambda x:50+(x-195)*6;Y=lambda y:125+(y-140)*6
    def rr(xy,col,fill='none',dash=False):return rect(X(xy[0]),Y(xy[1]),(xy[2]-xy[0])*6,(xy[3]-xy[1])*6,col,fill,dash)
    L +=[rr([236,174,312,210],'#253235'),text(X(248),Y(197),'CORE + 40 mm keep-out',16),rr([237,170,318,174],'#253235'),rr([199,142,313,184],'#376E61','none',True)]
    for xy in a['input']['roof_rectangles_xy_mm']:L.append(rr(xy,'#376E61'))
    for p in a['moving_parts']:
        if p['id'].startswith('C36-'):
            pts=' '.join(f'{X(x)},{Y(y)}' for x,y in p['poly']);L.append(f'<polygon points="{pts}" fill="none" stroke="#9FB9AE"/>')
    for i,(x,y) in enumerate(a['input']['root_centres_mm']):
        L +=[rr([x-3,y-3,x+3,y+3],'#A65E42'),text(X(x)-20,Y(y)-28,'R'+str(i+1),17)]
    for x,y,label in [(210,173,'SIG local'),(226,173,'PWR local'),(250,152,'SIG middle'),(290,150,'PWR middle')]:
        L +=[f'<circle cx="{X(x)}" cy="{Y(y)}" r="5" fill="#376E61"/>',text(X(x)-25,Y(y)-10,label,13)]
    L +=[text(830,150,'Proposed interfaces',21),text(830,185,'Opening: x199–313'),text(830,212,'y142–184; ribs excluded'),text(830,252,'Roof: z98–100'),text(830,290,'Roots: (265,169)'),text(830,317,'and (305,169)'),text(830,357,'M3 threads + 6 mm tools'),text(830,397,'Unknown neighbors:'),text(830,424,'caps in analysis.json'),text(830,451,'NOT cleared or adopted'),text(30,610,'Known core/board obstacles are retained. Dashed opening is a new enclosure obligation.',19),text(30,645,'Closed corridor outlines reserve space; actual GH keepers and latch access remain undefined.',19),text(30,690,'STOP: plain-guide alignment and four-housing capture are not established.',22,'#A65E42'),'</g></svg>']
    S=svg_start('C36 axial service and failed alignment interface','Conceptual section, not manufacturing geometry. Service studs are fitted only after cover removal.')
    S +=[text(30,40,'C36 / service section and stop condition',26),text(30,72,'Same forward/reverse swept volume • cable lengths and R12 unchanged',19)]
    X=lambda x:55+x*5;Z=lambda z:600-(z-30)*4
    for z,label in [(62,'Rear-carrier datum A: z62'),(100,'Roof top: z100'),(105,'Cover inner face: z105'),(132,'Service shaft top: z132')]:
        S +=[f'<path d="M55 {Z(z)} H640" stroke="#B7C0C0" stroke-dasharray="5 5"/>',text(660,Z(z)+5,label,17)]
    for x in [35,75]:
        S +=[rect(X(x)-15,Z(90),30,(90-62)*4),rect(X(x)-10,Z(132),20,(132-90)*4,'#376E61'),rect(X(x)-15,Z(100),30,10*4,'#A65E42'),rect(X(x)-15,Z(115),30,10*4,'#A65E42','none',True)]
    S +=[rect(X(5),Z(100),100*5,2*4,'#376E61'),rect(X(5),Z(115),100*5,2*4,'#376E61','none',True),text(70,190,'+15 mm common lift',18),text(70,220,'All sleeves/keepers retained',18),text(70,250,'No tracking former',18),text(660,120,'Install studs one at a time'),text(660,150,'after cover/core sequence'),text(660,510,'Guide bore 4.4 / shaft 4.0'),text(660,535,'10 mm bearing length'),text(660,560,f"Exit-path screen: {a['alignment']['guide_path_bound_mm']:.3f} mm"),text(660,590,'Target: 0.25 mm — FAIL',20,'#A65E42'),text(30,650,'Rigid four-end remating: independent carrier errors + signed bow need a capture interface.',18),text(30,680,'GH latch travel, keeper load surfaces and capture tolerance are UNSOURCED.',18,'#A65E42'),text(30,715,'REMOVAL FAIL: D6 stud head blocks D4.4 bushing at +32 mm; +75 mm is unreachable.',18),'</g></svg>']
    return {'c36-plan.svg':'\n'.join(L)+'\n','c36-service.svg':'\n'.join(S)+'\n'}

def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines();need(set(changed)<=MUTABLE,'historical/canonical edit')
    added=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage36/') or p in SCRIPTS for p in added),'outside Stage36 scope')
def history():
    with tempfile.TemporaryDirectory(prefix='osc-stage36-history-') as tmp:
        p=Path(tmp)/'repo';subprocess.run(['git','worktree','add','--detach',str(p),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage35_cover_service.py','--check','--check-history','--check-review'],cwd=p,check=True,timeout=900)
            for flags in ([],['-O']):subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage35_cover_service.py'],cwd=p,check=True,timeout=120)
        finally:subprocess.run(['git','worktree','remove','--force',str(p)],cwd=ROOT,check=True)
def review():
    d=json.loads((OUT/'independent-review.json').read_text());need(d['status']=='PASS_SOURCE_REVIEW_ONLY','review status')
    need(set(source_paths()+[REL+'stage36/'+n for n in GENERATED])<=set(d['reviewed_sha256']),'review coverage')
    for p,h in d['reviewed_sha256'].items():need(digest(ROOT/p)==h,'review drift '+p)
def main():
    p=argparse.ArgumentParser()
    for f in ('check','check-history','check-review'):p.add_argument('--'+f,action='store_true')
    a=p.parse_args();protected()
    if a.check_history:history()
    obj=build();bodies={'analysis.json':dump(obj),'summary.md':summary(obj),**drawings(obj)}
    for n,b in bodies.items():
        if a.check:need((OUT/n).read_text()==b,'drift '+n)
        else:(OUT/n).write_text(b)
    if a.check_review:review()
    print('PASS Stage36 source checks; FAILED_INTERFACE_CONCEPT_NOT_SOURCE_FEASIBLE; native/physical NOT_RUN')
if __name__=='__main__':main()
