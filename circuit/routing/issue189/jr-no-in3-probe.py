import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
source=Path('.circuit-cache/issue189-downloaded/jr-dump.json');dump=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='b53fc851992843175db2669ec12540e1e6e27b4eda4c28a5834ce349c11f377b'
nets=sorted({r['net'] for r in json.load(open('circuit/routing/issue189/jr-additive-subset-proposal.json'))['copper']});events=[];start=time.monotonic()
results,removed=route(dump,nets,res=.075,clearance=.2,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},
 fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,diagnostics=events,**neck_kwargs('osc-jack-right'))
rows,links=copper_rows(results,'osc-jack-right','issue189-no-in3-additive')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Previously routed JR subset nets on identical original input; In3 excluded from signal paths because native results proved supply fragmentation; additive only,0.075mm raster,300000 expansions/window,6mm window','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'selected_nets':nets,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jr-no-in3-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
