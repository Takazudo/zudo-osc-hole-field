import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-coupled/osc-jack-left-grid-189-jl-coupled/dump.json');dump=json.loads(source.read_text())
events=[];start=time.monotonic()
results,removed=route(dump,['-12V'],res=.05,clearance=.25,rail_width=.4,
 allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,
 fill_guards={'-12V':'In3.Cu'},window_mm=6,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-rail-component-link')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE', 'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jl-rail-link-probe.json').write_text(json.dumps(out,indent=2)+'\n')
print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
