#!/usr/bin/env python3
"""MC04-S8 Revisions 6 and 7: block members on the other face than their IC, at the confirmed link-era poses.

Every confirmed block (the ten confirmed poses and the U4502 block moved with U4647) is placed face-aware: each member
keeps its face relative to its IC and flips with the block. This check lifts one block at a time and verifies that each
of its members, on its own face at the recorded pose, meets no obstacle in the link-era model with every other confirmed
pose in place. Writes member-faces.json; --check verifies it.
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
from replacement import p2  # noqa: E402

OUT = D / 'member-faces.json'


def build():
    s = r7.R7()
    s.prepare()
    rows = []
    for board, ic, members, face0, pose in s.confirmed_blocks():
        f = s.build_field(skip={(board, ic)})
        rects = dict(((fc, k), rr) for fc, k, rr in s.orients(board, ic, members, face0))[(pose['face'], pose.get('turn_deg', 0))]
        dx, dy = pose['shift_mm']
        out = []
        for ref, c in rects:
            face = s.mf(board, ref, pose['face'])
            why = f.blocked(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [])
            other = s.fps[(board, ref)]['side'] != s.fps[(board, ic)]['side']
            if other or why:
                out.append({'ref': ref, 'other_face': other, 'face': face, 'blocked_by': why})
        rows.append({'board': board, 'ic': ic, 'pose': {k: pose[k] for k in ('face', 'origin', 'moved_mm') if k in pose},
                     'other_face_members': [x for x in out if x['other_face']], 'blocked_members': [x for x in out if x['blocked_by']],
                     'all_clear': not any(x['blocked_by'] for x in out)})
    return {'schema_version': 1, 'model': rp.MODEL, 'face_aware': True,
            'status': 'CHECK (MC04-S8 Revisions 6 and 7): every member of each confirmed block on its own face at the recorded pose',
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
        print(r['ic'], r['all_clear'], len(r['other_face_members']), r['blocked_members'])


if __name__ == '__main__':
    main()
