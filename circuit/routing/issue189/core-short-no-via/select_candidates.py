"""Pin short outer-layer signal links without vias; future rebase/native gates required."""
import json,hashlib,math
from pathlib import Path
from shapely.geometry import LineString
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
source=HERE.parent/'core1441-no-via/result.json';data=json.loads(source.read_text());rows=[];selected=[]
for t in data['transactions']:
 c=t['proposal']['copper']
 if not 1<=len(c)<=4 or not all(r['kind']=='segment' and r['layer'] in ['F.Cu','B.Cu'] and r['width_nm'] in [150000,200000] for r in c):continue
 length=sum(math.dist(r['start_nm'],r['end_nm'])/1e6 for r in c)
 if length>4:continue
 selected.append({'net':t['net'],'layer':t['layer'],'objects':len(c),'length_mm':length,'source_islands':[r['island'] for r in t['results'] if r['path']]});rows.extend(c)
assert len(rows)==12 and len(selected)==7 and len({r['uuid'] for r in rows})==len(rows)
distances=[]
for i,a in enumerate(rows):
 for b in rows[:i]:
  if a['net']==b['net'] or a['layer']!=b['layer']:continue
  distances.append((LineString([a['start_nm'],a['end_nm']]).distance(LineString([b['start_nm'],b['end_nm']]))-(a['width_nm']+b['width_nm'])/2)/1e6)
minimum=min(distances);assert minimum>=.25
sha='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932';assert all(t['proposal']['board_sha256']==sha for t in data['transactions'])
p=HERE/'proposal-original.json';p.write_text(json.dumps({'board_sha256':sha,'removed_uuids':[],'copper':rows},indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'status':'SAVED ORIGINAL INPUT ONLY; WAIT FOR CORE37936741388; NOT REBASED OR NATIVE VALIDATED','source_result_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_board_sha256':sha,'rule':'1to4outer segments, total length<=4mm per case; no vias/cuts; conservative0.25mm new/new foreign-net clearance','selected':selected,'objects':len(rows),'minimum_new_cross_net_gap_mm':minimum,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n');print('Saved',len(rows),'objects across',len(selected),'nets; minimum gap',minimum,'native NOT RUN')
