"""Bounded read-only repair diagnosis for exact native original-group splits."""
import hashlib,json,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
with zipfile.ZipFile('/tmp/issue189-core-supply-terminal.zip') as z:
 raw=z.read(next(n for n in z.namelist() if n.endswith('osc-core-grid-shards-fresh/dump.json')))
d=json.loads(raw);assert d['board_sha256']=='4f90bfc16d5e338cc31adc3a41f0da8ff8f289a24b963ab8f9c9caf9d98cec10';proof=json.loads(Path('/tmp/issue189-core-supply-partial-proof.json').read_text());splits=proof['stages']['fresh']['raw_gate']['split_pad_groups'];pads={p['uuid']:p for p in d['pads']};results=[];started=time.monotonic()
for i,split in enumerate(splits):
 old=set(split['previously_connected_pads']);parts=[g for g in d['islands']['AGND'] if old.intersection(g)];assert len(parts)==2
 parts.sort(key=lambda g:len(old.intersection(g)));small,retained=parts;target=[pads[u] for u in old.intersection(small)];pts=[p['xy'] for p in target];bounds=[min(p[0] for p in pts)/1e6-10,min(p[1] for p in pts)/1e6-10,max(p[0] for p in pts)/1e6+10,max(p[1] for p in pts)/1e6+10];assert max(bounds[2]-bounds[0],bounds[3]-bounds[1])<=50
 search={**d,'islands':{'AGND':[small,retained]}};events=[];begin=time.monotonic()
 paths,removed=route(search,['AGND'],res=.05,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=['F.Cu','In2.Cu','In3.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=200000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-core'));assert not removed
 rows,_=copper_rows(paths,'osc-core','issue189-exact-return-repair-'+str(i));ok=bool(rows) and bool(paths) and all(p['path'] for p in paths)
 results.append({'original_pad_group':len(old),'detached_pads':[p['ref']+'.'+p['pad'] for p in target],'native_component_members':[len(small),len(retained)],'bounds_mm':bounds,'elapsed_seconds':time.monotonic()-begin,'path_found':ok,'diagnostics':events,'provisional_copper':rows});print(results[-1]['detached_pads'],ok,len(rows),flush=True)
 result={'status':'READ-ONLY BOUNDED RETURN REPAIR DIAGNOSIS; NATIVE RESTORATION AND ACCEPTANCE NOT RUN; NO ADOPTION','native_candidate_sha256':d['board_sha256'],'dump_sha256':hashlib.sha256(raw).hexdigest(),'res_mm':.05,'max_expansions':200000,'elapsed_seconds':time.monotonic()-started,'cases':results};Path('/tmp/issue189-core-return-repair-screen.json').write_text(json.dumps(result,indent=2)+'\n')
