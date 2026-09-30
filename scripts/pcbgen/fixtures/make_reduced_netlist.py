#!/usr/bin/env python3
"""Delete one complete component from the generated fixture netlist."""
import re,sys
from pathlib import Path
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);text=src.read_text()
pattern=re.compile(r'\n\t\t\(comp\n.*?\n\t\t\)',re.S)
blocks=pattern.findall(text);target=[b for b in blocks if '(ref "J110")' in b]
if len(target)!=1:raise ValueError('expected one J110 component block')
text=text.replace(target[0],'',1)
# Strip J110 from all net-node lists, preserving all other nodes and nets.
text,n=re.subn(r'\n\t\t\t\(node\n\t\t\t\t\(ref "J110"\).*?\n\t\t\t\)', '', text,flags=re.S)
if n<2:raise ValueError(f'expected two J110 net nodes, saw {n}')
dst.write_text(text)
print('reduced fixture netlist: J110 removed')
