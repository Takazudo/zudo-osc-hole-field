#!/usr/bin/env python3
"""Saved analytic primitive joints; no regeneration/sweep/native/placement search."""
import argparse,resource,time,json,gzip,hashlib,itertools
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
import numpy as np
START=time.monotonic()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def frame(o):
 if o['shape']=='oriented_box':return np.array(o['center_xyz_mm']),np.array(o['axes_xyz']),np.array(o['half_extents_mm'])
 a,b=np.array(o['axis_endpoints_xyz_mm']);w=b-a;return a,w/np.linalg.norm(w),np.linalg.norm(w)
def inside(o,pts):
 """Signed exact Euclidean distance to primitive boundary, positive inside."""
 pts=np.atleast_2d(pts)
 if o['shape']=='oriented_box':
  c,A,H=frame(o);q=np.abs((pts-c)@A.T)-H;outside=np.linalg.norm(np.maximum(q,0),axis=1);return np.where(np.max(q,axis=1)>0,-outside,-np.max(q,axis=1))
 a,w,L=frame(o);d=pts-a;s=d@w;rad=np.linalg.norm(d-s[:,None]*w,axis=1);q=np.c_[rad-o['radius_mm'],np.maximum(-s,s-L)];outside=np.linalg.norm(np.maximum(q,0),axis=1);return np.where(np.max(q,axis=1)>0,-outside,-np.max(q,axis=1))
def material(o,pts):
 m=inside(o,pts)
 for hole in o.get('holes',[]):m=np.minimum(m,-inside(hole['analytic_primitive'],pts))
 return m
def bounds(o):
 if o['shape']=='oriented_box':
  c,A,H=frame(o);r=np.abs(A).T@H;return c-r,c+r
 a,w,L=frame(o);r=o['radius_mm']*np.sqrt(np.maximum(0,1-w*w));return np.minimum(a,a+L*w)-r,np.maximum(a,a+L*w)+r

def interior_witness(a,b):
 la,ha=bounds(a);lb,hb=bounds(b);lo=np.maximum(la,lb);hi=np.minimum(ha,hb)
 if np.any(hi<lo-1e-9):return None
 # Only witness discovery uses this box; certificate is exact analytic distance.
 pts=np.array(list(itertools.product(*[np.linspace(l,h,11) for l,h in zip(lo,hi)])))
 margin=np.minimum(material(a,pts),material(b,pts));k=int(np.argmax(margin));r=float(margin[k])
 if r<=1e-7:return None
 r=max(0,r-1e-9)
 return {'type':'POSITIVE_VOLUME_ANALYTIC_BALL','center_xyz_mm':pts[k].tolist(),'radius_mm':r,'volume_lower_mm3':4*np.pi*r**3/3,'proof':'Exact signed distances to both outer analytic primitives and all actual boolean holes exceed ballradius; no AABB-only inference.'}

def face_witness(a,b):
 if a['shape']!=b['shape'] or a['shape']!='oriented_box':return None
 ca,A,Ha=frame(a);cb,B,Hb=frame(b)
 if not np.allclose(A,B,atol=1e-12):return None
 bc=(cb-ca)@A.T
 for axis in range(3):
  for sign in (-1,1):
   plane=sign*Ha[axis]
   if abs(plane-(bc[axis]-sign*Hb[axis]))>1e-8:continue
   others=[j for j in range(3) if j!=axis];lo=np.maximum(-Ha,bc-Hb);hi=np.minimum(Ha,bc+Hb)
   if any(hi[j]<=lo[j] for j in others):continue
   for uv in itertools.product(*[np.linspace(lo[j],hi[j],11)[1:-1] for j in others]):
    q=np.zeros(3);q[axis]=plane;q[others]=uv;point=ca+q@A;r=min(min(q[j]-lo[j],hi[j]-q[j]) for j in others)
    for o in [a,b]:
     if inside(o,[point])[0]<-1e-8:r=-1;break
     for hole in o.get('holes',[]):r=min(r,float(-inside(hole['analytic_primitive'],[point])[0]))
    if r>1e-7:
     r-=1e-9;return {'type':'POSITIVE_AREA_SHARED_FACE_DISK','center_xyz_mm':point.tolist(),'normal_xyz':A[axis].tolist(),'radius_mm':r,'area_lower_mm2':np.pi*r*r,'proof':'Opposing coincident oriented-box planes, interior tangentdisk separated from every remaining outer edge and all true holes.'}
 return None

def captured(a,b):
 for hole in a.get('holes',[]):
  q=hole['analytic_primitive']
  fields=['shape','center_xyz_mm','axes_xyz','half_extents_mm'] if b['shape']=='oriented_box' else ['shape','axis_endpoints_xyz_mm','radius_mm']
  if all(q.get(k)==b.get(k) for k in fields):
   if b['shape']=='oriented_box':
    h=np.array(b['half_extents_mm']);area=8*(h[0]*h[1]+h[0]*h[2]+h[1]*h[2])
   else:
    _,_,length=frame(b);r=b['radius_mm'];area=2*np.pi*r*(r+length)
   return {'type':'EXACT_CAVITY_INTERFACE','shared_surface_area_mm2':float(area),'proof':'Cavity primitive exactly equals inserted solid; interface is boundary, not overlapping material.','limit':'Geometric interface only; fabrication sequence, fit tolerance and axial retention are separate. Other holes may subtract portions of this interface; nominal total area is not qualified bearing area.'}
 return None

def tangent_disk(o,point,normal,radius,touch_holes=()):
 p=np.asarray(point);n=np.asarray(normal);n=n/np.linalg.norm(n)
 if o['shape']=='oriented_box':
  c,A,H=frame(o);m=H-np.abs((p-c)@A.T);f=np.sqrt(np.maximum(0,1-(A@n)**2))
  if np.any(m<radius*f-1e-8):return False
 else:
  a,w,L=frame(o)
  if abs(abs(w@n)-1)>1e-9:return False
  t=(p-a)@w;r=np.linalg.norm(p-a-t*w)
  if t < -1e-8 or t>L+1e-8 or r+radius>o['radius_mm']+1e-9:return False
 for h in o.get('holes',[]):
  obj=h['analytic_primitive']
  if h['id'] in touch_holes:
   if abs(float(inside(obj,[p])[0]))>1e-8 or not tangent_disk(obj,p,n,radius):return False
  elif -inside(obj,[p])[0]<radius-1e-9:return False
 return True

def bearing_record(name,a,b,point,normal,touch_a=(),touch_b=()):
 radius=.02;point=np.array(point);normal=np.array(normal)
 ok=tangent_disk(a,point,normal,radius,touch_a) and tangent_disk(b,point,normal,radius,touch_b)
 # Both sides must contain material; overlapping material alone is not this test.
 side=lambda o: [float(material(o,[point+v*1e-6*normal])[0]) for v in [-1,1]]
 sides=[side(a),side(b)]
 ok=ok and ((sides[0][0]>0 and sides[1][1]>0) or (sides[0][1]>0 and sides[1][0]>0))
 return {'id':name,'status':'POSITIVE_AREA_ANALYTIC_BEARING' if ok else 'UNPROVED','center_xyz_mm':point.tolist(),'normal_xyz':normal.tolist(),'disk_radius_mm':radius,'area_lower_mm2':float(np.pi*radius**2) if ok else 0,'material_side_margins_mm':sides,'proof':'Entire tangentdisk satisfies analytic outer constraints and actual hole exclusions; permitted shared cavityboundaries exact. Opposite material neighborhoods establish bearing, not AABB overlap.'}

def axial_interval(o,origin,axis):
 if o['shape']=='finite_cylinder':
  a,b=np.array(o['axis_endpoints_xyz_mm']);w=(b-a)/np.linalg.norm(b-a)
  assert abs(abs(float(w@axis))-1)<1e-9
  return sorted([float((a-origin)@axis),float((b-origin)@axis)])
 c,A,H=frame(o);v=np.abs(A@axis)@H;t=float((c-origin)@axis);return [t-v,t+v]

def coaxial_hole_coverage(cap,shaft):
 origin,axis,length=frame(shaft)
 if cap['shape']!='finite_cylinder':return None
 lo,hi=axial_interval(cap,origin,axis);lo=max(0.,lo);hi=min(length,hi)
 assert hi>lo
 intervals=[]
 for h in cap.get('holes',[]):
  q=h['analytic_primitive']
  if q['shape']!='finite_cylinder':continue
  a,w,L=frame(q);radial=np.linalg.norm((a-origin)-((a-origin)@axis)*axis)
  if abs(abs(w@axis)-1)>1e-10 or radial+shaft['radius_mm']>q['radius_mm']-1e-8:continue
  v=axial_interval(q,origin,axis);intervals.append((v[0],v[1],h['id'],q['radius_mm']-radial-shaft['radius_mm']))
 cursor=lo
 for a,b,_,_ in sorted(intervals):
  if a>cursor+1e-9:break
  cursor=max(cursor,b)
 ok=cursor>=hi-1e-9
 return {'status':'PROVED_COAXIAL_SHAFT_CLEARANCE' if ok else 'UNPROVED','shaft_cap_axial_intersection_mm':[lo,hi],'hole_intervals':intervals,'proof':'Parallel coaxial cylinder cutters with strict radial clearance cover the entire shaft/cap axial intersection; union coverage excludes all shaft material from dielectric cap, including floor crossings.'}

def analyze(folder):
 p=folder/'mechanical.json.gz';initial=digest(p);d=rd(p);lookup={o['id']:o for o in d['solids']};assert len(lookup)==len(d['solids']);reports=[]
 for j in d['intended_structural_joints']:
  assert time.monotonic()-START<170
  a,b=lookup[j['a']],lookup[j['b']]
  if j['type']=='own_support_hole_clamp':
   reports.append(j|{'status':'REQUIRES_AXIAL_STACK_NOT_SHAFT_RADIAL_CONTACT','shaft_radius_mm':b['radius_mm'],'bore_radius_mm':1.1});continue
  proof=captured(a,b) if j['type']=='captured_sleeve_fit' else interior_witness(a,b) or face_witness(a,b)
  reports.append(j|{'status':'PROVED_GEOMETRIC_INTERFACE' if proof else 'UNPROVED','proof':proof})
 checks=[]
 for board in ['KA','KB']:
  for i in range(1,7):
   pre=f'{board}/w{i}/';shaft=lookup[pre+'M1-shaft'];origin,w,L=frame(shaft);lug=lookup[pre+'lug'];head=lookup[pre+'M1-head'];nut=lookup[pre+'M1-nut'];l=axial_interval(lug,origin,w);he=axial_interval(head,origin,w);nu=axial_interval(nut,origin,w)
   checks.append({'id':pre+'M1-clamp-stack','head_to_lug_axial_gap_mm':l[0]-he[1],'nut_to_lug_axial_gap_mm':nu[0]-l[1],'status':'AXIAL_BEARING_PLANES_COINCIDE' if abs(l[0]-he[1])<1e-8 and abs(nu[0]-l[1])<1e-8 else 'NO_COMPLETE_AXIAL_CLAMP','head_shaft_join':interior_witness(head,shaft),'nut_shaft_join':interior_witness(nut,shaft),'scope':'Coincident bearingplanes necessary; annular bearingarea is independently verified by bounded tangentdisk below.'})
   # Independent small contactdisk at radial0.70 toward lug n-axis, radius0.02.
   ca,A,H=frame(lug);radial=A[1]
   for nm,obj,surface in [('head',head,l[0]),('nut',nut,l[1])]:
    point=origin+surface*w+.70*radial
    # Moving infinitesimally to each side verifies actual material, not bore.
    plus=material(lug,[point+(1e-6 if nm=='head' else -1e-6)*w])[0]
    minus=material(obj,[point+(-1e-6 if nm=='head' else 1e-6)*w])[0]
    clearholes=min([-inside(h['analytic_primitive'],[point])[0] for h in lug.get('holes',[])]+[1.])
    gap=(l[0]-he[1]) if nm=='head' else (nu[0]-l[1])
    checks.append({'id':pre+nm+'-bearing-patch','point_xyz_mm':point.tolist(),'radius_mm':.02,'status':'POSITIVE_AREA_PATCH' if abs(gap)<1e-8 and plus>0 and minus>0 and clearholes>.02 else 'UNPROVED','scope':'0.02mm tangentdisk at0.70mm radialstation; stays within lugbox, outsideR.55hole and within metalR>=1 head/nut. Material neighborhoods confirm sides.'})
  for i in [1,2]:
   pre=f'{board}/support-{i}/';shaft=lookup[pre+'M2-shaft']
   for part in ['head','nut']:
    cap=lookup[pre+part+'-outer-cap'];metal=lookup[pre+part+'-metal'];bad=interior_witness(cap,shaft)
    checks.append({'id':pre+part+'-cap-shaft','status':'ILLEGAL_MATERIAL_OVERLAP' if bad else 'NO_INTERIOR_WITNESS','overlap':bad,'scope':'No-interior-witness alone is not global nonintersection proof; coaxial bore dimensions below must certify separation.'})
    bores=[h['analytic_primitive'] for h in cap.get('holes',[]) if h['analytic_primitive']['id']!=metal['id']]
    checks.append({'id':pre+part+'-coaxial-separation',**coaxial_hole_coverage(cap,shaft)})
    checks.append({'id':pre+part+'-shaft-floor-bore','status':'DEDICATED_CLEARANCE_BORE_PRESENT' if any(h.get('radius_mm',0)>shaft['radius_mm'] for h in bores) else 'MISSING_SHAFT_CLEARANCE','bores':[{'id':h['id'],'radius_mm':h.get('radius_mm')} for h in bores]})

 # Explicit collar stack and cap attachment interfaces, not shaft-in-hole inference.
 for board,face,nz in [('KA',-101.6,-1),('KB',-126.,1)]:
  normal=np.array([0.,0.,nz]);local=lambda x,y,dep:np.array([x,y,face+nz*dep])
  for i,x in [(1,6.5),(2,311.5)]:
   pre=f'{board}/support-{i}/';lug=lookup[pre+'lug'];fw=lookup[pre+'face-washer'];ow=lookup[pre+'opposite-washer'];hc=lookup[pre+'head-outer-cap'];nc=lookup[pre+'nut-outer-cap'];hm=lookup[pre+'head-metal'];nm=lookup[pre+'nut-metal'];shaft=lookup[pre+'M2-shaft']
   for label,a,b,dep,ta,tb in [('facewasher-lug',fw,lug,.65,(),()),('headcap-oppositewasher',hc,ow,-2.1,(),()),('nutcap-lug',nc,lug,4.65,(),()),('headmetal-capfloor',hm,hc,-2.35,(),(hm['id'],)),('nutmetal-capfloor',nm,nc,4.9,(),(nm['id'],))]:
    checks.append(bearing_record(pre+label,a,b,local(x+1.4,10.5,dep),normal,ta,tb))
   for label,metal in [('headshaft',hm),('nutshaft',nm)]:
    proof=interior_witness(metal,shaft);checks.append({'id':pre+label,'status':'POSITIVE_VOLUME_METAL_JOIN' if proof else 'UNPROVED','proof':proof})
   # Original boardplanes and2.2mm NPTH, sourceidentity in support-bindings.json.
   for label,washer,dep in [('boardface-washer',fw,0),('boardback-washer',ow,-1.6)]:
    point=local(x+1.4,10.5,dep);ok=tangent_disk(washer,point,normal,.02)
    checks.append({'id':pre+label,'status':'SOURCE_PLANE_ANNULAR_PATCH' if ok else 'UNPROVED','center_xyz_mm':point.tolist(),'disk_radius_mm':.02,'source_board_thickness_mm':1.6,'source_hole_radius_mm':1.1,'scope':'Patchradial1.4±.02 liesoutside originalNPTH andinside retainedboardoutline at topcollar; sourcehole/ref identity sealed separately. No PCBstrength orpreloadqualification.'})
  for i in range(1,7):
   pre=f'{board}/w{i}/';sh=lookup[pre+'termination-shroud'];sc,sa,shalf=frame(sh);bond=None
   for dx,dy in itertools.product([-2.25,2.25],repeat=2):
    point=sc+dx*sa[0]+dy*sa[1]-.75*sa[2]
    if tangent_disk(sh,point,normal,.02) and material(sh,[point+1e-6*normal])[0]>0:
     bond={'center_xyz_mm':point.tolist(),'radius_mm':.02,'area_mm2':float(np.pi*.02**2)};break
   checks.append({'id':pre+'shroud-board-bondpatch','status':'SOURCE_PLANE_BOND_PATCH' if bond else 'UNPROVED','proof':bond,'scope':'Positive-area actual dielectric base patch on nominal boardplane, outside cavity/entry holes. Requires declared adhesive and retained bare substrate bond land; no strength/material qualification.'})
   pre=f'{board}/w{i}/';lug=lookup[pre+'lug'];c,A,H=frame(lug);shaft=lookup[pre+'M1-shaft'];origin,axis,L=frame(shaft);bounds_l=axial_interval(lug,origin,axis)
   for label,station in [('head',bounds_l[0]),('nut',bounds_l[1])]:
    cap=lookup[pre+label+'-cap'];point=origin+station*axis+1.30*A[1]
    checks.append(bearing_record(pre+label+'-cap-lug-bondpatch',cap,lug,point,axis))
 assert digest(p)==initial
 out={'status':'GEOMETRIC_JOINT_AUDIT_NOT_STRENGTH_OR_ASSEMBLY_QUALIFICATION','input_mechanical_sha256':initial,'candidate_receipt_sha256':digest(folder/'receipt.json'),'helper_sha256':digest(Path(__file__)),'support_bindings_sha256':digest(folder/'support-bindings.json'),'candidate':str(folder),'intended_joint_count':len(reports),'joint_status_counts':dict(__import__('collections').Counter(r['status'] for r in reports)),'joints':reports,'fastener_checks':checks,'assembly_findings':['Closed beam sleeve/captured core requires explicit insert-molding or split-shell fabrication sequence; no insertion path established by coincident cavity.','Splitcollet has two removable halves: preassemble finger/beam, route wire before final clamp tightening, then solder; actual access/tool envelopes must be validated.','Collet neck geometry is not a shear/creep/load proof; material, preload and retention remain unqualified.','M1 caps with clearance to head/nut need declared attachment to lug or mechanical retention; cavity containment alone does not retain them.','M2 board stack requires original PCB/collar and washer interfaces, no newholes; recorded source2.2mm holes do not prove torque/structural capacity.'],'limits':['Analytic ball/sharedface witnesses account actual primitiveholes; conservative outerpolyhedra not mistaken for material overlap.','Witness search only on fixed savedgeometry, no candidate modifications or newplacement/routing.','No-witness result is UNPROVED, never disjointness or strength PASS.'],'elapsed_seconds':time.monotonic()-START,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0}
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists();r=analyze(a.candidate);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['intended_joint_count','joint_status_counts','elapsed_seconds','peak_memory_KiB']}))
