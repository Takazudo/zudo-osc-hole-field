import json,time,hashlib,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,split_pad_groups
root=Path('.circuit-cache/issue189-downloaded/jr-return-aware');source=root/'osc-jack-right-grid-189-jr-return-aware/dump.json';dump=json.loads(source.read_text());before=json.loads((root/'osc-jack-right-grid-189-local-base/dump.json').read_text());splits=split_pad_groups(before,dump);records=[];all_rows=[];start=time.monotonic();physical=copy.deepcopy(dump)
for net,width,layers in [('-12V',.4,SIGNAL_LAYERS)]:
 affected=set().union(*(set(s['previously_connected_pads']) for s in splits if s['net']==net));groups=[g for g in dump['islands'][net] if affected.intersection(g)]
 search={**physical,'islands':{net:groups}};events=[]
 results,removed=route(search,[net],res=.05,clearance=.25,rail_width=width,via_diameter=.6,
  allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=12,max_expansions=1000000,diagnostics=events)
 assert not removed
 rows,links=copper_rows(results,'osc-jack-right','issue189-return-aware-restore-'+net);all_rows+=rows
 records.append({'net':net,'results':results,'diagnostics':events,'links':links,'copper_count':len(rows)})
 for row in rows:
  if row['kind']=='segment':physical['tracks'].append({'uuid':row['uuid'],'net':row['net'],'a':row['start_nm'],'b':row['end_nm'],'width':row['width_nm'],'layer':row['layer']})
  else:physical['vias'].append({'uuid':row['uuid'],'net':row['net'],'xy':row['at_nm'],'diameter':row['diameter_nm'],'drill':row['drill_nm']})
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Repair only native pieces of originally connected supply/AGND groups; AGND may use its dedicated In1 plane; no signal on In1; all physical copper retained','elapsed_seconds':time.monotonic()-start,'records':records,'repair_rows':all_rows}
Path('.circuit-cache/issue189-jr-return-aware-restore.json').write_text(json.dumps(out,indent=2)+'\n');print('added',len(all_rows),'seconds',out['elapsed_seconds'])
