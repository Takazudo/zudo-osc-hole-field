#!/usr/bin/env python3
"""One deterministic proposal subregion from saved geometry; no pose audit."""
import gzip,hashlib,json,resource,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
from shapely import maximum_inscribed_circle,normalize
import shapely
from shapely.geometry import shape,box,mapping,Point
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'f3-rearrangement-v1'
ROOT=HERE.parents[5]
start=time.monotonic()
assert shapely.__version__=='2.1.2' and shapely.geos_version_string=='3.13.1'
assert not (HERE/'evidence/region-selection.json').exists()
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def key(r):return ':'.join(map(str,r['source_span']))+':'+r['sha256']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[OLD/'evidence/regions/A24-N-result.json',OLD/'evidence/pad-regions/A24-N-constraints.json.gz',ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz',OLD/'ledger.json',Path(__file__).resolve()]
seals={str(p.relative_to(ROOT)):sha(p) for p in paths}
old=read(OLD/'ledger.json')
for p in paths[:2]:assert old['files_sha256'][str(p.relative_to(OLD))]==sha(p)
assert seals[str(paths[2].relative_to(ROOT))]=='1fd9f4191b76cbc391ff4d4eedbea985a501e5417959c950903add3b99efb74c'
available=shape(read(paths[0])['robust_external_free'])
parts=list(available.geoms) if available.geom_type=='MultiPolygon' else [available]
part=sorted(parts,key=lambda g:(-g.area,g.bounds,normalize(g).wkb))[0]
center=Point(maximum_inscribed_circle(part,tolerance=.001).coords[0])
radius=center.distance(part.boundary);half=min(.25,radius/4)
assert radius>0 and half>0
cell=box(center.x-half,center.y-half,center.x+half,center.y+half)
assert part.contains(cell) and cell.distance(part.boundary)>0
constraints=read(paths[1]);indices=[];keys=set();fixed=[]
for n,c in enumerate(constraints):
 if shape(c['upper']).buffer(.001,quad_segs=32).intersects(cell):
  indices.append(n)
  if c['kind'] in ('FOREIGN_COPPER','SAME_NET_VIA_SMD'):keys.add(c['fixed_id'])
  else:fixed.append({'constraint_index':n,**{k:v for k,v in c.items() if k not in ('lower','upper')}})
assert not fixed,'Nonreleasable fixed geometry intersects proposal cell; no alternative permitted'
retained=[shape(c['upper']).buffer(.001,quad_segs=32) for c in constraints if c['fixed_id'] not in keys]
conditional=available.difference(unary_union(retained));assert conditional.covers(cell)
index=[json.loads(line) for line in gzip.decompress(paths[2].read_bytes()).splitlines()]
roster=[dict(row,object_key=key(row),source_index_ordinal=n) for n,row in enumerate(index) if key(row) in keys]
assert len(roster)==len(keys) and all(r['kind'] in ('segment','via') for r in roster)
counts={}
for row in roster:counts[row['net_token']]=counts.get(row['net_token'],0)+1
out={'status':'HYPOTHETICAL_PAD_ONLY_OPPORTUNITY_NOT_PLACEMENT_FEASIBILITY','method':'One largest-courtyard-component maximum-inscribed-center datum, tolerance0.001mm, square halfside=min(0.25mm,boundarydistance/4); all saved guarded-upper intersections, no pose search or minimum claim','center_datum_offset_mm':[center.x,center.y],'radius_mm':radius,'half_side_mm':half,'proposal_offset_region':mapping(cell),'proposal_offset_area_mm2':cell.area,'conditional_full_region':mapping(conditional),'conditional_full_region_area_mm2':conditional.area,'selected_constraint_indices':indices,'selected_objects':roster,'net_token_object_counts':counts,'nonreleasable_conflicts':fixed,'all_remaining_constraints_clear_cell':True,'source_sha256':seals,'elapsed_seconds':time.monotonic()-start,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0,'selected_PCB_poses':0,'canonical_edits':0}
for p in paths:assert seals[str(p.relative_to(ROOT))]==sha(p)
(HERE/'evidence/region-selection.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('selected_objects','conditional_full_region','source_sha256')},sort_keys=True))
