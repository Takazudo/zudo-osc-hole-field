"""Reserve a ground link and reconnect exact retained cut endpoints on native geometry."""
import json,hashlib,time,sys,copy,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jl-c2248-ground');p=root/'osc-jack-left-grid-189-jl120-c2248-2-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-left-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jl120-c2248-2-ground-cut/plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert joined==max(d['islands']['AGND'],key=len) and set(original)<set(joined)
net='X3A5D9B9F1077037AEA2A';assert net not in before['islands'] and len(d['islands'][net])==2
cuts=[t for t in before['tracks'] if t['uuid'] in plan['stage']['repair_source_uuids']];ends={tuple(t[e]) for t in cuts for e in ['a','b']};anchors=[]
for t in d['tracks']:
 if t['net']!=net:continue
 for e in ['a','b']:
  if tuple(t[e]) in ends:anchors.append({'retained_uuid':t['uuid'],'xy':t[e],'layer':t['layer'],'cut_component':next(i for i,g in enumerate(d['islands'][net]) if t['uuid'] in g)})
assert {a['cut_component'] for a in anchors}=={0,1}
search=copy.deepcopy(d)
out=[];start=time.monotonic()
for resolution in [.025,.0125]:
    current=copy.deepcopy(search);current['islands']['AGND']=[original];events=[]
    kwargs=dict(allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=resolution,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
    ground,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'},**kwargs);assert not removed
    rows,_=copper_rows(ground,'osc-jack-left',f'jl-c2248-fanout-ground-{resolution}')
    for row in rows:
        obj={'uuid':row['uuid'],'net':row['net']}
        if row['kind']=='via':obj.update(xy=row['at_nm'],diameter=row['diameter_nm'],drill=row['drill_nm'],layers=row['layers']);current['vias'].append(obj)
        else:obj.update(a=row['start_nm'],b=row['end_nm'],width=row['width_nm'],layer=row['layer']);current['tracks'].append(obj)
    signal,removed=route(current,[net],**kwargs);assert not removed
    signal_rows,_=copper_rows(signal,'osc-jack-left',f'jl-c2248-fanout-signal-{resolution}');rows.extend(signal_rows)
    complete=bool(rows) and bool(signal_rows) and all(r['path'] for r in ground+signal)
    out.append({'resolution':resolution,'complete_raster_transaction':complete,'results':ground+signal,'diagnostics':events,'proposal':{'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows}});print('resolution',resolution,'complete',complete,'objects',len(rows),'vias',sum(r['kind']=='via' for r in rows),flush=True)
    if complete:break
here=Path('circuit/routing/issue189/jl-c2248-ground-fanout');(here/'result.json').write_text(json.dumps({'status':'RASTER ONLY; EXPLICIT AGND FANOUT TO EXISTING In1 PLANE; NATIVE ORIGINAL BASELINE REMAINS AUTHORITATIVE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'exact_endpoint_anchors':anchors,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
if out[-1]['complete_raster_transaction']:(here/'proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
