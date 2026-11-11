# Current orchestration mapping

Policy revision: 2026-11-11. Source snapshot inspected: `d00638cbfbf204bdeaabb95bca5206f7b6dd7511` (`main`). Apply [ORCHESTRATION.md](../ORCHESTRATION.md) and the canonical [WORKFLOW.md](../WORKFLOW.md).

This is the initial task/environment/model mapping, not a dispatch receipt. No worker sessions, resource reservations, local connections or routing jobs were created by this documentation change. Existing live jobs/sessions have not been inventoried here. Do not infer that the machine or account is idle.

## Control record

| Field | Initial state / action before dispatch |
| --- | --- |
| Active campaign / top-level manager | `osc-cloud-20261111` (2026-11-11): one Claude Code Cloud Project thread session is the sole manager and dispatcher; see [campaigns/osc-cloud-20261111/plan.md](campaigns/osc-cloud-20261111/plan.md) |
| Hard-design authority | Fable or Astra in an actually selectable/confirmed session; otherwise pending |
| Actions dispatcher | The campaign manager itself (no separate child); ceiling 4 compute jobs plus 7-job CI reserve, recorded in the campaign plan |
| Account concurrency / current headroom | Unknown; inspect current plan/settings, active work including other repositories, and runner-specific limits |
| Ordinary CI / integration reserve | Must be explicitly allocated before compute fan-out; do not consume all capacity with routing |
| Cloud implementation sessions | No new sessions admitted here; determine number from independent work and measured VM/session budgets |
| Heavy processes per unprofiled VM | At most one admitted bounded pilot, not automatic permission to start one |
| Local machines | No connection/authorization receipt recorded here; use existing scoped permission or ask only for the missing access/scope |
| Grok / Cursor | Excluded from default execution by owner decision |
| Campaign/model/spend/time caps | Must be finite and recorded before work; no additional paid capacity purchased by this plan |

The top-level manager updates this mapping when priorities, environment or model choices change. Per-attempt evidence belongs in the campaign's task records, not in an ever-growing conversation or this table. An allocation change is not itself a board-design decision or an authorization to revive a parked campaign.

## Proposed work lanes

All rows are **PROPOSED; NOT DISPATCHED**. Model entries are preferences, not claims that those sessions already exist.

| ID | Bounded deliverable | Manager / model | Execution environment | Dependencies / parallel boundary |
| --- | --- | --- | --- | --- |
| O1 | Inventory actual launch controls, available model selectors, Actions quota/headroom, live tasks and relevant VM fingerprints; propose numeric allocations | Narrow coordinator: Haiku/Luna or smallest demonstrated adequate model | Read-only cloud/connected service calls; bounded probes only when admitted | First; no stress tests, limit-flooding or native run. Missing quota visibility is reported, not guessed |
| O2 | Profile the K transaction phases and propose a timeout/checkpoint plan preserving all gates; distinguish search, refill and repeated verification | Opus/Sol for diagnosis; Fable/Astra for validation-policy decisions | Cloud code inspection and existing logs first; one admitted benchmark only if needed | Can inspect code in parallel with O1; native runs wait for resources and specific admission |
| O3 | Review executor/collector lifecycle, bounded retries, artifact retention and summary output using existing tools rather than a new framework | Implementation child: Sonnet/Sol; small worker for fixed tests | Independent Claude Code Cloud or Codex Cloud workspace | May proceed with O1/O2 only on disjoint files; coordinate shared `scripts/pcbgen/` and workflow edits before writing |
| O4 | Continue the approved K signal work from the current canonical checkpoint, as a sequential kept-candidate chain | Actions child coordinator: Haiku/Luna; strategy escalates to Fable/Astra | Actions only when the complete unit fits; otherwise an admitted cloud VM; approved local fallback if necessary | Needs O1, applicable O2/O3 fixes, current input binding and native admission. Later stages consume the prior kept candidate; no stale parallel chain |
| O5 | Independently bounded JL/JR candidate work or explicitly reviewed shards, with owned candidate branches | Same Actions coordinator for pooled jobs; no manager per shard | Actions first; bounded cloud alternatives only when justified | Can overlap K and each other only if inputs/authority/resources allow. Final merge/native checks remain required; failed old transactions are not blindly retried |
| O6 | Verify artifacts, independent review, serialized adoption, regeneration and checkpoint update | Assigned integrator; Fable/Astra for new design decisions, adequate smaller model for mechanical collection | Reserved CI/native capacity; cloud integration workspace | Follows completed candidates. One writer per canonical board and aggregate outputs; base drift triggers reconciliation |

Do not turn these rows into six mandatory concurrent managers. O1/O3 may be combined when small; O4/O5 normally share one Actions coordinator. The actual number of implementation children follows the dependency graph and resource allocations. Do not create an expensive design session merely to collect a successful fixed-command result.

## Existing implementation to reuse

| Entry point | Existing behavior / planning constraint |
| --- | --- |
| `.github/workflows/check.yml` | Required documentation, Python/regeneration and native checks; reserve capacity for integration CI |
| `.github/workflows/local-transactions.yml` | Per-board bounded OSC4 transactions, no push/promotion, artifact collection; source is pinned by the prepare job |
| `.github/workflows/route-shards.yml` | 1–16 requested shard jobs and a merge job; writes results to the supplied branch; shared routing concurrency group; no `max-parallel` in the inspected shard job |
| `.github/workflows/route.yml` | Existing routing workflow; inspect its current inputs/write behavior and shared concurrency group before dispatch |
| `.github/workflows/osc-candidate-check.yml`, `.github/workflows/routing-benchmark.yml` | Existing candidate/benchmark entry points to inspect for the exact intended mode; existence alone is not run admission |
| `scripts/pcbgen/route_jack_grid.py` | Stage driver and native validation; stage-name workspaces must not be shared between simultaneous attempts |
| `scripts/pcbgen/grid_router.py`, `scripts/pcbgen/grid_astar.c` | Numerical/native routing, not LLM generation of every track |
| `circuit/reviews/osc3-k-signals/chain.py` | Chains kept candidates and performs complete-warning gating; supports hash-bound completed-stage resume, not arbitrary in-flight resume |
| `circuit/reviews/osc4-local-transactions-20261107/transaction.py` and `lifecycle.py` | Bounded non-promoting transactions, owned processes/containers, interruption receipts and reconciliation |
| `scripts/kicad/run.sh`, `scripts/kicad/pin.env` | The project's fixed native oracle; do not substitute a convenient installed KiCad version |

These are a source snapshot, not a guarantee that every listed mode fits every environment. Re-read the current file and its tests before constructing a task brief. In particular, do not launch old routing workflows just because they already have a matrix.

## Specific blockers to resolve before scaling

1. **K time-budget mismatch.** The OSC4 README's 2026-11-08 lifecycle section records five native checks at roughly 18–19 minutes each, about 95 minutes. The inspected `budgets.json`/workflow path uses an 80-minute K budget with a 100-minute job ceiling and separate setup/finalization allowances. Merely changing the model or moving the same attempt to another VM does not fix that contradiction. O2 must establish a fitting, admitted execution/recovery plan without deleting verification passes. This document does not increase those limits.
2. **Full native evidence is expensive and binding.** The K chain explicitly amortizes the complete-warning audit across stages. Preserve existing native refill stability, fresh-copy and complete-warning requirements; analyze proven equivalent reuse or early rejection separately.
3. **Current board authority is elsewhere.** Read `circuit/routing/osc-pcb-current-checkpoint.json` and the current `project/next-actions.mdx` before each campaign. Do not copy mutable accepted counts into this policy as another source of truth. Parked #242/#253 work and draft PRs #260/#277 remain parked unless explicitly reauthorized.
4. **No per-provider VM specification is assumed.** This session's Cursor experiment is not a Codex/Claude benchmark. The Windows/WSL preference reflects the owner's experience, not a quota guarantee. Measure the environment used by the actual job.
5. **Cheap execution needs a strict contract.** Fix commands, permissions, limits and acceptance first; unknown failure analysis returns to the implementation/design lane rather than expanding a small executor's authority.

## First admitted campaign

The next manager should inventory live work, then create `circuit/orchestration/campaigns/<campaign-id>/plan.md` with the single manager/dispatcher, dependency graph, current capacity evidence, CI reserve and numeric allocations. Create one task brief per independently useful deliverable from [the template](../templates/orchestration-task.md). Bind an exact source revision and existing native admission before starting expensive work.

Record actual model/environment selections and their evidence in each task. Use deterministic execution and terminal summaries first. Evaluate savings using measured model usage (or `unknown`), compute wall time, successful gated progress and restart/retry waste, not the number of agents launched.

## Validation boundary of this policy change

Only operating documents and a template are changed. No circuit, PCB, pinned tool, workflow executable, budget, receipt, generated page or acceptance rule is changed. No native benchmark or routing was run. Repository-wide checks and independent review must be recorded by the implementation PR; a Markdown consistency check is not a circuit or hardware pass.
