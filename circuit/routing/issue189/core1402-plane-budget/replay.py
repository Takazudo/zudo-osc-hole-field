"""Compare bounded ground-plane windows on saved accepted core1402; never publish."""
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path('/workspace/issue189-plane-budget');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).parent;p=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/core-complete-accepted/fresh/dump.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='5218becd38f6bb612f9a169230bd8e6657776a09fc12af5baa6113825e671ffb'
d=json.loads(p.read_text());board=ROOT/'boards/osc-core/osc-core.kicad_pcb';assert sha(board)=='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10';assert d['open_edges']==1402
pads={p['uuid']:p for p in d['pads']};groups=d['islands']['AGND'];main=max(groups,key=len);targets=[]
for group in groups:
 if group==main:continue
 ps=[pads[u] for u in group if u in pads]
 if ps:targets.append((len(group),ps[0]['ref'],ps[0]['pad'],group,ps))
targets=[t for t in targets if any(p['ref']=='U4231' and p['pad']=='7' for p in t[4])];assert len(targets)==1
out={'status':'BOUNDED READ-ONLY SCREEN; NOT REBASED ON PENDING CORE OUTPUT; NATIVE NOT RUN','dump_sha256':sha(p),'published_board_sha256':sha(board),'router_sha256':sha(ROOT/'scripts/pcbgen/grid_router.py'),'selection':'only historical expansion-limited ground group U4231.7/J900249.2/C4248.2; compare300000vs5000000bound and3vs6mm windows on identical current1402 input','transactions':[]}
for _,ref,pad,group,ps in targets:
 xs=[p['xy'][0]/1e6 for p in ps];ys=[p['xy'][1]/1e6 for p in ps];bounds=[min(xs)-6,min(ys)-6,max(xs)+6,max(ys)+6];assert (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<=2500
 for window,limit in ((3,300000),(3,5000000),(6,300000),(6,5000000)):
  trial={**d,'islands':{'AGND':[group]}};events=[];start=time.monotonic()
  paths,removed=route(trial,['AGND'],res=.0125,clearance=.25,rail_width=.3,via_diameter=.6,planes={'AGND':'In1.Cu'},allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,fill_guards={'-12V':'In3.Cu'},window_mm=6,plane_window_mm=window,max_expansions=limit,plane_max_expansions=limit,bounds_mm=bounds,diagnostics=events,log=lambda *args:None,**neck_kwargs('osc-core'))
  rows,_=copper_rows(paths,'osc-core','issue189-core1402-explicit-plane-budget-'+str(window)+'-'+str(limit));assert not removed and all(r['kind']=='via' or r['width_nm']==300000 for r in rows)
  c={'source_group':group,'pads':[[p['ref'],p['pad']] for p in ps],'plane_window_mm':window,'maximum_expansions':limit,'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'complete':bool(rows) and bool(paths) and all(r['path'] for r in paths),'diagnostics':events,'routes':paths,'proposal':{'board_sha256':sha(board),'removed_uuids':[],'copper':rows}};out['transactions'].append(c);(HERE/'explicit-budget-result.json').write_text(json.dumps(out,indent=2)+'\n');print(ref,pad,window,limit,c['complete'],len(rows),flush=True)
assert sha(board)==out['published_board_sha256'];out['status']='COMPLETE BOUNDED SCREEN; ACTUAL FUTURE REBASE AND NATIVE GATES STILL REQUIRED';(HERE/'explicit-budget-result.json').write_text(json.dumps(out,indent=2)+'\n')
