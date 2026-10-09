import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jr-two-without-d7504/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='72a24ee996ae454c099ed165de1bd857721c42bef37861907a98ba5a4bf39d0c';net='X3307A17C148FAA8F7A4D';source=json.loads(Path('circuit/routing/issue189/jr146-bounded-screen/result.json').read_text());bounds=next(t['bounds_mm'] for t in source['transactions'] if t['net']==net);out=[];start=time.monotonic()
for layers,ground_growth in ((['F.Cu','B.Cu'],.05),(SIGNAL_LAYERS,.3),(SIGNAL_LAYERS,.6),(['F.Cu','B.Cu'],.3)):
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,grow={**{n:.05 for n in RAILS},'AGND':ground_growth},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-right'))
 rows,_=copper_rows(results,'osc-jack-right','issue189-d7504-protected-ground');assert not removed
 out.append({'allowed_layers':layers,'ground_growth_mm':ground_growth,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(layers,ground_growth,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jr-d7504-alternatives.json').write_text(json.dumps({'status':'ADDITIVE RASTER ONLY; MORE CONSERVATIVE GROUND OBSTACLES; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
