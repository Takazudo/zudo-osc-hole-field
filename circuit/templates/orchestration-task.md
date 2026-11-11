# Orchestration task brief

Copy to `circuit/orchestration/campaigns/<campaign-id>/<task-id>.md`. Complete required fields before admission. `unknown` is honest but does not satisfy a required model, resource, permission or validation precondition. This template does not launch anything or implement a lock.

## Identity and authority

- Campaign / task ID / attempt ID:
- State: PLANNED (not admitted)
- Top-level manager session / current campaign revision:
- Child manager / sole dispatcher session:
- Parent decision / issue / applicable native admission:
- Goal and non-goals:
- Dependencies and completion criteria:
- Independent reviewer / canonical-board integrator:

## Immutable inputs and write ownership

- Repository / source commit / input board and dependency hashes:
- Program, parameters and tool/image digest:
- Stable task key (inputs + tool/program identity + normalized parameters):
- Candidate branch / isolated checkout or worktree / unique cache/output directory:
- Allowed files and write targets:
- Forbidden changes (including rules, pins, fixed hardware and canonical adoption):
- Existing conflicting runs, workspace names or writer ownership checked:
- Base-drift behavior: stop and reconcile; never overwrite a newer accepted board.

## Model and environment

- Requested model family / exact selected model label or ID:
- Selection evidence (client configuration/launch receipt; not self-description):
- Effort requested / observed, or unknown:
- Why this model is adequate; decisions that require Fable/Astra escalation:
- Session-launch capability confirmed / actual session ID after launch:
- Environment / actual VM or runner identifier / physical-host pool:
- Environment fingerprint artifact, timestamp and confidence:
- CPU affinity/quota/effective allocation:
- RAM total / cgroup ceiling and remaining allowance / MemAvailable / safety reserve:
- Swap / disk headroom / known active workloads / nested-container accounting:
- Native oracle availability, image digest and version check:
- Timeout, stop/resume behavior and durable artifact destination:
- Local access/authorization receipt when applicable; Windows/WSL shared-host accounting:

## Admission and execution budget

- Account/pool capacity evidence and observation time:
- Other-work occupancy / ordinary-CI and integration reserve:
- Campaign allocation / this child's allocation / exact jobs or sessions admitted:
- Per-job native workers and maximum concurrent heavy processes:
- Estimated incremental memory including children/containers; basis and uncertainty:
- Setup / compute / cleanup / upload budgets; total deadline and outer deadline:
- Model-usage or credit budget if exposed; otherwise explicit bounded-turn policy:
- Compute/job count and spend ceiling; no automatic paid-capacity expansion:
- Retry limit (default at most one proven transient retry) / no-progress stop condition:
- Exact command or workflow ref and inputs (no guessed CLI flags):
- Dispatcher admission record / date / expiry / scope:

Do not mark ADMITTED until inputs, dependencies, permissions, model requirements, capacity and complete validation time fit. Confirm that an earlier attempt has stopped before any replacement. A zero exit or valid JSON is not board adoption.

## Waiting and durable recovery

- Completion event or bounded non-LLM monitoring mechanism:
- Fallback next-check handoff when durable monitoring is unavailable:
- Returned workflow run/job/attempt IDs or session IDs:
- Checkpoint boundaries actually supported by the driver:
- Candidate, delta, evidence and log artifact locations and retention:
- Artifact hashes / upload verification / expiry or preservation plan:
- Last completed phase and next safe resume operation:
- Cleanup/reconciliation mechanism for this attempt's processes and containers:

## Result (executor fills; retain failures)

- Execution state / exit code / separate adoption state:
- Actual input/output/tool identities and hashes:
- Search / refill / DRC / full-warning audit / queue / setup / total wall time:
- Aggregate peak memory and measurement method; CPU usage; model usage or unknown:
- Progress metrics, native gate outcomes, warning completeness, parity and remaining gaps:
- Files changed / candidate branch / commit / result artifact hashes:
- Failure classification: deterministic rejection, no improvement, timeout, measured OOM, environment, stale input, cancelled, unknown, or needs design:
- Retry history and why any retry was admitted:
- Evidence of terminal cleanup; unresolved live/orphan jobs:
- Checks NOT RUN, with reasons:
- Decision requested (one bounded question, only when needed):

## Review, integration and handoff

- Independent reviewer session, inspected revision and findings:
- Required checks on the actual integration revision:
- Current-base comparison / single integrator's adoption decision and receipt:
- Regeneration/checkpoint update or explicit not-applicable reason:
- Released capacity / remaining artifact retention responsibility:
- Next task and minimum context required to resume:

Never call a draft electrically, thermally, mechanically or manufacturing qualified from an orchestration or DRC result. Preserve the project's existing evidence vocabulary and receipt bytes.
