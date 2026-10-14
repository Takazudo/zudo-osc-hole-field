> Historical containment/host-fixture checkpoint. Current delegated authority, real attempts and remaining certificate blocker are recorded in [WORK.md](../../../../WORK.md) and the [latest terminal audit](../qualification-attempt7/review.md). The “no operation admitted” statements below describe this earlier fixture checkpoint.

# Task-local containment on the existing WSL host

The reviewed alternative is implemented and exercised on this host with tiny
synthetic payloads. Host swap remains configured at 16 GiB. **No qualification
or production operation was admitted. Stage C remains NOT RUN;
KEEP_K1402_INCUMBENT.** This is host-mechanism progress, not numerical progress.

This continuation starts at PR #277 head
`24f91c18e74d75dc28409d67342d9c76fcf69423`, on the clean existing
`topic/e16-attribution-executor` worktree. Refreshed local/remote heads agreed;
tmux/process/worktree checks identified this continuation as its owner. The base
remains `topic/e16-attribution-reconstruction` / `dec36940e2691e384b9d8d499675761078d64308`.
No integration ownership, stack rewrite, merge or duplicate executor branch.

## Selected contract and source changes

`attribution_containment.py` implements `task-local-notify-v1`.
`attribution_host.py` launches the enclosing service and uses direct delegated
child cgroups instead of launching a second systemd scope outside its parent.
`attribution_admission.py` includes the new module in explicit source bindings.
Numerical executor, solver/refinement, selected RHS, tolerances and physical
identities are unchanged. The old host-swap refusal is still called if the new
complete pre-claim containment proof fails. There is no flag to waive it.

The compiler's `host_limits`, source manifest and operation digest bind this
contract, including the enclosing limits, fixed timer, log/receipt reserves and
external reserve. Old sealed requests cannot silently select it. The fresh
[source-only description](operation-description.json) has operation digest
`45bbbfff987208a65e99c5f500244706783e831b4da5bfbc485e27e78f0f1bba`.
This is **not** a qualification or production request digest. Both request digests,
numerical run IDs and numerical output identities remain null. Final clean HEAD
must be bound by the compiler when an independent owner later seals a request.

## Complete process and cgroup accounting

```text
initial CLI -> exec systemd-run --user --no-block -> exits before guard starts
shared user manager / D-Bus: activation and collection, external reserve
fresh notify service: memory.max=1984 MiB, memory.swap.max=0, pids.max=48
  bootstrap (64 MiB): main wrapper, queue notifications, custody, final receipt
  control (576 MiB): unchanged guard shell, sampler/watchdog/utilities,
                    outer admission/accounting controller, verification helpers
  active (1344 MiB): direct unshare / fixed contained host
    supervisor (64 MiB): verification, retention, mount/cleanup helpers
    worker (1216 MiB): one numerical worker and its subprocesses
    sticky bootstrap allowance (64 MiB), charged at the active parent
```

All admitted operation-owned processes are born in, or fork from, the enclosing
service; the inner worker's process ancestry and actual cgroup placement are both
checked. There is no nested manager-created scope that can escape to `app.slice`.
The service is created with hard limits before its first exec. The wrapper starts
in `DelegateSubgroup=bootstrap`, enables children only with an empty parent,
and verifies root and child limits before launching the guard.

The initial CLI execs its launcher, whose PID **and start identity** must be gone
before the guard starts. Exec releases that launcher's previous anonymous address
space; moving a PID does not transfer previous charges. Fork/bootstrap charges
created inside the service remain charged under its root, even when descendants
move to a child. File cache, tmpfs, pipe/kernel memory, verification objects,
retained copies, cleanup and receipts created there count against its hard cap.

**1984 MiB root + 64 MiB external shared-service/pre-exec file/kernel reserve =
2048 MiB.** The former 64 MiB systemd-launcher allowance now pays for the resident
notify wrapper. Inside the root: 64 + 576 + 1344 = 1984 MiB. The numerical worker
stays at 1216 MiB. Root hard limits also cover sticky parent charges; summing
child samples is never used as proof of the aggregate bound.

The external reserve is an explicit conservative allowance, **not** a claim that
shared systemd/D-Bus processes were moved, locked or kernel-contained. No global
service or another workload was changed. Its attributable activation/collection
cost remains part of future combined resource qualification; tiny fixture peaks
do not qualify that allowance or the real pipeline. Host-wide swap counters are
not used as the new operation proof. Zero swap for service-owned charges is
kernel-enforced from service creation, then checked at actual parent/child paths.

## Clock, shared scheduling and termination

The shared guard and its configuration/hash are unchanged. Queueing retains its
existing semantics. Only the main notify wrapper receives `NOTIFY_SOCKET`; the
service unsets the installed platform's documented loader-control variables
before Python exec, and descendants receive the existing clean environment.
While queued, the wrapper extends the startup timeout. On observing its actual
guard PID and original entry timestamp, it stops extensions and sends READY.

Before READY, Linux `pidfd_getfd` duplicates the direct guard child's **actual
fd200 open-file description** into wrapper fd201. Reopening `/proc/PID/fd/200`
or releasing/reacquiring a new flock would not preserve custody. The wrapper
keeps this duplicate through fsynced terminal work until process exit. Thus the
unchanged guard writes its durable row, but the shared slot remains locked while
the wrapper kills/reaps leftover helpers, cleans actual cgroup subtrees and writes
its receipt. No scheduling control or reservation authority is invented.

Before a diagnostic claim, the outer controller verifies actual unit/cgroup
identity, wrapper descriptor custody, `Type=notify`, `NotifyAccess=main`, no
restart, whole-control-group kill, and that activation + **174 seconds runtime +
1 second forced-stop allowance** fits within the original guard-entry +180s.
Missing/late notification, changed limits or wrong placement refuse admission.
Existing deadlines still use the original guard timestamp; no timer restarts.
The manager kills all service descendants if the wrapper fails or exceeds its
runtime. Crash/incomplete evidence requires external reconciliation, never retry.

## Output and terminal acceptance

The aggregate cap remains 64 MiB. Temporary output and its retained full copy
share the existing two-copy quota. Existing claim, accounting, worker/supervisor
logs and receipts remain charged. The contained-host receipt ceiling is reduced
from 128 to 96 KiB within the existing 256 KiB host-receipt reserve, making room for
the additional envelope receipt. Envelope log bytes are capped at 4 KiB and stored
losslessly as base64 inside its at-most 16 KiB receipt.

The envelope receipt is an O_EXCL state file outside the numerical output tree:
`~/.local/state/zudo-e16-attribution/<run_id>.envelope.json`. It binds the exact
request/run, immutable accounting-journal hash, exact durable guard-row hash,
unit/cgroup, kernel limits/observations, cleanup, timing and false acceptance flags.
The final aggregate check adds its actual bytes. Grants must cover the envelope
tail, not only the guard's earlier timestamp. Read-only `accepted_result()` also
requires the actual unit and cgroup to be collected. Worker success, a zero swap
sample, an inner host receipt or a guard PASS alone is insufficient.

Valid-identity failures before guard setup retain bounded INCOMPLETE evidence.
That evidence deliberately does not claim successful cleanup; later host fixture
observation confirmed automatic service collection. No existing receipt is
replaced. A missing/incomplete terminal or accounting record is not accepted.

## Real host fixtures and bounds

All fixtures used fresh task-owned resources, current UID 1000 permissions and
unchanged shared scheduling. No privilege escalation, keys, grants, real packets,
original data, campaign accounting, native oracle or host settings were used.
The full driver substitutes synthetic metadata/command providers and small
fixture ceilings; production admission itself is not mocked into approval.

Reproducible current mechanism fixture, from the executable source directory:

```sh
/usr/bin/python3 -I -S -B evidence/e16/attribution-admission-wsl-20261014/containment/fixtures/envelope_fixture.py
```

Its `coverage`, `failure` and `bootstrap` arguments test wrong placement, a failed
payload with a detached descendant, and a deliberately mismatched fresh root
memory cap. These are fixture cases, not production flags. The driver uses the
real unchanged guard inside its service, so do not wrap it in a second guard.

Declared per complete fixture: 192 MiB service +64 MiB observer, 48 service tasks,
1 MiB tmpfs, under 64 KiB output, 6s active runtime +1s forced stop; observer stops
only its exact owned unit after 20s. The payload is 4096 synthetic bytes. Initial
scope probes used192 MiB/16 tasks/12s; timer/custody probes used smaller caps.
Commands and all source/probe transcripts are in [fixtures](fixtures/) and
[checks](checks/). The final successful fixture measured **47,013,888 bytes peak**
at the service root, elapsed 0.7703s from the conservative guard timestamp,
kernel `memory.swap.max=0`, observed swap 0, no OOM, complete retention and cleanup.
These are tiny-mechanism measurements, not estimated numerical resource use.

Retained negative findings:

- Live `RuntimeMaxSec` mutation fails for both scope and service with the exact OS
  message `Cannot set property RuntimeMaxUSec, or unknown property.` The supported
  delayed-notify path replaces that rejected design; it is not a global host blocker.
- Initial notify probe mistakenly expected child memory files before enabling the
  controller. The corrected probe demonstrated delayed runtime and collection.
- Applying `RLIMIT_FSIZE` to the shared guard also prevented appending its already
  large existing ledger, yielding exit 153 after the displayed verdict. Those
  preliminary transcripts are **not accepted durable-guard evidence**. Later runs
  keep that guard unrestricted and enforce task output limits in the task code.
- Initial scope reporter joined an empty collected ControlGroup to the cgroup
  root; its false `scope_path_absent` boolean was corrected by checking the exact
  previously observed path. Both that path and its mount directory were absent.
- The first integrated fixture rejected an unrelated 4616-byte historical guard
  row. The bounded historical parser now matches the existing 16 KiB reader while
  the selected operation's own receipt remains at most 4 KiB. The failure is retained.
- The bootstrap refusal reporter initially indexed a deliberately absent guard
  hash. The actual INCOMPLETE receipt and collected unit were retained, the
  reporter corrected, and its task-owned temporary directory removed.

The positive fixture and negative placement/worker fixtures checked task-owned
subgroups, namespace/tmpfs, actual worker membership, detached-child termination,
full copy/hash retention and removal. The separate custody test proved the lock
remained held after the child exited and released only when its copied descriptor
closed. Failed capability setups were not retried unchanged.

## Checks, preservation and next owner

70 key-free focused source/fixture tests PASS. Circuit checks before and after
PASS (manual inventory scope; no schematic/placement binding). Independent
[review](review.md) covers process/cgroup coverage, startup, scheduling custody,
resource/output accounting, terminal acceptance and failures.

[Preservation](preservation.json): 539 topic and 550 original protected files match;
11 expected absent topic UI-state files remain absent. All 195 retained numerical
artifact paths/sizes match, but **their contents were not opened or rehashed**
because this task prohibits opening original numerical artifacts. Ledger bytes
are unchanged at `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`:
2/3 baselines, 8/24 diagnostics, delta 0, no live owned work, no attribution charges.
Attempt 5 and all prior failures remain untouched.

Aggregate/native/original-data workloads, full qualification and production are
NOT RUN. CI is skipped for this narrowly authorized continuation, not passed.
The full pipeline's verification, decode, certification, solve, all original mesh
passes, accounting, serialization and cleanup still need separately admitted
combined qualification under unchanged caps. No resource fit is inferred here.

The next action belongs to independent trust/operator/controller owners: follow
[the missing signing setup](signing.md), compile a fresh exact qualification
request on the final clean checkout, and provide genuine applicable signed grants
and a current exclusive reservation. This task supplies none. `--launch` now returns after asynchronous service submission; its exit zero
does not mean admission or completion. Final acceptance still comes only from
`attribution_host.accepted_result()` and the complete retained evidence.
No host swap change
is needed for the demonstrated task-local path; all its capability proofs run
again before any future claim. Qualification success would still not admit a
separate production operation.

Stage C's original 10% barrel-copper AND resolved nonzero TP990026 reaction screen
is unchanged and NOT RUN. Missing evidence supports no via; no Stage D/adoption.
Canonical geometry/copper, held sources, transfer-barrel intervals, decision.json,
separate +5V/native-negative-control work remain unchanged. PR #260 stays draft and
unmerged; issue #253 stays open.
