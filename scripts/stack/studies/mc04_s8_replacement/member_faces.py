#!/usr/bin/env python3
"""MC04-S8 Revision 6 follow-up: block members on the other face than their IC.

The S8 searches (Parts A to A5) place every block member on the block's face. Five blocks have cell-local passives on
the other face (U1415, U5110, U5209, U5210 and the open U8409). This check re-places those members on their own face
(flipped with the block when the block changes face) at each recorded link-era pose, in the link-era model with every
other recorded pose in place, and reports any obstacle they meet. Writes member-faces.json; --check verifies it.
Model: link-era (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402
import replacement_a5 as a5  # noqa: E402
from replacement import p2, r2  # noqa: E402

OUT = D / 'member-faces.json'
REC = rp.ROOT / 'design/stack/geometry/links/link-era-replacements.json'


def flip(f):
    return 'B' if f == 'F' else 'F'


def build():
    s = a5.A5()
    s.prepare()
    rec = json.loads(REC.read_text())
    rows = []
    mixed = {}
    for r in rec['placed']:
        b, ic = r['board'], r['ic']
        face0 = s.fps[(b, ic)]['side']
        other = [m for m in r['block'] if s.fps[(b, m)]['side'] != face0]
        if other:
            mixed[(b, ic)] = (r, other)
    for (b, ic), (r, other) in sorted(mixed.items()):
        f = s.build_field({(b, m) for m in other})
        if ic == 'U5210':  # placed by A5 after the ruled set: apply its run (U8412, U5208 moved; U8409 stays)
            run = next(x for x in json.loads(a5.OUT.read_text())['runs'] if x['found'] and x['targets'] == ['U5210'])
            for ic2, c in sorted(run['poses'].items()):
                if ic2 == ic:
                    continue
                s.place(f, b, ic2, s.set_members(ic2), s.fps[(b, ic2)]['side'], c)
            for ref, c in s.shapes(b, s.set_members('U8409'), s.fps[(b, 'U8409')]['side'], 'U8409')[s.fps[(b, 'U8409')]['side']]:
                f.add(b, s.fps[(b, ref)]['side'], [round(v, 4) for v in c], [], ref)
            for m in run['passives_moved']:
                s.add_part(f, b, m)
        pose = r['pose']
        shift = next((x['shift_mm'] for x in [r.get('pose')] if x and 'shift_mm' in x), None)
        if shift is None:
            o = s.fps[(b, ic)]['origin']
            shift = [round(pose['origin'][0] - o[0], 4), round(pose['origin'][1] - o[1], 4)]
        flipped = pose['face'] != s.fps[(b, ic)]['side']
        rects = dict(((fc, k), rr) for fc, k, rr in s.orients(b, ic, r['block'], s.fps[(b, ic)]['side']))[(pose['face'], pose['turn_deg'])]
        out = []
        for ref, c in rects:
            if ref not in other:
                continue
            true_face = flip(s.fps[(b, ref)]['side']) if flipped else s.fps[(b, ref)]['side']
            cy = [round(v, 4) for v in p2.shift(c, shift[0], shift[1])]
            why = f.blocked(b, true_face, cy, [])
            out.append({'ref': ref, 'recorded_face': pose['face'], 'true_face': true_face, 'blocked_by': why})
        rows.append({'board': b, 'ic': ic, 'pose': pose, 'other_face_members': out,
                     'all_clear': all(x['blocked_by'] is None for x in out)})
    return {'schema_version': 1, 'model': rp.MODEL,
            'status': 'CHECK (MC04-S8 Revision 6 follow-up): other-face block members at the recorded link-era poses',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/member_faces.py', 'blocks': rows}


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
    for r in json.loads(text)['blocks']:
        print(r['ic'], r['all_clear'], [(x['ref'], x['true_face'], x['blocked_by']) for x in r['other_face_members']])


if __name__ == '__main__':
    main()
