#!/usr/bin/env python3
"""Apply a grid_router.py proposal to a board copy for native checking.

Run inside the KiCad oracle. Writes only --output; the caller must run native
DRC/parity, refill and ratsnest gates before promoting it.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import pcbnew,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.copper_identity import reject_new_uuid_collisions,drop_copper_blocks,load_board_text,board_bytes

def apply(board_path,proposal,output):
    if hashlib.sha256(Path(board_path).read_bytes()).hexdigest()!=proposal['board_sha256']:raise ValueError('proposal was made for a different board')
    removed=set(proposal['removed_uuids']);source=Path(board_path)
    if removed:
        # Drop ripped copper as text: removing SWIG-owned tracks corrupts later pcbnew calls.
        # A removal UUID that names two objects is refused before anything is dropped.
        ripped=drop_copper_blocks(load_board_text(source),removed,'grid_apply removal')
        source=Path(output).with_suffix('.ripped.kicad_pcb');source.write_bytes(board_bytes(ripped))
    # LoadBoard reads <stem>.kicad_pro and SaveBoard writes it next to --output; a ripped copy
    # without its project loads default net classes and overwrites the candidate's project.
    project=Path(output).with_suffix('.kicad_pro');source_project=source.with_suffix('.kicad_pro')
    if source!=Path(board_path):
        if not project.exists():raise ValueError(f'{project} missing: net classes unknown')
        source_project.write_bytes(project.read_bytes())
    board=pcbnew.LoadBoard(str(source))
    reject_new_uuid_collisions((t.m_Uuid.AsString() for t in board.GetTracks()),proposal['copper'])
    for row in proposal['copper']:
        net=board.FindNet(row['net'])
        if net is None:raise ValueError('net absent: '+row['net'])
        if row['kind']=='segment':
            item=pcbnew.PCB_TRACK(board);item.SetStart(pcbnew.VECTOR2I(*row['start_nm']));item.SetEnd(pcbnew.VECTOR2I(*row['end_nm']))
            item.SetWidth(row['width_nm']);item.SetLayer(board.GetLayerID(row['layer']))
        else:
            item=pcbnew.PCB_VIA(board);item.SetViaType(pcbnew.VIATYPE_THROUGH);item.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            item.SetPosition(pcbnew.VECTOR2I(*row['at_nm']));item.SetWidth(row['diameter_nm']);item.SetDrill(row['drill_nm'])
        item.SetNetCode(net.GetNetCode());item.SetUuid(pcbnew.KIID(row['uuid']));board.Add(item)
    pcbnew.SaveBoard(str(output),board)
    if source!=Path(board_path):source.unlink();source_project.unlink()

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('proposal',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve()==a.board.resolve():raise ValueError('write a candidate copy, not the source board')
    apply(a.board,json.loads(a.proposal.read_text()),a.output)
    print('wrote',a.output)
if __name__=='__main__':main()
