"""Reserve a ground link and reconnect exact retained cut endpoints on native geometry."""
import json,hashlib,time,sys,copy,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jl-u2205-ground');p=root/'osc-jack-left-grid-189-jl119-u2205-9-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-left-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jl119-u2205-9-ground-cut/plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert joined==max(d['islands']['AGND'],key=len) and set(original)<set(joined)
nets=['X77D98D4570DBC8F06DA7','X9C4932E28DB349FED377'];assert all(n not in before['islands'] and len(d['islands'][n])==2 for n in nets)
anchors=[]
search=copy.deepcopy(d)
out=[];start=time.monotonic()
for resolution in [.025,.0125]:
    current=copy.deepcopy(search);current['islands']['AGND']=[original];events=[]
    kwargs=dict(allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=resolution,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
    ground,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'},**kwargs);assert not removed
    rows,_=copper_rows(ground,'osc-jack-left',f'jl-u2205-fanout-ground-{resolution}')
    for row in rows:
        obj={'uuid':row['uuid'],'net':row['net']}
        if row['kind']=='via':obj.update(xy=row['at_nm'],diameter=row['diameter_nm'],drill=row['drill_nm'],layers=row['layers']);current['vias'].append(obj)
        else:obj.update(a=row['start_nm'],b=row['end_nm'],width=row['width_nm'],layer=row['layer']);current['tracks'].append(obj)
    signal,removed=route(current,nets,**kwargs);assert not removed
    signal_rows,_=copper_rows(signal,'osc-jack-left',f'jl-u2205-fanout-signal-{resolution}');rows.extend(signal_rows)
    complete=bool(ground) and {r['net'] for r in signal if r['path']}==set(nets) and all(r['path'] for r in ground+signal)
    out.append({'resolution':resolution,'complete_raster_transaction':complete,'results':ground+signal,'diagnostics':events,'proposal':{'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows}});print('resolution',resolution,'complete',complete,'objects',len(rows),'vias',sum(r['kind']=='via' for r in rows),flush=True)
    if complete:break
here=Path('circuit/routing/issue189/jl-u2205-ground-fanout');(here/'result.json').write_text(json.dumps({'status':'RASTER ONLY; EXPLICIT AGND FANOUT TO EXISTING In1 PLANE; NATIVE ORIGINAL BASELINE REMAINS AUTHORITATIVE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'exact_endpoint_anchors':anchors,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
if out[-1]['complete_raster_transaction']:(here/'proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
