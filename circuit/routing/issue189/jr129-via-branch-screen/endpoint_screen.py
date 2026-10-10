"""Provisional endpoint restoration; requires native cut-component validation."""
import argparse,copy,hashlib,json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--dump',type=Path,default=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/jr129-full/fresh/dump.json'));parser.add_argument('--screen',type=Path,default=HERE/'result.json');parser.add_argument('--output',type=Path,default=HERE/'other-joint-result.json');args=parser.parse_args()
P=args.dump;d=json.loads(P.read_text());screen=json.loads(args.screen.read_text());all_results=[]
for candidate in screen['transactions']:
 if not candidate['ground_path_found']:continue
 selected={**screen,'transaction':candidate}
 x=selected['transaction'];cut=set(x['spec']['repair_source_uuids']);net=x['via']['net'];assert hashlib.sha256(P.read_bytes()).hexdigest()==selected['dump_sha256'];assert hashlib.sha256(P.with_name('osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==selected['board_sha256']
 search={**d,'pads':copy.deepcopy(d['pads']),'tracks':[t for t in d['tracks'] if t['uuid'] not in cut],'vias':[v for v in d['vias'] if v['uuid'] not in cut],'islands':{net:[]}}
 for row in x['ground_copper']:
  v={'uuid':row['uuid'],'net':row['net']}
  if row['kind']=='via':v.update(xy=row['at_nm'],diameter=row['diameter_nm'],drill=row['drill_nm']);search['vias'].append(v)
  else:v.update(a=row['start_nm'],b=row['end_nm'],width=row['width_nm'],layer=row['layer']);search['tracks'].append(v)
 for i,a in enumerate(x['boundary_endpoints']):
  px,py=a['xy'];h=10000;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-jr129-boundary-'+str(i)));search['pads'].append({'uuid':uid,'ref':'SEARCH_ONLY_RETAINED_ENDPOINT','pad':str(i),'net':net,'xy':a['xy'],'layers':[a['layer']],'poly':[[px-h,py-h],[px+h,py-h],[px+h,py+h],[px-h,py+h]],'drill':0,'npth':False,'locked':False});search['islands'][net].append([uid])
 out=[]
 for layers in [['F.Cu','In2.Cu','In3.Cu','B.Cu']]:
  events=[];start=time.monotonic();paths,removed=route(search,[net],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=x['spec']['repair_bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'));assert not removed
  rows,_=copper_rows(paths,'osc-jack-right','issue189-jr129-via-branch-joint-'+x['pad']+'-'+x['via']['uuid']+'-'+','.join(layers));ok=bool(rows) and bool(paths) and all(p['path'] for p in paths);out.append({'layers':layers,'endpoint_path_found':ok,'elapsed_seconds':time.monotonic()-start,'diagnostics':events,'proposal':{'board_sha256':selected['board_sha256'],'removed_uuids':sorted(cut),'copper':x['ground_copper']+rows}});print(layers,ok,len(rows),flush=True)
 all_results.append({'pad':candidate['pad'],'cut_spec':candidate['spec'],'via_uuid':candidate['via']['uuid'],'boundary_endpoints':candidate['boundary_endpoints'],'transactions':out})
 print(candidate['pad'],out[0]['endpoint_path_found'],flush=True)
 args.output.write_text(json.dumps({'status':'PROVISIONAL RASTER ONLY; NATIVE CUT TOPOLOGY AND FULL BASELINE ACCEPTANCE REQUIRED','board_sha256':screen['board_sha256'],'dump_sha256':screen['dump_sha256'],'cases':all_results},indent=2)+'\n')
