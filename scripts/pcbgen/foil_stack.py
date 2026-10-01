"""Explicit physical foil identities and positive nominal depth bands.

Copper weight labels alone do not specify this conditional conductor geometry.
The same contract is used by native metadata and numerical extraction.
"""
import math

FOIL_ORDERS = {2: ('F.Cu', 'B.Cu'), 4: ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}


def resolve_stack(rows, total_depth=None):
    names = tuple(r['layer'] for r in rows if r['layer'].endswith('.Cu'))
    if names != FOIL_ORDERS.get(len(names)) or len(rows) != 2*len(names)-1:
        raise ValueError('source requires exactly two or four ordered physical copper foils')
    depth = 0.; bands = []; thickness = []
    for index, row in enumerate(rows):
        copper = index % 2 == 0
        if copper != row['layer'].endswith('.Cu'):
            raise ValueError('source copper and dielectric bands must alternate')
        t = float(row['copper_thickness_mm'] if copper else row['thickness_mm'])
        if not math.isfinite(t) or t <= 0:
            raise ValueError('positive finite stack thickness required')
        if copper:
            if row['layer'] != names[index//2]:
                raise ValueError('physical foil ordering differs')
            mid = float(row.get('nominal_midplane_depth_mm', depth+t/2))
            if not math.isfinite(mid) or abs(mid-(depth+t/2)) > 1e-10:
                raise ValueError('source foil depth differs from the complete stack')
            bands.append((mid-t/2, mid+t/2)); thickness.append(t)
        depth += t
    if total_depth is not None:
        total_depth = float(total_depth)
        if not math.isfinite(total_depth) or abs(depth-total_depth) > 1e-10:
            raise ValueError('source stack does not sum to board thickness')
        depth = total_depth
    bands[0] = (0., bands[0][1]); bands[-1] = (bands[-1][0], depth)
    if any(bands[i][1] >= bands[i+1][0] for i in range(len(bands)-1)):
        raise ValueError('physical foil bands require strictly positive dielectric gaps')
    return {'layers': names, 'thickness': thickness, 'bands': bands, 'depth': depth}


def require_native_layers(names, source_names):
    if tuple(names) != tuple(source_names):
        raise ValueError('native enabled copper layers differ from the source stack')
    return tuple(names)


def validate_export_stack(rows, total_depth):
    """Raw native topology exports may retain legacy copper-weight labels.

They do not supply a volume model. Once ANY physical band dimension appears,
the complete positive stack is mandatory; partial dimensions cannot silently
fall back to the legacy path.
"""
    dimensions={'copper_thickness_mm','thickness_mm','nominal_midplane_depth_mm'}
    legacy=(all(r['layer'].endswith('.Cu') and 'copper_oz' in r for r in rows)
            and not any(dimensions.intersection(r) for r in rows))
    if legacy:
        return {'mode':'legacy copper-weight labels only',
                'physical_depth_bands':'UNSPECIFIED; numerical conductor entry prohibited'}
    stack=resolve_stack(rows,total_depth)
    return {'mode':'explicit positive physical bands','layers':list(stack['layers']),
            'bands_mm':stack['bands'],'total_depth_mm':stack['depth']}
