"""Explicit short power-cluster transfers into existing native rail copper.

Each proposal names its native pad/cluster, finite surface path and plated
transfer. Geometry comes from the pinned native export. The result is not
promoted until native refill, connectivity and full rule/parity checks pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

LAYERS = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')


def geometry(contours):
    polygons = [Polygon(p['shell'], p['holes']) for p in contours]
    if any(not p.is_valid for p in polygons):
        raise ValueError('native export contains invalid copper polygon')
    return shapely.union_all(polygons)


def drill_geometry(hole):
    x, y = hole['xy_mm']; sx, sy = hole['size_mm']
    length = abs(sx - sy)
    angle = math.radians(hole['angle_deg'] + (90 if sy > sx else 0))
    dx, dy = math.cos(angle) * length / 2, math.sin(angle) * length / 2
    centre = LineString([(x-dx, y-dy), (x+dx, y+dy)]) if length else Point(x, y)
    return centre.buffer(min(sx, sy) / 2, quad_segs=32)


def legal_path(start, end, allowed):
    choices = ([start, end], [start, (start[0], end[1]), end],
               [start, (end[0], start[1]), end])
    paths = []
    for points in choices:
        points = [p for i, p in enumerate(points) if i == 0 or p != points[i-1]]
        line = LineString(points)
        if shapely.covers(allowed, line):
            paths.append((line.length, points))
    return min(paths, key=lambda p: p[0]) if paths else None


def widen_path(points, narrow, wide, wide_allowed):
    """Restore the source default width wherever its full clearance fits."""
    result = [points[0]]; widths = []
    for a, b in zip(points, points[1:]):
        line = LineString([a, b]); positions = [0., line.length]
        for point in shapely.get_coordinates(line.intersection(wide_allowed.boundary)):
            positions.append(line.project(Point(point)))
        positions = sorted(set(round(v, 9) for v in positions))
        for lo, hi in zip(positions, positions[1:]):
            if hi-lo < 1e-8:
                continue
            widths.append(wide if wide_allowed.covers(line.interpolate((lo+hi)/2)) else narrow)
            result.append(tuple(line.interpolate(hi).coords[0]))
    return result, widths


def propose(source, output):
    data = json.loads(source.read_text())
    # Extra two micrometres protect polygon and native integer boundaries.
    tolerance = .002
    edge_clearance = data['native_project_rules']['min_copper_edge_clearance']
    outline = Polygon(data['outline_mm'])
    items = [{**i, 'shapes': {layer: geometry(polys) for layer, polys in i['copper'].items()}}
             for i in data['items']]
    zones = [{**z, 'shape': geometry(z['contours'])} for z in data['zones']]
    hole_shapes = [drill_geometry(h) for h in data['holes']]
    added = []; unresolved = []; rules_by_net = {}
    layer_clearance = {r['layer']: r.get('minimum_copper_clearance_mm', 0)
                       for r in data.get('stackup', [])}
    depth = {r['layer']: r['nominal_midplane_depth_mm'] for r in data.get('stackup', [])
             if 'nominal_midplane_depth_mm' in r}
    for net in ('AGND', '+12V', '-12V', '+5V'):
        rules = next(r for r in data['routing']['net_classes'] if net in r['nets'])
        rules_by_net[net] = rules
        width = rules['track_width_mm']; clearance = rules['clearance_mm']
        radius = rules['via_diameter_mm']/2; drill = rules['via_drill_mm']
        drill_exclusion = shapely.union_all([shape.buffer(drill/2+.25+tolerance) for shape in hole_shapes])
        plane_layers = [l for z in data['routing']['zones'] if z['net'] == net for l in z['layers']]
        plane_layer = 'In1.Cu' if net == 'AGND' else plane_layers[0]
        main = set(data['main_rail_members'][net])
        fed_shapes = {l: shapely.union_all([i['shapes'][l] for i in items
                      if i.get('uuid') in main and l in i['shapes']]) for l in LAYERS}
        plane = shapely.union_all([z['shape'] for z in zones
                                  if not z['keepout'] and z['net'] == net and z['layer'] == plane_layer])
        plane = shapely.union_all([p for p in shapely.get_parts(plane) if p.intersects(fed_shapes[plane_layer])])
        fed_shapes[plane_layer] = fed_shapes[plane_layer].union(plane)
        obstacles = {layer: shapely.union_all([i['shapes'][layer] for i in items
                     if i['net'] != net and layer in i['shapes']]) for layer in LAYERS}
        via_forbidden = shapely.union_all([p.buffer(radius + max(clearance, layer_clearance.get(l, 0)) + tolerance) for l,p in obstacles.items()] +
            [z['shape'].buffer(radius + tolerance) for z in zones if z['keepout'] and z['vias_forbidden']] +
            [drill_exclusion])
        via_allowed = outline.buffer(-radius-edge_clearance-tolerance).difference(via_forbidden)
        via_allowed = via_allowed.intersection(plane.buffer(-radius-tolerance))
        track_allowed = {}
        widths = sorted({width, rules.get('local_escape_track_width_mm', width)}, reverse=True)
        for layer in ('F.Cu', 'B.Cu'):
            for candidate_width in widths:
                forbidden = shapely.union_all([obstacles[layer].buffer(candidate_width/2+clearance+tolerance)] +
                    [z['shape'].buffer(candidate_width/2+tolerance) for z in zones
                     if z['keepout'] and z['tracks_forbidden'] and z['layer'] == layer])
                track_allowed[layer, candidate_width] = outline.buffer(-candidate_width/2-edge_clearance-tolerance).difference(forbidden)
                shapely.prepare(track_allowed[layer, candidate_width])
        shapely.prepare(via_allowed)
        for cluster in sorted((r for r in data['clusters'] if r['net'] == net and not r['fed']), key=lambda r: r['id']):
            choices = []
            for pad in cluster['pads']:
                start = tuple(pad['xy_mm'])
                for layer in ('F.Cu', 'B.Cu'):
                    if layer not in pad['layers']:
                        continue
                    allowed_widths = [w for w in widths if track_allowed[layer, w].covers(Point(start))]
                    if not allowed_widths:
                        continue
                    width = allowed_widths[0]
                    if not fed_shapes[layer].is_empty:
                        target = nearest_points(Point(start), fed_shapes[layer])[1]
                        if 1e-6 < Point(start).distance(target) <= 3.5:
                            target_xy = tuple(target.coords[0])
                            direct = legal_path(start, target_xy, track_allowed[layer, width])
                            if direct:
                                choices.append((direct[0], pad['ref'], pad['pad'], layer, pad, None, direct[1], direct[0], width))
                    if layer == plane_layer:
                        continue
                    for distance in (.8, 1.1, 1.5, 2., 2.75, 3.5):
                        for angle in range(0, 360, 15):
                            a = math.radians(angle)
                            end = (round(start[0]+distance*math.cos(a), 6), round(start[1]+distance*math.sin(a), 6))
                            if not shapely.covers(via_allowed, Point(end)):
                                continue
                            path = legal_path(start, end, track_allowed[layer, width])
                            if path:
                                axial_mm = abs(depth[layer]-depth[plane_layer]) if layer in depth and plane_layer in depth else 1.6
                                # Equivalent copper-strip length is ranking
                                # only; authoritative native extraction charges
                                # the complete actual shared access afterward.
                                via_length = .07*axial_mm*width/(math.pi*drill*.025)
                                choices.append((path[0]+via_length, pad['ref'], pad['pad'], layer, pad, end, path[1], path[0], width))
            if not choices:
                distance = min(Point(p['xy_mm']).distance(plane) for p in cluster['pads'])
                unresolved.append({'cluster': cluster['id'], 'net': net, 'pads': cluster['pads'],
                    'nearest_existing_plane_mm': distance,
                    'reason': 'No contained, all-layer-clear local transfer within 3.5 mm; long-feed/source geometry work remains.'})
                continue
            _, _, _, layer, pad, end, points, length, width = min(choices, key=lambda v: v[:4])
            points, segment_widths = widen_path(points, width, rules['track_width_mm'],
                                                track_allowed[layer, rules['track_width_mm']])
            row = {'cluster': cluster['id'], 'net': net, 'pad': pad, 'layer': layer,
                'points_mm': points, 'length_mm': length, 'via_xy_mm': end,
                'segment_widths_mm': segment_widths,
                'width_mm': width, 'via_diameter_mm': radius*2, 'via_drill_mm': drill,
                'target_kind': 'plated plane transfer' if end is not None else 'existing main-connected native copper',
                'plane_layer': plane_layer}
            added.append(row)
            # Subsequent clusters and nets see every new physical conductor.
            track_shape = shapely.union_all([LineString([a, b]).buffer(w/2+tolerance, quad_segs=16)
                for a, b, w in zip(points, points[1:], segment_widths)])
            items.append({'net': net, 'shapes': {layer: track_shape}})
            group = set(cluster['members'])
            for l in LAYERS:
                fed_shapes[l] = shapely.union_all([fed_shapes[l]]+[i['shapes'][l] for i in items
                    if i.get('uuid') in group and l in i['shapes']])
            fed_shapes[layer] = fed_shapes[layer].union(shapely.union_all([
                LineString([a, b]).buffer(w/2) for a, b, w in zip(points, points[1:], segment_widths)]))
            if end is not None:
                via_shape = Point(end).buffer(radius+tolerance, quad_segs=32)
                items.append({'net': net, 'shapes': {l: via_shape for l in LAYERS}})
                hole_shapes.append(Point(end).buffer(drill/2, quad_segs=32))
                via_allowed = via_allowed.difference(Point(end).buffer(drill+.25+tolerance))
                shapely.prepare(via_allowed)
                for l in LAYERS:
                    fed_shapes[l] = fed_shapes[l].union(Point(end).buffer(radius))
        print(net, 'proposed', sum(r['net'] == net for r in added),
              'unresolved', sum(r['net'] == net for r in unresolved), flush=True)
    output.write_text(json.dumps({'status': 'DISPOSABLE EXPLICIT FEED PROPOSAL; native and resistance gates pending',
        'board_id': data['board_id'], 'board_sha256': data['board_sha256'],
        'coordinate_frame': data.get('coordinate_frame', {'name': 'native KiCad millimetres',
                             'source_to_native_translation_mm': [100, 50]}),
        'geometry_export_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'added': added, 'unresolved': unresolved,
        'rules_by_net': rules_by_net, 'source_geometry_unchanged': True}, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    propose(args.source, args.output)
