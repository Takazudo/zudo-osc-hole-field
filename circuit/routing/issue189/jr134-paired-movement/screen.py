"""Bounded paired-placement proposal screen; never mutate source or canonical copper."""
import argparse,hashlib,itertools,json,re,sys,time,uuid
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.checks.routing_placement_translations import apply_translations
from scripts.pcbgen.route_jack_grid import RAILS
TARGETS=['R4409','R4611','R7609','R8490','RB4413','RB4414','RB4613','RB4614','RB4615']
MOVES=[[a,b] for a,b in [(v,0) for v in (-.2,-.1,.1,.2)]+[(0,v) for v in (-.2,-.1,.1,.2)]]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);args=p.parse_args();started=time.monotonic()
assert sha(args.dump)=='f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a'
d=json.loads(args.dump.read_text());board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb'
assert sha(board)==d['board_sha256']=='35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445'
floor=ROOT/'design/partition/floorplan-candidate.json';placements=json.loads(floor.read_text())['placements'];byref={r['ref']:r for r in placements}
source_path=ROOT/'design/partition/partition-input.json';source=json.loads(source_path.read_text())
header_path=ROOT/'design/partition/connector-packing-candidate.json';headers=json.loads(header_path.read_text())['headers']
pads={}
for pad in d['pads']:pads.setdefault(pad['ref'],[]).append(pad)
def eligible(r):
 return r['board']=='JR' and not r['fixed'] and 'bypass_cluster' not in r and re.fullmatch(r'RB?\d+',r['ref']) and len(pads.get(r['ref'],[]))==2 and not any(p['net'] in RAILS for p in pads[r['ref']])
# One immutable obstacle index per face. Only the two moved pad envelopes are
# omitted during queries; every old track/via stays an obstacle.
indices={}
for side in ('F.Cu','B.Cu'):
 shapes=[];meta=[]
 for pad in d['pads']:
  if side not in pad['layers']:continue
  shapes.append(Polygon([(x/1e6,y/1e6) for x,y in pad['poly']]) if pad['poly'] else Point([v/1e6 for v in pad['xy']]))
  meta.append((pad['net'],pad['uuid'],pad['ref']))
 for t in d['tracks']:
  if t['layer']==side:
   shapes.append(LineString([[v/1e6 for v in t[k]] for k in ('a','b')]).buffer(t['width']/2e6));meta.append((t['net'],t['uuid'],None))
 for v in d['vias']:
  shapes.append(Point([a/1e6 for a in v['xy']]).buffer(v['diameter']/2e6));meta.append((v['net'],v['uuid'],None))
 indices[side]=(STRtree(shapes),shapes,meta)
def conflict(side,shape,net,moved):
 tree,shapes,meta=indices[side]
 for i in tree.query(shape.buffer(.25)):
  other,uid,ref=meta[i]
  if ref in moved or other==net:continue
  if shape.distance(shapes[i])<.25-1e-8:return uid
 return None
pairs=[];cases=[];candidates=[]
for target in TARGETS:
 part=byref[target];assert eligible(part)
 peers=sorted([r for r in placements if r['ref']!=target and r['side']==part['side'] and eligible(r)],key=lambda r:((r['x_mm']-part['x_mm'])**2+(r['y_mm']-part['y_mm'])**2,r['ref']))[:2]
 for peer in peers:
  refs=[target,peer['ref']];side=part['side'];pairs.append(refs)
  for moves in itertools.product(MOVES,repeat=2):
   case=dict(target=target,peer=peer['ref'],delta_mm=dict(zip(refs,moves)))
   changes=dict(schema_version=1,translations=[dict(ref=ref,expected_source=byref[ref],delta_mm=move,evidence='issue189 bounded paired movement; native NOT RUN') for ref,move in zip(refs,moves)])
   try:apply_translations(placements,source,changes,headers=headers)
   except ValueError as error:case['rejected']=str(error);cases.append(case);continue
   shapes=[];bridges=[]
   for ref,move in zip(refs,moves):
    dx,dy=move
    for pad in pads[ref]:
     shapes.append((Polygon([(x/1e6+dx,y/1e6+dy) for x,y in pad['poly']]),pad['net'],'moved-pad-'+pad['uuid']))
     start=pad['xy'];end=[v+round(delta*1e6) for v,delta in zip(start,move)];width=300000 if pad['net']=='AGND' else 200000
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-jr-paired-bridge-'+ref+str(move)+pad['uuid']))
     bridges.append(dict(kind='segment',uuid=uid,net=pad['net'],layer=side,start_nm=start,end_nm=end,width_nm=width))
     shapes.append((LineString([[v/1e6 for v in point] for point in (start,end)]).buffer(width/2e6),pad['net'],uid))
   block=None
   for shape,net,uid in shapes:
    hit=conflict(side,shape,net,set(refs))
    if hit:block=dict(object=uid,conflict=hit);break
   if block is None:
    for (a,net,uid),(b,other,oid) in itertools.combinations(shapes,2):
     if net!=other and a.distance(b)<.25-1e-8:block=dict(object=uid,conflict=oid);break
   if block:case['rejected_copper']=block
   else:
    case.update(static_candidate=True,source_translations=changes,bridges=bridges);candidates.append(case)
   cases.append(case)
  print(target,peer['ref'],'candidates',sum(c.get('static_candidate',False) for c in cases if c['target']==target and c['peer']==peer['ref']),flush=True)
assert len(pairs)<=18 and len(cases)==64*len(pairs) and sha(board)==d['board_sha256']
out=dict(status='READ-ONLY JOINT SOURCE/COPPER SCREEN; NATIVE NOT RUN; NO BOARD CHANGE',board_sha256=sha(board),dump_sha256=sha(args.dump),floorplan_sha256=sha(floor),source_sha256=sha(source_path),headers_sha256=sha(header_path),pairs=pairs,case_count=len(cases),candidate_count=len(candidates),elapsed_seconds=time.monotonic()-started,cases=cases,static_candidates=candidates)
(Path(__file__).parent/'screen.json').write_text(json.dumps(out,indent=2)+'\n');print('COMPLETE',len(cases),'cases;',len(candidates),'candidates; native NOT RUN')
