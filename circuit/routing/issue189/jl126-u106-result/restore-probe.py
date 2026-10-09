import json,time,hashlib,sys,copy
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jl-u106-cut');p=root/'osc-jack-left-grid-189-jl126-u106-pair-cut-verify/dump.json';d=json.loads(p.read_text());base=json.loads((root/'osc-jack-left-grid-189-local-base/dump.json').read_text());restore={'ee3e3926-713a-5c94-8bf2-4892ab8edfb1','b9103000-e591-5bd2-8e04-b6be838a6747'};restored=[t for t in base['tracks'] if t['uuid'] in restore]
# This is an explicit raster-only inference. The fixed combined proposal must
# still pass native memberships against the complete original baseline.
for t in restored:
 line=LineString([t['a'],t['b']]).buffer(t['width']/2);groups=d['islands'][t['net']];hits=[]
 for i,g in enumerate(groups):
  ids=set(g);shapes=[]
  for k in d['tracks']:
   if k['uuid'] in ids and k['layer']==t['layer']:shapes.append(LineString([k['a'],k['b']]).buffer(k['width']/2))
  for k in d['pads']:
   if k['uuid'] in ids and t['layer'] in k['layers'] and k['poly']:shapes.append(Polygon(k['poly']))
  for k in d['vias']:
   if k['uuid'] in ids:shapes.append(Point(k['xy']).buffer(k['diameter']/2))
  if shapes and line.distance(unary_union(shapes))<1:hits.append(i)
 assert hits
 d['islands'][t['net']]=[g for i,g in enumerate(groups) if i not in hits]+[[u for i in hits for u in groups[i]]+[t['uuid']]]
 d['tracks'].append(t)
net='X7F1517D2A1A5A4E8D80F';bounds=[197.226065,182.696066,212.313933,197.993934];out=[];start=time.monotonic()
for res in [.05,.025]:
 events=[];t=time.monotonic();results,removed=route(d,[net],res=res,clearance=.2,signal_width=.2,signal_via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,grow={n:.05 for n in RAILS+['AGND']},fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,weight=2.5,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-u106-restore');assert not removed
 out.append({'res':res,'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'copper':rows});print(res,'paths',sum(bool(r['path']) for r in results),'objects',len(rows),flush=True)
Path('.circuit-cache/issue189-jl-u106-restore-probe.json').write_text(json.dumps({'status':'RASTER ONLY;2ORIGINAL SEGMENTS RESTORED WITH INFERRED MEMBERSHIPS; ALL NATIVE GATES NOT RUN','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'restored_original_uuids':sorted(restore),'remaining_original_cut':'41029fa4-d64d-551e-9c7a-74ca518743b5','bounds_mm':bounds,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
