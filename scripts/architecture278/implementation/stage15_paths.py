"""Replace six resistors with two local networks in the complete allocation graph."""
import argparse
import copy
import json
from pathlib import Path
import stage15_packages as packages
import stage10_interfaces as interface
import stage12_budget as budget
import stage11_electrical as old_electrical
import stage11_assessment as common

ROOT=packages.ROOT
OUT=packages.OUT
need=common.need
read=packages.read


def remap(value, aliases):
    if isinstance(value,str):return aliases.get(value,value)
    if isinstance(value,list):return [remap(x,aliases) for x in value]
    if isinstance(value,dict):return {aliases.get(k,k):remap(v,aliases) for k,v in value.items()}
    return value


def mapping(graph,previous,inv):
 expected={f'{ref}:{pin}':net for ref,p in inv['packages'].items()for pin,net in p['pins'].items()if net in ('AGND','+12V','-12V','+5V')}
 rows=previous['power_and_return_endpoint_paths'];need(len(rows)==108 and {r['to']:r['net']for r in rows}==expected,'all108 actual source endpoints')
 usage={}
 for row in rows:
  for i in row['edge_indices']:usage[i]=usage.get(i,0)+1
 out=[]
 for row in rows:
  here=row['source_boundary'];terms=[]
  for i in row['edge_indices']:
   e=graph['edges'][i];need(e['net']==row['net']and here in (e['from'],e['to']),'continuous actual path')
   here=e['to']if here==e['from']else e['from']
   terms.append({'edge_index':i,'kind':e['kind'],'domains':budget.edge_domains(e['kind']),'from':e['from'],'to':e['to'],'allocated_mm':e['allocated_developed_mm'],'wire_max_mm':e['wire_cut_max_mm'],'GH_contacts':e['mated_GH_contacts'],'DIN_contacts':int(e['kind']=='DIN_mated_pair'),'endpoint_walk_use_count':usage[i],'resistance_ohm':None,'shared_current_A':None})
  need(here==row['to']and graph['nodes'][here]['net']==row['net'],'actual endpoint net')
  out.append({'to':row['to'],'net':row['net'],'source_boundary':row['source_boundary'],'source_pad_xyz_mm':graph['nodes'][here]['pad_xyz_mm'],'edge_terms':terms,'upstream_source_feed':{'domain':'upstream_source_feed','resistance_ohm':None,'regulation_error_V':None},'original_plane_requirement':{'limit_ohm':.0005 if row['net']=='AGND'else .001,'applies_to':'Combined applicable PCB spreading/necks/vias domain across boards, not each edge and not contacts/wires','applicability':'Mapping to split A01 boards requires review; source value preserved'},'expanded_architecture_comparison':{'limit_ohm':.0005 if row['net']=='AGND'else .001,'applies_to':'Broader complete branch/common or rail transfer wording; unresolved conflict of domains','accepted_redefinition':False},'complete_transfer_error_V':None})
 return out

def analyze(overlay, old_graph, old_paths, inventory, support, old_feed):
    aliases=overlay['endpoint_aliases'];places=overlay['placements']
    need(len(aliases)==12 and len(set(aliases.values()))==12,'complete injective twelve endpoint migration')
    graph=remap(copy.deepcopy(old_graph),aliases)
    graph.pop('source_sha256',None)
    for old,new in aliases.items():
        ref,pin=new.split(':');node=graph['nodes'][new]
        need(old_graph['nodes'][old]['net']==places[ref]['pins'][pin], 'replacement net identity')
        node.update(id=new,ref=ref,pin=pin,pad_xyz_mm=places[ref]['pads_xyz_mm'][pin][0])
    for ref in ('RN7101','RN7102'):
        p=places[ref]
        for pin,net in p['pins'].items():
            key=ref+':'+pin
            if key in graph['nodes']:continue
            graph['nodes'][key]={'id':key,'ref':ref,'pin':pin,'net':net,'pad_xyz_mm':p['pads_xyz_mm'][pin][0],'kind':'source'}
            if net is None:graph['NC_source_endpoints'].append(key)
            else:
                need(pin=='9' and net=='AGND','only added shield return')
                graph['source_endpoints'].append(key)
                group=next(g for g in graph['local_net_groups'] if g['owner']==p['owner'] and g['net']=='AGND')
                group['source_endpoints'].append(key)
                graph['edges'].append({'net':net,'from':group['anchor'],'to':key,'kind':'local_source_copper','allocated_developed_mm':0,'wire_cut_max_mm':0,'mated_GH_contacts':0,'routed_mm':None})
    changes=[]
    for i,e in enumerate(graph['edges']):
        affected=i>=len(old_graph['edges']) or any(n in aliases.values() for n in (e['from'],e['to']))
        if affected:
            need(e['kind'] in ('local_source_copper','local_transport_branch'),'no remote feedback or transport replacement')
            e['allocated_developed_mm']=interface.trace_length(graph['nodes'][e['from']]['pad_xyz_mm'],graph['nodes'][e['to']]['pad_xyz_mm'])
            changes.append({'edge_index':i,'before':old_graph['edges'][i] if i<len(old_graph['edges']) else None,'after':copy.deepcopy(e)})
        else:need(e==old_graph['edges'][i],'unaffected edge changed')
    # Rebuild every path from graph connectivity; historical ordering is not evidence of reachability.
    paths=remap(copy.deepcopy(old_paths),aliases);paths.pop('source_sha256',None);paths.pop('interface_object_sha256',None)
    groups=graph['local_net_groups'];paths['all_local_net_groups']=copy.deepcopy(groups)
    paths['NC_source_endpoints']=graph['NC_source_endpoints']
    for group in groups:
        for key in group['source_endpoints']:
            if key.endswith(':9') and key.startswith('RN'):
                paths['local_endpoint_paths'].append({'net':'AGND','owner':group['owner'],'from':group['anchor'],'to':key,'scope':'Local quiet AC shield; no resistor-terminal DC connection. Noise/impedance unknown.'})
                paths['power_and_return_endpoint_paths'].append({'net':'AGND','source_boundary':graph['upstream_power_boundaries']['AGND'],'to':key,'scope':'New shield return; no invented DC load. Complete current and impedance unknown.'})
    deltas={}
    for name in ('signal_net_paths','local_endpoint_paths','power_and_return_endpoint_paths'):
        power=name=='power_and_return_endpoint_paths';metric='allocated_developed_mm' if power else 'complete_net_pad_path_allocation_mm'
        previous={r['to']:r for r in remap(old_paths[name],aliases)};delta=[]
        for row in paths[name]:
            start=row['source_boundary'] if power else row['from']
            indices=interface.path_edges(graph,start,row['to']);edges=[graph['edges'][i] for i in indices]
            need(all(e['net']==row['net'] for e in edges),'walk net continuity')
            row['edge_indices']=indices;row[metric]=sum(e['allocated_developed_mm'] for e in edges)
            wire=sum(e['wire_cut_max_mm'] for e in edges)
            if power:row['wire_cut_max_mm']=wire
            elif name=='signal_net_paths':
                row.update(harness_wire_cut_max_mm=wire,GH_mated_contacts=sum(e['mated_GH_contacts'] for e in edges),DIN_mated_contacts=sum(e['kind']=='DIN_mated_pair' for e in edges),routed_mm=None)
            else:row['all_wire_cut_max_mm']=wire
            prev=previous.get(row['to'])
            if prev is None or prev[metric]!=row[metric]:delta.append({'to':row['to'],'net':row['net'],'before_mm':None if prev is None else prev[metric],'after_mm':row[metric],'actual_copper_mm':None})
        deltas[name]=delta
    source={f'{r}:{p}' for r,v in places.items() for p,n in v['pins'].items() if n is not None}
    nc={f'{r}:{p}' for r,v in places.items() for p,n in v['pins'].items() if n is None}
    need(set(graph['source_endpoints'])==source and set(graph['NC_source_endpoints'])==nc,'full active/NC package-pad parity')
    need({r['to'] for r in paths['local_endpoint_paths']}==source,'every connected physical pad represented')
    expected_power={k for k in source if graph['nodes'][k]['net'] in ('AGND','+12V','-12V','+5V')}
    need(len(expected_power)==108 and {r['to'] for r in paths['power_and_return_endpoint_paths']}==expected_power,'all106 original plus two shields')
    for row in old_paths['power_and_return_endpoint_paths']:
        new=next(r for r in paths['power_and_return_endpoint_paths'] if r['to']==row['to'])
        need(new==row,'prior power/return geometry changed')
    for key in ('counts',):
        counts=copy.deepcopy(old_graph[key]);counts.update(source_packages=86,source_units=120,source_pins_including_NC=291)
        graph[key]=counts;paths[key]=counts
    # Update net endpoint ownership for network pads; logical source function mapping retained separately.
    inv=copy.deepcopy(inventory)
    for ref in packages.REPLACED:del inv['packages'][ref]
    for ref in ('RN7101','RN7102'):
        inv['packages'][ref]={'owner':places[ref]['owner'],'pins':places[ref]['pins'],'units':[1,2,3,4]}
    inv['net_endpoints']={}
    for ref,p in inv['packages'].items():
        for pin,net in p['pins'].items():
            if net is not None:inv['net_endpoints'].setdefault(net,[]).append({'ref':ref,'pin':pin,'owner':p['owner']})
    mapped=mapping(graph,paths,inv)
    prior_map={r['to']:r for r in read('stage14/rebudget-report.json')['resistance_endpoint_mapping']}
    for row in mapped:
        if row['to'] in prior_map:
            clean=lambda r: {k:v for k,v in r.items() if k!='edge_terms'}
            need(clean(row)==clean(prior_map[row['to']]), 'old resistance domains/path changed')
            need([{k:v for k,v in t.items() if k!='endpoint_walk_use_count'} for t in row['edge_terms']]==[{k:v for k,v in t.items() if k!='endpoint_walk_use_count'} for t in prior_map[row['to']]['edge_terms']], 'old resistance edges changed')
    feed=copy.deepcopy(old_feed)
    for ref,core in [('RN7101',True),('RN7102',False)]:
        feed['power_endpoint_comparison'].append({'to':ref+':9','net':'AGND','source_boundary':graph['upstream_power_boundaries']['AGND'],'candidate_core_strap_replaces_K_PWR_branch':core})
    old_electrical.feed_alternative(feed,support,graph,paths)
    # Existing conditional_budgets apply unchanged circuit sections only; ratio/load replacement gets its own report.
    paths['conditional_budgets']['replacement_scope']='Historical reference/quiescent/harness/contact subtotals retained. Six-resistor loading/ratios replaced by Stage15 electrical-report; not a complete current or accuracy bound.'
    summary={'counts':{'nodes':len(graph['nodes']),'edges':len(graph['edges']),'connected_source_pads':len(source),'NC_source_pads':len(nc),'power_return_endpoints':len(mapped),'preserved_power_return_endpoints':106,'new_shield_return_endpoints':2,'crossing_paths':len(paths['signal_net_paths']),'local_paths':len(paths['local_endpoint_paths']),'strap_core_endpoints':len(feed['lowR_complete_endpoint_paths']),'strap_front_endpoints':len(feed['lowR_unmodified_front_endpoint_targets'])},'endpoint_aliases':aliases,'incident_edge_changes':changes,'path_deltas':deltas,'resistance_endpoint_mapping':mapped,'resistance_accounting':read('stage14/rebudget-report.json')['resistance_accounting'],'unselected_strap_endpoint_paths':feed['lowR_complete_endpoint_paths'],'unselected_strap_front_targets':feed['lowR_unmodified_front_endpoint_targets'],'source_inventory_scope':'86 whole physical packages;291 pads;120 unit records including two unused resistor elements. Six existing resistor functions mapped, not deleted from functional transfer.','actual_complete_resistance_ohm':None,'complete_error_bound_V':None,'allocation_scope':'All lengths are allocation proxies, not obstacle-aware routed copper. No equal return sharing, current cancellation or qualification credit. Added shield returns carry unknown AC current; no resistor DC load invented.','frozen_calibration':'Stage13 historical result preserved, no knob fitting; new network algebra is separate.'}
    for obj in (graph,paths,summary):obj.update(status='STAGE15 CANDIDATE SOURCE ONLY; ACCEPTANCE OPEN',hardware_acceptance=False,native='NOT RUN',CAD='NOT RUN',simulation='NOT RUN',physical='NOT RUN',actual_copper_routing='NOT RUN')
    return graph,paths,summary


def build():
    files=[OUT/'package-report.json',OUT.parent/'stage14/interfaces-report.json',OUT.parent/'stage14/paths-report.json',OUT.parent/'stage10/inventory-report.json',OUT.parent/'stage11/support-report.json',OUT.parent/'stage11/electrical-report.json']
    values=[json.loads(p.read_text()) for p in files]
    for v in values:common.bindings(v)
    results=analyze(*values)
    files += [Path(__file__),Path(__file__).with_name('test_stage15_paths.py'),Path(interface.__file__),Path(budget.__file__),Path(old_electrical.__file__),OUT.parent/'stage14/rebudget-report.json']
    for r in results:r['source_sha256']={str(p.relative_to(ROOT)):common.digest(p) for p in files}
    return results


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    for name,r in zip(('interfaces','paths','rebudget'),build()):
        text=json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+'\n';dest=OUT/(name+'-report.json')
        if args.check:need(dest.read_text()==text,'stale Stage15 '+name)
        else:dest.write_text(text)
    print('PASS Stage15 complete migrated graph and108 returns; electrical acceptance OPEN')
if __name__=='__main__':main()
