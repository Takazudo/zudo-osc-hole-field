"""Join the two exposed retained endpoints while preserving the native ground gain."""
import copy,hashlib,json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).parent;root=Path('.circuit-cache/issue189-downloaded/jr-rb4614');p=root/'osc-jack-right-grid-189-jr134-rb4614-2-ground-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-right-grid-189-local-base/dump.json').read_text());r=json.loads((root/'issue189-local-osc-jack-right/result.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jr134-rb4614-2-ground-cut/plan.json').read_text());proposal=json.loads((p.parent/'proposal.json').read_text());proposal.update(board_sha256=plan['input_board_sha256'],removed_uuids=plan['stage']['repair_source_uuids']);assert hashlib.sha256(Path('boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256']
ids={u for kind,us in r['gate']['new_warning_identities'] for u in us};assert len(ids)==2 and all(kind=='track_dangling' for kind,_ in r['gate']['new_warning_identities'])
ends={tuple(t[k]) for t in before['tracks'] if t['uuid'] in proposal['removed_uuids'] for k in ['a','b']};anchors=[]
for t in d['tracks']:
 if t['uuid'] in ids:
  xy=[t[k] for k in ['a','b'] if tuple(t[k]) in ends];assert len(xy)==1
  anchors.append(dict(retained_uuid=t['uuid'],net=t['net'],layer=t['layer'],xy=xy[0]))
assert len(anchors)==2 and len({a['net'] for a in anchors})==1;net=anchors[0]['net'];assert net not in before['islands'] and len(d['islands'][net])==2;assert len({i for a in anchors for i,g in enumerate(d['islands'][net]) if a['retained_uuid'] in g})==2
out=[];start=time.monotonic()
for layers,res in [(['F.Cu','B.Cu'],.025),(['F.Cu','In2.Cu','B.Cu'],.0125)]:
 search=copy.deepcopy(d);names=[];events=[]
 for i,a in enumerate(anchors):
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'issue189-rb4614-anchor-{i}'));names.append(uid);x,y=a['xy'];h=10000
  search['pads'].append(dict(uuid=uid,ref='SEARCH_ONLY_ENDPOINT',pad=str(i),net=net,xy=[x,y],layers=[a['layer']],poly=[[x-h,y-h],[x+h,y-h],[x+h,y+h],[x-h,y+h]],drill=0,npth=False,locked=False))
 search['islands'][net]=[[u] for u in names]
 results,removed=route(search,[net],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=res,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'));assert not removed
 rows,_=copper_rows(results,'osc-jack-right','issue189-rb4614-endpoints-'+str(res));complete=bool(rows) and all(v['path'] for v in results);out.append(dict(layers=layers,resolution=res,complete=complete,extra_objects=len(rows),results=results,diagnostics=events,proposal={**proposal,'copper':proposal['copper']+rows}));print(layers,res,'complete',complete,'extra',len(rows),flush=True)
 if complete:break
(HERE/'result.json').write_text(json.dumps(dict(status='RASTER ONLY; FULL ORIGINAL NATIVE GATES REQUIRED',input_dump_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),input_candidate_sha256=d['board_sha256'],anchors=anchors,elapsed_seconds=time.monotonic()-start,transactions=out),indent=2)+'\n')
if out[-1]['complete']:(HERE/'proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
