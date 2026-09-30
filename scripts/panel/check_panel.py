#!/usr/bin/env python3
"""Read the generated KiCad panel and verify every locked physical feature."""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'design/grid/placements.lock.json'


def mm(value):
    return round(pcbnew.ToMM(value), 4)


def check(board_path: Path, output: Path | None = None):
    lock = json.loads(LOCK.read_text())
    board = pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise ValueError(f'could not load {board_path}')
    frame = lock['frame']['kicad_translation_mm']
    expected = {('PW_' if row['kind'] == 'led' else 'PH_') + row['slug']: row
                for row in lock['placements']}
    footprints = list(board.GetFootprints())
    actual = {fp.GetReference(): fp for fp in footprints}
    if len(expected) != 438 or len(actual) != 438 or set(actual) != set(expected):
        raise ValueError(f'feature references differ: expected {len(expected)}, got {len(actual)}')
    holes = windows = 0
    rows = []
    for ref, source in sorted(expected.items()):
        fp = actual[ref]
        pads = list(fp.Pads())
        if len(pads) != 1:
            raise ValueError(f'{ref}: expected one pad')
        pad = pads[0]
        x = mm(fp.GetPosition().x) - frame['x']
        y = mm(fp.GetPosition().y) - frame['y']
        if (round(x, 4), round(y, 4)) != (source['x_mm'], source['y_mm']):
            raise ValueError(f'{ref}: centre drift: {(x, y)} vs {(source["x_mm"], source["y_mm"])}')
        if pad.GetPosition() != fp.GetPosition():
            raise ValueError(f'{ref}: physical pad not centred on footprint')
        if not (fp.IsBoardOnly() and fp.IsExcludedFromBOM() and fp.IsExcludedFromPosFiles()):
            raise ValueError(f'{ref}: not board-only/BOM/POS excluded')
        if source['kind'] == 'led':
            windows += 1
            if pad.HasDrilledHole() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                raise ValueError(f'{ref}: optical window must be an undrilled mask opening')
        else:
            holes += 1
            if not pad.HasDrilledHole() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                raise ValueError(f'{ref}: panel hole must be NPTH')
            if mm(pad.GetDrillSizeX()) != source['hole_d_mm']:
                raise ValueError(f'{ref}: drill diameter drift')
        rows.append({'uid': source['uid'], 'ref': ref, 'kind': source['kind'],
                     'x_mm': source['x_mm'], 'y_mm': source['y_mm'],
                     'diameter_mm': 1.6 if source['kind'] == 'led' else source['hole_d_mm']})
    if (holes, windows) != (324, 114):
        raise ValueError(f'feature counts drift: {holes} holes, {windows} windows')
    groups = {group.GetName(): group for group in board.Groups()}
    expected_groups = {'panelgen:geometry', 'panelgen:art:F.Cu',
                       'panelgen:art:F.Mask', 'panelgen:art:F.SilkS'}
    if not expected_groups <= set(groups):
        raise ValueError(f'missing panel ownership groups: {expected_groups - set(groups)}')
    geometry_ids = {item.m_Uuid.AsString() for item in groups['panelgen:geometry'].GetItems()}
    feature_ids = {fp.m_Uuid.AsString() for fp in footprints}
    if not feature_ids <= geometry_ids:
        raise ValueError('a locked feature is missing from the panel geometry group')
    for layer, layer_id in (('F.Cu', pcbnew.F_Cu), ('F.Mask', pcbnew.F_Mask),
                            ('F.SilkS', pcbnew.F_SilkS)):
        members = list(groups['panelgen:art:' + layer].GetItems())
        if not members or any(item.GetLayer() != layer_id for item in members):
            raise ValueError(f'{layer}: artwork group is empty or contains another layer')
    bbox = board.GetBoardEdgesBoundingBox()
    # KiCad's edge bounding box includes half of the 0.05 mm Edge.Cuts stroke
    # on both sides; the outline centreline is exactly 318 × 298 mm.
    if (mm(bbox.GetWidth()), mm(bbox.GetHeight())) != (318.05, 298.05):
        raise ValueError('panel outline centreline is not 318 × 298 mm')
    text = board_path.read_text()
    if 'OSC PLAYGROUND' in text or 'INTEGER CELLS / FIXED HARDWARE' in text:
        raise ValueError('old title or proof annotation on panel board')
    counts = Counter(row['kind'] for row in lock['placements'])
    report = {'schema_version': 1, 'status': 'PASS - source/board centre parity, unvalidated draft',
              'outline_mm': [318, 298], 'features': len(rows),
              'drilled_holes': holes, 'undrilled_optical_windows': windows,
              'by_kind': dict(sorted(counts.items())), 'rows': rows}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('PASS: 438/438 lock centres, 324 NPTH holes, 114 undrilled mask windows; no extra features')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--board', type=Path, default=ROOT / 'boards/panel/panel.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'boards/panel/reports/feature-table.json')
    args = parser.parse_args()
    check(args.board, args.output)
