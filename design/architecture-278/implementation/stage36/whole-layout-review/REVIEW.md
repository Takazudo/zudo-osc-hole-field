# Review/check receipt — 2026-10-18

Base367f0b12b17c720e2aa9f40b23659d551abeceb8. Only this additive viewer directory changes; historical viewer and coupon checkpoint remain byte-identical. Parent PR286 remainsb58068fbaeb65886958a67a4f4978613414e31c5.

## First failures and corrections retained

- Independent review found overlap focus inferred block IDs by splitting display names; retained A01 names use hyphens, hiding its conflicts. Fixed by carrying explicit source box.block identities. Source and browser regressions now cover this.
- Browser test originally wrote reviewed screenshots in place. Changed to default `/tmp/osc-whole-layout-render` with optional REVIEW_OUTPUT_DIR. Final reviewed artifacts are copied deliberately; subsequent checks do not alter them.
- First sandbox guard invocation could not create its shared lock and fell through unguarded; browser then failed on `file://` navigation with ERR_BLOCKED_BY_ADMINISTRATOR before checks ran. Retried the normal guard with approved full escalation; no alternate queue or guard bypass used. Browser rendering uses supplied HTML via set_content, as the earlier viewer tests do. Direct local-file navigation is NOT VERIFIED in this managed browser. Users need a browser permitted to open their downloaded file.
- Enlarged labels and reduced whole-view label duplication after visual inspection. Red crosses mark overlap centres rather than filling entire overlap regions. Conflict count/warning remains prominent; no conflict erased.

## Final evidence

Six focused source tests PASS in normal and optimized Python. Extractor and standalone build --check PASS in both modes.24browser checks PASS: coverage, fixed markers, opposite-face orientation, focus including A01 conflicts, each layer, explode/historical visibility, PNG export and offline execution. Zero JavaScript errors / external requests. Final guarded browser verdict=PASS exit=0 secs=9 min_mem_mb=16462. Screenshots inspected. Input hashes and all16artifact hashes verified against artifact-sha256.json (manifest SHA256 `5e422e247c6ca29291628a76d5485ea617aa353f10be234d2fc9cb021b09c5d9`).

Commands from repository root:

- `python3 [and python3 -O] design/architecture-278/implementation/stage36/whole-layout-review/test_source.py`
- `python3 [and python3 -O] design/architecture-278/implementation/stage36/whole-layout-review/extract.py --check`
- `python3 [and python3 -O] design/architecture-278/implementation/stage36/whole-layout-review/build.py --check`
- `bash /workspace/codex-settings/.portable-profile-home/.codex/scripts/heavy-guard.sh -- python3 design/architecture-278/implementation/stage36/whole-layout-review/test_browser.py` (approved escalation for native shared lock)
- `python3 [and python3 -O] scripts/architecture278/implementation/stage36_interface_cassette.py --check --check-review`
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before and after; `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` after.
- `git diff --check`, staged whitespace check and predecessor byte-diff checks.

All final commands passed. Contract scope remains manual inventory68lines with no schematic/placement binding, pin-asset check performed. Generated pages/models/31footprint previews and TypeScript checks pass. Stage36 guard preserves the failed interface-concept result. Full historical replay not repeated because its sources/entrypoints are unchanged; prior evidence remains retained. Native KiCad/ERC/DRC, manufacturing, physical fit and electrical testing NOT RUN by scope.

Final independent reviewer `/root/stage36_review`: **PASS_SOURCE_AND_RENDER_REVIEW_ONLY**, no remaining material findings after final substantive changes. Independently reran six source tests/extraction/build normal and optimized, guarded24browser checks with no JS errors/external requests, and inspected screenshots. Verified all16artifact hashes against the manifest above. HTML SHA256 `e06d60ef54760134ff0022e3a49c25a5d0fb4c3c31548e0e37179c7d08d18226`. Reviewer initially encountered read-only guard-lock access; exact approved escalated retry passed. No reviewer edits. This is visual/source acceptance only, never hardware qualification.
