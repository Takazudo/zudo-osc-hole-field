# Clip LED reference work note

## Requested change

Replace the ten clip LED references that ended in `A` with unique numeric KiCad designators. Keep each clip LED's UID and all panel coordinates and geometry unchanged.

## Source and output

- Source: `panel_frame.reference_designator()` now appends numeric discriminator `1` to the cell number for `led_type="clip"`.
- Regression: geometry tests require every generated lock reference to match an alphabetic prefix plus digits and verify the ten exact clip references are unique.
- Generated output: `design/grid/placements.lock.json`; regeneration changed only the ten `ref` fields.
- KiCad regression: `scripts/geometry/check_kicad_references.sh` renders all ten refs from the generated placement lock and exports their netlist through the pinned KiCad oracle. The numeric export must contain ten unique D references and have no annotation warning; a negative-control fixture with the old `D906A` form must trigger KiCad's annotation warning.

## Verification

- Baseline `bash scripts/checks/regen-all.sh`: pass; no pre-edit changes.
- Post-edit `bash scripts/checks/regen-all.sh --check`: pass.
- `python3 -m unittest discover -s scripts/geometry -p 'test_*.py'`: pass.
- `bash scripts/checks/run-python-tests.sh`: 83 tests pass.
- `scripts/geometry/check_kicad_references.sh`: pass with KiCad 10.0.6; numeric refs export cleanly and the legacy control warns.
- `pnpm circuit:check` and `pnpm check`: pass.
- Panel regeneration preserved all 438 lock centres, 324 hardware holes and 114 undrilled windows.

No UID, x/y centre, hole diameter, LED offset, window or panel geometry changed.
