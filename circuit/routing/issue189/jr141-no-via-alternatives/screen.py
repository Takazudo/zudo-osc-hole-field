import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jr-two-after-protected/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='3d9940791131e31d22ea65e4457ccb77d5250d629eaa2b5d3c6b03024ac3405c'
source=json.loads(Path('circuit/routing/issue189/jr141-remaining-short/result.json').read_text());selected=[t for t in source['transactions'] if t['proposal']['copper']];out=[];start=time.monotonic()
for t in selected:
 for layer in ['F.Cu','B.Cu']:
  net=t['net'];events=[];begin=time.monotonic()
  results,removed=route(d,[net],res=.025,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=[layer],layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=1,bounds_mm=t['bounds_mm'],diagnostics=events,**neck_kwargs('osc-jack-right'))
  rows,_=copper_rows(results,'osc-jack-right','issue189-jr141-no-via');assert not removed
  out.append({'net':net,'layer':layer,'bounds_mm':t['bounds_mm'],'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(net,layer,len(rows),flush=True)
Path('circuit/routing/issue189/jr141-no-via-alternatives/result.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_board_sha256':d['board_sha256'],'input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'weight':1,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
