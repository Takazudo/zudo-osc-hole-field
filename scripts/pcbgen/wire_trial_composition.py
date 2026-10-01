"""Conditional whole-wire current/potential witnesses, with open endpoint gates.

This helper computes a proposed material/geometry class. It supplies no Alpha
lay evidence and does not turn scalar assembled DCR into a profile certificate.
"""
import json
import math
from fractions import Fraction
from pathlib import Path
from scripts.pcbgen.contact_transfer import main_strand_trial,specification
from scripts.pcbgen.strand_adapter import bounds as adapter_bounds
from scripts.geometry.power_wire import registered_route,directed
from scripts.geometry.parallel_wire_cores import bounds as individual_core_bounds


def source_budget_comparison(upper_ohm, distribution):
    """Compare the computed trial to current decimal source requirements.

    Exact budget arithmetic avoids rounding a failing comparison into a pass.
    This does not upgrade the upstream numerical trial or qualify a cut wire.
    """
    def positive(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError('finite positive wire budget operand required')
        return Fraction(str(value))
    length=positive(distribution['max_wire_length_mm'])
    rate=positive(distribution['hot_resistance_requirement_ohm_per_m'])
    termination=positive(distribution['combined_termination_resistance_ohm'])
    positive(upper_ohm)
    # Preserve the actual binary value returned by the numerical trial.
    upper=Fraction(upper_ohm)
    limit=rate*length/1000+termination
    margin=limit-upper
    display=float(margin)
    if Fraction(display)>margin:display=math.nextafter(display,-math.inf)
    return {'source_max_wire_length_mm':float(length),
        'source_hot_resistance_requirement_ohm_per_m':float(rate),
        'source_combined_termination_allowance_ohm':float(termination),
        'whole_wire_budget_exact_ohm':str(limit),
        'whole_wire_budget_ohm':float(limit),
        'remaining_budget_lower_ohm':display,
        'conditional_trial_within_budget':upper<=limit,
        'physical_or_joined_acceptance':False}


def bounds(*,source=None):
    proposal=json.loads(Path('design/partition/wire-transfer-proposal.json').read_text())
    if source is None:source=json.loads(Path('design/partition/partition-input.json').read_text())
    current=proposal['bulk_current_class'];potential=proposal['bulk_potential_class']
    normal_material=proposal['normal_material_class']
    if not math.isclose(normal_material['equivalent_resistivity_lower_ohm_mm'],
                        1000/normal_material['maximum_all_metal_conductivity_S_per_m'],rel_tol=1e-14):
        raise ValueError('normal conductivity and resistivity units disagree')
    tip=main_strand_trial();count=current['contained_core_count']
    area=tip['minimum_effective_copper_area_mm2']/count;a=current['contained_core_radius_mm']
    # The actual contained polygon lies inside radius a, so its centred second
    # moment is <=a². This universal bound also covers a non-circular polygon;
    # no unverified exact disk moment is substituted for the actual section.
    spin_factor=1+current['frame_spin_upper_rad_per_mm']**2*a*a/(1-current['core_radius_times_curvature_upper'])
    per_axis=current['hot_resistivity_upper_ohm_mm']/(count*area)*current['mean_strand_arclength_over_bundle_axis_upper']*spin_factor
    fan=specification();fan_height=fan['initial_expansion_height_mm']+fan['main_fan_height_mm']+fan['redistribution_tip_height_mm']
    radius=potential['maximum_metal_radius_from_bundle_axis_mm'];bend=potential['minimum_bundle_bend_radius_mm']
    jacobian=1-radius/bend
    if jacobian<=0:raise ValueError('bundle-coordinate potential map has nonpositive Jacobian')
    interface=proposal['interface_trial_class']
    adapter=adapter_bounds(proposal['endpoint_adapter_class'],current['hot_resistivity_upper_ohm_mm'],
        a,area,count,fan['root_hex_pitch_mm'],tip['fan_geometry']['maximum_arclength_upper_mm'],fan_height,radius,bend,potential['maximum_bundle_transverse_slope'])
    area_total=count*fan['square_support_side_mm']**2
    interfaces=2*interface['metallurgical_interfaces_per_end']*interface['normal_areal_resistance_upper_ohm_mm2']/area_total
    termination=tip['two_terminal_added_transfer_ohm']+interfaces+adapter['two_adapter_full_energy_debit_ohm']
    if termination>source['load_distribution']['combined_termination_resistance_ohm']:
        raise ValueError('conditional contact class exceeds the existing termination budget')
    rows=[]
    cases=[(board,i) for board in source['load_distribution']['branches']
           for i in range(len(source['load_distribution']['wire_labels']))]
    for branch,index in cases:
        spec=source['load_distribution']['branches'][branch]
        # Solder is a separate prism below the copper tip, not inside the
        # fan height. Charge its fixed modeled thickness in both end planes.
        reference=registered_route(source,branch,index,fan,proposal['endpoint_adapter_class'],metal_radius=radius)
        H=reference['bulk_span_mm'];curve=reference['bulk_curve_bounds']
        if not curve['axial_endpoint_tangents']:
            raise ValueError('the potential collar requires axial endpoint tangents')
        if curve['slope_upper']>potential['maximum_bundle_transverse_slope']:
            raise ValueError('actual source curve exceeds the collar inverse slope bound')
        axis_upper=curve['axis_length_upper_mm']
        bend_lower=curve['curvature_radius_lower_mm']
        if bend_lower<bend:raise ValueError('fan-compatible bulk curve violates the retained bend radius')
        length_upper=current['mean_strand_arclength_over_bundle_axis_upper']*axis_upper+2*fan['maximum_fanned_length_per_end_mm']
        if length_upper>source['load_distribution']['max_wire_length_mm']:
            raise ValueError('mean-strand length screen exceeds the source cut-length allowance; physical cut qualification remains open')
        bulk_upper=per_axis*axis_upper
        # phi varies only along the common bundle coordinate. The area,
        # conductivity and 1/(1-kappa dot xi) bounds cover ALL actual metal.
        varying_span=directed(Fraction(reference['exact_axial_datums_mm']['bulk_span'])-2*Fraction(adapter['constant_primal_collar_mm']),False)
        if varying_span<=0:raise ValueError('all-metal collars consume the entire varying bulk span')
        bulk_lower=potential['hot_resistivity_lower_ohm_mm']*varying_span*jacobian/potential['maximum_total_metal_area_per_bundle_normal_section_mm2']
        normal_lower=normal_material['equivalent_resistivity_lower_ohm_mm']*varying_span*jacobian/potential['maximum_total_metal_area_per_bundle_normal_section_mm2']
        full_fans=2*tip['one_terminal_fan_copper_ohm']+tip['two_terminal_added_transfer_ohm']
        whole_upper=bulk_upper+full_fans+interfaces+adapter['two_adapter_full_energy_debit_ohm']
        row={'branch':branch,'wire_labels':[source['load_distribution']['wire_labels'][index]],
            'bulk_axial_height_mm':H,'bundle_axis_length_upper_mm':axis_upper,
            'minimum_bulk_bend_radius_mm':bend_lower,'mean_strand_length_with_both_fans_upper_mm':length_upper,
            'bulk_varying_primal_span_lower_mm':varying_span,
            'bulk_hot_only_lower_ohm':bulk_lower,'bulk_normal_material_lower_ohm':normal_lower,'bulk_upper_ohm':bulk_upper,
            'whole_wire_hot_only_lower_ohm':bulk_lower,'whole_wire_normal_material_lower_ohm':normal_lower,'whole_wire_upper_ohm':whole_upper,
            'current_source_budget':source_budget_comparison(whole_upper,source['load_distribution']),
            'remaining_historical_125mm_budget_ohm':.013*.125+.0002-whole_upper}
        row['registered_endpoint_reference']={k:v for k,v in reference.items() if 'points' not in k}
        row['endpoint_y_offset_mm']=spec['core_pad_y_mm'][index]-spec['pad_y_mm']
        row['individual_reference_core_construction']=individual_core_bounds(
            reference,tip['fan_geometry'],fan,proposal['endpoint_adapter_class'],current,
            source['load_distribution']['max_wire_length_mm'])
        rows.append(row)
    return {'status':'UNSELECTED conditional inequalities only; actual containment and source selection remain OPEN',
        'endpoint_adapter':adapter,
        'bulk_trial_upper_ohm_per_bundle_axis_m':per_axis*1000,
        'temperature_scope':potential['temperature_scope'],
        'normal_GH_current_conductivity_class':normal_material,
        'bulk_potential_jacobian_lower':jacobian,'normal_interface_energy_two_ends_ohm':interfaces,
        'combined_termination_trial_ohm':termination,
        'remaining_combined_termination_allowance_ohm':source['load_distribution']['combined_termination_resistance_ohm']-termination,
        'historical_comparison_only':{'length_mm':125,'hot_resistance_ohm_per_m':.013,'combined_termination_ohm':.0002},
        'length_screen_scope':'Mean contained-strand arclength including both fans; not maximum individual strand length or a finished manufactured cut-length certificate. Source preparation/slack and endpoint/trace qualification remain OPEN.',
        'branches_not_evaluated':{},
        'reference_scope':'All 18 source-labelled wires use registered planar trial cuts, zero-tilt reference adapters and explicit fixed solder prisms. Actual arbitrary endpoint staggering is not covered; physical containment/material/trace qualification remains OPEN.',
        'rows':rows,'scope':proposal['endpoint_gate']}


if __name__=='__main__':print(json.dumps(bounds(),indent=2))
