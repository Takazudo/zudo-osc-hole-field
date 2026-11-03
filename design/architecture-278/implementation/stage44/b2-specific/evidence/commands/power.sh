#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
root=design/architecture-278/implementation/stage44/b2-specific
src=.circuit-cache/stage44-b2-placement-v2
work=.circuit-cache/stage44-b2-power
python3 - <<'PY'
import json,shutil
from pathlib import Path
s=Path('.circuit-cache/stage44-b2-placement-v2');d=Path('.circuit-cache/stage44-b2-power');report=json.loads((s/'drc-placement.json').read_text())
if report['schematic_parity'] or any(r['severity']=='error' for r in report['violations']):raise SystemExit('placement rejected')
d.mkdir()
for p in s.iterdir():
 if p.name=='sheets':shutil.copytree(p,d/p.name)
 elif p.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru') or p.name in ('receipt.json','fp-lib-table','sym-lib-table'):shutil.copy2(p,d/p.name)
PY
bash scripts/kicad/run.sh python3 "$root/audit.py" "$src/osc-jack-left.kicad_pcb" "$src/receipt.json" .circuit-cache/stage44/branches.json
bash scripts/kicad/run.sh python3 "$root/route_power.py" "$src/osc-jack-left.kicad_pcb" "$src/power-proposal.json"
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py "$src/osc-jack-left.kicad_pcb" "$src/power-proposal.json" --output "$work/osc-jack-left.kicad_pcb"
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json --proposal "$src/power-proposal.json"
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all -o "$work/drc-power.json" "$work/osc-jack-left.kicad_pcb"
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json --proposal "$src/power-proposal.json"
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_dump.py "$work/osc-jack-left.kicad_pcb" "$work/dump-power.json"
