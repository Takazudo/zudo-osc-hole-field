#!/bin/bash
set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage46/ground-escape/route_plane.py .circuit-cache/stage45/dump.json .circuit-cache/stage46/plane-06-proposal.json --diameter .6
