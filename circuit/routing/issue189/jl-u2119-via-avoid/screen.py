import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2119-outer/.circuit-cache/osc-jack-left-grid-shards-start/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='55a3edef21878d3e89ac9a02b0264f27d7a97da0d666648b5ffc27e47afde17d';net='X632AF8DD6216ED26A96D';source=json.loads(Path('circuit/routing/issue189/jl126-nearest-pairs/outer.json').read_text());bounds=next(t['bounds_mm'] for t in source['transactions'] if t['net']==net);out=[];start=time.monotonic()
for avoid,layers in [((200.675,109.375,201.275,109.975),['F.Cu','B.Cu']),((200.675,109.375,201.275,109.975),SIGNAL_LAYERS),((200.375,109.075,201.575,110.275),SIGNAL_LAYERS)]:
 ground_growth=.05
 x0,y0,x1,y1=avoid
 search={**d,'keepouts':d['keepouts']+[{'name':'experimental-via-avoid-only','poly':[[int(x*1e6),int(y*1e6)] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]],'layers':d['layers'],'tracks':False,'vias':True}]}

 events=[];t=time.monotonic();results,removed=route(search,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,grow={**{n:.05 for n in RAILS},'AGND':ground_growth},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-u2119-via-avoid');assert not removed
 out.append({'via_avoid_mm':avoid,'allowed_layers':layers,'ground_growth_mm':ground_growth,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(layers,ground_growth,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-u2119-via-avoid.json').write_text(json.dumps({'status':'ADDITIVE RASTER ONLY; SEARCH-ONLY VIA EXCLUSION AROUND NATIVE LOST FILL; BOARD RULES UNCHANGED; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
