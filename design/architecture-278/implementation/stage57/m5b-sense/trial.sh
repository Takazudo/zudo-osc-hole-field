#!/bin/bash
# Stage57 build of one proposal into one disposable copy, then the acceptance gate.
# Usage: trial.sh FOLDER LABEL   (FOLDER from setup.sh; LABEL pass1 or passfresh)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
F=$1; L=$2; I=design/architecture-278/implementation; K="bash scripts/kicad/run.sh"
P=$I/stage57/m5b-sense/proposal.json
[[ -f $P ]] || { echo "NOT RUN: no proposal (route search not run)"; exit 5; }
$K python3 scripts/pcbgen/grid_apply.py .circuit-cache/stage53-fresh/osc-jack-left.kicad_pcb $P --output $F/osc-jack-left.kicad_pcb
$K python3 $I/stage44/b2-specific/drc_run.py $F/osc-jack-left.kicad_pcb $F/drc-$L.json
$K python3 $I/stage41/native-pilot/connectivity.py $F/osc-jack-left.kicad_pcb $F/connectivity-$L.json
python3 $I/stage57/m5b-sense/accept.py .circuit-cache/stage53-fresh $F $P $L
