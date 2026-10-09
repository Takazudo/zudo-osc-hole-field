"""Follow only the natively warned terminal centerline to its first fixed junction."""
import hashlib,json
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
source=Path('.circuit-cache/issue189-downloaded/jl-ground-corridor/osc-jack-left-grid-189-jl-ground-corridor-verify/dump.json')
d=json.loads(source.read_text());assert d['board_sha256']=='52ccc61d654358e065e965a8017480c3d5f916a7a11def61f4bdca5e913e47d3'
net='XB64017DF2FF0BC77988E';tracks={t['uuid']:t for t in d['tracks'] if t['net']==net};vias=[v for v in d['vias'] if v['net']==net];pads=[p for p in d['pads'] if p['net']==net]
uid='314bbbeb-a6d9-58dc-8d13-9539dd4a935d';free=[143500000,122700000];removed=[];stop=None
for _ in range(20):
 t=tracks[uid];assert free in (t['a'],t['b']);end=t['b'] if free==t['a'] else t['a'];line=LineString([free,end]);others=[o for u,o in tracks.items() if u!=uid and o['layer']==t['layer']]
 assert not any(Point(free).distance(LineString([o['a'],o['b']]))<=1 for o in others)
 # Refuse to remove a track with an interior centerline junction or fixed anchor.
 interior=False
 for o in others:
  cross=line.intersection(LineString([o['a'],o['b']]))
  if not cross.is_empty and cross.distance(Point(end))>1:interior=True
 for v in vias:
  q=line.interpolate(line.project(Point(v['xy'])))
  if Point(v['xy']).distance(line)<=v['diameter']/2 and q.distance(Point(end))>1:interior=True
 for p in pads:
  if t['layer'] in p['layers'] and line.intersects(Polygon(p['poly'])):interior=True
 if interior:stop='interior junction/anchor; keep complete track';break
 removed.append(tracks.pop(uid))
 if end==[146800000,123600000]:stop='source-defined preserved long-track junction';break
 if any(Point(end).distance(Point(v['xy']))<=v['diameter']/2 for v in vias):stop='fixed via anchor';break
 if any(t['layer'] in p['layers'] and Point(end).distance(Polygon(p['poly']))<=t['width']/2 for p in pads):stop='fixed pad anchor';break
 neighbors=[o for o in others if Point(end).distance(LineString([o['a'],o['b']]))<=1]
 if len(neighbors)!=1 or end not in (neighbors[0]['a'],neighbors[0]['b']):stop='branch or centerline junction';break
 uid=neighbors[0]['uuid'];free=end
else:raise ValueError('terminal-chain budget exceeded')
length=sum(LineString([t['a'],t['b']]).length for t in removed)/1e6
assert removed and length<=5
out={'status':'GEOMETRIC PROPOSAL; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'removed_tracks':removed,'length_mm':length,'stop':stop,'stop_track':t,'approach_end':free,'scope':'Only the known native-warning terminal branch; track centerlines distinguish tiny staircase segments from nearby overlapping stroke caps. Fixed pads/vias and interior branches stop deletion. Maximum20 tracks/5mm; full native pad membership and warning gates mandatory.'}
Path('.circuit-cache/issue189-jl-ground-inner-tail-screen.json').write_text(json.dumps(out,indent=2)+'\n');print('tracks',len(removed),'length',length,'stop',stop)
