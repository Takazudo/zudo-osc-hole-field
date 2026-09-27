#!/usr/bin/env bash
set -euo pipefail

script_dir=${BASH_SOURCE[0]%/*}
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

temp_dir=$(mktemp -d "$repo_root/.kicad-smoke.XXXXXX")
trap 'rm -rf -- "$temp_dir"' EXIT
temp_relative=${temp_dir#"$repo_root"/}

version=$(bash scripts/kicad/run.sh kicad-cli version)
printf 'KiCad oracle: %s\n' "$version"

bash scripts/kicad/run.sh python3 scripts/kicad/smoke/build_fixture.py "$temp_relative"
bash scripts/kicad/run.sh kicad-cli sch erc \
  --format json --severity-all --exit-code-violations \
  -o "$temp_relative/erc.json" "$temp_relative/smoke.kicad_sch"
bash scripts/kicad/run.sh kicad-cli sch export netlist \
  --format kicadsexpr -o "$temp_relative/smoke.net" \
  "$temp_relative/smoke.kicad_sch"
bash scripts/kicad/run.sh python3 scripts/kicad/smoke/build_board.py "$temp_relative"
bash scripts/kicad/run.sh kicad-cli pcb drc \
  --schematic-parity --format json --severity-all \
  -o "$temp_relative/drc.json" "$temp_relative/smoke.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb export svg \
  --mode-single --layers F.Cu,F.Fab,Edge.Cuts --exclude-drawing-sheet \
  -o "$temp_relative/smoke.svg" "$temp_relative/smoke.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb render \
  --width 640 --height 480 --side top --quality basic \
  -o "$temp_relative/smoke.png" "$temp_relative/smoke.kicad_pcb"
bash scripts/kicad/run.sh python3 scripts/kicad/smoke/check_reports.py \
  "$temp_relative/erc.json" "$temp_relative/drc.json" \
  "$temp_relative/smoke.svg" "$temp_relative/smoke.png"

printf 'Smoke loop: PASS (ERC has zero violations, PCB parity has zero issues, SVG and PNG exported)\n'
