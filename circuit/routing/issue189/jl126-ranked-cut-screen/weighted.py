import json,time,hashlib,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-d2326/osc-jack-left-grid-189-jl127-d2326-fresh/dump.json');base=json.loads(p.read_text());rank=json.loads(Path('circuit/routing/issue189/jl126-bounded-screen/repair-ranking.json').read_text());out=[];start=time.monotonic()
for spec in rank:
 net=spec['net'];cuts=set(spec['cut']);pads=[x for x in base['pads'] if x['net']==net]
 coords=[z for x in pads for z in x['poly']]
 for x in base['tracks']:
  if x['uuid'] in cuts:coords.extend([[x['a'][0]-x['width']/2,x['a'][1]-x['width']/2],[x['a'][0]+x['width']/2,x['a'][1]+x['width']/2],[x['b'][0]-x['width']/2,x['b'][1]-x['width']/2],[x['b'][0]+x['width']/2,x['b'][1]+x['width']/2]])
 bounds=[min(x[0] for x in coords)/1e6-2,min(x[1] for x in coords)/1e6-2,max(x[0] for x in coords)/1e6+2,max(x[1] for x in coords)/1e6+2]
 if (bounds[2]-bounds[0])*(bounds[3]-bounds[1])>2500 or max(bounds[2]-bounds[0],bounds[3]-bounds[1])>100:
  out.append({'selection':spec,'bounds_mm':bounds,'status':'SKIPPED exceeds2500mm2 or100mm raster bound'});continue
 d=copy.deepcopy(base)
 for kind in ['tracks','vias']:d[kind]=[x for x in d[kind] if x['uuid'] not in cuts]
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-ranked-cut');assert not removed
 out.append({'selection':spec,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'copper':rows})
 print(net,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
 Path('.circuit-cache/issue189-jl-ranked-cut-weighted.json').write_text(json.dumps({'status':'TARGET SCREEN ONLY; VICTIM MEMBERSHIP/RESTORATION AND ALL NATIVE GATES NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')

Path('.circuit-cache/issue189-jl-ranked-cut-weighted.json').write_text(json.dumps({'status':'TARGET SCREEN ONLY; VICTIM MEMBERSHIP/RESTORATION AND ALL NATIVE GATES NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'weight':2.5,'max_expansions':300000,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
