"""Deterministic courtyard-level ST-07 candidate from the retained FFC projection.

This is a placement screen, not a copper, loop, or physical tool-access check.
"""
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import stackgeom as sg

OUT = ROOT / 'design/stack/trimmers/relocation-plan.json'
SOURCES = [
    'design/stack/geometry/links/link-gate.json',
    'design/stack/geometry/links/link-gate-options.json',
    'design/stack/fixings/fixing-sites.json',
    'design/stack/geometry/stack-candidate.json',
    'boards/osc-core/osc-core.kicad_pcb',
    'design/grid/placements.lock.json',
    'design/partition/partition.json',
    'design/stack/geometry/parameters.json',
    'scripts/stack/geometry/kicad_extract.py',
    'scripts/stack/geometry/stackgeom.py',
]
SEARCH_RADIUS_MM = 30.0  # Assumed planning window, not an electrical limit.
SEARCH_STEP_MM = 0.5


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def board_metadata():
    """Read project role/block fields and pad nets without changing the board."""
    text = (ROOT / 'boards/osc-core/osc-core.kicad_pcb').read_text()
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint "', text)]
    out = {}
    for a in starts:
        end = text.find('\n\t)', a + 1)
        block = text[a:end + 3]
        props = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', block))
        ref = props.get('Reference')
        if ref:
            out[ref] = {
                'module': props.get('Block') or None,
                'role': props.get('Role') or None,
                'nets': sorted(set(re.findall(r'\(net "([^"]+)"\)', block))),
            }
    return out


def shift_footprint(f, replacement):
    f = copy.deepcopy(f)
    dx = replacement['new'][0] - f['origin'][0]
    dy = replacement['new'][1] - f['origin'][1]
    f['origin'] = replacement['new']
    f['side'] = replacement['new_face']
    f['courtyard'] = replacement['new_courtyard']
    for pad in f['pads']:
        pad['center'] = [round(pad['center'][0] + dx, 4), round(pad['center'][1] + dy, 4)]
        pad['bbox'] = [round(v + (dx if i % 2 == 0 else dy), 4) for i, v in enumerate(pad['bbox'])]
    return f


def transformed_inventory(boards, gate):
    moves = {(x['board'], x['ref']): x for x in gate['replacement']['footprints'] if x.get('new')}
    out = {}
    for board, fps in boards.items():
        out[board] = [shift_footprint(f, moves[(board, f['ref'])])
                      if (board, f['ref']) in moves else copy.deepcopy(f) for f in fps]
    return out


def obstacles(ci, gate, moving):
    model = ci['parameters']['obstacle_model']
    base = [f for f in ci['boards']['K'] if f['ref'] not in moving]
    obs = sg.Obstacles(base, model, drop=sg.retired_k_headers(ci),
                       skip_hole=lambda f: f['ref'].startswith('MH_K-SERVICE'))
    for link in gate['links']:
        if not link['placed']:
            continue
        g = link['geometry']
        for key in ('K_connector', 'K_tail', 'slot'):
            obs._add('B', g[key], link['id'], key)
        obs._add('B', sg.grow(g['K_connector'], gate['parameters']['latch_margin_mm']),
                 link['id'], 'latch margin')
    for fixing in gate['fixings']['keepouts']:
        x, y = fixing['K']
        obs._add('B', sg.circle_rect(x, y, 2 * fixing['r_K']), fixing['id'], 'fixing keepout')
    return obs


def offsets():
    n = int(SEARCH_RADIUS_MM / SEARCH_STEP_MM)
    return sorted(((i * SEARCH_STEP_MM, j * SEARCH_STEP_MM)
                   for i in range(-n, n + 1) for j in range(-n, n + 1)
                   if i * i + j * j <= n * n),
                  key=lambda p: (p[0] * p[0] + p[1] * p[1], p[0], p[1]))


def place(f, obs, outline, margin, steps):
    c = f['courtyard']
    if c is None:
        return None
    for dx, dy in steps:
        rect = [round(c[i] + (dx if i % 2 == 0 else dy), 4) for i in range(4)]
        if sg.rect_inside_poly(rect, outline, margin) and not obs.hits('B', rect):
            obs._add('B', sg.grow(rect, 0.35), f['ref'], 'candidate courtyard')
            return {'xy_mm': [round(f['origin'][0] + dx, 4), round(f['origin'][1] + dy, 4)],
                    'courtyard_mm': rect, 'distance_mm': round(math.hypot(dx, dy), 4)}
    return None


def build():
    gate = json.loads((ROOT / SOURCES[0]).read_text())
    stack = json.loads((ROOT / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    raw = sg.load_raw()
    boards = sg.load_boards(raw)
    transformed = transformed_inventory(boards, gate)
    k_before = {f['ref']: f for f in boards['K']}
    k_after = {f['ref']: f for f in transformed['K']}
    adj = {r: f for r, f in k_after.items() if 'TC33X' in f['lib'] or f['lib'].startswith('TestPad')}
    moving = {r for r, f in adj.items() if f['side'] == 'F'}
    raw['partition']['boards']  # Ensure partition source is read before candidate construction.
    ci = {'parameters': raw['parameters'], 'partition': raw['partition'], 'boards': transformed}
    obs = obstacles(ci, gate, moving)
    outline = stack['planes']['K']['outline']
    margin = raw['parameters']['board_edge_margin_mm']
    meta = board_metadata()
    steps = offsets()
    records = []
    # Small courtyards first keeps this assignment deterministic, but is only a heuristic.
    order = sorted(moving, key=lambda r: ((adj[r]['courtyard'][2] - adj[r]['courtyard'][0]) *
                                          (adj[r]['courtyard'][3] - adj[r]['courtyard'][1]), r))
    placements = {r: place(adj[r], obs, outline, margin, steps) for r in order}
    gate_moves = {(x['board'], x['ref']): x for x in gate['replacement']['footprints']}
    for ref, f in sorted(adj.items()):
        before = k_before[ref]
        m = meta.get(ref, {})
        is_front = f['side'] == 'F'
        proposal = placements.get(ref)
        records.append({
            'ref': ref, 'kind': 'trimmer' if 'TC33X' in f['lib'] else 'test_pad',
            'footprint': f['lib'], 'module': m.get('module'), 'role': m.get('role'),
            'nets': m.get('nets', []),
            'canonical': {'face': before['side'], 'xy_mm': before['origin']},
            'after_link_projection': {'face': f['side'], 'xy_mm': f['origin'],
                                      'courtyard_mm': f['courtyard'],
                                      'replacement_step': gate_moves.get(('K', ref), {}).get('step')},
            'access': 'FRONT_BLOCKED_IN_CLOSED_STACK' if is_front else 'REAR_FACE_CANDIDATE',
            'proposal': {'face': 'B', **proposal} if proposal else None,
            'verdict': ('GEOMETRY_CANDIDATE_NEEDS_CIRCUIT_AND_SERVICE_REVIEW' if proposal else
                        'NO_COURTYARD_POSITION_WITHIN_30MM_NEEDS_DESIGN' if is_front else
                        'KEEP_REAR_NEEDS_SERVICE_REVIEW'),
            'node_sensitivity': 'UNRESOLVED: schematic role/net alone does not bound loop or guard',
            'loop_length_mm': None, 'added_vias': None, 'guard_status': 'UNRESOLVED',
            'service_tool_access': 'UNMEASURED',
            'fallback': ('rear-adjust exact part or facing-board aperture, neither selected'
                         if is_front and not proposal else None),
        })
    return {
        'schema_version': 1,
        'status': 'CANDIDATE ONLY; NO CANONICAL BOARD MOVE OR PHYSICAL ACCESS CLAIM',
        'source_commit': 'bf6c67718f2fe157bd58966d0c3555ea8f37b596',
        'source_sha256': {p: sha(p) for p in SOURCES},
        'canonical_geometry_digest': sg.canonical_digest(sg.canonical_inputs(raw, boards)),
        'board_metadata_digest': sg.canonical_digest({ref: meta[ref] for ref in sorted(adj)}),
        'source_counts': {'replacement_footprints': len(gate['replacement']['footprints']),
                          'link_count': len([x for x in gate['links'] if x['placed']]),
                          'fixing_keepouts': len(gate['fixings']['keepouts'])},
        'stack': {'K_rear_z_mm': stack['planes']['K']['rear_z_mm'],
                  'K_rear_parts_z_mm': stack['stack']['K_rear_parts_z_mm'],
                  'enclosure_inner_rear_z_mm': stack['stack']['enclosure_inner_rear_z_mm']},
        'search': {'radius_mm': SEARCH_RADIUS_MM, 'grid_mm': SEARCH_STEP_MM,
                   'assumption': 'courtyard-only screen; 30 mm is not an electrical limit',
                   'order': order},
        'unplaced_replacement_refs': [x['ref'] for x in gate['replacement']['footprints'] if not x.get('new')],
        'records': records,
    }


if __name__ == '__main__':
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + '\n')
