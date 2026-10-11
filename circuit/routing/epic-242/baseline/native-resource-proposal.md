# Native scheduling and resource proposal — SOURCE IMPLEMENTED / NATIVE NOT RUN

Implementation update: `scripts/kicad/native_resource_guard.py` and the opt-in
`scripts/kicad/run.sh` bounded hook now contain the source implementation.
`.github/workflows/check.yml` serializes the shared CI group, runs Python checks
before all three board DRC jobs, and caps board parallelism at two. Every native
CI command now goes through `ci_native_admission.py`, which refuses missing or
stale parent admission variables before invoking the guard. Its harmless source
tests pass; systemd
slice, Docker membership, watchdog death, cleanup and 6 GiB aggregate behavior
have **not** been qualified on a native runner. The rest of this retained document
records the original admission proposal and must not be read as authorization.

Scope: schedule existing checks safely; no new routing search, changed electrical gates or native dispatch. Parent must review the full patch/runner choice and reserve slots before any execution. The scheduling patch alongside this file is necessary but not sufficient.

## Admission and commands

Reserve both global native slots for the complete workflow. Admit only one queued CI workflow; do not cancel an admitted running workflow with a new push. Withhold local routing, audit controllers outside the shared group and every other native lane. Source prep remains independent. Use immutable reviewed integration SHA, pinned KiCad10.0.6 image and existing checks unchanged. Retain complete command/stdout/resource logs and output hashes; OOM/floor/time termination is failure/deferred evidence, never pass.

Sequence: existing python-tests job (one worker, all its current tests/fixture checks/regen --check, sequential); then all three existing board-drc matrix entries (max two workers, full severity/parity/refill checks and original45min job timeout). Documentation remains on a separate runner, with parent accounting for any colocated resources. No board is omitted. Existing audit40min controller/50min job guards remain unchanged; CI job timeouts stay unchanged. No long routing in baseline recovery.

## Original proposal retained for provenance

Use Linux runners with systemd+cgroupv2+local Docker daemon. Fail preflight for remote Docker, absent supported memory controller, unsupported Docker cgroup parent, unknown runner placement, native-binary fallback or insufficient RAM. Require at least8GiB **MemAvailable** before starting each6GiB worker (6GiB limit+2GiB floor), including image already pulled and runner overhead. Standard runners that cannot satisfy this must remain blocked; parent supplies a suitable larger runner, never lower floor/cap silently.

Each native job gets a unique systemd slice named `epic242-<run>-<job>.slice` (sanitized lowercase identifier). All host subprocesses and all KiCad Docker containers for that job must enter the SAME slice. Suggested reviewed slice unit (created only on the disposable admitted runner):

```ini
[Unit]
Description=Bounded Epic242 native worker
[Slice]
MemoryAccounting=yes
MemoryMax=6442450944
MemorySwapMax=0
```

Install this unit under runner `/run/systemd/system`, daemon-reload, start slice. Set and verify its `memory.max=6442450944`, `memory.swap.max=0`; capture path/controller values in evidence. The job command runs via `sudo systemd-run --wait --pipe --collect --unit=<unique>-checks --slice=<unique>.slice -p KillMode=control-group -p User=<runner-user> -p WorkingDirectory=<checkout> /usr/bin/bash <exact-job-script>`. Explicitly preserve only required CI/check environment, including a proposal-specific slice variable. Do not move the runner agent/Docker daemon or unrelated processes into this slice.

A separately reviewed opt-in change to `scripts/kicad/run.sh` must, in this mode, refuse KICAD_CLI_BIN/native fallback and require Docker. Every `docker run`, including version probe, receives:

```sh
--memory=6442450944 --memory-swap=6442450944 \
--cgroup-parent="$EPIC242_NATIVE_SLICE" \
--label "epic242.native.worker=$EPIC242_NATIVE_WORKER"
```

Keep network-none, pinned image, UID, mounts and version check intact. Per-container cap prevents bypass; shared slice cap covers SUM of host Python/native children and containers in this worker, not6GiB separately for each. Inspect a disposable bounded version-probe container's actual host cgroup path and ancestors to prove membership and limits before real checks; fail if Docker puts it outside the slice. This probe itself requires parent admission. At most two such6GiB slices globally =>12GiB aggregate hard maximum, with the parent excluding all other native processes. On separate hosts each host still has its own2GiB free floor; on a shared host parent must preflight total12GiB+2GiB free plus overhead before admitting two.

## Free-memory and time watchdog

A host watchdog OUTSIDE the bounded slice samples `/proc/meminfo` MemAvailable and slice memory.events every second from before launch through final container cleanup. Required floor is2147483648bytes; preflight8GiB/worker provides headroom. At or below floor, any `oom`/`oom_kill` increment, missing monitor/cgroup, or deadline: log reason/timestamp/current/peak/events, stop the checks service, kill/remove ALL containers matching this unique worker label, stop the slice, return nonzero. Signal/EXIT handlers must perform the same targeted cleanup; never kill unrelated containers. Use a conservative earlier abort threshold (e.g.2.5GiB) to protect the2GiB floor during polling/cleanup. Polling cannot prove a never-crossed instantaneous floor; continuous samples plus kernel limits and final events are required evidence, with any observed violation invalidating the run. Parent must monitor machine-wide native admissions as well.

Run exact job script under both the existing workflow timeout and a shorter watchdog deadline sufficient for cleanup (e.g.28min for30min python job,43min for45min DRC). Never lengthen existing route/controller guards. Capture worker ID, admitted SHA, command, time, available memory, slice peak/current/max/swap/events, Docker inspect membership/caps and exit status. Cleanup is bounded; parent receives any surviving process as a blocker. Native work on managed local machines additionally requires the existing heavy guard, when accessible and authorized; this proposal does not substitute for it or access denied home paths.

## Implementation acceptance before dispatch

A follow-up reviewed source patch must supply slice creation/cleanup, watchdog, opt-in run.sh changes and workflow wiring, plus non-native mocked tests for missing controller/remote daemon/refused fallback, argument injection safety, floor/OOM/time abort, exact targeted cleanup, monitor death and status propagation. No claim that the present scheduling-only patch already implements these controls. Then parent admits the bounded real version/cgroup proof; only if it passes does parent admit full checks. If runner/systemd privileges or memory are unavailable, defer under a verification issue. No execution is authorized by this document.

## Startup clarification

The tracked repository AGENTS.md delegates to circuit/WORKFLOW.md and does not itself require the personal loader. The stop requirement was supplied in the managed cloud startup block: "Stop on real conflicts or a missing loader" and "If the task requires stopping when canonical host instructions are absent, stop". The denial additionally forbids workaround/indirect execution; #250 reports no verified installed profile. That is its unresolved startup contract, not evidence that another environment's successful loader applies here. An explicit user instruction waiving unavailable optional personal-profile initialization **for repository-only work** would suffice to authorize that narrower continuation; it would not authorize denied runtime paths, link/config changes or claim personal context was loaded. The owner subsequently granted this repository-only waiver for #250. #250 is now resumed for source preparation only; the denied runtime paths remain prohibited. #246 reports its own successful read-only loader; do not generalize it to #250. No protected path was read for this diagnosis.

## Historical unwired proposal candidate (superseded)

`native_guard_proposal.py` is an **unwired proposal**, not an accepted guard. `native-docker-hook-proposal.patch` is unapplied; `scripts/kicad/run.sh` was unchanged at that proposal epoch; the source implementation above supersedes it. Eight non-native boundary tests pass; proposed shell syntax passes. `--plan` prints the proposed command with no Docker/systemd/native execution.

The candidate refuses existing worker labels/units/configs before entering owned cleanup, creates a dedicated bounded slice, checks exact reviewed hook digest, adds an independent systemd watchdog monitoring parent identity/free memory/OOM/deadline, watches supervisor health, uses RuntimeMaxSec on driver and absolute remaining-time timeout inside each proposed Docker container. Parent reserves all global slots; local flock only coordinates guard instances on this host. All real cgroup/Docker membership/version, signal/death/cleanup and global-runner qualification remain NOT RUN. The existing heavy guard remains required for admitted managed local work; denied home paths are not accessed by this proposal.

Before execution, independently review candidate and prove actual membership using an admitted bounded version probe. Current hook is not installed, so the proposal fails closed for execution. No native run is authorized. Existing-label cleanup and missing independent watchdog findings from first independent review were corrected in the candidate; no claim that these non-native tests prove operational Linux/systemd behavior.

Final independent cleanup review required producers-first ordering and monitoring through cleanup. Candidate now stops checks/anchor, removes only unique labeled containers, checks survivors, then stops watcher last; short individual cleanup timeouts and watchdog120second cleanup reserve replace the earlier30second reserve. Operational deadline/cleanup proof remains NOT RUN; do not treat source review or mocks as qualification. Exact installed Docker-hook digest is required, including hardcaps/cgroup-parent/absolute-inner-timeout tokens. First bounded cgroup/version proof must be separately reviewed and admitted before actual job execution.
