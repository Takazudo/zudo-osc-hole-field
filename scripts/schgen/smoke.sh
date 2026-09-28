#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
bash scripts/schgen/regen.sh
scratch=$(mktemp -d schematic/.schgen-smoke.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
python3 - "$scratch/erc.json" <<'PY'
import json,sys
report=json.load(open(sys.argv[1]))
v=[v for sheet in report['sheets'] for v in sheet.get('violations',[])]
errors=[x for x in v if x['severity']=='error']
warnings=[x for x in v if x['severity']=='warning']
expected={'/H1/':6,'/H2/':6,**{f'/E{i}/':10 for i in range(1,7)},
          **{f'/F{i}/':8 for i in range(1,4)},
          **{f'/B{i}/':2 for i in range(1,3)},
          **{f'/X{i}/':6 for i in range(1,3)},
          **{f'/A{i:02d}/':8 for i in range(1,7)},
          **{f'/M5{suffix}/':14 for suffix in ('A','B')},
          **{f'/M4{suffix}/':14 for suffix in ('A','B')},
          '/W2/':6,'/W1/':6,'/POWER/':12}
actual={sheet['path']:len(sheet.get('violations',[])) for sheet in report['sheets']
        if sheet.get('violations')}
if errors or actual!=expected or any(x['type']!='pin_to_pin' for x in warnings):
 raise SystemExit(f'instrument ERC: {len(errors)} errors, warning counts={actual}; expected={expected}')
print('PASS: instrument ERC zero errors; 240 documented pin-type warnings across captured families')
PY
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - "$scratch/netlist.net" <<'PY'
from dataclasses import replace
from pathlib import Path
import sys
from design.spec.instrument import specification
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import verify,exported_pin_nets
families, instances = specification()
f = families[0]
p = next(p for p in f.parts if p.key=='LF398.1')
actual=exported_pin_nets(Path(sys.argv[1]).read_text())
held=[actual[(designator(p,i),'7')] for i in instances[:2]]
assert held==['/H1/RAW_HELD','/H2/RAW_HELD'],held
changed = replace(f, parts=tuple(replace(p, pins={**p.pins, '8': 'DELIBERATELY_WRONG'}) if q.key==p.key else q for q in f.parts))
differences = verify((changed, *families[1:]), instances, Path(sys.argv[1]).read_text())
assert len(differences) == 2, differences
print('PASS: H1/H2 held outputs remain separate; deliberate hold-node change rejected in both instances')
PY
