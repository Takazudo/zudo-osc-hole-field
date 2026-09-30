#!/usr/bin/env python3
"""Change one terminal net for the update-in-place fault test."""
from pathlib import Path
import sys
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);text=src.read_text()
old='(name "/JACKS/SIGNAL_1")';new='(name "/JACKS/FAULT_NET")'
if text.count(old)!=1:raise ValueError('expected one SIGNAL_1 net declaration')
dst.write_text(text.replace(old,new,1))
