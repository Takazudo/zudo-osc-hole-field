import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,split_pad_groups
root=Path('.circuit-cache/issue189-downloaded/core-reviewed/.circuit-cache');source=root/'osc-core-grid-shards-fresh/dump.json';dump=json.loads(source.read_text());before=json.loads((root/'osc-core-grid-shards-start/dump.json').read_text())
assert dump['board_sha256']=='10571178b67fb2cf05e4ffc26bf834790f48525c14e6718c59c823233b5ff285'
splits=split_pad_groups(before,dump);affected=set().union(*(set(s['previously_connected_pads']) for s in splits if s['net']=='AGND'))
groups=[g for g in dump['islands']['AGND'] if affected.intersection(g)]
# Search scope only; never use this narrowed model as the acceptance metric.
search_dump={**dump,'islands':{'AGND':groups}};events=[];start=time.monotonic()
results,removed=route(search_dump,['AGND'],res=.075,clearance=.25,rail_width=.3,via_diameter=.6,
 allowed_layers=["F.Cu","In1.Cu","In2.Cu","In3.Cu","B.Cu"],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,diagnostics=events)
rows,links=copper_rows(results,'osc-core','issue189-ground-plane-links')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Only native pieces of three previously connected AGND groups; permit AGND itself on its dedicated In1.Cu layer; all physical copper retained; full native baseline gate required','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'search_component_count':len(groups),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-core-ground-plane-links.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'removed',len(removed),'seconds',out['elapsed_seconds'])
