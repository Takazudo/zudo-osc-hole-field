#!/usr/bin/env python3
"""Remove only the routed copper that native DRC reports in conflict with moved parts (MC04-S6 revision 3).

Input: a board, its KiCad DRC JSON, and the moved references. For each short, clearance, hole-clearance or
solder-mask-bridge violation between a pad/footprint of a moved part and a track, arc or via, the copper item is
removed; a track or arc is followed in both directions along same-layer, coincident ends to the nearest via, pad,
T-junction, zone or open end (the stub walk of strip_swapped_stubs.trace_chains), and that chain is removed. Zones,
footprints and unowned non-copper items are never removed. Zones are refilled before saving.

  bash scripts/kicad/run.sh python3 scripts/pcbgen/strip_drc_conflicts.py BOARD DRC.json --moved R1 R2 ... \
      --record out.json [--max-share 0.25] [--dry-run]
The selection of conflict pairs (conflicts()) is pure Python and unit-tested.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.strip_swapped_stubs import trace_chains  # noqa: E402

CONFLICT_TYPES = ('shorting_items', 'clearance', 'hole_clearance', 'solder_mask_bridge')
COPPER = re.compile(r'^(Track|Arc|Via)\b')
OWNER = re.compile(r'\bof (\S+) on\b|\bof (\S+)$')


def conflicts(violations, moved):
    """[(copper uuid, copper kind, moved ref, violation type, description pair)] for DRC violations that pair a
    pad or footprint of a moved part with a track, arc or via."""
    moved = set(moved)
    out = []
    for v in violations:
        if v.get('type') not in CONFLICT_TYPES:
            continue
        items = v.get('items', [])
        refs = set()
        for i in items:
            m = OWNER.search(i.get('description', ''))
            if m:
                refs.add(m.group(1) or m.group(2))
        hit = sorted(refs & moved)
        if not hit:
            continue
        for i in items:
            m = COPPER.match(i.get('description', ''))
            if m and i.get('uuid'):
                out.append((i['uuid'], m.group(1), hit[0], v['type'], [x.get('description', '') for x in items]))
    return out


def share_after(baseline_mm, current_mm, removed_mm):
    """Routed-length loss since the baseline board, as a fraction, once this pass's removal is applied."""
    return (baseline_mm - (current_mm - removed_mm)) / baseline_mm


def main():
    import pcbnew
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('drc')
    ap.add_argument('--moved', nargs='+', required=True)
    ap.add_argument('--record', required=True)
    ap.add_argument('--board-id')
    ap.add_argument('--max-share', type=float, default=0.25)
    ap.add_argument('--baseline-length-mm', type=float, help='routed track length of the pre-S6 board')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    board = pcbnew.LoadBoard(a.board)
    mm = pcbnew.ToMM
    drc = json.loads(Path(a.drc).read_text())
    pairs = conflicts(drc.get('violations', []), a.moved)
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    segs = {}
    for uid, t in tracks.items():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        s, e = t.GetStart(), t.GetEnd()
        segs[uid] = {'a': (s.x, s.y), 'b': (e.x, e.y), 'layer': board.GetLayerName(t.GetLayer()),
                     'net': t.GetNetname(), 'length': mm(t.GetLength())}
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    vias = [t for t in tracks.values() if t.Type() == pcbnew.PCB_VIA_T]
    zones = list(board.Zones())

    def vec(p):
        return pcbnew.VECTOR2I(int(p[0]), int(p[1]))

    def stop_at(p, layer, uid):
        lid = tracks[uid].GetLayer()
        if any(v.HitTest(vec(p)) for v in vias):
            return 'via'
        if any(pad.IsOnLayer(lid) and pad.HitTest(vec(p)) for pad in pads):
            return 'pad'
        net = tracks[uid].GetNetCode()
        if any(z.GetNetCode() == net and z.IsOnLayer(lid) and z.HitTestFilledArea(lid, vec(p)) for z in zones):
            return 'zone (kept)'
        return None

    cleared = {}
    remove = set()
    for uid, kind, ref, vtype, desc in pairs:
        if uid not in tracks:
            continue
        if kind == 'Via':
            items = [uid]
        else:
            chains = trace_chains(segs, [(uid, 'a'), (uid, 'b')], stop_at)
            items = sorted({s for c in chains for s in c['segments']})
        for s in items:
            remove.add(s)
            cleared.setdefault(s, []).append({'moved_ref': ref, 'violation': vtype, 'items': desc})
    total = sum(mm(t.GetLength()) for t in tracks.values() if t.Type() != pcbnew.PCB_VIA_T)
    base = a.baseline_length_mm or total
    removed_len = sum(mm(tracks[s].GetLength()) for s in remove if tracks[s].Type() != pcbnew.PCB_VIA_T)
    rows = []
    for s in sorted(remove):
        t = tracks[s]
        via = t.Type() == pcbnew.PCB_VIA_T
        st, en = (t.GetPosition(), t.GetPosition()) if via else (t.GetStart(), t.GetEnd())
        rows.append({'board': a.board_id or a.board, 'uuid': s, 'kind': 'via' if via else ('arc' if t.Type() == pcbnew.PCB_ARC_T else 'segment'),
                     'net': t.GetNetname(), 'layer': 'F.Cu-B.Cu' if via else board.GetLayerName(t.GetLayer()),
                     'start_mm': [mm(st.x), mm(st.y)], 'end_mm': [mm(en.x), mm(en.y)],
                     'width_mm': mm(t.GetWidth()), 'length_mm': 0.0 if via else mm(t.GetLength()), 'cleared': cleared[s]})
    rec = {'board': a.board_id or a.board, 'conflict_pairs': len(pairs), 'removed_items': len(rows),
           'removed_length_mm': round(removed_len, 4), 'board_routed_length_mm': round(total, 4),
           'baseline_routed_length_mm': round(base, 4), 'removed': rows}
    share = share_after(base, total, removed_len)
    rec['loss_share_after_pass'] = round(share, 6)
    rec['max_share'] = a.max_share
    Path(a.record).write_text(json.dumps(rec, indent=1) + '\n')
    print(f"{rec['board']}: {len(pairs)} conflict pairs, {len(rows)} items, {removed_len:.2f} mm removed this pass, "
          f"loss since baseline {100 * share:.2f} %")
    if share > a.max_share + 1e-12:
        print(f'REFUSED: loss {100 * share:.2f} % exceeds --max-share {100 * a.max_share:.2f} %; board not saved')
        return 2
    if a.dry_run or not rows:
        return 0
    for s in remove:
        board.Remove(tracks[s])
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(a.board)
    return 0


if __name__ == '__main__':
    sys.exit(main())
