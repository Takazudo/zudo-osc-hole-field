import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
source=Path('.circuit-cache/issue189-downloaded/jr-return-restored/osc-jack-right-grid-189-jr-return-restored-fresh/dump.json');dump=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='9b23f2e809ec92ffacd2727c69677f73de248a1919c4a4310ad1ab8f68845ed0'
nets=signal_chunk(dump,None);events=[];start=time.monotonic()
results,removed=route(dump,nets,res=.1,clearance=.2,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=[layer for layer in SIGNAL_LAYERS if layer != "In3.Cu"],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},
 fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=100000,rrr_rounds=1,rrr_max_rip=4,diagnostics=events,**neck_kwargs('osc-jack-right'))
rows,links=copper_rows(results,'osc-jack-right','issue189-bounded-rrr')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'All remaining signal nets; one RRR round,max4victims,0.1mm raster,100000 expansions/window,6mm window; full native gates mandatory; In3 excluded from signal search; input native-eligible155 pilot, canonical adoption pending','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'selected_nets':nets,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jr-next-corridors.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
