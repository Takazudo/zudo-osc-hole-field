"""Scalar candidate capacitor packages; no CAD/native or support changes."""
import argparse,copy,hashlib,json,math
from pathlib import Path
import assembly as a
ROOT=a.ROOT;OUT=a.OUT/'stage13'
FAMILY_SHA='c3c5bb70009b606c87b40156259670ca9c8452f172b73faa9e2dbf2fcee3522d'
GEOMETRY={'T491C475K050AT':([6.3,3.5,2.8],[7.82,4],2.47,2.23),'T491D226K035AT':([7.6,4.6,3.1],[9.12,5.10],3.12,2.43)}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def overlap(x,y):return x[0]<y[2]and y[0]<x[2]and x[1]<y[3]and y[1]<x[3]
def gap(x,y):return math.hypot(max(x[0]-y[2],y[0]-x[2],0),max(x[1]-y[3],y[1]-x[3],0))
def around(xy,r):return[xy[0]-r,xy[1]-r,xy[0]+r,xy[1]+r]
def analyze(spec,prior):
 need(set(spec['overlays'])=={'C7101','C7102'},'only two complete capacitor overlays')
 places=copy.deepcopy(prior['placements']);need(len(places)==90,'90 complete source packages')
 obstacles=[]
 for name,h in prior['headers'].items():
  if h['board']=='A01-core':obstacles.append({'id':name,'box':h['box_mm']})
 for m in prior['mounts']:
  if m['board']=='A01-core':obstacles.append({'id':m['id'],'box':around(m['xy_mm'],max(3,m['washer_diameter_mm']/2))})
 for d in prior['DIN_contacts']+prior['DIN_flange_holes']:obstacles.append({'id':d['id'],'box':around(d['point_mm'],d['radius_mm'])})
 for name,d in prior['din_connectors'].items():
  if name=='rear':obstacles.append({'id':'rear DIN whole projection','box':d['box_mm']})
 for xy in ([270,178],[270,278]):obstacles.append({'id':'retained core handle','box':around(xy,3)})
 rows={}
 for ref,q in spec['overlays'].items():
  old=places[ref];need(q['pins']==old['pins']and q['units']==old['units'],'source pin/unit conservation')
  need(q['board']=='A01-core'and q['side']=='rear'and q['pad_depth_mm']==70.8,'retained core pad face')
  need(q['quarter_turn']in(0,1,2,3),'quarter turn')
  geom=q['geometry'];need(q['candidate_MPN']in GEOMETRY,'unreviewed exact package')
  body,court,centre,width=GEOMETRY[q['candidate_MPN']]
  need(geom['body_max_mm']==body and geom['courtyard_mm']==[-court[0]/2,-court[1]/2,court[0]/2,court[1]/2]and geom['pads_mm']=={'1':[-centre,0],'2':[centre,0]}and geom['pad_sizes_mm']=={'1':[2.37,width],'2':[2.37,width]},'exact manufacturer densityB geometry')
  need(geom['evidence_sha256']==FAMILY_SHA and geom['evidence_url']=='https://content.kemet.com/datasheets/KEM_T2005_T491.pdf','retained manufacturer drawing')
  need(set(geom['pads_mm'])=={'1','2'}and set(geom['pad_sizes_mm'])=={'1','2'},'two pad geometry')
  need(all(v>0 and math.isfinite(v)for v in geom['body_max_mm']),'finite maximum body')
  need(geom['body_max_mm'][2]<=5,'retained package depth bound exceeded')
  need(len(geom['evidence_sha256'])==64 and bool(geom['evidence_url']),'exact manufacturer geometry evidence')
  need(geom['land_status']in('manufacturer recommended','candidate engineering proposal'),'land authority explicit')
  shape={'box':geom['courtyard_mm'],'pads':{k:[v]for k,v in geom['pads_mm'].items()},'holes':[]}
  shaped=a.face_shape(shape,'rear');origin=q['origin_mm'];turn=q['quarter_turn'];box=a.box_transform(shaped['box'],origin,turn)
  w,l,h=geom['body_max_mm'];need(a.inside([-w/2,-l/2,w/2,l/2],geom['courtyard_mm']),'body not inside courtyard')
  for pin,p in geom['pads_mm'].items():
   pw,ph=geom['pad_sizes_mm'][pin];need(pw>0 and ph>0,'positive land size');need(a.inside([p[0]-pw/2,p[1]-ph/2,p[0]+pw/2,p[1]+ph/2],geom['courtyard_mm']),'land outside courtyard')
  need(a.inside(box,prior['boards']['A01-core']['outline_mm'],spec['board_edge_clearance_mm']),'board edge clearance')
  pads={k:[a.transform(v,origin,turn)for v in vs]for k,vs in shaped['pads'].items()}
  updated=copy.deepcopy(old);updated.update(origin_mm=origin,quarter_turn=turn,box_mm=box,pads_mm=pads,pads_xyz_mm={k:[v+[70.8]for v in vs]for k,vs in pads.items()},candidate_MPN=q['candidate_MPN'],candidate_geometry_source=geom,source=old['source'],captured_source_footprint_only=old['source'])
  places[ref]=updated;rows[ref]={'candidate_MPN':q['candidate_MPN'],'body_height_mm':h,'maximum_rear_extent_mm':70.8+h,'land_status':geom['land_status'],'geometry_source':geom['evidence_url']}
 for ref in rows:
  p=places[ref];neighbors=[{'id':r,'box':v['box_mm']}for r,v in places.items()if r!=ref and v['board']=='A01-core']+obstacles
  distances=[{'id':n['id'],'clearance_mm':gap(p['box_mm'],n['box'])}for n in neighbors]
  need(all(not overlap(p['box_mm'],n['box'])for n in neighbors),'whole package/land envelope collision '+ref)
  need(min(n['clearance_mm']for n in distances)>=spec['courtyard_gap_mm'],'neighbor courtyard clearance '+ref)
  rows[ref]['neighbor_screens']=distances
 for ref,p in prior['placements'].items():
  if ref not in rows:need(places[ref]==p,'unrelated package changed')
 paths=[]
 for ref in ('C7101','C7102','C7107'):
  for pin,net in places[ref]['pins'].items():
   targets=[(k,vs[0])for k,vs in places['U7101']['pads_xyz_mm'].items()if places['U7101']['pins'][k]==net]
   need(bool(targets),'matching REF5050 actual pin')
   start=places[ref]['pads_xyz_mm'][pin][0];target,finish=min(targets,key=lambda x:math.dist(start,x[1]));before=prior['placements'][ref]['pads_xyz_mm'][pin][0]
   paths.append({'from':ref+':'+pin,'to':'U7101:'+target,'net':net,'from_xyz_mm':start,'to_xyz_mm':finish,'before_straight_floor_mm':math.dist(before,finish),'after_straight_floor_mm':math.dist(start,finish),'after_rectilinear_floor_mm':sum(abs(x-y)for x,y in zip(start,finish)),'status':'Actual pad separation only; route/return inductance/loop area NOT QUALIFIED. No trace implied through component body.'})
 return {'status':'SCALAR CAPACITOR PACKAGE CANDIDATE; NO PHYSICAL ACCEPTANCE','placements':places,'overlays':rows,'local_reference_pad_paths':paths,'conservation':{'packages':90,'unchanged_packages':88,'C7107_unchanged':places['C7107']==prior['placements']['C7107'],'pins_units_nets_preserved':True},'obstacles':obstacles,'unknowns':['Exact copper/assembly/solder-mask courtyard validation','All other-function populated Z solids remain unresolved; no newly free space claimed','Local pad distances do not qualify REF5050 effectiveC/ESR/stability or loop inductance','Support/strap/cassette and entire preceding geometry frozen'],'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def build():
 paths=[OUT/'package-input.json',a.OUT/'stage10/mechanical-report.json',OUT/'capacitor-input.json',a.OUT/'stage10/inventory-report.json',a.OUT/'stage10/interfaces-report.json',a.OUT/'stage4/occupied-report.json',a.OUT/'stage11/support-report.json']
 spec,prior,caps,inv,graph,occupied,support=[json.loads(p.read_text())for p in paths]
 need(len(inv['packages'])==90 and sum(len(p['units'])for p in inv['packages'].values())==118,'source90packages118units')
 for ref,p in prior['placements'].items():need(p['pins']==inv['packages'][ref]['pins']and p['units']==inv['packages'][ref]['units'],'source inventory pin/unit '+ref)
 for ref,q in spec['overlays'].items():
  c=caps['parts'][ref];g=q['geometry'];need(q['candidate_MPN']==c['MPN']and g['body_max_mm']==c['body_max_mm']and q['pins']==c['pins']and q['units']==c['units'],'exact selected capacitor binding')
  need(g['evidence_sha256']==caps['evidence']['family']['sha256']and g['evidence_url']==caps['evidence']['family']['url'],'selected family geometry source')
  need(g['pad_sizes_mm']['1']==c['land_pad_size_xy_mm']and g['pad_sizes_mm']['2']==c['land_pad_size_xy_mm'],'selected land dimensions')
  need(all(math.isclose(u,v,abs_tol=1e-12)for u,v in zip(g['pads_mm']['1'],c['pin1_positive_local_xy_mm']))and all(math.isclose(u,v,abs_tol=1e-12)for u,v in zip(g['pads_mm']['2'],c['pin2_negative_local_xy_mm'])),'positive stripe registration')
  need([g['courtyard_mm'][2]-g['courtyard_mm'][0],g['courtyard_mm'][3]-g['courtyard_mm'][1]]==c['courtyard_size_xy_mm'],'selected courtyard dimensions')
 r=analyze(spec,prior);deltas=[]
 for ref in spec['overlays']:
  for pin,vs in r['placements'][ref]['pads_xyz_mm'].items():
   node=ref+':'+pin;before=graph['nodes'][node]['pad_xyz_mm'];after=vs[0]
   deltas.append({'node':node,'net':graph['nodes'][node]['net'],'before_xyz_mm':before,'after_xyz_mm':after,'delta_xyz_mm':[y-x for x,y in zip(before,after)],'invalidated_incident_graph_edges':[i for i,e in enumerate(graph['edges'])if node in(e['from'],e['to'])]})
 r['endpoint_delta_and_invalidation']={'changed_source_pads':deltas,'scope':'Prior Stage10-12 graph lengths/endpoints are historical baseline, NOT current overlay path metrics. All incident edges and any walk using them require regeneration before adopting overlay. Local six pad distances do not update full signal/power/return budgets.','current_overlay_complete_path_metrics':None}
 r['other_function_projection_reservations']=[{'candidate':ref,'foreign_ref':p['ref'],'function':p['function_or_service'],'status':'HistoricalXYprojection; newZ/solid UNKNOWN, remains reserved'}for ref in spec['overlays']for p in occupied['rows']if p['function_or_service']!='A01'and overlap(r['placements'][ref]['box_mm'],p['historical_placement']['courtyard_mm'])]
 frozen=[]
 for name,frame in support['refined_frames'].items():
  for kind in ('rails_boxes_mm','crossmembers_boxes_mm'):
   for i,b in enumerate(frame[kind]):frozen.append({'id':name+':'+kind+str(i),'box_mm':b,'z_mm':frame['z_mm'],'option':'Stage11 support proposal, unqualified'})
 for st in support['low_R_feed_option']['straps']:frozen.append({'id':'strap:'+st['net'],'box_mm':st['lane_envelope_mm'],'z_mm':st['lane_z_mm'],'option':'UNSELECTED Stage11 lowR comparison'})
 v=support['low_R_feed_option']['cassette_removal_volume_mm'];frozen.append({'id':'cassette service sweep','box_mm':[v[0],v[1],v[3],v[4]],'z_mm':[v[2],v[5]],'option':'UNSELECTED Stage11 lowR comparison'})
 hits=[]
 for ref,q in r['overlays'].items():
  p=r['placements'][ref];z=[70.8,q['maximum_rear_extent_mm']]
  for f in frozen:
   if overlap(p['box_mm'],f['box_mm'])and z[0]<f['z_mm'][1]and f['z_mm'][0]<z[1]:hits.append({'candidate':ref,'solid':f['id']})
 need(not hits,'frozen Stage11 modeled envelope intersection')
 r['frozen_stage11_option_screen']={'solids':frozen,'intersections':hits,'status':'Read-only comparison, no option selection or geometry elaboration','unknown':'Exact terminal blocks/fastener/contact/support solids remain unmodeled as inStage11; no comprehensive free-volume or service acceptance.'}
 r['conservation']['source_units']=118
 paths += [Path(__file__),Path(__file__).with_name('test_stage13_packages.py'),Path(a.__file__),Path(a.c.__file__)];r['source_sha256']=a.binding(paths);return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();text=json.dumps(build(),sort_keys=True,indent=2)+'\n';dest=OUT/'package-report.json'
 if args.check:need(dest.read_text()==text,'stale package report')
 else:dest.write_text(text)
 print('Stage13 scalar package checks PASS; physical acceptance OPEN')
if __name__=='__main__':main()
