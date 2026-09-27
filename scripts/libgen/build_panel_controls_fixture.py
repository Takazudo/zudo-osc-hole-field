#!/usr/bin/env python3
"""Build fixed-pitch panel-control DRC fixtures with pinned KiCad pcbnew.

Run through scripts/kicad/run.sh, then use the same oracle's kicad-cli pcb drc.
The selector fixture intentionally retains the drawing-required mounting holes;
its overlap is an unresolved design gate, not a passing assembly.
"""
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'
OUT=ROOT/'.circuit-cache/topic12-fixtures'
OUT.mkdir(parents=True,exist_ok=True)

def board(name,part,centers):
    b=pcbnew.BOARD()
    for n,(x,y) in enumerate(centers,1):
        fp=pcbnew.FootprintLoad(str(LIB),part)
        if fp is None:raise RuntimeError(f'cannot load {part}')
        fp.SetReference(f'X{n}')
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
        b.Add(fp)
    # A generous closed outline avoids conflating mechanical spacing with missing board edge.
    rect=[(0,0),(120,0),(120,100),(0,100)]
    for a,c in zip(rect,rect[1:]+rect[:1]):
        shape=pcbnew.PCB_SHAPE(b);shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]),pcbnew.FromMM(a[1])))
        shape.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]),pcbnew.FromMM(c[1])))
        shape.SetLayer(pcbnew.Edge_Cuts);shape.SetWidth(pcbnew.FromMM(0.05));b.Add(shape)
    pcbnew.SaveBoard(str(OUT/f'{name}.kicad_pcb'),b)

board('pot-pitch','PTV09A-4020F',[(25+17*x,25+14*y) for y in range(2) for x in range(2)])
board('selector-pitch','SRBV160803',[(20+17*x,50) for x in range(5)])
print('pot centers: 17 x 14 mm; selector centers: 17 mm')
print('selector mounting-hole centers across neighbours: 17 - 16 = 1 mm; Ø2 holes overlap 1 mm')
