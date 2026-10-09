import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jr-u7509-on-ground/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='05a8d4beff64f5dee1356f679eb7d24842996d7a6b125047b8f48467e41bac26'
pad=next(p for p in d['pads'] if p['ref']=='U7506' and p['pad']=='11');groups=d['islands']['-12V'];main=max(groups,key=len);target=next(g for g in groups if pad['uuid'] in g);assert main!=target
search={**d,'islands':{'-12V':[main,target]}};x,y=[v/1e6 for v in pad['xy']];bounds=[x-6,y-6,x+6,y+6];out={}
for label,box in [('full',None),('bounded',bounds)]:
 events=[];start=time.monotonic();results,removed=route(search,['-12V'],res=.025,clearance=.25,rail_width=.25,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=box,diagnostics=events,**neck_kwargs('osc-jack-right'))
 rows,links=copper_rows(results,'osc-jack-right','issue189-existing-rail-escape');assert not removed;assert all(r['kind']=='segment' and r['width_nm']==250000 for r in rows)
 out[label]={'bounds_mm':box,'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}};print(label,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),'seconds',out[label]['elapsed_seconds'],flush=True)
Path('.circuit-cache/issue189-bounded-reference-probe.json').write_text(json.dumps({'status':'RASTER COMPARISON; NEW NATIVE INVOCATION NOT RUN','scope':'One existing U7506.11 supply escape on identical saved153input,dimensions and300000expansion/window budget. Compare full raster to12mm local frame. Full native acceptance remains mandatory for new transactions.','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'identical_proposals':out['full']['proposal']==out['bounded']['proposal'],'variants':out},indent=2)+'\n')
