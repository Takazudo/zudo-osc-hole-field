#!/usr/bin/env bash
set -euo pipefail
cd /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4
# OPERATOR ACTION: approves only the exact startup-success request below.
python3 scripts/kicad/local_native_admission.py approve --request .circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success.json --request-sha256 96460d07133d4ac62741abeadefdb1c990fee433033487beea08c9386242cfe4 --output .circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success-approval.json --operator takazudo --reservation-reference 'Operator invocation of this startup-success script reserves one global native slot and excludes all other native work for this request.' --qualification-reference '/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/harmless-controls/qualification.json sha256=64b46e301dcae8506b52d14653ca966594374ca0f0c3b4970cb3bc403f64bc4c'
python3 scripts/kicad/local_native_admission.py execute --request .circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success.json --approval .circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success-approval.json </dev/tty
