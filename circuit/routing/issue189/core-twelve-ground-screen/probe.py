import json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
source=Path('.circuit-cache/issue189-downloaded/core-reviewed/.circuit-cache/osc-core-grid-shards-start/dump.json');dump=json.loads(source.read_text());assert dump['board_sha256']=='34955f1f1ca3a31d897e54d890f4d2eac1877aacc828961624226366bf3e5382'
rank_path=Path(__file__).with_name('ranking.json');rank=json.loads(rank_path.read_text());assert rank['input_board_sha256']==dump['board_sha256'];groups=dump['islands']['AGND'];main=max(groups,key=len);targets=[next(g for g in groups if set(g)==set(e['members'])) for e in rank['groups'][:12]];assert main not in targets;search={**dump,'islands':{'AGND':[main,*targets]}};events=[];start=time.monotonic()
results,removed=route(search,['AGND'],res=.075,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=12,max_expansions=1000000,diagnostics=events)
rows,links=copper_rows(results,'osc-core','issue189-twelve-original-ground-links');assert not removed
out={'status':'RASTER ONLY; NATIVE NOT RUN; NOT ELIGIBLE','scope':'Twelve existing core AGND groups, ranked by nearest main-group pad distance. Distance is not route evidence. Original1509 input,zero removals; reconcile with active filtered core result before native replay. Full native gates mandatory.', 'ranking_sha256':hashlib.sha256(rank_path.read_bytes()).hexdigest(),'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':dump['board_sha256'],'removed_uuids':[],'copper':rows}}
Path('.circuit-cache/issue189-core-twelve-ground-probe.json').write_text(json.dumps(out,indent=2)+'\n');print('paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'copper',len(rows),'seconds',out['elapsed_seconds'])
