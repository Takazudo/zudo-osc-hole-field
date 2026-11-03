"""Optimistic continuous additive-escape screen; not a native routing pass."""
from pathlib import Path
import hashlib,json,sys
from shapely.geometry import Point,Polygon,LineString,box,mapping,shape
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441'
NET='XED7C19D453619667580D';SOURCE='3921a7e7-bdde-5afd-9636-95804e2a2928'
WINDOW=box(224,108,234,118)
def export():
 p=ROOT/'.circuit-cache/stage51/dump.json';d=json.loads(p.read_text())
 if d['board_sha256']!=BASE:raise ValueError('baseline')
 objects=[];unknown=[]
 def add(uid,name,net,layers,g):
  if g.distance(WINDOW)<2:objects.append(dict(id=uid,name=name,net=net,layers=layers,geometry=mapping(g)))
 for p1 in d['pads']:
  if p1['poly']:add(p1['uuid'],p1['ref']+':'+p1['pad'],p1['net'],p1['layers'],Polygon([(x/1e6,y/1e6) for x,y in p1['poly']]))
  else:
   distance=Point(*[x/1e6 for x in p1['xy']]).distance(WINDOW)
   unknown.append(dict(ref=p1['ref'],distance_to_window_mm=distance))
   if distance<2:raise ValueError('unknown local pad geometry')
 for t in d['tracks']:add(t['uuid'],t['uuid'],t['net'],[t['layer']],LineString([(x/1e6,y/1e6) for x,y in [t['a'],t['b']]]).buffer(t['width']/2e6,quad_segs=64))
 for v in d['vias']:add(v['uuid'],v['uuid'],v['net'],d['layers'],Point(*[x/1e6 for x in v['xy']]).buffer(v['diameter']/2e6,quad_segs=64))
 return dict(board_sha256=BASE,dump_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),window_mm=list(WINDOW.bounds),objects=objects,unknown_remote_pads=unknown,limits='Optimistic: ignores pours, drills, edge and rule areas; underapproximated circular buffers. Cannot accept a route from this screen.')
def analyze(d,width=.2,relax=.01):
 if d['board_sha256']!=BASE:raise ValueError('baseline')
 objects=[(o,shape(o['geometry'])) for o in d['objects']]
 seed=next(g for o,g in objects if o['id']==SOURCE)
 foreign=[(o,g) for o,g in objects if o['net']!=NET]
 clearance=lambda o:.25 if o['net'] in ['AGND','+12V','-12V','+5V'] else .2
 blocked=unary_union([g.buffer(width/2+clearance(o)-relax,quad_segs=64) for o,g in foreign if 'B.Cu' in o['layers']])
 free=WINDOW.difference(blocked);parts=list(free.geoms) if hasattr(free,'geoms') else [free]
 reachable=unary_union([g for g in parts if g.intersects(seed.buffer(width/2))])
 targets=unary_union([g for o,g in objects if o['net']==NET and o['id']!=SOURCE and 'B.Cu' in o['layers']])
 via={}
 for diameter in [.6,.5]:
  forbidden=unary_union([g.buffer(diameter/2+clearance(o)-relax,quad_segs=64) for o,g in foreign])
  candidates=reachable.buffer(diameter/2+width/2).union(seed.buffer(diameter/2)).difference(forbidden)
  via[str(diameter)]=dict(empty=candidates.is_empty,area_mm2=candidates.area,bounds=list(candidates.bounds) if not candidates.is_empty else None)
 result=dict(width_mm=width,optimistic_clearance_reduction_mm=relax,reachable_bounds=list(reachable.bounds),reachable_area_mm2=reachable.area,window_boundary_distance_mm=reachable.distance(WINDOW.boundary),same_net_target_empty=targets.is_empty,target_distance_mm=None if targets.is_empty else reachable.buffer(width/2).union(seed).distance(targets),vias=via)
 return result,reachable,objects,seed
if __name__=='__main__':
 if '--export' in sys.argv:(HERE/'geometry.json').write_text(json.dumps(export(),sort_keys=True,separators=(',',':'))+'\n')
 data=json.loads((HERE/'geometry.json').read_text());result=[analyze(data,w,m)[0] for w in [.2,.1] for m in [0,.01]]
 print(json.dumps(result,indent=2))
 (HERE/'screen.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
