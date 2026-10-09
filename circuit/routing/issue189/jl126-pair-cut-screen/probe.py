import json,time,hashlib,sys,copy
from pathlib import Path
from shapely.geometry import Point,LineString
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-d2326/osc-jack-left-grid-189-jl127-d2326-fresh/dump.json');base=json.loads(p.read_text());pairs=json.loads(Path('.circuit-cache/issue189-jl-island-pairs.json').read_text())['transactions'][:12]
out=[];start=time.monotonic()
for target in pairs:
 net=target['net'];bounds=target['bounds_mm'];previous=set()
 for radius in (.35,.6,.9):
  points=[Point(x*1e6,y*1e6) for x,y in target['nearest_points_mm']];cuts=[]
  for row in base['tracks']+base['vias']:
   if row['net'] in (*RAILS,'AGND',net):continue
   shape=LineString([row['a'],row['b']]) if 'a' in row else Point(row['xy'])
   if min(shape.distance(p) for p in points)<=radius*1e6:cuts.append(row)
  ids={r['uuid'] for r in cuts};victims={r['net'] for r in cuts}
  if not ids or ids==previous or len(ids)>12 or len(victims)>2:continue
  previous=ids
  if any(any(not(bounds[0]*1e6<=x<=bounds[2]*1e6 and bounds[1]*1e6<=y<=bounds[3]*1e6) for x,y in ([r['a'],r['b']] if 'a' in r else [r['xy']])) for r in cuts):continue
  d=copy.deepcopy(base)
  for kind in ['tracks','vias']:d[kind]=[x for x in d[kind] if x['uuid'] not in ids]
  events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
  rows,_=copper_rows(results,'osc-jack-left','issue189-pair-cut');assert not removed
  out.append({'net':net,'radius_mm':radius,'cuts':sorted(ids),'victims':sorted(victims),'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'copper':rows})
  print(net,radius,'cuts',len(ids),'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
  Path('.circuit-cache/issue189-jl-pair-cuts.json').write_text(json.dumps({'status':'TARGET SCREEN ONLY; NATIVE CUT MEMBERSHIPS AND VICTIM RESTORATION NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'weight':2.5,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
  if rows:break
