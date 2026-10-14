"""Exact E16 U2314 via policy. Source semantics only; native encoding is blocked.

The barrel wall remains copper on the omitted foil. ``layers`` always describes
physical through-barrel extent, never the set of flashed annuli. A source audit
is computed from all original objects; an operator's nonfunctional label is not
accepted as evidence. No production CLI or execution authority is supplied.
"""
import copy
import hashlib
import json
import math

from shapely.geometry import LineString, Point, Polygon

VIA_ID = '1e1b90ef-f82d-5e94-a82e-416153b33ef3'
PAD_ID = '118acdfc-28df-5ad2-b843-3daccc68d853'
LAYER = 'In3.Cu'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
FIELD = 'selective_annulus'
WALL_MM = .025  # Existing connectivity/finite model assumption; not process qualification.


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def original(obj):
    return {k: v for k, v in obj.items() if k != FIELD}


def validate_object(obj):
    """Refuse unknown identity, foil, geometry, broad/global or contradictory policy."""
    if FIELD not in obj:
        return
    p = obj[FIELD]
    need(isinstance(p, dict) and set(p) == {'schema', 'via_id', 'omit_layer',
         'original_via_sha256', 'original_objects_sha256', 'contact_audit_sha256'},
         'unsupported selective annulus fields')
    need(p['schema'] == 'e16-selective-annulus-v1' and p['via_id'] == obj['id'] == VIA_ID
         and p['omit_layer'] == LAYER, 'unknown selective annulus identity/layer')
    need(obj['kind'] == 'via' and obj['net'] == 'AGND' and obj['layers'] == LAYERS
         and obj.get('via_type', 'through') == 'through'
         and obj['center_mm'] == [110.245, 184.97] and obj['diameter_mm'] == .6
         and obj['drill_mm'] == .3 and obj.get('access_for_pad') == PAD_ID
         and obj.get('epoch') == 'E16' and obj.get('via_in_pad') is True,
         'selective annulus changes protected via geometry/net/contact')
    need(not any(k in obj for k in ('padstack', 'remove_unused_layers', 'keep_end_layers')),
         'global or custom padstack policy is unsupported')
    for key in ('original_via_sha256', 'original_objects_sha256', 'contact_audit_sha256'):
        need(isinstance(p[key], str) and len(p[key]) == 64
             and all(c in '0123456789abcdef' for c in p[key]), 'invalid annulus binding')
    need(digest(original(obj)) == p['original_via_sha256'], 'original via binding changed')


def diameter(obj, layer):
    """Foil projection outer diameter; physical drill and axial barrel are unchanged."""
    validate_object(obj)
    if FIELD in obj:
        need(layer in LAYERS, 'explicit known foil required for selective annulus')
        if layer == LAYER:
            return obj['drill_mm'] + 2 * WALL_MM
    return obj['diameter_mm']


def source_contact_audit(source):
    """Conservative original In3 contact proof; no clipping, routing or graph rebuild.

E16 AGND sheets are on In1, never In3. The complete normalized object inventory
includes other AGND traces/pads/vias; any contact (including tangency) refuses.
This proves the local source contact absence only, not native connectivity.
"""
    objects = [original(o) for o in source['objects']]
    ids = [o['id'] for o in objects]
    need(len(ids) == len(set(ids)), 'duplicate source identity')
    need(source.get('board') == 'KA', 'selective annulus requires KA')
    byid = dict(zip(ids, objects))
    need(VIA_ID in byid and PAD_ID in byid, 'exact via/access pad absent')
    via, pad = byid[VIA_ID], byid[PAD_ID]
    need(pad['kind'] == 'pad' and pad['net'] == 'AGND' and pad['layers'] == ['B.Cu'],
         'functional access pad identity/net/face changed')
    # Validate immutable intended geometry before constructing any geometry.
    provisional = {'schema': 'e16-selective-annulus-v1', 'via_id': VIA_ID,
        'omit_layer': LAYER, 'original_via_sha256': digest(via),
        'original_objects_sha256': digest(objects), 'contact_audit_sha256': '0' * 64}
    validate_object(dict(via, **{FIELD: provisional}))
    for cap in source.get('staged_cap_solids', {}).get('caps', []):
        need(not (cap.get('net') == 'AGND' and cap.get('layer') == LAYER),
             'unsupported AGND In3 staged cap contact inventory')
    ring = Point(via['center_mm']).buffer(via['diameter_mm'] / 2, quad_segs=32)
    inspected = []
    for o in objects:
        if o['id'] == VIA_ID or o.get('net') != 'AGND' or LAYER not in o.get('layers', []):
            continue
        need(o['kind'] in ('via', 'pad', 'segment'), 'unknown same-net In3 conductor')
        if o['kind'] == 'via':
            g = Point(o['center_mm']).buffer(o['diameter_mm'] / 2, quad_segs=32)
        elif o['kind'] == 'pad':
            g = Polygon(o['polygon_mm'], o.get('holes_mm', []))
        else:
            g = LineString(o['path_mm']).buffer(o['width_mm'] / 2, quad_segs=32)
        need(g.is_valid and not g.is_empty, 'invalid contact audit geometry')
        # Buffer outward by polygon sagitta so inscribed circles cannot hide contact.
        margin = (via['diameter_mm'] + max(o.get('diameter_mm', 0), o.get('width_mm', 0))) / 2 * (1 - math.cos(math.pi / 128))
        distance = ring.distance(g)
        need(distance > margin + 1e-9, 'functional or tangent In3 contact: ' + o['id'])
        inspected.append({'id': o['id'], 'distance_mm': distance})
    return {'schema': 'e16-annulus-contact-audit-v1', 'via_id': VIA_ID, 'layer': LAYER,
            'original_objects_sha256': digest(objects), 'same_net_candidates': inspected,
            'same_net_contacts': [], 'sheet_scope': 'E16 fixed AGND sheet on In1.Cu only',
            'barrel_outer_diameter_mm': via['drill_mm'] + 2 * WALL_MM,
            'native_acceptance': 'NOT RUN'}


def apply(source):
    """Apply exactly one policy, preserving every other object byte-for-byte in JSON."""
    out = copy.deepcopy(source)
    policies = [o for o in out['objects'] if FIELD in o]
    if policies:
        validate_source(out)
        return out
    audit = source_contact_audit(out)
    via = next(o for o in out['objects'] if o['id'] == VIA_ID)
    via[FIELD] = {'schema': 'e16-selective-annulus-v1', 'via_id': VIA_ID,
                  'omit_layer': LAYER, 'original_via_sha256': digest(via),
                  'original_objects_sha256': audit['original_objects_sha256'],
                  'contact_audit_sha256': digest(audit)}
    validate_source(out)
    return out


def validate_source(source, planes=None):
    policies = [o for o in source['objects'] if FIELD in o]
    if not policies:
        return
    need(len(policies) == 1, 'exactly one selective annulus allowed')
    if planes is not None:
        need(not planes.get('new_objects'), 'selective annulus requires empty supplemental object inventory')
        need(all(p.get('layer', 'In1.Cu') == 'In1.Cu'
                 for p in planes.get('clipped_sheets', {}).get('AGND', [])),
             'unsupported AGND sheet layer in selective annulus audit')
    via = policies[0]
    validate_object(via)
    audit = source_contact_audit(source)
    need(via[FIELD]['original_objects_sha256'] == audit['original_objects_sha256']
         and via[FIELD]['contact_audit_sha256'] == digest(audit),
         'selective annulus full-source/contact binding changed')


def require_native_supported(obj):
    if FIELD in obj:
        validate_object(obj)
        raise ValueError('UNSUPPORTED_NATIVE_SELECTIVE_ANNULUS: KiCad 10.0.6 has no '
                         'proven exact per-layer no-flash encoding; global removal, '
                         'zone overrides and diameter substitutions are not accepted')
