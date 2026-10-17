"""DIN manufacturing decision table and vendor-completed harness candidate; source only, no native/physical claims."""
import argparse
import copy
import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import stage22_requirements as requirements

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage28'
BASE='b58068fbaeb65886958a67a4f4978613414e31c5'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
INTERNAL={'stage5-catalogue':REL+'stage5/din-evidence.json','stage10-mechanical':REL+'stage10/mechanical-report.json','stage27-readme':REL+'stage27/README.md'}
STATUSES={'CONFIRMED_FROM_DRAWING','CONFLICT_REQUIRES_DECISION','UNCONFIRMED','NOT_GUARANTEED_BY_PUBLISHED_DEFAULT','UNDECIDED'}
FORBIDDEN=re.compile(r'\b(PASS(ED)?|QUALIFIED|ACCEPTED|VALIDATED|RELEASED|APPROVED)\b')
CLAIM=re.compile(r'(?<!not )(?<!no )(?<!never )\b(passed|qualified|validated|released)\b',re.I)
LINKS={'J-SIG':7,'J-PWR':4,'C-SIG':6,'K-PWR':3}
RECIPIENTS={'CONNECTOR_MANUFACTURER','PCB_FABRICATOR','PCB_ASSEMBLER','HARNESS_MAKER','OWNER'}

def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(p.read_text())
def dump(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def no_claims(value,where):
    # Status-like strings anywhere in the sources must not assert an unmeasured process outcome.
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('status','result','outcome','verdict'):
                need(isinstance(v,str) and FORBIDDEN.search(v) is None,'unsupported pass claim at '+where+'.'+k)
            no_claims(v,where+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):no_claims(v,where+f'[{i}]')
    elif isinstance(value,str):
        need(CLAIM.search(value) is None,'unsupported pass claim in text at '+where)


def validate_sources(sources,cache=False):
    need(set(sources)=={'harting-female','harting-male','jlc-assembly','jlc-pad-hole','jlc-pcb','jst-gh'},'exact Stage28 receipt set')
    for sid,s in sources.items():
        need(re.fullmatch(r'[0-9a-f]{64}',s['sha256']) is not None and s['bytes']>0 and s['url'].startswith('https://'),'receipt identity '+sid)
        need(s['authority'] in ('MANUFACTURER_PRIMARY','FABRICATOR_PRIMARY') and s['locator'],'primary authority/locator '+sid)
        if 'path' in s:
            need(sha(ROOT/s['path'])==s['sha256'],'retained in-repo primary '+sid)
            continue
        stamp=datetime.datetime.fromisoformat(s['retrieved_UTC'])
        need(stamp.utcoffset()==datetime.timedelta(0) and stamp.date()==datetime.date(2026,10,17),'dated UTC retrieval '+sid)
        if cache:
            p=ROOT/s['raw_cache'];need(p.stat().st_size==s['bytes'] and sha(p)==s['sha256'],'raw receipt drift '+sid)
            if sid.startswith('harting'):need(p.read_bytes().startswith(b'%PDF-'),'real PDF '+sid)
    for sid,old in (('harting-female',0),('harting-male',1)):
        need(read(ROOT/REL/'stage5/din-evidence.json')['sources'][old]['sha256']==sources[sid]['sha256'],'drawing bytes differ from Stage5 receipt '+sid)


def fit(drawing,positions):
    """Exact affine map drawing(X right, Y up) -> locked global XY from labeled contacts."""
    need(set(drawing)==set(positions) and len(drawing)==96,'complete 96 labeled contacts')
    (ax,ay),(bx,by),(cx,cy)=drawing['a1'],drawing['a32'],drawing['c1']
    g=lambda p:positions[p]
    col=[(g('a1')[i]-g('a32')[i])/(ax-bx) for i in range(2)];row=[(g('a1')[i]-g('c1')[i])/(ay-cy) for i in range(2)]
    m=[[round(col[0],9)+0.0,round(row[0],9)+0.0],[round(col[1],9)+0.0,round(row[1],9)+0.0]]
    need(all(v in (-1,0,1) for r in m for v in r) and abs(m[0][0]*m[1][1]-m[0][1]*m[1][0])==1,'labeled grid is not a rigid unit-pitch image of the drawing')
    t=[g('a1')[i]-m[i][0]*ax-m[i][1]*ay for i in range(2)]
    for p,(x,y) in drawing.items():
        need(all(math.isclose(m[i][0]*x+m[i][1]*y+t[i],g(p)[i],abs_tol=1e-6) for i in range(2)),'contact '+p+' off the rigid labeled grid (missing, swapped or moved)')
    return m,t


def apply(m,t,point):return [round(m[i][0]*point[0]+m[i][1]*point[1]+t[i],6) for i in range(2)]


def frame_facts(lock,mech):
    f=lock['frame'];need(f['positive_x']=='right' and f['positive_y']=='down' and f['origin']=='panel front top-left','locked front-view frame')
    b=mech['boards'];z=lambda n:b[n]['z_mm']
    need(z('A01-control')[1]<z('A01-jack')[0]<z('A01-middle')[0]<z('A01-core')[0],'z increases from front panel toward the rear core')
    d=mech['din_connectors']
    need(d['middle']['mount_surface_z_mm']==z('A01-middle')[1] and d['rear']['mount_surface_z_mm']==z('A01-core')[0],'female body behind middle board, male body in front of core board')
    # Right-handed x right / y down / z rear: a viewer looking along +z sees drawing (X,Y)=(x,-y) (det -1); along -z (X,Y)=(-x,-y) (det +1).
    return {'frame':'x right, y down viewed from the front, z toward rear (right-handed)',
            'female':{'body_side':'+z of A01-middle','view_A_looks_along':'-z','expected_det':1},
            'male':{'body_side':'-z of A01-core','view_B_looks_along':'+z','expected_det':-1}}


def din_analysis(evidence,mech,inventory,interfaces,facts):
    drawings={s:requirements.drawing_coordinates(evidence['DIN'][s]) for s in ('female','male')}
    sides={'female':'middle','male':'rear'};refs={'female':'J17909','male':'J17910'}
    pos={s:{p:v[0][:2] for p,v in mech['din_connectors'][sides[s]]['pads_xyz_mm'].items()} for s in sides}
    need(pos['female']==pos['male'],'labeled female/male contacts must coincide when mated')
    cx,cy=read(ROOT/REL/'stage10/mechanical-input.json')['DIN_centre_mm']
    grid={(round(cx+(1-'cba'.index(p[0]))*2.54,6),round(cy+(16.5-int(p[1:]))*2.54,6)) for p in pos['female']}
    need({tuple(round(v,6) for v in xy) for xy in pos['female'].values()}==grid,'fixed 96-hole DIN grid moved')
    pinmap=interfaces['DIN_pinmap']
    for s,ref in refs.items():
        row=inventory['unbound'][ref];need(row['selected_mpn']==evidence['DIN'][s]['mpn'] and row['in_bom'] is True and row['on_board'] is True,'exact DIN identity/flags '+ref)
        need(row['pins']==pinmap,'DIN net/NC assignment drift '+ref)
    fits={s:fit(drawings[s],pos[s]) for s in sides};out={}
    for s,(m,t) in fits.items():
        det=m[0][0]*m[1][1]-m[0][1]*m[1][0]
        out[s]={'drawing_to_global_matrix':m,'offset_mm':t,'labeled_det':det,'expected_det':facts[s]['expected_det'],'handedness_consistent':det==facts[s]['expected_det']}
    m,t=fits['female']
    holes=sorted((apply(m,t,[x,.3]) for x in (-45,45)),key=lambda p:p[1])
    stage10=sorted((h['point_mm'] for h in mech['DIN_flange_holes']),key=lambda p:p[1])
    need(holes==stage10,'female fixing holes moved from S(±45,+0.3 toward row a)')
    candidates={}
    for name,r in (('column_reversal',[[-1,0],[0,1]]),('row_reversal',[[1,0],[0,-1]])):
        cm=[[sum(m[i][k]*r[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        moved=sorted((apply(cm,t,[x,.3]) for x in (-45,45)),key=lambda p:p[1])
        shift=max(math.dist(a,b) for a,b in zip(moved,stage10))
        relabel={p:next(q for q,xy in pos['female'].items() if math.isclose(xy[0],apply(cm,t,drawings['female'][p])[0],abs_tol=1e-6) and math.isclose(xy[1],apply(cm,t,drawings['female'][p])[1],abs_tol=1e-6)) for p in pos['female']}
        mm,mt=fits['male'];male=[[sum(mm[i][k]*r[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        mated=all(apply(cm,t,drawings['female'][p])==apply(male,mt,drawings['male'][p]) for p in pos['female'])
        candidates[name]={'female_matrix':cm,'det':cm[0][0]*cm[1][1]-cm[0][1]*cm[1][0],'fixing_hole_shift_mm':round(shift,6),
            'keeps_fixed_hole_positions':shift<1e-9,'mated_identity':mated,
            'net_at_stage10_label_position':{q:pinmap[p] for p,q in sorted(relabel.items()) if pinmap[p]},
            'stage10_label_occupied_by_contact':{q:p for p,q in sorted(relabel.items()) if pinmap[p]}}
    conflict=not(out['female']['handedness_consistent'] and out['male']['handedness_consistent'])
    proper=[n for n,c in candidates.items() if c['det']==facts['female']['expected_det'] and c['keeps_fixed_hole_positions'] and c['mated_identity']]
    contacts=[]
    for p in sorted(pinmap,key=lambda q:('abc'.index(q[0]),int(q[1:]))):
        net=pinmap[p]
        contacts.append({'label':p,'middle_ref':'J17909','rear_ref':'J17910','net':net,'role':role(net) if net else 'NC',
            'stage10_xy_mm':pos['female'][p],'female_drawing_xy_mm':drawings['female'][p],'male_drawing_xy_mm':drawings['male'][p],
            'inspection':['I-CONT','I-ISO'] if net else ['I-ISO'],'results':'NOT_RUN'})
    need(sum(1 for c in contacts if c['net'])==16 and sum(1 for c in contacts if not c['net'])==80,'16 assigned / 80 NC DIN contacts')
    return {'facts':facts,'fits':out,'mirror_conflict':conflict,'candidates':candidates,'proper_handed_candidate':proper,
        'candidate_status':'NOT_ADOPTED; owner decision Q-O01 after Q-M01/M-01',
        'consequence':'Both boards share the same mirrored labeling, so a mated pair would still join equal nets through physically different contacts; contact-numbered inspection, pin-1 marking and male orientation would not match the HARTING parts. Board copper must not be bound until D02 is resolved.','fixing_holes_stage10_mm':stage10,
        'fixing_hole_offset_direction':'Stage22 records toward row a; not re-resolved from raster in Stage28',
        'hole_preserving_condition':'Column reversal keeps the Stage10 fixing holes only if the 0.3 offset is toward row a; if toward row c, row reversal is the hole-preserving relabeling and the Stage10 fixing holes are misplaced (Q-M04, M-01).',
        'stage6_frame_note':'Stage6 matrices act on a paper frame (u right, v down, v=-Y); their dets are not drawing-to-global dets. Stage10 signed_transform copies them.',
        'mated_contact_types':'09031966922 contact loading is all standard pin type A (no preleading/lagging), so mirrored-consistent labels change contact numbering but not mating sequence.'},contacts


def role(net):
    if net in ('+12V','-12V','+5V'):return 'POWER'
    if net=='AGND':return 'RETURN'
    if net in ('/A01/REF5','/A01/REFN5'):return 'REFERENCE'
    if '_LED_' in net or '_CLIP_N' in net:return 'INDICATOR'
    return 'SIGNAL'


def validate_policy(policy,questions,measurements,din):
    for name,data in (('policy',policy),('questions',questions),('measurements',measurements),('din',din)):no_claims(data,name)
    need(questions['status']=='UNSENT_QUESTIONNAIRE_NO_EXTERNAL_CONTACT' and measurements['status']=='MINIMUM_PHYSICAL_CHECKLIST_NOT_RUN','unsent/not-run status')
    qids=[q['id'] for q in questions['questions']];mids=[m['id'] for m in measurements['measurements']]
    need(len(set(qids))==len(qids) and len(set(mids))==len(mids),'unique question/measurement IDs')
    for q in questions['questions']:
        need(q['recipient'] in RECIPIENTS and q['ask'] and q['why'] and len(q['decision'])>=2,'question with recipient, reason and post-answer decision '+q['id'])
        need(all(d.get('if') and d.get('then') for d in q['decision']),'non-empty post-answer decision '+q['id'])
    for m in measurements['measurements']:
        need('result' not in m and m['method'] and m['where'] and m['acceptance'] and m['record'],'measurement definition only '+m['id'])
    ids=set(qids)|set(mids)
    need([r['id'] for r in din['rows']]==[f'D{i:02d}' for i in range(1,15)],'complete ordered DIN decision rows')
    sources=read(OUT/'sources.json')
    for r in din['rows']:
        need(r['status'] in STATUSES,'decision status vocabulary '+r['id'])
        need(r['pass_evidence'] and set(r['pass_evidence'])<=ids and set(r['confirmation_needed'])<=ids,'defined pass evidence/questions '+r['id'])
        need(r['status']=='CONFIRMED_FROM_DRAWING' or r['confirmation_needed'],'every open item needs a question '+r['id'])
        need(r['unconfirmed'] and r['confirmed'] and r['requirement'] and r['current_interpretation'],'complete row '+r['id'])
        for s in r['primary_source']:need(s['source'] in sources or s['source'] in INTERNAL,'known source '+r['id'])
    need({k:din['parts'][k]['mpn'] for k in ('female','male')}=={'female':'09032966824','male':'09031966922'},'exact HARTING parts')
    g,t=policy['gh'],policy['tail']
    need(g['allowed_awg']==[30,26] and g['insulation_od_mm']==[.76,1.0] and g['rated_voltage_V_min']==50 and g['candidate_awg'] in (26,27,28,29,30),'JST GH applicable wire range')
    need(g['selected_wire_mpn'] is None and t['selected_wire_mpn'] is None,'no unsupported wire selection')
    need(t['insulation_od_must_be_below_guide_min_open'] is True and t['clearance_mm'] is None and t['clearance_status'].startswith('UNDETERMINED'),'tail OD strictly below guide opening; margin unknown, not zero')
    for i in policy['inspection']:
        need(i['limit'] is not None or i.get('limit_status','').startswith('UNDETERMINED'),'unknown inspection limit must stay null with reason '+i['id'])
        need(i['limit']!=0,'unknown limit zeroed '+i['id'])
    for step in policy['route']:
        need(set(re.findall(r'[QM]-[A-Z]?\d\d',step['decision_after']))<=ids,'route decision references '+step['id'])
    need(all(a['status'].startswith(('COMPARISON','SEPARATE')) for a in policy['alternatives_not_adopted']),'alternatives stay unadopted')
    need(policy['o1_rear_trimmer_constraint']['count']==6,'six rear O1 trimmers')
    return ids


def segment_box(a,b,lo,hi):
    t0,t1=0.0,1.0
    for i in range(3):
        d=b[i]-a[i]
        if abs(d)<1e-12:
            if not lo[i]<a[i]<hi[i]:return False
            continue
        u,v=sorted(((lo[i]-a[i])/d,(hi[i]-a[i])/d));t0=max(t0,u);t1=min(t1,v)
        if t0>=t1:return False
    return True


def obstacles(mech):
    out=[]
    for s in mech['connector_release_sweeps']:
        x0,y0,x1,y1=s['box_mm'];out.append({'id':'release:'+s['ref'],'link':s['ref'].split(':')[1],'lo':[x0,y0,s['z_mm'][0]],'hi':[x1,y1,s['z_mm'][1]]})
    for m in mech['mounts']:
        x,y=m['xy_mm'];out.append({'id':'tool:'+m['id'],'link':None,'lo':[x-3,y-3,m['tool_z_mm'][0]],'hi':[x+3,y+3,m['tool_z_mm'][1]]})
    x0,y0,x1,y1=mech['din_connectors']['middle']['box_mm']
    out.append({'id':'DIN-mated-body','link':None,'lo':[x0,y0,mech['din_connectors']['middle']['mount_surface_z_mm']],'hi':[x1,y1,mech['din_connectors']['rear']['mount_surface_z_mm']]})
    x0,y0,x1,y1=mech['boards']['A01-core']['outline_mm'];z=mech['boards']['A01-core']['z_mm'][1]
    out.append({'id':'core-extraction-40mm','link':'K-PWR','lo':[x0,y0,z],'hi':[x1,y1,z+40]})
    return out


def harness(interfaces,mech,inventory,policy):
    nodes=interfaces['nodes'];wires=interfaces['wires'];tails=interfaces['terminal_wires']
    need(len(wires)==20 and len(tails)==14,'20 GH conductors and 14 permanent tails')
    need(all(w['wire_nominal_mm']>w['wire_tolerance_mm']>0 for w in wires+tails),'Stage10 nominal cut must stay a positive proposal, never zeroed')
    need(interfaces['headers']==mech['headers'],'GH header geometry differs from locked Stage10 mechanics')
    need({l:sum(1 for w in wires if w['link']==l) for l in LINKS}==LINKS,'complete GH link conductor counts')
    tp={row['source_nodes'][pin]:(ref,row) for ref,row in inventory['unbound'].items() if ref.startswith('TP') for pin in row['pins']}
    need(len(tp)==22 and all(r['in_bom'] is False and r['on_board'] is False for _,r in tp.values()),'22 non-BOM land annotations keep exclusion flags')
    lands={l['id']:l for l in mech['terminal_lands']}|{l['id']:l for l in mech['LED_wire_lands']}
    obs=obstacles(mech);rows=[]
    def screen(link,a,b):
        return sorted(o['id'] for o in obs if o['link']!=link and segment_box(a,b,o['lo'],o['hi']))
    for w in wires:
        a,b=nodes[w['from']],nodes[w['to']]
        need(a['net']==b['net']==w['net'] and a['pin']==b['pin']==w['pin'],'GH 1:1 straight conductor '+w['from'])
        ha,hb=mech['headers'][a['ref']],mech['headers'][b['ref']]
        need(ha['pins'][a['pin']]==hb['pins'][b['pin']]==w['net'] and ha['positions']==hb['positions']==LINKS[w['link']],'header pin/net/position count '+w['from'])
        need(a['pad_xyz_mm']==ha['pads_xyz_mm'][a['pin']][0] and b['pad_xyz_mm']==hb['pads_xyz_mm'][b['pin']][0],'fixed header pad moved '+w['from'])
        straight=math.dist(a['pad_xyz_mm'],b['pad_xyz_mm'])
        rows.append({'id':f"H-{w['link']}-{w['pin']}",'kind':'GH_HARNESS','link':w['link'],'net':w['net'],'role':role(w['net']),
            'end_a':{'board':ha['board'],'connector':a['ref'],'header_mpn':ha['header_mpn'],'housing_mpn':ha['housing_mpn'],'contact_mpn':ha['contact_mpn'],'pin':a['pin'],'pad_xyz_mm':a['pad_xyz_mm']},
            'end_b':{'board':hb['board'],'connector':b['ref'],'header_mpn':hb['header_mpn'],'housing_mpn':hb['housing_mpn'],'contact_mpn':hb['contact_mpn'],'pin':b['pin'],'pad_xyz_mm':b['pad_xyz_mm']},
            'wire':{'awg_allowed':policy['gh']['allowed_awg'],'awg_candidate':policy['gh']['candidate_awg'],'insulation_od_mm':policy['gh']['insulation_od_mm'],
                'rated_voltage_V_min':policy['gh']['rated_voltage_V_min'],'rated_temperature_C_min':policy['gh']['rated_temperature_C_min'],
                'current_limit_basis':'Stage10 GH contact limit 0.5 A; JST 1.0 A at AWG26','selected_mpn':None,'status':'CANDIDATE_UNCONFIRMED (Q-H02)'},
            'termination':{'a':policy['gh']['termination'],'b':policy['gh']['termination'],'status':'VENDOR_TO_COMPLETE (Q-H01)'},
            'marking':{'conductor_id':f"H-{w['link']}-{w['pin']}",'cable_label':'A01 '+w['link'],'pin1':'housing pin-1 mark to header pin 1 at both ends'},
            'polarity':{'map':'1:1 straight; end reversal is harmless','contact_view':'JST housing numbering as moulded; header layout viewed from mounting surface per JST','keying':f"{LINKS[w['link']]}-position housing; cross-mating trial M-10"},
            'geometry':{'straight_pad_distance_mm':round(straight,3),'stage10_nominal_cut_mm':w['wire_nominal_mm'],'stage10_tolerance_mm':w['wire_tolerance_mm'],
                'stage10_min_proxy_slack_mm':round(w['minimum_proxy_slack_mm'],3),'measured_path_mm':None,'chosen_cut_mm':None,'bend_radius_mm':None,
                'status':'STAGE10_PROPOSAL_UNMEASURED; fix only after M-09','proxy_intersections':screen(w['link'],a['pad_xyz_mm'],b['pad_xyz_mm'])},
            'anchor':{'position_mm':None,'status':'UNDETERMINED; define at fit-up (M-09/M-12)','load_path':'Mating/unmating force through the housing latch to the header and board; wire never pulled; anchor at the carrier near each housing to be defined'},
            'service':'Disconnect before core withdrawal' if w['link']=='K-PWR' else 'Disconnect via planned front/side access for front board service',
            'inspection':['I-CONT','I-ISO','I-IR','I-VIS','I-PULL','I-LATCH','I-FIX','I-LABEL'],'results':'NOT_RUN'})
    for t in tails:
        target=lands[t['target_land_id']];source=lands.get(t['from_LED_land_id']) if t['from_LED_land_id'] else None
        need(target['net']==t['net'] and target['xyz_mm']==t['to_xyz_mm'],'fixed tail land moved '+t['target_land_id'])
        need(source is None or (source['net']==t['net'] and source['xyz_mm']==t['from_xyz_mm']),'fixed LED land moved '+t['ref'])
        far=tp['TAIL:'+t['target_land_id']];near=tp.get('TAIL:'+t['from_LED_land_id']) if source else None
        need(far[1]['pins']=={t['pin']:t['net']} and (near is None or near[1]['pins']=={t['pin']:t['net']}),'land annotation net '+t['ref'])
        guide=next(g for g in mech['carrier_wire_guides'] if g['land']==t['target_land_id'])
        need(0<guide['minimum_open_diameter_mm']<guide['nominal_bore_mm'],'Stage10 guide opening '+t['target_land_id'])
        straight=math.dist(t['from_xyz_mm'],t['to_xyz_mm']);ident=f"T-{t['ref']}-{t['pin']}"
        rows.append({'id':ident,'kind':'PERMANENT_TAIL','link':'TAIL','net':t['net'],'role':role(t['net']),
            'end_a':{'board':'A01-fixed','connector':t['ref'],'pin':t['pin'],'land':t['from_LED_land_id'] or 'jack terminal '+t['pin'],'annotation':near[0] if near else None,'pad_xyz_mm':t['from_xyz_mm']},
            'end_b':{'board':'A01-jack','connector':t['target_land_id'],'pin':t['pin'],'land_drill_mm':target['drill_mm'],'annotation':far[0],'pad_xyz_mm':t['to_xyz_mm']},
            'wire':{'awg_candidate':policy['tail']['candidate_awg'],'insulation_od_strictly_below_mm':guide['minimum_open_diameter_mm'],'clearance_mm':None,'selected_mpn':None,'status':'PROPOSAL_UNCONFIRMED (Q-H02/Q-H03)'},
            'termination':{'a':'factory solder','b':'factory solder','status':'VENDOR_TO_COMPLETE (Q-H03); no owner soldering'},
            'marking':{'conductor_id':ident,'pin1':'ID sleeve at both ends; jack S/T and LED K/A named on label'},
            'polarity':{'map':'one conductor, distinct net','contact_view':'LED pin 1 cathode / pin 2 anode per ledger; jack S sleeve, T tip','keying':'none; ledger continuity test M-11 required'},
            'geometry':{'straight_pad_distance_mm':round(straight,3),'stage10_nominal_cut_mm':t['wire_nominal_mm'],'stage10_tolerance_mm':t['wire_tolerance_mm'],
                'stage10_min_proxy_slack_mm':round(t['minimum_straight_proxy_slack_mm'],3),'measured_path_mm':None,'chosen_cut_mm':None,'bend_radius_mm':None,
                'status':'STAGE10_PROPOSAL_UNMEASURED; fix only after M-09','proxy_intersections':screen('TAIL',t['from_xyz_mm'],t['to_xyz_mm'])},
            'anchor':{'position_mm':None,'guide_xy_mm':guide['xy_mm'],'guide_z_mm':guide['z_mm'],'guide_min_open_mm':guide['minimum_open_diameter_mm'],
                'status':'Stage10 carrier guide candidate; insulation retention UNQUALIFIED','load_path':'Wire to carrier guide bore to carrier rails to enclosure cleats; solder joint not credited as anchor'},
            'service':'Permanent; front assembly removed as a whole, no home soldering',
            'inspection':['I-CONT','I-ISO','I-IR','I-VIS','I-FIX','I-LABEL'],'results':'NOT_RUN'})
    nets={}
    for r in rows:nets.setdefault(r['net'],[]).append(r['id'])
    need(len({r['id'] for r in rows})==34,'34 unique conductors')
    for r in rows:
        g=r['geometry'];need(g['measured_path_mm'] is None and g['chosen_cut_mm'] is None and g['bend_radius_mm'] is None and r['anchor']['position_mm'] is None,'unmeasured value must remain null '+r['id'])
    return rows


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed')
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed={'scripts/architecture278/implementation/'+n for n in ('stage28_din_harness.py','test_stage28_din_harness.py')}
    need(all(p.startswith(REL+'stage28/') or p in allowed for p in new),'out-of-scope addition')
    return BASE


def load():
    return {'din':read(OUT/'din-requirements.json'),'policy':read(OUT/'harness-policy.json'),'questions':read(OUT/'questions.json'),
        'measurements':read(OUT/'measurements.json'),'sources':read(OUT/'sources.json'),'evidence':read(ROOT/REL/'stage22/evidence.json'),
        'mech':read(ROOT/REL/'stage10/mechanical-report.json'),'interfaces':read(ROOT/REL/'stage15/interfaces-report.json'),
        'inventory':read(ROOT/REL/'stage21/inventory-input.json'),'lock':read(ROOT/'design/grid/placements.lock.json'),
        'o1':read(ROOT/REL/'cluster-refinement-report.json')}


def build(data,cache=False,preserve=True):
    validate_sources(data['sources'],cache)
    ids=validate_policy(data['policy'],data['questions'],data['measurements'],data['din'])
    facts=frame_facts(data['lock'],data['mech'])
    need(data['interfaces']['DIN_pinmap']==data['mech']['din_connectors']['middle']['pins']==data['mech']['din_connectors']['rear']['pins'],'DIN ledger/mechanics pin map')
    din,contacts=din_analysis(data['evidence'],data['mech'],data['inventory'],data['interfaces'],facts)
    d02=next(r for r in data['din']['rows'] if r['id']=='D02')
    need((d02['status']=='CONFLICT_REQUIRES_DECISION')==din['mirror_conflict'],'D02 status must follow the computed handedness result')
    rows=harness(data['interfaces'],data['mech'],data['inventory'],data['policy'])
    trims=[p for p in data['o1']['placements'] if p.get('trim_tool_diameter_mm')]
    need(len(trims)==6 and all(p['rear_facing'] and p['trim_tool_diameter_mm']==6 for p in trims),'O1 rear trimmer reservations retained')
    ledger={'status':'HARNESS_LEDGER_CANDIDATE_NOT_ADOPTED','scope':'A01 representative transport contract (Stage15 interfaces = Stage16 transport_contract)',
        'conductors':rows,'din_contacts':contacts,'exclusions':data['policy']['exclusions'],
        'counts':{'GH_harnesses':4,'GH_conductors':20,'permanent_tails':14,'conductors':34,'DIN_contacts':96,'DIN_assigned':16,'DIN_NC':80,'land_annotations':22,
            'source_NC_endpoints':len(data['interfaces']['NC_source_endpoints'])},
        'source_NC_endpoints':data['interfaces']['NC_source_endpoints'],'physical':'NOT_RUN'}
    roles={}
    for r in rows:roles[r['role']]=roles.get(r['role'],0)+1
    report={'status':'SOURCE_SPECIFICATION_CANDIDATE; MANUFACTURING AND HARNESS UNCONFIRMED','din':din,
        'decision_status':{r['id']:r['status'] for r in data['din']['rows']},'conductor_roles':roles,
        'proxy_intersections':{r['id']:r['geometry']['proxy_intersections'] for r in rows if r['geometry']['proxy_intersections']},
        'o1_rear_trimmers':sorted(p['ref'] for p in trims),'questions':len(data['questions']['questions']),'measurements':len(data['measurements']['measurements']),
        'referenced_ids':sorted(ids),'native_request':'NONE','native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE',
        'production_CAD_changed':False,'architecture_adopted':False,'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('din-requirements.json','harness-policy.json','questions.json','measurements.json','sources.json','README.md')]
    files+=[ROOT/REL/p for p in ('stage22/evidence.json','stage10/mechanical-report.json','stage10/mechanical-input.json','stage15/interfaces-report.json','stage21/inventory-input.json','stage5/din-evidence.json','cluster-refinement-report.json','stage25/fabrication-request.md')]
    files+=[ROOT/'design/grid/placements.lock.json',ROOT/'design/connectors/sources/jst-gh.pdf',Path(__file__),Path(__file__).with_name('test_stage28_din_harness.py'),Path(__file__).with_name('stage22_requirements.py'),Path(__file__).with_name('check_source.py')]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    report['ledger_sha256']=hashlib.sha256(dump(ledger).encode()).hexdigest()
    return ledger,report


def esc(s):return html.escape(str(s),quote=True)


def cell(v):return esc(v).replace('|','\\|').replace('\n',' ')


def render_decisions(din,questions):
    q={x['id']:x for x in questions['questions']}
    lines=['# DIN manufacturing decision table','','Generated by `stage28_din_harness.py` from `din-requirements.json`. **No row is a pass.** Statuses: CONFIRMED_FROM_DRAWING means the requirement text is read from the HARTING drawing, not that a board conforms.','',
        '| ID | Topic | Requirement | Status | Current interpretation | Confirmed | Unconfirmed | Ask | Pass evidence |','|---|---|---|---|---|---|---|---|---|']
    for r in din['rows']:
        lines.append('| '+' | '.join([r['id'],cell(r['topic']),cell(r['requirement']),'**'+r['status']+'**',cell(r['current_interpretation']),cell('; '.join(r['confirmed'])),cell('; '.join(r['unconfirmed'])),
            ', '.join(r['confirmation_needed']) or '—',', '.join(r['pass_evidence'])])+' |')
    lines+=['','Primary sources: see `sources.json` (dated SHA-256 receipts). Questions: `questionnaire.md`. Measurements: `measurement-checklist.md`.','']
    return '\n'.join(lines)


def render_ledger(ledger):
    lines=['# A01 harness ledger (vendor-terminated, vendor-tested candidate)','','Generated. Lengths are Stage10 **proposals** and straight-line proxies; measured path, cut length, bend radius and anchor position are `null` until M-09/M-12. All inspection results are NOT_RUN.','',
        '## Conductors','','| ID | Role | Net | End A | End B | Wire | Straight mm | Stage10 cut ±tol | Proxy hits | Inspection |','|---|---|---|---|---|---|---|---|---|---|']
    for r in ledger['conductors']:
        a,b,w,g=r['end_a'],r['end_b'],r['wire'],r['geometry']
        lines.append('| '+' | '.join([r['id'],r['role'],cell(r['net']),cell(f"{a['board']} {a['connector']}:{a['pin']}"),cell(f"{b['board']} {b['connector']}:{b['pin']}"),
            cell(f"AWG{w['awg_candidate']} cand., MPN none"),f"{g['straight_pad_distance_mm']:.1f}",f"{g['stage10_nominal_cut_mm']}±{g['stage10_tolerance_mm']}",cell(', '.join(g['proxy_intersections']) or '—'),' '.join(r['inspection'])])+' |')
    lines+=['','## DIN mated contacts (J17909 middle ↔ J17910 core)','','Labels are the Stage10 labels. See report.json `din.mirror_conflict` before using any XY for copper.','','| Label | Net | Role | Stage10 XY mm | Inspection |','|---|---|---|---|---|']
    for c in ledger['din_contacts']:
        lines.append(f"| {c['label']} | {cell(c['net'] or 'NC')} | {c['role']} | {c['stage10_xy_mm'][0]:.2f}, {c['stage10_xy_mm'][1]:.2f} | {' '.join(c['inspection'])} |")
    lines+=['','## Excluded scope','']+[f"- **{cell(e['scope'])}** — {cell(e['reason'])}" for e in ledger['exclusions']]+['',f"Source NC endpoints retained: {', '.join(ledger['source_NC_endpoints'])}.",'']
    return '\n'.join(lines)


def render_questions(questions):
    lines=['# Unsent questionnaire','','**Not sent. No supplier, fabricator or manufacturer has been contacted.** Each question lists what is decided after the answer.','']
    order=['CONNECTOR_MANUFACTURER','PCB_FABRICATOR','PCB_ASSEMBLER','HARNESS_MAKER','OWNER']
    for rec in order:
        lines+=['## '+rec.replace('_',' ').title(),'']
        for q in questions['questions']:
            if q['recipient']!=rec:continue
            lines+=[f"### {q['id']}",'',cell(q['ask']),'',f"Why: {cell(q['why'])}",'']+[f"- If **{cell(d['if'])}** → {cell(d['then'])}" for d in q['decision']]+['']
    return '\n'.join(lines)


def render_measurements(measurements):
    lines=['# Minimum physical measurement checklist','','All items **NOT RUN**. Unpowered mechanical/inspection checks only; no energization is part of this list.','','| ID | Where | Method | Acceptance | Record |','|---|---|---|---|---|']
    for m in measurements['measurements']:
        lines.append('| '+' | '.join([m['id'],cell(m['where']),cell(m['method']),cell(m['acceptance']),cell(', '.join(m['record']))])+' |')
    return '\n'.join(lines+[''])


def render_svg(mech,ledger,report):
    sx=lambda x:20+(x-190)*3;sy=lambda y:60+(y-85)*3;ez=lambda z:450+z*3
    colors={'J-SIG':'#1f77b4','J-PWR':'#d62728','C-SIG':'#2ca02c','K-PWR':'#9467bd','TAIL':'#8c564b'}
    o=['<svg xmlns="http://www.w3.org/2000/svg" width="820" height="770" viewBox="0 0 820 770" font-family="sans-serif" font-size="9">',
       '<rect width="820" height="770" fill="#ffffff"/>',
       '<text x="20" y="18" font-size="13" font-weight="bold">A01 assembly drawing CANDIDATE — straight-line proxies, not routed, not measured, not for fabrication</text>',
       f"<text x=\"20\" y=\"34\">Plan: locked front view (x right, y down). Elevation: z toward rear. DIN handedness conflict: {'YES' if report['din']['mirror_conflict'] else 'NO'} (see report.json).</text>",
       '<text x="20" y="48">Rear service: disconnect K-PWR, release captive screws, withdraw core 40 mm by handles. O1 rear trimmer tool cylinders (6) are outside this frame and must stay clear in any O1 harness.</text>']
    for name,b in sorted(mech['boards'].items()):
        x0,y0,x1,y1=b['outline_mm'];o.append(f'<rect x="{sx(x0)}" y="{sy(y0)}" width="{(x1-x0)*3}" height="{(y1-y0)*3}" fill="none" stroke="#555" stroke-width="1"/><text x="{sx(x0)+2}" y="{sy(y0)+10}">{esc(name)} z{b["z_mm"]}</text>')
        o.append(f'<rect x="{ez(b["z_mm"][0])}" y="{sy(y0)}" width="{max(3,(b["z_mm"][1]-b["z_mm"][0])*3)}" height="{(y1-y0)*3}" fill="#ddd" stroke="#555"/>')
    for s in mech['connector_release_sweeps']:
        x0,y0,x1,y1=s['box_mm'];o.append(f'<rect x="{sx(x0)}" y="{sy(y0)}" width="{(x1-x0)*3}" height="{(y1-y0)*3}" fill="none" stroke="#e377c2" stroke-dasharray="3,2"/>')
    for m in mech['mounts']:
        x,y=m['xy_mm'];o.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="9" fill="none" stroke="#ff7f0e" stroke-dasharray="2,2"/>')
    for h in mech['service']['core_handles']:
        x,y=h['xy_mm'];o.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="{h["attachment_radius_mm"]*3}" fill="#bcbd22"/>')
        o.append(f'<rect x="{ez(h["rear_projection_z_mm"][0])}" y="{sy(y)-4}" width="{(h["rear_projection_z_mm"][1]-h["rear_projection_z_mm"][0])*3}" height="8" fill="#bcbd22"/>')
    core=mech['boards']['A01-core'];o.append(f'<rect x="{ez(core["z_mm"][1])}" y="{sy(core["outline_mm"][1])}" width="120" height="{(core["outline_mm"][3]-core["outline_mm"][1])*3}" fill="none" stroke="#9467bd" stroke-dasharray="6,3"/><text x="{ez(core["z_mm"][1])+4}" y="{sy(core["outline_mm"][1])-4}">core withdrawal 40 mm</text>')
    for c in ledger['din_contacts']:
        x,y=c['stage10_xy_mm'];o.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="1.4" fill="{"#000" if c["net"] else "#aaa"}"/>')
    for lab,dx,dy in (('a1',4,12),('c1',-70,12),('a32',4,-4)):
        x,y=next(c['stage10_xy_mm'] for c in ledger['din_contacts'] if c['label']==lab);o.append(f'<text x="{sx(x)+dx}" y="{sy(y)+dy}" fill="#c00">{lab} (Stage10 label)</text>')
    led=mech['fixed_LED_substrate'];x0,y0,x1,y1=led['outline_mm']
    o.append(f'<rect x="{sx(x0)}" y="{sy(y0)}" width="{(x1-x0)*3}" height="{(y1-y0)*3}" fill="none" stroke="#8c564b"/><rect x="{ez(led["z_mm"][0])}" y="{sy(y0)}" width="{(led["z_mm"][1]-led["z_mm"][0])*3}" height="{(y1-y0)*3}" fill="#e8d8c8" stroke="#8c564b"/>')
    o.append(f'<text x="{ez(0)}" y="72" font-weight="bold">Elevation: z horizontal (front left, rear right), y shared with plan</text>')
    for h in mech['DIN_flange_holes']:
        x,y=h['point_mm'];o.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="{1.4*3}" fill="none" stroke="#000"/>')
    o.append(f'<rect x="{ez(50)}" y="{sy(181)}" width="{19.2*3}" height="{94*3}" fill="#cfe" stroke="#088"/><text x="{ez(50)+2}" y="{sy(181)-4}">DIN mated 50–69.2</text>')
    for g in mech['carrier_wire_guides']:
        x,y=g['xy_mm'];o.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="2" fill="none" stroke="#8c564b"/>')
    for r in ledger['conductors']:
        a,b=r['end_a']['pad_xyz_mm'],r['end_b']['pad_xyz_mm'];col=colors[r['link']]
        o.append(f'<line x1="{sx(a[0])}" y1="{sy(a[1])}" x2="{sx(b[0])}" y2="{sy(b[1])}" stroke="{col}" stroke-width="0.8"/>')
        o.append(f'<line x1="{ez(a[2])}" y1="{sy(a[1])}" x2="{ez(b[2])}" y2="{sy(b[1])}" stroke="{col}" stroke-width="0.8"/>')
    for i,(k,c) in enumerate(colors.items()):
        o.append(f'<line x1="{20+i*110}" y1="745" x2="{40+i*110}" y2="745" stroke="{c}" stroke-width="2"/><text x="{44+i*110}" y="748">{k} proxy</text>')
    o.append('<text x="20" y="762">Dashed pink: connector release sweeps. Dashed orange: mount tool access. Yellow: core handles. Brown rings: carrier wire guides. Grey dots: DIN NC contacts.</text>')
    for z in (0,20,40,60,80,100):o.append(f'<text x="{ez(z)}" y="58">z{z}</text>')
    return '\n'.join(o+['</svg>',''])


def outputs(ledger,report,data):
    return {'harness-ledger.json':dump(ledger),'report.json':dump(report),'din-decision-table.md':render_decisions(data['din'],data['questions']),
        'harness-ledger.md':render_ledger(ledger),'questionnaire.md':render_questions(data['questions']),
        'measurement-checklist.md':render_measurements(data['measurements']),'assembly-candidate.svg':render_svg(data['mech'],ledger,report)}


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage28-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/check_source.py'],cwd=checkout,check=True)
            subprocess.run([sys.executable,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage27_hf_trim.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage27 source checkpoint including historical checks')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage28/'+n for n in ('report.json','harness-ledger.json','din-decision-table.md','harness-ledger.md','questionnaire.md','measurement-checklist.md','assembly-candidate.svg')}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-cache','check-history','check-review'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.check_history:history()
    data=load();ledger,report=build(data,a.check_cache)
    for name,body in outputs(ledger,report,data).items():
        path=OUT/name
        if a.check:need(path.read_text()==body,'deterministic drift '+name)
        else:path.write_text(body)
    if a.check_review:review()
    print(f"PASS Stage28 source checks: 34 conductors / 96 DIN contacts; DIN handedness conflict={report['din']['mirror_conflict']}; manufacturing UNCONFIRMED; physical/native NOT RUN")


if __name__=='__main__':main()
