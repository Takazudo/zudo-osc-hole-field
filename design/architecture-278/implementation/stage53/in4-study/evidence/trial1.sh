set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_apply.py .circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb design/architecture-278/implementation/stage53/in4-study/trial1-proposal.json --output .circuit-cache/stage53-trial1/osc-jack-left.kicad_pcb
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage44/b2-specific/drc_run.py .circuit-cache/stage53-trial1/osc-jack-left.kicad_pcb .circuit-cache/stage53-trial1/drc-pass1.json
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage41/native-pilot/connectivity.py .circuit-cache/stage53-trial1/osc-jack-left.kicad_pcb .circuit-cache/stage53-trial1/connectivity-pass1.json
