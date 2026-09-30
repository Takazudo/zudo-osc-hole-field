#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
node scripts/panel/export_art.cjs
bash scripts/kicad/run.sh python3 scripts/panel/gen_panel.py
bash scripts/kicad/run.sh python3 scripts/panel/check_panel.py
