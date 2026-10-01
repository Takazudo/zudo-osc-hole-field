"""Generate finite inner rail bridges and standard outside-collar via arrays."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks


def apply(source, specification, output, receipt):
    spec = json.loads(specification.read_text())
    if source.resolve() == output.resolve() or hashlib.sha256(source.read_bytes()).hexdigest() != spec['board_sha256']:
        raise ValueError('require separate output and exact native source hash')
    board = pcbnew.LoadBoard(str(source)); before = blocks(source)
    pads = {p.m_Uuid.AsString(): p for f in board.GetFootprints() for p in f.Pads()}
    expected = {'via': set(), 'segment': set(), 'arc': set()}
    for bridge in spec['bridges']:
        pad = pads[bridge['land_uuid']]
        if pad.GetNetname() != bridge['net'] or pad.GetSize().x != pcbnew.FromMM(4) or pad.GetSize().y != pcbnew.FromMM(4):
            raise ValueError('source bridge does not start at exact 4x4 net terminal')
        capture = bridge['finite_main_capture_points_mm']
        paths = [('capture', capture[0], capture[1], bridge['finite_main_capture_width_mm']),
                 ('bridge', bridge['start_mm'], bridge['end_mm'], bridge['width_mm'])]
        for name, start, end, width in paths:
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in start)))
            track.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in end)))
            track.SetLayer(pcbnew.In2_Cu); track.SetWidth(pcbnew.FromMM(width)); track.SetNetCode(pad.GetNetCode())
            uid = stable_uuid(spec['board_id'], 'rail-terminal-exit', bridge['net']+':'+name)
            track.SetUuid(pcbnew.KIID(uid)); board.Add(track); expected['segment'].add(uid)
        for index, at in enumerate(bridge['via_positions_mm']):
            via = pcbnew.PCB_VIA(board); via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in at)))
            via.SetWidth(pcbnew.FromMM(bridge['via_diameter_mm']))
            via.SetDrill(pcbnew.FromMM(bridge['via_drill_mm'])); via.SetNetCode(pad.GetNetCode())
            uid = stable_uuid(spec['board_id'], 'rail-terminal-exit', bridge['net']+':via:'+str(index))
            via.SetUuid(pcbnew.KIID(uid)); board.Add(via); expected['via'].add(uid)
    if any(expected[k] & set(before[k]) for k in expected):
        raise ValueError('a terminal exit already exists')
    pcbnew.SaveBoard(str(output), board); serialized = blocks(output); new = []
    for kind in expected:
        if set(serialized[kind])-set(before[kind]) != expected[kind]:
            raise ValueError('native terminal exit emitted unexpected copper')
        new.extend(serialized[kind][uid] for uid in sorted(expected[kind]))
    text = source.read_text(); end = text.rfind(')')
    output.write_text(text[:end]+''.join('\t'+block+'\n' for block in new)+text[end:])
    after = blocks(output)
    if before['non_copper'] != after['non_copper'] or any(after[k].get(uid) != value for k in expected for uid, value in before[k].items()):
        raise ValueError('terminal exits changed prior owner copper/state')
    receipt.write_text(json.dumps({'status': 'DISPOSABLE; full native/refill and resistance gates pending',
        'source_sha256': spec['board_sha256'], 'candidate_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_specification_sha256': hashlib.sha256(specification.read_bytes()).hexdigest(),
        'prior_owner_and_copper_blocks_preserved': True,
        'new_copper': {k: sorted(v) for k, v in expected.items()}}, indent=2, sort_keys=True)+'\n')
    print('Finite terminal bridges', len(spec['bridges']), 'new standard vias', len(expected['via']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('source', 'specification', 'output', 'receipt'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args(); apply(args.source, args.specification, args.output, args.receipt)
