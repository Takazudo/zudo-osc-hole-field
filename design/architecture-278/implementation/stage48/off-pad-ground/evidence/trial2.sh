set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py .circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage48/proposal-b-only.json --output .circuit-cache/stage48-trial2/osc-jack-left.kicad_pcb
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage44/b2-specific/drc_run.py .circuit-cache/stage48-trial2/osc-jack-left.kicad_pcb .circuit-cache/stage48-trial2/drc-pass1.json
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage41/native-pilot/connectivity.py .circuit-cache/stage48-trial2/osc-jack-left.kicad_pcb .circuit-cache/stage48-trial2/connectivity-pass1.json
