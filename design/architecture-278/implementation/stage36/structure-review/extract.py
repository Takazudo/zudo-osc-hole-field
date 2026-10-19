from pathlib import Path
import json,hashlib,math,sys
O=Path(__file__).resolve().parent;R=O.parents[4]
paths=['design/grid/placements.lock.json','design/architecture-278/implementation/stage10/mechanical-report.json','design/architecture-278/implementation/stage33/model.json','design/architecture-278/revision-mechanical-report.json','design/architecture-278/revision-mechanical-input.json']
lock,m,r,old,oi=[json.loads((R/p).read_text()) for p in paths]
boxes=[]
def box(name,bb,z,layer,status):boxes.append(dict(name=name,xy=bb,z=z,layer=layer,status=status))
for name,v in m['boards'].items():box(name,v['outline_mm'],v['z_mm'],'middle' if 'middle' in name else 'rear' if 'core' in name else 'front','A01 source-study outer envelope; holes/notches omitted; unadopted')
v=m['fixed_LED_substrate'];box('A01 LED substrate',v['outline_mm'],v['z_mm'],'front','A01 source-study outer envelope; holes/notches omitted; unadopted')
for name,v in m['carrier_frames'].items():
 for key in ['rails_boxes_mm','crossmembers_boxes_mm']:
  for i,bb in enumerate(v[key]):box(name+' '+key.split('_')[0]+' '+str(i),bb,v.get('bottom_crossmember_z_mm',v['z_mm']) if key=='crossmembers_boxes_mm' else v['z_mm'],'carriers','Proposed carrier envelope; support/registration unqualified')
moves={x['ref']:x for x in r['R33']['header_moves']}
for name,v in m['headers'].items():
 bb=v['box_mm'];z=v['pad_depth_mm'];direction=1 if v['side']=='rear' else -1
 if name in moves:bb=moves[name]['box_mm'];z=moves[name]['face_z_mm'];direction=1
 box(name,bb,sorted([z,z+direction*7.3]),'connectors','Mated GH envelope (7.3 mm study allowance), not exact body; R33 rear-face move is design-only')
box('A01 DIN mating-stack envelope',[293.5,180.5,304.5,275.5],[50,69.2],'connectors','Union XY / board spacing only, not an exact DIN solid or contact map')
for v in old['cards']:box(v['instance']+' earlier rear-card allocation',v['box_mm'],[oi['core_depth_mm'],oi['core_depth_mm']+oi['pcb_thickness_mm']],'earlier','Earlier revision-2 proposal; NOT current whole-instrument fit; no populated package claim')
routes=[]
for name,v in r['R33']['routes'].items():
 a,va,vb,b=v['vertices_mm'];length=math.dist(va[:2],vb[:2]);u=[(vb[i]-va[i])/length for i in (0,1)];rad=12;z=va[2];points=[a,[a[0],a[1],z-rad]]
 c=[a[0]+rad*u[0],a[1]+rad*u[1],z-rad]
 for i in range(1,33):
  t=i*math.pi/64;points.append([c[0]-rad*u[0]*math.cos(t),c[1]-rad*u[1]*math.cos(t),c[2]+rad*math.sin(t)])
 c=[b[0]-rad*u[0],b[1]-rad*u[1],z-rad];points.append([c[0],c[1],z])
 for i in range(1,33):
  t=i*math.pi/64;points.append([c[0]+rad*u[0]*math.sin(t),c[1]+rad*u[1]*math.sin(t),c[2]+rad*math.cos(t)])
 points.append(b);routes.append({'name':name,'points':points,'design_length_mm':r['R33']['design_lengths'][name]['design_length_proposal_mm'],'status':'R33 installed ideal centreline, R12; retained study basis, wire/retention/service UNKNOWN. Screen line width is not cable OD.'})
D={'revision':'02e83bb6955d97958248946bd11d2e3f14014ad3','frame':'panel front top-left, x right, y down, z rear; rendered with y inverted','panel_mm':[318,298],'cover_depth_mm':105,'enclosure_candidate_mm':m['minimum_enclosure_internal_candidate_mm'],'placements':[{k:q[k] for k in ['uid','ref','kind','x_mm','y_mm']} for q in lock['placements']],'boxes':boxes,'routes':routes,'sources':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},'omissions':['No complete A02-A06/E2-E5/other front, middle or rear board outlines','No accepted retention, C36 cassette, RG34 guide or shorter-cable solution','C-SIG/K-PWR and whole-instrument cable routes omitted; not established by R33','No native solids, copper, collision verification or manufacturing acceptance','Empty-looking volumes are UNKNOWN, not free space','No protection/inlet implementation or ordering approval']}
body=json.dumps(D,indent=2)+'\n'
if '--check' in sys.argv:
 if (O/'view-data.json').read_text()!=body:raise SystemExit('FAIL stale view-data.json')
 print('PASS deterministic data and source hashes')
else:
 (O/'view-data.json').write_text(body);print(len(boxes),'boxes',len(D['placements']),'fixed positions',len(routes),'routes')
