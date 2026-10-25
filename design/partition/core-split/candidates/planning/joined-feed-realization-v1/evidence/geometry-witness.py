#!/usr/bin/env python3
"""Single three-pose sampled necessary-witness audit; no sweep/fit acceptance."""
import resource,time,json,hashlib,sys,os
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
t0=time.monotonic()
from pathlib import Path
P=Path('/workspace/zudo-osc-hole-field/circuit/routing/epic-242/decision-pilots/feed-arrangement');sys.path.insert(0,str(P))
import robust_curve as rc,check as base
import numpy as np
from scipy.spatial import cKDTree
from importlib.metadata import version
assert version('numpy')=='2.2.6' and version('scipy')=='1.15.3'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seals={str(P/n):H(P/n) for n in ['robust_curve.py','robust-curve.json','check.py','source-lock.json','reconciled-contract.json','offset-proposal.json','process-budget.md']}
for path,h in base.read(P/'source-lock.json')['files'].items():assert H(base.ROOT/path)==h
F=rc.Family();assert F.offset_mm==58 and F.free_length_nominal_mm==66 and F.tail_each_mm==2.5
c=base.read(base.ROOT/'design/partition/core-split/candidates/two.json')['boards'];part=base.read(base.ROOT/'design/partition/partition.json');mech=next(x for x in base.read(base.ROOT/'design/partition/core-split/mechanical/generated/comparison.json')['alternatives'] if x['id']=='two-deep')
over=base.read(P/'reconciled-contract.json')['producer_replacements'];old=base.read(P/'offset-proposal.json');signs=[1,-1,1,1,-1,1];radius=2.5908/2;coords=[(23+17*(i%3),15.5+9*(i//3)) for i in range(6)]
obstacles=[];landrows={};faces={'KA':{'F.Cu':-100.,'B.Cu':-101.6},'KB':{'F.Cu':-126.,'B.Cu':-127.6}}
for board,key,side in [('KA','two-A','B.Cu'),('KB','two-B','F.Cu')]:
 landrows[board]=base.obstacles(c[key],side,mech,part)
 for face in ['F.Cu','B.Cu']:
  for idx,row in enumerate(base.obstacles(c[key],face,mech,part)):
   xy=row['box'];z=faces[board][face]
   zz=[-160,-90] if row['kind'] in ('tool-column','support','loom') else ([z,z+7.3] if face=='F.Cu' else [z-5,z])
   obstacles.append({'id':board+'/'+face+'/'+row['id']+'/'+str(idx),'kind':row['kind'],'board':board,'box':xy[:2]+[zz[0]]+xy[2:]+[zz[1]],'moves':board=='KB' and row['kind'] not in ('tool-column','support','loom')})
for q in old['construction']['bulk_and_monitor_reserves']:
 if '-bulk-' in q['id']:obstacles.append({'id':q['id'],'kind':'new-reserve','board':q['board'],'box':q['box'],'moves':q['board']=='KB'})
m=over['monitor'];xy=m['box_xy_mm'];obstacles.append({'id':m['id'],'kind':'new-monitor','board':'KB','box':xy[:2]+[-132.6]+xy[2:]+[-127.6],'moves':True})
# Every source row is retained: no spatial broad-phase truncation.
lands=[];bridge=2/(-F.direction[2]);v0=np.array(F.direction);v1=v0*np.array([1,-1,1])
for board in ['KA','KB']:
 for i,(x,y) in enumerate(coords):
  a=np.array([x+(58 if board=='KB' else 0),y,(-124 if board=='KB' else -103.6)])
  center=a+((-bridge*v0) if board=='KA' else (bridge*v1))*[1,signs[i],1]
  box=[center[0]-3,center[1]-3,center[0]+3,center[1]+3]
  nearest=min((base.rectgap(box,r['box']),r['id'],r['kind']) for r in landrows[board])
  lands.append({'board':board,'wire':i+1,'center_nominal_xyz_mm':center.tolist(),'reserve_xy_mm':box,'source_gap_mm':nearest[0],'source_obstacle':nearest[1],'source_kind':nearest[2]})

def point_boxes(points,boxes):
 best=(float('inf'),None,None)
 for j in range(0,len(points),128):
  ps=points[j:j+128];delta=np.maximum(np.maximum(boxes[None,:,:3]-ps[:,None,:],ps[:,None,:]-boxes[None,:,3:]),0);ds=np.linalg.norm(delta,axis=2);a,b=np.unravel_index(ds.argmin(),ds.shape)
  if ds[a,b]<best[0]:best=(float(ds[a,b]),j+int(a),int(b))
 return best
assert point_boxes(np.array([[2.,0,0]]),np.array([[0.,-1,-1,1,1,1]]))[0]==1
poses=[]
for travel in [0.,5.,10.1]:
 assert time.monotonic()-t0<115
 gap=20.4+travel;handle=rc.handle(F,gap,66.);controls=rc.control(F,gap,handle);curves=[];labels=[];landpose=[]
 for x in lands:
  a=np.array(x['center_nominal_xyz_mm']);a[2]-=travel if x['board']=='KB' else 0;landpose.append(a)
 boxes=np.array([o['box'] for o in obstacles],float)
 for j,o in enumerate(obstacles):
  if o['moves']:boxes[j,[2,5]]-=travel
 wire_results=[]
 for i,(x,y) in enumerate(coords):
  reflect=np.array([1,signs[i],1]);anchor=np.array([x,y,-103.6]);end=np.array([58.,0,-gap]);p=controls*reflect+anchor
  pieces=[('KA-bridge',np.linspace(-bridge*v0,np.zeros(3),81)),('KA-tail',np.linspace(np.zeros(3),2.5*v0,81)),('free-curve',rc.position(controls,np.linspace(0,1,1001))),('KB-tail',np.linspace(end-2.5*v1,end,81)),('KB-bridge',np.linspace(end,end+bridge*v1,81))]
  pts=np.concatenate([a*reflect+anchor for _,a in pieces]);tags=[(name,k/(len(a)-1)) for name,a in pieces for k in range(len(a))];curves.append(pts);labels.append(tags)
  dist,k,j=point_boxes(pts,boxes);gapobs=dist-radius
  box=boxes[j];closest=np.clip(pts[k],box[:3],box[3:]);
  # [-2,320] x [-2,300] retained enclosure: necessary XY wall clearance.
  wall=np.minimum.reduce([pts[:,0]+2,320-pts[:,0],pts[:,1]+2,300-pts[:,1]])-radius;wi=int(wall.argmin())
  wire_results.append({'wire':i+1,'control_points_xyz_mm':p.tolist(),'nearest_reserved_box':{'gap_mm':gapobs,'obstacle':obstacles[j],'obstacle_box_at_pose':box.tolist(),'wire_center_xyz_mm':pts[k].tolist(),'closest_box_point_xyz_mm':closest.tolist(),'curve_parameter':tags[k],'required_nominal_gap_mm':.70,'violates_nominal_service_budget':gapobs<.70},'enclosure_xy':{'gap_mm':float(wall[wi]),'wire_center_xyz_mm':pts[wi].tolist(),'curve_parameter':tags[wi]}})
 pairs=[]
 for i in range(6):
  tree=cKDTree(curves[i])
  for j in range(i+1,6):
   ds,ii=tree.query(curves[j]);q=int(ds.argmin());k=int(ii[q]);gap=float(ds[q])-2*radius
   pairs.append({'wires':[i+1,j+1],'surface_gap_mm':gap,'points_xyz_mm':[curves[i][k].tolist(),curves[j][q].tolist()],'parameters':[labels[i][k],labels[j][q]],'violates_nominal_pair_budget':gap<.85})
 foreign=[]
 for i in range(6):
  for j,land in enumerate(lands):
   if land['wire']==i+1:continue
   q=land['reserve_xy_mm'];z=landpose[j][2];bb=np.array([[q[0],q[1],z,q[2],q[3],z]])
   dist,k,_=point_boxes(curves[i],bb)
   if dist-radius<.70:foreign.append({'wire':i+1,'foreign_land':land,'surface_gap_mm':dist-radius,'point':curves[i][k].tolist()})
 poses.append({'travel_mm':travel,'free_length_mm':rc.arclength(controls),'handle_mm':handle,'wires':wire_results,'wire_pairs':pairs,'foreign_land_reservation_failures':foreign})
for path,h in seals.items():assert H(Path(path))==h
for path,h in base.read(P/'source-lock.json')['files'].items():assert H(base.ROOT/path)==h
out={'status':'THREE_FIXED_POSE_NECESSARY_WITNESS_AUDIT_NOT_COMPLETE_SWEEP','source_sha256':H(Path(__file__)),'source_hashes':seals,'nominal_family':{'offset_mm':58,'anchor_height_mm':2,'free_length_mm':66,'tail_mm':2.5,'bridge_each_mm':bridge,'wire_OD_mm':2.5908},'obstacle_count':len(obstacles),'land_reservations':lands,'poses':poses,'limitations':['All gaps are sampled actual centerline-to-retained-reservation bounds at three fixed nominal poses; absence of witness is not complete-sweep or tolerance acceptance.','Source reservation boxes conservatively use retained face-height envelopes; intersection proves reservation-model conflict, not necessarily physical component-solid intersection.','Own solder/land contact permitted; stripped insulation geometry and complete revised carrier absent.','No curve optimization, alternative family, native, F3 or physical change.'],'elapsed_seconds':time.monotonic()-t0,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
Path('/tmp/joined-feed-geometry-witness.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'elapsed':out['elapsed_seconds'],'peak':out['peak_memory_KiB'],'obstacles':len(obstacles),'min_land':min(x['source_gap_mm'] for x in lands),'poses':[{'travel':q['travel_mm'],'min_source':min(w['nearest_reserved_box']['gap_mm'] for w in q['wires']),'min_pair':min(w['surface_gap_mm'] for w in q['wire_pairs']),'min_enclosure':min(w['enclosure_xy']['gap_mm'] for w in q['wires'])} for q in poses]}))
