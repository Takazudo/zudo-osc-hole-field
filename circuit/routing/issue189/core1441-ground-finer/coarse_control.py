import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,signal_chunk
p=Path('.circuit-cache/issue189-downloaded/core-filtered/.circuit-cache/osc-core-grid-189-compact-refill/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
board=Path('boards/osc-core/osc-core.kicad_pcb');sha=hashlib.sha256(board.read_bytes()).hexdigest();assert sha=='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932'
targets=[]
for net in ('AGND',):
 groups=d['islands'][net];main=max(groups,key=len)
 for group in groups:
  if group==main:continue
  pads=[p for p in d['pads'] if p['uuid'] in group]
  if pads:targets.append((len(group),net,group,main,pads))
targets=sorted(targets,key=lambda t:(t[0],t[1],t[4][0]['ref'],t[4][0]['pad']))[:24]
out=[];start=time.monotonic()
for _,net,group,main,pads in targets:
 xs=[p['xy'][0]/1e6 for p in pads];ys=[p['xy'][1]/1e6 for p in pads];bounds=[min(xs)-6,min(ys)-6,max(xs)+6,max(ys)+6]
 if (bounds[2]-bounds[0])*(bounds[3]-bounds[1])>2500:continue
 search={**d,'islands':{net:[group]}};events=[];t=time.monotonic()
 results,removed=route(search,[net],res=.025,clearance=.25,rail_width=.3,via_diameter=.6,planes={net:'In1.Cu'},allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-core'))
 rows,links=copper_rows(results,'osc-core','issue189-core1441-finer-ground');assert not removed;assert all(r['kind']!='segment' or r['width_nm']==300000 for r in rows)
 out.append({'net':net,'pads':[p['ref']+'.'+p['pad'] for p in pads],'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'proposal':{'board_sha256':sha,'removed_uuids':[],'copper':rows}})
 print(net,out[-1]['pads'],'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
 Path('circuit/routing/issue189/core1441-ground-finer/coarse-control.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_native_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'published_board_sha256':sha,'router_sha256':hashlib.sha256(Path('scripts/pcbgen/grid_router.py').read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
