#!/usr/bin/env python3
"""Trace original discrete rail components and settled zone evidence; no native."""
import argparse,gzip,hashlib,importlib.util,json,os,re,resource,subprocess,sys,time
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];OLD=HERE.parent/'f3-north-reconstruction-proposal-v1';RAILS={'AGND','+12V','-12V','+5V'}
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(r):return ':'.join(map(str,r['source_span']))+':'+r['sha256']
def save(out,name,o):
 raw=(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n').encode();p=out/name;t=out/(name+'.tmp');t.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw);t.replace(p)
def worker(a):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));started=time.monotonic()
 from shapely.geometry import Point,Polygon,box
 from shapely.strtree import STRtree
 from shapely.validation import explain_validity
 sys.path.insert(0,str(ROOT));from scripts.pcbgen.uuid_tools import top_level_spans
 sp=importlib.util.spec_from_file_location('repair',HERE.parents[1]/'pilots/f3-integrator-cluster-v2/repair.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
 assert r.shapely.__version__=='2.1.2' and r.shapely.geos_version_string=='3.13.1'
 seals=read(HERE/'input-seals.json')
 for p,h in seals.items():assert sha(ROOT/p)==h,p
 assert sha(a.dump)=='2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807'
 assert sha(a.settled)=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
 source=(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text();original=read(a.dump);pads=original['pads'];two=read(ROOT/'design/partition/core-split/candidates/two.json');owners={ref:bid for bid,b in two['boards'].items() for ref in b['refs']}
 assert original['board_sha256']==sha(a.settled)
 join=read(ROOT/'design/partition/core-split/candidates/pilots/f3-whole-east-v1/full-footprint-source-join.json');assert join['source_sha256']==hashlib.sha256(source.encode()).hexdigest() and join['settled_sha256']==original['board_sha256'] and join['all_full_footprint_bytes_equal'] and join['full_footprint_count']==len(join['footprint_hashes'])==3793
 index=[json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')];allrows,cg,cr,cl,ends=r.load_copper(index,source,original['layers']);allkeys=[key(x) for x in allrows]
 ids=[i for i,x in enumerate(allrows) if x['net_token'] in RAILS];rows=[allrows[i] for i in ids];gs=[cg[i] for i in ids];radii=[cr[i] for i in ids];layers=[cl[i] for i in ids];points=[ends[i] for i in ids];keys=[allkeys[i] for i in ids];ki={k:i for i,k in enumerate(keys)}
 seedrows=[x for x in read(OLD/'evidence/region-selection.json')['selected_objects'] if x['net_token'] in RAILS];seeds={ki[x['object_key']] for x in seedrows};assert len(seeds)==40 and len(rows)==9130
 tree=STRtree(gs);maxrad=max(radii);pg=[r.polygon(p) for p in pads];pt=STRtree(pg);seen=set();groups=[];query_count=0
 def tick():
  nonlocal query_count
  query_count+=1;assert query_count<=1000000,'contact query bound'
 for seed in sorted(seeds):
  if seed in seen:continue
  pending=[seed];members=set();copperedges=set();pad_edges=set();touchedpads=set()
  while pending:
   i=pending.pop()
   if i in members:continue
   assert i not in seen,'discrete component overlap';members.add(i);assert len(members)<=9130
   for n in tree.query(r.expanded_bounds(gs[i],radii[i]+maxrad+1e-7)):
    j=int(n);tick()
    if i==j or rows[i]['net_token']!=rows[j]['net_token'] or not set(layers[i]).intersection(layers[j]):continue
    if gs[i].distance(gs[j])<=radii[i]+radii[j]+1e-7:
     copperedges.add(tuple(sorted((i,j))))
     if j not in members:pending.append(j)
   for n in pt.query(r.expanded_bounds(gs[i],radii[i]+1e-7)):
    j=int(n);p=pads[j];tick()
    if p['net']!=rows[i]['net_token'] or not set(p['layers']).intersection(layers[i]) or pg[j].distance(gs[i])>radii[i]+1e-7:continue
    pad_edges.add((i,j))
    if j in touchedpads:continue
    touchedpads.add(j)
    # Whole-pad incidence bridges must be followed to exhaustion too.
    for m in tree.query(r.expanded_bounds(pg[j],maxrad+1e-7)):
     k=int(m);tick()
     if rows[k]['net_token']==p['net'] and set(p['layers']).intersection(layers[k]) and pg[j].distance(gs[k])<=radii[k]+1e-7:
      pad_edges.add((k,j))
      if k not in members:pending.append(k)
  seen.update(members);group={'id':len(groups),'net_token':rows[seed]['net_token'],'seed_keys':sorted(keys[i] for i in members&seeds),'object_keys':sorted(keys[i] for i in members),'copper_edges':[[keys[i],keys[j]] for i,j in sorted(copperedges)],'pad_edges':[{'object_key':keys[i],'pad_uuid':pads[j]['uuid']} for i,j in sorted(pad_edges)],'pads':[pads[j]|{'candidate_board':owners.get(pads[j]['ref'],'UNKNOWN')} for j in sorted(touchedpads)],'terminal_board_counts':dict(Counter(owners.get(pads[j]['ref'],'UNKNOWN') for j in touchedpads)),'traversal':'EXHAUSTED_DISCRETE_COPPER_AND_PAD_GRAPH_NO_ZONE_UNION'};groups.append(group)
 # Parse authenticated historical filled polygons without repairing invalid rings.
 settled=a.settled.read_text();zone_index={z['uuid']:z for z in index if z['kind']=='zone'};polys=[];zone_reports=[]
 xy=re.compile(r'\(xy\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)')
 for za,zb in top_level_spans(settled):
  if not settled.startswith('(zone',za):continue
  blob=settled[za:zb]
  if '(keepout' in blob:continue
  uid=r.v1.scalar(blob,'uuid');assert uid in zone_index
  srcrow=zone_index[uid];srcblob=source[slice(*srcrow['source_span'])]
  net=r.v1.scalar(blob,'net');layer=r.v1.scalar(blob,'layer');assert net==srcrow['net_token'] and layer==r.v1.scalar(srcblob,'layer')
  count=0
  for fa,fb in top_level_spans(blob):
   if not blob.startswith('(filled_polygon',fa):continue
   fill=blob[fa:fb];flayer=r.v1.scalar(fill,'layer');assert flayer==layer
   children=[fill[pa:pb] for pa,pb in top_level_spans(fill)];pts=[c for c in children if c.startswith('(pts')];assert len(pts)==1 and all(c.startswith(('(pts','(layer','(island')) for c in children),'unsupported filled polygon geometry'
   coords=[(float(x),float(y)) for x,y in xy.findall(pts[0])];poly=Polygon(coords);valid=poly.is_valid and not poly.is_empty
   meta={'zone_source_key':key(srcrow),'zone_uuid':uid,'net_token':net,'layer':flayer,'settled_fill_span':[za+fa,za+fb],'settled_fill_sha256':hashlib.sha256(fill.encode()).hexdigest(),'fill_index_in_zone':count,'vertices':len(coords),'valid_polygon':valid,'validity':explain_validity(poly),'bounds_physical_mm':list(poly.bounds)}
   polys.append((poly if valid else box(*poly.bounds),meta));count+=1
  zone_reports.append(srcrow|{'source_layer':layer,'canonical_saved_fills':srcblob.count('(filled_polygon'),'settled_zone_span':[za,zb],'settled_zone_sha256':hashlib.sha256(blob.encode()).hexdigest(),'settled_filled_polygon_count':count,'projection':'HISTORICAL_K_ZONE_ONLY; candidate A/B zone topology/feeds unselected; no duplicated-plane continuity claim'})
 assert len(zone_reports)==5 and len(polys)==440
 zt=STRtree([g for g,_ in polys]);zone_contacts=[]
 for group in groups:
  for object_key in group['object_keys']:
   i=ki[object_key]
   for n in zt.query(r.expanded_bounds(gs[i],radii[i]+1e-7)):
    poly,z=polys[int(n)];tick()
    if z['net_token']!=rows[i]['net_token'] or z['layer'] not in layers[i]:continue
    gap=poly.distance(gs[i])-radii[i]
    if gap<=1e-7:zone_contacts.append({'component_id':group['id'],'object_key':object_key,'zone_source_key':z['zone_source_key'],'settled_fill_sha256':z['settled_fill_sha256'],'filled_polygon_index':int(n),'layer':z['layer'],'gap_mm':gap,'status':'SOURCE_POLYGON_CONTACT' if z['valid_polygon'] else 'UNRESOLVED_INVALID_RING_BOUNDING_BOX_ONLY_NOT_CONTACT'})
  # Record pad-only plane interfaces, not merely interfaces through selected copper.
  for p in group['pads']:
   poly_p=r.polygon(p)
   for n in zt.query(poly_p):
    poly,z=polys[int(n)];tick()
    if z['net_token']!=p['net'] or z['layer'] not in p['layers']:continue
    if poly.distance(poly_p)<=1e-7:zone_contacts.append({'component_id':group['id'],'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'zone_source_key':z['zone_source_key'],'settled_fill_sha256':z['settled_fill_sha256'],'filled_polygon_index':int(n),'layer':z['layer'],'status':'SOURCE_POLYGON_CONTACT' if z['valid_polygon'] else 'UNRESOLVED_INVALID_RING_BOUNDING_BOX_ONLY_NOT_CONTACT'})
 reports=[]
 for group in groups:
  contacts=[z for z in zone_contacts if z['component_id']==group['id']];boards=set(group['terminal_board_counts'])
  classification='MUST_UNRESOLVED' if not boards or 'UNKNOWN' in boards else 'MIXED_A_B_DISCRETE_COMPONENT' if len(boards)>1 else 'B_ONLY_DISCRETE_CONTACT_COMPONENT' if boards=={'two-B'} else 'A_ONLY_DISCRETE_CONTACT_COMPONENT'
  group['classification']=classification;group['zone_interface_records']=len(contacts);group['zone_contact_status']='PLANE_COUPLED_OR_UNRESOLVED' if contacts else 'NO_RECORDED_SAME_NET_FILL_INTERFACE'
  for k in group['seed_keys']:
   i=ki[k];reports.append(rows[i]|{'object_key':k,'points_physical_mm':points[i],'width_or_diameter_mm':radii[i]*2,'layers':layers[i],'component_id':group['id'],'canonical':'UNCHANGED','existing_two_A_fixture':'ABSENT_SOURCE_GENERATOR_INVALIDATES_SHARED_RAIL_TRACKS_VIAS','A_projection':'UNRESOLVED_NO_OMISSION_OR_DUPLICATION_AUTHORITY','B_projection':'SOURCE_TERMINAL_CONNECTIVITY_REQUIRED' if 'two-B' in boards else 'UNRESOLVED','classification':classification,'zone_gate':group['zone_contact_status'],'authority':'Accounting only; component terminal ownership does not prove every object necessary or authorize removal/copying.'})
 for p,h in seals.items():assert sha(ROOT/p)==h,p
 assert sha(a.dump)=='2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807' and sha(a.settled)==original['board_sha256'],'external input changed'
 save(a.output,'components.json.gz',groups);save(a.output,'seed-dispositions.json',reports);save(a.output,'zone-contact-records.json.gz',zone_contacts);save(a.output,'zones.json',zone_reports);save(a.output,'filled-polygon-index.json.gz',[m for _,m in polys]);save(a.output,'reached-source-objects.json.gz',[rows[i]|{'object_key':keys[i],'points_physical_mm':points[i],'width_or_diameter_mm':2*radii[i],'layers':layers[i]} for i in sorted(seen)])
 summary={'status':'COMPLETE_SOURCE_PROJECTION_ACCOUNTING_NO_FIXTURE_EDITS','seed_objects':len(seeds),'full_discrete_components':len(groups),'reached_objects':len(seen),'component_summaries':[{'id':g['id'],'net_token':g['net_token'],'seeds':len(g['seed_keys']),'objects':len(g['object_keys']),'pads':len(g['pads']),'boards':g['terminal_board_counts'],'classification':g['classification'],'zone_records':g['zone_interface_records']} for g in groups],'historical_filled_polygons':len(polys),'invalid_filled_polygons':sum(not m['valid_polygon'] for _,m in polys),'zone_contact_records':len(zone_contacts),'query_count':query_count,'elapsed_seconds':time.monotonic()-started,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'contact_tolerance_mm':1e-7,'pad_geometry':'Saved native effective polygons; no fresh native','fill_contact_scope':'Historical geometric interface only; no projected plane continuity','native_calls':0,'fixture_edits':0}
 save(a.output,'summary.json',summary);print(json.dumps(summary,sort_keys=True))
def main():
 p=argparse.ArgumentParser();p.add_argument('--dump',type=Path,required=True);p.add_argument('--settled',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a);return
 assert not a.output.exists();a.output.mkdir(parents=True);start=time.monotonic();save(a.output,'start.json',{'source_sha256':sha(Path(__file__)),'wall_seconds':180,'memory_GiB':2,'workers':1})
 try:code=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--dump',str(a.dump),'--settled',str(a.settled),'--output',str(a.output)],timeout=180,env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}).returncode
 except subprocess.TimeoutExpired:code=124
 save(a.output,'receipt.json',{'status':'COMPLETE' if code==0 else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-start});sys.exit(code)
if __name__=='__main__':main()
