#!/usr/bin/env python3
"""Bounded source contact/frontier census for one frozen hypothetical roster."""
import argparse,gzip,hashlib,importlib.util,json,os,resource,subprocess,sys,time
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];OLD=HERE.parent/'f3-rearrangement-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def key(r):return ':'.join(map(str,r['source_span']))+':'+r['sha256']
def save(out,name,obj):
 raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode();p=out/name;t=out/(name+'.tmp');t.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw);t.replace(p)
def worker(a):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));started=time.monotonic()
 from shapely.geometry import Point
 from shapely.ops import nearest_points
 from shapely.strtree import STRtree
 sp=importlib.util.spec_from_file_location('repair',HERE.parents[1]/'pilots/f3-integrator-cluster-v2/repair.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
 assert r.shapely.__version__=='2.1.2' and r.shapely.geos_version_string=='3.13.1'
 seal=read(HERE/'input-seals.json')
 for path,h in seal.items():assert sha(ROOT/path)==h,path
 assert sha(a.dump)=='2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807'
 chosen=read(HERE/'evidence/region-selection.json');selected_keys={x['object_key'] for x in chosen['selected_objects']}
 assert chosen['status']=='HYPOTHETICAL_PAD_ONLY_OPPORTUNITY_NOT_PLACEMENT_FEASIBILITY' and chosen['all_remaining_constraints_clear_cell'] and not chosen['nonreleasable_conflicts']
 assert len(selected_keys)==len(chosen['selected_objects'])==52
 original=read(a.dump);pads=original['pads'];source=(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text();index=[json.loads(line) for line in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
 rows,cg,cr,cl,ends=r.load_copper(index,source,original['layers']);keys=[key(x) for x in rows];ki={k:i for i,k in enumerate(keys)};assert len(rows)==len(ki)==133551
 selected={ki[k] for k in selected_keys};assert len(selected)==len(chosen['selected_objects'])
 ct=STRtree(cg);maxrad=max(cr);pg=[r.polygon(p) for p in pads];pt=STRtree(pg)
 uuid_counts=Counter(row['uuid'] for row in rows);dump_by_uuid=defaultdict(list)
 for kind,name in [('segment','tracks'),('via','vias')]:
  for item in original[name]:dump_by_uuid[item['uuid']].append((kind,item))
 islands=original['islands'];island_lookup=defaultdict(list)
 for net,groups in islands.items():
  for n,group in enumerate(groups):
   for uid in group:island_lookup[(net,uid)].append(n)
 def identity(i):return dict(rows[i],object_key=keys[i],points_physical_mm=ends[i],layers=cl[i],diameter_or_width_mm=2*cr[i])
 def binding(i):
  row=rows[i];matches=[]
  for kind,item in dump_by_uuid[row['uuid']]:
   if kind!=row['kind'] or item['net']!=row['net_token']:continue
   if kind=='segment':ok=sorted(tuple(round(v*1e6) for v in p) for p in ends[i])==sorted([tuple(item['a']),tuple(item['b'])]) and round(cr[i]*2e6)==item['width'] and cl[i]==[item['layer']]
   else:ok=[round(v*1e6) for v in ends[i][0]]==item['xy'] and round(cr[i]*2e6)==item['diameter'] and round(row['drill_mm']*1e6)==item['drill'] and cl[i]==original['layers']
   if ok:matches.append(item)
  group_ids=island_lookup[(row['net_token'],row['uuid'])]
  return {'status':'BOUND_BY_UNIQUE_UUID_NET_KIND_GEOMETRY' if len(matches)==1 and uuid_counts[row['uuid']]==1 and len(group_ids)==1 else 'UNRESOLVED_IDENTITY_OR_ISLAND','layer_binding':'DUMP_SEGMENT_LAYER_MATCH' if row['kind']=='segment' else 'SOURCE_THROUGH_SPAN_ONLY_NATIVE_PER_VIA_LAYERS_UNRECORDED','matching_dump_records':len(matches),'canonical_uuid_multiplicity':uuid_counts[row['uuid']],'original_island_indices':group_ids}
 frontier={};affected=[];pairs=[];padcontacts=[];tests=0
 def tick():
  nonlocal tests
  tests+=1;assert tests<=1000000,'source contact query bound'
 for i in sorted(selected):
  contact_rows=[]
  for j in sorted(map(int,ct.query(r.expanded_bounds(cg[i],cr[i]+maxrad+1e-7)))):
   tick()
   if i==j or rows[i]['net_token']!=rows[j]['net_token'] or not set(cl[i]).intersection(cl[j]):continue
   gap=cg[i].distance(cg[j])-cr[i]-cr[j]
   if gap>1e-7:continue
   pa,pb=nearest_points(cg[i],cg[j]);item={'source_key':keys[i],'neighbor_key':keys[j],'neighbor_uuid':rows[j]['uuid'],'common_layers':sorted(set(cl[i]).intersection(cl[j])),'source_gap_mm':gap,'nearest_centerline_points_physical_mm':[list(pa.coords[0]),list(pb.coords[0])],'touches_source_endpoint_indices':[n for n,xy in enumerate(ends[i]) if Point(xy).distance(cg[j])<=cr[i]+cr[j]+1e-7],'neighbor_disposition':'PROPOSED_RECONSTRUCTION' if j in selected else 'UNCHANGED_FRONTIER'}
   contact_rows.append(item);pairs.append(item)
   if j not in selected:frontier[keys[j]]=identity(j)|{'dump_binding':binding(j)}
  pc=[]
  for j in sorted(map(int,pt.query(r.expanded_bounds(cg[i],cr[i]+1e-7)))):
   p=pads[j];tick()
   if p['net']!=rows[i]['net_token'] or not set(p['layers']).intersection(cl[i]):continue
   gap=pg[j].distance(cg[i])-cr[i]
   if gap>1e-7:continue
   pa,pb=nearest_points(cg[i],pg[j]);item={'source_key':keys[i],'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'net_token':p['net'],'xy_nm':p['xy'],'layers':p['layers'],'gap_mm':gap,'nearest_points_physical_mm':[list(pa.coords[0]),list(pb.coords[0])]};pc.append(item);padcontacts.append(item)
  affected.append(identity(i)|{'dump_binding':binding(i),'same_net_copper_contacts':contact_rows,'pad_contacts':pc,'canonical_disposition':'UNCHANGED','proposal_disposition':'CONDITIONAL_RECONSTRUCTION_ONLY_NO_ROUTE_OR_CUT'})
 parent={i:i for i in selected}
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for pair in pairs:
  i,j=ki[pair['source_key']],ki[pair['neighbor_key']]
  if j in selected:parent[find(j)]=find(i)
 # Pad-mediated selected incidence is part of current equivalence too.
 pad_incidence=defaultdict(list)
 for pc in padcontacts:pad_incidence[pc['pad_uuid']].append(ki[pc['source_key']])
 for ids in pad_incidence.values():
  for i in ids[1:]:parent[find(i)]=find(ids[0])
 groups=defaultdict(list)
 for i in sorted(selected):groups[find(i)].append(i)
 components=[]
 for n,ids in enumerate(groups.values()):
  idskeys={keys[i] for i in ids};ps=[p for p in pairs if p['source_key'] in idskeys];pcs=[p for p in padcontacts if p['source_key'] in idskeys]
  components.append({'id':n,'net_token':rows[ids[0]]['net_token'],'selected_keys':sorted(idskeys),'unchanged_frontier_keys':sorted({p['neighbor_key'] for p in ps if p['neighbor_disposition']=='UNCHANGED_FRONTIER'}),'pad_uuids':sorted({p['pad_uuid'] for p in pcs}),'required_equivalence':'Preserve original full-object copper and pad contact equivalence among these members; records are not separate required new routes. Retain unrelated branch geometry and all historical native-group equivalences; zone contacts unresolved.'})
 selected_nets={rows[i]['net_token'] for i in selected};source_groups=[]
 for net in sorted(selected_nets):
  indices=sorted({n for i in selected if rows[i]['net_token']==net for n in binding(i)['original_island_indices']})
  for n in indices:
   members=islands[net][n];source_groups.append({'net_token':net,'index':n,'member_count':len(members),'sorted_members_sha256':hashlib.sha256(('\n'.join(sorted(members))+'\n').encode()).hexdigest(),'members':members,'qualification':'Historical original-dump island membership, no fresh native proof; ambiguous bindings remain unresolved.'})
 old_contacts=read(OLD/'evidence/pad-regions/A24-N-contacts.json.gz');old_debts=[p for p in old_contacts if not p['same_transform']]
 overlap=[p for p in old_debts if p['object_key'] in selected_keys]
 names=read(ROOT/'design/reports/board-net-tokens.json');name_by_token={v:k for k,v in names.items()} if all(isinstance(v,str) for v in names.values()) else {}
 bounds=[cg[i].bounds for i in selected]
 summary={'status':'COMPLETE_SOURCE_CONTACT_CENSUS_NO_ROUTING','selected_objects':len(selected),'selected_kinds':dict(Counter(rows[i]['kind'] for i in selected)),'net_counts':dict(Counter(rows[i]['net_token'] for i in selected)),'selected_components':len(components),'directed_copper_contacts':len(pairs),'unique_unchanged_frontier_objects':len(frontier),'pad_contacts':len(padcontacts),'source_bounds_physical_mm':[min(b[0]-cr[i] for b,i in zip(bounds,selected)),min(b[1]-cr[i] for b,i in zip(bounds,selected)),max(b[2]+cr[i] for b,i in zip(bounds,selected)),max(b[3]+cr[i] for b,i in zip(bounds,selected))],'prior_A_reconnection_contacts':len(old_debts),'overlap_A_debts_with_selected_roster':len(overlap),'unresolved_selected_bindings':sum(x['dump_binding']['status'].startswith('UNRESOLVED') for x in affected),'unresolved_frontier_bindings':sum(x['dump_binding']['status'].startswith('UNRESOLVED') for x in frontier.values()),'historical_islands':len(source_groups),'contact_query_iterations':tests,'elapsed_seconds':time.monotonic()-started,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0}
 save(a.output,'selected-object-contacts.json.gz',affected);save(a.output,'preserved-frontier.json.gz',list(frontier.values()));save(a.output,'selected-components.json',components);save(a.output,'historical-islands.json.gz',source_groups);save(a.output,'prior-A-contact-debts.json',{'all_41':old_debts,'overlap_selected_roster':overlap});save(a.output,'zone-obligations.json',[row|{'disposition':'UNCHANGED','gate':'Filled contact locus not established; preserve every original net equivalence and refill continuity, cannot exempt shared planes.'} for row in index if row['kind']=='zone'])
 for path,h in seal.items():assert sha(ROOT/path)==h,path
 save(a.output,'summary.json',summary)
 print(json.dumps(summary,sort_keys=True))
def main():
 p=argparse.ArgumentParser();p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a);return
 assert not a.output.exists();a.output.mkdir(parents=True);start=time.monotonic();save(a.output,'start.json',{'source_sha256':sha(Path(__file__)),'wall_seconds':180,'memory_GiB':2,'workers':1})
 try:code=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--dump',str(a.dump),'--output',str(a.output)],timeout=180,env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}).returncode
 except subprocess.TimeoutExpired:code=124
 save(a.output,'receipt.json',{'status':'COMPLETE' if code==0 else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-start});sys.exit(code)
if __name__=='__main__':main()
