# Campaign osc-cloud-20261111

Cloud-first continuation campaign started by the owner on 2026-11-11 (thread root in the Claude Code Cloud Project "osc"). Policy: [ORCHESTRATION.md](../../../ORCHESTRATION.md). Precedence: the owner's 2026-11-11 Project prompt and [#315 comment 6799956908](https://github.com/Takazudo/zudo-osc-hole-field/issues/315#issuecomment-6799956908) (known APT DNS CI incident deferred; affected checks are NOT RUN, not PASS).

## Control record

| Field | Value (observed 2026-11-11 UTC) |
| --- | --- |
| Base | `main` at `ebfbc0940d2af6bc199405d4d5dbef8950a6bfa5` (contains #329) |
| Top-level manager and sole dispatcher | One Claude Code Cloud Project thread session ("Run OSC cloud-first prototype campaign"). No other live manager or child session for this campaign was found; earlier project threads were resolved by the owner. The separate PD/LED thread is out of scope. |
| Canonical boards | K2518 / JL184 / JR192 per `circuit/routing/osc-pcb-current-checkpoint.json`. `boards/osc-core/osc-core.kicad_pcb` SHA256 `7251dd93…` is unchanged since frozen source `433c88b2`; no board, schgen or pcbgen source changed between `433c88b2` and `ebfbc094` (only readiness/protection/decision files). |
| K2226 | Candidate-only, NOT ADOPTED. Bytes not yet recovered (see Recovery). |
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

## Allocations (finite)

- Actions campaign ceiling: **4 concurrent compute jobs**, plus a reserved **7 job** ordinary-CI/integration margin (check.yml fan-out). Account headroom is unknown, so this is a conservative pilot ceiling, not a measured one.
- Per Actions job: ≤ 330 min `timeout-minutes` including setup/upload; retry ≤ 1, only for a proven transient infrastructure failure.
- Manager VM: one heavy native process at a time; ≤ 10 GiB incremental memory budget, leaving ≥ 5 GiB for the manager, subagents and Docker.
- Subagents: at most 3 concurrently, read-only or confined to their own worktree under `/home/user/wt/<task>`.

## Recovery status (dependency of T1/T5–T9)

The 2026-11-10 pause archives (`codex-order-readiness-20261109/`, five tar.gz with recorded SHA256) live on the owner's WSL host and Dropbox. They are not reachable from this cloud VM or the connected Mac checkout. The owner was asked for the minimal transfer. Until then every task that needs the K2226 bytes or the staged `.circuit-cache/order-readiness-20261110/` packets is **BLOCKED_ON_EVIDENCE_OR_ENVIRONMENT**. No retained WSL worktree, branch or cache may be deleted.

Files needed for the K2226 gate-only audit: the progress JSON (`53277b7f…`), `.circuit-cache/osc-core-grid-osc3-wsl-20261109a-start/` and the signals-12 verify directory (board, `dump.json`, `drc.json`, `.kicad_pro`, `.kicad_dru`), any partial complete-warnings evidence, and the archive manifest. See [exec-budget-design.md](exec-budget-design.md).

## Tasks

| ID | Issue | Deliverable | Model / environment | State | Depends on |
| --- | --- | --- | --- | --- | --- |
| T0 | #315 | This record, backlog inventory, execution design | Manager | DONE (this PR) | — |
| T1 | #311 | Recover and hash-verify K2226 and its start/context | Manager | BLOCKED (archive access) | owner transfer |
| T2 | #311 | Shardable complete-warning audit (`--fixture-range`, assembler with coverage proof, negative controls) so the final audit fits bounded Actions jobs | Design check: Fable subagent; implementation: Opus subagent in own worktree | PLANNED | — |
| T3 | #308 | Make the OSC4 K budget internally consistent (setup + five native checks + one retry reserve + upload within the job) without removing checks; no rerun on K2518 | Sonnet subagent after T2 design check | PLANNED | — |
| T4 | #311 | Run the sharded final audit on K2226, then independent exact-byte review and single-integrator adoption decision | Actions, ≤4 jobs | PLANNED | T1, T2 |
| T5 | #21/#324 | Install `parts-439-with-324` onto current main after baseline | Opus | BLOCKED (archive) | T1 archive, T4 ordering for K receipts |
| T6 | #326 | SEL regional E2 experiment from reviewed recipe, new attempt ID | Actions/VM | BLOCKED (archive) | T1 archive |
| T7 | #327 | MIX4 vendor-model comparison, new attempt ID | VM | BLOCKED (archive) | T1 archive |
| T8 | #328 | NOISE2 bypass source fix rebased on the adopted K | Opus | BLOCKED (archive) | T1, T4 |
| T9 | #38/#39, #59, #305 | P retention/current-copper, protection, UUID migration | — | BLOCKED (archive / evidence) | T1 archive, T4 |
| T10 | #318 | Manufacturing review package | — | NOT STARTED: prerequisites unmet | all above |

Ordering rule: any source/metadata change that alters K receipts (T5 parts identities, T8 bypass) is applied after the K2226 decision (T4) so the candidate's receipt binding stays valid; otherwise K2226 must be rebound or re-audited.

## Backlog disposition

See [backlog-inventory.md](backlog-inventory.md). All 30 held drafts are labelled OWNER_HOLD (23) or REJECTED_EXPERIMENT_RETAINED (7); none is MERGE_READY and none was proven superseded without losing unique evidence, so **no PR was closed**. Parked (#189, #242–#259), protected (#278–#284, #288) and deployment (#2) records are untouched. `status: paused` labels stay until each lane actually resumes.

## Time accounting

Model usage: unknown (not exposed). Wall time per task is recorded in each task result.
