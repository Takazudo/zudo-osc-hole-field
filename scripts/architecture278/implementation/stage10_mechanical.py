"""Independent A01 candidate geometry; no native or physical acceptance."""
import argparse,copy,itertools,json,math
from pathlib import Path
import assembly as a
import stage6_mechanical as din
import stage10_interfaces as interfaces
ROOT=a.ROOT;OUT=a.OUT/'stage10'
def overlap(x,y):return x[0]<y[2]and y[0]<x[2]and x[1]<y[3]and y[1]<x[3]
def expand(b,r):return[b[0]-r,b[1]-r,b[2]+r,b[3]+r]
def build(spec_override=None):
 files=[OUT/'mechanical-input.json',OUT/'inventory-report.json',OUT/'interface-input.json',ROOT/'design/grid/placements.lock.json',a.OUT/'stage6/mechanical-input.json',a.OUT/'stage5/din-evidence.json',a.OUT/'stage6/candidate-report.json',ROOT/'design/partition/floorplan-candidate.json']
 spec,inventory,interface,locked,ds,de,osc,floor=[json.loads(p.read_text())for p in files];spec=copy.deepcopy(spec_override)if spec_override is not None else spec
 assert spec['fixed_jack_LED_pad_z_proposal_mm']==20 and spec['ordinary_boundary_allowance_mm']>=.4,'unreviewed datum or ordinary process allowance'
 boards=spec['boards'];faces={b:{'panel':v['z_mm'][0],'rear':v['z_mm'][1]}for b,v in boards.items()};faces['A01-fixed']={'panel':20,'rear':21.6};placed={};sources=[]
 assert set(spec['positions'])==set(inventory['packages']),'whole package inventory changed'
 for ref,p in inventory['packages'].items():
  pose=spec['positions'][ref];board=pose['board'];side=pose['side'];q=a.located(a.face_shape(a.shape(ref,p),side),pose['origin_mm'],pose['quarter_turn'],board,side);q.update(panel_uid=p['attributes'].get('PanelUid',''),source_board=p['current_board'],unit_pin_record_indices=p['unit_pin_record_indices'],cluster=pose.get('cluster','front-local'))
  q['pads_xyz_mm']={pin:[xy+[faces[board][side]]for xy in pts]for pin,pts in q['pads_mm'].items()};q['conditional_pad_depth_mm']=faces[board][side];placed[ref]=q;sources.append(ROOT/q['source'])
 for p in inventory['fixed_controls']:
  q=placed[p['ref']];assert q['origin_mm']==[p['x_mm'],p['y_mm']]and q['quarter_turn']==p['rot_deg']//90 and q['side']=='panel','fixed shaft/panel datum changed'
 assert sum(len(p['units'])for p in placed.values())==118 and sum(len(p['pins'])for p in placed.values())==285
 headers=interfaces.transport_geometry(interface)
 for h in headers.values():sources.append(ROOT/h['source'])
 contacts,flanges=din.register({'connector_turn_deg':spec['DIN_turn_deg'],'origins_mm':{'A01':[0,0]},'connector_centre_mm':spec['DIN_centre_mm'],'paths':[]},ds,de)
 cx,cy=spec['DIN_centre_mm'];connectors={}
 for end,z,mpn,width,length in [('middle',50,'09032966824',max(de['female_body_width_mm']),de['female_body_max_length_mm']),('rear',69.2,'09031966922',de['male_body_max_width_mm'],de['male_body_max_length_mm'])]:
  connectors[end]={'ref':'A01:DIN:'+end,'mpn':mpn,'source':'design/architecture-278/implementation/stage5/din-evidence.json','pins':interfaces.DINMAP,'pads_xyz_mm':{p['label']:[p['point_mm']+[z]]for p in contacts},'box_mm':[cx-width/2,cy-length/2,cx+width/2,cy+length/2],'mount_surface_z_mm':z,'pad_diameter_proposal_mm':ds['proposed_contact_pad_diameter_mm'],'signed_transform':ds['female_A_to_global_xy_matrix']if end=='middle'else ds['male_B_to_global_xy_matrix']}
 # Local LED substrate supports all four real SMT packages; jacks use permanent factory tails.
 ledboard={'outline_mm':[222,121,227.5,163],'z_mm':[20,21.6],'ordinary_outline_allowance_mm':.4};ledlands=[];terminal_lands=[];extensions=[]
 fixedpins=[]
 for ref,y in [('D1308',123),('D1309',137),('D1310',153.5),('D13101',160.5)]:
  for pin,x in [('1',223.5),('2',226)]:
   p=placed[ref];land={'id':ref+':wire:'+pin,'ref':ref,'pin':pin,'net':p['pins'][pin],'xyz_mm':[x,y,21.6],'diameter_mm':1,'drill_mm':.5};ledlands.append(land);fixedpins.append((ref,pin,land))
 for ref in ['J1308','J1309','J1310']:
  for pin in ['S','T']:fixedpins.append((ref,pin,None))
 for i,(ref,pin,local)in enumerate(fixedpins):
  p=placed[ref];to=[236,116+3*i,35];start=local['xyz_mm']if local else p['pads_xyz_mm'][pin][0];land={'id':'A01:tail:'+ref+':'+pin,'ref':ref,'pin':pin,'net':p['pins'][pin],'xyz_mm':to,'diameter_mm':1.6,'drill_mm':.8,'board':'A01-jack'};terminal_lands.append(land)
  extensions.append({'ref':ref,'pin':pin,'net':p['pins'][pin],'source_terminal_xyz_mm':p['pads_xyz_mm'][pin][0],'from_xyz_mm':start,'from_LED_land_id':local['id']if local else None,'to_xyz_mm':to,'target_land_id':land['id'],'wire_nominal_mm':85,'wire_tolerance_mm':3,'local_terminal_copper_mm':sum(abs(u-v)for u,v in zip(start,p['pads_xyz_mm'][pin][0]))if local else 0,'source_terminal_status':'Nominal source PCB datum, not measured free-tail solder location'})
 # Full source courtyard and actual THT/landing checks are distinct from unknown bodies.
 collisions=[];mount_hits=[];land_hits=[];containment=[]
 for u,v in itertools.combinations(placed.values(),2):
  if u['board']==v['board']and u['side']==v['side']and overlap(u['box_mm'],v['box_mm']):collisions.append([u['ref'],v['ref']])
 for board,b in boards.items():
  for p in placed.values():
   if p['board']==board and not p['panel_uid']and not a.inside(p['box_mm'],b['outline_mm'],.25):containment.append(p['ref'])
  for xy in b['mounts_mm']:
   box=expand(xy+xy,spec['mount']['tool_diameter_mm']/2)
   assert a.inside(expand(xy+xy,spec['mount']['washer_diameter_mm']/2),b['outline_mm']), 'mount edge support absent'
   for p in list(placed.values())+list(headers.values()):
    if p['board']==board and overlap(box,p['box_mm']):mount_hits.append({'board':board,'mount':xy,'ref':p['ref']})
 for h in headers.values():
  if h['board']in boards:assert a.inside(h['box_mm'],boards[h['board']]['outline_mm']), 'header outside board'
  for p in placed.values():
   if p['board']==h['board']and (p['side']==h['side']or any(overlap(h['box_mm'],b)for b in p['through_pad_keepouts_mm']))and overlap(p['box_mm'],h['box_mm']):collisions.append([p['ref'],h['ref']])
 for land in terminal_lands:
  xy=land['xyz_mm'][:2];box=expand(xy+xy,1.05);assert a.inside(box,boards['A01-jack']['outline_mm'])
  for p in list(placed.values())+list(headers.values()):
   if p['board']=='A01-jack'and overlap(box,p['box_mm']):land_hits.append([land['id'],p['ref']])
 for land in ledlands:
  xy=land['xyz_mm'][:2];assert a.inside(expand(xy+xy,.5+.4+.25),ledboard['outline_mm']),'LED land ordinary edge'
 hardware=a.locked_hardware(locked['placements']);foreign=[p for p in hardware if p['ref']not in placed]
 # PCB only requires exclusion of through terminals; body projection is separately unknown.
 foreign_pads=[{'board':name,'ref':p['ref']}for name,b in {'A01-control':boards['A01-control'],'LED-strip':ledboard}.items()for p in foreign if any(overlap(expand(b['outline_mm'],.4),pad)for pad in p['through_pad_keepouts_mm'])]
 projections=[{'board':name,'ref':p['ref'],'status':'UNKNOWN actual body/tail Z; XY projection is not free space'}for name,b in {**boards,'LED-strip':ledboard}.items()for p in foreign if overlap(b['outline_mm'],p['box_mm'])]
 own_led_pads=[p['ref']for p in placed.values()if p['ref'].startswith('J')and any(overlap(expand(ledboard['outline_mm'],.4),b)for b in p['through_pad_keepouts_mm'])]
 own_led_body=[p['ref']for p in placed.values()if p['ref'].startswith('J')and overlap(ledboard['outline_mm'],p['box_mm'])]
 # Actual bore rearshaft relief, nonconductive body cradles and positive clamp surfaces.
 relief=[{'ref':ref,'centre_mm':placed[ref]['origin_mm'],'diameter_proposal_mm':3,'source_rear_shaft_diameter_mm':2,'shaft_rear_projection_mm':3.8,'z_mm':[10,13.8]}for ref in ['RV1307','RV1308']]
 for hole in relief:
  p=placed[hole['ref']];xy=hole['centre_mm'];assert not any(din.tail_circle_overlap(*xy,b,hole['diameter_proposal_mm']/2+.2)for b in p['through_pad_keepouts_mm']),'shaft relief intersects own terminal/mount land'
 supports=[]
 for board,b in boards.items():
  z0,z1=b['z_mm'];framez=[60,62]if board=='A01-core'else[28,30]if board=='A01-jack'else[40,42]if board=='A01-middle'else[18,20]
  for i,xy in enumerate(b['mounts_mm']):supports.append({'id':board+':M'+str(i+1),'board':board,'xy_mm':xy,'drill_mm':2.7,'washer_diameter_mm':5,'rear_head_z_mm':[z1,z1+2.5]if board!='A01-control'else[z0-2.5,z0],'spacer_z_mm':[framez[1],z0]if framez[1]<z0 else[z1,framez[0]],'frame_z_mm':framez,'tool_z_mm':[z1+2.5,105]if board!='A01-control'else[-5,z0-2.5],'load_path':'PCB washer/insulating shoulder→spacer→two longitudinal carrier rails→candidate side/bottom enclosure cleats; no solder joint credited as chassis anchor'})
 frame={'rear':{'rails_boxes_mm':[[237,174,243,282],[305,174,311,282]],'z_mm':[51,62],'crossmembers_boxes_mm':[[237,170,318,174],[237,282,318,286]],'anchors_mm':[[315,172],[315,284]],'anchor_screw':'Proposed M3 rear-access screw into right-side enclosure cleat,6mm tool,5mm washer; enclosure cleat is new candidate structure'},'jack':{'rails_boxes_mm':[[195,94,201,182],[234,94,240,182]],'z_mm':[22,30],'crossmembers_boxes_mm':[[195,91,318,94],[195,182,318,185]],'anchors_mm':[[315,92.5],[315,183.5]],'anchor_screw':'New right-side enclosure cleat; actual neighboring solids along beam remain UNKNOWN'},'control':{'rails_boxes_mm':[[208,264,209.5,307],[227.5,264,229,307]],'z_mm':[18,20],'crossmembers_boxes_mm':[[208,303,229,307],[208,307,318,313]],'anchors_mm':[[315,310]],'body_cradles':[{'ref':ref,'body_box_mm':[213.5,y-5,223.5,y+5],'body_z_mm':[3.2,10],'reaction':'Captive insulating split cradle bears body side/rear surfaces, holds shaft at lockedXY; joined to edge rails by rear bridge beyond lead row; exact retention force and shell tolerance OPEN'}for ref,y in [('RV1307',269),('RV1308',283)]]}}
 frame['middle']={'rails_boxes_mm':[[242,142,248,274],[242,286,248,294],[306,142,314,294]],'z_mm':[34,46],'crossmembers_boxes_mm':[[242,138,318,142],[242,286,318,294]],'mount_tabs':{'boxes_mm':[[233,143,248,149],[233,286,248,292]],'z_mm':[42,46]},'anchors_mm':[[315,140],[315,290]],'status':'New separately supported A01 middle carrier; no shared-backplane anchorage assumed'}
 frame['control']['bottom_crossmember_z_mm']=[12,20]
 for f in frame.values():f['anchor_bosses']=[{'xy_mm':xy,'radius_mm':4,'drill_mm':3.4,'washer_diameter_mm':5,'tool_diameter_mm':6,'status':'Proposed integral circular boss overlaps carrier crossmember; bolts to new enclosure cleat, not an existing panel hole'}for xy in f['anchors_mm']]
 for mount in supports:
  key={'A01-core':'rear','A01-jack':'jack','A01-control':'control','A01-middle':'middle'}[mount['board']];mount['frame_z_mm']=frame[key]['z_mm'];mount['spacer_z_mm']=[frame[key]['z_mm'][1],boards[mount['board']]['z_mm'][0]]if key!='control'else[11.6,18]
 # Explicit bores in right jack rail clear all fourteen permanent terminal approaches.
 guides=[{'land':l['id'],'xy_mm':l['xyz_mm'][:2],'nominal_bore_mm':1.2,'diameter_tolerance_mm':.2,'radial_position_allowance_mm':.3,'maximum_removed_diameter_mm':2,'minimum_open_diameter_mm':1,'z_mm':[22,30],'status':'Insulated wire/insert must fit1mm opening; machining, insulation retention and stress concentration unqualified'}for l in terminal_lands]
 for u,v in itertools.combinations(guides,2):assert math.dist(u['xy_mm'],v['xy_mm'])>=3-1e-9
 # Propose connected rigid carriers; explicit simple beam sensitivity, not installed-load qualification.
 for name,f in frame.items():
  span=max(b[2]-b[0]for b in f['crossmembers_boxes_mm']);width=min(b[3]-b[1]for b in f['crossmembers_boxes_mm']);depth=f['z_mm'][1]-f['z_mm'][0]if name in('rear','middle')else 8;I=width*depth**3/12
  f['planning_model']={'E_MPa':70000,'source':'../stage8/material-evidence.json','load_N':5,'span_mm':span,'rib_depth_mm':depth,'rib_width_mm':width,'cantilever_deflection_mm':5*span**3/(3*70000*I),'bending_stress_MPa':6*5*span/(width*depth**2),'DIN_90N_deflection_sensitivity_mm':90*span**3/(3*70000*I)if name in('rear','middle')else None,'status':'Straight full-span planning surrogate only; cleats/joints, wire bores, panel loads and DIN insertion/removal loads remain unqualified'}
 # Source-coordinate neighboring parts are retained as exclusions, never converted to free volume.
 occupied=json.loads((a.OUT/'stage4/occupied-report.json').read_text());other_rows=[p for p in occupied['rows']if p['function_or_service']!='A01'];historical=[{'ref':p['ref'],'function':p['function_or_service'],'historical_board':p['historical_placement']['board'],'candidate_board':name}for p in other_rows for name,b in boards.items()if overlap(p['historical_placement']['courtyard_mm'],b['outline_mm'])]
 retained_middle=osc['candidate']['middle_header_placements_all_instances']+osc['candidate']['shared_middle_placements']
 middle_retained=[{'A01':h['ref'],'retained':p['ref']}for h in headers.values()if h['board']=='A01-middle'for p in retained_middle if overlap(h['box_mm'],p['box_mm'])]
 old_contacts,old_flanges=din.register(osc['candidate'],ds,de)
 old_DIN_hits=din.screen([dict(h,instance='A01')for h in headers.values()if h['board']=='A01-middle'],old_contacts+old_flanges)
 sweep_hits=[];sweeps=[]
 for h in headers.values():
  z=h['pad_depth_mm'];sweeps.append({'ref':h['ref'],'box_mm':expand(h['box_mm'],2),'z_mm':[z,z+22.3]if h['side']=='rear'else[z-22.3,z],'scope':'Mated7.3mm+15mm axial release;2mm latch/tool XY margin proposal'})
 for u,v in itertools.combinations(sweeps,2):
  if overlap(u['box_mm'],v['box_mm'])and max(u['z_mm'][0],v['z_mm'][0])<min(u['z_mm'][1],v['z_mm'][1]):sweep_hits.append([u['ref'],v['ref']])
 # Local front GH margins pass beside proposed A01 middle except one explicit edge notch.
 middle_notches=spec['middle_access_edge_notches_mm']
 for sw in sweeps:
  for board,b in boards.items():
   owner=headers[sw['ref']]['board']
   if board==owner or not(overlap(sw['box_mm'],b['outline_mm'])and max(sw['z_mm'][0],b['z_mm'][0])<min(sw['z_mm'][1],b['z_mm'][1])):continue
   inter=[max(sw['box_mm'][0],b['outline_mm'][0]),max(sw['box_mm'][1],b['outline_mm'][1]),min(sw['box_mm'][2],b['outline_mm'][2]),min(sw['box_mm'][3],b['outline_mm'][3])]
   effective=[[n[0]-1,n[1]+.4,n[2]-.4,n[3]-.4]for n in middle_notches]if board=='A01-middle'else[]
   assert any(a.inside(inter,n)for n in effective),'connector release crosses uncut own substrate'
 for sw in sweeps:
  if not sw['ref'].endswith(':local')or ':K-PWR:'in sw['ref']:continue
  for oldname,origin in osc['candidate']['origins_mm'].items():
   oldbox=a.box_transform(next(f['box_mm']for f in osc['candidate']['fixtures']if f['id']=='DIN'),origin)
   if overlap(sw['box_mm'],oldbox)and sw['z_mm'][1]>50:sweep_hits.append([sw['ref'],oldname+':DIN conservativereservation'])
 frame_sweep_hits=[]
 for name,f in frame.items():
  for b in f['rails_boxes_mm']+f['crossmembers_boxes_mm']:
   for sw in sweeps:
    if overlap(b,sw['box_mm'])and max(f['z_mm'][0],sw['z_mm'][0])<min(f['z_mm'][1],sw['z_mm'][1]):frame_sweep_hits.append({'frame':name,'header':sw['ref'],'frame_box_mm':b})
 frame_board_hits=[]
 for name,f in frame.items():
  for box in f['rails_boxes_mm']+f['crossmembers_boxes_mm']:
   for board,b in boards.items():
    if overlap(box,b['outline_mm'])and max(f['z_mm'][0],b['z_mm'][0])<min(f['z_mm'][1],b['z_mm'][1]):frame_board_hits.append({'frame':name,'board':board,'box_mm':box})
 tool_board_blockers=[]
 for mount in supports:
  for board,b in boards.items():
   if board!=mount['board']and overlap(expand(mount['xy_mm']+mount['xy_mm'],3),b['outline_mm'])and max(mount['tool_z_mm'][0],b['z_mm'][0])<min(mount['tool_z_mm'][1],b['z_mm'][1]):tool_board_blockers.append({'mount':mount['id'],'blocked_by_board':board,'disposition':'Installed PCB screw access NOT available; remove whole captive front subassembly via front panel before PCB-level factory service. Do not insert driver through retained boards.'})
 handle_hits=[]
 for xy in [[270,178],[270,278]]:
  for p in list(placed.values())+list(headers.values()):
   if p['board']=='A01-core'and overlap(expand(xy+xy,3),p['box_mm']):handle_hits.append(p['ref'])
 # Candidate core board is geometrically disjoint from five retained OSC card outlines.
 core_osc=[key for key,b in osc['candidate']['geometry']['five_card_boxes_mm'].items()if overlap(boards['A01-core']['outline_mm'],b)]
 middle_headers=[dict(h,instance='A01')for h in headers.values()if h['board']=='A01-middle'];din_hits=din.screen(middle_headers,contacts+flanges)
 rear_din_hits=[p['ref']for p in placed.values()if p['board']=='A01-core'and overlap(p['box_mm'],expand(connectors['rear']['box_mm'],1))]
 span=[];bynet={}
 for p in placed.values():
  for pin,net in p['pins'].items():
   if net is not None:bynet.setdefault(net,[]).extend(p['pads_xyz_mm'][pin])
 for net,pts in bynet.items():span.append({'net':net,'endpoint_pad_count':len(pts),'maximum_pad_separation_mm':max((math.dist(x,y)for x,y in itertools.combinations(pts,2)),default=0),'interpretation':'All endpoints included; not routed path or loop stability'})
 bypass=[]
 for pair in inventory['bypass_associations']:
  p=placed[pair['bypass_ref']];q=placed[pair['target_ref']];dist={}
  for net in set(p['pins'].values())&set(q['pins'].values()):
   if net is not None:dist[net]=min(math.dist(x,y)for pin,n in p['pins'].items()if n==net for x in p['pads_xyz_mm'][pin]for pin2,n2 in q['pins'].items()if n2==net for y in q['pads_xyz_mm'][pin2])
  bypass.append({'capacitor':p['ref'],'target':q['ref'],'same_net_nearest_pad_mm':dist,'status':'Source association retained; actual loop routing/parasitics unqualified'})
 checks={'same_face_or_THT_header_collisions':collisions,'mount_tool_package_collisions':mount_hits,'terminal_land_package_collisions':land_hits,'package_outside_board':containment,'foreign_through_pad_board_conflicts':foreign_pads,'own_jack_through_pad_LED_strip_conflicts':own_led_pads,'core_OSC_outline_conflicts':core_osc,'middle_DIN_header_exclusions':din_hits,'rear_DIN_package_exclusions':rear_din_hits,'middle_retained_header_exclusions':middle_retained,'retained_DIN_header_exclusions':old_DIN_hits,'connector_release_sweep_conflicts':sweep_hits,'handle_attachment_exclusions':handle_hits,'frame_connector_release_conflicts':frame_sweep_hits,'carrier_through_own_PCB_conflicts':frame_board_hits}
 assert not any(checks.values()),'A01 modeled exclusion: '+str({k:v for k,v in checks.items()if v})
 bindings=files+[a.OUT/'stage4/occupied-report.json',a.OUT/'stage8/material-evidence.json',Path(__file__),Path(__file__).with_name('test_stage10_mechanical.py'),Path(a.__file__),Path(din.__file__),Path(a.c.__file__),Path(__file__).with_name('stage3_reservations.py'),Path(__file__).with_name('stage4_mechanical.py'),Path(interfaces.__file__)]+sources+list((ROOT/'.claude/skills/component-bourns-ptv09a-4020f-b103').glob('*.json'))+list((ROOT/'.claude/skills/component-bourns-ptv09a-4020f-b104').glob('*.json'))
 return {'status':'A01 INDEPENDENT SOURCE MECHANICAL CANDIDATE; ACCEPTANCE OPEN','placements':placed,'boards':boards,'board_pad_faces_mm':faces,'headers':headers,'din_connectors':connectors,'DIN_contacts':contacts,'DIN_flange_holes':flanges,'fixed_LED_substrate':ledboard,'LED_wire_lands':ledlands,'terminal_lands':terminal_lands,'terminal_extensions':extensions,'retained_NC_terminals':[{'ref':r,'pin':'TN','net':None}for r in ['J1308','J1309','J1310']],'bypass_associations':bypass,'all_net_pad_spans':span,'mounts':supports,'carrier_frames':frame,'minimum_enclosure_internal_candidate_mm':spec['minimum_enclosure_internal_candidate_mm'],'carrier_wire_guides':guides,'installed_tool_board_blockers':tool_board_blockers,'connector_release_sweeps':sweeps,'middle_access_edge_notches_mm':middle_notches,'historical_other_function_projections':historical,'pot_rearshaft_relief_holes':relief,'pot_datum':{'source_url':'https://www.bourns.com/docs/product-datasheets/PTV09.pdf','sha256':'411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558','locator':'physicalpage1 PTV09A-4 side/frontviews; physicalpage0 horizontalrear PCB layout','signed_transform':'drawing rear-body seating plane→Z10; shaftfront→negativeZ; lockedshaftXY=footprintorigin; terminals topositiveZ; no perpendicular-board inference','body_depth_mm':6.8,'shaft_L_mm':20,'shaft_L_tolerance_mm':.5,'panel_rear_z_mm':0,'panel_thickness_proposal_mm':spec['panel_thickness_proposal_mm'],'shaft_tip_z_mm':-10,'shaft_projection_past_panel_front_mm':10-spec['panel_thickness_proposal_mm'],'bushingless':True,'no_pot_nut_reaction':True},'source_checks':checks,'foreign_hardware_projections':projections,'LED_strip_own_jack_body_projections_UNKNOWN':own_led_body,'service':{'procedure':['Power off/discharge; remove rear cover.','Disconnect A01 rear power GH, release four captive core screws, support both handles and withdraw rear core40mm axially from supported DIN.','Front jack/control replacement requires disconnecting its two/one GH ports via planned enclosure access, retaining carrier, removing the removable front panel and relevant knobs/jacknuts, then releasing carrier cleats; no home soldering.','Reinstall factory assembly with fixed shaft registration; verify clamp/insulation before power.'],'core_handles':[{'xy_mm':[270,178],'attachment_radius_mm':3,'rear_projection_z_mm':[76,94]},{'xy_mm':[270,278],'attachment_radius_mm':3,'rear_projection_z_mm':[76,94]}],'extraction_mm':40,'external_workspace_mm':100,'access_status':'Candidate removable front panel/right-side service opening and cleats required; otherfunction harness retention remains UNKNOWN','normal_OSC_calibration':'No middle removal proposed'},'counts':inventory['counts'],'source_sha256':a.binding(bindings),'physical_acceptance':False,'qualified_free_regions':[],'native':'NOT RUN','simulation':'NOT RUN'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
 for name,data in [('mechanical-report.json',json.dumps(r,separators=(',',':'),sort_keys=True)+'\n')]:
  p=OUT/name
  if args.check:assert p.read_text()==data,'stale '+name
  else:p.write_text(data)
 print({k:len(v)for k,v in r['source_checks'].items()})
if __name__=='__main__':main()
