"""Task D step 3: is there free rear room for RV4508, RV8308 and RV8408 close to their circuit partners, and what
sits on the rear face under each one?

Uses the retained cumulative MC04-R1 scene (412 accepted moves, the other unresolved bodies frozen) through the
capacity census. For each trim, vacates only the trim, rasterises K's rear face, and ranks every raster fit by the
distance from the centroid of its circuit partners (TIA: R_TIA_FIXED and the CURRENT_TO_VOLTAGE amp; E5: the
470 kΩ feed resistor), confirming the nearest with the retained exact predicate (displacement cap excepted, as
in the census; rotation unchanged). No search radius applies: this is a room question, not a move proposal.
Paper only: no tool access, routing or electrical claim."""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402

TRIMS = {'RV8308': ('R8380', 'U8313', 'U8307'), 'RV8408': ('R8480', 'U8413', 'U8407'), 'RV4508': ('R4581',)}
ANCHOR = {'RV8308': ('R8380', 'U8313'), 'RV8408': ('R8480', 'U8413'), 'RV4508': ('R4581',)}


def run():
    scene, _, accepted = cap.scene_and_rows()
    if accepted != 412:
        raise ValueError('cumulative scene changed')
    out = []
    for ref, partners in TRIMS.items():
        fp = scene.bodies[('K', ref)]
        pos = {p: (scene.bodies[('K', p)]['origin'], scene.bodies[('K', p)]['side']) for p in partners}
        ax = sum(pos[p][0][0] for p in ANCHOR[ref]) / len(ANCHOR[ref])
        ay = sum(pos[p][0][1] for p in ANCHOR[ref]) / len(ANCHOR[ref])
        m, org = cap.blocked_mask(scene, 'K', 'B', {('K', ref)})
        cands = sorted(cap.fits(m, org, cap.footprint_box(fp, 0)), key=lambda q: math.hypot(q[0] - ax, q[1] - ay))
        moved = dict(fp, side='B')
        hit, tried = None, 0
        ox, oy = fp['origin']
        for x, y in cands[:400]:
            tried += 1
            v = [h for h in scene._violations('K', moved, x - ox, y - oy, {('K', ref)}) if h != 'displacement cap']
            if not v:
                hit = (x, y)
                break
        row = {'ref': ref, 'current': [fp['origin'], fp['side']], 'partners': {p: [o, s] for p, (o, s) in pos.items()},
               'anchor': [round(ax, 2), round(ay, 2)], 'raster_rear_fits': len(cands), 'exact_checks': tried,
               'current_anchor_mm': round(math.hypot(ox - ax, oy - ay), 2)}
        if hit:
            row.update(rear=[round(hit[0], 3), round(hit[1], 3)], rear_anchor_mm=round(math.hypot(hit[0] - ax, hit[1] - ay), 2),
                       rear_shift_mm=round(math.hypot(hit[0] - ox, hit[1] - oy), 2),
                       rear_partner_mm={p: round(math.dist(hit, o), 2) for p, (o, s) in pos.items()})
        rs = cap.r1.rectangles(fp)
        box = [min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs)]
        row['current_courtyard'] = [round(v, 3) for v in box]
        # Rear-face items under the trim's own courtyard: what a through-board adjustment axis would have to clear.
        row['rear_items_under_courtyard'] = sorted({'%s %s' % (pl[0], pl[1][1] if isinstance(pl[1], tuple) else pl[1])
                                                    for rect, pl in scene.field.idx[('K', 'B')].items
                                                    if rect[0] < box[2] and rect[2] > box[0] and rect[1] < box[3] and rect[3] > box[1]})
        out.append(row)
    return {'status': 'TASK_D_STEP_3_BLOCKED_TRIM_REAR_ROOM', 'trims': out,
            'scope': 'Courtyard room on the cumulative scene only (other unresolved bodies frozen at their old positions); '
                     'origin distances are locators, not routed lengths; no tool access, height, routing or electrical claim.'}


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
