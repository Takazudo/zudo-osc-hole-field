#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mode=${1:-}
if [[ -n $mode && $mode != --check ]]; then
  printf 'Usage: bash scripts/schgen/regen-master-reports.sh [--check]\n' >&2
  exit 2
fi
if [[ $mode == --check ]]; then
  bash scripts/checks/regen-all.sh --check
  python3 -m design.spec.cells.harness --check
else
  bash scripts/checks/regen-all.sh
  python3 -m design.spec.cells.harness
fi
mkdir -p .circuit-cache/master-audit
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr \
  -o .circuit-cache/master-audit/netlist.net schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py .circuit-cache/master-audit/netlist.net
python3 scripts/schgen/audit_master.py .circuit-cache/master-audit/netlist.net ${mode:+$mode}
python3 scripts/schgen/build_master_budget.py ${mode:+$mode}
