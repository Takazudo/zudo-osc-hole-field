"""Candidate source compiler. Pure stdlib; never launches native tools or writes CAD."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/architecture278'))
from populated_mechanics import courtyard, overlap, sexpr, field

PACK = ROOT / 'design/architecture-278'
OUT = PACK / 'implementation'
REQUIRED_CLUSTERS = {'fm-pwm': ['C1101', 'C1102', 'C1103', 'C1104', 'C1142', 'C1143', 'R1117', 'R1118', 'R1119', 'R1120', 'R1121', 'R1122', 'R1123', 'R1124', 'R1125', 'R1126', 'R1127', 'R1128', 'U1112'], 'local-reference': ['C1115', 'C1116', 'C1117', 'C1118', 'C1136', 'C1137', 'RB1110', 'RB1111', 'RB1112', 'RB1113', 'RB1114', 'RB1115', 'RB1116', 'RB1117', 'U1110'], 'tune-octave-vee': ['C1105', 'C1106', 'C1108', 'C1109', 'C1134', 'C1135', 'R1129', 'R1130', 'R1131', 'R1132', 'R1135', 'R1136', 'R1148', 'R1149', 'U1109'], 'pw-lfo': ['C1107', 'C1144', 'C1145', 'R1133', 'R1134', 'R1137', 'R1138', 'R1165', 'R1166', 'R1167', 'R1168', 'R1169', 'R1170', 'U1113'], 'core-timing': ['C1110', 'C1111', 'C1112', 'C1113', 'C1114', 'C1129', 'C1130', 'DO1105', 'R1139', 'R1140', 'R1141', 'R1142', 'R1143', 'R1144', 'R1145', 'R1146', 'R1147', 'R1150', 'R1151', 'R1152', 'R1153', 'R1154', 'R1155', 'R1161', 'R1162', 'R1163', 'R1164', 'R1173', 'RVO1106', 'RVO1107', 'RVO1108', 'RVO1109', 'U1105'], 'sync': ['C1131', 'C1132', 'R1156', 'R1157', 'R1158', 'R1159', 'R1160', 'U1106', 'U1107'], 'wave-scale': ['C1133', 'C1146', 'C1147', 'R1171', 'R1172', 'R1174', 'R1175', 'R1176', 'R1177', 'R1178', 'R1179', 'R1180', 'R1181', 'R1182', 'R1183', 'R1184', 'R1185', 'R1186', 'R1187', 'R1188', 'U1108', 'U1114'], 'sine': ['C1119', 'C1120', 'C1138', 'C1139', 'C1148', 'C1149', 'Q1101', 'R1189', 'R1190', 'R1191', 'R1192', 'R1193', 'R1194', 'R1195', 'R1196', 'R1197', 'R1198', 'R1199', 'RB1101', 'RB1118', 'RB1119', 'RB1120', 'RB1121', 'RVO1110', 'RVO1111', 'U1111', 'U1115']}

CHECKPOINT = 'd218fc537818dcbbd470eb15d192cfc8d0be5f0a'

def read(name):
    return json.loads((PACK / name).read_text())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def finite(value):
    if isinstance(value, dict):
        for v in value.values(): finite(v)
    elif isinstance(value, list):
        for v in value: finite(v)
    elif isinstance(value, (float, int)):
        require(not isinstance(value, bool) and math.isfinite(value), 'nonfinite/boolean geometry')

def packages(contract):
    result = {}
    for unit in contract['parts']:
        p = result.setdefault(unit['ref'], {'ref': unit['ref'], 'owner': unit['proposed_owner'],
            'footprint': unit['footprint'], 'units': [], 'pins': {}, 'attributes': unit['attributes']})
        require(p['owner'] == unit['proposed_owner'], 'split package')
        require(not set(p['pins']).intersection(unit['pins']), 'duplicate package pin')
        p['units'].append(unit['unit'])
        p['pins'].update(unit['pins'])
    return result

def footprint_pads(path):
    result = {}
    for node in sexpr((ROOT / path).read_text()):
        if isinstance(node, list) and node[0] == 'pad' and node[1]:
            xy = list(map(float, field(node, 'at')[:2]))
            result.setdefault(node[1], []).append(xy)
    return result

def place(spec, physical):
    placed = []
    for cluster in spec['clusters']:
        x0,y0,x1,y1 = cluster['box_mm']
        x,y,row_h = x0,y0,0
        shapes=[]
        for ref in cluster['refs']:
            p=physical[ref]
            path='footprints/kicad/zudo-osc-hole-field.pretty/'+p['footprint'].split(':')[1]+'.kicad_mod'
            box=courtyard(path)
            trim=ref.startswith('RVO')
            reserve=[min(box[0],-3),min(box[1],-3),max(box[2],3),max(box[3],3)] if trim else box
            shapes.append((ref,path,box,reserve))
        for ref,path,box,reserve in sorted(shapes,key=lambda s: (-(s[3][3]-s[3][1]),s[0])):
            a,b,c,d=reserve;w,h=c-a,d-b
            if x+w>x1: x=x0;y+=row_h+spec['clearance_mm'];row_h=0
            require(y+h<=y1, 'cluster capacity: '+cluster['id'])
            origin=spec.get('local_overrides_mm',{}).get(ref,[x-a,y-b])
            require(x0-1e-9<=origin[0]+a and origin[0]+c<=x1+1e-9 and y0-1e-9<=origin[1]+b and origin[1]+d<=y1+1e-9,'override outside cluster '+ref+str((origin,reserve,cluster['box_mm'])))
            pads={pin:[[origin[0]+px,origin[1]+py] for px,py in coords] for pin,coords in footprint_pads(path).items()}
            require(set(physical[ref]['pins'])==set(pads), 'missing footprint pin '+ref)
            placed.append({'ref':ref,'cluster':cluster['id'],'origin_mm':origin,
                'box_mm':[origin[0]+box[0],origin[1]+box[1],origin[0]+box[2],origin[1]+box[3]],
                'reserved_box_mm':[origin[0]+a,origin[1]+b,origin[0]+c,origin[1]+d],'pads_mm':pads,'footprint_source':path,
                'units':physical[ref]['units'],'rear_facing':True,'trim_tool_diameter_mm':6 if ref.startswith('RVO') else None})
            x+=w+spec['clearance_mm'];row_h=max(row_h,h)
    return placed

def mechanical(spec, placed):
    m=spec['mechanical'];w,h=spec['tile_mm'];t=m['xy_tolerance_mm']
    require(t>=.5,'XY tolerance weakened')
    require(spec['connector']['orientation']=='vertical','unsupported connector orientation')
    cx,cy=spec['connector']['centre_mm']
    require(spec['connector']['body_reservation_mm']==[cx-7.5,cy-50,cx+7.5,cy+50], 'connector datum mismatch')
    fixtures=[{'id':'DIN','box_mm':spec['connector']['body_reservation_mm']}]
    for key,count,r in [('supports_mm',4,3),('guides_mm',2,2),('handles_mm',2,3),('probes_mm',4,2)]:
        require(len(m[key])==count and len({tuple(p) for p in m[key]})==count,'fixture count '+key)
        for i,(x,y) in enumerate(m[key]): fixtures.append({'id':key+str(i),'box_mm':[x-r,y-r,x+r,y+r]})
    require(len(m['power_boxes_mm'])==4,'four power straps required')
    fixtures += [{'id':'power'+str(i),'box_mm':b} for i,b in enumerate(m['power_boxes_mm'])]
    objects=[{'id':p['ref'],'box_mm':p['reserved_box_mm']} for p in placed]+fixtures
    for p in objects:
        x,y,xx,yy=p['box_mm'];require(t<=x<xx<=w-t and t<=y<yy<=h-t,'outside tile '+p['id'])
    for i,p in enumerate(objects):
        for q in objects[i+1:]:require(not overlap(p['box_mm'],q['box_mm']), 'fixture/tool collision '+p['id']+'/'+q['id'])
    require(set(spec['origins_mm'])=={'O1','O2'},'adjacent instances required')
    cards={n:[x,y,x+w,y+h] for n,(x,y) in spec['origins_mm'].items()}
    require(m['other_reservations_mm']=={'O3':[2,5,105,120],'O4':[107,5,210,120],'O5':[212,5,315,120]},'retain other oscillator reservations')
    cards.update(m['other_reservations_mm'])
    for name,(x,y,xx,yy) in cards.items():require(t<=x<xx<=318-t and t<=y<yy<=298-t,'outside fixed panel '+name)
    for i,(name,box) in enumerate(cards.items()):
        for other,b in list(cards.items())[i+1:]:require(not overlap(box,b,2*t),'adjacent/extraction collision '+name+'/'+other)
    require(m['rear_height_bound_mm']>=5,'height procurement bound weakened')
    stack=m['core_depth_mm']-m['middle_depth_mm']
    require(m['stack_tolerance_mm']>=.3 and stack-m['stack_tolerance_mm']>=18.3 and stack+m['stack_tolerance_mm']<=20,'connector stack')
    require(m['relative_depth_tolerance_mm']>=1,'depth tolerance weakened')
    require(m['cover_depth_mm']-m['core_depth_mm']-max(m['handle_projection_mm'],m['rear_height_bound_mm'])-m['relative_depth_tolerance_mm']>=2,'cover clearance')
    require(m['handle_projection_mm']-10-m['relative_depth_tolerance_mm']-m['rear_height_bound_mm']>=2,'handle finger height')
    require(m['withdrawal_mm']>=40 and m['workspace_mm']>=m['withdrawal_mm'],'extraction workspace')
    require(m['middle_depth_mm']-33-9-m['relative_depth_tolerance_mm']>=2,'selector tail clearance')
    require(m['guides_mm'][0][1]!=m['guides_mm'][1][1],'asymmetric guides required')
    axes=[{'ref':p['ref'],'local_axis_mm':p['origin_mm'],'diameter_mm':6} for p in placed if p['trim_tool_diameter_mm']]
    require(len(axes)==6,'six rear trims required')
    probe_nets=['AGND','+12V','-12V','/O1/TRI_SCALED']
    return {'probe_assignments':[{'axis_mm':xy,'net':net} for xy,net in zip(m['probes_mm'],probe_nets)],'scope':'bounded XY/tool/depth allocation; no structural/native/physical qualification','fixtures':fixtures,'cards_mm':cards,'trim_axes':axes,
        'O2_mapping':read('interface-contract.json')['instance_mapping'],
        'nonreplication':'O3-O5 remain prior115mm reservations, not copies of150mm O1/O2; five-card population OPEN',
        'service':'Power off; isolate all external patch sources; verify discharged; remove cover, release four supported captive power screws and four retainers; withdraw40mm using handles. Middle and adjacent core stay installed. Torque/discharge criterion/guide engagement/formed straps OPEN.'}

def build(spec=None):
    spec=copy.deepcopy(spec if spec is not None else read('implementation/candidate.json'))
    finite(spec)
    require(spec['checkpoint']==CHECKPOINT, 'wrong checkpoint')
    require(spec['limit_mm']==300, 'cannot relax length limit')
    for key,minimum in [('clearance_mm',.5),('front_flex_mm',60),('connector_path_mm',25),('front_trace_mm',10),('middle_detour_mm',5),('rear_fanout_mm',5)]:
        require(spec[key]>=minimum, 'invalid allocation '+key)
    contract=read('interface-contract.json'); old=read('revision-electrical-report.json'); mech=read('revision-mechanical-report.json')
    ps=packages(contract)
    physical={r:p for r,p in ps.items() if p['owner']=='rear-core' and p['footprint']}
    assigned=[r for g in spec['clusters'] for r in g['refs']]
    require(Counter(assigned)==Counter(physical.keys()), 'cluster package coverage')
    require(len({g['id'] for g in spec['clusters']})==len(spec['clusters']), 'duplicate cluster')
    require({g['id']:sorted(g['refs']) for g in spec['clusters']}==REQUIRED_CLUSTERS, 'functional cluster changed')
    membership={r:g['id'] for g in spec['clusters'] for r in g['refs']}
    # Source Decouples uses package keys, not the occasionally stale C_DEC display name.
    key_refs={u['key'].split('.')[0]:u['ref'] for u in contract['parts'] if u['instance']=='O1'}
    for p in contract['parts']:
        target=p['attributes'].get('Decouples')
        if p['ref'] in physical and target:
            require(membership[p['ref']]==membership[key_refs[target]], 'bypass detached '+p['ref'])
    for g in spec['clusters']:
        x,y,xx,yy=g['box_mm'];require(0<x<xx<spec['tile_mm'][0] and 0<y<yy<spec['tile_mm'][1]-10, 'cluster bounds')
    for i,g in enumerate(spec['clusters']):
        for h in spec['clusters'][i+1:]: require(not overlap(g['box_mm'],h['box_mm']), 'cluster overlap')
    placed=place(spec,physical); byref={p['ref']:p for p in placed}
    for i,p in enumerate(placed):
        for q in placed[i+1:]:require(not overlap(p['reserved_box_mm'],q['reserved_box_mm']), 'package/tool overlap')
    links=copy.deepcopy(old['functional_front_links'])
    # Split both eight-position jack links into eight signal+return links.
    jack_sources=contract['harnesses'][:2]
    jack_conductors=[n for h in jack_sources for n in h['faces'][0]['pin_map'].values()]
    require(jack_conductors.count('AGND')==8 and len(jack_conductors)==16, 'jack source multiplicity')
    for n in jack_conductors:
        if n=='AGND':continue
        net=next(row for row in contract['nets'] if row['net']==n)
        uids={m['uid'] for m in net['source_crossing']['members'] if m.get('uid','').startswith('J:')}
        if not uids: uids={'J:O1.'+n.split('/')[-1].split('_')[0]}
        require(len(uids)==1,'jack association')
        uid=uids.pop()
        links.append({'id':'FRONT-'+uid,'uid':uid,'pins':{'1':n,'2':'AGND'},
            'header_mpn':'BM02B-GHS-TBT(LF)(SN)','housing_mpn':'GHR-02V-S','contact_mpn':'SSHL-002T-P0.2',
            'identity_status':'candidate; exact installed connector/clearance evidence OPEN'})
    for h in contract['harnesses'][2:4]:
        links.append({'id':h['id'],'uid':'C:O1.OCT','pins':h['faces'][0]['pin_map']})
    oldnets=Counter(n for h in contract['harnesses'] for n in h['faces'][0]['pin_map'].values())
    newnets=Counter(n for h in links for n in h['pins'].values())
    require(newnets-oldnets==Counter({'/O1/LOCAL_REF5':2,'/O1/LOCAL_REFN5':1}) and not oldnets-newnets, 'lost signal/return')
    def path_rows(pinout):
        rows=[]
        for instance in ('O1','O2'):
            ox,oy=spec['origins_mm'][instance]
            for link in links:
                uid=link['uid'].replace('O1',instance)
                front=next(p for p in mech['front_locked_O1_O2'] if p['uid']==uid)
                for lp,net in link['pins'].items():
                    if net=='AGND' or net.startswith('OSC_OCT'):continue
                    pin=next(p['pin'] for p in pinout if p['net']==net)
                    px=spec['connector']['centre_mm'][0]+('abc'.index(pin[0])-1)*2.54;py=spec['connector']['centre_mm'][1]-39.37+(int(pin[1:])-1)*2.54
                    n=next(n for n in contract['nets'] if n['net']==net)
                    direction=n['source_crossing'].get('direction',{})
                    drivers=direction.get('source_nodes',[]) if isinstance(direction,dict) else []
                    ends=[e for e in n['endpoints'] if e['owner']=='rear-core']
                    sources=[e for e in ends if any(d['ref']==e['ref'] and d['pin']==e['pin'] for d in drivers)]
                    targets=sources or ends
                    require(targets,'missing rear endpoint')
                    rear=max(abs(x-px)+abs(y-py) for e in targets for x,y in byref[e['ref']]['pads_mm'][e['pin']])+spec['rear_fanout_mm']
                    middle=math.hypot(ox+px-front['x_mm'],oy+py-front['y_mm'])+spec['middle_detour_mm']
                    total=spec['front_trace_mm']+spec['front_flex_mm']+middle+spec['connector_path_mm']+rear
                    rows.append({'instance':instance,'link':link['id'],'pin':lp,'net':net,'DIN_pin':pin,'front_uid':uid,
                        'front_trace_allocation_mm':spec['front_trace_mm'],'front_flex_mm':spec['front_flex_mm'],
                        'middle_allocation_mm':middle,'connector_allocation_mm':spec['connector_path_mm'],'rear_pad_allocation_mm':rear,
                        'rear_endpoints':[e['ref']+':'+e['pin'] for e in targets], 'total_mm':total,'within_300mm':total<=300,
                        'return':'Dedicated retained AGND conductor in same front link; middle/rear corridor and parallel-return extraction OPEN',
                        'capacitance_pF':None,'acceptance':'OPEN: front pads/header positions, obstacles, return and capacitance not extracted'})
        return rows
    pinout=copy.deepcopy(old['rear_connector_pinout'])
    # Exact bottleneck matching across all contacts: one physical pin per signal,
    # optimize both adjacent instances together, never independent conflicting choices.
    signals=[p for p in pinout if p['net'] is not None and p['net']!='AGND']
    costs={}
    for signal in signals:
        costs[signal['net']]={}
        for slot in [p for p in pinout if p['pin'].startswith('c')]:
            trial=copy.deepcopy(pinout)
            next(p for p in trial if p['net']==signal['net'])['pin']=slot['pin']
            relevant=[r['total_mm'] for r in path_rows(trial) if r['net']==signal['net']]
            costs[signal['net']][slot['pin']]=max(relevant,default=0)
    def matching(threshold):
        used={}
        def visit(net,seen):
            for pin,cost in sorted(costs[net].items(),key=lambda p:(p[1],p[0])):
                if cost>threshold or pin in seen:continue
                seen.add(pin)
                if pin not in used or visit(used[pin],seen):used[pin]=net;return True
            return False
        for net in sorted(costs,key=lambda n:sum(v<=threshold for v in costs[n].values())):
            if not visit(net,set()):return None
        return used
    thresholds=sorted({v for row in costs.values() for v in row.values()})
    low,high=0,len(thresholds)-1
    while low<high:
        mid=(low+high)//2
        if matching(thresholds[mid]) is None:low=mid+1
        else:high=mid
    selected=matching(thresholds[low]);require(selected is not None,'no pin assignment')
    ground=[p for p in pinout if p['net']=='AGND']
    signal_by_net={p['net']:p for p in signals}
    require(len(selected)==26 and len(ground)==25,'unexpected source DIN population')
    added_ground={'net':'AGND','source_conductor':'added adjacent return; candidate only'}
    ground.append(added_ground)
    mapped=[]
    for p in pinout:
        pin=p['pin']
        if pin in selected: entry=signal_by_net[selected[pin]]
        elif pin.startswith('b') and 'c'+pin[1:] in selected:entry=ground.pop(0)
        else:entry={'net':None,'source_conductor':'NC spare'}
        mapped.append(dict(entry,pin=pin))
    pinout=mapped
    require(Counter(p['net'] for p in pinout)==Counter(p['net'] for p in old['rear_connector_pinout'])+Counter({'AGND':1})-Counter({None:1}), 'DIN conductor loss')
    rows=path_rows(pinout)
    endpoints=sorted((u['ref'],str(u['unit']),pin,net,u['proposed_owner']) for u in contract['parts'] for pin,net in u['pins'].items())
    source_netlist={'source_checkpoint':CHECKPOINT,'packages':list(ps.values()),'endpoints':endpoints,'NC_endpoints':[e for e in endpoints if e[3] is None],
        'shared_services':contract['shared_services'],'original_factory_terminals':contract['rear_terminals'],
        'DIN_electrical_pin_labels':pinout,'mating_face_geometry':'OPEN; electrical labels are not a verified mating-face transform','front_links':links,
        'native_schematic_ERC':'NOT RUN','native_board_DRC':'NOT RUN'}
    inputs=['implementation/candidate.json','interface-contract.json','revision-mechanical-report.json','revision-electrical-report.json','electrical-report.json']
    paths=[PACK/p for p in inputs]+[Path(__file__),ROOT/'scripts/architecture278/populated_mechanics.py']+[ROOT/p['footprint_source'] for p in placed]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    failures=[r for r in rows if not r['within_300mm']]
    report={'status':'SOURCE CANDIDATE; Stage 1 NOT ACCEPTED','source_sha256':hashes,'config':spec,'rear_placements':placed,
        'source_unit_count':len(contract['parts']),'package_count_including_nonphysical':len(ps),'rear_package_count':len(placed),'mechanical_model':mechanical(spec,placed),
        'rear_connector_pinout':pinout,'front_links':links,'transport_subtotal':{'harnesses':len(links),'conductors':sum(newnets.values()),'crimps':2*sum(newnets.values()),'GH_signal_solder_joints':2*sum(newnets.values()),'GH_hold_down_joints':4*len(links),'DIN_solder_joints':192},
        'paths':rows,'overlength_paths':failures,'maximum_evaluated_front_rear_path_mm':max(r['total_mm'] for r in rows),'unmodeled_shared_middle_nets':['OSC_REF5','OSC_REFN5','OSC_GATE_REF',*[f'OSC_OCT{i}' for i in range(6)]], 'adjacent_DIN_returns_added':1,
        'preserved_power_paths':old['paths'],'preserved_power_bound':old['power_bound'],
        'raw_wiper_loading':old['raw_wipers'],'five_receiver_dynamics':old['octave_dynamics'],
        'whole_path_limits':{'return_mOhm':.5,'rail_mOhm':1,'hot_mV':20,'source_rail_return_V':.2,'GH_contact_A':.5,'remote_pF':1000},
        'full_electrical_acceptance':'OPEN: source regulation, state maxima, contact/joint tolerances and actual paths unknown',
        'front_placement':'OPEN: entire source package/pin inventory retained; no populated front candidate yet',
        'mechanical_acceptance':'OPEN: candidate XY/tool/depth allocations only; exact solids, tails, guide engagement, strap bends, support strength and physical service unqualified',
        'native':'NOT RUN: no exact-run admission; installed CLI9.0.2 differs from required10.0.6',
        'missing_exact_MPNs':[p['ref'] for p in ps.values() if p['footprint'] and not p['attributes'].get('MPN')]}
    return report,source_netlist

def drawing(report):
    colors=['#d3e7f5','#e1e9be','#f5d8b4','#e1d2ee','#f6cccc','#c5e6de','#e4e4e4','#f6e9b1']
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="618" height="960" viewBox="0 0 103 160">','<rect width="103" height="160" fill="white"/>','<g font-family="sans-serif" font-size="2">','<text x="2" y="3">Candidate rear clusters — NOT ROUTED / NOT QUALIFIED</text>']
    for i,g in enumerate(report['config']['clusters']):
        x,y,xx,yy=g['box_mm'];lines.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="{colors[i]}"/><text x="{x}" y="{y-1}">{g["id"]}</text>')
    for f in report['mechanical_model']['fixtures']:
        x,y,xx,yy=f['box_mm'];lines.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="#eed6a7" stroke="#555" stroke-width=".2"/><text x="{x}" y="{y+2}" font-size="1.4">{f["id"]}</text>')
    for p in report['rear_placements']:
        x,y,xx,yy=p['box_mm'];lines.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="none" stroke="#222" stroke-width=".15"/><text x="{x}" y="{y+1.5}" font-size="1.3">{p["ref"]}</text>')
        if p['trim_tool_diameter_mm']:
            x,y=p['origin_mm'];lines.append(f'<circle cx="{x}" cy="{y}" r="3" fill="none" stroke="red" stroke-width=".2"/>')
    lines+=['<text x="2" y="155">Vertical DIN x2.5..17.5/y25..125; support/service layout OPEN.</text>','</g></svg>']
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    report,netlist=build()
    outputs={'candidate-report.json':json.dumps(report,indent=2,sort_keys=True)+'\n','candidate-netlist.json':json.dumps(netlist,indent=2,sort_keys=True)+'\n','candidate-clusters.svg':drawing(report)}
    for name,data in outputs.items():
        target=OUT/name
        if args.check:require(target.exists() and target.read_text()==data,'stale '+name)
        else:target.write_text(data)
    print(f'SOURCE reproduction PASS; {len(report["overlength_paths"])} overlength paths; max {report["maximum_evaluated_front_rear_path_mm"]:.3f}mm; Stage1 OPEN; native NOT RUN')
if __name__=='__main__':main()
