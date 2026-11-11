# Execution-budget design for OSC4 K (#308) and the K complete-warning audit (#311)

Read-only investigation of `/home/user/zudo-osc-hole-field` at `ebfbc09` (main). Nothing was edited, run natively or dispatched. Every validation obligation is kept: settled refill, fresh-copy connectivity, complete warning identity, original connected-pad groups, and copper retention/replay. Paths are relative to the repository root.

---

# A. Issue #308 / OSC4 K transaction

## The five native checks are base, cut, candidate, stage verify and transaction fresh copy

Each native check is `route_jack_grid.check()` (`scripts/pcbgen/route_jack_grid.py:126-142`). It runs `kicad-cli pcb drc --refill-zones --save-board` plus `grid_dump.py` through `scripts/kicad/run.sh` (`:136-137`), repeats until 3 equal island signatures are seen (`:140`), and allows at most 6 passes (`:126`, `:141`). The README measures 3 passes at about 5-7 min, or 18-19 min per check (`circuit/reviews/osc4-local-transactions-20261107/README.md:96-98`, `:140`).

| # | Check | Where | Why it exists |
|---|---|---|---|
| 1 | Base | `transaction.py:120-123` | `before`/`before_drc` for `promotion_gate`: open edges, split pad groups and warning identities (`route_jack_grid.py:621-627`). It also writes `base/dump.json`, which `stage()` reads (`:383`, `:500`, `:515`, `:534`). |
| 2 | After the cut | `route_jack_grid.py:397-398` | The repair routes against the cut board's native islands (`:399-415`). |
| 3 | Candidate | `route_jack_grid.py:494-497` | Attributes DRC errors and splits for the drop-and-retry loop. It is repeated on each retry, with up to 8 attempts (`:493`, `:512-525`). `agnd_guard: true` is set in the K spec (`transactions.json`, osc-core spec). |
| 4 | Stage verify (fresh copy #1) | `route_jack_grid.py:528-533` | Fresh-workspace connectivity must equal the candidate, with no errors or parity findings. |
| 5 | Transaction fresh (fresh copy #2) | `transaction.py:136-140` | A second fresh copy of the `-verify` board. Its result feeds the gate, retention and `candidate_sha256` (`:142-148`). |

The AGND stitch would add 2+ more checks, but it cannot run for this spec. `stitched()` returns at once unless signal edges fell (`route_jack_grid.py:335-337`), and the K repair only routes the target plus restores the victim (`:393`, `:414`).

## All five checks stay per transaction; only check 5 has an existing equivalence, and deferring it is not recommended

- **Checks 1-4 are mandatory, and no code defines a deferral for them.** Checks 2 and 3 are inputs to the transaction's own logic. Check 4 is the fresh-copy obligation.
- **Check 5 has a precedent.** Neither `chain.py` (`circuit/reviews/osc3-k-signals/chain.py:87-93`) nor the driver's `main()` (`route_jack_grid.py:798-816`) runs a second fresh check. Both treat the stage's `-verify` check (#4) as the fresh copy. Even so, the full set fits a hosted job (table below), so drop nothing.
- **Check 1 could reuse a cached base only under a binding the code does not yet have.** `chain.py` resume already trusts a retained, already-checked start `dump.json`/`drc.json` when only the board sha256 matches (`chain.py:37`, `:54`). That assumes `--save-board` refill is byte-stable on the accepted board, which no receipt proves for K2518. The base is also re-saved by the check, and the cut proposal binds that post-check sha (`route_jack_grid.py:396`). Not recommended.

## The hosted job ceiling is the workflow's 100 min, not GitHub's 360

- **Job and step limits.** `transaction` job `timeout-minutes: 100` (`.github/workflows/local-transactions.yml:105`); run step 95 (`:175`); `prepare` 5 (`:54`).
- **The prepare formula enforces 100.** `budget + WRAPPER_GRACE 3 + KILL_AFTER 2 + SETUP 10 <= JOB_TIMEOUT 100` (`:45-48`, `:90-93`), so 80 is the maximum (`budgets.json` `osc-core: 80`).
- **Input validation also caps at 80.** `max_minutes` is limited to 1-80 (`:67`), and budgets.json values to 1-99 (`:88`).
- **GitHub's own maximum is 360 min per job.** That is the GitHub docs figure, linked from `circuit/ORCHESTRATION.md:138`; it is not encoded in the repo. A repo precedent uses `timeout-minutes: 355` (`.github/workflows/route.yml:57`).

## A 140-minute driver budget in a 170-minute job fits every check with one retry

| Phase | Source | Nominal | Allowance |
|---|---|---:|---:|
| Setup: checkout, pip, `docker pull`, A* build | `yml:116-169`, allowance `yml:47` | ≤10 | 10 |
| Preflight + `--validate` (host) | `transaction.py:108-111` | <1 | 1 |
| Base check (#1) | `transaction.py:121` | 19 | 20 |
| Cut `grid_apply` + check (#2) | `route_jack_grid.py:397-398` | ~20 | 21 |
| Frame-bounded routing (300k expansions) | `route_jack_grid.py:404-415` | not measured, small: whole JL run 928 s (`README:129`) | 5 |
| Candidate apply + check (#3) | `:494-497` | ~20 | 21 |
| One drop-and-retry reserve | `:518`, `:524` | 0 | 21 |
| Stage verify (#4) | `:528-529` | 19 | 20 |
| Transaction fresh (#5) | `transaction.py:137-138` | 19 | 20 |
| Gate, `delta`, retention, receipt | `transaction.py:141-152` | ~1-2 | 3 |
| **Driver `--max-minutes`** | | ~118 | **140** |
| Wrapper TERM grace / kill-after | `yml:45-46` | | 3 + 2 |
| Collect, manifest, upload (≤400 MB) | `yml:40`, `:211-273` | | 10 |
| **Job `timeout-minutes`** | | | **170** (≤360) |

- **Worst-case retry profile also fits.** All 8 retries need a 257-min driver budget, or a 285-min job, still under 360.
- **Edits needed (config only, no check removed):**
  - `budgets.json` osc-core 80 → 140.
  - `yml:48` `JOB_TIMEOUT_MINUTES` 100 → 170.
  - `yml:105` 100 → 170.
  - `yml:175` 95 → 160.
  - `yml:67` regex/cap `^[1-9][0-9]{0,2}$` and ≤ 250.
  - `yml:88` range.
  - `scripts/checks/test_osc4_transaction_signals.py:92` asserts `max_minutes == 80`.
  - README `:89-100` and `:294`.
- **Local runs.** `HEAVY_GUARD_MAX_RUN` must exceed the budget (`README:101-105`).

## Running OSC4 K on K2518 now is not worthwhile

- **The outcome is already known.** The first run's log shows the candidate still at 2518 and no route for the AGND target R5243.2 (`README:140-142`). The raw gate fails (`route_jack_grid.py:626` needs `after < before`). A rerun would only buy a terminal receipt.
- **The README forbids a time-limit retry.** "No transaction is retried with a larger frame, budget or time limit" (`README:120`). `ORCHESTRATION.md:103` repeats it.
- **The plan is hash-bound to K2518.** `transactions.json` osc-core `input_board_sha256 = 7251dd93…`, and `transaction.py:85` refuses any other board. Adopting K2226 makes it stale (`README:262-263`).
- **A passing receipt would not be adoptable anyway.** It still needs the complete-warning audit (`transaction.py:149`, `README:225`).
- **Recommendation.** Apply the budget fix now so the mismatch is closed. After K2226 is decided, replan K with `extract_residuals.py`/`select_transactions.py --board osc-core` (`README:309-311`).

---

# B. Issue #311 / complete-warning audit

## The 22.9 h figure is the whole chain, of which at most about 14.9 h was the audit

- **What the figure measures.** `wall_seconds: 82356` (`wsl-20261107a.json:224`) is measured from chain start (`chain.py:74`) to after the gate (`:120`). It includes the stage chain, which stopped starting stages at 480 min (checkpoint `not_started_reason: "480 min chain time budget"`, `circuit/routing/osc-pcb-current-checkpoint.json`).
- **The resulting bound.** The audit took at most 82356 − 28800 = 53,556 s, about 14.9 h. Nothing in the repo records the split by sub-audit.
- **How to get the real split.** Read member mtimes from the retained tar: `k1107-wsl-20261107a-evidence.tar`, 65,466 members (`wsl-20261107a-adoption.json` `evidence_archive`).

## The audit is four sequential sub-audits, and the silk sub-audit (one DRC per added copper object) dominates

`complete_gate` (`route_jack_grid.py:724-740`) → `warning_complete_gate` (`:653-699`; it runs only when a warning type hit the 199 cap, `:667-669`) → `audit_current_reports` (`scripts/pcbgen/complete_native_warnings.py:303-346`). That function runs four container calls in series, each looping fixtures single-threaded (`:322-341`), then the host-side `complete_reports` verifier (`:214-277`).

| Sub-audit | Unit | Size for K3363→K2518 |
|---|---|---|
| `holes-before`, `holes-after` (`audit_hole_pairs.py:132-188`) | One DRC per packed fixture of ≤14 holes covering every possible pair (`:147-164`) | 80 hole identities each (`wsl-20261107a.json` proof) |
| `silk` (`audit_added_mask.py` main, L209-304) | **One `kicad-cli pcb drc` per added copper object**, sorted by uuid, probe batches of 32 (`L276-L295`) | **12,049 fixtures** (11,068 segments + 981 vias, adoption `review_summary`) |
| `zones` (`audit_zone_silk_scope.py:157-191`) | Per growing (zone, layer); paired before/after fixtures per artwork batch (`:122-153`) | 982 fixtures at batch 16 (proof `zone_fixture_count`) |

The 12,049 silk fixtures of the 65,466 tar members (about 4 files each) dominate. That inference needs the tar mtimes to confirm. Silk cost scales with the copper added between before and after, so K2518→K2226 scales with the signals-06..12 delta.

## Checkpointing exists for zones and whole sub-audits only; an interrupted silk audit restarts from zero

- **Whole sub-audits are reused only for the same before/after pair.** They need the same `before_sha256`/`after_sha256` manifest (`complete_native_warnings.py:283-300`) and pass through `route_jack_grid.resume_evidence` (`:712-721`) and `chain.py:108` (`resume=True`).
- **Zones resume within a sub-audit.** An exact ordered prefix of byte-identical batches is reused (`zone_batch_resume.py` `completed_prefix`, `verified_report`), and `audit_current_reports` passes `--resume-from` (`:331-333`).
- **Silk has no in-progress resume.** It is reused only when complete (`:296-299`).
- **A complete `holes-before` is not reused across candidates.** This is so even though it depends only on the before bytes plus project/rules; `hole_evidence` re-verifies all of that (`:91-133`). K2518's hole audit already exists as the `holes-after` of the 20261107a gate, in the WSL archive.
- **`--max-minutes` never bounds the gate.** See the gate-only section below.

## Batch sharding is sound if one host-side merge rebuilds the existing evidence layout and the existing verifier runs unchanged

- **Why the units are independent.**
  - Silk fixture *i*: deterministic text from the after-board plus one copper block (`audit_added_mask.py` L82-90).
  - Hole fixtures: per packed group.
  - Zones: per zone uuid/layer (`classify_zone`).
- **The completeness proof already in `complete_reports` / `zone_evidence`:**
  - Silk fixture set == recomputed `added_copper_scope`, exactly once with kinds (`:244-256`).
  - Per-fixture report sha and context sha (`:258-262`).
  - Identities recomputed from the raw reports (`:263-266`).
  - Full hole-pair coverage (`:103-104`, `:128`).
  - Full-board identities ⊆ fixture identities (`:131`).
  - Zones: exact batch coverage order (`zone_batch_evidence.py:26-42`) and fixture bytes re-derived from the source text (`:107-113`).
  - Proof bound to both board shas (`route_jack_grid.py:640-647`).
- **An assembled tree needs no extra merge code.** Place it at `.circuit-cache/osc-core-grid-osc3-<label>-complete-warnings/native-audits/` with `added-copper-scope.json` and complete `result.json` files. `resume_evidence` → `resumable_audits` then copies all four sub-audits with no native run (`complete_native_warnings.py:340`), and `complete_reports` re-verifies everything.
- **Minimal code changes:**
  1. `audit_added_mask.py`: `--fixture-range START:END` writes `fixture-{i:03d}` folders and a shard receipt. The receipt holds before/after sha, scope sha, range, version and the KiCad image digest from `scripts/kicad/pin.env`. Add `fixture_sha256` and fixture-level resume, modelled on `zone_batch_resume.verified_report`.
  2. A host-only assembler (new, small). It requires shard ranges to tile 0..N-1 exactly once, with identical before/after/scope/image/project/rules hashes. It rebuilds each silk fixture's text from `selected_native_bbox_uuids` and compares it to `fixture_sha256`. Today nothing re-derives silk fixture bytes, a gap that exists in the monolithic audit too. It then writes the single silk `result.json`.
  3. `audit_zone_silk_scope.py`: `--zone UUID` restricts `classify_zone` to one zone. The assembler concatenates rows; `verify_result` already re-derives the bytes.
  4. `resumable_audits`: accept a `holes-before` directory bound only by `source_sha256` plus `project_sha256`/`rules_sha256` (still fully re-checked by `hole_evidence`).
- **Fitting Actions.** Jobs on `ubuntu-latest` run `scripts/kicad/run.sh` with the pinned digest (`pin.env`). They need the 90 MB start and candidate boards plus pro/dru as an artifact (`boards/osc-core/osc-core.kicad_pcb` is 90,210,926 B). Shard size comes from one pilot shard (for example 200 silk fixtures) measuring s/fixture on 4 vCPU. Target ≤240 min of fixtures per job so setup, upload and margin fit in 360. Run the final assemble + gate host-only in a small job. The existing `route-shards.yml` merge job (120 min, `:188`) is not a fit for K.

## Equivalence needs these negative controls before a sharded result counts

1. **Monolithic vs sharded.** On a small disposable before/after pair (a few hundred added objects), the per-fixture `report_sha256`, the identity unions and the final proof must match byte for byte.
2. **Missing shard or range gap** → reject ("silk audit omits added copper", `:251-252`).
3. **Duplicate or overlapping range** → assembler rejects.
4. **Shard built from a different after or before board** → reject on sha.
5. **Tampered `drc.json`** → report hash mismatch (`:260`).
6. **Swapped fixture folders** → `fixture_sha256` / copper_uuid mismatch. This needs change 2.
7. **A different KiCad image digest or project/rules file in one shard** → reject. Today only the version string `10.0.6` is checked (`:93`, `:241`).
8. **Positive control.** A planted silk-overlapping via in a disposable after-board must surface a new identity and reject the gate, as in `probe_zone_batch_controls.py`.
9. **Reused `holes-before` with a changed `.kicad_dru`** → context mismatch (`:95-96`).
10. **A `drc.json`/`dump.json` recovered for the wrong bytes.** These files are not hash-bound by the chain (`route_jack_grid.py:729-730`), so bind them by the archive manifest or by one fresh `check()` on a copy.

## The gate-only resume command runs no stage, only the hash checks, one `kicad-cli version` and `complete_gate`

The command is `chain.py wsl-20261109a signals-06 … signals-12 signal-escapes --resume-from signal-escapes --max-minutes 540`.

- **No stage runs.** `specs = specs[index(signal-escapes)+1:] = []` (`chain.py:78`), so the stage loop body never executes (`:84-100`).
- **`resumed()` checks are host-only:**
  - Start sha == the checkout's `boards/osc-core/osc-core.kicad_pcb` sha (`:72`, `:37`).
  - Progress steps, minus `resumed:` markers, == exactly the 8 listed stages (`:39-43`).
  - Ancestry chain of `input_sha256` (`:46-49`).
  - `current` is the last kept step's `-verify` or `-stitch-verify` (`:50-52`).
  - `current` sha matches (`:53`).
  - Raw `promotion_gate` of current vs start passes (`:55-57`).
- **Native work.** `kicad-cli version` (`:103`), then `complete_gate` (`:108`) with `resume=True`, then `enforce_warning_completeness` (`:110`). It writes `circuit/reviews/osc3-k-signals/wsl-20261109a.json` (`:121`), plus `-copper.json` if adopted (`:116-118`). Without `--promote` it never writes `boards/`.
- **`--max-minutes 540` has no effect here.** It only gates stage starts (`:85`; help `:66`: "the gate still runs"). The audit is unbounded, so plan for about 15 h or more of local wall time unless it is sharded.
- **`workspace()` can delete prior evidence.** It `rmtree`s the `-complete-warnings` workspace (`route_jack_grid.py:110-113`, `:733`). `resume_evidence` first renames an existing one to `-resume`, deleting any older `-resume` (`:714-717`). Copy any partial audit out of `.circuit-cache` before running.

## Files to recover from the WSL archive for that resume

| Required | Path | Used at |
|---|---|---|
| Yes | Checkout with `boards/osc-core/osc-core.kicad_pcb` == the chain's start (K2518 `7251dd93…`, assuming 20261109a started from it) | `chain.py:72`, `:37`, `:115` |
| Yes | `circuit/reviews/osc3-k-signals/wsl-20261109a-progress.json` (not in the repo) | `chain.py:38` |
| Yes | `.circuit-cache/osc-core-grid-osc3-wsl-20261109a-start/` with `osc-core.kicad_pcb`, `dump.json`, `drc.json`, `osc-core.kicad_pro`, `osc-core.kicad_dru` | `chain.py:35`, `:54`; `route_jack_grid.py:729-730`; `complete_native_warnings.py:221-227`; `audit_hole_pairs.py:137` |
| Yes | `.circuit-cache/osc-core-grid-signals-12-verify/` (or `signals-12-stitch-verify/`, whichever progress `current` names) with the same five files | `chain.py:50-55`; `route_jack_grid.py:729-730` |
| Safer | The rest of each workspace: `fp-lib-table`, `sym-lib-table`, `.kicad_sch`, `sheets/` (`route_jack_grid.py:110-118`) | Not read by the gate path, but keeps the layout |
| Optional | `.circuit-cache/osc-core-grid-osc3-wsl-20261109a-complete-warnings[-resume]/native-audits/` with `added-copper-scope.json` for the same bytes | `route_jack_grid.py:712-721`; `complete_native_warnings.py:283-300` |
| Optional | K2518 `holes-*` audit from the 20261107a evidence tar (usable only after change 4) | — |
| Not needed | `signals-06…11` verify directories (only their hashes in progress are checked, `chain.py:47-49`) | — |

- **Environment needed.** The `.circuit-cache` directory must sit inside the same checkout, because `complete_native_warnings.py:317` takes paths relative to the root that `run.sh` mounts at `/work`. You also need the numerical venv (numpy/scipy imports, `route_jack_grid.py:19-22`) and the pinned image.
- **Manifest needed.** Recover the archive's sha256 manifest so that `dump.json`/`drc.json` are bound to their boards (control 10).
