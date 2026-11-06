"""P37 populated source candidate; no canonical CAD or free-space inference."""
from pathlib import Path
import json,hashlib,sys,copy,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'scripts/architecture278/implementation'))
from stage36_interface_cassette import svg_start,text,rect
BASE='28b301520861cfe2e925fffff5f849d5681250fe'
FILES={k:'design/architecture-278/implementation/'+v for k,v in {
 'mechanical':'stage10/mechanical-report.json','packages':'stage15/package-report.json',
 'transport':'stage17/generated/transport-component-rows.json','inventory':'stage26/candidate-inventory.json',
 'maps':'stage36/ordinary-header-comparison/analysis.json','neighbors':'stage36/whole-layout-review/view-data.json'}.items()}
def read(p):return json.loads((ROOT/p).read_text())
def ov(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def box(c,w,h):return [c[0]-w/2,c[1]-h/2,c[0]+w/2,c[1]+h/2]
def grow(a,d):return[a[0]-d,a[1]-d,a[2]+d,a[3]+d]
def build():
 m=read(FILES['mechanical']);p=copy.deepcopy(read(FILES['packages'])['placements']);t=read(FILES['transport']);inv=read(FILES['inventory'])
 # Deliberately use the unapplied latest118-reference candidate, not mixed canonical90+candidate extras.
 if set(p)|set(t)!=set(inv['packages']) or set(p)&set(t):raise ValueError('118-reference reconciliation failed')
 boards=copy.deepcopy(m['boards']);boards['A01-core']['z_mm']=[74,75.6]
 boards['A01-control']['outline_proposal_polygon_mm']=[[210,264],[227,264],[227,290],[230.5,290],[230.5,312],[206.5,312],[206.5,290],[210,290]]
 boards['A01-control']['mounts_mm']=[[213,308],[224,308]]
 for v in p.values():
  if v['board']=='A01-core':
   v['conditional_pad_depth_mm']=75.6
   for points in v['pads_xyz_mm'].values():
    for q in points:q[2]+=4.8
 connectors=[]
 def add(ref,board,xy,w,h,count,role,mpn,z):
  connectors.append(dict(ref=ref,board=board,centre_mm=xy,box_mm=box(xy,w,h),circuits=count,role=role,mpn=mpn,z_mm=z,z_status='IDC_OPEN_STATE_PROVISIONAL_NOT_MATED_HEIGHT' if '6120' in mpn else 'CONDITIONAL_DRAWING_SCREEN'))
 add('J17905','A01-jack',[208,108],9.5,25.64,14,'J-SIG:local','61201421621',[36.6,54.9])
 add('J17903','A01-jack',[212,170],18.02,9.5,8,'J-PWR:local','61200821621',[36.6,54.9])
 add('J17906','A01-middle',[258,154],25.64,9.5,14,'J-SIG:middle','61201421621',[50,68.3])
 add('J17904','A01-middle',[292,154],18.02,9.5,8,'J-PWR:middle','61200821621',[50,68.3])
 add('J17901','A01-control',[218.5,297.5],20.56,9.5,10,'C-SIG:local','61201021621',[11.6,29.9])
 add('J17902','A01-middle',[274,286],20.56,9.5,10,'C-SIG:middle','61201021621',[50,68.3])
 # Long axis along y; identical global contact XY on both mating boards.
 add('J17909','A01-middle',[295,220],5.5,21.2,16,'rear-signal:male','TSW-108-18-L-D',[50,70.83])
 add('J17910','A01-core',[295,220],5.5,21.2,16,'rear-signal:socket','SSW-108-01-L-D',[65.49,74])
 add('J17908','A01-middle',[295,250],5.5,11,8,'K-PWR:male','TSW-104-18-L-D',[50,70.83])
 add('J17907','A01-core',[295,250],5.5,11,8,'K-PWR:socket','SSW-104-01-L-D',[65.49,74])
 supports=[dict(xy_mm=[x,y],body_radius_screen_mm=3.18,tool_radius_mm=4,z_mm=[50,74],mpn='970240321',drill_proposal_mm=3.4) for x in [254,300] for y in [180,274]]
 screens=[]
 for c in connectors:
  hits=[r for r,v in p.items() if v['board']==c['board'] and ov(grow(c['box_mm'],1),v['box_mm'])]
  mounts=[v['id'] for v in m['mounts'] if v['board']==c['board'] and c['board']!='A01-control' and ov(c['box_mm'],box(v['xy_mm'],8,8))]
  tails=[v['id'] for v in m['terminal_lands'] if v['board']==c['board'] and ov(grow(c['box_mm'],1),box(v['xyz_mm'][:2],2.6,2.6))]
  screens.append(dict(ref=c['ref'],package_collisions_1mm=hits,old_mount_tool_intersections=mounts,terminal_land_intersections=tails))
 for i,s in enumerate(supports):
  hits=[r for r,v in p.items() if v['board'] in ['A01-middle','A01-core'] and ov(box(s['xy_mm'],8,8),v['box_mm'])]
  screens.append(dict(ref='spacer'+str(i+1),package_collisions_1mm=hits))
 maps=read(FILES['maps'])['maps'];binding=[]
 for name,n,xy,refs in [('rear_signal',16,[295,220],['J17909','J17910']),('K-PWR',8,[295,250],['J17908','J17907'])]:
  for num in range(1,n+1):
   # Global rear-facing view: odd row x293.73, even row296.27; column grows+y.
   gx=xy[0]+(-1.27 if num%2 else 1.27);gy=xy[1]+((num-1)//2-(n/2-1)/2)*2.54
   binding.append(dict(link=name,pin=num,net=maps[name]['pins'].get(str(num)),global_xy_mm=[gx,gy],male_ref=refs[0],socket_ref=refs[1],male_local_mm=[gx-xy[0],gy-xy[1]],socket_local_face_view_mm=[-(gx-xy[0]),gy-xy[1]]))
 corridors=[dict(id='J-SIG-route',xy_mm=[198,94,273,169],z_mm=[54.9,92],status='ROUTE_RESERVATION_NOT_FREE'),dict(id='J-PWR-local-rise',xy_mm=[202,164,222,176],z_mm=[54.9,92],status='ROUTE_RESERVATION_NOT_FREE'),dict(id='J-PWR-bridge',xy_mm=[207,141,303,165],z_mm=[68.3,92],status='ROUTE_RESERVATION_NOT_FREE'),dict(id='C-SIG-route',xy_mm=[206.5,281.25,286,313],z_mm=[29.9,92],status='ROUTE_RESERVATION_NOT_FREE')]
 # Record every conceptual other-function board projection touched; never certify it as absent.
 neighbor_boxes=[]
 def walk(v):
  if isinstance(v,dict):
   if v.get('block') not in [None,'A01'] and 'xy' in v and 'z' in v:neighbor_boxes.append(v)
   for w in v.values():walk(w)
  elif isinstance(v,list):
   for w in v:walk(w)
 walk(read(FILES['neighbors']))
 for c in corridors:
  c['neighbor_envelopes']=[v['name'] for v in neighbor_boxes if ov(c['xy_mm'],v['xy']) and c['z_mm'][0]<v['z'][1] and c['z_mm'][1]>v['z'][0]]
  c['known_core_projection_overlap']=ov(c['xy_mm'],boards['A01-core']['outline_mm'])
 a=dict(status='RECOMMENDED_P37_SOURCE_CANDIDATE_NOT_FIT_APPROVED',baseline=BASE,source_sha256={v:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in FILES.values()},population_refs=sorted(inv['packages']),package_count=len(p),transport_count=len(t),packages=p,boards=boards,connectors=connectors,supports=supports,screens=screens,direct_pin_binding=binding,corridors=corridors,retained_wire_lands=[r for r in t if r.startswith('TP')],foreign_hardware_unknown_z_count=len(m['foreign_hardware_projections']),options=[dict(gap=12,status='NOT_PREFERRED_SHORT_PIN_LOW_CLEARANCE'),dict(gap=24,status='RECOMMENDED_LONG_PIN',nominal_insertion=5.34,conditional_insertion_interval=[4.55,6.13]),dict(gap=25,status='FAIL_STATED_TOLERANCE_SCREEN',conditional_insertion_interval=[3.55,5.13])],service=dict(core_axial_clearance_proposal_mm=7,core_total_removal_mm=40,core_final_z_mm=[114,115.6],cover_inner_proposal_mm=110,neighbor_clearance_established=False),applied_to_canonical=False)
 return a

def drawing(a):
 s=svg_start('P37 populated A01 hybrid proposal','All dimensions mm. Colored package rectangles are source courtyard/pad envelopes, not qualified full solids. Unknown neighbors are not free.')
 s +=[text(25,35,'P37 / populated A01 hybrid — 24 mm ordinary spacer stack',25),text(25,64,'86 package candidates +10 connector positions; 22 retained wire lands/fixed LED substrate omitted from view',16),text(25,91,'Source courtyard views; fixed front controls unchanged. Dashed rings: Ø8 tool reservations, not proved access.',15)]
 for b,x0 in [('A01-jack',35),('A01-control',270),('A01-middle',480),('A01-core',840)]:
  bd=a['boards'][b];o=bd['outline_mm'];sc=2.2;xx=lambda x:x0+(x-o[0])*sc;yy=lambda y:155+(y-o[1])*sc
  s +=[text(x0,127,b,20),text(x0,146,'z '+str(bd['z_mm']),13),rect(xx(o[0]),yy(o[1]),(o[2]-o[0])*sc,(o[3]-o[1])*sc,'#376E61','#f0f5ef')]
  if 'outline_proposal_polygon_mm' in bd:s.append('<polygon points="'+' '.join(f'{xx(x)},{yy(y)}' for x,y in bd['outline_proposal_polygon_mm'])+'" fill="none" stroke="#a65e42" stroke-width="2"/>')
  for ref,p in a['packages'].items():
   if p['board']!=b:continue
   q=p['box_mm'];s.append(rect(xx(q[0]),yy(q[1]),(q[2]-q[0])*sc,(q[3]-q[1])*sc,'#82918c','#d2dcd6'));s.append(text(xx(q[0]),yy(q[1])-1,ref,7))
  for c in a['connectors']:
   if c['board']!=b:continue
   q=c['box_mm'];s+=[rect(xx(q[0]),yy(q[1]),(q[2]-q[0])*sc,(q[3]-q[1])*sc,'#965e2c','#f0d6ac'),text(xx(q[0]),yy(q[1])-3,c['ref'],10)]
  if b in ['A01-middle','A01-core']:
   for p in a['supports']:
    x,y=p['xy_mm'];s.append(f'<circle cx="{xx(x)}" cy="{yy(y)}" r="{4*sc}" fill="none" stroke="#9c4234" stroke-dasharray="3 2"/>')
  for x,y in bd['mounts_mm']:s.append(f'<circle cx="{xx(x)}" cy="{yy(y)}" r="{2.5*sc}" fill="none" stroke="#697e91"/>')
 s +=[text(25,525,'Direct headers: (295,220) signal16; (295,250) power8. Same global XY, opposite-face numbering mirrored.',16),text(25,553,'New M3 spacer sites: (254,180), (300,180), (254,274), (300,274). Old rear carrier removed in proposal.',16),text(25,581,'Core near face74; far face75.6. Exposed18.29 pins; socket8.51; conditional insertion4.55–6.13.',16),text(25,609,'IDC: jack(208,108)/(212,170); middle(258,154)/(292,154)/(274,286); control(218.5,297.5).',16),text(25,637,'Control lower tab x206.5–230.5,y290–312. Orange outline is a NEW PCB change; neighboring fit still open.',16),text(25,674,'Cable routes / parking and foreign populated volumes remain reservations — see report, not hidden clear space.',17,'#a65e42'),text(25,708,'Remove cover → support core → undo4 screws → axial7 mm → total40 mm → unplug front IDC for front service.',16),text(25,738,'Unpowered integrated prototype: actual A01 stack + three ribbons + representative neighbor envelopes. No coupon/order.',15),'</g></svg>']
 return '\n'.join(s)+'\n'
if __name__=='__main__':
 a=build();out={'layout.json':json.dumps(a,indent=2,sort_keys=True)+'\n','layout.svg':drawing(a)}
 for n,s in out.items():
  if '--check' in sys.argv:
   if not (HERE/n).exists() or (HERE/n).read_text()!=s:raise SystemExit('STALE '+n)
  else:(HERE/n).write_text(s)
 print(json.dumps(a['screens'],indent=2));print('PASS deterministic layout' if '--check' in sys.argv else 'Wrote proposal')
