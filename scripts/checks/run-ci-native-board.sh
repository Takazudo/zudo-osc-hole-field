#!/usr/bin/env bash
set -euo pipefail

board=${1:?board required}
case "$board" in
  osc-jack-left|osc-jack-right|osc-core) ;;
  *) printf 'Unknown CI board: %s\n' "$board" >&2; exit 2 ;;
esac
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --format json --severity-all \
  -o "boards/$board/reports/ci-drc.json" "boards/$board/$board.kicad_pcb"
python3 scripts/pcbgen/summarize.py "boards/$board/reports/ci-drc.json"
