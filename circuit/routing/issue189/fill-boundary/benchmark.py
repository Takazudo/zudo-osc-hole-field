import hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import grid_router as new
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source='3f7fb6895f4a7d2d7590ef40d3d66486025480a8'
p=Path('.circuit-cache/old-router/grid_router.py');p.parent.mkdir(parents=True,exist_ok=True)
p.write_bytes(subprocess.check_output(['git','show',source+':scripts/pcbgen/grid_router.py']))
p.with_name('grid_astar.c').write_bytes(subprocess.check_output(['git','show',source+':scripts/pcbgen/grid_astar.c']))
spec=importlib.util.spec_from_file_location('old_grid_router',p);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
p=Path('.circuit-cache/issue189-downloaded/jr-two-after-protected/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text())
assert d['board_sha256']=='3d9940791131e31d22ea65e4457ccb77d5250d629eaa2b5d3c6b03024ac3405c'
saved=json.loads(Path('circuit/routing/issue189/jr141-remaining-short/result.json').read_text())
assert old.native_astar() is not None and new.native_astar() is not None
t=next(t for t in saved['transactions'] if t['net']=='X6522EE2C05A9BE92D3C2');out=[]
for name,module in [('before',old),('after',new)]:
 events=[];start=time.monotonic()
 results,removed=module.route(d,[t['net']],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=t['bounds_mm'],diagnostics=events,**neck_kwargs('osc-jack-right'))
 rows,_=module.copper_rows(results,'osc-jack-right','issue189-jr141-remaining-short');assert not removed
 if name=='before':assert rows==t['proposal']['copper'],'control must reproduce saved copper exactly'
 out.append({'case':name,'elapsed_seconds':time.monotonic()-start,'objects':len(rows),'diagnostics':events,'copper':rows})
 print(name,len(rows),flush=True)
Path('circuit/routing/issue189/fill-boundary/benchmark.json').write_text(json.dumps({'status':'RASTER ONLY; no new native validation','source_before':source,'input_board_sha256':d['board_sha256'],'input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'net':t['net'],'bounds_mm':t['bounds_mm'],'cases':out},indent=2)+'\n')
