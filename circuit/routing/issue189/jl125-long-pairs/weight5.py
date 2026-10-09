import json,time,hashlib,sys,itertools
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union,nearest_points
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2119-outer/.circuit-cache/osc-jack-left-grid-shards-start/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='55a3edef21878d3e89ac9a02b0264f27d7a97da0d666648b5ffc27e47afde17d'
geometry={}
for r in d['pads']:
 if r['poly']:geometry.setdefault(r['uuid'],[]).append(Polygon(r['poly']))
for r in d['tracks']:geometry.setdefault(r['uuid'],[]).append(LineString([r['a'],r['b']]))
for r in d['vias']:geometry.setdefault(r['uuid'],[]).append(Point(r['xy']))
candidates=[]
for net,groups in d['islands'].items():
 if net in (*RAILS,'AGND') or len(groups)<2:continue
 shapes=[unary_union([shape for u in g for shape in geometry.get(u,[])]) for g in groups]
 pairs=[]
 for i,a in enumerate(shapes):
  if a.is_empty:continue
  for j,b in enumerate(shapes[:i]):
   if b.is_empty:continue
   x,y=nearest_points(a,b);pairs.append((x.distance(y)/1e6,i,j,[x.x/1e6,x.y/1e6],[y.x/1e6,y.y/1e6]))
 if pairs:candidates.append((min(pairs),net))
selected=[c for c in sorted(candidates)[24:] if abs(c[0][3][0]-c[0][4][0])<=88 and abs(c[0][3][1]-c[0][4][1])<=88][:24];out=[];start=time.monotonic()
for (distance,i,j,a,b),net in selected:
 bounds=[min(a[0],b[0])-6,min(a[1],b[1])-6,max(a[0],b[0])+6,max(a[1],b[1])+6]
 assert bounds[2]-bounds[0]<=100 and bounds[3]-bounds[1]<=100
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=5.0,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-jl125-long-pairs-weight5');assert not removed
 out.append({'net':net,'native_component_pair':[i,j],'nearest_points_mm':[a,b],'distance_mm':distance,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}})
 print(net,distance,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
 Path('.circuit-cache/issue189-jl125-long-pairs-weight5.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'allowed_layers':SIGNAL_LAYERS,'weight':5.0,'selection':'native component pairs ranked25–48 by nearest native component copper pairs; full original memberships retained','elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
