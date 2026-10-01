"""Generate exact source-defined rail transfers on a disposable PCB.

Only new copper blocks are serialized into the original source bytes.
Native refill and complete rule/parity/connectivity checks remain mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks


def apply(source, specification, output, receipt):
    if source.resolve() == output.resolve():
        raise ValueError('rail transfer output must be disposable')
    spec = json.loads(specification.read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != spec['board_sha256']:
        raise ValueError('rail proposal belongs to different native board bytes')
    board = pcbnew.LoadBoard(str(source))
    before = blocks(source)
    pads = {p.m_Uuid.AsString(): p for f in board.GetFootprints() for p in f.Pads()}
    expected = {'via': set(), 'segment': set(), 'arc': set()}
    for row in spec['added']:
        pad = pads[row['pad']['uuid']]
        if pad.GetNetname() != row['net']:
            raise ValueError('rail proposal pad/net mismatch')
        origin = pad.GetPosition()
        if max(abs(pcbnew.ToMM(origin.x)-row['points_mm'][0][0]),
               abs(pcbnew.ToMM(origin.y)-row['points_mm'][0][1])) > 1e-6:
            raise ValueError('rail proposal does not start on exact native pad')
        rules = spec['rules_by_net'][row['net']] if 'rules_by_net' in spec else spec['rules']
        allowed_widths = {rules['track_width_mm'], rules.get('local_escape_track_width_mm', rules['track_width_mm'])}
        for exception in spec.get('local_escape_overrides',[]):
            if exception['ref']==row['pad']['ref'] and exception['pad']==row['pad']['pad'] and exception['net']==row['net']:
                allowed_widths.add(exception['width_mm'])
        if row['width_mm'] not in allowed_widths or \
           row['via_diameter_mm'] != rules['via_diameter_mm'] or \
           row['via_drill_mm'] != rules['via_drill_mm']:
            raise ValueError('rail proposal changed source design rule')
        identity = row['net'] + ':' + row['cluster']
        if row['via_xy_mm'] is not None:
            via = pcbnew.PCB_VIA(board)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in row['via_xy_mm'])))
            via.SetWidth(pcbnew.FromMM(row['via_diameter_mm']))
            via.SetDrill(pcbnew.FromMM(row['via_drill_mm']))
            via.SetNetCode(pad.GetNetCode())
            uid = stable_uuid(spec['board_id'], 'rail-transfer-via', identity)
            if uid in before['via']:
                raise ValueError('rail transfer already exists')
            via.SetUuid(pcbnew.KIID(uid)); board.Add(via); expected['via'].add(uid)
        for i, (a, b) in enumerate(zip(row['points_mm'], row['points_mm'][1:])):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in a)))
            track.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in b)))
            width = row.get('segment_widths_mm', [row['width_mm']]*(len(row['points_mm'])-1))[i]
            if width not in allowed_widths:
                raise ValueError('segment width not defined by source')
            track.SetWidth(pcbnew.FromMM(width))
            layer = row.get('segment_layers', [row['layer']]*(len(row['points_mm'])-1))[i]
            if layer not in ('F.Cu', 'B.Cu'):
                raise ValueError('local escape must stay on an explicitly supported outer layer')
            track.SetLayer(board.GetLayerID(layer))
            track.SetNetCode(pad.GetNetCode())
            uid = stable_uuid(spec['board_id'], 'rail-transfer-track', identity+':'+str(i))
            track.SetUuid(pcbnew.KIID(uid)); board.Add(track); expected['segment'].add(uid)
    pcbnew.SaveBoard(str(output), board)
    serialized = blocks(output)
    new = []
    for kind in ('via', 'segment', 'arc'):
        actual = set(serialized[kind]) - set(before[kind])
        if actual != expected[kind]:
            raise ValueError('native serializer emitted unexpected '+kind)
        new.extend(serialized[kind][uid] for uid in sorted(actual))
    text = source.read_text(); end = text.rfind(')')
    output.write_text(text[:end]+''.join('\t'+item+'\n' for item in new)+text[end:])
    after = blocks(output)
    if after['non_copper'] != before['non_copper']:
        raise ValueError('rail transfer changed non-copper owner blocks')
    for kind in ('via', 'segment', 'arc'):
        if any(after[kind].get(uid) != value for uid, value in before[kind].items()):
            raise ValueError('rail transfer changed previous copper')
    receipt.write_text(json.dumps({'status': 'DISPOSABLE DRAFT; native promotion gates pending',
        'source_sha256': spec['board_sha256'],
        'candidate_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'specification_sha256': hashlib.sha256(specification.read_bytes()).hexdigest(),
        'all_prior_copper_and_owner_blocks_preserved': True,
        'new_copper': {kind: sorted(ids) for kind, ids in expected.items()}}, indent=2, sort_keys=True)+'\n')
    print('Explicit rail transfers:', len(spec['added']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('source', 'specification', 'output', 'receipt'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    apply(args.source, args.specification, args.output, args.receipt)
