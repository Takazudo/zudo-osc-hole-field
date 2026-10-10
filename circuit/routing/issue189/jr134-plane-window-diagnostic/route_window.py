"""One cause-driven6mm fanout comparison, with default3mm controls and identical inputs."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.dump)=='f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a'
d=json.loads(a.dump.read_text());board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==d['board_sha256']
rows=[];start=time.monotonic()
for ref in ('R8490','RB4615'):
 original=next(p for p in d['pads'] if p['ref']==ref and p['net']=='AGND');group=next(g for g in d['islands']['AGND'] if original['uuid'] in g);assert group==[original['uuid']]
 x,y=[v/1e6 for v in original['xy']]
 for window in (3,6):
  current=copy.deepcopy(d);current['islands']['AGND']=[group];events=[];then=time.monotonic()
  result,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'},plane_window_mm=window,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=[x-8,y-8,x+8,y+8],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'))
  assert not removed
  copper,_=copper_rows(result,'osc-jack-right','issue189-plane-window-'+ref+'-'+str(window));complete=bool(copper) and bool(result) and all(r['path'] for r in result)
  rows.append(dict(ref=ref,plane_window_mm=window,elapsed_seconds=time.monotonic()-then,complete_raster_transaction=complete,diagnostics=events,results=result,proposal={'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':copper}));print(ref,window,complete,flush=True)
assert sha(board)==d['board_sha256']
(HERE/'route-result.json').write_text(json.dumps(dict(status='BOUNDED RASTER COMPARISON; NO BOARD CHANGE; NATIVE NOT RUN',dump_sha256=sha(a.dump),board_sha256=sha(board),router_sha256=sha(ROOT/'scripts/pcbgen/grid_router.py'),elapsed_seconds=time.monotonic()-start,transactions=rows),indent=2)+'\n')
