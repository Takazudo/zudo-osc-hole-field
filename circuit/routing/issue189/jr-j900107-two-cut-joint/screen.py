"""Reserve a ground link and reconnect exact retained cut endpoints on native geometry."""
import json,hashlib,time,sys,copy,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
root=Path('.circuit-cache/issue189-downloaded/jr-j900107-ground');p=root/'osc-jack-right-grid-189-jr136-j900107-4-ground-cut-cut/dump.json';d=json.loads(p.read_text());before=json.loads((root/'osc-jack-right-grid-189-local-base/dump.json').read_text());plan=json.loads(Path('circuit/routing/issue189/jr136-j900107-4-ground-cut/plan.json').read_text());assert hashlib.sha256(Path('boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==plan['input_board_sha256'];uid=plan['stage']['repair_ground_pad_uuids'][0]
# Keep the tiny original segment that joins the pad-only and padless native pieces.
from shapely.geometry import Point,Polygon
restored_uuid='7ce0d76d-8094-5807-b95d-ce967dc887af';victim='XE429289AAEFEAA3661F7'
restored=next(t for t in before['tracks'] if t['uuid']==restored_uuid)
pad=next(p for p in d['pads'] if p['uuid']=='ffc60cfa-9872-53a7-b0f4-391cfe389822')
end_track=next(t for t in d['tracks'] if t['uuid']=='d156553a-aaca-57ac-9bc0-466894f9488f')
assert Polygon(pad['poly']).covers(Point(restored['a'])) and restored['b']==end_track['a']
groups=d['islands'][victim];a=next(i for i,g in enumerate(groups) if pad['uuid'] in g);b=next(i for i,g in enumerate(groups) if end_track['uuid'] in g);assert a!=b
merged=sorted(set(groups[a]+groups[b]+[restored_uuid]));d['islands'][victim]=[g for i,g in enumerate(groups) if i not in [a,b]]+[merged];d['tracks'].append(restored)
plan['stage']['repair_source_uuids']=[u for u in plan['stage']['repair_source_uuids'] if u!=restored_uuid]
original=next(g for g in before['islands']['AGND'] if uid in g);joined=next(g for g in d['islands']['AGND'] if uid in g);assert joined==max(d['islands']['AGND'],key=len) and set(original)<set(joined)
net='XE429289AAEFEAA3661F7';assert net not in before['islands'] and len(d['islands'][net])==2
cuts=[t for t in before['tracks'] if t['uuid'] in plan['stage']['repair_source_uuids']];ends={tuple(t[e]) for t in cuts for e in ['a','b']};anchors=[]
for t in d['tracks']:
 if t['net']!=net:continue
 for e in ['a','b']:
  if tuple(t[e]) in ends:anchors.append({'retained_uuid':t['uuid'],'xy':t[e],'layer':t['layer'],'cut_component':next(i for i,g in enumerate(d['islands'][net]) if t['uuid'] in g)})
assert len(anchors)==2 and {a['cut_component'] for a in anchors}=={0,1}
search=copy.deepcopy(d);search['islands']['AGND']=[original,max(before['islands']['AGND'],key=len)];search['islands'][net]=[]
for i,a in enumerate(anchors):
 x,y=a['xy'];u=str(uuid.uuid5(uuid.NAMESPACE_URL,f'issue189-j900107-two-cut-retained-endpoint-{i}'));h=10000;search['pads'].append({'uuid':u,'ref':'SEARCH_ONLY_ENDPOINT','pad':str(i),'net':net,'xy':[x,y],'layers':[a['layer']],'poly':[[x-h,y-h],[x+h,y-h],[x+h,y+h],[x-h,y+h]],'drill':0,'npth':False,'locked':False});search['islands'][net].append([u])
search['islands'][net]=d['islands'][net]
search['pads']=[p for p in search['pads'] if p['ref']!='SEARCH_ONLY_ENDPOINT']
out=[];start=time.monotonic()
for layers in [['F.Cu','B.Cu'],['F.Cu','In2.Cu','B.Cu']]:
 events=[];begin=time.monotonic();results,removed=route(search,['AGND',net],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=plan['stage']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'))
 rows,_=copper_rows(results,'osc-jack-right','issue189-j900107-two-cut-joint-'+','.join(layers));assert not removed
 complete={r['net'] for r in results if r['path']}=={'AGND',net} and all(r['path'] for r in results)
 proposal={'board_sha256':plan['input_board_sha256'],'removed_uuids':plan['stage']['repair_source_uuids'],'copper':rows};out.append({'layers':layers,'complete_raster_transaction':complete,'elapsed_seconds':time.monotonic()-begin,'results':results,'diagnostics':events,'proposal':proposal});print(layers,'complete',complete,'objects',len(rows),'vias',sum(r['kind']=='via' for r in rows),flush=True)
 if complete:break
here=Path('circuit/routing/issue189/jr-j900107-two-cut-joint');(here/'result.json').write_text(json.dumps({'status':'RASTER ONLY; FULL NATIVE CUT COMPONENTS USED; RETAINED ENDPOINTS STILL REQUIRE REVIEW; NATIVE ORIGINAL BASELINE REMAINS AUTHORITATIVE','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_cut_board_sha256':d['board_sha256'],'original_ground_group':original,'reconstruction':{'restored_original_track':restored,'merged_native_cut_components':[a,b],'native_two_cut_topology_not_yet_run':True},'exact_endpoint_anchors':anchors,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
if out[-1]['complete_raster_transaction']:(here/'proposal.json').write_text(json.dumps(out[-1]['proposal'],indent=2)+'\n')
