import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jr-three-compatible/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='682ad2f791da4bbf4eaf76b03f3329e1c8c9765121ae44b3b2690225b7fb7120'
out=[];start=time.monotonic()
for ref in ['R7530','R7505']:
 pad=next(p for p in d['pads'] if p['ref']==ref and p['pad']=='2');group=next(g for g in d['islands']['AGND'] if pad['uuid'] in g);x,y=[v/1e6 for v in pad['xy']];bounds=[x-6,y-6,x+6,y+6];search={**d,'islands':{'AGND':[group]}}
 for res in [.025,.0125]:
  events=[];t=time.monotonic();results,removed=route(search,['AGND'],res=res,clearance=.25,rail_width=.3,via_diameter=.6,planes={'AGND':'In1.Cu'},allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-right'))
  rows,_=copper_rows(results,'osc-jack-right','issue189-d7504-ground');assert not removed
  out.append({'ref':ref,'res':res,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(ref,res,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jr-d7504-ground-probe.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
