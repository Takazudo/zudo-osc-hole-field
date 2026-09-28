#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
args=()
if [[ ${1:-} == --check && $# == 1 ]]; then args=(--check)
elif (( $# != 0 )); then printf 'Usage: bash scripts/partition/regen.sh [--check]\n' >&2; exit 2; fi
mkdir -p .circuit-cache/partition
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o .circuit-cache/partition/master.net schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/checks/io_partition60.py --netlist .circuit-cache/partition/master.net --require-cut "${args[@]}"
python3 -m scripts.geometry.check_compact_led "${args[@]}"
for script in stage_optical35 connector_packing35 partition35_floorplan partition35_loom partition35_mechanical partition35 partition35_drawing; do
  python3 "scripts/checks/$script.py" "${args[@]}"
done
bash scripts/kicad/run.sh python3 scripts/checks/partition35_orientation.py "${args[@]}"
