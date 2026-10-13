#!/usr/bin/env python3
"""Preflight one additive face-copper corridor feeding an orphan same-net component (no construction).

The orphan component is the structurally disconnected fragment component holding the
target pad. A corridor is a face trace that starts on that component's face copper and
ends on feed-connected same-net face copper of the same face, at the E16 access rules:
0.25 (then 0.2) mm width, 0.25 mm clearance to other-net copper, 0.25 mm to every
drill, outside rule areas, inside the declared window. Nothing is drilled, moved,
removed or re-layered. The output is the record to seal and review before the single
construction; it predicts nothing as credited (only a full census credits).
"""
import argparse,gzip,hashlib,heapq,json,math,resource,time
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString
import fragments as F,construct_access as CA
HERE=Path(__file__).resolve().parent;FACES=('F.Cu','B.Cu')
LIMITS={'window_margin_mm':6.,'max_length_mm':12.,'max_segments':10,'pitch_mm':.05,'widths_mm':[.25,.2],'clearance_mm':CA.CLEARANCE,'hole_clearance_mm':CA.HOLE_CLEARANCE,
        'unit_seconds':180,'unit_address_space_GiB':2}
def jl(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(c,m):
 if not c:raise ValueError(m)
def corridor(start,goal,face,net,width,obs,box):
 """Shortest 8-connected legal path from start region to goal region inside box; exact re-validation."""
 cuts=[]
 if face in obs.trees:
  for i in obs.trees[face].query(box):
   if obs.nets[face][int(i)]!=net:cuts.append(obs.geoms[face][int(i)].buffer(width/2+CA.CLEARANCE,quad_segs=8))
 if obs.drill_tree is not None:cuts+=[obs.drills[int(i)].buffer(width/2+CA.HOLE_CLEARANCE,quad_segs=8) for i in obs.drill_tree.query(box)]
 if face in obs.forbid_trees:cuts+=[obs.forbid[face][int(i)] for i in obs.forbid_trees[face].query(box)]
 forbidden=shapely.union_all(cuts) if cuts else shapely.Polygon();shapely.prepare(forbidden)
 x0,y0,x1,y1=box.bounds;p=LIMITS['pitch_mm'];xs=np.arange(x0,x1+1e-9,p);ys=np.arange(y0,y1+1e-9,p);X,Y=np.meshgrid(xs,ys)
 free=~shapely.intersects_xy(forbidden,X,Y)
 s=shapely.contains_xy(start,X,Y)&free;g=shapely.contains_xy(goal,X,Y)&free
 if not s.any():return None,'start_copper_fully_blocked'
 if not g.any():return None,'goal_copper_fully_blocked_in_window'
 h,w=X.shape;dist=np.full(X.shape,np.inf);prev={};heap=[]
 for i,j in zip(*np.nonzero(s)):dist[i,j]=0;heapq.heappush(heap,(0.,i,j))
 steps=[(a,b,math.hypot(a,b)) for a in (-1,0,1) for b in (-1,0,1) if a or b];hit=None
 while heap:
  d,i,j=heapq.heappop(heap)
  if d>dist[i,j]:continue
  if g[i,j]:hit=(i,j);break
  for a,b,c in steps:
   u,v=i+a,j+b
   if 0<=u<h and 0<=v<w and free[u,v] and d+c<dist[u,v]:dist[u,v]=d+c;prev[(u,v)]=(i,j);heapq.heappush(heap,(d+c,u,v))
 if hit is None:return None,'no_clear_path_in_window'
 node=hit;path=[node]
 while node in prev:node=prev[node];path.append(node)
 pts=[(float(X[i,j]),float(Y[i,j])) for i,j in reversed(path)];out=[pts[0]];k=0
 while k<len(pts)-1:
  m=len(pts)-1
  while m>k+1 and LineString([pts[k],pts[m]]).intersects(forbidden):m-=1
  out.append(pts[m]);k=m
 if len(out)<2:out=[pts[0],pts[0]]
 line=LineString(out)
 if line.length>0 and line.intersects(forbidden):return None,'simplification_failed'
 keep,hole=line.buffer(width/2+CA.CLEARANCE,quad_segs=8),line.buffer(width/2+CA.HOLE_CLEARANCE,quad_segs=8)
 if obs.blocked(keep,[face],net,hole):return None,'exact_validation_failed'
 body=line.buffer(width/2,quad_segs=8)
 if not (body.intersection(start).area>1e-6 and body.intersection(goal).area>1e-6):return None,'no_positive_overlap_at_both_ends'
 return out,None
def preflight(source,planes,graph,census,pad_id):
 byid={o['id']:o for o in source['objects']};pad=byid[pad_id];net=pad['net']
 need(any(u['pad_id']==pad_id for u in census['unresolved']),'target is not a t2 residual')
 frag=F.NetFragments(source,planes,net);fed=set(frag.fed)
 roots={frag.root(i) for i in frag.portnodes[pad_id] if i not in fed};need(roots,'target has no orphan fragment')
 comp=[i for i in range(len(frag.nodes)) if frag.root(i) in roots]
 members=sorted({frag.owner[i] for i in comp});pads=sorted({(byid[m].get('ref'),byid[m].get('pad'),m) for m in members if m in byid and byid[m]['kind']=='pad'})
 obs=CA.Obstacles(source['objects']);tried=[];best=None
 for face in FACES:
  mine=[i for i in comp if frag.layer[i]==face];fedf=[i for i in fed if frag.layer[i]==face]
  if not mine:tried.append({'face':face,'reason':'orphan_component_has_no_copper_on_face'});continue
  start=shapely.union_all([frag.nodes[i] for i in mine]);x0,y0,x1,y1=start.bounds;m=LIMITS['window_margin_mm']
  box=shapely.box(x0-m,y0-m,x1+m,y1+m);near=[i for i in fedf if frag.nodes[i].intersects(box)]
  if not near:tried.append({'face':face,'reason':'no_fed_copper_in_window'});continue
  goal=shapely.union_all([frag.nodes[i] for i in near]).intersection(box)
  for width in LIMITS['widths_mm']:
   pts,why=corridor(start,goal,face,net,width,obs,box)
   rec={'face':face,'width_mm':width,'reason':why}
   if pts:
    L=LineString(pts).length;rec.update(reason=None,path_mm=[[round(x,6),round(y,6)] for x,y in pts],length_mm=round(L,6),segments=len(pts)-1)
    if L>LIMITS['max_length_mm'] or len(pts)-1>LIMITS['max_segments']:rec['reason']='exceeds_sealed_limits'
    else:
     a=next(frag.owner[i] for i in mine if frag.nodes[i].distance(shapely.Point(pts[0]))<width);b=min(near,key=lambda i:frag.nodes[i].distance(shapely.Point(pts[-1])))
     rec.update(start_object=a,end_object=frag.owner[b],end_fragment=frag.ids[b])
     if best is None or L<best['length_mm']:best=rec
   tried.append(rec)
   if pts and rec['reason'] is None:break
 return {'board':source['board'],'net':net,'target':{'pad_id':pad_id,'ref':pad.get('ref'),'pad':pad.get('pad')},'orphan_component':{'identities':members,'pads':[{'ref':r,'pad':q,'pad_id':i} for r,q,i in pads],
         'fragments':[frag.ids[i] for i in comp]},'attempts':tried,'proposal':best,'legal':best is not None}
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));start=time.monotonic()
 p=argparse.ArgumentParser()
 for k in ['source','planes','graph','census','pad-id','output']:p.add_argument('--'+k,required=True)
 p.add_argument('--window-margin-mm',type=float,default=LIMITS['window_margin_mm']);p.add_argument('--max-length-mm',type=float,default=LIMITS['max_length_mm'])
 a=p.parse_args();LIMITS.update(window_margin_mm=a.window_margin_mm,max_length_mm=a.max_length_mm);out=preflight(jl(a.source),jl(a.planes),jl(a.graph),jl(a.census),a.pad_id)
 out.update(schema='e16-pilot-preflight-v1',limits=LIMITS,rules='No new drill, moved part, removed copper, changed layer or relaxed clearance; additive face trace only.',
            input_sha256={'source':sha(a.source),'planes_net':sha(a.planes),'graph':sha(a.graph),'census':sha(a.census)},
            method_sha256={m:sha(HERE/m) for m in ['pilot_preflight.py','fragments.py','construct_access.py','connectivity.py']},
            elapsed_seconds=round(time.monotonic()-start,2),peak_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,constructed=False,credited=False)
 Path(a.output).write_text(json.dumps(out,indent=1)+'\n');print(json.dumps({k:out[k] for k in ['board','net','legal','elapsed_seconds','peak_KiB']}|{'proposal':out['proposal'] and {k:out['proposal'][k] for k in ['face','width_mm','length_mm','segments','start_object','end_object']}}))
if __name__=='__main__':main()
