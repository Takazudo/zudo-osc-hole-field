"""Approximate topology/envelope screen only; native gates remain mandatory.
Run from the repo root after extracting the hash-verified recovery artifact.
"""
import json,math,hashlib
from pathlib import Path
plan=json.loads(Path("circuit/routing/issue189/core-reviewed/plan.json").read_text())
dump_path=Path(".circuit-cache/issue189-downloaded/core-repair/.circuit-cache/osc-core-grid-shards-start/dump.json")
assert hashlib.sha256(dump_path.read_bytes()).hexdigest()==plan["baseline_native_dump_sha256"]
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
b=json.load(open('.circuit-cache/issue189-downloaded/core-repair/.circuit-cache/osc-core-grid-shards-start/dump.json'));net='X1A3A22F4B289D6F62B00';center=[206300000,273475000];vs=[v for v in b['vias'] if v['net']==net and math.dist(v['xy'],center)<650000]
old=unary_union([Point(v['xy']).buffer(v['diameter']/2) for v in vs]);replacement=unary_union([Point(center).buffer(300000)]+[LineString([v['xy'],center]).buffer(100000) for v in vs if v['xy']!=center])

from shapely.geometry import Polygon
netpads=[p for p in b['pads'] if p['net']==net];tracks=[t for t in b['tracks'] if t['net']==net];allvias=[v for v in b['vias'] if v['net']==net]
def groups(changed):
 polys={};parent={}
 def find(x):
  parent.setdefault(x,x)
  if parent[x]!=x:parent[x]=find(parent[x])
  return parent[x]
 def join(x,y):parent[find(x)]=find(y)
 for layer in b['layers']:
  shapes=[LineString([t['a'],t['b']]).buffer(t['width']/2) for t in tracks if t['layer']==layer]+[Polygon(p['poly']) for p in netpads if layer in p['layers']]+[Point(v['xy']).buffer(v['diameter']/2) for v in allvias if not changed or v not in vs]
  if changed:shapes+=[Point(center).buffer(300000)]+([replacement] if layer in ['F.Cu','In2.Cu','In3.Cu','B.Cu'] else [])
  u=unary_union(shapes);polys[layer]=list(getattr(u,'geoms',[u]))
 def nodes(xy,layers):return [(l,i) for l in layers for i,g in enumerate(polys[l]) if g.covers(Point(xy))]
 for v in ([v for v in allvias if v not in vs]+[{'xy':center}] if changed else allvias):
  ns=nodes(v['xy'],b['layers'])
  for n in ns[1:]:join(ns[0],n)
 result={}
 for t in tracks:
  ns=nodes([(x+y)/2 for x,y in zip(t['a'],t['b'])],[t['layer']]);result[t['uuid']]=find(ns[0]) if ns else None
 for p in netpads:
  ns=nodes(p['xy'],p['layers'])
  for n in ns[1:]:join(ns[0],n)
  result[p['uuid']]=find(ns[0]) if ns else None
 return {k:find(v) if v else None for k,v in result.items()}
x,y=groups(False),groups(True);oldgroups={v:{k for k,w in x.items() if v==w} for v in set(x.values())};print('groups before/after',len(set(x.values())),len(set(y.values())))
for members in oldgroups.values():
 if len({y[u] for u in members})>1:print('SPLIT',len(members),[len([u for u in members if y[u]==g]) for g in {y[u] for u in members}])

assert replacement.difference(old).area<1, 'new copper exceeds original envelope'
assert all(len({y[u] for u in members})==1 for members in oldgroups.values()), 'existing copper group splits'
print('Approximate geometry screen PASS; native validation NOT RUN by this script')
