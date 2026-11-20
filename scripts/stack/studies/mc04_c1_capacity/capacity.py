"""Task C first step: is the 26-IC liability local congestion or missing board capacity?

Reconstructs the retained cumulative scene (412 accepted moves, 25 other unresolved bodies frozen,
links/slots/fields/fixings/outline) exactly as MC04-R1 does, rasterises it per board face, and asks, for
each unresolved IC with its declared decouplers held to the same face, where on its own board (either
face, 0/90/180/270 degrees) its complete courtyard fits with no displacement limit. Every raster hit is
confirmed with the retained exact predicate. Room-only: no routing, electrical or adoption claim.
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_r1'))
import study as r1  # noqa: E402

STEP = 0.25


def scene_and_rows():
    spec = json.loads(r1.SPEC.read_text())
    r1.verify_pins(ROOT, spec)
    doc = json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())
    inp = r1.lg.load_inputs(ROOT)
    inp['ci']['boards'], accepted = r1.reconstruct(inp['ci']['boards'], doc['replacement']['footprints'], spec['replacement'])
    model = r1.lg.GateModel(inp, r1.lg.gate_sites(inp))
    ctx = r1.SimpleNamespace(model=model, opts=inp['opts'])
    scene = r1.Scene(ctx, inp, doc['links'])
    unresolved = [row for row in spec['replacement'] if row['new'] is None]
    return scene, unresolved, len(accepted)


def blocked_mask(scene, board, face, exclude):
    """Conservative raster: a cell is blocked if any obstacle, grown link field or outline margin touches it."""
    import numpy as np
    rects = [rect for rect, _ in scene.field.idx[(board, face)].items]
    bx0 = min(r[0] for r in rects) - 5; by0 = min(r[1] for r in rects) - 5
    bx1 = max(r[2] for r in rects) + 5; by1 = max(r[3] for r in rects) + 5
    nx, ny = int(math.ceil((bx1 - bx0) / STEP)), int(math.ceil((by1 - by0) / STEP))
    m = np.zeros((nx, ny), bool)

    def cells(r):
        i0 = max(0, int(math.floor((r[0] - bx0) / STEP))); i1 = min(nx - 1, int(math.floor((r[2] - bx0) / STEP)))
        j0 = max(0, int(math.floor((r[1] - by0) / STEP))); j1 = min(ny - 1, int(math.floor((r[3] - by0) / STEP)))
        return i0, i1, j0, j1

    for rect, payload in scene.field.idx[(board, face)].items:
        if payload[0] == 'body' and payload[1] in exclude:
            continue
        if payload[0] == 'circle':
            cx, cy, rad = payload[1][:3]
            i0, i1, j0, j1 = cells([cx - rad, cy - rad, cx + rad, cy + rad])
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    cell = [bx0 + i * STEP, by0 + j * STEP, bx0 + (i + 1) * STEP, by0 + (j + 1) * STEP]
                    if r1.sg.circle_rect_depth(*payload[1], cell) > 1e-9:
                        m[i, j] = True
            continue
        i0, i1, j0, j1 = cells(rect)
        m[i0:i1 + 1, j0:j1 + 1] = True
    for rect, _ in (scene.field.links.get((board, face)).items if scene.field.links.get((board, face)) else []):
        i0, i1, j0, j1 = cells(r1.sg.grow(rect, scene.field.gap))
        m[i0:i1 + 1, j0:j1 + 1] = True
    for i in range(nx):
        for j in range(ny):
            if not m[i, j]:
                cell = [bx0 + i * STEP, by0 + j * STEP, bx0 + (i + 1) * STEP, by0 + (j + 1) * STEP]
                if not scene.model.inside(board, cell, scene.field.margin):
                    m[i, j] = True
    return m, (bx0, by0)


def footprint_box(fp, turn):
    rs = r1.rectangles(fp)
    ox, oy = fp['origin']
    pts = []
    for r in rs:
        for x, y in ((r[0], r[1]), (r[2], r[3])):
            dx, dy = x - ox, y - oy
            for _ in range(turn):
                dx, dy = -dy, dx
            pts.append((dx, dy))
    return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]


def fits(mask, origin, box):
    """Positions (origin coords) where the box covers only free cells, via a summed-area table."""
    import numpy as np
    w = int(math.ceil((box[2] - box[0]) / STEP)) + 1
    h = int(math.ceil((box[3] - box[1]) / STEP)) + 1
    occ = mask.astype(np.int32)
    sat = np.zeros((occ.shape[0] + 1, occ.shape[1] + 1), np.int32)
    sat[1:, 1:] = occ.cumsum(0).cumsum(1)
    if occ.shape[0] < w or occ.shape[1] < h:
        return []
    s = sat[w:, h:] - sat[:-w, h:] - sat[w:, :-h] + sat[:-w, :-h]
    ii, jj = np.nonzero(s == 0)
    return [(origin[0] + i * STEP - box[0], origin[1] + j * STEP - box[1]) for i, j in zip(ii, jj)]


def nearest_exact(scene, board, fp, face, mask, origin, limit=200):
    """Nearest raster candidate (orientation unchanged) confirmed by the retained exact predicate."""
    ox, oy = fp['origin']
    cands = sorted(fits(mask, origin, footprint_box(fp, 0)), key=lambda p: math.hypot(p[0] - ox, p[1] - oy))
    moved = dict(fp, side=face)
    for x, y in cands[:limit]:
        hits = [h for h in scene._violations(board, moved, x - ox, y - oy, {(board, fp['ref'])}) if h != 'displacement cap']
        if not hits:
            return {'distance_mm': round(math.hypot(x - ox, y - oy), 2), 'origin': [round(x, 3), round(y, 3)]}
    return None


def run():
    scene, unresolved, accepted = scene_and_rows()
    if accepted != 412 or len(unresolved) != 26:
        raise r1.AdmissionError('accepted/unresolved count changed')
    masks, rows = {}, []
    for row in unresolved:
        board, ref = row['board'], row['ref']
        fp = scene.bodies[(board, ref)]
        per_face = {}
        for face in 'FB':
            if (board, face) not in masks:
                masks[(board, face)] = blocked_mask(scene, board, face, set())
            m, org = masks[(board, face)]
            counts = [len(fits(m, org, footprint_box(fp, t))) for t in range(4)]
            per_face[face] = {'raster_positions_by_rotation': counts,
                              'nearest_exact_same_rotation': nearest_exact(scene, board, fp, face, m, org)}
        near = [n['nearest_exact_same_rotation']['distance_mm'] for n in per_face.values() if n['nearest_exact_same_rotation']]
        rows.append({'board': board, 'ref': ref, 'package': row['package'], 'face': fp['side'], 'origin': fp['origin'],
                     'reason': row.get('why') or row.get('reason'), 'fits': per_face,
                     'nearest_mm': min(near) if near else None,
                     'within_retained_25mm': bool(near) and min(near) <= 25.0})
    free = {f'{b}.{f}': round(float((~m).sum()) * STEP * STEP, 1) for (b, f), (m, _) in masks.items()}
    return {'status': 'CAPACITY_CENSUS', 'step_mm': STEP, 'free_area_mm2_conservative': free, 'ics': rows,
            'room_on_own_board': sum(1 for r in rows if r['nearest_mm'] is not None),
            'within_retained_25mm': [r['ref'] for r in rows if r['within_retained_25mm']],
            'scope': 'Room-only. Conservative raster of the retained scene (all other unresolved bodies frozen as '
                     'obstacles, the IC\'s own frozen body still blocking); every reported nearest position is '
                     'confirmed by the retained exact predicate except the displacement cap; decouplers and '
                     'functional neighbours are not moved; not routing, electrical acceptance or adoption.'}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if args.output:
        with args.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
