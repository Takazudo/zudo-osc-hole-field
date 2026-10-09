import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2105-cut/osc-jack-left-grid-189-jl126-u2105-bounded-cut-cut/dump.json');d=json.loads(p.read_text())
net='X2AAA855333149167D66B';victim='XA914644BA42DD5692426';out=[]
for bounds in ([201.7425,128.755,213.7425,140.755],[186.8,87.1,211.5,136.9]):
 events=[];start=time.monotonic()
 results,removed=route(d,[net,victim],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,links=copper_rows(results,'osc-jack-left','issue189-u2105-goal-frame');assert not removed
 out.append({'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}})
 print(bounds,'paths',[(r['net'],bool(r['path'])) for r in results],flush=True)
 Path('.circuit-cache/issue189-jl-u2105-frame-probe.json').write_text(json.dumps({'input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'status':'RASTER ONLY; NATIVE NOT RUN','comparisons':out},indent=2)+'\n')
