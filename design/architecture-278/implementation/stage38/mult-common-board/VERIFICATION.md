# Work and verification receipt

Scope: one populated B1 common-board source candidate, exact34mm B2 translation, independently reviewed rejection/unknowns, normal push to existing draft287 and exact-head CI. Baseline `8dbbc9d835832b0b55d7745692963fe2da0d29e8` freshly matched to PR287; latest Issue278 completion/clarification read. Portable bootstrap already completed and fully consumed in this same environment/chat, not rerun. Repository instructions, source workflow and relevant retained facts apply. User prohibits canonical changes/native regeneration, taking precedence over generic regeneration-at-task-start instruction.

Actual local commands:

- `pnpm circuit:check` before edits —PASS; manual68-line inventory, no schematic/placement binding, pin-asset check performed.
- `PYTHONDONTWRITEBYTECODE=1 python3 design/architecture-278/implementation/stage38/mult-common-board/generate.py` —writes only additive layout JSON/SVG/CSV; final generator passes.
- `python3 -m unittest discover -s scripts/checks -p test_mult_common_board.py` and same with `python3 -O` —8PASS each, repeated after connector-face correction.
- `python3 -m unittest discover -s scripts/checks -p test_family_reuse.py` and same with `python3 -O` —7PASS each; retained Stage37 candidate unchanged.
- Import `scripts/checks/architecture_history.py`; call `verify_binding(Path.cwd(),commit,modules)` for all `CHECKPOINTS` —7checkpoints/8modules PASS normal/-O. Full historical replay NOT RUN locally.
- `pnpm check` —PASS: component contract, current generated docs/preflight/models/footprints, documentation TypeScript checks.
- `pnpm circuit:check` after edits —PASS with same manual68-line scope.
- `git diff --check` —PASS.
- Existing `/workspace/shared/osc-ci-python/bin/python` Playwright with `/usr/bin/chromium` rendered SVG to `/tmp/mult-common-board.png`; visually inspected. This is diagram review, not a physical or browser integration qualification.
- Both retained3M PDF cache files were rehashed against `stage36/standard-idc-assembly/sources.json`; both match. No procurement, download or installation required.

First failures retained: initial header(28,168) grip/expanded J210:T reservation overlap; corrected proposed headerY169, no jack movement or allowance reduction. Decisive four pad-boundary failures remain0.38mm at retained0.5mm edges. No candidate is tuned through that failure. Exploratory searches referenced nonexistent `scripts/pcbgen/footprints.py`; actual retained footprint helpers were found and used. Initial uncached placement run was slow; immutable footprint parsing is now cached, without geometry/output changes.

Independent review initially rejected the connector mapping convention: rear SMT mirroredX into panel-front coordinates, but P8 reused component-face coordinates without that mirror. Corrected both explicit header/socket-to-panel transforms and added independent equality assertions for all eight pins. This substantive fix was rerun in both Python modes and resubmitted for final review. Review findings and final file hashes live in REVIEW.md; no earlier review is represented as covering an unreviewed correction.

Local KiCad/regeneration/ERC/DRC, copper routing, full native/aggregate suites, physical/energized/mock-up/manufacturing checks: NOT RUN in this source-only task. No heavy local suite started. Exact-head remote CI is reported separately in Issue278 after the normal push; baseline CI is not proof for this head. No fabricated MPN, wire/flex/current/strength limit, source free-space assumption or physical result. No canonical/history/panel/parent286 change.
