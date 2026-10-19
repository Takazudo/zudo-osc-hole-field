"""Review-only panel-derived allocation envelopes; never manufacturing geometry."""
from pathlib import Path
import json, hashlib, sys
P=Path(__file__).resolve().parent; R=P.parents[4]
paths=['design/grid/placements.lock.json','project/osc-hole-field/block-contracts.json','design/partition/partition.json','design/architecture-278/source-ledger.json','design/architecture-278/implementation/stage36/structure-review/view-data.json']
lock,contracts,inc,ledger,prior=[json.loads((R/p).read_text()) for p in paths]
placements=lock['placements']; boxes=[]; coverage=[]
def bounds(ps):return [min(p['x_mm'] for p in ps)-6,min(p['y_mm'] for p in ps)-6,max(p['x_mm'] for p in ps)+6,max(p['y_mm'] for p in ps)+6]
def add(name,block,xy,z,layer,status):boxes.append(dict(name=name,block=block,xy=xy,z=z,layer=layer,status=status))
for b in contracts:
 ps=[p for p in placements if p['block']==b['id']]
 row={'id':b['id'],'name':b['name'],'family':b['family'],'markers':len(ps),'boards':[],'status':'retained A01 study' if b['id']=='A01' else 'conceptual allocation; capacity UNKNOWN'}
 if b['id']=='A01':
  for q in prior['boxes']:
   if q['layer'] in ['front','middle','rear']:
    layer='jack' if 'jack' in q['name'] else 'led' if 'LED' in q['name'] else 'control' if q['layer']=='front' else q['layer']
    add(q['name'],b['id'],q['xy'],q['z'],layer,'STUDY / '+q['status']);row['boards'].append(q['name'])
 else:
  for layer,z,group in [('jack',35,[p for p in ps if p['kind']=='jack']),('control',10,[p for p in ps if p['kind'] not in ['jack','led','octave']]),('led',4.2,[p for p in ps if p['kind']=='led']),('selector',16,[p for p in ps if p['kind']=='octave'])]:
   if group:
    if layer=='selector':z=29 if b['id'] in ['O2','O4'] else 16
    name=b['id']+' '+layer;add(name,b['id'],bounds(group),[z,z+1.6],layer,'CONCEPT / fixed-panel group bounds +6mm; thickness1.6 and depth allocations only; seated datum, parts, support and routing UNKNOWN');row['boards'].append(name)
  for layer,z in [('middle',48.4),('rear',69.2)]:
   name=b['id']+' '+layer;add(name,b['id'],bounds(ps),[z,z+1.6],layer,'CONCEPT / full block panel projection +6mm; NOT package packing or routable board; overlaps expected; depth borrowed only as review proposal');row['boards'].append(name)
 coverage.append(row)
conflicts=[]
for i,a in enumerate(boxes):
 for b in boxes[i+1:]:
  if a['layer']!=b['layer']:continue
  x0=max(a['xy'][0],b['xy'][0]);y0=max(a['xy'][1],b['xy'][1]);x1=min(a['xy'][2],b['xy'][2]);y1=min(a['xy'][3],b['xy'][3])
  if x1>x0 and y1>y0 and min(a['z'][1],b['z'][1])>max(a['z'][0],b['z'][0]):conflicts.append({'a':a['name'],'b':b['name'],'layer':a['layer'],'blocks':[a['block'],b['block']],'xy':[x0,y0,x1,y1]})
D={'revision':'367f0b12b17c720e2aa9f40b23659d551abeceb8','panel_mm':[318,298],'frame':'x right, y down, z rear from panel front; layer faces are geometric only, not KiCad F.Cu/B.Cu assignments','placements':placements,'boxes':boxes,'coverage':coverage,'overlaps':conflicts,'incumbent':[{'name':b['id'],'polygon':b['outline'],'z':-b['face_z_mm'],'status':'Incumbent partition outline; sign-converted front-negative datum; not adopted in new architecture'} for b in inc['boards']],'shared_services':ledger['shared_services'],'sources':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},'rules':{'padding_mm':6,'thickness_mm':1.6,'middle_depth_mm':48.4,'rear_depth_mm':69.2,'capacity':'UNKNOWN','collision':'overlap diagnostics only; missing solids remain UNKNOWN'}}
body=json.dumps(D,indent=2)+'\n'
if '--check' in sys.argv:
 if (P/'view-data.json').read_text()!=body:raise SystemExit('FAIL stale data')
else:(P/'view-data.json').write_text(body)
print(f'PASS source extraction: {len(coverage)} blocks, {len(placements)} markers, {len(boxes)} envelopes, {len(conflicts)} nominal same-layer overlap pairs')
