import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-two-ground/osc-jack-left-grid-189-jl-two-ground-corridors-verify/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='5a27ab66f7736a8cc2bc3fa1837055e34ce417635f8b331e73b53f695dfaddde'
events=[];start=time.monotonic()
results,removed=route(dump,['X2408354846003BF2C899','XA23B6CC73603CD7235D3'],res=.05,clearance=.25,signal_width=.2,signal_via_diameter=.6,allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},window_mm=8,max_expansions=1600000,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-two-ground-victim-repair');assert not removed
out={'status':'RASTER DIAGNOSTIC ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Two natively split victim groups on the rejected two-ground candidate; exclude In3 to test the fill-guard obstruction. Existing minus-twelve fill guard retained. Full original native gates mandatory.','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jl-two-ground-victim-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
