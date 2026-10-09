import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
source=Path('.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='3d40f1db27f350ce063bf601cab2eeb9f6394b47da9930fca21b6bc0258d2352'
search=dump;events=[];start=time.monotonic()
results,removed=route(search,['AGND'],res=.075,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=12,max_expansions=1000000,diagnostics=events)
rows,links=copper_rows(results,'osc-jack-left','issue189-original-ground-link');assert not removed
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Canonical JL135 existing AGND groups; full original copper retained and native gates mandatory. Dedicated ground layer allowed only for AGND.','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jl-original-ground-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
