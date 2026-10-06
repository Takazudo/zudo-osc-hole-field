#!/usr/bin/env python3
"""Neck-down rule areas around IC pad fields, plus the board's custom DRC rules.

Source: design/partition/neckdown-areas.json ("rule" and per-board IC lists).
  --select  records, for the board, every IC (reference U*) with a pad on an open
            Default-class net (native connectivity), replacing that board's list.
  default   draws one rule area (nothing disallowed) per listed IC over its pads plus
            margin_mm on the signal layers, and writes <board>.kicad_dru so Default-class
            signal copper inside may use the neck-down width and clearance.
Runs inside the KiCad image (scripts/kicad/run.sh). Unvalidated draft tooling.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.grid_dump import dump

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'design/partition/neckdown-areas.json'
SIGNAL_LAYERS=('F.Cu','In2.Cu','In3.Cu','B.Cu')


def dru_text(area,rule):
    w,c,cls=rule['track_width_mm'],rule['clearance_mm'],rule['netclass']
    return ('(version 1)\n'
            f'# Neck-down at IC pin rows (design/partition/neckdown-areas.json): {rule["reason"]}\n'
            f'(rule "neck-down clearance" (condition "A.NetClass == \'{cls}\' && B.NetClass == \'{cls}\' && (A.intersectsArea(\'{area}\') || B.intersectsArea(\'{area}\'))") (constraint clearance (min {c}mm)))\n'
            f'(rule "neck-down track width" (condition "A.Type == \'track\' && A.intersectsArea(\'{area}\')") (constraint track_width (min {w}mm)))\n')


def select(board,path,netclass):
    """ICs with a pad on a net that has open pad islands and belongs to the neck-down net class."""
    # Net classes come from the project file; without it every net reads as Default.
    if not path.with_suffix('.kicad_pro').exists():raise ValueError(f'{path.with_suffix(".kicad_pro")} missing: net classes unknown')
    state=dump(str(path));klass={n.GetNetname():n.GetNetClassName() for n in board.GetNetsByName().values()}
    open_nets={n for n in state['islands'] if klass.get(n)==netclass}
    return sorted({p['ref'] for p in state['pads'] if p['net'] in open_nets and p['ref'].startswith('U')},key=lambda r:(len(r),r))


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('board_id');p.add_argument('--board')
    p.add_argument('--select',action='store_true',help='record the ICs with open-net pads for this board, then stop');a=p.parse_args()
    src=json.loads(SOURCE.read_text());rule=src['rule']
    path=Path(a.board) if a.board else ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb'
    board=pcbnew.LoadBoard(str(path))
    if a.select:
        src['boards'][a.board_id]=select(board,path,rule['netclass'])
        SOURCE.write_text(json.dumps(src,indent=1)+'\n')
        print(f"{a.board_id}: {len(src['boards'][a.board_id])} ICs with open-net pads recorded in {SOURCE.relative_to(ROOT)}");return
    refs=src['boards'][a.board_id];area=f'pcbgen:{a.board_id}:neckdown'
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
