#!/usr/bin/env python3
"""E16 two-face access: pad -> existing same-net through transition -> opposite-face feed.

Kept apart from construct_access.py so the retained r1-r4 method bytes stay
unchanged. Reuses its obstacle model, clearances, via legality and cumulative
sheet-severance guard. A placed route is a proposal; only the complete
cap/clip/graph/census rerun credits a connection.
"""
import argparse,hashlib,json,math,os,resource,time,uuid
from collections import defaultdict
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,Polygon,LineString
from shapely.strtree import STRtree
from construct_access import (LAYERS,NET_LAYER,VIA_DIAMETER,VIA_DRILL,CLEARANCE,HOLE_CLEARANCE,ROUTE_WIDTHS,ROUTE_PITCH,ROUTE_HALF,
                              NS,need,sha,copper,Obstacles,antipad,legal_via_sites)
BARREL_WALL=.025       # connectivity.py declared annular barrel wall
CONTACT_AREA=1e-6
FACES=('F.Cu','B.Cu')
def through(o):return o['kind'] in ('via','pad') and o.get('drill_mm',0)>0 and all(f in o['layers'] for f in FACES)
def annulus(o):
 """Face copper of a plated transition outside its own bore."""
 return copper(o).difference(Point(o['center_mm']).buffer(o['drill_mm']/2,quad_segs=32))
def wall_cut(t,obs,extra):
 """Another bore crossing this transition's declared barrel wall (connectivity.py rejects it)."""
 r=t['drill_mm']/2;c=Point(t['center_mm']);wall=c.buffer(r+BARREL_WALL,quad_segs=32).difference(c.buffer(r,quad_segs=32))
 for o in (obs,extra):
  if o.drill_tree is None:continue
  for i in o.drill_tree.query(wall,predicate='intersects'):
   d=o.drills[int(i)]
   if d.centroid.distance(c)>1e-9:return True
 return False
def face_route(start,center,face,net,width,obs,extra,goal,sites=(),exempt=None):
 """Shortest 8-connected path on one face from START to GOAL copper or a via site.

 EXEMPT is the one same-net transition whose own bore the path may enter, as a
 track ending on its via/through-hole does; every other drill keeps hole clearance."""
 cx,cy=center;box=shapely.box(cx-ROUTE_HALF,cy-ROUTE_HALF,cx+ROUTE_HALF,cy+ROUTE_HALF)
 goal=list(goal)+[Point(q).buffer(ROUTE_PITCH/4) for q in sites]
 if not goal:return None,'no_target_in_window'
 own=None if exempt is None else Point(exempt['center_mm'])
 cuts=[]
 for o in (obs,extra):
  if face in o.trees:
   for i in o.trees[face].query(box):
    if o.nets[face][int(i)]!=net:cuts.append(o.geoms[face][int(i)].buffer(width/2+CLEARANCE,quad_segs=8))
  if o.drill_tree is not None:
   cuts+=[o.drills[int(i)].buffer(width/2+HOLE_CLEARANCE,quad_segs=8) for i in o.drill_tree.query(box) if own is None or o.drills[int(i)].centroid.distance(own)>1e-9]
  if face in o.forbid_trees:cuts+=[o.forbid[face][int(i)] for i in o.forbid_trees[face].query(box)]
 forbidden=shapely.unary_union(cuts) if cuts else shapely.Polygon();shapely.prepare(forbidden)
 xs=np.arange(cx-ROUTE_HALF,cx+ROUTE_HALF+1e-9,ROUTE_PITCH);ys=np.arange(cy-ROUTE_HALF,cy+ROUTE_HALF+1e-9,ROUTE_PITCH)
 X,Y=np.meshgrid(xs,ys);free=~shapely.contains_xy(forbidden,X,Y)&~shapely.intersects_xy(forbidden,X,Y)
 begin=shapely.contains_xy(start,X,Y)&free;target=shapely.unary_union(goal);end=shapely.contains_xy(target,X,Y)&free
 if not begin.any():return None,'start_blocked'
 if not end.any():return None,'target_blocked'
 import heapq
 h,w=X.shape;dist=np.full(X.shape,np.inf);prev={};heap=[]
 for i,j in zip(*np.nonzero(begin)):dist[i,j]=0;heapq.heappush(heap,(0.,i,j))
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
 out=[pts[0]];k=0
 while k<len(pts)-1:
  m=len(pts)-1
  while m>k+1 and LineString([pts[k],pts[m]]).intersects(forbidden):m-=1
  out.append(pts[m]);k=m
 line=LineString(out) if len(out)>1 else None
 if line is None or line.intersects(forbidden):return None,'simplification_failed'
 if site is None and not line.buffer(width/2).intersection(target).area>CONTACT_AREA:return None,'no_positive_target_overlap'
 return (out,site,line),None
def exact_reject(pad,t,width,legs,obs,extra,net):
 """Exact positive contact and clearance of a candidate route, or the rejection reason."""
 ring={f:annulus(t) for f in FACES}
 for i,(line,f) in enumerate(legs):
  if line is None:continue
  b=line.buffer(width/2)
  if not b.intersection(ring[f]).area>CONTACT_AREA:return 'no_transition_contact'
  if i==0 and not b.intersection(Polygon(pad['polygon_mm'])).area>CONTACT_AREA:return 'no_pad_contact'
  keep,hole=line.buffer(width/2+CLEARANCE,quad_segs=8),line.buffer(width/2+HOLE_CLEARANCE,quad_segs=8)
  if obs.blocked(keep,[f],net) or extra.blocked(keep,[f],net):return 'exact_copper_clearance'
  for o in (obs,extra):
   if o.drill_tree is not None and any(o.drills[int(k)].centroid.distance(Point(t['center_mm']))>1e-9 for k in o.drill_tree.query(hole,predicate='intersects')):return 'foreign_drill_clearance'
 return None
def two_face_access(source,graph,census,planes,only=None,use_fed=False):
 """Pad -> existing same-net through transition -> feed copper or new via on the opposite face.

 Each leg is a face route. The transition must be a same-net plated via or
 through-hole that touches both faces with an intact barrel wall; both legs need
 positive-area contact with its copper outside the bore. Only the full census
 rerun credits a connection."""
 objs=source['objects'];byid={o['id']:o for o in objs};conn=graph['object_connections']
 fed=lambda o:conn.get(o['id'],{}).get('all_fragments_connected_to_feed')
 sheets={}
 for net,rows in planes['clipped_sheets'].items():
  polys=[Polygon(p['polygon_mm'],p['holes_mm']) for p in rows if conn.get(p['id'],{}).get('all_fragments_connected_to_feed')]
  shapely.prepare(polys);sheets[net]=(STRtree(polys),polys) if polys else None
 feed=defaultdict(list)
 for o in objs:
  if o.get('net') in NET_LAYER and o['kind'] in ('pad','segment','via') and fed(o):
   for l in o['layers']:
    if l in FACES:feed[(o['net'],l)].append(copper(o))
 feed_trees={k:STRtree(v) for k,v in feed.items()}
 transitions=defaultdict(list)
 for o in objs:
  if o.get('net') in NET_LAYER and through(o):transitions[o['net']].append(o)
 trans_trees={n:STRtree([Point(t['center_mm']) for t in v]) for n,v in transitions.items()}
 obs=Obstacles(objs);extra=Obstacles([]);added=[];results=[];placed=[];used=set(byid)
 # Bore centres shared by more than one drilled object: the own-bore exemption must not cover a coaxial foreign bore.
 bores=defaultdict(int)
 for o in objs:
  if o.get('drill_mm',0)>0 and 'center_mm' in o:bores[(round(o['center_mm'][0],6),round(o['center_mm'][1],6))]+=1
 for r in census['unresolved']:
  if only is not None and r['pad_id'] not in only:continue
  pad=byid[r['pad_id']];net=pad['net'];face=[l for l in pad['layers'] if l in FACES]
  if pad.get('drill_mm',0)>0 or len(face)!=1:results.append({'pad_id':pad['id'],'status':'SKIP_NOT_SINGLE_FACE_SMD'});continue
  face=face[0];other='B.Cu' if face=='F.Cu' else 'F.Cu';c=Point(pad['center_mm']);reasons=defaultdict(int);found=None
  near=[]
  if net in trans_trees:
   box=shapely.box(c.x-ROUTE_HALF+.5,c.y-ROUTE_HALF+.5,c.x+ROUTE_HALF-.5,c.y+ROUTE_HALF-.5)
   near=sorted((transitions[net][int(i)] for i in trans_trees[net].query(box)),key=lambda t:(round(c.distance(Point(t['center_mm'])),9),t['id']))
  if not near:reasons['no_same_net_transition_in_window']+=1
  for t in near:
   if t['id']==pad['id']:continue
   if fed(t) and not use_fed:reasons['transition_already_feed_connected']+=1;continue
   if bores[(round(t['center_mm'][0],6),round(t['center_mm'][1],6))]>1:reasons['transition_bore_shared']+=1;continue
   if wall_cut(t,obs,extra):reasons['transition_wall_cut']+=1;continue
   ring={f:annulus(t) for f in FACES}
   if any(g.is_empty for g in ring.values()):reasons['transition_without_face_annulus']+=1;continue
   tree=feed_trees.get((net,other));tc=t['center_mm']
   goal=list(tree.geometries.take(tree.query(shapely.box(tc[0]-ROUTE_HALF,tc[1]-ROUTE_HALF,tc[0]+ROUTE_HALF,tc[1]+ROUTE_HALF)))) if tree is not None else []
   for width in ROUTE_WIDTHS:
    if fed(t):
     # The graph already proves this transition feed-connected on every fragment: no opposite leg is added.
     leg1,why=face_route(Polygon(pad['polygon_mm']),pad['center_mm'],face,net,width,obs,extra,[ring[face]],(),t)
     if not leg1:reasons['fed_transition:'+why]+=1;continue
     why=exact_reject(pad,t,width,[(leg1[2],face)],obs,extra,net)
     if why:reasons['fed_transition:'+why]+=1;continue
     found=(t,width,leg1,None);break
    leg2,why=face_route(ring[other],tc,other,net,width,obs,extra,goal,(),t)
    if not leg2:
     sites=legal_via_sites(tc,net,obs,extra,sheets.get(net),sheets,placed)
     leg2,why=face_route(ring[other],tc,other,net,width,obs,extra,[],sites,t) if sites else (None,'no_target_or_via_site')
    if not leg2:reasons['opposite:'+why]+=1;continue
    leg1,why=face_route(Polygon(pad['polygon_mm']),pad['center_mm'],face,net,width,obs,extra,[ring[face]],(),t)
    if not leg1:reasons['pad_face:'+why]+=1;continue
    why=exact_reject(pad,t,width,[(leg1[2],face),(leg2[2],other)],obs,extra,net)
    if why:reasons['exact:'+why]+=1;continue
    found=(t,width,leg1,leg2);break
   if found:break
  if found is None:
   results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'NO_TWO_FACE_ROUTE','reasons':dict(reasons),'transitions_considered':len(near)});continue
  t,width,(p1,_,l1),leg2=found;mode='fed_transition' if leg2 is None else 'two_face'
  p2,site,l2=leg2 if leg2 else ([],None,None)
  contact={'pad':l1.buffer(width/2).intersection(Polygon(pad['polygon_mm'])).area,face:l1.buffer(width/2).intersection(ring[face]).area}
  if l2 is not None:contact[other]=l2.buffer(width/2).intersection(ring[other]).area
  need(all(v>CONTACT_AREA for v in contact.values()),'contact must have positive area at the pad and every used transition face')
  need(exact_reject(pad,t,width,[(l1,face),(l2,other)],obs,extra,net) is None,'exact validation must hold at commit')
  key=f'{source["board"]}:{pad["id"]}:two-face';new=[]
  for leg,(pts,f) in enumerate(((p1,face),(p2,other))):
   if not pts:continue
   for n,(a,b) in enumerate(zip(pts,pts[1:])):
    new.append({'id':str(uuid.uuid5(NS,f'{key}:{leg}:{n}')),'kind':'segment','net':net,'layers':[f],'path_mm':[[round(a[0],6),round(a[1],6)],[round(b[0],6),round(b[1],6)]],
                'width_mm':width,'access_for_pad':pad['id'],'transition_id':t['id'],'epoch':'E16','method':'route_to_fed_transition' if mode=='fed_transition' else 'two_face_route_through_existing_transition'})
  if site is not None:
   new.append({'id':str(uuid.uuid5(NS,key+':via')),'kind':'via','net':net,'layers':list(LAYERS),'center_mm':[round(site[0],6),round(site[1],6)],
               'diameter_mm':VIA_DIAMETER,'drill_mm':VIA_DRILL,'access_for_pad':pad['id'],'epoch':'E16','process':'standard through via','via_in_pad':False,'method':'two_face_route_to_new_via'})
   placed.append((net,antipad(Point(site))))
  for o in new:need(o['id'] not in used,'duplicate object identity '+o['id']);used.add(o['id']);extra.add(o)
  extra.freeze();added+=new
  results.append({'pad_id':pad['id'],'ref':pad['ref'],'pad':pad['pad'],'net':net,'status':'ROUTED_FED_TRANSITION' if mode=='fed_transition' else 'ROUTED_TWO_FACE','width_mm':width,'face':face,'transition':{'id':t['id'],'kind':t['kind'],'ref':t.get('ref'),'pad':t.get('pad'),'center_mm':t['center_mm'],'drill_mm':t['drill_mm']},
                  'leg_lengths_mm':[round(l.length,6) for l in (l1,l2) if l is not None],'contact_area_mm2':{k:round(v,6) for k,v in contact.items()},'new_via':site is not None})
 return added,results
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser()
 for k in ['source','graph','census','planes']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--use-fed-transitions',action='store_true',help='also route onto an already feed-connected same-net through object')
 p.add_argument('--only',type=Path,help='JSON {board: [pad ids]} batch; absent board means every residual');p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists() and not a.report.exists(),'fresh outputs required');start=time.monotonic()
 inputs=[a.source,a.graph,a.census,a.planes,Path(__file__),Path(__file__).with_name('construct_access.py')]+([a.only] if a.only else [])
 seals={str(q.resolve()):sha(q) for q in inputs}
 source,graph,census,planes=[json.loads(q.read_text()) for q in [a.source,a.graph,a.census,a.planes]]
 need(source['board']==graph['board']==census['board']==planes['board'],'one board epoch')
 need(census['graph_sha256']==sha(a.graph),'census must bind this exact graph')
 need(graph['input_sha256'].get(str(a.planes))==sha(a.planes) or sha(a.planes) in graph['input_sha256'].values(),'graph must bind these exact sheets')
 only=None
 if a.only:
  batch=json.loads(a.only.read_text());need(isinstance(batch,dict),'batch is keyed by board');only=set(batch[source['board']]) if source['board'] in batch else None
 added,results=two_face_access(source,graph,census,planes,only,a.use_fed_transitions)
 need(all(sha(Path(q))==h for q,h in seals.items()),'input changed')
 out=dict(source);out['objects']=source['objects']+added;out.pop('input_sha256',None);out['parent_sha256']=sha(a.source)
 with a.output.open('w') as f:json.dump(out,f,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
 counts=defaultdict(int)
 for r in results:counts[r['status']]+=1
 rep={'board':source['board'],'input_sha256':seals,'output_sha256':sha(a.output),'method':'two-face'+('+fed-transition' if a.use_fed_transitions else ''),'batch':sorted(only) if only is not None else 'ALL_RESIDUALS',
      'parameters_mm':{'route_widths':list(ROUTE_WIDTHS),'route_pitch':ROUTE_PITCH,'route_half_window':ROUTE_HALF,'via_diameter':VIA_DIAMETER,'via_drill':VIA_DRILL,'clearance':CLEARANCE,'hole_clearance':HOLE_CLEARANCE,'barrel_wall':BARREL_WALL,'contact_area_mm2':CONTACT_AREA},
      'counts':dict(counts),'results':results,'credited_connections':0,'note':'Placement only. Feed closure is credited solely by the complete census rerun.','elapsed_seconds':round(time.monotonic()-start,2),'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0}
 a.report.write_text(json.dumps(rep,indent=1)+'\n');print(json.dumps({k:rep[k] for k in ['board','counts','elapsed_seconds','peak_KiB']}),flush=True)
 os._exit(0)
if __name__=='__main__':main()
