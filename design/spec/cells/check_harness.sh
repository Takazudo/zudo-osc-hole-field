#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
python3 -m design.spec.cells.harness --check
probe=$(mktemp -d "$PWD/.cell-check.XXXXXX")
trap 'python3 - "$probe" <<'"'"'PY'"'"'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
for q in sorted(p.rglob("*"),reverse=True):
 if q.is_file():q.unlink()
 elif q.is_dir():q.rmdir()
p.rmdir()
PY' EXIT
probe_rel=${probe#"$PWD"/}
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$probe_rel/erc.json" schematic/cells/osc-standard-cells.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --output "$probe_rel/cells.net" schematic/cells/osc-standard-cells.kicad_sch
python3 - "$probe" <<'PY'
import json,sys
from pathlib import Path
from design.spec.cells.harness import specification
from scripts.schgen.verify_netlist import verify
p=Path(sys.argv[1]);report=json.loads((p/'erc.json').read_text())
v=[v for sheet in report.get('sheets',[]) for v in sheet.get('violations',[])]
errors=[x for x in v if x.get('severity')=='error']
warnings=[x for x in v if x.get('severity')=='warning']
if errors or len(warnings)!=6 or any(x['type']!='pin_to_pin' for x in warnings):
 raise SystemExit(f'Cell ERC mismatch: {len(errors)} errors, warnings={[x["type"] for x in warnings]}')
differences=verify(*specification(),(p/'cells.net').read_text())
if differences:raise SystemExit('Cell netlist mismatch:\n'+'\n'.join(differences[:30]))
print('PASS: 19 cells, zero ERC errors, six documented LED pin-type warnings, all pin nets match KiCad export')
PY
