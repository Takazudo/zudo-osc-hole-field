#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
bash scripts/schgen/regen.sh
scratch=$(mktemp -d schematic/.schgen-smoke.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
bash scripts/kicad/run.sh kicad-cli sch erc --severity-all -o "$scratch/erc.rpt" schematic/zudo-osc-hole-field.kicad_sch
if ! grep -q 'ERC messages: 0  Errors 0  Warnings 0' "$scratch/erc.rpt"; then
  cat "$scratch/erc.rpt" >&2
  exit 1
fi
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - "$scratch/netlist.net" <<'PY'
from dataclasses import replace
from pathlib import Path
import sys
from design.spec.instrument import specification
from scripts.schgen.verify_netlist import verify
families, instances = specification()
f = families[0]
p = f.parts[0]
changed = replace(f, parts=(replace(p, pins={**p.pins, '2': 'DELIBERATELY_WRONG'}), *f.parts[1:]))
differences = verify((changed, *families[1:]), instances, Path(sys.argv[1]).read_text())
assert len(differences) == 3, differences
print('PASS: deliberate connection change rejected in all three instances')
PY
