# Read-only aggregate regeneration timeout diagnosis

Head inspected: 0755535b46939c82d70703277b347bc4ebb7252a. No repository changes, native regeneration, CI retries or timeout changes made.

## Exact runs and timings

| Run / head | Python tests | Aggregate regeneration | Job result |
| --- | ---: | ---: | --- |
| 39139211137 / 49cb773954a24439f0fd302f5937c5a1a9aca013 | 621 s | 341 s, completed | success, 19m04s |
| 39141920865 / b81d0a19f18168a4da9578ef2d155b809ec40cd4 | 1053 s | 507 s, interrupted | cancelled, 30m14s |
| 39144277825 / 0755535b46939c82d70703277b347bc4ebb7252a | 1062 s | 497 s, interrupted | cancelled, 30m14s |

Decoded full logs retained at /tmp/osc-ci-timeout-{green,first,second}.log. Original GitHub jobs: 117709964584, 117717916608, 117724826265 respectively. All three runs used Ubuntu image 20261012.334.1 and runner2.337.0; green was centralus, both later runs eastus. Region is correlation, not proof of the performance cause.

## Where cancellation occurred

Exact workflow command: `bash scripts/checks/regen-all.sh --check`, within the existing 30-minute Python job. Both reached `bash scripts/schgen/smoke.sh --generated`.

First: instrument ERC PASS at16:15:25.038; netlist verification PASS at16:15:39.355; cancellation16:15:46.186. The next command is `python3 scripts/schgen/audit_master.py "$scratch/netlist.net" --check`; no completion message appeared. This is the likely interrupted child, inferred from sequential shell order, not a traced process record.

Second: instrument ERC PASS at16:46:55.983; cancellation16:47:05.609 before netlist verification PASS. The outstanding portion was native netlist export and/or `verify_netlist.py`. Logs do not identify which process was active, so an exact leaf beyond this interval cannot honestly be asserted.

Green: ERC PASS15:27:54.123, pin-net PASS15:28:02.575, master audit PASS15:28:06.869, mutation control PASS15:28:11.014; then exports, monitor checks and final WRL check completed15:28:42.268. Both cancellations occurred near the end of a progressing pipeline, not inside the large floorplan computation.

## Work added versus existing cost

The preview adds two source tests: panel suite14→16 tests,1.092→5.698/5.718s. Its browser suites are outside scripts/design discovery; aggregate regeneration does not invoke the new preview builder or tessellator.

Unchanged architecture suite1281 tests:387.197→663.379/673.955s. Even exact frozen Stage34 replay (14 tests, original9d9aa404 checkpoint) increased75.294→136.901/140.273s. Existing pcbgen662 tests increased55.609→88.884/88.717s. This broad slowdown is consistent with lower runner throughput; hardware/CPU telemetry is absent, so its cause is not proven.

`python3 scripts/checks/partition35_floorplan.py` consumed197.255→326.761/327.277s, measured between its predecessor and its own completion message. It completed successfully with identical reported package counts. This accounts for most aggregate work and is not new preview work.

## Unchanged output evidence and unnecessary regeneration

Git comparison49cb773..HEAD reports no changes in the workflow, aggregate wrapper, geometry/library/schematic/partition/native generators, design specifications/reports, schematic exports, boards, footprints or circuit evidence. Changes are preview/editor files and scripts/panel/test_component_preview.py. The prior green aggregate run completed its final tracked-output comparison; the retained native outputs and their source inputs remain identical. This establishes preserved historical output evidence, not completion of a fresh native run on the current head.

`regen-all.sh --check` does not select affected generators. It invokes each generator in write mode, then compares the before/after tracked diff. `partition35_floorplan.py --check` also calls full build() before comparison; switching to --check alone will not save its327s. There is no complete persistent input/output digest receipt for that computation. Its lru_cache only memoizes footprint reads within one process.

## Recommendation before changes

Smallest conservative correction: move the unchanged aggregate command and its drift-artifact handling into a separate job with the same30-minute limit and pinned environment, starting from a fresh checkout. Keep every assertion and generator. The measured complete aggregate cost was5m41s on the successful runner; later runs reached8m17s/8m27s before cancellation near the end. Roughly9–10minutes on those slower runners is an estimate, not a completed measurement. The current problem is sharing one30-minute budget with18minutes of tests and other native checks. No timeout increase or output/cache trust policy is necessary. Verify that the fresh job reproduces the same prerequisites, and keep deterministic clean-output comparison.

A narrower runtime optimization could reuse the unchanged floorplan/native evidence, but only after adding a complete source/tool/output digest binding and mutation tests that fail closed. It would save work unrelated to preview edits, but is more semantic change than separating the existing command. Do not simply bypass generation on a green status, a timestamp, or a partial path list.

Any workflow edit also needs the reviewed historical-context binding updated: architecture_history.py explicitly pins .github/workflows/check.yml to ed3a6612. Do not loosen that guard or rewrite historical assertions. Add per-command start/end timing if exact future leaf-process attribution is desired.

## Authorized correction

The follow-up separates aggregate regeneration into an independent 30-minute job.
Its checkout, Python/Node pins, numerical/browser setup, exact regeneration shell
command and drift artifact upload are copied unchanged. The other worker retains
all unit and native commands. The existing `Python unit tests` check name becomes
an `always()` gate requiring both worker results to equal `success`; failure,
cancellation, skipped and absent results fail. Documentation and DRC jobs are
unchanged. No timeout increase, historical skip or cached-output trust is added.
This duplicates checkout, setup, dependency/browser installation and native image
pull work on two disposable runners, trading extra runner resources for separate
bounded execution budgets. It does not prove a physical or hardware result.

Workflow regression tests compare both workers against the immutable pre-split
0755535 checkpoint, preserving all original commands and setup. They execute the
actual gate shell over all 25 pairs of success/failure/cancelled/skipped/missing
results. Local normal and optimized runs pass four tests each. Actionlint 1.7.7
passes (`-shellcheck=`: shellcheck is not installed; gate shell is exercised by the
regressions). The initial `go install` attempt failed because this environment's
`go` executable is not the Go compiler; the official prebuilt actionlint release
was used instead. No repository dependency or tool version changed.

The historical adapter's ten current-context paths remain byte-bound to an exact
commit containing the reviewed workflow split; seven original checkpoints and
all eight historical modules remain unchanged. Updating this pin is an explicit
context-policy review, not a new exemption. Local native regeneration is NOT RUN;
exact-head GitHub CI supplies the fresh aggregate/native result separately.
