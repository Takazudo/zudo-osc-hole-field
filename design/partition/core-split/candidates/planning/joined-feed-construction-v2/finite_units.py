#!/usr/bin/env python3
"""Bounded units of the E16 finite adapter: one process each, <=2 GiB address space.

  split     all-net clipped sheets -> one file per net (the 100 MB input is read once)
  describe  verified fragments -> conductor groups, barrels, supports, fragment ledger
  mesh      a contiguous range of (group, tile) items -> conforming unit-resistance stiffness
  assemble  merged operator + per-pad/per-fragment finite coverage ledger

Every unit binds the SHA-256 of what it reads. run_finite_e16.py sequences them.
"""
import argparse,gzip,hashlib,json,os,pickle,resource,sys,time
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(_v,'1')
from pathlib import Path
import numpy as np
import scipy.sparse as sp
HERE=Path(__file__).resolve().parent
NETS=['+12V','-12V','+5V','AGND']
LIMIT=2*1024**3
VERTEX_BUDGET=300_000      # per mesh unit, in vertex-equivalents; measured 110-280 us per Sheet vertex (KA-KB)
ITEM_COST=600              # vertex-equivalents per (group, tile) item: Sheet set-up and support loads
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jload(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def jsave(p,d):Path(p).write_bytes(gzip.compress(json.dumps(d,sort_keys=True,separators=(',',':')).encode(),mtime=0))
def psave(p,d):Path(p).write_bytes(gzip.compress(pickle.dumps(d,protocol=5),mtime=0))
def pload(p):return pickle.loads(gzip.decompress(Path(p).read_bytes()))
def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
def split(a):
 planes=jload(a.planes);need(not any(Path(a.outdir,f'planes-{n}.json.gz').exists() for n in NETS),'fresh outputs')
 for net in NETS:
  jsave(Path(a.outdir,f'planes-{net}.json.gz'),{'board':planes['board'],'net':net,'new_objects':planes['new_objects'],'clipped_sheets':{net:planes['clipped_sheets'][net]},
        'all_net_planes_sha256':sha(a.planes),'all_net_input_sha256':planes['input_sha256']})
 return {'board':planes['board'],'planes_sha256':sha(a.planes)}
def describe(a):
 import fragments as F,finite_adapter as A
 source,planes,graph,census=jload(a.source),jload(a.planes),jload(a.graph),jload(a.census)
 need(census['graph_sha256']==sha(a.graph),'census does not bind this graph')
 seals=set(graph['input_sha256'].values())
 need(sha(a.source) in seals and planes['all_net_planes_sha256'] in seals,'graph was not built from this source and these clipped sheets')
 need(source['board']==planes['board']==graph['board']==census['board'],'one board')
 frag=F.NetFragments(source,planes,a.net);check=frag.verify(graph);desc=A.describe(frag)
 desc.update(board=source['board'],net=a.net,verified=check,
             bindings={'source':sha(a.source),'planes_all_nets':planes['all_net_planes_sha256'],'planes_net':sha(a.planes),'graph':sha(a.graph),'census':sha(a.census),
                       'methods':{m:sha(HERE/m) for m in ['fragments.py','finite_adapter.py','finite_units.py','connectivity.py','staged_caps.py']}})
 jsave(a.output,desc);return {'board':desc['board'],'net':a.net,'verified':check,'groups':len(desc['groups']),'barrels':len(desc['barrels'])}
def plan(desc,pitch,face_pitch,tile_mm,origin=(0.,0.)):
 """Deterministic item list and contiguous chunks under the vertex budget."""
 import shapely
 from shapely.geometry import box
 import finite_adapter as A
 items=A.tiles(desc,pitch,tile_mm,origin);cost=[]
 polys={g['group']:shapely.from_wkb(g['wkb']) for g in desc['groups']}
 for g,t in items:
  c=polys[g] if t is None else polys[g].intersection(box(*t));p=face_pitch if desc['groups'][g]['layer'] in A.FACES else pitch
  cost.append(shapely.get_num_coordinates(c)*1.3+2*c.area/p**2+ITEM_COST)
 chunks=[];start=0;acc=0.
 for i,c in enumerate(cost):
  need(c<=VERTEX_BUDGET,f'one item exceeds the unit budget ({c:.0f} estimated vertices); reduce the tile size')
  if acc+c>VERTEX_BUDGET:chunks.append((start,i));start=i;acc=0.
  acc+=c
 chunks.append((start,len(items)));return items,chunks,cost
def mesh(a):
 import finite_adapter as A
 desc=jload(a.desc);items,chunks,_=plan(desc,a.pitch,a.face_pitch,a.tile_mm,a.origin);i0,i1=chunks[a.chunk]
 idx=A.supports_by_group(desc);out=[A.mesh_item(desc,g,t,a.pitch,a.face_pitch,a.origin,idx) for g,t in items[i0:i1]]
 psave(a.output,{'desc_sha256':sha(a.desc),'pitch':a.pitch,'face_pitch':a.face_pitch,'tile_mm':a.tile_mm,'origin':a.origin,'chunk':a.chunk,'items':out})
 return {'items':i1-i0,'vertices':int(sum(len(it['xy']) for it in out)),'triangles':int(sum(it['triangles'] for it in out))}
def assemble(a):
 import finite_adapter as A
 desc=jload(a.desc);items=[];h=sha(a.desc)
 for m in a.mesh:
  d=pload(m);need(d['desc_sha256']==h,'mesh chunk from another description');items+=d['items']
 expect,_,_=plan(desc,a.pitch,a.face_pitch,a.tile_mm,a.origin)
 need([(it['group'],it['tile']) for it in items]==[(g,t) for g,t in expect],'mesh chunks do not cover every item exactly once')
 asm=A.Assembly(desc,items);del items
 # Coverage: a pad is finitely covered when its whole support lies in a component holding a feed terminal.
 K,_,_=asm.matrix({'rho_ohm_mm':1.,'outer_copper_mm':1.,'inner_copper_mm':1.,'barrel_plating_mm':.018},{'foil_mm':.07,'dielectric_mm':[.236]*5,'board_mm':1.6})
 ncomp,label=sp.csgraph.connected_components(K,directed=False)
 term={t:set(label[asm.supports[t][0]].tolist()) for t in desc['terminals']}
 source=set().union(*term.values())
 # Every finite component must hold a feed terminal: a floating component would make the board system singular.
 floating=sorted(set(range(ncomp))-source)
 graph=jload(a.graph);census=jload(a.census);unresolved={r['pad_id'] for r in census['unresolved']}
 ports=[p for p in graph['physical_ports'] if p['net']==desc['net']];rows=[];fail=[]
 for p in ports:
  pid=p['id'];frs=desc['fragment_ledger'][pid];obligated=p['all_port_fragments_connected_to_feed']
  sup=asm.supports.get(pid);comps=sorted(set(label[sup[0]].tolist())) if sup else []
  covered=bool(sup) and set(comps)<=source
  row={'pad_id':pid,'ref':p.get('ref'),'pad':p.get('pad'),'terminal':pid.startswith('CS247-'),'obligated':obligated,'structurally_unresolved':pid in unresolved,
       'fragments':frs,'fed_fragments':sum(f['fed'] for f in frs),'support_nodes':int(len(sup[0])) if sup else 0,'finite_components':comps,'finite_path_to_feed':covered}
  if obligated and not covered:fail.append(pid)
  need(obligated==(pid not in unresolved) or pid.startswith('CS247-'),'graph and census disagree on '+pid)
  rows.append(row)
 ops={'Kg_face':asm.Kg['face'],'Kg_inner':asm.Kg['inner'],'rings':asm.rings,'barrels':desc['barrels'],'supports':asm.supports,'terminals':desc['terminals'],
      'support_inside':asm.support_inside,'N':asm.N,'desc_sha256':h,'receipts':asm.receipts,'origin':list(a.origin),'pitch':a.pitch,'face_pitch':a.face_pitch}
 psave(a.operator,ops)
 cov={'board':desc['board'],'net':desc['net'],'desc_sha256':h,'mesh_sha256':{Path(m).name:sha(m) for m in a.mesh},'mesh':asm.receipts,'finite_components':int(ncomp),
      'source_components':sorted(source),'ports':len(ports),'obligated':sum(r['obligated'] for r in rows),'obligated_without_finite_path':fail,
      'terminals_covered':all(r['finite_path_to_feed'] for r in rows if r['terminal']),'floating_finite_components':floating,'rows':rows}
 need(not floating,f'{len(floating)} finite components hold no feed terminal')
 jsave(a.output,cov)
 return {k:cov[k] for k in ['board','net','ports','obligated','finite_components']}|{'missing':len(fail),'nodes':asm.N}
def main(argv=None):
 if argv is None:resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 x=s.add_parser('split');x.add_argument('--planes',required=True);x.add_argument('--outdir',required=True)
 x=s.add_parser('describe')
 for k in ['source','planes','graph','census','output']:x.add_argument('--'+k,required=True)
 x.add_argument('--net',choices=NETS,required=True)
 for name in ('mesh','assemble'):
  x=s.add_parser(name);x.add_argument('--desc',required=True);x.add_argument('--pitch',type=float,default=1.);x.add_argument('--face-pitch',type=float,default=.25);x.add_argument('--tile-mm',type=float,default=24.);x.add_argument('--origin',type=float,nargs=2,default=(0.,0.))
  if name=='mesh':x.add_argument('--chunk',type=int,required=True);x.add_argument('--output',required=True)
  else:
   x.add_argument('--mesh',nargs='+',required=True)
   for k in ['graph','census','operator','output']:x.add_argument('--'+k,required=True)
 x=s.add_parser('plan');x.add_argument('--desc',required=True);x.add_argument('--pitch',type=float,default=1.);x.add_argument('--face-pitch',type=float,default=.25);x.add_argument('--tile-mm',type=float,default=24.);x.add_argument('--origin',type=float,nargs=2,default=(0.,0.));x.add_argument('--output',required=True)
 a=p.parse_args(argv);start=time.monotonic()
 if a.cmd=='plan':
  items,chunks,cost=plan(jload(a.desc),a.pitch,a.face_pitch,a.tile_mm,a.origin);r={'items':len(items),'chunks':chunks,'estimated_vertices':round(sum(cost))}
  Path(a.output).write_text(json.dumps(dict(r,desc_sha256=sha(a.desc),pitch=a.pitch,face_pitch=a.face_pitch,tile_mm=a.tile_mm,origin=list(a.origin)))+'\n')
 else:r={'split':split,'describe':describe,'mesh':mesh,'assemble':assemble}[a.cmd](a)
 r.update(elapsed_seconds=round(time.monotonic()-start,2),peak_KiB=peak());print(json.dumps(r))
if __name__=='__main__':main()
