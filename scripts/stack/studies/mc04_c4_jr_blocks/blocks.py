"""Task C step 4: can each unplaced JR IC move to K with its functional block, and what does it cost in links?

A block is the IC, its declared decouplers and its one-hop passive/diode signal neighbours that sit on JR, as in the
MC02 analog remedy brief (panel jacks and other ICs stay).
On K the IC goes nearest its original x/y (JR and K share the stack x/y frame) and each member nearest the IC, with
earlier parts blocking later ones. Signals: a non-power net crosses JR-K when it
has members on both boards; the change in crossing nets is counted for each block and for all six. Room and count
only: no electrical review, no allocation, no canonical write."""
import argparse
import collections
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402

ICS = ('U4346', 'U4347', 'U4348', 'U8314', 'U8318', 'U8417')
POWER = {'+12V', '-12V', '+5V', 'AGND', 'GND', 'DGND'}


def run():
    scene, unresolved, _ = cap.scene_and_rows()
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    pp = {x['ref']: x for x in part['physical_packages']}
    net_refs, ref_nets = collections.defaultdict(set), collections.defaultdict(set)
    for u in part['package_units']:
        for n in (u.get('pins') or {}).values():
            if n and n not in POWER:
                net_refs[n].add(u['ref']); ref_nets[u['ref']].add(n)
    board_of = {}
    for (b, ref), fp in scene.bodies.items():
        if ref not in scene.model.dropped.get(b, ()):
            board_of.setdefault(ref, set()).add(b)

    def block(ic):
        g = {ic} | {x['ref'] for x in part['physical_packages'] if x.get('decouples_ref') == ic}
        for n in ref_nets[ic]:
            for r in net_refs[n]:
                if r != ic and r in pp and r[0] in 'RCD' and not pp[r]['courtyard'].get('through_hole'):
                    g.add(r)
        return sorted(r for r in g if board_of.get(r) == {'JR'})

    def crossing(moved):
        n_cross = 0
        for n, refs in net_refs.items():
            boards = set()
            for r in refs:
                for b in board_of.get(r, ()):
                    boards.add('K' if (b == 'JR' and r in moved) else b)
            n_cross += {'JR', 'K'} <= boards
        return n_cross

    base = crossing(set())
    masks = {f: cap.blocked_mask(scene, 'K', f, set()) for f in 'FB'}
    masks = {f: (m.copy(), o) for f, (m, o) in masks.items()}
    def put(m, o, box, target):
        pts = cap.fits(m, o, box)
        if not pts:
            return None
        x, y = min(pts, key=lambda p: math.hypot(p[0] - target[0], p[1] - target[1]))
        i0 = max(0, int((x + box[0] - 0.35 - o[0]) / cap.STEP)); i1 = int(math.ceil((x + box[2] + 0.35 - o[0]) / cap.STEP))
        j0 = max(0, int((y + box[1] - 0.35 - o[1]) / cap.STEP)); j1 = int(math.ceil((y + box[3] + 0.35 - o[1]) / cap.STEP))
        m[i0:i1 + 1, j0:j1 + 1] = True
        return x, y

    rows, moved_all = [], set()
    for ic in ICS:
        members = block(ic)
        fp = scene.bodies[('JR', ic)]
        ox, oy = fp['origin']
        orig_span = max(math.hypot(scene.bodies[('JR', r)]['origin'][0] - ox, scene.bodies[('JR', r)]['origin'][1] - oy)
                        for r in members)
        row = {'ic': ic, 'members': members, 'crossing_change_alone': crossing(set(members)) - base,
               'original_max_member_distance_mm': round(orig_span, 2)}
        best = None
        for f in 'BF':
            m, o = masks[f]
            pts = cap.fits(m, o, cap.footprint_box(fp, 0))
            if pts:
                x, y = min(pts, key=lambda p: math.hypot(p[0] - ox, p[1] - oy))
                d = math.hypot(x - ox, y - oy)
                if best is None or d < best[0]:
                    best = (d, f)
        if best is None:
            row['k_face'] = None; rows.append(row); continue
        f = best[1]
        m, o = masks[f]
        x, y = put(m, o, cap.footprint_box(fp, 0), (ox, oy))
        dist, missing = [], []
        for r in members:
            if r == ic:
                continue
            q = put(m, o, cap.footprint_box(scene.bodies[('JR', r)], 0), (x, y))
            if q is None:
                missing.append(r)
            else:
                dist.append(math.hypot(q[0] - x, q[1] - y))
        row.update(k_face=f, ic_k_origin=[round(x, 2), round(y, 2)], ic_shift_mm=round(best[0], 2),
                   members_without_room=missing, max_member_distance_mm=round(max(dist), 2) if dist else 0.0,
                   mean_member_distance_mm=round(sum(dist) / len(dist), 2) if dist else 0.0)
        if not missing:
            moved_all |= set(members)
        rows.append(row)
    jr_links = [l for l in json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())['links']
                if not l.get('gone') and l['front_board'] == 'JR']
    return {'status': 'TASK_C_STEP_4_JR_BLOCKS_TO_K', 'blocks': rows,
            'crossing_nets_before': base, 'crossing_change_all_placed_blocks': crossing(moved_all) - base,
            'jr_link_unused_positions': sum(l['unused'] for l in jr_links),
            'scope': ('Greedy raster packing on K (0.25 mm, obstacles as the capacity census, 0.35 mm between placed '
                      'parts, no rotation, not exact-confirmed): the IC nearest its original x/y on the better face, then each '
                      'member nearest the IC on the same face; one-hop block boundary from the remedy brief, not a '
                      'stability model; crossing-net count is not an allocation (class and ground rules not applied). '
                      'Room and count only.')}


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
