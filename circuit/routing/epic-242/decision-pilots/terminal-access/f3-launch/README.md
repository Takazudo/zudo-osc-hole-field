# First F3/K1402 launch binding

**Admission consumed once.** Parent reconciled the exact identity-bound SHA and
the first run completed with NO IMPROVEMENT. See the
[actual result and cleanup evidence](../route-1623/README.md). The execution
branch now exists and is frozen; the preparation instructions below are
historical and must not be executed again. All downstream phases remain held.

**Historical preparation record:** the following prelaunch details are superseded by the completed run above.

Exact identity-bound orchestration commit: `bf671866e73e8d133726090c0e8295ccdd41c5c1`.
Exact routing method: `6f0783335fa23d760877a91db3b63f93c039b4b4`.
The [frozen request](../f3-packet/request.json) remains SHA256
`10be49ae32997a36c54436e48226a295678e47dda1fc1c14f4569c72ef4bdd92`.
The K1402 fixture lock remains
`0ee20e3e409a93f1f4b1417c8e2ed64b18564f00213edd1aeaf6cd3af4ffbf7b`.
[launch.json](launch.json) records exact source hashes and the review receipt.

The only launch action, **after parent approval of this exact tuple and a fresh
global capacity reservation**, is creation of
`integration/epic-242-f3-k1402-access-v1` at the orchestration commit above. The
parent admitted token `epic242-f3-k1402-route-20261011-1623` at orchestration
`4a948fbbabaa94fcdc030c15d5922a7b4e8b300b`, but that immutable source hardcodes the
earlier proposed token. The reviewed two-line identity substitution produces
`bf671866e73e8d133726090c0e8295ccdd41c5c1`; parent must reconcile this new SHA before
launch. Worker naming, evidence paths, method, packet and limits are unchanged.
The execution branch remains absent. Do not push the later integration
or documentation head to it, force/reset/recreate it, or rerun an attempt.

The workflow runs only on creation of that branch and attempt 1. A complete
branch-run census also rejects earlier use of this workflow or an incomplete
history. The orchestrator binds its checkout to the Actions SHA, loads the
literal frozen packet, and checks the separate clean method checkout and all
426 method hashes plus the outer dispatch wrapper before execution.
The method checkout uses `fetch-depth: 0`. Before provisioning, source checks
read the exact historical cohort commit
`191a4db30d90fe43025ec2633e23f9b069f12b85` and verify its bytes against the frozen
packet hash. Missing history or altered bytes fail closed. This correction
supersedes orchestration `4aade25ec10edd3fdada3deedfe7f55d275fd7b8`; independent delta review and
historical-availability regressions pass.

## What the first job will do after admission

1. Bind the actual absolute Python 3.11 executable, resolved path, binary hash,
   version and exact numpy 2.2.6 / scipy 1.15.3 / shapely 2.1.2 dependencies.
2. Reuse the unchanged hosted-runner dispatch wrapper, pinned image preparation
   helper and native resource guard. Verify actual systemd, cgroup, Docker and
   image capabilities; refuse missing capabilities without substitutes.
3. Authenticate the complete retained K1402 ZIP, regenerate the exact private
   fixture and compare its literal reviewed lock and all 297 files.
4. Substitute only four runtime identity fields in the frozen K1402 argv:
   Python executable, admission token, unique worker and fresh guard JSON file.
   Execute one 300-second route, including both gated probes. The enclosing job
   remains 43 minutes, image preparation 300 seconds, with existing 6 GiB worker,
   12 GiB aggregate, two-worker maximum, no-swap and free-memory controls.
5. Recheck source and fixture hashes, both retained probe identities/exits,
   unchanged guard plan and cleanup. Preserve every original demand and both
   blocked rails. Any proposal remains unchecked and cannot earn native closure,
   complete cohort or architecture credit.

The runner refuses native start without 600 seconds remaining in the enclosing
job, leaving room for the existing guard deadline, cleanup and retention. There
is no apply, settlement, fresh-board or full-warning phase, retry, fallback or
two-A dispatch. The old `provision_host.py` is neither imported nor invoked.

## Evidence and validation

An `always()` finalizer copies the complete or partial fixture and inventories
missing proposal, diagnostics, guard and route-log files as `NOT PRODUCED`.
Bootstrap, initialization, dependency, image, artifact and route evidence is
retained for 30 days. Failed finalization produces a separate negative receipt.
Platform cancellation or timeout can prevent upload; missing evidence never
proves successful execution or cleanup and blocks subsequent admission.

Both independent reviewers cleared the source orchestration. All 51 source
tests passed, including 16 orchestration/receipt regressions. YAML and shell
syntax, circuit/docs/TypeScript and frozen baseline checks passed. The prior
two-probe result checker is unchanged except for its method binding; no new
guard framework or repeated native qualification was introduced. The pinned
numerical environment supplies routing dependencies; test-only PyYAML comes
from the source-test interpreter and is not an execution dependency.

Actual execution-host provisioning, image preparation, probes and routing are
**NOT RUN**. Fixed panel, circuits, harness identities/full pin order, non-core
poses and canonical copper remain unchanged. The ordinary integration branch
contains the workflow for review but does not match its execution trigger.
