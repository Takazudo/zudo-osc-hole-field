#!/usr/bin/env python3
"""Build a fixed-pitch toggle/button geometry fixture for KiCad 10 DRC."""
from __future__ import annotations

import sys
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty'
TOGGLE = 'Toggle_Dailywell_2MS_T1B1M2'
BUTTON = 'Button_Omron_B3F_6x6_P6.5x4.5'

def mm(x): return pcbnew.FromMM(x)

def add(board, name, ref, x, y):
    fp = pcbnew.FootprintLoad(str(LIB), name)
    if fp is None: raise SystemExit(f'missing footprint {name}')
    fp.SetParent(board)
    fp.SetFPID(pcbnew.LIB_ID('zudo-osc-hole-field', name))
    fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    for pad in fp.Pads():
        n = pad.GetNumber()
        group = n  # DRC geometry fixture; internal switch shorts are documented in pin-map
        net = pcbnew.NETINFO_ITEM(board, f'{ref}_{group}')
        if board.FindNet(net.GetNetname()) is None: board.Add(net)
        else: net = board.FindNet(net.GetNetname())
        pad.SetNet(net)
    board.Add(fp)

def main():
    if len(sys.argv) != 2: raise SystemExit('usage: check_toggle_button_pitch.py <output.kicad_pcb>')
    b = pcbnew.BOARD()
    for ref,x,y in [('SW1',30,30),('SW2',47,30),('SW3',30,44),('SW4',47,44)]: add(b,TOGGLE,ref,x,y)
    for ref,x,y in [('SW5',65,30),('SW6',65,44)]: add(b,BUTTON,ref,x,y)
    edge = pcbnew.PCB_SHAPE(b)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pcbnew.VECTOR2I(mm(18),mm(18)))
    edge.SetEnd(pcbnew.VECTOR2I(mm(77),mm(56)))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.05))
    b.Add(edge)
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True);pcbnew.SaveBoard(str(out),b)
    print('Fixture: four toggles at 17 x 14 mm pitch; two buttons 14 mm apart')

if __name__ == '__main__': main()
