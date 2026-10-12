#!/usr/bin/env bash
# Rebuild the complete E16 chain from tracked sources into a fresh directory.
# Usage: replay_e16.sh PYTHON OUTDIR
# PYTHON must carry the pinned numpy/scipy/shapely (scripts/pcbgen/numerical-requirements.txt).
# Source-only: no KiCad/native call. Each step keeps its own 180 s / 2 GiB bound.
set -euo pipefail
py=$1; out=$2
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[[ $out = /* && ! -e $out ]] || { echo "fresh absolute OUTDIR required" >&2; exit 2; }
mkdir -p "$out"
cd "$here"
timeout 180s "$py" construct.py --output "$out/cand05" >/dev/null
eval_chain() { "$py" evaluate_access.py --source "$1" --clip-helper clip_sheets.py --design evidence/board-access-design.json --python "$py" --output "$2" | tail -1; }
for b in KA KB; do
  timeout 180s "$py" normalize_board.py --board-id $b --pcb "$out/cand05/$b.kicad_pcb" --terminals "$out/cand05/terminals.json" --output "$out/$b-normalized.json"
  eval_chain "$out/$b-normalized.json" "$out/$b-eval-base"
  prev=$out/$b-normalized.json; e=$out/$b-eval-base
  for round in r1 r2 r3; do
    case $round in
      r1) args=(--method via --planes "$e/clipped-sheets.json");;
      r2) args=(--method route);;
      r3) args=(--method route --planes "$e/clipped-sheets.json");;
    esac
    timeout 180s "$py" construct_access.py "${args[@]}" --source "$prev" --graph "$e/port-graph.json" --census "$e/port-obligations.json" \
      --output "$out/$b-access-$round.json" --report "$out/$b-access-$round-report.json"
    eval_chain "$out/$b-access-$round.json" "$out/$b-eval-$round"
    prev=$out/$b-access-$round.json; e=$out/$b-eval-$round
  done
done
