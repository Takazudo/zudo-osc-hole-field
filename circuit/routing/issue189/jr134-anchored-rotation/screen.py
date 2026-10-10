"""Screen27 virtual rotations around unchanged signal landings; no source edits."""
import argparse,hashlib,json,re,sys,time,uuid
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT))
from scripts.pcbgen.placement_geometry import Box,inside_outline
from scripts.pcbgen.route_jack_grid import RAILS
TARGETS=['R4409','R4611','R7609','R8490','RB4413','RB4414','RB4613','RB4614','RB4615']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rotate(point,anchor,turn):
 x,y=[v-a for v,a in zip(point,anchor)]
 dx,dy={90:(-y,x),180:(-x,-y),270:(y,-x)}[turn]
 return [anchor[0]+dx,anchor[1]+dy]
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();started=time.monotonic()
assert sha(a.dump)=='f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a'
d=json.loads(a.dump.read_text());board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==d['board_sha256']=='35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445'
floor=ROOT/'design/partition/floorplan-candidate.json';placements=json.loads(floor.read_text())['placements'];byref={r['ref']:r for r in placements}
source_path=ROOT/'design/partition/partition-input.json';source=json.loads(source_path.read_text())
header_path=ROOT/'design/partition/connector-packing-candidate.json';headers=json.loads(header_path.read_text())['headers']
indices={}
for side in ('F.Cu','B.Cu'):
 shapes=[];meta=[]
 for pad in d['pads']:
  if side not in pad['layers']:continue
  shapes.append(Polygon([(x/1e6,y/1e6) for x,y in pad['poly']]) if pad['poly'] else Point([v/1e6 for v in pad['xy']]))
  meta.append((pad['net'],pad['uuid'],pad['ref']))
 for t in d['tracks']:
  if t['layer']==side:
   shapes.append(LineString([[v/1e6 for v in t[k]] for k in ('a','b')]).buffer(t['width']/2e6));meta.append((t['net'],t['uuid'],None))
 for v in d['vias']:
  shapes.append(Point([a/1e6 for a in v['xy']]).buffer(v['diameter']/2e6));meta.append((v['net'],v['uuid'],None))
 indices[side]=(STRtree(shapes),shapes,meta)
cases=[]
for ref in TARGETS:
 part=byref[ref];side=part['side'];pads=[p for p in d['pads'] if p['ref']==ref]
 assert not part['fixed'] and 'bypass_cluster' not in part and part['board']=='JR' and re.fullmatch(r'RB?\d+',ref)
 assert len(pads)==2 and all(not p['drill'] and p['layers']==[side] for p in pads)
 ground=next(p for p in pads if p['net']=='AGND');signal=next(p for p in pads if p['net']!='AGND');assert signal['net'] not in RAILS
 # Derive the board's source-to-native translation from this symmetric resistor.
 midpoint_nm=[sum(p['xy'][i] for p in pads)//2 for i in (0,1)]
 assert all(sum(p['xy'][i] for p in pads)%2==0 for i in (0,1))
 # Match the integer source-coordinate conversion exactly, including the saved
 # one-nanometre truncation in R8490/RB4414; do not widen a geometric tolerance.
 assert midpoint_nm==[int((part['x_mm']+100)*1e6),int((part['y_mm']+50)*1e6)]
 anchor=[v+(n-m)/1e6 for v,n,m in zip([part['x_mm'],part['y_mm']],signal['xy'],midpoint_nm)]
 tree,fixed,meta=indices[side];old_ground=Polygon([(x/1e6,y/1e6) for x,y in ground['poly']])
 contacts=[meta[i][1] for i in tree.query(old_ground) if meta[i][0]=='AGND' and meta[i][2] is None and old_ground.distance(fixed[i])<=1e-8]
 for turn in (90,180,270):
  case=dict(ref=ref,turn_degrees=turn,signal_pad=signal['pad'],signal_anchor_nm=signal['xy'],old_ground_copper_contacts=contacts,expected_source=part)
  moved_center=rotate([part['x_mm'],part['y_mm']],anchor,turn)
  x0,y0,x1,y1=part['courtyard_mm'];corners=[rotate(p,anchor,turn) for p in ([x0,y0],[x0,y1],[x1,y0],[x1,y1])]
  bounds=[min(p[0] for p in corners),min(p[1] for p in corners),max(p[0] for p in corners),max(p[1] for p in corners)]
  new=dict(part,x_mm=moved_center[0],y_mm=moved_center[1],rotation_deg=(part['rotation_deg']+turn)%360,kicad_orientation_deg=(part['kicad_orientation_deg']-turn)%360,courtyard_mm=bounds)
  case['proposed_source']=new;courtyard=Box(*bounds)
  case['expected_native_center_nm']=rotate(midpoint_nm,signal['xy'],turn)
  if [int((new['x_mm']+100)*1e6),int((new['y_mm']+50)*1e6)]!=case['expected_native_center_nm']:
   case['rejected']='source quantization would shift the fixed signal anchor';cases.append(case);continue
  if not inside_outline(courtyard,source['boards']['JR']['outline'],.30):case['rejected']='source board edge'
  else:
   for other in placements:
    if other['ref']!=ref and other['board']=='JR' and other['side']==side and courtyard.intersects(Box(*other['courtyard_mm']),.35-1e-8):case['rejected']='source courtyard '+other['ref'];break
   if 'rejected' not in case:
    for h in headers:
     if h['board']=='JR' and h['side']==side and courtyard.intersects(Box(*h['land_courtyard_mm']),.35-1e-8):case['rejected']='source connector '+h['id'];break
  if 'rejected' in case:cases.append(case);continue
  newpads=[];shapes=[]
  for pad in pads:
   updated=dict(pad,xy=rotate(pad['xy'],signal['xy'],turn),poly=[rotate(point,signal['xy'],turn) for point in pad['poly']]);newpads.append(updated)
   shapes.append((Polygon([(x/1e6,y/1e6) for x,y in updated['poly']]),pad['net'],pad['uuid']))
  assert next(p for p in newpads if p['uuid']==signal['uuid'])['xy']==signal['xy']
  bridges=[]
  if contacts:
   end=next(p for p in newpads if p['net']=='AGND')['xy'];uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-jr-anchor-'+ref+str(turn)))
   bridges.append(dict(kind='segment',uuid=uid,net='AGND',layer=side,start_nm=ground['xy'],end_nm=end,width_nm=300000))
   shapes.append((LineString([[v/1e6 for v in point] for point in (ground['xy'],end)]).buffer(.15),'AGND',uid))
  block=None
  for shape,net,uid in shapes:
   for i in tree.query(shape.buffer(.25)):
    if meta[i][2]==ref or meta[i][0]==net:continue
    if shape.distance(fixed[i])<.25-1e-8:block=dict(object=uid,conflict=meta[i][1]);break
   if block:break
  if block is None:
   for i,(shape,net,uid) in enumerate(shapes):
    for other,on,oid in shapes[i+1:]:
     if net!=on and shape.distance(other)<.25-1e-8:block=dict(object=uid,conflict=oid);break
    if block:break
  if block:case['rejected_copper']=block
  else:case.update(static_candidate=True,virtual_pads=newpads,bridges=bridges,anchor_source_mm=anchor,requires_source_rotation_support=True)
  cases.append(case)
 print(ref,'candidates',sum(c.get('static_candidate',False) for c in cases if c['ref']==ref),'old ground contacts',len(contacts),flush=True)
assert len(cases)==27 and sha(board)==d['board_sha256']
out=dict(status='READ-ONLY ROTATION SCREEN; SOURCE ROTATION SUPPORT/NATIVE VALIDATION NOT IMPLEMENTED OR RUN',board_sha256=sha(board),dump_sha256=sha(a.dump),floorplan_sha256=sha(floor),source_sha256=sha(source_path),headers_sha256=sha(header_path),case_count=27,elapsed_seconds=time.monotonic()-started,cases=cases,static_candidates=[c for c in cases if c.get('static_candidate')])
(HERE/'screen.json').write_text(json.dumps(out,indent=2)+'\n');print('COMPLETE27cases;',len(out['static_candidates']),'candidates; no source/board change')
