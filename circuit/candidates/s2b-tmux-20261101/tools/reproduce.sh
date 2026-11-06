#!/usr/bin/env bash
# Rebuild the UNADOPTED S2b candidate in a disposable worktree at the predecessor commit.
# Usage: bash reproduce.sh <worktree-at-60c7c3ab> <record-dir> <main-repo>
# <main-repo> supplies the ignored local caches (.circuit-cache/sources) only; it is read, never written.
# Generation order, not a validation. No DRC, no zone fill, no fabrication output.
set -euo pipefail
tree=$(cd "$1" && pwd -P); record=$(cd "$2" && pwd -P); main=$(cd "$3" && pwd -P)
cd "$tree"
git apply --whitespace=nowarn "$record/patches/source.patch"
# The two TI datasheets and the BAV199 mirror copy (phase 24) are retained bytes (not in the
# text patch); verify, then place.
mkdir -p .circuit-cache && cp -a "$main/.circuit-cache/sources" .circuit-cache/
while read -r sum dest cache; do
  cp "$main/.circuit-cache/sources/$cache" "$dest"
  echo "$sum  $dest" | sha256sum -c -
done <<'L'
7396d8a34f80b178a8b5c72272b5bb0eb7da7ad3182e7d3cd80d294fc32f26e5 circuit/sources/ic-library/TMUX7412F.pdf readiness-20261031/ds/tmux7412f.pdf
c0fab3135a4438048a759aa91b33480f95f01140885896e3bfa1202a9daa2ae1 circuit/sources/ic-library/TMUX6112.pdf readiness-20261031/ds/tmux6112.pdf
c09cdf672eb4274e137efcf7a0d4e34fc8de099a975cfe8efa3a5a3c560cdf81 circuit/sources/ic-library/BAV199.pdf readiness-20261101/ds/bav199.pdf
L
git add -N .
bash scripts/libgen/regen.sh
./node_modules/.bin/zudo-circuit-doc generate
for m in envelope filter manual_ab mixer mult offset oscillator sample_hold wavefolder; do
  python3 -m "design.spec.modules.build_${m}_current"
done
# Readiness tables that the candidate revises (phase 20): S2b fault rows and R-exact roles.
PYTHONPATH="$tree" python3 scripts/checks/s2b_protection_map.py
PYTHONPATH="$tree" python3 scripts/checks/r_exact_candidates.py
# regen-all is expected to stop at master-audit drift (designator lock +12 +85 +108).
bash scripts/checks/regen-all.sh || true
mkdir -p .circuit-cache/master-audit
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr \
  -o .circuit-cache/master-audit/netlist.net schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/audit_master.py .circuit-cache/master-audit/netlist.net
bash scripts/schgen/regen-master-reports.sh
# protection58 first: precision_output_cell, fast_disconnect and integrated_output read its audit.
PYTHONPATH="$tree" python3 scripts/checks/protection58.py
for m in run_envelope_spice run_wavefolder_spice run_manual_ab_spice; do python3 -m "design.spec.modules.$m"; done
for n in precision_output_cell negative_monitor_network rail_monitor_candidate fast_disconnect_candidate integrated_output_candidate; do
  PYTHONPATH="$tree" python3 "scripts/checks/$n.py"
done
PYTHONPATH="$tree" python3 scripts/checks/precision_output_cell_model.py
bash scripts/schgen/regen-master-reports.sh --check
