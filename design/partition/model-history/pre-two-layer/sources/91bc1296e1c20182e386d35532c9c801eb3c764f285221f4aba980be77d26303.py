"""Screen P original-grid main vias against the passing bare native authority."""
import argparse
import hashlib
import json
from pathlib import Path
import shapely
from shapely.geometry import Point, Polygon, box
from scripts.pcbgen.propose_rail_transfers import geometry, drill_geometry
from scripts.pcbgen.uuid_tools import stable_uuid

ROOT = Path(__file__).resolve().parents[2]


def retained_path(name):
    path = Path(name)
    if str(path).startswith('/work/'):
        path = ROOT / path.relative_to('/work')
    elif not path.is_absolute():
        path = ROOT / path
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('P source authority lies outside the worktree')
    return path


def plan(native_path, receipt_path, manifest_path, output):
    paths = [native_path, receipt_path, manifest_path, Path(__file__),
        Path('scripts/pcbgen/propose_rail_transfers.py'), Path('scripts/pcbgen/uuid_tools.py')]
    raw = {str(path): Path(path).read_bytes() for path in paths}
    sha = lambda value: hashlib.sha256(value).hexdigest()
    hashes = {path: sha(value) for path, value in raw.items()}
    native = json.loads(raw[str(native_path)])
    receipt = json.loads(raw[str(receipt_path)])
    manifest = json.loads(raw[str(manifest_path)])
    if native['board_id'] != 'osc-control' or receipt['stage'] != 'bare_source_planning' or receipt['rule_error_count'] or receipt['schematic_parity_count']:
        raise ValueError('Passing P bare geometry/parity authority required for site screening')
    if receipt['model_entry_allowed'] or native['board_sha256'] != receipt['board_sha256']:
        raise ValueError('Expected bare planning authority, not a conductor model')
    if receipt['artifacts_sha256'][str(native_path)] != hashes[str(native_path)]:
        raise ValueError('Bare native export changed')
    for path, expected in receipt['source_sha256'].items():
        resolved = retained_path(path)
        if sha(resolved.read_bytes()) != expected:
            raise ValueError('Bare source changed before array planning: '+path)
        hashes[str(resolved)] = expected
    board_path = retained_path(native['board'])
    if sha(board_path.read_bytes()) != native['board_sha256']:
        raise ValueError('Bare board changed')
    hashes[str(board_path)] = native['board_sha256']
    lands = manifest['all_P_main_lands']
    if len(lands) != 6 or len({row['reference'] for row in lands}) != 6:
        raise ValueError('All six fixed P lands required')
    rules = {row['ref']: row for row in receipt['own_terminal_exceptions']}
    if set(rules) != {row['reference'] for row in lands}:
        raise ValueError('Every land needs its exact native-tested reservation')
    custom_keepouts = {row['keepout_uuid'] for row in rules.values()}
    shapes, owners = [], []
    for item in native['items']:
        for contours in item['copper'].values():
            shapes.append(geometry(contours))
            owners.append(item)
    tree = shapely.STRtree(shapes)
    holes = native['holes']
    hole_shapes = [drill_geometry(row) for row in holes]
    hole_tree = shapely.STRtree(hole_shapes)
    keepouts = [(row, geometry(row['contours'])) for row in native['zones']
                if row['keepout'] and (row['vias_forbidden'] or row['uuid'] in custom_keepouts)]
    outline = Polygon(native['outline_mm'])
    rows = []
    for land in lands:
        ref, net = land['reference'], land['net']
        pads = [item for item in native['items'] if item.get('ref') == ref]
        x, y = [a+b for a, b in zip(land['center_mm'], [100, 50])]
        if len(pads) != 1 or pads[0]['pad'] != '1' or pads[0]['net'] != net or pads[0]['xy_mm'] != [x, y] or set(pads[0]['copper']) != {'B.Cu'}:
            raise ValueError('Fixed main pad identity, position, net or face changed')
        own_area = box(x-2, y-2, x+2, y+2)
        accepted, blocked = [], []
        for ix in range(5):
            for iy in range(5):
                point = Point(x+(ix-2)*.7, y+(iy-2)*.7)
                issues = []
                if not own_area.covers(point.buffer(.352)):
                    raise ValueError('Finite via escapes its owning land')
                if not outline.buffer(-.852).covers(point):
                    issues.append({'type': 'board-edge'})
                for j in tree.query(point.buffer(.602)):
                    if owners[j]['net'] != net and point.distance(shapes[j]) < .602:
                        issues.append({'type': 'foreign-copper', 'uuid': owners[j]['uuid'],
                            'ref': owners[j].get('ref'), 'pad': owners[j].get('pad'), 'net': owners[j]['net']})
                for j in hole_tree.query(point.buffer(.402)):
                    if point.distance(hole_shapes[j]) < .402:
                        issues.append({'type': 'existing-hole', 'uuid': holes[j]['uuid']})
                for zone, shape in keepouts:
                    if not shape.intersects(point.buffer(.352)):
                        continue
                    if zone['uuid'] == rules[ref]['keepout_uuid'] and zone['layer'] == 'B.Cu' and shape.covers(own_area):
                        continue
                    issues.append({'type': 'foreign-reservation', 'uuid': zone['uuid']})
                row = {'uuid': stable_uuid('osc-control', 'load-array:'+net, ref+':'+str(ix)+':'+str(iy)),
                    'grid_index': [ix, iy], 'xy_mm': [point.x, point.y], 'collisions': issues}
                (blocked if issues else accepted).append(row)
        if not accepted:
            raise ValueError('No legal original-grid transfer site for '+ref)
        rows.append({'ref': ref, 'net': net, 'owning_pad_uuid': pads[0]['uuid'],
            'legal_sites': accepted, 'blocked_sites': blocked})
    if any(sha(Path(path).read_bytes()) != expected for path, expected in hashes.items()):
        raise ValueError('Array planning authority changed')
    portable_hashes = {str(retained_path(path).relative_to(ROOT)): value for path, value in hashes.items()}
    report = {'status': 'UNSELECTED finite P main-array plan; fresh native candidate/connectivity and electrical gates required',
        'source_sha256': portable_hashes, 'board_sha256': native['board_sha256'],
        'via_diameter_mm': .7, 'via_drill_mm': .3, 'pitch_mm': .7,
        'copper_clearance_mm': .25, 'hole_clearance_mm': .25, 'copper_edge_clearance_mm': .5,
        'geometry_guard_mm': .002, 'rows': rows,
        'retained_via_count': sum(len(row['legal_sites']) for row in rows),
        'scope': 'Only original 5 x 5 grid sites. Whole finite via inside exact own land; all four native conductor layers, existing holes and both native/custom reservations checked. No equal-sharing or barrel resistance assumption.'}
    Path(output).write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('P legal original-grid main sites:', report['retained_via_count'], 'over six lands')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('native', 'receipt', 'manifest', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    plan(args.native, args.receipt, args.manifest, args.output)
