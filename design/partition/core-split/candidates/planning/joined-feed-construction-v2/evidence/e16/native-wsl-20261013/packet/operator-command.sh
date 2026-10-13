#!/usr/bin/env bash
set -euo pipefail
cd /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4
bash /home/takazudo/.codex/scripts/heavy-guard.sh -- /usr/bin/script --quiet --return --echo=never --command 'python3 scripts/kicad/operator_terminal.py --request .circuit-cache/e16-local-packet-093f14b-3f8e1f74/harmless-control-request.json --control-request-sha256 ff2bbff34c6a24b3f0944eb9ef058ecb170440dce394e35ece78d74cfd5d230c' /dev/null </dev/tty
