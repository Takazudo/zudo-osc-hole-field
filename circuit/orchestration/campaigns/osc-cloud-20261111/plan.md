# Campaign osc-cloud-20261111

Cloud-first continuation campaign started by the owner on 2026-11-11 (thread root in the Claude Code Cloud Project "osc"). Policy: [ORCHESTRATION.md](../../../ORCHESTRATION.md). Precedence: the owner's 2026-11-11 Project prompt and [#315 comment 6799956908](https://github.com/Takazudo/zudo-osc-hole-field/issues/315#issuecomment-6799956908) (known APT DNS CI incident deferred; affected checks are NOT RUN, not PASS).

## Control record

| Field | Value (observed 2026-11-11 UTC) |
| --- | --- |
| Base | `main` at `ebfbc0940d2af6bc199405d4d5dbef8950a6bfa5` (contains #329) |
| Top-level manager and sole dispatcher | One Claude Code Cloud Project thread session ("Run OSC cloud-first prototype campaign"). No other live manager or child session for this campaign was found; earlier project threads were resolved by the owner. The separate PD/LED thread is out of scope. |
| Canonical boards | K2518 / JL184 / JR192 per `circuit/routing/osc-pcb-current-checkpoint.json`. `boards/osc-core/osc-core.kicad_pcb` SHA256 `7251dd93…` is unchanged since frozen source `433c88b2`; no board, schgen or pcbgen source changed between `433c88b2` and `ebfbc094` (only readiness/protection/decision files). |
| K2226 | ADOPTED 2026-11-13 by #336 (`ddae895`): `boards/osc-core/osc-core.kicad_pcb` = `680da674…`, adoption record `circuit/reviews/osc3-k-signals/wsl-20261109a-adoption.json`. Later identity-metadata successor `7311cd8e…` (#334). |
| Grok / Cursor | Excluded |

## Capabilities actually available

| Capability | Evidence | Limits |
| --- | --- | --- |
| In-session subagents | Agent tool with a `model` parameter accepting `fable`, `opus`, `sonnet`, `haiku` | Share this VM's CPU/RAM; not extra compute |
| Additional Project child threads | Only via the coordinator on request | None requested yet |
| Cloud VM (manager) | 4 vCPU, 15 GiB RAM (MemAvailable 15.2 GiB at start), no swap, ~29 GiB free disk; cgroup v1, no readable cpu/memory limit files | Lifetime is the session's; reclaimed when idle |
| Native oracle in VM | Docker 29.9.2 daemon started; pinned `kicad/kicad@sha256:18693567…` pulled in 36 s; `scripts/kicad/run.sh kicad-cli version` → `10.0.6`. Wrapper `bc74f0ad…`, pin.env `769e2be0…` match the pause record | One heavy native process at a time |
| GitHub Actions | MCP tools list/get runs, jobs, artifacts and trigger workflow_dispatch | Repo is public (hosted standard runners). Account plan and account-wide concurrency are NOT visible; other repositories' load unknown |
| Local Mac (`wrath-of-god`) | Folder access to `/Users/takazudo/repos/circuits/zudo-osc-hole-field` granted | Mac checkout is stale (`36f5cad0`) and has no `worktrees/` or `.circuit-cache/`. WSL host and Dropbox pause folder are not reachable |
| Windows `x0x` (WSL Ubuntu), owner-approved 2026-11-12 | Remote Control session; Docker with the pinned image present; Node 24 / pnpm 11 installed; 12 cores, 11 GiB RAM + 16 GiB swap, ~292 GB free | Owner approved: new worktree from `origin/main`, heavy jobs with the pinned image, push `wsl/…` branches only (no PR/merge from there). Frozen worktrees untouched. Session parks when the device sleeps |

## Allocations (finite)

- Actions campaign ceiling: **4 concurrent compute jobs**, plus a reserved **7 job** ordinary-CI/integration margin (check.yml fan-out). Account headroom is unknown, so this is a conservative pilot ceiling, not a measured one.
- Per Actions job: ≤ 330 min `timeout-minutes` including setup/upload; retry ≤ 1, only for a proven transient infrastructure failure.
- Manager VM: one heavy native process at a time; ≤ 10 GiB incremental memory budget, leaving ≥ 5 GiB for the manager, subagents and Docker.
- Subagents: at most 3 concurrently, read-only or confined to their own worktree under `/home/user/wt/<task>`.

## Recovery status

The owner pointed to the Dropbox folder `/cclogs/zudo-osc-hole-field/codex-order-readiness-20261109/`, reachable read-only through the connected Mac (`~/Library/CloudStorage/Dropbox/...`). On 2026-11-11 the Mac-side SHA256 of all five archives matched the pause index, including `native-pause-20261109T203700Z.tar.gz` (601,926,045 bytes, `1cb067e2…`), whose remote presence had been unverified at pause. Dropbox therefore holds durable off-host copies.

Transferred to the cloud VM and re-hashed there: `engineering-20261109T182519Z` (`a4b83626…`), `owner-scope-final` (`9d0561f4…`), `pause-engineering` (`948c8a99…`), `pause-supplement` (`13b78ab5…`), the handoff JSON/Markdown files, and a K subset extracted from the native archive (`k2226-subset.tar.gz`, `31742b74…`). Large single-file staging timed out, so files move in 15–20 MB parts that are re-hashed after reassembly. The full native archive was not transferred: besides the K subset it holds only the completed Pair B fixture evidence (`mask304-pairB-{pre304,cur}`, 16,754 files) and the intermediate signals-06…11 stage directories, none needed by a current task. It stays durable in Dropbox and can be subset on demand. Transfer parts sit in the Mac checkout's ignored `.circuit-cache/cloud-transfer-20261111/`.

K2226 recovered and verified in an isolated worktree at frozen source `433c88b2` (`/home/user/wt/k2226-audit`, not the frozen WSL worktree):

| Item | SHA256 | Matches record |
| --- | --- | --- |
| signals-12-verify candidate | `680da674…3b656` | yes |
| start board (= canonical K2518) | `7251dd93…be42` | yes; also equals current `main` |
| progress JSON | `53277b7f…7e20` | yes |

Progress lineage: signals-06…12, 2518→2513→2506→2502→2458→2369→2299→2226, each step's input hash equal to the previous candidate hash, all `raw_gate_adopted: true`, no split pad groups, no new warning identities. The final complete-warning audit is NOT RUN; K2226 is NOT ADOPTED.

Applicability: no board, schgen or pcbgen file changed between `433c88b2` and `ebfbc094`, and canonical K is still K2518, so the frozen start applies. Readiness/protection/decision files that changed (E17 etc.) do not feed the K route or audit inputs; this will be re-checked at adoption time.

Staged source packets (from the four non-native archives, unpacked under `/home/user/recovery/x/`, never into a tracked checkout): the SHA256 of each packet's `SHA256SUMS` and a full `sha256sum -c` of its contents both match the pause record for `parts-439-with-324` (`681dd5df…`), `parts439-input-closure` (`b9033096…`), `owner-scope-e20-r2` (`d8bce10b…`), `selector-stagger-source-r2` (`bb4adce5…`), `selector-tail-reconcile` (`f01fc0b9…`), `p-geometry-equality-r2` (`4d486fe1…`), `negative-hotswap-v2` (`6c83f9c1…`), `negative-precision-limiter-v2` (`e3ea2c81…`), `negative-precision-return-v3` (`0a7aa154…`), `return-interface-observability` (`44f946a4…`) and `uuid305-adapter-v2` (`3a905bc5…`). Cancelled-job recipes for MIX4 #327, P control retention B (#38/#39) and E2 #326 are in `pause-supplement`.

## Tasks

| ID | Issue | Deliverable | Model / environment | State | Depends on |
| --- | --- | --- | --- | --- | --- |
| T0 | #315 | This record, backlog inventory, execution design | Manager | DONE (this PR) | — |
| T1 | #311 | Recover and hash-verify K2226 and its start/context | Manager | DONE (K subset; remainder not needed now) | — |
| T2 | #311 | Shardable complete-warning audit per [design-decision-t2-t3.md](design-decision-t2-t3.md) | Design: Fable subagent (selected via Agent `model: fable`, effort not exposed); implementation: Opus subagent, worktree `/home/user/wt/t2`; review: Fable subagent (APPROVE) | DONE: merged #333 (`542602c`) | — |
| T3 | #308 | OSC4 osc-core budget 80→140 min driver / 170 min job with an explicit osc-core run hold until a new plan after #311 | Sonnet subagent, worktree `/home/user/wt/t3`; review: Opus subagent (APPROVE) | DONE: merged #331 (`05b1498`) | — |
| T3b | #315 | Install owner-scope packet E18/E19/E20 (`d8bce10b`) | Manager; review: Opus subagent | DONE: merged #332 (`3e8c900`) | — |
| T4 | #311 | Run the sharded final audit on K2226, then independent exact-byte review and single-integrator adoption decision | VM (silk, holes) + Windows x0x WSL (zones, gate), pinned image, tool `41d664e`; exact-byte review: independent subagent (APPROVE) | DONE: zones completed on x0x (attempt 3, after VM ENOSPC and a VM container restart), x0x cross-check equals VM silk/holes digests; gate PASS via `chain.py --resume-from` at `433c88b`; evidence branch `wsl/k2226-final-x0x-20261113` (`9f9d05a`); adopted by #336 | T1, T2 |
| T5 | #21/#324 | Install `parts-439-with-324` onto current main after baseline | Opus subagent; review: independent subagent | DONE: merged #334 (`f34e440`). Owner chose a metadata-only successor for adopted PCBs (MPN/Manufacturer/LCSC footprint properties only, verified by `scripts/checks/metadata_successor.py`); new protection study `design/power/protection-study-parts439.json`; IC capture 54/54. P/EL views and ratsnest were rebound by hash, not natively re-rendered | T4 |
| T6 | #326 | SEL regional E2 experiment from reviewed recipe, new attempt ID | Actions/VM | DONE: attempt a1 `NO_INCUMBENT_INFEASIBLE_FOR_LISTED_FINITE_DOMAINS_ONLY`, recorded on #326 | — |
| T7 | #327, #59 | MIX4 vendor-model comparison and precision 4990 comparison, attempts `*-run-20261111a1` in `/home/user/wt/{mix4-327,precision4990}-a20261111` at `d00638c` | Sonnet subagent, VM | DONE: MIX4 no failures (#327); precision 4.99k 3/12 cases exceed 10 % overshoot at 5 nF (20–25 %); r2 checker footer fix reviewed APPROVE, recorded on #59 | — |
| T8 | #328 | NOISE2 bypass source fix rebased on the adopted K | Opus subagent; review: independent subagent | DONE: merged #335 (`bbe7e68`), P control-layout receipt rebound. Open: 56 K first-pin mismatch placements remain a separate finding | T4 |
| T9a | #38/#39 | P control retention / current copper (packet B + path-depth fix = packet C `e62bee16…`) | Manager VM native slot; review: independent subagent (APPROVE) | PR #339: native attempt C failed (nested layout dir broke `${KIPRJMOD}/../../footprints`); attempt D PASS: 0 open edges, 0 errors, 0 parity findings, 344/344 ground contacts | T4 |
| T9b | #305 | UUID migration adapter (`uuid305-adapter-v2`) bound to the adopted checkpoint or its recorded metadata successor | Manager; review: independent subagent (APPROVE) | PR #338 | T4, T5 |
| T9c | #59 | Protection (negative hot-swap / precision limiter / return packets) | — | BLOCKED (engineering/owner design): the pre-ramp predicate is false and the recovered packets are studies, not limiter implementations | T7 |
| T10 | #318 | Manufacturing review package | — | NOT STARTED: prerequisites unmet | all above |

Ordering rule: any source/metadata change that alters K receipts (T5 parts identities, T8 bypass) is applied after the K2226 decision (T4) so the candidate's receipt binding stays valid; otherwise K2226 must be rebound or re-audited.

## Backlog disposition

See [backlog-inventory.md](backlog-inventory.md). All 30 held drafts are labelled OWNER_HOLD (23) or REJECTED_EXPERIMENT_RETAINED (7); none is MERGE_READY and none was proven superseded without losing unique evidence, so **no PR was closed**. Parked (#189, #242–#259), protected (#278–#284, #288) and deployment (#2) records are untouched. `status: paused` labels stay until each lane actually resumes.

## Time accounting

Model usage: unknown (not exposed). Wall time per task is recorded in each task result.
