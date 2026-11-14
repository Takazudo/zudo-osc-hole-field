"""Shared inputs, canonical digest and courtyard-level geometry for the direct-stack candidate.

Everything here is a courtyard-and-pad-level planning screen. Nothing is a copper
clearance, a tolerance result or a physical fit.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

import kicad_extract

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / 'design/stack/geometry'
CANDIDATE = OUT_DIR / 'stack-candidate.json'
REPORT = OUT_DIR / 'check-report.json'
# One threshold, in mm, for every "is this power post offset" decision (generator, checker, measurements).
OFFSET_TOL_MM = 1e-3
# Boards whose partition reserves are obstacles: EL, for the EL-to-P joint of attempt a2. P's reserves stay
# outside the obstacle model so the reconciled P measurements keep their basis.
RESERVE_BOARDS = ('EL',)
REGEN_COMMAND = 'python3 scripts/stack/geometry/generate.py && python3 scripts/stack/geometry/check.py'

BOARD_FILES = {
    'K': 'boards/osc-core/osc-core.kicad_pcb',
    'JL': 'boards/osc-jack-left/osc-jack-left.kicad_pcb',
    'JR': 'boards/osc-jack-right/osc-jack-right.kicad_pcb',
    'P': 'boards/osc-control/osc-control-routed-draft.kicad_pcb',
    'EL': 'boards/osc-stage-optical/osc-stage-optical.kicad_pcb',
    'O1': 'boards/osc-octave-1/osc-octave-1.kicad_pcb',
    'O2': 'boards/osc-octave-2/osc-octave-2.kicad_pcb',
    'O3': 'boards/osc-octave-3/osc-octave-3.kicad_pcb',
    'O4': 'boards/osc-octave-4/osc-octave-4.kicad_pcb',
    'O5': 'boards/osc-octave-5/osc-octave-5.kicad_pcb',
}
JSON_FILES = {
    'partition': 'design/partition/partition.json',
    'lock': 'design/grid/placements.lock.json',
    'core_rear': 'design/mechanical/core-rear-allowance.json',
    'selector_assembly': 'design/mechanical/selector-assembly.json',
    'ic_envelopes': 'design/mechanical/ic-envelope-native-report.json',
    'checkpoint': 'circuit/routing/osc-pcb-current-checkpoint.json',
    'parameters': 'design/stack/geometry/parameters.json',
    'land_pattern': 'design/stack/geometry/land-pattern.json',
}
PROGRAM_FILES = ['scripts/stack/geometry/kicad_extract.py', 'scripts/stack/geometry/stackgeom.py',
                 'scripts/stack/geometry/generate.py']


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


# ---------------------------------------------------------------- canonical inputs

def _subset(d, keys):
    return {k: d[k] for k in keys if k in d}


def canonical_inputs(raw, boards):
    """The exact fields the candidate uses. Routing (tracks, vias, zones, nets) is not among them."""
    part = raw['partition']
    lock = raw['lock']
    sel = raw['selector_assembly']
    return {
        'boards': {key: [_subset(f, ('ref', 'lib', 'value', 'side', 'origin', 'angle', 'courtyard', 'pads'))
                         for f in fps] for key, fps in sorted(boards.items())},
        'partition': {
            'boards': [_subset(b, ('id', 'board_key', 'outline', 'face_z_mm', 'thickness_mm', 'supports_mm',
                                   'board_bulk_reserve', 'reserves')) for b in part['boards']],
            'connectors': [_subset(c, ('id', 'board', 'center_mm', 'side', 'pcb_reference', 'contacts', 'pin_map',
                                       'header_mpn')) for c in part['connectors']],
            'harnesses': [dict(_subset(h, ('id', 'boards', 'header_ids', 'signal_count', 'return_contacts',
                                           'rail_contacts', 'unused_contacts')),
                               signals=[s['net'] for s in h['signals']]) for h in part['harnesses']],
            'load_side_terminals': [_subset(t, ('reference', 'board', 'net', 'center_mm', 'side', 'copper_land_mm',
                                                'maximum_courtyard_mm')) for t in part['load_side_terminals']],
            'load_side_wires': [_subset(w, ('id', 'net', 'terminal_refs')) for w in part['load_side_wires']],
            'supports': [_subset(s, ('id', 'board', 'position_mm', 'pcb_hole_mm', 'collar_diameter_mm'))
                         for s in part['supports']],
            'K_service_apertures': [_subset(a, ('header_id', 'center_mm', 'diameter_mm'))
                                    for a in part['K_service_apertures']],
            'jack_seam_carrier': _subset(part['jack_split']['carrier'],
                                         ('rear_rect_mm', 'rear_z_mm', 'front_lip_rect_mm', 'front_lip_z_mm',
                                          'cross_members')),
            'optical_passages': [_subset(o, ('uid', 'kind', 'center_mm', 'diameter_mm')) for o in part['optical_passages']],
            'counts': part['counts'],
            'enclosure': _subset(part['enclosure'], ('inside_depth_mm', 'rear_clearance_from_K_B_face_mm')),
        },
        'lock': {
            'kicad_translation_mm': lock['frame']['kicad_translation_mm'],
            'octave_rows': [_subset(r, ('uid', 'ref', 'block', 'x_mm', 'y_mm', 'rot_deg', 'assembly_pcb_z_mm'))
                            for r in lock['placements'] if r['kind'] == 'octave'],
        },
        'mechanical': {
            'core_rear_ceiling_mm': raw['core_rear']['component_height_ceiling_mm'],
            'selector_body_support_z_mm': sel['drawing']['body_support_z_mm'],
            'selector_instances': [_subset(i, ('uid', 'pcb_z_mm', 'adapter_group')) for i in sel['instances']],
            'model_envelopes': [{'footprint': c['footprint'], 'side': c['side'],
                                 'z': c['native_model']['bounds'][2]}
                                for c in raw['ic_envelopes']['cases'] if c.get('native_model')],
        },
        'parameters': raw['parameters'],
        'land_pattern': raw['land_pattern'],
    }


def load_raw(root=ROOT):
    return {k: json.loads((Path(root) / p).read_text()) for k, p in JSON_FILES.items()}


def load_boards(raw, root=ROOT, files=BOARD_FILES):
    t = raw['lock']['frame']['kicad_translation_mm']
    return {k: kicad_extract.parse_board(Path(root) / p, (t['x'], t['y'])) for k, p in files.items()}


def input_hashes(root=ROOT):
    paths = list(JSON_FILES.values()) + list(BOARD_FILES.values()) + PROGRAM_FILES
    return {p: sha256_file(Path(root) / p) for p in sorted(paths)}


# ---------------------------------------------------------------- rectangles

def inter(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def overlap_depth(a, b):
    """Positive penetration depth of two rectangles (smaller axis overlap), else <= 0."""
    return min(a[2] - b[0], b[2] - a[0], a[3] - b[1], b[3] - a[1])


def grow(r, m):
    return [r[0] - m, r[1] - m, r[2] + m, r[3] + m]


def inside(inner, outer, eps=1e-6):
    return (inner[0] >= outer[0] - eps and inner[1] >= outer[1] - eps and
            inner[2] <= outer[2] + eps and inner[3] <= outer[3] + eps)


def centre(r):
    return [round((r[0] + r[2]) / 2, 4), round((r[1] + r[3]) / 2, 4)]


def env_rect(cx, cy, width, length, long_axis_x):
    if long_axis_x:
        return [round(cx - length / 2, 4), round(cy - width / 2, 4), round(cx + length / 2, 4), round(cy + width / 2, 4)]
    return [round(cx - width / 2, 4), round(cy - length / 2, 4), round(cx + width / 2, 4), round(cy + length / 2, 4)]


def point_in_poly(x, y, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def rect_poly_overlap(rect, poly):
    """True when the rectangle and a rectilinear outline share area (sampled at 0.25 mm)."""
    steps_x = max(2, int((rect[2] - rect[0]) / 0.25) + 1)
    steps_y = max(2, int((rect[3] - rect[1]) / 0.25) + 1)
    for i in range(steps_x):
        x = rect[0] + (rect[2] - rect[0]) * (i + 0.5) / steps_x
        for j in range(steps_y):
            y = rect[1] + (rect[3] - rect[1]) * (j + 0.5) / steps_y
            if point_in_poly(x, y, poly):
                return True
    return False


def circle_rect(cx, cy, d):
    return [cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2]


# ---------------------------------------------------------------- obstacle model

class RectIndex:
    """5 mm spatial hash of (rect, payload) items."""
    CELL = 5.0

    def __init__(self):
        self.items = []
        self.cells = {}

    def add(self, rect, payload):
        k = len(self.items)
        self.items.append((rect, payload))
        for i in range(int(rect[0] // self.CELL), int(rect[2] // self.CELL) + 1):
            for j in range(int(rect[1] // self.CELL), int(rect[3] // self.CELL) + 1):
                self.cells.setdefault((i, j), []).append(k)

    def near(self, rect):
        """Items whose cells meet the cells of `rect` (a superset of the intersecting items), each once."""
        seen = set()
        for i in range(int(rect[0] // self.CELL), int(rect[2] // self.CELL) + 1):
            for j in range(int(rect[1] // self.CELL), int(rect[3] // self.CELL) + 1):
                for k in self.cells.get((i, j), ()):
                    if k not in seen:
                        seen.add(k)
                        yield self.items[k]


class Obstacles:
    """Courtyards grown on their own face, through-hole pads and holes grown on the opposite face."""

    def __init__(self, fps, model, drop=frozenset(), skip_hole=lambda f: False):
        self.index = {'F': RectIndex(), 'B': RectIndex()}
        g_cy = model['own_face_courtyard_growth_mm']
        g_pad = model['opposite_face_through_hole_pad_growth_mm']
        g_hole = model['hole_growth_mm']
        for f in fps:
            if f['ref'] in drop:
                continue
            tht = [p for p in f['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
            if f['lib'] == '':
                if skip_hole(f):
                    continue
                for p in tht:
                    m = max(p['bbox'][2] - p['bbox'][0], p['drill'])
                    r = circle_rect(p['center'][0], p['center'][1], m)
                    for s in 'FB':
                        self._add(s, grow(r, g_hole), f['ref'], 'hole')
                continue
            if f['courtyard']:
                self._add(f['side'], grow(f['courtyard'], g_cy), f['ref'], 'courtyard')
            other = 'B' if f['side'] == 'F' else 'F'
            for p in tht:
                self._add(other, grow(p['bbox'], g_pad), f['ref'], 'through-hole pad')

    def _add(self, side, rect, ref, kind):
        self.index[side].add([round(v, 4) for v in rect], (ref, kind))

    def add_reserves(self, board, growth):
        """Partition reserves (bulk-part allocations) of a board, grown like courtyards on their own faces."""
        for r in board.get('reserves', []):
            for side in r['sides']:
                self._add(side[0], grow(r['rect'], growth), 'reserve ' + r['id'], 'reserve')

    def circle_hits(self, side, cx, cy, r, skip=()):
        """(ref, kind, penetration_mm) of every obstacle a circle of radius r overlaps on one face."""
        out = {}
        for rect, payload in self.index[side].near(circle_rect(cx, cy, 2 * r)):
            if payload[0] in skip:
                continue
            d = circle_rect_depth(cx, cy, r, rect)
            if d > 1e-9:
                out[payload] = max(out.get(payload, 0), round(d, 4))
        return sorted((a, b, d) for (a, b), d in out.items())

    def hits_depth(self, side, rect, skip=()):
        """(ref, kind, penetration_mm) of every obstacle the rectangle overlaps on one face."""
        out = {}
        for r, payload in self.index[side].near(rect):
            if payload[0] not in skip and inter(rect, r):
                out[payload] = max(out.get(payload, 0), round(overlap_depth(rect, r), 4))
        return sorted((a, b, d) for (a, b), d in out.items())

    def hits(self, side, rect, skip=()):
        return sorted({payload for r, payload in self.index[side].near(rect)
                       if payload[0] not in skip and inter(rect, r)})


def retired_k_headers(ci):
    """K-side headers of harnesses that end on a retired board."""
    retired = set(ci['parameters']['retired_boards'])
    con = {c['id']: c for c in ci['partition']['connectors']}
    out = set()
    for h in ci['partition']['harnesses']:
        if any(b in retired for b in h['boards']):
            out |= {con[cid]['pcb_reference'] for cid in h['header_ids'] if con[cid]['board'] == 'K'}
    return frozenset(out)


def stack_obstacles(ci, keys=('K', 'JL', 'JR', 'P', 'EL', 'O1', 'O3', 'O5')):
    """Obstacle sets of the stack: K without its retired headers and service apertures, other boards as drawn."""
    model = ci['parameters']['obstacle_model']
    out = {}
    for key in keys:
        if key == 'K':
            out[key] = Obstacles(ci['boards']['K'], model, drop=retired_k_headers(ci),
                                 skip_hole=lambda f: f['ref'].startswith('MH_K-SERVICE'))
        else:
            out[key] = Obstacles(ci['boards'][key], model)
        if key in RESERVE_BOARDS:
            board = next(b for b in ci['partition']['boards'] if b['board_key'] == key)
            out[key].add_reserves(board, model['own_face_courtyard_growth_mm'])
    return out


def rect_inside_poly(rect, poly, margin=0.0):
    """The rectangle grown by `margin` lies inside a rectilinear outline (corners inside, no vertex inside)."""
    r = grow(rect, margin)
    eps = 1e-6
    for x, y in ((r[0] + eps, r[1] + eps), (r[2] - eps, r[1] + eps), (r[2] - eps, r[3] - eps), (r[0] + eps, r[3] - eps)):
        if not point_in_poly(x, y, poly):
            return False
    return not any(r[0] + eps < x < r[2] - eps and r[1] + eps < y < r[3] - eps for x, y in poly)


def point_segment_distance(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def distance_to_outline(px, py, poly):
    return min(point_segment_distance(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


# ---------------------------------------------------------------- land pattern

def envelope_info(land, positions, half, rows=1):
    """Courtyard envelope of one connector half: width across the rows, length along them, with provenance.

    An explicit entry "<rows>x<per_row>" of the half overrides its per-row-count rule.
    """
    if positions % rows:
        raise ValueError('%d positions do not fill %d rows' % (positions, rows))
    per_row = positions // rows
    key = '%dx%d' % (rows, per_row)
    h = land['halves'][half]
    if key in h.get('explicit', {}):
        e = h['explicit'][key]
        return {'key': key, 'width_mm': float(e['width_mm']), 'length_mm': float(e['length_mm']),
                'status': e['status'], 'source': e['source']}
    rule = h['rules'][str(rows)]
    length = round(rule['pitch_mm'] * (per_row - 1) + rule['length_at_one_position_mm'], 4)
    return {'key': key, 'width_mm': float(rule['width_mm']), 'length_mm': length,
            'status': rule['status'], 'source': rule['source']}


def envelope(land, positions, half, rows=1):
    e = envelope_info(land, positions, half, rows)
    return e['width_mm'], e['length_mm']


def circle_rect_depth(cx, cy, r, rect):
    """Penetration of a circle into a rectangle (> 0 means overlap): r minus the centre's distance to it, or r plus
    the distance to the nearest edge when the centre lies inside."""
    dx = max(rect[0] - cx, 0, cx - rect[2])
    dy = max(rect[1] - cy, 0, cy - rect[3])
    if dx == dy == 0:
        return r + min(cx - rect[0], rect[2] - cx, cy - rect[1], rect[3] - cy)
    return r - math.hypot(dx, dy)


def runs(values, step):
    out = []
    start = prev = None
    for v in values:
        if start is None:
            start = v
        elif v - prev > step * 1.01:
            out.append([start, prev])
            start = v
        prev = v
    if start is not None:
        out.append([start, prev])
    return out


def frange(a, b, step):
    n = int(round((b - a) / step))
    return [round(a + i * step, 4) for i in range(n + 1)]


# ---------------------------------------------------------------- interior fastener candidates

INTERIOR_SITE_RULE = ('front B.Cu and K F.Cu clear within 3.0 mm, K B.Cu within 2.6 mm, 3 mm inside both outlines, '
                      '0.5 mm grid, greedy 8 mm thinning')
_INTERIOR_CACHE = {}


def _interior_sites(ci, edge, step):
    def build(key):
        idx = {'F': RectIndex(), 'B': RectIndex()}
        for f in ci['boards'][key]:
            if 'LoadWire' in f['lib']:
                continue
            if f['courtyard']:
                idx[f['side']].add(f['courtyard'], None)
            for p in f['pads']:
                if p['drill']:
                    idx['F'].add(p['bbox'], None)
                    idx['B'].add(p['bbox'], None)
                else:
                    idx[f['side']].add(p['bbox'], None)
        return idx

    def free(idx, side, cx, cy, rad):
        for r, _ in idx[side].near([cx - rad, cy - rad, cx + rad, cy + rad]):
            dx = max(r[0] - cx, 0, cx - r[2])
            dy = max(r[1] - cy, 0, cy - r[3])
            if dx * dx + dy * dy < rad * rad:
                return False
        return True
    ol = {b['board_key']: b['outline'] for b in ci['partition']['boards']}
    kidx = build('K')
    out = {}
    for front in ('JL', 'JR', 'P'):
        fidx = build(front)
        poly = ol[front]
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        pts = []
        x = min(xs) + edge
        while x <= max(xs) - edge:
            y = min(ys) + edge
            while y <= max(ys) - edge:
                if all(point_in_poly(x + dx, y + dy, poly) and point_in_poly(x + dx, y + dy, ol['K'])
                       for dx, dy in ((0, 0), (edge, 0), (-edge, 0), (0, edge), (0, -edge))):
                    if free(fidx, 'B', x, y, 3.0) and free(kidx, 'F', x, y, 3.0) and free(kidx, 'B', x, y, 2.6):
                        pts.append((x, y))
                y += step
            x += step
        kept = []
        for p in pts:
            if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= 64 for q in kept):
                kept.append(p)
        out[front] = [[round(p[0], 4), round(p[1], 4)] for p in kept]
    return out


def interior_fastener_sites(ci, edge=3.0, step=0.5):
    """Interior tie-post candidate sites per front board (JL, JR, P) under the ST-02 planning screen; cached per input."""
    key = canonical_digest([ci['boards'][k] for k in ('K', 'JL', 'JR', 'P')] +
                           [b['outline'] for b in ci['partition']['boards']] + [edge, step])
    if key not in _INTERIOR_CACHE:
        _INTERIOR_CACHE[key] = _interior_sites(ci, edge, step)
    return copy.deepcopy(_INTERIOR_CACHE[key])
