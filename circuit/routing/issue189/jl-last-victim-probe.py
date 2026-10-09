import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jl-first-no-in3/osc-jack-left-grid-189-jl-first-no-in3-verify/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='545699bc65587169166f382910b94565615eb58231160fe4deb0f1fbc86ed912'
prior=json.loads(Path('.circuit-cache/issue189-jl-alternate-victim-probe.json').read_text())
for r in prior['proposal']['copper']:
 if r['kind']=='segment':dump['tracks'].append({'uuid':r['uuid'],'net':r['net'],'a':r['start_nm'],'b':r['end_nm'],'width':r['width_nm'],'layer':r['layer']})
 else:dump['vias'].append({'uuid':r['uuid'],'net':r['net'],'xy':r['at_nm'],'diameter':r['diameter_nm'],'drill':r['drill_nm'],'layers':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']})
events=[];start=time.monotonic()
results,removed=route(dump,['XCE094E302B27A4079262'],res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},window_mm=8,max_expansions=1600000,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
rows,links=copper_rows(results,'osc-jack-left','issue189-alternate-victim-repair');assert not removed
out={'status':'RASTER DIAGNOSTIC ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Three natively split victim groups on the alternate-layer rejected candidate. Existing minus-twelve fill guard retained. Full original native gates mandatory.','prior_probe_sha256':hashlib.sha256(Path('.circuit-cache/issue189-jl-alternate-victim-probe.json').read_bytes()).hexdigest(),'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-jl-last-victim-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
