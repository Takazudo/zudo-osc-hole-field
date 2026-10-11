"""Bounded saved-witness terminal adapter; shared grid router remains unchanged."""
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
ROOT = PILOT.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen import grid_router as grid
from exact_access import Geometry, EPS, point


def require(ok, message):
    if not ok:
        raise ValueError(message)


class AccessError(ValueError):
    def __init__(self, message, receipt):
        super().__init__(message)
        self.receipt = receipt


def geometry_gate(geometry, result, reason, xy=None, budget=None):
    if result['pass']: return
    margins = result['checked_margins_mm']
    owners = {}
    if margins.get('foreign_copper') is not None and margins['foreign_copper'] < EPS:
        owners['foreign_copper_uuid'] = result['nearest_foreign']
    if xy is not None and margins.get('existing_hole') is not None and margins['existing_hole'] < EPS:
        q = point(xy)
        owners['existing_hole_uuids'] = [uid for shape, radius, uid in geometry.holes
            if q.distance(shape)-radius-budget['via_diameter_mm']/2-.25 < EPS]
    if xy is not None and margins.get('smd') is not None and margins['smd'] < EPS:
        owners['smd_pad_uuids'] = [uid for shape, uid in geometry.smd if point(xy).distance(shape)-budget['via_diameter_mm']/2 < EPS]
    raise AccessError(reason, {'validation': result, 'failing_owners': owners})


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def saved_pool(report, domain):
    """Same union on both boards; retained geometry is rechecked, never trusted."""
    pool = {}
    for kind, target in domain['targets'].items():
        pool[kind] = {}
        for anchor in target['anchor_records']:
            choices = {}
            for board in ('K1402', 'two-A'):
                demand = next(d for d in report['cohorts']['F3']['boards'][board] if d['kind'] == kind)
                endpoint = next(e for e in demand['endpoints'] if e['uuid'] == anchor['uuid'])
                require(endpoint['layer'] == anchor['layers'][0], 'saved anchor layer drift')
                for field, via in (('edge_witnesses', False), ('edge_and_via_witnesses', True)):
                    require(len(endpoint[field]) <= 3, 'saved witness cap exceeded')
                    for witness in endpoint[field]:
                        row = {'start_nm': [round(v * 1e6) for v in witness['start_mm']],
                               'end_nm': [round(v * 1e6) for v in witness['end_mm']], 'via': via}
                        choices[digest(row)] = row
            pool[kind][anchor['uuid']] = [choices[k] for k in sorted(choices)]
    return pool


def path_check(geometry, path, net, width, budget):
    require(len(path) >= 2, 'empty/trivial attachment')
    for p in path:
        require(len(p) == 4 and p[3] == 0 and p[0] in geometry.layers, 'unexplained through/neck/layer')
        require(all(type(v) is int for v in p[1:3]), 'noninteger emitted coordinates')
    for p, q in zip(path, path[1:]):
        a, b = [v / 1e6 for v in p[1:3]], [v / 1e6 for v in q[1:3]]
        if p[0] == q[0]:
            geometry_gate(geometry, geometry.segment(a, b, net, p[0], width, budget['clearance_mm']), 'foreign/edge/keepout segment collision')
        else:
            require(p[1:3] == q[1:3], 'layer change with unequal XY')
            geometry_gate(geometry, geometry.via(a, net, budget['via_diameter_mm'], budget['via_drill_mm'], budget['clearance_mm']), 'via collision', a, budget)


def portals(physical, target, choices, budget, bounds):
    geometry = Geometry(physical)
    raster = grid.Raster(physical, budget['raster_mm'], bounds_mm=bounds)
    net = target['net_token']
    width = budget['rail_width_mm'] if net in ('+12V', '-12V', '+5V', 'AGND') else budget['signal_width_mm']
    groups, records, rejected = [], {}, []
    for anchor in target['anchor_records']:
        uid = anchor['uuid']; group = []
        require(geometry.pads.get(uid) == anchor, 'original anchor changed')
        for choice in choices[uid]:
            ident = digest({'anchor': uid, 'choice': choice})
            start, end = choice['start_nm'], choice['end_nm']
            layer = anchor['layers'][0]
            path = [[layer, *start, 0], [layer, *end, 0]]
            if choice['via']:
                require('In2.Cu' in raster.layers and layer != 'In2.Cu', 'fixed via handoff layer unavailable')
                layer = 'In2.Cu'
                path.append([layer, *end, 0])
            y, x = raster.cell(*end)
            landing = list(raster.point(y, x))
            path.append([layer, *landing, 0])
            try:
                require(all(bounds[0] <= p[1] / 1e6 <= bounds[2] and bounds[1] <= p[2] / 1e6 <= bounds[3] for p in path), 'attachment outside common bounds')
                require(0 < y < raster.h - 1 and 0 < x < raster.w - 1, 'landing outside raster fence')
                require(geometry.contact(uid, [v / 1e6 for v in start], net, anchor['layers'][0])['pass'], 'named terminal contact failed')
                path_check(geometry, path, net, width, budget)
            except ValueError as error:
                rejected.append({'anchor': uid, 'witness_id': ident, 'reason': str(error), 'failure': getattr(error, 'receipt', None)})
                continue
            # Single-layer, one-lattice-node search marker. Never a physical pad.
            virtual = 'access-' + ident
            px, py = landing
            pad = {'uuid': virtual, 'ref': 'ACCESS', 'pad': virtual, 'net': net,
                   'xy': landing, 'poly': [[px-1, py-1], [px+1, py-1], [px+1, py+1], [px-1, py+1]],
                   'layers': [layer], 'drill': 0, 'npth': False, 'locked': False}
            records[virtual] = {'anchor': uid, 'path': path, 'pad': pad, 'node': (layer, px, py), 'witness_id': ident}
            group.append(virtual)
        groups.append(group)
    return groups, records, rejected


def stitch(raw, groups, records, target):
    """A path must terminate in different real-anchor alternative sets."""
    require(raw and len(raw) >= 1, 'missing grid path')
    require(all(len(p) == 4 and p[3] == 0 for p in raw), 'unexplained synthetic through/neck')
    first, last = tuple(raw[0][:3]), tuple(raw[-1][:3])
    for left, right in ((groups[0], groups[1]), (groups[1], groups[0])):
        a = sorted(u for u in left if records[u]['node'] == first)
        b = sorted(u for u in right if records[u]['node'] == last)
        if a and b:
            sa, sb = records[a[0]], records[b[0]]
            require(sa['anchor'] != sb['anchor'], 'same-anchor fictional join')
            chain = sa['path'] + raw[1:] + list(reversed(sb['path']))[1:]
            return chain, [sa['anchor'], sb['anchor']]
    raise ValueError('grid endpoints are not two named-anchor landings')


def validate_rows(physical, rows, target, budget):
    """Exact emitted geometry plus new-via spacing and real-anchor graph receipt."""
    geometry = Geometry(physical); net = target['net_token']
    original_ids = {o['uuid'] for kind in ('pads', 'tracks', 'vias') for o in physical[kind]}
    new_ids = [r['uuid'] for r in rows]
    require(len(new_ids) == len(set(new_ids)) and not original_ids.intersection(new_ids), 'new copper UUID aliases existing object')
    width = budget['rail_width_mm'] if net in ('+12V', '-12V', '+5V', 'AGND') else budget['signal_width_mm']
    graph = {}; vias = []
    def join(a, b):
        graph.setdefault(a, set()).add(b); graph.setdefault(b, set()).add(a)
    for row in rows:
        require(row['net'] == net and not row['uuid'].startswith('access-'), 'virtual/foreign proposal identity')
        if row['kind'] == 'segment':
            require(row['width_nm'] == round(width * 1e6), 'width relaxation')
            a, b = row['start_nm'], row['end_nm']
            geometry_gate(geometry, geometry.segment([v/1e6 for v in a], [v/1e6 for v in b], net, row['layer'], width, budget['clearance_mm']), 'emitted segment collision')
            join((row['layer'], *a), (row['layer'], *b))
        else:
            require(row['kind'] == 'via' and row['diameter_nm'] == round(budget['via_diameter_mm']*1e6)
                    and row['drill_nm'] == round(budget['via_drill_mm']*1e6), 'via dimension drift')
            xy = [v/1e6 for v in row['at_nm']]
            geometry_gate(geometry, geometry.via(xy, net, budget['via_diameter_mm'], budget['via_drill_mm'], budget['clearance_mm']), 'emitted via collision', xy, budget)
            for previous in vias:
                require(math.dist(previous, xy) >= budget['via_diameter_mm']/2 + budget['via_drill_mm']/2 + .25 + EPS, 'new vias violate existing-hole policy')
            vias.append(xy)
            nodes = [(layer, *row['at_nm']) for layer in geometry.layers]
            for node in nodes[1:]: join(nodes[0], node)
    terminals = []
    for pad in target['anchor_records']:
        terminals.append({node for node in graph if geometry.contact(pad['uuid'], [v/1e6 for v in node[1:]], net, node[0])['pass']})
    require(all(terminals), 'emitted rows miss named terminals')
    reached = set(terminals[0]); todo = list(reached)
    while todo:
        node = todo.pop()
        for neighbor in graph[node] - reached:
            reached.add(neighbor); todo.append(neighbor)
    require(bool(reached & terminals[1]), 'emitted rows do not join named terminals')
    return {'emitted_geometry_connects_named_anchors': True, 'native_exact_pair_closed': False,
            'accepted': False, 'scope': 'Source geometric continuity only; full native closure/preservation gates pending'}


def add_rows(original, rows):
    dump = copy.deepcopy(original)
    for row in rows:
        if row['kind'] == 'segment':
            dump['tracks'].append({'uuid': row['uuid'], 'net': row['net'], 'a': row['start_nm'], 'b': row['end_nm'],
                                   'width': row['width_nm'], 'layer': row['layer']})
        else:
            dump['vias'].append({'uuid': row['uuid'], 'net': row['net'], 'xy': row['at_nm'],
                                 'diameter': row['diameter_nm'], 'drill': row['drill_nm']})
    return dump


def cumulative_fill_ok(original, rows, budget, policy, bounds):
    raster = grid.Raster(original, budget['raster_mm'], bounds_mm=bounds)
    for net, layer in policy['fill_guards'].items():
        if net not in raster.net_id: continue
        li = raster.layers.index(layer)
        guard = grid.FillGuard(raster.label[li], raster.net_id[net], .45, budget['raster_mm'], domain=raster.d_edge > 0)
        pieces = []
        for row in rows:
            if row['kind'] == 'via':
                pieces.append(raster.disc(row['at_nm'], row['diameter_nm']/2))
            elif row['layer'] == layer:
                pieces.append(raster.segment_mask(row['start_nm'], row['end_nm'], row['width_nm'] + 2*raster.step))
        after = guard.partition(guard.shrunk(pieces))
        if grid.splits(guard.base, after) or any(b and not a for b, a in zip(guard.base, after)):
            return False
    return True


def run(original, domain, pool, budget, policy, board, router=grid.route):
    """Only the admitted driver calls this on saved boards. Tests use toy stubs."""
    rows, links, statuses = [], [], []
    for kind in policy['target_order']:
        target = domain['targets'][kind]; net = target['net_token']
        physical = add_rows(original, rows)
        groups, records, rejected = portals(physical, target, pool[kind], budget, domain['common_bounds_mm'])
        status = {'kind': kind, 'net': net, 'anchors': [p['uuid'] for p in target['anchor_records']],
                  'portal_counts': list(map(len, groups)), 'rejected_witnesses': rejected,
                  'search_direction': 'second original anchor toward first; never reverse on availability',
                  'native_exact_pair_closed': False, 'accepted': False}
        if not all(groups):
            status['status'] = 'NO_VALID_SAVED_ACCESS; original demand retained'
            statuses.append(status); continue
        if len(groups[0]) < len(groups[1]):
            status['status'] = 'LANDING_CENSUS_WOULD_REVERSE_SEARCH; original demand retained'
            statuses.append(status); continue
        derived = copy.deepcopy(physical)
        derived['pads'].extend(records[u]['pad'] for group in groups for u in group)
        derived['islands'] = {net: groups}
        diagnostics = []
        results, removed = router(derived, nets=[net], res=budget['raster_mm'], clearance=budget['clearance_mm'],
            rail_nets=policy['rail_nets'], rail_width=budget['rail_width_mm'], signal_width=budget['signal_width_mm'],
            via_diameter=budget['via_diameter_mm'], via_drill=budget['via_drill_mm'],
            max_expansions=budget['max_expansions_per_search'], window_mm=budget['window_margin_mm'],
            bounds_mm=domain['common_bounds_mm'], planes={}, fill_guards=policy['fill_guards'],
            rip=(), full_board=False, rrr_rounds=0, diagnostics=diagnostics, log=lambda s: print(s, flush=True))
        require(not removed and len(results) == 1, 'unexpected router removal/result census')
        status['search_diagnostics'] = diagnostics
        if not results[0]['path']:
            status['status'] = 'NO_GRID_PATH; original demand retained'
            statuses.append(status); continue
        try:
            chain, anchors = stitch(results[0]['path'], groups, records, target)
            bounds = domain['common_bounds_mm']
            require(all(bounds[0] <= p[1]/1e6 <= bounds[2] and bounds[1] <= p[2]/1e6 <= bounds[3] for p in chain), 'complete chain outside common bounds')
            width = budget['rail_width_mm'] if net in policy['rail_nets'] else budget['signal_width_mm']
            path_check(Geometry(physical), chain, net, width, budget)
            result = {'net': net, 'island': [p['ref']+'.'+p['pad'] for p in target['anchor_records']],
                      'path': chain, 'width_nm': round(width*1e6), 'via_diameter_nm': round(budget['via_diameter_mm']*1e6)}
            added, _ = grid.copper_rows([result], 'fixture-253-F3-'+board, 'exact-access-v1-'+kind,
                                      via_diameter=budget['via_diameter_mm'], via_drill=budget['via_drill_mm'])
            continuity = validate_rows(physical, added, target, budget)
            require(cumulative_fill_ok(original, rows+added, budget, policy, domain['common_bounds_mm']), 'cumulative original-baseline fill veto')
        except ValueError as error:
            status.update(status='REJECTED_ATOMICALLY; no stub or grid copper retained', reason=str(error), failure=getattr(error, 'receipt', None))
            statuses.append(status); continue
        rows.extend(added)
        links.append({'net': net, 'island': result['island'], 'anchor_uuids': anchors,
                      'copper_uuids': [r['uuid'] for r in added], 'native_exact_pair_closed': False})
        status.update(status='UNCHECKED_COMPLETE_PAIR_PROPOSAL', continuity=continuity)
        statuses.append(status)
    return {'status': 'UNCHECKED PROPOSAL; all four original native demands and obligations pending',
            'accepted': False, 'adopted': False, 'coupled_connectivity_success': False,
            'board_sha256': original['board_sha256'], 'removed_uuids': [], 'copper': rows, 'links': links,
            'demands': statuses, 'unrouted': [{'net': s['net'], 'island': s['anchors']} for s in statuses if s['status'] != 'UNCHECKED_COMPLETE_PAIR_PROPOSAL']}
