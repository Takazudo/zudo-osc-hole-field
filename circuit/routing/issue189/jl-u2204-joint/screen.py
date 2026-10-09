"""Reserve explicit ground copper while restoring a victim on the exact native cut input."""
import json,hashlib,time,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jl-u2204-ground-cut');p=root/'osc-jack-left-grid-189-jl121-u2204-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-left-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jl121-ground-cut-screen/u2204-plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert joined==max(d['islands']['AGND'],key=len) and set(original)<set(joined)
search={**d,'islands':{**d['islands'],'AGND':[original,[u for u in joined if u not in original]]}};out=[];start=time.monotonic();nets=['AGND','X1350D6DDB5A475CC1BA8']
for layers in [['F.Cu','B.Cu'],['F.Cu','In2.Cu','B.Cu']]:
 events=[];begin=time.monotonic();results,removed=route(search,nets,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-u2204-joint-'+','.join(layers));assert not removed
 complete={r['net'] for r in results if r['path']}==set(nets) and all(r['path'] for r in results)
 out.append({'layers':layers,'complete_raster_transaction':complete,'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows}});print(layers,'complete',complete,'objects',len(rows),'vias',sum(r['kind']=='via' for r in rows),flush=True)
Path('circuit/routing/issue189/jl-u2204-joint/result.json').write_text(json.dumps({'status':'RASTER ONLY; GROUND GROUP ARTIFICIALLY PARTITIONED TO REQUIRE PERMANENT LINK; FULL ORIGINAL NATIVE ACCEPTANCE NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
