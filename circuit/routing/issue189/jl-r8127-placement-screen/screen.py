"""Read-only sub-mm R8127 translation screen; native validation remains mandatory."""
import hashlib,json,sys
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
p=ROOT/'.circuit-cache/issue189-downloaded/jl-u1518-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json'
d=json.loads(p.read_text());board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert hashlib.sha256(board.read_bytes()).hexdigest()==d['board_sha256']
floor=ROOT/'design/partition/floorplan-candidate.json';placements=json.loads(floor.read_text())['placements'];part=next(p for p in placements if p['ref']=='R8127');assert not part['fixed'] and 'bypass_cluster' not in part and part['side']=='B.Cu' and part['board']=='JL'
pads=[p for p in d['pads'] if p['ref']=='R8127'];assert len(pads)==2
shapes=[];meta=[]
for pad in d['pads']:
 if pad['ref']=='R8127' or 'B.Cu' not in pad['layers']:continue
 shapes.append(Polygon([(x/1e6,y/1e6) for x,y in pad['poly']]) if pad['poly'] else Point([v/1e6 for v in pad['xy']]))
 meta.append((pad['net'],pad['uuid']))
for t in d['tracks']:
 if t['layer']!='B.Cu':continue
 shapes.append(LineString([[v/1e6 for v in t[k]] for k in ['a','b']]).buffer(t['width']/2e6));meta.append((t['net'],t['uuid']))
for v in d['vias']:
 shapes.append(Point([a/1e6 for a in v['xy']]).buffer(v['diameter']/2e6));meta.append((v['net'],v['uuid']))
tree=STRtree(shapes)
def conflict(shape,net):
 for i in tree.query(shape.buffer(.25)):
  if meta[i][0]!=net and shape.distance(shapes[i])<.25-1e-8:return meta[i][1]
 return None
others=[(p['ref'],box(*p['courtyard_mm'])) for p in placements if p['ref']!='R8127' and p['board']=='JL' and p['side']=='B.Cu']
partition=ROOT/'design/partition/partition.json';outline=next(b['outline'] for b in json.loads(partition.read_text())['boards'] if b.get('board_key')=='JL');inside=Polygon(outline).buffer(-.30)
source_box=part['courtyard_mm'];cases=[]
# Use the exact source JL outline with the floorplan generator's .30mm inset.
for ix in range(-8,9):
 for iy in range(-8,9):
  if not(ix or iy):continue
  dx,dy=ix/10,iy/10;b=[source_box[0]+dx,source_box[1]+dy,source_box[2]+dx,source_box[3]+dy]
  courtyard=box(*b)
  if not inside.covers(courtyard):
   cases.append({'delta_mm':[dx,dy],'courtyard_conflict':'SOURCE_BOARD_EDGE'});continue
  block=next((ref for ref,other in others if courtyard.distance(other)<.35-1e-8),None)
  item={'delta_mm':[dx,dy],'courtyard_conflict':block}
  if block:cases.append(item);continue
  conflicts=[]
  for pad in pads:
   poly=Polygon([(x/1e6+dx,y/1e6+dy) for x,y in pad['poly']]);hit=conflict(poly,pad['net'])
   if hit:conflicts.append({'pad':pad['pad'],'object':hit})
  item['pad_clearance_conflicts']=conflicts
  # Preserve the old signal landing with an additive .2mm bridge, never cutting copper.
  signal=next(p for p in pads if p['net']!='AGND');x,y=[v/1e6 for v in signal['xy']]
  bridge=LineString([(x,y),(x+dx,y+dy)]).buffer(.1)
  item['signal_bridge_conflict']=conflict(bridge,signal['net'])
  item['static_candidate']=not conflicts and not item['signal_bridge_conflict'];cases.append(item)
out={'status':'READ-ONLY STATIC SCREEN; NO PLACEMENT CHANGED; NATIVE NOT RUN','board_sha256':d['board_sha256'],'dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'floorplan_sha256':hashlib.sha256(floor.read_bytes()).hexdigest(),'part':part,'source_outline':outline,'source_partition_sha256':hashlib.sha256(partition.read_bytes()).hexdigest(),'scope':'R8127 only, translations in 0.1mm increments within +/-0.8mm, unchanged orientation/side, no cuts, full .2mm signal bridge, .25mm copper/.35mm courtyard screening. Exact zones, native clearance, source regeneration and all original topology/warning gates remain mandatory.','cases':cases,'static_candidates':[c for c in cases if c.get('static_candidate')]}
(HERE/'result.json').write_text(json.dumps(out,indent=2)+'\n');print('cases',len(cases),'courtyard clear',sum(not c['courtyard_conflict'] for c in cases),'static candidates',len(out['static_candidates']))
