"""Explicit disposable P outline and terminal-reservation source revision.

The fixed component origins, footprints, drills and clearances are preserved.
The revision addresses measured native conflicts and is not canonical adoption.
"""
import copy
import math


def revise(original, proposal, lands):
    definition = copy.deepcopy(original)
    change = proposal['geometry_replan']
    expected = [[1, 194], [94, 194], [94, 176], [317, 176], [317, 292], [1, 292]]
    if original['outline'] != expected or original['board_id'] != 'osc-control':
        raise ValueError('Original P outline differs from the reviewed conflict')
    tab = change['RV601_tab']
    x = tab['left_x_mm']
    low, high = tab['y_interval_mm']
    centre = [94.2, 185.0]
    radius = 1.2
    clearance = min(centre[0] - x - radius,
                    math.hypot(94 - centre[0], low - centre[1]) - radius,
                    math.hypot(94 - centre[0], high - centre[1]) - radius)
    if not (x < 94 and 176 < low < 185 < high < 194) or clearance < 0.5:
        raise ValueError('Tab does not preserve the 0.5 mm copper-edge rule')
    definition['outline'] = [[1, 194], [94, 194], [94, high], [x, high],
                             [x, low], [94, low], [94, 176], [317, 176],
                             [317, 292], [1, 292]]
    old = [k for k in original['keepouts'] if k['id'] == 'load-power']
    if old != [{'id': 'load-power', 'polygon': [[139, 176.5], [196, 176.5],
                [196, 184], [139, 184]], 'layers': ['F.Cu', 'B.Cu']}]:
        raise ValueError('Original broad terminal reservation changed')
    wanted = change['individual_reservations']['references']
    if wanted != ['TP990025', 'TP990027', 'TP990029', 'TP990031']:
        raise ValueError('Reservation replan must identify the exact four original lands')
    additions = []
    for ref in wanted:
        matches = [land for land in lands if land['reference'] == ref]
        if len(matches) != 1 or matches[0]['side'] != 'B.Cu':
            raise ValueError('Missing or changed source land')
        land = matches[0]
        X, Y = land['center_mm']
        if Y != 179 or land['copper_land_mm'] != [4, 4]:
            raise ValueError('Fixed land geometry changed')
        additions.append({'id': f"POWER-{land['net']}-{X}-{Y}",
            'polygon': [[X-3, Y-3], [X+3, Y-3], [X+3, Y+3], [X-3, Y+3]],
            'layers': ['B.Cu']})
    definition['keepouts'] = [k for k in definition['keepouts'] if k['id'] != 'load-power'] + additions
    if any(definition[k] != value for k, value in original.items() if k not in ('outline', 'keepouts')):
        raise ValueError('Unrelated P source property changed')
    return definition, {
        'status': 'UNSELECTED source geometry revision; native and assembly gates required',
        'old_outline': original['outline'], 'new_outline': definition['outline'],
        'RV601_nominal_copper_edge_clearance_mm': clearance,
        'RV601_nominal_drill_edge_clearance_mm': centre[0] - x - 0.9,
        'removed_keepouts': old, 'added_keepouts': additions,
        'unchanged_keepout_count': len(original['keepouts']) - 1,
        'scope': 'Only the source-owned outline and broad load-power reservation change. No hardware, copper pad, hole, component face or global clearance changes.',
    }


def neighbor_envelopes(selector, partition_input, lock, left_x):
    """Conditional source envelope arithmetic, not manufactured fit proof."""
    rows = {row['uid']: row for row in lock['placements']}
    o5 = rows['C:O5.OCT']
    instance = next(row for row in selector['instances'] if row['uid'] == 'C:O5.OCT')
    if o5['rot_deg'] != 0 or instance['rotation_deg'] != 0 or o5['x_mm'] != 82.5:
        raise ValueError('O5 source orientation or origin changed')
    budget = selector['tolerance_budget']
    right = o5['x_mm'] + selector['drawing']['conservative_body_support_xy_mm'][2]
    nominal = left_x - right
    allocated = nominal - 2 * budget['axis_position_error_per_part_mm']
    if allocated < budget['min_neighbor_xy_clearance_mm']:
        raise ValueError('O5 body/support source allocation does not fit')
    p = partition_input['boards']['P']
    p_rear = p['face_z_mm'] - p['thickness_mm']
    o5_front = instance['pcb_z_mm']
    board_gap = p_rear - o5_front
    remaining = board_gap - budget['body_and_tail_z_growth_mm'] - budget['relative_adapter_z_error_mm']
    if remaining < budget['allocated_min_z_gap_mm']:
        raise ValueError('O5 board/copper/solder source allocation does not fit')
    return {
        'status': 'Conditional nominal source-envelope screen; physical qualification remains #55/#65',
        'O5_body_support_right_x_mm': right,
        'nominal_body_support_XY_gap_mm': nominal,
        'two_axis_errors_mm': 2 * budget['axis_position_error_per_part_mm'],
        'allocated_body_support_XY_gap_mm': allocated,
        'required_XY_gap_mm': budget['min_neighbor_xy_clearance_mm'],
        'P_rear_z_mm': p_rear, 'O5_front_z_mm': o5_front,
        'nominal_board_z_gap_mm': board_gap,
        'body_tail_growth_mm': budget['body_and_tail_z_growth_mm'],
        'relative_adapter_z_error_mm': budget['relative_adapter_z_error_mm'],
        'remaining_board_copper_solder_z_gap_mm': remaining,
        'required_z_gap_mm': budget['allocated_min_z_gap_mm'],
        'scope': 'Conservative full body/support XY projection is used wherever its z range crosses P. O5 board/copper and rear solder/tails may overlap P in XY but remain in the separate z interval. Exact manufactured envelopes must meet the existing conditional source allocations.',
    }
