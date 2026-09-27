#!/usr/bin/env python3
"""Print an honest KiCad DRC summary; warnings and unrouted nets are separate."""
import json,sys
from collections import Counter
from pathlib import Path
p=Path(sys.argv[1]);j=json.loads(p.read_text())
violations=j.get('violations',[]);by_severity=Counter(x.get('severity','unknown') for x in violations)
parity=j.get('schematic_parity',[]);unconnected=j.get('unconnected_items',[])
print(f"KiCad {j.get('kicad_version','unknown')} draft DRC: errors={by_severity['error']}, warnings={by_severity['warning']}, unconnected={len(unconnected)}, schematic_parity={len(parity)}")
for item in violations+parity:
 print(f"  {item.get('severity','unknown')}: {item.get('type','unknown')}: {item.get('description','')}")
print('DRC is a rule check, not circuit or mechanical qualification.')

if by_severity['error'] or parity:
    raise SystemExit(1)
