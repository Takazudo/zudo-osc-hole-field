#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
root=design/architecture-278/implementation/stage44/b2-specific
power=.circuit-cache/stage44-b2-placement-v2/power-proposal.json
signal=.circuit-cache/stage44-b2-anchor/signals-priority-proposal.json
anchor=.circuit-cache/stage44-b2-power/anchor-proposal.json
python3 - <<'FIRST'
from pathlib import Path
import shutil,json
p=Path('.circuit-cache/stage44-b2-routed')
r=json.loads((p/'drc-routed.json').read_text())
if r['schematic_parity'] or any(v['severity']=='error' for v in r['violations']):raise SystemExit('first DRC failed')
if not json.loads((p/'connectivity-comparison.json').read_text())['accepted_connectivity_only']:raise SystemExit('first connectivity failed')
if not json.loads((p/'power-connections.json').read_text())['accepted_native_connections_only']:raise SystemExit('first power failed')
for a,b in [('drc-routed.json','drc-signals-pass1.json'),('drc-routed.json.execution.json','drc-signals-pass1.json.execution.json'),('connectivity-complete.json','connectivity-complete-pass1.json'),('connectivity-comparison.json','connectivity-comparison-pass1.json'),('power-connections.json','power-connections-pass1.json'),('identity-audit.json','identity-audit-pass1.json')]:
 if (p/b).exists():raise SystemExit('first pass already archived')
 shutil.copy2(p/a,p/b)
FIRST
for pass in 2 3 fresh; do
 work=.circuit-cache/stage44-b2-routed
 if [[ "$pass" == fresh ]]; then
  python3 - <<'COPY'
from pathlib import Path
import shutil
src=Path('.circuit-cache/stage44-b2-routed');dst=Path('.circuit-cache/stage44-b2-fresh')
dst.mkdir()
for p in src.iterdir():
 if p.is_dir():shutil.copytree(p,dst/p.name)
 elif p.suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru') or p.name in ('receipt.json','fp-lib-table','sym-lib-table'):
  shutil.copy2(p,dst/p.name)
COPY
  work=.circuit-cache/stage44-b2-fresh
 fi
 bash scripts/kicad/run.sh python3 "$root/drc_run.py" "$work/osc-jack-left.kicad_pcb" "$work/drc-pass$pass.json"
 bash scripts/kicad/run.sh python3 "$root/audit.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json --proposal "$power" --proposal "$anchor" --proposal "$signal"
 bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage41/native-pilot/connectivity.py "$work/osc-jack-left.kicad_pcb" "$work/connectivity-pass$pass.json"
 python3 "$root/connectivity.py" "$work/osc-jack-left.kicad_pcb" "$work/receipt.json" .circuit-cache/stage44/branches.json "$work/connectivity-pass$pass.json" "$work/comparison-pass$pass.json" --proposal "$power" --proposal "$anchor" --proposal "$signal"
 bash scripts/kicad/run.sh python3 "$root/verify_power.py" "$work/osc-jack-left.kicad_pcb" .circuit-cache/stage44-b2-placement-v2/power-proposal-paths.json "$power" "$work/power-pass$pass.json"
 cp "$work/identity-audit.json" "$work/identity-pass$pass.json"
 printf 'Completed native pass %s\n' "$pass"
done
python3 "$root/settlement.py" .circuit-cache/stage42-full-b1-fresh .circuit-cache/stage44-b2-routed .circuit-cache/stage44-b2-fresh .circuit-cache/stage44/settlement.json
python3 -O "$root/settlement.py" .circuit-cache/stage42-full-b1-fresh .circuit-cache/stage44-b2-routed .circuit-cache/stage44-b2-fresh .circuit-cache/stage44/settlement-optimized.json
cmp .circuit-cache/stage44/settlement.json .circuit-cache/stage44/settlement-optimized.json
