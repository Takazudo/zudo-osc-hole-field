#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
root=design/architecture-278/implementation/stage44/b2-specific
work=.circuit-cache/stage44-b2-placement-v2
bash scripts/kicad/run.sh python3 "$root/prepare.py" "$work" .circuit-cache/stage44/branches.json .circuit-cache/stage44/adjustments-v2.json
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage43/b2-translation/native_identity.py "$work"
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all -o "$work/drc-placement.json" "$work/osc-jack-left.kicad_pcb"
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage43/b2-translation/native_identity.py "$work"
