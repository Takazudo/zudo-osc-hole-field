import json,hashlib,sys,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
p=Path('.circuit-cache/issue189-jl-corridor-probe.json');probe=json.loads(p.read_text());event=next(e for e in probe['diagnostics'] if e['reason']=='probe_candidate');rows=event['probe_path_nm'];victims=set(event['victims']);source=Path('.circuit-cache/issue189-downloaded/jl-leaf-adopt/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(source.read_text());paths={};switches=[]
for a,b in zip(rows,rows[1:]):
 if a[0]==b[0]:paths.setdefault(a[0],[]).append(LineString([a[1:],b[1:]]))
 else:switches.append(Point(b[1:]))
paths={k:unary_union(v) for k,v in paths.items()};whole=unary_union(list(paths.values()));switches=unary_union(switches);margin=(.1/math.sqrt(2)+.01)*1e6;track_radius=.3e6+margin;via_radius=.5e6+margin;hits=[]
for t in d['tracks']:
 if t['net'] not in victims:continue
 g=LineString([t['a'],t['b']]);near=t['layer'] in paths and g.distance(paths[t['layer']])<=track_radius+t['width']/2
 if near or (not switches.is_empty and g.distance(switches)<=via_radius+t['width']/2):hits.append({'kind':'track','object':t,'length_mm':g.length/1e6})
for v in d['vias']:
 if v['net'] not in victims:continue
 g=Point(v['xy']);near=g.distance(whole)<=track_radius+v['diameter']/2
 if near or (not switches.is_empty and g.distance(switches)<=via_radius+v['diameter']/2):hits.append({'kind':'via','object':v})
out={'status':'BOUNDED GEOMETRIC CORRIDOR SELECTION; NATIVE CUT/REPAIR NOT RUN','input_board_sha256':d['board_sha256'],'input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'target':event['net'],'endpoints':event['endpoints'],'victims':sorted(victims),'probe_path_nm':rows,'selection_clearance_mm':.2,'selection_track_width_mm':.2,'selection_via_diameter_mm':.6,'raster_margin_mm':margin/1e6,'selected_objects':hits,'removed_source_uuids':sorted(x['object']['uuid'] for x in hits)}
Path('.circuit-cache/issue189-jl-corridor-selection.json').write_text(json.dumps(out,indent=2)+'\n');print('selected',len(hits),'objects; nets',sorted({x['object']['net'] for x in hits}),'longest segment',max([x.get('length_mm',0) for x in hits]));print('total victim objects',sum(t['net'] in victims for k in ['tracks','vias'] for t in d[k]))
