"""Try additive ground reinforcement before adding the signal that split its pour."""
import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
p=Path('.circuit-cache/issue189-downloaded/jl-u2119-ground-corridor/.circuit-cache/osc-jack-left-grid-shards-start/dump.json');d=json.loads(p.read_text());assert d['board_sha256']=='55a3edef21878d3e89ac9a02b0264f27d7a97da0d666648b5ffc27e47afde17d';uid='773b4d25-1c84-52db-b24e-e7cfe563c376';pad=next(p for p in d['pads'] if p['uuid']==uid);group=next(g for g in d['islands']['AGND'] if uid in g);x,y=[v/1e6 for v in pad['xy']];bounds=[x-6,y-6,x+6,y+6];out=[];start=time.monotonic()
for mode,res in [('plane',.025),('link',.025),('plane',.0125),('link',.0125)]:
 groups=[[uid]] if mode=='plane' else [[uid],[u for u in group if u!=uid]]
 search={**d,'islands':{**d['islands'],'AGND':groups}};events=[];begin=time.monotonic();results,removed=route(search,['AGND'],res=res,clearance=.25,rail_width=.3,via_diameter=.6,planes={'AGND':'In1.Cu'} if mode=='plane' else None,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-c2148-reinforcement');assert not removed
 out.append({'mode':mode,'res':res,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows}});print(mode,res,'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-c2148-reinforcement.json').write_text(json.dumps({'status':'RASTER ONLY; ARTIFICIAL SOURCE/GROUP SPLIT FOR REDUNDANT GROUND SEARCH ONLY; ORIGINAL NATIVE MEMBERSHIP MUST REMAIN THE ACCEPTANCE BASELINE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
