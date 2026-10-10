"""Bounded full-width repair of the exact C7523/R7331 split on rejected In2 copper."""
import argparse, copy, hashlib, json, sys, time
from pathlib import Path
ROOT=Path('/workspace/issue189-jr131-next');sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('native_root',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=a.native_root/'base.json'
candidate=a.native_root/'candidate.json'
b=json.loads(base.read_text());d=json.loads(candidate.read_text())
assert b['board_sha256']=='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965'
assert d['board_sha256']=='ced4240944e5f16ebcf8b3c17ebf29347a2fe57c920530aa31c5fa39c0786230'
target=next(p for p in d['pads'] if p['ref']=='C7523' and p['pad']=='2')
source=next(g for g in d['islands']['AGND'] if target['uuid'] in g)
main=max(d['islands']['AGND'],key=len)
assert len(source)==2 and len(main)==1164
assert sha(candidate)=='d6a3925d1495bd6ba9e5234868d89e22fd602ad4eb40adbf0676cf49d35044ca'
assert any(set(source+main)==set(g) for g in b['islands']['AGND'])
xy=[[v/1e6 for v in p['xy']] for p in d['pads'] if p['uuid'] in source];bounds=[min(p[0] for p in xy)-6,min(p[1] for p in xy)-6,max(p[0] for p in xy)+6,max(p[1] for p in xy)+6]
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
    copper,_=copper_rows(routes,'osc-jack-right','issue189-jr-in2-return-'+mode+str(window))
    complete=bool(copper) and bool(routes) and all(r['path'] for r in routes)
    assert all(r['net']=='AGND' and (r['kind']=='via' or r['width_nm']==300000) for r in copper)
    result['trials'].append(dict(mode=mode,plane_window_mm=window,complete=complete,
        elapsed_seconds=time.monotonic()-start,diagnostics=events,routes=routes,copper=copper))
    (HERE/'repair-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(mode,window,'complete',complete,'objects',len(copper),flush=True)
result['status']='COMPLETE BOUNDED RESTORATION SCREEN; NATIVE NOT RUN'
(HERE/'repair-result.json').write_text(json.dumps(result,indent=2)+'\n')
