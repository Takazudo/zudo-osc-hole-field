import json,hashlib
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
source=Path('.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(source.read_text());foreign=[];ids=[]
net='-12V';layer='F.Cu'
for p in d['pads']:
 if p['net']!=net and layer in p['layers'] and p['poly']:foreign.append(Polygon(p['poly']));ids.append(p['ref']+'.'+p['pad'])
for t in d['tracks']:
 if t['net']!=net and t['layer']==layer:foreign.append(LineString([t['a'],t['b']]).buffer(t['width']/2));ids.append(t['uuid'])
for v in d['vias']:
 if v['net']!=net:foreign.append(Point(v['xy']).buffer(v['diameter']/2));ids.append(v['uuid'])
tree=STRtree(foreign);out=[]
for ref in ['U204','U3102','U3202']:
 p=next(p for p in d['pads'] if p['ref']==ref and p['pad']=='11');assert p['net']==net and p['layers']==[layer]
 bounds=Polygon(p['poly']).bounds;axis=0 if bounds[2]-bounds[0]>bounds[3]-bounds[1] else 1
 for sign in [-1,1]:
  end=list(p['xy']);end[axis]=int(bounds[axis+(2 if sign>0 else 0)]+sign*400000);line=LineString([p['xy'],end]);near=tree.query(line.buffer(450001));viol=[{'object':ids[int(i)],'clearance_mm':(line.distance(foreign[int(i)])-200000)/1e6} for i in near if line.distance(foreign[int(i)])<449999]
  row={'pad':ref+'.11','start_nm':p['xy'],'end_nm':end,'width_nm':400000,'layer':layer,'net':net,'foreign_clearance_screen_pass':not viol,'blockers':viol};out.append(row);print(ref,sign,'blockers',len(viol),viol[:2])
Path('.circuit-cache/issue189-jl-rail-escape-screen.json').write_text(json.dumps({'status':'GEOMETRIC SCREEN ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'board_sha256':d['board_sha256'],'scope':'0.4mm source-pin lead escape; minimum0.25mm foreign copper clearance screen. No pad movement or rule changes. Full native checks remain mandatory.','candidates':out},indent=2)+'\n')
