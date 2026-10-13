#!/usr/bin/env python3
"""Necessary pad-clearance region filter and exact source copper ownership accounting."""
import argparse,gzip,hashlib,importlib.util,json,os,resource,subprocess,sys,time
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(out,name,obj):
 raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode();p=out/name;t=out/(name+'.tmp');t.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw);t.replace(p)
def gz(p):return json.loads(gzip.decompress(p.read_bytes()))
def key(r):return ':'.join(map(str,r['source_span']))+':'+r['sha256']
def worker(a):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));start=time.monotonic()
 from shapely import affinity
 from shapely.geometry import Point,Polygon,MultiPoint,box,shape,mapping
 from shapely.ops import unary_union
 from shapely.strtree import STRtree
 sp=importlib.util.spec_from_file_location('repair',HERE.parents[1]/'pilots/f3-integrator-cluster-v2/repair.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
 sp=importlib.util.spec_from_file_location('static',HERE.parent/'f3-static-region-screen/screen.py');s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
 assert r.shapely.__version__=='2.1.2' and r.shapely.geos_version_string=='3.13.1'
 for f,h in (read(HERE/'input-seals.json')|read(HERE/'pad-input-seals.json')).items():assert sha(ROOT/f)==h
 assert sha(a.dump)=='2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807'
 region_seals={label:sha(HERE/'evidence/regions'/f'{label}-result.json') for label in ['A24-N','B25-FOLD-N']}
 for label,h in region_seals.items():assert sha(a.regions/f'{label}-result.json')==h,'supplied region hash mismatch'
 original=read(a.dump);pads=original['pads'];assert len(pads)==13406
 source=(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text();index=[json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
 rows,cg,cr,cl,ends=r.load_copper(index,source,original['layers']);assert len(rows)==133551 and len(index)==133902
 keys=[key(x) for x in rows];assert len(set(keys))==len(keys);ki={k:i for i,k in enumerate(keys)}
 old=HERE.parents[1]/'pilots/f3-whole-east-v1/evidence';inventory=gz(old/'internal-copper-classification.json.gz');components=gz(old/'internal-source-components.json.gz')
 ir={x['object_key']:x for x in inventory};assert len(ir)==4491
 for k,x in ir.items():assert k in ki and rows[ki[k]]['sha256']==x['sha256']
 pg=[affinity.translate(r.polygon(p),-100,-50) for p in pads]
 cg=[affinity.translate(g,-100,-50) for g in cg];ct=STRtree(cg);maxrad=max(cr)
 count=0;iterations=0;results=[]
 for label in ['A24-N','B25-FOLD-N']:
  case=read(a.regions/f'{label}-result.json');assert case['status']=='EXTERNAL_COURTYARD_REGION_ONLY'
  data=read(ROOT/f"design/partition/core-split/candidates/{case['option']}.json");board=data['boards'][case['board']];bid=case['board'][-1]
  refs=set(case['refs']);off={k:tuple(round(x,9) for x in v) for k,v in case['base_offsets_mm'].items()};fixedrefs=set(board['refs'])|set(board['mechanical_refs'])
  assert refs<=fixedrefs;domain=box(*case['global_offset_domain_mm']);available=shape(case['robust_external_free'])
  comp_rows=[];eligible={}
  for comp in components:
   contacts=[p for k in comp['objects'] for p in ir[k]['contacts']['original_pad_contacts']]
   transforms={off.get(p['ref'],(0.,0.)) for p in contacts}
   if comp['source_contact_closed'] and len(transforms)==1 and next(iter(transforms))!=(0.,0.):
    delta=next(iter(transforms));eligible.update({ki[k]:delta for k in comp['objects']});status='RIGID_SOURCE_CONTACT_COMPONENT'
   else:status='PRESERVE_IN_PLACE_RECONNECT_MOVED_CONTACTS' if any(p['ref'] in refs for p in contacts) else 'PRESERVE_UNCHANGED'
   comp_rows.append({'component':comp['id'],'status':status,'objects':comp['objects'],'pad_contacts':contacts,'transforms':sorted(transforms)})
  # Shared-pad incidence must assign all incident eligible components the same transform.
  incidence=defaultdict(set)
  for c in comp_rows:
   for p in c['pad_contacts']:incidence[p['uuid']].add(tuple(off.get(p['ref'],(0.,0.))))
  assert all(len(v)==1 for v in incidence.values())
  def scope(row):
   owners=data['net_owners'].get(row['net_token'],[])
   return 'SHARED_RAIL_RETURN' if row['net_token'] in ('+12V','-12V','+5V','AGND') else 'OTHER_CANDIDATE_UNCHANGED' if owners and bid not in owners else 'RETAINED_CANDIDATE_OR_UNKNOWN'
  scopes=[scope(x) for x in rows];fixed_ids=[i for i,x in enumerate(rows) if i not in eligible and scopes[i]!='OTHER_CANDIDATE_UNCHANGED'];fixedset=set(fixed_ids)
  fpi=[i for i,p in enumerate(pads) if p['ref'] in fixedrefs and p['ref'] not in refs and not pg[i].is_empty];pt=STRtree([pg[i] for i in fpi]);drills=[(i,Point(p['xy'][0]/1e6-100,p['xy'][1]/1e6-50),p['drill']/2e6) for i,p in enumerate(pads) if p['ref'] in fixedrefs and p['ref'] not in refs and p['drill']];dt=STRtree([g for _,g,_ in drills]);maxdrill=max((rad for _,_,rad in drills),default=0)
  lower=[];upper=[];constraints=[];contacts=[]
  def forbid(ref,pad,kind,oid,m,o,exp):
   nonlocal count
   count+=1;assert count<=50000,'configuration constraint limit'
   assert m.equals(m.convex_hull),'nonconvex moving pad'
   op=list(o.coords) if o.geom_type in ('Point','LineString') else list(o.exterior.coords)[:-1]
   if o.geom_type=='Polygon':assert o.equals(o.convex_hull),'nonconvex fixed pad'
   hull=s.forbidden_vertices(list(m.exterior.coords)[:-1],op);core=Polygon(hull);lo,hi=s.forbidden_bounds(core,exp)
   if not hi.intersects(domain):return
   lo=lo.intersection(domain);hi=hi.intersection(domain);assert s.bounds_nested(lo,hi)
   lower.append(lo);upper.append(hi);constraints.append({'ref':ref,'pad':pad,'kind':kind,'fixed_id':oid,'expansion_mm':exp,'lower':mapping(lo),'upper':mapping(hi)})
  for i,p in enumerate(pads):
   if p['ref'] not in refs:continue
   m=affinity.translate(pg[i],*off[p['ref']]);x,y,z,w=m.bounds;dx,dy,dz,dw=domain.bounds;swept=box(x+dx,y+dy,z+dz,w+dw)
   for q in pt.query(r.expanded_bounds(swept,.251)):
    j=fpi[int(q)];iterations+=1
    if p['net']==pads[j]['net'] or not set(p['layers']).intersection(pads[j]['layers']):continue
    forbid(p['ref'],p['pad'],'FOREIGN_PAD',pads[j]['uuid'],m,pg[j],.25)
   for q in dt.query(r.expanded_bounds(swept,maxdrill+.251)):
    j,g,rad=drills[int(q)];iterations+=1;forbid(p['ref'],p['pad'],'FIXED_PAD_DRILL',pads[j]['uuid'],m,g,rad+.25)
   for q in ct.query(r.expanded_bounds(swept,maxrad+.251)):
    j=int(q);iterations+=1
    if j not in fixedset or not set(p['layers']).intersection(cl[j]):continue
    foreign=p['net']!=rows[j]['net_token'];via=rows[j]['kind']=='via' and not p['drill']
    if foreign or via:forbid(p['ref'],p['pad'],'FOREIGN_COPPER' if foreign else 'SAME_NET_VIA_SMD',keys[j],m,cg[j],cr[j]+(.25 if foreign else .000001))
   # Preserve exact original contact identity; actual selected-pose contact fate is deferred.
   for q in ct.query(r.expanded_bounds(pg[i],maxrad+1e-7)):
    j=int(q);iterations+=1
    if p['net']==rows[j]['net_token'] and set(p['layers']).intersection(cl[j]) and pg[i].distance(cg[j])-cr[j]<=1e-7:
     contacts.append({'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'net_token':p['net'],'object_key':keys[j],'source_gap_mm':pg[i].distance(cg[j])-cr[j],'source_pad_xy_nm':p['xy'],'source_object_points_physical_mm':ends[j],'pad_base_offset_mm':off[p['ref']],'object_base_offset_mm':eligible.get(j,[0,0]),'object_global_offset_follows':j in eligible,'same_transform':j in eligible and eligible[j]==off[p['ref']],'scope':scopes[j],'obligation':'Preserve exact sourcecontact or explicitly reconnect; no silent endpoint loss.'})
  lo=unary_union(lower);hi=unary_union(upper);remaining=available.difference(hi.buffer(.001,quad_segs=32));excluded=lo.covers(available) and available.difference(lo).is_empty
  status='EXCLUDED_BY_NECESSARY_PAD_CONSTRAINTS' if excluded else 'PAD_REGION_SURVIVES_MORE_GATES_REQUIRED' if remaining.area>0 else 'NUMERICAL_FRINGE_UNRESOLVED'
  result={'concept':label,'status':status,'available_courtyard_area_mm2':available.area,'lower_covers_available_region':excluded,'lower_uncovered':mapping(available.difference(lo)),'remaining_guarded_region':mapping(remaining),'remaining_guarded_area_mm2':remaining.area,'eligible_source_components':sum(c['status']=='RIGID_SOURCE_CONTACT_COMPONENT' for c in comp_rows),'eligible_source_objects':len(eligible),'selected_pad_original_contacts':len(contacts),'same_transform_contacts':sum(c['same_transform'] for c in contacts),'fixed_or_different_transform_contacts':sum(not c['same_transform'] for c in contacts),'constructed_constraints':len(constraints),'constraint_kinds':dict(Counter(c['kind'] for c in constraints)),'scope':'Necessary pad-only region filter, not complete copper/zone/native eligibility; no candidate selected.'}
  save(a.output,label+'-components.json.gz',comp_rows);save(a.output,label+'-contacts.json.gz',contacts);save(a.output,label+'-constraints.json.gz',constraints);save(a.output,label+'-result.json',result)
  save(a.output,label+'-object-dispositions.json.gz',[{'object_key':keys[i],'scope':scopes[i],'candidate_disposition':'ELIGIBLE_COMPONENT_TRANSFORM_PENDING_GATES' if i in eligible else 'PRESERVED_IN_PLACE','base_offset_mm':eligible.get(i,[0,0]),'canonical_disposition':'UNCHANGED'} for i in range(len(rows))])
  save(a.output,label+'-zones-rule-areas.json',[x|{'canonical_disposition':'UNCHANGED','candidate_gate':'UNRESOLVED_ZONE_REFILL_CONTACT' if x['kind']=='zone' else 'RETAINED_FIXED_KEEPOUT'} for x in index if x['kind']in('zone','rule_area')])
  results.append(result)
 for f,h in (read(HERE/'input-seals.json')|read(HERE/'pad-input-seals.json')).items():assert sha(ROOT/f)==h
 for label,h in region_seals.items():assert sha(a.regions/f'{label}-result.json')==h,'supplied region changed'
 save(a.output,'summary.json',{'status':'COMPLETE_NECESSARY_PAD_FILTER','results':results,'all_source_objects':len(index),'segments_vias':len(rows),'all_pads':len(pads),'constraint_candidates_built':count,'broadphase_iterations':iterations,'elapsed_seconds':time.monotonic()-start,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'selected_poses':0,'native_calls':0})
def main():
 p=argparse.ArgumentParser();p.add_argument('--dump',type=Path,required=True);p.add_argument('--regions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a);return
 assert not a.output.exists();a.output.mkdir(parents=True);start=time.monotonic();save(a.output,'start.json',{'source_sha256':sha(Path(__file__)),'wall_seconds':180,'memory_GiB':2,'workers':1})
 try:code=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--dump',str(a.dump),'--regions',str(a.regions),'--output',str(a.output)],timeout=180,env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}).returncode
 except subprocess.TimeoutExpired:code=124
 save(a.output,'receipt.json',{'status':'COMPLETE' if code==0 else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-start});sys.exit(code)
if __name__=='__main__':main()
