import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
source=Path('.circuit-cache/issue189-downloaded/jl-leaf-adopt/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');dump=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='1f6fbab0e4f5771924a4f51099eecad31aa3f3a8ea4009d5806a6b63c57aee1b'
nets=signal_chunk(dump,None);events=[];start=time.monotonic()
results,removed=route(dump,nets,res=.075,clearance=.2,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},
 fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-additive075')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'All remaining signal nets; additive only, no rip-up,0.075mm raster,300000 expansions/window,6mm window','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'selected_nets':nets,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jl-additive-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
