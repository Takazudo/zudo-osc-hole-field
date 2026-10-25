#!/usr/bin/env python3
"""Authenticate saved inputs and validate finite local straight access templates."""
import argparse
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import zipfile
import shapely
from exact_access import Geometry, terminal_clearance_upper_bound

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent
METHOD='29140d4e19d526eed3a02a73c33f8ce4219c78f0'
INPUTS={'K1402':('1420','9232ff3212f41604a72b3f49a9d3a8b10884186884bf50f367a57693a7e082a5'),
        'two-A':('1438','ed8de7933f40369ecefb3ea28f382662923b414298e0cdb72ed5e32578e64e3f')}
sha=lambda b:hashlib.sha256(b).hexdigest()
DIRECTIONS=tuple((x/math.hypot(x,y),y/math.hypot(x,y)) for x,y in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1),(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)))
LENGTHS=(.25,.5,.75,1.,1.25,1.5,2.)


def examine(geometry,pad,width,budget,bounds):
    net=pad['net'];layer=pad['layers'][0]
    assert len(pad['layers'])==1 and not pad['drill']
    polygon=shapely.Polygon([(x/1e6,y/1e6) for x,y in pad['poly']]);x0,y0,x1,y1=polygon.bounds
    # Deterministic local .1mm sampling plus actual pad center. No raster/search call.
    starts={(round(i*.1,9),round(j*.1,9)) for i in range(math.ceil(x0/.1),math.floor(x1/.1)+1) for j in range(math.ceil(y0/.1),math.floor(y1/.1)+1)}
    starts.add(tuple(v/1e6 for v in pad['xy']))
    starts=sorted(s for s in starts if geometry.contact(pad['uuid'],s,net,layer)['pass'])
    legal_starts=[];best=None
    for s in starts:
        result=geometry.segment(s,s,net,layer,width,budget['clearance_mm'])
        if result['pass']:legal_starts.append(s)
        margin=min(v for v in result['checked_margins_mm'].values() if v is not None)
        if best is None or margin>best['minimum_checked_margin_mm']:best={'xy_mm':s,'minimum_checked_margin_mm':margin,'sweep':result}
    total=0;segments=0;vias=0;witnesses=[];segment_witnesses=[]
    cache={}
    for s in legal_starts:
        for dx,dy in DIRECTIONS:
            for length in LENGTHS:
                end=(round(s[0]+dx*length,9),round(s[1]+dy*length,9))
                if not(bounds[0]<=end[0]<=bounds[2] and bounds[1]<=end[1]<=bounds[3]):continue
                if polygon.distance(shapely.Point(end))<width/2:continue
                total+=1
                result=geometry.terminal_edge(pad['uuid'],s,end,net,layer,width,budget['clearance_mm'])
                if not result['pass']:continue
                segments+=1
                if len(segment_witnesses)<3:segment_witnesses.append({'start_mm':s,'end_mm':end,'validation':result})
                if end not in cache:cache[end]=geometry.via(end,net,budget['via_diameter_mm'],budget['via_drill_mm'],budget['clearance_mm'])
                via=cache[end]
                if via['pass']:
                    vias+=1
                    if len(witnesses)<3:witnesses.append({'start_mm':s,'end_mm':end,'edge':result,'via':via})
    return {'anchor':pad['ref']+'.'+pad['pad'],'uuid':pad['uuid'],'layer':layer,'width_mm':width,
            'interior_start_centers':len(starts),'foreign_clear_full_width_start_caps':len(legal_starts),'best_start_cap':best,
            'straight_templates_checked':total,'valid_swept_terminal_edges':segments,'valid_edges_ending_in_new_through_via':vias,
            'whole_pad_start_certificate':terminal_clearance_upper_bound(geometry,pad['uuid'],width,budget['clearance_mm']) if not legal_starts else {'status':'NOT NEEDED: valid full-width start caps exist'},
            'edge_witnesses':segment_witnesses,'edge_and_via_witnesses':witnesses,
            'verdict':'LOCAL_GEOMETRIC_ACCESS_WITNESS_ONLY' if vias else 'NO_LOCAL_EDGE_PLUS_VIA_CERTIFICATE_IN_THIS_FINITE_TEMPLATE_SET',
            'scope':'Sufficient center-inside contact; full-width capsules, original foreign obstacles and same rules. Finite local templates only, not exhaustive off-grid/curved escape or whole-route proof.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--k',type=Path,required=True);p.add_argument('--two-a',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    versions={n:version(n) for n in ('numpy','scipy','shapely')}
    assert versions=={'numpy':'2.2.6','scipy':'1.15.3','shapely':'2.1.2'}
    spec=json.loads((PILOT/'matching-spec.json').read_text());manifest=json.loads((PILOT/'matched-demands.json').read_text());domain=manifest['domains']['O1'];budget=spec['budget']
    report={'status':'SOURCE-ONLY SUFFICIENT LOCAL GEOMETRY VALIDATION; NO NATIVE ADMISSION, SEARCH, COPPER OR ACCEPTANCE','method_input':METHOD,'versions':versions,
            'tool_sha256':{f:sha((HERE/f).read_bytes()) for f in ('exact_access.py','check_saved.py')},
            'spec_sha256':sha((PILOT/'matching-spec.json').read_bytes()),'manifest_sha256':sha((PILOT/'matched-demands.json').read_bytes()),
            'template_contract':{'start_grid_mm':.1,'include_original_pad_center':True,'directions':DIRECTIONS,'lengths_mm':LENGTHS,'common_bounds_mm':domain['common_bounds_mm'],'budget_changed':False,'raster_or_router_modified':False,'trace_or_via_width_changed':False,'clearance_changed':False},'boards':{}}
    geometries={}
    for board,path in [('K1402',a.k),('two-A',a.two_a)]:
        tag,expected=INPUTS[board];assert sha(path.read_bytes())==expected
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            lock=json.loads(z.read('fixture/fixture-lock.json'));dump=json.loads(z.read('fixture/before/dump.json'))
            assert lock['source_tree_sha']==METHOD and lock['board']==board
            assert lock['spec_sha256']==report['spec_sha256'] and lock['matched_demands_sha256']==report['manifest_sha256']
            assert sha(z.read('fixture/before/dump.json'))==lock['artifact']['dump_sha256']
            assert sha(z.read('fixture/before/osc-core.kicad_pcb'))==lock['artifact']['board_sha256']==dump['board_sha256']
        geometry=Geometry(dump);geometries[board]=geometry;rows=[]
        for kind in spec['route_policy']['target_order']:
            target=domain['targets'][kind];net=target['net_token'];width=budget['rail_width_mm'] if net in spec['route_policy']['rail_nets'] else budget['signal_width_mm']
            assert all(geometry.pads[p['uuid']]==p for p in target['anchor_records'])
            endpoints=[examine(geometry,p,width,budget,domain['common_bounds_mm']) for p in target['anchor_records']]
            rows.append({'kind':kind,'net':net,'endpoints':endpoints})
            print(board,kind,[(e['anchor'],e['foreign_clear_full_width_start_caps'],e['valid_swept_terminal_edges'],e['valid_edges_ending_in_new_through_via']) for e in endpoints],flush=True)
        report['boards'][board]={'artifact_sha256':expected,'board_sha256':lock['artifact']['board_sha256'],'dump_sha256':lock['artifact']['dump_sha256'],'source_objects':{'pads':len(dump['pads']),'tracks':len(dump['tracks']),'vias':len(dump['vias'])},'demands':rows}
    comparisons=[]
    for source,other in [('K1402','two-A'),('two-A','K1402')]:
        for demand in report['boards'][source]['demands']:
            for endpoint in demand['endpoints']:
                for witness in endpoint['edge_and_via_witnesses']:
                    start,end=witness['start_mm'],witness['end_mm'];g=geometries[other]
                    edge=g.terminal_edge(endpoint['uuid'],start,end,demand['net'],endpoint['layer'],endpoint['width_mm'],budget['clearance_mm'])
                    via=g.via(end,demand['net'],budget['via_diameter_mm'],budget['via_drill_mm'],budget['clearance_mm'])
                    comparisons.append({'witness_board':source,'other_board':other,'anchor':endpoint['anchor'],'start_mm':start,'end_mm':end,'other_edge':edge,'other_via':via,'same_local_geometry_passes_both':edge['pass'] and via['pass']})
    report['cross_board_same_geometry_checks']=comparisons
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
