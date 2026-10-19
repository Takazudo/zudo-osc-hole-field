#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 scripts/pcbgen/grid_dump.py .circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb .circuit-cache/stage45/dump.json
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage45/connectivity-inventory/route_ground.py .circuit-cache/stage45/dump.json .circuit-cache/stage45/ground-proposal.json
