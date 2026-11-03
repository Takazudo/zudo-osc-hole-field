"""Optimistic local additive escape screen; never edits a PCB or proves DRC."""
from pathlib import Path
import hashlib
import json
import sys
from shapely.geometry import Point, Polygon, LineString, box, mapping, shape
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = 'd1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
WINDOW = box(267, 131, 272, 136)
SOURCE = 'b9d402b4-b8c4-5ab2-a8c0-3fd450c4809c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export():
    dump = ROOT / '.circuit-cache/stage45/dump.json'
    fill = ROOT / '.circuit-cache/stage46/filled-B.json'
    d, f = json.loads(dump.read_text()), json.loads(fill.read_text())
    if d['board_sha256'] != BASE or f['board_sha256'] != BASE:
        raise ValueError('wrong native input')
    objects = []
    def add(uid, name, net, layers, geometry):
        if geometry.distance(WINDOW) < 1:
            objects.append(dict(id=uid, name=name, net=net, layers=layers,
                                geometry=mapping(geometry)))
    for p in d['pads']:
        if p['poly']:
            add(p['uuid'], p['ref']+':'+p['pad'], p['net'], p['layers'],
                Polygon([(a/1e6,b/1e6) for a,b in p['poly']]))
    for t in d['tracks']:
        add(t['uuid'],t['uuid'],t['net'],[t['layer']],
            LineString([(a/1e6,b/1e6) for a,b in [t['a'],t['b']]]).buffer(t['width']/2e6, resolution=64))
    for v in d['vias']:
        add(v['uuid'],v['uuid'],v['net'],d['layers'],
            Point(v['xy'][0]/1e6,v['xy'][1]/1e6).buffer(v['diameter']/2e6,resolution=64))
    for i,p in enumerate(f['polygons']):
        g = Polygon(p['shell'],p['holes']).intersection(WINDOW.buffer(1))
        if not g.is_empty:
            add('fill:'+str(i),'B.Cu fill '+str(i),'AGND',['B.Cu'],g)
    return dict(board_sha256=BASE, input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [dump,fill]},
                native_open_edges=f['native_open_edges'], pad_neighbors=f['native_pad_connected_items'],
                area_audit={k:v for k,v in f.items() if k.startswith('area_')},
                witness_count=len(f['witnesses']), witness_mismatches=sum(
                    w['native_hit'] != w['unfractured_contains'] or w['native_hit'] != w['raw_contains'] for w in f['witnesses']),
                objects=objects)


def analyze(data, width=.1, margin=.01):
    objects = [(o,shape(o['geometry'])) for o in data['objects']]
    pad = next(g for o,g in objects if o['id']==SOURCE)
    island = next(g for o,g in objects if o['id'].startswith('fill:') and g.covers(pad.centroid))
    seed = pad.union(island)
    foreign = [(o,g) for o,g in objects if o['net']!='AGND']
    blocked = unary_union([g.buffer(width/2+.25-margin,resolution=64) for o,g in foreign if 'B.Cu' in o['layers']])
    free = WINDOW.difference(blocked)
    parts = list(free.geoms) if hasattr(free,'geoms') else [free]
    reachable = unary_union([g for g in parts if g.intersects(seed.buffer(width/2))])
    targets = unary_union([g for o,g in objects if o['net']=='AGND' and 'B.Cu' in o['layers'] and o['id']!=SOURCE and not g.intersects(seed)])
    via = {}
    for diameter in [.7,.6,.5]:
        forbidden = unary_union([g.buffer(diameter/2+.25-margin,resolution=64) for o,g in foreign])
        # Deliberately generous: pad/island overlap OR overlap with any reachable
        # track disk. This includes off-center via/track contacts and tangencies.
        candidates = reachable.buffer(diameter/2+width/2).union(seed.buffer(diameter/2)).difference(forbidden)
        via[str(diameter)] = dict(empty=candidates.is_empty, area_mm2=candidates.area)
    result = dict(width_mm=width, optimistic_clearance_reduction_mm=margin,
                  source_island_area_mm2=island.area, source_island_bounds=list(island.bounds),
                  reachable_area_mm2=reachable.area, reachable_bounds=list(reachable.bounds),
                  window_boundary_distance_mm=reachable.distance(WINDOW.boundary),
                  other_ground_distance_mm=reachable.buffer(width/2).union(seed).distance(targets), vias=via)
    return result, reachable, objects, seed


def main():
    if '--export' in sys.argv:
        (HERE/'geometry.json').write_text(json.dumps(export(),sort_keys=True,separators=(",",":"))+'\n')
    data=json.loads((HERE/'geometry.json').read_text())
    results=[analyze(data,w,m)[0] for m in [0,.01] for w in [.4,.15,.1]]
    output=json.dumps(results,sort_keys=True,indent=2)+'\n'
    if '--check' in sys.argv:
        if (HERE/'results.json').read_text()!=output: raise ValueError('results drift')
    else: (HERE/'results.json').write_text(output)
    print(output)

if __name__=='__main__': main()
