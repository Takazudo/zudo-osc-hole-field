"""Read-only planar comparison of saved native fills; not a native acceptance test."""
import hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from scripts.pcbgen.uuid_tools import top_level_spans
ROOT=Path('.circuit-cache/issue189-downloaded/jr-three-protected/.circuit-cache')
ROI=box(403,168,414,185)
OUT=Path('circuit/routing/issue189/jr-d7504-fill-diagnosis')
def fills(path):
 text=path.read_text();by={}
 for a,b in top_level_spans(text):
  z=text[a:b]
  if not z.startswith('(zone') or '(net "AGND")' not in z:continue
  for c,d in top_level_spans(z):
   child=z[c:d]
   if not child.startswith('(filled_polygon'):continue
   layer=re.search(r'\(layer "([^"]+)"\)',child)[1]
   pts=[tuple(map(float,p)) for p in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)',child)]
   if len(pts)<3:continue
   poly=Polygon(pts)
   if not poly.is_valid:poly=poly.buffer(0)
   if poly.intersects(ROI):by.setdefault(layer,[]).append(poly.intersection(ROI))
 return {k:unary_union(v) for k,v in by.items()}
p=ROOT/'osc-jack-right-grid-shards-start/osc-jack-right.kicad_pcb';q=ROOT/'osc-jack-right-grid-shards-merge/osc-jack-right.kicad_pcb'
a,b=fills(p),fills(q);result={'status':'READ-ONLY NATIVE FILL GEOMETRY DIAGNOSIS; NOT ACCEPTANCE','before_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'roi_mm':[403,168,414,185],'layers':{}}
for layer in sorted(set(a)|set(b)):
 before=a.get(layer,Polygon());after=b.get(layer,Polygon());lost=before.difference(after);added=after.difference(before)
 result['layers'][layer]={'before_area_mm2':before.area,'after_area_mm2':after.area,'lost_area_mm2':lost.area,'added_area_mm2':added.area,'lost_bounds_mm':list(lost.bounds) if not lost.is_empty else None}
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="402 167 13 19"><rect x="402" y="167" width="13" height="19" fill="white"/>'
 svg+=before.svg(fill_color='#b5c9b5',opacity=.5)+lost.svg(fill_color='#e05050',opacity=1)+added.svg(fill_color='#4060f0',opacity=1)
 for x,y,label in [(412.41,173.59,'R7505.2'),(412.41,180.989999,'R7530.2')]:svg+=f'<circle cx="{x}" cy="{y}" r=".15"/><text x="403" y="{y}" font-size=".45">{label}</text>'
 svg+='</svg>';(OUT/(layer+'.svg')).write_text(svg)
(OUT/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
