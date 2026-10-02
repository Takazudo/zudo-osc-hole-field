#!/usr/bin/env python3
"""Read the generated KiCad panel and verify every locked physical feature."""
from __future__ import annotations

from collections import Counter
import argparse
import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'design/grid/placements.lock.json'
PARAMS = ROOT / 'design/panel/panel-params.json'


def mm(value):
    return round(pcbnew.ToMM(value), 4)


def check_physical_boundary(board, params, frame):
    """Compare native physical features with the independently defined rectangle."""
    dimensions = {}
    for key in ('width_mm', 'height_mm', 'thickness_mm', 'corner_radius_mm'):
        value = params[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0
                or (key != 'corner_radius_mm' and value == 0)):
            raise ValueError(f'invalid panel source {key}')
        dimensions[key] = value
    width, height, radius = (dimensions[k] for k in
                             ('width_mm', 'height_mm', 'corner_radius_mm'))
    if (width, height) != (frame['panel_width_mm'], frame['panel_height_mm']):
        raise ValueError('panel source dimensions differ from locked frame')
    if radius >= min(width, height) / 2:
        raise ValueError('panel corner radius consumes an outline edge')
    if board.GetDesignSettings().GetBoardThickness() != pcbnew.FromMM(dimensions['thickness_mm']):
        raise ValueError('panel thickness differs from source')
    if any(isinstance(item, pcbnew.PCB_VIA) for item in board.GetTracks()):
        raise ValueError('extra drilled via on panel')

    # The source outline may not remove material occupied by any fixed circular
    # hole/window. Signed distance to a rounded rectangle is negative inside.
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            x = pcbnew.ToMM(pad.GetPosition().x) - frame['kicad_translation_mm']['x']
            y = pcbnew.ToMM(pad.GetPosition().y) - frame['kicad_translation_mm']['y']
            qx = abs(x - width / 2) - (width / 2 - radius)
            qy = abs(y - height / 2) - (height / 2 - radius)
            distance = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius
            if distance > -pcbnew.ToMM(pad.GetSize().x) / 2:
                raise ValueError(f'{fp.GetReference()}: panel outline intersects a locked feature')

    def point(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x + frame['kicad_translation_mm']['x']),
                              pcbnew.FromMM(y + frame['kicad_translation_mm']['y']))

    def signature(item):
        if not isinstance(item, pcbnew.PCB_SHAPE):
            raise ValueError('unsupported panel Edge.Cuts item')
        shape = item.GetShape()
        if shape not in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_ARC):
            raise ValueError('panel outline differs from source')
        start, end = item.GetStart(), item.GetEnd()
        endpoints = tuple(sorted(((start.x, start.y), (end.x, end.y))))
        mid = item.GetArcMid() if shape == pcbnew.SHAPE_T_ARC else None
        return (shape, endpoints, (mid.x, mid.y) if mid else None, item.GetWidth())

    expected = []
    corners = ((0, 0, 1, 1), (width, 0, -1, 1),
               (width, height, -1, -1), (0, height, 1, -1))
    if radius:
        # Each rounded corner has tangent points r from the sharp corner and
        # a 45-degree midpoint at r*(1-1/sqrt(2)) along each inward axis.
        delta = radius * (1 - 1 / math.sqrt(2))
        arcs = []
        for x, y, dx, dy in corners:
            arcs.append((point(x, y + dy * radius),
                         point(x + dx * delta, y + dy * delta),
                         point(x + dx * radius, y)))
        # Tangent order is reversed at the top-right and bottom-left corners.
        arcs = [arc if i % 2 == 0 else (arc[2], arc[1], arc[0])
                for i, arc in enumerate(arcs)]
        for i, arc in enumerate(arcs):
            item = pcbnew.PCB_SHAPE(board); item.SetShape(pcbnew.SHAPE_T_ARC)
            item.SetArcGeometry(*arc); item.SetWidth(pcbnew.FromMM(.05))
            expected.append(signature(item))
            item = pcbnew.PCB_SHAPE(board); item.SetShape(pcbnew.SHAPE_T_SEGMENT)
            item.SetStart(arc[2]); item.SetEnd(arcs[(i + 1) % 4][0])
            item.SetWidth(pcbnew.FromMM(.05)); expected.append(signature(item))
    else:
        for i, (x, y, _, _) in enumerate(corners):
            x2, y2, _, _ = corners[(i + 1) % 4]
            item = pcbnew.PCB_SHAPE(board); item.SetShape(pcbnew.SHAPE_T_SEGMENT)
            item.SetStart(point(x, y)); item.SetEnd(point(x2, y2))
            item.SetWidth(pcbnew.FromMM(.05)); expected.append(signature(item))
    graphics = list(board.GetDrawings()) + [item for fp in board.GetFootprints()
                                            for item in fp.GraphicalItems()]
    actual = [signature(item) for item in graphics if item.GetLayer() == pcbnew.Edge_Cuts]
    if Counter(actual) != Counter(expected):
        raise ValueError('panel outline differs from source (segments, arcs, layers or stroke)')


def check(board_path: Path, output: Path | None = None, params_path: Path = PARAMS):
    lock = json.loads(LOCK.read_text())
    params = json.loads(params_path.read_text())
    board = pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise ValueError(f'could not load {board_path}')
    frame = lock['frame']['kicad_translation_mm']
    expected = {('PW_' if row['kind'] == 'led' else 'PH_') + row['slug']: row
                for row in lock['placements']}
    footprints = list(board.GetFootprints())
    actual = {fp.GetReference(): fp for fp in footprints}
    if (len(lock['placements']) != 438 or len(expected) != 438
            or len(footprints) != 438 or len(actual) != 438 or set(actual) != set(expected)):
        raise ValueError(f'feature references differ: expected {len(expected)}, got {len(footprints)} footprints / {len(actual)} unique references')
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
        diameter = (params['indicator_window']['diameter_mm']
                    if source['kind'] == 'led' else source['hole_d_mm'])
        if (isinstance(diameter, bool) or not isinstance(diameter, (int, float))
                or not math.isfinite(diameter) or diameter <= 0):
            raise ValueError(f'{ref}: invalid source diameter')
        expected_size = pcbnew.FromMM(diameter)
        if (pad.GetShape() != pcbnew.PAD_SHAPE_CIRCLE
                or (pad.GetSize().x, pad.GetSize().y) != (expected_size, expected_size)):
            raise ValueError(f'{ref}: circular pad diameter differs from source')
        if set(pad.GetLayerSet().Seq()) != {pcbnew.F_Mask, pcbnew.B_Mask}:
            raise ValueError(f'{ref}: feature must use only both mask layers')
        if source['kind'] == 'led':
            windows += 1
            if pad.HasDrilledHole() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                raise ValueError(f'{ref}: optical window must be an undrilled mask opening')
        else:
            holes += 1
            if not pad.HasDrilledHole() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                raise ValueError(f'{ref}: panel hole must be NPTH')
            if (pad.GetDrillSizeX(), pad.GetDrillSizeY()) != (expected_size, expected_size):
                raise ValueError(f'{ref}: drill diameter drift')
        rows.append({'uid': source['uid'], 'ref': ref, 'kind': source['kind'],
                     'x_mm': source['x_mm'], 'y_mm': source['y_mm'],
                     'diameter_mm': diameter})
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
    check_physical_boundary(board, params, lock['frame'])
    text = board_path.read_text()
    if 'OSC PLAYGROUND' in text or 'INTEGER CELLS / FIXED HARDWARE' in text:
        raise ValueError('old title or proof annotation on panel board')
    counts = Counter(row['kind'] for row in lock['placements'])
    report = {'schema_version': 1, 'status': 'PASS - source/board centre parity, unvalidated draft',
              'outline_mm': [params['width_mm'], params['height_mm']], 'features': len(rows),
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
    parser.add_argument('--params', type=Path, default=PARAMS)
    args = parser.parse_args()
    check(args.board, args.output, args.params)
