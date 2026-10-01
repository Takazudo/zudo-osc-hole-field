"""Constructed individual reference cores, not a manufactured wire certificate."""
from fractions import Fraction as F
from scripts.geometry.power_wire import directed, finite, sqrt_interval, registered_endpoint


def number(value, *, positive=False):
    finite(value)
    if positive and value <= 0:
        raise ValueError('positive reference geometry required')
    return F(value)


def vector(value):
    if len(value) != 2:
        raise ValueError('two-dimensional fan coordinates required')
    return tuple(number(v) for v in value)


def squared(v):
    return sum((x*x for x in v), F())


def difference(a, b):
    return tuple(x-y for x, y in zip(a, b))


def bounds(reference, geometry, fan, adapter, current, maximum_cut_mm, preparation_mm=10):
    """Prove a sufficient registered planar class with exact bound arithmetic.

    For a fixed Bishop offset a in the bend plane, ds_core=(1-a*kappa)ds.
    Signed total turn is zero, so every individual bulk centreline has length L.
    The whole tube is injective by strict convexity of squared distance to its
    monotone-depth graph; this is stronger than a positive local Jacobian alone.
    """
    if (reference['profile'] != 'registered-planar-smoothstep'
            or not reference['bulk_curve_bounds']['axial_endpoint_tangents']
            or reference['endpoint_reference']['adapter_tilt_deg'] != 0
            or not reference['endpoint_reference']['registered_trial_cuts']):
        raise ValueError('registered planar axial endpoints required')
    if reference['endpoint_reference'] != registered_endpoint(fan, adapter):
        raise ValueError('endpoint reference differs from fan/adapter source')
    if not fan['tip_inside_fanned_length']:
        raise ValueError('tip must be inside the fan length allocation')
    if geometry['stage_heights_mm'] != [fan['initial_expansion_height_mm'], fan['main_fan_height_mm']]:
        raise ValueError('fan stage heights differ from source')
    count = current['contained_core_count']
    if isinstance(count, bool) or not isinstance(count, int) or count < 2 or count != fan['strand_count']:
        raise ValueError('matching reference core count required')
    groups = [list(map(vector, geometry[key])) for key in
              ('root_xy_mm', 'expanded_xy_mm', 'tip_xy_mm')]
    if any(len(group) != count for group in groups):
        raise ValueError('fan geometry core count differs')
    roots, expanded, tips = groups
    radius = number(current['contained_core_radius_mm'], positive=True)
    if radius != number(fan['minimum_copper_core_diameter_mm'], positive=True)/2:
        raise ValueError('bulk and fan core sections differ')
    metal = number(reference['bulk_metal_radius_mm'], positive=True)
    curve = reference['bulk_curve_bounds']
    datum = {key:F(value) for key,value in reference['exact_axial_datums_mm'].items()}
    height = F(reference['endpoint_reference']['axial_height_exact_mm'])
    if (datum['endpoint_height'] != height
            or datum['bulk_front'] != datum['foil_front']+height
            or datum['bulk_rear'] != datum['foil_rear']-height
            or datum['bulk_span'] != datum['bulk_rear']-datum['bulk_front']):
        raise ValueError('exact shared endpoint cuts disagree')
    stages=[('solder',number(fan['solder_height_upper_mm'],positive=True)),
            ('tip',number(fan['redistribution_tip_height_mm'],positive=True)),
            ('main_fan',number(fan['main_fan_height_mm'],positive=True)),
            ('expansion',number(fan['initial_expansion_height_mm'],positive=True)),
            ('adapter',number(adapter['arclength_mm'],positive=True))]
    for i,(foil,target,sign) in enumerate(((datum['foil_front'],datum['bulk_front'],1),
                                         (datum['foil_rear'],datum['bulk_rear'],-1))):
        cuts={'foil':str(foil)};position=foil
        for name,stage_height in stages:
            position+=sign*stage_height;cuts[name]=str(position)
        if position!=target or cuts!=reference['exact_endpoint_stage_cuts_mm'][i]:
            raise ValueError('fan/adapter and bulk stage cuts disagree')
    span = number(reference['bulk_span_lower_mm'], positive=True)
    if not span <= datum['bulk_span'] <= number(reference['bulk_span_upper_mm'], positive=True):
        raise ValueError('bulk span bounds do not enclose exact cuts')
    slope = number(curve['slope_upper'])
    second = number(curve['second_parameter_derivative_norm_upper_mm'], positive=True)
    bend = number(curve['curvature_radius_lower_mm'], positive=True)
    axis_length = number(curve['axis_length_upper_mm'], positive=True)
    if slope < 0:
        raise ValueError('nonnegative slope bound required')
    root_radius = max(sqrt_interval(squared(p))[1] for p in roots)
    if root_radius + radius > metal:
        raise ValueError('reference cores leave full-metal tube')
    # Every smoothstep fan centre is a convex combination of its two
    # stage endpoints. Include the horizontal core and solder support.
    support = number(fan['square_support_side_mm'], positive=True)/2
    extent = max(radius, support)
    low = [min(p[k] for group in groups for p in group)-extent for k in range(2)]
    high = [max(p[k] for group in groups for p in group)+extent for k in range(2)]
    caps = reference['endpoint_reservations_mm_positive_rear']
    if len(caps) != 2 or any(len(cap) != 6 for cap in caps):
        raise ValueError('two complete endpoint reservation boxes required')
    terminals = [reference['points_mm_positive_rear'][0], reference['points_mm_positive_rear'][-1]]
    clearances = []
    axial = sum((number(fan[key], positive=True) for key in
                 ('initial_expansion_height_mm', 'main_fan_height_mm',
                  'redistribution_tip_height_mm', 'solder_height_upper_mm')), F())
    axial += number(adapter['arclength_mm'], positive=True)
    for end_index, (cap, terminal) in enumerate(zip(caps, terminals)):
        cap = list(map(number, cap))
        z = datum['foil_front' if end_index == 0 else 'foil_rear']
        required_low, required_high = (z,z+axial) if end_index == 0 else (z-axial,z)
        if cap[2] > required_low or cap[5] < required_high:
            raise ValueError('reference endpoint axial geometry leaves reservation')
        for k in range(2):
            centre = number(terminal[k])
            clearances.extend((centre+low[k]-cap[k], cap[k+3]-centre-high[k]))
    clearance = min(clearances)
    if clearance < 0:
        raise ValueError('reference fan/core/solder support leaves endpoint reservation')
    # M is RAW |d²g/dz²|, not geometric curvature. Two normal incidences
    # have depth separation <=2RS. Between them |g-p|<=R(1+2S²), hence
    # (|r-p|²/2)'' >= 1-MR(1+2S²)>0 contradicts two stationary points.
    injectivity = second/span**2 * metal*(1+2*slope**2)
    if injectivity >= 1 or metal >= bend:
        raise ValueError('global tube injectivity or local Jacobian unproved')
    core_curvature_product = radius/(bend-root_radius)
    if core_curvature_product > number(current['core_radius_times_curvature_upper'], positive=True):
        raise ValueError('individual core curvature exceeds current class')
    if number(current['mean_strand_arclength_over_bundle_axis_upper'], positive=True) < 1:
        raise ValueError('reference core length ratio exceeds current class')
    if number(current['frame_spin_upper_rad_per_mm']) < 0:
        raise ValueError('reference zero spin exceeds current class')

    heights = [number(fan[key], positive=True) for key in
               ('initial_expansion_height_mm', 'main_fan_height_mm')]
    fixed_end = sum((number(fan[key], positive=True) for key in
                     ('redistribution_tip_height_mm', 'solder_height_upper_mm')), F())
    fixed_end += number(adapter['arclength_mm'], positive=True)
    end_lengths = [fixed_end for _ in roots]
    minimum_separation2 = None
    for start, end, height in zip((roots, expanded), (expanded, tips), heights):
        deltas = [difference(b, a) for a, b in zip(start, end)]
        for i, delta in enumerate(deltas):
            end_lengths[i] += sqrt_interval(height**2 + F(6, 5)*squared(delta))[1]
        # Smoothstep takes every w in [0,1]; exact quadratic minimization
        # proves separation at all heights, not only sampled slices.
        for i in range(count):
            for j in range(i):
                a = difference(start[i], start[j])
                d = difference(deltas[i], deltas[j])
                q = squared(d)
                w = min(F(1), max(F(0), -sum(x*y for x, y in zip(a, d))/q)) if q else F()
                sep2 = squared(tuple(x+w*y for x, y in zip(a, d)))
                minimum_separation2 = sep2 if minimum_separation2 is None else min(minimum_separation2, sep2)
    if minimum_separation2 <= (2*radius)**2:
        raise ValueError('reference fan or bulk cores overlap')
    separation = sqrt_interval(minimum_separation2)[0]
    end_allowance = min(number(fan['maximum_fanned_length_per_end_mm'], positive=True),
                        number(adapter['maximum_total_fan_arclength_mm'], positive=True))
    if max(end_lengths) > end_allowance:
        raise ValueError('complete endpoint including solder exceeds fan allocation')
    preparation = number(preparation_mm)
    ceiling = number(maximum_cut_mm, positive=True)
    if preparation < 0:
        raise ValueError('nonnegative preparation allowance required')
    complete = axis_length + 2*end_allowance
    cut = complete + preparation
    if cut > ceiling:
        raise ValueError('individual reference path plus preparation exceeds source cut')
    return {
        'status': 'CONDITIONAL constructed reference cores only; actual metal/cut qualification OPEN',
        'core_count': count,
        'exact_shared_cut_datums_mm': reference['exact_axial_datums_mm'],
        'exact_endpoint_stage_cuts_mm': reference['exact_endpoint_stage_cuts_mm'],
        'global_graph_injectivity_factor_upper': directed(injectivity, True),
        'full_tube_jacobian_lower': directed(1-metal/bend, False),
        'maximum_root_radius_upper_mm': directed(root_radius, True),
        'minimum_endpoint_horizontal_clearance_lower_mm': directed(clearance, False),
        'minimum_core_gap_lower_mm': directed(separation-2*radius, False),
        'individual_core_radius_times_curvature_upper': directed(core_curvature_product, True),
        'individual_bulk_length_over_axis': 1,
        'reference_frame_spin_rad_per_mm': 0,
        'complete_endpoint_length_upper_mm': [directed(x, True) for x in end_lengths],
        'endpoint_allocation_each_end_mm': directed(end_allowance, True),
        'maximum_individual_reference_length_upper_mm': directed(complete, True),
        'preparation_allowance_mm': directed(preparation, True),
        'maximum_reference_with_preparation_upper_mm': directed(cut, True),
        'source_cut_margin_lower_mm': directed(ceiling-cut, False),
        'manufactured_cut_or_material_admission': False,
        'scope': 'Fixed Bishop offsets of the registered planar axis, matching fan roots at both ends. Individual reference lengths do not bound arbitrary physical strand lay; actual contained cores, all-metal envelopes, interfaces and terminal traces remain unqualified.'
    }
