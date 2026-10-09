"""Reserve ground and restore both native-cut victim components, with two explicit orders."""
import copy,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).resolve().parent
r=Path('.circuit-cache/issue189-downloaded/jr-rb4614');p=r/'osc-jack-right-grid-189-jr134-rb4614-2-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((r/'osc-jack-right-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jr134-rb4614-2-ground-cut/plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert set(original)<=set(joined);main=max(d['islands']['AGND'],key=len)
nets=['X67A5B6E02FA33495DE9E','XEA7C7050656B2E06AA0A'];assert all(n not in before['islands'] and len(d['islands'][n])==2 for n in nets)
search=copy.deepcopy(d);search['islands']['AGND']=([original,[u for u in joined if u not in original]] if joined==main else [joined,main]);out=[];started=time.monotonic()
for order in [nets,list(reversed(nets))]:
 events=[];t=time.monotonic();results,removed=route(search,['AGND']+order,allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'));assert not removed
 rows,_=copper_rows(results,'osc-jack-right','issue189-rb4614-joint-'+','.join(order));complete={r['net'] for r in results if r['path']}=={'AGND',*nets} and all(r['path'] for r in results)
 out.append({'signal_order':order,'complete_raster_transaction':complete,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows}});print(order,'complete',complete,'objects',len(rows),flush=True)
 if complete:break
(HERE/'result.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE ORIGINAL GROUPS AND ALL ACCEPTANCE GATES REMAIN MANDATORY','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'elapsed_seconds':time.monotonic()-started,'transactions':out},indent=2)+'\n')
if out[-1]['complete_raster_transaction']:(HERE/'proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
