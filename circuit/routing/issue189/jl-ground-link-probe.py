import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS
source=Path('.circuit-cache/issue189-downloaded/jl-links/osc-jack-left-grid-189-jl-coupled-links-fresh/dump.json');dump=json.loads(source.read_text())
assert dump['board_sha256']=='957c12c1a4baae05e77c1f2dc22ff96cfdce299362fcb8e6c2be21d28368840c'
target=next(p['uuid'] for p in dump['pads'] if p['ref']=='C2148' and p['pad']=='2');groups=dump['islands']['AGND'];main=max(groups,key=len);cut=next(g for g in groups if target in g);assert cut!=main
# Search only the newly detached component and original main. All physical copper
# remains in the raster; this narrowed search model is never a native metric.
search_dump={**dump,'islands':{'AGND':[main,cut]}};events=[];start=time.monotonic()
results,removed=route(search_dump,['AGND'],res=.05,clearance=.25,rail_width=.3,via_diameter=.6,
 allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,diagnostics=events)
rows,links=copper_rows(results,'osc-jack-left','issue189-ground-component-link')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Only C2148.2 native island to main AGND; original stitching dimensions retained; full native baseline must gate any candidate','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jl-ground-link-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
