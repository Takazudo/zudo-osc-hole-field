#!/usr/bin/env python3
"""Move and lock a synthetic free footprint for placer owner-preservation test."""
import sys
from pathlib import Path
import pcbnew
board_path=Path(sys.argv[1]);board=pcbnew.LoadBoard(str(board_path))
fp=next(fp for fp in board.GetFootprints() if fp.GetReference()=='R105')
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(114.5),pcbnew.FromMM(120)))
fp.SetLocked(True)
pcbnew.SaveBoard(str(board_path),board)
