"""Bounded X1 complete-package placement, explicit mounts and conditional service screen."""
import argparse,copy,hashlib,itertools,json,math
from pathlib import Path
import assembly as a
import stage6_hosting as hosting
import stage6_mechanical as din
import stage7_interfaces as transport
ROOT=a.ROOT;OUT=a.OUT/'stage7'
def overlap3(a_box,a_z,b_box,b_z):return hosting.overlap(a_box,b_box)and max(a_z[0],b_z[0])<min(a_z[1],b_z[1])
def move(p,delta):
 q=copy.deepcopy(p);q['origin_mm']=a.transform(q['origin_mm'],delta);q['box_mm']=a.box_transform(q['box_mm'],delta);q['pads_mm']={pin:[a.transform(x,delta)for x in points]for pin,points in q['pads_mm'].items()};q['through_pad_keepouts_mm']=[a.box_transform(b,delta)for b in q['through_pad_keepouts_mm']];return q

def substrate_screen(outline,cuts):
 xs=sorted({outline[0],outline[2],*[v for b in cuts for v in (b[0],b[2])]});ys=sorted({outline[1],outline[3],*[v for b in cuts for v in (b[1],b[3])]})
 cells={(i,j)for i in range(len(xs)-1)for j in range(len(ys)-1)if not any(b[0]<(xs[i]+xs[i+1])/2<b[2]and b[1]<(ys[j]+ys[j+1])/2<b[3]for b in cuts)}
 components=0
 while cells:
  components+=1;todo=[cells.pop()]
  while todo:
   i,j=todo.pop()
   for n in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
    if n in cells:cells.remove(n);todo.append(n)
 gaps=[]
 for b in cuts:
  gaps.extend(v for v in [b[0]-outline[0],outline[2]-b[2],b[1]-outline[1],outline[3]-b[3]]if v>1e-8)
 for a,b in itertools.combinations(cuts,2):
  if max(a[1],b[1])<min(a[3],b[3]):gaps.extend(v for v in [a[0]-b[2],b[0]-a[2]]if v>1e-8)
  if max(a[0],b[0])<min(a[2],b[2]):gaps.extend(v for v in [a[1]-b[3],b[1]-a[3]]if v>1e-8)
 return {'connected_components':components,'minimum_axis_aligned_positive_web_mm':min(gaps)if gaps else None,'status':'Exact rectangular aperture arrangement connectivity only; minimumpositiveweb is a source diagnostic, not a stiffness/fabrication acceptance threshold. Circularmount holes conservatively boxed.'}

def build():
 files=[a.OUT/'stage6/hosting-report.json',OUT/'mechanical-input.json',OUT/'interface-input.json',ROOT/'design/grid/placements.lock.json',ROOT/'design/architecture-278/source-ledger.json',a.OUT/'stage6/candidate-report.json',a.OUT/'stage6/mechanical-input.json',a.OUT/'stage5/din-evidence.json',ROOT/'design/partition/floorplan-candidate.json']
 prior,spec,interface,lock,ledger,osc,ds,de,floor=[json.loads(p.read_text())for p in files];placed=copy.deepcopy(prior['placements']);assert spec['front_rear_face_z_mm']-spec['front_panel_face_z_mm']==spec['PCB_thickness_mm']or math.isclose(spec['front_rear_face_z_mm']-spec['front_panel_face_z_mm'],spec['PCB_thickness_mm'])
 for ref,delta in spec['package_translations_from_stage6_mm'].items():
  assert ref in placed and not placed[ref]['panel_uid'],'fixed/invented package movement'
  assert len(delta)==2 and all(math.isfinite(v)for v in delta),'invalid package translation'
  placed[ref]=move(placed[ref],delta)
 packages,source=hosting.live_packages(ledger);fixed={p['ref']:p for p in lock['placements']if p['block']=='X1'};hosting.validate(placed,packages,source,fixed)
 for p in placed.values():p['conditional_pad_depth_mm']=spec['front_panel_face_z_mm']if p['side']=='panel'else spec['front_rear_face_z_mm'];p['pads_xyz_mm']={pin:[xy+[p['conditional_pad_depth_mm']]for xy in points]for pin,points in p['pads_mm'].items()}
 headers=transport.transport_geometry(interface);hardware=a.locked_hardware(lock['placements']);mounts=[]
 assert spec['mount']['washer_contact_surface_z_mm']==spec['front_rear_face_z_mm'] and spec['mount']['spacer_contact_surface_z_mm']==spec['front_panel_face_z_mm'],'PCB clamp contact faces mismatch'
 assert spec['mount']['spacer_z_mm'][1]==spec['front_panel_face_z_mm'] and spec['mount']['head_z_mm'][0]==spec['front_rear_face_z_mm'],'head and spacer must straddle PCB'
 bypass=[]
 for old in prior['bypass_associations']:
  cap,target=placed[old['capacitor']],placed[old['target']];distances={}
  for net in hosting.RAILS:
   left=[xyz for pin,n in cap['pins'].items()if n==net for xyz in cap['pads_xyz_mm'][pin]];right=[xyz for pin,n in target['pins'].items()if n==net for xyz in target['pads_xyz_mm'][pin]]
   if left and right:distances[net]=min(math.dist(x,y)for x,y in itertools.product(left,right))
  bypass.append({'capacitor':old['capacitor'],'target':old['target'],'owner':cap['owner'],'same_net_nearest_pad_mm':distances,'loop_status':'CURRENT Stage7 XYZ nearestmatchingpads; grounded inputs are not dedicated supply-return pins; routedloop/impedance UNKNOWN'})
 apertures=[]
 for board,b in spec['boards'].items():
  for h in hardware:
   if h['ref']in placed:continue
   for i,pad in enumerate(h['through_pad_keepouts_mm']):
    margin=spec['foreign_THT_aperture_margin_mm'];cut=[pad[0]-margin,pad[1]-margin,pad[2]+margin,pad[3]+margin]
    if hosting.overlap(cut,b['outline_mm']):apertures.append({'board':board,'foreign_ref':h['ref'],'pad_index':i,'source':h['source'],'aperture_box_mm':[max(cut[0],b['outline_mm'][0]),max(cut[1],b['outline_mm'][1]),min(cut[2],b['outline_mm'][2]),min(cut[3],b['outline_mm'][3])],'z_mm':[20,21.6],'authority':spec['foreign_THT_aperture_authority']})
 aperture_hits=[{'board':cut['board'],'foreign_ref':cut['foreign_ref'],'own_ref':p['ref']}for cut in apertures for p in list(placed.values())+list(headers.values())if p['board']==cut['board']and hosting.overlap(cut['aperture_box_mm'],p['box_mm'])]

 for board,b in spec['boards'].items():
  assert len(b['mount_centres_mm'])>=3,'insufficient mounting points'
  points=b['mount_centres_mm'];assert any(abs((v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0]))>1 for u,v,w in itertools.combinations(points,3)),'collinear support pattern'
  for i,(x,y)in enumerate(points):
   d=spec['mount']['driver_envelope_diameter_mm'];r=d/2;box=[x-r,y-r,x+r,y+r];assert a.inside(box,b['outline_mm']),'mount/tool outside board outline'
   assert min(x-b['outline_mm'][0],b['outline_mm'][2]-x,y-b['outline_mm'][1],b['outline_mm'][3]-y)-spec['mount']['PCB_hole_diameter_mm']/2>=spec['mount']['minimum_edge_annulus_mm'],'mount hole edge annulus insufficient'
   mounts.append({'id':board+':M'+str(i+1),'board':board,'centre_mm':[x,y],'hole_diameter_mm':spec['mount']['PCB_hole_diameter_mm'],'attachment_box_mm':box,'screw_head_z_mm':spec['mount']['head_z_mm'],'driver_z_mm':spec['mount']['driver_approach_z_mm'],'spacer_z_mm':spec['mount']['spacer_z_mm'],'carrier_boss_z_mm':spec['mount']['carrier_boss_z_mm'],'load_path':spec['mount']['load_path']})
 mount_hardware=[{'mount':m['id'],'fixed_ref':h['ref']}for m in mounts for h in hardware if hosting.overlap(m['attachment_box_mm'],h['box_mm'])]
 mount_apertures=[{'mount':m['id'],'foreign_ref':c['foreign_ref']}for m in mounts for c in apertures if m['board']==c['board']and hosting.overlap(m['attachment_box_mm'],c['aperture_box_mm'])]
 mount_packages=[{'mount':m['id'],'ref':p['ref']}for m in mounts for p in list(placed.values())+list(headers.values())if p['board']==m['board']and hosting.overlap(m['attachment_box_mm'],p['box_mm'])]
 pairs=[{'a':p['ref'],'b':q['ref'],'same_face':p['side']==q['side']}for p,q in itertools.combinations(placed.values(),2)if p['board']==q['board']and hosting.overlap(p['box_mm'],q['box_mm'])]
 tails=[{'ref':p['ref'],'fixed_ref':h['ref']}for p in placed.values()for h in hardware if p['ref']!=h['ref']and any(hosting.overlap(p['box_mm'],b)for b in h['through_pad_keepouts_mm'])]
 header_packages=[{'header':h['ref'],'ref':p['ref']}for h in headers.values()for p in placed.values()if h['board']==p['board']and hosting.overlap(h['box_mm'],p['box_mm'])]
 for p in list(placed.values())+list(headers.values()):
  if p['board']in spec['boards']:assert a.inside(p['box_mm'],spec['boards'][p['board']]['outline_mm']),'own package/header outside board outline'
 contacts,flanges=din.register(osc['candidate'],ds,de);middle=[dict(h,instance='X1')for h in headers.values()if h['board']=='middle-X1'];din_hits=din.screen(middle,contacts+flanges)
 sweeps=[]
 for h in headers.values():
  link=next(l for l in interface['links']if l['id']==h['link']);stroke=link['service']['normal_withdrawal_proposal_mm'];z=h['pad_depth_mm'];height=7.3
  sweeps.append({'id':h['ref'],'box_mm':h['box_mm'],'z_mm':[z,z+height+stroke]if h['side']=='rear'else[z-height-stroke,z],'mated_z_mm':[z,z+height]if h['side']=='rear'else[z-height,z]})
 sweep_pairs=[{'a':p['id'],'b':q['id'],'classification':'SIMULTANEOUS SWEEP COLLISION; sequential removal alone needs parked-housing/cable proof'}for p,q in itertools.combinations(sweeps,2)if overlap3(p['box_mm'],p['z_mm'],q['box_mm'],q['z_mm'])]
 mount_sweeps=[{'mount':m['id'],'header':s['id']}for m in mounts for s in sweeps if overlap3(m['attachment_box_mm'],m['driver_z_mm'],s['box_mm'],s['z_mm'])]
 strain=[]
 for link in interface['links']:
  service=link['service'];offset=service['strain_relief_offset_xy_mm'];size=service['strain_relief_box_size_mm']
  for end in ['front','middle']:
   h=headers['X1:'+link['id']+':'+end];x,y=a.transform(offset,h['origin_mm'],h['quarter_turn']);box=[x-size[0]/2,y-size[1]/2,x+size[0]/2,y+size[1]/2]
   strain.append({'id':h['ref']+':strain','box_mm':box,'z_mm':[30,34],'attachment':'PROPOSED insulated enclosure/carrier anchored clamp; attachment design and force rating UNKNOWN; not solder-supported'})
 strain_sweeps=[{'strain':p['id'],'sweep':q['id']}for p in strain for q in sweeps if overlap3(p['box_mm'],p['z_mm'],q['box_mm'],q['z_mm'])]
 strain_mounts=[{'strain':p['id'],'mount':m['id']}for p in strain for m in mounts if overlap3(p['box_mm'],p['z_mm'],m['attachment_box_mm'],m['driver_z_mm'])]
 fixtures=[]
 for old in prior['obstruction_screen']['existing_middle_reservation_intersections']:
  f=spec['rear_fixture_required_envelopes'][old['ref']];fixtures.append({'instance':old['instance'],'ref':old['ref'],'box_mm':old['box_mm'],'required_z_mm':f['z_mm'],'intersects_new_header_sweep':any(overlap3(old['box_mm'],f['z_mm'],s['box_mm'],s['z_mm'])for s in sweeps),'classification':'CONDITIONALLY SEPARATED ONLY IF PROPOSED REAR-FACING HARDWARE Z LIMIT IS MET; source hardware unselected','minimum_Z_gap_to_middle_sweep_mm':f['z_mm'][0]-48.4})
 substrates={}
 for board,b in spec['boards'].items():
  cuts=[c['aperture_box_mm']for c in apertures if c['board']==board]+[[m['centre_mm'][0]-m['hole_diameter_mm']/2,m['centre_mm'][1]-m['hole_diameter_mm']/2,m['centre_mm'][0]+m['hole_diameter_mm']/2,m['centre_mm'][1]+m['hole_diameter_mm']/2]for m in mounts if m['board']==board]
  substrates[board]=substrate_screen(b['outline_mm'],cuts)
 spans=[]
 for net in sorted({n for p in placed.values()for n in p['pins'].values()if n is not None}):
  def ends(pop):return[xy+[spec['front_panel_face_z_mm']if p['side']=='panel'else spec['front_rear_face_z_mm']]for p in pop.values()for pin,n in p['pins'].items()if n==net for xy in p['pads_mm'][pin]]
  old,new=ends(prior['placements']),ends(placed);span=lambda pts:max((math.dist(x,y)for x,y in itertools.combinations(pts,2)),default=0);spans.append({'net':net,'endpoint_count':len(new),'before_max_pad_separation_mm':span(old),'after_max_pad_separation_mm':span(new),'delta_mm':span(new)-span(old),'qualification':'actual pad geometry only; complete electrical feedback/returns/budgets separately reviewed'})
 foreign=[{'board':board,'historical_ref':p['ref'],'historical_board':p['board'],'classification':'UNKNOWN new3Dsolid; historical overlap retained, not free space'}for board,b in spec['boards'].items()for p in floor['placements']if p['ref']not in placed and hosting.overlap(b['outline_mm'],p['courtyard_mm'])]
 files += [Path(__file__),Path(__file__).with_name('test_stage7_mechanical.py'),Path(transport.__file__),Path(hosting.__file__),Path(a.__file__),Path(din.__file__),ROOT/'scripts/architecture278/implementation/stage4_mechanical.py',ROOT/'scripts/architecture278/implementation/stage3_reservations.py']+[ROOT/h['source']for h in hardware]+[ROOT/p['source']for p in headers.values()]
 hashes=a.binding(files);hashes.update(prior['source_sha256']);hashes.update(osc['source_sha256'])
 return {'status':'X1 EXPLICIT MOUNT/PACKAGE/SERVICE SOURCE DEMONSTRATOR; NOT PHYSICAL ACCEPTANCE','source_sha256':hashes,'placements':placed,'boards':spec['boards'],'counts':prior['counts'],'source_pins_including_NC':sum(len(p['pins'])for p in placed.values()),'mounts':mounts,'mount_requirements':spec['mount'],'functional_groups':spec['functional_groups'],'bypass_associations':bypass,'foreign_through_pad_substrate_apertures':apertures,'substrate_geometry_checks':substrates,'strain_relief_reservations':strain,'all_net_pad_span_changes':spans,'source_checks':{'substrate_aperture_own_package_hits':aperture_hits,'mount_aperture_hits':mount_apertures,'strain_header_sweep_hits':strain_sweeps,'strain_mount_driver_hits':strain_mounts,'mount_fixed_hardware_XY_hits':mount_hardware,'mount_package_header_XY_hits':mount_packages,'whole_package_courtyard_pairs':pairs,'package_fixed_through_pad_hits':tails,'header_source_package_pairs':header_packages,'middle_registered_DIN_hits':din_hits,'simultaneous_header_sweep_pairs':sweep_pairs,'mount_driver_header_sweep_pairs':mount_sweeps},'source_service_sweeps':sweeps,'five_rear_fixture_projections':fixtures,'stage6_25_opposite_pairs':[{'a':p['a'],'b':p['b'],'classification':'RESOLVED_BY_WHOLE_COURTYARD_EXCLUSION'if not hosting.overlap(placed[p['a']]['box_mm'],placed[p['b']]['box_mm'])else'UNRESOLVED'}for p in prior['obstruction_screen']['internal_courtyard_pairs']],'stage6_13_perimeter_projections':'Old generic support strips superseded by seven explicit mount/attachment/tool locations, with all438 fixed hardware screened','historical_other_function_reservations':foreign,'qualified_free_regions':[],'mount_load_path_acceptance':'UNKNOWN carrier-to-enclosure anchor/structural stiffness/fastener grade; explicitly not force-qualified','physical_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();s=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';p=OUT/'mechanical-report.json'
 if args.check:assert p.read_text()==s,'stale Stage7 mechanical report'
 else:p.write_text(s)
 print({k:len(v)for k,v in r['source_checks'].items()})
if __name__=='__main__':main()
