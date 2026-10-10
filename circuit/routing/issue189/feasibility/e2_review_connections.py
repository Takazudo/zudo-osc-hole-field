"""Freeze20native obligations for review; no routing, placement or acceptance."""
import hashlib,itertools,json,math,zipfile
from pathlib import Path
from scripts.pcbgen.netlist import read_netlist
bid='osc-core';source=Path('boards/osc-core/osc-core.kicad_pcb');assert hashlib.sha256(source.read_bytes()).hexdigest()=='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10'
components,_=read_netlist(Path('schematic/boards/osc-core.net'));fields={c.ref:dict(c.fields) for c in components}
with zipfile.ZipFile('/tmp/issue189-core-supply-terminal.zip') as z:raw=z.read(next(n for n in z.namelist() if n.endswith('osc-core-grid-shards-start/dump.json')))
d=json.loads(raw);assert d['open_edges']==1402 and d['board_sha256']=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66';pads={p['uuid']:p for p in d['pads']}
def info(uid):
 p=pads[uid];f=fields[p['ref']];return {k:p[k] for k in ['uuid','ref','pad','net','xy','layers','locked']}|{k:f.get(k,'') for k in ['Block','Role','Island','Sensitive','PanelUid']}
def pair(net,groups):
 candidates=[]
 for i,g in enumerate(groups):
  for u in g:
   if u not in pads or fields[pads[u]['ref']].get('Block')!='E2':continue
   for j,h in enumerate(groups):
    if i==j:continue
    for v in h:
     if v in pads:candidates.append((math.dist(pads[u]['xy'],pads[v]['xy'])/1e6,u,v,i,j))
 if not candidates:return None
 dist,u,v,i,j=min(candidates);return {'net':net,'nearest_pad_distance_mm':dist,'endpoints':[info(u),info(v)],'native_groups':[{'member_count':len(g),'pad_count':sum(u in pads for u in g),'sorted_members_sha256':hashlib.sha256(('\n'.join(sorted(g))+'\n').encode()).hexdigest()} for g in [groups[i],groups[j]]],'attribution':'unknown; representative native disconnected groups, not diagnosed obstruction'}
signal=[pair(n,g) for n,g in d['islands'].items() if n not in ['AGND','+12V','-12V','+5V']];signal=[x for x in signal if x];signal.sort(key=lambda x:(x['nearest_pad_distance_mm'],x['net']));selected=[dict(x,kind='signal-short-pin-access') for x in signal[:5]]+[dict(x,kind='signal-longer-channel') for x in signal[-5:]];assert len({x['net'] for x in selected})==10
for net in ['+12V','-12V']:
 groups=d['islands'][net];main=max(groups,key=len);candidates=[]
 for g in groups:
  if g is main:continue
  e2=[u for u in g if u in pads and fields[pads[u]['ref']].get('Block')=='E2']
  if not e2:continue
  row=pair(net,[g,main]);candidates.append(row)
 candidates.sort(key=lambda x:(x['nearest_pad_distance_mm'],x['endpoints'][0]['uuid']));selected.extend(dict(x,kind='supply-feed') for x in candidates[:3])
groups=d['islands']['AGND'];main=max(groups,key=len);ground=[]
for g in groups:
 if g is main:continue
 row=pair('AGND',[g,main])
 if row:ground.append(row)
ground.sort(key=lambda x:(x['nearest_pad_distance_mm'],x['endpoints'][0]['uuid']));selected.extend(dict(x,kind='return-feed') for x in ground[:4]);assert len(selected)==20
context={s:hashlib.sha256(source.with_suffix(s).read_bytes()).hexdigest() for s in ['.kicad_pro','.kicad_dru','.kicad_sch']};result={'status':'REVIEW-ONLY20-CONNECTION SET; NO ROUTING/PLACEMENT OR NATIVE COUNTERFACTUAL RUN','source_main':'65cefd41fc39e064d38319115ad96016a1c6b71c','canonical_board_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_dump_sha256':hashlib.sha256(raw).hexdigest(),'native_filled_board_sha256':d['board_sha256'],'context_sha256':context,'native_open_edges':1402,'scope':'E2 electrical ownership;10signal/6supply/4return obligations; disjoint signalnets, shared supply/return pours mean safe batchcompatibility UNPROVEN','constraints':['Fixed318x298panel/438fixedcentres,headers,outlines,stack,electricalrules and outsidecopper preserved','No placement changes in this preparation; any future permittedfreepart changes must preserve IC/bypass/sensitive islands and be source-replayable','No fictitious EXT protection bridge, home jumpers, fabrication/order/deployment or service contact','Before any new longtrial: parent higher-model review; predeclare input/budget/minimumusefulacceptedgain; after two comparable negligible results change method','Any returnedmanualcopper must be converted to source/replay and pass originalgroup/fullwarning/DRC/parity/settled/fresh/publication gates'],'connections':selected};Path('/tmp/issue189-e2-review-connections.json').write_text(json.dumps(result,indent=2)+'\n');print([(c['kind'],[(p['ref'],p['pad']) for p in c['endpoints']],round(c['nearest_pad_distance_mm'],3)) for c in selected])
