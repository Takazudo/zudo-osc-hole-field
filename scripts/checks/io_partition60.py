#!/usr/bin/env python3
"""Fail-closed source/package/net boundary and courtyard necessary-condition audit."""
from __future__ import annotations
import argparse
from collections import defaultdict, Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from design.spec.instrument import specification
from design.spec.cells._builder import load_symbol
from design.spec.modules.io_partition import AMP_MAPS
from scripts.schgen.core import designator, parse, tokens, children
from scripts.schgen.verify_netlist import verify
from scripts.checks.prepartition54 import canonical_netlist_sha256

OUT = ROOT/'design/reports/io-partition.json'
RAILS = {'+12V','-12V','+5V','AGND'}


@lru_cache(None)
def courtyard(footprint):
    path=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(footprint.split(':')[-1]+'.kicad_mod')
    tree,_=parse(tokens(path.read_text()))
    points=[]
    for node in tree:
        if not isinstance(node,list) or not node or node[0] not in ('fp_line','fp_rect','fp_poly'):continue
        layers=children(node,'layer')
        if not layers or layers[0][1] not in ('F.CrtYd','B.CrtYd'):continue
        for tag in ('start','end'):
            points.extend((float(p[1]),float(p[2])) for p in children(node,tag))
        for pts in children(node,'pts'):
            points.extend((float(p[1]),float(p[2])) for p in children(pts,'xy'))
    if not points:raise ValueError(f'missing linear courtyard: {path}')
    xs,ys=zip(*points);w=max(xs)-min(xs);h=max(ys)-min(ys)
    return {'width_mm':round(w,6),'height_mm':round(h,6),'area_mm2':round(w*h,6),
            'footprint_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'through_hole':bool(children(tree,'attr') and 'through_hole' in children(tree,'attr')[0])}


def reverse_jack_pad_area():
    """Disjoint opposite-face pad copper is an additional area lower bound."""
    path=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty/Jack_3.5mm_QingPu_WQP518MA.kicad_mod'
    tree,_=parse(tokens(path.read_text()));pads=[]
    for p in children(tree,'pad'):
        if p[2]!='thru_hole':continue
        w,h=map(float,children(p,'size')[0][1:3]);x,y=map(float,children(p,'at')[0][1:3])
        if p[3]=='circle':area=math.pi*w*h/4
        elif p[3]=='rect':area=w*h
        elif p[3]=='oval':area=min(w,h)*(max(w,h)-min(w,h))+math.pi*min(w,h)**2/4
        else:raise ValueError('unsupported jack through-hole pad shape')
        pads.append((x,y,w,h,area))
    boxes=[];area=0
    for row in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']:
        if not row['uid'].startswith('J:'):continue
        if row['rot_deg']!=0:raise ValueError('unexpected jack rotation')
        for x,y,w,h,a in pads:
            x+=row['x_mm'];y+=row['y_mm'];box=(x-w/2,y-h/2,x+w/2,y+h/2)
            if any(box[0]<b[2] and b[0]<box[2] and box[1]<b[3] and b[1]<box[3] for b in boxes):raise ValueError('opposite jack pad areas overlap')
            boxes.append(box);area+=a
    return area


def source_data(families=None, instances=None):
    if families is None:families,instances=specification()
    byname={f.name:f for f in families};packages={};nets=defaultdict(list);sensitive=set();units=[]
    for inst in instances:
        f=byname[inst.family]
        stem_refs={p.key.rsplit('.',1)[0]:designator(p,inst) for p in f.parts}
        def netname(n):return n if n in f.global_nets else f'/{inst.name}/{n}'
        sensitive.update(netname(n) for n in f.sensitive_nets)
        for p in f.parts:
            if p.symbol.startswith('Fixture:') or p.abstract:continue
            ref=designator(p,inst)
            uid=p.attributes.get('PanelUid','').replace('${SHEETNAME}',inst.name)
            reg=p.attributes.get('BoardRegion','core')
            if reg=='selector':reg='selector_rear' if inst.name in ('O2','O4') else 'selector_front'
            island=p.attributes.get('Island','').replace('${SHEETNAME}',inst.name)
            q=packages.setdefault(ref,{'ref':ref,'instance':inst.name,'family':f.name,'mpn':p.attributes.get('MPN',''),
                    'symbol':p.symbol.split(':')[-1],'footprint':p.footprint,'dnp':p.dnp,
                    'panel_uid':uid,'decouples_ref':stem_refs.get(p.attributes.get('Decouples')),'units':[],'regions':set(),'islands':set(),
                    'courtyard':courtyard(p.footprint)})
            q['units'].append(p.unit);q['regions'].add(reg);q['islands'].add(island)
            units.append({'ref':ref,'unit':p.unit,'region':reg,'key':p.key,'role':p.attributes.get('Role',''),
                          'logical_key':p.attributes.get('LogicalCellKey') or p.key,
                          'pins':{k:netname(n) if n is not None else None for k,n in p.pins.items()}})
            library=load_symbol(p.symbol.split(':')[-1]);pin_types={v.number:v.electrical for v in library.units[p.unit]}
            for pin,n in p.pins.items():
                if n is not None:
                    nets[netname(n)].append({'ref':ref,'unit':p.unit,'pin':pin,'region':reg,'island':island,
                                           'role':p.attributes.get('Role',''),'type':pin_types[pin], 'uid':uid})
            if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in range(1,5):
                output,minus,_=AMP_MAPS[p.unit-1]
                if p.pins[minus] != p.pins[output]:sensitive.add(netname(p.pins[minus]))
    for p in packages.values():
        p['regions']=sorted(p['regions']);p['islands']=sorted(p['islands'])
    return packages,nets,sensitive,units


def assignment_errors(packages, assignments):
    errors=[];seen=Counter(row['ref'] for row in assignments)
    for ref in sorted(set(packages)|set(seen)):
        if seen[ref]!=1:errors.append(f'assignment count {ref}: {seen[ref]} (expected 1)')
        if ref not in packages:errors.append(f'unknown assigned package {ref}')
    for row in assignments:
        if row['ref'] in packages and packages[row['ref']]['regions'] != [row['region']]:
            errors.append(f"split/swapped package region {row['ref']}: source {packages[row['ref']]['regions']}, assigned {row['region']}")
    return errors


def crossing_kind(name, members, sensitive, nets=None):
    if name in sensitive:return None,'sensitive storage, summing or feedback node'
    if name.endswith('_TIP'):return None,'raw/exposed jack TIP'
    if name in RAILS:return 'power/return',None
    # Only real driven outputs qualify; passive output symbol types on jacks and
    # switches cannot make an unconditioned net a buffered signal.
    drivers=[m for m in members if m['type']=='output' and m['ref'].startswith('U')]
    if drivers:
        return 'conditioned logic' if all(m['role'].startswith(('switch_button_input:','gate_trigger_input:')) or 'LOGIC_' in m['role'] for m in drivers) else 'buffered signal/reference',None
    # remote_buffer post-resistor output is locally sensed via R_FB. This exact
    # cell is the standard's conditioned internal harness source.
    if any(m['role']=='remote_buffer:R_ISO' and m['pin']=='2' for m in members):return 'compensated remote buffer',None
    if any(m['role']=='internal_selector_buffer:R_ISO_B' and m['pin']=='2' for m in members):
        return 'isolated internal selector buffer',None
    # A remote wiper is allowed only for the declared standard control cells;
    # a selector or signal switch requires source tracing, not a broad waiver.
    if any(m['uid'].startswith('C:') and m['pin']=='2' and m['role'].split(':')[0] in ('dc_control_source','bipolar_attenuverter','level_attenuator') for m in members):return 'wiper to high impedance receiver',None
    switched = {'oscillator:OCT_SELECTOR': {'1','10'}, 'oscillator:RANGE': {'2'},
                'oscillator:SYNC_SELECT': {'1','3'}}
    for member in members:
        if member['pin'] not in switched.get(member['role'],set()) or nets is None:continue
        source_pins={'oscillator:OCT_SELECTOR':set('234567'), 'oscillator:RANGE':{'1','3'}, 'oscillator:SYNC_SELECT':{'2'}}[member['role']]
        sources=[(n,ms) for n,ms in nets.items() if any(m['ref']==member['ref'] and m['pin'] in source_pins for m in ms)]
        if sources and all(n=='AGND' or any(m['type']=='output' and m['ref'].startswith('U') for m in ms) for n,ms in sources):
            return 'selected buffered reference/conditioned logic',None
    return None,'no supported buffered/conditioned crossing source'


def build(families=None, instances=None, assignments=None, capacities=None):
    packages,nets,sensitive,units=source_data(families,instances)
    if assignments is None:assignments=[{'ref':r,'region':p['regions'][0]} for r,p in sorted(packages.items())]
    errors=assignment_errors(packages,assignments)
    for p in packages.values():
        expected={unit for unit,pins in load_symbol(p['symbol']).units.items() if pins}
        if set(p['units'])!=expected or len(p['units'])!=len(set(p['units'])):
            errors.append(f"package unit coverage {p['ref']}: {p['units']} != {sorted(expected)}")
        if not set(p['regions']) <= {'jack','control','core','selector_front','selector_rear'}:
            errors.append(f"unknown source region {p['ref']}: {p['regions']}")
    regions={r['ref']:r['region'] for r in assignments}
    crossings=[];forbidden=[];local=[]
    for name,rows in sorted(nets.items()):
        members=[{**m,'region':regions.get(m['ref'],'MISSING')} for m in rows]
        boards=sorted({m['region'] for m in members})
        if len(boards)<2:
            if name in sensitive or name.endswith('_TIP'):local.append({'net':name,'region':boards[0],'refs':sorted({m['ref'] for m in members})})
            continue
        kind,reason=crossing_kind(name,members,sensitive,nets)
        row={'net':name,'regions':boards,'kind':kind,'members':members}
        if reason:
            row['reason']=reason;forbidden.append(row)
        else:
            driver_members=[m for m in members if m['type']=='output' and m['ref'].startswith('U')]
            if not driver_members:
                driver_members=[m for m in members if (m['role']=='remote_buffer:R_ISO' or m['role']=='internal_selector_buffer:R_ISO_B') and m['pin']=='2'
                                or m['uid'].startswith('C:') and (m['pin']=='2' or m['role']=='oscillator:OCT_SELECTOR' and m['pin'] in ('1','10')
                                or m['role']=='oscillator:SYNC_SELECT' and m['pin'] in ('1','3'))]
            drivers=sorted({m['region'] for m in driver_members})
            row.update(direction={'drivers':drivers, 'receivers':sorted(set(boards)-set(drivers)),
                                  'source_nodes':[{'ref':m['ref'],'pin':m['pin']} for m in driver_members]},
                       voltage_V={'minimum':-12,'maximum':12,'basis':'OSC-ES-1 analog operating rails; nominal signal typically +/-5 V, ENV 0..8 V; not a fault qualification'},
                       current_mA={'design_limit':2,'status':'OSC-ES-1 signal-driver planning limit; connector fanout/load sum to be checked in #35'},
                       capacitance_F={'maximum':1e-9,'basis':'OSC-ES-1 remote_controls design envelope, physical stability NOT RUN'},
                       max_harness_length_m=.3, adjacent_return='AGND')
            if kind=='power/return':
                contracts={'+12V':(12,1900,150e-6),'-12V':(-12,1800,150e-6),'+5V':(5,400,100e-6),'AGND':(0,4400,None)}
                voltage,current,capacitance=contracts[name]
                row.update(direction={'source':'EXT conditional boundary/star','receivers':boards}, voltage_V={'nominal':voltage,'status':'conditional regulated rail'},current_mA={'whole_domain_transient_requirement':current,'status':'not a per-contact allocation'},capacitance_F={'whole_domain_nominal_ceiling':capacitance,'initial_bulk_per_powered_board':4.7e-6 if name!='AGND' else None,'status':'board count OPEN #35'})
            crossings.append(row)
    # An island may contain multiple independent package sections, but cannot
    # straddle boards. DNP parts count for ownership, not fitted area.
    islands=defaultdict(lambda:{'regions':set(),'refs':set(),'panel_uids':set()})
    for p in packages.values():
        for island in p['islands']:
            if not island:continue
            key=p['instance']+'/'+island
            islands[key]['regions'].add(regions.get(p['ref'],'MISSING'));islands[key]['refs'].add(p['ref'])
            if p['panel_uid']:islands[key]['panel_uids'].add(p['panel_uid'])
    island_rows=[]
    for key,v in sorted(islands.items()):
        row={'island_id':key,**{k:sorted(x) for k,x in v.items()}}
        if len(v['regions'])!=1:errors.append(f'split island {key}: {sorted(v["regions"])}')
        row['local_nets']=[name for name,ms in nets.items() if any(m['ref'] in v['refs'] for m in ms) and len({regions.get(m['ref']) for m in ms})==1]
        row['allowed_crossing_nets']=[x['net'] for x in crossings if any(m['ref'] in v['refs'] for m in x['members'])]
        island_rows.append(row)
    capacities=capacities or {'jack':{'width_mm':306,'height_mm':140,'faces':2}}
    area=[]
    for reg in sorted(set(regions.values())):
        parts=[p for r,p in packages.items() if regions.get(r)==reg and not p['dnp']]
        used=sum(p['courtyard']['area_mm2'] for p in parts)
        through=sum(p['courtyard']['area_mm2'] for p in parts if p['courtyard']['through_hole'])
        opposite=reverse_jack_pad_area() if reg=='jack' else 0
        occupied=used+opposite
        capacity=capacities.get(reg)
        gross=capacity['width_mm']*capacity['height_mm']*capacity['faces'] if capacity else None
        area.append({'region':reg,'packages':len(parts),'courtyard_sum_mm2':round(used,3),
                     'through_hole_courtyard_mm2':round(through,3),'proposal':capacity,
                     'opposite_jack_pad_area_mm2':round(opposite,6),'occupied_lower_bound_mm2':round(occupied,6),
                     'gross_face_area_mm2':gross,'gross_residual_mm2':round(gross-occupied,3) if gross else None,
                     'usable_area_mm2':None,'status':'FAIL' if gross is not None and occupied>gross else 'NECESSARY AREA BOUND ONLY' if gross else 'OPEN: dimensions required',
                     'unbooked':'connectors, supports, routing, through-hole reverse-face exclusions, protection #59 and real usable-region geometry'})
    errors.extend(f"area lower bound exceeds gross faces: {r['region']}" for r in area if r['status']=='FAIL')
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
    fixed_digest=hashlib.sha256(json.dumps(sorted((p['uid'],p['x_mm'],p['y_mm']) for p in lock),separators=(',',':')).encode()).hexdigest()
    if fixed_digest!='8354aed4a72bf5357e1ccfb4da7c3234f139ba19f75a49d825d733c30a6da843':errors.append('fixed R21 UID/XY digest changed')
    extra_refs=sorted({u['ref'] for u in units if u['key'].startswith('IO_EXTRA_')})
    return {'schema_version':1,'fixed_uid_xy_sha256':fixed_digest,'source_cut_accepted':not(errors or forbidden),'added_fitted_quads':extra_refs,
            'rail_change':{'planning_quiescent_delta_mA':{'+12V':16,'-12V':16,'+5V':0},'bypass_delta_uF':{'+12V':.6,'-12V':.6,'+5V':0},'basis':'Four exact OPA4196IDR at 1mA/rail and two exact OPA4197IPWR at 6mA/rail, full-temperature quiescent only. Generated current worksheets, rail ledger and supply architecture are the load authority.'},'status':'BLOCKED' if errors or forbidden else 'DRAFT ELECTRICAL CUT; FIT/CONNECTOR LOADS OPEN',
            'module_count':len({p['instance'] for p in packages.values()}-{'POWER','OCTAVE_REF'}),
            'fixed_uid_count':len({p['panel_uid'] for p in packages.values() if p['panel_uid']}),
            'source_domain':'EXT conditional requirement only; #59 protection OPEN; #55/#57 physical fit NOT RUN',
            'errors':errors,'forbidden_crossings':forbidden,'allowed_crossings':crossings,'local_raw_sensitive_nets':local,
            'package_assignments':assignments,'physical_packages':list(packages.values()),'package_units':units,'islands':island_rows,
            'area_lower_bounds':area,'complete_cut_accepted':False,
            'limits':'Courtyard sums are necessary area bounds only. Open current/voltage receiver contracts, connector pin counts, geometry and physical fit prevent acceptance of the final #35 physical partition.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--netlist',type=Path,required=True);parser.add_argument('--check',action='store_true');parser.add_argument('--require-cut',action='store_true');args=parser.parse_args()
    families,instances=specification();diff=verify(families,instances,args.netlist.read_text())
    if diff:raise SystemExit('\n'.join(diff))
    report=build(families,instances)
    report['native_netlist']={'oracle':'KiCad 10.0.6 via scripts/kicad/run.sh','sha256':canonical_netlist_sha256(args.netlist),'parity':'PASS'}
    # One physical/package/net record per line keeps this large machine
    # manifest reviewable without repeating hundreds of thousands of indent lines.
    fields=[]
    for key,value in report.items():
        if isinstance(value,list):
            body='[\n'+',\n'.join('    '+json.dumps(row,ensure_ascii=False) for row in value)+'\n  ]'
        else:body=json.dumps(value,ensure_ascii=False)
        fields.append('  '+json.dumps(key)+': '+body)
    text='{\n'+',\n'.join(fields)+'\n}\n'
    if args.check:
        if OUT.read_text()!=text:raise SystemExit('I/O boundary report drift')
    else:OUT.write_text(text)
    print(f"{report['status']}: {len(report['physical_packages'])} physical package rows; {len(report['allowed_crossings'])} candidate crossings; {len(report['forbidden_crossings'])} forbidden crossings; {len(report['errors'])} assignment/island errors")
    for row in report['area_lower_bounds']:print(row['region'],row['courtyard_sum_mm2'],row['status'])
    if args.require_cut and not report['source_cut_accepted']:raise SystemExit(1)

if __name__=='__main__':main()
