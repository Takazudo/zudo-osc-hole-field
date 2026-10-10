"""Screen direct ground-via sites in the exact rejected native filled island; no adoption."""
import hashlib,json,math,re,sys,time
from pathlib import Path
import numpy as np
import shapely
from scipy import ndimage
ROOT=Path('/workspace/issue189-jr131-next');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
from scripts.pcbgen.grid_router import Raster,SQRT2
HERE=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
board=Path('/tmp/issue189-jr131-in2-candidate.kicad_pcb');assert sha(board)=='ced4240944e5f16ebcf8b3c17ebf29347a2fe57c920530aa31c5fa39c0786230'
d=json.loads((HERE/'candidate.json').read_text());assert sha(HERE/'candidate.json')=='d6a3925d1495bd6ba9e5234868d89e22fd602ad4eb40adbf0676cf49d35044ca'
pads=[p for p in d['pads'] if (p['ref'],p['pad']) in [('C7523','2'),('R7331','2')]];assert len(pads)==2
source=next(g for g in d['islands']['AGND'] if pads[0]['uuid'] in g);assert set(source)=={p['uuid'] for p in pads}
pad_shapes=[shapely.Polygon(np.array(p['poly'])/1e6) for p in pads]
text=board.read_text();chosen=[];plane=[];invalid=0;stats={}
for a,b in top_level_spans(text):
 block=text[a:b]
 if not block.startswith('(zone') or '(net "AGND")' not in block:continue
 layer=re.search(r'\(layer\s+"([^"]+)"\)',block)[1]
 if layer not in ('B.Cu','In1.Cu'):continue
 stats[layer]=0
 for x,y in top_level_spans(block):
  child=block[x:y]
  if not child.startswith('(filled_polygon'):continue
  assert '(arc' not in child
  pts=[(float(x),float(y)) for x,y in re.findall(r'\(xy\s+([-\d.eE+]+)\s+([-\d.eE+]+)\)',child)]
  assert len(pts)>=3
  shape=shapely.Polygon(pts);stats[layer]+=1
  if not shape.is_valid:invalid+=1;shape=shapely.make_valid(shape)
  polys=[shape] if shape.geom_type=='Polygon' else [p for p in shapely.get_parts(shape) if p.geom_type=='Polygon']
  for poly in polys:
   if layer=='In1.Cu':plane.append(poly)
   elif all(poly.intersects(p) for p in pad_shapes):chosen.append((poly,hashlib.sha256(child.encode()).hexdigest()))
assert len(chosen)<=1,('ambiguous native island',len(chosen))
result=dict(status='BOUNDED NATIVE-FILL GEOMETRY SCREEN; NO NATIVE ACCEPTANCE',candidate_board_sha256=sha(board),candidate_dump_sha256=sha(HERE/'candidate.json'),raw_filled_polygon_counts=stats,invalid_contours_made_valid_for_screen_only=invalid,matching_islands=len(chosen),sites=[])
if chosen:
 poly,digest=chosen[0];other=[p for p in d['pads'] if p['net']=='AGND' and p['uuid'] not in source and 'B.Cu' in p['layers'] and p['poly']]
 assert not any(poly.intersects(shapely.Polygon(np.array(p['poly'])/1e6)) for p in other),'parsed island touches other original ground pads'
 bounds=[poly.bounds[0]-.6,poly.bounds[1]-.6,poly.bounds[2]+.6,poly.bounds[3]+.6];assert bounds[2]-bounds[0]<30 and bounds[3]-bounds[1]<30
 res=.025;margin=res/SQRT2+.01;r=Raster(d,res,grow={n:.05 for n in ['+12V','-12V','+5V','AGND']},bounds_mm=bounds);N=r.net_id['AGND']
 foreign=np.any((r.label!=0)&(r.label!=N),axis=0)|np.any((r.fixed_label!=0)&(r.fixed_label!=N),axis=0)
 good=(ndimage.distance_transform_edt(~foreign)*res>=.25+.3+margin)&(r.d_edge>=.5+.3+margin)&(r.d_keep_via>=.3+margin)&(ndimage.distance_transform_edt(~r.hole)*res>=.3+.25+margin)&(r.d_smd>=.3+margin)
 gx,gy=r.centres();gx=gx/1e6;gy=gy/1e6
 raw_y,raw_x=np.nonzero(good)
 before=int(good.sum());inside=shapely.contains_xy(poly.buffer(-(.3+margin)),gx,gy);plane_inside=shapely.contains_xy(shapely.union_all(plane).buffer(-(.3+margin)),gx,gy);good&=inside&plane_inside
 result['legal_uncontained_sites']=[dict(x_mm=float(gx[y,x]),y_mm=float(gy[y,x]),island_distance_mm=poly.distance(shapely.Point(float(gx[y,x]),float(gy[y,x]))),inside_native_ground_plane=bool(plane_inside[y,x]),inside_ground_island=bool(shapely.contains_xy(poly,float(gx[y,x]),float(gy[y,x])))) for y,x in zip(raw_y,raw_x)]
 ys,xs=np.nonzero(good);sites=sorted([(min(math.dist((float(gx[y,x]),float(gy[y,x])),[v/1e6 for v in p['xy']]) for p in pads),float(gx[y,x]),float(gy[y,x])) for y,x in zip(ys,xs)])
 result.update(island_area_mm2=poly.area,island_bounds_mm=list(poly.bounds),native_fill_block_sha256=digest,raw_legal_via_cells=before,legal_island_plane_cells=len(sites),sites=[dict(x_mm=x,y_mm=y,nearest_source_pad_mm=dist) for dist,x,y in sites[:12]],via_diameter_mm=.6,via_drill_mm=.3,clearance_mm=.25,lattice_mm=res,conservative_margin_mm=margin)
(HERE/'zone-via-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
