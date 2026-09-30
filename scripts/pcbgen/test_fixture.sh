#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd -P)
cd "$repo_root"
python3 scripts/pcbgen/fixtures/build_fixture.py
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o boards/fixture-jacks/fixture-jacks.net boards/fixture-jacks/fixture-jacks.kicad_sch
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks
first=$(sha256sum boards/fixture-jacks/fixture-jacks.kicad_pcb | cut -d' ' -f1)
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks
second=$(sha256sum boards/fixture-jacks/fixture-jacks.kicad_pcb | cut -d' ' -f1)
[[ "$first" == "$second" ]] || { echo 'PCB sync is not byte-identical' >&2; exit 1; }
bash scripts/kicad/run.sh kicad-cli pcb drc --schematic-parity --format json --severity-all -o boards/fixture-jacks/reports/drc.json boards/fixture-jacks/fixture-jacks.kicad_pcb
python3 scripts/pcbgen/fixtures/assert_fixture.py full boards/fixture-jacks/fixture-jacks.kicad_pcb
scratch=.circuit-cache/pcbgen-test
mkdir -p "$scratch"
cp boards/fixture-jacks/fixture-jacks.kicad_pcb "$scratch/fixture-jacks.kicad_pcb"
bash scripts/kicad/run.sh python3 scripts/pcbgen/fixtures/add_owner_items.py "$scratch/fixture-jacks.kicad_pcb"
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks --output "$scratch/fixture-jacks.kicad_pcb"
python3 scripts/pcbgen/fixtures/assert_fixture.py owner "$scratch/fixture-jacks.kicad_pcb"
python3 scripts/pcbgen/fixtures/make_renet_netlist.py boards/fixture-jacks/fixture-jacks.net "$scratch/renet.net"
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks --output "$scratch/fixture-jacks.kicad_pcb" --netlist "$scratch/renet.net"
python3 scripts/pcbgen/fixtures/assert_fixture.py renet "$scratch/fixture-jacks.kicad_pcb"
# Restore the original net before checking that removing J110 leaves the rest unchanged.
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks --output "$scratch/fixture-jacks.kicad_pcb"
cp "$scratch/fixture-jacks.kicad_pcb" "$scratch/before-removal.kicad_pcb"
python3 scripts/pcbgen/fixtures/make_reduced_netlist.py boards/fixture-jacks/fixture-jacks.net "$scratch/reduced.net"
bash scripts/kicad/run.sh python3 scripts/pcbgen/sync.py fixture-jacks --output "$scratch/fixture-jacks.kicad_pcb" --netlist "$scratch/reduced.net"
python3 scripts/pcbgen/fixtures/assert_fixture.py reduced "$scratch/fixture-jacks.kicad_pcb" "$scratch/before-removal.kicad_pcb"
echo 'PCB sync fixture: PASS (parity, idempotence, owner preservation, component removal)'
