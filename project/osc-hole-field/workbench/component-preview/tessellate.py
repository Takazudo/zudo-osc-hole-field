"""Optional CAD acquisition derivative; normal browser build needs no CAD packages."""
from pathlib import Path
import hashlib,json
import cadquery as cq
P=Path(__file__).resolve().parent
out={}
for name in ('pot','jack'):
    path=P/'models'/f'{name}.step'
    shape=cq.importers.importStep(str(path)).val()
    solids=[]
    for solid in shape.Solids():
        vertices,triangles=solid.tessellate(.08,.15)
        solids.append({'positions':[round(c,6) for v in vertices for c in v.toTuple()], 'indices':[i for t in triangles for i in t]})
    b=shape.BoundingBox()
    out[name]={'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(), 'bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax], 'solids':solids}
(P/'models/meshes.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
print('Tessellated',[(k,sum(len(s['indices'])//3 for s in v['solids'])) for k,v in out.items()])
