# KiCad footprints

The project has one footprint library at
`footprints/kicad/zudo-osc-hole-field.pretty/`. Keep each `.kicad_mod` there
once; do not maintain a second byte-identical master copy. Place associated 3D
models under `footprints/kicad/zudo-osc-hole-field.3dshapes/` and use the
project's `${KIPRJMOD}` model prefix.

Footprint origins follow the part's functional datum. For panel hardware, the
origin is on the panel-hole axis so the fixed panel placement remains the
reference. This seed set contains generic parts and does not move any panel
hardware.

Courtyards are generated, never hand-drawn. `scripts/libgen/gen_courtyards.py`
replaces only `F.CrtYd` artwork with a rectangular outline enclosing pads and
body artwork plus 0.25 mm, using a 0.05 mm stroke. Run
`bash scripts/libgen/regen.sh` after footprint changes and regenerate after a
merge conflict; preserve any non-courtyard artwork edits.

Each imported symbol, footprint, and model is covered by a receipt in
`circuit/cad-receipts/`. A receipt records the pinned source path and commit,
hashes of inspected source bytes and output bytes, plus a fidelity class. The
seeded package footprints are classified as `family`; they are not proven
manufacturer-specific geometry. The white LED footprint's source model was
unavailable in the pinned commit, so that footprint has no 3D-model reference.

The seed importer refuses to overwrite existing assets. To intentionally
refresh them from the read-only sibling checkout, review the current diffs and
run `python3 scripts/libgen/seed_assets.py --source-repo <path> --replace`,
then run `bash scripts/libgen/regen.sh --check`.
