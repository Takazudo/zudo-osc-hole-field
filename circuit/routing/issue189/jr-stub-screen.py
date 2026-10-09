import json
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
p=Path('.circuit-cache/issue189-downloaded/jr-six-corridors/osc-jack-right-grid-189-jr-six-corridors-verify/dump.json');d=json.loads(p.read_text());net='X117A9D03425A2C3FC85C';tracks={t['uuid']:t for t in d['tracks'] if t['net']==net};vias=[v for v in d['vias'] if v['net']==net];pads=[p for p in d['pads'] if p['net']==net];removed=[]
def at(t,q,others):
 r=t['width']/2
 return any(o['layer']==t['layer'] and Point(q).distance(LineString([o['a'],o['b']]))<=r+o['width']/2 for o in others) or any(Point(q).distance(Point(v['xy']))<=r+v['diameter']/2 for v in vias) or any(t['layer'] in p['layers'] and Point(q).distance(Polygon(p['poly']))<=r for p in pads)
while len(removed)<20:
 found=[]
 for uid,t in tracks.items():
  others=[o for u,o in tracks.items() if u!=uid]
  if at(t,t['a'],others) and at(t,t['b'],others):continue
  line=LineString([t['a'],t['b']]);interior=line.interpolate(.5,normalized=True)
  # Stop at any interior branch/anchor; the complete track cannot be dropped.
  branch=False
  for o in others:
   if o['layer']!=t['layer']:continue
   cross=line.intersection(LineString([o['a'],o['b']]))
   if not cross.is_empty and cross.distance(Point(t['a']))>1 and cross.distance(Point(t['b']))>1:branch=True
  if branch:continue
  found.append(uid)
 if not found:break
 if len(removed)+len(found)>20:raise ValueError('bounded cleanup budget exceeded')
 for u in found:removed.append(tracks.pop(u))
out={'status':'GEOMETRIC PROPOSAL ONLY; NATIVE NOT RUN','net':net,'removed_tracks':removed,'scope':'Only terminal track chains on the one warned victim net; vias/pads are fixed anchors, interior track junctions stop trimming; maximum20 tracks. Native original membership/warnings mandatory.'};Path('.circuit-cache/issue189-jr-stub-screen.json').write_text(json.dumps(out,indent=2)+'\n');print('proposed tail removals',len(removed),'length_mm',sum(LineString([t['a'],t['b']]).length for t in removed)/1e6);print([x['uuid'] for x in removed])
