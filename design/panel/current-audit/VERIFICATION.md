# Source audit verification — native panel rerun unavailable

Baseline `142da27810994bc01f99bc2e6e1a559cd8f9c884`. Checks describe this audit, not manufacturing qualification.

## Completed checks

These are author-run results. The independent reviewer reran the audit/render checks, art equivalence, five focused tests in normal/optimized Python and the normal receipt check, and inspected the PNG. The broad build/site checks, 39 module tests, screenshot capture and environment events are author-run/reported.

- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before edits: PASS; manual inventory, 68 lines, no schematic/placement binding, pin-asset check performed.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check`: PASS generated pages/preflight, 31 models/footprint previews and TypeScript.
- `python3 scripts/panel/audit_current.py --check`: PASS deterministic binding inventory; all 438 UID/reference rows and retained feature-table XY/kind/apertures match. Includes each of 48 B104 overrides.
- `node scripts/panel/render_current.cjs --check`: PASS deterministic SVG/HTML.
- `node scripts/panel/test_current_art.cjs`: PASS shared export/current-preview profile; five OCT circles use lock diameter; removing unstroked dark background circles yields identical convertible art to historical settings-equivalent rendering. Native converter ignores those fills. No native board regeneration claimed.
- `python3 -m unittest scripts.panel.test_current_audit` and `python3 -O -m unittest scripts.panel.test_current_audit`: **5 tests PASS each**. Covers source counts/overrides, negative mutations of XY/kind/reference/diameter/missing/duplicate feature, perimeter arithmetic, prose/matrix regressions and all preview apertures/switch text.
- `python3 -m unittest design.spec.modules.test_filter design.spec.modules.test_envelope design.spec.modules.test_mixers design.spec.modules.test_oscillator design.spec.modules.test_mult design.spec.modules.test_manual_ab design.spec.modules.test_wavefolder`, repeated with `python3 -O`: **39 tests PASS each**. Includes G06 topology and G07 captured logic; no hardware result.
- `python3 scripts/panel/check_review_receipt.py`, also `python3 -O`: PASS retained native panel receipt hashes. Existing board/project/parameters/lock, DRC/feature table and PNGs remain unchanged. This checks retained evidence, not native KiCad execution.
- `python3 scripts/geometry/build_placements.py --check`: PASS 438 generated features, no lock write.
- Guarded `pnpm build && pnpm check:site`: PASS, 298 pages built; publication/artifact checks pass. Known historical workbench `${esc(x.url)}` template link is covered by the existing allowlist; no new exception. Guard verdict PASS. Used `HEAVY_GUARD_DIR=/workspace/shared/.agent-guard/heavy` with the portable heavy-guard script because host home is read-only; no admission bypass or thresholds changed.
- One visual screenshot via installed Chromium/Playwright over a loopback HTTP server: 438 aperture nodes rendered; PNG inspected. Header, legend, entire panel, all function regions and fixed centres visible. No browser suite or physical/render-to-native equivalence claimed. Caption identifies browser/native font/stroke differences and the three native long-label offsets. PNG is an observed rendering artifact, not a deterministic golden test.
- Whole-change whitespace and byte preservation checks: no coupon, Stage36 viewer, R21 static proof/HTML/grid, canonical board/lock or circuit changes. Check staged new files too; ordinary `git diff` excludes untracked files.

## First failures and unavailable checks retained

- Environment replaced: portable context loader verified the published snapshot. First stdout was truncated; saved read-only loader stdout to `/tmp/panel-startup.txt` and consumed all chunks. No runtime restoration or default-home fallback.
- Initial lead paths `workbench/...` were shorthand; actual source is `project/osc-hole-field/workbench/...`. Corrected reads; no file created at the wrong path.
- `KICAD_CLI_BIN=/usr/bin/kicad-cli bash scripts/kicad/run.sh kicad-cli version`: FAIL, installed 9.0.2 vs repository 10.0.6 (wrapper admits 10.0.x). Read-only home cache/config diagnostics also appeared. No incompatible native execution, Docker pull or installation.
- First direct Chromium screenshot could not create its default user-data directory; explicit temporary user-data launched but did not produce a screenshot and was stopped. Browser `file:` navigation was rejected by host administrator policy. Normal loopback HTTP preview with Playwright succeeded, using the installed browser. No browser policy changed; no external website was involved.
- Independent functional reviewer initially summarized 53 remaining pots as B103. Cross-check corrected that to **51 B103 + 2 B504** before publication. No audit JSON ever replaced SLEW with B103.
- Final review found FOLD family wording could imply a separate BIAS CV-depth pot. Corrected to FOLD CV depth only; all controls remain unchanged.

`regen-all.sh` was inspected but NOT RUN: it regenerates canonical/native boards and runs native workflows outside this source correction scope. Full historical stage replay, new native panel DRC/render/export, physical tests, energization and manufacturing actions NOT RUN. Existing coupon native evidence is preserved, not rerun and not used to qualify the instrument. The standalone coupon is unordered/deferred and is not a dependency.

Independent review verdict and final source hashes are recorded after final corrections; a receipt hash does not promote these checks to native or physical acceptance.

## Independent review

Fresh-context reviewer `stage36_review`: **PASS_SOURCE_REVIEW_ONLY**, no blocking findings after the final substantive wording correction. Receipt reviewed separately (pre-clarification SHA256 `49835406b01665c1e52ccbf57199be8b345fae8038b880b9eb2b6bb7cb15f319`); this final attribution clarification and completed-run record are administrative additions.

Final guarded documentation build/site rerun: `verdict=PASS exit=0 secs=28 min_mem_mb=15876`; 298 pages, 532 files within the 25 MiB publication limit. No source change followed this run.
