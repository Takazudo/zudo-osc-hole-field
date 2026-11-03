#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
root=design/architecture-278/implementation/stage44/b2-specific
src=.circuit-cache/stage44-b2-power
work=.circuit-cache/stage44-b2-anchor
python3 - <<'INNER'
import json,shutil
from pathlib import Path
s=Path('.circuit-cache/stage44-b2-power');d=Path('.circuit-cache/stage44-b2-anchor');r=json.loads((s/'drc-power.json').read_text())
assert not r['schematic_parity'] and not any(x['severity']=='error' for x in r['violations'])
d.mkdir()
for p in s.iterdir():
 if p.name=='sheets':shutil.copytree(p,d/p.name)
 elif p.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru') or p.name in ('receipt.json','fp-lib-table','sym-lib-table'):shutil.copy2(p,d/p.name)
INNER
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py "$src/osc-jack-left.kicad_pcb" "$src/anchor-proposal.json" --output "$work/osc-jack-left.kicad_pcb"
args=(--proposal .circuit-cache/stage44-b2-placement-v2/power-proposal.json --proposal "$src/anchor-proposal.json")
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "${args[@]}"
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all -o "$work/drc-anchor.json" "$work/osc-jack-left.kicad_pcb"
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "${args[@]}"
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_dump.py "$work/osc-jack-left.kicad_pcb" "$work/dump-anchor.json"
/workspace/shared/osc-ci-python/bin/python "$root/route_signals.py" "$work/dump-anchor.json" "$work/receipt.json" "$work/signals-proposal.json" --resolution .05
