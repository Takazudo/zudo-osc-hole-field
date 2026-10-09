import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2119-outer/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='308a6e28adc821743e18bd25f96e4f71f910f6c3f04b6855fc3e8f8de4822ec5'
out=[];start=time.monotonic()
for ref,number in [('C2148','2'),('U2102','6')]:
 pad=next(p for p in d['pads'] if p['ref']==ref and p['pad']==number);group=next(g for g in d['islands']['AGND'] if pad['uuid'] in g);x,y=[v/1e6 for v in pad['xy']];bounds=[x-6,y-6,x+6,y+6];search=d
 for res in [.025]:
  events=[];t=time.monotonic();results,removed=route(search,['AGND'],res=res,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
  rows,_=copper_rows(results,'osc-jack-left','issue189-u2119-ground-links');assert not removed
  out.append({'ref':ref,'res':res,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(ref,res,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-u2119-ground-links.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
