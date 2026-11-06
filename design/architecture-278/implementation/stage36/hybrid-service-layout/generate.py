"""Source-only bounded IDC map and revised support proposal. Never native CAD."""
from pathlib import Path
import json,hashlib,sys,math,copy
H=Path(__file__).resolve().parent;R=H.parents[4]
sys.path.insert(0,str(R/'scripts/architecture278/implementation'))
import assembly
from stage36_interface_cassette import svg_start,text,rect
P=H.parent/'populated-a01-hybrid/layout.json';M=R/'design/architecture-278/implementation/stage10/mechanical-report.json';T=R/'design/architecture-278/implementation/stage17/generated/transport-component-rows.json';L=R/'design/grid/placements.lock.json'
def ov(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def hit(a,b):return ov(a['xy'],b['xy']) and a['z'][0]<b['z'][1] and a['z'][1]>b['z'][0]
def grow(b,d):return[b[0]-d,b[1]-d,b[2]+d,b[3]+d]
def subtract(b,c):
 if not hit(b,c):return [b]
 v=[b['xy'][0],b['xy'][1],b['z'][0],b['xy'][2],b['xy'][3],b['z'][1]]
 w=[c['xy'][0],c['xy'][1],c['z'][0],c['xy'][2],c['xy'][3],c['z'][1]]
 lo=[max(v[i],w[i]) for i in range(3)];hi=[min(v[i+3],w[i+3]) for i in range(3)]
 parts=[];core=v[:]
 for i in range(3):
  if core[i]<lo[i]:q=core[:];q[i+3]=lo[i];parts.append(q);core[i]=lo[i]
  if core[i+3]>hi[i]:q=core[:];q[i]=hi[i];parts.append(q);core[i+3]=hi[i]
 return [dict(b,xy=[q[0],q[1],q[3],q[4]],z=[q[2],q[5]]) for q in parts]
def build():
 p=json.loads(P.read_text());m=json.loads(M.read_text());t=json.loads(T.read_text());locked=json.loads(L.read_text())
 a={'status':'BOUNDED_SOURCE_PROPOSAL_NOT_INTEGRATED_FIT','baseline':'51aa218dc5eb17c22fd13531e04c115da87c8520','source_sha256':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [P,M,T,L]},'adopted':False,'support_joint_model':'Control carrier members form a single joined-frame union; not stacked overlapping stock. Middle rail seats subtract explicit pockets before crossbar insertion.','pin_maps':{},'connector_coordinates':[],'supports':[],'removed_supports':[],'known_obstacle_hits':[],'unknown_obstacles':[]}
 for name,n,ref,end,turn in [('C-SIG',10,'J17901','J17902',0),('J-PWR',8,'J17903','J17904',0),('J-SIG',14,'J17905','J17906',90)]:
  # Stage17 pin record is the compatibility authority, not handwritten duplicate nets.
  nets=t[ref]['pins'];other=t[end]['pins']
  if nets!=other:raise ValueError('old end maps differ')
  pins={str(k):nets.get(str(k)) for k in range(1,n+1)}
  a['pin_maps'][name]={'refs':[ref,end],'pins':pins,'header':f'612{n:03d}21621','socket':f'612{n:03d}23021','legacy_active_pins':{k:v for k,v in nets.items() if k.isdigit()},'extra_pins':'NC_NO_COPPER_NO_PARALLEL_CREDIT','ribbon':'equal-number continuity; stripe conductor1; no twists inferred from stripe'}
  for rr in [ref,end]:
   c=next(c for c in p['connectors'] if c['ref']==rr);theta=math.radians(turn if rr==ref else 0);cx,cy=c['centre_mm'];rows=[]
   for k in range(1,n+1):
    # Header drawing: key at negativeY; pin1 left on negativeY row.
    x=((k-1)//2-(n/2-1)/2)*2.54;y=-1.27 if k%2 else 1.27
    rows.append({'pin':k,'net':pins[str(k)],'header_face_xy':[round(x,5),y],'socket_face_xy':[round(x,5),-y],'global_xy':[round(cx+x*math.cos(theta)-y*math.sin(theta),5),round(cy+x*math.sin(theta)+y*math.cos(theta),5)]})
   a['connector_coordinates'].append({'ref':rr,'rotation_deg':turn if rr==ref else 0,'centre_mm':[cx,cy],'pins':rows})
 def add(name,xy,z,role):a['supports'].append({'id':name,'xy':xy,'z':z,'role':role})
 # Retain jack/middle frames. Remove entire oldrear frame; replace control lower elements.
 for name in ['jack','middle']:
  f=m['carrier_frames'][name]
  for k in ['rails_boxes_mm','crossmembers_boxes_mm']:
   for i,b in enumerate(f[k]):add(f'{name}-{k}-{i}',b,f['z_mm'],'retained-source-carrier')
  if 'mount_tabs' in f:
   for i,b in enumerate(f['mount_tabs']['boxes_mm']):add(f'{name}-tab-{i}',b,f['mount_tabs']['z_mm'],'retained-source-carrier')
 a['removed_supports']=['rear:all rails/crossmembers/bosses','control:old lower crossmembers and anchor at315,310','control:side-rail portions y289..307','control:old mount spacer/fastener arrangements']
 for x0,x1 in [(208,209.5),(227.5,229)]:add('control-upper-'+str(x0),[x0,264,x1,289],[18,20],'retained-upper-rail-shortened')
 for side,lo,hi,bridge in [('left',203,206,[203,287,209.5,289]),('right',231,234,[227.5,287,234,289])]:
  add('control-'+side+'-offset',bridge,[18,20],'new-stock-bar-joint')
  add('control-'+side+'-lower',[lo,287,hi,320],[18,20],'new-stock-bar')
 add('control-mount-bridge',[203,306,234,310],[18,20],'new-bar-with-through-fastener-holes')
 add('control-bottom-crossmember',[203,314,318,320],[18,20],'new-stock-bar-to-relocated-cleat')
 for y in [180,274]:add('middle-load-crossbar-'+str(y),[242,y-4,314,y+4],[44.4,48.4],'new-ordinary-8x4-bar-drilled-at254-and300')
 a['middle_rail_pockets']=[{'xy':[242,y-4,314,y+4],'z':[44.4,46],'operation':'subtract only from retained middle rails at crossbar seats; new machining proposal'} for y in [180,274]]
 a['effective_support_solids']=[]
 for s in a['supports']:
  pieces=[s]
  if s['id'].startswith('middle-rails'):
   for cut in a['middle_rail_pockets']:pieces=[q for p0 in pieces for q in subtract(p0,cut)]
  a['effective_support_solids']+=pieces
 a['new_crossbar_retained_support_hits']=[[x['id'],y['id']] for x in a['effective_support_solids'] if x['id'].startswith('middle-load') for y in a['effective_support_solids'] if y['role']=='retained-source-carrier' and hit(x,y)]
 a['control_fasteners']=[{'xy':[x,308],'post_z':[11.6,18],'post_length':6.4,'bridge_hole_diameter':3.4,'tool_diameter':6,'tool_z':[20,105],'front_nut_z_reservation':[6,10],'status':'M2.5 through-fastener proposal; select exact screw/post before adoption'} for x in [213,224]]
 a['new_anchor']={'xy':[315,317],'tool_diameter':8,'enclosure_y_minimum_proposal':322,'z':[18,20]}
 a['core_supports']=p['supports'];a['core_lower_screws']={'size_proposal':'M3x10','bar_mm':4,'pcb_mm':1.6,'thread_engagement_nominal_mm':4.4,'spacer_thread_depth_mm':7,'assembly':'install frombelow before seating middleframe; no installed tool-access claim'}
 # Known finite obstacles include board solids and connector body plus3.15mm tail allowance.
 obstacles=[]
 for name,b in p['boards'].items():
  if name=='A01-control':
   obstacles +=[{'id':name+'upper','xy':[210,264,227,290],'z':b['z_mm']},{'id':name+'tab','xy':[206.5,290,230.5,312],'z':b['z_mm']}]
  else:obstacles.append({'id':name,'xy':b['outline_mm'],'z':b['z_mm']})
 for c in p['connectors']:
  z=list(c['z_mm']);z[0]-=3.15
  if c['board']=='A01-core':z[1]+=2.79
  obstacles.append({'id':c['ref'],'xy':grow(c['box_mm'],1),'z':z})
 obstacles.append({'id':'fixed_LED_substrate','xy':m['fixed_LED_substrate']['outline_mm'],'z':m['fixed_LED_substrate']['z_mm']})
 for q in m['carrier_frames']['control']['body_cradles']:obstacles.append({'id':q['ref']+'body','xy':q['body_box_mm'],'z':q['body_z_mm']})
 a['known_obstacles']=obstacles
 for s in a['effective_support_solids']:
  for b in obstacles:
   if hit(s,b):a['known_obstacle_hits'].append([s['id'],b['id']])
 # New bar/spacer holes must avoid every same-board candidate courtyard, even missing heights.
 a['new_fastener_package_hits']=[]
 for s in p['supports']:
  x,y=s['xy_mm']
  for ref,v in p['packages'].items():
   if v['board'] in ['A01-core','A01-middle'] and ov([x-4,y-4,x+4,y+4],v['box_mm']):a['new_fastener_package_hits'].append([s['xy_mm'],ref])
 # Actual part geometry can supply relative bounds; installation datum is not fabricated.
 hw=assembly.locked_hardware(locked['placements']);byref={v['ref']:v for v in hw};refs=sorted({q['ref'] for q in m['foreign_hardware_projections']});pots=[]
 for ref in refs:
  q=byref[ref]
  entry={'ref':ref,'xy':q['box_mm'],'source':q['source'],'absolute_z':None,'status':'OCCUPIED_UNKNOWN_INSTALLATION_DATUM'}
  if 'PTV09A' in q['source']:
   entry.update(relative_body_z_from_rear_seating_plane=[-6.8,0],relative_rear_shaft_z=[0,3.8],conditional_existing_pcb_plane=q['conditional_pcb_depth_mm'],limitation='body andshaft only; terminal/harness depth andactualinstalledplane remainunknown');pots.append(ref)
  a['unknown_obstacles'].append(entry)
 a['unknown_support_projection_hits']=[{'support':s['id'],'ref':q['ref']} for s in a['supports'] if s['role']!='retained-source-carrier' for q in a['unknown_obstacles'] if ov(s['xy'],q['xy'])]
 a['neighbor_recovery']={'unique_refs':len(refs),'repeated_projection_rows':len(m['foreign_hardware_projections']),'pots_with_relative_source_depth':pots,'qualified_free_regions':[],'smallest_missing_datum':'actual rear seating plane Z of neighboring PTV09 groups; forotherfamilies exact installed datum plus terminal/harness furthestZ'}
 a['missing_mated_datum']='Closed, fullylatched strainrelief highestZ above board and cableexit plane for each612008/010/01423021 with selectedribbon; sourceSTEP isopenstate.'
 return a

def drawing(a):
 s=svg_start('A01 hybrid support revision','Source proposal. Known solid screens only; unknown neighbors remain occupied.')
 s +=[text(25,35,'A01 / IDC maps and revised ordinary supports',25),text(25,65,'24 mm stack retained. No fixed controls moved. This is a source candidate, not complete fit approval.',16)]
 for name,origin,bounds,scale in [('Control lower carrier',(35,120),[199,260,322,322],3.5),('Middle load path',(600,120),[232,138,320,296],3)]:
  ox,oy=origin;xx=lambda x:ox+(x-bounds[0])*scale;yy=lambda y:oy+(y-bounds[1])*scale
  s.append(text(ox,105,name,20))
  for ob in a['known_obstacles']:
   if (name.startswith('Control') and ob['id'].startswith('A01-control'))or(name.startswith('Middle') and ob['id']=='A01-middle'):
    q=ob['xy'];s.append(rect(xx(q[0]),yy(q[1]),(q[2]-q[0])*scale,(q[3]-q[1])*scale,'#36705c','#e2eee8'))
  for q in a['supports']:
   if (name.startswith('Control') and q['id'].startswith('control'))or(name.startswith('Middle') and q['id'].startswith('middle')):
    b=q['xy'];s.append(rect(xx(b[0]),yy(b[1]),(b[2]-b[0])*scale,(b[3]-b[1])*scale,'#94603a','#dfc5a7'))
  for c in a['connector_coordinates']:
   if (name.startswith('Control') and c['ref']=='J17901')or(name.startswith('Middle') and c['ref'] in ['J17902','J17904','J17906']):
    x,y=c['centre_mm'];s.append(text(xx(x)-20,yy(y),c['ref'],12))
  pts=[q['xy'] for q in a['control_fasteners']]+[a['new_anchor']['xy']] if name.startswith('Control') else [q['xy_mm'] for q in a['core_supports']]
  for x,y in pts:s.append(f'<circle cx="{xx(x)}" cy="{yy(y)}" r="{3*scale}" fill="none" stroke="#973f36"/>')
 s +=[text(25,380,'Control: new lower rails x203–206 /231–234; bridge y306–310;',16),text(25,405,'crossmember y314–320; new cleat(315,317). Z18–20.',16),text(25,435,'Fasteners(213,308)/(224,308) through bridge; posts6.4.',16),text(25,465,'2 mm nominal tab-to-bottom-crossmember XY gap.',16),text(25,505,'Middle: two8×4 mm stock crossbars y176–184 /270–278,',16),text(25,530,'x242–314,z44.4–48.4;1.6-deep seats cut into old rails.',16),text(25,560,'Four24 mm M3 spacers at(254/300,180/274).',16),text(25,635,'Header mating view: key −Y, odd pins on −Y row, pin1 at left. Socket face: reverse Y, preserve X.',16),text(25,665,'Keep original1–6 C-SIG,1–4 J-PWR,1–7 J-SIG; extra pins NC. J-PWR includes+5; K-PWR does not.',16),text(25,705,'Closed strain-relief/cable-exit height and neighbor seating datums remain required; do not infer free space.',17,'#a65e42'),'</g></svg>']
 return '\n'.join(s)+'\n'
if __name__=='__main__':
 a=build()
 for n,s in {'proposal.json':json.dumps(a,indent=2,sort_keys=True)+'\n','support-layout.svg':drawing(a)}.items():
  if '--check' in sys.argv:
   if (H/n).read_text()!=s:raise SystemExit('STALE '+n)
  else:(H/n).write_text(s)
 print('Known obstacle hits:',a['known_obstacle_hits']);print('Fastener package hits:',a['new_fastener_package_hits'])
