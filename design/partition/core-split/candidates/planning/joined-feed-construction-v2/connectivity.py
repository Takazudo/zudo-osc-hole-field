#!/usr/bin/env python3
"""All-port graph of contained, drilled source copper; never a resistance proof."""
import argparse,hashlib,json,math,resource,time
from collections import defaultdict,Counter
from pathlib import Path
import shapely
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
import staged_caps
import selective_annulus
NET_LAYER={'AGND':'In1.Cu','+5V':'In2.Cu','-12V':'In3.Cu','+12V':'In4.Cu'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
 if not c:raise ValueError(m)
def chunks(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 need(g.geom_type in ('MultiPolygon','GeometryCollection'),'unexpected conductor dimension')
 return [p for q in g.geoms if q.geom_type in ('Polygon','MultiPolygon','GeometryCollection') for p in chunks(q)]
def shape(o,layer=None):
 if o['kind']=='via':return Point(o['center_mm']).buffer(selective_annulus.diameter(o,layer)/2,quad_segs=32)
 if o['kind']=='segment':return LineString(o['path_mm']).buffer(o['width_mm']/2,quad_segs=32)
 if o['kind']=='pad':return Polygon(o['polygon_mm'],o.get('holes_mm',[]))
 raise ValueError('unreviewed graph object '+o['kind'])
def build(source,planes):
 selective_annulus.validate_source(source,planes)
 closed_barrels=staged_caps.validate(source)
 complete=source['objects']+planes['new_objects']
 rows=[o for o in complete if o.get('net') in NET_LAYER and o['kind'] in ('pad','segment','via')]
 need(len({o['id'] for o in rows})==len(rows),'duplicate physical object identity')
 identities=[o['id'] for o in rows]+[p['id'] for pieces in planes['clipped_sheets'].values() for p in pieces]
 need(len(identities)==len(set(identities)),'plane/source identity collision')
 bynet=defaultdict(list)
 for o in rows:bynet[o['net']].append(o)
 need(set(bynet)==set(NET_LAYER) and {o['net'] for o in source['loads']}==set(NET_LAYER),'complete four-net census')
 expected={f'CS247-{source["board"]}-W{i+1}':net for i,net in enumerate(['+12V','-12V','+5V','AGND','AGND','AGND'])}
 actual={o['id']:o['net'] for o in rows if o['kind']=='pad' and o['id'].startswith('CS247-')}
 need(actual==expected,'exact six terminal identities/nets')
 holes=defaultdict(list);drill_sources=[];drill_records=[];drill_shapes=[]
 for o in complete:
  if o.get('drill_mm',0)<=0:continue
  radius=o['drill_mm']/2
  if 'center_mm' in o:center=o['center_mm']
  else:
   need(o['kind']=='keepout' and o['id'].startswith('NPTH:'),'drilled object requires exact centre')
   polygon=Polygon(o['polygon_mm']);need(polygon.is_valid,'invalid NPTH ring');x0,y0,x1,y1=polygon.bounds;center=[(x0+x1)/2,(y0+y1)/2]
   need(all(abs(math.dist(center,p)-radius)<1e-5 for p in o['polygon_mm']),'NPTH is not the declared circular drill')
  hole=Point(center).buffer(radius/math.cos(math.pi/128),quad_segs=32)
  depth=closed_barrels[o['id']]['z_band_mm'] if o['id'] in closed_barrels else [min(staged_caps.BANDS[l][0] for l in o['layers']),max(staged_caps.BANDS[l][1] for l in o['layers'])]
  for layer,foil in staged_caps.BANDS.items():
   if min(depth[1],foil[1])-max(depth[0],foil[0])>1e-10:holes[layer].append(hole)
  drill_records.append((o['id'],center,radius,depth));drill_shapes.append(hole)
  drill_sources.append(o['id'])
 hole_trees={layer:STRtree(gs) for layer,gs in holes.items()}
 drill_tree=STRtree(drill_shapes)
 caps=source.get('staged_cap_solids',{}).get('caps',[])
 for cap in caps:
  disk=Point(cap['center_mm']).buffer(cap['radius_mm'],quad_segs=32)
  for raw in drill_tree.query(disk.envelope):
   other_id,center,radius,depth=drill_records[int(raw)]
   if min(depth[1],cap['z_band_mm'][1])-max(depth[0],cap['z_band_mm'][0])<=1e-10:continue
   need(math.dist(center,cap['center_mm'])>=radius+cap['radius_mm']-1e-10,'open drill cuts closed copper cap: '+cap['id']+' / '+other_id)
 cap_shapes=[Point(c['center_mm']).buffer(c['radius_mm'],quad_segs=32) for c in caps]
 cap_tree=STRtree(cap_shapes)
 for i,cap in enumerate(caps):
  for raw in cap_tree.query(cap_shapes[i].envelope):
   other=caps[int(raw)]
   if cap['layer']!=other['layer'] or cap['net']==other['net']:continue
   need(math.dist(cap['center_mm'],other['center_mm'])>=cap['radius_mm']+other['radius_mm']-1e-10,'different-net cap solids overlap')
 summaries={};ports=[];missing=[];terminal_ports=[];counts=Counter();object_connections={}
 for net,objs in bynet.items():
  nodes=[];nodeids=[];node_layers=[];portnodes=defaultdict(list);barrels=defaultdict(list)
  def add(identity,g,layer,barrel_band=None):
   need(g.is_valid and not g.is_empty,'invalid input conductor '+identity)
   cutters=holes.get(layer,[])
   if cutters:
    selected=hole_trees[layer].query(g)
    if len(selected):g=g.difference(unary_union([cutters[int(j)] for j in selected]))
   need(g.is_valid,'invalid drilled conductor '+identity)
   for i,piece in enumerate(chunks(g)):
    if piece.area<=1e-12:continue
    index=len(nodes);nodes.append(piece);nodeids.append(f'{identity}|{layer}|{i}');node_layers.append(layer);portnodes[identity].append(index)
    if barrel_band is not None and piece.intersection(barrel_band).area>1e-10:barrels[identity].append(index)
  for p in planes['clipped_sheets'][net]:
   add(p['id'],Polygon(p.get('polygon_mm',p.get('exterior')),p.get('holes_mm',p.get('holes',[]))),NET_LAYER[net])
  for o in objs:
   g=shape(o,'F.Cu');barrel=o['kind']=='via' or o['kind']=='pad' and o.get('drill_mm',0)>0 and len(o['layers'])>1
   need(len(o['layers'])==1 or barrel,'unproved cross-layer connection '+o['id'])
   band=None
   if barrel:
    radius=o['drill_mm']/2;centre=Point(o['center_mm'])
    band=centre.buffer(radius+.025,quad_segs=32).difference(centre.buffer(radius/math.cos(math.pi/128),quad_segs=32))
    need(not band.is_empty and g.covers(band),'declared .025mm annular barrel wall leaves source pad')
    # An intact annular wall is the explicit cross-foil connection model.
    # Test the analytic annulus, not its inscribed polygon: another drill
    # cutting any wall sector invalidates this model. Coaxial equal bores
    # merely meet its inner boundary and may belong to adjacent stages.
    depth=closed_barrels[o['id']]['z_band_mm'] if o['id'] in closed_barrels else [min(staged_caps.BANDS[l][0] for l in o['layers']),max(staged_caps.BANDS[l][1] for l in o['layers'])]
    for raw in drill_tree.query(centre.buffer(radius+.025,quad_segs=32).envelope):
     other_id,other_center,other_radius,other_depth=drill_records[int(raw)]
     if other_id==o['id'] or min(depth[1],other_depth[1])-max(depth[0],other_depth[0])<=1e-10:continue
     distance=math.dist(o['center_mm'],other_center)
     cuts_wall=distance+other_radius>radius+1e-10 and distance-other_radius<radius+.025-1e-10
     need(not cuts_wall,'other drill cuts declared continuous barrel wall: '+o['id']+' / '+other_id)
   for layer in o['layers']:add(o['id'],shape(o,layer) if selective_annulus.FIELD in o else g,layer,band)
  parent=list(range(len(nodes)));size=[1]*len(nodes)
  def root(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  def union(i,j):
   a,b=root(i),root(j)
   if a==b:return
   if size[a]<size[b]:a,b=b,a
   parent[b]=a;size[a]+=size[b]
  # Only explicit plated pad/via bodies join foils. A net label is not an edge.
  for members in barrels.values():
   for j in members[1:]:union(members[0],j)
  shapely.prepare(nodes);tree=STRtree(nodes);edges=0;near=0
  for i,ga in enumerate(nodes):
   for raw in tree.query(ga):
    j=int(raw)
    if j<=i or node_layers[i]!=node_layers[j]:continue
    gb=nodes[j]
    if not shapely.intersects(ga,gb):continue
    if shapely.covers(ga,gb) or shapely.covers(gb,ga) or ga.intersection(gb).area>1e-10:union(i,j);edges+=1
    else:near+=1
  terminals=[o for o in objs if o['id'].startswith('CS247-') and o['kind']=='pad']
  need(len(terminals)==(3 if net=='AGND' else 1),'complete feed terminal census '+net)
  source_roots={root(i) for o in terminals for i in portnodes[o['id']]}
  for o in terminals:
   terminal_ports.append({'id':o['id'],'net':net,'component_ids':sorted({nodeids[root(i)] for i in portnodes[o['id']]})})
  for identity in sorted(set(portnodes)|{o['id'] for o in objs}|{p['id'] for p in planes['clipped_sheets'][net]}):
   members=portnodes[identity]
   components={root(i) for i in members}
   object_connections[identity]={'net':net,'component_ids':sorted(nodeids[i] for i in components),'all_fragments_connected_to_feed':bool(components) and components<=source_roots,'any_fragment_connected':bool(components&source_roots),'fragment_count':len(members)}
  for o in objs:
   if o['kind']!='pad':continue
   components={root(i) for i in portnodes[o['id']]};connected=bool(components) and components<=source_roots
   ports.append({'id':o['id'],'ref':o.get('ref'),'pad':o.get('pad'),'net':net,'layers':o['layers'],'component_ids':sorted(nodeids[i] for i in components),'all_port_fragments_connected_to_feed':connected,'any_fragment_connected':bool(components&source_roots),'disconnected_fragment_component_ids':sorted(nodeids[i] for i in components-source_roots)})
  byid={p['id']:p for p in ports if p['net']==net}
  for load in source['loads']:
   if load['net']!=net:continue
   need(load['pad_id'] in byid,'missing exact load pad')
   if not byid[load['pad_id']]['all_port_fragments_connected_to_feed']:missing.append(load|{'component_ids':byid[load['pad_id']]['component_ids']})
  summaries[net]={'nodes':len(nodes),'positive_area_edges':edges,'uncredited_tangent_pairs':near,'components':len({root(i) for i in range(len(nodes))}),'source_components':len(source_roots),'all_three_returns_one_board_component':len(source_roots)==1 if net=='AGND' else None}
  counts['nodes']+=len(nodes);counts['edges']+=edges
 return {'status':'SOURCE_ALL_DIRECT_LOADS_CONNECTED' if not missing else 'SOURCE_DISCONNECTED_LOAD_PORTS','board':source['board'],'physical_ports':ports,'object_connections':object_connections,'terminal_ports':terminal_ports,'graph':summaries,'counts':dict(counts),'explicit_closed_cap_count':len(caps),'complete_drill_inventory_count':len(drill_sources),'complete_drill_inventory_sha256':hashlib.sha256(json.dumps(sorted(drill_sources)).encode()).hexdigest(),'disconnected_loads':missing,'direct_load_count':len(source['loads']),'downstream_active_or_resistive_paths_not_shortened':source.get('downstream_loads',[]),'limits':['Contained source conductors. Legacy/open bores subtract conservatively from every touched foil. Explicit new staged caps occupy their full specified foil bands; their closed bores occupy dielectric only. Unspecified fill supplies no conductivity.','Explicit plated-body cross-layer edges require positive foil-piece contact with the declared .025mm annular wall. Other drill volumes may not cut that wall or a closed cap. Plating/cap process is conditional and unqualified; graph connectivity implies no equipotential or zero resistance.','Positive-area connectivity is not a finite resistance/current/drop certificate. Full net loads, source and GH incidence must use finite field operators.','Unknown source-pad approximation and physical process still require native/physical verification.'],'native_calls':0,'accepted':False}
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--planes',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();need(not a.output.exists(),'fresh output')
 seals={str(q):sha(q) for q in [a.board,a.planes,Path(__file__),Path(staged_caps.__file__),Path(selective_annulus.__file__)]};s=json.loads(a.board.read_text());g=json.loads(a.planes.read_text());need(g['input_sha256']['filtered_board']==sha(a.board),'clipped/normalized epoch mismatch');start=time.monotonic();out=build(s,g)
 for name,h in seals.items():need(sha(Path(name))==h,'source changed during graph')
 out.update(input_sha256=seals,elapsed_seconds=time.monotonic()-start,peak_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','board','direct_load_count','counts','elapsed_seconds','peak_KiB']}));print('disconnected',len(out['disconnected_loads']))
if __name__=='__main__':main()
