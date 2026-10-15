"""Source-only hosting/reuse options. No adopted repartition, native or CAD edits."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import stage3_reservations as geometry

ROOT=geometry.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage5'
OSC={f'O{i}' for i in range(1,6)}


def need(ok,message):
    if not ok:raise ValueError(message)


def bucket(p):
    return 'OSC' if p['instance'] in OSC else p['instance'] if p['instance'] in ('OCTAVE_REF','POWER') else 'other28'


def assignments(packages,mode):
    result={}
    for ref,p in packages.items():
        board=p['current_board'];kind=bucket(p)
        if mode=='historical_whole_instrument':host='historical:'+board
        elif board=='K':
            host='proposed-OSC-core:'+p['instance'] if kind=='OSC' else 'proposed-shared-middle' if kind=='OCTAVE_REF' else 'proposed-POWER-service' if kind=='POWER' else 'proposed-nonOSC-carrier'
        elif mode=='core_only_front_reuse':host='historical:'+board
        elif kind=='OSC':host='proposed-OSC-front-jack' if board in ('JL','JR') else 'proposed-OSC-front-control' if board=='P' else 'proposed-selector:'+p['instance']
        elif board in ('JL','P'):host='proposed-other-front:'+board
        else:host='historical:'+board
        result[ref]=host
    return result


def bypasses(packages):
    rows=[(ref,p['decouples_ref']) for ref,p in packages.items() if p['decouples_ref']]
    assembly=json.loads((ROOT/'design/architecture-278/implementation/assembly-report.json').read_text())
    rows += [(x['capacitor'],x['package']) for x in assembly['bypass_associations'] if x['owner']=='shared-reference']
    need(len(rows)==len(set(rows))==1067,'complete bypass association inventory')
    return rows


def validate_assignment(mapping,packages,mode):
    need(set(mapping)==set(packages),'whole physical package omitted or invented')
    for ref,target in bypasses(packages):
        need(mapping[ref]==mapping[target],'bypass target split between hosts')
    expected=assignments(packages,mode)
    need(mapping==expected,'declared source ownership option violated')
    if mode=='core_only_front_reuse':
        need(all(mapping[ref]=='historical:'+p['current_board'] for ref,p in packages.items() if p['current_board']!='K'),'partial front copper reuse')
    if mode=='candidate_front_redesign':
        need(all(not mapping[ref].startswith('historical:') for ref,p in packages.items() if p['current_board'] in ('JL','P')),'mixed front board silently retained')


def build():
    ledger_path=ROOT/'design/architecture-278/source-ledger.json'
    ledger=json.loads(ledger_path.read_text());packages={p['ref']:p for p in ledger['packages']}
    need(len(packages)==5904 and sum(len(p['units']) for p in packages.values())==8226,'source population changed')
    other={f['id'] for f in ledger['functions'] if f['family']!='OSC'};need(len(other)==28,'function coverage')
    units=defaultdict(list)
    for i,u in enumerate(ledger['package_units']):units[u['ref']].append(i)
    for ref,p in packages.items():need(Counter(p['units'])==Counter(ledger['package_units'][i]['unit'] for i in units[ref]),'whole units changed')
    k_other={ref:p for ref,p in packages.items() if p['instance'] in other and p['current_board']=='K'}
    power={ref:p for ref,p in packages.items() if p['instance']=='POWER'}
    need(len(k_other)==2572 and len(power)==13,'nonOSC/POWER coverage')
    board_matrix={board:dict(Counter(bucket(p) for p in packages.values() if p['current_board']==board)) for board in sorted({p['current_board'] for p in packages.values()})}
    groups=[]
    for name in sorted(other):
        pp={ref:p for ref,p in packages.items() if p['instance']==name}
        kk=[ref for ref in pp if pp[ref]['current_board']=='K']
        groups.append({'function':name,'K_refs':kk,'K_package_count':len(kk),'K_unit_count':sum(len(pp[ref]['units']) for ref in kk),
            'all_retained_board_counts':dict(Counter(p['current_board'] for p in pp.values())),
            'new_carrier_geometry':None,'new_carrier_service_volume':None,
            'interpretation':'source ownership group for planning carrier sector(s); not a chosen separate PCB or qualified shape'})
    options={}
    for mode in ('historical_whole_instrument','candidate_front_redesign','core_only_front_reuse'):
        assigned=assignments(packages,mode);validate_assignment(assigned,packages,mode)
        options[mode]={'assignments':assigned,'host_package_counts':dict(Counter(assigned.values())),
            'package_count':len(assigned),'unit_count':sum(len(packages[ref]['units']) for ref in assigned),
            'bypass_association_count':len(bypasses(packages)),
            'placement_status':'historical source comparison only' if mode=='historical_whole_instrument' else 'proposed source ownership only; new board/copper/occupied/service geometry unimplemented',
            'implemented':False,'adopted':False,'qualified_free_regions':[]}
    mech_path=ROOT/'design/partition/mechanical-candidate.json';mech=json.loads(mech_path.read_text())
    k=mech['K_rear'];board_path=ROOT/'design/boards/osc-core.json';kb=json.loads(board_path.read_text())
    rectangles=geometry.polygon_rectangles(kb['outline'])
    candidate_path=ROOT/'design/architecture-278/implementation/stage4/candidate-report.json'
    candidate=json.loads(candidate_path.read_text())['candidate']
    cards=candidate['geometry']['five_card_boxes_mm'];sweep=[]
    kinterval=[-k['face_z_mm'],-k['back_face_z_mm']]
    # Scope matches the retained source proposal: 1.6mm PCB plus5mm rear allowance.
    swept_interval=[69.2,69.2+1.6+5+40]
    for name,box in cards.items():
        hits=[geometry.intersection(box,r) for r in rectangles];hits=[h for h in hits if h]
        blocked=bool(hits) and swept_interval[0]<kinterval[1] and kinterval[0]<swept_interval[1]
        sweep.append({'instance':name,'card_xy_mm':box,'retained_K_intersections_mm':hits,'conditional_withdrawal_Z_mm':swept_interval,
            'historical_K_board_Z_mm':kinterval,'conditional_straight_withdrawal_conflict':blocked,
            'status':'declared envelope intersection, not tested service; historical K retained in place blocks this candidate straight withdrawal comparison'})
    historical={'K_package_count':sum(p['current_board']=='K' for p in packages.values()),
        'K_components_by_owner':board_matrix['K'],'K_source_face_depth_mm':-k['face_z_mm'],'K_source_back_depth_mm':-k['back_face_z_mm'],
        'rear_component_allowance_mm':k['component_height_ceiling_mm'],'conditional_rear_extent_mm':-k['back_face_z_mm']+k['component_height_ceiling_mm'],
        'candidate_cover_depth_mm':105,'historical_enclosure_depth_mm':k['enclosure_inside_depth_mm'],
        'candidate_cover_excess_mm':-k['back_face_z_mm']+k['component_height_ceiling_mm']-105,
        'historical_enclosure_nominal_clearance_mm':k['nominal_back_component_clearance_mm'],'service_checks':sweep,
        'warning':'More case depth can address rear static clearance but does not remove the K plane from straight rear extraction. Do not infer K depopulation/cutting/removal or transfer old receipts.'}
    paths=[Path(__file__),Path(__file__).with_name('test_stage5_hosting_options.py'),Path(geometry.__file__),ledger_path,mech_path,board_path,candidate_path,ROOT/'design/architecture-278/implementation/assembly-report.json',ROOT/'design/architecture-278/GATE.md',ROOT/'design/architecture-278/electrical.md',ROOT/'design/architecture-278/reuse.md']
    return {'status':'CONCRETE SOURCE HOSTING OPTIONS; NO REPARTITION IMPLEMENTED OR ADOPTED','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'unit_pin_record_source':{'path':str(ledger_path.relative_to(ROOT)),'sha256':hashlib.sha256(ledger_path.read_bytes()).hexdigest(),'array':'package_units','indexing':'zero-based; all pin/net/NC records retained unchanged'},
        'package_index':{ref:{'instance':p['instance'],'board':p['current_board'],'units':p['units'],'unit_pin_record_indices':units[ref],'decouples_ref':p['decouples_ref'],'DNP':p['dnp']} for ref,p in packages.items()},
        'counts':{'functions':33,'fixed_centres':438,'packages':5904,'units':8226,'other_functions':28,'other_K_packages':2572,'other_K_units':sum(len(p['units']) for p in k_other.values()),'POWER_packages':13,'front_packages':sum(p['current_board']!='K' for p in packages.values())},
        'bypass_associations':[{'capacitor':ref,'target':target} for ref,target in bypasses(packages)],'front_board_ownership_matrix':board_matrix,'nonOSC_source_groups':groups,'POWER_refs':sorted(power),
        'POWER_scope':'All13 retained packages remain together as a proposed service ownership group; upstream source/inlet/protection selection, new placement, source limits and complete rail/return graph OPEN.',
        'options':options,'historical_K_consequences':historical,
        'option_consequences':{
            'historical_whole_instrument':['Physically retaining unchanged K retains all3385 source packages, including770OSC and30shared; cannot call it a2572+13only carrier without a separately designed depopulation/replacement.','NewOSC cards cannot be counted as simultaneous replacements while oldOSC functions remain connected; duplicate ownership is not assumed.','Use as incumbent/control comparison or isolated external candidate testpiece only; inside-instrument coexistence requires explicit new geometry/electrical changes.'],
            'candidate_front_redesign':['Replace mixed JL/P source-board ownership explicitly: all1060JL and285P packages are accounted;285JL+35P OSC parts move to proposedOSC fronts,775JL+250Pother parts require source-preserving replacement fronts.','Keep all2572nonOSC K packages as a complete proposed carrier ownership group with per-function sector inventory; preserve whole packages/units/bypasses and local-net board invariants. No carrier outline/Z/support is asserted.','All13POWER and30shared packages have distinct source-complete ownership groups; no invented regulator/inlet placement, wiring or new purchased parts.','JR1031 andEL138 source packages remain historical ownership comparisons; installed coexistence remains unqualified. Five selectors remain one complete package per proposed adapter.'],
            'core_only_front_reuse':['Retain every2519frontpackage on originalJL/JR/P/EL/selector ownership, including mixed boards; preserve whole original frontcopper as comparison, not onlyOSC portion.','Reuse originalfrontinterfaces/depths/actualpads; currentcandidate20mmfront/JST regrouping and route totals are not automatically transferable. Define adapters and recompute completeharness/developed/capacitance/return metrics.','Still requires an explicit host for2572nonOSCK+13POWER and30shared after replacingOSCcore; oldK cannot be assumed physically gone.','May reduce frontcopper redesign scope, but no cost/time/BOM parity, adapterfit or electrical qualification follows.']},
        'recommendation':'For continuing the source comparison of the proposed front-redesign candidate, use the source-preserving nonOSC-carrier plus explicit mixed-front replacement groups as the next geometry input; first assign carrier/support/service solids and check interactions. Keep core-only full-front reuse as a comparison when reuse priority warrants it. Do not install or adopt either option from this inventory alone.',
        'not_qualified':['Replacement carrier(s) outline,PCB stack,Z,source-preserving local routing,bulk/support/connector quantities and solids','All otherfunctions/newPOWER/service occupied volumes and common power/return topology','Historical board removal/cutting/depopulation and cost/assembly comparison','Native/ERC/DRC/physical fit/service tests'],
        'native':'NOT RUN','physical':'NOT RUN'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r=build();path=OUT/'hosting-options-report.json';data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n'
    if args.check:need(path.read_text()==data,'stale hosting options')
    else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data)
    print('PASS3hosting options;5904packages8226units conserved;2572nonOSCK+13POWER explicit;2519front mixedownership; nofit/adoption')
