#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
if (( $# > 1 )) || [[ ${1:-} != '' && ${1:-} != --generated ]]; then
  printf 'Usage: bash scripts/schgen/smoke.sh [--generated]\n' >&2
  exit 2
fi
if [[ ${1:-} != --generated ]]; then
  bash scripts/schgen/regen.sh
fi
scratch=$(mktemp -d schematic/.schgen-smoke.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/check_erc_warnings.py "$scratch/erc.json"
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 scripts/schgen/audit_master.py "$scratch/netlist.net" --check
python3 - "$scratch/netlist.net" <<'PY'
from dataclasses import replace
from pathlib import Path
import sys
from design.spec.instrument import specification
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import verify,exported_pin_nets
families, instances = specification()
f = families[0]
p = next(p for p in f.parts if p.key=='LF398.1')
actual=exported_pin_nets(Path(sys.argv[1]).read_text())
held=[actual[(designator(p,i),'7')] for i in instances[:2]]
assert held==['/H1/RAW_HELD','/H2/RAW_HELD'],held
changed = replace(f, parts=tuple(replace(p, pins={**p.pins, '8': 'DELIBERATELY_WRONG'}) if q.key==p.key else q for q in f.parts))
differences = verify((changed, *families[1:]), instances, Path(sys.argv[1]).read_text())
assert len(differences) == 2, differences
print('PASS: H1/H2 held outputs remain separate; deliberate hold-node change rejected in both instances')
PY
