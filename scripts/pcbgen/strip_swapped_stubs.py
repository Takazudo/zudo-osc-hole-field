#!/usr/bin/env python3
"""Remove only the routed copper stubs attached to the pads of swapped packages (MC04-S6 revision 1).

For each track end on a pad of a listed package, follow the connected track segments (same layer, exactly
coincident ends) to the first via, pad of another part, T-junction or open end, and remove that chain. Vias,
zones, other tracks and unowned items are never removed. A chain longer than --max-mm or one that touches a
zone of its net is not removed; it is reported instead and the run fails.

Run through the pinned oracle:
  bash scripts/kicad/run.sh python3 scripts/pcbgen/strip_swapped_stubs.py BOARD.kicad_pcb --refs U1 U2 \
      --record out.json [--board-id ID] [--dry-run]
The chain walk (trace_chains) is pure Python and is unit-tested without KiCad (test_strip_swapped_stubs.py).
"""
import argparse
import json
import math
import sys
from collections import defaultdict

MAX_CHAIN_MM = 20.0


def trace_chains(segments, starts, stop_at):
    """Pure chain walk.

    segments: {id: {'a': (x, y), 'b': (x, y), 'layer': str, 'net': str, 'length': float}}
    starts:   [(segment id, 'a' | 'b')] - the segment end that lies on a swapped package pad
    stop_at:  callable(point, layer, segment id) -> reason str or None; a reason ends the chain at that point
              ('zone' marks the chain as touching a zone)
    Returns a list of chains: {'start', 'segments', 'length', 'stop', 'stop_point'}."""
    index = defaultdict(set)
    for sid, s in segments.items():
        index[(s['layer'], s['a'])].add(sid)
        index[(s['layer'], s['b'])].add(sid)
    chains = []
    for sid, end in starts:
        chain, length = [], 0.0
        cur, far = sid, ('b' if end == 'a' else 'a')
        stop, point = None, None
        while True:
            seg = segments[cur]
            chain.append(cur)
            length += seg['length']
            point = seg[far]
            stop = stop_at(point, seg['layer'], cur)
            if stop:
                break
            nxt = [n for n in index[(seg['layer'], point)] if n not in chain]
            if not nxt:
                stop = 'open end'
                break
            if len(nxt) > 1:
                stop = 'T-junction'
                break
            cur = nxt[0]
            far = 'b' if segments[cur]['a'] == point else 'a'
        chains.append({'start': [sid, end], 'segments': chain, 'length': length, 'stop': stop,
                       'stop_point': list(point)})
    return chains


def accepted(chains, max_mm=MAX_CHAIN_MM):
    """Chains that may be removed, and the rejected ones with their reason."""
    ok, bad = [], []
    for c in chains:
        if c['stop'] == 'zone':
            bad.append({**c, 'reason': 'touches a zone'})
        elif c['length'] > max_mm + 1e-9:
            bad.append({**c, 'reason': f"longer than {max_mm:g} mm"})
        else:
            ok.append(c)
    return ok, bad


def main():
    import pcbnew  # inside the pinned oracle only
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--refs', nargs='+', required=True)
    ap.add_argument('--record', required=True)
    ap.add_argument('--board-id', default=None)
    ap.add_argument('--max-mm', type=float, default=MAX_CHAIN_MM)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    board = pcbnew.LoadBoard(args.board)
    mm = pcbnew.ToMM
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = [r for r in args.refs if r not in fps]
    if missing:
        raise SystemExit(f'missing packages: {missing}')
    package_pads = [pad for r in args.refs for pad in fps[r].Pads()]
    package_refs = set(args.refs)
    other_pads = [pad for fp in board.GetFootprints() if fp.GetReference() not in package_refs for pad in fp.Pads()]
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    zones = list(board.Zones())
    items, segments = {}, {}
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        uid = t.m_Uuid.AsString()
        items[uid] = t
        a, b = t.GetStart(), t.GetEnd()
        segments[uid] = {'a': (a.x, a.y), 'b': (b.x, b.y), 'layer': board.GetLayerName(t.GetLayer()),
                         'net': t.GetNetname(), 'length': mm(t.GetLength())}

    def vec(p):
        return pcbnew.VECTOR2I(int(p[0]), int(p[1]))

    def on_pad(pads, p, layer_id):
        return next((pad for pad in pads if pad.IsOnLayer(layer_id) and pad.HitTest(vec(p))), None)

    starts = []
    for uid, s in segments.items():
        lid = items[uid].GetLayer()
        for end in ('a', 'b'):
            if on_pad(package_pads, s[end], lid):
                starts.append((uid, end))
                break

    def stop_at(p, layer, uid):
        lid = items[uid].GetLayer()
        net = items[uid].GetNetCode()
        for z in zones:
            if z.GetNetCode() == net and z.IsOnLayer(lid) and z.HitTestFilledArea(lid, vec(p)):
                return 'zone'
        if any(v.HitTest(vec(p)) for v in vias):
            return 'via'
        if on_pad(other_pads, p, lid):
            return 'pad of another part'
        if on_pad(package_pads, p, lid):
            return 'pad of a swapped package'
        return None

    chains = trace_chains(segments, starts, stop_at)
    ok, bad = accepted(chains, args.max_mm)
    remove = sorted({sid for c in ok for sid in c['segments']})
    rows = []
    for sid in remove:
        t, s = items[sid], segments[sid]
        rows.append({'board': args.board_id or args.board, 'uuid': sid, 'net': s['net'], 'layer': s['layer'],
                     'start_mm': [mm(s['a'][0]), mm(s['a'][1])], 'end_mm': [mm(s['b'][0]), mm(s['b'][1])],
                     'width_mm': mm(t.GetWidth()), 'kind': 'arc' if t.Type() == pcbnew.PCB_ARC_T else 'segment'})
    record = {'board': args.board_id or args.board, 'refs': args.refs, 'max_chain_mm': args.max_mm,
              'chains': len(chains), 'removed_items': len(rows), 'removed_length_mm': round(sum(c['length'] for c in ok), 4),
              'nets': sorted({r['net'] for r in rows}),
              'stops': {k: sum(1 for c in ok if c['stop'] == k) for k in sorted({c['stop'] for c in ok})},
              'rejected_chains': [{'start_uuid': c['start'][0], 'net': segments[c['start'][0]]['net'],
                                   'length_mm': round(c['length'], 4), 'reason': c['reason'],
                                   'segments': c['segments']} for c in bad],
              'removed': rows}
    with open(args.record, 'w') as f:
        json.dump(record, f, indent=1)
        f.write('\n')
    print(f"{record['board']}: {len(chains)} chains, {len(rows)} items removed, {len(bad)} rejected")
    if bad:
        print('REJECTED chains (board not saved):', json.dumps(record['rejected_chains'])[:2000])
        return 1
    if not args.dry_run:
        for sid in remove:
            board.Remove(items[sid])
        board.Save(args.board)
    return 0


if __name__ == '__main__':
    sys.exit(main())
