#!/usr/bin/env python3
"""Place E16 local rail access: one through via plus a finite face trace per pad.

Implements the reviewed board-access rule (board-access-design.json
load_mapping.algorithm): first legal via site on a deterministic 0.25 mm grid
within 2 mm of an unresolved pad, with exact copper, drill and rule-area
clearance, landing inside an already feed-connected sheet piece. A placed via
is a proposal; only the complete cap/clip/graph/census rerun can credit it.
"""
import argparse,hashlib,json,math,os,resource,time,uuid
from collections import defaultdict
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,Polygon,LineString
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
NET_LAYER={'AGND':'In1.Cu','+5V':'In2.Cu','-12V':'In3.Cu','+12V':'In4.Cu'}
# Standard through via: within every published fab limit and the board's own
# min_via_diameter .5 / min_via_annular_width .1 (osc-core.kicad_pro).
VIA_DIAMETER,VIA_DRILL=.6,.3
TRACE_WIDTH=.25
CLEARANCE=.25          # Rails/Ground net-class clearance
HOLE_CLEARANCE=.25     # min_hole_clearance and min_hole_to_hole
GRID,RADIUS=.25,2.0
SHEET_MARGIN=.05
MIN_SHEET_WIDTH=.25    # clip_sheets.MIN_WIDTH_MM
NS=uuid.UUID('e16acce5-0000-5000-8000-000000000242')
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copper(o):
 if o['kind']=='via':return Point(o['center_mm']).buffer(o['diameter_mm']/2,quad_segs=16)
 if o['kind']=='segment':return LineString(o['path_mm']).buffer(o['width_mm']/2,quad_segs=16)
 if o['kind']=='pad':return Polygon(o['polygon_mm'])
 return None
class Obstacles:
 def __init__(self,objects):
  self.geoms=defaultdict(list);self.nets=defaultdict(list);self.drills=[];self.forbid=defaultdict(list)
  for o in objects:self.add(o)
  self.freeze()
 def add(self,o):
  if o['kind']=='rule_area':
   if o['rules'].get('vias')=='not_allowed' or o['rules'].get('tracks')=='not_allowed':
    for l in o['layers']:self.forbid[l].append(Polygon(o['polygon_mm']))
   return
  g=copper(o)
  if g is not None:
   for l in o['layers']:self.geoms[l].append(g);self.nets[l].append(o.get('net',''))
  if o.get('drill_mm',0)>0:self.drills.append(Point(o['center_mm']).buffer(o['drill_mm']/2,quad_segs=16))
 def freeze(self):
  self.trees={l:STRtree(g) for l,g in self.geoms.items()};self.drill_tree=STRtree(self.drills) if self.drills else None
  self.forbid_trees={l:STRtree(g) for l,g in self.forbid.items()}
 def blocked(self,shape,layers,net,drill_shape=None):
  for l in layers:
   if l in self.trees:
    for i in self.trees[l].query(shape,predicate='intersects'):
     if self.nets[l][int(i)]!=net:return 'copper:'+l
   if l in self.forbid_trees and len(self.forbid_trees[l].query(shape,predicate='intersects')):return 'rule_area:'+l
  if drill_shape is not None and self.drill_tree is not None and len(self.drill_tree.query(drill_shape,predicate='intersects')):return 'drill'
  return None
def sites(center):
 n=int(RADIUS/GRID);pts=[(i*GRID,j*GRID) for i in range(-n,n+1) for j in range(-n,n+1) if math.hypot(i*GRID,j*GRID)<=RADIUS+1e-9]
 pts.sort(key=lambda p:(round(math.hypot(*p),9),p[0],p[1]))
 return [(center[0]+x,center[1]+y) for x,y in pts]
def construct(source,planes,graph,census,only=None):
 objs=source['objects'];byid={o['id']:o for o in objs}
 feed={p['id']:Polygon(p['polygon_mm'],p['holes_mm']) for net,rows in planes['clipped_sheets'].items() for p in rows
       if graph['object_connections'].get(p['id'],{}).get('all_fragments_connected_to_feed')}
 feed_net=defaultdict(list)
 for pid,poly in feed.items():feed_net[pid.split('-SHEET-')[0].split('-',1)[1]].append(poly)
 for v in feed_net.values():shapely.prepare(v)
 feed_trees={n:(STRtree(v),v) for n,v in feed_net.items()}
 obs=Obstacles(objs);extra=Obstacles([]);added=[];results=[]
 targets=[r for r in census['unresolved'] if only is None or r['pad_id'] in only]
 for r in targets:
  pad=byid[r['pad_id']];net=pad['net'];face=[l for l in pad['layers'] if l in ('F.Cu','B.Cu')]
  if pad.get('drill_mm',0)>0 or len(face)!=1:results.append({'pad_id':pad['id'],'status':'SKIP_NOT_SINGLE_FACE_SMD'});continue
  face=face[0];target=NET_LAYER[net];tree,polys=feed_trees.get(net,(None,[]))
  reasons=defaultdict(int);placed=None
  for x,y in sites(pad['center_mm']):
   p=Point(x,y);via_keep=p.buffer(VIA_DIAMETER/2+CLEARANCE,quad_segs=16);drill_keep=p.buffer(VIA_DRILL/2+HOLE_CLEARANCE,quad_segs=16)
   why=obs.blocked(via_keep,LAYERS,net,drill_keep) or extra.blocked(via_keep,LAYERS,net,drill_keep)
   if why:reasons['via_'+why]+=1;continue
   ring=p.buffer(VIA_DIAMETER/2+SHEET_MARGIN,quad_segs=16)
   if tree is None or not any(shapely.contains(polys[int(i)],ring) for i in tree.query(ring,predicate='intersects')):reasons['not_in_feed_sheet']+=1;continue
   trace=None
   if not Polygon(pad['polygon_mm']).contains(p):
    trace=LineString([pad['center_mm'],[x,y]])
    keep,hole=trace.buffer(TRACE_WIDTH/2+CLEARANCE,quad_segs=8),trace.buffer(TRACE_WIDTH/2+HOLE_CLEARANCE,quad_segs=8)
    why=obs.blocked(keep,[face],net,hole) or extra.blocked(keep,[face],net,hole)
    if why:reasons['trace_'+why.split(':')[0]]+=1;continue
   placed=(x,y,trace);break
  if placed is None:
   results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'NO_LEGAL_SITE','rejections':dict(reasons)});continue
  x,y,trace=placed;key=f'{source["board"]}:{pad["id"]}'
  via={'id':str(uuid.uuid5(NS,key+':via')),'kind':'via','net':net,'layers':list(LAYERS),'center_mm':[round(x,6),round(y,6)],
       'diameter_mm':VIA_DIAMETER,'drill_mm':VIA_DRILL,'access_for_pad':pad['id'],'epoch':'E16',
       'process':'standard through via; filled and capped when inside its pad (via-in-pad)','via_in_pad':trace is None}
  new=[via]
  if trace is not None:
   new.append({'id':str(uuid.uuid5(NS,key+':trace')),'kind':'segment','net':net,'layers':[face],'path_mm':[list(pad['center_mm']),[round(x,6),round(y,6)]],
               'width_mm':TRACE_WIDTH,'access_for_pad':pad['id'],'epoch':'E16'})
  # Only the small set of new objects is re-indexed after each placement.
  for o in new:extra.add(o)
  extra.freeze();added+=new
  results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'PLACED','via_id':via['id'],'via_in_pad':trace is None,
                  'trace_length_mm':round(trace.length,6) if trace is not None else 0.,'target_layer':target})
 return added,results
ROUTE_WIDTHS=(.25,.2)
ROUTE_PITCH,ROUTE_HALF=.05,3.
GUARD_HALF=2.
def pieces(g):
 g=g.buffer(-MIN_SHEET_WIDTH/2,quad_segs=4).buffer(MIN_SHEET_WIDTH/2,quad_segs=4)
 return sum(1 for q in getattr(g,'geoms',[g]) if not q.is_empty and q.area>1e-6)
def antipad(p):return p.buffer(max(VIA_DIAMETER/2+CLEARANCE,VIA_DRILL/2+HOLE_CLEARANCE),quad_segs=16)
def severs(p,net,sheets,placed=()):
 """True if this via's antipad splits another rail's feed sheet inside the guard window.

 placed holds (net, antipad) of vias already added in this run, so cumulative
 necks are judged against the sheet those earlier vias leave behind."""
 box=shapely.box(p.x-GUARD_HALF,p.y-GUARD_HALF,p.x+GUARD_HALF,p.y+GUARD_HALF)
 cut=antipad(p)
 for other,sheet in sheets.items():
  if other==net or sheet is None:continue
  tree,polys=sheet;prior=[c for n,c in placed if n!=other and c.intersects(box)]
  for k in tree.query(cut,predicate='intersects'):
   local=polys[int(k)].intersection(box)
   if prior:local=local.difference(shapely.unary_union(prior))
   if pieces(local.difference(cut))>pieces(local):return True
 return False
def legal_via_sites(center,net,obs,extra,sheet,sheets=None,placed=()):
 """Grid sites in the route window where a new through via is legal on every layer."""
 if sheet is None:return []
 tree,polys=sheet;n=int((ROUTE_HALF-.5)/GRID);cx,cy=center;out=[]
 for i in range(-n,n+1):
  for j in range(-n,n+1):
   p=Point(cx+i*GRID,cy+j*GRID);keep=p.buffer(VIA_DIAMETER/2+CLEARANCE,quad_segs=16);hole=p.buffer(VIA_DRILL/2+HOLE_CLEARANCE,quad_segs=16)
   if obs.blocked(keep,LAYERS,net,hole) or extra.blocked(keep,LAYERS,net,hole):continue
   ring=p.buffer(VIA_DIAMETER/2+SHEET_MARGIN,quad_segs=16)
   if not any(shapely.contains(polys[int(k)],ring) for k in tree.query(ring,predicate='intersects')):continue
   if sheets is not None and severs(p,net,sheets,placed):continue
   out.append((cx+i*GRID,cy+j*GRID))
 return out
def local_route(pad,face,net,width,obs,extra,targets,sites=()):
 """Shortest 8-connected face path from pad to feed-connected same-net copper or a legal via site."""
 cx,cy=pad['center_mm'];box=shapely.box(cx-ROUTE_HALF,cy-ROUTE_HALF,cx+ROUTE_HALF,cy+ROUTE_HALF)
 goal=list(targets.geometries.take(targets.query(box))) if targets is not None else []
 goal+=[Point(q).buffer(ROUTE_PITCH/4) for q in sites]
 if not goal:return None,'no_feed_target_in_window'
 cuts=[]
 for o in (obs,extra):
  if face in o.trees:
   for i in o.trees[face].query(box):
    if o.nets[face][int(i)]!=net:cuts.append(o.geoms[face][int(i)].buffer(width/2+CLEARANCE,quad_segs=8))
  if o.drill_tree is not None:cuts+=[o.drills[int(i)].buffer(width/2+HOLE_CLEARANCE,quad_segs=8) for i in o.drill_tree.query(box)]
  if face in o.forbid_trees:cuts+=[o.forbid[face][int(i)] for i in o.forbid_trees[face].query(box)]
 forbidden=shapely.unary_union(cuts) if cuts else shapely.Polygon();shapely.prepare(forbidden)
 xs=np.arange(cx-ROUTE_HALF,cx+ROUTE_HALF+1e-9,ROUTE_PITCH);ys=np.arange(cy-ROUTE_HALF,cy+ROUTE_HALF+1e-9,ROUTE_PITCH)
 X,Y=np.meshgrid(xs,ys);free=~shapely.contains_xy(forbidden,X,Y)&~shapely.intersects_xy(forbidden,X,Y)
 padpoly=Polygon(pad['polygon_mm']);start=shapely.contains_xy(padpoly,X,Y)&free
 target=shapely.unary_union(goal);end=shapely.contains_xy(target,X,Y)&free
 if not start.any():return None,'pad_interior_blocked'
 if not end.any():return None,'feed_target_blocked'
 import heapq
 h,w=X.shape;dist=np.full(X.shape,np.inf);prev={};heap=[]
 for i,j in zip(*np.nonzero(start)):dist[i,j]=0;heapq.heappush(heap,(0.,i,j))
 steps=[(a,b,math.hypot(a,b)) for a in (-1,0,1) for b in (-1,0,1) if a or b];hit=None
 while heap:
  d,i,j=heapq.heappop(heap)
  if d>dist[i,j]:continue
  if end[i,j]:hit=(i,j);break
  for a,b,c in steps:
   u,v=i+a,j+b
   if 0<=u<h and 0<=v<w and free[u,v] and d+c<dist[u,v]:dist[u,v]=d+c;prev[(u,v)]=(i,j);heapq.heappush(heap,(d+c,u,v))
 if hit is None:return None,'no_clear_path'
 node=hit;path=[node]
 while node in prev:node=prev[node];path.append(node)
 pts=[(float(X[i,j]),float(Y[i,j])) for i,j in reversed(path)]
 site=min(sites,key=lambda q:math.dist(q,pts[-1])) if sites else None
 if site is not None and math.dist(site,pts[-1])<ROUTE_PITCH/2:pts[-1]=site
 else:site=None
 # Greedy line-of-sight simplification; every kept chord is re-tested exactly.
 out=[pts[0]];k=0
 while k<len(pts)-1:
  m=len(pts)-1
  while m>k+1 and LineString([pts[k],pts[m]]).intersects(forbidden):m-=1
  out.append(pts[m]);k=m
 line=LineString(out) if len(out)>1 else None
 if line is None or line.intersects(forbidden):return None,'simplification_failed'
 keep,hole=line.buffer(width/2+CLEARANCE,quad_segs=8),line.buffer(width/2+HOLE_CLEARANCE,quad_segs=8)
 if obs.blocked(keep,[face],net,hole) or extra.blocked(keep,[face],net,hole):return None,'exact_validation_failed'
 if site is None and not line.buffer(width/2).intersection(target).area>1e-6:return None,'no_positive_target_overlap'
 return (out,site),None
def route_access(source,graph,census,only=None,planes=None):
 objs=source['objects'];byid={o['id']:o for o in objs};sheets={}
 if planes is not None:
  for net,rows in planes['clipped_sheets'].items():
   polys=[Polygon(p['polygon_mm'],p['holes_mm']) for p in rows if graph['object_connections'].get(p['id'],{}).get('all_fragments_connected_to_feed')]
   shapely.prepare(polys);sheets[net]=(STRtree(polys),polys) if polys else None
 feed=defaultdict(list)
 for o in objs:
  if o.get('net') in NET_LAYER and o['kind'] in ('pad','segment','via') and graph['object_connections'].get(o['id'],{}).get('all_fragments_connected_to_feed'):
   for l in o['layers']:
    if l in ('F.Cu','B.Cu'):feed[(o['net'],l)].append(copper(o))
 feed_trees={k:STRtree(v) for k,v in feed.items()}
 obs=Obstacles(objs);extra=Obstacles([]);added=[];results=[];placed=[]
 for r in census['unresolved']:
  if only is not None and r['pad_id'] not in only:continue
  pad=byid[r['pad_id']];net=pad['net'];face=[l for l in pad['layers'] if l in ('F.Cu','B.Cu')]
  if pad.get('drill_mm',0)>0 or len(face)!=1:results.append({'pad_id':pad['id'],'status':'SKIP_NOT_SINGLE_FACE_SMD'});continue
  face=face[0];tree=feed_trees.get((net,face));reasons={};found=None
  for width in ROUTE_WIDTHS:
   found,why=local_route(pad,face,net,width,obs,extra,tree) if tree is not None else (None,'no_feed_copper_on_face')
   if found:break
   reasons[str(width)]=why
  if not found and planes is not None:
   sites=legal_via_sites(pad['center_mm'],net,obs,extra,sheets.get(net),sheets,placed)
   for width in ROUTE_WIDTHS:
    found,why=local_route(pad,face,net,width,obs,extra,None,sites) if sites else (None,'no_legal_via_site_in_window')
    if found:break
    reasons['via:'+str(width)]=why
  pts,site=found if found else (None,None)
  if not pts:results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'NO_ROUTE','reasons':reasons});continue
  key=f'{source["board"]}:{pad["id"]}:route';new=[]
  for n,(a,b) in enumerate(zip(pts,pts[1:])):
   new.append({'id':str(uuid.uuid5(NS,f'{key}:{n}')),'kind':'segment','net':net,'layers':[face],'path_mm':[[round(a[0],6),round(a[1],6)],[round(b[0],6),round(b[1],6)]],
               'width_mm':width,'access_for_pad':pad['id'],'epoch':'E16','method':'local_face_route_to_feed_connected_copper'})
  if site is not None:
   new.append({'id':str(uuid.uuid5(NS,key+':via')),'kind':'via','net':net,'layers':list(LAYERS),'center_mm':[round(site[0],6),round(site[1],6)],
               'diameter_mm':VIA_DIAMETER,'drill_mm':VIA_DRILL,'access_for_pad':pad['id'],'epoch':'E16','process':'standard through via','via_in_pad':False,'method':'local_face_route_to_new_via'})
   placed.append((net,antipad(Point(site))))
  for o in new:extra.add(o)
  extra.freeze();added+=new
  results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'ROUTED','width_mm':width,'segments':len(new)-(site is not None),
                  'length_mm':round(LineString(pts).length,6),'face':face,'new_via':site is not None})
 return added,results
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--method',choices=['via','route'],default='via')
 for k in ['source','graph','census']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--planes',type=Path,help='required by --method via')
 p.add_argument('--only',type=Path,help='JSON list of pad ids to attempt');p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists() and not a.report.exists(),'fresh outputs required');start=time.monotonic()
 need(a.method=='route' or a.planes,'--planes required for via placement')
 inputs=[a.source,a.graph,a.census,Path(__file__)]+([a.planes] if a.planes else [])+([a.only] if a.only else [])
 seals={str(q.resolve()):sha(q) for q in inputs}
 source,graph,census=[json.loads(q.read_text()) for q in [a.source,a.graph,a.census]]
 need(source['board']==graph['board']==census['board'],'one board epoch')
 need(census['graph_sha256']==sha(a.graph),'census must bind this exact graph')
 only=set(json.loads(a.only.read_text())) if a.only else None
 added,results=construct(source,json.loads(a.planes.read_text()),graph,census,only) if a.method=='via' else route_access(source,graph,census,only,json.loads(a.planes.read_text()) if a.planes else None)
 need(all(sha(Path(q))==h for q,h in seals.items()),'input changed')
 out=dict(source);out['objects']=source['objects']+added;out.pop('input_sha256',None);out['parent_sha256']=sha(a.source)
 with a.output.open('w') as f:json.dump(out,f,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
 counts=defaultdict(int)
 for r in results:counts[r['status']]+=1
 rep={'board':source['board'],'input_sha256':seals,'output_sha256':sha(a.output),'method':a.method,'parameters_mm':{'route_widths':list(ROUTE_WIDTHS),'route_pitch':ROUTE_PITCH,'route_half_window':ROUTE_HALF,'via_diameter':VIA_DIAMETER,'via_drill':VIA_DRILL,'trace_width':TRACE_WIDTH,'clearance':CLEARANCE,'hole_clearance':HOLE_CLEARANCE,'grid':GRID,'radius':RADIUS},
      'counts':dict(counts),'results':results,'credited_connections':0,'note':'Placement only. Feed closure is credited solely by the complete census rerun.','elapsed_seconds':round(time.monotonic()-start,2),'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0}
 a.report.write_text(json.dumps(rep,indent=1)+'\n');print(json.dumps({k:rep[k] for k in ['board','counts','elapsed_seconds','peak_KiB']}),flush=True)
 # Outputs are written and sealed; skip freeing ~10^6 GEOS objects, which costs minutes.
 os._exit(0)
if __name__=='__main__':main()
