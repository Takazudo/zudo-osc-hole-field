#!/usr/bin/env python3
"""Generate the conditional board decision and strict board-definition handoff."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import math
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import JACK_BOARDS
from scripts.checks.connector_packing35 import board_for,partition_source_digest
from scripts.checks.partition35_loom import power_route_errors
from scripts.pcbgen.definition import load_definition


def read(path):return json.loads((ROOT/path).read_text())
def xy_digest(lock):return hashlib.sha256(json.dumps(sorted((p['uid'],p['x_mm'],p['y_mm']) for p in lock),separators=(',',':')).encode()).hexdigest()

def subtract_rect(rect,cut):
    x0,y0,x1,y1=rect;a,b,c,d=cut
    a=max(x0,a);b=max(y0,b);c=min(x1,c);d=min(y1,d)
    if a>=c or b>=d:return [rect]
    # Floating-point subtraction can leave a ~1e-14 mm high sliver. KiCad
    # rounds that to a zero-area DSN keepout, which the router then skips.
    return [r for r in ((x0,y0,a,y1),(c,y0,x1,y1),(a,y0,c,b),(a,d,c,y1)) if r[2]-r[0]>1e-7 and r[3]-r[1]>1e-7]

def jack_reservation_keepouts(reserves,locations,headers,terminals,board):
    """Retain gross reserves while excluding installed native-facing envelopes."""
    exclusions=[]
    for p in locations.values():
        if p['board']==board and p['fixed'] and (p['ref'].startswith('J') or p['ref'].startswith('D')):
            x0,y0,x1,y1=p['courtyard_mm']
            sides=('F.Cu','B.Cu') if p['ref'].startswith('J') else (p['side'],)
            exclusions.append((p['ref'],(x0-.05,y0-.05,x1+.05,y1+.05),sides,'source fixed hardware courtyard plus 0.05 mm native inflation'))
    for h in headers:
        if h['board']==board:
            x0,y0,x1,y1=h['native_cached_courtyard_envelope_mm']
            exclusions.append((h['pcb_reference'],(x0-.05,y0-.05,x1+.05,y1+.05),(h['side'],),'installed GH header native cached courtyard plus 0.05 mm margin'))
    for t in terminals:
        if t['board']==board:
            x,y=t['center_mm'];w,h=t['maximum_courtyard_mm'];exclusions.append((t['reference'],(x-w/2,y-h/2,x+w/2,y+h/2),('F.Cu','B.Cu'),'source 5 x 5 mm load-land courtyard'))
    keepouts=[];receipt=[]
    for reserve in reserves:
        for side in reserve['sides']:
            original=tuple(reserve['rect']);pieces=[original];used=[]
            cuts=[(ref,cut,basis) for ref,cut,sides,basis in exclusions if side in sides]
            if reserve['id'].startswith('future-'):
                cuts += [(r['id'],tuple(r['rect']),'other explicit same-face reservation') for r in reserves if r['id']!=reserve['id'] and side in r['sides']]
            for ref,cut,basis in sorted(cuts):
                before=sum((q[2]-q[0])*(q[3]-q[1]) for q in pieces)
                pieces=[piece for q in pieces for piece in subtract_rect(q,cut)]
                after=sum((q[2]-q[0])*(q[3]-q[1]) for q in pieces)
                if before-after>1e-8:used.append({'ref':ref,'courtyard_mm':list(cut),'area_removed_mm2':round(before-after,6),'basis':basis})
            original_area=(original[2]-original[0])*(original[3]-original[1]);remaining=sum((q[2]-q[0])*(q[3]-q[1]) for q in pieces)
            for i,q in enumerate(pieces,1):
                keepouts.append({'id':f"{reserve['id']}-{side.replace('.','')}-{i}",'polygon':[[q[0],q[1]],[q[2],q[1]],[q[2],q[3]],[q[0],q[3]]],'layers':[side]})
            receipt.append({'reserve_id':reserve['id'],'side':side,'original_rect_mm':list(original),'original_area_mm2':round(original_area,6),'removed_area_mm2':round(original_area-remaining,6),'remaining_area_mm2':round(remaining,6),'subtractions':used,'status':'PROPOSAL remaining allowance; #59 exact protection geometry OPEN'})
    return keepouts,receipt

def jack_bulk_conflicts(reserves,locations,headers,terminals,board):
    obstacles=[]
    for p in locations.values():
        if p['board']==board and (p['side']=='B.Cu' or p['fixed'] and p['ref'].startswith('J')):
            obstacles.append((p['ref'],p['courtyard_mm']))
    for h in headers:
        if h['board']==board:obstacles.append((h['id'],h['native_cached_courtyard_envelope_mm']))
    for t in terminals:
        if t['board']==board:
            x,y=t['center_mm'];w,h=t['maximum_courtyard_mm'];obstacles.append((t['reference'],(x-w/2,y-h/2,x+w/2,y+h/2)))
    errors=[]
    for r in reserves:
        if not r['id'].startswith('UNSELECTED-BULK-'):continue
        a=r['rect']
        if abs((a[2]-a[0])-5)>1e-8 or abs((a[3]-a[1])-3)>1e-8:errors.append(r['id']+' lost its full 5 x 3 mm slot')
        if a[0]<120 or a[1]<143 or a[2]>310 or a[3]>161:errors.append(r['id']+' leaves the J B-face protection/bulk reservation')
        for ref,b in obstacles:
            if a[0]<b[2]+.25 and a[2]>b[0]-.25 and a[1]<b[3]+.25 and a[3]>b[1]-.25:
                errors.append(r['id']+' collides with '+ref)
    return errors

def bulk_reserve_source_errors(board):
    named=[r for r in board.get('reserves',[]) if r['id'].startswith('UNSELECTED-BULK-')]
    slots=board.get('board_bulk_reserve',[])
    if len(named)!=len(slots):return ['bulk reserve count differs between reserves and board_bulk_reserve']
    errors=[]
    for index,(reserve,slot) in enumerate(zip(named,slots),1):
        if reserve['id']!=f'UNSELECTED-BULK-{index}' or reserve['rect']!=slot['rect'] or slot['side'] not in reserve['sides']:
            errors.append(f'UNSELECTED-BULK-{index} geometry differs between reserves and board_bulk_reserve')
    return errors


def validate_assignment(parts,assignments,io):
    errors=[];refs=Counter(r['ref'] for r in assignments)
    if refs!=Counter(p['ref'] for p in parts):errors.append('Every physical package must appear exactly once')
    boards={p['ref']:p['board'] for p in assignments}
    for group in io['islands']:
        if len({boards.get(r) for r in group['refs']})!=1:errors.append('split island '+str(group.get('island',group.get('island_id','unknown'))))
    for row in io['local_raw_sensitive_nets']:
        if len({boards.get(r) for r in row['refs']})!=1:errors.append('split local/sensitive net '+row['net'])
    for p in parts:
        if p['decouples_ref'] and boards.get(p['decouples_ref'])!=boards.get(p['ref']):errors.append('split bypass '+p['ref'])
    return errors

def jack_rail_polygons(board,distribution,board_key):
    """Finite inner-plane tails reach the three unchanged load lands.

    0.50 mm source gaps separate different rail polygons. Native 0.25 mm
    clearances and zone fill remain the oracle for the resulting copper.
    """
    x0=min(p[0] for p in board['outline']);x3=max(p[0] for p in board['outline'])
    x1=x0+(x3-x0)/3;x2=x0+2*(x3-x0)/3
    lands=distribution['branches'][board_key]['x_mm'];left=lands[1]-2.5;right=lands[2]-2.5
    return {
        '+12V':[[x0+.25,20],[x1-.25,20],[x1-.25,145],[left-.5,145],[left-.5,163.75],[x0+.25,163.75]],
        '-12V':[[x1+.25,20],[x2-.25,20],[x2-.25,157.5],[right,157.5],[right,163.75],[left,163.75],[left,145.5],[x1+.25,145.5]],
        '+5V':[[x2+.25,20],[x3-.25,20],[x3-.25,163.75],[right+.5,163.75],[right+.5,158],[x2+.25,158]],
    }


def build():
    source=read('design/partition/partition-input.json');io=read('design/reports/io-partition.json');lock=read('design/grid/placements.lock.json')['placements']
    floor=read('design/partition/floorplan-candidate.json');ports=read('design/partition/connector-packing-candidate.json');loom=read('design/partition/loom-candidate.json');optical=read('design/partition/stage-optical-candidate.json');gh=read('design/connectors/jst-gh.json')
    parts=io['physical_packages'];byref={p['ref']:p for p in parts};loc={p['ref']:p for p in floor['placements']}
    assignment=[{'ref':p['ref'],'board':board_for(p),'side':loc[p['ref']]['side'],'fitted':not p['dnp'],'source_region':p['regions'][0],'status':'DERIVED'} for p in parts]
    errors=validate_assignment(parts,assignment,io)
    for name,receipt in [('connectors',ports),('loom',loom)]:
        if receipt.get('partition_source_digest')!=partition_source_digest(source):errors.append(name+': partition source digest drift')
    errors.extend(power_route_errors(loom['load_power_routes'],source))
    mechanical=read('design/partition/mechanical-candidate.json')
    for name,report in [('floorplan',floor),('connectors',ports),('loom',loom),('mechanical',mechanical)]:
        errors.extend(name+': '+e for e in report['errors'])
    if len(lock)!=438 or len({p['block'] for p in lock})!=33:errors.append('fixed hardware/module roster mismatch')
    fitted_ics=sum(p['ref'].startswith('U') and not p['dnp'] for p in parts)
    if fitted_ics!=sum(read('design/reports/netlist-stats.json')['IC_count_by_part'].values()):errors.append('fitted IC count differs from regenerated netlist statistics')
    if xy_digest(lock)!=io['fixed_uid_xy_sha256']:errors.append('fixed UID/XY source digest drift')
    led=Counter(p['mpn'] for p in parts if p['panel_uid'].startswith('L:'))
    if led!={'APHHS1005QWF/D':104,'APG1005SEC/E-T':10}:errors.append('compact LED identity mismatch')
    locked={p['uid']:p for p in lock}
    for part in parts:
        if part['panel_uid']:
            b=board_for(part);want='O' if b.startswith('O') else b
            if locked[part['panel_uid']]['domain']!=want:errors.append('lockfile domain differs from board ownership '+part['ref'])
    expected={r['net'] for r in io['allowed_crossings'] if r['kind']!='power/return'}
    actual={s['net'] for h in ports['harnesses'] for s in h['signals']}
    if expected!=actual:errors.append('connector signal net coverage differs from source cut')
    pairrefs={p['net']:p for p in io['allowed_crossings']};connector=[];family={p['positions']:p for p in gh['sizes']}
    for port_index,port in enumerate(ports['headers']):
        row={**port,'pcb_reference':'J'+str(900001+port_index),'kicad_orientation_deg':port['kicad_orientation_deg'],'mechanical_pads':['MP1','MP2'],'mechanical_pad_nets':'unassigned; mechanical only','rotation_deg':port['rotation_deg'],'mated_height_mm':{'value':7.3,'status':'SOURCED reference, no tolerance'},'exact_source':'design/connectors/jst-gh.json','supply_domain':'EXT','pins':[]}
        row['field_status']={'header_mpn':'SOURCED','housing_mpn':'SOURCED','contact_mpn':'SOURCED','pin_map':'DERIVED','land_courtyard_mm':'DERIVED','center_mm':'PROPOSAL','rotation_deg':'PROPOSAL'}
        for pin,net in port['pin_map'].items():
            if net=='NC':direction='unwired';v=[0,0];current=0;basis='no crimp/wire fitted'
            elif net=='AGND':direction='bidirectional common return';v=[-.2,.2];current=500;basis='0.5 A/contact planning derating; actual parallel-path bounds below, no equal sharing'
            elif net in ('+12V','-12V','+5V'):
                direction='K source / EL receiver';v=[0,5.5] if net=='+5V' else [0,13.2] if net=='+12V' else [-13.2,0];current=70;basis='entire EL rail upper contract; each individual branch allowed to carry total, no equal sharing'
            else:
                r=pairrefs[net];direction=r['direction'];v=[-13.2,13.2];current=r['current_mA'].get('panel_connector_branch_bound',r['current_mA']['design_limit']);basis=r['current_mA']['status']
            row['pins'].append({'manufacturer_pin':pin,'net':net,'direction':direction,'max_steady_voltage_V':v,'transient_voltage_requirement_V':[-13.2,13.2] if net!='NC' else [0,0],'current_bound_mA':current,'current_basis':basis,'status':'DERIVED source mapping; electrical envelope PROPOSAL; fault isolation OPEN #59'})
        connector.append(row)
    d=source['load_distribution'];boards=[];definitions={};supports=[];jack_reservation_receipt={}
    for b,s in source['boards'].items():
        selected=[p for p in parts if board_for(p)==b];uids=sorted(p['panel_uid'] for p in selected if p['panel_uid']);holes=[{'id':b+'-SUP-'+str(i+1),'center':xy,'diameter_mm':2.2} for i,xy in enumerate(s['supports_mm'])]
        if b in ('EL','P'):
            for i,post in enumerate(optical['support_posts']):
                if b=='P' and post['center_mm'][1]<176:continue
                holes.append({'id':b+'-OPT-'+str(i+1),'center':post['center_mm'],'diameter_mm':post['hole_mm']})
        if b=='K':holes +=[{'id':'K-SERVICE-'+str(i+1),'center':a['center_mm'],'diameter_mm':a['diameter_mm']} for i,a in enumerate(ports['K_service_apertures'])]
        layernames=['F.Cu','In1.Cu','In2.Cu','B.Cu'] if s['layers']==4 else ['F.Cu','B.Cu'];stack=[{'layer':n,'role':('continuous AGND' if n=='In1.Cu' else 'split regulated power planes' if n=='In2.Cu' else 'signals / local AGND fill'),'copper_oz':s['copper_oz']} for n in layernames]
        regions=[]
        for instance in sorted({p['instance'] for p in selected if not p['panel_uid']}):
            for side in ('F.Cu','B.Cu'):
                pp=[loc[p['ref']]['courtyard_mm'] for p in selected if p['instance']==instance and not p['panel_uid'] and loc[p['ref']]['side']==side]
                if not pp:continue
                rect=[min(q[0] for q in pp)-.30,min(q[1] for q in pp)-.30,max(q[2] for q in pp)+.30,max(q[3] for q in pp)+.30]
                regions.append({'instance':instance,'family':b+'-'+instance,'rect':rect,'side':side,'edge_clearance_mm':.25,'mounting_clearance_mm':.25})
        if b in JACK_BOARDS:
            branch=d['branches'][b]
            terminal_sites=[{'reference':b+'-POWER-'+str(i+1),'board':b,'center_mm':[x,branch['pad_y_mm']],'maximum_courtyard_mm':[5,5]} for i,x in enumerate(branch['x_mm'])]
            errors.extend(bulk_reserve_source_errors(s))
            errors.extend(jack_bulk_conflicts(s.get('reserves',[]),loc,ports['headers'],terminal_sites,b))
            keepouts,jack_reservation_receipt[b]=jack_reservation_keepouts(s.get('reserves',[]),loc,connector,terminal_sites,b)
        else:
            keepouts=[{'id':r['id'],'polygon':[[r['rect'][0],r['rect'][1]],[r['rect'][2],r['rect'][1]],[r['rect'][2],r['rect'][3]],[r['rect'][0],r['rect'][3]]],'layers':r['sides']} for r in s.get('reserves',[])]
        if b=='EL':
            # Source circles are represented by a circumscribed 64-gon for
            # conservative copper keepout, and an exact round NPTH/routed cut.
            for i,h in enumerate(optical['passages']):
                x,y=h['center_mm'];r=h['diameter_mm']/2
                polygon=[[x+(r+.01)*math.cos(j*math.pi/32),y+(r+.01)*math.sin(j*math.pi/32)] for j in range(64)]
                keepouts.append({'id':'PASSAGE-'+str(i+1),'polygon':polygon,'layers':layernames})
                holes.append({'id':'EL-PASSAGE-'+str(i+1),'center':[x,y],'diameter_mm':2*r})
        for hole in holes:
            if '-SERVICE-' in hole['id'] or '-PASSAGE-' in hole['id']:continue
            x,y=hole['center'];r=1.6
            keepouts.append({'id':'COLLAR-'+hole['id'],'polygon':[[x-r,y-r],[x+r,y-r],[x+r,y+r],[x-r,y+r]],'layers':['F.Cu'] if b=='EL' else ['F.Cu','B.Cu']})
        definition={'schema_version':1,'board_id':s['id'],'outline':s['outline'],'corner_radius_mm':0,'layers':s['layers'],'thickness_mm':s['thickness_mm'],'stackup':stack,'mounting_holes':holes,'keepouts':keepouts,'domains':sorted({p['domain'] for p in lock if p['uid'] in uids}),'placement_uids':uids,'netlist':'schematic/boards/'+s['id']+'.net','schematic':'schematic/boards/'+s['id']+'.kicad_sch','regions':regions}
        if b in JACK_BOARDS:
            definition['routing']={'min_track_width_mm':.1,'net_classes':[
                {'name':'Default','nets':[],'track_width_mm':.2,'clearance_mm':.2,'via_diameter_mm':.6,'via_drill_mm':.3},
                {'name':'Rails','nets':['+12V','-12V','+5V'],'track_width_mm':.4,'clearance_mm':.25,'via_diameter_mm':.7,'via_drill_mm':.3},
                {'name':'Ground','nets':['AGND'],'track_width_mm':.5,'clearance_mm':.25,'via_diameter_mm':.7,'via_drill_mm':.3}],
                'zones':[{'name':'agnd_plane','net':'AGND','layers':['In1.Cu'],'clearance_mm':.25,'min_thickness_mm':.15,'pad_connection':'full'},
                    {'name':'agnd_surface','net':'AGND','layers':['F.Cu','B.Cu'],'clearance_mm':.25,'min_thickness_mm':.15,'pad_connection':'full'}]+[
                    {'name':rail+'_plane','net':rail,'layers':['In2.Cu'],'polygon':polygon,'clearance_mm':.25,'min_thickness_mm':.15,'pad_connection':'full'}
                    for rail,polygon in jack_rail_polygons(s,d,b).items()]}
            if 'jack_terminal_transfer' in d:
                definition['routing']['load_terminal_transfer']=d['jack_terminal_transfer']
        definitions[s['id']]=definition
        boards.append({**s,'board_key':b,'role':{'JL':'left jack interfaces, whole local islands','JR':'right jack interfaces, whole local islands','P':'all pots/toggles/buttons and complete slew/control circuits','K':'distinct rear signal core and conditional load-side power star','EL':'complete stage-indicator circuits'}.get(b,'one selected stepped octave adapter'),
                       'facing_panel':'F.Cu','status':'PROPOSAL','supply_domain':'EXT','physical_package_count':len(selected),'fitted_package_count':sum(not p['dnp'] for p in selected),'definition':'design/boards/'+s['id']+'.json',
                       'single_board_assembly': 'Standard PCBA eligible size envelope' if b in (*JACK_BOARDS,'P','K','EL') else 'PROPOSAL one adapter per 70x70 mm factory handling panel, below250x250mm delivery cap; exact tabs/tooling #39, no order files',
                       'layer_reason':'Four layers: inner AGND plus rail planes; 2 oz plane-resistance requirement' if s['layers']==4 else 'EL 0.4 mm two-layer exception: complete sparse local LED loops, rear AGND fill and quiet signal returns' if b=='EL' else 'Passive selector adapter; two layers with local return fill; no sensitive storage circuit',
                       'field_status':{'id':'DERIVED','physical_package_count':'DERIVED','fitted_package_count':'DERIVED','outline':'PROPOSAL','face_z_mm':'PROPOSAL','thickness_mm':'PROPOSAL','layers':'PROPOSAL','copper_oz':'PROPOSAL'}})
        for h in holes:
            if '-SERVICE-' in h['id'] or '-PASSAGE-' in h['id']:continue
            supports.append({'id':h['id'],'board':b,'position_mm':h['center'],'pcb_hole_mm':h['diameter_mm'],'post_diameter_mm':2,'collar_diameter_mm':3.2,'status':'PROPOSAL custom captive M2 shoulder support; exact fastener order codes/strength OPEN #65; selectors #55','load_path':'enclosure side carrier to board; panel clamp/bushing/body carrier reacts operation; no connector/solder structural load'})
    rwire=d['hot_resistance_requirement_ohm_per_m']*d['max_wire_length_mm']/1000+d['combined_termination_resistance_ohm'];rp=rwire+d['rail_plane_resistance_ceiling_ohm'];rg=rwire+d['return_plane_resistance_ceiling_ohm'];drop={rail:(amps*rp+d['single_return_max_A']*rg)*1000 for rail,amps in d['rail_max_A'].items()}
    if max(drop.values())>20:errors.append('load distribution exceeds 20 mV')
    wire_requirements=read('design/partition/harness-wire-evidence.json')['proposal']
    return_bounds={};looms={r['id']:r for r in loom['routes']}
    for board in d['branches']:
        hs=[h for h in ports['harnesses'] if set(h['boards'])=={board,'K'}];n=sum(h['return_contacts'] for h in hs);minimum=min(looms[h['id']]['centreline_length_mm'] for h in hs)/1000*wire_requirements['wire_minimum_resistance_for_parallel_path_bounds_ohm_per_m'];maximum=max(looms[h['id']]['cut_length_max_mm'] for h in hs)/1000*wire_requirements['wire_hot_resistance_ceiling_ohm_per_m']+.1
        # Candidate GH return has zero contact/PCB resistance. All alternatives
        # have maximum wire/contact resistance AND the entire common PCB neck.
        # Independent dedicated ground wires are parallel before that neck.
        ground_count=d['net_order'].count('AGND')
        alternative=d['return_plane_resistance_ceiling_ohm']+1/((n-1)/maximum+ground_count/rwire)
        amps=d['single_return_max_A']*alternative/(minimum+alternative)
        if amps>.5:errors.append('GH return derating exceeded '+board)
        return_bounds[board]={'return_contact_count':n,'minimum_single_path_ohm':minimum,'maximum_other_path_ohm':maximum,'dedicated_ground_wire_count':ground_count,'dedicated_ground_wire_max_ohm':rwire,'common_PCB_neck_max_ohm':d['return_plane_resistance_ceiling_ohm'],'all_alternative_returns_max_equivalent_ohm':alternative,'worst_single_contact_A':amps,'equal_sharing_assumed':False,'routing_acceptance':d['ground_routing_requirement'],'wire_lower_bound_status':'0.1 ohm/m is an assembled acceptance condition, not a manufacturer guaranteed minimum; cold resistance qualification #65','status':'DERIVED conditional all-mates-present normal case; patch fault/main-return-open OPEN #59/#65'}
    # The four J/P utility returns also connect two powered board grounds.
    # Bound either node's voltage using only its three dedicated main returns,
    # ignore all helpful GH returns, and give the far node zero impedance.
    loop_hs=[h for h in ports['harnesses'] if set(h['boards'])=={'JL','P'}]
    loop_min=min(looms[h['id']]['centreline_length_mm'] for h in loop_hs)/1000*wire_requirements['wire_minimum_resistance_for_parallel_path_bounds_ohm_per_m']
    node_max=d['return_plane_resistance_ceiling_ohm']+rwire/d['net_order'].count('AGND')
    loop_current=d['single_return_max_A']*node_max/(loop_min+node_max)
    if loop_current>.5:errors.append('GH return derating exceeded J/P utility')
    return_bounds['JL/P utility']={'return_contact_count':len(loop_hs),'minimum_single_path_ohm':loop_min,'loaded_node_main_return_max_ohm':node_max,'worst_single_contact_A':loop_current,'equal_sharing_assumed':False,'status':'DERIVED conditional whole-domain absolute 4.6 A bound and all main returns present; zero far-node impedance; fault/patch returns OPEN #59/#65'}
    powered=[*JACK_BOARDS,'P','K','EL'];bulk={rail:len(powered)*4.7 for rail in ('+12V','-12V','+5V')};fitted={rail:r['captured_fitted_nominal_uF'] for rail,r in read('design/power/supply-architecture.json')['implementation']['actual_fitted_capacitor_inventory'].items()};cap={rail:fitted[rail]+bulk[rail] for rail in bulk}
    for rail,limit in [('+12V',150),('-12V',150),('+5V',100)]:
        if cap[rail]>limit:errors.append('bulk capacitance exceeds rail ceiling')
    ramp_mA={rail:cap[rail]*1e-6*1.2*voltage/.010*1000 for rail,voltage in [('+12V',13.2),('-12V',13.2),('+5V',5.5)]}
    ramp_total={rail:steady+ramp_mA[rail] for rail,steady in [('+12V',1700),('-12V',1600),('+5V',300)]}
    for rail,limit in [('+12V',2000),('-12V',1900),('+5V',400)]:
        if ramp_total[rail]>limit:errors.append('full capacitance ramp exceeds transient minimum '+rail)
    # Complete EL branch bound, including base drive and +20% bulk startup.
    # Values come from current source parts, not a remembered worksheet value.
    from design.spec.modules.envelope import family as envelope_family
    envelope=envelope_family()
    def ohms(part):
        bits=part.value.split();return float(bits[0])*({'kΩ':1000,'MΩ':1000000}.get(bits[1],1))
    ecount=len({p['instance'] for p in parts if p['regions']==['stage_optical']})
    base=[p for p in envelope.parts if p.attributes.get('Role')=='stage_indicator:R_BASE']
    pull=[p for p in envelope.parts if p.attributes.get('Role')=='stage_indicator:R_GATE']
    limiters=[p for p in envelope.parts if p.attributes.get('Role')=='stage_indicator:R_LED_LIMIT']
    iq=sum(p['mpn']=='OPA4196IDR' and p['regions']==['stage_optical'] for p in parts) # 1mA whole quad full-temp, existing worksheet
    analog=iq+ecount*sum(26.4/(ohms(p)*.99)*1000 for p in base)+4.7e-6*1.2*13.2/.010*1000
    digital=ecount*sum(5.5/(ohms(p)*.99)*1000 for p in limiters+pull)+4.7e-6*1.2*5.5/.010*1000
    el_contract={'+12V':50,'-12V':50,'+5V':70}
    if analog>50 or digital>70:errors.append('EL current contract exceeded by current source components')
    el_hs=[h for h in ports['harnesses'] if 'EL' in h['boards']]
    el_path=max(looms[h['id']]['cut_length_max_mm'] for h in el_hs)/1000*wire_requirements['wire_hot_resistance_ceiling_ohm_per_m']+.1
    el_return=sum(el_contract.values())/1000
    el_drop={rail:((current/1000)*(el_path/len(el_hs)+.001)+el_return*(el_path/sum(h['return_contacts'] for h in el_hs)+.0005))*1000 for rail,current in el_contract.items()}
    if max(el_drop.values())>20:errors.append('EL path drop exceeds 20mV')
    terminals=[];power_wires=[]
    for b,branch in d['branches'].items():
        for index,(x,net) in enumerate(zip(branch['x_mm'],d['net_order'])):
            ends=[]
            for board,y,side in [(b,branch['pad_y_mm'],'B.Cu'),('K',branch['core_pad_y_mm'][index],'F.Cu')]:
                ref='TP'+str(990001+len(terminals));ends.append(ref)
                terminals.append({'reference':ref,'board':board,'net':net,'manufacturer_pin':'1','center_mm':[x,y],'side':side,'copper_land_mm':[4,4],'maximum_courtyard_mm':[5,5],'wire_end':'factory stripped bare end at solder land; first/last 3mm have no full-diameter insulation; solder/profile qualification #65','mask_margin_mm':.1,'paste':'none; factory hand/wave solder process','identity':'custom PCB solder terminal, not an orderable inlet','status':'PROPOSAL copper geometry; native footprint/symbol generation #36, assembled ampacity/strain relief #65'})
            power_wires.append({'id':'POWER-'+b+'-'+d['wire_labels'][index],'net':net,'terminal_refs':ends,'wire_mpn':d['wire'],'maximum_length_mm':d['max_wire_length_mm'],'status':'PROPOSAL existing load-side nets only; physical continuity across CN301/XB301 remains absent'})
    interfaces=[]
    grouped=defaultdict(list)
    for h in ports['harnesses']:grouped['/'.join(h['boards'])].append(h)
    for pair,hs in grouped.items():
        interfaces.append({'board pair':pair,'exact connector MPNs including mate':'See exact connector entries for '+', '.join(h['id'] for h in hs),'manufacturer pin numbers':'pins[].manufacturer_pin; no fabricated housing PCB footprint','net and direction':'pins[] and source allowed_crossings; only permitted buffered/reference/wiper/conditioned logic crossings',
                           'maximum steady and transient voltage':'pins[]; ±13.2 V analogue / 5.5 V logic envelope; fault behavior OPEN #59','current/return capacity':'1 A nominal at AWG26; 0.5 A/contact planning limit; explicit load/return bounds, no equal-sharing assumption','default/power-off behavior':'Source disconnected and discharged before service. No new interboard injection isolation claimed; 82 output/16 sense/30 octave protection OPEN #59. Common AGND includes patch sleeves.',
                           'mating depth':'7.3 mm manufacturer reference per local PCB face; flexible cable spans distinct planes; no rigid 11 mm connector stack assumed','mechanical supports':'Custom enclosure-supported M2 carriers plus controlled insulating loom combs; force paths independent of solder/header friction','factory assembly procedure':'Populate all boards and factory crimp exact SSHL contacts onto audited AWG26, inspect pin order/continuity and pull force; mount carriers first; connect labelled harnesses using local backing; clamp loom; no owner soldering.',
                           'status':'PROPOSAL interface; sourced identities and derived pin counts called out in connector records'})
    report={'schema_version':1,'status':'CONDITIONAL UNVALIDATED DRAFT' if not errors else 'FAIL; no accepted partition','authority':'PROPOSAL (planning, owner-delegated)',
            'rotation_convention':'Source rotation_deg is clockwise after mirroring local X for B.Cu. Use explicit kicad_orientation_deg: F=-theta, B=180-theta. Native KiCad10.0.6 Flip(False) maps F angle0 to B angle180 and mirrors X.',
            'status_policy':'Every numeric/mechanical value is PROPOSAL unless its enclosing status or field_status explicitly says SOURCED or DERIVED. SOURCED nominal dimensions do not imply tolerance or installed fit.',
            'boards':boards,'jack_split':source['jack_split'],'jack_reservation_receipt':jack_reservation_receipt,'assignment':{'rule':'Exact master physical package after AbstractBoundary filtering: jack ->JL/JR by complete source module, control ->P, core ->K, stage_optical ->EL, each selector instance ->its O adapter. Whole package, bypass and island closure checked. Faces use floorplan-candidate per-reference map.','status':'DERIVED','components':assignment,'abstract_boundaries':['CN301','XB301'],'abstract_status':'Audit-only; NO physical footprint, NO BOM/orderable inlet, NO invented conductive bridge'},
            'load_side_terminals':terminals,'load_side_wires':power_wires,'connectors':connector,'harnesses':ports['harnesses'],'harness_geometry':'design/partition/loom-candidate.json','interfaces':interfaces,'supports':supports,
            'mechanical_datum_table':mechanical['datum_table'],'mechanical_report':'design/partition/mechanical-candidate.json','panel':read('design/panel/panel-params.json'),'optical_passages':optical['passages'],'K_service_apertures':ports['K_service_apertures'],'enclosure':source['enclosure'],
            'power':{'status':'PROPOSAL conditional EXT requirements; physical source/inlet NOT SELECTED','required_continuous_mA':{'+12V':1700,'-12V':1600,'+5V':300},'required_transient_mA':{'+12V':2000,'-12V':1900,'+5V':400},'maximum_delivered_mA':{'+12V':2100,'-12V':2000,'+5V':500},'load_distribution':d,'worst_load_distribution_drop_mV':drop,'GH_normal_return_bounds':return_bounds,'source_boundary':'No continuity across CN301/XB301 is created. Internal factory-soldered wires connect existing regulated load-side nets only. Source inlet retains separate #52 20 AWG contract.',
                     'EL_rail_current_contract_mA':el_contract,'EL_source_derived_bounds_mA':{'+12V':analog,'-12V':analog,'+5V':digital},'EL_parallel_path_drop_mV':el_drop,'EL_return_sum_bound_mA':el_return*1000,'EL_basis':'Six OPA4196 quads: 6 mA Iq per analog rail; 12 stage LED hard bounds 4.63 mA each; 4.7uF/rail 10ms ramp and margin. 12 base paths each conservatively 26.4V/(10kohm*0.99)=2.667mA plus6mA Iq and7.445mA bulk ramp, below50mA/analog rail; +5V 55.56mA LEDs +0.667mA pullups +3.102mA bulk ramp below70mA. Stage resistor/reference draw included by 50/50/70 mA ceilings; measured dynamic/fault bound NOT RUN. Six parallel rail paths and twelve ground paths use maximum-path conductance, no equal-current assertion.',
                     'capacitance_uF':{'fitted_nominal':fitted,'finite_bulk_reservations':{b:s['board_bulk_reserve'] for b,s in source['boards'].items() if 'board_bulk_reserve' in s},'new_reserved_board_bulk':bulk,'full_inventory_plus20percent_10ms_ramp_mA':ramp_mA,'continuous_requirement_plus_ramp_mA':ramp_total,'after_reserved_bulk':cap,'status':'DERIVED planning; 4.7 uF per each of 5 powered boards/rail, 150/150/100 nominal limits; +20% and >=10ms ramp retained; exact bulk/protection current/area source #59'},
                     'load_accounting':'All 650 ICs and every physical part assigned once; existing complete rail-ledger load IDs and oscillator fanout report retained without adding independent copies of shared worksheet reserves. J/P branch ampacity is conservatively bounded by the whole delivered-domain ceiling, not falsely summed as extra load.',
                     'reference_fanout':'design/reports/oscillator-reference-fanout.json','unresolved_protection':source['protection_obligations']},
            'counts':{'physical_rows':len(parts),'fitted_rows':sum(not p['dnp'] for p in parts),'fitted_ICs':fitted_ics,'fixed_UIDs':438,'modules':33,'boards':len(boards),'headers':len(connector),'harnesses':len(ports['harnesses']),'header_contacts':sum(h['contacts'] for h in ports['headers']),'wired_signal_conductors':sum(h['signal_count'] for h in ports['harnesses']),'wired_return_conductors':sum(h['return_contacts'] for h in ports['harnesses']),'rail_conductors_GH':18,'factory_load_side_wires':len(power_wires),'load_side_copper_terminals':len(terminals),'unwired_positions_across_all_harnesses_per_end':sum(h['unused_contacts'] for h in ports['harnesses']),'LED_identities':dict(led)},
            'checks':{'errors':errors,'complete_assignment_island_sensitive_package_closure':'PASS' if not errors else 'FAIL','header_pad_edge_nominal':'PASS with0.05mm native-courtyard inflation envelope','native_footprint_transform_oracle':'design/partition/orientation-oracle.json; separate pinned gate','courtyard_capacity_proposal':floor['status'],'loom_corridor_proposal':loom['status'],'physical_fit':'NOT RUN #65 main assembly, #55 selector, #57 source; conditional hardware body datum/tolerance requirements remain','optical_hot_qualification':'NOT RUN #64','exact_power_off_protection':'OPEN #59','actual_board_placement_routing_DRC':'NOT RUN #38/#39/#42/#43; #66 generates source geometry/schematics only; original J routing timeout historical','panel_artwork_regeneration':'Regenerated by aggregate pipeline; fixed geometry unchanged; installed fit NOT RUN','J_bypass_proximity':floor['bypass_proximity'],
                      'mixed_face_placer':'Merged #38 tooling consumes per-reference side/origin; native half-board placement/routing remains NOT RUN'},
            'downstream_dispositions':{'38':['osc-jack-left','osc-jack-right'],'39':['osc-control','osc-octave-1','osc-octave-2','osc-octave-3','osc-octave-4','osc-octave-5'],'40':[],'41':[],'42':['osc-stage-optical'],'43':['osc-core']}}
    return report,definitions


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report,defs=build();outputs={ROOT/'design/partition/partition.json':report};outputs.update({ROOT/'design/boards'/(name+'.json'):v for name,v in defs.items()})
    for path,value in outputs.items():
        text=dumps(value)+'\n'
        if args.check:
            if not path.exists() or path.read_text()!=text:raise SystemExit('partition/board drift '+str(path))
        else:path.write_text(text)
        if path.parent.name=='boards':load_definition(path)
    print(report['status'],report['counts']);print('Load distribution mV:',report['power']['worst_load_distribution_drop_mV']);print('GH return A:',{b:r['worst_single_contact_A'] for b,r in report['power']['GH_normal_return_bounds'].items()})
    if report['checks']['errors']:raise SystemExit('\n'.join(report['checks']['errors']))

if __name__=='__main__':main()
