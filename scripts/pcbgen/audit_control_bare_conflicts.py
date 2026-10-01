"""Retain the complete P bare-board conflicts and a bounded source proposal.

This is a source/geometry audit, not native candidate or electrical acceptance.
The original failed geometry remains immutable and is not rebound to a repair.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def audit(cache, output):
    cache = Path(cache)
    paths = {
        'drc': cache / 'bare-drc.json',
        'geometry': cache / 'bare-geometry.json',
        'receipt': cache / 'bare-native-receipt.json',
        'partition': Path('design/partition/partition.json'),
        'definition': Path('design/boards/osc-control.json'),
        'lock': Path('design/grid/placements.lock.json'),
        'selector': Path('design/mechanical/selector-assembly.json'),
        'algorithm': Path(__file__),
    }
    raw = {key: path.read_bytes() for key, path in paths.items()}
    data = {key: json.loads(value) for key, value in raw.items() if key != 'algorithm'}
    drc, geometry, receipt = (data[key] for key in ('drc', 'geometry', 'receipt'))
    sha = lambda value: hashlib.sha256(value).hexdigest()
    if receipt['model_entry_allowed'] or receipt['stage'] != 'bare_source_planning':
        raise ValueError('Expected the unaccepted bare planning receipt')
    for key in ('drc', 'geometry'):
        if receipt['artifacts_sha256'][str(paths[key])] != sha(raw[key]):
            raise ValueError('Bare artifact differs from its original receipt')
    board = Path(geometry['board'])
    if sha(board.read_bytes()) != geometry['board_sha256'] or geometry['board_sha256'] != receipt['board_sha256']:
        raise ValueError('Bare board authority changed')
    if drc['source'] != board.name or drc['kicad_version'] != '10.0.6':
        raise ValueError('Wrong native oracle or board')
    errors = [row for row in drc['violations'] if row['severity'] == 'error']
    counts = Counter(row['type'] for row in errors)
    if counts != {'items_not_allowed': 30, 'copper_edge_clearance': 1}:
        raise ValueError('The retained complete conflict inventory changed')
    classes = []
    for index, row in enumerate(errors):
        if row['type'] == 'items_not_allowed':
            if 'keepout:load-power:' not in row['description']:
                raise ValueError('Unexpected reservation in bare conflict set')
            cause = 'Broad original load-power reservation overlaps an actual fixed source object'
        else:
            if not any(item['uuid'] == 'cc975e76-8429-59d6-8fb9-2d60d8d3ee5e' for item in row['items']):
                raise ValueError('Unexpected copper-edge conflict')
            cause = 'RV601 retained mounting annulus and drill cross the original notch edge'
        classes.append({'index': index, 'source_cause': cause, 'native_violation': row})
    pad = next(item for item in geometry['items'] if item['uuid'] == 'cc975e76-8429-59d6-8fb9-2d60d8d3ee5e')
    hole = next(item for item in geometry['holes'] if item['uuid'] == pad['uuid'])
    placement = next(row for row in data['lock']['placements'] if row['ref'] == 'RV601')
    primitive = pad['analytic_primitives']['F.Cu']
    if primitive['kind'] != 'circle' or primitive['half_size_nm'] != [1200000, 1200000] or hole['size_mm'] != [1.8, 1.8]:
        raise ValueError('Exact retained mounting geometry changed')
    if placement['uid'] != 'C:F1.FREQ' or [placement['x_mm'], placement['y_mm'], placement['rot_deg']] != [99.5, 185.0, 0]:
        raise ValueError('Fixed panel hardware identity changed')
    report = {
        'status': '31 actual native errors; planning export only; candidate/model entry prohibited',
        'source_sha256': {str(paths[key]): sha(value) for key, value in raw.items()},
        'board_sha256': geometry['board_sha256'],
        'coordinate_frame': geometry['coordinate_frame'],
        'rule_counts': dict(counts), 'complete_native_conflicts': classes,
        'fixed_mount_conflict': {
            'ref': 'RV601', 'pad': '4', 'uid': placement['uid'], 'uuid': pad['uuid'],
            'source_centre_mm': [94.2, 185.0], 'copper_radius_mm': 1.2,
            'drill_radius_mm': 0.9, 'original_notch_edge_x_mm': 94.0,
            'copper_outside_board_mm': 1.0, 'drill_outside_board_mm': 0.7,
            'required_copper_edge_clearance_mm': 0.5,
            'maximum_legal_local_edge_x_mm': 92.5,
        },
        'unselected_local_tab_candidate': {
            'x_mm': 92.35, 'y_interval_mm': [182.8, 187.2],
            'nominal_copper_edge_clearance_mm': 0.65,
            'nominal_drill_edge_clearance_mm': 0.95,
            'O5_conservative_body_support_right_x_mm': 91.6,
            'nominal_body_support_XY_gap_mm': 0.75,
            'existing_two_axis_error_allocation_mm': 0.2,
            'remaining_XY_gap_mm': 0.55,
            'required_neighbor_XY_gap_mm': 0.5,
            'O5_adapter_right_x_mm': 92.4,
            'projected_adapter_overlap_mm': 0.05,
            'P_rear_z_mm': -13.4, 'O5_front_z_mm': -16.0,
            'nominal_P_to_O5_board_z_gap_mm': 2.6,
            'scope': 'Proposed source outline repair only. Full source envelope and tolerance audit, native rule gate and manager contract amendment remain required. No pad, hole, hardware or clearance change.',
        },
        'reservation_repair_candidate': {
            'old_id': 'load-power', 'old_rect_mm': [139, 176.5, 196, 184],
            'old_faces': ['F.Cu', 'B.Cu'],
            'proposal': 'Replace the undifferentiated strip with individual 6 x 6 mm B-side terminal/fan reservations at the same four lands, matching the two existing AGND reservations. Preserve actual finite fan, tool, wire and neighboring component volumes; do not grant foreign objects owning-terminal exceptions.',
            'refs': ['TP990025', 'TP990027', 'TP990029', 'TP990031'],
            'scope': 'UNSELECTED pending analytic volume checks and native source candidate; all unrelated reserves remain unchanged.',
        },
    }
    if any(path.read_bytes() != raw[key] for key, path in paths.items()):
        raise ValueError('Conflict authority changed during audit')
    Path(output).write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cache', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.cache, args.output)
    print(result['status'])
