import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/core-filtered/.circuit-cache/osc-core-grid-189-compact-refill/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5';sha='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932';net='X33ADBEB2EBFF18372234'
pads=[p for p in d['pads'] if p['net']==net];xs=[p['xy'][0]/1e6 for p in pads];ys=[p['xy'][1]/1e6 for p in pads];bounds=[min(xs)-6,min(ys)-6,max(xs)+6,max(ys)+6];assert (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<=2500
out=[];start=time.monotonic()
for layers,avoid,weight in [(['F.Cu','B.Cu'],False,1.0),(['F.Cu','B.Cu'],False,2.5),(SIGNAL_LAYERS,True,2.5)]:
 search=d
 if avoid:search={**d,'keepouts':d['keepouts']+[{'name':'experimental-via-avoid','poly':[[191325000,290400000],[191925000,290400000],[191925000,291000000],[191325000,291000000]],'layers':d['layers'],'tracks':False,'vias':True}]}
 events=[];t=time.monotonic();results,removed=route(search,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=weight,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-core'))
 rows,_=copper_rows(results,'osc-core','issue189-u1513-alternatives');assert not removed
 out.append({'layers':layers,'avoid_original_via':avoid,'weight':weight,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':sha,'removed_uuids':[],'copper':rows}});print(layers,avoid,weight,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-core-u1513-alternatives.json').write_text(json.dumps({'status':'RASTER ONLY; NOT REBASED ON PENDING POWER OUTPUT; NATIVE NOT RUN','input_native_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'published_board_sha256':sha,'native_publication_equivalence':'shards-issue189-outer-filtered.json publication_cache','elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
