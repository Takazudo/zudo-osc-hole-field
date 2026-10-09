import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-local/osc-jack-left-grid-189-jl-local-cut/dump.json');dump=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='609672968812b5bc443f8c4caf1e398b67a9c903d97e9bd1acbe32cb50b0b466'
fresh_path=Path('.circuit-cache/issue189-downloaded/jl-leaf-adopt/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');fresh=json.loads(fresh_path.read_text())
leaf='be3bc2d8-bbd6-5369-a979-582f4c429a5a';dump['tracks'] += [t for t in fresh['tracks'] if t['uuid']==leaf]
# Search-only model: original native cut, plus the separately adopted remote rail link.
# Original-baseline native validation remains mandatory; no computed islands used as acceptance.
dump['islands']['-12V']=fresh['islands']['-12V']
events=[];start=time.monotonic();nets=['X632AF8DD6216ED26A96D','X77D770C85A6A9FAC0452']
results,removed=route(dump,nets,res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,
 allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},
 fill_guards={'-12V':'In3.Cu'},window_mm=8,max_expansions=1000000,diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-no-in3');original=json.load(open('circuit/routing/issue189/jl-coupled-proposal.json'))
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Original three-object local cut with In3.Cu excluded from signal search; fresh accepted leaf added to physical search model; no additional removals','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fresh_dump_sha256':hashlib.sha256(fresh_path.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':fresh['board_sha256'],'removed_uuids':original['removed_uuids'],'copper':rows}}
assert not removed
Path('.circuit-cache/issue189-jl-no-in3-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
