#!/usr/bin/env python3
"""Three predeclared subgroup constructions, continuous offset regions; no pose trial."""
import argparse,gzip,hashlib,importlib.util,json,math,os,resource,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
GUARD=.001
GROUP11=['C2307','C2309','C2310','C2335','C2336','R2333','R2334','R2338','R2341','R2342','U2311']
GROUP14=['C2314','C2341','C2342','D2306','Q2305','R2386','R2387','R2388','R2391','R2392','R2393','R2394','R2395','U2314']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
 raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode();p.write_bytes(gzip.compress(raw,mtime=0) if p.name.endswith('.gz') else raw)
def worker(out):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 import shapely
 from shapely import affinity
 from shapely.geometry import Polygon,Point,box,mapping
 from shapely.ops import unary_union
 spec=importlib.util.spec_from_file_location('static',HERE.parent/'f3-static-region-screen/screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
 assert shapely.__version__=='2.1.2' and shapely.geos_version_string=='3.13.1'
 seals=read(HERE/'input-seals.json')
 for f,h in seals.items():assert sha(ROOT/f)==h,f
 started=time.monotonic();g24=read(HERE.parent/'f3-next-approach/group-boundary.json')['original24']
 cases=[('A24-N','two','two-A',[124,88,164,168],[g24]),('B25-FOLD-N','two','two-A',[124,88,164,168],[GROUP11,GROUP14]),('C24-SW-THREE','three','three-B',[4.3,208,64,288],[g24])]
 allresults=[]
 for label,option,bid,window,groups in cases:
  data=read(ROOT/f'design/partition/core-split/candidates/{option}.json');board=data['boards'][bid]
  pl={p['ref']:p for p in board['placements']};refs=set(sum(groups,[]));assert len(refs)==sum(map(len,groups))
  assert len([p for p in board['source_parts'] if p['module']=='F3'])==171
  raw={ref:unary_union([s.convex_geometry(q) for q in pl[ref]['courtyard_polygons_mm']]) for ref in refs}
  offsets={};height=0
  for group in groups:
   x,y,z,w=unary_union([raw[r] for r in group]).bounds
   for ref in group:offsets[ref]=[window[0]-x,window[1]+height-y]
   height+=w-y+.36
  corrections={'C2325':[-.04,.01]} if label!='B25-FOLD-N' else {}
  for ref,delta in corrections.items():offsets[ref]=[a+b for a,b in zip(offsets[ref],delta)]
  moving={r:affinity.translate(g,*offsets[r]) for r,g in raw.items()}
  bounds=unary_union(list(moving.values())).bounds
  db=s.translation_domain(window,bounds);assert db[0]<=db[2] and db[1]<=db[3]
  domain=box(*db);outline=Polygon(board['outline_mm']).buffer(-.30,join_style=2);assert outline.covers(box(*window))
  fixed=[]
  for p in board['placements']:
   if p['ref'] in refs:continue
   for i,q in enumerate(p['courtyard_polygons_mm']):fixed.append((p['ref'],p['side'],'FIXED_COURTYARD',i,s.convex_geometry(q),.35))
  for face,d in board['measurement']['faces'].items():
   for r in d['reservation_polygons_mm']:
    for i,q in enumerate(r['polygons']):fixed.append((r['id'],face,'RESERVATION',i,s.convex_geometry(q),0))
  for r in read(ROOT/'design/partition/partition.json')['K_service_apertures']:
   fixed.append((r['header_id'],'ALL','SERVICE_HOLE',0,Point(r['center_mm']),r['diameter_mm']/2))
  los=[];his=[];records=[];considered=0
  for ref,m in sorted(moving.items()):
   a,b,c,d=m.bounds;swept=box(a+db[0],b+db[1],c+db[2],d+db[3])
   for oid,face,kind,piece,o,exp in fixed:
    considered+=1
    if face not in (pl[ref]['side'],'ALL') or swept.distance(o.envelope)>exp+GUARD:continue
    points=list(o.coords) if o.geom_type=='Point' else list(o.exterior.coords)[:-1]
    core=Polygon(s.forbidden_vertices(list(m.exterior.coords)[:-1],points));lo,hi=s.forbidden_bounds(core,exp)
    if not hi.intersects(domain):continue
    lo=lo.intersection(domain);hi=hi.intersection(domain);assert s.bounds_nested(lo,hi)
    los.append(lo);his.append(hi);records.append({'moving_ref':ref,'fixed_id':oid,'kind':kind,'face':face,'piece':piece,'expansion_mm':exp,'lower':mapping(lo),'upper':mapping(hi)})
  lower=unary_union(los);upper=unary_union(his);free=domain.difference(upper.buffer(GUARD,quad_segs=32))
  intrinsic=[]
  for i,a in enumerate(sorted(moving)):
   for b in sorted(moving)[i+1:]:
    if pl[a]['side']!=pl[b]['side']:continue
    gap=moving[a].distance(moving[b])
    if gap<.35:intrinsic.append({'refs':[a,b],'gap_mm':gap,'old_gap_mm':raw[a].distance(raw[b])})
  internal={'gap_violations':intrinsic,'C2325_correction_mm':corrections,'C2325_U2306_gap_mm':moving['C2325'].distance(moving['U2306']) if 'C2325'in refs else .349999,'remaining_inherited_gap':label=='B25-FOLD-N'}
  if 'C2325'in refs:
   def dist(corr):return math.dist([pl['C2325']['x_mm']+corr[0],pl['C2325']['y_mm']+corr[1]],[pl['U2306']['x_mm'],pl['U2306']['y_mm']])
   internal['bypass_distance_old_new_mm']=[dist([0,0]),dist(corrections['C2325'])];assert dist(corrections['C2325'])<=dist([0,0])
  result={'concept':label,'board':bid,'option':option,'window_mm':window,'refs':sorted(refs),'groups':groups,'base_offsets_mm':offsets,'global_offset_domain_mm':db,'domain_area_mm2':domain.area,'lower_covers_closed_domain':s.excluded(lower,domain),'lower_uncovered':mapping(domain.difference(lower)),'robust_external_free':mapping(free),'robust_external_free_area_mm2':free.area,'intrinsic':internal,'full_pair_iteration_count':considered,'retained_constraint_count':len(records),'status':'NO_EXTERNAL_COURTYARD_REGION' if s.excluded(lower,domain) else 'EXTERNAL_COURTYARD_REGION_ONLY' if free.area>0 else 'NUMERICAL_FRINGE_UNRESOLVED','scope':'Courtyard/reservation/service-hole/edge region only; no selectedpose, coppereligibility or native claim.'}
  save(out/f'{label}-regions.json.gz',records);save(out/f'{label}-result.json',result);allresults.append(result)
 for f,h in seals.items():assert sha(ROOT/f)==h,f
 save(out/'summary.json',{'status':'COMPLETE_REGION_COMPARISON','concepts':[{k:v for k,v in r.items() if k not in ('lower_uncovered','robust_external_free','base_offsets_mm','refs','groups')} for r in allresults],'elapsed_seconds':time.monotonic()-started,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'new_selected_poses':0,'native_calls':0})
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a.output);return
 assert not a.output.exists();a.output.mkdir(parents=True);start=time.monotonic();save(a.output/'start.json',{'source_sha256':sha(Path(__file__)),'wall_limit_seconds':30,'memory_GiB':2,'workers':1})
 try:code=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--output',str(a.output)],timeout=30,env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}).returncode
 except subprocess.TimeoutExpired:code=124
 save(a.output/'receipt.json',{'status':'COMPLETE' if code==0 else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-start});sys.exit(code)
if __name__=='__main__':main()
