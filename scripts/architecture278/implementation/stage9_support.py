"""One elevated continuous X1 board/support comparison; no physical fit claim."""
import argparse,copy,json,math,itertools
from collections import deque
from pathlib import Path
import assembly as a
import stage7_mechanical as old
ROOT=a.ROOT;OUT=a.OUT/'stage9'
def expand(b,r):return[b[0]-r,b[1]-r,b[2]+r,b[3]+r]
def route_frame(start,end,box,obstacles,width):
 step=.5;r=width/2+.2;node=lambda p:(round(p[0]/step),round(p[1]/step));s=node(start);t=node(end);blocked=set()
 for b0 in obstacles:
  b=expand(b0,r);blocked.update((i,j)for i in range(math.floor(b[0]/step),math.ceil(b[2]/step)+1)for j in range(math.floor(b[1]/step),math.ceil(b[3]/step)+1))
 if s in blocked or t in blocked:return None
 q=deque([s]);prev={s:None}
 while q:
  n=q.popleft()
  if n==t:break
  for v in [(n[0]+1,n[1]),(n[0]-1,n[1]),(n[0],n[1]+1),(n[0],n[1]-1)]:
   if v in blocked or v in prev or not(box[0]+r<=v[0]*step<=box[2]-r and box[1]+r<=v[1]*step<=box[3]-r):continue
   prev[v]=n;q.append(v)
 if t not in prev:return None
 pts=[];n=t
 while n is not None:pts.append([n[0]*step,n[1]*step]);n=prev[n]
 pts.reverse();bends=[pts[0]]+[pts[i]for i in range(1,len(pts)-1)if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])]+[pts[-1]]
 return[start,[start[0],bends[0][1]]]+bends+[[end[0],bends[-1][1]],end]

def build(spec_override=None):
 files=[OUT/'support-input.json',a.OUT/'stage8/mechanical-report.json',ROOT/'design/grid/placements.lock.json',a.OUT/'stage6/candidate-report.json',a.OUT/'stage6/mechanical-input.json',a.OUT/'stage5/din-evidence.json',a.OUT/'stage8/material-evidence.json']
 spec,prior,lock,osc,ds,de,material=[json.loads(p.read_text())for p in files];spec=copy.deepcopy(spec_override)if spec_override is not None else spec;placed=copy.deepcopy(prior['placements']);assert math.isclose(spec['front_rear_face_z_mm']-spec['front_panel_face_z_mm'],1.6)
 for p in placed.values():
  if p['panel_uid']:continue
  z=spec['front_panel_face_z_mm']if p['side']=='panel'else spec['front_rear_face_z_mm'];p['conditional_pad_depth_mm']=z;p['pads_xyz_mm']={pin:[xy+[z]for xy in pts]for pin,pts in p['pads_mm'].items()}
 assert len(placed)==56 and sum(bool(p['panel_uid'])for p in placed.values())==7 and sum(len(p['units'])for p in placed.values())==76
 headers=copy.deepcopy(prior['header_obstacles'])
 for h in headers.values():
  if h['end']=='front':
   if h['link']=='J-PWR':h=old.move(h,[spec['service_headers']['front_J_PWR_origin_mm'][i]-h['origin_mm'][i]for i in(0,1)]);headers[h['ref']]=h
   z=spec['front_rear_face_z_mm']
  else:
   if h['link']=='C-PWR':h=old.move(h,spec['service_headers']['middle_C_PWR_delta_mm']);headers[h['ref']]=h
   z=spec['service_headers']['middle_pad_z_mm']
  h['pad_depth_mm']=z;h['pads_xyz_mm']={pin:[xy+[z]for xy in pts]for pin,pts in h['pads_mm'].items()}
 islands=[];ledlands=[];lands=[];extensions=[];r=spec['terminal_land']['diameter_mm']/2
 assert spec['LED_island']['ordinary_outline_boundary_allowance_mm']>=.4,'ordinaryoutlineallowance weakened'
 for led in ['D809','D909','D1009']:
  p=placed[led];x,y=p['origin_mm'];w,h=spec['LED_island']['size_mm'];box=[x-w/2,y-h/2,x+w/2,y+h/2]
  islands.append({'ref':led,'box_mm':box,'worst_outer_box_mm':expand(box,spec['LED_island']['ordinary_outline_boundary_allowance_mm']),'z_mm':spec['LED_island']['board_z_mm'],'purpose':'Actual0402supportsubstrate retained; geometrynotfreestandingwire'})
  for pin,sign in [('1',-1),('2',1)]:ledlands.append({'id':led+':wire:'+pin,'ref':led,'pin':pin,'net':p['pins'][pin],'xyz_mm':[x+sign*spec['LED_island']['wire_landing_offset_x_mm'],y+spec['LED_island']['wire_landing_y_offset_mm'],21.6],'diameter_mm':2*r,'drill_mm':spec['terminal_land']['drill_mm'],'minimum_edge_mm':min(w/2-spec['LED_island']['wire_landing_offset_x_mm'],h/2-spec['LED_island']['wire_landing_y_offset_mm'])-r-spec['LED_island']['ordinary_outline_boundary_allowance_mm']})
 assignments=[]
 for jack,led in [('J809','D809'),('J909','D909'),('J1009','D1009')]:
  x=placed[jack]['origin_mm'][0]
  assignments +=[(jack,'S',[x,136.5]),(led,'1',[x,139.5]),(led,'2',[x,142.5]),(jack,'T',[x,145.5])]
 assignments +=[('SW608',pin,placed['SW608']['pads_mm'][pin][0])for pin in ['1','2','3']]
 for ref,pin,xy in assignments:
  p=placed[ref];source=p['pads_xyz_mm'][pin][0];ledland=next((q for q in ledlands if q['ref']==ref and q['pin']==pin),None);start=ledland['xyz_mm']if ledland else source;target=xy+[spec['front_panel_face_z_mm']];net=p['pins'][pin]
  land={'id':'X1:permanent:'+ref+':'+pin,'ref':ref,'pin':pin,'net':net,'xyz_mm':target,'diameter_mm':2*r,'drill_mm':spec['terminal_land']['drill_mm'],'board':p['board']};lands.append(land)
  length=math.dist(start,target);local=sum(abs(source[i]-start[i])for i in range(3))if ledland else 0
  extensions.append({'ref':ref,'pin':pin,'net':net,'source_terminal_xyz_mm':source,'from_xyz_mm':start,'from_LED_land_id':ledland['id']if ledland else None,'to_xyz_mm':target,'target_land_id':land['id'],'local_terminal_copper_mm':local,'local_copper_status':'UnroutedLEDpad-to-wireland allocation including1.6mmbarrel'if ledland else'NoadditionallocalPCBleg','wire_nominal_mm':spec['terminal_wire']['nominal_mm'],'wire_tolerance_mm':spec['terminal_wire']['cut_tolerance_mm'],'minimum_geometric_slack_mm':spec['terminal_wire']['nominal_mm']-spec['terminal_wire']['cut_tolerance_mm']-length,'geometric_wire_minimum_mm':length,'scope':'Factorywiretoactualproposedland; retainedterminalZisnominalPCBdatum, notmeasuredfreetail solderposition'})
 for row in extensions:
  start=row['from_xyz_mm'];end=row['to_xyz_mm'];z=spec['terminal_wire']['dogleg_z_mm'];points=[start,[start[0],start[1],z],[end[0],start[1],z],[end[0],end[1],z],end];length=sum(math.dist(u,v)for u,v in zip(points,points[1:]));row.update(proposed_wire_points_xyz_mm=points,proposed_developed_wire_mm=length,minimum_proposed_route_slack_mm=row['wire_nominal_mm']-row['wire_tolerance_mm']-length)
 assert all(x['minimum_proposed_route_slack_mm']>=spec['terminal_wire']['required_geometric_slack_mm']>=10 for x in extensions),'terminal wire route slack failed'
 assert all(l['minimum_edge_mm']>=.25 for l in ledlands),'LEDislandedgeallowancefailed'
 assert len(extensions)==15 and all(x['net']is not None for x in extensions)
 nc=[{'ref':ref,'pin':'TN','net':placed[ref]['pins']['TN'],'disposition':'RetainedNCterminal insulated/unconnected; noaddedwire'}for ref in ['J809','J909','J1009']];assert all(x['net']is None for x in nc)
 hardware=a.locked_hardware(lock['placements']);nonfixed=[p for p in placed.values()if not p['panel_uid']];front=[h for h in headers.values()if h['end']=='front'];middle=[h for h in headers.values()if h['end']=='middle'];collisions=[]
 for h in front:
  assert a.inside(h['box_mm'],spec['continuous_boards'][h['board']]),'headeroutsidecontinuousboard'
  collisions +=[{'header':h['ref'],'package':p['ref']}for p in nonfixed if p['board']==h['board']and old.hosting.overlap(h['box_mm'],p['box_mm'])]
 for l in lands:assert a.inside(expand([*l['xyz_mm'][:2],*l['xyz_mm'][:2]],r+.25),spec['continuous_boards'][l['board']]),'terminal land outsideboard'
 land_hits=[{'land':l['id'],'package':p['ref']}for l in lands for p in nonfixed if p['board']==l['board']and old.hosting.overlap(expand([*l['xyz_mm'][:2],*l['xyz_mm'][:2]],r),p['box_mm'])]
 land_headers=[{'land':l['id'],'header':h['ref']}for l in lands for h in front if l['board']==h['board']and old.hosting.overlap(expand([*l['xyz_mm'][:2],*l['xyz_mm'][:2]],r+.25),h['box_mm'])]
 land_pairs=[{'a':u['id'],'b':v['id']}for u,v in itertools.combinations(lands,2)if u['board']==v['board']and math.dist(u['xyz_mm'],v['xyz_mm'])<2*r+.25]
 island_pads=[{'island':i['ref'],'hardware':h['ref']}for i in islands for h in hardware if h['ref']!=i['ref']and any(old.hosting.overlap(i['worst_outer_box_mm'],b)for b in h['through_pad_keepouts_mm'])]
 island_bodies=[{'island':i['ref'],'hardware':h['ref'],'status':'UNKNOWN bodyZ/profile; courtyardprojection not physicalsolidclearance'}for i in islands for h in hardware if h['ref']!=i['ref']and old.hosting.overlap(i['worst_outer_box_mm'],h['box_mm'])]
 windows=[{'id':h['ref']+':window','box_mm':expand(h['box_mm'],spec['service_headers']['middle_window_margin_mm']),'middle_z_mm':[48.4,50],'withdrawal_z_mm':[h['pad_depth_mm'],h['pad_depth_mm']+spec['service_headers']['mated_height_reference_mm']+spec['service_headers']['normal_extraction_stroke_proposal_mm']],'purpose':'Proposedbackplanewindowforhousing/latchtoolaccess; notPCBassemblywithdrawal'}for h in front]
 contacts,flanges=old.din.register(osc['candidate'],ds,de)
 din_hits=old.din.screen([dict(w,ref=w['id'],instance='X1')for w in windows],contacts+flanges)
 retained=osc['candidate']['middle_header_placements_all_instances']+osc['candidate']['shared_middle_placements']+middle
 window_hits=[{'window':w['id'],'retained_ref':p['ref']}for w in windows for p in retained if old.hosting.overlap(w['box_mm'],p['box_mm'])]
 backing=[]
 for h in front:
  anchor='SW608'if h['board']=='X1-control'else min(['J809','J909','J1009'],key=lambda ref:math.dist(placed[ref]['origin_mm'],h['origin_mm']));start=h['origin_mm'];end=placed[anchor]['origin_mm'];L=math.dist(start,end);width=spec['backing']['rib_width_mm'];depth=spec['backing']['frame_z_mm'][1]-spec['backing']['frame_z_mm'][0];I=width*depth**3/12;F=spec['backing']['service_force_N'];E=material['E_MPa']
  route=route_frame(start,end,spec['continuous_boards'][h['board']],[p['box_mm']for p in nonfixed if p['board']==h['board']and p['side']=='panel'],width)
  developed=sum(math.dist(u,v)for u,v in zip(route,route[1:]))if route else None
  backing.append({'port':h['ref'],'board':h['board'],'shoe_box_mm':h['box_mm'],'shoe_z_mm':spec['backing']['insulator_z_mm'],'rib_centreline_mm':route,'developed_rib_length_mm':developed,'routing_status':'SOURCE_ROUTE'if route else'BLOCKED_OWN_PANEL_PACKAGES','rib_width_mm':width,'rib_z_mm':spec['backing']['frame_z_mm'],'anchor_ref':anchor,'anchor_xy_mm':end,'anchor_required_z_mm':spec['backing']['clamp_required_z_mm'],'linear_span_surrogate_mm':L,'force_N':F,'cantilever_deflection_surrogate_mm':F*developed**3/(3*E*I)if developed else None,'net_1mm_section_deflection_surrogate_mm':F*developed**3/(3*E*(1*depth**3/12))if developed else None,'bending_stress_surrogate_MPa':6*F*developed/(width*depth**2)if developed else None,'load_path':spec['backing']['load_path'],'status':'Positiveproposedforcepath; exactclampstack/thread/bearing/cutwireguidegeometry NOT qualified'})
 rib_hits=[]
 for b in backing:
  for u,v in zip(b['rib_centreline_mm']or[],(b['rib_centreline_mm']or[])[1:]):
   box=expand([min(u[0],v[0]),min(u[1],v[1]),max(u[0],v[0]),max(u[1],v[1])],b['rib_width_mm']/2)
   rib_hits +=[{'port':b['port'],'package':p['ref']}for p in nonfixed if p['board']==b['board']and p['side']=='panel'and old.hosting.overlap(box,p['box_mm'])]
 process=spec['backing']['wire_guide_process'];assert math.isclose(process['nominal_bore_diameter_mm']+process['diameter_tolerance_mm']+2*process['radial_position_allowance_mm'],spec['backing']['wire_guide_bore_mm']),'wire guide manufacturing envelope omitted'
 guides=[];shoe_hits=[]
 for b in backing:
  assert b['rib_centreline_mm'],'blocked backing route'
  boxes=[expand([min(u[0],v[0]),min(u[1],v[1]),max(u[0],v[0]),max(u[1],v[1])],b['rib_width_mm']/2)for u,v in zip(b['rib_centreline_mm'],b['rib_centreline_mm'][1:])]
  for l in lands:
   xy=l['xyz_mm'][:2];d=spec['backing']['wire_guide_bore_mm']
   if l['board']==b['board']and any(old.hosting.overlap(expand(xy+xy,d/2),box)for box in boxes):guides.append({'port':b['port'],'land':l['id'],'xy_mm':xy,'maximum_removed_envelope_diameter_mm':d,'manufacturing_proposal':process,'through_z_mm':b['rib_z_mm'],'status':'Proposed insulated wire guide removes carrier material; exact wire OD, insert retention and machining not qualified'})
  w=spec['backing']['minimum_remaining_section_width_mm'][b['board']];depth=b['rib_z_mm'][1]-b['rib_z_mm'][0];L=b['developed_rib_length_mm'];F=b['force_N'];b['net_section_width_assumption_mm']=w;b['net_section_deflection_mm']=F*L**3/(3*material['E_MPa']*(w*depth**3/12));b['net_section_stress_MPa']=6*F*L/(w*depth**2)
  assert b['net_section_deflection_mm']<=spec['backing']['planning_deflection_mm'] and b['net_section_stress_MPa']<=spec['backing']['planning_stress_MPa'],'backing planning section failed'
  shoe_hits +=[{'port':b['port'],'package':p['ref']}for p in nonfixed if p['board']==b['board']and p['side']=='panel'and old.hosting.overlap(b['shoe_box_mm'],p['box_mm'])]
 # Bore spacing proves only a remaining local ligament, not tortuous-frame stiffness.
 for u,v in itertools.combinations(lands,2):
  if u['board']==v['board']:assert math.dist(u['xyz_mm'],v['xyz_mm'])-spec['backing']['wire_guide_bore_mm']>=spec['backing']['minimum_remaining_section_width_mm'][u['board']]-1e-9,'wire guide ligament failed'
 inherited_path=a.OUT/'stage8/interfaces-report.json';inherited=json.loads(inherited_path.read_text());service_wires=[]
 for link in inherited['links']:
  for wire in link['conductors']:
   f=headers[wire['front_header']]['pads_xyz_mm'][wire['pin']][0];m=headers[wire['middle_header']]['pads_xyz_mm'][wire['pin']][0];cases=[{'front_unplug_mm':df,'middle_unplug_mm':dm,'distance_mm':math.dist(f[:2]+[f[2]+df],m[:2]+[m[2]-dm])}for df,dm in itertools.product([0,15],repeat=2)];slack=wire['wire_cut_nominal_mm']-wire['wire_cut_tolerance_mm']-max(c['distance_mm']for c in cases)
   assert slack>=wire['minimum_slack_allocation_mm']>=10,'inherited service wire slack failed'
   service_wires.append({'front_header':wire['front_header'],'middle_header':wire['middle_header'],'pin':wire['pin'],'net':wire['net'],'front_pad_xyz_mm':f,'middle_pad_xyz_mm':m,'wire_cut_nominal_mm':wire['wire_cut_nominal_mm'],'wire_cut_tolerance_mm':wire['wire_cut_tolerance_mm'],'service_cases':cases,'minimum_proxy_slack_mm':slack,'status':'Pad proxy only; actual wire exits/bends/strain retention unqualified'})
 assert len(service_wires)==15
 sweeps=[{'id':h['ref'],'box_mm':h['box_mm'],'z_mm':[h['pad_depth_mm'],h['pad_depth_mm']+22.3]if h['side']=='rear'else[h['pad_depth_mm']-22.3,h['pad_depth_mm']]}for h in headers.values()]
 sweep_hits=[{'a':x['id'],'b':y['id']}for x,y in itertools.combinations(sweeps,2)if old.overlap3(x['box_mm'],x['z_mm'],y['box_mm'],y['z_mm'])]
 projections=[{'board':board,'hardware':h['ref'],'classification':'UNKNOWN actualbody/tailZ; mustmeetdeclared29mmrequiredceiling'}for board,box in spec['continuous_boards'].items()for h in hardware if old.hosting.overlap(box,h['box_mm'])]
 bindings=files+[inherited_path,Path(__file__),Path(__file__).with_name('test_stage9_support.py'),Path(a.__file__),Path(old.__file__),Path(old.din.__file__),ROOT/'design/architecture-278/source-ledger.json']+[ROOT/p['source']for p in placed.values()]+[ROOT/h['source']for h in headers.values()]
 assert not any([collisions,land_hits,land_headers,land_pairs,rib_hits,shoe_hits,island_pads,din_hits,window_hits,sweep_hits]),'modeled source collision or exclusion failed'
 return {'status':'ONE CONDITIONAL CONTINUOUS ELEVATED X1 ALTERNATIVE; NOT PHYSICAL ACCEPTANCE','placements':placed,'continuous_boards':spec['continuous_boards'],'header_obstacles':headers,'terminal_extensions':extensions,'terminal_lands':lands,'LED_wire_lands':ledlands,'LED_islands':islands,'retained_NC_terminals':nc,'added_mating_interfaces':0,'retained_service_links':4,'counts':{'packages':56,'nonfixed_on_continuous_boards':49,'fixed_centres':7,'units':76,'source_pins':sum(len(p['pins'])for p in placed.values()),'active_terminal_extensions':15,'permanent_end_terminations':30,'LED_support_islands':3,'factory_service_subassemblies':2},'backing_paths':backing,'carrier_wire_guides':guides,'inherited_service_wire_checks':service_wires,'SW608_support':{'ref':'SW608','xy_mm':placed['SW608']['origin_mm'],'load_path':'Actuator/body→captivesaddle→panelclampedbushing/shoulder→panel. NoPCBstrip/solderterminalcredited. Captivecarriergripsupportsassemblyduringrelease.','status':'Exact2MS1T1B1M2QES-5clampthread/engagement/bodyreactiongeometryrequiresretaineddrawingverification'},'service_access':spec['service_access'],'service_windows':windows,'normal_connector_sweeps':sweeps,'source_checks':{'new_header_package_collisions':collisions,'terminal_land_package_collisions':land_hits,'terminal_land_header_collisions':land_headers,'terminal_land_pairs':land_pairs,'backing_rib_panel_package_hits':rib_hits,'backing_shoe_panel_package_hits':shoe_hits,'LED_island_foreign_through_pad_hits':island_pads,'service_window_DIN_hits':din_hits,'service_window_retained_middle_hits':window_hits,'connector_sweep_pairs':sweep_hits},'LED_island_hardware_body_projections':island_bodies,'neighbor_hardware_projections':projections,'solid_requirements':spec['solid_requirements'],'qualified_free_regions':[],'source_sha256':a.binding(bindings),'native':'NOT RUN','simulation':'NOT RUN','physical_acceptance':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,sort_keys=True,separators=(',',':'))+'\n';target=OUT/'support-report.json'
 if args.check:assert target.read_text()==data,'staleStage9support'
 else:target.write_text(data)
 print({k:len(v)for k,v in r['source_checks'].items()})
if __name__=='__main__':main()
