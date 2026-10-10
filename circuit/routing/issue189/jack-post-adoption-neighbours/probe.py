"""Revisit ten signal obligations per jack board nearest the last accepted cuts.

Current native inputs include all accepted restoration copper. No cuts or moves.
"""
import argparse,copy,hashlib,itertools,json,math,re,subprocess,sys,time
from pathlib import Path
from shapely.geometry import LineString,Point
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs
from scripts.pcbgen.route_shards import copper_block_groups
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('saved_root',type=Path);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
boards=[('osc-jack-left','jl-r8276-adoption','r8276-joint','d50853d^','9d193cd974148e58b576d247edb5bce804f06a29d075098513a1292c21fbf136'),('osc-jack-right','jr-c7413-adoption','c7413-endpoints','133f2f6^','f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a')]
results=[];started=time.monotonic()
for bid,folder,label,base,dump_sha in boards:
 dump_path=a.saved_root/folder/'.circuit-cache'/f'{bid}-grid-shards-fresh/dump.json';assert sha(dump_path.read_bytes())==dump_sha;d=json.loads(dump_path.read_text())
 board=ROOT/'boards'/bid/(bid+'.kicad_pcb');assert sha(board.read_bytes())==d['board_sha256']
 replay_path=ROOT/'boards'/bid/'reports/grid-routing'/f'shards-issue189-{label}-copper.json';replay=json.loads(replay_path.read_text())
 old=subprocess.check_output(['git','show',base+':'+str(board.relative_to(ROOT))],cwd=ROOT);assert sha(old)==replay['base_sha256']
 blocks=copper_block_groups(old.decode());cuts=[]
 for row in replay['removed']:
  item=blocks[row['uuid']];assert len(item)==1;text=item[0][2];assert text.startswith('(segment')
  coords=[]
  for k in ('start','end'):
   m=re.search(r'\('+k+r'\s+([-0-9.]+)\s+([-0-9.]+)\)',text);assert m;coords.append(tuple(map(float,m.groups())))
  cuts.append(LineString(coords))
 pads={p['uuid']:p for p in d['pads']};choices=[]
 for net,groups in sorted(d['islands'].items()):
  if net in (*RAILS,'AGND') or len(groups)<2:continue
  pairs=[]
  for gi,gj in itertools.combinations(range(len(groups)),2):
   for u,v in itertools.product([u for u in groups[gi] if u in pads],[u for u in groups[gj] if u in pads]):
    x,y=pads[u],pads[v];dist=math.dist(x['xy'],y['xy'])/1e6;pairs.append((dist,u,v,gi,gj))
  if not pairs:continue
  distance,u,v,gi,gj=min(pairs)
  pp=[pads[u],pads[v]];xy=[[v/1e6 for v in pad['xy']] for pad in pp]
  if max(abs(xy[0][i]-xy[1][i]) for i in (0,1))>24:continue
  proximity=min(Point(pt).distance(cut) for pt in xy for cut in cuts)
  bounds=[min(pt[0] for pt in xy)-6,min(pt[1] for pt in xy)-6,max(pt[0] for pt in xy)+6,max(pt[1] for pt in xy)+6]
  choices.append(dict(net=net,source_group_indices=[gi,gj],native_groups=[groups[gi],groups[gj]],endpoints=[{k:p[k] for k in ('uuid','ref','pad','net','xy','layers')} for p in pp],pad_distance_mm=distance,nearest_last_cut_mm=proximity,bounds_mm=bounds))
 choices=sorted(choices,key=lambda c:(c['nearest_last_cut_mm'],c['pad_distance_mm'],c['net']))[:10];assert len(choices)==10
 output=dict(board=bid,board_sha256=d['board_sha256'],dump_sha256=dump_sha,last_accepted_replay_sha256=sha(replay_path.read_bytes()),last_accepted_removed_uuids=[r['uuid'] for r in replay['removed']],selection='Ten open signal component-pairs nearest last accepted cuts; current restored copper included; distance is selection heuristic, not evidence of an opened channel',cases=[]);results.append(output)
 for index,case in enumerate(choices):
  current=copy.deepcopy(d);current['islands'][case['net']]=case['native_groups'];events=[];then=time.monotonic()
  routed,removed=route(current,[case['net']],allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=case['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs(bid))
  assert not removed;copper,_=copper_rows(routed,bid,'issue189-post-adoption-'+str(index));complete=bool(copper) and bool(routed) and all(r['path'] for r in routed)
  output['cases'].append(dict(**case,elapsed_seconds=time.monotonic()-then,complete_raster_transaction=complete,diagnostics=events,routes=routed,proposal={'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':copper}))
  (HERE/'result.json').write_text(json.dumps(dict(status='BOUNDED SEARCH; NO CANONICAL CHANGES; NATIVE NOT RUN',router_sha256=sha((ROOT/'scripts/pcbgen/grid_router.py').read_bytes()),elapsed_seconds=time.monotonic()-started,boards=results),indent=2)+'\n')
  print(bid,index,case['endpoints'][0]['ref'],case['endpoints'][1]['ref'],'complete',complete,flush=True)
 assert sha(board.read_bytes())==d['board_sha256']

final=json.loads((HERE/"result.json").read_text());final["status"]="COMPLETE BOUNDED SEARCH; NO CANONICAL CHANGES; NATIVE NOT RUN"
(HERE/"result.json").write_text(json.dumps(final,indent=2)+"\n")
