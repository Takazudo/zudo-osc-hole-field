# Issue 263 — Mac browser and visual verification

Browser/source verification completed on 2026-10-14 JST. Review/integration remains pending; keep #263 and #246 open. No mechanical, electrical or native qualification is implied.

## Source and tools

- Separate local Mac worktree and branch `topic/263-mac-browser`, based on fetched integration `9f69cd8a2e7b80cba813a5bd66546c4d5ac705ec`. No mechanical changes since planning `0dab96a0`; #263 was open without comments or equivalent newer verification. PR #260 remained open.
- Final launcher/test source commit: 7466ae6a5f4de339988101b8288abe092379454b. `final/receipt.json` records that exact SHA, input hashes, browser command, version, timing, exit status and browser-produced assertions. Earlier receipts record the integration SHA plus hashes of then-uncommitted checker sources. Generated inspector/report/template/SVG bytes did not change throughout this task.
- macOS 26.6.2 (25G83), installed `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, Google Chrome 155.0.8059.40. Supplemental Playwright 1.59.1 was already installed; no dependency upgrade/download.
- Every browser command used the existing `/Users/takazudo/.claude/scripts/playwright-guard.sh` (Mac perl/flock backend). Python enforces the original 60-second process deadline and terminates the isolated process group in cleanup. Playwright additionally bounds launch to 20 seconds and actions to 5 seconds. Chrome sandbox enabled in both paths. Profiles are temporary and separate from the user's browser.
- Local desktop instructions/skill catalog supplied by the host; cloud-only readiness/runtime restoration/context loader not applicable. No WSL checkout touched.

## Commands and outcomes

From the repository root, using a new output directory each time:

```sh
bash /Users/takazudo/.claude/scripts/playwright-guard.sh -- python3 design/partition/core-split/mechanical/check_browser.py --output-dir design/partition/core-split/mechanical/evidence/issue263-mac/run-01 --visuals
# run-02 repeated with diagnosed capture-settling change and stronger physical-Ref assertion.
# final checks committed launcher/assertions (without the unsuccessful CLI scroll-capture path):
bash /Users/takazudo/.claude/scripts/playwright-guard.sh -- python3 design/partition/core-split/mechanical/check_browser.py --output-dir design/partition/core-split/mechanical/evidence/issue263-mac/final
bash /Users/takazudo/.claude/scripts/playwright-guard.sh -- python3 design/partition/core-split/mechanical/evidence/issue263-mac/review_scroll.py /Users/takazudo/.codex/skills/headless-browser/node_modules/playwright/index.mjs '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' design/partition/core-split/mechanical/evidence/issue263-mac/playwright-02
```

The supplemental helper accepts any installed Playwright module and Chrome executable as explicit arguments; those personal paths are this run's tool locations, not repository prerequisites. The ordinary checker is Python stdlib plus Chrome only. Use `--browser` or `CHROME_BIN` to override executable discovery. Missing/non-executable configuration fails with diagnostics instead of silently selecting another browser. Existing output directories are refused to preserve evidence.

- CLI runs 01/02/final: exit 0, browser assertions PASS. Final run took 2.116 seconds. Each visual capture in the earlier runs completed in under 4 seconds. A PASS assertion result does not automatically accept screenshot quality: the scroll captures below were rejected.
- Supplemental `playwright/receipt.json`: exit 1 after all board interaction checks; verification script mistyped `RVO1106` (letter O) as `RV01106` (zero). No application error; the 5-second locator timeout is retained. Corrected the script to select the representative Ref from source data, then ran `playwright-02`: exit 0, PASS, no page/console-error/request-failure events.
- `checks.json` and `check-*.txt`: all 22 focused source tests PASS, including 6 launcher tests; `build.py --check` PASS (read-only generated-byte comparison); `pnpm circuit:check` PASS. Circuit check also passed before edits and after the final launcher edits; final 6 launcher tests and `git diff --check` passed.
- Circuit scope: inventory provider=manual; schematic/placement binding not performed (68 lines, 0 declared placements unverified); pin-asset check performed.
- Full `regen-all.sh`, native KiCad/PCB, ngspice/production numerical, full build/CI and physical checks: NOT RUN, explicitly outside this browser-only assignment. Broader regeneration was inspected and includes canonical/native/numerical writes. No application defect required regeneration. `[skip ci]` preserves the frozen production-run boundary; no workflow dispatch.
- Per-run wall time retained in CLI receipts. Peak memory was not measured.

## Browser assertions

Five alternatives each contain the same 100 physical Ref identities, distributed across their boards: **500 alternative-specific rows**, not 500 physical trimmers. All 13 alternative/board combinations were checked. CLI tests compare complete row inventories, select representatives on both F.Cu/B.Cu (26 face cases), compare the entire selected detail object, selected title and highlighted plan/table Ref, and assert face/board/alternative changes clear stale selection. Board options and plan plane text match current source data. All ten assembled/exploded SVG assets decode successfully and their link identities match the alternative. Ref filtering, courtyard control and internal table scrolling pass.

Playwright separately drives real select and click inputs on the unmodified generated file for every board and both faces, compares full details and face selection, checks board/alternative reset and all 500 rows, then captures scrolled views. The final run's `errors` list is empty. Assertions are executed by Chrome; no syntax-only replacement or manually supplied PASS marker is used.

## Visual inspection (all listed PNGs opened and inspected)

| Retained view | Inspection |
| --- | --- |
| `run-02/two-compact.png`, `two-deep.png` | KA/F.Cu, RV2109 VCF1 BP OFFSET, corresponding plan/table/detail and different stack planes |
| `run-02/three-compact.png`, `three-deep.png`, `three-120mm-rejected.png` | KA/F.Cu, RVO1106 OSC1 BASE PITCH, selected Ref and alternative-specific planes/conflict summary |
| `run-02/three-compact-back.png` | KB/B.Cu, RV2110 VCF1 LP OFFSET; back-face plot and detail agree |
| `run-02/three-compact-kc.png` | KC/F.Cu, RV4104 AR1 RISE OFFSET; board and selected detail agree |
| `run-02/three-compact-reset.png` | KA/B.Cu after changing face: no selected highlight or detail, selection prompt restored |
| `run-02/two-deep-assembled.png`, `two-deep-exploded.png` | Full 1000×720 source SVG drawn in browser; both boards, plane labels, rear wall and footnotes visible |
| `run-02/three-compact-assembled.png`, `three-compact-exploded.png` | Full source SVG; all three boards, separation-only exploded label, dimensions and caveats visible |
| `final/three-compact.png` | Committed checker's required three-compact state; KA/F.Cu RVO1106, correct detail and highlighted row |
| `playwright-02/three-compact-1500x1200.png` | Original test viewport, usable controls, intact plan and stack; lower details reached by page scrolling |
| `playwright-02/selected-last-row.png` | Actual last-row click selects RV1601 ALL OSC OCT SPAN; correct detail/row, table and detail scrolled to their ends |
| `playwright-02/conflicts-scroll.png` | Page scroll reaches conflicts; wrapped prose and JSON readable, preceding selection preserved |

CLI inspector screenshots use 1500×1600 to expose selected details. Text/controls do not overlap or clip in the inspected desktop views. The board Ref and embedded stack labels are small at overview scale; the table/detail text and full-size linked SVG supply readable inspection text. Long tables/details use intentional internal scrolling; lower content is below the viewport, not lost. Red/orange geometry overlaps are source conflict/reservation overlays, not evidence of fit. No missing assets or mismatched board/face/detail association observed. Mobile, other browser engines and every possible selection were not visually audited.

## Negative capture evidence and logs

`run-01/three-compact-scroll.png` and `run-02/three-compact-scroll.png` contain a large blank upper region after programmatic page scroll in Chrome CLI capture. They are **rejected visual evidence**, even though interaction assertions passed. A 100 ms settle plus 2000 ms virtual-time budget did not cure it; these ineffective additions and CLI scroll capture were removed. Successful Playwright capture of the unmodified page establishes usable scrolling without an application patch; the internal Chrome CLI cause remains unconfirmed. Duplicate initial successful PNGs were omitted; run-01 receipt/stderr and its negative scroll PNG remain.

All CLI stderr is retained per view. `stderr-summary.json` groups the observed messages: Mac CVDisplayLink -6670, allocator notices, task-policy errors, a default Gmail web-app install failure, and Mach rendezvous/parent-ended messages. These are browser/platform diagnostics, not silently discarded application errors. Chrome still exited 0 and completed assertions/captures; no permission/profile startup failure was observed. All real application/resource error arrays are empty. Prior Cloud timeouts from #263 are historical and were not retried on WSL.

`SHA256SUMS.json` hashes the retained evidence (except itself). Screenshots prove these rendered states only. Installed mechanical fit, tool access, cable clearance, exact-body qualification and hardware safety remain unvalidated/open. Keep the topic PR unmerged and #263 open pending review/integration; PR #260's description and all broader issues remain under their existing owners.
