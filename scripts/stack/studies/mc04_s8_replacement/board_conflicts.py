#!/usr/bin/env python3
"""MC04-S8 premise check (Revisions 4 to 7): the confirmed link-era poses against the footprints at their current board
positions.

The S8 studies use the link gate's obstacle model, which drops the GH headers that the stack links replace
(links.Model.dropped) and treats the parts the gate re-placed at their paper positions. This script places every
confirmed pose (face-aware, as replacement_r7.R7 applies them) and lists every footprint at its current board position
that a pose would overlap on the same face (through-hole parts on both faces), so the conflict with the interim GH
boards stays visible. Writes board-conflicts.json; --check verifies it."""
import argparse
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402
from replacement import sg  # noqa: E402

OUT = D / 'board-conflicts.json'


class Collector:
    def __init__(self):
        self.placed = []

    def add(self, board, face, rect, pads, ref):
        self.placed.append((board, ref, face, rect))


class Live(r7.R7):
    snapshot = None  # MC04-S10: the current gate record


def build():
    s = Live()
    s.prepare()
    col = Collector()
    s.load_done()
    s.apply_confirmed(col)
    s.apply_done(col)
    placed = col.placed
    moved = {(b, ref) for b, ref, _, _ in placed}
    dropped = {b: set(v) for b, v in s.ctx.model.dropped.items()}
    hits = []
    for b, ref, face, rect in placed:
        for f in s.inp['ci']['boards'][b]:
            if (b, f['ref']) in moved or not f['courtyard']:
                continue
            tht = any(p['type'] in ('thru_hole', 'np_thru_hole') for p in f['pads'])
            if f['side'] != face and not tht:
                continue
            if sg.inter(rect, f['courtyard']):
                row = s.rows.get((b, f['ref']))
                kind = ('GH header (dropped by the link model)' if f['ref'] in dropped.get(b, ()) else
                        'gate-displaced part at its board position' if row else
                        'through-hole part (other face)' if f['side'] != face else 'footprint')
                hits.append({'board': b, 'moved': ref, 'face': face, 'overlaps': f['ref'], 'overlapped_face': f['side'], 'kind': kind})
    counts = {}
    for h in hits:
        counts[h['kind']] = counts.get(h['kind'], 0) + 1
    return {'schema_version': 1, 'model': rp.MODEL + ' (poses); checked here against the interim boards',
            'status': 'PREMISE CHECK (MC04-S8 Revisions 4 to 7): no board changed',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/board_conflicts.py',
            'placed_footprints': len(placed), 'counts': dict(sorted(counts.items())),
            'ics_overlapping_gh_headers': sorted({h['moved'] for h in hits if h['kind'].startswith('GH') and h['moved'].startswith('U')}),
            'overlaps': hits}


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
    d = json.loads(text)
    print(d['counts'], d['ics_overlapping_gh_headers'])


if __name__ == '__main__':
    main()
