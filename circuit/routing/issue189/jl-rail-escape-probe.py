import json,time,hashlib,sys,uuid
from pathlib import Path
from shapely.geometry import LineString,Polygon
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS
source=Path('.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(source.read_text());screen=json.loads(Path('.circuit-cache/issue189-jl-rail-escape-screen.json').read_text());assert screen['input_dump_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
chosen=[next(x for x in screen['candidates'] if x['pad']==ref+'.11' and x['end_nm'][1]<x['start_nm'][1] and x['foreign_clearance_screen_pass']) for ref in ['U204','U3102','U3202']];pads={p['ref']+'.'+p['pad']:p for p in d['pads']};stubs=[];groups=[]
for c in chosen:
 line=LineString([c['start_nm'],c['end_nm']]);assert all(not line.buffer(200000).intersects(Polygon(k['poly'])) for k in d['keepouts'] if k.get('tracks') and 'F.Cu' in k['layers'])
 uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-rail-lead/'+c['pad']));stub={'kind':'segment','uuid':uid,'net':'-12V','start_nm':c['start_nm'],'end_nm':c['end_nm'],'width_nm':400000,'layer':'F.Cu'};stubs.append(stub);groups.append([pads[c['pad']]['uuid']])
outputs={}
for seeded in [False,True]:
 search={**d,'islands':{'-12V':[g+([s['uuid']] if seeded else []) for g,s in zip(groups,stubs)]},'tracks':d['tracks']+([{'uuid':s['uuid'],'net':s['net'],'a':s['start_nm'],'b':s['end_nm'],'width':s['width_nm'],'layer':s['layer']} for s in stubs] if seeded else [])}
 events=[];start=time.monotonic();results,removed=route(search,['-12V'],planes={'-12V':'In3.Cu'},res=.075,clearance=.25,rail_width=.4,via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS,max_expansions=300000,diagnostics=events);assert not removed
 rows,links=copper_rows(results,'osc-jack-left','issue189-rail-lead-'+str(seeded));out={'elapsed_seconds':time.monotonic()-start,'results':results,'diagnostics':events,'links':links,'proposal':{'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':(stubs if seeded else [])+rows}};outputs['lead_extensions' if seeded else 'original']=out;print('seeded',seeded,'paths',sum(bool(r['path']) for r in results),'failed',sum(not r['path'] for r in results),'seconds',out['elapsed_seconds'],flush=True)
Path('.circuit-cache/issue189-jl-rail-escape-probe.json').write_text(json.dumps({'status':'RASTER ONLY; NATIVE NOT RUN','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Same native input and same plane-access parameters, comparing no extensions with source-defined0.4mm lead extensions. No removals, no changed pads/rules. Full native gates mandatory.','variants':outputs},indent=2)+'\n')
