"""Search additive links at retained endpoints exposed by reviewed joint cuts.

Synthetic anchor polygons are search-only and entirely inside existing copper.
The combined replay retains the original native input and exact reviewed cut set.
"""
import copy, hashlib, json, sys, time, uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
side=sys.argv[1]; part={'jl':'2204','jr':'8303'}[side]; board={'jl':'osc-jack-left','jr':'osc-jack-right'}[side]; count={'jl':121,'jr':137}[side]
base=Path(f'circuit/routing/issue189/{side}-u{part}-joint'); out=Path(f'circuit/routing/issue189/{side}-u{part}-endpoints');out.mkdir(exist_ok=True)
root=Path(f'.circuit-cache/issue189-downloaded/{side}-u{part}-joint'); p=root/f'{board}-grid-189-{side}{count}-u{part}-joint/dump.json';d=json.loads(p.read_text());before=json.loads((root/f'{board}-grid-189-local-base/dump.json').read_text());proposal=json.loads((base/'proposal.json').read_text());r=json.loads((root/f'issue189-local-{board}/result.json').read_text())
ids={u for typ,us in r['gate']['new_warning_identities'] for u in us};assert all(typ=='track_dangling' for typ,_ in r['gate']['new_warning_identities'])
cut_ends={tuple(t[e]) for t in before['tracks'] if t['uuid'] in proposal['removed_uuids'] for e in ['a','b']}
anchors=[]
for t in d['tracks']:
 if t['uuid'] not in ids:continue
 ends=[t[e] for e in ['a','b'] if tuple(t[e]) in cut_ends];assert len(ends)==1,(t,ends)
 anchors.append({'retained_uuid':t['uuid'],'xy':ends[0],'net':t['net'],'layer':t['layer']})
assert len(anchors)==len(ids)
plan=json.loads(Path(f'circuit/routing/issue189/{side}121-ground-cut-screen/u2204-plan.json' if side=='jl' else 'circuit/routing/issue189/jr137-ground-cut-screen/u8303-plan.json').read_text());bounds=plan['stage']['repair_bounds_mm'];transactions=[];start=time.monotonic()
for layers in [[anchors[0]['layer']],['F.Cu','B.Cu']]:
 current=copy.deepcopy(d);extra=[];events=[];complete=True
 for index,a in enumerate(anchors):
  search=copy.deepcopy(current);x,y=a['xy'];anchor=str(uuid.uuid5(uuid.NAMESPACE_URL,f'issue189-{side}-endpoint-{index}'));half=10000
  search['pads'].append({'uuid':anchor,'ref':'SEARCH_ONLY_ENDPOINT','pad':str(index),'net':a['net'],'xy':[x,y],'layers':[a['layer']],'poly':[[x-half,y-half],[x+half,y-half],[x+half,y+half],[x-half,y+half]],'drill':0,'npth':False,'locked':False})
  goals=[row['uuid'] for row in proposal['copper']+extra if row['net']==a['net']];assert goals
  search['islands'][a['net']]=[goals,[anchor]]
  results,removed=route(search,[a['net']],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs(board));assert not removed
  rows,_=copper_rows(results,board,f'issue189-{side}-endpoint-{index}-'+','.join(layers));ok=bool(rows) and all(v['path'] for v in results);complete &= ok
  extra.extend(rows)
  for row in rows:
   v={'uuid':row['uuid'],'net':row['net']}
   if row['kind']=='via':v.update(xy=row['at_nm'],diameter=row['diameter_nm'],drill=row['drill_nm'],layers=row['layers']);current['vias'].append(v)
   else:v.update(a=row['start_nm'],b=row['end_nm'],width=row['width_nm'],layer=row['layer']);current['tracks'].append(v)
  if not ok:break
 combined={**proposal,'copper':proposal['copper']+extra}
 transactions.append({'layers':layers,'complete':complete,'extra_objects':len(extra),'extra_vias':sum(v['kind']=='via' for v in extra),'diagnostics':events,'proposal':combined});print(side,layers,complete,len(extra),flush=True)
 if complete:break
(out/'result.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE ACCEPTANCE REQUIRED','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_candidate_sha256':d['board_sha256'],'anchors':anchors,'elapsed_seconds':time.monotonic()-start,'transactions':transactions},indent=2)+'\n')
if transactions[-1]['complete']:(out/'proposal.json').write_text(json.dumps(transactions[-1]['proposal'],indent=2)+'\n')
