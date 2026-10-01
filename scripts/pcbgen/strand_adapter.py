"""Finite normal-section to horizontal-section Bishop arc trial.

This is a sufficient unselected factory geometry, not an Alpha endpoint-angle
specification. Actual metal must contain every prescribed disjoint tube.
"""
import math
import numpy as np


def arc(s,length,tilt_rad,azimuth_rad=0.):
    """Return centre/tangent/normal-frame axes, with output centred at zero.

    Section coordinates are the global horizontal x/y coordinates at s=L,
    so the output polygon is exactly the existing finite fan's input polygon.
    The two frame derivatives are tangent-only: frame spin is zero.
    """
    s=np.asarray(s);alpha=tilt_rad*(1-s/length)
    e=np.array([math.cos(azimuth_rad),math.sin(azimuth_rad),0.])
    f=np.array([-math.sin(azimuth_rad),math.cos(azimuth_rad),0.]);z=np.array([0.,0.,1.])
    if tilt_rad:
        centre=-length/tilt_rad*((1-np.cos(alpha))[...,None]*e+np.sin(alpha)[...,None]*z)
    else:centre=-(length-s)[...,None]*z
    tangent=np.sin(alpha)[...,None]*e+np.cos(alpha)[...,None]*z
    n=np.cos(alpha)[...,None]*e-np.sin(alpha)[...,None]*z
    ex=math.cos(azimuth_rad)*n-math.sin(azimuth_rad)*f
    ey=math.sin(azimuth_rad)*n+math.cos(azimuth_rad)*f
    return centre,tangent,ex,ey


def curved_collar_extent(axial_extent,metal_radius,bend_radius,maximum_axis_slope):
    """Convert a global end cap to bundle arclength, with its branch proved.

    The declared axis is monotone in z, initially tangent to z. Any point in
    the cap has axis z <= d+R, hence s <= (d+R)*sqrt(1+slope_max²).
    This first bound must lie before the quarter-turn branch. Curvature then
    gives z_point >= (1/kappa-R)*sin(kappa*s), which can be inverted safely.
    """
    if not 0<=axial_extent or not 0<=metal_radius<bend_radius or maximum_axis_slope<0:
        raise ValueError('invalid positive bundle collar geometry')
    rough=(axial_extent+metal_radius)*math.sqrt(1+maximum_axis_slope**2)
    if rough>=math.pi*bend_radius/2:
        raise ValueError('monotone end cap does not establish the near-end inverse branch')
    argument=axial_extent/(bend_radius-metal_radius)
    if argument>=1:raise ValueError('curved end cap exceeds its invertible branch')
    return math.nextafter(bend_radius*math.asin(argument),math.inf),rough


def bounds(spec,rho,core_radius,core_area,count,root_pitch,existing_fan_length,existing_fan_height,metal_radius,bundle_bend_radius,maximum_axis_slope):
    length=spec['arclength_mm'];angle=math.radians(spec['incoming_tangent_tilt_upper_deg'])
    floor=spec['current_section_area_floor_mm2']
    if not 0<floor<=core_area or not 0<=angle<math.pi/2 or length<=0:
        raise ValueError('invalid finite adapter class')
    curvature=angle/length;hmin=1-core_radius*curvature
    lateral=length*(1-math.cos(angle))/angle if angle else 0.
    axial_min=length*math.sin(angle)/angle if angle else length
    gap=root_pitch-2*(core_radius+lateral)
    collar=spec['constant_primal_collar_mm']
    all_metal_extent=metal_radius*math.sin(angle)+length-axial_min
    arclength_extent,near_end=curved_collar_extent(all_metal_extent,metal_radius,bundle_bend_radius,maximum_axis_slope)
    if hmin<=0 or gap<=0 or collar<arclength_extent:
        raise ValueError('adapter has nonpositive Jacobian, overlap or incomplete primal collar')
    if existing_fan_length+length>spec['maximum_total_fan_arclength_mm']:
        raise ValueError('adapter exceeds the existing 4 mm fan allocation')
    debit=2*rho*length/(count*floor)
    return {'status':'Conditional contained geometry only; actual endpoint angles/roll/tubes require #65 qualification',
        'adapter_arclength_each_end_mm':length,'maximum_fan_plus_adapter_arclength_mm':existing_fan_length+length,
        'input_axial_distance_interval_mm':[axial_min,length],
        'input_lateral_offset_upper_mm':lateral,'core_tube_jacobian_lower':hmin,
        'minimum_pairwise_vertical_cylinder_gap_mm':gap,
        'normal_frame_spin':0.,'two_adapter_full_energy_debit_ohm':debit,
        'full_fan_axial_height_interval_mm':[existing_fan_height+axial_min,existing_fan_height+length],
        'all_metal_endpoint_axial_extent_upper_mm':all_metal_extent,
        'all_metal_endpoint_bundle_arclength_extent_upper_mm':arclength_extent,
        'monotone_near_end_branch_arclength_bound_mm':near_end,
        'constant_primal_collar_mm':collar,
        'accounting':'The full two-adapter current energy is charged as explicit conservative excess even though the retained 4 mm/end straight-wire baseline already funds this arclength. No second credit is taken.',
        'endpoint_conditions':'The actual incoming normal sections, centres and roll must match these arcs. A circular contained core permits choosing trial polygon roll independently of material rotation; any distributed bulk frame spin remains inside its charged bound.'}
