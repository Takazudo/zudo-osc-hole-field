# OSC4: named residuals and one bounded local transaction per board (2026-11-07)

Status: a host-only plan for unvalidated drafts. Nothing was routed, refilled
or DRC-checked. No board, spec or placement file changed, and no fabrication
output exists. Each transaction below needs one admitted native run, listed
under "Native runs" as NEEDS ADMISSION. Electrical, thermal and physical
qualification are NOT RUN.

## 2026-11-08 Receipt lifecycle: every run ends in a named terminal state, and the K budget is 80 minutes

Issue #308. No native run was made for this change; the behaviour below is
proven by `scripts/checks/test_osc4_transaction_signals.py` with harmless
stand-in children through the workflow's own control path (`timeout --signal=TERM
--kill-after` + `with_route_guard.sh`), and by two short docker tests that run
`sleep` in the pinned image. A full native K replay under this lifecycle is
NOT RUN.

- **Why the K receipt stayed RUNNING.** The job log shows the run step ending 0.6 s after
  its 60-minute mark with exit 137 and no traceback, so the Python driver was SIGKILLed before
  its `except BaseException` handler could write. The cause is the runner image's `timeout`:
  on `ubuntu-latest` = Ubuntu 26.04, `timeout --signal=INT --kill-after=20s 3s python …`
  ended the driver with SIGKILL at once (exit 137, receipt still `RUNNING`, no output), while
  `--signal=TERM` through the same wrapper was delivered and honoured (exit 143, receipt
  `INTERRUPTED`). CI run 42490037580 on this branch reproduced that with the lifecycle tests,
  and the same chain on GNU coreutils 9.4 here delivers INT normally. Ubuntu 26.04 serves
  `timeout` from uutils coreutils 0.8.0 (its readme lists `coreutils
  9.5-1ubuntu2+0.0.0~ubuntu25`); the uutils internals were not traced further. The workflow
  and the commands below therefore use `--signal=TERM`; the driver treats INT and TERM alike,
  and the lifecycle below does not depend on the wrapper's behaviour either way.
- **What the parent observed about containers.** Killing the host process tree of a guarded
  native job left the KiCad container running: `docker run` is only a client, and the container
  is not in the host process tree. `scripts/kicad/run.sh` is unchanged, because its bytes are
  retained native evidence (`scripts/panel/check_review_receipt.py` pins them; editing it
  makes the panel review stale and needs a native rerun). Instead the driver puts a `docker`
  wrapper first on its children's PATH (`lifecycle.docker_shim_dir`) that gives every
  `docker run` `--init`, so a proxied SIGINT/SIGTERM terminates kicad-cli (PID 1 would ignore
  it), and a `--cidfile` in the driver's own cid directory, so the driver can `docker stop`
  exactly its own containers. Both paths are covered by the docker tests. Moving `--init` and
  the cidfile into `run.sh` itself is a follow-up for the next native panel regeneration.
- **Schema `osc4-transaction-receipt-2`.** The schema-1 fields keep their meaning. Added:
  `invocation`, `source_revision`, `input_board`, `spec_name`, `environment` (hosted flag,
  run id), `driver` (PID/PGID), `max_minutes`, `budget_source`, `grace_seconds`,
  `oracle_cid_dir`, `phases` (one checkpoint written before each expensive step:
  `base_check`, `stage`, `stitch`, `fresh_check`, `final_gate`), `native_calls` (every owned
  child with PID/PGID, start/end, return code, and `ended_by` when it was signalled),
  `current_child`, `signals`, `interrupt`, `terminal`, `terminal_outcome`, `ended_utc`,
  `containers_stopped`, and `recovery` when the collector finished the receipt. Every write is
  temp file + `os.replace`.
- **Terminal states.** `NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED` / `RAW GATE FAILED;
  NOT ADOPTED` (COMPLETED; the only state that may carry `raw_gate_passed: true`),
  `REJECTED OR NOTHING TO DO; NOT ADOPTED` (REJECTED), `INTERRUPTED; NOT ADOPTED`
  (SIGINT/SIGTERM/SIGHUP, exit 128+signal), `TIMED OUT; NOT ADOPTED` (the driver's own
  `--max-minutes` deadline, exit 124), `KILLED; OUTCOME UNKNOWN; NOT ADOPTED` (exit 137 seen by
  the collector), `ERROR; NOT ADOPTED`. A receipt whose process exit status nobody saw stays
  nonterminal with `terminal_outcome: UNKNOWN`. `adopted` is always false.
- **Signals.** The driver installs its own handlers. On a signal it writes the receipt first,
  forwards the signal to the children it started (each runs in its own session), waits
  `--grace-seconds` (default 6), SIGKILLs only those children, stops any owned container that
  survived its client, finalises and exits 128+signal. Nothing else on the host is signalled.
  Once the result is decided the handler no longer writes (the main thread may be writing the
  same receipt); the signal is recorded in memory and the final save at the end of `run()`
  carries it. A child that exits normally is never labelled killed: session stragglers get two
  seconds and are then listed under `stragglers`, not signalled. The imported driver is reached
  through its `route_jack_grid.RUNNER` hook; the receipt opens with a `preflight` phase before
  plan validation and imports.
- **Reconciliation.** `transaction.py <board> --reconcile --exit-status <N|unknown>
  --invocation <id>` is host-only. It finishes a nonterminal receipt from the exit status the
  shell saw, keeps a terminal receipt byte for byte, refuses a receipt from another invocation
  or an unreadable one (exit 4; `--force-reconcile-corrupt` finishes unreadable bytes after
  preserving them, without stamping an invocation), appends the prior bytes to
  `<spec>.raw-events.jsonl`, and never sets a result. The workflow's collect step runs it and
  uploads the receipt only when the invocation matches; when the run step was cut off before it
  reported an exit status, the receipt is still collected, nonterminal, with
  `terminal_outcome: UNKNOWN`.
- **Known limit: signals inside native code.** Python runs the handler only between bytecodes,
  so a signal that lands inside a long ctypes call (`grid_router.native_astar`) waits until the
  C call returns. If the wrapper's `--kill-after` ends the driver first, the collector
  reconciles the last checkpoint as `KILLED; OUTCOME UNKNOWN; NOT ADOPTED`. Accepted behaviour:
  nothing is adopted either way.
- **Owned children are signalled by PID, never by a bare process group.** The driver records
  each child's session id and start time at spawn and enumerates the remaining members from
  `/proc`, so a reused PID of a reaped leader can never make it signal a foreign process. The
  per-invocation cid directory under `.circuit-cache/` is removed when no owned container is
  left in it; `*.tmp` and `*.raw-events.jsonl` in this folder are run artifacts and gitignored.
- **Stale data.** The driver refuses to start when `<spec>.json` exists from another
  invocation (exit 3), which includes the committed historical receipts in this folder: move or
  delete the file first. The workflow deletes it in the run step, stamps
  `<run id>-<attempt>-<board>` as the invocation, and verifies it when collecting.
- **Budgets.** `budgets.json` in this folder is the single source: 80 minutes for `osc-core`,
  60 for the jacks. `transaction.py` reads it for the `--max-minutes` default (`--print-budget`
  shows it), and the workflow reads the same file from the plan commit; an explicit value wins.
  The workflow's `max_minutes` input is now empty by default and resolves per board; `prepare`
  fails when budget + 3 min wrapper grace + 2 min kill-after + 10 min setup allowance exceeds the
  100-minute job timeout. The plan's `limits.wall_minutes: 60` stays as the
  2026-11-07 record. Frames, expansion limits, refill counts and retry policy are unchanged.
- **Open budget question.** The job log counts five native checks for K, not four: base, after
  the cut, candidate, the stage's own fresh verify, and the driver's fresh copy, at 18–19 min
  each. 80 minutes reaches the fifth check but does not finish it; a complete K run needs about
  95 minutes, which the 80-minute ceiling and the 100-minute job cannot hold. That decision is
  left to the manager.
- **Local runs.** `with_route_guard.sh` goes through heavy-guard locally, whose `--max-run`
  default of 1800 s would TERM a 60–80 minute run; set `HEAVY_GUARD_MAX_RUN` above the budget.
  The driver receives TERM from the guard and finalises `INTERRUPTED` the same way. The guard
  escalates TERM to KILL after a fixed 10 s, so the driver's grace (default 6 s) plus its kill
  and final save must fit inside that; do not raise `--grace-seconds` above about 8 s locally.

```
HEAVY_GUARD_MAX_RUN=6000 bash scripts/pcbgen/with_route_guard.sh timeout --signal=TERM --kill-after=2m 83m .circuit-cache/ground-solver-venv/bin/python -u circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core --max-minutes 80
python3 circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core --reconcile --exit-status "$status"
```

## 2026-11-08 Actions run results: no transaction improved a board; K hit the 60-minute limit

The three planned transactions ran once on GitHub Actions in run
https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/42412490176. The run
was dispatched from `main` with `branch=wsl/osc4-k-replan-20261107` and pinned to
plan commit `8618299ab1231e7d12660e99784aaf9441ece024`. Every artifact manifest
verifies, and each `source-sha.txt` equals that commit. No board changed, and
nothing was adopted or promoted. Complete native warning evidence is NOT RUN for
all three. No transaction is retried with a larger frame, budget or time limit.

| | JL184 `osc4-jl-agnd-r8270-2` | JR192 `osc4-jr-x8c35a836` | K2518 `osc4-k-agnd-r5243-2` |
| --- | --- | --- | --- |
| Exit / receipt status | 0 / NATIVE CHECKED; RAW GATE FAILED; NOT ADOPTED | 0 / NATIVE CHECKED; RAW GATE FAILED; NOT ADOPTED | 137 / RUNNING (never finalised) |
| raw_gate_passed | false | false | false (no gate reached) |
| Open edges | 184 → 184 | 192 → 192 | 2518 at every completed native check |
| Native errors / split groups / new warnings | none | none | not reached |
| AGND stitch fallback | not used | not used | not reached |
| Wall time / peak memory | 928 s / 2451 MB | 774 s / 2637 MB | 60 min (limit) / 4273 MB |
| Receipt files | receipt and copper delta | receipt and copper delta | receipt only |

The two jack runs restored their victim nets and failed only on the target:

- **JL.** It cut the two In3 tracks and rerouted `/F3/C3e5421_ENABLE`. The R8270.2 ground route then failed with `search_exhausted` after 772 of 300,000 expansions.
- **JR.** It cut the In3 track and rerouted `/A05/Cd4fa3b_LED_A`. The U7509.5 route failed with `search_exhausted` after 1283 expansions, and the J900069.3 end had no source inside the frame.
- **What that means.** Exhausting so early means each stranded pad is enclosed inside its frame. The straight-corridor estimate in `residuals.json` did not see that, because it ignores pad escape geometry and copper on the other layers. It is a weak predictor for these pads.

K was stopped by the run's 60-minute limit:

- **What completed.** Each native check of K2518 took three refill passes of about 5–7 minutes. The base check, the check after the cut and the candidate check all reported 2518.
- **What the log shows.** The log shows a route for the victim `/W1/AC_NODE` but none for the AGND target R5243.2. The fresh-copy check had started when the limit was reached.
- **Reading the counts.** The candidate count was 2518, so the raw gate would have failed even if the run had finished. That conclusion comes from the log, not from a receipt.
- **How it ended.** The process ended with exit 137 within a second of the limit. It printed no traceback, so `transaction.py`'s interrupt handler never wrote INTERRUPTED. The receipt kept its first-save status RUNNING. Why the SIGINT ended in an immediate SIGKILL was not determined.
- **Open driver issue.** On the runner, `transaction.py` does not reliably finalise its receipt when stopped. It is not fixed here, and no native rerun was made.
- **Time budget.** A K transaction needs four native checks, about 70 minutes, which the 60-minute default cannot fit.

## 2026-11-08 K2518 replan: the K transaction still applies unchanged and is rebound to K2518

The manager adopted K2518 (`7251dd933af810b7c659c9b90c6f6d9ba32d55ea432b0414c26c8b26b6b4be42`,
chain `wsl-20261107a`, 3363 to 2518 open edges) in place of K3363. Its copper is
purely additive: 12,049 new objects and none removed. Rails and AGND are
unchanged. The K plan was hash-bound to K3363, so it was replanned on the board
text. No native run was made.

- **Counts match.** Text connectivity matches K2518 exactly: 2518 open edges, with +12V 6, −12V 7, +5V 4 and AGND 22. The native source is `circuit/reviews/osc3-k-signals/wsl-20261107a-adoption.json`.
- **K residuals are the same.** The same 39 rail and AGND edges are stranded, with the same gaps. Only one corridor count changed: the unselected AGND edge to R1579.2/R2332.2 now has 2 In3 cuts instead of 1.
- **The selected K edge is unchanged.** The AGND edge from stranded R5243.2 to J900287.2 is still 3.42 mm on F.Cu. It still needs the single cut `1fb44ff3-7a2e-57ed-a422-f5aa4dbf32bc` on the victim `/W1/AC_NODE`. The K2518 delta adds no copper inside the frame and does not touch the victim net or the cut track.
- **Only the K binding changed.** `residuals.json` (K entry) and `transactions.json` (K entry) are rebound to K2518, and the K transaction body is identical. `--validate` passes on all three boards.
- **JL and JR are untouched.** Their boards did not change, and their entries are byte-identical. `extract_residuals.py --board osc-core` and `select_transactions.py --board osc-core` refresh one board and keep the others.

The K3363 tables below are kept as the 2026-11-07 record. The K values in this section supersede them.

## Text connectivity reproduces the native open-edge counts on all three accepted boards

`scripts/checks/board_text_geometry.py` rebuilds the islands from the board
text. It tests pads, tracks, vias and stored zone fills by shape overlap. The
cached native dumps (`.circuit-cache`) are not available here, so the result
was checked against the native counts in the receipts.

| Board | Accepted file sha256 | Native receipt | Native | Text | By-net match |
| --- | --- | --- | ---: | ---: | --- |
| K3363 `osc-core` | `2c1d67b7…0ec6751` | `boards/osc-core/reports/grid-routing/osc3-k-pilot.json` | 3363 | 3363 | +12V 6, −12V 7, +5V 4, AGND 22 |
| JL184 `osc-jack-left` | `a7fe6860…bb9ca251` | `boards/osc-jack-left/reports/grid-routing/rrr-01.json` | 184 | 184 | every net |
| JR192 `osc-jack-right` | `f6106300…031bfaa8` | `boards/osc-jack-right/reports/grid-routing/rrr-01.json` | 192 | 192 | every net |

`residuals.json` names every open edge by its nearest endpoints. That covers
the K rails and AGND, and all of JL and JR. For each edge it also lists the
foreign copper on a straight corridor on each signal layer. Explicit cut UUIDs
are kept only where a bounded repair could use them. The corridor is an
estimate: an empty corridor does not prove a route, and a blocked one does not
disprove it.

## K residuals: 17 rail edges and 22 AGND edges

| Net | Open | Stranded items |
| --- | ---: | --- |
| +12V | 6 | single supply pins U2308.4, U4439.4, U4541.4, U4341.4, U4308.13, U7405.4 |
| −12V | 7 | single pins U7405.11, U4540.11, U7404.11, U4541.11, U4439.11, U4240.11; one 106-item island: U4239/U4241/U4243/U4244/U4245 pin 11 with C4259/C4261/C4263/C4267/C4269/C4271 |
| +5V | 4 | U4113.14; C4433.1 + U4416.14; C4146.1, C4149.1, U4129.14, U4132.4/.10; U4538.10 |
| AGND | 22 | 22 small islands, 0.15–7.2 mm from the main group (listed in `residuals.json`) |

The rail singles are the pins that OSC2 H1 plane escapes and H3 guarded rail
escapes could not reach (`circuit/reviews/osc2-k-power-return/README.md`).

## Selected transactions: one explicit cut per board, or two on JL

`select_transactions.py` picks from the ranked corridor candidates in
`residuals.json`. A candidate's corridor must open with 1–12 explicit signal
cuts on one layer and nothing else. It may have at most two victim nets and a
frame of at most 50 mm, matching the driver's `repair_selection()` and
`repair_bounds()` limits. No earlier native transaction may have targeted it.
A same-layer path is preferred, then fewest cuts, then shortest gap.
`transactions.json` holds the exact specs, cut objects and frames.
`transaction.py <board> --validate` re-checks them against the board text, and
all three pass.

| | K3363 | JL184 | JR192 |
| --- | --- | --- | --- |
| Target | AGND: stranded R5243.2 (1 kΩ) to J900287.2 | AGND: stranded R8270.2 to R2305.2 | `/A05/OFFSET_BUFFER`: U7509.5 (B.Cu) to U7506.6 (F.Cu) |
| Gap | 3.42 mm, both pads F.Cu | 4.10 mm, both pads B.Cu | 9.86 mm |
| Mode | ground corridor (`repair_ground_pad_uuids`) | ground corridor | explicit signal repair |
| Cuts | 1 F.Cu track `1fb44ff3-7a2e-57ed-a422-f5aa4dbf32bc` | 2 In3 tracks `ded78b30-06e8-5b9a-9879-8c51b6d2903c`, `8fd8329c-89e2-532a-94a4-51bca7da2765` | 1 In3 track `843151a2-99cb-5ccb-849f-d76bc20b86ba` |
| Victim net to restore | `/W1/AC_NODE` | `/F3/C3e5421_ENABLE` | `/A05/Cd4fa3b_LED_A` |
| Frame (mm) | 259.41, 257.10 – 268.55, 266.375 (9.1 × 9.3) | 266.60, 126.09 – 274.40, 136.19 (7.8 × 10.1) | 392.65, 185.82 – 400.00, 201.683 (7.4 × 15.9) |

These limits apply to every transaction:

- **Cuts.** Only the listed cuts are made. There is no rip-up probe, negotiation or region pass.
- **Victims.** The victim is rerouted inside the frame by the same `route()` call. The search is capped by `bounds_mm` and 300,000 expansions.
- **Router arguments.** They are those of the `repair-NN` stages: clearance 0.2 mm (0.25 mm for the ground corridor), 0.05 mm raster, the AGND guard and the −12V In3 fill guard.
- **AGND recovery.** If signal edges close but AGND splits, the driver's existing `stitched()` is the only allowed recovery. It is not frame-bounded: it runs the board-wide `agnd_stitch` stage, which adds a via into the In1 AGND plane from every AGND island on the board. The receipt records its links and copper rows under `stage.agnd_stitch`, so that copper can be told apart from the frame-bounded repair.
- **Native check.** Refills settle on three equal island signatures, with at most six refills and at most eight drop-and-retry passes. A fresh copy must reproduce the candidate's connectivity.
- **Time.** Each run is bounded to 60 minutes.
- **Plan gate.** `transaction.py` refuses a changed board by hash, then runs the same host-side `--validate` checks before any native call.
- **Acceptance.** The driver's `promotion_gate()` needs fewer open edges, no split pad group, no new warning identity and no native error or parity. Adoption also needs the complete-warning audit, which this driver does not run. A passing receipt is a comparison input, never a promotion.
- **Receipt.** `raw_gate_passed` and the status name the raw-gate result, while `adopted` always stays false. A run cut short by the timeout's SIGINT is meant to be saved as `INTERRUPTED; NOT ADOPTED` with the error. That did not happen on run 42412490176: the K process ended with exit 137 and its receipt stayed `RUNNING`. See the 2026-11-08 Actions run results section and issue #308.

## None of the three repeats a preserved failed experiment

- **JL and JR `rrr-02`/`rrr-03` on these exact inputs.** These were all-or-nothing rip-up probes over every open net, with budgets of 8 and 12 rips. They ended with 0 rips and open edges unchanged. JR `/A05/OFFSET_BUFFER` was among the offered nets. The transactions here use no probe. They declare one or two cuts, a fixed frame and repair-mode victim restoration. If one fails, it is not retried with a larger frame or budget.
- **JR `repair-01`.** This was an unbounded terminal-local batch with 269 rips on an older input, rejected for split pad groups. The JR transaction targets one net with one cut.
- **JL and JR `agnd-stitch-1`/`agnd-stitch-2`.** These placed a via into the In1 plane from every AGND island, with no cuts, and were non-improving. The K and JL transactions instead cut the named blocking copper and route a surface or In3 ground corridor.
- **JL `negotiate`.** This was a whole-board PathFinder pass and is not repeated.
- **issue189 records.** No native transaction targeted these endpoints. JL R8270.2 appears in the raster-only screen `jl121-ground-cut-screen` on JL121, with a different five-cut set on another net. K R5243.2 appears in the selection-only ranking `core-twelve-ground-screen`. Neither was a native run.
- **The old OSC2 endpoint list is not reused.** All endpoints here are recomputed from the accepted K3363, JL184 and JR192 text.

## A K −12V island stitch has more value but cannot be scoped to its endpoints

The 106-item −12V island holds five op-amp V− pins and six decoupling
capacitors. It is 16.1 mm from main −12V copper at U4206.4. Its straight B.Cu
corridor has no blocker. One stitch would join 11 supply pins, more than any
AGND edge.

The existing driver cannot target a rail with named endpoints. `repair_selection()`
rejects rail targets, and a rail stage serves the whole net. Such a stage would
also re-offer the six −12V single pins that OSC2 H1 and H3 already failed on. An
endpoint-scoped rail stitch needs a small driver option first. That is a
decision for the manager or owner, so it was not selected.

## Native runs: NEEDS ADMISSION

Run each one from a checkout at this branch's head. That checkout must have
the numerical venv from `scripts/pcbgen/README.md`. Each run writes its receipt
and copper delta into this folder and leaves `boards/` untouched.

```
bash scripts/pcbgen/with_route_guard.sh timeout --signal=INT --kill-after=2m 60m .circuit-cache/ground-solver-venv/bin/python -u circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core
bash scripts/pcbgen/with_route_guard.sh timeout --signal=INT --kill-after=2m 60m .circuit-cache/ground-solver-venv/bin/python -u circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-jack-left
bash scripts/pcbgen/with_route_guard.sh timeout --signal=INT --kill-after=2m 60m .circuit-cache/ground-solver-venv/bin/python -u circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-jack-right
```

If the manager adopts a new K, the K plan is stale, and `transaction.py` refuses
it on the hash check. Re-plan with the reproduce steps below.

## GitHub Actions runs all three transactions in parallel and never pushes

`.github/workflows/local-transactions.yml` runs the same command on
github-hosted runners, one job per board in parallel. It uses the runner's
Python with `scripts/pcbgen/numerical-requirements.txt` instead of the
ground-solver venv. `with_route_guard.sh` execs the command directly there.

- **What it checks first.** Each job checks out the branch's current commit and records its sha. Before the numerical install, the KiCad pull or any native call, it confirms that the plan's input hash equals the checked-out board's sha256, and runs `transaction.py <board> --validate`. A mismatch fails the job, and the reason goes into the run summary.
- **Stale receipts are discarded.** The run step deletes any receipt already committed on the plan branch before the driver starts. Receipts are collected only from a run that started.
- **What it never does.** The workflow never commits or pushes. The driver never promotes.
- **What it uploads.** One artifact per board, kept for 7 days, holds:
  - the receipt `<spec>.json` and `<spec>-copper.json`
  - the `.circuit-cache` candidate workspaces (`-fresh` and every `-verify`: the board, `dump.json` and `drc.json`), up to 400 MB; larger files are listed in `excluded.txt` and in the summary
  - `run.log`, `status.txt`, `memory-peak-kb.txt`, `precheck.txt`, `validate.json` and `source-sha.txt`
  - `MANIFEST.sha256` covering every uploaded file

The workflow file must be on `main` before it can be dispatched. Dispatch it
from `main`. The jobs check out the commit of the `branch` input, so the plan
branch does not need to carry the workflow:

```
gh workflow run local-transactions.yml --ref main -f branch=<plan-branch>
gh workflow run local-transactions.yml --ref main -f branch=<plan-branch> -f boards=osc-core -f max_minutes=60
```

Runs share one concurrency group per plan branch and are never cancelled.
GitHub keeps only one pending run per group: a newer dispatch for the same
branch replaces one that is still queued.

`boards` defaults to all three, and `max_minutes` defaults to 60 (1–80, with no leading zero).
The job fails if `transaction.py` exits non-zero, but it still uploads what
exists.

To bring the results back:

1. Download the artifacts: `gh run download <run-id> -D <dir>`.
2. Verify each one inside its folder: `(cd <dir>/transaction-<board>-<run-id> && sha256sum -c MANIFEST.sha256)`.
3. Confirm that `source-sha.txt` is the plan branch commit you dispatched.
4. On the plan branch, copy `receipts/<spec>.json` and `receipts/<spec>-copper.json` into this folder. Commit them with the run URL in the commit body (`https://github.com/<owner>/<repo>/actions/runs/<run-id>`).
5. Leave the workspace boards out of git. A receipt is a comparison input; adoption still needs the complete-warning audit and a separate decision.

## Reproduce (host only)

```
python3 circuit/reviews/osc4-local-transactions-20261107/extract_residuals.py --board osc-core -o circuit/reviews/osc4-local-transactions-20261107/residuals.json
python3 circuit/reviews/osc4-local-transactions-20261107/select_transactions.py --board osc-core
python3 circuit/reviews/osc4-local-transactions-20261107/transaction.py osc-core --validate
```

| File | Content |
| --- | --- |
| `extract_residuals.py` | Named open edges, corridor estimates and ranked candidates; checks text against native counts |
| `residuals.json` | Every K rail/AGND and JL/JR open edge with endpoints, pad UUIDs and corridor counts |
| `select_transactions.py` | Deterministic choice of one transaction per board |
| `transactions.json` | Exact driver specs, cut objects, victims, frames and limits |
| `transaction.py` | Non-promoting native driver around `scripts/pcbgen/route_jack_grid.py` `run_stage()`; `--validate` is host-only |
| `scripts/checks/test_osc4_transaction.py` | Unit tests for `transaction.py` with the driver stubbed: hash refusal, plan-invalid gate, interrupted receipt; run by `scripts/checks/run-python-tests.sh` |
| `budgets.json` | Default wall-clock budget per board in minutes, read by `transaction.py` and the workflow (2026-11-08) |
| `lifecycle.py` | Receipt lifecycle for `transaction.py`: atomic writes, phase checkpoints, owned children and containers, signal handlers, `--reconcile` (2026-11-08) |
| `scripts/checks/test_osc4_transaction_signals.py` | Process-level tests of the lifecycle through `timeout` + `with_route_guard.sh` with `osc4_signal_harness.py` and `osc4_fake_oracle.sh`; two docker tests skip without docker and the pinned image |
