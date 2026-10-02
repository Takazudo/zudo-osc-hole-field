#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p schematic/exports/sheets
bash scripts/kicad/run.sh kicad-cli sch export pdf \
  -o schematic/exports/master-hierarchy.pdf schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export svg --pages 1 \
  -o schematic/exports schematic/zudo-osc-hole-field.kicad_sch
for sheet in schematic/sheets/*.kicad_sch; do
  bash scripts/kicad/run.sh kicad-cli sch export svg \
    -o schematic/exports/sheets "$sheet"
done
python3 scripts/schgen/normalize_exports.py

# These retained views cover the complete current source hierarchy.
python3 - <<'CHECK_EXPORTS'
from pathlib import Path
import re
from design.spec.instrument import specification
root = Path('schematic/exports')
expected = {'zudo-osc-hole-field.svg'} | {
    'sheets/' + p.stem + '.svg' for p in Path('schematic/sheets').glob('*.kicad_sch')
}
actual = {str(p.relative_to(root)) for p in root.rglob('*.svg')}
if actual != expected:
    raise SystemExit(f'Master SVG set differs: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}')
# The pinned KiCad PDF writer uses explicit, uncompressed page dictionaries.
# Fail if that format changes rather than guessing at hierarchy coverage.
pages = len(re.findall(rb'/Type\s*/Page\b', (root/'master-hierarchy.pdf').read_bytes()))
expected_pages = len(specification()[1]) + 1
if pages != expected_pages:
    raise SystemExit(f'Master PDF pages {pages} != source hierarchy {expected_pages}')
print(f'PASS: {len(actual)} retained SVGs and {pages} PDF pages match the draft master hierarchy')
CHECK_EXPORTS
