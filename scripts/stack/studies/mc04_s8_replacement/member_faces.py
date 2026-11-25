#!/usr/bin/env python3
"""MC04-S8 Revisions 6 to 8: a face-aware check of every placed link-era pose, and of the far options left open.

Every placed block (the confirmed poses, the Revision 7 poses that landed, the Revision 8 acceptance and DS-144), in the current gate record, is placed
face-aware: each member keeps its face relative to its IC and flips with the block. For each block in turn, its
members are checked at the recorded pose against every other placed pose (the block itself lifted), and its displaced
passives against every placed pose including the block. The far options of the blocks left open are checked pairwise
for overlap, since they are alternatives and not one joint solution. Writes member-faces.json; --check verifies it.
Model: link-era (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402
from replacement import p2, sg  # noqa: E402

OUT = D / 'member-faces.json'


def block_rects(s, board, ic, members, face0, pose):
    rects = dict(((fc, k), rr) for fc, k, rr in s.orients(board, ic, members, face0))[(pose['face'], pose.get('turn_deg', 0))]
    return [(ref, s.mf(board, ref, pose['face']), [round(v, 4) for v in p2.shift(c, *pose['shift_mm'])]) for ref, c in rects]


def part_rect(s, board, m):
    fp = s.fps[(board, m['ref'])]
    cy = fp['courtyard'] or p2.fp_bbox(fp)
    if m['face'] != fp['side']:
        cy = rp.mirror(cy, fp['origin'][0])
    return [round(v, 4) for v in p2.shift(cy, m['origin'][0] - fp['origin'][0], m['origin'][1] - fp['origin'][1])]


class Live(r7.R7):
    snapshot = None  # MC04-S10: the current gate record


def build():
    s = Live()
    s.prepare()
    doc = s.load_done()
    blocks = [(b, ic, ms, f0, pose, [], 'confirmed') for b, ic, ms, f0, pose in s.confirmed_blocks()]
    landed = {r['ic'] for r in doc['research'] if r['result'] == 'lands'}
    blocks += [(b, ic, ms, f0, pose, passives, 'Revision 7 re-search' if ic in landed else
                                                       'DS-144 acceptance' if ic in r7.ACCEPTED_DS144 else 'Revision 8 acceptance')
               for b, ic, ms, f0, pose, passives, _ in s.done]
    rows = []
    for board, ic, members, face0, pose, passives, kind in blocks:
        f = s.build_field(extra={(board, m['ref']) for m in passives}, skip={(board, ic)})
        out = []
        for ref, face, rect in block_rects(s, board, ic, members, face0, pose):
            why = f.blocked(board, face, rect, [])
            other = s.fps[(board, ref)]['side'] != s.fps[(board, ic)]['side']
            if other or why:
                out.append({'ref': ref, 'other_face': other, 'face': face, 'blocked_by': why})
        for ref, face, rect in block_rects(s, board, ic, members, face0, pose):
            f.add(board, face, rect, [], ref)
        pas = []
        for m in passives:
            why = f.blocked(board, m['face'], part_rect(s, board, m), [])
            pas.append({'ref': m['ref'], 'face': m['face'], 'blocked_by': why})
            f.add(board, m['face'], part_rect(s, board, m), [], m['ref'])
        rows.append({'board': board, 'ic': ic, 'kind': kind, 'pose': {k: pose[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm') if k in pose},
                     'other_face_members': [x for x in out if x['other_face']], 'blocked_members': [x for x in out if x['blocked_by']],
                     'passives': pas, 'all_clear': not any(x['blocked_by'] for x in out) and not any(x['blocked_by'] for x in pas)})
    # far options of the blocks left open: pairwise overlap (face-aware, at the courtyard growth)
    far = {}
    open_now = {i['ref'] for i in s.items}  # MC04-S10: only the ICs the current gate leaves without a position
    for r in doc['research']:
        if r['result'] != 'lands' and not r7.accepted(r) and r.get('cheapest_option') and r['ic'] in open_now:
            far[r['ic']] = r['cheapest_option']['pose']
    for t, o in doc['joint']['far_poses'].items():
        if o and t in open_now:
            far[t] = o['pose']
    gap = s.build_field().gap
    shapes = {ic: block_rects(s, 'K', ic, s.set_members(ic), s.fps[('K', ic)]['side'], p) for ic, p in far.items()}
    pairs = []
    names = sorted(far)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            hits = sorted({(ra, rb) for ra, fa, xa in shapes[a] for rb, fb, xb in shapes[b] if fa == fb and sg.inter(sg.grow(xa, gap), xb)})
            if hits:
                pairs.append({'a': a, 'b': b, 'overlapping_members': [list(h) for h in hits[:6]], 'count': len(hits)})
    return {'schema_version': 1, 'model': rp.MODEL, 'face_aware': True,
            'status': 'CHECK (MC04-S8 Revisions 6 to 8): every placed link-era pose face-aware; far options of open blocks pairwise',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/member_faces.py', 'blocks': rows,
            'far_options': {ic: {k: p[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')} for ic, p in sorted(far.items())},
            'far_option_overlaps': pairs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('member-faces.json is stale')
        print('member-faces.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    for r in d['blocks']:
        print(r['ic'], r['kind'], r['all_clear'], r['blocked_members'], [p for p in r['passives'] if p['blocked_by']])
    for p in d['far_option_overlaps']:
        print('far overlap', p['a'], p['b'], p['count'])


if __name__ == '__main__':
    main()
