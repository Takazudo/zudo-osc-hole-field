import json,time,hashlib,sys,itertools
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union,nearest_points
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/core-filtered/.circuit-cache/osc-core-grid-189-compact-refill/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
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
published='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932'
assert hashlib.sha256(Path('boards/osc-core/osc-core.kicad_pcb').read_bytes()).hexdigest()==published
tested={'X33ADBEB2EBFF18372234'}|{t['net'] for t in json.loads(Path('circuit/routing/issue189/core1441-no-via/result.json').read_text())['transactions']}
selected=[c for c in sorted(candidates) if c[1] not in tested and abs(c[0][3][0]-c[0][4][0])<=88 and abs(c[0][3][1]-c[0][4][1])<=88][:24];out=[];start=time.monotonic()
for (distance,i,j,a,b),net,layer in [(pair,net,layer) for pair,net in selected for layer in ['F.Cu','B.Cu']]:
 if time.monotonic()-start>600:break
 bounds=[min(a[0],b[0])-6,min(a[1],b[1])-6,max(a[0],b[0])+6,max(a[1],b[1])+6]
 assert bounds[2]-bounds[0]<=100 and bounds[3]-bounds[1]<=100
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=[layer],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=1,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-core'))
 rows,_=copper_rows(results,'osc-core','issue189-core1441-next-no-via');assert not removed
 out.append({'net':net,'layer':layer,'native_component_pair':[i,j],'nearest_points_mm':[a,b],'distance_mm':distance,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':published,'removed_uuids':[],'copper':rows}})
 print(net,distance,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
 Path('circuit/routing/issue189/core1441-next-no-via/result.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'single_layer_cases':['F.Cu','B.Cu'],'weight':1,'selection':'next24 eligible native component pairs excluding the previous24 and active U1513 trial; each F.Cu/B.Cu only; full original memberships retained','elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
