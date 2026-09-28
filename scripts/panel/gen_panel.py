#!/usr/bin/env python3
"""Generate the fixed-hole front-panel PCB and a restylable baseline artwork.

Run through the pinned KiCad 10 oracle. The placement lock is the only source
of physical hole/window centres. Imported R21 art supplies labels and styling.
"""
from __future__ import annotations

from collections import Counter
import argparse
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import pcbnew

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.geometry.panel_frame import to_kicad  # noqa: E402
from scripts.pcbgen.geometry import outline_segments  # noqa: E402
from scripts.pcbgen.uuid_tools import stable_uuid, normalize_file, top_level_spans, UUID_RE  # noqa: E402

BOARD_ID = 'panel'
BOARD_PATH = ROOT / 'boards/panel/panel.kicad_pcb'
MANIFEST_PATH = ROOT / 'boards/panel/reports/generated-manifest.json'
REPORT_PATH = ROOT / 'boards/panel/reports/regeneration.json'
ART_PATH = ROOT / '.circuit-cache/panel/art.svg'
LOCK_PATH = ROOT / 'design/grid/placements.lock.json'
PARAMS_PATH = ROOT / 'design/panel/panel-params.json'
GOLD = '#c6a35e'
DIM = '#695935'
WHITE = '#edece5'


def mm(value):
    return pcbnew.FromMM(float(value))


def vec(x, y):
    a, b = to_kicad(x, y)
    return pcbnew.VECTOR2I(mm(a), mm(b))


def item_uuid(item):
    return item.m_Uuid.AsString()


def tag(element):
    return element.tag.rsplit('}', 1)[-1]


def transform_point(x, y, transform):
    scale, tx, ty = transform
    return x * scale + tx, y * scale + ty


def nested_transform(raw, parent):
    scale, tx, ty = parent
    if not raw:
        return parent
    for command, args in re.findall(r'(translate|scale)\(([^)]+)\)', raw):
        values = [float(x) for x in re.findall(r'-?(?:\d+(?:\.\d*)?|\.\d+)', args)]
        if command == 'translate':
            tx += scale * values[0]
            ty += scale * (values[1] if len(values) > 1 else 0)
        else:
            if len(values) != 1:
                raise ValueError('artwork permits uniform scale only')
            scale *= values[0]
    return scale, tx, ty


def svg_path_segments(data):
    tokens = re.findall(r'[MLHVZmlhvz]|-?(?:\d+(?:\.\d*)?|\.\d+)', data)
    i = 0
    command = None
    x = y = 0.0
    first = None
    result = []
    while i < len(tokens):
        if re.fullmatch('[MLHVZmlhvz]', tokens[i]):
            command = tokens[i]
            i += 1
        if command in ('M', 'L', 'm', 'l'):
            nx = float(tokens[i]); ny = float(tokens[i + 1]); i += 2
            if command.islower():
                nx += x; ny += y
            if command in ('M', 'm'):
                first = (nx, ny)
                command = 'L' if command == 'M' else 'l'
            elif (nx, ny) != (x, y):
                result.append(((x, y), (nx, ny)))
            x, y = nx, ny
        elif command in ('H', 'h', 'V', 'v'):
            n = float(tokens[i]); i += 1
            nx, ny = (x + n if command == 'h' else n, y) if command.lower() == 'h' else (x, y + n if command == 'v' else n)
            if (nx, ny) != (x, y):
                result.append(((x, y), (nx, ny)))
            x, y = nx, ny
        elif command in ('Z', 'z'):
            if first and (x, y) != first:
                result.append(((x, y), first))
            command = None
            first = None
        else:
            raise ValueError(f'unsupported SVG path command: {command!r}')
    return result


def artwork_items():
    root = ET.parse(ART_PATH).getroot()
    out = []
    counters = Counter()

    def add(kind, attrs, color, width):
        if color == WHITE:
            layers = ('F.SilkS',)
        elif color == GOLD:
            layers = ('F.Cu', 'F.Mask')
        elif color == DIM:
            layers = ('F.Cu',)
        else:
            return
        for layer in layers:
            counters[(kind, layer)] += 1
            key = f'{kind}:{layer}:{counters[(kind, layer)]:04d}'
            out.append({'key': key, 'kind': kind, 'layer': layer,
                        'width_mm': max(float(width), .15 if layer == 'F.SilkS' else .20), **attrs})

    def visit(node, transform=(1.0, 0.0, 0.0), stroke=None, color=None):
        t = nested_transform(node.get('transform'), transform)
        c = node.get('color', color)
        s = node.get('stroke', stroke)
        if s == 'currentColor':
            s = c
        kind = tag(node)
        if kind == 'text':
            value = ''.join(node.itertext()).strip()
            if value and not value.startswith('R21 ·') and not value.startswith('INTEGER CELLS /'):
                x, y = transform_point(float(node.get('x')), float(node.get('y')), t)
                height = max(1.0, float(node.get('font-size', '1.0')) * t[0])
                # These three jack label strings touch the exposed bracket in
                # the stock stroke font. Lower only them 0.4 mm, inside the
                # 14 mm row pitch; the fixed hole and window centres do not move.
                if 'label-jack' in node.get('class', '') and value in {'1V/OCT', 'TRIGGER', 'BROWN'}:
                    y += .4
                add('text', {'x_mm': round(x, 4), 'y_mm': round(y - height * .42, 4),
                             'text': value, 'height_mm': round(height, 4),
                             'anchor': node.get('text-anchor', 'middle'),
                             'font_width_ratio': .62},
                    node.get('fill'), max(.15, height * .13))
        elif kind == 'line':
            x1, y1 = transform_point(float(node.get('x1')), float(node.get('y1')), t)
            x2, y2 = transform_point(float(node.get('x2')), float(node.get('y2')), t)
            if abs(x1 - x2) + abs(y1 - y2) > 1e-6:
                add('line', {'start_mm': [round(x1, 4), round(y1, 4)],
                             'end_mm': [round(x2, 4), round(y2, 4)]},
                    s, float(node.get('stroke-width', '.2')) * t[0])
        elif kind == 'path':
            for start, end in svg_path_segments(node.get('d', '')):
                x1, y1 = transform_point(*start, t)
                x2, y2 = transform_point(*end, t)
                add('line', {'start_mm': [round(x1, 4), round(y1, 4)],
                             'end_mm': [round(x2, 4), round(y2, 4)]},
                    s, float(node.get('stroke-width', '.2')) * t[0])
        elif kind == 'circle':
            if s in (WHITE, GOLD, DIM) and node.get('fill') != 'transparent':
                cx, cy = transform_point(float(node.get('cx')), float(node.get('cy')), t)
                radius = float(node.get('r')) * t[0]
                add('circle', {'center_mm': [round(cx, 4), round(cy, 4)],
                               'radius_mm': round(radius, 4)},
                    s, float(node.get('stroke-width', '.2')) * t[0])
        elif kind == 'rect' and node.get('stroke') in (WHITE, GOLD, DIM):
            x = float(node.get('x')); y = float(node.get('y'))
            w = float(node.get('width')); h = float(node.get('height'))
            radius = float(node.get('rx', '0'))
            if radius:
                pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                pieces = outline_segments(pts, radius)
                for piece in pieces:
                    if piece[0] == 'line':
                        a = transform_point(*piece[1], t); b = transform_point(*piece[2], t)
                        add('line', {'start_mm': [round(a[0], 4), round(a[1], 4)],
                                     'end_mm': [round(b[0], 4), round(b[1], 4)]},
                            node.get('stroke'), float(node.get('stroke-width', '.2')) * t[0])
                    else:
                        a, m, b = [transform_point(*point, t) for point in piece[1:]]
                        add('arc', {'start_mm': [round(a[0], 4), round(a[1], 4)],
                                    'mid_mm': [round(m[0], 4), round(m[1], 4)],
                                    'end_mm': [round(b[0], 4), round(b[1], 4)]},
                            node.get('stroke'), float(node.get('stroke-width', '.2')) * t[0])
            else:
                for a, b in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                             ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
                    a = transform_point(*a, t); b = transform_point(*b, t)
                    add('line', {'start_mm': [round(a[0], 4), round(a[1], 4)],
                                 'end_mm': [round(b[0], 4), round(b[1], 4)]},
                        s, float(node.get('stroke-width', '.2')) * t[0])
        for child in node:
            visit(child, t, s, c)

    visit(root)
    return out


def spec_fingerprint(item):
    return {k: v for k, v in item.items() if k != 'key'}


def current_fingerprint(item):
    layer = pcbnew.LayerName(item.GetLayer())
    if isinstance(item, pcbnew.PCB_TEXT):
        pos = item.GetPosition()
        return {'kind': 'text', 'layer': layer, 'text': item.GetText(),
                'x': pos.x, 'y': pos.y, 'size_x': item.GetTextWidth(),
                'size_y': item.GetTextHeight(), 'width': item.GetTextThickness(),
                'align': item.GetHorizJustify()}
    start = item.GetStart(); end = item.GetEnd()
    result = {'kind': 'shape', 'layer': layer, 'shape': int(item.GetShape()),
              'start': [start.x, start.y], 'end': [end.x, end.y],
              'width': item.GetWidth()}
    if item.GetShape() == pcbnew.SHAPE_T_ARC:
        mid = item.GetArcMid(); result['mid'] = [mid.x, mid.y]
    return result


def add_art(board, spec):
    layer = {'F.SilkS': pcbnew.F_SilkS, 'F.Cu': pcbnew.F_Cu,
             'F.Mask': pcbnew.F_Mask}[spec['layer']]
    if spec['kind'] == 'text':
        item = pcbnew.PCB_TEXT(board)
        item.SetText(spec['text'])
        item.SetLayer(layer)
        height = spec['height_mm']
        item.SetTextSize(pcbnew.VECTOR2I(mm(height * spec['font_width_ratio']), mm(height)))
        item.SetTextThickness(mm(spec['width_mm']))
        item.SetPosition(vec(spec['x_mm'], spec['y_mm']))
        aligns = {'start': pcbnew.GR_TEXT_H_ALIGN_LEFT,
                  'middle': pcbnew.GR_TEXT_H_ALIGN_CENTER,
                  'end': pcbnew.GR_TEXT_H_ALIGN_RIGHT}
        item.SetHorizJustify(aligns[spec['anchor']])
    else:
        item = pcbnew.PCB_SHAPE(board)
        item.SetLayer(layer)
        item.SetWidth(mm(spec['width_mm']))
        if spec['kind'] == 'line':
            item.SetShape(pcbnew.SHAPE_T_SEGMENT)
            item.SetStart(vec(*spec['start_mm']))
            item.SetEnd(vec(*spec['end_mm']))
        elif spec['kind'] == 'arc':
            item.SetShape(pcbnew.SHAPE_T_ARC)
            item.SetArcGeometry(vec(*spec['start_mm']), vec(*spec['mid_mm']),
                                vec(*spec['end_mm']))
        else:
            item.SetShape(pcbnew.SHAPE_T_CIRCLE)
            x, y = spec['center_mm']; r = spec['radius_mm']
            item.SetStart(vec(x, y)); item.SetEnd(vec(x + r, y))
    board.Add(item)
    return item


def make_feature(board, placement, params, existing=None):
    is_window = placement['kind'] == 'led'
    ref = ('PW_' if is_window else 'PH_') + placement['slug']
    fp = existing or pcbnew.FOOTPRINT(board)
    if existing is None:
        fp.SetReference(ref)
    fp.SetValue('Optical window PROPOSAL' if is_window else 'Panel hole PROPOSAL')
    fp.SetBoardOnly(True)
    fp.SetExcludedFromBOM(True)
    fp.SetExcludedFromPosFiles(True)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    if existing is None:
        pad = pcbnew.PAD(fp)
        pad.SetNumber('')
        fp.Add(pad)
    else:
        pads = list(fp.Pads())
        if len(pads) != 1:
            raise ValueError(f'{ref}: expected exactly one pad')
        pad = pads[0]
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Mask); layers.AddLayer(pcbnew.B_Mask)
    pad.SetLayerSet(layers)
    diameter = params['indicator_window']['diameter_mm'] if is_window else placement['hole_d_mm']
    pad.SetSize(pcbnew.VECTOR2I(mm(diameter), mm(diameter)))
    if is_window:
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    else:
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(diameter), mm(diameter)))
    fp.SetPosition(vec(placement['x_mm'], placement['y_mm']))
    # pcbnew's SetPosition on a PAD uses board coordinates, even when the pad
    # belongs to a footprint. Saving then writes a zero local pad offset.
    pad.SetPosition(fp.GetPosition())
    fp.SetLocked(True)
    if existing is None:
        board.Add(fp)
    return fp


def sort_generated_blocks(path, drawing_ids):
    text = path.read_text()
    slots = []
    for a, b in top_level_spans(text):
        block = text[a:b]
        if block.startswith(('(gr_line', '(gr_arc', '(gr_circle', '(gr_text')):
            match = UUID_RE.search(block)
            if match and match[1] in drawing_ids:
                slots.append((a, b, match[1], block))
    ordered = sorted(slots, key=lambda row: row[2])
    for (a, b, _, _), (_, _, _, block) in reversed(list(zip(slots, ordered))):
        text = text[:a] + block + text[b:]
    path.write_text(text)


def ensure_stackup(path, params):
    """Persist the proposal colors and thickness for KiCad's 3D renderer."""
    core = params['thickness_mm'] - .09  # two 35 um Cu and two 10 um masks
    stackup = ('(stackup\n'
               '\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))\n'
               '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))\n'
               '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))\n'
               '\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))\n'
               f'\t\t\t(layer "dielectric 1" (type "core") (thickness {core:g}) (material "FR4"))\n'
               '\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))\n'
               '\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))\n'
               '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))\n'
               '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))\n'
               '\t\t\t(copper_finish "ENIG")\n'
               '\t\t\t(dielectric_constraints no)\n'
               '\t\t)')
    text = path.read_text()
    setup = next((a for a, b in top_level_spans(text) if text[a:b].startswith('(setup')), None)
    if setup is None:
        raise ValueError('board setup form missing')
    end = next(b for a, b in top_level_spans(text) if a == setup)
    body = text[setup:end]
    previous = next(((a, b) for a, b in top_level_spans(body)
                     if body[a:b].startswith('(stackup')), None)
    if previous:
        a, b = previous
        body = body[:a] + stackup + body[b:]
    else:
        body = body.replace('(setup\n', '(setup\n\t\t' + stackup + '\n', 1)
    path.write_text(text[:setup] + body + text[end:])


def normalize_group_members(path, new_ids):
    text = path.read_text()
    for temporary, stable in new_ids.items():
        if temporary != stable:
            text = text.replace(temporary, stable)
    path.write_text(text)


def generate(board_path=BOARD_PATH, manifest_path=MANIFEST_PATH, report_path=REPORT_PATH):
    params = json.loads(PARAMS_PATH.read_text())
    lock = json.loads(LOCK_PATH.read_text())
    placements = lock['placements']
    if (params['width_mm'], params['height_mm']) != (lock['frame']['panel_width_mm'], lock['frame']['panel_height_mm']):
        raise ValueError('panel dimensions drift from placement lock')
    if len(placements) != 438 or len({p['uid'] for p in placements}) != 438:
        raise ValueError('placement lock must have 438 unique features')
    art = artwork_items()
    if not any(x['kind'] == 'text' and x['text'] == params['artwork']['title'] for x in art):
        raise ValueError('new project title missing from art')
    if any('PLAYGROUND' in x.get('text', '') or x.get('text', '').startswith('R21 ·') for x in art):
        raise ValueError('forbidden handoff title/review annotation in art')

    board_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    created = not board_path.exists()
    board = pcbnew.BOARD() if created else pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise ValueError(f'KiCad could not load panel board: {board_path}')
    board.SetFileName(str(board_path))
    board.GetDesignSettings().SetBoardThickness(mm(params['thickness_mm']))
    board.GetDesignSettings().SetCopperLayerCount(2)
    old_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'art': {}}
    old_art = old_manifest.get('art', {})
    old_drawings = {item_uuid(x): x for x in board.GetDrawings()}
    group_names = ('panelgen:geometry', 'panelgen:art:F.Cu',
                   'panelgen:art:F.Mask', 'panelgen:art:F.SilkS')
    groups = {group.GetName(): group for group in board.Groups()
              if group.GetName() in group_names}
    for name, group in groups.items():
        if item_uuid(group) != stable_uuid(BOARD_ID, 'group', name):
            raise ValueError(f'cannot take over unowned group {name}')
        for member in list(group.GetItems()):
            group.RemoveItem(member)
    group_items = {name: [] for name in group_names}
    edited = []
    preserved_owner = sum(1 for x in board.GetDrawings() if item_uuid(x) not in {v['uuid'] for v in old_art.values()})
    desired_ids = {stable_uuid(BOARD_ID, 'art', item['key']) for item in art}
    retained_art = set()
    for key, record in old_art.items():
        old = old_drawings.get(record['uuid'])
        if old is None:
            continue
        if current_fingerprint(old) != record['fingerprint']:
            edited.append(key)
            continue
        current = next((spec for spec in art if spec['key'] == key), None)
        if current is not None and spec_fingerprint(current) == record.get('source'):
            retained_art.add(key)
            continue
        board.Remove(old)
    owned_refs = set()
    new_ids = {}
    for placement in placements:
        ref = ('PW_' if placement['kind'] == 'led' else 'PH_') + placement['slug']
        owned_refs.add(ref)
    existing_features = {}
    for fp in list(board.GetFootprints()):
        ref = fp.GetReference()
        if ref in owned_refs:
            if item_uuid(fp) != stable_uuid(BOARD_ID, 'footprint:' + ref, 'root'):
                raise ValueError(f'cannot take over unowned panel feature {ref}')
            existing_features[ref] = fp
    for placement in placements:
        ref = ('PW_' if placement['kind'] == 'led' else 'PH_') + placement['slug']
        fp = make_feature(board, placement, params, existing_features.get(ref))
        new_ids[item_uuid(fp)] = stable_uuid(BOARD_ID, 'footprint:' + ref, 'root')
        group_items['panelgen:geometry'].append(fp)
    # Replace the managed outline, keeping any owner-drawn Edge.Cuts item.
    old_outline = {item_uuid(item): item for item in board.GetDrawings()
                   if item_uuid(item) in {stable_uuid(BOARD_ID, 'outline', str(i))
                                          for i in range(8)}}
    outline = [(0, 0), (params['width_mm'], 0),
               (params['width_mm'], params['height_mm']), (0, params['height_mm'])]
    for i, segment in enumerate(outline_segments(outline, params['corner_radius_mm'])):
        stable = stable_uuid(BOARD_ID, 'outline', str(i))
        shape = old_outline.get(stable) or pcbnew.PCB_SHAPE(board)
        shape.SetLayer(pcbnew.Edge_Cuts)
        shape.SetWidth(mm(.05))
        if segment[0] == 'line':
            shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
            shape.SetStart(vec(*segment[1])); shape.SetEnd(vec(*segment[2]))
        else:
            shape.SetShape(pcbnew.SHAPE_T_ARC)
            shape.SetArcGeometry(*(vec(*point) for point in segment[1:]))
        if stable not in old_outline:
            board.Add(shape)
            new_ids[item_uuid(shape)] = stable
        group_items['panelgen:geometry'].append(shape)
    manifest = {'schema_version': 1, 'source': str(LOCK_PATH.relative_to(ROOT)),
                'art': {}}
    for spec in art:
        key = spec['key']
        uuid = stable_uuid(BOARD_ID, 'art', key)
        prior = old_art.get(key)
        if key in edited:
            manifest['art'][key] = prior
            group_items['panelgen:art:' + spec['layer']].append(old_drawings[uuid])
            continue
        if key in retained_art:
            manifest['art'][key] = prior
            group_items['panelgen:art:' + spec['layer']].append(old_drawings[uuid])
            continue
        created_item = add_art(board, spec)
        new_ids[item_uuid(created_item)] = uuid
        group_items['panelgen:art:' + spec['layer']].append(created_item)
        manifest['art'][key] = {'uuid': uuid, 'fingerprint': current_fingerprint(created_item),
                                'source': spec_fingerprint(spec)}
    for key, record in old_art.items():
        if key not in manifest['art'] and key in edited:
            manifest['art'][key] = record
    for name in group_names:
        group = groups.get(name)
        if group is None:
            group = pcbnew.PCB_GROUP(board)
            group.SetName(name)
            board.Add(group)
            new_ids[item_uuid(group)] = stable_uuid(BOARD_ID, 'group', name)
        for member in group_items[name]:
            group.AddItem(member)
    pcbnew.SaveBoard(str(board_path), board)
    normalize_file(board_path, BOARD_ID, owned_refs, new_ids, created)
    normalize_group_members(board_path, new_ids)
    ensure_stackup(board_path, params)
    sort_generated_blocks(board_path, desired_ids)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    report = {'schema_version': 1, 'status': 'unvalidated draft',
              'holes': sum(p['kind'] != 'led' for p in placements),
              'windows': sum(p['kind'] == 'led' for p in placements),
              'artwork_primitives': len(art),
              'edited_generated_artwork_preserved': edited,
              'unowned_drawing_count_preserved': preserved_owner,
              'title': params['artwork']['title']}
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f"panel: {report['holes']} holes, {report['windows']} optical windows, "
          f"{len(art)} art primitives; {len(edited)} edited art item(s) retained")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--board', type=Path, default=BOARD_PATH)
    parser.add_argument('--manifest', type=Path, default=MANIFEST_PATH)
    parser.add_argument('--report', type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    generate(args.board, args.manifest, args.report)
