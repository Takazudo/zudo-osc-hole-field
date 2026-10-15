"""A01 source composition and immutable predecessor guard; no CAD execution."""
import argparse
from collections import Counter
import hashlib
import json
import math
import candidate as source_geometry
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation/stage10'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def bindings(report):
    need(bool(report.get('source_sha256')),'missing source bindings')
    for path,digest in report['source_sha256'].items():
        need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'stale source '+path)
def preserve(scope):
    need(scope['baseline_commit']=='ce779ce6ba5709fd26493f0bb71e22d8f3675969','wrong Stage9 baseline')
    need(len(scope['preserved_prior_source_sha256'])==212,'incomplete predecessor guard')
    for path,digest in scope['preserved_prior_source_sha256'].items():
        need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'prior candidate changed '+path)
def population(inventory,placements,board_faces):
    source=inventory['packages']
    need(len(source)==len(placements)==90 and set(source)==set(placements),'complete90 package population')
    for ref,p in source.items():
        q=placements[ref]
        need(q['pins']==p['pins'],'source pin/net/NC changed '+ref)
        need(Counter(q['units'])==Counter(p['units']),'source physical units changed '+ref)
        need(q['owner']==p['owner'],'source owner changed '+ref)
        expected_board='A01-fixed' if p['owner']=='front-jack' and p['attributes']['PanelUid'] else {'front-jack':'A01-jack','front-control':'A01-control','rear-core':'A01-core'}[p['owner']]
        need(q['board']==expected_board,'unowned physical board '+ref)
        need(q['side']in('panel','rear'),'unknown board face '+ref)
        path='footprints/kicad/zudo-osc-hole-field.pretty/'+p['footprint'].split(':')[1]+'.kicad_mod'
        need(q['source']==path,'footprint source changed '+ref)
        expected={}
        for pin,points in source_geometry.footprint_pads(path).items():
            expected[pin]=[]
            for x,y in points:
                if q['side']=='rear':x=-x
                for _ in range(q['quarter_turn']%4):x,y=-y,x
                expected[pin].append([x+q['origin_mm'][0],y+q['origin_mm'][1],board_faces[q['board']][q['side']]])
        need(q['pads_xyz_mm']==expected,'actual footprint/board-plane pad transform changed '+ref)
        need(set(q['pads_xyz_mm'])==set(p['pins']),'missing actual physical pad '+ref)
        need(all(pts and all(len(xyz)==3 and all(math.isfinite(v)for v in xyz)for xyz in pts)for pts in q['pads_xyz_mm'].values()),'invalid actual pad geometry '+ref)
    for row in inventory['fixed_controls']:
        q=placements[row['ref']]
        need(q['origin_mm']==[row['x_mm'],row['y_mm']] and q['quarter_turn']==row['rot_deg']//90,'fixed centre/rotation changed '+row['ref'])
    for pair in inventory['bypass_associations']:
        need(placements[pair['bypass_ref']]['board']==placements[pair['target_ref']]['board'],'bypass ownership split')
    return inventory['counts']
def transport(inventory,graph,electrical,placements):
    digest=hashlib.sha256((json.dumps(graph,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
    need(electrical['interface_object_sha256']==digest,'electrical graph binding changed')
    expected={ref+':'+pin:net for ref,p in inventory['packages'].items()for pin,net in p['pins'].items()}
    connected={k for k,v in expected.items()if v is not None};nc=set(expected)-connected
    for key in connected:
        ref,pin=key.split(':');node=graph['nodes'][key]
        need(node['net']==expected[key] and node['pad_xyz_mm']==placements[ref]['pads_xyz_mm'][pin][0],'source graph node detached from actual pad/net')
    need(len(graph['source_endpoints'])==269 and set(graph['source_endpoints'])==connected,'connected endpoint omission')
    need(len(graph['NC_source_endpoints'])==16 and set(graph['NC_source_endpoints'])==nc==set(electrical['NC_source_endpoints']),'NC endpoint omission')
    need(electrical['counts']['physical_wires']==34 and len(graph['wires'])==20 and len(graph['terminal_wires'])==14,'physical wire inventory')
    local=electrical['local_endpoint_paths'];power=electrical['power_and_return_endpoint_paths'];signals=electrical['signal_net_paths']
    need(len(local)==269 and {r['to']for r in local}==connected,'local endpoint coverage')
    power_targets={k for k,v in expected.items()if v in ('+12V','-12V','+5V','AGND')}
    need(len(power)==len(power_targets)==106 and {r['to']for r in power}==power_targets,'power/return endpoint coverage')
    drivers={'REF5':'U7104:1','REFN5':'U7104:7','IN_BUFFER':'U7106:1','OFFSET_BUFFER':'U7106:7','SUM_NEG':'U7105:8','IN_REMOTE':'R7113:2','Cc045d2_W':'RV1307:2','C38cac0_W':'RV1308:2'}
    pairs={(driver,key)for name,driver in drivers.items()for key,net in expected.items()if net=='/A01/'+name and key!=driver}
    need(len(signals)==len(pairs)==21 and {(r['from'],r['to'])for r in signals}==pairs,'crossing signal endpoint coverage')
    for row in local+power+signals:
        need(row['net']==expected[row['to']],'path target net changed')
        current=row.get('from',row.get('source_boundary'));total=wire=gh=din=0
        for index in row['edge_indices']:
            edge=graph['edges'][index];need(edge['net']==row['net'],'cross-net graph edge')
            need(current in (edge['from'],edge['to']),'disconnected graph walk')
            current=edge['to']if current==edge['from']else edge['from'];total+=edge['allocated_developed_mm'];wire+=edge['wire_cut_max_mm'];gh+=edge['mated_GH_contacts'];din+=edge['kind']=='DIN_mated_pair'
        need(current==row['to'],'wrong graph destination')
        need(math.isclose(wire,row.get('harness_wire_cut_max_mm',row.get('all_wire_cut_max_mm',row.get('wire_cut_max_mm'))),abs_tol=1e-8),'wire metric sum changed')
        if 'GH_mated_contacts'in row:need(gh==row['GH_mated_contacts'] and din==row['DIN_mated_contacts'],'path contact count changed')
        need(math.isclose(total,row.get('complete_net_pad_path_allocation_mm',row.get('allocated_developed_mm')),abs_tol=1e-8),'path allocation sum changed')
    return {'connected_source_endpoints':269,'NC_endpoints':16,'crossing_signal_paths':21,'power_return_endpoint_paths':106,'physical_wires':34,'GH_harness_wires':20,'permanent_terminal_wires':14}
def build():
    paths={k:OUT/(k+'.json')for k in ('scope','inventory-report','mechanical-report','interfaces-report','electrical-report')}
    r={k:json.loads(p.read_text())for k,p in paths.items()}
    preserve(r['scope'])
    for k in ('inventory-report','mechanical-report','interfaces-report','electrical-report'):bindings(r[k])
    counts=population(r['inventory-report'],r['mechanical-report']['placements'],r['mechanical-report']['board_pad_faces_mm'])
    need(r['mechanical-report']['physical_acceptance']is False,'unreviewed physical acceptance')
    need(r['electrical-report']['hardware_acceptance']is False,'unreviewed electrical acceptance')
    transport_counts=transport(r['inventory-report'],r['interfaces-report'],r['electrical-report'],r['mechanical-report']['placements'])
    reconciliation=r['inventory-report']['prior_hosting_reconciliation']['counts']
    need(reconciliation=={'prior_nonOSC_K':2572,'new_candidate_K_assignments':29,'remaining_nonOSC_K':2543,'POWER_unknown':13},'K ownership reconciliation')
    result={'status':'ONE A01 SOURCE DEMONSTRATOR; CONDITIONAL AND NOT ADOPTED','counts':counts,'transport_counts':transport_counts,'K_reconciliation':reconciliation,'whole_instrument_host_overlay':r['inventory-report']['whole_instrument_host_overlay'],'predecessor_files_preserved':212,'independent_support_boundary':'A01 owns its outlines/support/insulation/service proposal; no X1 carrier is credited as qualified infrastructure. Exact assembled fit and strength remain open.','electrical_boundary':'Read electrical report for per-net contact/harness/full-path terms and power/return failures. Source ownership or short paths cannot close current, impedance, protection, stability or physical acceptance.','metadata_findings':r['inventory-report']['metadata_findings'],'unselected_MPN_refs':r['inventory-report']['unselected_MPN_refs'],'stop_boundary':'Stop after A01; no replication, POWER hosting or X1 reopening.','architecture_adopted':False,'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
    sources=[*paths.values(),Path(__file__),Path(__file__).with_name('test_stage10_assessment.py')]
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources}
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();body=json.dumps(build(),sort_keys=True,indent=2)+'\n';dest=OUT/'assessment-report.json'
    if args.check:need(dest.read_text()==body,'stale Stage10 assessment')
    else:dest.write_text(body)
    print('A01 composition90packages/29newK;212priorfiles unchanged; hardware NOT ACCEPTED')
if __name__=='__main__':main()
