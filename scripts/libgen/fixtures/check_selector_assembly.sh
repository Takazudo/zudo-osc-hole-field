#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/build_selector_assembly.py
for name in front rear rejected-alternating-coplanar rejected-same-coplanar; do
  bash scripts/kicad/run.sh kicad-cli pcb drc --format json --output ".circuit-cache/selector-fixture/${name}-drc.json" ".circuit-cache/selector-fixture/${name}.kicad_pcb"
done
bash scripts/kicad/run.sh kicad-cli pcb drc --format json --output .circuit-cache/selector-fixture/panel-drc.json boards/panel/panel.kicad_pcb
python3 scripts/libgen/fixtures/check_selector_assembly.py
