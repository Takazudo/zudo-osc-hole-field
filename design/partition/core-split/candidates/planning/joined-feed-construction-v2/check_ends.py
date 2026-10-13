#!/usr/bin/env python3
"""Conservative straight-end/contact service check. Root-reviewed bounded source run.
No native/routing. Positive clearance comes from covering volumes, not samples.
"""
import argparse,copy,gzip,hashlib,json,math,resource,sys,time
from pathlib import Path
import numpy as np
METHOD=Path(__file__).resolve().parent
ROOT=METHOD.parents[5]
sys.path.insert(0,str(METHOD))
import check_geometry as cg

def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def moved(p,board,t):
 q=np.array(p,copy=True);q[...,2]-=t if board=='KB' else 0.;return q

def bbox_gap(a,b):return np.linalg.norm(np.maximum(np.maximum(a[:3]-b[3:],b[:3]-a[3:]),0),axis=-1)
def cover(land,w,lo,hi,radius,n=48):
 """Spheres enclose whole finite cylinder including disks at both axial ends."""
 need(hi>lo,'empty axis interval');edges=np.linspace(lo,hi,n+1);mid=(edges[:-1]+edges[1:])/2
 return np.array(land)+mid[:,None]*np.array(w),np.full(n,radius+(hi-lo)/(2*n)+1e-9)
def depth(points,land,normal):return (np.asarray(points)[...,2]-land[2])*normal

def authenticate_collet(s,term,proof):
 need(proof['reference_exclusion']['finite_tube_exclusion'],'missing finite exit exclusion')
 need(s['shape']=='finite_cylinder' and s['radius_mm']==2.,'unreviewed collet')
 land=np.array(term['land_xyz_mm']);w=np.array(term['axis_from_land_xyz']);L=term['bridge_axis_length_mm'];ends=np.array(s['axis_endpoints_xyz_mm'])
 need(np.max(np.abs(ends-np.array([land+(L+1)*w,land+(L+2.5)*w])))<1e-8,'collet station/axis mismatch')
 holes=[h['analytic_primitive'] for h in s['holes'] if h['kind']=='own_wire_bore']
 need(len(holes)==1,'missing bore');h=holes[0]
 need(h['radius_mm']>=1.2954 and np.max(np.abs(np.array(h['axis_endpoints_xyz_mm'])-np.array([land+(L+.5)*w,land+(L+3)*w])))<1e-8,'bore mismatch')
 return True

def lug_proxy(s,collet,term):
 """Remove only material within proved own collet annulus, never whole lug."""
 q=copy.deepcopy(s);w=np.array(term['axis_from_land_xyz']);land=np.array(term['land_xyz_mm']);L=term['bridge_axis_length_mm']
 axes=np.array(s['axes_xyz']);half=np.array(s['half_extents_mm']);delta=np.array(s['center_xyz_mm'])-land
 along=delta@w;extent=np.sum(half*np.abs(axes@w));rad=delta-along*w;rn=rad/np.linalg.norm(rad)
 radial_lower=float(np.linalg.norm(rad)-np.sum(half*np.abs(axes@rn)))
 need(radial_lower>=1.2954-1e-8 and along-extent>=L+1-1e-8 and along+extent<=L+2.5+1e-8,'lug not confined to declared annulus overlap class')
 h={k:copy.deepcopy(v) for k,v in collet.items() if k not in ['holes','vertices_xyz_mm','subtract']}
 # The asserted lug axial interval is inside the finite grip, and every lug
 # point is outside the bore. Thus its intersection with this long cylinder
 # equals its intersection with the proved finite collet annulus. Extending
 # the negative primitive avoids a spurious distance to the hole end caps.
 h['axis_endpoints_xyz_mm']=[(np.array(h['axis_endpoints_xyz_mm'][0])-100*w).tolist(),(np.array(h['axis_endpoints_xyz_mm'][1])+100*w).tolist()]
 q['holes'].append({'id':collet['id']+'/proved-annulus-overlap-only','kind':'proved_own_collet_annulus','analytic_primitive':h})
 return q

def shroud_containment(s,term):
 """Exact nominal end-tube containment in cavity/bore or beyond shroud roof."""
 land=np.array(term['land_xyz_mm']);w=np.array(term['axis_from_land_xyz']);normal=-1 if term['board']=='KA' else 1;c=w[2]*normal;radial_z=math.sqrt(1-c*c)
 holes={h['id'].rsplit('/',1)[-1]:h['analytic_primitive'] for h in s['holes']}
 need('termination-cavity' in holes and 'termination-entry' in holes,'shroud holes absent')
 cv=holes['termination-cavity'];en=holes['termination-entry']
 need(en['radius_mm']>=1.7 and np.max(np.abs(np.array(en['axis_endpoints_xyz_mm'])-np.array([land-w,land+5*w])))<1e-8,'entry bore changed')
 verts=np.array(s['vertices_xyz_mm']);cverts=np.array(cg.box_vertices(np.r_[np.array(cv['center_xyz_mm'])-np.abs(np.array(cv['axes_xyz'])).T@np.array(cv['half_extents_mm']),np.array(cv['center_xyz_mm'])+np.abs(np.array(cv['axes_xyz'])).T@np.array(cv['half_extents_mm'])]))
 need(np.max(np.abs(verts[:,:2]-land[:2]))<=2.5+1e-8 and depth(verts,land,normal).max()<=1.5+1e-8,'shroud outer changed')
 need(cv['shape']=='oriented_box' and np.max(np.abs(np.abs(np.array(cv['axes_xyz']))-np.eye(3)))<1e-10 and np.max(np.abs(np.array(cv['center_xyz_mm'])[:2]-land[:2]))<1e-8 and np.min(np.array(cv['half_extents_mm'])[:2])>=2-1e-8 and depth(cverts,land,normal).min()<=-.1+1e-8 and depth(cverts,land,normal).max()>=1-1e-8,'cavity changed')
 # Bare cylinder portion before entry start station -1 lies in lower cavity.
 slow=(.05-radial_z)/c
 xybound=np.abs(w[:2])*abs(slow)+np.sqrt(1-w[:2]**2)
 low_zmax=-c+radial_z
 beyond_zmin=5*c-1.2954*radial_z
 need(np.max(xybound)<2 and low_zmax<1 and beyond_zmin>1.5,'shroud analytic coverage failed')
 return {'bare_before_bore_XY_bound_mm':xybound.tolist(),'bare_before_bore_depth_max_mm':low_zmax,'insulation_beyond_bore_depth_min_mm':beyond_zmin,'scope':'Own designed insulating guide/contact only; requires relative datum/entry containment. Not a generic carrier exemption or insulation qualification.'}

def run(candidate,exit_path,travel_cells=100,axis_cells=48,curve_cells=256):
 start=time.monotonic();files=[candidate/x for x in ['receipt.json','terminals.json','contacts.json.gz','mechanical.json.gz']]+[exit_path,Path(__file__),METHOD/'check_geometry.py'];seals={str(p):sha(p) for p in files}
 feed=ROOT/'circuit/routing/epic-242/decision-pilots/feed-arrangement'
 lock=read(feed/'source-lock.json')
 for name,digest in lock['files'].items():
  need(sha(ROOT/name)==digest,'inherited source drift '+name);seals[str(ROOT/name)]=digest
 for name in ['source-lock.json','reconciled-contract.json','offset-proposal.json']:
  seals[str(feed/name)]=sha(feed/name)
 proof=read(exit_path)
 for p,h in proof['source_sha256'].items():need(sha(p)==h,'exit proof source drift '+p)
 need(proof['reference_exclusion']['finite_tube_exclusion'] and proof['insulation_cut']['remaining_gap_mm']>.25,'unproved own masks')
 mech=read(candidate/'mechanical.json.gz');contacts=read(candidate/'contacts.json.gz');terms=read(candidate/'terminals.json');solids=mech['solids'];obs=cg.source_obstacles();lookup={s['id']:s for s in solids};ends=[];contact_checks=0;own_proofs=[]
 for term in mech['wire_termination_regions']:
  b=term['board'];wire=term['wire'];key=f'{b}/w{wire}';land=np.array(term['land_xyz_mm']);w=np.array(term['axis_from_land_xyz']);normal=-1 if b=='KA' else 1;c=w[2]*normal;L=term['bridge_axis_length_mm']
  need(abs(np.linalg.norm(w)-1)<1e-10 and term['insulation_start_axis_mm']==3.75 and term['insulation_start_tolerance_mm']==.05,'end class mismatch')
  solder=lookup[key+'/solder-envelope']
  need(solder['shape']=='oriented_box' and np.max(np.abs(np.abs(np.array(solder['axes_xyz']))-np.eye(3)))<1e-10 and np.max(np.abs(np.array(solder['center_xyz_mm'])[:2]-land[:2]))<1e-8 and np.max(np.abs(np.array(solder['half_extents_mm'])-[2,2,.025]))<1e-8 and abs((solder['center_xyz_mm'][2]-land[2])*normal-.025)<1e-8,'own solder mask changed')
  collet=lookup[key+'/collet'];authenticate_collet(collet,term,proof);sp=shroud_containment(lookup[key+'/termination-shroud'],term);own_proofs.append({'id':key,'collet':True,'shroud':sp})
  # Clip bare metal by board-parallel z=.05; sphere cover deliberately overbounds it.
  slow=(.05-math.sqrt(1-c*c))/c
  parts=[]
  for label,lo,hi,r in [('bare-metal',slow,3.80,1.),('original-insulation',3.70,L+2.5,1.2954)]:
   p,rr=cover(land,w,lo,hi,r,axis_cells);parts.append({'label':label,'points':p,'radii':rr,'bounds':np.r_[(p-rr[:,None]).min(0),(p+rr[:,None]).max(0)]})
  ct=next(x for x in contacts if x['board']==b and x['wire']==wire)
  for patch in ct['foil_patches']:
   for tag in ['tip_vertices_xyz_mm','copper_end_vertices_xyz_mm']:
    vs=np.array(patch[tag]);delta=vs-land;stations=delta@w;rad=np.linalg.norm(delta-stations[:,None]*w,axis=1)
    need(np.max(rad)<=1+1e-8 and np.min(depth(vs,land,normal))>=.05-1e-8 and np.max(stations)<=L+2.5+1e-8,'actual copper primitive outside declared end union')
   fv=np.array(patch['foil_vertices_xyz_mm']);need(np.max(np.abs(fv[:,:2]-land[:2]))<=2+1e-8 and np.max(np.abs(fv[:,2]-land[2]))<1e-8,'solder support outside own landing')
   contact_checks+=1
  ends.append({'board':b,'wire':wire,'term':term,'key':key,'parts':parts,'collet':collet})
 minima={k:[math.inf,None] for k in ['source','carrier','foreign_land','foreign_end','foreign_free']};findings=[];pairs_checked=0
 def record(kind,value,witness,threshold):
  if value<minima[kind][0]:minima[kind]=[float(value),witness]
  if value<threshold and len(findings)<1000:findings.append({'kind':kind,'bound_mm':float(value),'required_mm':threshold,**witness})
 # Rigid ends vs rigid source/carrier/land, interval relative translation.
 ts=np.linspace(0,10.1,travel_cells+1)
 for low,high in zip(ts,ts[1:]):
  t=(low+high)/2;half=(high-low)/2
  for e in ends:
   for part in e['parts']:
    pts=moved(part['points'],e['board'],t);rr=part['radii'];bounds=np.r_[(pts-rr[:,None]).min(0),(pts+rr[:,None]).max(0)]
    for o in obs:
     box=np.array(o['box'],float);moving=o['moves'];box[[2,5]]-=t if moving else 0;err=(half+.10) if moving!=(e['board']=='KB') else 0
     if bbox_gap(bounds,box)>.70+err:continue
     dd=np.maximum(np.maximum(box[:3]-pts,pts-box[3:]),0);dist=np.linalg.norm(dd,axis=1)-rr-err;ix=int(dist.argmin());pairs_checked+=1
     record('source',dist[ix],{'end':e['key'],'part':part['label'],'obstacle':o['id'],'travel_mm':[low,high],'axis_cell':ix},.70)
    for s in solids:
     own=s['board']==e['board'] and s.get('wire')==e['wire']
     if own and s['id'] in (e['key']+'/collet',e['key']+'/termination-shroud',e['key']+'/solder-envelope'):continue # authenticated exact contact masks above
     obj=lug_proxy(s,e['collet'],e['term']) if own and s['kind'] in ('clamp_lug','clamp_lug_tongue') else s
     err=(half+.10) if (s['board']=='KB')!=(e['board']=='KB') else 0
     sb=cg.aabb(s['vertices_xyz_mm']);sb[[2,5]]-=t if s['board']=='KB' else 0
     if bbox_gap(bounds,sb)>.60+err:continue
     dist=cg.primitive_distance(pts,obj,t if s['board']=='KB' else 0)-rr-err;ix=int(dist.argmin());pairs_checked+=1
     record('carrier',dist[ix],{'end':e['key'],'part':part['label'],'solid':s['id'],'travel_mm':[low,high],'axis_cell':ix},.60)
    for term in terms:
     if term['board']==e['board'] and term['wire']==e['wire']:continue
     q=term['copper_xy_mm'];z=term['center_xyz_mm'][2]-(t if term['board']=='KB' else 0);box=np.array([q[0],q[1],z,q[2],q[3],z]);err=(half+.10) if (term['board']=='KB')!=(e['board']=='KB') else 0
     if bbox_gap(bounds,box)>.70+err:continue
     delta=np.maximum(np.maximum(box[:3]-pts,pts-box[3:]),0);dist=np.linalg.norm(delta,axis=1)-rr-err;ix=int(dist.argmin())
     record('foreign_land',dist[ix],{'end':e['key'],'land':term['id'],'part':part['label'],'travel_mm':[low,high]},.70)
  for i,e in enumerate(ends):
   for f in ends[i+1:]:
    if e['wire']==f['wire']:continue
    err=half+.10 if e['board']!=f['board'] else 0
    for pa in e['parts']:
     a=moved(pa['points'],e['board'],t)
     for pb in f['parts']:
      b=moved(pb['points'],f['board'],t);dist=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2)-pa['radii'][:,None]-pb['radii'][None,:]-err
      record('foreign_end',float(dist.min()),{'ends':[e['key'],f['key']],'parts':[pa['label'],pb['label']],'travel_mm':[low,high]},.85)
 # End volumes vs every FOREIGN free cubic, enclosing whole g/h/t rectangles.
 F=cg.rc.Family();gs=np.linspace(*F.gap_range,travel_cells+1);hs=[(cg.rc.handle(F,g,F.free_length_range_mm[0]),cg.rc.handle(F,g,F.free_length_range_mm[1])) for g in gs];tt=(np.arange(curve_cells)+.5)/curve_cells;dt=.5/curve_cells
 for k,(g0,g1) in enumerate(zip(gs,gs[1:])):
  ctr=[cg.rc.control(F,g,h) for g in [g0,g1] for h in [hs[k+1][0]-1e-7,hs[k][1]+1e-7]];pp=np.array([cg.rc.position(p,tt) for p in ctr]);der=np.max(np.abs([3*(p[1:]-p[:-1]) for p in ctr]),axis=(0,1));lo=pp.min(0)-der*dt;hi=pp.max(0)+der*dt;mid=(lo+hi)/2;rad=1.2954+np.linalg.norm((hi-lo)/2,axis=1)+.05;shift=(g0+g1)/2-20.4
  for e in ends:
   for i,sign in enumerate([1,-1,1,1,-1,1]):
    if i+1==e['wire']:continue
    curve=mid*np.array([1,sign,1])+np.array([23+17*(i%3),15.5+9*(i//3),-103.6]);err=(g1-g0)/2+.20 if e['board']=='KB' else 0
    for part in e['parts']:
     p=moved(part['points'],e['board'],shift);dist=np.linalg.norm(p[:,None,:]-curve[None,:,:],axis=2)-part['radii'][:,None]-rad[None,:]-err
     record('foreign_free',float(dist.min()),{'end':e['key'],'part':part['label'],'free_wire':i+1,'gap_interval_mm':[g0,g1]},.85)
 for p,h in seals.items():need(sha(p)==h,'input drift '+p)
 for key,value in minima.items():
  if not math.isfinite(value[0]):minima[key]=[None,'Every pair excluded by conservative broad-phase threshold; no narrow candidate.']
 return {'status':'CONSERVATIVE_END_VOLUME_SCREEN_CLEAR' if not findings else 'CONSERVATIVE_END_VOLUME_BOUNDS_UNRESOLVED','input_sha256':seals,'end_count':len(ends),'finite_contact_supports_checked':contact_checks,'travel_cells':travel_cells,'axis_cells':axis_cells,'curve_cells':curve_cells,'source_objects':len(obs),'rigid_pair_candidates_checked':pairs_checked,'minima':minima,'findings_first1000':findings,'own_contact_proofs':own_proofs,'lug_proxy_equivalence':'Both lug and tongue must lie wholly within actual grip axial interval and wholly outside bore. On these solids only, long-cylinder subtraction equals finite proved-collet-annulus subtraction; no material outside the proved annulus is exempt.','owned_insulation_board_gap':proof['insulation_cut'],'scope':['Sphere chains enclose full finite cylinders, including both disks. Bare metal cover overbounds the foil-clipped cylinder; only the authenticated own solder/collet/shroud contacts are removed from checks. Negative bounds may be conservative false positives, never definite collision proof.','All19 tip/copper endpoints lie in the convex core cylinder; solder foil/tip vertices are within intended4x4 landing prism. Actual continuous cap/foil/barrel process remains conditional.','Actual C0/C1/C2, datum/retention/thermal capability remains conditional. Source=.70, carrier=.60, foreignwire=.85 nominal clearances carry process allocations. Own terminal strip uses its separately charged .45 closure and .25 residual criterion.','Checker covers straight ends against source, foreignlands, complete carrier outer primitives with holes, foreign ends and every foreign freecurve. Root separately checks solid-solid service, board/enclosure and all100tool access.','No full assembly pass follows from this helper alone.'],'elapsed_seconds':time.monotonic()-start,'native':False}

if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--exit-proof',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();result=run(a.candidate,a.exit_proof);a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({k:result[k] for k in ['status','end_count','finite_contact_supports_checked','elapsed_seconds']}))
