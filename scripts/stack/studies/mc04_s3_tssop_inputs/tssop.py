"""Stage 3 what-if for the six input-buffer ICs that the stage 1a draft limits keep off the cable: with a TSSOP-14
body (the project's OPA4197IPWR courtyard, U4341 on K) instead of SOIC-14, how close to its current position can each
one go on its own front board?

For JL and JR, all of that board's unresolved ICs are vacated. The input buffers are placed one at a time, nearest
their current origin, either face, rotations 0-3, each new body blocking later ones with 0.35 mm, in every order;
each placement is confirmed with the retained exact predicate (displacement cap excepted). Decouplers and block
passives are not placed. Room only: no substitution, electrical or routing claim."""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402

BOARDS = {'JL': (('U1216', 'U1416', 'U1417', 'U1518', 'U2119', 'U2218'), ('U1216', 'U1416', 'U1518')),
          'JR': (('U4346', 'U4347', 'U4348', 'U8314', 'U8318', 'U8417'), ('U4346', 'U8314', 'U8417'))}
GAP = 0.35


def turned(fp, t):
    """The TSSOP body rotated t quarter turns about its own origin, as rectangle data the exact predicate accepts."""
    if t == 0:
        return fp
    ox, oy = fp['origin']
    rects = []
    for r in cap.r1.rectangles(fp):
        pts = []
        for x, y in ((r[0], r[1]), (r[2], r[3])):
            dx, dy = x - ox, y - oy
            for _ in range(t):
                dx, dy = -dy, dx
            pts.append((ox + dx, oy + dy))
        rects.append([min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)])
    return rects


def run():
    scene, unresolved, accepted = cap.scene_and_rows()
    if accepted != 412:
        raise ValueError('cumulative scene changed')
    body = scene.bodies[('K', 'U4341')]
    out = {}
    for board, (vac_refs, inputs) in BOARDS.items():
        if sorted(r['ref'] for r in unresolved if r['board'] == board) != sorted(vac_refs):
            raise ValueError('%s unresolved set changed' % board)
        vac = {(board, r) for r in vac_refs}
        base = {f: cap.blocked_mask(scene, board, f, vac) for f in 'FB'}
        orders = []
        for order in itertools.permutations(inputs):
            masks = {f: (m.copy(), o) for f, (m, o) in base.items()}
            rows = []
            for ref in order:
                ox, oy = scene.bodies[(board, ref)]['origin']
                cands = []
                for face in 'FB':
                    m, org = masks[face]
                    for t in range(4):
                        box = cap.footprint_box(body, t)
                        for x, y in cap.fits(m, org, box):
                            cands.append((math.hypot(x - ox, y - oy), face, t, x, y, box))
                cands.sort(key=lambda c: c[0])
                hit = None
                for dist, face, t, x, y, box in cands[:300]:
                    if t == 0:
                        moved = dict(body, side=face)
                        bx, by = body['origin']
                        v = [h for h in scene._violations(board, moved, x - bx, y - by, vac | {('K', 'U4341')})
                             if h != 'displacement cap']
                        if v:
                            continue
                    hit = (dist, face, t, x, y, box)
                    break
                if not hit:
                    rows.append({'ref': ref, 'placed': False})
                    continue
                dist, face, t, x, y, box = hit
                m, org = masks[face]
                i0 = max(0, int((x + box[0] - GAP - org[0]) / cap.STEP)); i1 = int(math.ceil((x + box[2] + GAP - org[0]) / cap.STEP))
                j0 = max(0, int((y + box[1] - GAP - org[1]) / cap.STEP)); j1 = int(math.ceil((y + box[3] + GAP - org[1]) / cap.STEP))
                m[i0:i1 + 1, j0:j1 + 1] = True
                rows.append({'ref': ref, 'placed': True, 'face': face, 'turn': t, 'xy': [round(x, 2), round(y, 2)],
                             'distance_mm': round(dist, 2), 'exact_checked': t == 0})
            orders.append({'order': list(order), 'rows': rows,
                           'max_distance_mm': max((r['distance_mm'] for r in rows if r['placed']), default=None),
                           'all_placed': all(r['placed'] for r in rows)})
        best = min((o for o in orders if o['all_placed']), key=lambda o: o['max_distance_mm'], default=None)
        out[board] = {'vacated': list(vac_refs), 'inputs': list(inputs), 'orders': orders, 'best_order': best}
    return {'status': 'STAGE_3_TSSOP_INPUT_BUFFER_ROOM', 'tssop_body': 'K U4341 (OPA4197IPWR) courtyard', 'boards': out,
            'scope': 'IC courtyard only, greedy, unrotated placements exact-checked and rotated ones raster-only; '
                     'what-if for a part substitution that is not selected; room only.'}


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
