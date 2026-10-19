#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage45/connectivity-inventory/route_ground.py .circuit-cache/stage45/dump.json .circuit-cache/stage45/ground-v2-proposal.json
