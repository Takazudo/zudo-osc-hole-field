#!/usr/bin/env python3
"""Construct before/after source masks; stop before A* and forbid native search."""
import argparse,copy,json,sys,math,hashlib
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy import ndimage
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import f3_adapter as a
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args=p.parse_args()
D=args.candidate.resolve();read=lambda p:json.loads(p.read_text())
original=read(D/'original-dump.json');card=read(D/'terminal-breakout.json');receipt=read(D/'breakout-receipt.json');pool=read(D/'adapter-pool.json');packet=read(H/'f3-packet/request.json');policy=packet['route_policy'];budget=packet['budget'];domain=packet['demand_and_preservation_contract'];target=domain['targets']['signal'];net=target['net_token'];geo=a.Geometry(original)
import f3_breakout
binding=read(D/'source-binding.json')
current_binding=f3_breakout.source_binding(H,D/'original-dump.json',D/'terminal-breakout.json')
a.require({k:v for k,v in binding.items() if k!='candidate_file_sha256'}==current_binding,'candidate method binding drift')
for name,want in binding['candidate_file_sha256'].items():
 a.require(hashlib.sha256((D/name).read_bytes()).hexdigest()==want,'candidate file drift: '+name)
expected_pool,expected_receipt=f3_breakout.prepare(original,domain,a.saved_pool(read(H/'cohort-validation.json'),domain),budget,policy,'two-A',card)
a.require(pool==expected_pool and a.digest(receipt)==a.digest(expected_receipt),'candidate pool or receipt drift')
a.require(hashlib.sha256((D/'original-dump.json').read_bytes()).hexdigest()==packet['cases']['two-A']['dump_sha256'],'exact original dump mismatch')
a.require(hashlib.sha256((H/'route-1641/access-plan.json').read_bytes()).hexdigest()==packet['cases']['two-A']['access_plan_sha256'],'retained before-plan mismatch')
plan_before=read(H/'route-1641/access-plan.json')['demands']['signal'];after_groups,after_records,_=a.portals(original,target,pool['signal'],budget,domain['common_bounds_mm'])
results={}
for name,groups,records in [('before',plan_before['groups'],plan_before['records']),('after',after_groups,after_records)]:
 derived=copy.deepcopy(original);derived['pads'].extend(records[u]['pad'] for group in groups for u in group);derived['islands']={net:groups};saved={};real=a.grid.Raster
 class NoSearch(Exception):pass
 def capture(*args,**kwargs):
  raster=real(*args,**kwargs);saved['raster']=raster;return raster
 def stop(free,via,src,goal,*args):saved.update(free=free,via=via,src=src,goal=goal);raise NoSearch()
 try:
  with patch.object(a.grid,'Raster',capture),patch.object(a.grid,'astar',stop),patch.object(a.grid,'native_astar',side_effect=AssertionError('native prohibited')):
   a.grid.route(derived,nets=[net],res=.1,clearance=.25,rail_nets=policy['rail_nets'],rail_width=.5,signal_width=.3,via_diameter=.6,via_drill=.3,max_expansions=50000,window_mm=6,bounds_mm=domain['common_bounds_mm'],planes={},fill_guards=policy['fill_guards'],rip=(),full_board=False,rrr_rounds=0,log=lambda _:None)
 except NoSearch:pass
 raster=saved['raster'];src=saved['src'];goal=saved['goal'];free=saved['free'];via=saved['via'];mask=a.grid.island_mask(raster,derived,groups[0]+groups[1]);points=np.argwhere(mask.any(0));lo=points.min(0);hi=points.max(0);y0=max(0,int(lo[0])-60);x0=max(0,int(lo[1])-60);y1=min(raster.h,int(hi[0])+61);x1=min(raster.w,int(hi[1])+61);assert free.shape[1:]==(y1-y0,x1-x0)
 gy,gx=raster.cell(*card['via_nm']);y,x=gy-y0,gx-x0;l=raster.layers.index('In2.Cu');neighbors=[]
 for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
  xx,yy=raster.point(gy+dy,gx+dx);validation=geo.segment([v/1e6 for v in card['via_nm']],[xx/1e6,yy/1e6],net,'In2.Cu',.3)
  neighbors.append({'xy_nm':[xx,yy],'raster_free':bool(free[l,y+dy,x+dx]),'exact_segment':validation})
 foreign=np.any((raster.label!=0)&(raster.label!=raster.net_id[net]),axis=0);foreign|=np.any((raster.fixed_label!=0)&(raster.fixed_label!=raster.net_id[net]),axis=0)
 dist=float(ndimage.distance_transform_edt(~foreign)[gy,gx]*.1)
 results[name]={'source_layers_present':[raster.layers[i] for i in range(len(raster.layers)) if src[i].any()],'source_layers_at_breakout':[raster.layers[i] for i in range(len(raster.layers)) if src[i,y,x]],'goal_at_breakout':bool(goal[:,y,x].any()),'raster_via_ok':bool(via[y,x]),'invented_through':bool(src[:,y,x].all() or goal[:,y,x].all()),'In2_free_neighbors':neighbors,'raster_foreign_distance_mm':dist,'raster_via_required_distance_mm':.25+.3+.1/math.sqrt(2)+.01,'physical_input_changed':False,'search_executed':False}
 assert name!='before' or not src[l,y,x]
 assert name!='after' or (src[l,y,x] and any(n['raster_free'] and n['exact_segment']['pass'] for n in neighbors))
assert original==read(D/'original-dump.json')
a.require(not args.output.exists(), 'fresh proof output required')
args.output.write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'status':'PASS; before B-only source, after explicit In2 source with legal adjacent transitions', 'search_executed':False,'native_executed':False,'output':str(args.output)}))
