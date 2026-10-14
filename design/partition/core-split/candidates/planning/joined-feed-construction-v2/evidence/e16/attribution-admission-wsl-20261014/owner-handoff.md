> Historical checkpoint. The current [task-local containment continuation](containment/README.md) supersedes the host-swap-only path and adds real mechanism evidence. Original numerical and external-signature restrictions remain in force.

# Independent-owner action for selected E16 qualification

**Stop at the external boundary.** This source-only continuation did not admit
qualification or production, decode any real numerical artifact, or create a
request, signer, grant, reservation, claim, scope or numerical output. The current
host fails the existing zero-host-swap prerequisite. No executor source change
was needed; this handoff corrects the working-directory instruction and makes
the owner actions concrete. Stage C remains NOT RUN; missing evidence supports
no via. KEEP_K1402_INCUMBENT.

## Refreshed checkpoint and evidence

Inspected local and refreshed remote `topic/e16-attribution-executor`:
`d1e967f64804ca3335ff5d957998e57b598dcbf1`, draft [PR #277](https://github.com/Takazudo/zudo-osc-hole-field/pull/277).
Stacked base remains `topic/e16-attribution-reconstruction` at
`dec36940e2691e384b9d8d499675761078d64308`. The clean existing executor worktree
was reused after checking worktree records, processes and tmux ownership; the
project's active terminal was this continuation. No stack integration is claimed.
This evidence-only commit descends from the inspected head; the compiler must
bind the final clean HEAD when a future owner seals a request.

The actual `attribution_request.py describe` CLI reproduced the retained
[operation-description.json](operation-description.json) byte for byte:

| Binding | SHA-256 / identity |
| --- | --- |
| Operation, **not a request** | `8013ecb171a02ae5794d228c39713c647dbc911f917325f8a1cd62589abbe214` |
| Description bytes | `9a87bb9379e4f26451528c059a1da0dea9bdcb13cafccd0abab609f8c317138f` |
| Independent original inventory | `8cfcf5fac5bd749dcd58313b4df8eb1a9080723a5c5d34d80c548098c2d60b18` |
| Original request, compressed | `3ac6356762419c653c8949adb1c2d12db58e109408d52246ef482e9a398adc54` |
| Original request, retained decompressed identity | `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6` |
| Shared guard | `074a463dd6b3a65b7e2168df95b200c0192c414862375bcfb95f979c34c67ee7` |
| Live campaign ledger | `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb` |

The description carries all 99 source and 3161 toolchain/library file paths and
hashes, the 16 explicit source bindings, and all 33 selected original input
bindings. Original artifacts were checked only as raw bytes: no decompression
or deserialization. The original decompressed request identity above is retained
provenance, not a fresh decode. Exact command results, host observations and
preservation are retained in [checks/owner-review.json](checks/owner-review.json)
and [checks/owner-checks.txt](checks/owner-checks.txt).

## Observed host facts versus untested capability

At the recorded observation, `/proc/meminfo` reported **SwapTotal=16777216 kB**
(16 GiB); `/proc/swaps` listed `/dev/sdc`. Calling the existing read-only
`attribution_host.prove_no_host_swap()` refused with
`outside controllers require host SwapTotal=0; no host configuration fallback`.
This is an observed hard prerequisite failure, not merely absent resource proof.
No guard was entered. No swap or other host configuration was changed.

The user systemd manager responded as `255.4-1ubuntu8.17`;
`user@1000.service` reported `Delegate=yes`; cgroup v2 advertised `memory`.
These facts do **not** prove the requested fresh scope can delegate memory,
preserve UID in a user/mount namespace, enforce the exact child limits, mount
the quota tmpfs, or complete cleanup. Those operations and actual library
loading remain NOT RUN. Missing optional user-namespace sysctl paths are not
treated as evidence of disabled namespaces. Available RAM is a host snapshot,
not a pipeline peak or a resource-fit result.

The fixed signer store and attribution state directory were absent; no matching
attribution scope was listed. No genuine exact qualification packet, applicable
authorization or current exclusive reservation was supplied to this continuation.

## Required owners and actual compiler interface

1. **Host owner:** separately resolve the zero-host-swap prerequisite and choose
   the execution host. This task authorizes no host change. Moving hosts or
   changing toolchain/paths requires a fresh description and exact bindings;
   historical host facts and grants cannot be reused. Kernel feasibility remains
   a gate of the separately admitted operation, not an unapproved probe.
2. **Independent trust owner:** provision the fixed account file
   `/home/takazudo/.config/zudo-e16/attribution.allowed_signers` with genuine
   independently controlled public signing identities. Code requires a regular
   file owned by the execution UID, no group/other write bits, at most 65536 bytes,
   and an exact SHA-256 bound into the request. It is outside the checkout and
   packet; no alternative packet-supplied trust root is accepted. Fixture keys
   and grants are never authority. This continuation installs and signs nothing.
3. **Request preparer:** on the final clean immutable checkout and intended host,
   review the complete description, then use the existing compiler below to seal
   a distinct qualification request. Sealing is preparation, not authorization.
4. **Independent operator and controller:** review that exact request and issue
   the applicable signed authorization and current exclusive reservation below.
   No numerical work can start until these pass the existing admission checks.

Commands below are **owner preparation instructions, not executed sealing or
launch commands**. Run from the repository root; output paths must be fresh
absolute paths outside tracked files. The owner sets `DESCRIPTION` and
`QUALIFICATION_REQUEST` to those reviewed paths. `describe` itself is source-only.

```sh
cd design/partition/core-split/candidates/planning/joined-feed-construction-v2
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python attribution_request.py describe --output "$DESCRIPTION"
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python attribution_request.py seal-qualification --description "$DESCRIPTION" --output "$QUALIFICATION_REQUEST"
```

The schema is `e16-attribution-request-v1`, request kind
`resource-qualification`, operation `e16-selected-attribution-v1`, attempt 1.
The compiler creates the 32-hex run ID and output identity and binds current
HEAD, checkout, Python path, host UID/boot/machine, trust digest and ledger digest.
Its `qualification` is null. Do not substitute the operation digest for its
canonical request digest. No request was sealed here; **both request digests
and both run/output identities remain null**.

| Signed evidence | Principal | Schema and OpenSSH namespace |
| --- | --- | --- |
| Qualification authorization | `e16-operator` | `e16-attribution-qualification-authorization-v1` |
| Qualification reservation | `e16-controller` | `e16-attribution-qualification-reservation-v1` |
| Reviewed resource report, after success | `e16-resource-reviewer` | `e16-attribution-resource-v1` |
| Later production authorization | `e16-operator` | `e16-attribution-authorization-v1` |
| Later production reservation | `e16-controller` | `e16-attribution-reservation-v1` |

Each grant is bounded JSON (at most 64 KiB) with a detached `<path>.sig` (at most
16 KiB). Authorization and reservation both bind `request_kind`,
`request_sha256`, `run_id`, `operation`, exact `limits`, `issued_unix` and
`expires_unix`. Authorization requires `approved: true`; reservation requires
`exclusive: true`, exact current `host` and the request's `ledger_sha256`.
Times must be finite, issued no later than verification and valid for the full
remaining 180-second interval; queue delay can invalidate an otherwise signed
grant. The controller's live exclusive flock at
`~/.local/state/zudo-e16-attribution/reservation.lock` and ancestor/descriptor
proof must also hold. A signed reservation alone is insufficient.

Once separately authorized, the existing execution entry is
`attribution_host.py --launch --request ... --digest ... --authority ... --reservation ...`;
there is no lifecycle execute CLI. This describes its interface, supplies no
approvable packet or authority, and is **not an instruction to launch now**.

## Fixed consumption, complete qualification, terminal evidence

Caps stay **180 seconds from actual shared-guard entry, 2147483648 bytes total
memory, zero swap, 67108864 bytes aggregate output; one diagnostic, unit, selected
RHS and attempt**. Worker allowance remains 1216 MiB. Active scope 1344 MiB plus
512 MiB shared-guard helpers and three 64 MiB outer/launcher/cache reserves
equals 2048 MiB. The scope includes the 64 MiB supervisor and 64 MiB bootstrap
reserves. Logs, accounting and receipts, temporary output and durable retention
copies all count; cleanup and terminal receipt time are inside the interval.
The detailed [resource plan](resource-plan.md) is unchanged.

Qualification must cover all verification and repeated manifests/linkage checks,
original decoding, exact certification, original solve/refinement, nine complete
mesh passes per board, exhaustive accounting, serialization, retention, cleanup
and receipts. Tiny fixtures, compressed sizes, historical individual timings or
partial mesh coverage cannot qualify it. No cap increase or automatic retry.

Only the existing E16 accounting path may charge the canonical
`~/.cache/zudo-e16-runs/campaign-20261014/campaign-note.json`. A claimed
qualification consumes one diagnostic even if launch or execution fails:
the observed 8/24 would become 9/24, while 2/3 baselines stays unchanged.
Production is separately charged (10/24 only if these are the next two claims).
Pre-claim refusal consumes no diagnostic. O_EXCL claim records preserve the
original ledger bytes; worker-start identity is single-use. Crash, partial
accounting or incomplete cleanup requires external reconciliation, never retry.

Retain the exact request and signed grants, claim and worker-start token,
contained resources and complete output inventory, numerical/component output,
cleanup evidence, host `terminal.json`, immutable
`~/.local/state/zudo-e16-attribution/<run_id>.terminal.json`, final campaign state,
and exact durable row in `~/.agent-guard/heavy/runs.jsonl`. Worker success is
unaccepted; host status stays `PENDING_SHARED_GUARD` until read-only
`attribution_host.accepted_result(request_path, digest)` verifies the terminal
journal, output, claim, cleanup, grants and unique guard PASS receipt together.

After qualification succeeds, the independent resource reviewer must inspect
the actual complete evidence and sign `RESOURCE_QUALIFIED` for this operation,
exact caps, expiry, all phases, cleanup and measured elapsed/peak memory/output,
zero swap, concurrency one and attempt one. The schema also requires a
production-admission time allowance of at least 10 seconds, with measured time
plus that allowance at most 180 seconds, and 1–16 bound compact receipts totaling
at most 1 MiB. Only then does production preparation use
`attribution_request.py seal --description ... --qualification ... --output ...`,
followed by fresh production authorization and reservation. Qualification success
alone admits no production work.

## Actual result and preserved experiment

Readiness exit **2**, expected blocked readiness. **95 focused source/fixture
tests PASS**; fixture signatures/ledgers were temporary, host observations in
tests were mocked, and tiny numerical fixtures are not real qualification.
Circuit contract checks before/after PASS with manual inventory scope: 68 lines,
0 declared placements, no schematic/placement binding; pin-asset check performed.
Raw preservation matched 135 retained solver files plus 60 original +12V inputs,
all 33 selected inputs, 539 topic/550 original protected files and 19 browser
bindings. Ledger delta **0**, no attribution charges, no live owned work;
Attempt 5 remains terminal (`8262c033387f444581d19ef816622eb5`). No real execution
resource peak, timing, output, cleanup receipt or qualification result exists.

Aggregate regeneration, native oracle, browser, documentation build, broad suite
and numerical workloads were NOT RUN in this evidence-only continuation. The
aggregate workflow includes native operations outside the narrow authorization;
unchanged fixture/source checks do not stand in for these gates. CI is skipped
for this scoped evidence commit to avoid unadmitted native scheduling, not passed.

Selected experiment remains KB U7105.4 / `e97b2d02-463a-5a6d-ab37-748ce29d7cf8`,
+12V, nominal-average, uniform-dielectric, all-present, exactly one 1 A RHS and
complete original KA + interfaces/wires + KB. TP990002/014/026 remain held sources;
TP990026 is neither moved nor deleted. Preserve barrel
`87d2de81-b7e7-5e5c-9063-52b28f51939e` and every original consecutive interval,
solver/refinement conventions, tolerances and maximum-absolute-global-nodal-
injection normalization. Stage C still requires at least 10% original-barrel
copper share **and** a resolved nonzero TP990026 reaction. No result exists;
no via, Stage D or geometry adoption follows. All electrical/whole-board/adoption
flags remain false. Canonical boards, copper, panel/harness/pin intent, protection
and decision.json remain unchanged; PR #260 stays draft/unmerged, issue #253
stays open, and separate +5V and native-negative-control work remain untouched.
