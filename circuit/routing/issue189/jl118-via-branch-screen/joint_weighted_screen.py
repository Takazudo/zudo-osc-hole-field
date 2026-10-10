"""Provisional endpoint restoration; requires native cut-component validation."""
import copy,hashlib,json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).resolve().parent;P=HERE.parent/'issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json';d=json.loads(P.read_text());selected=json.loads(Path('circuit/routing/issue189/jl118-r8107-via-branch/selected-ground-only-screen.json').read_text());x=selected['transaction'];cut=set(x['spec']['repair_source_uuids']);net=x['via']['net'];assert hashlib.sha256(P.read_bytes()).hexdigest()==selected['dump_sha256'];assert hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==selected['board_sha256']
search={**d,'pads':copy.deepcopy(d['pads']),'tracks':[t for t in d['tracks'] if t['uuid'] not in cut],'vias':[v for v in d['vias'] if v['uuid'] not in cut],'islands':{net:[]}}
for row in x['ground_copper']:
 v={'uuid':row['uuid'],'net':row['net']}
 if row['kind']=='via':v.update(xy=row['at_nm'],diameter=row['diameter_nm'],drill=row['drill_nm']);search['vias'].append(v)
 else:v.update(a=row['start_nm'],b=row['end_nm'],width=row['width_nm'],layer=row['layer']);search['tracks'].append(v)
for i,a in enumerate(x['boundary_endpoints']):
 px,py=a['xy'];h=10000;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-r8107-boundary-'+str(i)));search['pads'].append({'uuid':uid,'ref':'SEARCH_ONLY_RETAINED_ENDPOINT','pad':str(i),'net':net,'xy':a['xy'],'layers':[a['layer']],'poly':[[px-h,py-h],[px+h,py-h],[px+h,py+h],[px-h,py+h]],'drill':0,'npth':False,'locked':False});search['islands'][net].append([uid])
out=[]
for layers in [['F.Cu','In2.Cu','B.Cu'],['F.Cu','In3.Cu','In2.Cu','B.Cu']]:
 events=[];start=time.monotonic();paths,removed=route(search,[net],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=1200000,weight=2.5,bounds_mm=x['spec']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'));assert not removed
 rows,_=copper_rows(paths,'osc-jack-left','issue189-r8107-joint-weighted-'+','.join(layers));ok=bool(rows) and bool(paths) and all(p['path'] for p in paths);out.append({'layers':layers,'endpoint_path_found':ok,'elapsed_seconds':time.monotonic()-start,'diagnostics':events,'proposal':{'board_sha256':selected['board_sha256'],'removed_uuids':sorted(cut),'copper':x['ground_copper']+rows}});print(layers,ok,len(rows),flush=True)
(HERE/'joint-weighted-result.json').write_text(json.dumps({'status':'PROVISIONAL RASTER ENDPOINT RECONNECTION ONLY; NATIVE CUT COMPONENTS, ALL VICTIMS AND COMPLETE BASELINE GATES STILL REQUIRED; NOT ELIGIBLE','board_sha256':selected['board_sha256'],'dump_sha256':selected['dump_sha256'],'boundary_endpoints':x['boundary_endpoints'],'transactions':out},indent=2)+'\n')
