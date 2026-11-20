"""Extract the current OSC boards into a compact view model for the instrument preview.

Reads native KiCad 10 boards in pure Python (no KiCad, no network) and writes
``view-data.json`` plus one 1-bit PNG per copper layer under ``data/``. Nothing under
boards/, design/ or schematic/ is written. This is not a native KiCad render.

    python3 project/osc-hole-field/instrument-preview/extract.py [--check]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from kicad_pcb import outline_loops, polygon_area, read_board, rot  # noqa: E402

DATA_DIR = HERE / 'data'
VIEW = HERE / 'view-data.json'

# Current boards. P is the routed draft: design/reports/instrument-readiness.json binds
# it as the P unit and lists osc-control-layout.kicad_pcb under excluded_board_files.
BOARDS = [
    ('osc-stage-optical', 'boards/osc-stage-optical/osc-stage-optical.kicad_pcb', 'Stage optical board'),
    ('osc-jack-left', 'boards/osc-jack-left/osc-jack-left.kicad_pcb', 'Jack board, left half'),
    ('osc-jack-right', 'boards/osc-jack-right/osc-jack-right.kicad_pcb', 'Jack board, right half'),
    ('osc-control', 'boards/osc-control/osc-control-routed-draft.kicad_pcb', 'Control board (routed draft)'),
    ('osc-octave-1', 'boards/osc-octave-1/osc-octave-1.kicad_pcb', 'Octave adapter 1'),
    ('osc-octave-2', 'boards/osc-octave-2/osc-octave-2.kicad_pcb', 'Octave adapter 2'),
    ('osc-octave-3', 'boards/osc-octave-3/osc-octave-3.kicad_pcb', 'Octave adapter 3'),
    ('osc-octave-4', 'boards/osc-octave-4/osc-octave-4.kicad_pcb', 'Octave adapter 4'),
    ('osc-octave-5', 'boards/osc-octave-5/osc-octave-5.kicad_pcb', 'Octave adapter 5'),
    ('osc-core', 'boards/osc-core/osc-core.kicad_pcb', 'Core board'),
]
PANEL_PCB = 'boards/panel/panel.kicad_pcb'
EXCLUDED = {
    'boards/osc-control/osc-control-layout.kicad_pcb': 'placement-only P layout input without copper; excluded by design/reports/instrument-readiness.json',
    'boards/osc-jack/osc-jack.kicad_pcb': 'historical single jack board, replaced by the JL/JR halves',
    'boards/fixture-jacks/fixture-jacks.kicad_pcb': 'test fixture, not an instrument board',
}
OTHER_INPUTS = {
    'partition': 'design/partition/partition.json',
    'lock': 'design/grid/placements.lock.json',
    'checkpoint': 'circuit/routing/osc-pcb-current-checkpoint.json',
    'readiness': 'design/reports/instrument-readiness.json',
    'panel_params': 'design/panel/panel-params.json',
    'selector': 'design/mechanical/selector-assembly.json',
    'artwork': 'design/panel/current-audit/current-panel.svg',
    'meshes': 'project/osc-hole-field/workbench/component-preview/models/meshes.json',
}

# Pixels per mm for copper rasters, chosen to keep the page under its 12 MB budget.
PPM = {'osc-core': 12, 'osc-jack-left': 14, 'osc-jack-right': 14, 'osc-control': 12, 'osc-stage-optical': 16}
PPM_DEFAULT = 24

# Display heights (mm) by package family. ILLUSTRATIVE ONLY: not datasheet heights,
# not fit or clearance evidence.
FAMILIES = [
    # key, label, regex on footprint name, height mm, colour
    ('r0603', '0603 resistor', r'^R0603$', 0.45, '#2b2d30'),
    ('c0603', '0603 capacitor', r'^C0603$', 0.8, '#b08a5a'),
    ('c0805', '0805/1206 capacitor', r'^C(0805|1206)$', 1.1, '#a47b4c'),
    ('r1210', '1210 resistor', r'^R_1210', 0.55, '#33363a'),
    ('diode', 'SOD-123 diode', r'^SOD-123', 1.1, '#3b3f45'),
    ('soic', 'SOIC IC', r'^SOIC-', 1.6, '#1d1f22'),
    ('tssop', 'TSSOP / QFN IC', r'^(TSSOP-|TI_RRP)', 1.0, '#202328'),
    ('sot', 'SOT-23 / SC-70', r'^SOT-', 1.1, '#26292d'),
    ('dip', 'DIP IC', r'^DIP-', 3.5, '#1d1f22'),
    ('gh', 'JST GH header', r'^JST_GH', 4.25, '#c9bfa4'),
    ('trim', 'TC33X trimmer', r'TC33X', 2.0, '#c8c2b0'),
    ('wire', 'load-wire terminal', r'^LoadWireTerminal', 2.5, '#c08040'),
    ('led', '0402 LED', r'^LED0402', 0.35, '#f4f1e6'),
    ('jack', 'WQP518MA jack', r'^Jack_3.5mm', 10.0, '#1b1c1e'),
    ('pot', 'PTV09A pot', r'^PTV09A', 7.0, '#7a5b37'),
    ('toggle', 'toggle switch', r'^Toggle_', 9.0, '#5d8fa3'),
    ('button', 'tactile button', r'^Button_', 3.5, '#4d5560'),
    ('selector', 'rotary selector', r'^SRBV', 7.5, '#5d8fa3'),
    ('testpad', 'test pad', r'^TestPad', 0.05, '#d6b25e'),
    ('mech', 'mounting / support', r'^(MountingHole|MH)', 0.05, '#8a8f94'),
    ('other', 'other package', r'.', 1.0, '#6c7178'),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def family(lib_name: str, ref: str) -> int:
    name = lib_name.split(':')[-1]
    if not name and ref.startswith('MH'):
        return [f[0] for f in FAMILIES].index('mech')
    for i, (_, _, rx, _, _) in enumerate(FAMILIES):
        if re.search(rx, name):
            return i
    return len(FAMILIES) - 1


def r2(v):
    return round(v, 3)


def copper_layers_of(pad_layers, stack):
    out = set()
    for ln in pad_layers:
        if ln == '*.Cu':
            out.update(stack)
        elif ln == 'F&B.Cu':
            out.update(('F.Cu', 'B.Cu'))
        elif ln in stack:
            out.add(ln)
    return out


def pad_outline(fp, pad):
    """Pad copper outline in board coordinates (list of points) or a circle (cx, cy, r)."""
    ox, oy = rot(pad.x, pad.y, fp.rot)
    cx, cy = fp.x + ox, fp.y + oy
    if pad.shape == 'circle':
        return ('circle', cx, cy, pad.w / 2)
    hw, hh = pad.w / 2, pad.h / 2
    if pad.shape == 'oval' and abs(pad.w - pad.h) > 1e-6:
        r = min(hw, hh)
        pts = []
        if pad.w > pad.h:
            cs = ((hw - r, 0, -90, 90), (-(hw - r), 0, 90, 270))
        else:
            cs = ((0, hh - r, 0, 180), (0, -(hh - r), 180, 360))
        for ax, ay, a0, a1 in cs:
            for k in range(9):
                a = math.radians(a0 + (a1 - a0) * k / 8)
                pts.append((ax + r * math.cos(a), ay + r * math.sin(a)))
    elif pad.shape == 'oval':
        return ('circle', cx, cy, hw)
    elif pad.shape == 'custom' and pad.poly:
        pts = list(pad.poly)
    else:
        pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    out = []
    for px, py in pts:
        qx, qy = rot(px, py, pad.angle)
        out.append((cx + qx, cy + qy))
    if pad.shape == 'custom' and pad.poly:
        # the anchor pad itself is copper too
        return ('multi', out, [(cx + q[0], cy + q[1]) for q in (rot(x, y, pad.angle) for x, y in
                                                                  ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)))])
    return ('poly', out)


def rasterize(board, bbox, ppm):
    """Return {layer: png bytes} for every copper layer, in panel-frame pixels (y down)."""
    x0, y0, x1, y1 = bbox
    W, H = int(math.ceil((x1 - x0) * ppm)) + 1, int(math.ceil((y1 - y0) * ppm)) + 1

    def P(x, y):
        return ((x - x0) * ppm, (y - y0) * ppm)

    stack = board.copper
    imgs = {ln: Image.new('1', (W, H), 0) for ln in stack}
    draws = {ln: ImageDraw.Draw(im) for ln, im in imgs.items()}
    for ln, polys in board.zones.items():
        if ln in draws:
            for pts in polys:
                draws[ln].polygon([P(*p) for p in pts], fill=1)
    for ln, segs in board.segments.items():
        if ln not in draws:
            continue
        d = draws[ln]
        for xa, ya, xb, yb, w in segs:
            pw = max(1, int(round(w * ppm)))
            a, b = P(xa, ya), P(xb, yb)
            d.line([a, b], fill=1, width=pw)
            r = w * ppm / 2
            if r >= 1:
                d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=1)
                d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=1)
    for ln, arcs in board.arcs.items():
        if ln not in draws:
            continue
        from kicad_pcb import _arc_points
        for xa, ya, xm, ym, xb, yb, w in arcs:
            pts = _arc_points(xa, ya, xm, ym, xb, yb, 5)
            draws[ln].line([P(*p) for p in pts], fill=1, width=max(1, int(round(w * ppm))), joint='curve')
    holes = []
    for x, y, size, drill, lays in board.vias:
        span = stack[stack.index(lays[0]):stack.index(lays[-1]) + 1] if lays[0] in stack and lays[-1] in stack else stack
        cx, cy = P(x, y)
        r = size * ppm / 2
        for ln in span:
            draws[ln].ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
        holes.append((cx, cy, drill * ppm / 2))
    for fp in board.footprints:
        for pad in fp.pads:
            lays = copper_layers_of(pad.layers, stack) if pad.kind != 'np_thru_hole' else set()
            if lays:
                shp = pad_outline(fp, pad)
                for ln in lays:
                    d = draws[ln]
                    if shp[0] == 'circle':
                        cx, cy = P(shp[1], shp[2]); r = shp[3] * ppm
                        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
                    elif shp[0] == 'multi':
                        d.polygon([P(*p) for p in shp[1]], fill=1)
                        d.polygon([P(*p) for p in shp[2]], fill=1)
                    else:
                        d.polygon([P(*p) for p in shp[1]], fill=1)
            if pad.drill:
                ox, oy = rot(pad.x, pad.y, fp.rot)
                cx, cy = P(fp.x + ox, fp.y + oy)
                holes.append((cx, cy, pad.drill * ppm / 2))
    for cx, cy, r in holes:
        if r >= 0.5:
            for d in draws.values():
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    out = {}
    for ln, im in imgs.items():
        buf = io.BytesIO()
        im.save(buf, 'PNG', optimize=True)
        out[ln] = (buf.getvalue(), sum(im.histogram()[1:]) / (W * H))
    return out, (W, H)


def history_trail(checkpoint, key):
    """Open-edge labels recorded in the checkpoint for this board key, oldest first."""
    trail = []
    for ep in reversed(checkpoint.get('historical_epochs', [])):
        if 'Different design epoch' in ep.get('note', ''):
            continue
        for m in re.finditer(r'\b(K|JL|JR)(\d+)\b', ep['label']):
            if m.group(1) == key:
                trail.append({'label': m.group(0), 'open_edges': int(m.group(2)), 'recorded': ep['recorded']})
    return trail


def git(*args):
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def extract(base_commit: str | None):
    inputs = {}

    def use(path):
        p = ROOT / path
        inputs[path] = {'sha256': sha256(p), 'bytes': p.stat().st_size}
        return p

    for _, path, _ in BOARDS:
        use(path)
    use(PANEL_PCB)
    for path in OTHER_INPUTS.values():
        use(path)
    partition = json.loads((ROOT / OTHER_INPUTS['partition']).read_text())
    lock = json.loads((ROOT / OTHER_INPUTS['lock']).read_text())
    checkpoint = json.loads((ROOT / OTHER_INPUTS['checkpoint']).read_text())
    readiness = json.loads((ROOT / OTHER_INPUTS['readiness']).read_text())
    units = {u['board']: u for u in readiness['units']}
    pboards = {b['id']: b for b in partition['boards']}

    pngs = {}
    boards_out = []
    totals = {'footprints': 0, 'segments': 0, 'vias': 0}
    for bid, path, title in BOARDS:
        b = read_board(ROOT / path)
        pb = pboards[bid]
        # Panel frame = KiCad board coordinates minus the FootprintOriginMm offset.
        offs = set()
        for fp in b.footprints:
            o = fp.props.get('FootprintOriginMm')
            if o:
                ox, oy = (float(v) for v in o.split(','))
                offs.add((round(fp.x - ox, 3), round(fp.y - oy, 3)))
        if len(offs) != 1:
            raise SystemExit(f'{bid}: footprint origin offsets are not uniform: {sorted(offs)[:5]}')
        dx, dy = offs.pop()
        loops = sorted(outline_loops(b.edges), key=lambda l: -abs(polygon_area(l)))
        outer = loops[0]
        bbox = (min(p[0] for p in outer) - dx, min(p[1] for p in outer) - dy,
                max(p[0] for p in outer) - dx, max(p[1] for p in outer) - dy)
        ppm = PPM.get(bid, PPM_DEFAULT)
        rasters, size = rasterize(b, (bbox[0] + dx, bbox[1] + dy, bbox[2] + dx, bbox[3] + dy), ppm)
        copper = []
        for i, ln in enumerate(b.copper):
            png, cover = rasters[ln]
            name = f'{bid}.{ln.replace(".", "-")}.png'
            pngs[name] = png
            copper.append({'layer': ln, 'file': 'data/' + name, 'bytes': len(png), 'coverage': round(cover, 4),
                           'segments': len(b.segments.get(ln, [])), 'zone_fills': len(b.zones.get(ln, []))})
        parts = []
        for fp in b.footprints:
            ref = fp.props.get('Reference', '')
            box = fp.court or fp.fab or fp.padbox or (-0.5, -0.5, 0.5, 0.5)
            src = 'courtyard' if fp.court else 'fab' if fp.fab else 'pads' if fp.padbox else 'none'
            lcx, lcy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            ox, oy = rot(lcx, lcy, fp.rot)
            fam = family(fp.lib, ref)
            uid = fp.props.get('PanelUid', '')
            parts.append([ref, fp.props.get('Value', ''), fp.props.get('MPN', ''), fp.props.get('Manufacturer', ''),
                          fp.lib.split(':')[-1], r2(fp.x - dx), r2(fp.y - dy), r2(fp.rot),
                          r2(fp.x + ox - dx), r2(fp.y + oy - dy), r2(box[2] - box[0]), r2(box[3] - box[1]),
                          0 if fp.side == 'F.Cu' else 1, fam, fp.props.get('Block', '') or fp.sheet.strip('/'),
                          uid, src, 1 if 'dnp' in fp.attrs else 0])
        npth = []
        for fp in b.footprints:
            for pad in fp.pads:
                if pad.kind == 'np_thru_hole' and pad.drill > 0:
                    ox, oy = rot(pad.x, pad.y, fp.rot)
                    npth.append([r2(fp.x + ox - dx), r2(fp.y + oy - dy), r2(pad.drill)])
        unit = units.get(path, {})
        cp = checkpoint['boards'].get(bid)
        status = {
            'adoption': unit.get('adoption', ''),
            'remaining_issues': unit.get('remaining_issues', []),
            'readiness_board_sha256': unit.get('board_sha256', ''),
            'readiness_open_edges': unit.get('retained_connectivity', {}).get('complete_native_open_edges'),
            'readiness_connectivity_status': unit.get('retained_connectivity', {}).get('status', ''),
        }
        if cp:
            ms = cp.get('metadata_successor', {})
            status.update({
                'checkpoint_label': cp['label'],
                'successor_label': ms.get('label', ''),
                'checkpoint_successor_sha256': ms.get('successor_board_sha256', ''),
                'checkpoint_board_sha256': cp['board_sha256'],
                'open_edges': cp['connectivity']['open_edges'],
                'open_edges_source': 'circuit/routing/osc-pcb-current-checkpoint.json',
                'rail_open_edges': cp['connectivity'].get('rail_open_edges', {}),
                'agnd_open_edges': cp['connectivity'].get('agnd_open_edges'),
                'signal_open_edges': cp['connectivity'].get('signal_open_edges'),
                'trail': history_trail(checkpoint, pb['board_key']) + [{'label': cp['label'], 'open_edges': cp['connectivity']['open_edges'], 'recorded': checkpoint['recorded']}],
            })
        else:
            status.update({'open_edges': status['readiness_open_edges'],
                           'open_edges_source': 'design/reports/instrument-readiness.json (retained native connectivity report)'})
        sha = inputs[path]['sha256']
        label = status.get('successor_label') if cp and status['checkpoint_successor_sha256'] == sha else (cp or {}).get('label', '')
        if bid == 'osc-control':
            label = 'P routed draft'
        totals['footprints'] += len(b.footprints)
        totals['segments'] += b.counts['segment']
        totals['vias'] += b.counts['via']
        boards_out.append({
            'id': bid, 'key': pb['board_key'], 'title': title, 'file': path, 'sha256': sha, 'label': label or pb['board_key'],
            'role': pb.get('role', ''), 'layers': b.copper, 'thickness_mm': b.thickness,
            'partition_thickness_mm': pb['thickness_mm'], 'face_z_mm': pb['face_z_mm'],
            'partition_outline': pb['outline'], 'supports_mm': pb.get('supports_mm', []),
            'kicad_to_panel_offset_mm': [dx, dy],
            'outline': [[r2(x - dx), r2(y - dy)] for x, y in outer],
            'holes': [[[r2(x - dx), r2(y - dy)] for x, y in l] for l in loops[1:]],
            'npth': npth,
            'bbox': [r2(v) for v in bbox], 'ppm': ppm, 'raster_px': list(size), 'copper': copper,
            'counts': {**b.counts, 'panel_uid_footprints': sum(1 for p in parts if p[15])},
            'status': status, 'parts': parts,
        })
        print(f'{bid}: {len(b.footprints)} footprints, {b.counts["segment"]} segments, {b.counts["via"]} vias, '
              f'rasters {sum(c["bytes"] for c in copper)/1e6:.2f} MB at {ppm} px/mm', flush=True)

    panel = read_board(ROOT / PANEL_PCB)
    pdx = pdy = None
    slug = {p['slug']: p for p in lock['placements']}
    panel_feats = []
    for fp in panel.footprints:
        ref = fp.props.get('Reference', '')
        q = slug.get(ref[3:]) if ref[:3] in ('PH_', 'PW_') else None
        hole = max((pd.drill for pd in fp.pads), default=0.0)
        panel_feats.append([ref, r2(fp.x), r2(fp.y), r2(hole), q['uid'] if q else ''])
    # The panel board carries no FootprintOriginMm; its offset follows from its Edge.Cuts origin.
    ploops = sorted(outline_loops(panel.edges), key=lambda l: -abs(polygon_area(l)))
    pdx = min(p[0] for p in ploops[0]); pdy = min(p[1] for p in ploops[0])
    for f in panel_feats:
        f[1] = r2(f[1] - pdx); f[2] = r2(f[2] - pdy)

    meshes = json.loads((ROOT / OTHER_INPUTS['meshes']).read_text())
    for m in meshes.values():
        for s in m['solids']:
            s['positions'] = [round(v, 3) for v in s['positions']]
    view = {
        'schema': 'osc-instrument-preview-1',
        'status': ('UNVALIDATED DRAFTS. Routing incomplete on K, JL and JR. Component heights are illustrative display '
                   'values. Not a native KiCad render: KiCad render NOT RUN because the pinned oracle needs Docker, '
                   'which is unavailable in this cloud container. Nothing here is fit, clearance, electrical or '
                   'manufacturing evidence.'),
        'base_commit': base_commit or git('rev-parse', '--short=10', 'HEAD'),
        'extracted_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'),
        'inputs': inputs,
        'excluded': EXCLUDED,
        'families': [{'key': k, 'label': l, 'height_mm': h, 'color': c} for k, l, _, h, c in FAMILIES],
        'part_columns': ['ref', 'value', 'mpn', 'manufacturer', 'footprint', 'x', 'y', 'rot', 'cx', 'cy', 'w', 'h',
                         'side', 'family', 'block', 'panel_uid', 'extent_source', 'dnp'],
        'frame': {'world': 'X = panel x - 159, Y = 149 - panel y, Z = 0 at panel front, +Z toward the viewer',
                  'panel': 'panel x = KiCad x - offset x, panel y = KiCad y - offset y (no mirroring: F.Cu faces the panel and the viewer)'},
        'boards': boards_out,
        'totals': totals,
        'panel': {'file': PANEL_PCB, 'sha256': inputs[PANEL_PCB]['sha256'], 'kicad_to_panel_offset_mm': [pdx, pdy],
                  'footprints': len(panel.footprints), 'features': panel_feats,
                  'width_mm': partition['panel']['width_mm'], 'height_mm': partition['panel']['height_mm'],
                  'thickness_mm': partition['panel']['thickness_mm'], 'corner_radius_mm': partition['panel'].get('corner_radius_mm', 0),
                  'adoption': readiness['panel'].get('adoption', '')},
        'lock': [{k: p.get(k) for k in ('uid', 'ref', 'kind', 'block', 'key', 'label', 'x_mm', 'y_mm', 'rot_deg', 'hole_d_mm', 'led_type', 'component')}
                 for p in lock['placements']],
        'enclosure': partition['enclosure'],
        'checkpoint': {'recorded': checkpoint['recorded'], 'status': checkpoint['status']},
        'selector': json.loads((ROOT / OTHER_INPUTS['selector']).read_text()).get('instances', []),
        'indicator_window_mm': json.loads((ROOT / OTHER_INPUTS['panel_params']).read_text())['indicator_window']['diameter_mm'],
        'meshes': meshes,
    }
    return view, pngs


def stable(view):
    v = dict(view)
    v.pop('extracted_utc', None)
    v.pop('base_commit', None)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='fail if view-data.json or data/*.png differ from a fresh extraction')
    ap.add_argument('--base-commit', default=None)
    args = ap.parse_args()
    if args.check:
        old = json.loads(VIEW.read_text())
        before = {p.name: p.read_bytes() for p in DATA_DIR.glob('*.png')}
        view, pngs = extract(old.get('base_commit'))
        if stable(view) != stable(old) or before != pngs:
            raise SystemExit('FAIL view-data.json or copper rasters are stale; run extract.py')
        print('PASS view data matches a fresh extraction')
        return
    view, pngs = extract(args.base_commit)
    DATA_DIR.mkdir(exist_ok=True)
    for old in DATA_DIR.glob('*.png'):
        if old.name not in pngs:
            old.unlink()
    for name, png in pngs.items():
        (DATA_DIR / name).write_bytes(png)
    VIEW.write_text(json.dumps(view, separators=(',', ':'), ensure_ascii=False) + '\n')
    print(f'wrote {VIEW.relative_to(ROOT)} ({VIEW.stat().st_size/1e6:.2f} MB), totals {view["totals"]}')


if __name__ == '__main__':
    main()
