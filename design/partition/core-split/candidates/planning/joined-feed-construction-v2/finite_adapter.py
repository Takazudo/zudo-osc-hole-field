#!/usr/bin/env python3
"""Fragment-level conforming finite conductor of one E16 board net (E16 adapter, not a field solver).

Built on the exact drilled fragments of the structural graph (fragments.py, verified
identity-by-identity against the retained port graph), so finite coverage cannot
drift from the structural census:

- Only feed-connected fragments carry current. Per layer, fed fragments joined by
  the graph's positive-area edges form one conductor group: the union of those
  fragments, so overlapping pad/segment/annulus/sheet copper is owned once. Members
  that only touch along an edge or at a point are slit apart there (a 2 um cut that
  no other member covers), so, as in the graph, no tangent contact conducts.
- Each group (or tile of a large group) is meshed by scripts/pcbgen/sheet_mesh.Sheet
  on one globally aligned uniform cell grid: exact clipped copper area and conforming
  P1 triangles. Tile meshes conform along their cut lines and merge by coordinate
  within the same group only. The geometric stiffness is stored at unit sheet
  resistance, so a process case only rescales it by t/rho.
- A barrel (via or plated pad) taps every layer where a fed fragment touches its
  wall band. At each tap the mesh vertices on the drilled hole boundary form one
  ring node (finite support along the bore; angular barrel resistance omitted).
  Consecutive taps are joined once by the annular barrel interval between their
  declared layer depths, so an axial interval is shared by every current using it.
- Pads and feed terminals are finite area supports with uniform current density
  over their fed face fragments, represented by the consistent finite-element load
  vector (basis functions of elements overlapping the pad). A held source land fixes
  only the mesh nodes lying inside its copper, so the held region never exceeds it.
No ideal edge joins two conductors; nothing is snapped to a nearest endpoint.
"""
import math,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import shapely
from shapely.geometry import box
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts.pcbgen.sheet_mesh import Sheet,make_cells
FACES=('F.Cu','B.Cu')
ORDER=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
SCALE=10**9           # vertex identity: coordinates on Sheet's 1e-9 mm grid
SLIT_MM=1e-6          # half-width of the cut separating tangent-only contacts
def need(c,m):
 if not c:raise ValueError(m)
def layer_z(depth):
 """Foil-centre depth (mm) of each layer in a declared conditional stack."""
 t=depth['foil_mm'];gaps=depth['dielectric_mm'];need(len(gaps)==5,'six-layer stack needs five dielectrics')
 z={};top=0.
 for k,l in enumerate(ORDER):
  z[l]=top+t/2;top+=t+(gaps[k] if k<5 else 0)
 need(abs(top-depth['board_mm'])<1e-9,'declared stack does not sum to the board thickness')
 return z
def barrel_interval_ohm(rho,length,drill,plating):
 r=drill/2;return rho*length/(math.pi*((r+plating)**2-r**2))

def conductor_groups(frag):
 """Fed fragments joined by positive-area same-layer edges; returns list of member lists."""
 fed=set(frag.fed);parent={i:i for i in fed}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,j in frag.edges:
  if i in fed and j in fed:parent[root(i)]=root(j)
 members=defaultdict(list)
 for i in sorted(fed):members[root(i)].append(i)
 return sorted(members.values())
def tangent_slits(frag,ms):
 """Cuts along every tangent-only contact between two members that no third member covers."""
 geoms=[frag.nodes[i] for i in ms];tree=shapely.STRtree(geoms);cuts=[];pairs=0
 for a,ga in enumerate(geoms):
  for b in map(int,tree.query(ga)):
   if b<=a:continue
   gb=geoms[b]
   if not shapely.intersects(ga,gb) or shapely.covers(ga,gb) or shapely.covers(gb,ga) or ga.intersection(gb).area>1e-10:continue
   slit=ga.intersection(gb).buffer(SLIT_MM,quad_segs=2)
   others=[geoms[k] for k in map(int,tree.query(slit)) if k not in (a,b)]
   if others:slit=slit.difference(shapely.union_all(others))
   if not slit.is_empty:cuts.append(slit);pairs+=1
 return cuts,pairs
def describe(frag):
 """Serializable group/barrel/support description of one verified net (no mesh yet)."""
 groups=conductor_groups(frag);group_of={i:g for g,ms in enumerate(groups) for i in ms};out=[];coppers=[]
 for g,ms in enumerate(groups):
  layer=frag.layer[ms[0]];need(all(frag.layer[i]==layer for i in ms),'group spans layers')
  whole=shapely.union_all([frag.nodes[i] for i in ms]);cuts,pairs=tangent_slits(frag,ms)
  copper=whole.difference(shapely.union_all(cuts)) if cuts else whole
  need(copper.geom_type=='Polygon' and copper.is_valid,'conductor group is not one valid polygon after tangent slits: '+frag.ids[ms[0]])
  coppers.append(copper)
  out.append({'group':g,'layer':layer,'fragments':[frag.ids[i] for i in ms],'wkb':shapely.to_wkb(copper,hex=True),'area_mm2':copper.area,
              'tangent_slits':pairs,'slit_area_mm2':whole.area-copper.area})
 barrels={}
 for bid,mem in sorted(frag.barrels.items()):
  o=frag.objects[bid];taps=sorted({(frag.layer[i],group_of[i]) for i in mem if i in group_of})
  if taps:barrels[bid]={'center_mm':o['center_mm'],'drill_mm':o['drill_mm'],'taps':[{'layer':l,'group':g} for l,g in taps]}
 supports={}
 for identity in sorted(frag.portnodes):
  o=frag.objects.get(identity)
  if not o or o['kind']!='pad':continue
  fed=[i for i in frag.portnodes[identity] if i in group_of];face=[i for i in fed if frag.layer[i] in FACES] or fed
  supports[identity]=[{'fragment':frag.ids[i],'group':group_of[i],'wkb':shapely.to_wkb(frag.nodes[i],hex=True),'area_mm2':frag.nodes[i].area,
                        'copper_area_mm2':frag.nodes[i].intersection(coppers[group_of[i]]).area} for i in face]
  need(all(f['copper_area_mm2']>1e-12 for f in supports[identity]),'support fragment has no copper after slits: '+identity)
 ledger={identity:[{'fragment':frag.ids[i],'layer':frag.layer[i],'fed':i in group_of,'group':group_of.get(i),'area_mm2':frag.nodes[i].area} for i in frag.portnodes[identity]]
         for identity in sorted(frag.portnodes) if identity in frag.objects and frag.objects[identity]['kind']=='pad'}
 return {'groups':out,'barrels':barrels,'supports':supports,'fragment_ledger':ledger,'terminals':frag.terminals}

def tiles(desc,pitch,tile_mm,origin=(0.,0.)):
 """Mesh work items (group, tile box). Tiles are aligned to the global cell grid."""
 items=[]
 for g in desc['groups']:
  poly=shapely.from_wkb(g['wkb']);x0,y0,x1,y1=poly.bounds
  if max(x1-x0,y1-y0)<=tile_mm:items.append((g['group'],None));continue
  need(tile_mm%pitch<1e-9 or abs(tile_mm%pitch-pitch)<1e-9,'tile must be a whole number of cells')
  ox,oy=origin
  for i in range(math.floor((x0-ox)/tile_mm),math.ceil((x1-ox)/tile_mm)):
   for j in range(math.floor((y0-oy)/tile_mm),math.ceil((y1-oy)/tile_mm)):
    tb=(ox+i*tile_mm,oy+j*tile_mm,ox+(i+1)*tile_mm,oy+(j+1)*tile_mm)
    if poly.intersects(box(*tb)) and poly.intersection(box(*tb)).area>1e-12:items.append((g['group'],tb))
 return items
def supports_by_group(desc):
 out={}
 for identity,frags in desc['supports'].items():
  for f in frags:out.setdefault(f['group'],[]).append((identity,f))
 return out
def mesh_item(desc,group,tile,pitch,face_pitch,origin=(0.,0.),by_group=None):
 """Mesh one (group, tile) at unit sheet resistance; supports for pad fragments in untiled face groups."""
 g=desc['groups'][group];poly=shapely.from_wkb(g['wkb'])
 copper=poly if tile is None else poly.intersection(box(*tile))
 if copper.geom_type=='GeometryCollection':copper=shapely.union_all([p for p in shapely.get_parts(copper) if p.geom_type=='Polygon'])
 p=face_pitch if g['layer'] in FACES else pitch
 by_group=supports_by_group(desc) if by_group is None else by_group;pieces=[]
 for identity,f in by_group.get(group,[]):
  whole=shapely.from_wkb(f['wkb']);piece=whole.intersection(copper)
  piece=shapely.union_all([q for q in shapely.get_parts(piece) if q.geom_type=='Polygon' and q.area>1e-12]) if not piece.is_empty else piece
  if piece.area>1e-12:pieces.append((identity,f,whole,piece))
 sheet=Sheet(copper,make_cells(copper.bounds,p,p,origin=origin),1.)
 m=sheet.matrix.tocoo();onb=np.zeros(len(sheet.xy),bool);onb[sheet.boundary_edges.ravel()]=True
 out={'group':group,'tile':tile,'xy':np.asarray(sheet.xy),'row':m.row,'col':m.col,'val':m.data,'boundary':onb,'area_mm2':copper.area,
      'area_error_mm2':sheet.area_error_mm2,'triangles':len(sheet.triangles),'supports':{}}
 # A support fragment cut by tiles or slits contributes each piece in proportion to its copper area.
 for identity,f,whole,piece in pieces:
  w=sheet.area_load(piece)*(piece.area/f['copper_area_mm2']);nz=np.flatnonzero(w)
  out['supports'].setdefault(identity,[]).append((f['fragment'],nz,w[nz]))
 return out

class Assembly:
 """Merged conforming operator of one board net; geometry only, process applied by matrix()."""
 def __init__(self,desc,items):
  self.desc=desc;layer={g['group']:g['layer'] for g in desc['groups']}
  keys=[];offs=[];n=0
  for it in items:
   xy=np.rint(it['xy']*SCALE).astype(np.int64);keys.append(np.column_stack((np.full(len(xy),it['group'],np.int64),xy)));offs.append(n);n+=len(xy)
  allkeys=np.concatenate(keys);uniq,inv=np.unique(allkeys,axis=0,return_inverse=True);inv=inv.ravel()
  # Boundary flag: a boundary vertex in any tile (tile-cut vertices included); ring detection
  # additionally requires the bore annulus window below, which tile cuts cannot satisfy off-bore.
  self.xy=uniq[:,1:].astype(float)/SCALE;self.group=uniq[:,0];vertex=inv
  bnd=np.zeros(len(uniq),bool)
  for it,o in zip(items,offs):bnd[vertex[o:o+len(it['xy'])][it['boundary']]]=True
  # Rings: each barrel tap merges the group's bore-boundary vertices into one node.
  node=np.arange(len(uniq));self.rings={};extra=len(uniq);order={}
  for bid,b in desc['barrels'].items():
   r=b['drill_mm']/2;c=np.asarray(b['center_mm'])
   for tap in b['taps']:
    sel=np.flatnonzero(self.group==tap['group'])
    d=np.linalg.norm(self.xy[sel]-c,axis=1);on=sel[(d>=r-1e-6)&(d<=r/math.cos(math.pi/128)+1e-6)&bnd[sel]]
    need(len(on)>=3,f'barrel {bid} has no bore-boundary support on {tap["layer"]}')
    need((node[on]==on).all(),f'barrel {bid} shares bore-boundary vertices with another barrel on {tap["layer"]} (coaxial bores are not modelled)')
    node[on]=extra;self.rings[bid,tap['layer']]=extra;extra+=1
  used,compact=np.unique(node,return_inverse=True);compact=compact.ravel();self.N=len(used)
  self.rings={k:int(np.searchsorted(used,v)) for k,v in self.rings.items()}
  self.vertex_node=compact
  # Geometric stiffness split by foil class.
  self.Kg={}
  for cls in ('face','inner'):
   rr,cc,vv=[],[],[]
   for it,o in zip(items,offs):
    if (layer[it['group']] in FACES)!=(cls=='face'):continue
    rr.append(compact[vertex[o+it['row']]]);cc.append(compact[vertex[o+it['col']]]);vv.append(it['val'])
   self.Kg[cls]=sp.csr_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(self.N,self.N)) if vv else sp.csr_matrix((self.N,self.N))
  # Supports: uniform current density over each pad's fed face fragments.
  self.supports={}
  area={k:{f['fragment']:f['copper_area_mm2'] for f in fs} for k,fs in desc['supports'].items()}
  for it,o in zip(items,offs):
   for identity,parts in it['supports'].items():
    acc=self.supports.setdefault(identity,defaultdict(float));total=sum(area[identity].values())
    for frag,nz,w in parts:
     for v,x in zip(compact[vertex[o+nz]],w*area[identity][frag]/total):acc[int(v)]+=x
  self.supports={k:(np.fromiter(v,int),np.fromiter(v.values(),float)) for k,v in self.supports.items()}
  for k,(nodes,w) in self.supports.items():need(abs(w.sum()-1)<1e-9 and (w>=-1e-12).all(),'support is not a partition of unity: '+k)
  # Node coordinates (ring nodes have none) and, per support, which of its nodes lie inside its copper.
  self.node_xy=np.full((self.N,2),np.nan);ring=np.zeros(self.N,bool);ring[list(self.rings.values())]=True
  plain=~ring[self.vertex_node];self.node_xy[self.vertex_node[plain]]=self.xy[plain]
  self.support_inside={}
  for k,(nodes,w) in self.supports.items():
   patch=shapely.union_all([shapely.from_wkb(f['wkb']) for f in desc['supports'][k]]).buffer(1e-7)
   xy=self.node_xy[nodes];ok=~np.isnan(xy[:,0]);inside=np.zeros(len(nodes),bool)
   inside[ok]=shapely.contains_xy(patch,xy[ok,0],xy[ok,1]);self.support_inside[k]=inside
  self.receipts={'vertices':int(len(uniq)),'nodes':int(self.N),'ring_nodes':len(self.rings),'tiles':len(items),
                 'triangles':int(sum(it['triangles'] for it in items)),'area_mm2':float(sum(it['area_mm2'] for it in items)),
                 'area_error_mm2':float(sum(abs(it['area_error_mm2']) for it in items))}
 def matrix(self,case,depth):
  return laplacian(self.Kg['face'],self.Kg['inner'],self.desc['barrels'],self.rings,case,depth)
def laplacian(Kg_face,Kg_inner,barrels,rings,case,depth):
 """Laplacian (siemens) for one process case and declared stack; returns (K, barrel interval records)."""
 rho=case['rho_ohm_mm'];K=Kg_face*(case['outer_copper_mm']/rho)+Kg_inner*(case['inner_copper_mm']/rho)
 z=layer_z(depth);rows,cols,vals=[],[],[];records=[]
 for bid,b in barrels.items():
  taps=sorted((z[t['layer']],t['layer']) for t in b['taps'])
  for (za,la),(zb,lb) in zip(taps,taps[1:]):
   length=depth.get('legacy_leg_mm') or zb-za
   R=barrel_interval_ohm(rho,length,b['drill_mm'],case['barrel_plating_mm']);a,c=rings[bid,la],rings[bid,lb]
   rows+=[a,c,a,c];cols+=[a,c,c,a];vals+=[1/R,1/R,-1/R,-1/R];records.append((bid,la,lb,length,R))
 Kb=sp.csr_matrix((vals,(rows,cols)),shape=K.shape)
 return (K+Kb).tocsr(),Kb.tocsr(),records
