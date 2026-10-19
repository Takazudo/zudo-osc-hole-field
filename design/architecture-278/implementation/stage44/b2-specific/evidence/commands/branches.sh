#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage44/b2-specific/branches.py .circuit-cache/stage44/branches.json
