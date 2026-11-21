"""Stage 2 room check: if JR's three output and indicator blocks go to K, is there room on JR for its three
input-buffer ICs (U4346, U8314, U8417), which the stage 1a draft limits keep off the cable?

All six JR unresolved ICs are vacated; only the three input buffers are placed, greedily as in the capacity
census joint first fit (own face first, rotations 0-3, 0.35 mm between placed parts), in each of the six orders.
Every placement is then re-checked with the retained exact predicate (displacement cap excepted). Decouplers and
one-hop passives are not placed here. Room only."""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402

JR_ALL = ('U4346', 'U4347', 'U4348', 'U8314', 'U8318', 'U8417')
INPUTS = ('U4346', 'U8314', 'U8417')


def place(scene, order, base, gap=0.35):
    masks = {f: (m.copy(), o) for f, (m, o) in base.items()}
    placed, unplaced = [], []
    for ref in order:
        fp = scene.bodies[('JR', ref)]
        hit = None
        for face in (fp['side'], 'B' if fp['side'] == 'F' else 'F'):
            m, org = masks[face]
            for t in range(4):
                box = cap.footprint_box(fp, t)
                ox, oy = fp['origin']
                pts = sorted(cap.fits(m, org, box), key=lambda p: math.hypot(p[0] - ox, p[1] - oy))
                for x, y in pts[:50]:
                    moved = dict(fp, side=face)
                    if t == 0 and [h for h in scene._violations('JR', moved, x - ox, y - oy, {('JR', r) for r in JR_ALL})
                                   if h != 'displacement cap']:
                        continue
                    hit = (face, t, box, (x, y))
                    break
                if hit:
                    break
            if hit:
                break
        if not hit:
            unplaced.append(ref)
            continue
        face, t, box, (x, y) = hit
        m, org = masks[face]
        i0 = max(0, int((x + box[0] - gap - org[0]) / cap.STEP)); i1 = int(math.ceil((x + box[2] + gap - org[0]) / cap.STEP))
        j0 = max(0, int((y + box[1] - gap - org[1]) / cap.STEP)); j1 = int(math.ceil((y + box[3] + gap - org[1]) / cap.STEP))
        m[i0:i1 + 1, j0:j1 + 1] = True
        placed.append({'ref': ref, 'face': face, 'turn': t, 'xy': [round(x, 2), round(y, 2)],
                       'shift_mm': round(math.hypot(x - fp['origin'][0], y - fp['origin'][1]), 2),
                       'exact_checked': t == 0})
    return placed, unplaced


def run():
    scene, unresolved, accepted = cap.scene_and_rows()
    if accepted != 412 or sorted(r['ref'] for r in unresolved if r['board'] == 'JR') != sorted(JR_ALL):
        raise ValueError('cumulative scene or JR unresolved set changed')
    vac = {('JR', r) for r in JR_ALL}
    base = {f: cap.blocked_mask(scene, 'JR', f, vac) for f in 'FB'}
    orders = []
    for order in itertools.permutations(INPUTS):
        placed, unplaced = place(scene, order, base)
        orders.append({'order': list(order), 'placed': placed, 'unplaced': unplaced})
    # What-if: the nearest room for a TSSOP-14 courtyard (the project's OPA4197IPWR body U4341) per input buffer,
    # each alone with all six vacated; OPA4196 itself is orderable only in SOIC-14 (SBOS869 addendum).
    tssop = scene.bodies[('K', 'U4341')]
    tssop_near = []
    for ref in INPUTS:
        fp = scene.bodies[('JR', ref)]
        ox, oy = fp['origin']
        best = None
        for face in 'FB':
            m, org = base[face]
            for t in range(4):
                box = cap.footprint_box(tssop, t)
                for x, y in sorted(cap.fits(m, org, box), key=lambda q: math.hypot(q[0] - ox, q[1] - oy))[:1]:
                    dd = math.hypot(x - ox, y - oy)
                    if best is None or dd < best[0]:
                        best = (dd, face, t, x, y)
        tssop_near.append({'ref': ref, 'nearest_mm': round(best[0], 2) if best else None,
                           'face': best[1] if best else None, 'turn': best[2] if best else None})
    soic_near = []
    for ref in INPUTS:
        fp = scene.bodies[('JR', ref)]
        ox, oy = fp['origin']
        best = None
        for face in 'FB':
            m, org = base[face]
            for t in range(4):
                for x, y in sorted(cap.fits(m, org, cap.footprint_box(fp, t)), key=lambda q: math.hypot(q[0] - ox, q[1] - oy))[:1]:
                    dd = math.hypot(x - ox, y - oy)
                    if best is None or dd < best[0]:
                        best = (dd, face, t)
        soic_near.append({'ref': ref, 'nearest_mm': round(best[0], 2) if best else None})
    return {'status': 'STAGE_2_JR_INPUT_BUFFER_ROOM', 'vacated': list(JR_ALL), 'placed_set': list(INPUTS),
            'orders': orders, 'nearest_alone_soic14_raster': soic_near, 'nearest_alone_tssop14_raster_what_if': tssop_near, 'all_three_fit_in_some_order': any(not o['unplaced'] for o in orders),
            'scope': 'IC courtyards only (no decouplers or block passives), greedy raster, exact predicate re-checked '
                     'for unrotated placements; room only, no electrical or routing claim.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
