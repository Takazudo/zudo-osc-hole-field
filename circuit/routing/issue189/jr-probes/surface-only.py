import json,time,hashlib,sys,resource
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
source=Path('.circuit-cache/issue189-downloaded/jr-dump.json');dump=json.loads(source.read_text())
events=[];start=time.monotonic();net='XC13372BA423E9AD7226E'
results,removed=route(dump,[net],res=.05,clearance=.2,signal_width=.2,signal_via_diameter=.6,
    allowed_layers=['B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,
    grow={n:.05 for n in [*RAILS,'AGND']},fill_guards={'-12V':'In3.Cu'},
    rip_only={n for n in {p['net'] for p in dump['pads']} if n not in (*RAILS,'AGND') and all('B.Cu' in p['layers'] for p in dump['pads'] if p['net']==n)},rrr_rounds=1,rrr_max_rip=4,max_expansions=100000,diagnostics=events,
    **neck_kwargs('osc-jack-right'))
rows,links=copper_rows(results,'osc-jack-right','issue189-surface-local')
out={'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
     'net':net,'res_mm':.05,'elapsed_seconds':time.monotonic()-start,
     'peak_python_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'results':results,'diagnostics':events,'links':links,
     'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':removed,'copper':rows}}
Path('.circuit-cache/issue189-downloaded/jr-surface-local.json').write_text(json.dumps(out,indent=2)+'\n')
print('proposal',len(rows),'copper objects;',len(removed),'removed;',out['elapsed_seconds'],'seconds')
