#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Replay the retained, reviewed solution. No heuristic routing is needed.
python3 scripts/pcbgen/fixtures/build_dense_slice.py
id=fixture-route-dense
dir=.circuit-cache/router/dense
board="$dir/$id.kicad_pcb"
evidence=scripts/pcbgen/fixtures/dense-evidence
bash scripts/kicad/run.sh kicad-cli sch export netlist -o "$dir/$id.net" "$dir/$id.kicad_sch"
python3 - "$board" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py "$id" --output "$board"
bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$board"
for manifest in copper stitching; do
  bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/dense_copper.py replay "$board" "$evidence/$manifest.json"
done
bash scripts/pcbgen/route.sh "$id" --board "$board" --report "$dir/reports/replay-routing.json" --timeout-sec 1
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --refill-zones --format json --severity-all -o "$dir/reports/replay-drc.json" "$board"
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/assert_dense_fixture.py "$board" "$dir/reports/replay-drc.json"
# A second complete source generation must preserve board bytes and the full gate.
python3 scripts/pcbgen/fixtures/canonicalize_dense.py "$board"
cp "$board" "$dir/replay-first.kicad_pcb"
before=$(sha256sum "$board" | cut -d' ' -f1)
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py "$id" --output "$board"
bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$board"
for manifest in copper stitching; do
  bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/dense_copper.py replay "$board" "$evidence/$manifest.json"
done
bash scripts/pcbgen/route.sh "$id" --board "$board" --report "$dir/reports/replay-routing.json" --timeout-sec 1
python3 scripts/pcbgen/fixtures/canonicalize_dense.py "$board"
after=$(sha256sum "$board" | cut -d' ' -f1)
[[ $before == "$after" ]] || { echo 'Repeat generation changed board bytes' >&2; exit 1; }
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/assert_dense_fixture.py "$board" "$dir/routing-work/pre-drc.json"
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/check_dense_replay.py "$board"
echo 'PASS: fresh dense replay, complete DRC, byte-identical regeneration, preservation and negative regressions'
