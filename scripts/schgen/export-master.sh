#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p schematic/exports/sheets
bash scripts/kicad/run.sh kicad-cli sch export pdf \
  -o schematic/exports/master-hierarchy.pdf schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export svg --pages 1 \
  -o schematic/exports schematic/zudo-osc-hole-field.kicad_sch
for sheet in schematic/sheets/*.kicad_sch; do
  bash scripts/kicad/run.sh kicad-cli sch export svg \
    -o schematic/exports/sheets "$sheet"
done
python3 scripts/schgen/normalize_exports.py
