"""Bounded additive-via screen on saved native JL118 fills; not native acceptance."""
import hashlib,json,math,re,sys,time
from pathlib import Path
import numpy as np
import shapely
from scipy import ndimage
ROOT=Path('/workspace/issue189-jr131-next');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans
from scripts.pcbgen.grid_router import Raster,SQRT2
HERE=Path(__file__).parent
INPUT=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=INPUT/'dump.json';board=INPUT/'osc-jack-left.kicad_pcb'
assert sha(dump)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
d=json.loads(dump.read_text());pads={p['uuid']:p for p in d['pads']};groups=sorted(d['islands']['AGND'],key=len);main=set(groups[-1]);zones={};invalid=0
board_text=board.read_text()
for a,b in top_level_spans(board_text):
 block=board_text[a:b]
 if not block.startswith('(zone') or '(net "AGND")' not in block:continue
 layer=re.search(r'\(layer\s+"([^"]+)"\)',block)[1]
 if layer not in ('F.Cu','B.Cu','In1.Cu'):continue
 for x,y in top_level_spans(block):
  child=block[x:y]
  if not child.startswith('(filled_polygon'):continue
  assert '(arc' not in child
  pts=[(float(x),float(y)) for x,y in re.findall(r'\(xy\s+([-\d.eE+]+)\s+([-\d.eE+]+)\)',child)]
  poly=shapely.Polygon(pts)
  if not poly.is_valid:invalid+=1;poly=shapely.make_valid(poly)
  for p in ([poly] if poly.geom_type=='Polygon' else shapely.get_parts(poly)):
   if p.geom_type=='Polygon':zones.setdefault(layer,[]).append((p,hashlib.sha256(child.encode()).hexdigest()))
plane=shapely.union_all([p for p,h in zones['In1.Cu']]);results=[];res=.025;margin=res/SQRT2+.01
for group in groups[:-1]:
 ps=[pads[u] for u in group if u in pads];row={'source_pad_uuids':[p['uuid'] for p in ps],'source_pads':[[p['ref'],p['pad']] for p in ps],'matches':[]};results.append(row)
 for layer in ('F.Cu','B.Cu'):
  shapes=[shapely.Polygon(np.array(p['poly'])/1e6) for p in ps if layer in p['layers'] and p['poly']]
  if not shapes:continue
  for poly,digest in zones.get(layer,[]):
   if not any(poly.intersects(s) for s in shapes):continue
   foreign_ground=[p for u,p in pads.items() if p['net']=='AGND' and u not in group and layer in p['layers'] and p['poly']]
   touches_other=any(poly.intersects(shapely.Polygon(np.array(p['poly'])/1e6)) for p in foreign_ground)
   item={'layer':layer,'fill_sha256':digest,'bounds_mm':list(poly.bounds),'touches_other_ground_pads':touches_other};row['matches'].append(item)
   if touches_other:item['status']='ambiguous mapping; skipped';continue
   bounds=[poly.bounds[0]-.6,poly.bounds[1]-.6,poly.bounds[2]+.6,poly.bounds[3]+.6]
   if max(bounds[2]-bounds[0],bounds[3]-bounds[1])>30:item['status']='outside 30 mm bound';continue
   r=Raster(d,res,grow={n:.05 for n in ['+12V','-12V','+5V','AGND']},bounds_mm=bounds);N=r.net_id['AGND']
   foreign=np.any((r.label!=0)&(r.label!=N),axis=0)|np.any((r.fixed_label!=0)&(r.fixed_label!=N),axis=0)
   good=(ndimage.distance_transform_edt(~foreign)*res>=.25+.3+margin)&(r.d_edge>=.5+.3+margin)&(r.d_keep_via>=.3+margin)&(ndimage.distance_transform_edt(~r.hole)*res>=.3+.25+margin)&(r.d_smd>=.3+margin)
   gx,gy=r.centres();gx=gx/1e6;gy=gy/1e6
   good&=shapely.contains_xy(poly.buffer(-(.3+margin)),gx,gy)&shapely.contains_xy(plane.buffer(-(.3+margin)),gx,gy)
   ys,xs=np.nonzero(good);sites=sorted([(min(math.dist((float(gx[y,x]),float(gy[y,x])),[v/1e6 for v in p['xy']]) for p in ps),float(gx[y,x]),float(gy[y,x])) for y,x in zip(ys,xs)])
   item.update(status='screened',legal_cells=len(sites),sites=[{'x_mm':x,'y_mm':y,'nearest_pad_mm':dist} for dist,x,y in sites[:5]])
 print(json.dumps(row),flush=True)
result={'status':'READ-ONLY BOUNDED SCREEN; NO NATIVE ACCEPTANCE','board_sha256':sha(board),'dump_sha256':sha(dump),'invalid_contours_made_valid_for_screen_only':invalid,'via_diameter_mm':.6,'drill_mm':.3,'clearance_mm':.25,'lattice_mm':res,'margin_mm':margin,'islands':results}
(HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
