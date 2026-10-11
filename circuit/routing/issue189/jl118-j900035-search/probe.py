"""Search-only via exclusions for two native rejected JL routes; no physical edits."""
import copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path('/workspace/issue189-jl-layer-escape');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,LAYER_COST,neck_kwargs
HERE=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');assert sha(dump)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
d=json.loads(dump.read_text());board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(board)==d['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
screen=ROOT/'circuit/routing/issue189/jl118-u8215-bounded/weighted-5m-result.json';s=json.loads(screen.read_text());assert s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py');case=next(c for c in s['cases'] if c['net']=='XB8780C34DCDC50D9A9BA' and c['domain']=='in3')
out={'status':'BOUNDED SCREEN; NO NATIVE ACCEPTANCE','board_sha256':sha(board),'dump_sha256':sha(dump),'router_sha256':s['router_sha256'],'baseline_screen_sha256':sha(screen),'cases':[]}
for label,rect in [('shared-first',[262.925,111.425,263.225,111.725]),('near-last',[262.7,124.0,263.175,124.475]),('jack-corridor',[253,123,267,130])]:
 for domain,layers in [('in2',['F.Cu','In2.Cu','B.Cu']),('in3',['F.Cu','In3.Cu','B.Cu']),('four-layer',['F.Cu','In2.Cu','In3.Cu','B.Cu'])]:
  trial=copy.deepcopy(d);trial['islands'][case['net']]=case['native_groups'];x0,y0,x1,y1=rect;keepout={'name':'search-only-J900035-via-exclusion','layers':layers,'poly':[[round(x*1e6),round(y*1e6)] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]],'tracks':False,'vias':True};trial['keepouts'].append(keepout);events=[];start=time.monotonic()
  paths,removed=route(trial,[case['net']],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,weight=2.5,max_expansions=5000000,bounds_mm=case['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,log=lambda *args:None,**neck_kwargs('osc-jack-left'))
  assert not removed
  rows,_=copper_rows(paths,'osc-jack-left','issue189-jl-J900035-'+label+'-'+domain);complete=bool(rows) and bool(paths) and all(r['path'] for r in paths)
  out['cases'].append({'exclusion':label,'domain':domain,'search_only_keepout':keepout,'elapsed_seconds':time.monotonic()-start,'complete':complete,'diagnostics':events,'routes':paths,'proposal':{'board_sha256':sha(board),'removed_uuids':[],'copper':rows}});(HERE/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(label,domain,complete,len(rows),flush=True)
assert sha(board)==d['board_sha256'];out['status']='COMPLETE BOUNDED SCREEN; NO NATIVE ACCEPTANCE';(HERE/'result.json').write_text(json.dumps(out,indent=2)+'\n')
