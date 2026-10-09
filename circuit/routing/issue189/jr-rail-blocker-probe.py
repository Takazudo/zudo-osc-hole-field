import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jr-dump.json');dump=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='b53fc851992843175db2669ec12540e1e6e27b4eda4c28a5834ce349c11f377b'
victims=['X6B33772BC30314E16C07','XCC3D11ADA365B386C3F5','XCE107A8A443162AB8037'];events=[];start=time.monotonic()
results,removed=route(dump,['-12V'],res=.05,clearance=.25,rail_width=.4,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,
 fill_guards={'-12V':'In3.Cu'},window_mm=6,rrr_rounds=1,rrr_max_rip=2,rip_only=victims,diagnostics=events,**neck_kwargs('osc-jack-right'))
rows,links=copper_rows(results,'osc-jack-right','issue189-rail-local-blockers')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'U7106.11; only three signal nets with source copper within2mm; max2victims/one round','permitted_victims':victims,'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jr-rail-blocker-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
