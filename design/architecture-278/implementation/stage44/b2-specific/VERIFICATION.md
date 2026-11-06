# Stage44 verification record

Native tooling is the existing task-local KiCad10.0.6 via
`source /workspace/task-tools/kicad-10.0.6/env.sh` and `bash scripts/kicad/run.sh`.
The retained official archive SHA256 is
`8c789e36644856cff30a66801692881582b9ca7c7475699494e614ce1bcb1f9c`.
Exact release does not establish bitwise Docker-oracle equivalence. Earlier
signature-key retrieval limitations remain unresolved. No tool installation or
Docker run was needed. Numerical routing uses the saved
`/workspace/shared/osc-ci-python/bin/python` environment.

All native/routing jobs ran through
`bash /home/agent/.codex/scripts/heavy-guard.sh --label <label> -- <command>`.
Actual drivers are copied into `evidence/commands/`; logs and large native
artifacts are bound in `evidence/local-artifact-bindings.json`. The guard's
process PASS alone does not accept DRC, routing or electrical results.

## Actual sequence and first failures

1. `branches.py` screens28 exact local supply retirements from the pinned Stage42
   board. Independent review checked all28, including all11 objects wrongly
   renetted by Stage43. Three external anchors remain. Old geometric contacts
   are only ownership evidence; final retained-partition equality is mandatory.
2. `placement-v1.sh` fails native clearance at R3204 pad2 versus a foreign via.
   The full report and board remain. `placement-v2.sh` uses +0.15mm Y and reports
   zero rule errors/parity,177opens. Its477warnings include the +5V anchor made
   temporarily dangling by removing its old local feed.
3. `power.sh` adds30objects for18paths; zero rule errors/parity,165opens. It does
   not by itself establish final connectivity. All required packages remain.
4. `route_anchor.py` proposes a real B.Cu R3202 feed to retained+5V anchor157,205.
   Destination membership is restricted solely to select that anchor; all
   obstacles stay. `anchor-apply.sh` applies14segments and reports zero rule
   errors/parity,164opens,476warnings. All uncapped warning identities match
   Stage42 at this point; there is no dummy anchor loop or deleted boundary via.
5. The first signal order misses C3203.1 on X4C67F313FD4F29BCBD2D. Its generated
   proposal is not accepted or applied. A separate priority-net retry at the
   same resolution/bounds routes all47links. The script can exit0 despite a
   failed link; the apply driver explicitly rejects any nonzero failed count.
6. `routed-check.sh` applies the complete proposal to a fresh copy, runs source
   and native identity checks before/after bound DRC/refill/save, complete native
   connectivity and all18power-path checks. First pass: zero rule errors/parity,
   117opens,476warnings; all24private targets closed; retained partitions equal.
7. `settle.sh` repeats refill/save, identity, complete connectivity and power
   checks twice, then on a separately loaded fresh copy. `settlement.py` binds
   each native result and DRC execution to the same final board, baseline
   dependencies, receipt and scope. Normal/optimized settlement outputs must
   be identical. All four passes completed and both settlement outputs are
   byte-identical; guard PASS, 623seconds. Saved board SHA256 is
   `d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73`.
   Final bound results are in `evidence/settlement.json`.

## Review-driven hardening

Preliminary independent review found two false-acceptance risks, corrected before
final native acceptance: receipt-provided moved-footprint hashes did not alone
protect non-property package metadata, and DRC JSON lacked execution bindings.
The package gate now replays only permitted native pose changes from the pinned
baseline and compares complete serialized packages. The DRC wrapper records exact
command, return code, pre/post board and dependency hashes, and report hash.
Settlement also requires clean/fresh dependencies to equal the accepted baseline,
rejecting a new DRC run under modified rules after a stale identity audit.
Mutation tests cover DNP/BOM flags, library ID, pad shape/size/local pose, model,
foreign DRC reports, changed rules with matching new execution receipts, incomplete
power evidence, membership drift, changed board, new warnings/errors and missing
package proof. Semantic DRC mutations refresh execution hashes so they exercise
the acceptance criteria, not merely stale-report rejection.

## Source checks and limits

The selected source suite runs95tests in normal and optimized Python. All seven
historical checkpoint bindings pass in both modes. `pnpm check` and
`pnpm circuit:check` pass. The latter remains manual inventory68lines/0declared
placements, no schematic/placement binding; the pin-asset check is performed.
Final compilation, whitespace and review-manifest checks are recorded with the
review. Long historical replay is left to the existing exact-head CI budget.
Canonical regeneration is not run locally under the explicit preservation
instruction. Baseline Stage43 run39210793513 passed all seven jobs and2869tests;
this does not substitute for Stage44's exact-head CI. Terminal CI is reported
on Issue278 after push, never predicted by this record.

The117 inherited opens remain unchanged by full native partition comparison.
Uncapped warning identities remain subject to strict nonregression. KiCad caps
both silk_overlap and silk_over_copper at199, so their sampled output cannot prove
exhaustive silkscreen equivalence. This is bounded disposable-native evidence,
not a full-board DRC pass. Physical fit/access, analog behavior, impedance, flex
life, current qualification and supplier/placement qualification remain unresolved.
No canonical adoption, fabrication, order, energization, release, deployment or
merge was performed. Earlier harness/service measurement requirements remain.
