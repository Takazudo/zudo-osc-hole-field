#!/usr/bin/env python3
"""Add neck-down rule areas around listed IC pad fields and write the board's custom DRC rules.

Source: design/partition/neckdown-areas.json. Each listed IC gets one rule area (nothing
disallowed) on the signal layers covering its pads plus margin_mm; the .kicad_dru lets
Default-class signal copper inside these areas use the neck-down width and clearance.
Runs inside the KiCad image (scripts/kicad/run.sh). Unvalidated draft tooling.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import stable_uuid

ROOT=Path(__file__).resolve().parents[2]
SIGNAL_LAYERS=('F.Cu','In2.Cu','In3.Cu','B.Cu')


def dru_text(area,rule):
    w,c,cls=rule['track_width_mm'],rule['clearance_mm'],rule['netclass']
    return ('(version 1)\n'
            f'# Neck-down at IC pin rows (design/partition/neckdown-areas.json): {rule["reason"]}\n'
            f'(rule "neck-down clearance" (condition "A.NetClass == \'{cls}\' && B.NetClass == \'{cls}\' && (A.intersectsArea(\'{area}\') || B.intersectsArea(\'{area}\'))") (constraint clearance (min {c}mm)))\n'
            f'(rule "neck-down track width" (condition "A.Type == \'track\' && A.intersectsArea(\'{area}\')") (constraint track_width (min {w}mm)))\n')


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('board_id');p.add_argument('--board');a=p.parse_args()
    src=json.loads((ROOT/'design/partition/neckdown-areas.json').read_text());rule=src['rule']
    refs=src['boards'][a.board_id];area=f'pcbgen:{a.board_id}:neckdown'
    path=Path(a.board) if a.board else ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb'
    board=pcbnew.LoadBoard(str(path))
    for z in list(board.Zones()):
        if z.GetIsRuleArea() and z.GetZoneName()==area:board.Remove(z)
    fps={f.GetReference():f for f in board.GetFootprints()}
    missing=[r for r in refs if r not in fps]
    if missing:raise ValueError(f'neck-down refs not on {a.board_id}: {missing}')
    m=pcbnew.FromMM(rule['margin_mm']);lset=pcbnew.LSET()
    for name in SIGNAL_LAYERS:lset.AddLayer(board.GetLayerID(name))
    for ref in refs:
        box=None
        for pad in fps[ref].Pads():
            bb=pad.GetBoundingBox()
            if box is None:box=pcbnew.BOX2I(bb.GetOrigin(),bb.GetSize())
            else:box.Merge(bb)
        x0,y0,x1,y1=box.GetLeft()-m,box.GetTop()-m,box.GetRight()+m,box.GetBottom()+m
        zone=pcbnew.ZONE(board);zone.SetZoneName(area);zone.SetIsRuleArea(True);zone.SetLayerSet(lset)
        for method in ('SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowZoneFills','SetDoNotAllowFootprints'):getattr(zone,method)(False)
        outline=zone.Outline();index=outline.NewOutline()
        for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):outline.Append(pcbnew.VECTOR2I(int(x),int(y)),index)
        zone.SetUuid(pcbnew.KIID(stable_uuid(a.board_id,'neckdown',ref)))
        board.Add(zone)
    pcbnew.SaveBoard(str(path),board)
    (path.parent/f'{path.stem}.kicad_dru').write_text(dru_text(area,rule))
    print(f'{a.board_id}: {len(refs)} neck-down areas ({rule["track_width_mm"]} mm / {rule["clearance_mm"]} mm); unvalidated draft')


if __name__=='__main__':main()
