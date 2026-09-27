#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
fixture_dir=$(mktemp -d "$PWD/.ic-units.XXXXXX")
trap 'python3 - "$fixture_dir" <<'"'"'PY'"'"'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
for q in sorted(p.rglob("*"),reverse=True):
 if q.is_file():q.unlink()
 elif q.is_dir():q.rmdir()
p.rmdir()
PY' EXIT
fixture_rel=${fixture_dir#"$PWD"/}
python3 scripts/libgen/fixtures/build_ic_erc_fixture.py "$fixture_rel"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$fixture_rel/erc.json" "$fixture_rel/ic-library-probe.kicad_sch"
python3 - "$fixture_dir/erc.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
violations=[v for sheet in r.get('sheets',[]) for v in sheet.get('violations',[])]
for v in violations[:20]:print(v.get('type'),v.get('description'))
if violations:raise SystemExit(f'ERC FAIL: {len(violations)} violations')
print('KiCad 10 ERC PASS: 0 violations, all issue-15 symbol units placed')
PY
