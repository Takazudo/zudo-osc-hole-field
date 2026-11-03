# Verification receipt

Baseline: `42ff6eab4f4fd4be28b78cd35ef49ecbabaf2b64`. Additive candidate directory plus `scripts/checks/test_standard_idc_assembly.py`; existing source/history/manufacturing/artwork bytes unchanged.

Commands from repository root:

- `python3 design/architecture-278/implementation/stage36/standard-idc-assembly/generate.py` — generated candidate JSON. The focused test recomputes and compares it exactly.
- `python3 -m unittest discover -s scripts/checks -p test_standard_idc_assembly.py` — 7 PASS.
- `python3 -O -m unittest discover -s scripts/checks -p test_standard_idc_assembly.py` — 7 PASS.
- `python3 -m unittest discover -s scripts/checks -p test_architecture_history.py` and corresponding `python3 -O` — 12 PASS each. Intentional broken/empty snapshot fixtures print failures inside passing rejection tests; these are not failed product checks.
- Normal and optimized Python: import `scripts/checks/architecture_history.py`; for each `(commit, modules)` in `CHECKPOINTS`, call `verify_binding(Path.cwd(), commit, modules)` — all seven checkpoints/eight historical module bindings PASS.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before edits and after — PASS, manual inventory 68 lines; no schematic/placement binding.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` — PASS: evidence contract, generated docs/preflight/models/footprints current; documentation type check has no errors.
- `git diff --check` — PASS.

Focused tests exercise unchanged numbered maps and opposing-face reflection, NC isolation, controlled-inch/reference distinction, tail versus board underside, known negative service cases, fail-closed unknowns, touching-obstacle sensitivity and rotated footprint bounds. They do not test a physical connector.

First design failures preserved: J17902 15 mm withdrawal ceiling 8 mm with core installed; control symmetric grip/withdrawal conflicts with side supports. Earlier Würth closure inference failures remain untouched. No unit-test first failure occurred in this additive checkpoint.

Full historical replay, aggregate regeneration, KiCad/native ERC/DRC and manufacturing checks NOT RUN locally: this bounded source-only candidate does not modify their inputs and the owner excludes native regeneration. Existing CI may execute its unchanged checks after push; no new exact-head CI success is claimed in this receipt. No heavy suite, Docker/KiCad installation, physical fit, electrical operation, unpowered prototype construction, force test, order, fabrication, deployment or merge was performed.
