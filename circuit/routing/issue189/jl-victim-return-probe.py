import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-six-corridors/osc-jack-left-grid-189-jl-six-corridors-verify/dump.json');dump=json.loads(source.read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()=='71aaeb67dacd46cdcc7282ff005eeb1d74fdf8ec3b60b6845ed35c37eb6d665a'
events=[];start=time.monotonic()
results,removed=route(dump,['X1C571F565717425C0CCC','X862F9C0AC61EAF484CDC'],res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},window_mm=8,max_expansions=400000,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-victim-return-diagnostic');assert not removed
out={'status':'RASTER DIAGNOSTIC ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Two natively split victim groups. Search omits heuristic fill guard only to capture a possible coupled signal/rail restoration proposal. Full original native fill membership, warnings, DRC/parity and independent reload remain mandatory; no standalone signal adoption authorized by this result. Input is rejected six-corridor candidate, not canonical.','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jl-victim-return-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
