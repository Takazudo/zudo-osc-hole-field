"""Bounded geometric diagnosis of saved native pours; never acceptance or causal proof."""
import hashlib,json,re,zipfile
from pathlib import Path
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely import make_valid
ARC=Path('/tmp/issue189-core-supply-terminal.zip');expected='0855bdbccdc250a3a273511b8d519cedc3f110a86cc0c887ac08a5f94596d8e4'
with ARC.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
folder=Path('circuit/routing/issue189/core-supply-away-from-splits');proposal=json.loads((folder/'proposal.json').read_text());cases=json.loads((folder/'rebase.json').read_text())['selected'];split=json.loads((folder/'native-split-pads.json').read_text());by_id={r['uuid']:r for r in proposal['copper']};stages={}
with zipfile.ZipFile(ARC) as z:
 for name,sha in [('start','b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'),('fresh','4f90bfc16d5e338cc31adc3a41f0da8ff8f289a24b963ab8f9c9caf9d98cec10')]:
  raw=z.read(next(n for n in z.namelist() if n.endswith(f'osc-core-grid-shards-{name}/osc-core.kicad_pcb')));assert hashlib.sha256(raw).hexdigest()==sha;text=raw.decode();zones={}
  for m in re.finditer(r'\n\t\(zone\n.*?\n\t\)',text,re.S):
   block=m.group();head=block[:400]
   if '(net "AGND")' not in head:continue
   layer=re.search(r'\(layer "([^"]+)"\)',head)[1]
   if layer not in ('F.Cu','B.Cu'):continue
   polygons=[]
   for f in re.finditer(r'\n\t\t\(filled_polygon\n.*?\n\t\t\)',block,re.S):
    xy=[(float(x),float(y)) for x,y in re.findall(r'\(xy ([\d.eE+-]+) ([\d.eE+-]+)\)',f.group())];assert len(xy)>=3;poly=make_valid(Polygon(xy));polygons.append(poly)
   zones[layer]=polygons
  assert set(zones)=={'F.Cu','B.Cu'};stages[name]=zones
results=[]
for group in split:
 pads=[p for part in group['smaller_parts'] for p in part];layer=pads[0]['layers'][0];assert all(layer in p['layers'] for p in pads);points=[(p['xy'][0]/1e6,p['xy'][1]/1e6) for p in pads];bounds=[min(p[0] for p in points)-12,min(p[1] for p in points)-12,max(p[0] for p in points)+12,max(p[1] for p in points)+12];window=box(*bounds)
 unions={name:unary_union([p.intersection(window) for p in zones[layer] if p.intersects(window)]) for name,zones in stages.items()};lost=unions['start'].difference(unions['fresh']);rank=[]
 for case in cases:
  added=[by_id[u] for u in case['uuids'] if by_id[u]['layer']==layer]
  if not added:continue
  # 0.25mm zone clearance plus half the exact segment width.
  buffers=[LineString([(c[k][0]/1e6,c[k][1]/1e6) for k in ('start_nm','end_nm')]).buffer(.25+c['width_nm']/2e6) for c in added];envelope=unary_union(buffers);overlap=lost.intersection(envelope).area
  if overlap>1e-6:rank.append({'case_pads':case['pads'],'net':case['net'],'whole_case_uuids':case['uuids'],'native_pour_loss_within_clearance_envelope_mm2':overlap})
 rank.sort(key=lambda x:(-x['native_pour_loss_within_clearance_envelope_mm2'],x['case_pads']));results.append({'original_pad_group':group['before_size'],'detached_pads':[p['ref']+'.'+p['pad'] for p in pads],'layer':layer,'bounds_mm':bounds,'local_lost_pour_area_mm2':lost.area,'whole_cases_overlapping_saved_pour_loss':rank})
result={'status':'GEOMETRIC OVERLAP DIAGNOSIS ONLY; NO COUNTERFACTUAL NATIVE CHECK; NOT CAUSAL ATTRIBUTION OR ACCEPTANCE','artifact':11666004488,'artifact_sha256':expected,'proposal_sha256':hashlib.sha256((folder/'proposal.json').read_bytes()).hexdigest(),'method':'Read exact native cached filled polygons; make_valid then clip12mm beyond detached-pad bounds; compare loss to added-track clearance envelopes. Native graph connectivity is not reconstructed.','groups':results};Path('/tmp/issue189-core-pour-loss-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
