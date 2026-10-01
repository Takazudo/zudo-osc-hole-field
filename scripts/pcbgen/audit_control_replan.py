"""Check the finite P revision against complete retained source envelopes.

The source envelopes remain conditional manufacturing/assembly requirements.
This screen does not replace the fresh pinned native candidate or qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.control_geometry_replan import neighbor_envelopes


def run(cache, output):
    cache = Path(cache)
    paths = {name: Path(path) for name, path in {
        'proposal': 'design/partition/control-ground-feasibility/proposal.json',
        'definition': 'design/partition/control-ground-feasibility/osc-control.json',
        'manifest': 'design/partition/control-ground-feasibility/osc-control.receipt.json',
        'partition': 'design/partition/partition.json',
        'partition_input': 'design/partition/partition-input.json',
        'floorplan': 'design/partition/floorplan-candidate.json',
        'selector': 'design/mechanical/selector-assembly.json',
        'lock': 'design/grid/placements.lock.json',
        'loom': 'design/partition/loom-candidate.json',
        'contact': 'design/partition/contact-transfer-proposal.json',
        'netlist': 'schematic/boards/osc-control.net',
        'algorithm': __file__,
        'geometry_algorithm': 'scripts/pcbgen/control_geometry_replan.py',
        'netlist_algorithm': 'scripts/pcbgen/netlist.py',
    }.items()}
    paths.update(geometry=cache/'bare-geometry.json', receipt=cache/'bare-native-receipt.json')
    raw = {name: path.read_bytes() for name, path in paths.items()}
    sha = lambda value: hashlib.sha256(value).hexdigest()
    data = {name: json.loads(value) for name, value in raw.items() if paths[name].suffix == '.json'}
    native, receipt, source = data['geometry'], data['receipt'], data['partition']
    for name, key in (('proposal', 'proposal_sha256'), ('definition', 'definition_sha256')):
        if data['manifest'][key] != sha(raw[name]):
            raise ValueError('Generated P revision is stale')
    if receipt['model_entry_allowed'] or receipt['artifacts_sha256'][str(paths['geometry'])] != sha(raw['geometry']):
        raise ValueError('Exact original bare planning authority required')
    if native['board_id'] != 'osc-control' or native['board_sha256'] != receipt['board_sha256']:
        raise ValueError('Bare native identity mismatch')
    if sha(Path(native['board']).read_bytes()) != native['board_sha256']:
        raise ValueError('Original bare board changed')
    original_sources = {Path(path).resolve(): value for path, value in receipt['source_sha256'].items()}
    if original_sources.get(paths['netlist'].resolve()) != sha(raw['netlist']):
        raise ValueError('Source package geometry changed since the bare export')
    components, _ = read_netlist(paths['netlist'])
    placements = [row for row in data['floorplan']['placements'] if row['board'] == 'P']
    headers = [row for row in source['connectors'] if row['board'] == 'P']
    lands = [row for row in source['load_side_terminals'] if row['board'] == 'P']
    refs = [r['ref'] for r in placements] + [r['pcb_reference'] for r in headers] + [r['reference'] for r in lands]
    if len(refs) != 418 or len(set(refs)) != 418 or set(refs) != {c.ref for c in components}:
        raise ValueError('Source body/land/header coverage is incomplete or duplicated')
    if set(refs) != {r['ref'] for r in receipt['source_footprint_origins']}:
        raise ValueError('Bare native footprint coverage differs from source')
    origins = {row['ref']: row for row in receipt['source_footprint_origins']}
    for row in placements:
        if origins[row['ref']]['source_xy_mm'] != [row['x_mm'], row['y_mm']] or origins[row['ref']]['side'] != row['side']:
            raise ValueError('Placement envelope differs from bare native source')
    front_count = sum(row['side'] == 'F.Cu' for row in placements)
    if front_count != 139 or len(placements)-front_count != 146:
        raise ValueError('P fixed/front and rear package inventory changed')
    # Full foreign B-side package courtyards are conservatively extruded in z.
    # F-side surface bodies are separated by the solid PCB; every actual
    # through-hole contact is still included by its B-side copper projection.
    bodies = []
    inflation = data['floorplan']['native_cached_inflation_ceiling_mm']
    for row in placements:
        if row['side'] == 'B.Cu':
            l, t, r, b = row['courtyard_mm']
            bodies.append((row['ref'], 'B-side package courtyard', box(l-inflation, t-inflation, r+inflation, b+inflation)))
    for row in headers:
        if row['side'] != 'B.Cu':
            raise ValueError('P header face changed')
        bodies.append((row['pcb_reference'], 'B-side header cached courtyard', box(*row['native_cached_courtyard_envelope_mm'])))
    copper = []
    for item in native['items']:
        contours = item['copper'].get('B.Cu', [])
        if contours:
            shape = unary_union([Polygon(c['shell'], c['holes']) for c in contours])
            copper.append((item.get('ref'), item.get('pad'), item['uuid'], translate(shape, -100, -50)))
    reservations = []
    for land in lands:
        x, y = land['center_mm']
        column = box(x-3, y-3, x+3, y+3)
        body_distances = sorted((column.distance(shape), ref, kind) for ref, kind, shape in bodies)
        copper_distances = sorted((column.distance(shape), ref, pad, uid) for ref, pad, uid, shape in copper if ref != land['reference'])
        if body_distances[0][0] < 0.25-1e-9 or copper_distances[0][0] < 0.25-1e-9:
            raise ValueError('Individual reservation collides with a foreign source envelope: '+land['reference'])
        reservations.append({'ref': land['reference'], 'column_XY_mm': [x-3, y-3, x+3, y+3],
            'foreign_body_count': len(body_distances), 'foreign_B_copper_count': len(copper_distances),
            'nearest_foreign_bodies': body_distances[:5], 'nearest_foreign_copper': copper_distances[:5]})
    contact = data['contact']['main_strand_class']
    radius = contact['minimum_copper_core_diameter_mm']/2
    extent = max(abs(value)+radius for point in contact['support_centres_relative_to_land_mm'] for value in point)
    if extent >= 2:
        raise ValueError('Proposed finite trial fan cores escape the fixed land projection')
    tab = data['proposal']['geometry_replan']['RV601_tab']
    neighboring = neighbor_envelopes(data['selector'], data['partition_input'], data['lock'], tab['left_x_mm'])
    tab_xy = box(tab['left_x_mm'], tab['y_interval_mm'][0], 94, tab['y_interval_mm'][1])
    o5_headers = []
    for row in source['connectors']:
        if row['board'] != 'O5':
            continue
        gap = tab_xy.distance(box(*row['native_cached_courtyard_envelope_mm']))
        o5_headers.append({'ref': row['pcb_reference'], 'XY_gap_mm': gap,
            'side': row['side'], 'closest_board_rear_z_mm': -17.6,
            'scope': 'Full header courtyard projection; body and mated harness are behind the unchanged O5 B face.'})
    if len(o5_headers) != 2 or any(row['side'] != 'B.Cu' for row in o5_headers):
        raise ValueError('Both O5 rear header envelopes required')
    channels = []
    for row in data['loom']['routes']:
        if not row['id'].startswith('K-O5-'):
            continue
        points = row['centreline_points_mm_positive_rear']
        width, depth = row['ribbon_channel_width_mm'], row['ribbon_channel_depth_mm']
        projection = box(min(p[0] for p in points)-width/2-.05,
                         min(p[1] for p in points)-depth/2-.05,
                         max(p[0] for p in points)+width/2+.05,
                         max(p[1] for p in points)+depth/2+.05)
        z_gap = min(p[2] for p in points)-.05 + neighboring['P_rear_z_mm']
        xy_gap = tab_xy.distance(projection)
        if min(xy_gap, z_gap) <= .5:
            raise ValueError('O5 retained loom channel lacks source clearance')
        channels.append({'id': row['id'], 'complete_channel_XY_bounds_mm': list(projection.bounds),
            'XY_gap_mm': xy_gap, 'rear_z_gap_mm': z_gap, 'interpolation_guard_mm': .05})
    if len(channels) != 2:
        raise ValueError('Both complete O5 channels required')
    result = {'status': 'PASS conditional source-envelope screen only; native candidate and physical qualification NOT RUN',
        'source_sha256': {str(paths[name]): sha(value) for name, value in raw.items()},
        'source_footprint_count': len(refs), 'source_front_surface_packages': front_count,
        'source_rear_package_count': len(bodies)-len(headers), 'source_rear_header_count': len(headers),
        'terminal_reservations': reservations, 'trial_core_fan_half_extent_mm': extent,
        'O5_body_support_and_board': neighboring, 'O5_headers': o5_headers, 'O5_loom_channels': channels,
        'other_O5_envelopes': {
            'carrier_plate_and_tool_right_x_mm': 90.0,
            'carrier_stem_right_x_mm': 84.0,
            'carrier_rails_max_y_mm': 172.0,
            'scope': 'Existing 15 mm plate/tool and 3 mm stem at x82.5, plus source rail y170..172, are separated in XY. Bushing/shaft/8 mm knob are narrower. No new installed tool corridor is claimed.',
        },
        'qualification_requirements': [
            'Existing body/support/tail, relative-axis and relative-z source allocations must hold in the installed O5/P assembly under #55/#65.',
            'All B-side components, solder and through-hole tails must remain within their retained courtyard/pad assembly envelopes. Unknown exact solid dimensions remain qualification requirements.',
            'Factory P soldering/tool approach is constrained to each finite individual column with K and intervening loom absent; no installed service access is inferred.',
            'The nineteen-core trial fits only its declared cores; actual extra solder/strand/insulation metal must satisfy the explicit maximum contact envelope. Conductivity/current/resistance qualification is separate.',
            'Unchanged full load-wire routes remain their existing conditional source proposals. New finite P fan-to-bulk interfaces and whole-wire electrical witnesses are not selected by this envelope screen.',
        ], 'canonical_promotion_allowed': False}
    if any(path.read_bytes() != raw[name] for name, path in paths.items()):
        raise ValueError('P source changed during envelope screen')
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cache', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = run(args.cache, args.output)
    print(result['status'])
