#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage46/ground-escape/fill_probe.py .circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage46/filled-B.json
