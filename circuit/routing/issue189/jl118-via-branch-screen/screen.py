"""Bounded via-branch prefilter only; native victim topology/restoration is mandatory."""
import copy,hashlib,json,math,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,SIGNAL_LAYERS,neck_kwargs,repair_selection,repair_bounds
HERE=Path(__file__).resolve().parent
P=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json')
d=json.loads(P.read_text());board=Path('boards/osc-jack-left/osc-jack-left.kicad_pcb')
assert hashlib.sha256(P.read_bytes()).hexdigest()=='9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'
assert hashlib.sha256(board.read_bytes()).hexdigest()==d['board_sha256']=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
main=max(d['islands']['AGND'],key=len);groups={u:g for g in d['islands']['AGND'] if g is not main for u in g};results=[];skipped=[];started=time.monotonic()
for pad in d['pads']:
 if pad['uuid'] not in groups:continue
 near=sorted((v for v in d['vias'] if v['net'] not in RAILS+['AGND'] and math.dist(pad['xy'],v['xy'])<=2500000),key=lambda v:(math.dist(pad['xy'],v['xy']),v['uuid']))[:2]
 for vi,via in enumerate(near):
  # Remove only this via and the entire exact segments ending at its centre.
  branch=[t for t in d['tracks'] if t['net']==via['net'] and (t['a']==via['xy'] or t['b']==via['xy'])]
  cut={via['uuid'],*(t['uuid'] for t in branch)}
  if not branch or len(cut)>12:skipped.append([pad['ref']+'.'+pad['pad'],via['uuid'],'branch-count',len(cut)]);continue
  pts=[pad['xy'],via['xy']]+[t[e] for t in branch for e in ('a','b')]
  bounds=[min(p[0] for p in pts)/1e6-6,min(p[1] for p in pts)/1e6-6,max(p[0] for p in pts)/1e6+6,max(p[1] for p in pts)/1e6+6]
  if max(bounds[2]-bounds[0],bounds[3]-bounds[1])>50:skipped.append([pad['ref']+'.'+pad['pad'],via['uuid'],'frame-too-large']);continue
  spec={'repair_targets':['AGND'],'repair_ground_pad_uuids':[pad['uuid']],'repair_source_uuids':sorted(cut),'repair_bounds_mm':bounds}
  repair_selection(d,spec);repair_bounds(d,spec,['AGND'],cut)
  endpoints=[{'cut_uuid':t['uuid'],'xy':t[e],'layer':t['layer'],'victim_net':t['net']} for t in branch for e in ('a','b') if t[e]!=via['xy']]
  search={**d,'tracks':[t for t in d['tracks'] if t['uuid'] not in cut],'vias':[v for v in d['vias'] if v['uuid'] not in cut],'islands':{'AGND':[groups[pad['uuid']],main]}}
  events=[];begin=time.monotonic()
  paths,removed=route(search,['AGND'],res=.0125,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
  assert not removed
  rows,_=copper_rows(paths,'osc-jack-left','issue189-jl118-via-branch-'+pad['uuid']+'-'+via['uuid'])
  complete=bool(rows) and bool(paths) and all(x['path'] for x in paths)
  results.append({'pad':pad['ref']+'.'+pad['pad'],'spec':spec,'via':via,'cut_segments':branch,'boundary_endpoints':endpoints,'elapsed_seconds':time.monotonic()-begin,'ground_path_found':complete,'ground_copper':rows,'diagnostics':events})
  print(results[-1]['pad'],vi,'cut',len(cut),'ground',complete,len(rows),flush=True)
  (HERE/'result.json').write_text(json.dumps({'status':'RASTER GROUND-ONLY PREFILTER; NATIVE CUT TOPOLOGY AND ALL VICTIM RESTORATION NOT RUN; NO ADOPTION','board_sha256':d['board_sha256'],'dump_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-started,'skipped':skipped,'transactions':results},indent=2)+'\n')
print('complete',len(results),'positive',sum(x['ground_path_found'] for x in results),flush=True)
