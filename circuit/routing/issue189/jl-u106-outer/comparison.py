import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u106-cut/osc-jack-left-grid-189-local-base/dump.json');d=json.loads(p.read_text());net='XE696508C2D9B11400F0C';bounds=[197.226065,182.696066,212.313933,197.993934];out=[];start=time.monotonic()
for layers in (['F.Cu','In3.Cu','B.Cu'],['F.Cu','In2.Cu','B.Cu'],['F.Cu','B.Cu']):
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-u106-layer-choice');assert not removed
 out.append({'allowed_layers':layers,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(layers,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-u106-layers.json').write_text(json.dumps({'status':'ADDITIVE RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
