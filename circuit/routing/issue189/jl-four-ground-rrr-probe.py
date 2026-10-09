import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='3d40f1db27f350ce063bf601cab2eeb9f6394b47da9930fca21b6bc0258d2352'
groups=dump['islands']['AGND'];main=max(groups,key=len);refs={'R8105','RB2217','R2209','R8276'};ids={p['uuid'] for p in dump['pads'] if p['ref'] in refs and p['pad']=='2'};targets=[g for g in groups if set(g)&ids];assert len(targets)==4 and main not in targets;search={**dump,'islands':{'AGND':[main,*targets]}};events=[];start=time.monotonic()
results,removed=route(search,['AGND'],res=.1,clearance=.25,signal_width=.2,signal_via_diameter=.6,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','In2.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=12,max_expansions=200000,rrr_rounds=1,rrr_max_rip=2,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-original-ground-link')
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Canonical JL135 four isolated AGND groups R8105/RB2217/R2209/R8276; one bounded RRR round, maximum two signal victims; signal layers only, original native membership and every gate mandatory. Raster only, no canonical edits.','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-jl-four-ground-rrr-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
