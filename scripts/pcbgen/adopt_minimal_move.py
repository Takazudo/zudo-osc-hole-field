#!/usr/bin/env python3
"""Decision E15 minimal-move layout pass on a synced PCB (run through scripts/kicad/run.sh).

apply:     move every free footprint to its netlisted FootprintOriginMm, then remove the tracks and
           vias of the affected nets: every signal net on a moved, swapped, added or re-netted pad,
           and plane-net copper inside the old or new courtyard of a moved package. Zones are
           refilled by the following DRC (--refill-zones) and by the router's prepare step.
drc-clean: remove the tracks and vias that a DRC report names in copper rule errors, and optionally
           the dangling stubs left on ripped nets.
The PCB stays an unvalidated draft; nothing here exports fabrication files.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.geometry.panel_frame import to_kicad

PLANE_NETS = {'AGND', '+12V', '-12V', '+5V', 'GND'}
COPPER_ERRORS = {'clearance', 'shorting_items', 'hole_clearance', 'tracks_crossing', 'copper_edge_clearance',
                 'items_not_allowed', 'solder_mask_bridge', 'hole_to_hole', 'via_diameter', 'track_dangling',
                 'drill_out_of_range', 'annular_width', 'connection_width', 'track_width'}
MARGIN_MM = 0.3


def mm(v):
    return pcbnew.ToMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pose(fp):
    p = fp.GetPosition()
    return (round(mm(p.x), 4), round(mm(p.y), 4), fp.GetLayer(), round(fp.GetOrientationDegrees() % 360, 3),
            str(fp.GetFPID().GetLibItemName()))


def courtyard_box(fp, margin=MARGIN_MM):
    bb = fp.GetBoundingBox(False)
    return (mm(bb.GetLeft()) - margin, mm(bb.GetTop()) - margin, mm(bb.GetRight()) + margin, mm(bb.GetBottom()) + margin)


def inside(box, item):
    bb = item.GetBoundingBox()
    return mm(bb.GetLeft()) < box[2] and box[0] < mm(bb.GetRight()) and mm(bb.GetTop()) < box[3] and box[1] < mm(bb.GetBottom())


def pad_nets(board):
    return {(fp.GetReference(), pad.GetNumber(), i): pad.GetNetname()
            for fp in board.GetFootprints() for i, pad in enumerate(fp.Pads())}


def apply(args):
    old = pcbnew.LoadBoard(str(args.old_pcb))
    board = pcbnew.LoadBoard(str(args.board))
    before = {fp.GetReference(): (pose(fp), courtyard_box(fp)) for fp in old.GetFootprints()}
    old_pads = pad_nets(old)
    moved_to = 0
    for fp in board.GetFootprints():
        if fp.IsLocked() and not fp.HasField('FootprintOriginMm'):
            continue
        origin = fp.GetFieldText('FootprintOriginMm') if fp.HasField('FootprintOriginMm') else ''
        if not origin or fp.GetFieldText('PanelUid'):
            continue
        x, y = (float(v) for v in origin.split(','))
        target = vec(*to_kicad(x, y))
        if fp.GetPosition() != target:
            fp.SetPosition(target)
            moved_to += 1
    moved, boxes = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in before or before[ref][0] != pose(fp):
            moved.append(ref)
            boxes.append(courtyard_box(fp))
            if ref in before:
                boxes.append(before[ref][1])
    moved_set = set(moved)
    new_pads = pad_nets(board)
    renetted = {k for k in new_pads if k in old_pads and old_pads[k] != new_pads[k]}
    signal = set()
    for fp in board.GetFootprints():
        if fp.GetReference() in moved_set:
            signal |= {pad.GetNetname() for pad in fp.Pads()}
    for k in renetted:
        signal |= {old_pads[k], new_pads[k]}
    signal = {n for n in signal if n and n not in PLANE_NETS and not n.startswith('unconnected-')}
    removed_signal = removed_plane = 0
    for item in list(board.GetTracks()):
        net = item.GetNetname()
        if net in signal:
            board.Remove(item); removed_signal += 1
        elif net in PLANE_NETS and any(inside(b, item) for b in boxes):
            board.Remove(item); removed_plane += 1
    pcbnew.SaveBoard(str(args.board), board)
    report = {'board': str(args.board), 'footprints_moved_to_origin': moved_to, 'moved_swapped_or_added': len(moved),
              'renetted_pads': len(renetted), 'affected_signal_nets': sorted(signal),
              'removed_signal_items': removed_signal, 'removed_plane_items_near_moved': removed_plane}
    Path(args.report).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in report.items()}))


def drc_clean(args):
    data = json.loads(Path(args.drc).read_text())
    board = pcbnew.LoadBoard(str(args.board))
    tracks = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
    doomed, kinds = set(), {}
    dangling = set(json.loads(Path(args.dangling_nets).read_text())) | PLANE_NETS if args.dangling_nets else set()
    for v in data.get('violations', []):
        stub = v['type'] in ('track_dangling', 'via_dangling') and dangling
        if not stub and (v['severity'] != 'error' or v['type'] not in COPPER_ERRORS):
            continue
        for it in v['items']:
            # Dangling stubs are removed only on ripped nets, never on untouched copper.
            if it['uuid'] in tracks and (not stub or tracks[it['uuid']].GetNetname() in dangling):
                doomed.add(it['uuid']); kinds[v['type']] = kinds.get(v['type'], 0) + 1
    # A ripped signal net with a dangling stub is a partial remnant: remove the whole net so it reroutes cleanly.
    whole = {tracks[u].GetNetname() for u in doomed if kinds and tracks[u].GetNetname() in dangling - PLANE_NETS}
    whole &= {tracks[it['uuid']].GetNetname() for v in data.get('violations', []) if v['type'] in ('track_dangling', 'via_dangling')
              for it in v['items'] if it['uuid'] in tracks}
    doomed |= {u for u, item in tracks.items() if item.GetNetname() in whole}
    nets = sorted({tracks[u].GetNetname() for u in doomed})
    for u in doomed:
        board.Remove(tracks[u])
    if doomed:
        pcbnew.SaveBoard(str(args.board), board)
    print(json.dumps({'removed': len(doomed), 'by_type': kinds, 'nets': len(nets), 'whole_nets_removed': len(whole)}))
    if args.nets_out:
        prior = json.loads(Path(args.nets_out).read_text()) if Path(args.nets_out).exists() else []
        Path(args.nets_out).write_text(json.dumps(sorted(set(prior) | set(nets)), indent=1) + '\n')


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('apply'); a.add_argument('board', type=Path); a.add_argument('--old-pcb', type=Path, required=True); a.add_argument('--report', required=True)
    d = sub.add_parser('drc-clean'); d.add_argument('board', type=Path); d.add_argument('--drc', required=True); d.add_argument('--nets-out'); d.add_argument('--dangling-nets', help='JSON list of ripped nets whose dangling stubs are removed too')
    args = p.parse_args()
    apply(args) if args.cmd == 'apply' else drc_clean(args)


if __name__ == '__main__':
    main()
