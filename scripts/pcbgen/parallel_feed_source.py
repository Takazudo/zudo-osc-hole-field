"""Source-defined parallel transfers for real shared B-to-F +12 branches.

Native electrical membership is retained separately from synthetic planner
requests. Existing copper is never retired here. Run whole-board planning
through heavy-guard; subsequent pinned native checks remain mandatory.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import shapely
from shapely.geometry import Point
from scripts.pcbgen.propose_rail_transfers import geometry,propose


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(data):
    selected=[i for i in data['items'] if i['net']=='+12V']
    by_layer={layer:[(i,geometry(i['copper'][layer])) for i in selected if layer in i['copper']]
              for layer in ('F.Cu','In1.Cu','In2.Cu','B.Cu')}
    zone_shapes={layer:[geometry(z['contours']) for z in data['zones']
                        if not z['keepout'] and z['net']=='+12V' and z['layer']==layer] for layer in by_layer}
    body=shapely.union_all([g for _,g in by_layer['B.Cu']]+zone_shapes['B.Cu'])
    holes={h['uuid']:h for h in data['holes'] if h['net']=='+12V' and h['plated']}
    rows=[]
    for island in shapely.get_parts(body):
        owned=[i for i,g in by_layer['B.Cu'] if island.intersects(g)]
        pads=[i for i in owned if 'ref' in i and not i['ref'].startswith('TP990')]
        bridges=[i for i in owned if i['uuid'] in holes]
        if len(pads)<2 or len(bridges)!=1:continue
        via=bridges[0];hole=holes[via['uuid']]
        if hole['size_mm']!=[.3,.3]:continue
        # The cylindrical lower bound needs all current to traverse every
        # dielectric gap: no intermediate foil may provide another +12 exit.
        isolated={}
        for layer in ('In1.Cu','In2.Cu'):
            ring=geometry(via['copper'][layer])
            others=[i['uuid'] for i,g in by_layer[layer] if i['uuid']!=via['uuid'] and ring.intersects(g)]
            zones=[j for j,g in enumerate(zone_shapes[layer]) if ring.intersects(g)]
            isolated[layer]={'other_contacting_items':others,'contacting_zones':zones}
        no_inner_exit=all(not r['other_contacting_items'] and not r['contacting_zones'] for r in isolated.values())
        rows.append({'id':'parallel-shared-'+min(i['uuid'] for i in owned),'net':'+12V','layer':'B.Cu',
            'pads':[{'ref':p['ref'],'pad':p['pad'],'uuid':p['uuid'],'xy_mm':p['xy_mm'],'layers':['B.Cu']} for p in pads],
            'members':sorted(i['uuid'] for i in owned),'existing_via_uuid':via['uuid'],
            'existing_via_xy_mm':hole['xy_mm'],'intermediate_foil_exit_audit':isolated,
            'sole_full_height_transfer_proved':no_inner_exit,'component_bounds_mm':list(island.bounds)})
    return sorted(rows,key=lambda row:row['id'])


def run(source,output,extra_vias):
    if extra_vias<1:raise ValueError('at least one additional finite transfer required')
    raw=source.read_bytes();data=json.loads(raw);before=digest(source)
    rows=inventory(data);requests=[]
    for row in rows:
        for index in range(extra_vias):
            requests.append({'id':row['id']+'-'+str(index+1),'net':'+12V','fed':False,
                'pads':row['pads'],'members':row['members']})
    request=copy.deepcopy(data);request['clusters']=requests
    request['synthetic_request_scope']='Already connected local branches requesting extra parallel conductors; fed=false is planner control, not a native connectivity assertion.'
    planner_input=output.with_name(output.stem+'-planner-input.json')
    planner_output=output.with_name(output.stem+'-planner-output.json')
    planner_input.write_text(json.dumps(request,separators=(',',':'))+'\n')
    propose(planner_input,planner_output)
    planned=json.loads(planner_output.read_text())
    if any(r['via_xy_mm'] is None for r in planned['added']):
        raise ValueError('parallel request did not produce an actual plated transfer')
    rho=1.7241e-5*(1+.003947*50)
    foil=sum(float(r['copper_thickness_mm']) for r in data['stackup'] if 'copper_thickness_mm' in r)
    lower=rho*(1.6-foil)/(math.pi*(.175**2-.15**2))
    result={**planned,'status':'UNSELECTED additional parallel-feed source; native/electrical gates NOT RUN',
        'original_native_export_sha256':before,'planner_request_sha256':digest(planner_input),
        'source_script_sha256':digest(__file__),'planner_script_sha256':digest('scripts/pcbgen/propose_rail_transfers.py'),
        'native_existing_feed_status':'Connected before this proposal; added conductors reduce paid shared local access',
        'requested_additional_vias_per_shared_branch':extra_vias,'shared_branches':rows,
        'nominal_sole_barrel_dielectric_lower_ohm':lower,
        'lower_bound_scope':'Only branches with sole_full_height_transfer_proved. All intermediate foil escape connections checked. The shared local branch energy is proportional to (I_IC + I_bypass)^2, not separately to two full source currents. Classification against the common ceiling is explicit source scope, not inferred here.',
        'prior_copper_retirements':[]}
    if digest(source)!=before:raise ValueError('native source changed during parallel planning')
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('Shared local branches',len(rows),'full-height cut proofs',sum(r['sole_full_height_transfer_proved'] for r in rows),
          'additional transfers',len(planned['added']),'unresolved',len(planned['unresolved']),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--extra-vias',type=int,default=2);args=parser.parse_args();run(args.source,args.output,args.extra_vias)
