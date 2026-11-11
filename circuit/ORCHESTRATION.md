# Cloud-first PCB development orchestration

Owner-directed operating policy, 2026-11-11. Read [WORKFLOW.md](WORKFLOW.md) first. This policy governs delegation, resource admission and handoff for this project; it does not replace circuit evidence, native validation, review or release gates.

This is a runbook, not an installed scheduler or a provider API configuration. Session creation, model selection, notifications and local-machine access must be confirmed in the actual client. Never claim that a session, VM, reservation or background monitor exists merely because a plan mentions it. Generalization into a reusable product is deferred until this project is complete.

## 1. Authority and responsibilities

Use one active top-level manager per campaign: either a Claude Code Cloud manager session or ChatGPT Dots (for example Moya). The two are alternative control surfaces, not concurrent owners of the same work. Record the manager's session URL/ID and the campaign revision. A handoff requires a durable checkpoint, reconciliation of live jobs and acknowledgment by the new manager; an expired conversation alone is not proof that its jobs stopped.

| Role | Responsibility | Boundary |
| --- | --- | --- |
| Top-level manager | Design direction, dependency graph, model/environment mapping, shared capacity, escalation and integration decisions | Does not spend expensive reasoning turns watching healthy jobs |
| Design session | Difficult circuit, architecture, routing-strategy or validation-policy decisions | Fable or Astra; returns a reviewed decision and bounded execution contract |
| Child manager: Actions coordinator | Dispatch admitted workflows, track run/attempt IDs, collect and verify results | One dispatcher per allocated Actions pool; no independent budget expansion |
| Child manager: implementation | Own one bounded code/design-tool change in an isolated branch/workspace | May use subagents inside its assigned scope and resource budget |
| Execution worker | Run the approved command/manifest, checkpoint and report | No design changes, gate relaxation, speculative retries or canonical-board promotion |
| Integrator/reviewer | Independently inspect candidate evidence and serialize adoption | Review is not the implementer's self-approval; native gates remain mandatory |

The top-level manager may perform hard design directly only when its selected model is confirmed to satisfy the Fable/Astra requirement. Otherwise delegate it to a selectable, confirmed design session. An opaque Dots model route is not proof of Astra use. If that selection cannot be established, keep the design decision pending and request the required session rather than silently downgrading it. Routine coordination can continue.

Normally use at most two management levels (top-level and child managers), with bounded workers beneath them. Do not recursively create managers just to wait for other managers. Split sessions by independent deliverable, write ownership, resource profile and recovery boundary, not one session per shell command or net.

## 2. Model mapping

These are owner-selected role preferences, not benchmark claims or guarantees that a client exposes an API model ID. Discover available models at launch and record the requested and actually selected label/ID, its evidence, effort setting if exposed, and why it fits the task. Use `unknown` when unavailable; prose asking for a model is not a model selector. Do not infer ChatGPT effort from an API effort label or from response latency.

| Work | Claude preference | OpenAI preference |
| --- | --- | --- |
| Hard design, new electrical constraints, routing/validation policy changes | Fable | Astra |
| Child manager with substantial implementation judgment | Opus; Fable for hard decisions | Sol; Astra for hard decisions |
| Narrow implementation with a fixed design and tests | Sonnet or a demonstrated adequate smaller model | Luna/Terra, escalating to Sol when needed |
| Fixed Actions dispatch, collection and structured reporting | Smallest available model demonstrated adequate, such as Haiku | Luna; Terra when the actual task benefits from it |
| A* search, refill, DRC, ordinary waiting and metrics collection | No LLM: scripts/workflows | No LLM: scripts/workflows |

A powerful child manager can delegate bounded execution and log extraction to a smaller subagent when supported. That saves reasoning work only if the parent also stops polling. Subagent usage still counts; a cheap agent repeatedly reading logs is not free. If per-subagent model selection is unavailable, use scripts or a separately selectable session; never pretend the model changed.

An executor returns `NEEDS_DESIGN` for new constraints, failed assumptions or a proposed rule change. It cannot change clearances, layers, pin assignments, hardware positions, supply/AGND rules, warning completeness, acceptance criteria or tool pins to get a pass. Strong models are not a substitute for source evidence, independent review or bench qualification.

## 3. Plan from the execution resources upward

First classify each operation as (a) engineering judgment, (b) code implementation, (c) deterministic computation or (d) waiting/collection. Prefer existing GitHub Actions for repeatable computation that fits their tools, resources, permitted network access and complete job time budget. Prefer cloud child sessions for implementation, interactive diagnosis and admitted computations not suited to Actions. Use local resources only through section 7.

An Actions coordinator can manage many independent jobs. Do not create one LLM manager for each matrix entry. When Actions is full, compare queuing with a cloud-VM alternative: setup cost, measured capacity, interruption risk, model usage and artifact transfer all matter. A full queue is not an automatic reason to start additional VMs or duplicate an existing attempt.

Cloud sessions are additional compute only when their environments are genuinely independent. A subagent, terminal, clone or git worktree is not evidence of additional CPU/RAM. Until verified otherwise, account for all subagents and processes in the same VM as one shared pool. Windows and its WSL instances share a physical host and must not be counted twice.

### Capacity admission

The top-level manager owns the shared allocation. Child managers may schedule within it, but may not each interpret the account's entire allowance as theirs. Inventory current provider/account or organization limits, runner type, other-repository usage, this repository's running/queued jobs, workflow concurrency groups, matrix size, artifact/storage budget, session limits and user-approved spend. Repository visibility or a matrix limit does not reveal available account concurrency. Unknown limits are not unlimited.

Record an observation time, source and confidence for every capacity value. GitHub settings/plan evidence may require owner input when the connection cannot read it; do not guess a paid plan. Before fan-out, set a numeric project ceiling, ordinary-CI/integration reserve, other-work occupancy and per-child allocation. When capacity is uncertain, use only an explicitly admitted bounded pilot or leave the work queued; do not probe the account limit by flooding it.

For an Actions pool, new work must fit all of:

```text
new compute jobs <= min(
  ready independent work,
  remaining campaign allocation,
  observed account/pool headroom after other work and CI reserve,
  workflow / runner-specific allowance
)
```

Count prepare, merge, audit, artifact collection and required PR CI as well as routing jobs. A workflow's `max-parallel` limits that matrix, not the sum of all workflows or the account. Use bounded waves when a workflow lacks the needed cap; changing its default is a separate reviewed implementation. Preserve existing concurrency groups and never cancel unrelated work to make room.

For each VM, admit work from a fresh environment fingerprint: OS/architecture, tool/image digest, CPU affinity/quota (including readable ancestors), memory limit/current/headroom and `MemAvailable`, swap, disk, existing processes, timeout behavior and checkpoint destination. Keep physical RAM, cgroup ceiling and currently available RAM distinct. Unknown reclamation is not usable memory. Reserve manager/OS/finalization memory and record child/container peaks, not only the parent process RSS.

```text
sum(admitted incremental memory budgets) <= conservative observed free headroom - safety reserve
sum(admitted CPU allocations)            <= measured effective CPU budget
estimated full transaction time + setup + cleanup + upload margin <= enforced job deadline
```

Also check the remaining cgroup limit; use the tighter constraint. Profiles already include their subprocesses and native workers: do not count a worker twice. Default to one heavy process per unprofiled VM; do not start even that process without a bounded, admitted memory/time estimate. Raise concurrency only after a representative pilot, not from `nproc` alone. Existing heavy-guard restrictions remain binding.

Reconcile allocations at launch, completion, failure, takeover, changed inputs and changed resource conditions. Sessions should be proportional to independently useful work and actual capacity, not to an arbitrary desired agent count. Persist the revised task/environment/model mapping before launching the next wave.

## 4. Dispatch and isolated ownership

Use [orchestration/current-plan.md](orchestration/current-plan.md) for the project mapping and [templates/orchestration-task.md](templates/orchestration-task.md) for each runnable task. Store campaign records under `circuit/orchestration/campaigns/<campaign-id>/` when a campaign is admitted. The top-level manager alone writes the campaign allocation; each child writes its own result/receipt, never overwriting another child's status file.

Before dispatch, bind the task to a commit, input hashes, allowed writes, exact command/workflow inputs, dependencies, model, environment, resource ceiling, deadline, artifact policy, stop conditions and authority. A partially filled template is not executable authorization. Cloud launch credentials, local-machine connections and billable capacity are capabilities to verify, not assumptions made by this document.

Give independent implementations separate branches and separate workspaces. Within a shared VM, use worktrees or equivalent directory isolation for writers and disjoint cache/output directories; read-only exploration may share a checkout. Worktree isolation does not isolate memory. The current router uses stage-based workspace names: concurrent runs with identical stage names must not share a checkout/cache. Candidate directories must preserve the library-relative layout required by the existing driver.

Prevent duplicate attempts using a stable task key derived from the input commit/hashes, program/tool identity and normalized parameters, plus a distinct attempt ID. The named dispatcher checks the durable ledger and provider job status before launch and records the returned run/session ID immediately. After an uncertain launch response, search/reconcile the original attempt before retrying. A Markdown ledger is not an atomic distributed lock: keep a single dispatcher, and require a real lease/compare-and-swap mechanism before allowing multiple dispatchers over one allocation.

Keep exploratory branches distinct from the canonical board. Existing workflows that push results must target the task's candidate branch, not `main`; they are not all read-only. Independent candidates on one frozen baseline can run in parallel, but they cannot all promote themselves. Disjoint nets/regions may still interact through copper, zones and return paths. Apply deltas through the existing merge and full-board gate, never by blindly merging PCB text or treating per-shard passes as whole-board acceptance.

A sequential stage chain depends on its previously kept candidate. Do not parallelize later stages against stale predecessors as though they were independent; label alternative full candidates as alternatives and choose/revalidate them explicitly.

## 5. Waiting, cost and bounded failure handling

Prefer provider completion events or workflow results where available. Otherwise a bounded non-LLM monitor may poll status with backoff, within the host's supported lifetime, and return a compact terminal summary. Where durable monitoring is unavailable, record the run ID and a concrete next-check handoff; do not claim an unattached process or a sleeping chat will survive. An LLM may inspect a heartbeat at a milestone or on an anomaly, not narrate healthy waiting.

Keep complete logs in attributable artifacts. Return only the command/input identity, terminal state, wall time, aggregate peak memory, progress, changed files, gate outcomes, artifact hashes and a concise failure explanation. Record model usage/credits where actually exposed; otherwise `unknown`. Separate setup, route search, refill, DRC, full-warning audit, queue/wait and model/coordination time to avoid solving the wrong bottleneck.

Each task has finite wall-time, compute/usage, retry and no-progress limits. Default infrastructure retry allowance is at most one, and only after proving the previous attempt stopped and recording a plausible transient cause. A deterministic invalid plan, changed input hash, native rejection, zero improvement or unsupported environment is not a transient failure. Do not enlarge frames, relax rules, change models or repeat identical searches without a newly approved plan. A valid but rejected candidate is a result, not an infrastructure failure.

Exit 137 alone does not prove OOM: retain timeout/signal records and cgroup OOM counters where available. Preserve partial receipts on timeout, use owned-process/container cleanup, and reconcile interrupted results through the existing lifecycle tools. A missing final receipt is `UNKNOWN`, not success or proof that the VM is dead. Do not start a replacement while an orphan may still consume the same resources.

Use early rejection and caching only when their equivalence is established under unchanged inputs, tool/rule identities and existing validation obligations. Never remove native refill-stability passes, fresh-copy verification or complete-warning checks just to shorten a run. Treat the known OSC4 time-budget mismatch as planning work, not permission for a larger blind retry.

## 6. Evidence, restart and integration

A task progresses through planned/admitted/running/collecting/review-ready to integrated, rejected, blocked, cancelled or failed. Keep the computation outcome separate from board adoption; exit zero is not `ADOPTED`. Unknown interrupted state must be reconciled before claiming a terminal result. Preserve existing driver receipt schemas and vocabulary; the campaign record links them rather than rewriting historical receipts.

Persist after each expensive recoverable boundary: input commit/hashes, tool fingerprint, actual model when known, run/attempt ID, candidate/delta and hashes, native evidence, last completed stage, current resource owner and next safe operation. Store recovery-critical bytes outside an ephemeral VM before releasing it. A progress JSON without its candidate and evidence files is not a recoverable checkpoint. Verify upload/download hashes, retention/expiry and access; do not put secrets in logs or repository files. Keep large intermediates as budgeted artifacts, not repeated Git blobs.

On restart, reread the repository's current checkpoint and the campaign ledger, query live attempts, verify the kept candidate/evidence hashes and resume only at a boundary the driver actually supports. The existing K chain supports completed-stage recovery, not arbitrary in-flight A* recovery. Never label an unsupported restart as a resume.

Only the assigned integrator adopts a board, after independent review and the existing native/full-warning gates. Check the current base again: a changed base requires reconciliation/revalidation, not overwriting newer copper. Regenerate aggregate outputs from sources after integration, update the canonical checkpoint through its established workflow, and run required checks on the actual integration revision. Do not weaken CI, create fabrication outputs, order hardware, deploy, or convert an unvalidated draft into a qualified design.

## 7. Cloud-first local escalation

The owner prefers cloud completion. If a task needs Windows, WSL or macOS because of measured resources, OS-specific evidence, unavailable tools/hardware or an unsuitable cloud lifetime, the top-level manager records why, the smallest local scope, expected resource/time budget and return artifact, then requests access/approval when not already granted.

A preconnected Claude app environment may be used within the owner's existing authorization; do not repeatedly ask for the same permission. Connection alone is not approval for unrelated destructive work, broader filesystem access or increased spending. Verify which machine, checkout and execution context the connection exposes. Desktop connection does not establish WSL access. If the required host or scope is unavailable, mark that task blocked and continue independent cloud work.

Windows/WSL is the owner's preferred high-capacity fallback, not a measured capacity guarantee. Fingerprint it before use and coordinate Windows, WSL, Docker and other sessions against their shared host. macOS is used when it supplies the needed capability or native evidence. Keep local work limited and return reproducible artifacts to the campaign so the cloud manager can continue.

Grok Bot / Cursor execution is excluded from this project's current default routing by owner choice. This is an operational risk/cost decision, not a general product-performance claim.

## 8. Manager startup checklist

1. Read this workflow, current project/PCB checkpoints, current plan, open work and any live campaign. Claim or receive the single manager role without displacing a live owner.
2. Separate judgment, implementation and deterministic jobs; form a dependency graph and write scopes. Identify the critical path and work that can truly run independently.
3. Confirm launch/model controls and resource pools. Reserve ordinary CI and integration capacity; choose numeric, finite allocations and smaller execution models where adequate.
4. Fill task briefs, reconcile existing runs, admit a bounded wave and record the returned IDs. Do not start native work whose specific admission is still missing.
5. Collect results without repeated reasoning loops; escalate only decisions/anomalies. Recompute capacity before another wave.
6. Review and integrate serially; publish a durable handoff containing the next actionable task, not just a narrative summary.

## Reference boundaries

Provider documentation was consulted on 2026-11-11. Recheck it at launch; account-specific capabilities and limits must still be observed. The numerical budgets in a campaign are project allocations, not invented provider guarantees.

- [GitHub Actions limits](https://docs.github.com/en/actions/reference/limits) and [matrix parallelism](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations): provider limits and per-matrix `max-parallel`.
- [Claude Code cloud](https://code.claude.com/docs/en/claude-code-on-the-web) and [subagents](https://code.claude.com/docs/en/sub-agents): session surfaces, delegation and model configuration; actual access is client/account dependent.
- [OpenAI models](https://learn.chatgpt.com/docs/models), [Dots](https://openai.com/index/introducing-dots/) and [Dots tasks](https://learn.chatgpt.com/docs/dots/tasks-and-memory): model/task surfaces; no assumed fixed model for an opaque Dots route.

This policy adds no paid service, scheduled task, credential, automatically spawned session or custom scheduler. Existing commands and gates remain authoritative until separately reviewed implementation changes are merged.
