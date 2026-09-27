#!/usr/bin/env python3
"""Build a four-jack pitch coupon for KiCad 10 DRC; never an order board."""
from __future__ import annotations

import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
FOOTPRINT_DIR = ROOT / "footprints/kicad/zudo-osc-hole-field.pretty"
NAME = "Jack_3.5mm_QingPu_WQP518MA"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_jack_pitch.py <output.kicad_pcb>")
    board = pcbnew.BOARD()
    for index, (x, y) in enumerate(((30, 30), (30, 44), (47, 30), (47, 44)), 1):
        fp = pcbnew.FootprintLoad(str(FOOTPRINT_DIR), NAME)
        if fp is None:
            raise SystemExit("jack footprint unavailable")
        fp.SetParent(board)
        fp.SetFPID(pcbnew.LIB_ID("zudo-osc-hole-field", NAME))
        fp.SetReference(f"J{index}")
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        for pad in fp.Pads():
            net = pcbnew.NETINFO_ITEM(board, f"{fp.GetReference()}_{pad.GetNumber()}")
            board.Add(net)
            pad.SetNet(net)
        board.Add(fp)
    outline = pcbnew.PCB_SHAPE(board)
    outline.SetShape(pcbnew.SHAPE_T_RECT)
    outline.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(18), pcbnew.FromMM(18)))
    outline.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(59), pcbnew.FromMM(56)))
    outline.SetLayer(pcbnew.Edge_Cuts)
    outline.SetWidth(pcbnew.FromMM(0.05))
    board.Add(outline)
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(output), board)
    print("Fixture built: four barrel centres, 14 mm vertical and 17 mm horizontal pitch")


if __name__ == "__main__":
    main()
