import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
p=Path('.circuit-cache/issue189-downloaded/jr-bounded-one/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='7e548f08e57c5b982c707583b537c7364939f4e336c1f2e8cfc2b2b7bf0253b6'
board=Path('boards/osc-jack-right/osc-jack-right.kicad_pcb');sha=hashlib.sha256(board.read_bytes()).hexdigest();assert sha=='7e548f08e57c5b982c707583b537c7364939f4e336c1f2e8cfc2b2b7bf0253b6'
prior=set(json.loads(Path('circuit/routing/issue189/jr146-bounded-screen/result.json').read_text())['selected_nets']);nets=signal_chunk(d,24,skip=prior);out=[];start=time.monotonic()
for net in nets:
 pads=[p for p in d['pads'] if p['net']==net];xs=[p['xy'][0]/1e6 for p in pads];ys=[p['xy'][1]/1e6 for p in pads];bounds=[min(xs)-6,min(ys)-6,max(xs)+6,max(ys)+6]
 if (bounds[2]-bounds[0])*(bounds[3]-bounds[1])>2500:
  out.append({'net':net,'status':'SKIPPED bounded area exceeds2500mm2','bounds_mm':bounds});continue
 events=[];t=time.monotonic();results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-right'))
 rows,links=copper_rows(results,'osc-jack-right','issue189-jr145-next24');assert not removed
 out.append({'net':net,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':sha,'removed_uuids':[],'copper':rows}})
 print(net,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),'seconds',out[-1]['elapsed_seconds'],flush=True)
 Path('.circuit-cache/issue189-jr145-next24.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_native_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'published_board_sha256':sha,'native_publication_equivalence':'shards-issue189-bounded-one.json','router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'selected_nets':nets,'transactions':out},indent=2)+'\n')
