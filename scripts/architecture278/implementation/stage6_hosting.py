"""Complete X1 redesigned-front placement seed and middle-interface reservation.

No canonical writes, route/native/simulation calls or claimed installed fit.
"""
import argparse
from collections import Counter,defaultdict
import copy,hashlib,itertools,json,math,sys
from pathlib import Path
import assembly as a
sys.path.insert(0,str(a.ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator
import stage6_mechanical as mechanical

ROOT=a.ROOT
OUT=a.OUT/'stage6'
RAILS={'+12V','-12V','+5V','AGND'}

def need(ok,msg):
    if not ok:raise ValueError(msg)

def bbox(boxes,margin=0):
    return [min(b[0]for b in boxes)-margin,min(b[1]for b in boxes)-margin,max(b[2]for b in boxes)+margin,max(b[3]for b in boxes)+margin]

def overlap(x,y):return x[0]<y[2]and y[0]<x[2]and x[1]<y[3]and y[1]<x[3]

def live_packages(ledger):
    source={p['ref']:p for p in ledger['packages']if p['instance']=='X1'}
    fs,ins=specification();inst=next(i for i in ins if i.name=='X1');family=next(f for f in fs if f.name==inst.family)
    result={};indices=defaultdict(list)
    for index,u in enumerate(ledger['package_units']):
        if u['ref']in source:indices[u['ref']].append(index)
    for p in family.parts:
        ref=designator(p,inst);pins={pin:(n if n is None or n in family.global_nets else '/X1/'+n)for pin,n in p.pins.items()}
        attrs={k:v.replace('${SHEETNAME}','X1')for k,v in p.attributes.items()}
        q=result.setdefault(ref,{'ref':ref,'footprint':p.footprint,'owner':'front-jack'if attrs['BoardRegion']=='jack'else'front-control','pins':{},'units':[],'unit_pin_record_indices':indices[ref],'attributes':attrs})
        need(not set(q['pins'])&set(pins),'duplicate physical pin');q['pins'].update(pins);q['units'].append(p.unit)
        u=next(u for u in ledger['package_units']if u['ref']==ref and u['unit']==p.unit)
        need(u['pins']==pins,'live/source pin drift '+ref)
    need(set(result)==set(source)and len(result)==56,'complete X1 population')
    for ref,q in result.items():
        need(sorted(q['units'])==sorted(source[ref]['units']),'whole IC units')
        need(q['owner']==('front-jack'if source[ref]['current_board']=='JL'else'front-control'),'retained source host region drift')
    need(sum(len(q['units'])for q in result.values())==76,'unit inventory')
    return result,source

def validate(placed,packages,source,lock):
    need(set(placed)==set(packages),'missing/invented X1 package')
    for ref,p in placed.items():
        need(p['pins']==packages[ref]['pins']and sorted(p['units'])==sorted(packages[ref]['units']),'source connectivity/unit mutation')
        need(set(p['pads_mm'])==set(p['pins']),'incomplete actual pad inventory')
        need(p['owner']==packages[ref]['owner'],'package host changed')
        if ref in lock:need(p['origin_mm']==[lock[ref]['x_mm'],lock[ref]['y_mm']]and p['quarter_turn']==lock[ref]['rot_deg']//90,'fixed panel datum changed')
        if source[ref]['decouples_ref']:need(p['owner']==placed[source[ref]['decouples_ref']]['owner'],'bypass host split')

def build():
    files=[ROOT/'design/architecture-278/source-ledger.json',ROOT/'design/partition/floorplan-candidate.json',ROOT/'design/grid/placements.lock.json',a.OUT/'stage6/candidate-report.json',a.OUT/'assembly-report.json']
    ledger,floor,locked,prior,assembly=[json.loads(p.read_text())for p in files]
    packages,source=live_packages(ledger);seed={p['ref']:p for p in floor['placements']};lock={p['ref']:p for p in locked['placements']if p['block']=='X1'}
    need(len(locked['placements'])==438 and len(lock)==7,'fixed panel population')
    need(len(ledger['packages'])==5904 and len(ledger['package_units'])==8226 and len(ledger['functions'])==33,'whole instrument source population')
    placed={};footprints=set()
    for ref,p in packages.items():
        s=seed[ref];side='rear'if s['side']=='B.Cu'else'panel'
        shape=a.shape(ref,p);footprints.add(ROOT/shape['source'])
        q=a.located(a.face_shape(shape,side),[s['x_mm'],s['y_mm']],s['rotation_deg']//90,'X1-jack'if p['owner']=='front-jack'else'X1-control',side)
        q.update({'source_board':s['board'],'seed_source_placement':s,'conditional_pcb_depth_mm':20,'unit_pin_record_indices':p['unit_pin_record_indices'],'panel_uid':p['attributes'].get('PanelUid','')})
        placed[ref]=q
    inherited=copy.deepcopy(placed)
    # One bounded refinement: preserve the complete U3303/bypass cluster rigidly.
    shift=[111-placed['U3303']['origin_mm'][0],275-placed['U3303']['origin_mm'][1]]
    for ref in ('U3303','C3306','C3307'):
        q=placed[ref];q['origin_mm']=a.transform(q['origin_mm'],shift);q['box_mm']=a.box_transform(q['box_mm'],shift)
        q['pads_mm']={pin:[a.transform(x,shift)for x in pts]for pin,pts in q['pads_mm'].items()}
        q['through_pad_keepouts_mm']=[a.box_transform(b,shift)for b in q['through_pad_keepouts_mm']]
    resistor_refs=['R3309','R3310','R3311','R3312','R3313']
    shapes=[a.shape(ref,packages[ref])for ref in resistor_refs]
    obstacles=[placed[ref]['box_mm']for ref in ('SW608','U3303','C3306','C3307')]
    packed=a.pack(shapes,[87,267,122,292],obstacles,{r:[99.5,276]for r in resistor_refs},'X1-control',side='rear')
    for q in packed:
        old=placed[q['ref']];q.update({k:old[k]for k in ('source_board','seed_source_placement','conditional_pcb_depth_mm','unit_pin_record_indices','panel_uid')});placed[q['ref']]=q
    validate(placed,packages,source,lock)
    hosting_path=a.OUT/'stage5/hosting-options-report.json';hosting=json.loads(hosting_path.read_text())
    overlay=copy.deepcopy(hosting['options']['candidate_front_redesign']['assignments'])
    for ref,p in placed.items():overlay[ref]='stage6-'+p['board']
    need(set(overlay)=={p['ref']for p in ledger['packages']},'complete ownership overlay')
    need(all(overlay[r]==hosting['options']['candidate_front_redesign']['assignments'][r]for r in overlay if r not in placed),'unrelated host assignment changed')
    boards={}
    for board in ('X1-jack','X1-control'):
        rows=[p for p in placed.values()if p['board']==board];outline=bbox([p['box_mm']for p in rows],2)
        boards[board]={'refs':[p['ref']for p in rows],'outline_reservation_mm':outline,'depth_mm':20,'PCB_thickness_proposal_mm':1.6,'component_envelope_proposal_Z_mm':[15,26.6],
            'support_reservation':'2mm perimeter strip outside occupied courtyard bounding rectangle; no holes or load-bearing detail selected','support_attachment':None,'seated_panel_reach':'UNKNOWN;20mm matches candidate front plane, not proven hardware seating','status':'CONCRETE SOURCE PLACEMENT SEED; NOT FIT QUALIFIED'}
    bynet=defaultdict(list);nc=[]
    for ref,p in placed.items():
        for pin,net in p['pins'].items():
            row={'ref':ref,'pin':pin,'board':p['board'],'pads_xyz_mm':[xy+[20]for xy in p['pads_mm'][pin]]}
            (nc if net is None else bynet[net]).append(row)
    cross={net:ends for net,ends in bynet.items()if net not in RAILS and len({e['board']for e in ends})>1}
    # Reserved interface region only: these are NOT pads or a selected connector.
    region=[110,155,122,275];middle={};pathrows=[]
    for index,(net,ends)in enumerate(sorted(cross.items())):
        handoffs={'X1-jack':[112+index*3,157,50],'X1-control':[112+index*3,273,50]}
        middle[net]={'source_endpoints':ends,'virtual_handoffs_xyz_mm':handoffs,'reservation_only':True,'connector_pads':None,'route_RLC':None,'electrical_budget_status':'UNKNOWN; retain original source behavior; no300mm whole-path acceptance invented'}
        for u,v in itertools.product([e for e in ends if e['board']=='X1-jack'],[e for e in ends if e['board']=='X1-control']):
            points=[u['pads_xyz_mm'][0],handoffs['X1-jack'],handoffs['X1-control'],v['pads_xyz_mm'][0]]
            pathrows.append({'net':net,'from':u['ref']+':'+u['pin'],'to':v['ref']+':'+v['pin'],'direct_pad_separation_mm':math.dist(points[0],points[-1]),'via_reserved_handoffs_straight_sum_mm':sum(math.dist(p,q)for p,q in zip(points,points[1:])),'complete_developed_budget_mm':None,'wire_cut_allocation_mm':None,'contacts_traces_returns_parasitics':'UNASSIGNED; geometric sensitivity only, not routed length or qualification'})
    need(len(cross)<=4,'interface reservation capacity requires review')
    rail_interface={net:{'source_endpoints':bynet[net],'middle_handoff_xyz_mm':[112+i*2,215,50],'reservation_only':True,'source_connector_or_regulator_placement':None,'branch_current_A':None,'contact_resistance_ohm':None,'return_error_V':None,'status':'all source rail/AGND endpoints retained; complete common POWER distribution UNKNOWN'}for i,net in enumerate(sorted(RAILS&set(bynet)))}
    returns={board:[e for e in bynet['AGND']if e['board']==board]for board in boards}
    bypass=[]
    for ref,p in source.items():
        if not p['decouples_ref']:continue
        target=p['decouples_ref'];distances={}
        for net in RAILS:
            left=[xy for pin,n in placed[ref]['pins'].items()if n==net for xy in placed[ref]['pads_mm'][pin]];right=[xy for pin,n in placed[target]['pins'].items()if n==net for xy in placed[target]['pads_mm'][pin]]
            if left and right:distances[net]=min(math.dist(x,y)for x,y in itertools.product(left,right))
        bypass.append({'capacitor':ref,'target':target,'owner':placed[ref]['owner'],'same_net_nearest_pad_mm':distances,'loop_status':'SOURCE ASSOCIATION/PAD PROXIMITY; AGND matches include grounded signal inputs, not an asserted dedicated supply-return pin. Return route/loop inductance UNKNOWN'})
    need(len(bypass)==10,'all X1 bypass associations')
    internal=[];foreign=[];support=[];middle_conflicts=[]
    for p,q in itertools.combinations(placed.values(),2):
        if p['board']==q['board']and overlap(p['box_mm'],q['box_mm']):internal.append({'a':p['ref'],'b':q['ref'],'same_face':p['side']==q['side'],'status':'same-face conflict'if p['side']==q['side']else'opposite-face XY overlap; actual solids/drills UNKNOWN'})
    for board,b in boards.items():
        for p in floor['placements']:
            if p['ref']in placed:continue
            if overlap(b['outline_reservation_mm'],p['courtyard_mm']):foreign.append({'board':board,'historical_ref':p['ref'],'historical_board':p['board'],'same_retained_board':p['board']==('JL'if board=='X1-jack'else'P'),'new_candidate_depth_mm':None,'scope':'historical XY intersection only; not a proven3Dcollision; new other-function depth/placement UNKNOWN'})
    existing_front=[p for group in assembly['front_instances'].values()for p in group]
    osc_front=[{'board':board,'existing_ref':p['ref'],'existing_instance':p['instance'],'overlap':'XY board envelope atfront; package depths retained separately'}for board,b in boards.items()for p in existing_front if overlap(b['outline_reservation_mm'],p['box_mm'])]
    middle_parts=prior['candidate']['middle_header_placements_all_instances']
    for p in middle_parts:
        if overlap(region,p['box_mm']):middle_conflicts.append({'ref':p['ref'],'instance':p['instance'],'type':'existing transport header atmiddle'})
    for p in assembly['shared_middle_placements']:
        box=a.box_transform(p['box_mm'],[6,0])
        if overlap(region,box):middle_conflicts.append({'ref':p['ref'],'type':'existing shared package atmiddle'})
    for inst,origin in prior['candidate']['origins_mm'].items():
        for fixture in prior['candidate']['fixtures']:
            box=a.box_transform(fixture['box_mm'],origin)
            if overlap(region,box):middle_conflicts.append({'ref':fixture['id'],'instance':inst,'box_mm':box,'type':'existing rear fixture projection; DIN spansmiddle, otherfixture ZextentUNKNOWN'})
    # Perimeter strips are reserved for support, never credited as installed hardware.
    all_hardware=a.locked_hardware(locked['placements'])
    for board,b in boards.items():
        x0,y0,x1,y1=b['outline_reservation_mm'];strips=[[x0,y0,x1,y0+2],[x0,y1-2,x1,y1],[x0,y0+2,x0+2,y1-2],[x1-2,y0+2,x1,y1-2]]
        b['support_perimeter_strips_mm']=strips
        for obstacle in all_hardware:
            if any(overlap(strip,obstacle['box_mm'])for strip in strips):support.append({'board':board,'fixed_ref':obstacle['ref'],'fixed_uid':obstacle['uid'],'status':'supportstrip/fixedhardware XYintersection; loads/Z UNKNOWN'})
    support_package_hits=[{'board':b,'ref':p['ref']}for b,q in boards.items()for p in placed.values()if p['board']==b and any(overlap(strip,p['box_mm'])for strip in q['support_perimeter_strips_mm'])]
    spec_path=OUT/'mechanical-input.json';official_path=a.OUT/'stage5/din-evidence.json'
    contacts,flanges=mechanical.register(prior['candidate'],json.loads(spec_path.read_text()),json.loads(official_path.read_text()))
    middle_drill_hits=[p for p in contacts+flanges if mechanical.tail_circle_overlap(*p['point_mm'],region,p['radius_mm'])]
    board_pairs=[{'boards':[x,y],'XY_intersection':overlap(boards[x]['outline_reservation_mm'],boards[y]['outline_reservation_mm']),'proposed_Z_intersection':max(boards[x]['component_envelope_proposal_Z_mm'][0],boards[y]['component_envelope_proposal_Z_mm'][0])<min(boards[x]['component_envelope_proposal_Z_mm'][1],boards[y]['component_envelope_proposal_Z_mm'][1])}for x,y in itertools.combinations(boards,2)]
    span_changes=[]
    for net,ends in bynet.items():
        if net in RAILS:continue
        def span(pop):return max((math.dist(pop[x['ref']]['pads_mm'][x['pin']][0],pop[y['ref']]['pads_mm'][y['pin']][0])for x,y in itertools.combinations(ends,2)),default=0)
        old,new=span(inherited),span(placed)
        span_changes.append({'net':net,'source_endpoint_count':len(ends),'before_max_pad_separation_mm':old,'after_max_pad_separation_mm':new,'delta_mm':new-old,'status':'all local/feedback/summing nodes included; no route/loopstability implication'})
    local={n:{'nodes':e,'max_pad_separation_mm':max((math.dist(x['pads_xyz_mm'][0],y['pads_xyz_mm'][0])for x,y in itertools.combinations(e,2)),default=0),'status':'complete node inventory; pair span not route budget'}for n,e in bynet.items()if n not in RAILS and n not in cross}
    files += [hosting_path,OUT/'scope.json',spec_path,official_path,Path(mechanical.__file__),ROOT/'scripts/architecture278/implementation/stage4_mechanical.py',Path(__file__),Path(__file__).with_name('test_stage6_hosting.py'),Path(a.__file__),Path(a.c.__file__),ROOT/'scripts/architecture278/populated_mechanics.py',ROOT/'design/spec/instrument.py']+sorted(footprints)
    # Family source filename can differ; bind every module used by specification conservatively.
    files=files+sorted((ROOT/'design/spec/modules').glob('*.py'))+[ROOT/p['source']for p in all_hardware]
    return {'status':'X1 COMPLETE REDESIGNED FRONT HOSTING INCREMENT; ACCEPTANCE OPEN','source_sha256':a.binding(files),'counts':{'packages':56,'units':76,'fixed_X1_centres':7,'instrument_fixed_centres':438,'instrument_functions':33,'bypass_associations':10,'jack_packages':47,'control_packages':9,'other_K_packages_still_unhosted':2572,'POWER_packages_still_unhosted':13},
        'placements':placed,'inherited_seed_placements':inherited,'whole_instrument_host_overlay':overlay,'all_nonrail_net_span_changes':span_changes,'boards':boards,'source_pins_including_NC':sum(len(p['pins'])for p in placed.values()),'NC_endpoints':nc,'local_net_nodes':local,'cross_board_signal_interfaces':middle,'crossing_geometric_sensitivities':pathrows,'rail_interfaces':rail_interface,'AGND_return_endpoint_groups':returns,'bypass_associations':bypass,
        'middle_reservation':{'box_mm':region,'depth_mm':50,'volume_Z_mm':[48.4,55],'status':'INTERFACE/POWER/RETURN RESERVATION ONLY; no new connector or routed topology','handoff_capacity':4,'signal_handoffs_used':len(cross),'shared_reference_and_OSC_geometry_unchanged':True},
        'obstruction_screen':{'internal_courtyard_pairs':internal,'board_pair_screens':board_pairs,'support_perimeter_fixed_hardware_intersections':support,'support_perimeter_own_package_intersections':support_package_hits,'middle_registered_DIN_hole_pad_intersections':middle_drill_hits,'middle_DIN_screen_count':len(contacts)+len(flanges),'historical_foreign_XY_intersections':foreign,'existing_OSC_front_envelope_intersections':osc_front,'existing_middle_reservation_intersections':middle_conflicts,'within_panel':{b:a.inside(x['outline_reservation_mm'],[0,0,318,298])for b,x in boards.items()},'new_other_function_occupied_geometry':None,'full3Dfit':'UNKNOWN','support_and_drill_proof':'NOT RUN'},
        'unchanged_OSC_evidence':{'path':'design/architecture-278/implementation/stage6/candidate-report.json','sha256':hashlib.sha256(files[3].read_bytes()).hexdigest(),'crossings':len(prior['candidate']['paths']),'returns':len(prior['candidate']['returns'])},
        'scope':'New source candidate host definitions use retainedXY/rotation as seeds, not mandatory reuse of oldJL/P copper. All56packages/76units/pins/spares/bypasses preserved. OtherK/POWER volumes stay unknown; X1 hasnoK population. No route acceptance from source inventory or historical coordinates. Middlevirtualhandoffs are geometryreservations notphysicalpads.',
        'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','adopted':False,'qualified_free_regions':[]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();out=OUT/'hosting-report.json';data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n'
    if args.check:need(out.read_text()==data,'stale stage6 hosting report')
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(data)
    print('X1 hosting56packages76units7fixed10bypasses; candidate placement/interfaces only; allqualification OPEN')
