#!/usr/bin/env python3
"""Put the swapped packages at their netlisted floorplan pose (FootprintOriginMm, BoardSide, KiCadOrientationDeg).

sync.py keeps an existing free footprint where it is when its library footprint changes, and place.py never moves
an anchored part, so after the MC04 swap the six TSSOP-14 bodies still sit at the old SOIC-14 origins. This moves
only the listed references, the same way sync.py places a new footprint, and records each move.

  bash scripts/kicad/run.sh python3 scripts/pcbgen/pose_swapped.py <board-id> --refs U1 ... --record out.json [--dry-run]
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.geometry.panel_frame import to_kicad  # noqa: E402
from scripts.pcbgen.definition import load_definition  # noqa: E402
from scripts.pcbgen.netlist import read_netlist  # noqa: E402
from scripts.pcbgen.pose import source_pose  # noqa: E402


def main():
    import pcbnew
    ap = argparse.ArgumentParser()
    ap.add_argument('board_id')
    ap.add_argument('--refs', nargs='+', default=[])
    ap.add_argument('--all-offset', action='store_true',
                    help='every free footprint whose position, side or angle differs from its netlisted floorplan pose')
    ap.add_argument('--board', type=Path, help='board path (default boards/<id>/<id>.kicad_pcb)')
    ap.add_argument('--list', help='write the selected references, one per line, and do not move anything')
    ap.add_argument('--record', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    definition = load_definition(ROOT / 'design/boards' / f'{a.board_id}.json')
    board_path = a.board or ROOT / 'boards' / a.board_id / f'{a.board_id}.kicad_pcb'
    components, _ = read_netlist(ROOT / definition.netlist)
    by_ref = {c.ref: c for c in components}
    board = pcbnew.LoadBoard(str(board_path))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    mm = pcbnew.ToMM
    refs = list(a.refs)
    if a.all_offset:
        for ref, fp in sorted(fps.items()):
            fields = dict(by_ref[ref].fields) if ref in by_ref else {}
            origin = fields.get('FootprintOriginMm')
            if not origin or fp.IsLocked() or ref in refs:
                continue
            x, y = (float(v) for v in origin.split(','))
            tx, ty = to_kicad(x, y)
            pose = source_pose(fields)
            off = (abs(mm(fp.GetPosition().x) - tx) > 1e-4 or abs(mm(fp.GetPosition().y) - ty) > 1e-4 or
                   (pose.side is not None and board.GetLayerName(fp.GetLayer()) != pose.side) or
                   (pose.orientation is not None and abs(((fp.GetOrientationDegrees() - pose.orientation) + 180) % 360 - 180) > 1e-6))
            if off:
                refs.append(ref)
    if a.list:
        Path(a.list).write_text('\n'.join(refs) + '\n')
        print(len(refs), 'selected')
        return 0
    rows = []
    for ref in refs:
        fields = dict(by_ref[ref].fields)
        x, y = (float(v) for v in fields['FootprintOriginMm'].split(','))
        pose = source_pose(fields)
        fp = fps[ref]
        before = {'x_mm': mm(fp.GetPosition().x), 'y_mm': mm(fp.GetPosition().y),
                  'side': board.GetLayerName(fp.GetLayer()), 'rotation_deg': fp.GetOrientationDegrees()}
        tx, ty = to_kicad(x, y)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(tx), pcbnew.FromMM(ty)))
        if pose.side is not None:
            target = board.GetLayerID(pose.side)
            if fp.GetLayer() != target:
                fp.Flip(fp.GetPosition(), False)
        if pose.orientation is not None:
            fp.SetOrientationDegrees(pose.orientation)
        after = {'x_mm': mm(fp.GetPosition().x), 'y_mm': mm(fp.GetPosition().y),
                 'side': board.GetLayerName(fp.GetLayer()), 'rotation_deg': fp.GetOrientationDegrees()}
        rows.append({'ref': ref, 'footprint': fp.GetFPIDAsString(), 'source_origin_mm': [x, y],
                     'before_kicad': before, 'after_kicad': after,
                     'moved_mm': round(math.hypot(after['x_mm'] - before['x_mm'], after['y_mm'] - before['y_mm']), 4)})
    Path(a.record).write_text(json.dumps({'board': a.board_id, 'moves': rows}, indent=1) + '\n')
    for r in rows:
        print(r['ref'], r['footprint'].split(':')[-1], r['before_kicad'], '->', r['after_kicad'], 'moved', r['moved_mm'], 'mm')
    if not a.dry_run:
        board.Save(str(board_path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
