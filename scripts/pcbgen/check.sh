#!/usr/bin/env bash
set -euo pipefail
if (($# != 1)); then echo 'Usage: scripts/pcbgen/check.sh <board-id>' >&2; exit 2; fi
board_id=$1
repo_root=$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd -P)
cd "$repo_root"
board="boards/$board_id/$board_id.kicad_pcb"
reports="boards/$board_id/reports"
if [[ ! -f "$board" ]]; then echo "Missing PCB draft: $board" >&2; exit 1; fi
mkdir -p "$reports"
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --format json --severity-all -o "$reports/drc.json" "$board"
bash scripts/kicad/run.sh kicad-cli pcb render --width 1200 --height 900 --side top --quality basic -o "$reports/top.png" "$board"
bash scripts/kicad/run.sh kicad-cli pcb render --width 1200 --height 900 --side bottom --quality basic -o "$reports/bottom.png" "$board"
bash scripts/kicad/run.sh kicad-cli pcb export svg --mode-single --layers F.Cu,F.SilkS,Edge.Cuts --exclude-drawing-sheet -o "$reports/$board_id.svg" "$board"
python3 scripts/pcbgen/summarize.py "$reports/drc.json"
