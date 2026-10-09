import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
source=Path('.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');dump=json.loads(source.read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()=='8d593d00963d16d7553fe574eaa519c4d6fd3bf6f166b7371b5ad6a5fe08feb2'
nets=["XED7C19D453619667580D"];events=[];start=time.monotonic()
results,removed=route(dump,nets,res=.1,clearance=.2,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=[l for l in SIGNAL_LAYERS if l != "In3.Cu"],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},
 fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=100000,rrr_rounds=1,rrr_max_rip=4,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-bounded-rrr')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Only R2316.2 signal net; In3 excluded after native return split; one RRR round,max4victims,0.1mm raster,100000 expansions/window,6mm window; full native gates mandatory','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'selected_nets':nets,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jl-first-no-in3-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
