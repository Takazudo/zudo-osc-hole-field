# Design decision T2 (#311) and T3 (#308) — campaign osc-cloud-20261111

Design authority decision, 2026-11-11. Read-only review of `claude/project-thread-vkfz17` (base `ebfbc094`). Nothing was edited, run natively or dispatched. Every board stays an unvalidated draft. Paths are relative to the repository root.

## Citations in exec-budget-design.md hold, with three corrections

Verified by reading: `chain.py:37,54,72-78,85,103-121`; `route_jack_grid.py:126-142,621-627,640-647,653-699,712-740`; `complete_native_warnings.py:91-133,214-277,283-300,303-346`; `audit_added_mask.py:209-304`; `local-transactions.yml:45-48,67,88,90-93,105,175`; `budgets.json`; README `:89-100,:120`.

1. **Report hashes cannot match across runs.** KiCad's DRC JSON carries a `date` field (`boards/osc-core/reports/drc.json`), so the design note's control 1 ("`report_sha256` must match byte for byte") is unachievable. Equivalence is on fixture bytes and normalised report content (below).
2. **Run-step timeout 160 is wrong.** With setup 10 and collection 10 inside a 170 min job, the run step may be at most 150. Use 150.
3. **`resumable_audits` cannot yet take a reused `holes-before`.** It matches on `source_sha256` only inside an `added-copper-scope.json` bound to the same before/after pair (`:285-288`), so reuse across candidates is a real trust-binding change, not a config change.

---

# T2 (#311) — sharded complete-warning audit

## Sharding the silk audit is equivalent to the monolith, under five conditions

Fixture *i* is a pure function of the after-board bytes, `.kicad_pro`, `.kicad_dru` and added object *i* (`audit_added_mask.py:241-275`); each DRC is a fresh `kicad-cli` process (`:287`); no state passes between fixtures except the `identities` union and the `receipts` list, both order-independent sets/concatenations. The unchanged `complete_reports` already proves exact-once coverage against a recomputed scope, per-fixture report and context hashes, and identities recomputed from raw reports (`:244-267`).

Conditions:

1. Every shard runs the monolith's **global** preconditions on the full boards (`:215-236`, `:262-264`): non-routing invariance, scope, project/rules equality, no custom silk/mask rule, mask healing 0, no mask zones or mask artwork, native scope == source scope, via count.
2. Index *i* means the same object in every shard: `sorted(added, key=uuid)` (`:276`), bound by a hash of the ordered UUID list.
3. Range starts are multiples of `PROBE_BATCH` (32), so probe batches are identical to the monolith's.
4. All shards share one tool commit, one image digest, one before/after/project/rules/removal-scope hash set.
5. One host-side assembly rebuilds the existing `native-audits/` layout and the **unchanged** `complete_reports` re-verifies the whole tree.

Not equivalent byte for byte: `report_sha256` and `drc.json` (date). Everything else in `silk/result.json` must be identical.

## Scope for now: silk is sharded; holes and zones run whole; holes-before reuse is deferred

| Sub-audit | Decision |
| --- | --- |
| `silk` | Fixed-range shards, new `--fixture-range` |
| `holes-before`, `holes-after` | One job each, script unchanged |
| `zones` | One job, script unchanged, `--classify --batch-size 16` as `route_jack_grid.py:654` defaults |
| holes-before reuse across candidates | **Deferred.** It changes the binding in `resumable_audits`, the K2518 evidence sits in the unreachable WSL archive, and its saving is unmeasured |
| per-zone sharding (`--zone UUID`) | **Deferred.** Zone resume is refused with removal scopes (`complete_native_warnings.py:331-332`), so a zone job that does not fit is a NEEDS_DESIGN stop, not a retry |
| fixture-level resume inside a silk shard | **Deferred.** A failed shard reruns whole |

## Goal and non-goals

- **Goal.** Produce, from bounded jobs, a `native-audits/` tree that `audit_current_reports(..., resume_from=<tree>)` accepts with zero native calls and that `complete_reports` verifies unchanged.
- **Non-goals.** No change to `complete_reports`, `hole_evidence`, `zone_evidence`, `resumable_audits`, `warning_complete_gate`, `promotion_gate`, `check()`, `chain.py`, `run.sh`, `pin.env`. No adoption, no promotion, no push, no K2226 run (T4), no time-limit change elsewhere.

## Allowed files

| File | Change |
| --- | --- |
| `scripts/pcbgen/audit_added_mask.py` | `--fixture-range START:END`; additive `fixture_sha256` per fixture row (the already-probed `view['sha256']`, `:280`), in monolithic mode too; in range mode write `shard-result.json`, never `result.json` |
| `scripts/pcbgen/warning_shards.py` (new, host-only, no pcbnew import) | `plan`, `run-unit` (wraps `bash scripts/kicad/run.sh python3 …` and writes the host receipt), `assemble` |
| `scripts/pcbgen/test_warning_shards.py` (new) | Host-only tests and negative controls with faked pcbnew/kicad-cli, reusing `test_audit_added_mask.board/item` |
| `scripts/pcbgen/test_audit_added_mask_probe.py` | Range-mode cases |
| `scripts/pcbgen/fixtures/warning-shards/` (new) | Small committed triple `before/`, `after-clean/`, `after-planted/` (each `.kicad_pcb`, `.kicad_pro`, `.kicad_dru`), deterministic builder script, `manifest.json` of sha256, README. ≥70 added objects so ranges are 32/32/rest; `after-planted` has one via under silk |
| `.github/workflows/warning-audit-shards.yml` (new) | Below |
| `scripts/pcbgen/README.md`, campaign `plan.md` | Wording and task state only |

Any other file → NEEDS_DESIGN.

## Shard mode contract (`audit_added_mask.py --fixture-range`)

- `START % 32 == 0`, `START < END <= N`; otherwise exit non-zero before any fixture.
- Folders keep the global name `fixture-{i:03d}`.
- `shard-result.json` reuses the `result.json` keys with these differences: `status = 'SHARD ONLY; NOT COMPLETE EVIDENCE'`; **no** `added_copper_scope_complete` key (so `resumable_audits:296-299` can never accept a shard); `fixtures` and `new_mask_identities` cover the range only; plus `fixture_range`, `fixture_total`, `ordered_scope_sha256`, `project_sha256`, `rules_sha256`.
- Written once, at the end. A killed shard leaves no receipt.
- Removal scope: same `--stage-removal-scope` / `--reviewed-cut-uuid` arguments as `removal_arguments()` produces.

## Each unit receipt binds these fields

In-container (written by the audit script), existing keys reused:

- `version` (`10.0.6`), `before_sha256`, `after_sha256`
- `project_sha256`, `rules_sha256`
- `added_copper_source_scope` (full scope), `ordered_scope_sha256`, `fixture_total`
- `unchanged_nonrouting_objects`, `added_unmasked_tracks`
- `reviewed_copper_removals`, `copper_removal_source` when cuts exist
- `fixture_range`
- per fixture: `copper_uuid`, `kind`, `native_mask_signature`, `selected_native_bbox_uuids`, `conservative_bbox_margin_nm`, `violations`, `report_sha256`, `fixture_sha256`

Host (`warning_shards.py run-unit`, written beside it as `unit-receipt.json`; same file for the holes and zones units):

- `unit` (`silk:START:END`, `holes-before`, `holes-after`, `zones`) and the exact command argv
- `tool_commit` (40 hex) and sha256 of each tool file executed: `audit_added_mask.py`, `audit_hole_pairs.py`, `audit_zone_silk_scope.py`, `zone_batch_evidence.py`, `zone_batch_resume.py`, `uuid_tools.py`, `copper_identity.py`, `scripts/kicad/run.sh`, `scripts/kicad/pin.env`
- `kicad_image` from `pin.env` **and** the digest `docker image inspect` reports for it; `oracle_mode` must be `docker`
- `before_sha256`, `after_sha256`, `project_sha256`, `rules_sha256`, removal-scope file sha256 or `null`
- input provenance: `before_commit`, `before_dir`, `after_commit`, `after_dir`
- sha256 of `shard-result.json` / `result.json` and a sha256 manifest of every file in the unit directory
- `github_run_id`, `run_attempt`, job name, start/end UTC, wall seconds, peak memory, runner image

## The assembler rejects all of these

1. Silk ranges that do not tile `0..N-1` exactly once: gap, overlap, duplicate, wrong `fixture_total`, unaligned start.
2. Any difference between units in: `tool_commit`, tool file hashes, `kicad_image`, inspected digest, `oracle_mode`, `version`, before/after/project/rules/removal-scope hashes, `ordered_scope_sha256`, full scope, `unchanged_nonrouting_objects`, `added_unmasked_tracks`.
3. Any of those not equal to the assembler's own host recomputation: file hashes, `added_copper_scope`, `reviewed_copper_removals`, `sorted(scope)` hash, `pin.env` image.
4. `fixtures[i].copper_uuid != sorted(scope)[i]`, or kind mismatch.
5. A unit directory whose file manifest does not verify, or a `drc.json` whose sha differs from `report_sha256`.
6. A retained fixture board whose sha differs from `fixture_sha256`, or whose top-level `segment`/`via` blocks are not exactly the after-board block of that `copper_uuid`, or that contains any `zone` block or `pad`.
7. A unit with no terminal receipt, a `STARTED` marker only, or a second receipt for the same unit from another attempt.
8. A `result.json` already present in a silk shard directory, or a shard receipt carrying `added_copper_scope_complete`.
9. A holes or zones unit that is not the unmodified script's complete `result.json` for these exact hashes.

On success it writes `native-audits/{added-copper-scope.json,holes-before/,holes-after/,silk/,zones/}` exactly as `audit_current_reports:321` and the audit scripts would, plus `assembly-receipt.json` (all unit receipt hashes, tiling proof, tool commit, image digest). `silk/result.json` gets `status` and `added_copper_scope_complete: true` from the assembler only. The assembler never writes `proof.json`; only `audit_current_reports` does.

## Mandatory controls before a sharded result may be used for adoption

Host-only, in the ordinary test run (faked native), every one a failing-closed assertion:

1. Missing shard / range gap → assembler rejects; a hand-built tree with the gap → `complete_reports` raises `silk audit omits added copper`.
2. Overlapping or duplicated range → rejects.
3. Unaligned start, `END > N`, wrong `fixture_total` → rejects.
4. Shard from a different after board; from a different before board → rejects.
5. One shard with a different image digest; different tool commit; different `.kicad_dru`; different `.kicad_pro` → rejects.
6. Tampered `drc.json` → rejects in the assembler and in `complete_reports` (`silk fixture report hash mismatch`).
7. Two fixture folders swapped → rejects on `fixture_sha256` / copper block.
8. Fixture board with an extra copper block or a retained pad → rejects.
9. Shard directory passed straight to `resumable_audits` → not accepted as `silk`.
10. Shard killed before its receipt → rejects.
11. Assembled tree → `audit_current_reports(resume_from=tree)` makes zero `run.sh` calls and reaches `complete_reports`.

Native, on the pinned image, on `scripts/pcbgen/fixtures/warning-shards/`, recorded as a receipt for the exact tool commit later used:

12. **Equivalence, clean pair.** Monolithic `audit_current_reports` vs sharded (32/32/rest) + assembled, sharing the same holes and zones directories. `silk/result.json` identical after dropping `report_sha256`; every `drc.json` identical after dropping `date`; `proof.json` identical except the silk entry of `audit_result_sha256`.
13. **Equivalence and positive control, planted pair.** Both arms report the same non-empty `new_mask_identities` and both end in `new complete native silk warning identities`. A sharded arm that passes is a tool defect.
14. **Capped fixture.** A fixture at 199 silk rows fails the shard (`:162-163`), not just the assembly.

Controls 12-14 are NOT RUN until executed on the image; unit tests do not stand in for them. Without all fourteen the sharded result is not admissible for T4.

## Workflow: new, dispatch-only, read-only, artifact-only

`.github/workflows/warning-audit-shards.yml`:

- `on: workflow_dispatch` only. `permissions: contents: read`. `persist-credentials: false`. No commit, no push, no PR, no cache write of board bytes. Actions pinned by SHA as in `local-transactions.yml`.
- **Code and data are separate checkouts.** Code is `github.workflow_sha` (`tool_commit`). Data comes from `before_commit`/`after_commit` into a separate directory, is never executed, and is copied to `.circuit-cache/warning-shards/<label>/{before,after}/` so `run.sh`'s `/work` mount sees it.
- Inputs: `label`, `board_name`, `before_commit`, `before_dir`, `after_commit`, `after_dir`, `expected_before_sha256`, `expected_after_sha256`, `shard_size` (multiple of 32), `mode` (`pilot` | `full`), `pilot_ranges`.
- Jobs:
  - `prepare` (host, ≤10 min): validate inputs, both commits 40-hex and fetchable, hashes equal the expected values, host-only `added_copper_scope` → N, emit the unit matrix and `plan.json`.
  - `unit` (matrix, `max-parallel: 4`, `fail-fast: false`, `ubuntu-latest`): `timeout-minutes` ≤ 330, native step timeout ≤ 300, leaving 30 for setup and upload. Uploads one artifact per unit with a sha256 manifest.
  - `assemble` (host-only, ≤60 min, `full` mode only, `needs` every unit): download, verify manifests, assemble, then run `complete_reports` on the tree as a cloud verification and upload tree + receipts. Its summary says `CLOUD VERIFICATION; NOT AN ADOPTION`.
- `pilot` mode runs only the listed ranges, no assembly, and marks its output `PILOT TIMING; NOT EVIDENCE`.
- Retry: "re-run failed jobs" at most once, only for a proven transient infrastructure failure; attempt number is in the receipt and a duplicate unit is rejected (rule 7).

Adoption is not this workflow's job. T4 places the tree at `.circuit-cache/osc-core-grid-osc3-<label>-complete-warnings/native-audits/` and runs the unchanged gate-only `chain.py … --resume-from` path, which re-verifies everything through `resume_evidence` → `resumable_audits` → `complete_reports` → `enforce_warning_completeness`.

## Inputs reach the runner as commits, not artifacts

An artifact needs a producing run and is not content-addressed for re-runs; a commit SHA is immutable, re-fetchable and auditable.

- **Tooling tests and controls 12-14:** `before_commit = after_commit = tool_commit`, directories under `scripts/pcbgen/fixtures/warning-shards/`. No K2226 bytes needed.
- **Timing pilot at real scale:** two commits already in `main` history that hold a jack board before and after an adopted stage, `mode=pilot`. No new bytes.
- **K2226 (T4, blocked on T1):** a data-only branch `audit-input/<label>` holding `circuit/audit-inputs/<label>/after/` (`.kicad_pcb`, `.kicad_pro`, `.kicad_dru`, `drc.json`, `dump.json`, `manifest.json`), never merged and never opened as a PR. The before side is the commit and path whose bytes equal the chain start (`chain.py:37`). Pushing that branch is an owner-approved manager action outside T2.

## Acceptance criteria

1. Controls 1-11 pass in `bash scripts/checks/run-python-tests.sh`; existing `test_audit_added_mask*`, `test_complete_native_warnings`, `test_route_jack_grid` pass unchanged.
2. `git diff --stat` touches only the allowed files; the non-goal files are byte-identical.
3. Monolithic mode output differs from before only by the added `fixture_sha256` key.
4. The workflow has `contents: read`, no write permission anywhere, no `git push`, and its job timeouts are ≤ 330.
5. Controls 12-14 have a retained receipt naming tool commit and image digest, or are reported `NOT RUN` with the reason.
6. Report states sizes: K shard size is **not** fixed by T2; it comes from a pilot shard, target p95 s/fixture × size ≤ 200 min.

## Verification commands

```sh
bash scripts/checks/regen-all.sh
pnpm circuit:check
python3 -m unittest scripts.pcbgen.test_warning_shards scripts.pcbgen.test_audit_added_mask scripts.pcbgen.test_audit_added_mask_probe scripts.pcbgen.test_complete_native_warnings -v
bash scripts/checks/run-python-tests.sh
git diff --stat ebfbc094 -- scripts/pcbgen/complete_native_warnings.py scripts/pcbgen/route_jack_grid.py circuit/reviews/osc3-k-signals/chain.py scripts/kicad   # must be empty
# native, one heavy process, manager VM or the new workflow:
python3 scripts/pcbgen/warning_shards.py plan     <before> <after> --shard-size 32
python3 scripts/pcbgen/warning_shards.py run-unit <before> <after> <out> --unit silk:0:32
python3 scripts/pcbgen/warning_shards.py assemble <before> <after> <units-dir> <native-audits>
```

## Stop and return NEEDS_DESIGN

- Any need to edit a non-goal file, or to relax a `complete_reports` check to make an assembled tree pass.
- Control 12 shows any difference beyond `date` / `report_sha256`.
- Fixture bytes are not deterministic across two runs of the same range.
- Zones or a holes unit exceeds 240 min in a pilot, or zone resume is needed while removal scopes exist.
- The K2226 board is ≥ 100 MB (GitHub blob limit), or the chain start bytes differ from every committed board.
- `run.sh` selects a native oracle instead of the pinned Docker image on the runner.
- A capped fixture (199 rows) on real bytes: needs fixture subdivision, a separate design.
- Pressure to add holes-before reuse, per-zone sharding or in-shard resume inside this task.

---

# T3 (#308) — OSC4 osc-core budget

## 80 → 140 is a legitimate correction, not a larger blind retry

The transaction's own definition requires five native checks (`transaction.py:120-123,136-140`; `route_jack_grid.py:397-398,494-497,528-533`) at 18-19 min each. The README already records that 80 min "reaches the fifth check but does not finish it" and leaves the decision to the manager (`README:96-100`). A budget that cannot hold the transaction's mandatory checks is a configuration defect: no run under it can ever produce a terminal receipt. Fixing it removes no check, changes no frame, expansion limit, refill count, stability rule or retry policy, and dispatches nothing.

It would become the forbidden case (`README:120`, `ORCHESTRATION.md:103`) only if used to re-run `osc4-k-agnd-r5243-2` on K2518, whose outcome is already known (candidate still 2518, no route for R5243.2, `README:140-142`). That run is therefore blocked in data, not only in prose.

## Goal and non-goals

- **Goal.** Budget, workflow limits, test and README agree, and one complete K transaction with one drop-and-retry reserve fits the job.
- **Non-goals.** No change to the five checks, `check()`, `max_refills=6`, `stable=3`, frames, expansion limits, the 8-attempt retry loop, `transactions.json`, jack budgets (60). No workflow dispatch. No local native run. No replan.

## Acceptable change

| File | Change |
| --- | --- |
| `circuit/reviews/osc4-local-transactions-20261107/budgets.json` | `osc-core: 140`; jacks stay 60; add `"holds": {"osc-core": "<reason text below>"}`; update `note` |
| `…/transaction.py` | `run` path only: refuse a board listed in `holds` with a distinct exit and message, before any native call. `--validate`, `--print-budget`, `--reconcile` unaffected. Update the budget comment (`:28-30`) |
| `.github/workflows/local-transactions.yml` | `JOB_TIMEOUT_MINUTES` 100 → 170 (`:48`); job `timeout-minutes` 100 → 170 (`:105`); run step 95 → **150** (`:175`); new `COLLECT_ALLOWANCE_MINUTES: "10"` added to the `prepare` sum; `max_minutes` input 1-140 (`:22`, `:67`, regex `^[1-9][0-9]{0,2}$`); budgets.json range 1-140 (`:88`); `prepare` fails for a board in `holds`; comments `:41-44` |
| `scripts/checks/test_osc4_transaction_signals.py` | `:92` 80 → 140 |
| `scripts/checks/test_osc4_transaction.py` | New tests below |
| `…/README.md` | `:89-100`, the run examples (`:108`, `83m` → `143m`, `HEAVY_GUARD_MAX_RUN` above 8700 s), `:294`-area and the `max_minutes` range near `:388` |
| campaign `plan.md` | T3 state |

Budget arithmetic the workflow must enforce: `140 + 3 + 2 + 10 (setup) + 10 (collect) = 165 ≤ 170`, and `145 ≤ run-step 150 ≤ 170 − 10 − 10`. The 140 comes from the phase table in `exec-budget-design.md` (five checks at 20-21 min, one 21 min retry reserve, routing 5, gate 3). The all-8-retries profile (257 min) is deliberately not budgeted: a transaction that needs it stops as `TIMED OUT; NOT ADOPTED`.

## Hold text and release condition

`holds["osc-core"]`: `"NOT ADMITTED: osc4-k-agnd-r5243-2 on K2518 already ran to a known non-improving result (README 2026-11-08). No OSC4 osc-core run until the K2226 adoption decision (#311) is recorded and a new plan is selected with extract_residuals.py / select_transactions.py --board osc-core on the then-canonical K board."`

The hold is removed only by the commit that installs that new `transactions.json` plan, with a new spec name and a new `input_board_sha256`. Removing it for the current plan is NEEDS_DESIGN. README wording must say the same thing and must keep the sentence "No transaction is retried with a larger frame, budget or time limit", adding: "The 2026-11-11 change to 140 min corrects a budget that could not hold the five mandatory checks; it is not a retry and admits no run."

## Tests to add

1. `budgets.json` invariant: for every board, `minutes + 3 + 2 + 10 + 10 ≤ JOB_TIMEOUT_MINUTES`, and `minutes + 5 ≤ run-step timeout ≤ job − 20`, read from the workflow file.
2. Job `timeout-minutes` equals `JOB_TIMEOUT_MINUTES` and is ≤ 330 (campaign per-job ceiling).
3. A held board: `transaction.py <board>` exits non-zero with the hold text and makes zero native calls; `--validate` and `--print-budget` still work.
4. The workflow `prepare` script rejects a held board (shell-level test or a parsed-YAML assertion that the hold check precedes the matrix output).
5. Existing signal tests pass with 140; jack defaults still 60.

## Acceptance criteria

- All of the above pass; `route_jack_grid.py` and `transactions.json` are byte-identical to `ebfbc094`.
- No workflow run, no native process, no receipt file created or changed.
- Report states: OSC4 K on K2518 `NOT RUN` (held), complete-warning evidence `NOT RUN`.

## Verification commands

```sh
bash scripts/checks/regen-all.sh
pnpm circuit:check
python3 -m unittest scripts.checks.test_osc4_transaction scripts.checks.test_osc4_transaction_signals -v
python3 circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core --print-budget   # 140
python3 circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core --validate
python3 circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core; echo $?          # refused by the hold, no native call
git diff --stat ebfbc094 -- scripts/pcbgen/route_jack_grid.py circuit/reviews/osc4-local-transactions-20261107/transactions.json   # empty
```

## Stop and return NEEDS_DESIGN

- The budget cannot be made consistent without touching a check, refill count, retry policy or `route_jack_grid.py`.
- A test or the workflow needs a job above 170 min, or a jack budget change.
- The hold breaks an existing test in a way that needs the hold weakened rather than the test fixture adjusted.
- Anyone asks to dispatch `local-transactions.yml` for `osc-core`, or to lift the hold, before the K2226 decision and a new plan exist.
