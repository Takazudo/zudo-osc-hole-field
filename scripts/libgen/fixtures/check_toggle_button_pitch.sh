#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
fixture_dir=$(mktemp -d "$PWD/.toggle-button-pitch.XXXXXX")
trap 'python3 - "$fixture_dir" <<'"'"'PY'"'"'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
for q in p.iterdir(): q.unlink()
p.rmdir()
PY' EXIT
fixture_rel=${fixture_dir#"$PWD"/}
cat > "$fixture_dir/fp-lib-table" <<'TABLE'
(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")))
TABLE
bash scripts/kicad/run.sh python3 scripts/libgen/fixtures/check_toggle_button_pitch.py "$fixture_rel/toggle-button-pitch.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb drc --format json --severity-all -o "$fixture_rel/drc.json" "$fixture_rel/toggle-button-pitch.kicad_pcb"
bash scripts/kicad/run.sh kicad-cli pcb export svg --mode-single --layers F.Cu,F.Fab,F.CrtYd,Edge.Cuts --exclude-drawing-sheet -o "$fixture_rel/toggle-button-pitch.svg" "$fixture_rel/toggle-button-pitch.kicad_pcb"
test -s "$fixture_dir/toggle-button-pitch.svg"
python3 - "$fixture_dir/drc.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
for v in r['violations']: print(v['type']+': '+v['description'])
if r['violations'] or r['unconnected_items']: raise SystemExit(f"DRC FAIL: {len(r['violations'])} violations, {len(r['unconnected_items'])} unconnected items")
print('KiCad 10 DRC PASS: 0 violations; SVG rendered')
print('Nominal toggle courtyard gaps: 8.36 mm horizontal, 7.50 mm vertical')
print('Conservative 9.4 mm radial lever reach would overlap adjacent 17 mm centres by 1.8 mm; actual swept reach UNSOURCED')
PY
