# Issue 38 continuation: isolated native fixtures and K recovery

## Entry state — 2026-09-30

Continue from `f5ae36b` / routing fix `57084d0` in the preserved
`topic/38-jack-halves` worktree. Root main remains at `fac9929`. Incoming WIP
and all recovery caches remain intact. Baseline `pnpm circuit:check` passed:
manual inventory, 49 lines, zero declared placements, no schematic/placement
binding, pin-asset check performed. Guarded aggregate regeneration check passed
in 213 s with no tracked diff change; no regeneration commit was needed.

The jobs queued by the previous turn both ran and returned real FAIL verdicts:

- Native prerequisite suite: exit 1, 45 s, minimum available memory 5827 MB.
  Core metadata fixture had 199 extra-footprint parity entries (182 headers,
  17 terminals). The first three standalone native regressions passed.
- K resume with explicit OPENBLAS/OMP thread limits: exit 1, 201 s, minimum
  available memory 1867 MB. The mesh key matched, but the strict checkpoint
  run-key comparison refused restoration. No final result/profile was emitted;
  the 188 original batches through profile 1504 were preserved.

Neither is an environment deferral or a demonstrated electrical limit failure.
The queued status in the earlier handoff is historical and superseded here.

## Native fixture repair and result

The new isolated fixture runner copied the root schematic/project without the
41 referenced sheet files. `core_fields_native_regression.py` now mirrors the
complete schematic hierarchy beside the fixture, retains the bytes unchanged,
records every copied sheet hash, refuses pre-existing fixture copies, and checks
both source and copy hashes before emitting a receipt. Canonical circuit,
component, footprint and panel geometry remain unchanged.

The guarded four-regression suite passed in 64 s (minimum available memory
5623 MB). Core positive parity is zero across all 3594 packages; the intentional
mixed-unit field mutation produces exactly one parity issue and is rejected.
All terminal-access positive/negative assertions and the two-layer native export
regression passed. These are metadata/source-bound native fixtures, not routed
or qualified hardware. Core geometry warnings/open nets in this deliberately
unplaced metadata fixture are not a PCB acceptance result.

Receipt: `.circuit-cache/native-prerequisites.zmTi0T/core-fields/receipt.json`,
SHA-256 `a9123d03398dab761e061cf7b5e86b032999760542a9c73c3f5631b7c27619c8`.
Historical failure remains in `.circuit-cache/native-prerequisites.2XZNHv/`.
Log: `/tmp/osc38-native-prerequisites-fixed.log` (also retain in the review cache).
Post-fix evidence validation passed. No component identity or publication
selection was changed.

## Exact K launch recovered; admission pending

The original 2026-09-29 22:43:55 UTC launch was recovered from the project's
prior session record. It used the same pinned venv, v7 native files, source
manifest, output stem, adaptive mesh, full loads/main strands and full port set,
but did not force OPENBLAS_NUM_THREADS or OMP_NUM_THREADS. The reconstructed
command in the previous turn added both as 1. This is a candidate cause of the
operand-key difference, not a proven explanation yet.

The original command is now running under the same guard with a 14400 s run
bound and 6000 MB admission requirement. Guard label:
`issue38-core-full-original-command-recovery`; tool session 15022; guard PID
4162729 and Python PID 4163286 at initial observation. Script:
`.circuit-cache/review-20260930/resume-k-original-command.sh`; log:
`.circuit-cache/review-20260930/k-original-command-recovery.log`.

The source-bound mesh was reused. Rebuilt-operand/checkpoint admission and new
profile progress are still pending. Keep solver/native dependencies frozen.
Never rewrite a stored run key or rebind a historical result to force recovery.
Source/profile/library/operand identity and all existing residual/final gates
remain enabled. No numerical or physical acceptance is inferred from a mesh hit.

Issue 38 and its unchanged power/ground/current/voltage gates remain OPEN;
downstream board groups are not authorized as completed dependencies. Physical
qualification 55/57/64/65 is NOT RUN; exact protection 59 remains OPEN. No orders,
fabrication exports, supplier contact, deployment or credential access occurred.

## Recovery admission succeeded

The original launch configuration matched the stored run key
`7d21a6bc0c3128f9b6e682f127854811994646255662f6511ab88903832f27b3`.
The driver printed `current restored profiles 1504 / 2287` and has committed
new current batches under that same key. No checkpoint, model source or
numerical gate was modified to obtain admission. The earlier thread-limited
reconstruction is a failed historical attempt, not the continuation command.

Latest observed persisted coverage: **1560 / 2287 current profiles**, 195 committed batches; the newest payload hash matches its manifest. Recent new batches have reported residuals below the unchanged 1e-8 A gate. Full current/potential matrices, final bracket checks and a terminal guard verdict remain pending. This is live numerical progress, not a completed or physically accepted result.
