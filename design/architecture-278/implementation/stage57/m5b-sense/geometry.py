"""Native geometry of the Stage57 target net on the Stage53 disposable board (oracle only).

Writes the source pad, every target-net pad/track/via, and the nearest source-to-target
distances. Usage (through scripts/kicad/run.sh): geometry.py BOARD OUTPUT
"""
from pathlib import Path
import hashlib, json, math, sys
import pcbnew
NET = 'X1B64D2A971AB89E1AF19'


def mm(v): return round(v / 1e6, 6)


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def main(board_path, output):
    raw = Path(board_path).read_bytes()
    board = pcbnew.LoadBoard(str(board_path))
    pads, tracks = [], []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != NET: continue
            pos = p.GetPosition(); bb = p.GetBoundingBox()
            pads.append(dict(ref=f.GetReference(), pin=p.GetNumber(), at_mm=[mm(pos.x), mm(pos.y)],
                             layers=[board.GetLayerName(l) for l in p.GetLayerSet().CuStack()],
                             bbox_mm=[mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
                             footprint=f.GetFPIDAsString(), side=board.GetLayerName(f.GetLayer())))
    for t in board.GetTracks():
        if t.GetNetname() != NET: continue
        if t.GetClass() == 'PCB_VIA':
            pos = t.GetPosition()
            tracks.append(dict(kind='via', uuid=t.m_Uuid.AsString(), at_mm=[mm(pos.x), mm(pos.y)],
                               diameter_mm=mm(t.GetWidth(pcbnew.F_Cu)), drill_mm=mm(t.GetDrillValue())))
        else:
            s, e = t.GetStart(), t.GetEnd()
            tracks.append(dict(kind='segment', uuid=t.m_Uuid.AsString(), layer=t.GetLayerName(),
                               start_mm=[mm(s.x), mm(s.y)], end_mm=[mm(e.x), mm(e.y)], width_mm=mm(t.GetWidth())))
    pads.sort(key=lambda r: (r['ref'], r['pin'])); tracks.sort(key=lambda r: r['uuid'])
    out = dict(board_sha256=hashlib.sha256(raw).hexdigest(), kicad_version=pcbnew.GetBuildVersion(), net=NET,
               pads=pads, copper=tracks)
    Path(output).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(pads=len(pads), copper=len(tracks))))


if __name__ == '__main__':
    main(*sys.argv[1:3])
