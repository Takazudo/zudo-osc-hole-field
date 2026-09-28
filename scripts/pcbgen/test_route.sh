#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mode=${1:---quick}
if [[ $mode == --quick ]]; then
  python3 scripts/pcbgen/fixtures/build_route_fixture.py one four six unroutable
  for case in one four six unroutable; do
    id="fixture-route-$case"; dir=".circuit-cache/router/$case"; board="$dir/$id.kicad_pcb"
    bash scripts/kicad/run.sh kicad-cli sch export netlist -o "$dir/$id.net" "$dir/$id.kicad_sch"
    python3 - "$board" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
    bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py "$id" --output "$board"
    bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$board"
  done
  bash scripts/pcbgen/route.sh fixture-route-one --board .circuit-cache/router/one/fixture-route-one.kicad_pcb --timeout-sec 60
  bash scripts/pcbgen/route.sh fixture-route-four --board .circuit-cache/router/four/fixture-route-four.kicad_pcb --timeout-sec 60
  bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/copy_source_routes.py .circuit-cache/router/one/fixture-route-one.kicad_pcb .circuit-cache/router/six/fixture-route-six.kicad_pcb
  bash scripts/kicad/run.sh python3 scripts/pcbgen/replicate.py fixture-route-six --board .circuit-cache/router/six/fixture-route-six.kicad_pcb --source S1
  bash scripts/pcbgen/route.sh fixture-route-six --board .circuit-cache/router/six/fixture-route-six.kicad_pcb --timeout-sec 120
  board=.circuit-cache/router/six/fixture-route-six.kicad_pcb
  before=$(sha256sum "$board" | cut -d' ' -f1)
  bash scripts/kicad/run.sh python3 scripts/pcbgen/replicate.py fixture-route-six --board "$board" --source S1 --report .circuit-cache/router/six/reports/replication-repeat.json
  repeated=$(sha256sum "$board" | cut -d' ' -f1)
  [[ $before == "$repeated" ]] || { echo 'replication rerun changed board bytes' >&2; exit 1; }
  python3 - <<'PYREP'
import json
r=json.load(open('.circuit-cache/router/six/reports/replication-repeat.json'))
assert r['status']=='UNCHANGED DRAFT',r['status']
PYREP
  bash scripts/pcbgen/route.sh fixture-route-six --board "$board" --timeout-sec 120
  after=$(sha256sum "$board" | cut -d' ' -f1)
  [[ $before == "$after" ]] || { echo 'fully routed rerun changed board bytes' >&2; exit 1; }
  if bash scripts/pcbgen/route.sh fixture-route-unroutable --board .circuit-cache/router/unroutable/fixture-route-unroutable.kicad_pcb --timeout-sec 3; then
    echo 'unroutable barrier unexpectedly completed' >&2; exit 1
  else
    status=$?
    [[ $status == 3 ]] || { echo "unroutable fixture returned $status, expected 3" >&2; exit 1; }
  fi
  python3 scripts/pcbgen/fixtures/assert_route_fixture.py
elif [[ $mode == --dense ]]; then
  exec bash "$HOME/.codex/scripts/heavy-guard.sh" -- bash scripts/pcbgen/test_dense.sh
elif [[ $mode == --dense-route ]]; then
  python3 - <<'PYCLEAN'
from pathlib import Path
from datetime import datetime, timezone
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
for case in ('dense', 'dense-source'):
    path=Path('.circuit-cache/router')/case
    if path.exists():path.rename(path.with_name(case+'-attempt-'+stamp))
PYCLEAN
  python3 scripts/pcbgen/fixtures/build_dense_slice.py --source-column
  python3 scripts/pcbgen/fixtures/build_dense_slice.py
  for case in dense-source dense; do
    id="fixture-route-$case"; dir=".circuit-cache/router/$case"; board="$dir/$id.kicad_pcb"
    bash scripts/kicad/run.sh kicad-cli sch export netlist -o "$dir/$id.net" "$dir/$id.kicad_sch"
    python3 - "$board" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
    bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py "$id" --output "$board"
    bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$board"
  done
  source_status=0
  bash scripts/pcbgen/route.sh fixture-route-dense-source --board .circuit-cache/router/dense-source/fixture-route-dense-source.kicad_pcb --timeout-sec 120 --threads 4 --heap-mb 1536 || source_status=$?
  [[ $source_status == 0 || $source_status == 2 ]] || exit "$source_status"
  # Connector inputs may remain open; local source nets must be complete before replication.
  python3 - <<'PY'
import json
r=json.load(open('.circuit-cache/router/dense-source/reports/routing.json'))
assert not any(n.startswith('/C') for n in r['unrouted_net_names']),r['unrouted_net_names']
PY
  bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/copy_source_routes.py .circuit-cache/router/dense-source/fixture-route-dense-source.kicad_pcb .circuit-cache/router/dense/fixture-route-dense.kicad_pcb
  for i in $(seq 1 10); do
    b=$((i+10)); c=$((i+20))
    bash scripts/kicad/run.sh python3 scripts/pcbgen/replicate.py fixture-route-dense --board .circuit-cache/router/dense/fixture-route-dense.kicad_pcb --source "C$i" --targets "C$b" "C$c" --report ".circuit-cache/router/dense/reports/replicate-C$i.json"
  done
  bash scripts/kicad/run.sh python3 scripts/pcbgen/route_kicad.py inspect fixture-route-dense --board .circuit-cache/router/dense/fixture-route-dense.kicad_pcb --stats .circuit-cache/router/dense/routing-work/preexisting-stats.json
  route_status=0
  bash scripts/pcbgen/route.sh fixture-route-dense --board .circuit-cache/router/dense/fixture-route-dense.kicad_pcb --timeout-sec 300 --threads 4 --heap-mb 1536 || route_status=$?
  echo "Diagnostic reports retained under .circuit-cache/router/dense; this does not replace the accepted fixture evidence."
  exit "$route_status"
else
  echo 'Usage: scripts/pcbgen/test_route.sh --quick|--dense|--dense-route' >&2;exit 2
fi
