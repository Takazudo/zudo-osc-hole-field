"""Remove short supply transactions near observed ground splits; native gates remain mandatory."""
import hashlib,json,math
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
source=HERE.parent/'core1441-rail-screen';files=[source/'first24.json',source/'rest.json']
sha='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932'
dump_path=ROOT/'.circuit-cache/issue189-downloaded/core-short-power/.circuit-cache/osc-core-grid-shards-start/dump.json';dump=json.loads(dump_path.read_text());rejection_path=HERE.parent/'core-short-power/rejection.json';rejection=json.loads(rejection_path.read_text())
labels={name for group in rejection['ground_splits'] for piece in group['smaller_pieces'] for name in piece};pads=[p for p in dump['pads'] if p['ref']+'.'+p['pad'] in labels];assert len(pads)==len(labels)
shapes=[(p['ref']+'.'+p['pad'],Polygon(p['poly']) if p['poly'] else Point(p['xy'])) for p in pads]
rows=[];selected=[];excluded=[];all_rows=[]
for file in files:
 data=json.loads(file.read_text());assert data['published_board_sha256']==sha
 for t in data['transactions']:
  c=t['proposal']['copper']
  if not 1<=len(c)<=2 or not all(r['kind']=='segment' and r['width_nm']==250000 for r in c):continue
  length=sum(math.dist(r['start_nm'],r['end_nm'])/1e6 for r in c)
  if length>2:continue
  all_rows.extend(c)
  distances=[((LineString([r['start_nm'],r['end_nm']]).distance(poly)-r['width_nm']/2)/1e6,name) for r in c for name,poly in shapes]
  distance,name=min(distances)
  item={'net':t['net'],'pads':t['pads'],'objects':len(c),'nearest_regressed_ground_pad':name,'minimum_gap_mm':distance,'uuids':[r['uuid'] for r in c]}
  if distance<3:excluded.append(item)
  else:selected.append(item);rows.extend(c)
assert len(all_rows)==135 and len(selected)+len(excluded)==109
original=json.loads((HERE.parent/'core-short-power/proposal.json').read_text())['copper'];assert {r['uuid'] for r in all_rows}=={r['uuid'] for r in original if r['net'] in ['+12V','-12V']}
out=HERE/'proposal-original.json';out.write_text(json.dumps({'board_sha256':sha,'removed_uuids':[],'copper':rows},indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'status':'HEURISTIC SUBSET ONLY; NOT REBASED; WAIT FOR CORE37936741388; NATIVE NOT RUN','source_sha256':sha,'native_rejection_run':37925863664,'native_rejection_sha256':hashlib.sha256(rejection_path.read_bytes()).hexdigest(),'native_input_dump_sha256':hashlib.sha256(dump_path.read_bytes()).hexdigest(),'rule':'Retain original1or2segment supply transactions only if at least3mm from every pad in the smaller native-split AGND pieces; omit all four ground fanouts. Proximity is not causal attribution or proof of safety.','selected':selected,'excluded':excluded,'objects':len(rows),'proposal_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')
print('Selected',len(selected),'targets',len(rows),'segments; excluded',len(excluded),'targets; native NOT RUN')
