"""Bounded full-width search from existing native JL ground pours; no physical pad changes."""
import copy,json,math,runpy,time,uuid
from pathlib import Path
import shapely
HERE=Path(__file__).parent
s=runpy.run_path(str(HERE/'probe.py'))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS
results=[]
for row in s['results']:
 source=row['source_pad_uuids'];seeds=[];matched=[]
 for match in row['matches']:
  if match['status']!='screened':continue
  poly=next(poly for poly,digest in s['zones'][match['layer']] if digest==match['fill_sha256']);matched.append(poly)
  interior=poly.buffer(-.2)
  for part in ([interior] if interior.geom_type=='Polygon' else shapely.get_parts(interior)):
   if part.is_empty or part.geom_type!='Polygon':continue
   for i in range(32):
    point=part.exterior.interpolate(i/32,normalized=True);xy=[round(point.x*1e6),round(point.y*1e6)]
    if not poly.covers(shapely.Point(*[v/1e6 for v in xy]).buffer(.175)):continue
    if any(p['xy']==xy for p in seeds):continue
    radius=12500;seeds.append(dict(uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189:JL-native-fill-seed:'+str(xy))),ref='existing-native-AGND-pour',pad=str(len(seeds)),net='AGND',xy=xy,layers=[match['layer']],poly=[[xy[0]-radius,xy[1]-radius],[xy[0]+radius,xy[1]-radius],[xy[0]+radius,xy[1]+radius],[xy[0]-radius,xy[1]+radius]],drill=0,npth=False,locked=True))
 if not seeds:results.append({'source_pads':row['source_pads'],'status':'no bounded interior seeds'});continue
 assert len(seeds)<=128
 bounds=list(shapely.union_all(matched).bounds);bounds=[bounds[0]-6,bounds[1]-6,bounds[2]+6,bounds[3]+6]
 trial=copy.deepcopy(s['d']);trial['pads']+=seeds;trial['islands']['AGND']=[source+[p['uuid'] for p in seeds]];events=[];start=time.monotonic()
 paths,removed=route(trial,['AGND'],planes={'AGND':'In1.Cu'},allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,plane_window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,log=lambda *args:None)
 assert not removed
 rows,_=copper_rows(paths,'osc-jack-left','issue189-jl-native-pour-stitch-'+source[0]);assert all(r['net']=='AGND' and (r['kind']=='via' or r['width_nm']==300000) for r in rows)
 result={'source_pads':row['source_pads'],'source_uuids':source,'search_seeds':seeds,'fill_provenance':row['matches'],'bounds_mm':bounds,'complete':bool(rows) and bool(paths) and all(r['path'] for r in paths),'elapsed_seconds':time.monotonic()-start,'diagnostics':events,'routes':paths,'copper':rows};results.append(result)
 print(json.dumps({k:v for k,v in result.items() if k not in ('routes','copper','search_seeds','fill_provenance')}),flush=True)
 (HERE/'seed-result.json').write_text(json.dumps({'status':'BOUNDED SEARCH; NO NATIVE REPLAY OR ACCEPTANCE','input_board_sha256':s['result']['board_sha256'],'input_dump_sha256':s['result']['dump_sha256'],'physical_pad_changes':0,'cases':results},indent=2)+'\n')
