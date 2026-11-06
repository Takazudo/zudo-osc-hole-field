set -euo pipefail
source /workspace/task-tools/kicad-10.0.6/env.sh
for name in omit-16 omit-17 omit-25; do
 bash scripts/kicad/run.sh python3 design/architecture-278/implementation/stage52/layer-bridges/probe.py .circuit-cache/stage52/$name.json .circuit-cache/stage52-$name > .circuit-cache/stage52/$name.log
done
