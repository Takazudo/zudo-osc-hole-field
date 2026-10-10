"""Screen translated ground pads against exact saved native connected-ground pours."""
import hashlib,json,re,sys
from pathlib import Path
import numpy as np
import shapely
from shapely.strtree import STRtree
ROOT=Path('/workspace/issue189-jl-layer-escape');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans
HERE=Path(__file__).parent;INPUT=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh');d=json.loads((INPUT/'dump.json').read_text());board=INPUT/'osc-jack-left.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(board)==d['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
main=set(max(d['islands']['AGND'],key=len));trees={}
for layer in ('F.Cu','B.Cu'):
 trees[layer]=STRtree([shapely.Polygon(np.array(p['poly'])/1e6) for p in d['pads'] if p['uuid'] in main and p['poly'] and layer in p['layers']])
text=board.read_text();polys={};invalid=0
for a,b in top_level_spans(text):
 block=text[a:b]
 if not block.startswith('(zone') or '(net "AGND")' not in block:continue
 layer=re.search(r'\(layer\s+"([^"]+)"\)',block)[1]
 if layer not in trees:continue
 for x,y in top_level_spans(block):
  child=block[x:y]
  if not child.startswith('(filled_polygon'):continue
  assert '(arc' not in child
  shape=shapely.Polygon([(float(x),float(y)) for x,y in re.findall(r'\(xy\s+([-\d.eE+]+)\s+([-\d.eE+]+)\)',child)])
  if not shape.is_valid:invalid+=1;shape=shapely.make_valid(shape)
  for poly in ([shape] if shape.geom_type=='Polygon' else shapely.get_parts(shape)):
   if poly.geom_type!='Polygon' or not len(trees[layer].query(poly,predicate='intersects')):continue
   polys.setdefault(layer,[]).append((poly,hashlib.sha256(child.encode()).hexdigest()))
results=[]
for ref in ['R8107','R8270','R8273']:
 screen=json.loads((HERE/ref/'result.json').read_text());layer=screen['part']['side'];pad=next(p for p in d['pads'] if p['ref']==ref and p['net']=='AGND');cases=[]
 for c in screen['static_candidates']:
  delta=np.array(c['delta_mm']);poly=shapely.Polygon(np.array(pad['poly'])/1e6+delta)
  hits=[{'native_fill_sha256':h,'overlap_mm2':poly.intersection(p).area} for p,h in polys.get(layer,[]) if poly.intersects(p)]
  cases.append({'delta_mm':c['delta_mm'],'main_ground_fill_hits':hits})
 result={'ref':ref,'side':layer,'static_count':len(cases),'cases':cases,'overlap_candidates':[c for c in cases if any(h['overlap_mm2']>=.05 for h in c['main_ground_fill_hits'])]};results.append(result);print(ref,len(result['overlap_candidates']),flush=True)
(HERE/'pour-overlap-result.json').write_text(json.dumps({'status':'STATIC NATIVE-POUR OVERLAP SCREEN; NO PLACEMENT OR NATIVE ACCEPTANCE','board_sha256':sha(board),'dump_sha256':sha(INPUT/'dump.json'),'invalid_contours_made_valid_for_screen_only':invalid,'results':results},indent=2)+'\n')
