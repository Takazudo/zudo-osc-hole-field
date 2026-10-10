"""Read-only source-permitted translations plus additive signal landing and ground fanout."""
import copy,hashlib,json,sys,time,uuid
from pathlib import Path
import numpy as np
ROOT=Path('/workspace/issue189-jl-layer-escape');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
from scripts.checks.routing_placement_translations import apply_translations
HERE=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');assert sha(dump)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136';d=json.loads(dump.read_text())
placements=json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements'];source=json.loads((ROOT/'design/partition/partition-input.json').read_text());headers=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())['headers'];out={'status':'STATIC SOURCE/ROUTING PROPOSALS ONLY; NO PHYSICAL PLACEMENT OR NATIVE ACCEPTANCE','board_sha256':d['board_sha256'],'dump_sha256':sha(dump),'cases':[]}
for ref in ['R8107','R8270','R8273']:
 screen=json.loads((HERE/ref/'result.json').read_text());part=screen['part'];candidates=screen['static_candidates']
 if ref=='R8107':candidates=[c for c in candidates if c['delta_mm'][0] in [0,.2,.4,.6,.8,1,1.2,1.4,1.6,1.7] and c['delta_mm'][1] in [0,.4]]
 for case in candidates:
  delta=case['delta_mm'];change={'ref':ref,'expected_source':part,'delta_mm':delta,'evidence':'issue189 read-only bounded screen'};result={'ref':ref,'translation':change};out['cases'].append(result)
  try:apply_translations(placements,source,{'schema_version':1,'translations':[change]},headers=headers)
  except ValueError as error:result.update(status='SOURCE GEOMETRY REJECTED',reason=str(error));continue
  trial=copy.deepcopy(d);moved=[p for p in trial['pads'] if p['ref']==ref];assert len(moved)==2
  signal=next(p for p in moved if p['net']!='AGND');original_xy=list(signal['xy']);shift=np.array(delta)*1e6
  for p in moved:
   p['xy']=[round(v) for v in np.array(p['xy'])+shift];p['poly']=[[round(v) for v in row] for row in np.array(p['poly'])+shift]
  bridge={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189:'+ref+':landing:'+str(delta))),'net':signal['net'],'a':original_xy,'b':signal['xy'],'width':200000,'layer':part['side']};trial['tracks'].append(bridge)
  ground=next(p for p in moved if p['net']=='AGND');trial['islands']['AGND']=[[ground['uuid']]];x,y=np.array(ground['xy'])/1e6;bounds=[x-6,y-6,x+6,y+6];events=[];start=time.monotonic()
  paths,removed=route(trial,['AGND'],planes={'AGND':'In1.Cu'},res=.0125,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,plane_window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,log=lambda *args:None)
  rows,_=copper_rows(paths,'osc-jack-left','issue189-fine-translation-'+ref+'-'+str(delta));assert not removed
  result.update(status='RASTER ONLY; ALL NATIVE/REGENERATION/RETENTION GATES STILL REQUIRED',complete=bool(rows) and bool(paths) and all(p['path'] for p in paths),elapsed_seconds=time.monotonic()-start,source_signal_bridge=bridge,diagnostics=events,routes=paths,ground_copper=rows)
  print(ref,delta,result['complete'],len(rows),flush=True);(HERE/'fine-route-result.json').write_text(json.dumps(out,indent=2)+'\n')
(HERE/'fine-route-result.json').write_text(json.dumps(out,indent=2)+'\n')
