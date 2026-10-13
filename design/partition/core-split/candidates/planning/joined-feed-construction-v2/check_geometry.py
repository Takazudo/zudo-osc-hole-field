#!/usr/bin/env python3
"""Full-source solid screen and interval-enclosed continuous wire service sweep."""
import argparse,gzip,json,math,resource,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];FEED=ROOT/'circuit/routing/epic-242/decision-pilots/feed-arrangement'
sys.path.insert(0,str(FEED));import robust_curve as rc,check as base

def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def source_obstacles():
 c=base.read(ROOT/'design/partition/core-split/candidates/two.json')['boards'];part=base.read(ROOT/'design/partition/partition.json');mech=next(x for x in base.read(ROOT/'design/partition/core-split/mechanical/generated/comparison.json')['alternatives'] if x['id']=='two-deep');over=base.read(FEED/'reconciled-contract.json')['producer_replacements'];old=base.read(FEED/'offset-proposal.json');out=[];faces={'KA':{'F.Cu':-100.,'B.Cu':-101.6},'KB':{'F.Cu':-126.,'B.Cu':-127.6}}
 for board,key in [('KA','two-A'),('KB','two-B')]:
  for face in ['F.Cu','B.Cu']:
   for idx,row in enumerate(base.obstacles(c[key],face,mech,part)):
    xy=row['box'];z=faces[board][face];zz=[-160,-90] if row['kind'] in ('tool-column','support','loom') else ([z,z+7.3] if face=='F.Cu' else [z-5,z])
    out.append({'id':board+'/'+face+'/'+row['id']+'/'+str(idx),'kind':row['kind'],'board':board,'box':xy[:2]+[zz[0]]+xy[2:]+[zz[1]],'moves':board=='KB' and row['kind'] not in ('tool-column','support','loom')})
 for q in old['construction']['bulk_and_monitor_reserves']:
  if '-bulk-' in q['id']:out.append({'id':q['id'],'kind':'new-reserve','board':q['board'],'box':q['box'],'moves':q['board']=='KB'})
 m=over['monitor'];xy=m['box_xy_mm'];out.append({'id':m['id'],'kind':'new-monitor','board':'KB','box':xy[:2]+[-132.6]+xy[2:]+[-127.6],'moves':True})
 for t in mech['trimmers']:
  x,y=t['xy_mm'];r=t['tool_proposal']['shaft_diameter_mm']/2
  out.append({'id':'TRIMMER-TOOL/'+t['ref'],'kind':'trimmer-tool','board':t['board'],'box':[x-r,y-r,-160,x+r,y+r,-30],'moves':False})
 assert len(mech['trimmers'])==100
 return out

def primitive_distance(points,obj,shift=0.):
 """Exact point-to-outer primitive; holes give conservative material lower bound."""
 points=np.array(points,copy=True);points[:,2]+=shift
 if obj['shape']=='oriented_box':
  q=(points-np.array(obj['center_xyz_mm']))@np.array(obj['axes_xyz']).T;d=np.abs(q)-obj['half_extents_mm'];outer=np.linalg.norm(np.maximum(d,0),axis=1)
 else:
  a,b=np.array(obj['axis_endpoints_xyz_mm']);w=(b-a)/np.linalg.norm(b-a);p=points-a;s=p@w;rad=np.linalg.norm(p-s[:,None]*w,axis=1)-obj['radius_mm'];ax=np.maximum(-s,s-np.linalg.norm(b-a));outer=np.hypot(np.maximum(rad,0),np.maximum(ax,0))
 for h in obj.get('holes',[]):
  h=h['analytic_primitive']
  if h['shape']=='oriented_box':
   q=(points-h['center_xyz_mm'])@np.array(h['axes_xyz']).T;inside=np.min(np.array(h['half_extents_mm'])-np.abs(q),axis=1)
  else:
   a,b=np.array(h['axis_endpoints_xyz_mm']);w=(b-a)/np.linalg.norm(b-a);p=points-a;s=p@w;rad=h['radius_mm']-np.linalg.norm(p-s[:,None]*w,axis=1);inside=np.minimum(rad,np.minimum(s,np.linalg.norm(b-a)-s))
  outer=np.maximum(outer,inside)
 return outer

def aabb(vertices):
 v=np.asarray(vertices);return np.r_[v.min(axis=0),v.max(axis=0)]
def box_vertices(box):return np.array([[x,y,z] for x in [box[0],box[3]] for y in [box[1],box[4]] for z in [box[2],box[5]]])
def box_gap(a,b):return np.linalg.norm(np.maximum(np.maximum(a[:3]-b[3:],b[:3]-a[3:]),0))
def separating_bound(va,vb):
 """SAT lower distance bound. Nonpositive identifies possible/intersecting solids."""
 va=np.asarray(va);vb=np.asarray(vb);ha=ConvexHull(va);hb=ConvexHull(vb)
 axes=np.concatenate([ha.equations[:,:3],hb.equations[:,:3]])
 # Face normals suffice for a lower bound (may conservatively flag edge pairs).
 aa=va@axes.T;bb=vb@axes.T
 gaps=np.maximum(aa.min(axis=0)-bb.max(axis=0),bb.min(axis=0)-aa.max(axis=0))
 return float(gaps.max())

def static_screen(solids,obs):
 findings=[];closest=(1e9,None,None);boxes=np.array([o['box'] for o in obs]);checked=0
 for s in solids:
  v=np.asarray(s['vertices_xyz_mm']);bound=aabb(v)
  # Mechanical sleeves contain their own captured metal; both still obstacles to wires.
  for j,o in enumerate(obs):
   b=boxes[j]
   if box_gap(bound,b)>.70:continue
   checked+=1
   if o['kind']=='support' and s['id'].split('/')[1].startswith('support-'):
    # Precise intended top-collar attachment, same XY on either source face.
    center=(b[:2]+b[3:5])/2
    if min(np.linalg.norm(center-np.array(x)) for x in [(6.5,10.5),(311.5,10.5)])<1e-7:continue
   gap=separating_bound(v,box_vertices(b))
   if gap<closest[0]:closest=(gap,s['id'],o['id'])
   if gap<.60:findings.append({'solid':s['id'],'obstacle':o['id'],'kind':o['kind'],'separating_lower_bound_mm':gap,'solid_bounds_mm':bound.tolist(),'obstacle_box_mm':b.tolist()})
  # Except explicit board-contact insulators and own support fasteners, all carrier
  # material must remain clear of both slab faces at the installed state.
  face=-101.6 if s['board']=='KA' else -126.;normal=-1 if s['board']=='KA' else 1
  depth=(v[:,2]-face)*normal;minimum=float(depth.min())
  if s['kind'] not in ('termination_insulator','own_net_solder_envelope','support_fastener','insulating_washer','insulated_fastener_envelope','fastener_metal') and minimum<.60 and bound[4]>=8 and bound[3]>=4 and bound[0]<=314:
   findings.append({'solid':s['id'],'obstacle':'own-board-face','separating_lower_bound_mm':minimum})
 return {'status':'CLEAR' if not findings else 'SOURCE_CONSTRUCTION_CONFLICTS','pair_candidates':checked,'minimum_bound':closest,'findings':findings}

def wire_screen(solids,obs,gap_cells=100,curve_cells=256):
 F=rc.Family();gs=np.linspace(*F.gap_range,gap_cells+1);hs=[(rc.handle(F,g,F.free_length_range_mm[0]),rc.handle(F,g,F.free_length_range_mm[1])) for g in gs]
 findings=[];near=[];minsrc=(1e9,None);minarm=(1e9,None);minpair=1e9;minwall=1e9;total=0
 # Every gap and length in the admissible rectangle is enclosed through h-corner
 # monotonic bounds; cubic control/derivative hull encloses every t cell.
 edges=np.unique(np.r_[np.linspace(0,.05,81),np.linspace(.05,.95,curve_cells+1),np.linspace(.95,1,81)]);t=(edges[:-1]+edges[1:])/2;dt=np.diff(edges)/2;v0=np.array(F.direction);v1=v0*[1,-1,1]
 signs=[1,-1,1,1,-1,1];radius=2.5908/2
 for k,(g0,g1) in enumerate(zip(gs,gs[1:])):
  if k%10==0:print(f'gap cells {k}/{gap_cells}',flush=True)
  gh=(g0+g1)/2;shift=gh-20.4
  controls=[rc.control(F,g,h) for g in [g0,g1] for h in [hs[k+1][0]-1e-7,hs[k][1]+1e-7]]
  pp=np.array([rc.position(p,t) for p in controls]);dmax=np.max(np.abs([3*(p[1:]-p[:-1]) for p in controls]),axis=(0,1))
  lo=pp.min(axis=0)-dmax*dt[:,None];hi=pp.max(axis=0)+dmax*dt[:,None];mid=(lo+hi)/2;err=np.linalg.norm((hi-lo)/2,axis=1)
  ob=np.array([o['box'] for o in obs],float)
  for j,o in enumerate(obs):
   if o['moves']:ob[j,[2,5]]-=shift;ob[j,2]-=(g1-g0)/2+.2;ob[j,5]+=(g1-g0)/2+.2
  ppb=np.array([rc.position(p,t)+[0,0,g-20.4] for g in [g0,g1] for h in [hs[k+1][0]-1e-7,hs[k][1]+1e-7] for p in [rc.control(F,g,h)]]);lob=ppb.min(axis=0)-dmax*dt[:,None];hib=ppb.max(axis=0)+dmax*dt[:,None];midb=(lob+hib)/2;errb=np.linalg.norm((hib-lob)/2,axis=1)
  curves=[]
  for i,sign in enumerate(signs):
   anchor=np.array([23+17*(i%3),15.5+9*(i//3),-103.6]);reflect=np.array([1,sign,1]);p=mid*reflect+anchor;rr=radius+err+.05 # independently variable KA anchor height
   curves.append((p,rr));total+=len(p)
   # Source checks are broad-phased by full box distance, never by an x cutoff.
   for j in range(0,len(p),128):
    pts=p[j:j+128];delta=np.maximum(np.maximum(ob[None,:,:3]-pts[:,None,:],pts[:,None,:]-ob[None,:,3:]),0);ds=np.linalg.norm(delta,axis=2)-rr[j:j+128,None];a,b=np.unravel_index(ds.argmin(),ds.shape);d=float(ds[a,b])
    if d<minsrc[0]:minsrc=(d,{'gap_interval_mm':[g0,g1],'wire':i+1,'obstacle':obs[b]['id'],'t_cell':j+int(a)})
   walls=np.minimum.reduce([p[:,0]+2,320-p[:,0],p[:,1]+2,300-p[:,1]])-rr;minwall=min(minwall,float(walls.min()))
   for s in solids:
    # Own collet contact is checked separately by analytic flat-exit conditions;
    # generic exemptions do not include its lug, fingers, fasteners or cap.
    if s['kind']=='split_collet' and s['wire']==i+1:continue
    q=midb*reflect+anchor if s['board']=='KB' else p
    radial=radius+errb+.05 if s['board']=='KB' else rr
    d=primitive_distance(q,s,0)-radial
    ix=int(d.argmin());value=float(d[ix])
    if value<minarm[0]:minarm=(value,{'gap_interval_mm':[g0,g1],'wire':i+1,'solid':s['id'],'t_cell':ix,'center_box_mid_mm':p[ix].tolist(),'tube_radius_including_interval_mm':float(rr[ix])})
    if value<.60 and len(findings)<300:findings.append({'gap_interval_mm':[g0,g1],'wire':i+1,'solid':s['id'],'bound_mm':value,'t_cell':ix})
  for i in range(6):
   for j in range(i+1,6):
    a,ra=curves[i];b,rb=curves[j];ds=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2)-ra[:,None]-rb[None,:];minpair=min(minpair,float(ds.min()))
 return {'status':'CONTINUOUS_SOURCE_ENCLOSURE_SCREEN','gap_cells':gap_cells,'interior_curve_cells':curve_cells,'curve_cells':len(t),'enclosed_centerline_cells':total,'source_minimum':minsrc,'carrier_minimum':minarm,'pair_minimum_mm':minpair,'enclosure_minimum_mm':minwall,'carrier_findings_first300':findings,'includes':'All six free cubic curves over full gap20.2..30.7 and length65.9..66.1, complete new carrier solids and all source obstacles. This stage covers free curves; complete checker supplies separate straight/end/contact and solid-sweep records. Bounds use engineering floating arithmetic with padded handle roots; physical C0/C1/C2 remains conditional.'}

def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--static-only',action='store_true');a=p.parse_args();start=time.monotonic();m=read(a.candidate/'mechanical.json.gz');obs=source_obstacles();out={'source_obstacles':len(obs),'solid_count':len(m['solids']),'static':static_screen(m['solids'],obs)}
 if not a.static_only:out['continuous']=wire_screen(m['solids'],obs)
 out['elapsed_seconds']=time.monotonic()-start;out['peak_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['static','continuous']}));print(out['static']['status'])
if __name__=='__main__':main()
