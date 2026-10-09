"""Reserve a permanent ground link and restore only native components split by reviewed cuts."""
import json,hashlib,time,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jl-c8142-ground');p=root/'osc-jack-left-grid-189-jl119-c8142-2-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-left-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jl119-c8142-2-ground-cut/plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert joined==max(d['islands']['AGND'],key=len) and set(original)<set(joined)
net='XA182BFDAEE78E0F2784C';cuts=set(plan['stage']['repair_source_uuids']);victim=next(g for g in before['islands'][net] if cuts.intersection(g));assert cuts<=set(victim);parts=[g for g in d['islands'][net] if set(victim).intersection(g)];assert len(parts)==2
search={**d,'islands':{**d['islands'],'AGND':[original,[u for u in joined if u not in original]],net:parts}};out=[];start=time.monotonic();nets=['AGND',net]
for layers in [['F.Cu','In2.Cu','B.Cu']]:
 events=[];begin=time.monotonic();results,removed=route(search,nets,allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-c8142-joint-finer-'+','.join(layers));assert not removed
 complete={r['net'] for r in results if r['path']}==set(nets) and all(r['path'] for r in results)
 out.append({'layers':layers,'complete_raster_transaction':complete,'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows}});print(layers,'complete',complete,'objects',len(rows),'vias',sum(r['kind']=='via' for r in rows),flush=True)
Path('circuit/routing/issue189/jl-c8142-joint-finer/result.json').write_text(json.dumps({'status':'RASTER ONLY; GROUND PARTITION FOR EXPLICIT LINK; ONLY CUT VICTIM PARTS SEARCHED; FULL ORIGINAL NATIVE GATES NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'original_victim_group':victim,'required_native_cut_parts':parts,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')

if out[-1]['complete_raster_transaction']:
 Path('circuit/routing/issue189/jl-c8142-joint-finer/proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
