#!/usr/bin/env python3
"""Source-only mechanical comparisons; no KiCad invocation or canonical writes."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE_FILES = [
    'design/partition/partition-input.json', 'design/partition/partition.json',
    'design/partition/connector-packing-candidate.json',
    'design/partition/floorplan-candidate.json', 'design/partition/loom-candidate.json',
    'design/partition/mechanical-candidate.json', 'design/reports/io-partition.json',
    'design/grid/placements.lock.json', 'design/mechanical/core-rear-allowance.json',
    'design/connectors/jst-gh.json', 'design/partition/harness-wire-evidence.json',
    'schematic/boards/osc-core.net', 'scripts/checks/partition35_loom.py',
    'scripts/checks/partition35_mechanical.py', 'scripts/checks/connector_packing35.py',
    'circuit/cad-receipts/ic15-footprint-potentiometer-bourns-tc33x-vertical.receipt.json',
]


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def fingerprint(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def rect_overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def overlap_box(a, b):
    return [round(max(a[0], b[0]), 6), round(max(a[1], b[1]), 6),
            round(min(a[2], b[2]), 6), round(min(a[3], b[3]), 6)]


def bounds(points, hx=0, hy=0):
    return [min(p[0] for p in points)-hx, min(p[1] for p in points)-hy,
            max(p[0] for p in points)+hx, max(p[1] for p in points)+hy]


def in_outline(rect, outline):
    # Candidate keeps the exact orthogonal K outline including the inlet notch.
    x0, y0, x1, y1 = bounds(outline)
    return rect_overlap(rect, [x0, y0, x1, 246]) or rect_overlap(rect, [x0, 246, 258, y1])


def axial_route(x, y, start, end):
    if end <= start:
        raise ValueError('nonpositive axial span')
    points = [[x, y+4*math.sin(math.pi*i/100)**2, start+(end-start)*i/100] for i in range(101)]
    # Analytic curvature lower bound for the continuous sine-squared bow.
    radius = (end-start)**2/(8*math.pi**2)
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    # Chords underbound arc length. Integral sqrt(1+yprime²) <= 1+yprime²/2.
    upper = end-start + 4*math.pi**2/(end-start)
    return points, radius, length, upper


def slab_box(points, z0, z1, hx, hy):
    selected = []
    for a, b in zip(points, points[1:]):
        lo, hi = sorted((a[2], b[2]))
        if hi < z0 or lo > z1:
            continue
        for z in (max(lo, z0), min(hi, z1)):
            t = (z-a[2])/(b[2]-a[2]) if b[2] != a[2] else 0
            selected.append([a[k]+t*(b[k]-a[k]) for k in range(3)])
    return bounds(selected, hx, hy) if selected else None


def owner(family, partition):
    matches = [board for board, families in partition.items() if family in families]
    if len(matches) != 1:
        raise ValueError('missing/ambiguous family: '+family)
    return matches[0]


def freeze_interfaces(partition):
    connectors = {h['id']: h for h in partition['connectors']}
    fields = ('id', 'pcb_reference', 'board', 'center_mm', 'footprint_origin_mm',
              'rotation_deg', 'kicad_orientation_deg', 'side', 'pin_map',
              'header_mpn', 'housing_mpn', 'contact_mpn', 'mechanical_pads')
    return [{'id': h['id'], 'endpoints': [{k: connectors[i][k] for k in fields}
                                       for i in h['header_ids']]}
            for h in partition['harnesses']]


def assert_interfaces(frozen, partition):
    if frozen != freeze_interfaces(partition):
        raise ValueError('frozen harness identity/pin order/endpoint pose changed')


def roles():
    text = (ROOT/'schematic/boards/osc-core.net').read_text()
    out = {}
    for block in text.split('\n\t\t(comp\n')[1:]:
        ref = re.match(r'\s*\(ref "([^\"]+)"\)', block).group(1)
        if not ref.startswith('RV'):
            continue
        role = re.search(r'\(name "Role"\)\s*\(value "([^\"]+)"\)', block)
        if not role:
            raise ValueError('missing role '+ref)
        out[ref] = role.group(1)
    return out


def load_inputs():
    return {Path(p).stem: read(p) for p in BASE_FILES if p.endswith('.json')}


def source_lock(inputs, cfg):
    paths = set(BASE_FILES)
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'footprints/kicad/zudo-osc-hole-field.3dshapes').glob('*') if p.is_file())
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'boards').glob('*/*.kicad_pcb'))
    for p in inputs['io-partition']['physical_packages']:
        paths.add('footprints/kicad/zudo-osc-hole-field.pretty/'+p['footprint'].split(':')[-1]+'.kicad_mod')
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'circuit/cad-receipts').glob('*.json'))
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'.claude/skills/component-jst-gh').glob('*.json'))
    paths.update(['.claude/skills/component-spec-audit/references/inventory.json',
                  '.claude/skills/circuit-spec-integration/references/rules.json',
                  'design/connectors/sources/jst-gh.pdf', 'design/partition/sources/alpha-6821.pdf',
                  'design/partition/sources/alpha-5859.pdf', 'circuit/sources/ic-library/TC33X.pdf'])
    return {'baseline_sha': cfg['baseline_sha'], 'tool_sha256': {p.name: digest(p) for p in [HERE/'build.py', HERE/'candidates.json', HERE/'preview-template.html', HERE/'inputs/trimmer-functions.json', HERE/'inputs/component-review.json']}, 'sha256': {p: digest(ROOT/p) for p in sorted(paths)}}


def model_inventory(parts):
    receipts = [json.loads(p.read_text()) for p in (ROOT/'circuit/cad-receipts').glob('*.json')]
    rows = []
    for fp, count in sorted(Counter(p['footprint'] for p in parts).items()):
        path = 'footprints/kicad/zudo-osc-hole-field.pretty/'+fp.split(':')[-1]+'.kicad_mod'
        refs = []
        for receipt in receipts:
            if path in receipt.get('representation', {}).get('files', []):
                refs.append({'asset': receipt['identity']['asset_id'], 'fidelity': receipt.get('fidelity', {})})
        models = re.findall(r'\(model\s+"([^\"]+)"', (ROOT/path).read_text())
        rows.append({'footprint': fp, 'count': count, 'footprint_sha256': digest(ROOT/path),
                     'models': models, 'receipts': refs, 'body_height_mm': None,
                     'scope': 'Actual courtyard used; model references/fidelity inventoried only. Exact assembled height, terminals and adjustment axis NOT VERIFIED. No opaque solid inferred from footprint.'})
    return rows


def place_label(seed, size, obstacles, occupied):
    def inside(q):
        return q[0] >= 4.3 and q[1] >= 8.3 and q[2] <= 313.7 and q[3] <= 291.7 and not (q[2] > 257.7 and q[3] > 245.7)
    candidates = sorted(((x, y) for x in range(5, 314-int(size[0]), 2) for y in range(9, 292-int(size[1]), 2)),
                        key=lambda xy: ((xy[0]-seed[0])**2+(xy[1]-seed[1])**2, xy))
    for x, y in candidates:
        q = [x, y, x+size[0], y+size[1]]
        if not inside(q):
            continue
        cells = [(i, j) for i in range(math.floor(q[0]/10), math.floor(q[2]/10)+1)
                        for j in range(math.floor(q[1]/10), math.floor(q[3]/10)+1)]
        nearby = {k for cell in cells for k in obstacles.get(cell, ())}
        if not any(rect_overlap(q, occupied[k]) for k in nearby):
            for cell in cells:
                obstacles.setdefault(cell, []).append(len(occupied))
            occupied.append(q)
            return q
    raise ValueError('no readable label reservation fits')


def label_obstacles(board, side, core, assigned, connectors, passages, supports):
    boxes = [p['courtyard_mm'] for p in core if assigned[p['ref']] == board and p['side'] == side]
    boxes += [p['box_mm'] for p in passages if p['board'] == board]
    boxes += [[x-1.6, y-1.6, x+1.6, y+1.6] for x, y in supports]
    # Conservatively reserve every existing K header on either face, including removed mates.
    boxes += [h['land_courtyard_mm'] for h in connectors.values() if h['board'] == 'K']
    boxes += [a['box_mm'] for a in read('design/partition/partition.json')['K_service_apertures']]
    boxes += [[180, 220, 256, 290]]
    expanded = [[q[0]-.25, q[1]-.25, q[2]+.25, q[3]+.25] for q in boxes]
    buckets = {}
    for k, q in enumerate(expanded):
        for i in range(math.floor(q[0]/10), math.floor(q[2]/10)+1):
            for j in range(math.floor(q[1]/10), math.floor(q[3]/10)+1):
                buckets.setdefault((i, j), []).append(k)
    return buckets, expanded


def reservation_conflicts(box, board, connectors, harnesses, supports, apertures):
    occupied = [('support', str([x, y]), [x-1.6, y-1.6, x+1.6, y+1.6]) for x, y in supports]
    occupied.append(('protection-feed-reserve', 'unselected feed/protection', [180, 220, 256, 290]))
    for h in harnesses:
        if not h['unchanged'] and h['core_board'] == board:
            c = connectors[h['id']+'-K']
            occupied.append(('header-courtyard', c['pcb_reference'], c['land_courtyard_mm']))
    occupied.extend(('service-aperture', a['header_id'], a['box_mm']) for a in apertures)
    return [{'kind': kind, 'id': name, 'overlap_mm': overlap_box(box, other)}
            for kind, name, other in occupied if rect_overlap(box, other)]


def build(cfg, inputs):
    src, partition = inputs['partition-input'], inputs['partition']
    floor = inputs['floorplan-candidate']['placements']
    physical = {p['ref']: p for p in inputs['io-partition']['physical_packages']}
    core = [p for p in floor if p['board'] == 'K']
    connectors = {h['id']: h for h in partition['connectors']}
    routes = {r['id']: r for r in inputs['loom-candidate']['routes']}
    frozen = freeze_interfaces(partition)
    assert len(frozen) == 195 and sum(any(e['board'] == 'K' for e in h['endpoints']) for h in frozen) == 191
    role_map = roles()
    labels = {t['ref']: t for t in json.loads((HERE/'inputs/trimmer-functions.json').read_text())['trimmers']}
    if set(labels) != set(role_map): raise ValueError('label Ref inventory changed')
    for ref, t in labels.items():
        if t['role'] != role_map[ref] or t['block'] != physical[ref]['instance']: raise ValueError('label Ref/Block/Role mismatch '+ref)
    source_trims = [p for p in core if p['ref'].startswith('RV')]
    assert len(source_trims) == 100
    families = {p['instance']: p['family'] for p in physical.values()}
    board_outline = src['boards']['K']['outline']
    alternatives = []
    for alt in cfg['alternatives']:
        mapping = cfg['partitions'][alt['partition']]
        planes = alt['front_z_mm']
        if set(mapping) != set(planes) or any(not math.isfinite(z) or z >= 0 for z in planes.values()):
            raise ValueError('invalid board planes')
        if len(set(planes.values())) != len(planes):
            raise ValueError('coincident core planes')
        assigned = {p['ref']: owner(physical[p['ref']]['family'], mapping) for p in core}
        boards = []
        for board, z in planes.items():
            count = sum(b == board for b in assigned.values())
            boards.append({'id': board, 'outline_mm': board_outline, 'bounding_size_mm': [310, 284],
                           'notch_size_mm': [56, 46], 'gross_area_mm2': 85464,
                           'front_z_mm': z, 'back_z_mm': z-cfg['core_thickness_mm'],
                           'front_body_limit_z_mm': z+cfg['front_body_ceiling_mm'],
                           'rear_body_limit_z_mm': z-cfg['core_thickness_mm']-cfg['rear_body_ceiling_mm'],
                           'supports_xy_mm': src['boards']['K']['supports_mm'],
                           'master_package_count_including_dnp': count,
                           'support_load_path': cfg['support_contract']})
        harnesses, passages, problems = [], [], []
        min_bend = inputs['harness-wire-evidence']['derived']['minimum_bend_radius_using_max_OD_mm']
        for h in partition['harnesses']:
            ends = [connectors[i] for i in h['header_ids']]
            old = routes[h['id']]
            if all(e['board'] != 'K' for e in ends):
                harnesses.append({'id': h['id'], 'unchanged': True,
                                  'centreline_length_mm': old['centreline_length_mm'],
                                  'cut_length_mm': old['cut_length_max_mm'], 'delta_cut_mm': 0})
                points = old['centreline_points_mm_positive_rear']
                for board, z in planes.items():
                    box = slab_box(points, -z, -z+cfg['core_thickness_mm'],
                                   old['ribbon_channel_width_mm']/2+.05,
                                   old['ribbon_channel_depth_mm']/2+.05)
                    if box and in_outline(box, board_outline):
                        problems.append({'kind': 'utility-loom-board', 'id': h['id'], 'board': board,
                                         'box_mm': box, 'depth_mm': [-z, -z+cfg['core_thickness_mm']],
                                         'disposition': 'Unchanged JL-P interface/loop must clear a reviewed board passage or core shape; do not move non-core endpoint.'})
                continue
            noncore = next(e for e in ends if e['board'] != 'K')
            endpoint = next(e for e in ends if e['board'] == 'K')
            instances = {s['net'].split('/')[1] for s in h['signals'] if s['net'].startswith('/')}
            targets = {owner(families[i], mapping) for i in instances}
            if not targets:
                # Octave harness contains only global reference signals and belongs with OSC/reference.
                if not noncore['board'].startswith('O'):
                    raise ValueError('unresolved harness owner '+h['id'])
                targets = {owner('oscillator', mapping)}
            if len(targets) != 1:
                raise ValueError('mixed-destination harness '+h['id'])
            target = targets.pop()
            start = -src['boards'][noncore['board']]['face_z_mm'] + src['boards'][noncore['board']]['thickness_mm'] + 7.3
            end = -planes[target]-7.3
            x, y = endpoint['center_mm']
            points, radius, length, upper = axial_route(x, y, start, end)
            cut = math.ceil(upper+cfg['cut_allowance_mm'])
            row = {'id': h['id'], 'unchanged': False, 'core_board': target,
                   'core_endpoint_ref': endpoint['pcb_reference'], 'noncore_endpoint_ref': noncore['pcb_reference'],
                   'core_xy_mm': [x, y], 'core_face_z_mm': planes[target],
                   'route_positive_rear': {'x_mm': x, 'y_mm': y, 'start_depth_mm': start, 'end_depth_mm': end,
                                           'bow_y_mm': 4, 'equation': 'y=y0+4*sin(pi*t)^2; depth=start+(end-start)*t'},
                   'centreline_length_mm': round(length, 6), 'continuous_length_upper_mm': round(upper, 6),
                   'cut_length_mm': cut, 'previous_cut_length_mm': old['cut_length_max_mm'],
                   'delta_cut_mm': cut-old['cut_length_max_mm'],
                   'radius_lower_mm': round(radius, 6), 'bend_requirement_mm': min_bend,
                   'bend_pass': radius >= min_bend,
                   'channel_mm': [old['ribbon_channel_width_mm'], old['ribbon_channel_depth_mm']],
                   'comb_max_spacing_mm': 25, 'end_comb_max_distance_mm': 15,
                   'reuse': 'NOT QUALIFIED; modeled cut differs and installed slack/retention unknown'}
            harnesses.append(row)
            if radius < min_bend:
                problems.append({'kind': 'bend-radius', 'id': h['id'], 'board': target,
                                 'radius_mm': radius, 'required_mm': min_bend})
            for board, z in planes.items():
                if z <= planes[target]:
                    continue
                box = slab_box(points, -z, -z+cfg['core_thickness_mm'],
                               old['ribbon_channel_width_mm']/2+.05+cfg['passage_edge_margin_mm'],
                               old['ribbon_channel_depth_mm']/2+.05+cfg['passage_edge_margin_mm'])
                if box and in_outline(box, board_outline):
                    conflicts = [{'ref': p['ref'], 'overlap_mm': overlap_box(box, p['courtyard_mm'])}
                                 for p in core if assigned[p['ref']] == board and rect_overlap(box, p['courtyard_mm'])]
                    passages.append({'kind': 'through-loom', 'id': h['id'], 'board': board,
                                     'box_mm': box, 'depth_mm': [-z, -z+1.6], 'part_conflicts': conflicts,
                                     'status': 'Required passage reservation, NOT cut/adopted. Full board material conflicts until reviewed.'})
        trims = []
        label_spaces = {(b, side): label_obstacles(b, side, core, assigned, connectors, passages+[p for p in problems if 'box_mm' in p], src['boards']['K']['supports_mm']) for b in planes for side in ('F.Cu', 'B.Cu')}
        for p in source_trims:
            ref, x, y = p['ref'], p['x_mm'], p['y_mm']
            board = assigned[ref]
            q = p['courtyard_mm']
            function_text = labels[ref]['label']
            label_size = [max(cfg['label_size_mm'][0], len(function_text)*.7+2), cfg['label_size_mm'][1]]
            label = place_label([q[0], q[3]+.5], label_size, *label_spaces[(board, p['side'])])
            collisions = [other['ref'] for other in core if other['ref'] != ref and assigned[other['ref']] == board
                          and other['side'] == p['side'] and rect_overlap(label, other['courtyard_mm'])]
            blocked_boards = [b for b, z in planes.items() if b != board and
                              ((p['side'] == 'B.Cu' and z < planes[board]) or
                               (p['side'] == 'F.Cu' and z > planes[board]))]
            trims.append({'ref': ref, 'function': function_text, 'role': role_map[ref], 'instance': physical[ref]['instance'],
                          'mpn': physical[ref]['mpn'] or None, 'board': board, 'mounted_face': p['side'],
                          'xy_mm': [x, y], 'rotation_deg': p['rotation_deg'], 'courtyard_mm': q,
                          'label_reservation_mm': label, 'label_conflicting_refs': collisions,
                          'label_lines': [ref, function_text], 'label_height_mm': cfg['label_text_height_mm'],
                          'label_displacement_mm': round(math.dist([q[0], q[3]+.5], label[:2]), 6),
                          'label_link': 'Matching Ref at device; leader/production silk reviewed by #249. This is reserved label area only.',
                          'label': ref+' '+function_text,
                          'tool_proposal': {'axis': '+Z normal if F.Cu / -Z normal if B.Cu; exact axis not verified',
                                            'shaft_diameter_mm': cfg['tool_shaft_diameter_mm'],
                                            'free_length_mm': cfg['tool_free_length_mm'],
                                            'blocked_core_planes': blocked_boards},
                          'access': 'OPEN: exact shaft/body/hand sweep and F-side approach through front assembly not qualified. Supported reversible tray required where blocked; no owner soldering.',
                          'envelope_status': 'MPN UNRESOLVED #248' if not physical[ref]['mpn'] else 'Source TC33X-2 top adjustment; #248 candidate bound 3.9 x 4.1 x 1.5 mm, alignment/seating and tool sweep unqualified'})
        connector_service = []
        for aperture in partition['K_service_apertures']:
            h = next(r for r in harnesses if not r['unchanged'] and r['id']+'-K' == aperture['header_id'])
            target = h['core_board']
            for b, z in planes.items():
                if z < planes[target]:
                    box = aperture['box_mm']
                    connector_service.append({'header_id': aperture['header_id'], 'target': target,
                                              'blocking_board': b, 'required_shaft_passage_box_mm': box,
                                              'shaft_diameter_mm': aperture['tool_shaft_diameter_mm'],
                                              'hole_diameter_mm': aperture['diameter_mm'],
                                              'part_conflicts': [p['ref'] for p in core if assigned[p['ref']] == b and rect_overlap(box, p['courtyard_mm'])],
                                              'status': 'Rear approach blocked until clearance/tool passage is reviewed; no fabricated latch fit.'})
        for passage in passages:
            passage['other_reservation_conflicts'] = reservation_conflicts(passage['box_mm'], passage['board'], connectors, harnesses, src['boards']['K']['supports_mm'], partition['K_service_apertures'])
        for passage in connector_service:
            passage['other_reservation_conflicts'] = reservation_conflicts(passage['required_shaft_passage_box_mm'], passage['blocking_board'], connectors, harnesses, src['boards']['K']['supports_mm'], [])
        power = []
        for route in inputs['loom-candidate']['load_power_routes']:
            a, b = route['points_mm_positive_rear'][0], route['points_mm_positive_rear'][-1]
            for board, z in planes.items():
                # Comparison bound only: #247 decides whether each branch is actually fed by this core.
                new_end = [b[0], b[1], b[2]+(-z-100)]
                lower = math.dist(a, new_end)+10
                power.append({'id': route['id'], 'hypothetical_feed_core': board,
                              'cut_lower_bound_mm': round(lower, 6), 'existing_ceiling_mm': 110,
                              'deterministic_budget_exceedance': lower > 110,
                              'required_bend_radius_mm': src['load_distribution']['minimum_bend_radius_mm'],
                              'diameter_max_mm': src['load_distribution']['diameter_max_mm'],
                              'status': 'Straight-line necessary bound only, not a realizable bent wire. Existing routes preserved; new feed topology/length/resistance pending #247.'})
        ordered = sorted(planes.items(), key=lambda x: -x[1])
        gaps = [{'front_board': a, 'rear_board': b, 'plane_pitch_mm': za-zb,
                 'pcb_face_gap_mm': round(za-zb-cfg['core_thickness_mm'], 6),
                 'body_gap_mm': round(za-zb-cfg['core_thickness_mm']-cfg['rear_body_ceiling_mm']-cfg['front_body_ceiling_mm'], 6)}
                for (a, za), (b, zb) in zip(ordered, ordered[1:])]
        alternative = {**alt, 'status': 'COMPARISON ONLY; identified blockers; not physical fit or adoption',
                       'boards': boards, 'family_owners': {f: b for b, fs in mapping.items() for f in fs}, 'interplane_gaps': gaps,
                       'rear_body_to_wall_mm': round(min(planes.values())-1.6-5-alt['rear_wall_z_mm'], 6),
                       'extra_case_depth_mm': -alt['rear_wall_z_mm']-src['enclosure']['inside_depth_mm'],
                       'harnesses': harnesses, 'through_loom_passages': passages,
                       'hard_conflicts': problems, 'connector_service_passages': connector_service,
                       'trimmers': trims, 'power_bounds': power,
                       'summary': {'harnesses_by_core': dict(Counter(h.get('core_board') for h in harnesses if not h['unchanged'])),
                                   'trimmers_by_core': dict(Counter(t['board'] for t in trims)),
                                   'hard_conflicts': dict(Counter(p['kind'] for p in problems)),
                                   'through_loom_passages': len(passages),
                                   'passage_part_conflicts': sum(len(p['part_conflicts']) for p in passages),
                                   'connector_service_passages': len(connector_service),
                                   'label_conflict_count': sum(bool(t['label_conflicting_refs']) for t in trims),
                                   'max_cut_mm': max(h['cut_length_mm'] for h in harnesses),
                                   'core_cut_range_mm': [min(h['cut_length_mm'] for h in harnesses if not h['unchanged']), max(h['cut_length_mm'] for h in harnesses if not h['unchanged'])]}}
        alternatives.append(alternative)
    return {'schema_version': 1, 'baseline_sha': cfg['baseline_sha'], 'status': cfg['status'],
            'config_sha256': digest(HERE/'candidates.json'),
            'frozen_interfaces': frozen, 'noncore_placements_sha256': fingerprint([p for p in floor if p['board'] != 'K']),
            'panel_sha256': digest(ROOT/'design/grid/placements.lock.json'),
            'physical_fit': 'NOT RUN #55/#64/#65', 'native_acceptance': 'NOT RUN; no native command or global slot',
            'models': model_inventory([physical[p['ref']] for p in core]),
            'core_placements': [{**p, 'family': physical[p['ref']]['family']} for p in core],
            'trimmer_unresolved_mpn_count': sum(not physical[p['ref']]['mpn'] for p in source_trims),
            'integration_parent_sha': cfg['integration_parent_sha'],
            'label_contract_sha': cfg['label_contract_sha'],
            'limitations': ['No route-to-route continuous collision or full harness/support sweep acceptance', 'No measured installation, carrier stiffness/thread engagement, seated component solids or tool/hand sweep', 'Power feed topology and service loops pending #247; no selected component substitution'],
            'component_review': json.loads((HERE/'inputs/component-review.json').read_text())['architecture_envelope_effects'],
            'alternatives': alternatives}


def stack_svg(alt, exploded=False):
    width, height = 1000, 720
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
           '<style>text{font:14px sans-serif;fill:#182836}.dim{font:12px monospace}.board{fill:#23896f;fill-opacity:.23;stroke:#17634f;stroke-width:2}.support{stroke:#805f31;stroke-width:3}</style>',
           f'<rect width="{width}" height="{height}" fill="#fafafa"/>',
           f'<text x="28" y="28">{alt["id"]} — {"exploded (display separation only)" if exploded else "assembled side section"}</text>',
           '<text x="28" y="51">UNVALIDATED COMPARISON · dimensions mm · panel front Z=0 · bodies are allowances</text>']
    scale = 2.35
    # X/depth side projection. Exploded mode changes only display Y, never reported physical Z.
    def line(depth, label, color='#888'):
        y = 90+depth*scale
        out.append(f'<path d="M45 {y}H775" stroke="{color}"/><text x="785" y="{y+4}" class="dim">{label}</text>')
    line(0, 'panel 0 / -2')
    for depth, label in [(4.2, 'EL -4.2'), (11.8, 'P -11.8'), (29, 'O rear -29')]:
        y = 90+depth*scale
        out.append(f'<path d="M45 {y}H775" stroke="#aab4bc"/>')
    out.append('<text x="45" y="145">Fixed JL/JR −10; P −11.8; EL −4.2; O −16/−29</text>')
    out.append(f'<rect x="{45+260*scale}" y="{90+45*scale}" width="{48*scale}" height="{40*scale}" fill="#bd654d" opacity=".22"/>')
    out.append(f'<text x="{45+230*scale}" y="{90+55*scale}">EXT reserve (y248–293)</text>')
    for i, b in enumerate(alt['boards']):
        depth = -b['front_z_mm']; y = 90+(depth+(i*12 if exploded else 0))*scale
        out.append(f'<rect class="board" x="{45+4*scale}" y="{y}" width="{310*scale}" height="{1.6*scale}"/>')
        out.append(f'<rect x="{45+4*scale}" y="{y-7.3*scale}" width="{310*scale}" height="{13.9*scale}" fill="#94b9aa" opacity=".15"/>')
        out.append(f'<text x="60" y="{y-22}">{b["id"]} 310 × 284, notch 56 × 46; F {b["front_z_mm"]:g}, B {b["back_z_mm"]:g}</text>')
        for x in (6.5, 311.5):
            out.append(f'<path class="support" d="M{45+x*scale} {y+4}v18"/>')
        out.append(f'<text class="dim" x="785" y="{y+4}">8 M2 seats</text>')
    rear_display = -alt['rear_wall_z_mm']+(len(alt['boards'])-1)*12 if exploded else -alt['rear_wall_z_mm']
    line(rear_display, f'rear {alt["rear_wall_z_mm"]:g}')
    out += [f'<text x="28" y="620">26 mm pitch · 24.4 mm bare face gap · 12.1 mm body gap · rear clearance {alt["rear_body_to_wall_mm"]:g} mm</text>',
            f'<text x="28" y="645">Through-loom openings: {alt["summary"]["through_loom_passages"]}; rear connector tool passages: {alt["summary"]["connector_service_passages"]}</text>',
            '<text x="28" y="670">Side carriers bear tray mass. Apertures, exact parts, cables, fasteners and tool sweeps need review.</text>',
            '<text x="28" y="696">Exploded service order: rear tray first; F/B adjustment requires supported access without owner soldering.</text>', '</svg>']
    return '\n'.join(out)+'\n'


def preview(report):
    data = json.dumps(report, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    template = (HERE/'preview-template.html').read_text()
    return template.replace('__REPORT__', data)


def outputs(cfg, inputs):
    report = build(cfg, inputs)
    out = {'comparison.json': encoded(report), 'source-lock.json': encoded(source_lock(inputs, cfg)),
           'inspection.html': preview(report)}
    for alt in report['alternatives']:
        for exploded in (False, True):
            out[alt['id']+('-exploded' if exploded else '-assembled')+'.svg'] = stack_svg(alt, exploded)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    cfg = json.loads((HERE/'candidates.json').read_text())
    existing_lock = HERE/'generated/source-lock.json'
    if existing_lock.exists():
        for name, expected in json.loads(existing_lock.read_text())['sha256'].items():
            if digest(ROOT/name) != expected:
                raise SystemExit('INPUT DRIFT: '+name+'; coordinator must review a new input epoch')
    generated = outputs(cfg, load_inputs())
    destination = HERE/'generated'
    if not args.check:
        destination.mkdir(exist_ok=True)
    for name, content in generated.items():
        path = destination/name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit('DRIFT: '+str(path.relative_to(ROOT)))
        else:
            path.write_text(content)
    print(('CHECK' if args.check else 'BUILD')+' source-only comparison: 5 alternatives, 195 frozen harnesses, 100 trimmers; physical/native NOT RUN')


if __name__ == '__main__':
    main()
