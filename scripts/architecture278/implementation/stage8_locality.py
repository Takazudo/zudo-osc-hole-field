"""Bounded source-only feedback corridors; never native routing or qualification."""
import argparse,copy,heapq,itertools,json,math
from pathlib import Path
import assembly as a
import front_evidence as fe
import stage7_mechanical as old
import stage7_interfaces as interfaces
ROOT=a.ROOT; OUT=a.OUT/'stage8'
PAIRS=[('U3305','8','C3301','1'),('U3305','9','C3301','2'),('U3305','9','R3316','2'),('R3316','1','J1009','T'),('U3305','8','R3314','1'),('R3314','2','R3315','1'),('R3315','2','J1009','T'),('U3305','4','C3308','1'),('U3305','11','C3309','1'),('C3308','2','C3309','2')]
def rotate_package(p,turn):
 q=copy.deepcopy(p);origin=p['origin_mm']
 def xy(v):return a.transform([v[i]-origin[i]for i in (0,1)],origin,turn)
 def box(b):
  pts=[xy(v)for v in itertools.product((b[0],b[2]),(b[1],b[3]))]
  return[min(v[0]for v in pts),min(v[1]for v in pts),max(v[0]for v in pts),max(v[1]for v in pts)]
 q['pads_mm']={pin:[xy(v)for v in pts]for pin,pts in p['pads_mm'].items()};q['box_mm']=box(p['box_mm']);q['through_pad_keepouts_mm']=[box(b)for b in p['through_pad_keepouts_mm']];q['quarter_turn']=(p['quarter_turn']+turn)%4
 return q

def placements_from(seed,spec):
 p=copy.deepcopy(seed)
 for ref,delta in spec['translations_from_stage7_mm'].items():
  assert ref in p and not p[ref]['panel_uid'],'invented or fixed package movement'
  assert len(delta)==2 and all(math.isfinite(v)for v in delta)
  p[ref]=old.move(p[ref],delta)
  p[ref]['pads_xyz_mm']={pin:[xy+[p[ref]['conditional_pad_depth_mm']]for xy in pts]for pin,pts in p[ref]['pads_mm'].items()}
 for ref,turn in spec.get('rotations_from_stage7_quarter_turns',{}).items():
  assert ref in p and not p[ref]['panel_uid']and type(turn)is int and turn in (0,1,2,3),'invalid whole-package rotation'
  p[ref]=rotate_package(p[ref],turn)
  p[ref]['pads_xyz_mm']={pin:[xy+[p[ref]['conditional_pad_depth_mm']]for xy in pts]for pin,pts in p[ref]['pads_mm'].items()}
 assert set(p)==set(seed)and len(p)==56
 return p

def expand(b,r):return[b[0]-r,b[1]-r,b[2]+r,b[3]+r]
def hit(p,q,b):
 # Closed axis-aligned segment against closed rectangle. Tangency is rejected.
 assert p[0]==q[0]or p[1]==q[1],'nonorthogonal segment'
 return max(min(p[0],q[0]),b[0])<=min(max(p[0],q[0]),b[2])and max(min(p[1],q[1]),b[1])<=min(max(p[1],q[1]),b[3])
def clearance_radius(o,r):
 return r+o.get('additional_edge_clearance_mm',0)
def free_segment(p,q,obs,layer,r,exempt_courtyard=None):
 return not any(layer in o['layers']and not(o['kind']=='courtyard'and o['ref']==exempt_courtyard)and hit(p,q,expand(o['box_mm'],clearance_radius(o,r)))for o in obs)
def compress(points):
 out=[]
 for p in points:
  if len(out)>1 and out[-1][2]==p[2]==out[-2][2]and ((out[-2][0]==out[-1][0]==p[0])or(out[-2][1]==out[-1][1]==p[1])):out[-1]=p
  else:out.append(p)
 return out

def endpoint_barrels(points,endpoints):
 rows=[]
 for point,endpoint in zip([points[0],points[-1]],endpoints):
  depth=[20.0,21.6][point[2]];length=abs(depth-endpoint['pad_xyz_mm'][2])
  assert math.isclose(length,0,abs_tol=1e-9)or endpoint['layers']==[0,1],'SMD endpoint face jump'
  rows.append({'ref':endpoint['ref'],'pin':endpoint.get('pin'),'corridor_layer':point[2],'source_pad_z_mm':endpoint['pad_xyz_mm'][2],'barrel_mm':length})
 return rows

def route(start,end,obs,outline,settings):
 """Two-face orthogonal grid with actual-pad fanout and explicitly checked vias.
 Each endpoint may cross only its own courtyard on its short pad escape. Other
 pads and all substrate removals remain obstacles. Grid cells are conservative.
 """
 step=settings['grid_step_mm'];clear=settings['copper_clearance_mm'];r=settings['trace_width_mm']/2+clear;vr=settings['via_diameter_mm']/2+clear
 bounds=[outline[0]+settings['substrate_edge_clearance_mm']+r,outline[1]+settings['substrate_edge_clearance_mm']+r,outline[2]-settings['substrate_edge_clearance_mm']-r,outline[3]-settings['substrate_edge_clearance_mm']-r]
 nx=int((bounds[2]-bounds[0])/step)+1;ny=int((bounds[3]-bounds[1])/step)+1
 def xy(i,j):return[round(bounds[0]+i*step,8),round(bounds[1]+j*step,8)]
 masks=[]
 for radius in [r,vr]:
  blocked=[set(),set()]
  for o in obs:
   b=expand(o['box_mm'],clearance_radius(o,radius)+step/2)
   lo=[max(0,math.ceil((b[k]-bounds[k])/step))for k in (0,1)];hi=[min([nx,ny][k]-1,math.floor((b[k+2]-bounds[k])/step))for k in (0,1)]
   for layer in o['layers']:
    blocked[layer].update((i,j)for i in range(lo[0],hi[0]+1)for j in range(lo[1],hi[1]+1))
  masks.append(blocked)
 escape_diagnostics=[]
 def escapes(endpoint):
  p=endpoint['pad_xyz_mm'][:2];result={};b=endpoint['box_mm']
  for layer in endpoint['layers']:
   for target in [[b[0]-r-step,p[1]],[b[2]+r+step,p[1]],[p[0],b[1]-r-step],[p[0],b[3]+r+step]]:
    i=round((target[0]-bounds[0])/step);j=round((target[1]-bounds[1])/step)
    if not(0<=i<nx and 0<=j<ny):continue
    snap=xy(i,j);corner=[snap[0],target[1]];pts=[p,target,corner,snap]
    blockers=[o['id']for o in obs if layer in o['layers']and not(o['kind']=='courtyard'and o['ref']==endpoint['ref'])and any(hit(u,v,expand(o['box_mm'],clearance_radius(o,r)))for u,v in zip(pts,pts[1:]))]
    escape_diagnostics.append({'ref':endpoint['ref'],'pin':endpoint.get('pin'),'layer':layer,'target_mm':snap,'blocking_obstacle_ids':blockers,'conservative_grid_cell_blocked':(i,j)in masks[0][layer]})
    if any(not(bounds[0]<=v[0]<=bounds[2]and bounds[1]<=v[1]<=bounds[3])for v in pts):continue
    if(i,j)in masks[0][layer]:continue
    if all(free_segment(u,v,obs,layer,r,endpoint['ref'])for u,v in zip(pts,pts[1:])):
     result[(i,j,layer)]=[v+[layer]for v in pts]
  return result
 starts=escapes(start);ends=escapes(end)
 if not starts or not ends:return {'status':'BLOCKED','reason':'No width/clearance-preserving endpoint escape','start_escape_count':len(starts),'end_escape_count':len(ends),'escape_diagnostics':escape_diagnostics,'reserved_other_nets':sorted({o['net']for o in obs if o['kind']in ['reserved_trace','reserved_via']})}
 queue=[];dist={};prev={}
 for s,path in starts.items():dist[s]=sum(math.dist(u[:2],v[:2])for u,v in zip(path,path[1:]));heapq.heappush(queue,(dist[s],s))
 found=None
 while queue:
  cost,state=heapq.heappop(queue)
  if cost!=dist[state]:continue
  if state in ends:found=state;break
  i,j,l=state
  neighbours=[(i+1,j,l),(i-1,j,l),(i,j+1,l),(i,j-1,l)]
  if (i,j)not in masks[1][0]and(i,j)not in masks[1][1]:neighbours.append((i,j,1-l))
  for n in neighbours:
   x,y,z=n
   if not(0<=x<nx and 0<=y<ny)or(x,y)in masks[0][z]:continue
   c=cost+(step if z==l else 3.0) # deterministic via penalty, not electrical length
   if c<dist.get(n,math.inf):dist[n]=c;prev[n]=state;heapq.heappush(queue,(c,n))
 if found is None:return {'status':'BLOCKED','reason':'No connected two-face corridor on conservative grid','start_escape_count':len(starts),'end_escape_count':len(ends),'escape_diagnostics':escape_diagnostics,'reserved_other_nets':sorted({o['net']for o in obs if o['kind']in ['reserved_trace','reserved_via']})}
 states=[found]
 while states[-1]in prev:states.append(prev[states[-1]])
 states.reverse();pts=starts[states[0]]+[xy(i,j)+[l]for i,j,l in states]+list(reversed(ends[found]));pts=compress(pts)
 # Verify exact segment geometry independently of grid occupancy.
 segments=[]
 for i,(p,q)in enumerate(zip(pts,pts[1:])):
  if p[2]!=q[2]:
   assert p[:2]==q[:2]and all(free_segment(p[:2],p[:2],obs,l,vr)for l in [0,1]),'via clearance'
  else:
   exemptions=[None]
   if p[2]in start['layers']:exemptions.append(start['ref'])
   if p[2]in end['layers']:exemptions.append(end['ref'])
   valid=[e for e in exemptions if free_segment(p[:2],q[:2],obs,p[2],r,e)]
   assert valid,'segment clearance'
   segments.append({'from_xy_mm':p[:2],'to_xy_mm':q[:2],'layer':p[2],'endpoint_courtyard_escape_exemption':valid[0]})
 vias=[{'xy_mm':p[:2],'diameter_mm':settings['via_diameter_mm'],'drill_mm':settings['via_drill_mm'],'layers':[0,1]}for p,q in zip(pts,pts[1:])if p[2]!=q[2]]
 terminal=endpoint_barrels(pts,[start,end]);terminal_length=sum(e['barrel_mm']for e in terminal);copper=sum(math.dist(p[:2],q[:2])for p,q in zip(pts,pts[1:]))
 return {'endpoint_THT_barrels':terminal,'endpoint_THT_barrel_mm':terminal_length,'developed_copper_and_barrel_mm':copper+len(vias)*1.6+terminal_length,'status':'CONDITIONAL_CORRIDOR','points_xy_layer':pts,'segments':segments,'vias':vias,'copper_centreline_mm':sum(math.dist(p[:2],q[:2])for p,q in zip(pts,pts[1:])),'via_barrel_mm':len(vias)*1.6,'qualification':'Explicit geometric corridor only; no native routing, plane continuity, parasitics or manufacturing acceptance.'}

def pad_obstacles(placed):
 rows=[]
 for ref,p in placed.items():
  nodes=fe.sexpr((ROOT/p['source']).read_text());sizes={}
  for n in nodes:
   if isinstance(n,list)and n and n[0]=='pad':
    size=list(map(float,fe.field(n,'size')));at=fe.field(n,'at');angle=float(at[2])if len(at)>2 else 0
    if (round(angle/90)+p['quarter_turn'])%2:size.reverse()
    sizes.setdefault(n[1],[]).append((size,n[2]))
  assert set(sizes)==set(p['pads_mm']),'unaccounted footprint pads or holes'
  for pin,pts in p['pads_mm'].items():
   assert len(pts)==len(sizes[pin]),(ref,pin)
   for xy,(size,kind)in zip(pts,sizes[pin]):
    rows.append({'id':f'pad:{ref}:{pin}','kind':'pad','ref':ref,'pin':pin,'net':p['pins'].get(pin),'box_mm':[xy[0]-size[0]/2,xy[1]-size[1]/2,xy[0]+size[0]/2,xy[1]+size[1]/2],'layers':[0,1]if kind in ['thru_hole','np_thru_hole']else[0 if p['side']=='panel'else 1],'source':p['source']})
 return rows

def build():
 spec=json.loads((OUT/'placement-input.json').read_text());seed=json.loads((a.OUT/'stage7/mechanical-report.json').read_text());mech=json.loads((OUT/'mechanical-report.json').read_text());placed=placements_from(seed['placements'],spec)
 assert placed==mech['placements'],'mechanical/locality placement disagreement'
 settings=spec['routing_proposal'];obs=[]
 for ref,p in placed.items():
  if p['board']=='X1-jack':obs.append({'id':'courtyard:'+ref,'kind':'courtyard','ref':ref,'box_mm':p['box_mm'],'layers':[0 if p['side']=='panel'else 1],'source':p['source']})
 obs+=pad_obstacles({r:p for r,p in placed.items()if p['board']=='X1-jack'})
 # Mechanical author supplies conservative removed substrate, not nominal hole centres.
 for c in mech['manufacturing_sweep_bounds']:
  if c['board']=='X1-jack':obs.append(dict(c,kind='substrate',ref=c['id'],layers=[0,1],source='stage8 mechanical manufacturing_sweep_bounds',additional_edge_clearance_mm=max(0,settings['substrate_edge_clearance_mm']-settings['copper_clearance_mm'])))
 for m in mech['mounts']:
  if m['board']=='X1-jack':obs.append({'id':m['id'],'ref':m['id'],'kind':'mount_attachment','box_mm':m['attachment_box_mm'],'layers':[0,1],'source':'stage8 mechanical mounts'})
 for ref,h in mech['header_obstacles'].items():
  if h['board']=='X1-jack':obs.append({'id':ref,'ref':ref,'kind':'header','box_mm':h['box_mm'],'layers':[1],'source':h['source']})
 rows=[]
 for ra,pa,rb,pb in PAIRS:
  net=placed[ra]['pins'][pa];assert net==placed[rb]['pins'][pb]
  endpoints=[]
  for ref,pin in [(ra,pa),(rb,pb)]:
   p=placed[ref];pad=next(o for o in obs if o['kind']=='pad'and o['ref']==ref and o['pin']==pin)
   endpoints.append({'ref':ref,'pin':pin,'pad_xyz_mm':p['pads_xyz_mm'][pin][0],'layers':pad['layers'],'box_mm':p['box_mm']})
  applicable=[o for o in obs if not(o['kind']in ['pad','reserved_trace','reserved_via']and o.get('net')==net)]
  result=route(*endpoints,applicable,mech['boards']['X1-jack']['outline_mm'],settings)
  result.update({'net':net,'endpoints':endpoints,'before_pad_distance_mm':math.dist(seed['placements'][ra]['pads_xyz_mm'][pa][0],seed['placements'][rb]['pads_xyz_mm'][pb][0]),'after_pad_distance_mm':math.dist(endpoints[0]['pad_xyz_mm'],endpoints[1]['pad_xyz_mm']),'obstacle_ids':[o['id']for o in applicable],'width_mm':settings['trace_width_mm'],'clearance_mm':settings['copper_clearance_mm']})
  rows.append(result)
  if result['status']=='CONDITIONAL_CORRIDOR':
   for i,(u,v)in enumerate(zip(result['points_xy_layer'],result['points_xy_layer'][1:])):
    isvia=u[2]!=v[2];radius=settings['via_diameter_mm']/2 if isvia else settings['trace_width_mm']/2
    obs.append({'id':f'reserved:{len(rows)}:{i}','kind':'reserved_via'if isvia else'reserved_trace','ref':f'corridor:{len(rows)}','net':net,'box_mm':expand([min(u[0],v[0]),min(u[1],v[1]),max(u[0],v[0]),max(u[1],v[1])],radius),'layers':[0,1]if isvia else[u[2]],'source':'earlier explicit Stage8 corridor, deterministic PAIRS order'})
 spans=[]
 for net in sorted({n for p in placed.values()for n in p['pins'].values()if n is not None}):
  def span(pop):
   pts=[xy for p in pop.values()for pin,n in p['pins'].items()if n==net for xy in p['pads_xyz_mm'][pin]]
   return max((math.dist(x,y)for x,y in itertools.combinations(pts,2)),default=0)
  before,after=span(seed['placements']),span(placed);spans.append({'net':net,'before_max_mm':before,'after_max_mm':after,'delta_mm':after-before})
 return {'all_net_pad_span_changes':spans,'status':'BOUNDED LOCALITY/CORRIDOR STUDY; NOT ROUTED PCB ACCEPTANCE','source_sha256':a.binding([Path(__file__),Path(__file__).with_name('test_stage8_locality.py'),OUT/'placement-input.json',OUT/'mechanical-report.json',a.OUT/'stage7/mechanical-report.json',Path(old.__file__),Path(fe.__file__),Path(a.__file__),ROOT/'scripts/architecture278/populated_mechanics.py',OUT/'scope.json']+[ROOT/p['source']for p in placed.values()]),'counts':{'packages':len(placed),'fixed':sum(bool(p['panel_uid'])for p in placed.values()),'source_pins':sum(len(p['pins'])for p in placed.values())},'routing_settings':settings,'substrate_scope':'Conservative manufacturing swept-tool bounds plus tolerance and mounting attachments. No ideal nominal cutout substitution.','layer_names':{'0':'panel copper Z20','1':'rear copper Z21.6'},'obstacles':obs,'corridors':rows,'limitations':['Successful corridors reserve copper and via extents against subsequent different nets; failed corridors remain unconnected. Full power/AGND return routing remains OPEN.','Pad escape may traverse only endpoint own courtyard; actual other-net pads and substrate remain excluded.','Courtyards block their own face; plated through pads and substrate removals block both faces.','Via drills/annuli are explicit proposals, not fabrication acceptance.','No universal feedback length or stability threshold inferred.'],'physical_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();s=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';path=OUT/'locality-report.json'
 if args.check:assert path.read_text()==s,'stale locality report'
 else:path.write_text(s)
 print([(x['endpoints'][0]['ref'],x['endpoints'][1]['ref'],x['status'])for x in r['corridors']])
if __name__=='__main__':main()
