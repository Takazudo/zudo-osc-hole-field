#!/usr/bin/env python3
"""Reproducible, source-only #245 core comparisons and disposable fixture inputs.

No KiCad invocation, routing, production registry mutation or acceptance decision.
Geometry uses the serialized accepted PCB, not a regenerated unrouted placement.
Requires the existing scripts/pcbgen/numerical-requirements.txt environment.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.netlist import TOKEN, many, one, parse, read_netlist
from scripts.pcbgen.uuid_tools import REF_RE, UUID_RE, top_level_spans, replace_spans
from scripts.schgen.project_boards import net_token

OUT = ROOT / 'design/partition/core-split/candidates'
BASE = '65cefd41fc39e064d38319115ad96016a1c6b71c'
PCB = 'boards/osc-core/osc-core.kicad_pcb'
RAILS = {'AGND', '+12V', '-12V', '+5V', '+12V_IN', '-12V_IN', '+5V_IN'}
OPTIONS = {
    'two': {
        'A': ['O1', 'O2', 'O3', 'O4', 'O5', 'OCTAVE_REF', 'F1', 'F2', 'F3', 'W1', 'W2', 'M4A', 'M4B', 'N1'],
        'B': ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'H1', 'H2', 'M5A', 'M5B'],
    },
    'three': {
        'A': ['O1', 'O2', 'O3', 'O4', 'O5', 'OCTAVE_REF', 'H1', 'H2'],
        'B': ['F1', 'F2', 'F3', 'W1', 'W2', 'M4A', 'M4B', 'M5A', 'M5B', 'N1'],
        'C': ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'A01', 'A02', 'A03', 'A04', 'A05', 'A06'],
    },
}
# Whole-module fixtures; these declared pads are checked against the actual netlist.
SAMPLES = {
    'two-A': ('O1', 'U1109', '4', '11', '/O1/TIMING_CAP', [('U1105', '11'), ('C1111', '1')], [('U1105', '12'), ('C1111', '2')]),
    'two-B': ('H1', 'U115', '12', '3', '/H1/HOLD_CAP', [('U115', '8'), ('C105', '1')], [('U115', '10'), ('C105', '2')]),
    'three-A': ('O1', 'U1109', '4', '11', '/O1/TIMING_CAP', [('U1105', '11'), ('C1111', '1')], [('U1105', '12'), ('C1111', '2')]),
    'three-B': ('F1', 'U2106', '11', '6', '/F1/BP_INT', [('U2106', '5'), ('C2112', '1')], [('C2112', '2')]),
    'three-C': ('E1', 'U4106', '13', '4', '/E1/ENV_STORAGE', [('U4141', '10'), ('C4113', '1')], [('C4113', '2')]),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value, *, compact=False):
    return (json.dumps(value, sort_keys=True, indent=None if compact else 2, separators=(',', ':') if compact else None, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads((ROOT / path).read_text())


def parsed(text):
    tokens = TOKEN.findall(text)
    result, end = parse(tokens)
    if end != len(tokens):
        raise ValueError('trailing S-expression data')
    return result


def unique(rows, key):
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f'duplicate {key}')
    return result


def geometry_runtime():
    import shapely
    if shapely.__version__ != '2.1.2':
        raise ValueError('use pinned shapely==2.1.2')
    return {'shapely': shapely.__version__, 'geos': shapely.geos_version_string}


def geometry_modules():
    from shapely import affinity
    from shapely.geometry import Polygon, LineString, Point, box
    from shapely.ops import polygonize, unary_union
    from shapely.strtree import STRtree
    return affinity, Polygon, LineString, Point, box, polygonize, unary_union, STRtree


def courtyard(node):
    """Polygonize the actual serialized courtyard edges, refusing unsupported curves."""
    _, Polygon, LineString, _, box, polygonize, union, _ = geometry_modules()
    lines, polygons = [], []
    for item in node:
        if not isinstance(item, list) or not item[0].startswith('fp_'):
            continue
        layers = many(item, 'layer')
        if not layers or layers[0][1] not in ('F.CrtYd', 'B.CrtYd'):
            continue
        if item[0] == 'fp_line':
            lines.append(LineString([list(map(float, one(item, tag)[1:3])) for tag in ('start', 'end')]))
        elif item[0] == 'fp_rect':
            x, y = map(float, one(item, 'start')[1:3]); a, b = map(float, one(item, 'end')[1:3])
            polygons.append(box(min(x, a), min(y, b), max(x, a), max(y, b)))
        elif item[0] == 'fp_poly':
            polygons.append(Polygon([list(map(float, p[1:3])) for p in many(one(item, 'pts'), 'xy')]))
        else:
            raise ValueError(f'unsupported courtyard primitive {item[0]}')
    polygons.extend(polygonize(lines))
    shape = union(polygons)
    if shape.is_empty or not shape.is_valid:
        raise ValueError('missing or invalid closed courtyard polygon')
    if lines and abs(union(lines).length - sum(p.length for p in polygonize(lines))) > 1e-5:
        raise ValueError('open or redundant courtyard linework')
    return shape


def native_geometry(block):
    """KiCad serialized footprint coordinates already encode its face reflection."""
    affinity, _, _, _, _, _, _, _ = geometry_modules()
    node = parsed(block)
    at = list(map(float, one(node, 'at')[1:]))
    angle = at[2] if len(at) > 2 else 0
    shape = affinity.translate(affinity.rotate(courtyard(node), -angle, origin=(0, 0)), at[0]-100, at[1]-50)
    return node, shape, {'x_mm': at[0]-100, 'y_mm': at[1]-50,
                         'kicad_orientation_deg': angle % 360, 'side': one(node, 'layer')[1]}


def polygon_data(shape):
    polys = [shape] if shape.geom_type == 'Polygon' else list(shape.geoms)
    return [[[round(x, 6), round(y, 6)] for x, y in p.exterior.coords] for p in polys]


class Inputs:
    def __init__(self):
        self.partition = read('design/partition/partition.json')
        self.io = read('design/reports/io-partition.json')
        self.floor = unique(read('design/partition/floorplan-candidate.json')['placements'], 'ref')
        self.parts = unique(self.io['physical_packages'], 'ref')
        assigned = unique(self.partition['assignment']['components'], 'ref')
        self.core = {r: self.parts[r] for r, a in assigned.items() if a['board'] == 'K'}
        self.components, self.pins = read_netlist(ROOT / 'schematic/boards/osc-core.net')
        self.components = {c.ref: c for c in self.components}
        self.names = read('design/reports/board-net-tokens.json')
        self.net_refs = defaultdict(set)
        for (ref, _), net in self.pins.items():
            self.net_refs[net].add(ref)
        self.text = (ROOT / PCB).read_text()
        self.blocks = [(a, b, self.text[a:b].split(None, 1)[0][1:]) for a, b in top_level_spans(self.text)]
        self.footprints, self.geometry, self.poses, self.pad_identity = {}, {}, {}, {}
        self.copper = []
        self.mechanical_refs = []
        for a, b, kind in self.blocks:
            block = self.text[a:b]
            if kind == 'footprint':
                match = REF_RE.search(block)
                if not match:
                    raise ValueError('footprint without Ref')
                ref = match[1]
                if ref not in self.components:
                    # Non-electrical mounting/service-hole footprint, retained on every candidate.
                    if ref.startswith(('H', 'MH')):
                        self.mechanical_refs.append(ref)
                        continue
                    raise ValueError('unexpected PCB-only footprint ' + ref)
                if ref in self.footprints:
                    raise ValueError('duplicate PCB footprint ' + ref)
                node, shape, pose = native_geometry(block)
                self.footprints[ref] = (a, b)
                self.geometry[ref], self.poses[ref] = shape, pose
                pads = []
                for pad in many(node, 'pad'):
                    netrows = many(pad, 'net')
                    net = netrows[0][-1] if netrows else None
                    want = self.pins.get((ref, pad[1]))
                    if want and net != want:
                        raise ValueError(f'PCB/netlist pin mismatch {ref}.{pad[1]}: {net} != {want}')
                    pads.append({'pad': pad[1], 'net_token': net, 'uuid': one(pad, 'uuid')[1],
                                 'local_at_mm': list(map(float, one(pad, 'at')[1:3]))})
                self.pad_identity[ref] = pads
            elif kind in ('segment', 'via', 'zone'):
                uid = UUID_RE.search(block)
                net = re.search(r'\(net(?:\s+\d+)?\s+"([^"]*)"\)', block)
                if not uid:
                    raise ValueError('copper without UUID')
                self.copper.append({'uuid': uid[1], 'kind': 'rule_area' if kind == 'zone' and '(keepout' in block else kind, 'net_token': net[1] if net else '',
                                    'sha256': digest(block.encode()), 'source_span': [a, b]})
        if self.footprints.keys() != self.components.keys():
            raise ValueError('PCB/netlist component roster mismatch')
        if len(self.core) != 3385 or len(self.components) != 3594:
            raise ValueError('core inventory changed; review counts and candidate policy')
        self.board = next(b for b in self.partition['boards'] if b['board_key'] == 'K')
        self.validate_poses()

    def validate_poses(self):
        for ref in self.core:
            expected = self.floor[ref]
            actual = self.poses[ref]
            for k in ('x_mm', 'y_mm', 'kicad_orientation_deg'):
                if abs(expected[k]-actual[k]) > 1e-5:
                    raise ValueError(f'accepted/source pose drift {ref} {k}; coordinator must reconcile')
            if actual['side'] != expected['side']:
                raise ValueError('accepted/source face drift ' + ref)
        for c in self.partition['connectors']:
            if c['board'] != 'K':
                continue
            for pin, net in c['pin_map'].items():
                actual = self.pins.get((c['pcb_reference'], pin))
                valid = (actual is None or actual.startswith('unconnected-')) if net in (None, 'NC') else actual == net_token(net)
                if not valid:
                    raise ValueError(f'harness pin mismatch {c["id"]}.{pin}')

    def source_hashes(self):
        paths = {PCB, 'design/partition/partition.json', 'design/reports/io-partition.json',
                 'design/partition/floorplan-candidate.json', 'design/grid/placements.lock.json',
                 'design/partition/partition-input.json', 'design/reports/board-net-tokens.json',
                 'schematic/boards/osc-core.net', 'design/boards/osc-core.json',
                 'scripts/kicad/pin.env', 'scripts/pcbgen/numerical-requirements.txt', 'scripts/schgen/project_boards.py'}
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'boards/osc-core').rglob('*') if p.is_file() and 'reports' not in p.parts)
        paths.update(str(p.relative_to(ROOT)) for d in ('symbols', 'footprints/kicad/zudo-osc-hole-field.pretty', 'scripts/schgen/fixtures') for p in (ROOT/d).glob('*') if p.is_file())
        # Issue 249's annotation-only trimmer helper and regression are not
        # imported by this partition generator or packaged into a fixture.
        # Keep the accepted #245 input epoch stable while binding every actual
        # board/context/router input to the original source commit below.
        unrelated_labels = {'scripts/pcbgen/trimmer_labels.py',
                            'scripts/pcbgen/test_trimmer_labels.py',
                            'scripts/pcbgen/trimmer_labels_native_regression.py'}
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/pcbgen').rglob('*.py')
                     if str(p.relative_to(ROOT)) not in unrelated_labels)
        paths.update(f'scripts/pcbgen/{n}.py' for n in ('grid_dump', 'grid_router', 'grid_apply', 'route_jack_grid', 'uuid_tools', 'complete_native_warnings', 'netlist', 'route', 'copper_identity', 'audit_added_mask', 'audit_hole_pairs', 'audit_zone_silk_scope', 'native_companion_binding'))
        # Bind every declared input to the immutable source commit; a dirty or newer
        # source must not silently inherit the old epoch label.
        ordered = sorted(paths)
        tree = subprocess.check_output(['git', 'ls-tree', '-r', BASE, '--', *ordered], cwd=ROOT, text=True)
        expected = {line.split('\t', 1)[1]: line.split()[2] for line in tree.splitlines()}
        actual = subprocess.check_output(['git', 'hash-object', '--stdin-paths'], cwd=ROOT,
                                         input='\n'.join(ordered)+'\n', text=True).splitlines()
        for path, blob in zip(ordered, actual):
            if expected.get(path) != blob:
                raise ValueError('source differs from pinned main; coordinate new epoch: '+path)
        return {p: digest((ROOT/p).read_bytes()) for p in ordered}


def assignments(inputs, option):
    blocks = {}
    for board, modules in OPTIONS[option].items():
        for module in modules:
            if module in blocks:
                raise ValueError('duplicate module ' + module)
            blocks[module] = board
    blocks['POWER'] = 'A'  # Accounting-only provisional allocation, explicitly subject to #247.
    if set(blocks) != {p['instance'] for p in inputs.core.values()}:
        raise ValueError('missing/unknown module')
    owners = {r: blocks[p['instance']] for r, p in inputs.core.items()}
    for h in inputs.partition['connectors']:
        if h['board'] != 'K':
            continue
        touched = {owners[r] for n in h['pin_map'].values() if n not in RAILS | {'NC', None}
                   for r in inputs.net_refs[net_token(n)] if r in owners}
        if len(touched) != 1:
            raise ValueError(f'mixed or unassigned harness {h["id"]}: {sorted(touched)}')
        owners[h['pcb_reference']] = touched.pop()
    for t in inputs.partition['load_side_terminals']:
        if t['board'] == 'K':
            owners[t['reference']] = 'A'
    if owners.keys() != inputs.components.keys():
        raise ValueError('native ownership roster mismatch')
    for group in inputs.io['islands'] + inputs.io['local_raw_sensitive_nets']:
        refs = set(group['refs']) & inputs.core.keys()
        if refs and len({owners[r] for r in refs}) != 1:
            raise ValueError('sensitive island split ' + str(group))
    for r, part in inputs.core.items():
        parent = part['decouples_ref']
        if parent and (parent not in owners or owners[r] != owners[parent]):
            raise ValueError('bypass split ' + r)
    for net, refs in inputs.net_refs.items():
        if net not in RAILS and len({owners[r] for r in refs}) != 1:
            raise ValueError('unplanned signal bridge ' + inputs.names.get(net, net))
    return owners


def collision_pairs(refs, shapes, gap):
    *_, STRtree = geometry_modules()
    items = [shapes[r] for r in refs]
    tree = STRtree(items)
    rows = []
    for i, a in enumerate(items):
        for j in tree.query(a.buffer(gap)):
            j = int(j)
            if j <= i:
                continue
            d = a.distance(items[j])
            area = a.intersection(items[j]).area
            if area > 1e-7 or d < gap-1e-7:
                rows.append({'refs': [refs[i], refs[j]], 'distance_mm': round(d, 6), 'overlap_mm2': round(area, 6)})
    return sorted(rows, key=lambda row: row['refs'])


def measure(inputs, refs, header_ids):
    _, Polygon, _, Point, box, _, union, _ = geometry_modules()
    outline = Polygon(inputs.board['outline'])
    usable_outline = outline.buffer(-0.30, join_style=2)
    results = {}
    for face in ('F.Cu', 'B.Cu'):
        face_refs = sorted(r for r in refs if inputs.poses[r]['side'] == face)
        shapes = [inputs.geometry[r] for r in face_refs]
        occupied = union(shapes)
        # Exact source corridors/reserves; holes conservative support-collar polygons.
        reserves = [(r['id'], box(*r['rect'])) for r in inputs.board['reserves'] if face in r['sides']]
        reserves += [(f'support-{i}', Point(x, y).buffer(1.6, quad_segs=32)) for i, (x, y) in enumerate(inputs.board['supports_mm'])]
        # All 191 legacy service holes survive the identity-envelope policy.
        for a in inputs.partition['K_service_apertures']:
            reserves += [(a['header_id']+'-hole', Point(*a['center_mm']).buffer(a['diameter_mm']/2, quad_segs=32)),
                             (a['header_id']+'-hook', box(*a['hook_sweep_xy_mm']))]
        excluded = union([g for _, g in reserves])
        usable = usable_outline.difference(excluded)
        # New per-core feed parts remain unidentified: retain the entire existing source
        # protection, bulk and 18-land envelope on every board instead of claiming zero area.
        tiles = []
        for x in range(4, 314, 20):
            for y in range(8, 292, 20):
                tile = box(x, y, min(x+20, 314), min(y+20, 292))
                available = usable.intersection(tile).area
                area = occupied.intersection(tile).area
                if area > 0:
                    tiles.append({'rect_mm': [x, y, min(x+20, 314), min(y+20, 292)],
                                  'occupied_mm2': round(area, 6), 'usable_mm2': round(available, 6),
                                  'occupancy_fraction': round(area/available, 6) if available > 1e-9 else None})
        overlaps = collision_pairs(face_refs, inputs.geometry, .35)
        conflicts = [{'reservation': name, 'overlap_mm2': round(occupied.intersection(g).area, 6)}
                     for name, g in reserves if occupied.intersection(g).area > 1e-7]
        results[face] = {'courtyard_sum_mm2': round(sum(g.area for g in shapes), 6),
                         'courtyard_union_mm2': round(occupied.area, 6),
                         'courtyard_overlap_mm2': round(sum(g.area for g in shapes)-occupied.area, 6),
                         'usable_after_reservations_mm2': round(usable.area, 6),
                         'outside_edge_allocation_mm2': round(occupied.difference(usable_outline).area, 6),
                         'reservation_overlap_mm2': round(occupied.intersection(excluded).area, 6),
                         'courtyard_gap_violations': overlaps, 'reservation_conflicts': conflicts,
                         'tiles_20mm': tiles, 'reservation_polygons_mm': [{'id': n, 'polygons': polygon_data(g)} for n, g in reserves]}
    return {'outline_area_mm2': round(outline.area, 6), 'faces': results,
            'courtyard_gap_requirement_mm': .35, 'board_edge_allocation_mm': .30,
            'method': 'GEOS polygon union/intersection, exact serialized courtyard vertices; circular reservation polygons use 128 edges. Counts and areas are separate. No native or installed-fit acceptance.',
            'limits': ['Same-face courtyard gap screen only; opposing-face through-hole body/pad and installed solids need native/mechanical checks.',
                       '1 nm serialized gap shortfalls remain listed; the 0.35 mm requirement is not reduced.',
                       'Hook sweeps conservatively projected onto both faces; intersection with their own connector/body is reported, not suppressed.',
                       'Existing load-land reserves overlap their own installed terminals intentionally; these conflicts are reported.',
                       'New supply identities and conductor routing are pending #247; existing full power/protection reservations retained on every core.']}


def candidate(inputs, option):
    owners = assignments(inputs, option)
    boards = {}
    for short in OPTIONS[option]:
        key = option+'-'+short
        refs = sorted(r for r, owner in owners.items() if owner == short)
        parts = sorted(set(refs) & inputs.core.keys())
        connectors = [copy.deepcopy(c) for c in inputs.partition['connectors'] if c['board'] == 'K' and c['pcb_reference'] in refs]
        islands = [g for g in inputs.io['islands'] if set(g['refs']) & set(parts)]
        sensitive = [g for g in inputs.io['local_raw_sensitive_nets'] if set(g['refs']) & set(parts)]
        boards[key] = {'id': key, 'provisional_board_key': 'K'+short, 'status': 'SOURCE COMPARISON ONLY / NOT SELECTED',
                       'outline_mm': inputs.board['outline'], 'layers': 6, 'thickness_mm': 1.6,
                       'copper_oz': 2, 'face_z_mm': None, 'supports_mm': inputs.board['supports_mm'],
                       'placement_policy': 'Preserve accepted absolute XY, face, rotation and pad UUIDs. Separate full-envelope stack boards; no equal-area packing or accepted stack height implied.',
                       'transform_from_accepted_K': {'translation_mm': [0, 0], 'rotation_deg': 0, 'flip': False},
                       'counts': {'source_parts': len(parts), 'fitted': sum(not inputs.core[r]['dnp'] for r in parts),
                                  'dnp': sum(inputs.core[r]['dnp'] for r in parts),
                                  'trimmers': sum(inputs.core[r]['footprint'].endswith(':Potentiometer_Bourns_TC33X_Vertical') for r in parts),
                                  'headers': len(connectors), 'load_lands': sum(r.startswith('TP990') for r in refs),
                                  'electrical_footprints': len(refs), 'mechanical_footprints': len(inputs.mechanical_refs), 'total_native_footprints': len(refs)+len(inputs.mechanical_refs)},
                       'modules': sorted({inputs.core[r]['instance'] for r in parts}), 'refs': refs,
                       'source_part_courtyard_sum_mm2': round(sum(inputs.geometry[r].area for r in parts), 6),
                       'mechanical_refs': sorted(inputs.mechanical_refs),
                       'source_parts': [{'ref': r, 'module': inputs.core[r]['instance'], 'dnp': inputs.core[r]['dnp'],
                                         'footprint': inputs.core[r]['footprint'], 'mpn': inputs.core[r]['mpn'],
                                         'decouples_ref': inputs.core[r]['decouples_ref']} for r in parts],
                       'placements': [{'ref': r, **inputs.poses[r], 'courtyard_polygons_mm': polygon_data(inputs.geometry[r]),
                                       'pad_identity': inputs.pad_identity[r]} for r in refs],
                       'core_endpoints': connectors, 'islands': islands, 'sensitive_nets': sensitive,
                       'power_accounting': {'existing_POWER_refs': [r for r in parts if inputs.core[r]['instance'] == 'POWER'],
                                            'status': 'POWER and existing 18 load lands provisionally assigned to A only for complete accounting; #247 must select feeds/parts/AGND. Existing power/protection envelope retained on every board.',
                                            'new_feed_interfaces': 'UNSELECTED; must use new identities; no legacy header repacking'},
                       'measurement': measure(inputs, refs, {c['id'] for c in connectors})}
    net_owners = {n: sorted({owners[r] for r in rs}) for n, rs in inputs.net_refs.items()}
    return {'schema': 'core-split-candidate-1', 'option': option, 'selected': False,
            'boards': boards, 'ownership': owners, 'net_owners': net_owners,
            'checks': {'source_parts': len(inputs.core), 'all_native_refs': len(owners),
                       'whole_harnesses': 191, 'mixed_signal_harnesses': 0, 'islands': 66,
                       'sensitive_nets': 493, 'bypass_pairs': 617,
                       'native_routing': 'NOT RUN', 'installed_fit': 'NOT RUN'}}


def copper_contract(inputs, candidates):
    by_net = defaultdict(list)
    pads_by_net = defaultdict(list)
    for (ref, pad), net in sorted(inputs.pins.items()):
        pads_by_net[net].append({'ref': ref, 'pad': pad})
    for row in inputs.copper:
        by_net[row['net_token']].append(row)
    result = {}
    for option, candidate_data in candidates.items():
        nets = []
        for net, rows in sorted(by_net.items()):
            owners = candidate_data['net_owners'].get(net, [])
            reusable = net not in RAILS and len(owners) == 1 and all(r['kind'] not in ('zone', 'rule_area') for r in rows)
            rule_area = all(r['kind'] == 'rule_area' for r in rows)
            nets.append({'net_token': net, 'source_net': inputs.names.get(net, net), 'candidate_owners': owners,
                         'disposition': 'RETAIN_RULE_AREA' if rule_area else 'RETAIN_IDENTITY_RECHECK_NATIVE' if reusable else 'INVALIDATE_AND_REPLAY_COUPLED_COPPER',
                         'reason': 'keepout definitions retained byte-for-byte' if rule_area else 'all endpoint Refs and poses retained on one board; native groups still require recheck' if reusable else 'global rail/return, zone refill, or orphan copper needs explicit new topology/native connectivity; never duplicate across cores',
                         'count': len(rows), 'kinds': dict(sorted(Counter(r['kind'] for r in rows).items())),
                         'identity_sha256': digest(json_bytes(sorted((r['uuid'], r['sha256']) for r in rows))),
                         'pads': pads_by_net[net]})
        result[option] = {'nets': nets, 'counts': dict(Counter({d: sum(n['count'] for n in nets if n['disposition'] == d) for d in ('RETAIN_RULE_AREA', 'RETAIN_IDENTITY_RECHECK_NATIVE', 'INVALIDATE_AND_REPLAY_COUPLED_COPPER')}))}
    return {'schema': 'core-split-copper-1', 'source_pcb_sha256': digest(inputs.text.encode()),
            'index': 'copper-index.jsonl.gz', 'source_span_units': 'Unicode code points in UTF-8-decoded source text, not byte offsets',
            'policy': 'Exact source object UUID+hash index; rigid identity transform only. Retain whole eligible local nets; rails/AGND/zones are coupled replay obligations. Eligibility is not adopted copper or proof of connected original groups.',
            'options': result}


def pilot_contract(inputs, boards):
    pilots = {}
    for key, (module, amp, plus, minus, signal, signal_pads, return_pads) in SAMPLES.items():
        spec = boards[key]
        # Whole module plus every intersecting preserved endpoint, including unused pins
        # and explicit foreign-module boundary obligations.
        refs = {r for r in spec['refs'] if r in inputs.core and inputs.core[r]['instance'] == module}
        for c in spec['core_endpoints']:
            if any(inputs.net_refs[net_token(n)] & refs for n in c['pin_map'].values() if n not in RAILS | {'NC', None}):
                refs.add(c['pcb_reference'])
        sample_refs = sorted(refs)
        refs = set(spec['refs'])
        targets = {'positive_supply_escape': ('+12V', [(amp, plus)]),
                   'negative_supply_escape': ('-12V', [(amp, minus)]),
                   'sensitive_signal': (signal, signal_pads), 'coupled_return': ('AGND', return_pads)}
        target_rows = {}
        for kind, (net, pairs) in targets.items():
            token = net_token(net)
            for pair in pairs:
                if pair[0] not in refs or inputs.pins.get(tuple(pair)) != token:
                    raise ValueError(f'pilot pad identity mismatch {key} {pair} {net}')
            target_rows[kind] = {'source_net': net, 'net_token': token,
                                 'pads': [{'ref': r, 'pad': p, 'uuid': next(x['uuid'] for x in inputs.pad_identity[r] if x['pad'] == p)} for r, p in pairs]}
        boundary = []
        for net, members in sorted(inputs.net_refs.items()):
            if members & refs and members-refs:
                boundary.append({'net_token': net, 'source_net': inputs.names.get(net, net),
                                 'inside_refs': sorted(members & refs), 'outside_refs': sorted(members-refs),
                                 'status': 'CUT_BOUNDARY_OBLIGATION; not an intentional no-connect'})
        pilots[key] = {'schema': 'core-split-pilot-1', 'candidate': key, 'whole_module': module,
                       'refs': sorted(refs), 'sample_refs': sample_refs, 'fixture_scope': 'Full candidate context with bounded sample routing targets; no registry dependency', 'targets': target_rows, 'boundary_obligations': boundary,
                       'transform_to_candidate': {'translation_mm': [0, 0], 'rotation_deg': 0, 'flip': False},
                       'pcb_origin_offset_mm': [100, 50], 'native_status': 'NOT RUN',
                       'hotspot_status': 'SOURCE SENSITIVE SIGNAL/RETURN SAMPLE; native open-edge severity must be measured before comparison',
                       'budget': {'wall_seconds_per_command': 300, 'worker_memory_gib': 6, 'global_native_workers': 2,
                                  'global_memory_gib': 12, 'required_free_gib': 2, 'max_expansions': 50000,
                                  'window_mm': 6, 'max_refills': 6, 'stable_refills': 3, 'rerun_policy': 'No automatic retry; diagnose two comparable non-improving runs; at most three unchanged attempts'},
                       'limits': ['Complete candidate context retains sensitive and bypass closure, DNP, all assigned endpoint pins and candidate-specific neighboring obstacles. Routing selection is bounded to the sample.',
                                  'Other-core symbols/footprints are removed from disposable context only. Cross-boundary endpoints are retained in this manifest.',
                                  'Only complete fixture-local nonrail nets retain old tracks; rail/AGND tracks are replay obligations and inherited plane definitions are refilled as a provisional fixture assumption. Full candidate copper inventory is retained separately.',
                                  'Native sample success cannot establish stack fit, rail distribution or whole-board routability.']}
    return pilots


def svg_compare(boards):
    colors = ['#167a8a', '#985b28', '#5967b8']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="1780" viewBox="0 0 1320 1780">',
             '<rect width="1320" height="1780" fill="#f6f4ef"/>',
             '<style>text{font:14px sans-serif;fill:#162d38}.title{font:bold 24px sans-serif}.small{font:11px sans-serif}</style>',
             '<text x="24" y="36" class="title">Core split — preserved-pose comparison (unvalidated drafts)</text>',
             '<text x="24" y="60">Same 310 × 284 mm notched envelope per core. Both faces shown; no stack depth or topology selected.</text>']
    for row, (key, data) in enumerate(boards.items()):
        oy = 105 + row*330
        count = data['counts']
        parts.append(f'<text x="24" y="{oy}" class="title">{key}: {count["source_parts"]} parts · {count["headers"]} headers</text>')
        for col, face in enumerate(('F.Cu', 'B.Cu')):
            ox = 375 + col*445
            parts.append(f'<text x="{ox+100}" y="{oy-10}">{face}</text><g transform="translate({ox},{oy}) scale(.95)">')
            outline = ' '.join(f'{x},{y}' for x, y in data['outline_mm'])
            parts.append(f'<polygon points="{outline}" fill="white" stroke="#526575"/>')
            for reserve in data['measurement']['faces'][face]['reservation_polygons_mm']:
                for poly in reserve['polygons']:
                    points = ' '.join(f'{x:.3f},{y:.3f}' for x, y in poly)
                    parts.append(f'<polygon points="{points}" fill="#edb1a7" fill-opacity=".4"/>')
            for p in data['placements']:
                if p['side'] != face:
                    continue
                for poly in p['courtyard_polygons_mm']:
                    points = ' '.join(f'{x:.3f},{y:.3f}' for x, y in poly)
                    parts.append(f'<polygon points="{points}" fill="{colors[row%3]}" fill-opacity=".6"><title>{p["ref"]}</title></polygon>')
            parts.append('</g>')
        for i, face in enumerate(('F.Cu', 'B.Cu')):
            m = data['measurement']['faces'][face]
            parts.append(f'<text x="24" y="{oy+30+i*22}">{face}: union {m["courtyard_union_mm2"]:.1f} / usable {m["usable_after_reservations_mm2"]:.1f} mm²</text>')
        parts.append(f'<text x="24" y="{oy+90}" class="small">Red: projected reservations; coloured: actual PCB courtyards.</text>')
    parts.append('</svg>')
    return '\n'.join(parts)+'\n'


def build_outputs():
    geometry_runtime()
    inputs = Inputs()
    candidates = {option: candidate(inputs, option) for option in OPTIONS}
    boards = {k: b for c in candidates.values() for k, b in c['boards'].items()}
    pilots = pilot_contract(inputs, boards)
    contracts = {
        'schema': 'core-split-interface-1', 'source_main_sha': BASE,
        'fixed_panel': read('design/grid/placements.lock.json'),
        'non_core_placements': [p for r, p in sorted(inputs.floor.items()) if r not in inputs.core],
        'harnesses': inputs.partition['harnesses'], 'endpoints': inputs.partition['connectors'],
        'source_load_lands': inputs.partition['load_side_terminals'],
        'rule': 'Immutable legacy harness IDs, both endpoint Refs, every signal/AGND/rail/NC pin and non-core pose. Candidate changes only core owner; new feeds need new identities.'}
    outputs = {'interface-contract.json': json_bytes(contracts, compact=True),
               'copper-contract.json': json_bytes(copper_contract(inputs, candidates), compact=True),
               'comparison.svg': svg_compare(boards).encode()}
    raw = b''.join((json.dumps(r, sort_keys=True, separators=(',', ':'))+'\n').encode() for r in inputs.copper)
    outputs['copper-index.jsonl.gz'] = gzip.compress(raw, mtime=0)
    for name, c in candidates.items():
        outputs[f'{name}.json'] = json_bytes(c, compact=True)
    for key, pilot in pilots.items():
        outputs[f'pilots/{key}.json'] = json_bytes(pilot)
    outputs['pilots/commands.json'] = json_bytes(command_manifest(pilots))
    outputs['input-lock.json'] = json_bytes({'schema': 'core-split-input-lock-1', 'source_main_sha': BASE,
                                            'input_sha256': inputs.source_hashes(),
                                            'tool_sha256': digest(Path(__file__).read_bytes()),
                                            'geometry_runtime': geometry_runtime(),
                                            'generated_sha256': {p: digest(v) for p, v in sorted(outputs.items())},
                                            'native_status': 'NOT RUN / requires assigned global slot',
                                            'initial_regeneration': 'NOT RUN / native global slot not assigned',
                                            'production_adoption': False})
    return outputs


def command_manifest(pilots):
    return {'schema': 'core-split-command-manifest-1', 'required_oracle': 'KiCad 10.0.6 via scripts/kicad/run.sh and scripts/kicad/pin.env digest',
            'authorization': 'Do not execute until parent grants explicit global native slot and bounded command. Materialization itself is pure source processing.',
            'working_directory': 'repository root; replace {python} with pinned numerical environment interpreter and {output} with unique private repository-relative directory',
            'native_acceptance': 'NOT RUN. Use complete warning identities (uncapped independent audit), original connected pad groups, settled/fresh-copy agreement and source/candidate hashes. This manifest does not adopt copper.',
            'pilots': {key: {'materialize': ['{python}', 'scripts/partition/core_split_candidates.py', 'materialize', '--pilot', key, '--output', '{output}'],
                             'entrypoint': '{output}/commands.json', 'budget': value['budget']} for key, value in pilots.items()}}


def verify_lock():
    lock = read('design/partition/core-split/candidates/input-lock.json')
    if lock['geometry_runtime'] != geometry_runtime():
        raise ValueError('geometry runtime differs from candidate lock')
    for path, sha in lock['input_sha256'].items():
        if digest((ROOT/path).read_bytes()) != sha:
            raise ValueError('stale candidate input ' + path)
    if digest(Path(__file__).read_bytes()) != lock['tool_sha256']:
        raise ValueError('candidate generator changed; regenerate and review')
    for path, sha in lock['generated_sha256'].items():
        if digest((OUT/path).read_bytes()) != sha:
            raise ValueError('candidate output drift ' + path)
    return lock


def filtered_schematic(text, refs):
    """Retain native sheet/symbol UUIDs and all labels; remove whole excluded symbols."""
    edits = []
    for a, b in top_level_spans(text):
        block = text[a:b]
        if not block.startswith('(symbol '):
            continue
        match = REF_RE.search(block)
        if not match:
            raise ValueError('schematic symbol without reference')
        if match[1] not in refs and not match[1].startswith('#'):
            edits.append((a, b, ''))
    return replace_spans(text, edits)


def materialize(pilot_key, output):
    """Write complete fixture context without invoking a native tool or touching source."""
    verify_lock()
    if pilot_key not in SAMPLES:
        raise ValueError('unknown pilot')
    output = output.resolve()
    if output.exists():
        raise ValueError('fixture output must not exist; choose a new private path')
    # Prevent accidental source overwrite. External temp output is useful for source tests;
    # run.sh native commands require a path under the repository mount.
    if output.is_relative_to(ROOT) and not output.is_relative_to(OUT/'pilots/generated'):
        raise ValueError('in-repository fixture output must be under candidates/pilots/generated')
    pilot = json.loads((OUT/f'pilots/{pilot_key}.json').read_text())
    refs = set(pilot['refs'])
    inputs = Inputs()
    eligible = {n for n, rs in inputs.net_refs.items() if n not in RAILS and rs <= refs}
    output.mkdir(parents=True)
    for phase in ('before', 'after', 'fresh'):
        dest = output/phase
        dest.mkdir()
        source = ROOT/'boards/osc-core'
        for p in source.rglob('*'):
            if not p.is_file() or 'reports' in p.parts or p.suffix == '.kicad_pcb':
                continue
            relative = p.relative_to(source)
            target = dest/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix == '.kicad_sch':
                target.write_text(filtered_schematic(p.read_text(), refs))
            elif p.name in ('fp-lib-table', 'sym-lib-table'):
                target.write_text(p.read_text().replace('${KIPRJMOD}/../../', '${KIPRJMOD}/../context/'))
            else:
                shutil.copyfile(p, target)
    for directory in ('symbols', 'footprints/kicad/zudo-osc-hole-field.pretty', 'scripts/schgen/fixtures'):
        shutil.copytree(ROOT/directory, output/'context'/directory)
    edits = []
    copper_by_span = {tuple(r['source_span']): r for r in inputs.copper}
    kept = []
    for a, b, kind in inputs.blocks:
        block = inputs.text[a:b]
        if kind == 'footprint':
            match = REF_RE.search(block)
            if match and match[1] in inputs.components and match[1] not in refs:
                edits.append((a, b, ''))
        elif kind in ('segment', 'via', 'zone'):
            row = copper_by_span[a, b]
            # Retain rule areas unchanged; invalidate filled/global copper explicitly.
            keepout = kind == 'zone' and '(keepout' in block
            if kind == 'zone' and not keepout:
                zone_edits = [(x, y, '') for x, y in top_level_spans(block) if block[x:y].startswith(('(filled_polygon', '(fill_segments'))]
                edits.append((a, b, replace_spans(block, zone_edits)))
            elif keepout or (kind != 'zone' and row['net_token'] in eligible):
                kept.append(row)
            else:
                edits.append((a, b, ''))
    fixture_text = replace_spans(inputs.text, edits)
    (output/'before/osc-core.kicad_pcb').write_text(fixture_text)
    (output/'mapping.json').write_bytes(json_bytes({'pilot': pilot, 'source_pcb_sha256': digest(inputs.text.encode()),
                                                 'fixture_pcb_sha256': digest(fixture_text.encode()), 'retained_copper': kept,
                                                 'rules': 'Unchanged production project/rules with full source net class names; all library tables resolve packaged local context.',
                                                 'native_status': 'NOT RUN'}))
    base = output.relative_to(ROOT).as_posix() if output.is_relative_to(ROOT) else str(output)
    nets = ','.join(dict.fromkeys(t['net_token'] for t in pilot['targets'].values()))
    commands = [
        ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'settle', '--board', f'{base}/before/osc-core.kicad_pcb'],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'focus', '--output', base],
        ['{python}', 'scripts/pcbgen/grid_router.py', f'{base}/focused-dump.json', f'{base}/proposal.json', '--board-id', f'fixture-245-{pilot_key}', '--tag', 'pilot-1', '--nets', nets, '--max-expansions', '50000', '--window-mm', '6', '--rail-width', '0.5', '--planes', '+12V:In4.Cu,-12V:In3.Cu,AGND:In1.Cu', '--fill-guards', '+12V:In4.Cu,-12V:In3.Cu,AGND:In1.Cu'],
        ['bash', 'scripts/kicad/run.sh', 'python3', 'scripts/pcbgen/grid_apply.py', f'{base}/before/osc-core.kicad_pcb', f'{base}/proposal.json', '--output', f'{base}/after/osc-core.kicad_pcb'],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'settle', '--board', f'{base}/after/osc-core.kicad_pcb'],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'fresh-copy', '--output', base],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'settle', '--board', f'{base}/fresh/osc-core.kicad_pcb'],
        ['{python}', 'scripts/partition/core_split_candidates.py', 'audit-pilot', '--output', base],
    ]
    (output/'commands.json').write_bytes(json_bytes({'commands': commands, 'budget': pilot['budget'],
                                                  'gate': 'Parent slot approval required; each command bounded by 300 seconds and 6 GiB using existing guards. Verify version exactly 10.0.6. Stop on failure, do not retry automatically.',
                                                  'next': 'Execute commands sequentially under parent admission and existing resource guards; audit-pilot includes uncapped warnings and fresh/preservation gates. A timeout leaves an incomplete comparison. No production adoption.',
                                                  'status': 'SOURCE INPUTS EMITTED; NATIVE NOT RUN'}))
    files = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'sha256.json').write_bytes(json_bytes(files))
    return {'output': str(output), 'refs': len(refs), 'files': len(files), 'native': 'NOT RUN'}


def settle(board):
    # Deliberately separate command from pure source generation; only the decision
    # owner invokes this after global admission, bounded externally by existing guards.
    from scripts.pcbgen.route_jack_grid import check
    if not board.resolve().is_relative_to(OUT/'pilots/generated'):
        raise ValueError('settle only permits private candidate pilot outputs')
    version = subprocess.check_output(['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'], cwd=ROOT, text=True).strip()
    if not re.match(r'^10\.0\.6(?:$|[-+\s])', version):
        raise ValueError('required pinned KiCad 10.0.6, got '+version)
    drc, dump = check(board)
    validate_native_report(drc, board)
    board.with_name('settled-receipt.json').write_bytes(json_bytes({'board_sha256': digest(board.read_bytes()), 'drc_sha256': digest(board.with_name('drc.json').read_bytes()), 'dump_sha256': digest(board.with_name('dump.json').read_bytes()), 'status': 'SETTLED; NOT COMPLETE ACCEPTANCE'}))
    errors = [v for v in drc.get('violations', []) if v.get('severity') == 'error']
    if errors or drc.get('schematic_parity', []):
        raise ValueError('native errors/parity; retain outputs for diagnosis')
    print(json.dumps({'status': 'SETTLED ONLY; complete independent warnings/preservation not yet accepted', 'open_edges': dump['open_edges']}))



def validate_native_report(drc, board):
    from scripts.pcbgen.route import validate_drc_collections
    validate_drc_collections(drc)
    if drc.get('kicad_version') != '10.0.6' or drc.get('source') != board.name:
        raise ValueError('wrong native version or source')
    if set(drc.get('included_severities', [])) != {'error', 'warning', 'exclusion'}:
        raise ValueError('incomplete native severity scope')


def private_output(output):
    output = output.resolve()
    if not output.is_relative_to(OUT/'pilots/generated') or not (output/'mapping.json').is_file():
        raise ValueError('expected an existing private candidate fixture')
    return output


def settled_data(output, phase):
    folder = output/phase
    board = folder/'osc-core.kicad_pcb'
    receipt = json.loads((folder/'settled-receipt.json').read_text())
    for filename, key in [('osc-core.kicad_pcb', 'board_sha256'), ('drc.json', 'drc_sha256'), ('dump.json', 'dump_sha256')]:
        if digest((folder/filename).read_bytes()) != receipt[key]:
            raise ValueError('stale settled evidence '+str(folder/filename))
    drc = json.loads((folder/'drc.json').read_text())
    dump = json.loads((folder/'dump.json').read_text())
    validate_native_report(drc, board)
    if dump['board_sha256'] != receipt['board_sha256']:
        raise ValueError('native dump board hash mismatch')
    return board, drc, dump


def focused_dump(dump, targets):
    """Select at most one native group pair per target net; keep ALL obstacles.

    This derivative is a proposal selection, never a replacement native report.
    Closed sensitive targets stay NOT EXERCISED rather than requesting fake cuts.
    """
    chosen, observations = {}, {}
    pad_positions = {p['uuid']: p['xy'] for p in dump['pads']}
    for kind, target in targets.items():
        net = target['net_token']
        ids = {p['uuid'] for p in target['pads']}
        actual = {p['uuid'] for p in dump['pads'] if p['net'] == net}
        if not ids <= actual:
            raise ValueError('native target pad identity mismatch '+kind)
        groups = dump['islands'].get(net, [])
        touched = [i for i, group in enumerate(groups) if set(group) & ids]
        status = 'NOT EXERCISED: sample pads already connected'
        selected = []
        if touched and (len(ids) == 1 or len(touched) > 1):
            a = touched[0]
            if len(touched) > 1:
                b = touched[1]
            else:
                origin = [pad_positions[x] for x in groups[a] if x in pad_positions]
                options = [(min(math.dist(p, pad_positions[x]) for p in origin for x in group if x in pad_positions), i)
                           for i, group in enumerate(groups) if i != a and any(x in pad_positions for x in group)] if origin else []
                b = min(options)[1] if options else None
            if b is not None:
                selected = [groups[a], groups[b]]
                chosen[net] = selected
                status = 'OPEN SAMPLE: at most two native groups selected; plane fanout attempts or signal-pair proposal pending'
        observations[kind] = {'status': status, 'native_net_open_edges': max(0, len(groups)-1),
                              'selected_groups': selected, 'target_pad_uuids': sorted(ids)}
    result = copy.deepcopy(dump)
    # grid_router's plane mode creates per-pad groups for a missing plane net.
    # Explicit empty groups suppress that fallback for closed/unselected planes.
    for net in ('+12V', '-12V', 'AGND'):
        chosen.setdefault(net, [])
    result['islands'] = chosen
    result['open_edges'] = sum(max(0, len(groups)-1) for groups in chosen.values())
    result['scope'] = 'DERIVED ROUTING SELECTION ONLY; all geometry obstacles retained; original dump remains native count authority'
    return result, observations


def focus(output):
    output = private_output(output)
    _, _, dump = settled_data(output, 'before')
    mapping = json.loads((output/'mapping.json').read_text())
    selected, observations = focused_dump(dump, mapping['pilot']['targets'])
    (output/'focused-dump.json').write_bytes(json_bytes(selected, compact=True))
    (output/'target-observations.json').write_bytes(json_bytes(observations))
    print(json.dumps({'open_sample_pairs': selected['open_edges'], 'native_acceptance': False}))


def fresh_copy(output):
    output = private_output(output)
    board, _, _ = settled_data(output, 'after')
    target = output/'fresh/osc-core.kicad_pcb'
    if target.exists():
        raise ValueError('fresh output already used; do not silently retry')
    shutil.copyfile(board, target)
    # SaveBoard can serialize project defaults. Fresh comparison uses the exact
    # candidate companion context, still verified by the independent warning audit.
    shutil.copyfile(board.with_suffix('.kicad_pro'), target.with_suffix('.kicad_pro'))


def audit_pilot(output):
    """Native warning execution belongs exclusively to an admitted decision slot."""
    from scripts.pcbgen.complete_native_warnings import audit_current_reports
    from scripts.pcbgen.route_jack_grid import connectivity_signature, split_pad_groups, warning_identities
    from scripts.pcbgen.copper_identity import retention
    output = private_output(output)
    before, before_drc, before_dump = settled_data(output, 'before')
    after, after_drc, after_dump = settled_data(output, 'after')
    fresh, fresh_drc, fresh_dump = settled_data(output, 'fresh')
    if connectivity_signature(after_dump) != connectivity_signature(fresh_dump):
        raise ValueError('fresh-copy full connectivity mismatch')
    if warning_identities(after_drc) != warning_identities(fresh_drc):
        raise ValueError('fresh-copy warning identity mismatch')
    for report in (before_drc, after_drc, fresh_drc):
        if any(v['severity'] == 'error' for v in report['violations']) or report['schematic_parity']:
            raise ValueError('native errors/parity prevent pilot acceptance')
    splits = split_pad_groups(before_dump, after_dump)
    copper = retention(before_dump, after_dump)
    if splits or copper['removed_objects'] or copper['changed_existing_uuids']:
        raise ValueError('original pad groups/copper changed in additive pilot')
    if copper['added_objects']:
        full_before, full_after, proof = audit_current_reports(before, after, before_drc, after_drc, output/'complete-warnings', zone_batch_size=1)
        new_warnings = sorted(set(warning_identities(full_after))-set(warning_identities(full_before)))
    else:
        # The generic additive warning auditor correctly rejects an empty scope.
        # Preserve this negative result without pretending an audit occurred.
        from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
        unchanged_nonrouting(before.read_text(), after.read_text())
        if connectivity_signature(before_dump) != connectivity_signature(after_dump):
            raise ValueError('empty proposal changed native connectivity')
        if warning_identities(before_drc) != warning_identities(after_drc):
            raise ValueError('empty proposal changed observed warning identities')
        proof = {'status': 'NOT RUN: zero added copper; NOT EXERCISED / NO IMPROVEMENT; no native acceptance claim'}
        new_warnings = []
    if new_warnings:
        raise ValueError('new complete warning identities')
    mapping = json.loads((output/'mapping.json').read_text())
    _, observed = focused_dump(before_dump, mapping['pilot']['targets'])
    result = {'status': 'BOUNDED NATIVE COMPARISON; NOT PRODUCTION ADOPTION' if copper['added_objects'] else 'NO IMPROVEMENT / NOT EXERCISED; COMPLETE WARNINGS NOT RUN', 'adopted': False,
              'before_sha256': digest(before.read_bytes()), 'after_sha256': digest(after.read_bytes()),
              'fresh_sha256': digest(fresh.read_bytes()), 'whole_candidate_open_edges_before': before_dump['open_edges'],
              'whole_candidate_open_edges_after': after_dump['open_edges'], 'sample_observations': observed,
              'sample_after': focused_dump(after_dump, mapping['pilot']['targets'])[1],
              'copper_retention': copper, 'original_group_splits': splits, 'new_complete_warnings': new_warnings,
              'complete_warning_proof': proof,
              'limits': ['Compare sample outcomes/time at identical budgets, not raw open totals across different candidates.',
                         'Already-connected samples are NOT EXERCISED; decision owner must select a real demand or explicitly review a disposable cut.']}
    (output/'pilot-receipt.json').write_bytes(json_bytes(result))
    print(json.dumps({'receipt': str(output/'pilot-receipt.json'), 'adopted': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('generate', 'check', 'materialize', 'settle', 'focus', 'fresh-copy', 'audit-pilot'))
    parser.add_argument('--pilot', choices=tuple(SAMPLES))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--board', type=Path)
    args = parser.parse_args()
    if args.command in ('generate', 'check'):
        outputs = build_outputs()
        if args.command == 'check':
            changed = [p for p, data in outputs.items() if not (OUT/p).exists() or (OUT/p).read_bytes() != data]
            if changed:
                raise SystemExit('candidate drift: '+', '.join(changed))
            print(f'PASS: {len(outputs)} deterministic candidate artifacts; native NOT RUN')
        else:
            for path, data in outputs.items():
                target = OUT/path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            print(f'Generated {len(outputs)} source candidate artifacts; native NOT RUN')
    elif args.command == 'materialize':
        if not args.pilot or not args.output:
            parser.error('materialize requires --pilot and --output')
        print(json.dumps(materialize(args.pilot, args.output)))
    elif args.command in ('focus', 'fresh-copy', 'audit-pilot'):
        if not args.output:
            parser.error(args.command+' requires --output')
        {'focus': focus, 'fresh-copy': fresh_copy, 'audit-pilot': audit_pilot}[args.command](args.output)
    else:
        if not args.board:
            parser.error('settle requires --board')
        settle(args.board)


if __name__ == '__main__':
    main()
