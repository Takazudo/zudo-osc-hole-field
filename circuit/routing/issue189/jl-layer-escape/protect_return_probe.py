"""Stronger search-only B.Cu exclusions around the proven C2148 split."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,neck_kwargs,LAYER_COST
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(a.dump.read_text())
assert d['board_sha256']==sha(ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb')=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
assert sha(a.dump)=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
original=json.loads((HERE/'result.json').read_text())
c=next(c for c in original['cases'] if c['complete'])
assert c['net']=='X632AF8DD6216ED26A96D' and c['inner_layer']=='In2.Cu'
pad=next(p for p in d['pads'] if p['ref']=='C2148' and p['pad']=='2');x,y=pad['xy']
out=dict(status='BOUNDED SEARCH; NATIVE NOT RUN',board_sha256=d['board_sha256'],dump_sha256=sha(a.dump),
    reason='Native In2 proposal splits C2148.2 AGND. Add only search-model B.Cu exclusion; no physical keepout or placement changes.',trials=[])
for radius in (.8,1.2,1.6):
    trial=copy.deepcopy(d);trial['islands'][c['net']]=c['baseline']['native_groups'];h=round(radius*1e6)
    trial['keepouts'].append(dict(name='search-only C2148 native return protection',poly=[[x-h,y-h],[x+h,y-h],[x+h,y+h],[x-h,y+h]],layers=['B.Cu'],tracks=True,vias=True))
    events=[];start=time.monotonic()
    routes,removed=route(trial,[c['net']],allowed_layers=['F.Cu','In2.Cu','B.Cu'],layer_cost=LAYER_COST,
        rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.025,
        grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,
        bounds_mm=c['baseline']['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'))
    assert not removed
    copper,_=copper_rows(routes,'osc-jack-left','issue189-jl-return-protect-'+str(radius))
    complete=bool(copper) and bool(routes) and all(r['path'] for r in routes)
    out['trials'].append(dict(radius_mm=radius,elapsed_seconds=time.monotonic()-start,complete=complete,
        diagnostics=events,routes=routes,proposal=dict(board_sha256=d['board_sha256'],removed_uuids=[],copper=copper)))
    (HERE/'protect-return-result.json').write_text(json.dumps(out,indent=2)+'\n')
    print(radius,'complete',complete,'objects',len(copper),flush=True)
assert sha(ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb')==d['board_sha256']
out['status']='COMPLETE BOUNDED SEARCH; NATIVE NOT RUN'
(HERE/'protect-return-result.json').write_text(json.dumps(out,indent=2)+'\n')
