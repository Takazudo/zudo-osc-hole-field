#!/usr/bin/env python3
"""Conditional finite resistive network of one E16 board net on its actual source copper.

Begins the candidate-specific #247 network; it is not an electrical proof and
neither an upper nor a lower bound: ideal joins lower resistance, while
full-thickness barrel legs and dropped sub-pitch necks raise it.
Nodes: inner-sheet raster cells, face pads, segment ends, via/through-hole
layer nodes, terminal pads and one far-end node per feed. Each sheet cell edge,
segment and barrel leg is one resistor, so no copper is shared between two
elements; barrel legs are deliberately overcharged at full board thickness.
Unresolved ports and every idealization are reported, not hidden.

Process inputs are parameters (process_cases.json), not guaranteed bounds:
18 um is the published AVERAGE hole plating, not a minimum.
"""
import argparse,hashlib,json,math,os,resource,time
# One BLAS thread: per-thread arenas otherwise exhaust the 2 GiB address-space bound.
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(_v,'1')
from collections import defaultdict
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import shapely
from shapely.geometry import Point,Polygon,LineString
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent
NET_LAYER={'AGND':'In1.Cu','+5V':'In2.Cu','-12V':'In3.Cu','+12V':'In4.Cu'}
FACES=('F.Cu','B.Cu')
WIRES={'+12V':[1],'-12V':[2],'+5V':[3],'AGND':[4,5,6]}
BOARD_THICKNESS=1.6    # design/boards/osc-core.json thickness_mm; dielectric z-positions are not recorded
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def barrel_ohm(rho,length,drill,plating):
 r=drill/2;return rho*length/(math.pi*((r+plating)**2-r**2))
def build(source,planes,graph,net,case,pitch,removed=()):
 """Return (Laplacian G, port index map, metadata). Node 0..n-1."""
 rho=case['rho_ohm_mm'];t_in=case['inner_copper_mm'];t_out=case['outer_copper_mm'];plate=case['barrel_plating_mm']
 conn=graph['object_connections'];fed=lambda i:conn.get(i,{}).get('all_fragments_connected_to_feed')
 rows,cols,vals=[],[],[];n=[0]
 def node():n[0]+=1;return n[0]-1
 def R(a,b,ohm):
  need(ohm>0 and math.isfinite(ohm),'positive finite resistor');g=1/ohm;rows.extend([a,b,a,b]);cols.extend([a,b,b,a]);vals.extend([g,g,-g,-g])
 meta={'sheet_cells':0,'sheet_pieces':0,'segments':0,'barrel_legs':0,'pads':0,'idealizations':[]}
 # Inner sheet: square cells wholly inside a feed-connected sheet piece; 4-neighbour sheet resistors.
 layer=NET_LAYER[net];cells={};polys=[];piece_of={}
 for p in planes['clipped_sheets'][net]:
  if not fed(p['id']):continue
  g=Polygon(p['polygon_mm'],p['holes_mm']);shapely.prepare(g);polys.append(g);meta['sheet_pieces']+=1
  x0,y0,x1,y1=g.bounds;xs=np.arange(math.floor(x0/pitch)*pitch+pitch/2,x1,pitch);ys=np.arange(math.floor(y0/pitch)*pitch+pitch/2,y1,pitch)
  X,Y=np.meshgrid(xs,ys);X,Y=X.ravel(),Y.ravel()
  # Cheap centre test first, then the exact whole-cell containment in bounded chunks.
  cand=np.nonzero(shapely.contains_xy(g,X,Y))[0];inside=[]
  for k in range(0,len(cand),20000):
   c=cand[k:k+20000];inside.append(c[shapely.contains(g,shapely.box(X[c]-pitch/2,Y[c]-pitch/2,X[c]+pitch/2,Y[c]+pitch/2))])
  inside=np.concatenate(inside) if inside else np.zeros(0,int)
  for x,y in zip(X[inside],Y[inside]):
   k=(round(x/pitch-.5),round(y/pitch-.5))
   if k not in cells:cells[k]=node();piece_of[k]=len(polys)-1
 for (i,j),a in cells.items():
  for di,dj in ((1,0),(0,1)):
   b=cells.get((i+di,j+dj))
   if b is not None:R(a,b,rho/t_in)
 meta['sheet_cells']=len(cells)
 piece_tree=STRtree(polys) if polys else None
 def cell_near(x,y,reach):
  # Only the sheet piece that actually contains the bore centre may receive the barrel.
  if piece_tree is None:return None
  own={int(k) for k in piece_tree.query(Point(x,y)) if polys[int(k)].contains(Point(x,y))}
  if not own:return None
  i0,j0=math.floor(x/pitch),math.floor(y/pitch);best=None
  span=int(math.ceil(reach/pitch))+1
  for i in range(i0-span,i0+span+1):
   for j in range(j0-span,j0+span+1):
    if (i,j) in cells and piece_of[(i,j)] in own:
     d=math.hypot((i+.5)*pitch-x,(j+.5)*pitch-y)
     if d<=reach and (best is None or d<best[0]):best=(d,cells[(i,j)])
  return best[1] if best else None
 objs=[o for o in source['objects'] if o.get('net')==net and o['kind'] in ('pad','segment','via') and fed(o['id'])]
 face_nodes=defaultdict(dict)       # face -> object id -> node
 shapes={f:[] for f in FACES};owners={f:[] for f in FACES}
 for o in objs:
  for f in FACES:
   if f not in o['layers']:continue
   if o['kind']=='segment':
    a,b=node(),node();L=LineString(o['path_mm']).length
    R(a,b,rho*max(L,1e-6)/(o['width_mm']*t_out));meta['segments']+=1
    face_nodes[f][o['id']]=(a,b)
   else:
    face_nodes[f][o['id']]=(node(),)
    if o['kind']=='pad':meta['pads']+=1
   shapes[f].append(o);owners[f].append(o['id'])
 # Face joins: an overlap between two same-net face objects joins the nearest end nodes (ideal contact).
 joins=0
 for f in FACES:
  geoms=[]
  for o in shapes[f]:
   if o['kind']=='segment':geoms.append(LineString(o['path_mm']).buffer(o['width_mm']/2,quad_segs=4))
   elif o['kind']=='via':geoms.append(Point(o['center_mm']).buffer(o['diameter_mm']/2,quad_segs=8))
   else:geoms.append(Polygon(o['polygon_mm']))
  tree=STRtree(geoms)
  for i,g in enumerate(geoms):
   for j in tree.query(g,predicate='intersects'):
    j=int(j)
    if j<=i or g.intersection(geoms[j]).area<=1e-10:continue
    a,b=shapes[f][i],shapes[f][j];ov=g.intersection(geoms[j]).centroid
    def end(o):
     nodes=face_nodes[f][o['id']]
     if o['kind']!='segment':return nodes[0]
     return nodes[0] if Point(o['path_mm'][0]).distance(ov)<=Point(o['path_mm'][1]).distance(ov) else nodes[1]
    R(end(a),end(b),case['ideal_join_ohm']);joins+=1
 meta['face_joins']=joins
 # Barrels: each through object spans the full board; face -> net sheet -> other face legs.
 unattached=[]
 for o in objs:
  if not (o.get('drill_mm',0)>0 and len(o['layers'])>1):continue
  ends=[face_nodes[f][o['id']][0] for f in FACES if f in o['layers'] and o['id'] in face_nodes[f]]
  mid=None
  if layer in o['layers'] and cells:
   reach=(o.get('diameter_mm') or o['drill_mm']+.3)/2+pitch
   mid=cell_near(*o['center_mm'],reach)
  leg=barrel_ohm(rho,BOARD_THICKNESS,o['drill_mm'],plate)
  if mid is not None:
   for e in ends:R(e,mid,leg);meta['barrel_legs']+=1
  elif len(ends)==2:R(ends[0],ends[1],leg);meta['barrel_legs']+=1
  if mid is None and layer in o['layers'] and cells:unattached.append(o['id'])
 meta['barrels_without_sheet_cell']=len(unattached)
 # Terminals and far-end feed nodes: wire plus termination in series, one per wire identity.
 board=source['board'];far={};wires={}
 for w in WIRES[net]:
  tid=f'CS247-{board}-W{w}';need(any(tid in face_nodes[f] for f in FACES),'terminal pad present '+tid)
  t=next(face_nodes[f][tid][0] for f in FACES if tid in face_nodes[f])
  if w in removed:wires[w]=None;continue
  fn=node();R(t,fn,case['wire_plus_termination_ohm']);wires[w]=fn
 ports={}
 for o in objs:
  if o['kind']!='pad' or o['id'].startswith('CS247-'):continue
  nodes=[face_nodes[f][o['id']][0] for f in FACES if o['id'] in face_nodes[f]]
  if nodes:ports[o['id']]=nodes[0]
 N=n[0];G=sp.csr_matrix((vals,(rows,cols)),shape=(N,N))
 return G,ports,wires,meta
def solve(G,ports,wires,load_ids,batch=16):
 """Ground every live far-end node; unit current into each port. Returns per-port potential and per-wire current."""
 live=[v for v in wires.values() if v is not None];need(live,'at least one live return/feed')
 N=G.shape[0];keep=np.ones(N,bool);keep[live]=False
 # Discard floating islands (not connected to a live far end): they carry no feed current.
 ncomp,label=sp.csgraph.connected_components(G,directed=False)
 alive=set(label[live]);inside=np.isin(label,list(alive));keep&=inside
 idx=-np.ones(N,int);idx[keep]=np.arange(keep.sum())
 A=G[keep][:,keep].tocsc()
 # Symmetric minimum-degree ordering in symmetric mode: COLAMD fill exceeds the 2 GiB bound at 0.5 mm pitch.
 lu=spla.splu(A,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options=dict(SymmetricMode=True))
 out={};wire_ids=[w for w,v in wires.items() if v is not None]
 # Far-end rows: current leaving into a grounded far node is -sum(g_k * v_k) over its kept neighbours.
 rows={}
 for w in wire_ids:
  r=G[wires[w]];k=keep[r.indices];rows[w]=(idx[r.indices[k]],r.data[k])
 todo=[p for p in load_ids if p in ports and inside[ports[p]]];missing=[p for p in load_ids if p not in ports or not inside[ports[p]]]
 for k in range(0,len(todo),batch):
  chunk=todo[k:k+batch];B=np.zeros((A.shape[0],len(chunk)))
  for c,p in enumerate(chunk):B[idx[ports[p]],c]=1.
  X=lu.solve(B)
  for c,p in enumerate(chunk):
   cur={w:float(-(rows[w][1]@X[rows[w][0],c])) for w in wire_ids}
   out[p]={'potential_ohm':float(X[idx[ports[p]],c]),'wire_current_fraction':cur}
 return out,missing
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser()
 for k in ['source','planes','graph','census']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--net',choices=list(NET_LAYER),required=True);p.add_argument('--cases',type=Path,default=HERE/'evidence/e16/process-cases.json')
 p.add_argument('--case',action='append',help='case ids (default: all)');p.add_argument('--pitch',type=float,default=.5);p.add_argument('--faults',action='store_true',help='AGND: also solve every single and double return removal')
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();need(not a.output.exists(),'fresh output');start=time.monotonic()
 seals={str(q.resolve()):sha(q) for q in [a.source,a.planes,a.graph,a.census,a.cases,Path(__file__)]}
 source,graph,census,cases=[json.loads(q.read_text()) for q in [a.source,a.graph,a.census,a.cases]]
 planes=json.loads(a.planes.read_text());planes={'board':planes['board'],'clipped_sheets':{a.net:planes['clipped_sheets'][a.net]}}
 import gc;gc.collect()
 need(source['board']==planes['board']==graph['board']==census['board'],'one board epoch')
 need(census['graph_sha256']==sha(a.graph),'census binds this graph')
 board=source['board'];direct={l['pad_id'] for l in source['loads'] if l['net']==a.net}
 rail_pads=[pp['id'] for pp in graph['physical_ports'] if pp['net']==a.net and not pp['id'].startswith('CS247-')]
 unresolved=sorted(r['pad_id'] for r in census['unresolved'] if r['net']==a.net)
 resolved=[x for x in rail_pads if x not in set(unresolved)]
 states=[()]
 if a.faults and a.net=='AGND':states+=[(w,) for w in WIRES['AGND']]+[(w,v) for i,w in enumerate(WIRES['AGND']) for v in WIRES['AGND'][i+1:]]
 results=[]
 for cid,case in cases['cases'].items():
  if a.case and cid not in a.case:continue
  for removed in states:
   G,ports,wires,meta=build(source,planes,graph,a.net,case,a.pitch,removed)
   sol,missing=solve(G,ports,wires,resolved)
   wire_r=case['wire_plus_termination_ohm']
   worst=max(sol,key=lambda k:sol[k]['potential_ohm']) if sol else None
   maxshare={w:max((v['wire_current_fraction'][w] for v in sol.values()),default=None) for w in wires if wires[w] is not None}
   planning=cases['board_planning_total_A'][board].get(a.net)
   # Unsolved ports carry part of the planning current with unknown Z: no bound then.
   bound=planning*sol[worst]['potential_ohm'] if planning is not None and worst and not missing else None
   results.append({'case':cid,'removed_wires':list(removed),'pitch_mm':a.pitch,'model':meta,'ports_solved':len(sol),'ports_without_finite_path':missing,
                   'max_port_resistance_ohm':sol[worst]['potential_ohm'] if worst else None,'worst_port':worst,
                   'max_port_onboard_resistance_ohm':(sol[worst]['potential_ohm']-wire_r) if worst and len(WIRES[a.net])==1 and not removed else None,
                   'direct_load_max_resistance_ohm':max((sol[k]['potential_ohm'] for k in sol if k in direct),default=None),
                   'max_wire_current_fraction':maxshare,
                   'distribution_free_drop_bound_V':bound,
                   'drop_bound_basis':'|V_j| <= sum|I_i| * max_i Z_ii for this model network grounded at the live far ends (Z_ij <= Z_ii); uses the planning total, which is not a guaranteed maximum; null when any port lacks a finite path; a model figure, not a physical bound',
                   'ports':{k:{'R_ohm':round(v['potential_ohm'],9),'wire_fraction':{w:round(f,6) for w,f in v['wire_current_fraction'].items()}} for k,v in sorted(sol.items())}})
 out={'schema':'e16-finite-network-v1','board':board,'net':a.net,'input_sha256':seals,'status':'CONDITIONAL_PARTIAL_NETWORK_NOT_COMPLIANCE',
      'coverage':{'rail_pads':len(rail_pads),'structurally_unresolved_excluded':unresolved,'direct_loads':len(direct)},
      'results':results,'limits':cases['limits'],'elapsed_seconds':round(time.monotonic()-start,2),'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0,'accepted':False}
 a.output.write_text(json.dumps(out,indent=1)+'\n')
 print(json.dumps({'board':board,'net':a.net,'summary':[{k:r[k] for k in ['case','removed_wires','ports_solved','max_port_resistance_ohm','direct_load_max_resistance_ohm','max_wire_current_fraction','distribution_free_drop_bound_V']}|{'missing':len(r['ports_without_finite_path']),'cells':r['model']['sheet_cells']} for r in results],'elapsed_seconds':out['elapsed_seconds'],'peak_KiB':out['peak_KiB']}))
if __name__=='__main__':main()
