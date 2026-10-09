import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jr-u7509-on-ground/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');dump=json.loads(source.read_text())
assert dump['board_sha256']=='05a8d4beff64f5dee1356f679eb7d24842996d7a6b125047b8f48467e41bac26'
events=[];start=time.monotonic()
results,removed=route(dump,['-12V'],res=.025,clearance=.25,rail_width=.25,
 allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,
 fill_guards={'-12V':'In3.Cu'},window_mm=6,diagnostics=events,**neck_kwargs('osc-jack-right'))
rows,links=copper_rows(results,'osc-jack-right','issue189-existing-rail-escape')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE', 'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jr153-rail-finer-probe.json').write_text(json.dumps(out,indent=2)+'\n')
print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
