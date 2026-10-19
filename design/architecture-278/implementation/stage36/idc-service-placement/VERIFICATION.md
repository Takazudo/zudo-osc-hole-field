# Verification receipt

Baseline `2f30e91eaaea012dbf6eca5bff67ff088ba31d39`. Only this new proposal directory and `scripts/checks/test_idc_service_placement.py` change. No canonical/historical files or CI workflow changes.

Commands from repository root:

- `python3 design/architecture-278/implementation/stage36/idc-service-placement/generate.py` — deterministic candidate JSON and SVG; tests compare both byte-equivalent representations.
- `python3 -m unittest discover -s scripts/checks -p test_idc_service_placement.py` and matching `python3 -O` —7 PASS each; independently repeated by fresh reviewer.
- `python3 -m unittest discover -s scripts/checks -p 'test_*idc*.py'` and matching `python3 -O` —14 PASS each, covering both this revision and retained prior negative cases.
- Normal and optimized Python: import `scripts/checks/architecture_history.py`; call `verify_binding(Path.cwd(), commit, modules)` for every entry of `CHECKPOINTS` —7 checkpoints/8 historical module bindings PASS.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before/after —PASS; manual68-line scope, no schematic/placement binding.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` —PASS: generated pages/preflight/models/footprints current, documentation type check passes.
- `git diff --check` —PASS.
- SVG rendered with existing `/workspace/shared/osc-ci-python/bin/python`, Playwright and `/usr/bin/chromium` using `page.set_content` and screenshot; inspected locally at `/tmp/idc-placement.png`. This is a diagram inspection, not a browser suite or mechanical verification. Initial optional CairoSVG attempt failed with `ModuleNotFoundError`; no installation attempted and no CairoSVG success claimed.

First design failures retained: original control grip/side-support hit; original middle C-SIG/core overlap; newly screened original control grip/RV1308 courtyard overlap and J-PWR/five-resistor courtyard overlaps; rejected rotated control connector. Revised source screens pass their stated necessary geometric conditions without reducing allowances. Unknown absolute depths, height maxima and cable paths remain unknown, so no integrated fit pass follows.

No unit-test first failure occurred. Fresh review checks final substantive bytes and records their hashes separately. Full historical replay, aggregate regeneration, KiCad/native checks and physical/electrical qualification NOT RUN locally. Existing remote CI runs are reported by exact SHA separately in the issue; baseline CI success, if obtained, does not qualify this new commit. No heavy local suite, order, fabrication, merge or release.
