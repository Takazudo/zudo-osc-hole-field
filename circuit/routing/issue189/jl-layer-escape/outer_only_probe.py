"""Same-input bounded JL outer-only alternatives; no cuts or native acceptance."""
import argparse,copy,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,neck_kwargs,LAYER_COST
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
source='35535749cf7f9f10dc3f2257767e3346250b3de1'
raw=subprocess.check_output(['git','show',source+':circuit/routing/issue189/jack-post-adoption-neighbours/result.json'],cwd=ROOT)
baseline=next(b for b in json.loads(raw)['boards'] if b['board']=='osc-jack-left')
assert sha(a.dump.read_bytes())==baseline['dump_sha256'];dump=json.loads(a.dump.read_text())
board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(board.read_bytes())==dump['board_sha256']==baseline['board_sha256']
cases=[c for c in baseline['cases'] if any(e['reason']=='expansion_limit' for e in c['diagnostics'])];assert len(cases)==4
result=dict(status='BOUNDED SEARCH; NO NATIVE ACCEPTANCE',source_commit=source,saved_baseline_sha256=sha(raw),board_sha256=dump['board_sha256'],dump_sha256=sha(a.dump.read_bytes()),router_sha256=sha((ROOT/'scripts/pcbgen/grid_router.py').read_bytes()),method='Same four expansion-limited obligations, same0.025mm lattice/300000expansions/6mm bounds; restrict to the two outer layers, preserving all obstacles/fill guards and existing neck rules',cases=[])
for c in cases:
 for inner in ('outer-only',):
  d=copy.deepcopy(dump);d['islands'][c['net']]=c['native_groups'];events=[];start=time.monotonic()
  routed,removed=route(d,[c['net']],allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=c['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
  assert not removed;cu,_=copper_rows(routed,'osc-jack-left','issue189-layer-'+inner+'-'+c['net']);complete=bool(cu) and bool(routed) and all(r['path'] for r in routed)
  result['cases'].append(dict(net=c['net'],inner_layer=inner,baseline=c,elapsed_seconds=time.monotonic()-start,complete=complete,diagnostics=events,routes=routed,proposal=dict(board_sha256=dump['board_sha256'],removed_uuids=[],copper=cu)))
  (HERE/'outer-only-result.json').write_text(json.dumps(result,indent=2)+'\n');print(c['net'],inner,'complete',complete,'seconds',round(time.monotonic()-start,2),flush=True)
assert sha(board.read_bytes())==dump['board_sha256']
result['status']='COMPLETE BOUNDED SEARCH; NO NATIVE ACCEPTANCE';(HERE/'outer-only-result.json').write_text(json.dumps(result,indent=2)+'\n')
