"""Additive source candidate. No CAD, manufacturing, or cable qualification."""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PRIOR = HERE.parent / 'hybrid-service-layout/proposal.json'
BASELINE = '42ff6eab4f4fd4be28b78cd35ef49ecbabaf2b64'


def mm(inches):
    return round(inches * 25.4, 6)


def overlap(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def grow(box, margin):
    return [box[0]-margin, box[1]-margin, box[2]+margin, box[3]+margin]


def footprint(centre, length, width, angle):
    a = math.radians(angle)
    points = [(centre[0]+x*math.cos(a)-y*math.sin(a),
               centre[1]+x*math.sin(a)+y*math.cos(a))
              for x in (-length/2, length/2) for y in (-width/2, width/2)]
    return [round(min(p[0] for p in points), 6), round(min(p[1] for p in points), 6),
            round(max(p[0] for p in points), 6), round(max(p[1] for p in points), 6)]


def height_limit(xy, face, obstacles, withdrawal, margin):
    """Necessary ceiling only; obstacles below face are handled by tail screen."""
    limits = [{'id': o['id'], 'height_mm': round(o['z'][0]-face-withdrawal-margin, 6)}
              for o in obstacles if overlap(xy, o['xy']) and o['z'][1] > face]
    limits.append({'id': 'existing_cover_inner_z105',
                   'height_mm': round(105-face-withdrawal-margin, 6)})
    return sorted(limits, key=lambda x: (x['height_mm'], x['id']))


def build():
    old = json.loads(PRIOR.read_text())
    maps = old['pin_maps']
    # Same board planes and candidate support solids as prior study. No adoption.
    faces = {'J17901': 11.6, 'J17902': 50, 'J17903': 36.6,
             'J17904': 50, 'J17905': 36.6, 'J17906': 50}
    own_boards = {'J17901': ['A01-controltab', 'A01-controlupper'],
                  'J17903': ['A01-jack'], 'J17905': ['A01-jack']}
    coords = old['connector_coordinates']
    refs = {c['ref'] for c in coords}
    obstacles = [o for o in old['known_obstacles'] if o['id'] not in refs]
    obstacles += old['effective_support_solids']
    headers = []
    for c in coords:
        n = len(c['pins'])
        # TS0770 table A, three-decimal default tolerance +/- .005 inch.
        length = mm({8: .688, 10: .788, 14: .988}[n]+.005)
        xy = footprint(c['centre_mm'], length, mm(.338+.005), c['rotation_deg'])
        headers.append({'id': c['ref'], 'xy': xy, 'z': [faces[c['ref']], 105]})
    items = []
    for c, h in zip(coords, headers):
        ref = c['ref']; n = len(c['pins']); face = faces[ref]
        others = [o for o in obstacles if o['id'] not in own_boards.get(ref, ['A01-middle'])]
        # Other candidate assemblies have unknown maximum height: occupy through cover.
        others += [o for o in headers if o['id'] != ref]
        body_xy = grow(h['xy'], 1)  # planning positional/clearance allowance, not measured tolerance
        grip_xy = grow(body_xy, 2)  # extra housing-grip trial reservation, not ergonomic proof
        tail_z = [round(face-mm(.112+.011), 6), round(face-1.6, 6)]
        hits = [o['id'] for o in others if overlap(body_xy, o['xy']) and
                tail_z[0] <= o['z'][1] and o['z'][0] <= tail_z[1]]
        unknown = [o['ref'] for o in old['unknown_obstacles'] if overlap(grip_xy, o['xy'])]
        screens = {}
        for name, xy, delta in [('installed', body_xy, 0), ('withdrawal15', body_xy, 15),
                                ('grip_withdrawal15', grip_xy, 15)]:
            limits = height_limit(xy, face, others, delta, 1)
            screens[name] = {'xy_mm': xy, 'withdrawal_mm': delta,
                             'necessary_max_height_above_board_mm': limits[0]['height_mm'],
                             'limiting_obstacles': [o['id'] for o in limits if o['height_mm'] == limits[0]['height_mm']],
                             'status': 'UNKNOWN_ACTUAL_MAX_HEIGHT_AND_FULL_SWEEP'}
        items.append({'ref': ref, 'header': f'D25{n:02}-6002-AR', 'socket': f'891{n:02}-0101',
                      'socket_strain_relief': False, 'face_z_mm': face, 'coordinates': c,
                      'header_max_xy_mm': h['xy'], 'screens': screens,
                      'tail_below_nominal_pcb_mm': [mm(.112-.011)-1.6, mm(.112+.011)-1.6],
                      'tail_z_screen_mm': tail_z, 'known_tail_hits': hits,
                      'unknown_neighbor_projection_refs': sorted(unknown),
                      'mated_max_height_mm': None, 'cable_exit_z_mm': None,
                      'cable_cut_length_mm': None, 'minimum_bend_radius_mm': None})
    selected_maps = {}
    for name, m in maps.items():
        n = len(m['pins'])
        selected_maps[name] = {**m, 'header': f'D25{n:02}-6002-AR', 'socket': f'891{n:02}-0101'}
    bindings = [PRIOR, ROOT/'design/grid/placements.lock.json',
                ROOT/'design/architecture-278/implementation/stage17/generated/transport-component-rows.json']
    return {'adopted': False, 'status': 'SOURCE_CANDIDATE_NOT_INTEGRATED_FIT', 'baseline': BASELINE,
            'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in bindings},
            'pin_maps': selected_maps, 'connectors': items,
            'planning_assumptions': {'xy_allowance_mm': 1, 'vertical_clearance_mm': 1,
                'extra_grip_width_each_side_mm': 2, 'pcb_thickness_nominal_mm': 1.6,
                'withdrawal_trial_mm': 15, 'tolerance_or_ergonomic_qualification': False},
            'maker_constraints': {'controlled_units': 'inch; metric annotations reference only',
                'header_pin_exposure_interval_mm': [mm(.243-.005), mm(.243+.005)],
                'socket_minimum_pin_exposure_mm': mm(.230),
                'minimum_exposure_surplus_mm': mm(.243-.005-.230),
                'header_floor_above_seated_pcb_interval_mm': [mm(.390-.005-.253-.005), mm(.390+.005-.253+.005)],
                'conditional_floor_seated_socket_top_reference_mm': mm(.390-.253+.41),
                'minimum_body_cavity_total_width_gap_mm': mm(.250-.005-.238-.005),
                'minimum_body_cavity_total_length_gap_mm': mm(.608-.005-.58-.01),
                'minimum_bump_notch_width_gap_mm': mm(.165-.005-.14-.01),
                'header_tail_from_standoff_seat_interval_mm': [mm(.112-.011), mm(.112+.011)],
                'finished_hole_diameter_interval_mm': [mm(.035-.003), mm(.035+.003)],
                'socket_closed_height_reference_inch': .41,
                'socket_closed_height_metric_annotation_mm': 10.5,
                'socket_closed_height_inch_conversion_mm': mm(.41),
                'socket_closed_height_max_mm': None, 'socket_maximum_pin_insertion_mm': None},
            'retained_support_unknown_hits': old['unknown_support_projection_hits'],
            'unresolved': ['production header seating variation',
                'socket seated depth, maximum closed height, bump/key fit and retention',
                'ribbon exact selection, exit datum/direction, straight exit length, static/repeated-flex radius',
                'ribbon cut tolerance, clamp position and service slack allocation',
                'board bow and carrier registration tolerance',
                'full neighboring geometry including terminals and harnesses',
                'housing grip, supported unplugging, cable parking, core/board removal sweeps',
                '50 N support strength and no-SR cable strain management',
                'electrical budget, protection, ampacity, contact heating and signal integrity']}


def main():
    (HERE/'candidate.json').write_text(json.dumps(build(), indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
