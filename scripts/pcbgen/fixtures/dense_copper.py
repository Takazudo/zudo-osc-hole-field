#!/usr/bin/env python3
"""Retain/replay measured dense-fixture copper without rerunning a heuristic router.

The manifest is an explicit routing source, bound to all placed pads and nets.
Replay adds missing items only and rejects any changed existing source copper.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.route_kicad import uid
from scripts.pcbgen.uuid_tools import normalize_file


def geometry(board):
    result = []
    for fp in board.GetFootprints():
        pads = sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y,
                       p.GetSize().x, p.GetSize().y, p.GetShape(), p.GetOrientationDegrees(),
                       p.GetDrillSize().x, p.GetDrillSize().y, p.GetLayerSet().FmtHex(),
                       p.GetNetname()) for p in fp.Pads())
        result.append((fp.GetReference(), fp.GetPosition().x, fp.GetPosition().y,
                       fp.GetLayerName(), fp.GetOrientationDegrees(), pads))
    return hashlib.sha256(json.dumps(sorted(result), separators=(',', ':')).encode()).hexdigest()


def record(item):
    via = isinstance(item, pcbnew.PCB_VIA)
    result = dict(uuid=uid(item), net=item.GetNetname(), kind='via' if via else 'track',
                  start=[item.GetStart().x, item.GetStart().y],
                  end=[item.GetEnd().x, item.GetEnd().y],
                  width=item.GetWidth(pcbnew.F_Cu) if via else item.GetWidth(),
                  layer=item.GetLayerName())
    if via:
        result.update(drill=item.GetDrillValue(), layers=[item.TopLayer(), item.BottomLayer()])
    return result


def replay(board, source, new_ids=None):
    if new_ids is None:
        new_ids = {}
    if geometry(board) != source['placed_pad_geometry_sha256']:
        raise ValueError('retained copper does not match placed pads/nets')
    current = {uid(t): t for t in board.GetTracks()}
    added = 0
    for spec in source['items']:
        if spec['uuid'] in current:
            if record(current[spec['uuid']]) != spec:
                raise ValueError('source copper changed: ' + spec['uuid'])
            continue
        net = board.FindNet(spec['net'])
        if net is None:
            raise ValueError('source net missing: ' + spec['net'])
        if spec['kind'] == 'via':
            item = pcbnew.PCB_VIA(board)
            item.SetViaType(pcbnew.VIATYPE_THROUGH)
            item.SetLayerPair(*spec['layers'])
            item.SetDrill(spec['drill'])
        else:
            item = pcbnew.PCB_TRACK(board)
            item.SetLayer(board.GetLayerID(spec['layer']))
        item.SetStart(pcbnew.VECTOR2I(*spec['start']))
        item.SetEnd(pcbnew.VECTOR2I(*spec['end']))
        item.SetWidth(spec['width'])
        item.SetNet(net)
        item.SetLocked(True)
        new_ids[uid(item)] = spec['uuid']
        board.Add(item)
        added += 1
    return added


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('retain', 'replay'))
    parser.add_argument('board', type=Path)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    if args.stage == 'retain':
        source = dict(schema_version=1, units='KiCad internal nanometres',
                      status='UNVALIDATED DRAFT',
                      placed_pad_geometry_sha256=geometry(board),
                      items=sorted((record(t) for t in board.GetTracks()), key=lambda x: x['uuid']))
        args.manifest.write_text(json.dumps(source, indent=2, sort_keys=True) + '\n')
        print(f'Retained {len(source["items"])} measured copper items')
    else:
        new_ids = {}
        count = replay(board, json.loads(args.manifest.read_text()), new_ids)
        if count:
            pcbnew.SaveBoard(str(args.board), board)
            normalize_file(args.board, 'fixture-route-dense', set(), new_ids, False)
        print(f'Replayed {count} copper items; existing copper preserved')


if __name__ == '__main__':
    main()
