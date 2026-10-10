"""Bounded JL118 signal obligations outside the last ten cut-neighbour cases."""
import copy,hashlib,itertools,json,math,subprocess,sys,time
from pathlib import Path
ROOT=Path('/workspace/issue189-jl-layer-escape');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,LAYER_COST,neck_kwargs
HERE=Path(__file__).parent
source=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
d=json.loads(source.read_text());board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(board)==d['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
historical=subprocess.check_output(['git','show','35535749cf7f9f10dc3f2257767e3346250b3de1:circuit/routing/issue189/jack-post-adoption-neighbours/result.json'],cwd=ROOT)
excluded={c['net'] for b in json.loads(historical)['boards'] if b['board']=='osc-jack-left' for c in b['cases']};assert len(excluded)==10
pads={p['uuid']:p for p in d['pads']};choices=[]
for net,groups in sorted(d['islands'].items()):
 if net in {*RAILS,'AGND',*excluded} or len(groups)<2:continue
 pairs=[]
 for gi,gj in itertools.combinations(range(len(groups)),2):
  for u,v in itertools.product([u for u in groups[gi] if u in pads],[v for v in groups[gj] if v in pads]):
   pairs.append((math.dist(pads[u]['xy'],pads[v]['xy'])/1e6,u,v,gi,gj))
 if not pairs:continue
 distance,u,v,gi,gj=min(pairs);endpoints=[pads[u],pads[v]];xy=[[v/1e6 for v in p['xy']] for p in endpoints]
 if max(abs(xy[0][i]-xy[1][i]) for i in (0,1))>60:continue
 bounds=[min(p[0] for p in xy)-6,min(p[1] for p in xy)-6,max(p[0] for p in xy)+6,max(p[1] for p in xy)+6]
 choices.append(dict(net=net,source_group_indices=[gi,gj],native_groups=[groups[gi],groups[gj]],endpoints=[{k:p[k] for k in ('uuid','ref','pad','net','xy','layers')} for p in endpoints],pad_distance_mm=distance,bounds_mm=bounds))
choices=sorted(choices,key=lambda c:(c['pad_distance_mm'],c['net']))[6:18];assert len(choices)==12
baseline=json.loads((HERE/'result.json').read_text());limited={(c['net'],c['domain']) for c in baseline['cases'] if any(e['reason']=='expansion_limit' for e in c['diagnostics'])};assert len(limited)==18
out=dict(astar_weight=2.5,baseline_result_sha256=sha(HERE/'result.json'),status='BOUNDED SEARCH; NATIVE NOT RUN',board_sha256=d['board_sha256'],dump_sha256=sha(source),router_sha256=sha(ROOT/'scripts/pcbgen/grid_router.py'),excluded_previous_nets=sorted(excluded),maximum_axis_span_mm=60,lattice_mm=.05,selection_offset=6,selection_count=12,historical_selection_sha256=hashlib.sha256(historical).hexdigest(),selection='Next twelve current signal obligations after the prior six, outside ten cut-neighbour nets, maximum60mm axis span; distance is heuristic only',cases=[])
for case in choices:
 for label,layers in [('four-layer',['F.Cu','In2.Cu','In3.Cu','B.Cu']),('in2',['F.Cu','In2.Cu','B.Cu']),('in3',['F.Cu','In3.Cu','B.Cu'])]:
  if (case['net'],label) not in limited:continue
  trial=copy.deepcopy(d);trial['islands'][case['net']]=case['native_groups'];events=[];start=time.monotonic()
  routed,removed=route(trial,[case['net']],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.05,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,weight=2.5,max_expansions=300000,bounds_mm=case['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
  assert not removed
  copper,_=copper_rows(routed,'osc-jack-left','issue189-jl-next-long-weighted-'+case['net']+'-'+label)
  complete=bool(copper) and bool(routed) and all(r['path'] for r in routed)
  out['cases'].append(dict(**case,domain=label,elapsed_seconds=time.monotonic()-start,complete=complete,diagnostics=events,routes=routed,proposal=dict(board_sha256=d['board_sha256'],removed_uuids=[],copper=copper)))
  (HERE/'weighted-result.json').write_text(json.dumps(out,indent=2)+'\n');print(case['net'],label,'complete',complete,'objects',len(copper),flush=True)
assert sha(board)==d['board_sha256'] and sha(ROOT/'scripts/pcbgen/grid_router.py')==out['router_sha256']
out['status']='COMPLETE BOUNDED SEARCH; NATIVE NOT RUN';(HERE/'weighted-result.json').write_text(json.dumps(out,indent=2)+'\n')
