"""Explain observed masks with source object stamps; never propose copper."""
import hashlib
import json

import numpy as np
from scipy import ndimage


def seal(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def sites(mask, raster, origin):
    cells = np.argwhere(mask)
    rows = cells.tolist()
    return {'count': len(rows), 'sorted_yx_sha256': seal(rows),
            'sample_cells_yx': rows[:5],
            'sample_xy_nm': [list(raster.point(y + origin[0], x + origin[1])) for y, x in rows[:5]]}


def reachable_mask(free, source):
    labels, _ = ndimage.label(free | source, np.ones((3, 3), int))
    ids = np.unique(labels[source]); ids = ids[ids != 0]
    return np.isin(labels, ids) if len(ids) else np.zeros_like(free)


def explain(context, free, via_ok, source):
    """Attribute every effective blocker in two exact site sets, with overlap.

    Context is read from the intercepted source router's search frame. Stamps
    use that router's Raster methods and effective foreign/fixed label masks.
    Distances use the identical guarded crop, thresholds and strict comparison.
    A row is a contributing object, not a proposed cut or a minimum cut set.
    """
    r = context['raster']; win = context['win']; inner = context['inner']
    g0, g1, h0, h1 = (context[k] for k in ('g0', 'g1', 'h0', 'h1'))
    origin = (int(win[0].start), int(win[1].start))
    li = r.layers.index('F.Cu'); reached = reachable_mask(free[li], source[li])
    frontier = ndimage.binary_dilation(reached, np.ones((3, 3), bool)) & ~reached & ~free[li]
    queries = {'reachable_frontier': frontier,
               'reachable_rejected_via': reached & free[li] & ~source[li] & ~via_ok}
    guard_shape = (g1-g0, h1-h0); crop = (slice(g0, g1), slice(h0, h1))
    thresholds = {'track': context['clearance'] + context['w']/2 + context['margin'],
                  'via': context['clearance'] + context['vr'] + context['margin'],
                  'smd': context['vr'] + context['margin'],
                  'hole': context['vr'] + context['hole_clearance'] + context['margin']}
    totals = {key: np.zeros_like(value) for key, value in queries.items()}
    rows = []

    def add(identity, rule, occupied, threshold, categories, layers=None):
        if not occupied.any():
            return
        blocked = (ndimage.distance_transform_edt(~occupied)*r.res < threshold)[inner]
        hits = {key: queries[key] & blocked for key in categories}
        if not any(m.any() for m in hits.values()):
            return
        for key, m in hits.items(): totals[key] |= m
        rows.append({**identity, 'rule': rule, 'threshold_mm': threshold,
                     'obstacle_layers': layers, 'sites': {k: sites(m, r, origin) for k, m in hits.items() if m.any()}})

    def stamp(mask, sl):
        full = np.zeros((r.h, r.w), bool); full[sl] |= mask
        return full[crop]

    for kind in ('pads', 'tracks', 'vias'):
        for index, obj in enumerate(r.dump[kind]):
            growth = r.grow.get(obj['net'], 0)
            if kind == 'pads':
                if not obj['poly']: continue
                m, sl = r.polygon(obj['poly'], growth*1e6)
                layers = obj['layers']
            elif kind == 'tracks':
                m, sl = r.segment_mask(obj['a'], obj['b'], obj['width']+2e6*growth)
                layers = [obj['layer']]
            else:
                m, sl = r.disc(obj['xy'], obj['diameter']/2+1e6*growth)
                layers = list(r.layers)
            if not m.any(): continue
            occupied = stamp(m, sl)
            if not occupied.any(): continue
            identity = {'object_type': kind[:-1], 'uuid': obj['uuid'], 'source_row_index': index,
                        'source_row_sha256': seal(obj), 'net': obj['net'], 'rail_growth_mm': growth,
                        'raster_half_diagonal_mm': r.res/np.sqrt(2),
                        **({'ref': obj['ref'], 'pad': obj['pad']} if kind == 'pads' else {})}
            if kind == 'pads' and not obj['drill']:
                add(identity, 'smd_pad_via_prohibition', occupied, thresholds['smd'], ['reachable_rejected_via'], layers)
            value = r.net_id.get(obj['net'], -1)
            if value != context['N']:
                effective = np.zeros(guard_shape, bool)
                for layer in layers:
                    k = r.layers.index(layer)
                    visible = (r.label[k][crop] == value) | (r.fixed_label[k][crop] == value)
                    effective |= occupied & visible
                    if k == li:
                        add(identity, 'same_layer_foreign_copper_track_clearance', occupied & visible,
                            thresholds['track'], ['reachable_frontier'], [layer])
                add(identity, 'all_layer_foreign_copper_via_clearance', effective,
                    thresholds['via'], ['reachable_rejected_via'], layers)
            if obj.get('drill', 0):
                m, sl = r.disc(obj['xy'], obj['drill']/2)
                add(identity, 'drill_via_clearance', stamp(m, sl), thresholds['hole'], ['reachable_rejected_via'], layers)

    yy, xx = np.indices((r.h, r.w))
    fence_distance = np.minimum.reduce([yy, xx, r.h-1-yy, r.w-1-xx])*r.res
    for key, query in queries.items():
        radius = context['w']/2 if key == 'reachable_frontier' else context['vr']
        threshold = context['edge_clearance'] + radius + context['margin']
        fence_hit = query & (fence_distance[win] < threshold)
        outline_hit = query & (r.d_edge[win] < threshold) & ~fence_hit
        for kind, hit in [('computational_boundary_fence', fence_hit), ('board_outline', outline_hit)]:
            if hit.any():
                totals[key] |= hit
                rows.append({'object_type': kind, 'uuid': None, 'rule': kind + '_clearance',
                             'threshold_mm': threshold, 'sites': {key: sites(hit, r, origin)}})
    for index, obj in enumerate(r.dump['keepouts']):
        if len(obj['poly']) < 3 or obj.get('name') == 'NECKDOWN' or str(obj.get('name', '')).endswith(':neckdown'):
            continue
        m, sl = r.polygon(obj['poly'])
        identity = {'object_type': 'keepout', 'uuid': obj.get('uuid'), 'name': obj.get('name'),
                    'source_row_index': index, 'source_row_sha256': seal(obj)}
        occupied = stamp(m, sl)
        if obj['tracks'] and 'F.Cu' in obj['layers']:
            add(identity, 'track_keepout_clearance', occupied, context['w']/2 + context['margin'], ['reachable_frontier'], obj['layers'])
        if obj['vias']:
            add(identity, 'via_keepout_clearance', occupied, context['vr'] + context['margin'], ['reachable_rejected_via'], obj['layers'])
    return {'layer': 'F.Cu', 'window_origin_yx': list(origin),
            'window_lattice_origin_xy_nm': list(r.point(*origin)),
            'site_sets': {k: sites(m, r, origin) for k, m in queries.items()},
            'unattributed_sites': {k: sites(m & ~totals[k], r, origin) for k, m in queries.items()},
            'site_seal_format': 'SHA256 of compact JSON sorted row-major local [y,x] pairs; samples are first five',
            'overlap_policy': 'All contributing effective object rows retained; counts overlap and are not additive; repeated UUIDs retain source row identity',
            'zone_pours': 'IGNORED by this router mask; no poured-zone obstruction or connectivity claim',
            'rules_mm': thresholds, 'blockers': rows}


def existing_anchors(context, free, source, dump, target):
    """Optimistic same-layer distinct-component reachability; no new via/search."""
    from scripts.pcbgen.grid_router import island_mask
    r = context['raster']; win = context['win']; li = r.layers.index('F.Cu')
    objects = [(kind[:-1], i, obj) for kind in ('pads', 'tracks', 'vias') for i, obj in enumerate(dump[kind])]
    rows = []
    for group in dump['islands']['AGND']:
        if set(group) == set(target): continue
        group_set = set(group); goal = island_mask(r, dump, group)[:, win[0], win[1]]
        reachable = reachable_mask(free[li] | goal[li], source[li])
        hits = reachable & goal[li]
        anchors = []
        for kind, index, obj in objects:
            if obj['uuid'] not in group_set: continue
            row_dump = {name: [obj] if name == kind + 's' else [] for name in ('pads', 'tracks', 'vias')}
            mask = island_mask(r, row_dump, [obj['uuid']])[:, win[0], win[1]]
            local = mask[li]
            if not local.any(): continue
            anchors.append({'object_type': kind, 'uuid': obj['uuid'], 'source_row_index': index,
                            'source_row_sha256': seal(obj), 'through_copper': kind == 'via' or len(obj.get('layers', [])) == len(r.layers),
                            'reachable_cells': int((hits & local).sum())})
        if not anchors: continue
        rows.append({'original_all_member_count': len(group), 'original_sorted_members': sorted(group),
                     'original_sorted_members_sha256': hashlib.sha256(json.dumps(sorted(group), separators=(',', ':')).encode()).hexdigest(),
                     'goal_cells': int(goal[li].sum()), 'reachable_goal_cells': int(hits.sum()), 'anchors': anchors})
    return {'goal_model': 'existing distinct original AGND components, including through-copper anchors; free OR source OR per-component goal, eight-neighbour F.Cu flood',
            'allocation_shape': [r.h, r.w], 'window_shape': list(free.shape),
            'computational_window_mm': 100,
            'changed_scope': 'separate full-allocation mask capture; computational window enlarged to clip at allocation, unlike original 3/6 mm observations; physical geometry/rules unchanged',
            'same_component_is_progress': False, 'search_executed': False, 'native_executed': False,
            'classification': 'distinct existing AGND goal reachable in optimistic mask; route/native legality unresolved' if any(row['reachable_goal_cells'] for row in rows) else 'no distinct existing AGND goal reachable in tested allocation mask',
            'components': rows}
