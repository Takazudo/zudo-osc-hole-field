#!/usr/bin/env python3
"""Conditional finite-collet clearance; no carrier or physical-fit admission."""
import argparse
import json
import math
from pathlib import Path

import check as base

HERE = Path(__file__).resolve().parent
SIGNS = (1, -1, 1, 1, -1, 1)
OUTER_RADIUS = 2.0
GRIP = (1.0, 2.5)
REQUIRED_RESIDUAL = .25
# Worst-case independent sums. No supplier capability or correlation credit.
BOARD_CLOSURES = {'outer_profile': .05, 'board_warp': .10, 'thermal': .05,
                  'retention': .05, 'registration': .10}
XY_CLOSURES = {key: BOARD_CLOSURES[key]
               for key in ('outer_profile', 'thermal', 'retention', 'registration')}
SOURCE_XY_PROFILE = .10


def unit(values):
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError('finite three-dimensional direction required')
    if abs(sum(v*v for v in values)-1) > 1e-12:
        raise ValueError('unit direction required')
    return tuple(values)


def minimum_normal_component(normal_component, derivative_error):
    """q'=v+e', |v|=1, |e'|<=eta: angle(q',v)<=asin(eta)."""
    if not (0 < normal_component < 1 and 0 <= derivative_error < 1):
        raise ValueError('positive normal component and eta in [0,1) required')
    result = normal_component*math.sqrt(1-derivative_error**2) - math.sqrt(1-normal_component**2)*derivative_error
    if result <= 0:
        raise ValueError('axis cone includes a direction toward the board')
    return result


def cylinder_gap(height, grip_start, outer_radius, normal_component):
    """Exact support gap to a plane for an outward, flat-ended cylinder."""
    if not all(math.isfinite(v) for v in (height, grip_start, outer_radius, normal_component)):
        raise ValueError('finite geometry required')
    if min(height, grip_start, outer_radius) <= 0 or not 0 < normal_component <= 1:
        raise ValueError('positive cylinder geometry required')
    return height+grip_start*normal_component-outer_radius*math.sqrt(1-normal_component**2)


def xy_box(anchor, direction, axis_angle, radius, grip=GRIP):
    """Conservative box for every cylinder in the permitted axis cone."""
    direction = unit(direction)
    if (len(anchor) != 2 or not all(math.isfinite(v) for v in anchor)
            or not math.isfinite(radius) or radius <= 0
            or len(grip) != 2 or not all(math.isfinite(v) for v in grip)
            or not 0 < grip[0] <= grip[1]):
        raise ValueError('finite anchor, positive radius and ordered positive grip required')
    if not 0 <= axis_angle < math.pi/2:
        raise ValueError('bounded axis cone required')
    delta = 2*math.sin(axis_angle/2)
    lows, highs = [], []
    for j in range(2):
        points = [s*(direction[j]+d) for s in grip for d in (-delta, delta)]
        lows.append(anchor[j]+min(points)-radius)
        highs.append(anchor[j]+max(points)+radius)
    return lows+highs


def expand(box, amount):
    return [box[0]-amount, box[1]-amount, box[2]+amount, box[3]+amount]


def calculate():
    files = ('robust-curve.json', 'robust_curve.py', 'reconciled-contract.json',
             'process-budget.md', 'offset-proposal.json', 'source-lock.json', 'check.py')
    hashes = {name: base.sha(HERE/name) for name in files}
    robust = base.read(HERE/'robust-curve.json')
    reconciled = base.read(HERE/'reconciled-contract.json')
    old_geometry = base.read(HERE/'offset-proposal.json')
    lock = base.read(HERE/'source-lock.json')
    for name, digest in lock['files'].items():
        base.need(base.sha(base.ROOT/name) == digest, 'producer drift: '+name)
    base.need(robust['tool_sha256'] == hashes['robust_curve.py'], 'curve tool/evidence mismatch')
    base.need(reconciled['curve_evidence']['sha256'] == hashes['robust-curve.json'], 'reconciliation/curve mismatch')
    base.need(reconciled['process_budget_sha256'] == hashes['process-budget.md'], 'reconciliation/process mismatch')
    base.need(reconciled['source_lock_sha256'] == hashes['source-lock.json'], 'reconciliation/source mismatch')
    base.need(reconciled['producer_epoch'] == lock['source_commit'], 'producer epoch mismatch')
    family = robust['family']
    direction = unit(family['direction'])
    eta = family['first_derivative_error_max']
    angle = math.asin(eta)
    normal = minimum_normal_component(-direction[2], eta)
    minimum_height = min(family['anchor_height_range_mm'])
    bare_gap = cylinder_gap(minimum_height, GRIP[0], OUTER_RADIUS, normal)
    closure = math.fsum(BOARD_CLOSURES.values())
    residual = bare_gap-closure
    capsule_gap = minimum_height+GRIP[0]*normal-OUTER_RADIUS

    candidates = base.read(base.ROOT/'design/partition/core-split/candidates/two.json')['boards']
    partition = base.read(base.ROOT/'design/partition/partition.json')
    mechanical = next(a for a in base.read(base.ROOT/'design/partition/core-split/mechanical/generated/comparison.json')['alternatives'] if a['id'] == 'two-deep')
    endpoints = reconciled['producer_replacements']['feed']['endpoint_envelopes']
    base.need([(e['board'], e['side']) for e in endpoints] == [('KA', 'B.Cu'), ('KB', 'F.Cu')], 'unexpected endpoint faces')
    bulk = [q for q in old_geometry['construction']['bulk_and_monitor_reserves'] if '-bulk-' in q['id']]
    base.need(len(bulk) == 6, 'six retained bulk reservations required')
    monitor = reconciled['producer_replacements']['monitor']
    source_rows = {}
    for board, key, side in [('KA', 'two-A', 'B.Cu'), ('KB', 'two-B', 'F.Cu')]:
        rows = base.obstacles(candidates[key], side, mechanical, partition)
        rows += [{'id': q['id'], 'box': [q['box'][0], q['box'][1], q['box'][3], q['box'][4]], 'kind': 'new-bulk-reserve'} for q in bulk if q['board'] == board]
        if board == monitor['board']:
            # Opposite-face monitor is conservatively checked in XY as well.
            rows.append({'id': monitor['id'], 'box': monitor['box_xy_mm'], 'kind': 'new-monitor-reserve'})
        source_rows[board] = rows
    all_rows = [{**q, 'id': board+'/'+q['id']} for board, rows in source_rows.items() for q in rows]
    ledger = []
    for endpoint in endpoints:
        board = endpoint['board']
        anchors = endpoint['anchor_xy_mm']
        base.need(len(anchors) == 6, 'six anchors required')
        for i, anchor in enumerate(anchors):
            w = ((1 if board == 'KA' else -1)*direction[0], SIGNS[i]*direction[1], -direction[2])
            reference_box = xy_box(anchor, w, angle, OUTER_RADIUS)
            closed_box = expand(reference_box, math.fsum(XY_CLOSURES.values()))
            nearest = min((base.rectgap(closed_box, expand(q['box'], SOURCE_XY_PROFILE)), q['id'], q['kind']) for q in all_rows)
            ledger.append({'board': board, 'wire': i+1, 'anchor_xy_mm': anchor,
                           'axis_from_anchor_toward_free_wire': w,
                           'outer_reference_XY_box_mm': reference_box,
                           'outer_XY_box_after_independent_closures_mm': closed_box,
                           'source_XY_gap_after_closures_mm': nearest[0],
                           'nearest_source_obstacle': nearest[1], 'nearest_source_kind': nearest[2],
                           'own_board_gap_after_closures_mm': residual})
    source_min = min(q['source_XY_gap_after_closures_mm'] for q in ledger)
    return {
        'status': 'CONDITIONAL LOCAL COLLET CLEARANCE ONLY; COMPLETE FEED/ARMS/PHYSICAL FIT NOT QUALIFIED',
        'source_epoch': lock['source_commit'], 'input_sha256': hashes,
        'tool_sha256': base.sha(Path(__file__)), 'accepted': False,
        'outer_shape_contract': {'shape': 'Flat-ended finite annular cylinder; outer envelope only',
            'outer_radius_mm': OUTER_RADIUS, 'grip_axis_arclength_mm': list(GRIP),
            'datum': 'Depth is positive from each measured local PCB face into the inter-board gap.',
            'axis_cone_half_angle_rad': angle, 'axis_cone_half_angle_deg': math.degrees(angle),
            'axis_requirement': 'Collet bore axis must be aligned with the straight gripped wire and independently qualify within this C1-derived direction cone. Position tolerance alone does not establish this alignment.',
            'excluded': 'No unmodeled flange, screw head, split-clamp lug, stem, carrier, fastener or end cap may be included in this envelope claim. Such solids require separate full sweep checks.'},
        'board_bound': {'minimum_anchor_height_mm': minimum_height,
            'minimum_axis_normal_component': normal,
            'exact_cylinder_bare_gap_mm': bare_gap,
            'independent_closures_mm': BOARD_CLOSURES,
            'total_independent_closure_mm': closure,
            'remaining_gap_mm': residual, 'required_residual_mm': REQUIRED_RESIDUAL,
            'margin_above_required_mm': residual-REQUIRED_RESIDUAL,
            'capsule_bare_gap_mm': capsule_gap,
            'capsule_remaining_gap_mm': capsule_gap-closure,
            'derivation': 'For height H, outward axis normal component v>0 and start s, exact support gap is H+s*v-R*sqrt(1-v*v). It increases with H,s,v, so the listed minima bound all accepted poses. An annulus has the same outer support as its solid cylinder. Axis directions lie within asin(eta1); v_min=v0*sqrt(1-eta1^2)-sqrt(1-v0^2)*eta1.',
            'accounting': 'Includes minimum measured height AND full independent registration, retention, thermal, profile and warp allowances. This intentionally gives no cancellation credit; registration may overlap measured-height control. Published OD tolerance is not added again.'},
        'source_XY_screen': {'minimum_gap_after_closures_mm': source_min,
            'required_residual_mm': REQUIRED_RESIDUAL,
            'collet_XY_closures_mm': XY_CLOSURES, 'source_outward_profile_mm': SOURCE_XY_PROFILE,
            'source_obstacle_count': len(all_rows), 'ledger': ledger,
            'method': 'No broad phase. Check all twelve conservative axis-cone/capsule XY boxes against all retained KA-B/KB-F courtyard, support, tool and loom reservations, plus six retained bulk reserves and the reconciled monitor. Expand collets and source separately. XY nonoverlap holds through axial withdrawal regardless of Z. No part-height fidelity or unseen fastener claim.'},
        'gates': {'conditional_outer_collet_to_own_board': residual >= REQUIRED_RESIDUAL,
                  'conditional_outer_collet_to_listed_source': source_min >= REQUIRED_RESIDUAL,
                  'actual_axis_shape_material_qualification': False,
                  'bore_retention_and_insulation': False, 'new_arm_and_joint_geometry': False,
                  'wire_to_new_collet_or_arm': False, 'complete_new_feed_collision_sweep': False,
                  'actual_C0_C1_C2_wire_shape': False, 'physical_fit': False,
                  'all_100_trim_access': False, 'native': False},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    text = json.dumps(result, indent=2, sort_keys=True)+'\n'
    target = HERE/'collet-clearance.json'
    if args.check:
        base.need(target.read_text() == text, 'collet clearance evidence drift')
    else:
        target.write_text(text)
    print(json.dumps({'board_residual_mm': result['board_bound']['remaining_gap_mm'],
                      'source_XY_residual_mm': result['source_XY_screen']['minimum_gap_after_closures_mm'],
                      'gates': result['gates']}))


if __name__ == '__main__':
    main()
