"""Read-only planar comparison of saved native fills; not a native acceptance test."""
import hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from scripts.pcbgen.uuid_tools import top_level_spans
ROOT=Path('.circuit-cache/issue189-downloaded/jl-u2119-via-avoid/.circuit-cache')
ROI=box(198,106,206,114)
OUT=Path('circuit/routing/issue189/jl-u2119-fill-diagnosis')
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
p=ROOT/'osc-jack-left-grid-shards-start/osc-jack-left.kicad_pcb';q=ROOT/'osc-jack-left-grid-shards-merge/osc-jack-left.kicad_pcb'
a,b=fills(p),fills(q);result={'status':'READ-ONLY NATIVE FILL GEOMETRY DIAGNOSIS; NOT ACCEPTANCE','before_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'roi_mm':[198,106,206,114],'layers':{}}
for layer in sorted(set(a)|set(b)):
 before=a.get(layer,Polygon());after=b.get(layer,Polygon());lost=before.difference(after);added=after.difference(before)
 result['layers'][layer]={'before_area_mm2':before.area,'after_area_mm2':after.area,'lost_area_mm2':lost.area,'added_area_mm2':added.area,'lost_bounds_mm':list(lost.bounds) if not lost.is_empty else None}
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="197 105 10 11"><rect x="197" y="105" width="10" height="11" fill="white"/>'
 svg+=before.svg(scale_factor=.01,fill_color='#b5c9b5',opacity=.5)+lost.svg(scale_factor=.01,fill_color='#e05050',opacity=1)+added.svg(scale_factor=.01,fill_color='#4060f0',opacity=1)
 for x,y,label in [(201.959999,108.95,'C2148.2')]:svg+=f'<circle cx="{x}" cy="{y}" r=".15"/><text x="198" y="{y}" font-size=".45">{label}</text>'
 svg+='</svg>';(OUT/(layer+'.svg')).write_text(svg)
(OUT/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
