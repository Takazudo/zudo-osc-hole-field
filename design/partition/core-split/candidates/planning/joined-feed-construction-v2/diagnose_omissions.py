#!/usr/bin/env python3
"""Classify every port the 2026-10-13 partial finite model left without a finite path.

The retained finite_network.py builds its raster network without node maps. This
re-runs the same construction (finite_network.build is wrapped, not edited) while
recording which object/cell each node is, then must reproduce the retained
omission list exactly before classifying. Classes, with witnesses:

  WHOLE_OBJECT_FILTER      the port is not reachable even through every structurally
                           connected fragment once objects that are not wholly
                           feed-connected are dropped (the model's identity filter)
  BARREL_WITHOUT_SHEET_CELL a through object on the port's island has no raster cell
                           within reach in the sheet piece containing its centre
  SUB_PITCH_SHEET_NECK     the island's barrels attach to raster cells cut off from
                           the fed raster by necks narrower than one cell
  OTHER                    none of the above (reported with its island)
"""
import argparse,gzip,json,math,resource,sys
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import shapely
from shapely.geometry import Point,Polygon
from shapely.strtree import STRtree
import finite_network as fn,fragments as F
def need(c,m):
 if not c:raise ValueError(m)
def jl(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def old_islands(source,planes,graph,net,case,pitch):
 """Component-level replica of finite_network.build: (object, face) nodes, raster components, barrel attachments."""
 conn=graph['object_connections'];fed=lambda i:conn.get(i,{}).get('all_fragments_connected_to_feed')
 polys=[];pid=[];cells={}
 for p in planes['clipped_sheets'][net]:
  if not fed(p['id']):continue
  g=Polygon(p['polygon_mm'],p['holes_mm']);shapely.prepare(g);polys.append(g);pid.append(p['id'])
  x0,y0,x1,y1=g.bounds;xs=np.arange(math.floor(x0/pitch)*pitch+pitch/2,x1,pitch);ys=np.arange(math.floor(y0/pitch)*pitch+pitch/2,y1,pitch)
  X,Y=np.meshgrid(xs,ys);X,Y=X.ravel(),Y.ravel();cand=np.nonzero(shapely.contains_xy(g,X,Y))[0]
  for k in range(0,len(cand),20000):
   c=cand[k:k+20000];ins=c[shapely.contains(g,shapely.box(X[c]-pitch/2,Y[c]-pitch/2,X[c]+pitch/2,Y[c]+pitch/2))]
   for x,y in zip(X[ins],Y[ins]):
    key=(round(x/pitch-.5),round(y/pitch-.5))
    if key not in cells:cells[key]=len(polys)-1
 keys=list(cells);idx={k:i for i,k in enumerate(keys)};r,c=[],[]
 for (i,j),q in idx.items():
  for d in ((1,0),(0,1)):
   t=idx.get((i+d[0],j+d[1]))
   if t is not None:r.append(q);c.append(t)
 n=len(keys);rlab=sp.csgraph.connected_components(sp.csr_matrix((np.ones(len(r)),(r,c)),shape=(n,n)),directed=False)[1] if n else np.zeros(0,int)
 parent={}
 def root(x):
  parent.setdefault(x,x)
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(x,y):parent[root(x)]=root(y)
 objs=[o for o in source['objects'] if o.get('net')==net and o['kind'] in ('pad','segment','via') and fed(o['id'])]
 for f in fn.FACES:
  sel=[o for o in objs if f in o['layers']];geoms=[]
  for o in sel:
   root(('o',o['id'],f))
   if o['kind']=='segment':geoms.append(shapely.geometry.LineString(o['path_mm']).buffer(o['width_mm']/2,quad_segs=4))
   elif o['kind']=='via':geoms.append(Point(o['center_mm']).buffer(o['diameter_mm']/2,quad_segs=8))
   else:geoms.append(Polygon(o['polygon_mm']))
  tree=STRtree(geoms)
  for i,g in enumerate(geoms):
   for j in tree.query(g,predicate='intersects'):
    j=int(j)
    if j>i and g.intersection(geoms[j]).area>1e-10:union(('o',sel[i]['id'],f),('o',sel[j]['id'],f))
 tree=STRtree(polys) if polys else None;layer=fn.NET_LAYER[net];attach={}
 for o in objs:
  if not (o.get('drill_mm',0)>0 and len(o['layers'])>1):continue
  ends=[('o',o['id'],f) for f in fn.FACES if f in o['layers']];best=None;own=[]
  if layer in o['layers'] and cells:
   x,y=o['center_mm'];own=[int(k) for k in tree.query(Point(x,y)) if polys[int(k)].contains(Point(x,y))]
   reach=(o.get('diameter_mm') or o['drill_mm']+.3)/2+pitch;i0,j0=math.floor(x/pitch),math.floor(y/pitch);span=int(math.ceil(reach/pitch))+1
   for i in range(i0-span,i0+span+1):
    for j in range(j0-span,j0+span+1):
     if (i,j) in cells and cells[(i,j)] in own:
      d=math.hypot((i+.5)*pitch-x,(j+.5)*pitch-y)
      if d<=reach and (best is None or d<best[0]):best=(d,(i,j))
  if best:
   rc=('r',int(rlab[idx[best[1]]]))
   for e in ends:union(e,rc)
  elif len(ends)==2:union(ends[0],ends[1])
  if layer in o['layers'] and cells:attach[o['id']]={'piece':pid[own[0]] if own else None,'raster_component':int(rlab[idx[best[1]]]) if best else None}
 live={root(('o',f'CS247-{source["board"]}-W{w}',f)) for w in fn.WIRES[net] for f in fn.FACES if ('o',f'CS247-{source["board"]}-W{w}',f) in parent}
 port={}
 for o in objs:
  if o['kind']!='pad' or o['id'].startswith('CS247-'):continue
  faces=[f for f in fn.FACES if f in o['layers']]
  if faces:port[o['id']]=root(('o',o['id'],faces[0]))
 alive_rc={x[1] for x in parent if x[0]=='r' and root(x) in live}
 return port,live,attach,rlab,pid,alive_rc,root
def classify(source,planes,graph,census,net,case,pitch,retained_missing):
 frag=F.NetFragments(source,planes,net)
 port,live,attach,rlab,pid,alive_rc,root=old_islands(source,planes,graph,net,case,pitch)
 unresolved={r['pad_id'] for r in census['unresolved']}
 resolved=[p['id'] for p in graph['physical_ports'] if p['net']==net and not p['id'].startswith('CS247-') and p['id'] not in unresolved]
 missing=sorted(p for p in resolved if p not in port or port[p] not in live)
 need(missing==sorted(retained_missing),f'{net}: replica does not reproduce the retained omissions ({len(missing)} vs {len(retained_missing)})')
 allfed={k for k in frag.portnodes if frag.connection(k)['all_fragments_connected_to_feed']}
 adj=defaultdict(set);rep=lambda i:frag.owner[i] in allfed
 for i,j in frag.edges:
  if rep(i) and rep(j):adj[i].add(j);adj[j].add(i)
 for mem in frag.barrels.values():
  for i in mem:
   for j in mem:
    if i!=j and rep(i) and rep(j):adj[i].add(j)
 seen={i for t in frag.terminals for i in frag.portnodes[t]};stack=list(seen)
 while stack:
  x=stack.pop()
  for y in adj[x]:
   if y not in seen:seen.add(y);stack.append(y)
 fedset=set(frag.fed);nbr=defaultdict(set)
 for i,j in frag.edges:nbr[i].add(j);nbr[j].add(i)
 rows=[]
 for p in missing:
  frs=frag.portnodes[p]
  if not any(i in seen for i in frs):
   comp=set();st=list(frs);comp.update(frs)
   while st:
    x=st.pop()
    for y in adj[x]:
     if y not in comp:comp.add(y);st.append(y)
   blockers=sorted({frag.owner[j] for i in comp for j in nbr[i] if j in fedset and not rep(j)})
   rows.append({'pad_id':p,'class':'WHOLE_OBJECT_FILTER','witness':{'partially_fed_identities_adjacent':blockers[:20]}});continue
  isl=port.get(p);bar=[(o,x) for o,x in attach.items() if root(('o',o,'F.Cu'))==isl or root(('o',o,'B.Cu'))==isl]
  nocell=[o for o,x in bar if x['raster_component'] is None]
  dead=[(o,x) for o,x in bar if x['raster_component'] is not None and x['raster_component'] not in alive_rc]
  if nocell:rows.append({'pad_id':p,'class':'BARREL_WITHOUT_SHEET_CELL','witness':{'barrels':nocell[:10],'pieces':sorted({attach[o]['piece'] for o in nocell if attach[o]['piece']})}})
  elif dead:
   pieces=sorted({x['piece'] for _,x in dead});comps=sorted({x['raster_component'] for _,x in dead})
   rows.append({'pad_id':p,'class':'SUB_PITCH_SHEET_NECK','witness':{'barrels':[o for o,_ in dead][:10],'pieces':pieces,'dead_raster_components':comps,
                'dead_component_cells':int(sum(int(np.sum(rlab==c)) for c in comps))}})
  else:rows.append({'pad_id':p,'class':'OTHER','witness':{'barrels_on_island':[o for o,_ in bar][:10]}})
 return rows
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser()
 for k in ['source','planes','graph','census','retained','output']:p.add_argument('--'+k,required=True)
 p.add_argument('--board',required=True);p.add_argument('--net',required=True);p.add_argument('--pitch',type=float,default=.5);a=p.parse_args()
 source,graph,census=jl(a.source),jl(a.graph),jl(a.census);planes=jl(a.planes)
 planes={'board':planes['board'],'new_objects':planes.get('new_objects',[]),'clipped_sheets':{a.net:planes['clipped_sheets'][a.net]}}
 case=jl(HERE/'evidence/e16/process-cases.json')['cases']['nominal-average']
 solved=jl(a.retained)[f'{a.board}|{a.net}|all'];unres={r['pad_id'] for r in census['unresolved']}
 retained=[q['id'] for q in graph['physical_ports'] if q['net']==a.net and not q['id'].startswith('CS247-') and q['id'] not in unres and q['id'] not in solved]
 rows=classify(source,planes,graph,census,a.net,case,a.pitch,retained)
 out={'board':a.board,'net':a.net,'pitch_mm':a.pitch,'reproduced_retained_omissions':len(retained),'classes':dict(Counter(r['class'] for r in rows)),'rows':rows,
      'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 Path(a.output).write_text(json.dumps(out,indent=1)+'\n');print(json.dumps({k:out[k] for k in ['board','net','reproduced_retained_omissions','classes','peak_KiB']}))
HERE=Path(__file__).resolve().parent
if __name__=='__main__':main()
