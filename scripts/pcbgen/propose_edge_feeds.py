"""Bounded explicit two-face escapes for native edge load clusters.

A finite grid searches contained segment candidates only; every final segment
and via is checked against exact native copper/keepouts. No native connectivity
or resistance claim follows from finding a path. The full KiCad gate follows.
"""
import argparse
import hashlib
import heapq
import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box

from scripts.pcbgen.propose_rail_transfers import geometry, drill_geometry, LAYERS, widen_path


def propose(source, output, radius=6., pitch=.1):
    data = json.loads(source.read_text()); tolerance = .002
    edge_clearance = data['native_project_rules']['min_copper_edge_clearance']
    items = [{**i, 'shapes': {l: geometry(p) for l, p in i['copper'].items()}} for i in data['items']]
    zones = [{**z, 'shape': geometry(z['contours'])} for z in data['zones']]
    outline = Polygon(data['outline_mm']); added = []; unresolved = []; rules_by_net = {}
    for cluster in data['clusters']:
        if cluster['fed']:
            continue
        net = cluster['net']; rules = next(r for r in data['routing']['net_classes'] if net in r['nets'])
        rules_by_net[net] = rules; width = rules['local_escape_track_width_mm']; via_radius = rules['via_diameter_mm']/2
        exceptions = [r for r in data['routing'].get('local_escape_overrides',[]) if r['net']==net and
                      any(p['ref']==r['ref'] and p['pad']==r['pad'] for p in cluster['pads'])]
        if exceptions:
            if len(cluster['pads']) != 1 or len(exceptions) != 1:
                raise ValueError('explicit escape override must name one exact load pad')
            width = exceptions[0]['width_mm']; radius = exceptions[0]['maximum_search_radius_mm']
        obstacles = {l: shapely.union_all([i['shapes'][l] for i in items if i['net'] != net and l in i['shapes']]) for l in LAYERS}
        via_forbidden = shapely.union_all([p.buffer(via_radius+(.35 if l == 'In1.Cu' else rules['clearance_mm'])+tolerance) for l,p in obstacles.items()]+
            [z['shape'].buffer(via_radius+tolerance) for z in zones if z['keepout'] and z['vias_forbidden']]+
            [drill_geometry(h).buffer(rules['via_drill_mm']/2+.25+tolerance) for h in data['holes']])
        via_allowed = outline.buffer(-via_radius-edge_clearance-tolerance).difference(via_forbidden)
        allowed = {}; wide_allowed = {}
        for l in ('F.Cu', 'B.Cu'):
            for w, result in ((width, allowed), (rules['track_width_mm'], wide_allowed)):
                forbidden = shapely.union_all([obstacles[l].buffer(w/2+rules['clearance_mm']+tolerance)]+
                    [z['shape'].buffer(w/2+tolerance) for z in zones if z['keepout'] and z['tracks_forbidden'] and z['layer'] == l])
                result[l] = outline.buffer(-w/2-edge_clearance-tolerance).difference(forbidden)
                shapely.prepare(result[l])
        target_layer = next(l for z in data['routing']['zones'] if z['net'] == net for l in z['layers'])
        inner_target = target_layer not in allowed
        target = shapely.union_all([z['shape'] for z in zones if not z['keepout'] and z['net'] == net and z['layer'] == target_layer]).buffer(-(via_radius if inner_target else width/2)-tolerance)
        found = None
        for pad in cluster['pads']:
            start = np.asarray(pad['xy_mm']); n = int(radius/pitch); side = 2*n+1
            indices = np.arange(-n, n+1); gx, gy = np.meshgrid(indices, indices)
            points = shapely.points(np.column_stack((start[0]+pitch*gx.ravel(), start[1]+pitch*gy.ravel())))
            available = {l: shapely.covers(shape, points).reshape(side, side) for l, shape in allowed.items()}
            bridges = shapely.covers(via_allowed, points).reshape(side, side)
            goals = shapely.covers(target, points).reshape(side, side)
            layer_names = ('F.Cu', 'B.Cu'); target_index = None if inner_target else layer_names.index(target_layer)
            queue = []; costs = {}; previous = {}
            for layer in pad['layers']:
                if layer in layer_names and available[layer][n,n]:
                    node = (layer_names.index(layer), n, n); costs[node] = 0.; heapq.heappush(queue, (0., node))
            terminal = None
            while queue:
                cost, node = heapq.heappop(queue)
                if cost != costs[node]:
                    continue
                layer, iy, ix = node
                if goals[iy, ix] and ((inner_target and bridges[iy,ix]) or layer == target_index):
                    terminal = node; break
                neighbors = []
                for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                    yy, xx = iy+dy, ix+dx
                    if 0 <= yy < side and 0 <= xx < side and available[layer_names[layer]][yy,xx]:
                        a = start+pitch*np.array([ix-n,iy-n]); b = start+pitch*np.array([xx-n,yy-n])
                        if allowed[layer_names[layer]].covers(LineString([a,b])):
                            neighbors.append(((layer,yy,xx), pitch*math.hypot(dx,dy)))
                if not inner_target and bridges[iy,ix] and available[layer_names[1-layer]][iy,ix]:
                    # Finite full-thickness via ranking; actual model charges
                    # its layer spans and all current sharing independently.
                    penalty = .07*1.6*width/(math.pi*rules['via_drill_mm']*.025)
                    neighbors.append(((1-layer,iy,ix), penalty))
                for neighbor, length in neighbors:
                    new = cost+length
                    if new < costs.get(neighbor, math.inf):
                        costs[neighbor] = new; previous[neighbor] = node; heapq.heappush(queue,(new,neighbor))
            if terminal is None:
                continue
            route = [terminal]
            while route[-1] in previous:
                route.append(previous[route[-1]])
            route.reverse()
            via_nodes = [route[-1]] if inner_target else [a for a,b in zip(route,route[1:]) if a[0] != b[0]]
            if len(via_nodes) != 1:
                raise ValueError('bounded edge feed must use exactly one physical via')
            via = start+pitch*np.array([via_nodes[0][2]-n,via_nodes[0][1]-n])
            result_points = []; result_widths = []; result_layers = []
            for layer in dict.fromkeys((route[0][0], route[-1][0])):
                local = [start+pitch*np.array([x-n,y-n]) for l,y,x in route if l == layer]
                # Greedy line-of-sight reduction retains exact containment.
                simplified = [local[0]]; index = 0
                while index < len(local)-1:
                    end = next(j for j in range(len(local)-1,index,-1) if allowed[layer_names[layer]].covers(LineString([local[index],local[j]])))
                    simplified.append(local[end]); index = end
                widened, widths = widen_path(simplified,width,rules['track_width_mm'],wide_allowed[layer_names[layer]])
                result_points.extend(widened if not result_points else widened[1:])
                result_widths.extend(widths); result_layers.extend([layer_names[layer]]*len(widths))
            found = {'cluster':cluster['id'],'net':net,'pad':pad,'layer':layer_names[route[0][0]],
                'points_mm':[list(map(float,p)) for p in result_points],'segment_layers':result_layers,'segment_widths_mm':result_widths,
                'width_mm':width,'via_diameter_mm':rules['via_diameter_mm'],'via_drill_mm':rules['via_drill_mm'],
                'via_xy_mm':via.tolist(),'target_kind':'finite two-face bridge to native own-net plane',
                'length_mm':sum(math.dist(a,b) for a,b in zip(result_points,result_points[1:])),
                'search_radius_mm':radius,'search_pitch_mm':pitch}
            break
        if found:
            added.append(found)
        else:
            unresolved.append(cluster)
        print(net, [p['ref'] for p in cluster['pads']], 'found' if found else 'unresolved', flush=True)
    output.write_text(json.dumps({'status':'DISPOSABLE explicit finite edge feeds; native/electrical gates pending',
        'board_id':data['board_id'],'board_sha256':data['board_sha256'],
        'geometry_export_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rules_by_net':rules_by_net,'local_escape_overrides':data['routing'].get('local_escape_overrides',[]),
        'added':added,'unresolved':unresolved},indent=2,sort_keys=True)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('source',type=Path); parser.add_argument('output',type=Path)
    args=parser.parse_args(); propose(args.source,args.output)
