#!/usr/bin/env python3
"""Rigid solid continuous service screen; convex sweeps enclose all travel."""
import argparse,json,resource,time
from pathlib import Path
import numpy as np
import check_geometry as ck

def sweep(v,moving):
 v=np.asarray(v);return np.concatenate([v,v-[0,0,10.1]]) if moving else v

def check(candidate):
 model=ck.read(candidate/'mechanical.json.gz');solids=model['solids'];obs=ck.source_obstacles();source_findings=[];cross=[];walls=[];joints=[];near=1e9
 for s in solids:
  sv=np.asarray(s['vertices_xyz_mm']);sb=ck.aabb(sv);moving=s['board']=='KB'
  swept=sweep(sv,moving);bounds=ck.aabb(swept)
  gaps=[bounds[0]+2,320-bounds[3],bounds[1]+2,300-bounds[4],bounds[2]+146,-90-bounds[5]]
  walls.append({'solid':s['id'],'minimum_reference_gap_mm':min(gaps),'after_0p35_closure_mm':min(gaps)-.35})
  for o in obs:
   ov=ck.box_vertices(o['box']);same=moving==o['moves']
   av=sv if same else swept;bv=ov if same else sweep(ov,o['moves'])
   if ck.box_gap(ck.aabb(av),ck.aabb(bv))>=.60:continue
   if o['kind']=='support' and s['id'].split('/')[1].startswith('support-'):
    centre=(np.array(o['box'][:2])+o['box'][3:5])/2
    if min(np.linalg.norm(centre-np.array(x)) for x in [(6.5,10.5),(311.5,10.5)])<1e-7:continue
   gap=ck.separating_bound(av,bv);near=min(near,gap)
   if gap<.60:source_findings.append({'solid':s['id'],'source':o['id'],'lower_bound_mm':gap,'kind':'POSSIBLE_OVERLAP_OR_CLEARANCE_UNRESOLVED','whole_travel_mm':[0,10.1]})
 for i,a in enumerate(solids):
  for b in solids[i+1:]:
   if a['board']==b['board']:continue # joined own-board structure has explicit material union and cavities
   av=np.asarray(a['vertices_xyz_mm']);bv=np.asarray(b['vertices_xyz_mm']);av=sweep(av,a['board']=='KB');bv=sweep(bv,b['board']=='KB')
   if ck.box_gap(ck.aabb(av),ck.aabb(bv))>=.60:continue
   gap=ck.separating_bound(av,bv)
   if gap<.60:cross.append({'first':a['id'],'second':b['id'],'lower_bound_mm':gap,'status':'POSSIBLE_OVERLAP_OR_CLEARANCE_UNRESOLVED'})
 lookup={s['id']:s for s in solids}
 for j in model['intended_structural_joints']:
  a=lookup[j['a']];b=lookup[j['b']];aa=ck.aabb(a['vertices_xyz_mm']);bb=ck.aabb(b['vertices_xyz_mm']);overlap=np.minimum(aa[3:],bb[3:])-np.maximum(aa[:3],bb[:3]);joints.append(j|{'bounding_overlap_mm':overlap.tolist(),'bounding_overlap_is_not_strength_or_actual_CSG_contact_proof':True})
 return {'status':'SOURCE_SOLID_SERVICE_SCREEN','travel_mm':[0,10.1],'method':'Exact convex hull of each translating rigid solid at both end positions contains its complete service sweep; co-moving pairs tested in one relative frame. Holes ignored for conservative unrelated-source screening. Negative face-normal bound is unresolved, never a proven penetration.','source_obstacle_count':len(obs),'retained_trimmer_tool_columns':sum(o['kind']=='trimmer-tool' for o in obs),'solid_count':len(solids),'source_findings':source_findings,'cross_carrier_findings':cross,'enclosure':walls,'structural_joint_register':joints,'minimum_near_source_lower_bound_mm':near if near<1e9 else None,'qualification':'Source tool columns use the retained proposed axis/3mm shaft; unchanged baseline blocked front approach is not qualified by this incremental clearance check. Own-board carrier is a material union; shared structural junctions are intentional. Fastener fit/loads, thermal/retention/creep and service metrology remain unqualified.'}
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();t=time.monotonic();d=check(a.candidate);d['elapsed_seconds']=time.monotonic()-t;a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'source_findings':len(d['source_findings']),'cross_findings':len(d['cross_carrier_findings']),'wall_residual':min(x['after_0p35_closure_mm'] for x in d['enclosure']),'elapsed':d['elapsed_seconds']}))
if __name__=='__main__':main()
