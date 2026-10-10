"""Enumerate exact saved-input copper blockers; never cut or promote anything."""
import argparse,hashlib,json,sys
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();r=json.loads((HERE/'screen.json').read_text());assert sha(a.dump)==r['dump_sha256'];d=json.loads(a.dump.read_text());assert sha(ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb')==r['board_sha256']
def rotate(point,anchor,turn):
 x,y=[v-a for v,a in zip(point,anchor)];dx,dy={90:(-y,x),180:(-x,-y),270:(y,-x)}[turn];return [anchor[0]+dx,anchor[1]+dy]
indices={}
for side in ('F.Cu','B.Cu'):
 shapes=[];meta=[]
 for pad in d['pads']:
  if side in pad['layers']:
   shapes.append(Polygon([(x/1e6,y/1e6) for x,y in pad['poly']]) if pad['poly'] else Point([v/1e6 for v in pad['xy']]));meta.append(dict(kind='pad',ref=pad['ref'],uuid=pad['uuid'],net=pad['net']))
 for t in d['tracks']:
  if t['layer']==side:
   shapes.append(LineString([[v/1e6 for v in t[k]] for k in ('a','b')]).buffer(t['width']/2e6));meta.append(dict(kind='track',ref=None,uuid=t['uuid'],net=t['net']))
 for v in d['vias']:
  shapes.append(Point([x/1e6 for x in v['xy']]).buffer(v['diameter']/2e6));meta.append(dict(kind='via',ref=None,uuid=v['uuid'],net=v['net']))
 indices[side]=(STRtree(shapes),shapes,meta)
rows=[]
for c in r['cases']:
 if 'rejected_copper' not in c:continue
 ref=c['ref'];turn=c['turn_degrees'];side=c['expected_source']['side'];tree,shapes,meta=indices[side];hits={}
 for pad in [p for p in d['pads'] if p['ref']==ref]:
  poly=Polygon([[v/1e6 for v in rotate(p,c['signal_anchor_nm'],turn)] for p in pad['poly']])
  for i in tree.query(poly.buffer(.25)):
   m=meta[i]
   if m['ref']==ref or m['net']==pad['net']:continue
   distance=poly.distance(shapes[i])
   if distance<.25-1e-8:
    hit=hits.setdefault(m['uuid'],dict(m,affected_pads=[],minimum_clearance_mm=distance));hit['affected_pads'].append(pad['uuid']);hit['minimum_clearance_mm']=min(hit['minimum_clearance_mm'],distance)
 blockers=sorted(hits.values(),key=lambda x:(x['kind'],x['uuid']))
 row=dict(ref=ref,turn_degrees=turn,blockers=blockers,small_track_only_scope=bool(blockers) and len(blockers)<=3 and all(b['kind']=='track' for b in blockers));rows.append(row)
 print(ref,turn,[(b['kind'],b['uuid']) for b in blockers],'small track-only scope',row['small_track_only_scope'])
(HERE/'blockers.json').write_text(json.dumps(dict(status='READ-ONLY BLOCKER INVENTORY; NO CUT OR NATIVE ROUTE',dump_sha256=sha(a.dump),screen_sha256=sha(HERE/'screen.json'),cases=rows),indent=2)+'\n')
