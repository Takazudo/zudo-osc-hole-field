"""Stage8 substrate topology repair and explicit unqualified carrier proposal."""
import argparse,copy,itertools,json,math
from collections import deque
from pathlib import Path
import assembly as a
import stage7_mechanical as old
import stage8_locality as locality
ROOT=a.ROOT;OUT=a.OUT/'stage8'
def bounds(boxes):return [min(b[0]for b in boxes),min(b[1]for b in boxes),max(b[2]for b in boxes),max(b[3]for b in boxes)]
def expand(b,d):return[b[0]-d,b[1]-d,b[2]+d,b[3]+d]
def ligaments(cuts,outline):
 rows=[]
 for x,y in itertools.combinations(cuts,2):
  b,c=x['box_mm'],y['box_mm'];gap=None;bridge=None
  if max(b[1],c[1])<min(b[3],c[3]):
   lo,hi=sorted([b,c],key=lambda z:z[0]);gap=hi[0]-lo[2];bridge=[lo[2],max(lo[1],hi[1]),hi[0],min(lo[3],hi[3])]
  if max(b[0],c[0])<min(b[2],c[2]):
   lo,hi=sorted([b,c],key=lambda z:z[1]);gap=hi[1]-lo[3];bridge=[max(lo[0],hi[0]),lo[3],min(lo[2],hi[2]),hi[1]]
  if gap is not None and gap>1e-8:rows.append({'a':x['id'],'b':y['id'],'width_mm':gap,'box_mm':bridge})
 for x in cuts:
  b=x['box_mm'];gaps=[b[0]-outline[0],b[1]-outline[1],outline[2]-b[2],outline[3]-b[3]];boxes=[[outline[0],b[1],b[0],b[3]],[b[0],outline[1],b[2],b[1]],[b[2],b[1],outline[2],b[3]],[b[0],b[3],b[2],outline[3]]]
  rows.extend({'a':x['id'],'b':'outline:'+str(i),'width_mm':g,'box_mm':boxes[i]}for i,g in enumerate(gaps)if g>1e-8)
 return rows

def route_carrier(mounts,hardware,carrier):
 step=.5;radius=carrier['rib_width_mm']/2+carrier['hardware_clearance_mm'];xmin,xmax=-2,320;ymin,ymax=0,298
 node=lambda p:(round(p[0]/step),round(p[1]/step))
 blocked=set()
 for h in hardware:
  b=expand(h['box_mm'],radius)
  blocked.update((i,j)for i in range(math.floor(b[0]/step),math.ceil(b[2]/step)+1)for j in range(math.floor(b[1]/step),math.ceil(b[3]/step)+1))
 anchors={node(x['centre_mm']):x['id']for x in carrier['anchor_proposals']};q=deque(n for n in anchors if n not in blocked);prev={n:None for n in q};owner={n:anchors[n]for n in q}
 while q:
  n=q.popleft()
  for v in [(n[0]+1,n[1]),(n[0]-1,n[1]),(n[0],n[1]+1),(n[0],n[1]-1)]:
   if v in prev or v in blocked or not(xmin+radius<=v[0]*step<=xmax-radius and ymin+radius<=v[1]*step<=ymax-radius):continue
   prev[v]=n;owner[v]=owner[n];q.append(v)
 routes=[]
 for m in mounts:
  n=node(m['centre_mm'])
  if n not in prev:routes.append({'mount':m['id'],'status':'NO PATH within declared envelope/width/clearance','start_in_obstacle':n in blocked});continue
  pts=[];end=n
  while end is not None:pts.append([end[0]*step,end[1]*step]);end=prev[end]
  # Keep endpoints and bends only.
  bends=[pts[0]]+[pts[i]for i in range(1,len(pts)-1)if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])]+[pts[-1]]
  routes.append({'mount':m['id'],'anchor':owner[n],'status':'SOURCE XY ROUTE ONLY; strength/body Z/installation unqualified','centreline_mm':bends,'width_mm':carrier['rib_width_mm'],'z_mm':carrier['z_mm'],'length_mm':(len(pts)-1)*step})
 return routes

def force_routes(placed,headers,boards,mounts,cuts,E):
 rows=[];step=.5;width=1.;h=1.6;I=width*h**3/12
 for board,b in boards.items():
  o=b['outline_mm'];blocked=set()
  for c in cuts:
   if c['board']!=board:continue
   box=expand(c['box_mm'],width/2);blocked.update((i,j)for i in range(math.floor(box[0]/step),math.ceil(box[2]/step)+1)for j in range(math.floor(box[1]/step),math.ceil(box[3]/step)+1))
  own_holes=[box for p in placed.values()if p['board']==board for box in p['through_pad_keepouts_mm']]
  mount_holes=[expand([*m['centre_mm'],*m['centre_mm']],m['hole_diameter_mm']/2)for m in mounts if m['board']==board]
  for box0 in own_holes+mount_holes:
   box=expand(box0,width/2);blocked.update((i,j)for i in range(math.ceil(box[0]/step),math.floor(box[2]/step)+1)for j in range(math.ceil(box[1]/step),math.floor(box[3]/step)+1))
  node=lambda p:(round(p[0]/step),round(p[1]/step));owners={}
  for m in mounts:
   if m['board']!=board:continue
   for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]:
    n=node([m['centre_mm'][0]+dx,m['centre_mm'][1]+dy])
    if n not in blocked:owners[n]=m['id']
  prev={n:None for n in owners};owner=dict(owners);q=deque(prev)
  while q:
   n=q.popleft()
   for v in [(n[0]-1,n[1]),(n[0]+1,n[1]),(n[0],n[1]-1),(n[0],n[1]+1)]:
    if v in prev or v in blocked or not(o[0]+.5<=v[0]*step<=o[2]-.5 and o[1]+.5<=v[1]*step<=o[3]-.5):continue
    prev[v]=n;owner[v]=owner[n];q.append(v)
  points=[(p['ref'],p['origin_mm'],'user load→panel bushing/selector support; residualPCB fractionunknown'if p.get('panel_uid')else'GH insertion/unplug force; mustbe reactedbybacking fixture ifexceedingconditionalstripbudget')for p in list(placed.values())+list(headers.values())if p['board']==board and(p.get('panel_uid')or p.get('end')=='front')]
  pop=[p['origin_mm']for p in placed.values()if p['board']==board];points.append(('uniform_mass_surrogate',[sum(p[i]for p in pop)/len(pop)for i in(0,1)],'Uniformpackage centroid surrogate only; actualPCB/partmass distributionunknown;10g sourceplanningload'))
  for ref,xy,role in points:
   n=node(xy)
   if n not in prev:rows.append({'ref':ref,'board':board,'application_xy_mm':xy,'role':role,'status':'NO conservative1mm substrate strip route'});continue
   points0=[];v=n
   while v is not None:points0.append([v[0]*step,v[1]*step]);v=prev[v]
   entry=[xy,[xy[0],points0[0][1]],points0[0]]
   assert not any(locality.hit(u,v,expand(c['box_mm'],width/2))for u,v in zip(entry,entry[1:])for c in cuts if c['board']==board),'forceentrycrossescut'
   if any(locality.hit(u,v,expand(box,width/2))for u,v in zip(entry,entry[1:])for box in own_holes+mount_holes):rows.append({'ref':ref,'board':board,'application_xy_mm':xy,'role':role,'status':'NO conservative1mm strip: actualapplication entrycrossesownperforation'});continue
   L=(len(points0)-1)*step+sum(math.dist(u,v)for u,v in zip(entry,entry[1:]));allow=.5*3*E*I/L**3 if L else None
   bends=[points0[0]]+[points0[i]for i in range(1,len(points0)-1)if (points0[i][0]-points0[i-1][0],points0[i][1]-points0[i-1][1])!=(points0[i+1][0]-points0[i][0],points0[i+1][1]-points0[i][1])]+[points0[-1]]
   assert not any(locality.hit(u,v,expand(box,width/2))for u,v in zip(entry[:-1]+bends,(entry[:-1]+bends)[1:])for box in own_holes+mount_holes),'forcestripcrossesownperforation'
   rows.append({'ref':ref,'board':board,'application_xy_mm':xy,'role':role,'mount':owner[n],'route_mm':entry[:-1]+bends,'centreline_length_mm':L,'strip_width_mm':width,'conditional_force_for_half_mm_deflection_N':allow,'conditional_uniform_mass_at10g_kg':allow/(10*9.80665)if allow else None,'scope':'Planning straightcantilever surrogate alongunperforated1mm route; notplate/torsionproof. Terminatesonwashercontactmaterial2mm radiallyfrommountcentre; allownthroughpadboundsandallmountdrillsareexcluded. Washerbearing/loadtransferremainsunqualified. Largerforce requiresdefinedlocalbacking/support; material and plate responseunqualified.'})
 return rows

def build_from(placement_spec,mechanical_spec):
 evidence=json.loads((OUT/'fabrication-evidence.json').read_text());fields=evidence['process_fields'];assert mechanical_spec['tool_radius_mm']*2>=fields['minimum_slot_width_mm'];assert mechanical_spec['process_mode']=='REQUESTED_PRECISION_NOT_SUPPLIER_ACCEPTED';assert math.isclose(mechanical_spec['tool_path_tolerance_mm'],mechanical_spec['required_precision_process']['dimension_tolerance_plusminus_mm']+mechanical_spec['required_precision_process']['position_tolerance_plusminus_mm']);assert mechanical_spec['tool_path_tolerance_mm']<=mechanical_spec['required_precision_process']['maximum_total_boundary_allowance_mm']
 prior=json.loads((a.OUT/'stage7/mechanical-report.json').read_text());placed=copy.deepcopy(prior['placements'])
 prior['mounts']=[m for m in prior['mounts']if m['id']not in mechanical_spec['removed_nonfixed_mount_ids']]
 for board in prior['boards']:
  centres=[m['centre_mm']for m in prior['mounts']if m['board']==board];assert len(centres)>=3 and any(abs((v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0]))>1 for u,v,w in itertools.combinations(centres,3));prior['boards'][board]['mount_centres_mm']=centres
 placed=locality.placements_from(prior['placements'],placement_spec)
 cuts=[];identified=[];topology={};manufacturing=[]
 for board,b in prior['boards'].items():
  original=[{'id':f"{r['foreign_ref']}:{r['pad_index']}",'board':board,'box_mm':r['aperture_box_mm'],'z_mm':[20,21.6]}for r in prior['foreign_through_pad_substrate_apertures']if r['board']==board]
  selected=[dict(r,board=board,role='No routed copper exists here in source; removing ligament requires future copper reroute and forbids a structural load credit')for r in ligaments(original,b['outline_mm'])if any(math.isclose(r['width_mm'],v,abs_tol=1e-6)for v in mechanical_spec['join_exact_ligaments_mm'])]
  additions=[{'id':'JOIN:'+r['a']+':'+r['b'],'board':board,'box_mm':r['box_mm'],'z_mm':[20,21.6]}for r in selected];joined=original+additions
  # Collapse touching connected rectangles into conservative single slot reservations.
  changed=True
  while changed:
   changed=False
   for i,j in itertools.combinations(range(len(joined)),2):
    x,y=joined[i],joined[j];b0,b1=x['box_mm'],y['box_mm']
    if max(b0[0],b1[0])<=min(b0[2],b1[2])+1e-8 and max(b0[1],b1[1])<=min(b0[3],b1[3])+1e-8:
     merged=dict(x,id=x['id']+'|'+y['id'],box_mm=bounds([b0,b1]));joined=[c for k,c in enumerate(joined)if k not in(i,j)]+[merged];changed=True;break
  cuts+=joined;identified+=selected
  topology[board]=old.substrate_screen(b['outline_mm'],[c['box_mm']for c in joined])
  # Offset cutter inward: radius is not added to the whole cut boundary.
  # Original0.1mm margin covers nominal rounded corner recession.
  # Retain conservative dimension+position boundary tolerance around nominal joins.
  assert .1>=mechanical_spec['tool_radius_mm']*(1-1/math.sqrt(2)), 'internal corner consumes retained foreign-pad margin'
  d=2*mechanical_spec['tool_path_tolerance_mm']
  manufacturing.extend(dict(c,id='ROUTER:'+c['id'],box_mm=expand(c['box_mm'],d))for c in joined)
 ideal_topology=topology;topology={}
 for board,b in prior['boards'].items():
  o=b['outline_mm'];boxes=[[max(c['box_mm'][0],o[0]),max(c['box_mm'][1],o[1]),min(c['box_mm'][2],o[2]),min(c['box_mm'][3],o[3])]for c in manufacturing if c['board']==board]
  boxes +=[expand([*m['centre_mm'],*m['centre_mm']],m['hole_diameter_mm']/2)for m in prior['mounts']if m['board']==board]
  topology[board]=old.substrate_screen(o,boxes)
 interface=json.loads((OUT/'interface-input.json').read_text());headers=old.transport.transport_geometry(interface)
 objects=list(placed.values())+list(headers.values());hits=lambda obs:[{'obstacle':c['id'],'ref':p['ref'],'board':c['board']}for c in obs for p in objects if p['board']==c['board']and old.hosting.overlap(c['box_mm'],p['box_mm'])]
 pad_rows=[]
 for p in objects:
  if p['board']not in prior['boards']:continue
  counters={}
  for node0 in a.c.sexpr((ROOT/p['source']).read_text()):
   if not isinstance(node0,list)or not node0 or node0[0]!='pad':continue
   pin=node0[1];idx=counters.get(pin,0);counters[pin]=idx+1;centre=p['pads_mm'][pin][idx];w,h=map(float,a.c.field(node0,'size'));at=a.c.field(node0,'at');angle=(float(at[2])if len(at)>2 else 0)+p['quarter_turn']*90;theta=math.radians(angle);dx=(abs(w*math.cos(theta))+abs(h*math.sin(theta)))/2;dy=(abs(w*math.sin(theta))+abs(h*math.cos(theta)))/2;b=[centre[0]-dx,centre[1]-dy,centre[0]+dx,centre[1]+dy]
   distances=[]
   for c in manufacturing:
    if c['board']!=p['board']:continue
    q=c['box_mm'];sx=max(q[0]-b[2],b[0]-q[2]);sy=max(q[1]-b[3],b[1]-q[3]);gap=math.hypot(max(0,sx),max(0,sy))if sx>=0 or sy>=0 else max(sx,sy);distances.append((gap,c['id']))
   gap,nearest=min(distances);pad_rows.append({'ref':p['ref'],'pin':pin,'box_mm':b,'type':node0[2],'fixed':bool(p.get('panel_uid')),'minimum_cut_boundary_gap_mm':gap,'nearest_cut':nearest,'required_edge_clearance_mm':mechanical_spec['proposed_pad_edge_clearance_mm'],'classification':'CUT_INTERSECTS_PAD'if gap<0 else'BELOW_PROPOSED_EDGE_CLEARANCE'if gap<mechanical_spec['proposed_pad_edge_clearance_mm']else'SOURCE_PAD_BOUND_CLEAR'})
 mount_hits=[{'obstacle':c['id'],'mount':m['id']}for c in manufacturing for m in prior['mounts']if c['board']==m['board']and old.hosting.overlap(c['box_mm'],m['attachment_box_mm'])]
 carrier=mechanical_spec['carrier'];rails=[{'id':'CROSSMEMBER:'+str(y),'box_mm':[3,y-carrier['crossmember_width_mm']/2,315,y+carrier['crossmember_width_mm']/2],'z_mm':carrier['z_mm']}for y in carrier['crossmember_y_mm']]
 # Explicit links from every boss to its closest crossmember; no disconnected floating mounts.
 for m in prior['mounts']:
  x,y=m['centre_mm'];target=min(carrier['crossmember_y_mm'],key=lambda v:abs(v-y));rails.append({'id':'BOSS_LINK:'+m['id'],'box_mm':[x-2.5,min(y,target)-2.5,x+2.5,max(y,target)+2.5],'z_mm':carrier['z_mm']})
 lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text());hardware=a.locked_hardware(lock['placements'])
 projections=[{'carrier':r['id'],'fixed_ref':h['ref'],'classification':'UNKNOWN actual body Z; projected occupied hardware cannot be assumed free'}for r in rails for h in hardware if old.hosting.overlap(r['box_mm'],h['box_mm'])]
 route_obstacles=hardware+[p for p in placed.values()if p['side']=='panel'and not p['panel_uid']]
 routes=route_carrier(prior['mounts'],route_obstacles,carrier)
 segments=[{'id':r['mount']+':'+str(i),'box_mm':expand(bounds([[*p,*p],[*q,*q]]),r['width_mm']/2),'z_mm':r['z_mm']}for r in routes if 'centreline_mm'in r for i,(p,q)in enumerate(zip(r['centreline_mm'],r['centreline_mm'][1:]))]
 carrier_hits=[{'member':s['id'],'fixed_ref':h['ref']}for s in segments for h in route_obstacles if old.hosting.overlap(s['box_mm'],h['box_mm'])]
 anchor_hits=[{'anchor':v['id'],'fixed_ref':h['ref']}for v in carrier['anchor_proposals']for h in hardware if old.hosting.overlap(expand([*v['centre_mm'],*v['centre_mm']],carrier['anchor_head_tool_diameter_mm']/2),h['box_mm'])]
 material=json.loads((OUT/'material-evidence.json').read_text());beam=[]
 for r in routes:
  if 'centreline_mm'not in r:continue
  spans=[math.dist(p,q)for p,q in zip(r['centreline_mm'],r['centreline_mm'][1:])];L=max(spans);F=carrier['planning_force_N'];E=material['E_MPa'];w=carrier['rib_width_mm']
  for depth in [2,carrier['rib_depth_mm']]:
   I=w*depth**3/12;deflection=F*L**3/(3*E*I);stress=6*F*L/(w*depth**2)
   beam.append({'mount':r['mount'],'path_length_mm':r['length_mm'],'longest_straight_segment_mm':L,'rib_depth_mm':depth,'full_path_planning_pass':F*r['length_mm']**3/(3*E*I)<=carrier['planning_deflection_limit_mm'],'force_N':F,'cantilever_segment_deflection_mm':deflection,'cantilever_segment_stress_MPa':stress,'full_path_straight_surrogate_deflection_mm':F*r['length_mm']**3/(3*E*I),'full_path_straight_surrogate_status':'Sensitivity only, not a valid foldedframe proof; torsion/joints mustbe analysed separately','planning_pass':deflection<=carrier['planning_deflection_limit_mm']and stress<=carrier['planning_stress_limit_MPa'],'scope':'Straightsegment cantilever sensitivity only; bends/torsion/jointrotation not bounded by this estimate; no globalframe structuralpass'})
 alternatives=[]
 for width in [4,5]:
  variant=copy.deepcopy(carrier);variant['rib_width_mm']=width;rr=route_carrier(prior['mounts'],route_obstacles,variant);alternatives.append({'rib_width_mm':width,'unreachable_mounts':[r['mount']for r in rr if 'centreline_mm'not in r],'status':'REJECTED widthalternative cannot connectallmounts'})
 precision=mechanical_spec['required_precision_process'];requested=precision['dimension_tolerance_plusminus_mm']+precision['position_tolerance_plusminus_mm'];requested_margins=[]
 for p in pad_rows:
  b=p['box_mm'];board=objects[next(i for i,v in enumerate(objects)if v['ref']==p['ref'])]['board'];gaps=[]
  for c in cuts:
   if c['board']!=board:continue
   q=expand(c['box_mm'],2*requested);sx=max(q[0]-b[2],b[0]-q[2]);sy=max(q[1]-b[3],b[1]-q[3]);gaps.append(math.hypot(max(0,sx),max(0,sy))if sx>=0 or sy>=0 else max(sx,sy))
  requested_margins.append({'ref':p['ref'],'pin':p['pin'],'minimum_cut_boundary_gap_mm':min(gaps)})
 laminate=json.loads((OUT/'laminate-evidence.json').read_text());pcb_sensitivity=[]
 for board,b in prior['boards'].items():
  mm=[m['centre_mm']for m in prior['mounts']if m['board']==board];points=[(p['ref'],p['origin_mm'])for p in objects if p['board']==board];points += [('outlinecorner'+str(i),p)for i,p in enumerate([[b['outline_mm'][0],b['outline_mm'][1]],[b['outline_mm'][2],b['outline_mm'][1]],[b['outline_mm'][2],b['outline_mm'][3]],[b['outline_mm'][0],b['outline_mm'][3]]])]
  farthest=max((min(math.dist(p,v)for v in mm),ref,p)for ref,p in points);L=farthest[0];width=topology[board]['minimum_axis_aligned_positive_web_mm'];thick=1.6;I=width*thick**3/12;E=laminate['E_cross_MPa']
  pcb_sensitivity.append({'board':board,'maximum_nearest_mount_distance_mm':L,'at_ref':farthest[1],'point_mm':farthest[2],'surrogate_minimum_web_width_mm':width,'laminate_E_MPa':E,'force_sensitivity':[{'force_N':F,'cantilever_deflection_mm':F*L**3/(3*E*I),'bending_stress_MPa':6*F*L/(width*thick**2)}for F in [5,30]],'scope':'Diagnostic extreme strip sensitivity, not actualplate loadsharing or validperforatedboardproof. Panelnuts reactexternaljackloads; unrestrainedserviceforce cannotbe qualified by thismodel. Factorysupport duringplug/unplug and actualplate analysis remainrequired.'})
 standard_margins=[]
 standard_allowance=fields['cutout_dimension_tolerance_plusminus_mm']+fields['cutout_position_tolerance_plusminus_mm']
 for p in pad_rows:
  b=p['box_mm'];board=next(v['board']for v in objects if v['ref']==p['ref']);gaps=[]
  for c in cuts:
   if c['board']!=board:continue
   q=expand(c['box_mm'],2*standard_allowance);sx=max(q[0]-b[2],b[0]-q[2]);sy=max(q[1]-b[3],b[1]-q[3]);gaps.append(math.hypot(max(0,sx),max(0,sy))if sx>=0 or sy>=0 else max(sx,sy))
  standard_margins.append({'ref':p['ref'],'pin':p['pin'],'minimum_cut_boundary_gap_mm':min(gaps)})
 force_rows=force_routes(placed,headers,prior['boards'],prior['mounts'],manufacturing,laminate['E_cross_MPa'])
 source_pairs=[{'a':p['ref'],'b':q['ref']}for p,q in itertools.combinations(objects,2)if p['board']==q['board']and old.hosting.overlap(p['box_mm'],q['box_mm'])]
 for p in objects:
  if p['board']in prior['boards']:assert a.inside(p['box_mm'],prior['boards'][p['board']]['outline_mm']),'package/header outsideboard'
 mount_package_hits=[{'mount':m['id'],'ref':p['ref']}for m in prior['mounts']for p in objects if p['board']==m['board']and old.hosting.overlap(m['attachment_box_mm'],p['box_mm'])]
 return {'status':'TOPOLOGY REPAIR PROPOSAL; MANUFACTURING/CARRIER CONFLICTS OPEN','placements':placed,'boards':prior['boards'],'identified_ligaments':identified,'removed_rectangles':cuts,'manufacturing_sweep_bounds':manufacturing,'substrate_topology':topology,'ideal_joined_topology_not_manufacturing':ideal_topology,'source_checks':{'joined_cutout_package_hits':hits(cuts),'manufacturing_sweep_package_hits':hits(manufacturing),'manufacturing_sweep_mount_hits':mount_hits,'whole_package_pairs':source_pairs,'mount_package_header_hits':mount_package_hits},'mounts':prior['mounts'],'actual_pad_cut_margins':pad_rows,'carrier_proposal':carrier,'carrier_beam_planning':beam,'carrier_material_evidence':material,'PCB_support_sensitivity':pcb_sensitivity,'actual_force_application_routes':force_rows,'laminate_evidence':laminate,'carrier_width_alternatives':alternatives,'requested_precision_process':precision,'requested_precision_pad_margins':requested_margins,'standard_process_pad_margins':standard_margins,'nominal_precision_cut_bounds':[dict(c,box_mm=expand(c['box_mm'],requested))for c in cuts],'carrier_members':rails,'rejected_straight_carrier_hardware_projections':projections,'carrier_routed_members':routes,'carrier_hardware_projections':carrier_hits,'anchor_hardware_projections':anchor_hits,'carrier_segment_bounds':segments,'header_obstacles':headers,'obstacles':manufacturing+[dict(m,id=m['id'],box_mm=m['attachment_box_mm'],z_mm=[8,43.9])for m in prior['mounts']],'physical_neighbor_limitation':'Known438fixedhardware and23X1panel-side wholecourtyards excluded inXY; otherfunctionSMT/PCB occupiedZ notestablished. Routedrib is notfree-spaceorinstallationproof.','qualified_free_regions':[],'physical_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','source_sha256':a.binding([a.OUT/'stage7/mechanical-report.json',OUT/'interface-input.json',OUT/'placement-input.json',OUT/'mechanical-input.json',OUT/'fabrication-evidence.json',OUT/'material-evidence.json',OUT/'laminate-evidence.json',ROOT/'design/grid/placements.lock.json',ROOT/'design/architecture-278/mechanics.md',Path(__file__),Path(old.__file__),Path(locality.__file__),Path(old.transport.__file__),Path(old.hosting.__file__),Path(a.__file__),ROOT/'scripts/architecture278/implementation/test_stage8_mechanical.py']+[ROOT/p['source']for p in objects])}
def build():return build_from(json.loads((OUT/'placement-input.json').read_text()),json.loads((OUT/'mechanical-input.json').read_text()))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();s=json.dumps(r,sort_keys=True,separators=(',',':'))+'\n';p=OUT/'mechanical-report.json'
 if args.check:assert p.read_text()==s,'stale Stage8 mechanical report'
 else:p.write_text(s)
 print({k:len(v)for k,v in r['source_checks'].items()});print('carrier unknown projections',len(r['carrier_hardware_projections']))
if __name__=='__main__':main()
