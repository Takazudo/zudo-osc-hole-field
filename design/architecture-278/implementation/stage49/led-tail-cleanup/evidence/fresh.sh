set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py .circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb design/architecture-278/implementation/stage49/led-tail-cleanup/proposal.json --output .circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage44/b2-specific/drc_run.py .circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage49-fresh/drc-passfresh.json
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage41/native-pilot/connectivity.py .circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage49-fresh/connectivity-passfresh.json
