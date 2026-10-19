"""Pre-search geometric plausibility only: fractured polygon normalization is approximate."""
from pathlib import Path
import hashlib,json,sys
from shapely.geometry import Polygon,Point,LineString
p=Path(sys.argv[1]);d=json.loads(p.read_text());g=Polygon(d.pop('points'));valid=g.is_valid;g=g.buffer(0)
a=(227.980882,113.013236);result=[]
for name,b in [('seed',None),('closest',(235.3,95.7)),('farther',(226.5,84.1))]:
 cut=Point(a).buffer(.55)
 if b:cut=cut.union(LineString([a,b]).buffer(.35))
 h=g.difference(cut).buffer(0);parts=list(h.geoms) if hasattr(h,'geoms') else [h]
 result.append(dict(name=name,components=len(parts),areas_mm2=sorted(x.area for x in parts)))
r=dict(native=d,export_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_valid=valid,normalized_area_mm2=g.area,results=result,limits='Default polygonal buffers and buffer(0) normalization are approximate. Direct line fails fixed-copper clearance; this is not a route. Native refill, all retained rail partitions and electrical rail capacity remain unestablished by this diagnostic.')
Path(sys.argv[2]).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
