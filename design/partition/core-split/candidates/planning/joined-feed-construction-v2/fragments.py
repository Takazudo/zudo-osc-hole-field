#!/usr/bin/env python3
"""Drilled per-layer conductor fragments of one E16 rail net, exactly as connectivity.py builds them.

connectivity.build() returns only component summaries; the finite adapter needs the
fragments themselves. This mirrors its node construction, barrel-wall membership
and positive-area same-layer edges for one net, then verify() proves the result
equals the retained graph's object_connections identity-by-identity. Any drift
between the two is a failure, never a silent re-derivation.
"""
import math
from collections import defaultdict
import shapely
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
import connectivity,staged_caps
NET_LAYER=connectivity.NET_LAYER
LAYERS=list(staged_caps.BANDS)
WALL_MM=.025          # connectivity.py's annular barrel-wall test band
def need(c,m):
 if not c:raise ValueError(m)
class NetFragments:
 """nodes[i]: drilled polygon; ids[i] '<identity>|<layer>|<k>'; owner[i]; layer[i]; root(i) union-find."""
 def __init__(self,source,planes,net):
  closed=staged_caps.validate(source);complete=source['objects']+planes['new_objects']
  holes=defaultdict(list)
  for o in complete:
   if o.get('drill_mm',0)<=0:continue
   radius=o['drill_mm']/2
   if 'center_mm' in o:center=o['center_mm']
   else:
    x0,y0,x1,y1=Polygon(o['polygon_mm']).bounds;center=[(x0+x1)/2,(y0+y1)/2]
   hole=Point(center).buffer(radius/math.cos(math.pi/128),quad_segs=32)
   depth=closed[o['id']]['z_band_mm'] if o['id'] in closed else [min(staged_caps.BANDS[l][0] for l in o['layers']),max(staged_caps.BANDS[l][1] for l in o['layers'])]
   for layer,foil in staged_caps.BANDS.items():
    if min(depth[1],foil[1])-max(depth[0],foil[0])>1e-10:holes[layer].append(hole)
  trees={layer:STRtree(gs) for layer,gs in holes.items()}
  self.net=net;self.board=source['board'];self.nodes=[];self.ids=[];self.owner=[];self.layer=[];self.portnodes=defaultdict(list);self.barrels=defaultdict(list)
  self.objects={o['id']:o for o in source['objects'] if o.get('net')==net and o['kind'] in ('pad','segment','via')}
  self.sheets={p['id']:p for p in planes['clipped_sheets'][net]}
  def add(identity,g,layer,band=None):
   cutters=holes.get(layer,[])
   if cutters:
    sel=trees[layer].query(g)
    if len(sel):g=g.difference(unary_union([cutters[int(j)] for j in sel]))
   for k,piece in enumerate(connectivity.chunks(g)):
    if piece.area<=1e-12:continue
    i=len(self.nodes);self.nodes.append(piece);self.ids.append(f'{identity}|{layer}|{k}');self.owner.append(identity);self.layer.append(layer);self.portnodes[identity].append(i)
    if band is not None and piece.intersection(band).area>1e-10:self.barrels[identity].append(i)
  for p in planes['clipped_sheets'][net]:
   add(p['id'],Polygon(p.get('polygon_mm',p.get('exterior')),p.get('holes_mm',p.get('holes',[]))),NET_LAYER[net])
  for o in self.objects.values():
   g=connectivity.shape(o);band=None
   if o['kind']=='via' or o['kind']=='pad' and o.get('drill_mm',0)>0 and len(o['layers'])>1:
    r=o['drill_mm']/2;c=Point(o['center_mm']);band=c.buffer(r+WALL_MM,quad_segs=32).difference(c.buffer(r/math.cos(math.pi/128),quad_segs=32))
   for layer in o['layers']:add(o['id'],g,layer,band)
  self.parent=list(range(len(self.nodes)));size=[1]*len(self.nodes)
  def union(i,j):
   a,b=self.root(i),self.root(j)
   if a==b:return
   if size[a]<size[b]:a,b=b,a
   self.parent[b]=a;size[a]+=size[b]
  for members in self.barrels.values():
   for j in members[1:]:union(members[0],j)
  shapely.prepare(self.nodes);tree=STRtree(self.nodes);self.edges=[]
  for i,ga in enumerate(self.nodes):
   for raw in tree.query(ga):
    j=int(raw)
    if j<=i or self.layer[i]!=self.layer[j]:continue
    gb=self.nodes[j]
    if not shapely.intersects(ga,gb):continue
    if shapely.covers(ga,gb) or shapely.covers(gb,ga) or ga.intersection(gb).area>1e-10:union(i,j);self.edges.append((i,j))
  self.terminals=sorted(o['id'] for o in self.objects.values() if o['id'].startswith('CS247-') and o['kind']=='pad')
  self.source_roots={self.root(i) for t in self.terminals for i in self.portnodes[t]}
  self.fed=[i for i in range(len(self.nodes)) if self.root(i) in self.source_roots]
 def root(self,i):
  while self.parent[i]!=i:self.parent[i]=self.parent[self.parent[i]];i=self.parent[i]
  return i
 def connection(self,identity):
  comps={self.root(i) for i in self.portnodes[identity]}
  return {'component_ids':sorted(self.ids[i] for i in comps),'all_fragments_connected_to_feed':bool(comps) and comps<=self.source_roots,
          'any_fragment_connected':bool(comps&self.source_roots),'fragment_count':len(self.portnodes[identity])}
 def verify(self,graph):
  """Every identity of this net must reproduce the retained graph's record exactly."""
  mine={k for k in set(self.portnodes)|set(self.objects)|set(self.sheets)}
  theirs={k for k,v in graph['object_connections'].items() if v['net']==self.net}
  need(mine==theirs,f'{self.net}: identity sets differ ({len(mine^theirs)})')
  bad=[k for k in sorted(mine) if graph['object_connections'][k]!=dict(self.connection(k),net=self.net)]
  need(not bad,f'{self.net}: {len(bad)} fragment records differ from the retained graph, e.g. {bad[:3]}')
  ports={p['id']:p for p in graph['physical_ports'] if p['net']==self.net}
  for pid,p in ports.items():
   c=self.connection(pid);need(c['all_fragments_connected_to_feed']==p['all_port_fragments_connected_to_feed'] and c['component_ids']==p['component_ids'],'port record differs '+pid)
  return {'identities':len(mine),'fragments':len(self.nodes),'fed_fragments':len(self.fed),'positive_area_edges':len(self.edges),'barrels':len(self.barrels),'ports':len(ports)}
