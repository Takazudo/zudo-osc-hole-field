#!/usr/bin/env bash
# Rebuild the UNADOPTED candidate in a disposable worktree at the predecessor commit.
# Usage: bash reproduce.sh <empty-worktree-at-predecessor> <record-dir>
# Generation order, not a validation. No DRC, no zone fill, no fabrication output.
set -euo pipefail
tree=$(cd "$1" && pwd -P); record=$(cd "$2" && pwd -P)
cd "$tree"
git apply --whitespace=nowarn "$record/patches/source.patch"
git add -N .
bash scripts/libgen/regen.sh
./node_modules/.bin/zudo-circuit-doc generate
for m in envelope filter manual_ab mixer mult offset oscillator sample_hold wavefolder; do
  python3 -m "design.spec.modules.build_${m}_current"
done
# regen-all is expected to stop at master-audit drift (designator lock +80).
bash scripts/checks/regen-all.sh || true
mkdir -p .circuit-cache/master-audit
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr \
  -o .circuit-cache/master-audit/netlist.net schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/audit_master.py .circuit-cache/master-audit/netlist.net
bash scripts/schgen/regen-master-reports.sh
for m in run_envelope_spice run_wavefolder_spice run_manual_ab_spice; do python3 -m "design.spec.modules.$m"; done
# precision_output_cell first: fast_disconnect and integrated_output bind its report hash.
for n in precision_output_cell negative_monitor_network rail_monitor_candidate fast_disconnect_candidate integrated_output_candidate; do
  PYTHONPATH="$tree" python3 "scripts/checks/$n.py"
done
PYTHONPATH="$tree" python3 scripts/checks/precision_output_cell_model.py
bash scripts/schgen/regen-master-reports.sh --check
