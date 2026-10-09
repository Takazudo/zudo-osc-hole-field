import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
source=Path('.circuit-cache/issue189-downloaded/jr-single-corridor/osc-jack-right-grid-189-jr-single-corridor-fresh/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='ec9023059ed029878f0fac386e0ce285d3b863b25203152870e7bd4fc11a8ad6'
groups=dump['islands']['AGND'];main=max(groups,key=len);targets=[]
for ref in ('R7532','R7530'):
 p=next(p for p in dump['pads'] if p['ref']==ref and p['pad']=='2');g=next(g for g in groups if p['uuid'] in g);assert g!=main;targets.append(g)
search={**dump,'islands':{'AGND':[main,*targets]}};events=[];start=time.monotonic()
results,removed=route(search,['AGND'],res=.075,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=12,max_expansions=1000000,diagnostics=events)
rows,links=copper_rows(results,'osc-jack-right','issue189-explicit-ground-repair');assert not removed
out={'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jr-ground-repair-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
