# Resource and admission review

Reviewer: `/root/resource_review`. The review of the main author's executor, checker, resolution and lifecycle is independent. This reviewer subsequently authored the delegated supervisor/transport fixes and their tests; those portions are author validation, **not independent self-review**. Their independent cross-review belongs to `/root/numerical_review` and [numerical-review.md](numerical-review.md). That reviewer confirmed the final integrated supervisor delta and final hashes, reran 119 focused tests successfully in 5.306 seconds, and reported no remaining source-scope findings.

Disposition: **SOURCE_INCOMPLETE / NOT_QUALIFIED / NOT_PREPARED / NOT_ADMITTED / NOT_RUN**. The new source makes concrete progress through the actual selected pipeline, but is not an executable production request. No production artifact was decoded, numerical unit executed, native operation launched, scope/mount provisioned, approval created, reservation acquired, or campaign ledger mutated by this reviewer. Production request digest remains null.

## Independent source review and findings

Read the predecessor handoff, original `finite_units.py`, `finite_solve.py`, `numerical_unit_guard.py`, `replay_steps.py`, historical numerical wrappers, current native admission implementation, and the new executor/lifecycle/checker/resolution source. The historical wrapper requires 148 units. The native adapter has native-specific qualification and resource ownership. `replay_steps.Ledger` hashes before guard entry, captures whole pipe contents, writes/hash-checks after the guard, and supports resume. None is silently reused as this one-unit production launcher. Shared source and historical requests are unchanged.

The new lifecycle uses a fresh O_EXCL single-use claim and refuses changed source, digest, caps, bindings, duplicate identities, absent/inapplicable fixture authority and absent/nonexclusive fixture reservation. Those objects are **already-authenticated observations only** in the internal core, not independently verified production grants. `execute_production()` unconditionally refuses. No remaining campaign budget or native negative-control request is treated as authority.

Streaming decoding hashes the same opened descriptor before interpretation, keeps compressed/decoded identities distinct, bounds reads and decoded bytes, rejects trailing data, and verifies file identity/hash after interpretation. Pickle remains trusted-code input. The decoder's limits do not bound pickle memo/NumPy/Python allocation independently; the complete guarded worker cgroup and conservative object allowance remain necessary. Source fixtures are not an authorization path for original artifacts.

Original Assembly replay preserves source numbering and verifies node/ring/support/interior mappings and complete retained stiffness. The implementation makes **eight complete mesh passes per board in Assembly, plus one accounting pass**, each with decoding and two compressed-byte hash passes. A replay generator retains one chunk container at a time, but Assembly retains prior value arrays through its vv lists, along with keys/allkeys/unique/inverse/compact arrays and sparse-construction workspaces. A one-chunk container is not a one-chunk memory bound. Both original full Assemblies are not retained together.

The independent interval checker has separate input-CSR, retained-factor/fill and arithmetic caps. Exact stored symmetry, positive lower pivots, finite outward bounds and all caps are explicit fail-closed gates. No real matrix has been inspected for those gates. Natural-order Python dictionary LDL and retained inverse-bound factors can require substantial object memory/fill. The forward-error extension adds a second serial operator construction/residual enclosure pass, interval energy passes over every component and exact source-reaction functional passes. These must be included in qualification; they are not free consequences of the solve.

Concrete findings communicated and resolved in source include the inappropriate baseline/Ledger reuse risk, failure-receipt headroom consumption by success summaries, understated Assembly replay/lifetimes, conflated certificate input/fill caps, and missing retained comparison/resolved reaction decision operations. The main author implemented comparison and interval error enclosures; their numerical validity is covered by the independent numerical review. The deliberately absent host verifier/provisioning/qualification is retained as an explicit blocker, not relabeled as complete.

## Authored supervisor and transport fixes

`attribution_supervisor.py` is a stdlib subprocess supervision primitive, with no public production CLI, authority constructor, scope creator or shared-runner edit. Production checking requires existing guard ancestry and real cgroup-v2 files proving:

- A 2 GiB/no-swap parent, a 64 MiB supervisor subgroup, and a worker sibling limited to the remainder. Worker OOM cannot consume the supervisor's reserved subgroup capacity.
- A fresh worker cgroup, usable cgroup.kill, and a single-threaded supervisor before pre-exec migration.
- A dedicated worker-output tmpfs whose kernel capacity leaves 1 MiB log and 64 KiB terminal reserves. Earlier in-unit claim/log bytes are separately subtracted from this capacity.

The actual guard-entry monotonic timestamp determines the deadline. Production work stops at least ten seconds before the 180-second endpoint, preserving time for kill, worker-population verification, bounded output hashing and receipts. A caller cannot reset the clock to worker launch. Pipes are drained in bounded blocks; log overflow fails the operation. All retained files are counted and hashed; symlinks/special files and oversized inventories fail closed. The worker's apparent COMPLETE marker is renamed to an unaccepted marker below `.work.partial/result`; only the supervisor's final receipt can accept it. Timeout, cancellation, nonzero exit, OOM observation, failed cleanup, missing/mismatched output or late finalization cannot produce an accepted result.

Transport failure is idempotent, keeps separate failure-receipt space, revokes a previously completed component filename on late failure, rejects noncanonical output paths, and uses a pending receipt before final rename. The numerical reviewer found that supervisor log flush/fsync errors and worker-marker rename errors could escape before a negative receipt. These are now caught and reported, with explicit marker-revocation status and fault-injection tests. Persistent filesystem failure can prevent receipt retention; output then remains unaccepted rather than being reported as a successful diagnostic.

The supervisor's `cleanup_complete` records worker-process cleanup only. Host scope/mount ownership, persistence of retained output, and removal of owned scope/mount resources still require the disabled production adapter. No source statement claims that this host integration exists.

## Bounded validation

Final reviewer command:

```sh
/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_executor test_attribution_lifecycle test_attribution_supervisor -q
```

Result: **52 tests PASS in 3.853 seconds**: 21 executor/checker tests, 8 lifecycle tests, and 23 supervisor/transport tests. This is a focused result, not the full E16 suite count.

The final integrated supervisor regression creates the existing tiny serialized fixture with `test_attribution_executor.packet()`, verifies its fixture node ceilings, runs the actual `_once()` single-use claim and `run_pipeline()` operation in the supervised child, and checks the real five-component output, all three source reactions, supervisor hash inventory and consumed fixture claim. Child Budget uses the supervisor work deadline and output allowance. No mocked terminal marker substitutes for this integrated test.

Other supervisor fixtures cover bad/missing output, repeated output identity, timeout after an early worker COMPLETE, cancellation, simulated OOM observation, failed executable/spawn, missing real guard, bounded pipe-log exhaustion, output symlinks, prior claim-byte accounting, log fsync failure, marker rename failure, transport summary exhaustion, repeated failure, late success revocation and transport fsync failure. OOM is an injected observation; no native cgroup OOM test was run.

The synthetic subprocess wrapper has fixed 384 MiB address-space, 2 CPU-second, at most 4 MiB-per-file, and 64-file-descriptor ceilings. Initial 256 MiB AS rejected the integrated fixture: its child reached fixture operator creation, then was terminated by the CPU cap, and retained a negative supervisor receipt. A source-only tiny `packet()` measurement was 0.0402 seconds, VmPeak 281,244 KiB and RSS 71,492 KiB; imports alone used VmPeak 211,376 KiB. This justified the fixed 384 MiB fixture AS ceiling without changing numerical fixture dimensions. It is **not production memory or runtime qualification**. Temporary fixture directories and children were cleaned by the tests.

## Remaining exact production work

1. Implement and independently review the host-side verifier for applicable externally supplied numerical authority and a current exclusive reservation, with exact immutable packet/toolchain/input/output bindings. Neither internal dictionaries nor a reference string establish this.
2. Connect the fixed worker command, true guard-entry timestamp, claim accounting and worker Budget/result path to independently owned cgroup and quota provisioning. Review output persistence and scope/mount cleanup within the same interval. Do not substitute the 148-unit hook or modify shared runner ownership.
3. Qualify the **combined** load/decode/replay/certificate/residual/solve/accounting/hash/receipt/cleanup operation under the unchanged caps. Count retained factor dictionaries, array/memo storage, CSR/CSC and symmetry copies, long-double scratch, all repeated mesh/operator passes, interval functional loops, logs, quota filesystem memory and failure paths. An exact admitted qualification action is still needed if source analysis cannot establish these bounds.
4. Seal a complete production request only after that source/host/resource boundary is reviewable. Success of the certificate and all attribution/interval gates is still required on the actual in-run matrices. No exact-matrix evidence currently exists.

No production execution command is invented. Stage C for KB U7105.4 remains **NOT RUN**; source fixture outcomes are not evidence for the proposed via. All electrical acceptance, whole-board acceptance and adoption flags remain false.

Campaign ledger independently rehashed unchanged at `94aafb6d13f754fdbde718a5b44c5071d946897e798a8eebf1cd4b86c0731ffb`; actual delta is zero, preserving 2/3 baselines and 8/24 diagnostics. Attempt 5, prior failures, original held identities, fixed experiment and separate native request remain untouched.

## Reviewed source bindings

| File | SHA-256 |
| --- | --- |
| attribution_executor.py | 45033ebe5b5f7a366e31e0c5a6fd01aaaadacc7a13613899354a17c188a587e3 |
| attribution_lifecycle.py | 639b31dbddbee056585ba4af8205e191ff73c4c10a2b70f3a03b8ad78bb58343 |
| attribution_resolution.py | 02b993fff01a5c848ab751f7cc84a10f61a8ac855bcbeb6398c1df549cabc91e |
| attribution_uniqueness.py | c913e12e00d9a583631ef826e087efc6fb1cd20b769fe171d120d064b7df0b3c |
| attribution_transport.py | c122e14552447ee495f91840100f9e0dc703bd7cda6ce64d9cb726a246ca0d50 |
| attribution_supervisor.py | cd27b2abde547a3ed3d1bb1fa26587d16508fa078b2540c0810f565291671d8c |
| test_attribution_supervisor.py | 9255fbfa9f9c4e9cd10f5d1e2657205a99dc54fbeab3ed9ada44a386ef977b6f |

Final handoff note: the supervisor EOF-only whitespace correction is independently byte-reviewed in numerical-review.md. Its final SHA-256 is `b6a030b3e3011fe5df8601a817c2fbf092ee69711b8ee820b14eca45559d36e7`; the earlier table is the reviewed pre-whitespace snapshot. Final 358-test E16 evidence binds the final source in checks/summary.json.
