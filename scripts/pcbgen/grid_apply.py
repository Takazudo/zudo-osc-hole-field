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
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE

def apply(board_path,proposal,output):
    if hashlib.sha256(Path(board_path).read_bytes()).hexdigest()!=proposal['board_sha256']:raise ValueError('proposal was made for a different board')
    removed=set(proposal['removed_uuids']);source=Path(board_path)
    if removed:
        # Drop ripped copper as text: removing SWIG-owned tracks corrupts later pcbnew calls.
        text=source.read_text();keep=[];last=0;dropped=0
        for start,end in top_level_spans(text):
            block=text[start:end]
            if block.startswith(('(segment','(via')):
                match=UUID_RE.search(block)
                if match and match[1] in removed:
                    keep.append(text[last:start]);last=end;dropped+=1
        keep.append(text[last:])
        if dropped!=len(removed):raise ValueError(f'ripped copper not found: {dropped}/{len(removed)}')
        source=Path(output).with_suffix('.ripped.kicad_pcb');source.write_text(''.join(keep))
    board=pcbnew.LoadBoard(str(source))
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
    if source!=Path(board_path):source.unlink()

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('proposal',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve()==a.board.resolve():raise ValueError('write a candidate copy, not the source board')
    apply(a.board,json.loads(a.proposal.read_text()),a.output)
    print('wrote',a.output)
if __name__=='__main__':main()
