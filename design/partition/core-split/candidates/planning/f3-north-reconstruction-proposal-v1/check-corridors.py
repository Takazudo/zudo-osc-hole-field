#!/usr/bin/env python3
"""One necessary common-corridor check for the five frozen signal components."""
import argparse,gzip,hashlib,importlib.util,json,os,resource,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];OLD=HERE.parent/'f3-rearrangement-v1'
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(r):return ':'.join(map(str,r['source_span']))+':'+r['sha256']
def save(out,name,o):
 b=(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n').encode();p=out/name;t=out/(name+'.tmp');t.write_bytes(gzip.compress(b,mtime=0) if name.endswith('.gz') else b);t.replace(p)
def worker(a):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));started=time.monotonic()
 from shapely.geometry import Point,MultiPoint,shape,Polygon,mapping
 from shapely import affinity
 from shapely.ops import unary_union
 from shapely.strtree import STRtree
 sp=importlib.util.spec_from_file_location('repair',HERE.parents[1]/'pilots/f3-integrator-cluster-v2/repair.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
 assert r.shapely.__version__=='2.1.2' and r.shapely.geos_version_string=='3.13.1'
 seals=read(HERE/'corridor-input-seals.json')
 for p,h in seals.items():assert sha(ROOT/p)==h,p
 assert sha(a.dump)=='2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807'
 original=read(a.dump);index=[json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')];rows,cg,cr,cl,ends=r.load_copper(index,(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text(),original['layers']);keys=[key(x) for x in rows];ki={k:i for i,k in enumerate(keys)}
 selected=read(HERE/'evidence/region-selection.json');release={x['object_key'] for x in selected['selected_objects']};cell=shape(selected['proposal_offset_region']);cx,cy,cz,cw=cell.bounds
 case=read(OLD/'evidence/regions/A24-N-result.json');off=case['base_offsets_mm'];mov=set(case['refs']);data=read(ROOT/'design/partition/core-split/candidates/two.json');board=data['boards']['two-A'];fixedrefs=(set(board['refs'])|set(board['mechanical_refs']))-mov
 compact=read(OLD/'evidence/pad-regions/A24-N-object-dispositions.compact.json.gz');eligible={row[0]:row[3] for row in compact['records'] if row[1]!=0 and row[2]==0};assert len(eligible)==272
 def sweep(g,delta):
  coords=list(g.coords) if g.geom_type in ('Point','LineString') else list(g.exterior.coords)
  return MultiPoint([(x+delta[0]+dx,y+delta[1]+dy) for x,y in coords for dx,dy in [(cx,cy),(cx,cw),(cz,cy),(cz,cw)]]).convex_hull
 obs=[]
 for i,row in enumerate(rows):
  if keys[i] in release:continue
  owners=data['net_owners'].get(row['net_token'],[])
  scope='SHARED_RETAINED' if row['net_token'] in ('AGND','+12V','-12V','+5V') else 'A_OWNED' if 'A' in owners else 'OWNERSHIP_UNKNOWN' if not owners else 'OTHER_BOARD'
  if scope=='OTHER_BOARD':continue
  obs.append({'g':sweep(cg[i],eligible[i]) if i in eligible else cg[i],'radius':cr[i],'layers':cl[i],'net':row['net_token'],'kind':'COPPER','key':keys[i],'scope':scope})
 pads=original['pads']
 for p in pads:
  if p['ref'] not in fixedrefs and p['ref'] not in mov:continue
  g=r.polygon(p);g=sweep(g,off[p['ref']]) if p['ref'] in mov else g
  obs.append({'g':g,'radius':0,'layers':p['layers'],'net':p['net'],'kind':'PAD','key':p['uuid'],'scope':'MOVED_A_PAD_SWEEP' if p['ref'] in mov else 'FIXED_A_PAD','drill':p['drill']})
  if p['drill']:
   q=Point([v/1e6 for v in p['xy']]);q=sweep(q,off[p['ref']]) if p['ref'] in mov else q
   obs.append({'g':q,'radius':p['drill']/2e6,'layers':original['layers'],'net':p['net'],'kind':'DRILL','key':p['uuid'],'scope':'A_DRILL'})
 ot=STRtree([o['g'] for o in obs]);maxrad=max(o['radius'] for o in obs);groups=read(HERE/'evidence/contacts/selected-components.json');groups=[g for g in groups if g['net_token'] not in ('AGND','+12V','-12V','+5V')];assert len(groups)==5 and sum(len(g['selected_keys']) for g in groups)==12
 allcontacts=read(HERE/'evidence/contacts/selected-object-contacts.json.gz');results=[];constraint_count=0;retained_cache={}
 def retained_components(net):
  if net in retained_cache:return retained_cache[net]
  ids=[i for i,row in enumerate(rows) if row['net_token']==net and keys[i] not in release]
  uf={i:i for i in ids};tree=STRtree([cg[i] for i in ids])
  def root(i):
   while uf[i]!=i:uf[i]=uf[uf[i]];i=uf[i]
   return i
  for i in ids:
   for n in tree.query(r.expanded_bounds(cg[i],cr[i]+maxrad+1e-7)):
    j=ids[int(n)]
    if set(cl[i]).intersection(cl[j]) and cg[i].distance(cg[j])<=cr[i]+cr[j]+1e-7:uf[root(j)]=root(i)
  for p in pads:
   if p['net']!=net or p['ref'] not in fixedrefs:continue
   g=r.polygon(p);touch=[]
   for n in tree.query(r.expanded_bounds(g,maxrad+1e-7)):
    i=ids[int(n)]
    if set(p['layers']).intersection(cl[i]) and g.distance(cg[i])<=cr[i]+1e-7:touch.append(i)
   for i in touch[1:]:uf[root(i)]=root(touch[0])
  result={i:root(i) for i in ids};retained_cache[net]=result;return result
 def free_region(outer,rad,layer,net,via):
  nonlocal constraint_count
  allowed=outer.buffer(-rad-.001,quad_segs=32);blocks=[];witness=[]
  for n in ot.query(r.expanded_bounds(outer,maxrad+rad+.251)):
   o=obs[int(n)]
   if layer not in o['layers']:continue
   if o['kind']=='DRILL':exp=o['radius']+rad+.25+.001
   elif o['net']!=net:exp=o['radius']+rad+.25+.001
   elif via and o['kind']=='PAD' and not o.get('drill'):exp=rad+.000001+.001
   else:continue
   b=o['g'].buffer(exp,quad_segs=32)
   if b.intersects(allowed):
    constraint_count+=1;assert constraint_count<=20000
    blocks.append(b);witness.append({'key':o['key'],'kind':o['kind'],'scope':o['scope'],'net_token':o['net'],'expanded_radius_mm':exp,'forbidden':mapping(b.intersection(outer))})
  return allowed.difference(unary_union(blocks)),witness
 def polygons(g):
  if g.geom_type=='Polygon':return [g] if not g.is_empty else []
  return [p for x in getattr(g,'geoms',[]) for p in polygons(x)]
 for comp in groups:
  ids=[ki[k] for k in comp['selected_keys']];net=comp['net_token'];layers=sorted({l for i in ids for l in cl[i]});trace_radius=max([cr[i] for i in ids if rows[i]['kind']=='segment']+[.1]);assert trace_radius==.1
  outers={l:unary_union([cg[i].buffer(cr[i]+1.0,quad_segs=32) for i in ids if l in cl[i]]) for l in layers}
  frees={};witnesses={};nodes=[]
  for l in layers:
   free,wit=free_region(outers[l],trace_radius,l,net,False);frees[l]=free;witnesses[l]=wit
   for poly in polygons(free):nodes.append((l,poly))
  parent=list(range(len(nodes)))
  def find(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  via_ids=[i for i in ids if rows[i]['kind']=='via'];via_region=Polygon()
  if via_ids:
   rad=max(cr[i] for i in via_ids);via_region=None
   for l in original['layers']:
    f,w=free_region(outers.get(l,Polygon()),rad,l,net,True);witnesses['via:'+l]=w;via_region=f if via_region is None else via_region.intersection(f)
   for p in polygons(via_region):
    touched=[n for n,(_,g) in enumerate(nodes) if g.intersects(p)]
    for n in touched[1:]:parent[find(n)]=find(touched[0])
  terminals=[]
  bridges={};retained=retained_components(net)
  for k in comp['unchanged_frontier_keys']:
   j=ki[k];hits=[n for n,(l,g) in enumerate(nodes) if l in cl[j] and g.distance(cg[j])<=trace_radius+cr[j]+1e-7]
   bridges.setdefault(retained[j],[]).extend(hits)
   terminals.append({'frontier_key':k,'layers':cl[j],'source_points_physical_mm':ends[j],'reachable_node_indices':hits,'retained_source_component_key':keys[retained[j]],'attachment_policy':'Optimistic attachment anywhere on unchanged full frontier object; exact old contact-locus reconstruction remains unproved.'})
  for hits in bridges.values():
   for n in hits[1:]:parent[find(n)]=find(hits[0])
  for t in terminals:
   component=retained[ki[t['frontier_key']]]
   t['reachable_equivalence_components']=sorted({find(n) for n in bridges[component]})
   t['access_via_retained_source_component']=not t['reachable_node_indices'] and bool(t['reachable_equivalence_components'])
  common=set.intersection(*(set(t['reachable_equivalence_components']) for t in terminals)) if terminals else set()
  via_roots={find(n) for n,(_,g) in enumerate(nodes) if not via_region.is_empty and g.intersects(via_region)}
  if via_ids:common.intersection_update(via_roots)
  # For original vias, every contacted layer must reach the same valid through-via region.
  status='CONDITIONAL_NECESSARY_CORRIDOR_ONLY' if common else 'NO_COMMON_CORRIDOR_IN_FROZEN_ENVELOPE'
  comp['via_reachable_roots']=sorted(via_roots)
  results.append({'component_id':comp['id'],'net_token':net,'selected_keys':comp['selected_keys'],'status':status,'trace_width_mm':2*trace_radius,'outer_exterior_buffer_mm':1.0,'layer_outer_regions':{l:mapping(g) for l,g in outers.items()},'layer_free_regions':{l:mapping(g) for l,g in frees.items()},'through_via_landing_region':mapping(via_region),'through_via_landing_area_mm2':via_region.area,'terminals':terminals,'all_terminal_common_components':sorted(common),'via_reachable_roots':sorted(via_roots),'obstacle_records':witnesses,'source_pad_contacts':comp['pad_uuids'],'construction_policy':'At least one replacement through-via is required for each component containing a selected original via; retained source copper and fixed-pad bridges are credited, zone bridges are unknown. This is a frozen construction rule, not a universal routing requirement.','omitted_gates':['Zones and keepouts, including unrecorded external zone bridges','Other-board nonrail copper','Exact new trace geometry and all via-pair/hole rules','No-new-merges/native group equivalence','40 rail object branch projection and repair','41 A relocation debts']})
 for p,h in seals.items():assert sha(ROOT/p)==h,p
 save(a.output,'corridor-results.json.gz',results);save(a.output,'summary.json',{'status':'COMPLETE_ONE_COMMON_CORRIDOR_CONSTRUCTION','quantifier':'One corridor common to the entire frozen offset square; failure is not every individual offset or all routing strategies','components':[dict(component_id=x['component_id'],net_token=x['net_token'],status=x['status'],through_via_landing_area_mm2=x['through_via_landing_area_mm2'],terminal_count=len(x['terminals']),terminals_without_access=sum(not t['reachable_equivalence_components'] for t in x['terminals'])) for x in results],'constraint_count':constraint_count,'elapsed_seconds':time.monotonic()-started,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0,'replacement_routes':0})
def main():
 p=argparse.ArgumentParser();p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a);return
 assert not a.output.exists();a.output.mkdir(parents=True);start=time.monotonic();save(a.output,'start.json',{'source_sha256':sha(Path(__file__)),'wall_seconds':180,'memory_GiB':2,'workers':1})
 try:code=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--dump',str(a.dump),'--output',str(a.output)],timeout=180,env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}).returncode
 except subprocess.TimeoutExpired:code=124
 save(a.output,'receipt.json',{'status':'COMPLETE' if code==0 else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-start});sys.exit(code)
if __name__=='__main__':main()
