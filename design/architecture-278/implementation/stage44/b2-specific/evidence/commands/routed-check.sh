#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
root=design/architecture-278/implementation/stage44/b2-specific
old=design/architecture-278/implementation/stage41/native-pilot
src=.circuit-cache/stage44-b2-anchor
work=.circuit-cache/stage44-b2-routed
power=.circuit-cache/stage44-b2-placement-v2/power-proposal.json
anchor=.circuit-cache/stage44-b2-power/anchor-proposal.json
signal=$src/signals-priority-proposal.json
python3 - <<'INNER'
from pathlib import Path
import shutil,json
s=Path('.circuit-cache/stage44-b2-anchor');d=Path('.circuit-cache/stage44-b2-routed')
r=json.loads((s/'signals-priority-proposal-search.json').read_text())
if r['failed_links']:raise SystemExit('Unresolved raster links; do not apply as complete route')
r=json.loads((s/'drc-anchor.json').read_text())
if r['schematic_parity'] or any(x['severity']=='error' for x in r['violations']):raise SystemExit('Anchor rejected')
d.mkdir()
for p in s.iterdir():
 if p.name=='sheets':shutil.copytree(p,d/p.name)
 elif p.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru') or p.name in ('receipt.json','fp-lib-table','sym-lib-table'):shutil.copy2(p,d/p.name)
INNER
args=(--proposal "$power" --proposal "$anchor" --proposal "$signal")
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py "$src/osc-jack-left.kicad_pcb" "$signal" --output "$work/osc-jack-left.kicad_pcb"
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "${args[@]}"
bash scripts/kicad/run.sh python3 "$root/drc_run.py" "$work/osc-jack-left.kicad_pcb" "$work/drc-routed.json"
bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "${args[@]}"
bash scripts/kicad/run.sh python3 "$old/connectivity.py" "$work/osc-jack-left.kicad_pcb" "$work/connectivity-complete.json"
python3 "$root/connectivity.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "$work/connectivity-complete.json" "$work/connectivity-comparison.json" "${args[@]}"
bash scripts/kicad/run.sh python3 "$root/verify_power.py" "$work/osc-jack-left.kicad_pcb" .circuit-cache/stage44-b2-placement-v2/power-proposal-paths.json "$power" "$work/power-connections.json"
