#!/usr/bin/env python3
"""Exact atlas of every structurally unresolved rail pad of one board at a replayed round.

Per residual: net, direct/supplemental/DNP class, its disconnected fragment components
and every member identity of those components (the orphan component), existing
same-net transitions in it, the nearest fed same-net copper on each face and on the
net's sheet layer with the shortest straight corridor to it, the other-net copper and
drills obstructing that corridor at the access rules, and the r4/t2 rejection reasons.
A straight-corridor obstruction is a local witness, not a routing impossibility.
"""
import argparse,gc,gzip,json,resource
from collections import defaultdict
from pathlib import Path
import shapely
from shapely.geometry import Point
from shapely.strtree import STRtree
import fragments as F,construct_access as CA
HERE=Path(__file__).resolve().parent
FACES=('F.Cu','B.Cu');NETS=['+12V','-12V','+5V','AGND']
def jl(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def need(c,m):
 if not c:raise ValueError(m)
def atlas(board,source,planes_dir,graph,census,reports,ledger):
 objs=source['objects'];byid={o['id']:o for o in objs}
 obs=CA.Obstacles(objs);status={}
 # Obstacles stores copper per layer in object order; this index names each stored shape.
 layer_ids={l:[o['id'] for o in objs if o['kind']!='rule_area' and CA.copper(o) is not None and l in o['layers']] for l in FACES}
 for r in ledger['records']:
  if r['scenario_id']=='normal-typ-v1' and r['board']==board:status[r['pad_id']]=r['mapping_status']
 rows=[]
 for net in NETS:
  frag=F.NetFragments(source,jl(Path(planes_dir)/f'planes-{net}.json.gz'),net);fed=set(frag.fed)
  comp=defaultdict(list)
  for i in range(len(frag.nodes)):comp[frag.root(i)].append(i)
  fedgeom={l:[frag.nodes[i] for i in fed if frag.layer[i]==l] for l in FACES+(F.NET_LAYER[net],)}
  trees={l:STRtree(g) if g else None for l,g in fedgeom.items()}
  for u in census['unresolved']:
   if u['net']!=net:continue
   pid=u['pad_id'];pad=byid[pid];roots={frag.root(i) for i in frag.portnodes[pid] if i not in fed}
   members=sorted({frag.owner[i] for r in roots for i in comp[r]})
   pads=[{'pad_id':m,'ref':byid[m].get('ref'),'pad':byid[m].get('pad')} for m in members if m in byid and byid[m]['kind']=='pad']
   trans=[m for m in members if m in byid and CA.LAYERS[0] in byid[m]['layers'] and byid[m].get('drill_mm',0)>0]
   targets={}
   for l,tree in trees.items():
    mine=[frag.nodes[i] for r in roots for i in comp[r] if frag.layer[i]==l]
    if not mine or tree is None:targets[l]=None;continue
    g=shapely.union_all(mine);k=int(tree.nearest(g));tgt=fedgeom[l][k];line=shapely.shortest_line(g,tgt);d=float(line.length)
    rec={'distance_mm':round(d,4),'from_mm':[round(c,4) for c in line.coords[0]],'to_mm':[round(c,4) for c in line.coords[-1]]}
    if l in FACES and d>0:
     corridor=line.buffer(CA.TRACE_WIDTH/2+CA.CLEARANCE,quad_segs=8);hole=line.buffer(CA.TRACE_WIDTH/2+CA.HOLE_CLEARANCE,quad_segs=8);blk=set()
     for i in obs.trees[l].query(corridor,predicate='intersects') if l in obs.trees else []:
      if obs.nets[l][int(i)]!=net:blk.add(int(i))
     rec['obstructing_copper']=sorted({layer_ids[l][i] for i in blk})[:12];rec['obstructing_copper_count']=len(blk)
     rec['obstructing_drills']=int(len(obs.drill_tree.query(hole,predicate='intersects'))) if obs.drill_tree is not None else 0
    targets[l]=rec
   rows.append({'board':board,'net':net,'pad_id':pid,'ref':pad.get('ref'),'pad':pad.get('pad'),'layers':pad['layers'],'direct_load':u['direct_load'],
                'ledger_class':status.get(pid),'component_ids':u['component_ids'],'orphan_component_identities':members,'orphan_component_pads':pads,
                'existing_transitions':trans,'nearest_fed':targets,
                'rejection':{r:reports[r].get(pid) for r in reports}})
  del frag,comp,fedgeom,trees;gc.collect()
 return rows
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--board',required=True);p.add_argument('--source',required=True);p.add_argument('--planes-dir',required=True)
 p.add_argument('--graph',required=True);p.add_argument('--census',required=True);p.add_argument('--ledger',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 source,graph,census,ledger=jl(a.source),jl(a.graph),jl(a.census),jl(a.ledger)
 reports={r:{x['pad_id']:x.get('reasons',x['status']) for x in jl(HERE/f'evidence/e16/{a.board}-access-{r}-report.json.gz')['results']} for r in ('r4','t2')}
 rows=atlas(a.board,source,a.planes_dir,graph,census,reports,ledger);need(len(rows)==len(census['unresolved']),'every residual in the atlas')
 out={'schema':'e16-residual-atlas-v1','board':a.board,'round':'t2','residuals':len(rows),'by_net':{n:sum(r['net']==n for r in rows) for n in NETS},
      'direct':sum(r['direct_load'] for r in rows),'rows':rows,'limits':'Straight shortest corridors and their obstructions are local witnesses at the access rules (0.25 mm trace, 0.25 mm copper and hole clearance); a blocked straight corridor does not prove that no routed corridor exists.',
      'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 Path(a.output).write_bytes(gzip.compress(json.dumps(out,sort_keys=True).encode(),mtime=0));print(json.dumps({k:out[k] for k in ['board','residuals','by_net','direct','peak_KiB']}))
if __name__=='__main__':main()
