"""Concrete X1 GH harness transport source; no native, simulation or fabrication."""
import argparse,copy,hashlib,json,math
from pathlib import Path
import assembly as a
ROOT=a.ROOT;OUT=a.OUT/'stage7'
SIG={'1':'/X1/A_BUFFER','2':'/X1/B_BUFFER','3':'/X1/SELECTOR_REMOTE','4':'AGND'}
PINMAP={'J-SIG':SIG,'C-SIG':SIG,'J-PWR':{'1':'+12V','2':None,'3':'-12V','4':None,'5':'+5V','6':None,'7':'AGND'},'C-PWR':{'1':'+12V','2':'-12V','3':'AGND'}}
FOOTPRINTS={7:'footprints/kicad/zudo-osc-hole-field.pretty/JST_GH7_BM_TopEntry.kicad_mod',3:'footprints/kicad/zudo-osc-hole-field.pretty/JST_GH3_BM_TopEntry.kicad_mod',4:'design/architecture-278/implementation/stage7/footprints/JST_GH4_BM_TopEntry_Candidate.kicad_mod'}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def transport_geometry(spec):
 """Read-only geometry API for mechanical screening; does not read final reports."""
 need(len(spec['links'])==4 and {l['id']for l in spec['links']}==set(PINMAP),'four exact source transport links')
 need(spec['front_panel_surface_mm']==20 and spec['front_rear_surface_mm']==21.6 and spec['middle_GH_surface_mm']==48.4,'reviewed board-face datums changed')
 headers={}
 for link in spec['links']:
  need(link['pins']==PINMAP[link['id']],'signal/power pinmap mutation')
  n=len(link['pins']);path=FOOTPRINTS[n];pads=a.c.footprint_pads(path);need(set(pads)==set(link['pins'])|{'MP1','MP2'},'whole header physical pads')
  shape={'ref':'','owner':'added-transport','box':a.c.courtyard(path),'pads':pads,'pins':dict(link['pins'],MP1=None,MP2=None),'holes':[],'source':path,'units':[]}
  for end in ('front','middle'):
   pose=link[end];ref='X1:'+link['id']+':'+end;shape['ref']=ref
   need(pose['side']==('rear'if end=='front'else'panel'),'connector face changed')
   need(pose['pad_depth_mm']==(21.6 if end=='front'else 48.4),'actual mounting face required')
   need(pose['quarter_turn']in(0,1,2,3)and all(math.isfinite(x)for x in pose['origin_mm']),'finite orthogonal header pose')
   q=a.located(a.face_shape(shape,pose['side']),pose['origin_mm'],pose['quarter_turn'],pose['board'],pose['side'])
   q.update({'link':link['id'],'end':end,'pad_depth_mm':pose['pad_depth_mm'],'pads_xyz_mm':{p:[xy+[pose['pad_depth_mm']]for xy in points]for p,points in q['pads_mm'].items()},'header_mpn':f'BM{n:02}B-GHS-TBT(LF)(SN)','housing_mpn':f'GHR-{n:02}V-S','contact_mpn':'SSHL-002T-P0.2','positions':n,'native_validated':False})
   headers[ref]=q
 return headers

def evidence():
 conn=json.loads((ROOT/'design/connectors/jst-gh.json').read_text())
 front=json.loads((a.OUT/'front-evidence.json').read_text())
 pdf=ROOT/conn['source']['path'];need(hashlib.sha256(pdf.read_bytes()).hexdigest()==conn['source']['sha256'],'retained primary GH source hash')
 sizes={7:next(s for s in conn['sizes']if s['positions']==7),3:next(s for s in conn['sizes']if s['positions']==3),4:next(s for s in front['candidate_JST_2_4_derived']if s['positions']==4)}
 for n,s in sizes.items():
  need(s['header_mpn']==f'BM{n:02}B-GHS-TBT(LF)(SN)'and s['housing_mpn']==f'GHR-{n:02}V-S'and s['contact_mpn']=='SSHL-002T-P0.2','exact mating identity')
  pads=a.c.footprint_pads(FOOTPRINTS[n]);span=(n-1)*1.25
  expected={str(i):[[span/2-(i-1)*1.25,0]]for i in range(1,n+1)}|{'MP1':[[-span/2-1.85,3.35]],'MP2':[[span/2+1.85,3.35]]}
  need(pads==expected,'drawing-derived exact lands changed')
  for node in a.c.sexpr((ROOT/FOOTPRINTS[n]).read_text()):
   if isinstance(node,list)and node and node[0]=='pad':
    need(node[2:4]==['smd','rect'],'reviewed SMD rectangle changed')
    need(list(map(float,a.c.field(node,'size')))==([1,2.8]if node[1].startswith('MP')else[.6,1.7]),'source land dimensions changed')
  need(a.c.courtyard(FOOTPRINTS[n])==[-span/2-2.6,-1.1,span/2+2.6,5],'reviewed courtyard allocation changed')
 return {'primary_source':conn['source'],'exact_sizes':sizes,'rating_scope':{'source_current_A_per_contact':1,'condition':'AWG26; sourceoperatingtemperature includes energizedrise; installed bundled/contact/crimp qualification UNKNOWN','initial_mated_contact_max_ohm':.030,'after_test_mated_contact_max_ohm':.050,'per_harness_two_contacts_initial_ohm':.060,'per_harness_two_contacts_after_test_ohm':.100,'scope':'source testconditions only; not deliveredwire/crimp/copper/groundimpedance or qualifiedassemblycurrent'},'footprint_validation':'source parser/pad/courtyard evidence only; nativeKiCad NOT RUN'}

def endpoint(headers,ref,pin):
 return {'ref':ref,'pin':pin,'pad_xyz_mm':headers[ref]['pads_xyz_mm'][pin][0]}

def middle_edges(headers):
 defs=[(SIG[str(i)],'J-SIG',str(i),'C-SIG',str(i))for i in (1,2,3)]
 defs += [('+12V','J-PWR','1','C-PWR','1'),('-12V','J-PWR','3','C-PWR','2')]
 defs += [('AGND','J-PWR','7',link,pin)for link,pin in [('J-SIG','4'),('C-SIG','4'),('C-PWR','3')]]
 out=[]
 for net,left,lp,right,rp in defs:
  l=endpoint(headers,'X1:'+left+':middle',lp);r=endpoint(headers,'X1:'+right+':middle',rp)
  need(headers[l['ref']]['pins'][lp]==headers[r['ref']]['pins'][rp]==net,'middle copper cross-net join')
  dx,dy=sorted([abs(l['pad_xyz_mm'][0]-r['pad_xyz_mm'][0]),abs(l['pad_xyz_mm'][1]-r['pad_xyz_mm'][1])])
  out.append({'net':net,'from':l,'to':r,'geometric_minimum_mm':math.dist(l['pad_xyz_mm'],r['pad_xyz_mm']),'allocation_mm':1.15*(dy-dx+math.hypot(dx,dx))+7,'status':'proposed un-routed middlecopper allocation; impedance/width/layer unknown'})
 return out

def build_from(spec,mechanical):
 headers=transport_geometry(spec);ev=evidence();packages=copy.deepcopy(mechanical['placements'])
 original=json.loads((a.OUT/'stage6/hosting-report.json').read_text())
 need(set(packages)==set(original['placements'])and len(packages)==56,'complete X1 source placement population')
 inventory=[]
 for ref,p in packages.items():
  prior=original['placements'][ref]
  need(p['pins']==prior['pins']and p['units']==prior['units']and p['owner']==prior['owner'],'whole source units/net/owner changed')
  depth=p.get('conditional_pad_depth_mm')
  need(depth==(21.6 if p['side']=='rear'else 20),'explicit source package mounted-face datum required')
  need(set(p['pads_mm'])==set(p['pins']),'physical source pad omission')
  p['pads_xyz_mm']={pin:[xy+[depth]for xy in coords]for pin,coords in p['pads_mm'].items()}
  for pin,net in p['pins'].items():inventory.append({'ref':ref,'pin':pin,'net':net,'board':p['board'],'pads_xyz_mm':p['pads_xyz_mm'][pin]})
 need(len(inventory)==182 and sum(len(p['units'])for p in packages.values())==76,'source pin/unit coverage')
 links=[];service=[]
 for link in spec['links']:
  front='X1:'+link['id']+':front';middle='X1:'+link['id']+':middle';wire=link['wire'];cut=wire['nominal_mm'];tol=wire['cut_tolerance_mm']
  need(all(math.isfinite(v)for v in (cut,tol,wire['minimum_slack_mm']))and cut>tol>=0 and wire['minimum_slack_mm']>=10,'wire allocation invalid')
  need(wire['AWG']==26,'source current-condition wire gauge changed')
  conductors=[]
  for pin,net in link['pins'].items():
   if net is None:continue
   fp=headers[front]['pads_xyz_mm'][pin][0];mp=headers[middle]['pads_xyz_mm'][pin][0];dist=math.dist(fp,mp);stroke=link['service']['normal_withdrawal_proposal_mm']
   need(math.isfinite(stroke)and stroke>=0,'withdrawal proposal invalid')
   cases=[]
   for fmove,mmove in ((0,0),(stroke,0),(0,stroke),(stroke,stroke)):
    f=fp[:2]+[fp[2]+fmove];m=mp[:2]+[mp[2]-mmove]
    cases.append({'front_unplug_mm':fmove,'middle_unplug_mm':mmove,'front_pad_proxy_xyz_mm':f,'middle_pad_proxy_xyz_mm':m,'straight_separation_mm':math.dist(f,m)})
   maxdist=max(x['straight_separation_mm']for x in cases)
   conductors.append({'pin':pin,'net':net,'front_header':front,'middle_header':middle,'front_pad_xyz_mm':fp,'middle_pad_xyz_mm':mp,'wire_cut_nominal_mm':cut,'wire_cut_tolerance_mm':tol,'wire_min_mm':cut-tol,'wire_max_mm':cut+tol,'straight_pad_distance_mm':dist,'minimum_remaining_slack_mm':cut-tol-dist,'service_endpoint_cases':cases,'maximum_service_proxy_distance_mm':maxdist,'minimum_service_proxy_slack_mm':cut-tol-maxdist,'minimum_slack_allocation_mm':wire['minimum_slack_mm'],'slack_screen_pass':cut-tol-maxdist>=wire['minimum_slack_mm'],'mated_contacts':2,'crimp_terminations':2,'wire_resistance_ohm':None,'qualification':'UNKNOWN; cutlength proposed; actual wireexit/bend/slack/retention unmeasured'})
  links.append({'id':link['id'],'pins':link['pins'],'front_header':front,'middle_header':middle,'conductors':conductors,'GH_pair_developed_allocation_mm':spec['GH_pair_developed_allocation_mm'],'wire':wire,'transport_function':'signal-and-AGND'if link['id'].endswith('SIG')else'power-and-AGND'})
  for ref in (front,middle):
   h=headers[ref];box=h['box_mm'];z=h['pad_depth_mm'];normal=1 if h['side']=='rear'else-1;stroke=link['service']['normal_withdrawal_proposal_mm'];end=z+normal*(7.3+stroke)
   offset=link['service']['strain_relief_offset_xy_mm'];centre=a.transform(offset,h['origin_mm'],h['quarter_turn']);w,t=link['service']['strain_relief_box_size_mm']
   service.append({'header':ref,'normal_z':normal,'mated_height_reference_mm':7.3,'withdrawal_proposal_mm':stroke,'body_and_unplug_swept_box_xyz_mm':box[:2]+[min(z,end)]+box[2:]+[max(z,end)],'strain_relief_reservation_xy_mm':[centre[0]-w/2,centre[1]-t/2,centre[0]+w/2,centre[1]+t/2],'strain_relief_Z_reservation_mm':[30,34],'strain_relief_attachment':link['service']['attachment'],'proven_release_stroke_mm':None,'retention_force_N':None,'wire_bend_radius_mm':None,'status':'explicit conditional sweep/reservation; support/body/tool proof remains mechanical; not installed release clearance'})
 allw=[w for link in links for w in link['conductors']]
 need(len(allw)==15 and sum(w['net']=='AGND'for w in allw)==4 and sum(w['net'].startswith('/X1/')for w in allw)==6,'physical conductor accounting')
 boundaries=[{'net':net,'actual_middle_pad':endpoint(headers,'X1:J-PWR:middle',pin),'upstream_source_connector':None,'upstream_route_length_mm':None,'current_capacity_A':None,'source_return_impedance_ohm':None,'status':'real interfacepad identified; wholePOWERsource/distribution realization OPEN'}for pin,net in PINMAP['J-PWR'].items()if net is not None]
 bypass=[]
 for old in original['bypass_associations']:
  ref,target=old['capacitor'],old['target'];dist={}
  for net in ('+12V','-12V','+5V','AGND'):
   x=[pt for pin,n in packages[ref]['pins'].items()if n==net for pt in packages[ref]['pads_xyz_mm'][pin]];y=[pt for pin,n in packages[target]['pins'].items()if n==net for pt in packages[target]['pads_xyz_mm'][pin]]
   if x and y:dist[net]=min(math.dist(a,b)for a in x for b in y)
  bypass.append({'capacitor':ref,'target':target,'owner':packages[ref]['owner'],'same_net_nearest_pad_mm':dist,'scope':'actualupdatedpads; AGNDmaybegroundedinput, notdedicatedreturn; routedloopUNKNOWN'})
 front_nets={}
 for row in inventory:
  if row['net']is None:continue
  key=row['board']+'|'+row['net'];front_nets.setdefault(key,{'board':row['board'],'net':row['net'],'source_endpoints':[],'transport_header_endpoints':[],'routed_copper':None})['source_endpoints'].append(row)
 for h in headers.values():
  if h['end']!='front':continue
  for pin,net in h['pins'].items():
   if net is None:continue
   key=h['board']+'|'+net;need(key in front_nets,'front header introduces source-absent net')
   front_nets[key]['transport_header_endpoints'].append(endpoint(headers,h['ref'],pin))
 compatible=[]
 for i,left in enumerate(links):
  for right in links[i+1:]:
   if len(left['pins'])==len(right['pins']):compatible.append({'links':[left['id'],right['id']],'same_position_count':True,'identical_net_pinmap':left['pins']==right['pins'],'status':'same4positionSIGNALmap; notpower/signal swap; cablelength/service substitution stillunqualified'})
 need(all(p['identical_net_pinmap']for p in compatible),'physicallycompatible conflictingpinmaps')
 return {'status':'X1 REAL GH INTERFACES; COMPLETE SOURCE ACCOUNTING; HARDWARE QUALIFICATION OPEN','headers':headers,'links':links,'mating_compatibility':{'same_size_pairs':compatible,'J_PWR_unused_housing_cavities':['2','4','6'],'unused_cavities':'no wire/crimp; headerNCpads remain soldered isolated; no invented plugs','remaining':'Distinctsize prevents exactcompatible conflictingmap inthisset; partialinsertion, wrongvendorparts, coding andfactoryprocess stillunqualified'},'packages':packages,'source_packages':packages,'source_endpoint_inventory':inventory,'front_net_connections':list(front_nets.values()),'middle_trace_edges':middle_edges(headers),'middle_upstream_power_boundaries':boundaries,'service_reservations':service,'source_evidence':ev,
  'transport_BOM':{'added_headers':8,'added_housings':8,'crimp_contacts':30,'physical_wire_conductors':15,'signal_wire_conductors':6,'rail_wire_conductors':5,'AGND_wire_conductors':4,'active_header_pin_solder_joints':30,'NC_header_pin_solder_joints':6,'electrical_header_pin_solder_joints':36,'mechanical_MP_solder_joints':16,'total_header_solder_joints':52,'BM07B-GHS-TBT(LF)(SN)':2,'BM04B-GHS-TBT(LF)(SN)':4,'BM03B-GHS-TBT(LF)(SN)':2,'GHR-07V-S':2,'GHR-04V-S':4,'GHR-03V-S':2,'SSHL-002T-P0.2':30,'source_packages_unchanged':56,'added_transport_kept_separate':True,'wire_ordercode':None,'strain_relief_locations_proposed':8,'strain_relief_hardware_ordercode':None},
  'source_bypass_associations':bypass,'whole_instrument_host_overlay':original['whole_instrument_host_overlay'],'minimum_service_proxy_slack_mm':min(w['minimum_service_proxy_slack_mm']for w in allw),'all_wire_slack_screens_pass':all(w['slack_screen_pass']for w in allw),'fixed_panel_centres':438,'functions':33,'local_circuit_topology_unchanged':True,
  'return_constraints':'FourAGNDconductors deliberatelydistinct. Theirglobalnetjoin isnot equal-current-sharing or sourceerror cancellation credit. Two matedGH contacts perbranch have60/100mohm sourceinitial/aftertest maxima excludingwire/crimps/copper, so inherited0.5mohm goal cannotbe claimed achieved.',
  'unknowns':['upstreamPOWERsourceconnector/inlet/current/return realization','routedPCBtrace/contact/wireparasitics','exactwire/crimp/process/strainrelief qualification','actualreleaseforce/stroke/bend/toolaccess','installedglobalreturnerror andanalogstability'], 'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','accepted':False}

def build():
 inputpath=OUT/'interface-input.json';mechpath=OUT/'mechanical-report.json';spec=json.loads(inputpath.read_text());mechanical=json.loads(mechpath.read_text());r=build_from(spec,mechanical)
 files=[inputpath,mechpath,Path(__file__),Path(__file__).with_name('test_stage7_interfaces.py'),Path(a.__file__),Path(a.c.__file__),ROOT/'scripts/architecture278/populated_mechanics.py',a.OUT/'stage6/hosting-report.json',ROOT/'design/connectors/jst-gh.json',ROOT/'design/connectors/sources/jst-gh.pdf',a.OUT/'front-evidence.json',OUT/'scope.json']+[ROOT/f for f in FOOTPRINTS.values()]
 r['source_sha256']=a.binding(files);return r

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';out=OUT/'interfaces-report.json'
 if args.check:need(out.read_text()==data,'stale Stage7 interfaces report')
 else:out.write_text(data)
 print('X1 4harnesses15conductors8headers8housings30crimps52solderjoints; hardwarequalification OPEN')
