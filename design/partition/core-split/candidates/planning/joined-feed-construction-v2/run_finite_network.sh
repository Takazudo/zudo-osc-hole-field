#!/usr/bin/env bash
# Serialized conditional finite-network runs on one replay round: every board/net/process case,
# AGND return-removal faults for the nominal case, and a pitch-sensitivity pair. Source-only.
# Usage: run_finite_network.sh PYTHON RUNDIR ROUND OUTDIR
set -euo pipefail
py=$1; run=$2; round=$3; out=$4
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[[ $out = /* && ! -e $out ]] || { echo "fresh absolute OUTDIR required" >&2; exit 2; }
mkdir -p "$out"; cd "$here"
one() { local b=$1 net=$2 case=$3 pitch=$4 tag=$5; shift 5
  timeout 180s "$py" finite_network.py --source "$run/$b-access-$round.json" --planes "$run/$b-eval-$round/clipped-sheets.json" \
    --graph "$run/$b-eval-$round/port-graph.json" --census "$run/$b-eval-$round/port-obligations.json" \
    --net="$net" --case "$case" --pitch "$pitch" "$@" --output "$out/$b-$tag.json" | cut -c1-400; }
for b in KA KB; do
  for net in +12V -12V +5V AGND; do
    for case in nominal-average sensitivity-thin legacy-conditional-requirement; do
      if [[ $net = AGND && $case = nominal-average ]]; then one $b $net $case 0.5 "$net-$case-faults" --faults
      else one $b $net $case 0.5 "$net-$case"; fi
    done
    one $b $net nominal-average 1.0 "$net-nominal-average-pitch1"
  done
done
