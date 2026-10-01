"""Paid inner-layer exits across unchanged outer power-land collars."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon
from scripts.pcbgen.propose_rail_transfers import geometry, drill_geometry


def propose(source, output):
    data = json.loads(source.read_text()); routing = data['routing']
    rules = next(r for r in routing['net_classes'] if r['name'] == 'Rails')
    items = [{**r, 'shapes': {l: geometry(p) for l, p in r['copper'].items()}} for r in data['items']]
    zones = [{**r, 'shape': geometry(r['contours'])} for r in data['zones']]
    outline = Polygon(data['outline_mm'])
    edge_clearance = data['native_project_rules']['min_copper_edge_clearance']
    layer_clearance = {r['layer']: r.get('minimum_copper_clearance_mm', rules['clearance_mm'])
                       for r in data['stackup']}
    radius, drill = rules['via_diameter_mm']/2, rules['via_drill_mm']
    holes = shapely.union_all([drill_geometry(h).buffer(drill/2+.252) for h in data['holes']])
    bridges = []; unresolved = []
    for net, layer in (('+12V', 'F.Cu'), ('+5V', 'B.Cu')):
        main = set(data['main_rail_members'][net])
        lands = [i for i in items if i.get('uuid') in main and i['net'] == net and
                 set(i['shapes']) == {'B.Cu'} and abs(i['shapes']['B.Cu'].area-16) < 1e-5]
        if len(lands) != 1:
            raise ValueError('one exact native 4x4 rail land required')
        land = lands[0]; centre = tuple(land['shapes']['B.Cu'].centroid.coords[0])
        plane = shapely.union_all([z['shape'] for z in zones if not z['keepout'] and z['net'] == net and z['layer'] == layer])
        # The destination must lie in a broad outer conductor, not the same
        # isolated land island enclosed by its mechanical collar.
        plane = shapely.union_all([p for p in shapely.get_parts(plane) if p.area > 100])
        obstacles = {l: shapely.union_all([i['shapes'][l] for i in items if i['net'] != net and l in i['shapes']])
                     for l in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}
        via_allowed = outline.buffer(-radius-edge_clearance-.002).intersection(plane.buffer(-radius-.002)).difference(
            shapely.union_all([v.buffer(radius+max(rules['clearance_mm'],layer_clearance[l])+.002) for l,v in obstacles.items()]+
                [z['shape'].buffer(radius+.002) for z in zones if z['keepout'] and z['vias_forbidden']]+[holes]))
        shapely.prepare(via_allowed)
        choices = []
        capture = LineString([(centre[0]-.2, centre[1]), (centre[0]+.2, centre[1])])
        capture_shape = capture.buffer(2.4)
        if not outline.buffer(-edge_clearance-.002).covers(capture_shape) or obstacles['In2.Cu'].buffer(.252).intersects(capture_shape):
            unresolved.append({'net': net, 'land_uuid': land['uuid'], 'centre_mm': centre,
                               'reason': 'No 4.8mm finite capture conductor for all 25 existing land vias.'})
            continue
        for width in (4.8, 4., 3.2, 2.4):
            allowed = outline.buffer(-width/2-edge_clearance-.002).difference(shapely.union_all(
                [obstacles['In2.Cu'].buffer(width/2+.252)]+[z['shape'].buffer(width/2+.002)
                 for z in zones if z['keepout'] and z['layer'] == 'In2.Cu' and z['tracks_forbidden']]))
            shapely.prepare(allowed)
            for columns, rows in ((5, 5), (4, 4), (3, 3), (3, 2)):
                if 2*math.hypot((columns-1)*.35, (rows-1)*.35)+2*radius > width+.001:
                    continue
                for dx in tuple(v/2 for v in range(-24, 25)):
                    for dy in (0., -1., -2., -3., -4., -6., -8.):
                        if math.hypot(dx, dy) < 3.5:
                            continue
                        end = (centre[0]+dx, centre[1]+dy)
                        points = [(end[0]+(i-(columns-1)/2)*.7, end[1]+(j-(rows-1)/2)*.7)
                                  for i in range(columns) for j in range(rows)]
                        if not all(shapely.covers(via_allowed, Point(p)) for p in points):
                            continue
                        line = LineString([centre, end])
                        if not shapely.covers(allowed, line):
                            continue
                        # Ranking only. Final resistance uses actual copper,
                        # both transfer arrays and the selected finite stack.
                        score = .000295*line.length/width+.001402/(columns*rows)
                        choices.append((score, width, end, points, columns, rows, line.length))
        if not choices:
            unresolved.append({'net': net, 'land_uuid': land['uuid'], 'centre_mm': centre,
                               'reason': 'No all-layer-clear standard-via array and finite In2 bridge found in the explicit local envelope.'})
            continue
        score, width, end, points, columns, rows, length = min(choices, key=lambda r: r[0])
        bridges.append({'net': net, 'land_uuid': land['uuid'], 'start_mm': centre, 'end_mm': end,
            'track_layer': 'In2.Cu', 'width_mm': width, 'length_mm': length, 'destination_layer': layer,
            'finite_main_capture_points_mm': list(capture.coords), 'finite_main_capture_width_mm': 4.8,
            'via_positions_mm': points, 'array_columns': columns, 'array_rows': rows,
            'via_diameter_mm': radius*2, 'via_drill_mm': drill,
            'ranking_ohm_not_acceptance': score})
        via_shape = shapely.union_all([Point(p).buffer(radius+.002, quad_segs=32) for p in points])
        items.append({'net': net, 'shapes': {l: via_shape for l in obstacles}})
        items.append({'net': net, 'shapes': {'In2.Cu': LineString([centre, end]).buffer(width/2+.002)}})
        items.append({'net': net, 'shapes': {'In2.Cu': capture_shape}})
        holes = holes.union(shapely.union_all([Point(p).buffer(drill+.252) for p in points]))
    output.write_text(json.dumps({'status': 'DISPOSABLE SOURCE PROPOSAL; native and resistance gates pending',
        'board_id': data['board_id'], 'board_sha256': data['board_sha256'],
        'coordinate_frame': data['coordinate_frame'],
        'native_geometry_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'bridges': bridges, 'unresolved': unresolved,
        'preserved': 'Exact 4x4 lands, original arrays, collar keepouts, owner copper and all physical hardware'}, indent=2, sort_keys=True)+'\n')
    print('Terminal bridge proposals:', len(bridges), 'unresolved:', len(unresolved), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args(); propose(args.source, args.output)
