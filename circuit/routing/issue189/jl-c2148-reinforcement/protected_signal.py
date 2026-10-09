"""Route signal around proposed full-width redundant ground copper; no native claim."""
import json,time,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2119-ground-corridor/.circuit-cache/osc-jack-left-grid-shards-start/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='55a3edef21878d3e89ac9a02b0264f27d7a97da0d666648b5ffc27e47afde17d';source=json.load(open('circuit/routing/issue189/jl-c2148-reinforcement/result.json'));bounds=json.load(open('circuit/routing/issue189/jl-u2119-via-avoid/result.json'))['bounds_mm'];net='X632AF8DD6216ED26A96D';out=[];start=time.monotonic()
for t in source['transactions']:
 ground=t['proposal']['copper']
 if not ground:continue
 search={**d,'tracks':list(d['tracks']),'vias':list(d['vias'])}
 for c in ground:
  if c['kind']=='segment':search['tracks'].append({'uuid':c['uuid'],'net':c['net'],'a':c['start_nm'],'b':c['end_nm'],'width':c['width_nm'],'layer':c['layer']})
  else:search['vias'].append({'uuid':c['uuid'],'net':c['net'],'xy':c['at_nm'],'diameter':c['diameter_nm'],'drill':c['drill_nm']})
 events=[];begin=time.monotonic();results,removed=route(search,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-c2148-reinforced-signal');assert not removed
 out.append({'ground_mode':t['mode'],'ground_res':t['res'],'ground_objects':len(ground),'signal_objects':len(rows),'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':ground+rows if rows else []}});print(t['mode'],t['res'],'ground',len(ground),'signal',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-c2148-reinforced-signal.json').write_text(json.dumps({'status':'ADDITIVE RASTER ONLY; ORIGINAL NATIVE MEMBERSHIP REMAINS MANDATORY ACCEPTANCE BASELINE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
