"""Complete physical source inventory and candidate power endpoint rebinding.

Coordinates are candidate footprint pads, not routes or accepted installed solids.
No native, aggregate, network, canonical writes or invented POWER placements.
"""
import argparse
from collections import Counter,defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import stage3_crossing_audit as audit

ROOT=audit.ROOT
OUT=ROOT/'design/architecture-278/implementation'
RAILS=('+12V','-12V','+5V','AGND')


def need(ok,message):
    if not ok:raise ValueError(message)


def source_inventory(ledger):
    result={p['ref']:{'ref':p['ref'],'instance':p['instance'],'family':p['family'],'units':p['units'],
        'mpn':p['mpn'],'dnp':p['dnp'],'retained_board':p['current_board'],'decouples_ref':p['decouples_ref'],
        'unit_records':[],'pins':{}} for p in ledger['packages']}
    need(len(result)==len(ledger['packages'])==5904,'complete physical package inventory')
    for unit in ledger['package_units']:
        p=result[unit['ref']]
        need(not set(unit['pins'])&set(p['pins']),'duplicate source physical pin')
        p['unit_records'].append(copy.deepcopy(unit));p['pins'].update(unit['pins'])
    for p in result.values():
        need(Counter(p['units'])==Counter(u['unit'] for u in p['unit_records']),'whole unit inventory '+p['ref'])
    need(sum(len(p['units']) for p in result.values())==8226,'complete physical unit inventory')
    return result


def xyz(pads,xy_offset,z):
    return {pin:[[x+xy_offset[0],y+xy_offset[1],z] for x,y in coords] for pin,coords in pads.items()}


def placed_inventory(best,assembly,source,ctx,shared_translation):
    placed={}
    def add(template,instance,pads,owner,plane,origin):
        physical=next(iter(template['pads_mm']))
        mapped=audit.map_endpoint(template['ref']+':'+physical,instance,ctx)
        ref=mapped['ref'];p=source[ref]
        need(ref not in placed,'duplicate placed package')
        need(set(pads)==set(p['pins']),'complete actual pad coverage '+ref)
        for pin in p['pins']:
            m=audit.map_endpoint(template['ref']+':'+pin,instance,ctx)
            need(m['ref']==ref and m['net']==p['pins'][pin],'whole package mapping mismatch')
        placed[ref]={'ref':ref,'template_ref':template['ref'],'instance':p['instance'],'owner':owner,
            'units':p['units'],'pads_xyz_mm':pads,'origin_xyz_mm':origin,
            'plane':plane}
    for instance in audit.INSTANCES:
        for p in assembly['front_instances'][instance]:
            if p['owner']=='header':continue
            depth=p.get('conditional_pcb_depth_mm',assembly['config']['front_depth_mm'])
            add(p,instance,xyz(p['pads_mm'],[0,0],depth),p['owner'],p['board'],p['origin_mm']+[depth])
        origin=best['origins_mm'][instance];depth=assembly['config']['rear_depth_mm']
        for p in best['packages']:
            add(p,instance,xyz(p['pads_mm'],origin,depth),'rear-core','rear-card',
                [p['origin_mm'][0]+origin[0],p['origin_mm'][1]+origin[1],depth])
    for p in assembly['shared_middle_placements']:
        depth=assembly['config']['middle_depth_mm']
        add(p,'O1',xyz(p['pads_mm'],shared_translation,depth),'shared-reference','middle-reference',
            [p['origin_mm'][0]+shared_translation[0],p['origin_mm'][1]+shared_translation[1],depth])
    expected={ref for ref,p in source.items() if p['instance'] in audit.INSTANCES+['OCTAVE_REF']}
    need(set(placed)==expected and len(placed)==1125,'all five and shared package coverage')
    return placed


def validate_coordinates(placed,best,assembly,source,ctx,shared_translation):
    expected=placed_inventory(best,assembly,source,ctx,shared_translation)
    need(placed==expected,'candidate endpoint coordinate/ownership drift')


def coverage(best,placed,source,ctx,assembly):
    paths=[];returns=[]
    need(len(best['paths'])==225 and len(best['returns'])==240 and len(best['shared_aggregate_capacitance'])==9,'crossing/return/shared count changed')
    def identity(row):
        ends=[audit.map_endpoint(row[k],row['instance'],ctx) for k in ('front_endpoint','other_endpoint')]
        return (row['instance'],row['net'].replace('/O1/','/'+row['instance']+'/'),row.get('link'),row.get('link_pin'),*(e['ref']+':'+e['pin'] for e in ends))
    expected=Counter(identity(r) for r in assembly['alternatives']['five_card_two_rows']['paths'])
    need(Counter(identity(r) for r in best['paths'])==expected,'crossing endpoint identity coverage')
    links={h['id']:h for h in json.loads((OUT/'candidate-report.json').read_text())['front_links']}
    for i,row in enumerate(best['paths']):
        actual=row['actual_identity'];ends={}
        for role in ('front','other'):
            need(actual[role]==audit.map_endpoint(row[role+'_endpoint'],row['instance'],ctx),'wrong actual source alias')
            ref,pin=actual[role]['ref'],actual[role]['pin']
            need(source[ref]['pins'][pin]==actual['actual_net'],'crossing source net mismatch')
            ends[role]={'endpoint':ref+':'+pin,'pads_xyz_mm':placed[ref]['pads_xyz_mm'][pin]}
        paths.append({'source_path_index':i,'instance':row['instance'],'net':actual['actual_net'],**ends,
            'source_total_mm':row['total_mm'],'length_status':'inherited stage3 budget only; any shared-coordinate translation requires recomputation by candidate generator'})
    def return_key(row):return (row['instance'],row.get('link'),row.get('contact') if 'link' in row else row['from'])
    expected_returns=[]
    original=assembly['alternatives']['five_card_two_rows']
    for row in original['returns']:
        if 'link' in row:expected_returns.append(return_key(row))
        else:
            oldpin=row['from'].split(':')[1]
            net=next(n for n,label in original['DIN_signal_labels'].items() if label[1:]==oldpin[1:])
            expected_returns.append((row['instance'],None,'DIN:b'+best['common_DIN_signal_labels'][net][1:]))
    need(Counter(map(return_key,best['returns']))==Counter(expected_returns),'return group coverage')
    for i,row in enumerate(best['returns']):
        audit.validate_return(row,ctx,links,best['common_DIN_signal_labels'])
        ids=[]
        for endpoint in row['endpoint_ids']:
            mapped=audit.map_endpoint(endpoint,row['instance'],ctx);ref,pin=mapped['ref'],mapped['pin']
            need(source[ref]['pins'][pin]=='AGND' and ref in placed,'invalid ground endpoint')
            ids.append(ref+':'+pin)
        need(len(ids)==len(set(ids)),'duplicate return endpoint')
        returns.append({'source_return_index':i,'instance':row['instance'],'contact':row.get('from',row.get('contact')),
            'link':row.get('link'),'actual_AGND_endpoint_ids':ids,'resistance_mOhm':None,
            'status':'coordinates resolved through placed_packages; new source/common ground topology and impedance NOT EXTRACTED'})
    shared=copy.deepcopy(best['shared_aggregate_capacitance'])
    need({x['net'] for x in shared}==audit.SHARED and all(set(x['instances'])==set(audit.INSTANCES) for x in shared),'complete nine shared nets')
    return paths,returns,shared


def rebind_variant(name,best,assembly,ledger,ctx,shared_translation=(0,0)):
    need(len(shared_translation)==2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in shared_translation),'invalid shared translation')
    source=source_inventory(ledger);placed=placed_inventory(best,assembly,source,ctx,shared_translation)
    validate_coordinates(placed,best,assembly,source,ctx,shared_translation)
    # Whole global supply/return population: unknown coordinates remain null.
    supplies={}
    for net in RAILS:
        endpoints=[]
        for ref,p in source.items():
            for pin,n in p['pins'].items():
                if n!=net:continue
                endpoints.append(ref+':'+pin)
        supplies[net]={'external_source':{'id':'external-source:'+net,'pads_xyz_mm':None,'regulation_V':None,'status':'hardware/source binding OPEN'},
            'physical_endpoints':endpoints,'placed_endpoint_count':sum(e.split(':')[0] in placed for e in endpoints),
            'unplaced_endpoint_count':sum(e.split(':')[0] not in placed for e in endpoints),
            'routed_edges':None,'common_distribution_resistance_mOhm':None,'contact_joint_tolerance_mOhm':None,
            'parallel_current_solution':None,'status':'complete physical endpoint inventory; rail/source/return topology and state maxima NOT EXTRACTED'}
    bypass=[]
    extra={a['capacitor']:a['package'] for a in assembly['bypass_associations'] if a['owner']=='shared-reference'}
    for ref,p in source.items():
        target=p['decouples_ref'] or extra.get(ref)
        if not target:continue
        need(target in source,'missing bypass target')
        need(p['instance']==source[target]['instance'],'cross-instance bypass association')
        bypass.append({'capacitor':ref,'target':target,'instance':p['instance'],
            'association_basis':'retained ledger decouples_ref' if p['decouples_ref'] else 'retained shared source association from assembly report',
            'candidate_positions_bound':ref in placed and target in placed})
    paths,returns,shared=coverage(best,placed,source,ctx,assembly)
    unplaced=[ref for ref in source if ref not in placed]
    need(len(unplaced)==4779 and sum(source[r]['instance']=='POWER' for r in unplaced)==13,'other/POWER package coverage')
    return {'name':name,'status':'CANDIDATE ENDPOINT COORDINATES ONLY; Stage1 OPEN','shared_translation_mm':list(shared_translation),
        'coordinate_binding':'Every graph endpoint REF:PIN resolves to placed_packages[REF].pads_xyz_mm[PIN]; absent package resolves to null. This shared table is authoritative for supplies, bypasses and return groups.',
        'coordinate_frame':'panel XY; positive rearward conditional candidate PCB-depth Z; seated solids/tails/tolerance NOT QUALIFIED',
        'bypass_routing_status':'All associations retained; pad binding does not establish ground/via loop, inductance or feedback stability.',
        'placed_packages':placed,'placed_package_count':len(placed),'placed_unit_count':sum(len(p['units']) for p in placed.values()),
        'unplaced_package_refs':unplaced,'unplaced_package_count':len(unplaced),
        'supplies':supplies,'bypass_associations':bypass,'crossing_endpoint_bindings':paths,'return_group_bindings':returns,'shared_aggregate_capacitance':shared,
        'POWER_package_geometry':{r:None for r in unplaced if source[r]['instance']=='POWER'},
        'accepted':False,'native':'NOT RUN'}


def validate_supply_inventory(variant,source):
    for net in RAILS:
        expected=Counter(ref+':'+pin for ref,p in source.items() for pin,n in p['pins'].items() if n==net)
        got=Counter(variant['supplies'][net]['physical_endpoints'])
        need(expected==got,'missing/duplicate supply or return endpoint')
        for e in variant['supplies'][net]['physical_endpoints']:
            ref,pin=e.split(':')
            p=variant['placed_packages'].get(ref)
            need(p is None or pin in p['pads_xyz_mm'],'supply coordinate reference unresolved')
    need(all(v is None for v in variant['POWER_package_geometry'].values()),'invented POWER placement')


def build():
    ledger=json.loads((ROOT/'design/architecture-278/source-ledger.json').read_text());source=source_inventory(ledger)
    assembly=json.loads((OUT/'assembly-report.json').read_text());direct=json.loads((OUT/'direct-study-report.json').read_text())
    ctx=audit.context();variants={}
    scenarios=[(n,b,(0,0)) for n,b in direct['best_by_variant'].items()]+[('baseline_shared_x6',direct['best_by_variant']['baseline'],(6,0))]
    for name,best,translation in scenarios:
        variants[name]=rebind_variant(name,best,assembly,ledger,ctx,translation);validate_supply_inventory(variants[name],source)
    unit_count=sum(len(p['unit_records']) for p in source.values());pin_count=sum(len(p['pins']) for p in source.values())
    # Explicit original 249-package template graph correspondence before expansion.
    need(len(assembly['supply_graph'])==4,'retained supply graph missing rail')
    for net,g in assembly['supply_graph'].items():
        original=Counter(e['ref'] for e in g['physical_endpoints'])
        expected=Counter(ref+':'+pin for ref,p in source.items() if p['instance'] in ('O1','OCTAVE_REF') for pin,n in p['pins'].items() if n==net)
        need(original==expected,'original249package power graph omitted endpoint')
    paths=[Path(__file__),Path(__file__).with_name('test_stage4_power_inventory.py'),Path(audit.__file__),OUT/'assembly-report.json',OUT/'direct-study-report.json',ROOT/'design/architecture-278/source-ledger.json',ROOT/'design/reports/io-partition.json',OUT/'stage3-crossing-audit.json',OUT/'candidate-report.json']
    contract=json.loads((ROOT/'design/architecture-278/interface-contract.json').read_text())
    paths += [ROOT/p for p in contract['source_sha256']]+[ROOT/'design/architecture-278/interface-contract.json']
    return {'status':'FULL RETAINED POWER INVENTORY AND CANDIDATE PAD REBINDING; routing/acceptance OPEN',
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},
        'retained_packages':{ref:{**{k:v for k,v in p.items() if k!='unit_records'},'pin_to_unit':{pin:u['unit'] for u in p['unit_records'] for pin in u['pins']}} for ref,p in source.items()},'retained_package_count':len(source),'retained_unit_count':unit_count,'retained_pin_count':pin_count,
        'retained_NC_pin_count':sum(n is None for p in source.values() for n in p['pins'].values()),
        'original_template_physical_package_count':249,'five_oscillator_plus_shared_package_count':1125,'other_function_package_count':4766,'POWER_package_count':13,
        'variants':variants,'limitations':['No other-function or POWER package placement invented; historical coordinates are not transferred into candidate stack.',
            '249 original physical packages expand to1095 OSC plus30 shared packages by exact live source Ref/unit/pin mapping; all other4766 and13POWER remain in the same5904package ledger.',
            'Every signal, feedback, bypass, supply, return and NC source pin is preserved in retained_packages; coordinates exist only for placed1125 packages.',
            'Shared x+6 scenario rebinds coordinates only. Existing crossing totals are labeled inherited; new shared route budgets must be recalculated by candidate generator.',
            'PCB-plane Z values are conditional design datums, not measured package height/lead solids or fit qualification.',
            'Source/common/branch/load/return routed graph, capacitance, exact currents, impedances, voltage drop and fault-state maxima remain unknown.'],
        'native':'NOT RUN','accepted':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
    path=OUT/'stage4/power-inventory-report.json';text=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n'
    if args.check:need(path.read_text()==text,'stale stage4 power inventory')
    else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    print('PASS5904packages/8226units;1125candidateplaced,4779unplaced;225crossings/240returngroups/9shared pervariant; railrouting NOT EXTRACTED')
