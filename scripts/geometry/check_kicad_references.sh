#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
cd "$repo_root"
scratch=$(mktemp -d schematic/.clip-reference-check.XXXXXX)
cleanup() {
  python3 - "$scratch" <<'PY'
from pathlib import Path
import shutil
import sys
shutil.rmtree(Path(sys.argv[1]), ignore_errors=True)
PY
}
trap cleanup EXIT

python3 scripts/geometry/build_kicad_ref_fixture.py "$scratch/numeric"
python3 scripts/geometry/build_kicad_ref_fixture.py "$scratch/legacy" --legacy-suffix
log_path="$scratch/numeric-export.log"
netlist_path="$scratch/numeric-netlist.net"
bash scripts/kicad/run.sh kicad-cli sch export netlist \
  --format kicadsexpr -o "$netlist_path" \
  "$scratch/numeric/clip-ref-fixture.kicad_sch" >"$log_path" 2>&1

if rg -qi 'annotation errors|annotation warning|unannotated' "$log_path"; then
  cat "$log_path" >&2
  exit 1
fi

legacy_log="$scratch/legacy-export.log"
legacy_status=0
bash scripts/kicad/run.sh kicad-cli sch export netlist \
  --format kicadsexpr -o "$scratch/legacy/netlist.net" \
  "$scratch/legacy/clip-ref-fixture.kicad_sch" >"$legacy_log" 2>&1 || legacy_status=$?
if ! rg -qi 'annotation errors|annotation warning|unannotated' "$legacy_log"; then
  cat "$legacy_log" >&2
  printf 'Expected the legacy letter suffix to produce a KiCad annotation warning (exit %s).\n' "$legacy_status" >&2
  exit 1
fi

python3 - "$netlist_path" <<'PY'
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text(encoding='utf-8')
refs = re.findall(r'\(comp\s*\(ref\s+"?([A-Z]+[0-9]+)"?\)', text)
clip_refs = [ref for ref in refs if ref.startswith('D')]
if len(clip_refs) != 10 or len(set(clip_refs)) != 10:
    raise SystemExit(f'expected ten unique numeric clip designators, found {clip_refs!r}')
print('PASS: numeric clip refs export cleanly; legacy A-suffix control is rejected with an annotation warning')
PY
