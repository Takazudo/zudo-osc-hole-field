"""Read-only restoration search for the exact six-pad native -12V split."""
import hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).resolve().parent
P=Path('/tmp/issue189-jl-u8202-rejected-dump.json')
assert hashlib.sha256(P.read_bytes()).hexdigest()=='032346a47796ab47c2e684ab065a84d69aee02d8d1e1847ab589504f55b240ab'
d=json.loads(P.read_text());assert d['board_sha256']=='4b85b31bdd8fc059f95ab8df1674e761a140cca8b9ecfdc52eabf3294ee7b391'
pad_ids={p['uuid'] for p in d['pads']}
assert sorted(len(set(g)&pad_ids) for g in d['islands']['-12V'])==[6,264]
assert sorted(map(len,d['islands']['-12V']))==[17,1002]
original=json.loads((HERE.parent/'jl117-u8202-via-branch/provisional-joint-proposal.json').read_text());assert len(original['copper'])==186 and len(original['removed_uuids'])==3
bounds=[216.5,139.68,245.705,163.3];results=[]
for layers in [['F.Cu','B.Cu'],['F.Cu','In2.Cu','In3.Cu','B.Cu']]:
 events=[];start=time.monotonic()
 paths,removed=route(d,['-12V'],res=.025,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 assert not removed
 rows,_=copper_rows(paths,'osc-jack-left','issue189-u8202-minus12-'+','.join(layers));ok=bool(rows) and bool(paths) and all(p['path'] for p in paths)
 results.append({'layers':layers,'path_found':ok,'elapsed_seconds':time.monotonic()-start,'diagnostics':events,'rail_copper':rows,'joint_proposal':{**original,'copper':original['copper']+rows}})
 (HERE/'result.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE GROUP RESTORATION AND ALL ACCEPTANCE GATES UNRUN','input_dump_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'native_candidate_sha256':d['board_sha256'],'bounds_mm':bounds,'cases':results},indent=2)+'\n')
 print(layers,ok,len(rows),flush=True)
