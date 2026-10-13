#!/usr/bin/env python3
"""Conditional collet sensitivities; diagnostic limits never amend requirements."""
import argparse
import json
import math
from pathlib import Path

import collet_clearance as clearance
import check as base

HERE = Path(__file__).resolve().parent


def remaining_gap(height, grip_start, radius, nominal_normal, axis_angle, closures):
    if not math.isfinite(axis_angle) or axis_angle < 0:
        raise ValueError('finite nonnegative axis angle required')
    normal = math.cos(math.acos(nominal_normal)+axis_angle)
    if not math.isfinite(closures) or closures < 0:
        raise ValueError('finite nonnegative closure required')
    return clearance.cylinder_gap(height, grip_start, radius, normal)-closures


def limiting_axis_angle(height, grip_start, radius, nominal_normal, closures, residual):
    """Monotone bisection: lower result passes, upper result fails locally."""
    if not math.isfinite(residual) or residual < 0:
        raise ValueError('finite nonnegative residual criterion required')
    lo = 0.0
    hi = math.nextafter(math.pi/2-math.acos(nominal_normal), 0)
    if remaining_gap(height, grip_start, radius, nominal_normal, lo, closures) < residual:
        raise ValueError('even the nominal axis cannot meet this criterion')
    if remaining_gap(height, grip_start, radius, nominal_normal, hi, closures) >= residual:
        raise ValueError('no limiting angle inside the outward-axis domain')
    for _ in range(90):
        mid = (lo+hi)/2
        if remaining_gap(height, grip_start, radius, nominal_normal, mid, closures) >= residual:
            lo = mid
        else:
            hi = mid
    return lo, hi


def calculate():
    persisted = base.read(HERE/'collet-clearance.json')
    # Normalize tuples to JSON arrays before comparing the persisted evidence.
    base.need(persisted == json.loads(json.dumps(clearance.calculate())), 'collet source evidence drift')
    robust = base.read(HERE/'robust-curve.json')
    files = ('collet-clearance.json', 'collet_clearance.py', 'robust-curve.json',
             'process-budget.md', 'reconciled-contract.json', 'source-lock.json')
    hashes = {name: base.sha(HERE/name) for name in files}
    bound = persisted['board_bound']
    outer = persisted['outer_shape_contract']
    family = robust['family']
    height = bound['minimum_anchor_height_mm']
    start = outer['grip_axis_arclength_mm'][0]
    radius = outer['outer_radius_mm']
    nominal_normal = -family['direction'][2]
    angle = outer['axis_cone_half_angle_rad']
    closures = bound['total_independent_closure_mm']
    required = bound['required_residual_mm']
    gap = remaining_gap(height, start, radius, nominal_normal, angle, closures)
    normal = bound['minimum_axis_normal_component']
    headroom = gap-required
    max_closure = bound['exact_cylinder_bare_gap_mm']-required
    axis_lo, axis_hi = limiting_axis_angle(height, start, radius, nominal_normal, closures, required)
    reference_radius = robust['reference_curve']['radius_lower_bound_mm']
    eta2 = family['second_derivative_error_max_per_mm']
    minimum_radius = family['minimum_bend_radius_mm']
    reference_length = robust['cut_and_preparation']['reference_complete_path_upper_mm']
    minimum_cut = min(robust['cut_and_preparation']['new_cut_range_mm'])
    prep = robust['cut_and_preparation']['required_other_preparation_min_mm']
    bend_eta_limit = 1-math.sqrt(minimum_radius*(1/reference_radius+eta2))
    cut_eta_limit = (minimum_cut-prep)/reference_length-1
    axis_rows = []
    for alpha in (0, angle, math.radians(1), math.radians(2), math.radians(4), axis_lo, math.radians(7)):
        degrees = math.degrees(alpha)
        local_gap = remaining_gap(height, start, radius, nominal_normal, alpha, closures)
        eta = math.sin(alpha)
        shape_radius = (1-eta)**2/(1/reference_radius+eta2)
        other_prep = minimum_cut-(1+eta)*reference_length
        axis_rows.append({'axis_cone_deg': degrees, 'local_board_gap_mm': local_gap,
                          'local_board_bound_pass': local_gap >= required,
                          'C1_needed_to_cover_entire_axis_cone': eta,
                          'within_current_C1_requirement': eta <= family['first_derivative_error_max']+1e-15,
                          'diagnostic_shape_radius_bound_mm': shape_radius,
                          'diagnostic_preparation_remaining_mm': other_prep,
                          'diagnostic_shape_radius_bound_pass': shape_radius >= minimum_radius,
                          'diagnostic_preparation_bound_pass': other_prep >= prep})
    closure_rows = [{'total_closure_mm': value,
                     'remaining_gap_mm': bound['exact_cylinder_bare_gap_mm']-value,
                     'meets_residual_criterion': bound['exact_cylinder_bare_gap_mm']-value >= required}
                    for value in (.20, closures, .45, max_closure, max_closure+.01)]
    allocations = [{'name': name, 'current_mm': value,
                    'one_at_a_time_boundary_mm': value+headroom,
                    'other_allocations_held_fixed': True, 'qualified_capability': False}
                   for name, value in bound['independent_closures_mm'].items()]
    qualifications = [
        ('measured_anchor_height', 'Proposed dimensional acceptance', family['anchor_height_range_mm'],
         'Inspect assembled height in the measured board-face datum, with measurement uncertainty inside the interval.'),
        ('flat_ended_outer_cylinder', 'Geometric model assumption', {'radius_mm': radius, 'grip_mm': outer['grip_axis_arclength_mm']},
         'Inspect complete exterior containment. Lugs, fasteners, end caps and arms outside this cylinder require separate solids and clearance checks.'),
        ('collet_axis_alignment', 'Conditional directional assumption', {'half_cone_deg': math.degrees(angle)},
         'Measure bore-axis alignment to the straight gripped wire and registered datum. Position inspection alone does not establish the angular bound.'),
        ('outer_profile', 'Proposed machining acceptance', bound['independent_closures_mm']['outer_profile'],
         'Measure all noncontact exterior surfaces and end planes; no supplier capability is inferred.'),
        ('board_warp', 'Proposed assembled-board acceptance', bound['independent_closures_mm']['board_warp'],
         'Measure the complete relevant board surface relative to datum A under the intended assembly condition.'),
        ('registration', 'Proposed datum-location acceptance', bound['independent_closures_mm']['registration'],
         'Inspect the A/B/C registration after assembly. Loose retention holes are not precision datums; no cancellation credit is taken.'),
        ('retention', 'Proposed service/load displacement bound', bound['independent_closures_mm']['retention'],
         'Qualify repeated service and applied loads for the selected material, grip and attachment. Static CAD does not establish retention.'),
        ('thermal', 'Proposed operating-condition displacement bound', bound['independent_closures_mm']['thermal'],
         'Qualify relative displacement across the specified operating conditions after selecting actual materials and load paths.'),
        ('wire_C0_C1_C2', 'Conditional continuous-shape requirements',
         {'C0_mm': family['position_error_max_mm'], 'C1': family['first_derivative_error_max'], 'C2_per_mm': eta2},
         'Qualify the continuous shape including collet exits and strain transitions. Position samples alone are insufficient; material length remains fixed through withdrawal.'),
        ('new_cut_and_preparation', 'Proposed factory-process acceptance',
         {'cut_mm': robust['cut_and_preparation']['new_cut_range_mm'], 'other_preparation_min_mm': prep},
         'Inspect cut lengths and validate stripping/solder preparation on the actual assembly. The geometric path already spends both bridges and C1 length growth.'),
        ('residual_clearance', 'Design criterion', required,
         'A proposed service-clearance criterion, not a regulatory insulation rating or manufactured-process capability.'),
    ]
    ledger = [{'id': key, 'classification': kind, 'proposed_value': value,
               'qualified': False, 'qualification_evidence': None, 'required_evidence': evidence}
              for key, kind, value, evidence in qualifications]
    return {
        'status': 'CONDITIONAL SENSITIVITY AND QUALIFICATION LEDGER; NO REQUIREMENT RELAXATION OR PROCESS QUALIFICATION',
        'source_epoch': persisted['source_epoch'], 'input_sha256': hashes,
        'tool_sha256': base.sha(Path(__file__)), 'accepted': False,
        'current_local_board_bound': {'remaining_gap_mm': gap, 'required_residual_mm': required,
            'allocated_total_closure_mm': closures, 'maximum_total_closure_at_current_geometry_mm': max_closure,
            'single_shared_headroom_mm': headroom},
        'one_variable_local_boundaries': {
            'minimum_anchor_height_mm': height-headroom,
            'maximum_outer_radius_mm': (height+start*normal-closures-required)/math.sqrt(1-normal**2),
            'minimum_grip_start_mm': (required+closures-height+radius*math.sqrt(1-normal**2))/normal,
            'axis_half_cone_pass_boundary_deg': math.degrees(axis_lo),
            'axis_half_cone_fail_boundary_deg': math.degrees(axis_hi),
            'axis_half_cone_pass_boundary_rad': axis_lo,
            'axis_half_cone_fail_boundary_rad': axis_hi,
            'numerics': 'Double-precision diagnostic boundaries, not directed-rounding interval certificates. Degree conversion may merge adjacent radian values. Acceptance requires the original tolerances, not operation at these limiting values.',
            'diagnostic_only': True,
            'scope': 'Hold all other local inputs fixed. These boundaries are not accepted dimensions and do not update the curve, cut, source-clearance, bore or carrier proofs. Changing a dimension requires all dependent checks again.'},
        'one_closure_at_a_time': allocations,
        'axis_sensitivity': axis_rows, 'closure_sensitivity': closure_rows,
        'coupled_C1_diagnostics': {
            'current_requirement': family['first_derivative_error_max'],
            'local_collet_clearance_only_boundary': math.sin(axis_lo),
            'shape_radius_certificate_boundary': bend_eta_limit,
            'cut_and_preparation_certificate_boundary': cut_eta_limit,
            'scope': 'Other source values remain fixed. A local angular clearance pass does not authorize a larger C1 error. Radius and preparation are conditional certificate bounds, not proof that a failing bound implies actual physical failure. Existing C1 requirement is unchanged.'},
        'counterexamples': {
            'spending_full_shared_headroom_on_two_closures': {
                'each_individually_reaches_its_one_variable_boundary': True,
                'combined_total_closure_mm': closures+2*headroom,
                'combined_remaining_gap_mm': gap-2*headroom,
                'meets_residual_criterion': gap-2*headroom >= required},
            'unmodeled_0p25mm_extension_toward_board': {
                'remaining_gap_mm': gap-.25, 'meets_residual_criterion': gap-.25 >= required,
                'scope': 'An illustrative exterior feature outside the cylinder, not an authorized added flange or a claim that such a feature exists.'}},
        'qualification_ledger': ledger,
        'gates': {'source_bindings_verified': True, 'conditional_local_headroom_arithmetic': headroom > 0,
                  'requirement_changes_authorized': False, 'qualified_process_margin': False,
                  'supplier_capability': False, 'actual_measurements': False,
                  'complete_new_feed_collision_sweep': False, 'physical_fit': False,
                  'all_100_trim_access': False, 'native': False},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    text = json.dumps(result, indent=2, sort_keys=True)+'\n'
    target = HERE/'collet-headroom.json'
    if args.check:
        base.need(target.read_text() == text, 'collet headroom evidence drift')
    else:
        target.write_text(text)
    print(json.dumps({'headroom_mm': result['current_local_board_bound']['single_shared_headroom_mm'],
                      'coupled_C1_diagnostics': result['coupled_C1_diagnostics'],
                      'gates': result['gates']}))


if __name__ == '__main__':
    main()
