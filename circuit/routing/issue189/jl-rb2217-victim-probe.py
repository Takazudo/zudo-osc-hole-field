import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-rb2217/osc-jack-left-grid-189-jl-rb2217-ground-corridor-verify/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='0e290e09ef653369099fc2272b779a8e60a192d9ef745fd86ca44c3d22447e61'
events=[];start=time.monotonic()
results,removed=route(dump,['X1B3E1B9E41C624EA5258'],res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},window_mm=8,max_expansions=1600000,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-rb2217-victim-repair');assert not removed
out={'status':'RASTER DIAGNOSTIC ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'One natively split signal victim on the rejected RB2217 candidate; restore using the existing signal0.2mm clearance/width and existing neck-down rules, with unchanged rail/AGND growth and native acceptance. Existing minus-twelve fill guard retained. Full original native gates mandatory.','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jl-rb2217-victim-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
