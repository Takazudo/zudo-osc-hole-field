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
from pathlib import Path
from scripts.libgen.gen_courtyards import courtyard_box
r=json.load(open(sys.argv[1]))
for v in r['violations']: print(v['type']+': '+v['description'])
if r['violations'] or r['unconnected_items']: raise SystemExit(f"DRC FAIL: {len(r['violations'])} violations, {len(r['unconnected_items'])} unconnected items")
print('KiCad 10 DRC PASS: 0 violations; SVG rendered')
box=courtyard_box(Path('footprints/kicad/zudo-osc-hole-field.pretty/Toggle_Dailywell_2MS_T1B1M2.kicad_mod').read_text())
print(f'Nominal toggle courtyard gaps: {17-(box[2]-box[0]):.2f} mm horizontal, {14-(box[3]-box[1]):.2f} mm vertical')
print('NOT RUN: actual lever swept-envelope clearance; pivot/throw envelope is unverified. This fixture contains footprints only.')
PY
