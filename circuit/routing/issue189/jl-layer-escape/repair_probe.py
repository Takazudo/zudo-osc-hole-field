"""Bounded full-width repair of the exact C2148 split on rejected In2 copper."""
import argparse, copy, hashlib, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('native_root',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=a.native_root/'osc-jack-left-grid-189-local-base/dump.json'
candidate=a.native_root/'osc-jack-left-grid-189-jl118-u2119-in2-only/dump.json'
b=json.loads(base.read_text());d=json.loads(candidate.read_text())
assert b['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
assert d['board_sha256']=='19f46a21e720c2d58156dedad30ea95d12f6d01047aac781cc3d115588297afe'
target=next(p for p in d['pads'] if p['ref']=='C2148' and p['pad']=='2')
source=next(g for g in d['islands']['AGND'] if target['uuid'] in g)
main=max(d['islands']['AGND'],key=len)
assert source==[target['uuid']] and len(main)==1386
assert any(set(source+main)==set(g) for g in b['islands']['AGND'])
x,y=[v/1e6 for v in target['xy']];bounds=[x-6,y-6,x+6,y+6]
result=dict(status='BOUNDED RESTORATION SCREEN; NATIVE NOT RUN',input_dump_sha256=sha(candidate),
    original_board_sha256=b['board_sha256'],rejected_board_sha256=d['board_sha256'],trials=[])
for mode,window in [('direct',3),('plane',3),('plane',6)]:
    trial=copy.deepcopy(d);trial['islands']['AGND']=[source,main] if mode=='direct' else [source]
    events=[];start=time.monotonic()
    routes,removed=route(trial,['AGND'],planes={'AGND':'In1.Cu'} if mode=='plane' else None,
        allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],
        clearance=.25,rail_width=.3,via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},
        window_mm=6,plane_window_mm=window,max_expansions=300000,bounds_mm=bounds,
        fill_guards={'-12V':'In3.Cu'},diagnostics=events)
    assert not removed
    copper,_=copper_rows(routes,'osc-jack-left','issue189-jl-in2-return-'+mode+str(window))
    complete=bool(copper) and bool(routes) and all(r['path'] for r in routes)
    assert all(r['net']=='AGND' and (r['kind']=='via' or r['width_nm']==300000) for r in copper)
    result['trials'].append(dict(mode=mode,plane_window_mm=window,complete=complete,
        elapsed_seconds=time.monotonic()-start,diagnostics=events,routes=routes,copper=copper))
    (HERE/'repair-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(mode,window,'complete',complete,'objects',len(copper),flush=True)
result['status']='COMPLETE BOUNDED RESTORATION SCREEN; NATIVE NOT RUN'
(HERE/'repair-result.json').write_text(json.dumps(result,indent=2)+'\n')
