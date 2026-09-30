#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
fixture_dir=$(mktemp -d "$PWD/.jack-pitch.XXXXXX")
trap 'rm -rf -- "$fixture_dir"' EXIT
fixture_rel=${fixture_dir#"$PWD"/}
cat > "$fixture_dir/fp-lib-table" <<'TABLE'
(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")))
TABLE
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/check_jack_pitch.py "$fixture_rel/jack-pitch.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb drc --format json --severity-all -o "$fixture_rel/drc.json" "$fixture_rel/jack-pitch.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb export svg --mode-single --layers F.Cu,F.Fab,F.CrtYd,Edge.Cuts --exclude-drawing-sheet -o "$fixture_rel/jack-pitch.svg" "$fixture_rel/jack-pitch.kicad_pcb"
test -s "$fixture_dir/jack-pitch.svg"
python3 - "$fixture_dir/drc.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
violations=r['violations']
for v in violations: print(v['type']+': '+v['description'])
if violations: raise SystemExit(f"DRC FAIL: {len(violations)} violations")
print('KiCad 10 DRC PASS: four jack footprints at 14 x 17 mm pitch; 0 violations; SVG rendered')
PY
