"""Descriptive current-source windows only: no moved poses or routing."""
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('repair', ROOT/'design/partition/core-split/candidates/pilots/f3-integrator-cluster-v2/repair.py')
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)
paths = ['design/partition/core-split/candidates/two.json',
         'design/partition/core-split/candidates/three.json',
         'design/partition/core-split/candidates/copper-index.jsonl.gz',
         'design/reports/board-net-tokens.json','boards/osc-core/osc-core.kicad_pcb']
hashes = {s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in paths}
read = lambda s:json.loads((ROOT/s).read_text())
names = read('design/reports/board-net-tokens.json')
index = [json.loads(x) for x in gzip.open(ROOT/paths[2],'rt')]
layers = ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
rows,gs,radii,faces,ends = r.load_copper(index,(ROOT/paths[4]).read_text(),layers)
windows = [('N-two-A','two','two-A',[124,88,164,168]),
           ('E-two-A','two','two-A',[164,48,244,168]),
           ('SW-three-B','three','three-B',[4,208,64,288])]
result = {'input_sha256':hashes,'coordinate_frame':'Candidate XY mm; accepted PCB XY = candidate +(100,50)',
          'scope':'Descriptive existing geometry in three predeclared windows; no pose, optimized region, candidate fit or connectivity proof.',
          'windows':[]}
for label,option,bid,rect in windows:
    d = read('design/partition/core-split/candidates/'+option+'.json')
    b = d['boards'][bid]
    window = box(*rect)
    physical = box(rect[0]+100,rect[1]+50,rect[2]+100,rect[3]+50)
    outline = Polygon(b['outline_mm']).buffer(-.30,join_style=2)
    parts = {p['ref']:p for p in b['source_parts']}
    record = {'id':label,'candidate':bid,'rect_mm':rect,'area_mm2':window.area,'faces':{}}
    for face in ('F.Cu','B.Cu'):
        hits = []
        all_courtyards = []
        for p in b['placements']:
            if p['side'] != face:continue
            g = unary_union([Polygon(poly) for poly in p['courtyard_polygons_mm']])
            all_courtyards.append(g)
            area = g.intersection(window).area
            if area > 1e-9:hits.append((p['ref'],g,area))
        reserves = [(q['id'],unary_union([Polygon(poly) for poly in q['polygons']]))
                    for q in b['measurement']['faces'][face]['reservation_polygons_mm']]
        excluded = unary_union([g for _,g in reserves])
        occupied = unary_union([g for _,g,_ in hits])
        leftover = window.intersection(outline).difference(excluded).difference(unary_union(all_courtyards).buffer(.35))
        pieces = [leftover] if leftover.geom_type == 'Polygon' else list(leftover.geoms)
        record['faces'][face] = {
            'courtyard_area_mm2':occupied.intersection(window).area,
            'reservation_area_mm2':excluded.intersection(window).area,
            'unoccupied_after_035_clearance_mm2':leftover.area,
            'largest_connected_polygon_area_mm2':max((x.area for x in pieces),default=0),
            'claim':'Free polygon area is not an inscribed placement envelope or copper-free space; polygonized circular reserves only, no installed fit.',
            'occupied_refs':[{'ref':ref,'module':parts.get(ref,{}).get('module','header_or_mechanical'),
                              'intersection_mm2':area} for ref,_,area in hits],
            'reservations':[{'id':name,'intersection_mm2':g.intersection(window).area}
                            for name,g in reserves if g.intersection(window).area > 1e-9]}
    counts = Counter(); nets = Counter(); touched = []
    for row,g,rad in zip(rows,gs,radii):
        if g.distance(physical) > rad:continue
        owners = d['net_owners'].get(row['net_token'],[])
        cls = ('SHARED_RETURN_SUPPLY' if row['net_token'] in ('AGND','+12V','-12V','+5V') else
               'SAME_CANDIDATE_NET' if owners == [bid[-1]] else
               'OTHER_CANDIDATE_NET' if owners and bid[-1] not in owners else 'UNRESOLVED_OWNERSHIP')
        counts[cls]+=1
        if cls != 'OTHER_CANDIDATE_NET':nets[names.get(row['net_token'],row['net_token'])]+=1
        touched.append([row['source_span'],row['sha256'],cls])
    record['all_layer_source_copper'] = {'by_ownership_class':dict(counts),
        'selector':'Every accepted straight segment/circular via whose width/annulus intersects the physical window; no pad clearances applied. Whole-net candidate ownership is a source filter, not native retention acceptance.',
        'object_multiset_sha256':hashlib.sha256(json.dumps(touched,sort_keys=True).encode()).hexdigest(),
        'leading_retained_or_shared_nets':nets.most_common(8),
        'zones':'All five original zones remain full native refill/continuity obligations; not included in these segment/via counts.'}
    result['windows'].append(record)
for s,h in hashes.items():assert hashlib.sha256((ROOT/s).read_bytes()).hexdigest()==h
(HERE/'source-survey.json').write_text(json.dumps(result,indent=2)+'\n')
for x in result['windows']:
    print(x['id'],{f:{k:round(v,3) for k,v in a.items() if isinstance(v,float)} for f,a in x['faces'].items()}, x['all_layer_source_copper']['by_ownership_class'])
