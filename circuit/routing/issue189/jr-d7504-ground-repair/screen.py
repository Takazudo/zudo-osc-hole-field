import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jr-d7504-outer-avoid/.circuit-cache/osc-jack-right-grid-shards-fresh/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='9473dfcb383c76be2d27b5ff6ec7cf7d2d74e7cd1cbf37e64ef1df4e13aba173'
result=json.loads(Path('circuit/routing/issue189/jr-d7504-outer-avoid/native-result.json').read_text());out=[];start=time.monotonic()
for target in result['newly_split_pad_groups']:
 uid=target['pads'][0]['uuid'];pad=next(p for p in d['pads'] if p['uuid']==uid);x,y=[v/1e6 for v in pad['xy']];bounds=[x-6,y-6,x+6,y+6]
 for mode,res in [('plane',.025),('link',.025),('plane',.0125),('link',.0125)]:
  groups=[[uid]] if mode=='plane' else [[uid],max(d['islands']['AGND'],key=len)]
  search={**d,'islands':{**d['islands'],'AGND':groups}};events=[];begin=time.monotonic()
  results,removed=route(search,['AGND'],res=res,clearance=.25,rail_width=.3,via_diameter=.6,planes={'AGND':'In1.Cu'} if mode=='plane' else None,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-right'))
  rows,_=copper_rows(results,'osc-jack-right','issue189-d7504-ground-repair-'+pad['ref']);assert not removed
  out.append({'target':pad['ref']+'.'+pad['pad'],'mode':mode,'res':res,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(pad['ref'],mode,res,len(rows),flush=True)
Path('circuit/routing/issue189/jr-d7504-ground-repair/result.json').write_text(json.dumps({'status':'RASTER ONLY ON REJECTED CANDIDATE; COMBINED REPLAY MUST USE ACCEPTED141 NATIVE BASELINE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
