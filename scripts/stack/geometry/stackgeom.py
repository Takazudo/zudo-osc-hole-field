"""Shared inputs, canonical digest and courtyard-level geometry for the direct-stack candidate.

Everything here is a courtyard-and-pad-level planning screen. Nothing is a copper
clearance, a tolerance result or a physical fit.
"""
import hashlib
import json
import math
import subprocess
from pathlib import Path

import kicad_extract

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / 'design/stack/geometry'
CANDIDATE = OUT_DIR / 'stack-candidate.json'
REPORT = OUT_DIR / 'check-report.json'
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


def git_head(root=ROOT):
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'UNKNOWN'


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

class Obstacles:
    """Courtyards grown on their own face, through-hole pads and holes grown on the opposite face."""
    CELL = 5.0

    def __init__(self, fps, model, drop=frozenset(), skip_hole=lambda f: False):
        self.items = {'F': [], 'B': []}
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
        self.index = {}
        for s in 'FB':
            idx = {}
            for k, (r, ref, kind) in enumerate(self.items[s]):
                for i in range(int(r[0] // self.CELL), int(r[2] // self.CELL) + 1):
                    for j in range(int(r[1] // self.CELL), int(r[3] // self.CELL) + 1):
                        idx.setdefault((i, j), []).append(k)
            self.index[s] = idx

    def _add(self, side, rect, ref, kind):
        self.items[side].append(([round(v, 4) for v in rect], ref, kind))

    def hits(self, side, rect, skip=()):
        seen = set()
        out = []
        idx = self.index[side]
        for i in range(int(rect[0] // self.CELL), int(rect[2] // self.CELL) + 1):
            for j in range(int(rect[1] // self.CELL), int(rect[3] // self.CELL) + 1):
                for k in idx.get((i, j), ()):
                    if k in seen:
                        continue
                    seen.add(k)
                    r, ref, kind = self.items[side][k]
                    if ref not in skip and inter(rect, r):
                        out.append((ref, kind))
        return sorted(set(out))


# ---------------------------------------------------------------- land pattern

def envelope(land, positions, half):
    explicit = land.get('explicit_mm', {}).get(half, {})
    if str(positions) in explicit:
        w, l = explicit[str(positions)]
        return float(w), float(l)
    rule = land['rule']
    return float(rule['width_mm']), round(rule['pitch_mm'] * positions + rule['end_allowance_mm'], 4)


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
