#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/pcbgen/fixtures/build_placer_fixture.py one six island overflow
for case in one six island overflow; do
  id="fixture-place-$case"
  dir=".circuit-cache/placer/$case"
  bash scripts/kicad/run.sh kicad-cli sch export netlist -o "$dir/$id.net" "$dir/$id.kicad_sch"
  rm -f "$dir/$id.kicad_pcb"
  bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py "$id" --output "$dir/$id.kicad_pcb"
  if [[ $case == overflow ]]; then
    before=$(sha256sum "$dir/$id.kicad_pcb" | cut -d' ' -f1)
    if bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$dir/$id.kicad_pcb"; then
      echo 'Expected placement overflow' >&2; exit 1
    fi
    after=$(sha256sum "$dir/$id.kicad_pcb" | cut -d' ' -f1)
    [[ $before == "$after" ]] || { echo 'Overflow changed board' >&2; exit 1; }
  else
    bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$dir/$id.kicad_pcb"
    before=$(sha256sum "$dir/$id.kicad_pcb" "$dir/reports/placement.json")
    bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py "$id" --board "$dir/$id.kicad_pcb"
    after=$(sha256sum "$dir/$id.kicad_pcb" "$dir/reports/placement.json")
    [[ $before == "$after" ]] || { echo "$case: placer output changed on second run" >&2; exit 1; }
    # Unrouted fixture connections are expected; DRC may exit 1 for them.
    rm -f "$dir/drc.json"
    bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --format json --severity-all -o "$dir/drc.json" "$dir/$id.kicad_pcb" || true
  fi
done
python3 scripts/pcbgen/fixtures/assert_placer_fixture.py
# A manually moved, locked free part must keep its position through placement.
board=.circuit-cache/placer/one/fixture-place-one.kicad_pcb
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/lock_placer_fixture.py "$board"
bash scripts/kicad/run.sh python3 scripts/pcbgen/place.py fixture-place-one --board "$board"
python3 - <<'PYLOCK'
import json
r=json.load(open('.circuit-cache/placer/one/reports/placement.json'))
assert r['preserved_refs']==['R105'],r['preserved_refs']
assert 'R105' not in [p['ref'] for p in r['placements']]
s=open('.circuit-cache/placer/one/fixture-place-one.kicad_pcb').read()
assert '(at 114.5 120' in s
print('manual locked free footprint preserved: PASS')
PYLOCK
