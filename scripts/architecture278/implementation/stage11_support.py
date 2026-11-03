"""Bounded A01 support, capture and service design refinement; no physical validation."""
import argparse,copy,itertools,json,math
from pathlib import Path
import assembly as a
ROOT=a.ROOT;OUT=a.OUT/'stage11'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def overlap(x,y):return x[0]<y[2]and y[0]<x[2]and x[1]<y[3]and y[1]<x[3]
def expanded(x,r):return[x[0]-r,x[1]-r,x[2]+r,x[3]+r]
def rect_distance(p,b):return math.hypot(max(b[0]-p[0],0,p[0]-b[2]),max(b[1]-p[1],0,p[1]-b[3]))
def beam(F,L,b,h,E):
 need(min(L,b,h,E)>0 and F>=0,'invalid beam geometry/load')
 return {'load_N':F,'length_mm':L,'width_mm':b,'depth_mm':h,'E_MPa':E,'cantilever_delta_mm':F*L**3/(3*E*b*h**3/12),'bending_stress_MPa':6*F*L/(b*h*h),'scope':'Single straight cantilever sensitivity; not a proof for connected joints, torsion, creep or real force distribution'}
def build(override=None):
 files=[OUT/'support-input.json',OUT/'support-evidence.json',a.OUT/'stage10/mechanical-report.json',a.OUT/'stage8/material-evidence.json',ROOT/'design/grid/placements.lock.json',a.OUT/'stage4/occupied-report.json']
 spec,evidence,prior,metal,lock,occupied=[json.loads(p.read_text())for p in files];spec=copy.deepcopy(override)if override is not None else spec
 need(len(prior['placements'])==90 and len(prior['bypass_associations'])==17,'baseline population changed')
 material=next(s for s in evidence['sources']if s['id']=='ensinger-tecapeek-natural');need(material['availability']=='AVAILABLE'and len(material['sha256'])==64,'insulator evidence unavailable')
 E=metal['E_MPa'];Ep=material['values']['flexural_E_MPa'];loads=spec['loads'];frames=copy.deepcopy(prior['carrier_frames'])
 w=spec['rear_crossmember_width_mm'];need(w>=6,'rear refinement omitted')
 frames['rear']['crossmembers_boxes_mm']=[[237,172-w/2,318,172+w/2],[237,284-w/2,318,284+w/2]]
 depth=spec['control_rail_depth_mm'];need(depth>=8,'actual thin control rail not refined');frames['control']['z_mm']=[20-depth,20]
 for frame in frames.values():
  frame.pop('planning_model',None);frame.pop('anchor_bosses',None)
 frames['control']['anchors_mm']=[[300,310],[315,310]]
 members=[]
 for name,f in frames.items():
  for kind in ['rails_boxes_mm','crossmembers_boxes_mm']:
   for i,b in enumerate(f[kind]):
    dx,dy=b[2]-b[0],b[3]-b[1];d=(8 if name=='control'and kind=='crossmembers_boxes_mm'else f['z_mm'][1]-f['z_mm'][0]);F=loads['DIN_insertion_sensitivity_N']if name in('middle','rear')else loads['PCB_service_N']
    members.append({'frame':name,'kind':kind,'index':i,'source_box_mm':b,'actual_member_screen':beam(F,max(dx,dy),min(dx,dy),d,E),'criterion_mm':loads['deflection_screen_mm']})
 # Individual long rails remain visible even when a transverse member passes.
 for m in members:m['within_named_screen']=m['actual_member_screen']['cantilever_delta_mm']<=m['criterion_mm']
 old_control=beam(loads['PCB_service_N'],43,1.5,2,E);new_control=beam(loads['PCB_service_N'],43,1.5,depth,E)
 old_rear=beam(loads['DIN_insertion_sensitivity_N'],81,4,11,E);new_rear=beam(loads['DIN_insertion_sensitivity_N'],81,w,11,E)
 need(new_control['cantilever_delta_mm']<=loads['deflection_screen_mm']and new_rear['cantilever_delta_mm']<=loads['deflection_screen_mm'],'selected bounded refinement misses named planning screen')
 # Insulating shoulder sleeves require a real clearance stack; old2.7mm holes cannot silently accept3.5mm sleeves.
 f=spec['fasteners'];holemin=f['PCB_M2p5_drill_mm']-f['PCB_hole_tolerance_mm'];ODmax=f['PCB_sleeve_OD_mm']+f['PCB_sleeve_tolerance_mm'];IDmin=f['PCB_sleeve_ID_mm']-f['PCB_sleeve_tolerance_mm'];wall=(f['PCB_sleeve_OD_mm']-f['PCB_sleeve_tolerance_mm']-f['PCB_sleeve_ID_mm']-f['PCB_sleeve_tolerance_mm'])/2
 need(holemin>ODmax and IDmin>2.5 and wall>=.3-1e-9,'insulating sleeve fit or wall failed')
 mounts=[]
 for m in prior['mounts']:
  q=copy.deepcopy(m);board=prior['boards'][q['board']];lo,hi=board['z_mm'];t=f['PCB_flange_thickness_mm'];q.update(drill_mm=f['PCB_M2p5_drill_mm'],insulator_sleeve_OD_mm=f['PCB_sleeve_OD_mm'],insulator_sleeve_ID_mm=f['PCB_sleeve_ID_mm'],front_flange_z_mm=[lo-t,lo],rear_flange_z_mm=[hi,hi+t])
  if q['board']=='A01-control':q['rear_head_z_mm']=[lo-t-2.5,lo-t];q['spacer_z_mm']=[hi+t,18];q['tool_z_mm']=[-5,lo-t-2.5]
  else:q['rear_head_z_mm']=[hi+t,hi+t+2.5];q['spacer_z_mm']=[q['frame_z_mm'][1],lo-t];q['tool_z_mm']=[hi+t+2.5,105]
  need(q['spacer_z_mm'][1]>q['spacer_z_mm'][0],'negative spacer stack')
  neighbors=[p for p in list(prior['placements'].values())+list(prior['headers'].values())if p['board']==q['board']]
  gap=min((rect_distance(q['xy_mm'],p['box_mm'])-f['PCB_flange_OD_mm']/2 for p in neighbors),default=None)
  need(gap is None or gap>=spec['insulation']['required_nonfunctional_metal_clearance_mm'],'mount washer/courtyard clearance')
  o=board['outline_mm'];x,y=q['xy_mm'];edge=min(x-o[0],o[2]-x,y-o[1],o[3]-y);ligament=edge-(f['PCB_M2p5_drill_mm']+f['PCB_hole_tolerance_mm'])/2
  need(ligament>=1,'enlarged mounting hole edge ligament below proposed1mm');need(edge>=f['PCB_flange_OD_mm']/2,'flange outside substrate')
  q['minimum_drill_edge_ligament_mm']=ligament
  q['minimum_courtyard_gap_mm']=gap;q['scope']='Candidate insulating shoulder sleeve/flange stack; actual copper rules, sleeve creep and preload qualification OPEN';mounts.append(q)
 # Closed front capture lips, side jaws and relieved rear backing prevent a bare bushingless PCB-only load claim.
 cradles=[]
 for ref in ('RV1307','RV1308'):
  p=prior['placements'][ref];x,y=p['origin_mm'];gap=spec['body_clearance_each_side_mm'];shaftdia=spec['cradle_front_hole_diameter_mm'];need(shaftdia>=6.5,'front capture lip obstructs6mmshaft/tolerance')
  bridgeZ=spec['cradle_rear_bridge_z_mm'];bridgeY=spec['cradle_rear_bridge_height_y_mm'];mountdia=spec['mount_tail_relief_diameter_mm'];axisdia=spec['rear_shaft_relief_diameter_mm'];allow=spec['relief_position_allowance_mm']
  need(mountdia>=2.4+2*allow+.6 and axisdia>=2+2*allow+.6,'rear bridge relief lacks solder/position allowance')
  holes=[{'role':'mount_tail','pin':pin,'xy_mm':p['pads_mm'][pin][0],'diameter_mm':mountdia}for pin in('4','5')]+[{'role':'rear_shaft','xy_mm':[x,y],'diameter_mm':axisdia}]
  netwidth=bridgeY-max(mountdia,axisdia)-2*allow;need(netwidth>0,'backing bridge severed by relief')
  result=beam(loads['pot_push_N'],21,netwidth,bridgeZ[1]-bridgeZ[0],Ep);need(result['cantilever_delta_mm']<=loads['insulator_bridge_screen_mm'],'relieved backing bridge misses named deflection screen')
  lip=[x-11,y-6,x+11,y+6];left=[x-11,y-4,x-8.5,y+4];right=[x+8.5,y-4,x+11,y+4]
  cradles.append({'ref':ref,'shaft_origin_mm':[x,y],'nominal_body_box_mm':[x-5,y-5,x+5,y+5],'body_z_mm':[3.2,10],'body_tolerance':'UNKNOWN; drawing nominal envelope is not a guaranteed pocket fit','front_lip':{'box_mm':lip,'z_mm':spec['cradle_front_lip_z_mm'],'shaft_hole_diameter_mm':shaftdia},'side_jaws':[{'box_mm':[x-7,y-4,x-5-gap,y+4],'z_mm':[3.2,9.8]},{'box_mm':[x+5+gap,y-4,x+7,y+4],'z_mm':[3.2,9.8]}],'outer_columns':[{'box_mm':left,'z_mm':[2.2,20]},{'box_mm':right,'z_mm':[2.2,20]}],'rear_backing':{'box_mm':[x-10.5,y-bridgeY/2,x+10.5,y+bridgeY/2],'z_mm':bridgeZ,'interface_pad_z_mm':spec['cradle_insulator_pad_z_mm'],'relief_holes':holes,'minimum_remaining_strip_total_width_mm':netwidth,'model':result},'factory_shim_range_mm':spec['bearing_shim_requirement_mm'],'capture_fasteners':[{'xy_mm':[x-9.75,y],'nominal_thread_mm':1.6,'boss_diameter_mm':4,'tool_diameter_mm':4,'access':'Panel removed; captive through screw clamps split capture column to lower rail; grade/preload/locking not selected'},{'xy_mm':[x+9.75,y],'nominal_thread_mm':1.6,'boss_diameter_mm':4,'tool_diameter_mm':4,'access':'Panel removed'}],'load_paths':{'pull':'Shaft/body→front insulating lip→outer columns→control rails→bottom crossmember→two-point cleat','push':'Body rear seating→PCB locally backed across its thickness→insulating pad/relieved bridge→outer columns→control rails; no pin bending credited','torque':'Body sides→two positive jaws with factory-measured shims→outer columns/rail couple; friction preload alone not credited'},'operating_torque_source_Nm':[.000980665,.00980665],'external_torque_planning_Nm':loads['pot_external_torque_Nm'],'side_reaction_N_at_10mm_couple':loads['pot_external_torque_Nm']/.010,'contact_pressure_sensitivity_MPa':loads['pot_push_N']/(10*netwidth),'qualification':'Capture geometry proposal, not shell-bearing/creep/fastener validation. Exact body tolerance and usable bearing surfaces must be confirmed.'})
 # One-anchor control cleat lacked anti-rotation; use two positive anchors, same fixed-panel positions.
 anchors=[]
 for name,frame in frames.items():
  centres=frame['anchors_mm']if name!='control'else[[300,310],[315,310]]
  for xy in centres:
   radius=5;z=frame['z_mm'];anchors.append({'frame':name,'xy_mm':xy,'boss_radius_mm':radius,'drill_mm':f['anchor_M3_drill_mm'],'washer_OD_mm':f['anchor_washer_OD_mm'],'tool_OD_mm':f['anchor_tool_OD_mm'],'cleat_box_mm':[xy[0]-5,xy[1]-5,xy[0]+5,xy[1]+5],'cleat_z_mm':[z[0]-f['cleat_plate_thickness_mm'],z[0]],'joint':'Captive M3 through bolt and captive nut/metal cleat; positive bolt bearing plus two separated anchors, not friction-only antirotation','preload_sensitivity_N':f['joint_preload_range_N'],'contact_pressure_range_MPa':[F/(math.pi*((f['anchor_washer_OD_mm']/2)**2-(f['anchor_M3_drill_mm']/2)**2))for F in f['joint_preload_range_N']],'status':'New enclosure cleat construction; exact bolt grade, tightening/locking, surface and enclosure load path unqualified'})
 # Concrete low-R alternative: three separate U straps and six bolted end contacts, not GH parallel credit.
 feed=spec['feed'];need(feed['nets']==['+12V','-12V','AGND']and len(feed['stud_x_mm'])==3,'feed net/lane identity');straps=[]
 for net,x in zip(feed['nets'],feed['stud_x_mm']):
  y=feed['stud_y_mm'];z0,z1=feed['middle_face_z_mm'],feed['rear_face_z_mm'];yb=feed['bend_y_mm'];rad=feed['bend_radius_mm'];sharp=2*(y-yb)+(z1-z0);developed=sharp-2*(2*rad-math.pi*rad/2)
  need(y-yb>=rad+feed['washer_OD_mm']/2 and z1-z0>=2*rad,'bend conflicts with contact land or other bend');need(0<developed<=feed['maximum_developed_mm'],'strap developed length budget')
  need(feed['width_mm']>=feed['washer_OD_mm']+2*feed['dimension_tolerance_mm'],'washer outside conductor strip')
  straps.append({'net':net,'middle_stud_xyz_mm':[x,y,z0],'rear_stud_xyz_mm':[x,y,z1],'centreline_vertices_mm':[[x,y,z0],[x,yb,z0],[x,yb,z1],[x,y,z1]],'corner_radius_mm':rad,'radius_datum':'centreline','developed_centerline_mm':developed,'maximum_budget_mm':feed['maximum_developed_mm'],'width_mm':feed['width_mm'],'thickness_mm':feed['thickness_mm'],'bend_strain_geometric_outer_fibre_sensitivity':feed['thickness_mm']/(2*rad),'terminal_hole_mm':feed['stud_drill_mm'],'terminal_washer_mm':feed['washer_OD_mm'],'lane_envelope_mm':[x-feed['width_mm']/2-feed['placement_allowance_mm'],yb-feed['thickness_mm']/2-feed['placement_allowance_mm'],x+feed['width_mm']/2+feed['placement_allowance_mm'],y+feed['washer_OD_mm']/2+feed['placement_allowance_mm']],'lane_z_mm':[z0-feed['thickness_mm']/2,z1+feed['thickness_mm']/2],'status':'Formed busbar, not repeatedly flexed service lead. Alloy/temper/minimum bend radius/contact pressure and plating unqualified; geometric strain is not material acceptance.'})
 gaps=[]
 for l,r in zip(straps,straps[1:]):
  gap=r['lane_envelope_mm'][0]-l['lane_envelope_mm'][2];need(gap>=feed['insulating_barrier_thickness_mm']+2*spec['insulation']['required_nonfunctional_metal_clearance_mm'],'feed insulation lanes overlap');gaps.append(gap)
 need(feed['bend_radius_mm']>0 and feed['thickness_mm']>0,'invalid strap section/bend')
 # Actual stud drill exclusion against front-face middle GH lands/courtyards, plus new rear-wing source packages.
 studs=[(s['net'],s['middle_stud_xyz_mm'])for s in straps];stud_hits=[]
 for net,xyz in studs:
  b=expanded(xyz[:2]*2,feed['stud_drill_mm']/2+feed['placement_allowance_mm'])
  for h in prior['headers'].values():
   if h['board']=='A01-middle'and overlap(b,h['box_mm']):stud_hits.append({'net':net,'header':h['ref']})
 for net,xyz in studs:
  for d in prior['din_connectors'].values():
   for pin,points in d['pads_xyz_mm'].items():
    for v in points:
     need(math.dist(xyz[:2],v[:2])>=feed['stud_drill_mm']/2+feed['placement_allowance_mm']+d['pad_diameter_proposal_mm']/2,'feed stud intersects DIN pad')
 need(not stud_hits,'feed stud intersects middle GH')
 wing=feed['wing_outline_mm'];wing_hits=[p['ref']for p in prior['placements'].values()if p['board']=='A01-core'and overlap(wing,p['box_mm'])];need(not wing_hits,'feed wing intersects complete source package')
 lowR={'status':feed['status'],'straps':straps,'adjacent_max_envelope_gaps_mm':gaps,'barrier_thickness_mm':feed['insulating_barrier_thickness_mm'],'new_core_terminal_wing_mm':wing,'new_terminal_reaction':'Six insulated captive terminal blocks carry bolt preload through metal shoulders to dedicated wing/middle carrier brackets; PCB copper/solder is an electrical transfer leg, not a bolt preload reaction. Full block detail OPEN.','baseline_K_PWR':'Retained physically in Stage10. Option activation requires explicit mutually exclusive feed selection; no parallel-current sharing credited.','removal_sequence':['Power off/discharge; disconnect retained GH if present.','Release all six captive strap bolts and retain all three formed bars in insulating cassette; never bend bars as hinges.','Slide cassette30mm toward smallerY, then through specified right-side access opening; retain it on enclosure dock.','Only after cassette removal release core retainers and withdraw40mm axially.'],'cassette_removal_volume_mm':[min(s['lane_envelope_mm'][0]for s in straps),min(s['lane_envelope_mm'][1]for s in straps)-feed['cassette_slide_negative_y_mm'],50.5,feed['side_exit_x_mm'],max(s['lane_envelope_mm'][3]for s in straps),68.7],'service_status':'Own A01 source envelope screen only; other-function occupancy through cassette exit remains UNKNOWN and blocks installed service acceptance.'}
 lowR['side_opening_requirement']={'installed_inner_width_reference_mm':320,'service_exit_x_mm':feed['side_exit_x_mm'],'external_space_beyond_reference_mm':feed['side_exit_x_mm']-320,'status':'Removable enclosure side opening plus external service workspace REQUIRED; not installed fit'}
 lowR['transfer_legs']='Middle51mm contactface and rear68.2mm contactface are new terminal datums; retained core pads69.2/70.8 require distinct unrouted copper transfer legs and independently supported terminal blocks.'
 # Conservative AABB diagnostics: intersections are constraints, not silently credited clear.
 solids=[]
 for name,frame in frames.items():
  for kind in ('rails_boxes_mm','crossmembers_boxes_mm'):
   for i,b in enumerate(frame[kind]):solids.append({'id':name+':'+kind+str(i),'box':b,'z':frame['z_mm'],'class':'frame'})
 for name,b in prior['boards'].items():solids.append({'id':name,'box':b['outline_mm'],'z':b['z_mm'],'class':'substrate'})
 for name,d in prior['din_connectors'].items():solids.append({'id':'DIN:'+name,'box':d['box_mm'],'z':[50,69.2],'class':'DIN conservative full mating depth'})
 for name,h in prior['headers'].items():
  z=next(iter(h['pads_xyz_mm'].values()))[0][2];direction=1 if h['side']=='rear'else-1
  solids.append({'id':name,'box':h['box_mm'],'z':sorted([z,z+direction*7.3]),'class':'GH mated depth bound'})
 for name,p in prior['placements'].items():
  z=next(iter(p['pads_xyz_mm'].values()))[0][2];direction=1 if p['side']=='rear'else-1
  solids.append({'id':name,'box':p['box_mm'],'z':sorted([z,z+direction*5]),'class':'package conditional5mm bound; exact body unknown'})
 def hits(box,z):return [{'solid':q['id'],'classification':q['class']}for q in solids if overlap(box,q['box'])and z[0]<q['z'][1]and q['z'][0]<z[1]]
 lowR['installed_lane_intersections']=[{'net':q['net'],'hits':hits(q['lane_envelope_mm'],q['lane_z_mm'])}for q in straps]
 v=lowR['cassette_removal_volume_mm'];lowR['cassette_sweep_intersections']=hits([v[0],v[1],v[3],v[4]],[v[2],v[5]])
 refined_frame_projections=[]
 for name in ('control','rear'):
  frame=frames[name]
  for kind in ('rails_boxes_mm','crossmembers_boxes_mm'):
   for i,b in enumerate(frame[kind]):
    for q in solids:
     if q['class']!='frame'and overlap(b,q['box'])and frame['z_mm'][0]<q['z'][1]and q['z'][0]<frame['z_mm'][1]:refined_frame_projections.append({'frame':name,'member':kind+str(i),'solid':q['id'],'classification':q['class'],'disposition':'Conservative envelope intersection; no clearance acceptance without exact body/relief datum'})
 lowR['screen_scope']='Conservative source bounding solids only; any listed intersection blocks clearance credit. Contact supports/fastener heads and other-function Z remain unmodeled; no complete service pass.'
 for c in cradles:c['guaranteed_pocket_clearance_before_unknown_body_tolerance_mm']=spec['body_clearance_each_side_mm']-spec['manufacturing_dimension_allowance_mm']-.4
 # Retain actual coordinate evidence for all other functions, never declare their unassigned Z free.
 hardware=a.locked_hardware(lock['placements']);foreign=[p for p in hardware if p['ref']not in prior['placements']];cradle_proj=[]
 for c in cradles:
  for p in foreign:
   if overlap(c['front_lip']['box_mm'],p['box_mm']):cradle_proj.append({'cradle':c['ref'],'foreign_ref':p['ref'],'classification':'UNKNOWN actual foreign bodyZ/shape; fixed XY preserved'})
 historical=[{'ref':p['ref'],'function':p['function_or_service'],'old_board':p['historical_placement']['board']}for p in occupied['rows']if p['function_or_service']!='A01'and overlap([lowR['cassette_removal_volume_mm'][i]for i in(0,1,3,4)],p['historical_placement']['courtyard_mm'])]
 # Planning service state machine is explicit about which retained assemblies must be isolated.
 service={'baseline_core':['Power off/discharge, remove rear cover, support core on both handles.','Disconnect K-PWR GH; release four captive core screws; pull axially40mm without rocking supported DIN.'],'front_service':['Power off/discharge; disconnect A01 front ports and retain their harnesses on captive enclosure clips.','Keep every non-A01 harness attached to its own supported assembly; inventory slack/release interfaces before panel opening.','Remove/open proposed front panel while a captive enclosure service stay supports it; other-function retention and stay rating remain unqualified.','Remove A01 carrier as a complete factory subassembly before accessing jack M4 PCB screw; its installed tool path remains blocked by middle/core.','Pot cradle screws are accessible only with front panel removed; fixed shaft/body registration restored with factory shims.'],'proposed_panel_stay':{'number':2,'anchor':'New enclosure edge cleats, not circuit boards or wiring','planning_load_N':20,'status':'No panel mass/CG/harnessload evidence;20N is sensitivity requirement, not acceptedload or ratedstay'},'must_not_assume':['No home soldering','No hot swap','No free unassigned other-function volume','No pot threaded bushings','No repeated bending of formed copper straps'],'retention_unknown_functions':32,'normal_OSC_calibration':'Does not require middle removal'}
 paths=files+[Path(__file__),Path(__file__).with_name('test_stage11_support.py'),Path(a.__file__),Path(a.c.__file__)]+[ROOT/p['source']for p in hardware]
 return {'status':'STAGE11 SOURCE SUPPORT/SERVICE REFINEMENT; PHYSICAL NOT RUN','source_package_count':90,'source_package_placements_unchanged':True,'source_stage10_sha256':a.binding([files[2]]),'refined_frames':frames,'refined_frame_solid_projections':refined_frame_projections,'member_sensitivities':members,'bounded_refinement_comparison':{'control_rail_before':old_control,'control_rail_after':new_control,'rear_crossmember_before':old_rear,'rear_crossmember_after':new_rear},'insulating_mount_stacks':mounts,'sleeve_fit':{'minimum_hole_mm':holemin,'maximum_OD_mm':ODmax,'minimum_ID_mm':IDmin,'minimum_wall_mm':wall,'old2p7hole_usable':False,'required_new_hole_mm':f['PCB_M2p5_drill_mm']},'pot_capture_assemblies':cradles,'enclosure_anchors':anchors,'low_R_feed_option':lowR,'service':service,'cradle_foreign_hardware_projections':cradle_proj,'feed_removal_historical_other_function_projections':historical,'unchanged_installed_tool_blockers':prior['installed_tool_board_blockers'],'source_sha256':a.binding(paths),'physical_acceptance':False,'strength_qualified':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,sort_keys=True,separators=(',',':'))+'\n';p=OUT/'support-report.json'
 if args.check:need(p.read_text()==data,'stale Stage11 support report')
 else:p.write_text(data)
 print('Stage11 explicit capture/insulation/service and3strap envelope; physical/strength NOT QUALIFIED')
if __name__=='__main__':main()
