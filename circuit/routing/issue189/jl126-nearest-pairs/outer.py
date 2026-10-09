import json,time,hashlib,sys,itertools
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union,nearest_points
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-d2326/osc-jack-left-grid-189-jl127-d2326-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='54b4c9718f652dfdc98b4dab615845962dc8e3025f51a76541a50e0ba3d579d9'
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
selected=sorted(candidates)[1:24];out=[];start=time.monotonic()
for (distance,i,j,a,b),net in selected:
 bounds=[min(a[0],b[0])-6,min(a[1],b[1])-6,max(a[0],b[0])+6,max(a[1],b[1])+6]
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-nearest-islands-outer');assert not removed
 out.append({'net':net,'native_component_pair':[i,j],'nearest_points_mm':[a,b],'distance_mm':distance,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}})
 print(net,distance,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
 Path('.circuit-cache/issue189-jl-island-pairs-outer.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'allowed_layers':['F.Cu','B.Cu'],'weight':2.5,'selection':'next23 nearest native component copper pairs; full original memberships retained','elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
