"""Exclude whole local transactions near the four natively detached ground branches.

This is a bounded geometric attribution hypothesis, never native acceptance.
"""
import hashlib,json,sys
from pathlib import Path
from shapely.geometry import Point,LineString
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.copper_identity import retention
cache=ROOT/'.circuit-cache/issue189-downloaded/core-outer/.circuit-cache'
b=json.loads((cache/'osc-core-grid-shards-start/dump.json').read_text());d=json.loads((cache/'osc-core-grid-shards-fresh/dump.json').read_text())
sha='34955f1f1ca3a31d897e54d890f4d2eac1877aacc828961624226366bf3e5382'
assert b['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-core/osc-core.kicad_pcb').read_bytes()).hexdigest()
assert d['board_sha256']=='c4158ab258a43a54a154b6f1b69ea5b73ea635f606d79bdcad88bce69e22ebac'
reports=ROOT/'boards/osc-core/reports/grid-routing'
r=json.loads((reports/'shards-issue189-outer.json').read_text());p=reports/'shards-issue189-outer-copper.json'
assert not r['adopted'] and not r['native_errors'] and not r['new_warning_identities'] and r['independent_connectivity_agrees']
assert hashlib.sha256(p.read_bytes()).hexdigest()==r['copper_replay']['sha256']
delta=json.loads(p.read_text());assert not delta['removed'] and len(delta['added'])==317
ids={x['uuid'] for x in delta['added']};tracks=[t for t in d['tracks'] if t['uuid'] in ids];assert len(tracks)==317
pads={p['uuid']:p for p in d['pads']};excluded=set();clusters=[]
for split in r['split_pad_groups']:
 assert split['net']=='AGND'
 old=set(split['previously_connected_pads']);parts=[[pads[u] for u in g if u in old] for g in d['islands']['AGND'] if old.intersection(g)];main=max(parts,key=len)
 for part in parts:
  if part is main:continue
  distances={}
  for t in tracks:
   pts=[Point(p['xy']) for p in part if t['layer'] in p['layers']]
   if not pts:continue
   distance=min(p.distance(LineString([t['a'],t['b']])) for p in pts)/1e6
   distances[t['net']]=min(distance,distances.get(t['net'],float('inf')))
  near={n for n,v in distances.items() if v<=8};excluded|=near
  clusters.append({'detached_pads':[p['ref']+'.'+p['pad'] for p in part],'nearest_added_nets_mm':sorted(distances.items(),key=lambda x:x[1])[:8],'excluded_local_nets':sorted(near)})
assert len(clusters)==4 and len(excluded)==6
out={**delta,'added':[x for x in delta['added'] if x['net'] not in excluded]};out['nets']=sorted({x['net'] for x in out['added']})
assert len(out['nets'])==56 and all(x['layer'] in ('F.Cu','B.Cu') for x in out['added'])
(HERE/'copper.json').write_text(json.dumps(out,sort_keys=True)+'\n')
(HERE/'diagnosis.json').write_text(json.dumps({'status':'GEOMETRIC ATTRIBUTION HYPOTHESIS; NATIVE NOT RUN','input_board_sha256':sha,'rejected_candidate_sha256':d['board_sha256'],'source_replay_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'radius_mm':8,'clusters':clusters,'excluded_whole_nets':sorted(excluded),'remaining_nets':len(out['nets']),'remaining_segments':len(out['added']),'removed_existing_objects':0,'added_vias':0,'added_inner_tracks':0,'original_candidate_retention':retention(b,d)},indent=2)+'\n')
print('Prepared',len(out['nets']),'whole nets,',len(out['added']),'outer segments;6 local transactions excluded; native NOT RUN')
