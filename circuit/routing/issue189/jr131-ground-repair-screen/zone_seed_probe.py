"""Search from existing native poured copper, without adding physical pads or moving parts."""
import copy,json,math,runpy,sys,time,uuid
from pathlib import Path
import shapely
from shapely.ops import nearest_points
HERE=Path(__file__).parent
state=runpy.run_path(str(HERE/'zone_via_probe.py'))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
assert state['chosen'] and len(state['result']['legal_uncontained_sites'])==9
poly=state['poly'];inside=poly.buffer(-.18);assert not inside.is_empty
seeds=[]
for site in state['result']['legal_uncontained_sites']:
 if not site['inside_native_ground_plane']:continue
 point=nearest_points(inside,shapely.Point(site['x_mm'],site['y_mm']))[0]
 xy=[round(point.x*1e6),round(point.y*1e6)]
 if any(p['xy']==xy for p in seeds):continue
 assert poly.covers(shapely.Point(*[v/1e6 for v in xy]).buffer(.175))
 radius=12500
 seeds.append(dict(uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189:native-fill-seed:'+str(xy))),ref='existing-native-AGND-pour',pad=str(len(seeds)),net='AGND',xy=xy,layers=['B.Cu'],poly=[[xy[0]-radius,xy[1]-radius],[xy[0]+radius,xy[1]-radius],[xy[0]+radius,xy[1]+radius],[xy[0]-radius,xy[1]+radius]],drill=0,npth=False,locked=True))
assert seeds
trial=copy.deepcopy(state['d']);trial['pads']+=seeds;trial['islands']['AGND']=[list(state['source'])+[p['uuid'] for p in seeds]]
start=time.monotonic();events=[]
paths,removed=route(trial,['AGND'],planes={'AGND':'In1.Cu'},allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,plane_window_mm=6,max_expansions=300000,bounds_mm=state['bounds'],fill_guards={'-12V':'In3.Cu'},diagnostics=events)
assert not removed
rows,_=copper_rows(paths,'osc-jack-right','issue189-jr-native-pour-stitch')
assert all(r['net']=='AGND' and (r['kind']=='via' or r['width_nm']==300000) for r in rows)
assert all(r['kind'] in ('via','segment') for r in rows)
result=dict(status='BOUNDED NATIVE-POUR-SEEDED SEARCH; NATIVE REPLAY NOT RUN',candidate_board_sha256=state['result']['candidate_board_sha256'],candidate_dump_sha256=state['result']['candidate_dump_sha256'],native_fill_block_sha256=state['result']['native_fill_block_sha256'],search_only_existing_copper_seeds=seeds,physical_pad_changes=0,complete=bool(rows) and bool(paths) and all(r['path'] for r in paths),elapsed_seconds=time.monotonic()-start,diagnostics=events,routes=paths,copper=rows)
(HERE/'zone-seed-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('routes','copper','search_only_existing_copper_seeds')},indent=2));print('Search seeds',len(seeds),'copper objects',len(rows))
