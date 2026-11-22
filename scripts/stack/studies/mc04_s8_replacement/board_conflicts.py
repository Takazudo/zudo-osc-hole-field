#!/usr/bin/env python3
"""MC04-S8 Revision 4 premise check: the ruled S8 poses against the footprints at their current board positions.

The S8 studies use the link gate's obstacle model, which drops the GH headers that the stack links replace
(links.Model.dropped) and treats the parts the gate re-placed at their paper positions. This script lists every
footprint at its current board position that a ruled pose would overlap on the same face (through-hole parts on both
faces), so the conflict with the interim GH boards is visible before any pose is applied. Writes board-conflicts.json;
--check verifies it."""
import argparse
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import replacement as rp, replacement_a2 as a2, replacement_a3 as a3, replacement_a4 as a4  # noqa: E401,E402
from replacement import p2, sg  # noqa: E402

OUT = D / 'board-conflicts.json'


def build():
    s = a4.A4(); s.prepare()
    A = {r['ic']: r for r in json.loads(rp.OUT.read_text())['ics']}
    A2 = {r['ic']: r for r in json.loads(a2.OUT.read_text())['ics']}
    A3 = {r['ic']: r for r in json.loads(a3.OUT.read_text())['targets']}
    A4 = {r['ic']: r for r in json.loads(a4.OUT.read_text())['targets']}
    placed = []  # (board, ref, face, rect)
    def add_block(board, ic, members, face0, pose):
        for f, k, rects in s.orients(board, ic, members, face0):
            if (f, k) == (pose['face'], pose.get('turn_deg', 0)):
                for ref, c in rects:
                    placed.append((board, ref, f, p2.shift(c, *pose['shift_mm'])))
    def add_part(board, m):
        fp = s.fps[(board, m['ref'])]; cy = fp['courtyard'] or p2.fp_bbox(fp)
        if m['face'] != fp['side']: cy = rp.mirror(cy, fp['origin'][0])
        placed.append((board, m['ref'], m['face'], p2.shift(cy, m['origin'][0] - fp['origin'][0], m['origin'][1] - fp['origin'][1])))
    for ic in a2.RULED:
        r = A[ic]; add_block(r['board'], ic, s.members[(r['board'], ic)], r['face'], dict(r['chosen'], turn_deg=0))
        for m in r.get('displaced_moves', []): add_part(r['board'], m)
    for ic in ('U4524', 'U1318', 'U4417'):
        r = A2[ic]; add_block(r['board'], ic, s.members[(r['board'], ic)], r['face'], r['chosen'])
        for m in r['chosen'].get('displaced_moves', []): add_part(r['board'], m)
    u = A3['U4647']; add_block('JR', 'U4647', s.members[('JR', 'U4647')], A2['U4647']['face'], u['pose'])
    b = u['blocks_moved'][0]; add_block('JR', 'U4502', b['members'], s.fps[('JR', 'U4502')]['side'], b)
    for m in u['passives_moved']: add_part('JR', m)
    r = A4['U5209']; add_block('K', 'U5209', s.members[('K', 'U5209')], A2['U5209']['face'], r['pose'])
    for m in r['passives_moved']: add_part('K', m)
    moved = {(b, ref) for b, ref, _, _ in placed}
    hits = []
    for b, ref, face, rect in placed:
        for f in s.inp['ci']['boards'][b]:
            if (b, f['ref']) in moved or not f['courtyard']: continue
            tht = any(p['type'] in ('thru_hole', 'np_thru_hole') for p in f['pads'])
            if f['side'] != face and not tht: continue
            if sg.inter(rect, f['courtyard']):
                row = s.rows.get((b, f['ref']))
                kind = ('GH header (dropped by the link model)' if f['ref'] in set(s.ctx.model.dropped.get(b, ())) else
                        'gate-displaced part at its board position' if row else
                        'through-hole part (other face)' if f['side'] != face else 'footprint')
                hits.append({'board': b, 'moved': ref, 'face': face, 'overlaps': f['ref'], 'overlapped_face': f['side'], 'kind': kind})

    counts = {}
    for h in hits:
        counts[h['kind']] = counts.get(h['kind'], 0) + 1
    return {'schema_version': 1, 'status': 'PREMISE CHECK (MC04-S8 Revision 4): no board changed',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/board_conflicts.py',
            'placed_footprints': len(placed), 'counts': dict(sorted(counts.items())), 'overlaps': hits}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('board-conflicts.json is stale')
        print('board-conflicts.json current')
    else:
        OUT.write_text(text)
    print(json.loads(text)['counts'])


if __name__ == '__main__':
    main()
