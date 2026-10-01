"""Read-only native copper and fitted power-cluster inventory.

The export preserves native outlines and exact pad identities. It provides
geometry for explicit feed proposals; it does not certify a proposed route.
Run with the pinned KiCad oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.definition import load_definition

RAILS = ('+12V', '-12V', '+5V')
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def contours(poly):
    def ring(chain):
        return [[pcbnew.ToMM(chain.CPoint(i).x), pcbnew.ToMM(chain.CPoint(i).y)]
                for i in range(chain.PointCount())]
    return [{'shell': ring(poly.COutline(i)),
             'holes': [ring(poly.CHole(i, h)) for h in range(poly.HoleCount(i))]}
            for i in range(poly.OutlineCount())]


def extract(board_id, source, output, definition_path=None):
    extractor_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    definition_path=definition_path or ROOT / 'design/boards' / (board_id + '.json')
    board = pcbnew.LoadBoard(str(source))
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    definition = load_definition(definition_path)
    if definition.board_id != board_id:
        raise ValueError('geometry definition belongs to another board')
    packages = json.loads((ROOT / 'design/reports/io-partition.json').read_text())['physical_packages']
    fitted = {row['ref'] for row in packages if not row['dnp']}
    omitted = {row['ref'] for row in packages if row['dnp']}
    pads = [(fp, p) for fp in board.GetFootprints() for p in fp.Pads()]
    lands = [(fp, p) for fp, p in pads
             if str(fp.GetFPID().GetLibItemName()) == 'LoadWireTerminal_4x4mm']
    components = {}

    def members(pad):
        uid = pad.m_Uuid.AsString()
        if uid not in components:
            group = {m.m_Uuid.AsString() for m in conn.GetConnectedItems(pad)
                     if m.Type() != pcbnew.PCB_ZONE_T} | {uid}
            for key in group:
                components[key] = group
        return components[uid]

    main = {p.GetNetname(): members(p) for _, p in lands if p.GetNetname() in (*RAILS, 'AGND')}
    clusters = {}
    for fp, pad in pads:
        net = pad.GetNetname()
        if net not in (*RAILS, 'AGND') or fp.GetReference() in omitted or (net != 'AGND' and fp.GetReference() not in fitted):
            continue
        group = members(pad)
        key = min(group)
        row = clusters.setdefault(key, {'id': key, 'net': net,
            'fed': pad.m_Uuid.AsString() in main[net], 'members': sorted(group), 'pads': []})
        at = pad.GetPosition()
        row['pads'].append({'ref': fp.GetReference(), 'pad': pad.GetNumber(),
            'uuid': pad.m_Uuid.AsString(), 'xy_mm': [pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)],
            'layers': [board.GetLayerName(l) for l in LAYERS if pad.IsOnLayer(l)]})

    items = []
    for item in [p for _, p in pads] + list(board.GetTracks()):
        copper = {}; copper_inside = {}; primitives = {}
        for layer in LAYERS:
            if not item.IsOnLayer(layer):
                continue
            poly = pcbnew.SHAPE_POLY_SET()
            item.TransformShapeToPolygon(poly, layer, 0, pcbnew.FromMM(.001), pcbnew.ERROR_OUTSIDE)
            copper[board.GetLayerName(layer)] = contours(poly)
            inside = pcbnew.SHAPE_POLY_SET()
            item.TransformShapeToPolygon(inside, layer, 0, pcbnew.FromMM(.001), pcbnew.ERROR_INSIDE)
            copper_inside[board.GetLayerName(layer)] = contours(inside)
            if isinstance(item, pcbnew.PAD):
                shapes={pcbnew.PAD_SHAPE_CIRCLE:'circle',pcbnew.PAD_SHAPE_OVAL:'oval',
                        pcbnew.PAD_SHAPE_RECT:'rectangle',pcbnew.PAD_SHAPE_ROUNDRECT:'roundrect'}
                shape=shapes.get(item.GetShape(layer),'unsupported')
                at=item.ShapePos(layer);size=item.GetSize(layer);angle=item.GetOrientationDegrees()
                corner=item.GetRoundRectCornerRadius(layer) if shape=='roundrect' else 0
                if shape=='roundrect' and size.x//2-corner<100 and size.y//2-corner<100:
                    shape='circle';size=pcbnew.VECTOR2I(corner*2,corner*2);corner=0
                if item.GetNetname()=='AGND' and (shape=='unsupported' or abs(angle/90-round(angle/90))>1e-9):
                    raise ValueError('AGND analytic envelope has an unsupported native pad primitive')
                primitives[board.GetLayerName(layer)]={'kind':shape,'centre_nm':[at.x,at.y],
                    'half_size_nm':[size.x//2,size.y//2],'quarter_turns':round(angle/90)%4,
                    'corner_radius_nm':corner}
            elif isinstance(item, pcbnew.PCB_VIA):
                at=item.GetPosition()
                radius=item.GetWidth(layer)//2
                if radius<=0:raise ValueError('native plated via has no finite layer annulus')
                primitives[board.GetLayerName(layer)]={'kind':'circle','centre_nm':[at.x,at.y],
                    'half_size_nm':[radius,radius],'quarter_turns':0,'corner_radius_nm':0}
            elif not isinstance(item, pcbnew.PCB_ARC):
                a,b=item.GetStart(),item.GetEnd()
                primitives[board.GetLayerName(layer)]={'kind':'segment','start_nm':[a.x,a.y],
                    'end_nm':[b.x,b.y],'radius_nm':item.GetWidth()//2}
            elif item.GetNetname()=='AGND':
                raise ValueError('AGND analytic envelope does not support a native arc track')
        identity = {'uuid': item.m_Uuid.AsString(), 'net': item.GetNetname(),
                    'copper': copper, 'copper_inside': copper_inside,'analytic_primitives':primitives}
        if isinstance(item, pcbnew.PAD):
            identity.update({'ref': item.GetParentFootprint().GetReference(), 'pad': item.GetNumber(),
                             'xy_mm': [pcbnew.ToMM(item.GetPosition().x), pcbnew.ToMM(item.GetPosition().y)]})
        items.append(identity)

    zones = []
    for zone in board.Zones():
        for layer in LAYERS:
            if not zone.IsOnLayer(layer):
                continue
            if zone.GetIsRuleArea():
                zones.append({'uuid': zone.m_Uuid.AsString(), 'layer': board.GetLayerName(layer),
                    'keepout': True, 'tracks_forbidden': zone.GetDoNotAllowTracks(),
                    'vias_forbidden': zone.GetDoNotAllowVias(), 'contours': contours(zone.Outline())})
            else:
                poly = zone.GetFilledPolysList(layer).CloneDropTriangulation()
                before=poly.Area()/1e12;original=contours(poly)
                poly.Unfracture()
                after=poly.Area()/1e12
                perimeter=sum(math.dist(a,b) for p in original for ring in [p['shell'],*p['holes']]
                              for a,b in zip(ring,ring[1:]+ring[:1]))
                tolerance=perimeter*2e-6+1e-6
                if abs(after-before)>tolerance:raise ValueError('native Unfracture changed filled area outside rounding envelope')
                zones.append({'uuid': zone.m_Uuid.AsString(), 'net': zone.GetNetname(),
                    'layer': board.GetLayerName(layer), 'keepout': False, 'contours': contours(poly),
                    'original_filled_contours':original,
                    'native_unfracture_audit':{'area_before_mm2':before,'area_after_mm2':after,
                        'area_envelope_mm2':tolerance}})

    holes = []
    for _, pad in pads:
        if pad.HasDrilledHole():
            at, size = pad.GetPosition(), pad.GetDrillSize()
            holes.append({'xy_mm': [pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)],
                'uuid': pad.m_Uuid.AsString(), 'net': pad.GetNetname(),
                'plated': pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH,
                'copper_layers': [board.GetLayerName(l) for l in LAYERS if pad.IsOnLayer(l)],
                'size_mm': [pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)],
                'angle_deg': pad.GetOrientationDegrees()})
    for via in board.GetTracks():
        if isinstance(via, pcbnew.PCB_VIA):
            at = via.GetPosition(); d = pcbnew.ToMM(via.GetDrillValue())
            holes.append({'xy_mm': [pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)],
                'uuid': via.m_Uuid.AsString(), 'net': via.GetNetname(), 'plated': True,
                'copper_layers': [board.GetLayerName(l) for l in LAYERS if via.IsOnLayer(l)],
                'size_mm': [d, d], 'angle_deg': 0})
    project = source.with_suffix('.kicad_pro')
    project_rules = json.loads(project.read_text())['board']['design_settings']['rules']
    result = {'schema_version': 1, 'board_id': board_id, 'board': str(source),
        'board_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'extractor_sha256':extractor_hash,'definition_sha256':hashlib.sha256(definition_path.read_bytes()).hexdigest(),
        'project_sha256': hashlib.sha256(project.read_bytes()).hexdigest(),
        'native_project_rules': project_rules,
        'kicad_version': pcbnew.GetBuildVersion(),
        'coordinate_frame': {'name': 'native KiCad millimetres',
                             'source_to_native_translation_mm': [100, 50]},
        'outline_mm': [[x + 100, y + 50] for x, y in definition.outline],
        'routing': definition.routing, 'stackup': definition.stackup,
        'clusters': sorted(clusters.values(), key=lambda x: x['id']),
        'items': items, 'zones': zones, 'holes': holes,
        'main_rail_members': {net: sorted(ids) for net, ids in main.items()},
        'scope': 'Native continuity and geometry export only; no feed/resistance acceptance.'}
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(board_id, 'rail clusters:', len(clusters), 'unfed:', sum(not r['fed'] for r in clusters.values()), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('board_id')
    parser.add_argument('board', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--definition', type=Path)
    args = parser.parse_args()
    extract(args.board_id, args.board, args.output, args.definition)
