"""Read-only diagnostic proposal for one raster-rejected path; never adopt."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,LAYER_COST,neck_kwargs
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.dump)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
d=json.loads(a.dump.read_text());board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(board)==d['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
saved=json.loads((HERE/'guarded-case.json').read_text());case=saved['case'];assert case['net']=='X8DEDD995BB5D1F1ACF65' and case['domain']=='in3'
assert sha(ROOT/'scripts/pcbgen/grid_router.py')==saved['router_sha256']
result=dict(status='DISPOSABLE NATIVE DIAGNOSTIC ONLY; NOT ELIGIBLE OR ADOPTED',source_main_commit='16a248fc1dee8a68f416207fa3fd098e4e0d6490',board_sha256=sha(board),dump_sha256=sha(a.dump),router_sha256=saved['router_sha256'],cases=[])
for label,guards in [('production-guard',{'-12V':'In3.Cu'}),('native-diagnostic-only',{})]:
 trial=copy.deepcopy(d);trial['islands'][case['net']]=case['native_groups'];events=[];start=time.monotonic()
 paths,removed=route(trial,[case['net']],allowed_layers=['F.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.05,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=case['bounds_mm'],fill_guards=guards,diagnostics=events,**neck_kwargs('osc-jack-left'))
 assert not removed
 rows,_=copper_rows(paths,'osc-jack-left','issue189-jl-d8208-native-diagnostic')
 complete=bool(rows) and bool(paths) and all(p['path'] for p in paths)
 result['cases'].append(dict(label=label,fill_guards=guards,elapsed_seconds=time.monotonic()-start,complete=complete,diagnostics=events,routes=paths,proposal=dict(board_sha256=sha(board),removed_uuids=[],copper=rows)))
 print(label,complete,len(rows),flush=True)
assert not result['cases'][0]['complete'] and any(e['reason']=='fill_guard_disconnection' for e in result['cases'][0]['diagnostics'])
assert result['cases'][0]['diagnostics']==case['diagnostics']
assert result['cases'][1]['complete']
proposal=HERE/'proposal.json';proposal.write_text(json.dumps(result['cases'][1]['proposal'],indent=2)+'\n')
rows=result['cases'][1]['proposal']['copper'];vias=sum(r['kind']=='via' for r in rows)
assert sha(board)==d['board_sha256'] and sha(ROOT/'scripts/pcbgen/grid_router.py')==saved['router_sha256']
plan=dict(board='osc-jack-left',input_board_sha256=sha(board),name='189-jl118-d8208-native-diagnostic',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope=f'Read-only diagnostic of one raster -12V guard rejection: {len(rows)-vias}segments/{vias}vias,0cuts/moves. Production routing guard unchanged. No original group split allowed in native KiCad; mandatory native DRC/parity/fresh/warning/copper retention gates remain. No publication.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(ROOT/'circuit/routing/issue189/jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('Disposable proposal',sha(proposal),'native NOT RUN')
