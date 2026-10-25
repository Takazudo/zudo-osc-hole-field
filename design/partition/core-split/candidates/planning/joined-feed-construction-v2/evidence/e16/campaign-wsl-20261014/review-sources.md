# Independent source and retained-evidence review — PR272 / PR273

Review date: 2026-10-14 JST. Method: separate Codex review agent, read-only repository/GitHub inspection, `git show` of exact commits, synthetic source-selector execution, SHA-256 verification, and direct screenshot inspection. No browser, native, numerical, or production execution was launched. No checkout files, branch tips, or integration refs were changed. Git fetched the two exact PR heads to make reviewed objects available. Cache extraction is under `mac-review/` alongside this note; remote JSON and complete patches are `pr272.json`, `pr272.diff`, `pr273.json`, `pr273.diff`.

## Exact source incorporation

PR272 remains OPEN, head `3de64799d1402a469e9e73666bb83d2841283abf`; no PR comments/reviews. Incorporate its three commits in sequence with provenance, subject to coordinator clean candidate and focused verification:

1. `810a9dd6c1e1ed25c49c1b4eee0f0040ee6b43ce` — test fixture authority isolation.
2. `8528c3211cc2e295ed1f2207653f2ca6eaccb10e` — source-only Python selection.
3. `3de64799d1402a469e9e73666bb83d2841283abf` — bind exclusion to both discovery roots.

PR273 remains OPEN, head `78467f6adbb5466a5332239583c93c5b8e249e3b`; no PR comments/reviews. Incorporate:

1. `7466ae6a5f4de339988101b8288abe092379454b` — launcher/assertions/tests and mechanical README.
2. `78467f6adbb5466a5332239583c93c5b8e249e3b` — retained browser evidence.

No production numerical executable or application/generated mechanical asset change occurs in these five commits. No blocking source correctness finding found for incorporation. Preserve clean-head execution independently; do not cherry-pick into a running execution checkout.

## PR272 review and necessary coverage

The fixture patches exactly production `CI_KEYS` and `AUTHORITY_KEYS` to empty values using `patch.dict`, registers `stop` with `addCleanup` immediately after start, and does not change production authority logic. Restoration runs after test failure and failures in later setup. `no_mixed_authority` is unchanged and the new test explicitly supplies `GITHUB_RUN_ID` to prove mixed authority refusal.

`model()` moved from class-level setup into the exact oracle test. Thus the strict-threshold neighboring test no longer initializes a vendor model. Importing the module merely imports model/verdict; the source-only runner excludes the oracle before executing the suite.

The selector flattens nested suites and matches both exact unprefixed and suffix-prefixed oracle identities. It requires exactly `cells.<oracle>` in `design/spec` and `<oracle>` in `design/spec/cells`, and no oracle identity in any other root. Missing, duplicate, wrong-prefix, and unexpected-root identities fail before running any tests. The rest of the suite remains selected.

Independent synthetic checks executed from the exact PR head source: eight PASS, retained in `selector-review.json`. Covers both expected identities, missing/duplicate/unexpected prefix/unexpected root, clean unrelated root, nested suite. No native process involved. The PR has no committed selector tests, so these are useful focused regression additions. Also retain same-process clean/CI-contaminated LocalStagingTests with exact parent-environment restoration assertions; explicitly exercise the neighbor while patching `model()` to fail if invoked. Existing evidence alone is not the combined-source rerun.

Recommended source commands on the isolated combined candidate:

- From numerical source directory: `python -m unittest test_native_validation.LocalStagingTests test_native_validation.StagingTests test_native_validation.RequestTests`.
- Same LocalStagingTests under CI-like GitHub and parent keys; assert the entire authority subset equals its pre-run mapping afterward, including absent versus empty values.
- Pinned Python dependency interpreter: `python -m unittest test_native_validation test_numerical_unit_guard test_numerical_acceptance test_replay_steps test_refined_solve test_finite_adapter` in that source directory.
- After selector tests and dependency/history checks: shared heavy guard around `bash scripts/checks/run-python-tests.sh`. This is source-only aggregate discovery only after all three PR272 commits are present. Record actual count and two explicit oracle exclusions.

The excluded exact obligation is `design.spec.cells.test_sweep_precision_vendor.PrecisionVendorSweepGate.test_original_network_returns_nonzero_for_supported_failure`. It invokes native ngspice via the pinned KiCad wrapper and remains NOT RUN under this campaign. Inspection of `scripts/checks/run-ci-native-python.sh` finds no explicit call to that test; do not claim exclusion automatically moves it to the admitted suite. Separate documented exact native admission is still required.

## CI and broad regeneration

At PR272 head, Documentation checks succeeded. Python unit-test job and all three Native DRC jobs failed. Remote PR body records 1,737 selected source-only cases succeeded, followed by native admission refusal for missing exact parent run identity. Overall red jobs remain red; no native success inferred. PR273 has zero check records because its commits deliberately contain `[skip ci]`.

`.github/workflows/check.yml` triggers on pull requests and pushes to main. Updating the integration PR head can schedule Python/native gates. Ordinary Python step uses the audited selector once integrated; native steps still require exact admission. Native DRC job uses `if: always()` and can run its refusal gate after failures. Prefer skip-ci commit metadata for this campaign's safe push if suppressing forbidden native jobs; never waive required checks or advertise skipped checks as pass.

`regen-all.sh`, including `--check`, runs generators, canonical schematic generation, cell harness, exports, monitor native scripts and KiCad WRL checks. It is not a read-only source-only gate. Do not run in this scope. Documentation build/check commands and mechanical `build.py --check` are distinct applicable checks.

## PR273 source review and provenance

Launcher discovers an explicit executable or CHROME_BIN without silently falling back from an invalid configured value. Standard candidates cover macOS and Linux. Profiles are unique temporary directories, output directory creation is exclusive, Chrome sandbox stays enabled, each process uses a separate session, and TERM/KILL target only that process group. CLI process wait is 60 seconds; version probe is 10 seconds. Timeout and nonzero tests exercise process cleanup. It does not enforce acquiring the shared guard itself; invocation/receipt correctly uses the existing guard. Do not launch it unguarded.

Browser assertions inspect every alternative/board row inventory, both faces, selected full object/title/Ref, reset after face/board/alternative changes, 100 unique Refs per alternative and union=100, all ten SVG loads, filtering, courtyard controls, and internal scrolling. The supplemental script separately drives real Playwright select/click input against the unmodified inspector and confirms page/table/detail scroll positions. Browser context uses `chromiumSandbox:true`, launch 20 seconds, actions 5 seconds, and enclosing Python 60-second cleanup. It does not rely on syntax-only acceptance.

Low-priority reusable-helper limitation: `review_scroll.py` opens sibling stdout/stderr with `w` before the child refuses an existing output directory. Reusing an old output name could truncate sibling logs, although actual retained runs used fresh names and hashes are intact. No rerun is necessary for evidence validity; if reusing the helper later, exclusive-create those logs / reject existing output before opening them and add a focused regression.

Evidence verified:

- All 61 entries in `SHA256SUMS.json` match bytes at `78467f6`.
- All 19 `final/receipt.json` input hashes match `78467f6`.
- All 17 application/generator/generated input hashes, excluding the two checker files, also match `9f69cd8`. Thus application evidence is unchanged from numerical baseline to PR273 delivery.
- Final receipt is committed checker SHA `7466ae6`, Darwin, Chrome 155.0.8059.40, guard held, 60-second bound, exit 0, 2.116 seconds, PASS, no errors, 500 alternative-specific rows and 100 physical trimmers.
- Supplemental receipt is baseline SHA `9f69cd8`, not committed checker SHA. Its script was supplemental working source, retained with evidence; it reports all 13 board combinations and both faces, PASS, no errors, page/table/detail scroll values 1230/459/360.
- Earlier run-01/run-02 record 12/13 captures; all process exits 0, each under 4 seconds. Their assertion PASS does not upgrade rejected CLI scroll screenshots.
- Failed supplemental initial run retains the exact `RV01106` versus `RVO1106` locator timeout. Corrected helper derives the Ref from source data.
- `checks.json` and source logs report 22 focused tests (6 launcher tests), generated-byte check and circuit check, all PASS on Mac. Combined candidate still needs its own source-only tests.

Directly opened six representative screenshots: `final/three-compact.png`, `playwright-02/selected-last-row.png`, `run-02/three-compact-scroll.png`, `run-02/three-compact-back.png`, `run-02/three-compact-reset.png`, `run-02/three-compact-exploded.png`. The final/front and KB/back selected Ref/title/detail agree; reset clears detail/highlight; exploded dimensions/caveats are legible; Playwright last-row selection and scrolled details are visible. The rejected CLI image visibly contains the reported large blank upper region. Retained author visual notes cover remaining alternatives/KC/assembled/views. This independent review is six screenshots, not a claim to have rerun Mac or independently opened every screenshot.

Combined asset reuse strategy: hash every final receipt `input_sha256` path in the combined candidate and compare. If only added tests/docs/evidence changed, all 19 remain exact. Keep original Mac SHA and note impact-scoped reuse. Do not modify historical receipts/README/SHA256SUMS merely to update integration disposition; add a new integration note outside that evidence bundle.

Source commands on combined candidate: `python -m unittest discover -s design/partition/core-split/mechanical -p 'test_*.py' -v`; `python design/partition/core-split/mechanical/build.py --check`. Browser/native reruns NOT RUN; no changed relevant asset warrants them.

## Issue disposition

Issue263 is OPEN. Its original closure criterion is a successful real-browser run and screenshot/SVG review; latest comment explicitly leaves it open pending review/integration. On verified incorporation into PR260 with unchanged tested assets, those narrow browser criteria are met and closure can state browser complete, source/evidence independently reviewed, incorporated by exact integration commits. This is not mechanical acceptance. PR272/273 were not merged; report source incorporation by cherry-pick if used. PR260 remains draft/unmerged and issue253 open.
