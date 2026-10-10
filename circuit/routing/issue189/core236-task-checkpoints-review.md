# Core audit task checkpoint proposal — parent review required

This proposal changes audit orchestration only. No PCB, accepted copper, fixed
panel, electrical constraints, original zone-evidence verifier, or publication
gate changes. It has not dispatched a pilot. Its worker API is not an approved
standalone native controller.

## Terminal recovery reconciliation

Recovery 38069793801 tested immutable source
63f9541aa68ae3e05ee9700ae71dcaea6dfe02f6. The outer 100-minute controller ended
with timeout 124; native child 137 followed cleanup. This is not an OOM result.
Completed task coverage is 235/426: F.Cu 220/220, B.Cu before 15/103,
B.Cu after 0/103. There are 191 missing tasks. B.Cu before index 15 completed
validation but not DRC and therefore is not a completed checkpoint.

| Work | Completed seconds |
| --- | ---: |
| F.Cu 220 fresh native validations | 2969.174506342 |
| F.Cu 220 report-hash reuses | 3.356541599 |
| B.Cu 16 fresh native validations | 719.674650385 |
| B.Cu one report-hash reuse | 0.016162682 |
| B.Cu 14 new DRCs | 2017.277818009 |
| Total completed operations | 5709.499679017 |

Sampled wall time was 6000.005821705 seconds. The final unfinished DRC/cleanup
interval was 58.585154295 seconds; residual uninstrumented work was
231.920988393 seconds. Peak aggregate owned RSS was 2836588 KiB, minimum
MemAvailable 12489536 KiB. Cleanup left no owned processes or containers.
No final complete-zone, warning, group-connectivity, eligibility, or publication
gate ran. Candidate core 1312 remains unadopted; accepted main remains
JL117/JR129/core1402, native DRC/parity 0/0.

## Proof boundary

The manifest freezes exactly 426 task IDs, including zone, layer, stage, batch,
ordered artwork IDs, both source hashes, context hashes, native scope, kernel
blob revision and expected geometry source reference. Rebuilding the manifest
from different source/context/kernel fails closed. Geometry references freeze
exact source-zone bytes; they are not claims of locally measured native geometry.
The retained artifact binds three native geometry signatures. The fourth
(B.Cu after, 103 tasks) is deliberately unbound and cannot execute until a
reviewed pinned-native bootstrap supplies its exact signature.

Prior reuse relies on an externally approved immutable producer anchor:
run 38069793801/source 63f9541..., compact artifact 11679136451 digest
b2f5f4d7356eed1b0954e64a6eb7bef7b6195f7ff5a2d1535633eeae42ba2342,
and full artifact 11679236513 digest
aa953bd5537e320eabe7ef1119065856bad5f65fad4af3aab750040e9dda6dcb.
The compact artifact and nested inventory/report bytes were locally verified;
all 235 exact PCB fixtures were reconstructed and compared with the retained
full-output inventory. Native receipt, context, geometry, report hashes, version,
severity scope and warning identities were checked. The full 1.05 GB raw ZIP
was not locally byte-verified (download failed); this proposal explicitly uses
reviewed producer provenance rather than claiming that verification.

A matching version string or caller-supplied pass flag is insufficient. The
anchor must come from authenticated GitHub metadata and explicit producer
review. New output ledgers likewise require externally pinned artifact/producer
provenance and ledger hashes before reuse. The production loader authenticates GitHub metadata and mints an in-process
authority; arbitrary caller-provided JSON provenance is rejected. Parent must
review this boundary before any native skip.

New tasks always reconstruct source bytes and run the unchanged fresh-process
validator plus native DRC. Each completed task has atomic completion metadata;
interruption cannot convert partial DRC output into a complete leaf. Final union
rejects missing/duplicate/unknown IDs, rechecks exact bytes and all proof hashes,
derives identity unions, and invokes the unchanged zone_batch_evidence verifier.
It does not replace complete_reports, original groups/connectivity, eligibility,
or publication-equivalence gates.

## Bounded pilot plan — do not dispatch

Two disjoint packets contain B.Cu before batches 15–22 and 23–30. At most two
workers; shared command budget 40 minutes, job budget 50 minutes; aggregate
owned RSS ceiling 12 GiB and available-memory floor 2 GiB; disjoint task output
directories; upload partial completed checkpoints on every exit. Sixteen passing
new reports would bring coverage to 251/426, never full eligibility.

The packet plan and proposed guarded host/controller workflow are committed.
They require parent source review before dispatch. Do not launch run_missing
directly as a substitute.

## Exact continuation

1. Review this source, trust anchor, native geometry-reference binding and tests.
2. Authenticate the saved artifact metadata and approve or reject producer-proof
   equivalence; full raw artifact download may be required by that review.
3. Review the proposed bounded pilot host controller using the committed packet IDs,
   unchanged KiCad image and validator kernel, before a single dispatch.
4. Retain each completed pilot task through an immutable artifact/ledger anchor;
   resume only explicit missing IDs. Obtain reviewed B.Cu-after geometry binding
   before those 103 tasks; do not use local KiCad 9 as a substitute for 10.0.6.
5. Require exactly 426 verified leaves, then all original completion/gating checks.
   Keep issue #189 open and preserve all successful routed copper.

Read-only regeneration on the saved local inputs (heavy guard required):

```bash
bash /home/agent/.codex/scripts/heavy-guard.sh -- \
  /workspace/zudo-osc-hole-field/.circuit-cache/route-venv/bin/python \
  scripts/pcbgen/freeze_core_audit_tasks.py \
  --source-zip /tmp/issue189-core236-reconciliation-inputs.zip \
  --compact /tmp/issue189-isolated-terminal-diagnostics.zip \
  --metadata /tmp/issue189-isolated-terminal-metadata.json \
  --scratch /tmp/issue189-task-source \
  --output circuit/routing/issue189/core236-task-checkpoints
```

Focused verification: `python -m unittest scripts.pcbgen.test_audit_fixture_tasks
scripts.pcbgen.test_core_audit_pilot scripts.pcbgen.test_zone_fixture_validation scripts.pcbgen.test_zone_batch_resume
scripts.pcbgen.test_zone_batch_evidence scripts.pcbgen.test_isolated_audit_recovery`
(37 tests). No fresh native validation or native DRC was run in this proposal.

## Parent-review corrections (no dispatch)

`uuid_tools.py` is now part of the native kernel binding. Task IDs and all
receipt/missing/packet lists were regenerated from the same source and raw
reports. The manifest file SHA256 is
`e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e`.
The taskrunner/controller/aggregation and workflow revision is bound separately
in `orchestration-revision.json`; the host checks it before launching workers.

Production prior loading authenticates exact artifact/run/head/digest through
`gh api` against this repository, then validates immutable bytes and receipts.
It mints an in-process verified authority binding the manifest, kernel and exact
receipt hashes. `verify_leaf` and final aggregation reject JSON provenance,
including self-consistent fabricated receipts/reports. No authority is loaded
from serialized pass flags. New checkpoint loading additionally requires a
reviewed approval-file SHA, authenticated artifact metadata, exact immutable
producer source and orchestration blobs, artifact bytes, producer image evidence,
and approved ledger hashes. Its CLI subsequently reconstructs each fixture and
checks native/report hashes and identities. The private worker byte checker is
for newly executed native tasks; it does not create reusable prior authority.

Final aggregation uses lazy fixture/report readers and retains no access-map
copy of all 426 large PCB blobs. The original verify_result interface and all
coverage/raw-report/identity checks remain unchanged.

`core_audit_pilot.py` and `core-audit-task-pilot.yml` provide the proposed guarded
host path. Two explicit packets share one 2400-second deadline; the job is
50 minutes. The host checks aggregate process-tree RSS including its own process
and both native containers, the 2 GiB available-memory floor and 12 GiB RSS
ceiling, uses two 6 GiB hard-capped containers, verifies actual Docker image IDs,
cleans only owned workers, and seals partial ledgers even on failure. The workflow
uploads completed and partial outputs with `if: always()`. It never calls
connectivity/publication/adoption gates or changes a PCB.

New output reuse approval fields are `producer_commit`, `run`, `artifact_id`,
`artifact_sha256`, canonical `manifest_sha256`, `policy`, `orchestration`, and
`ledgers` (relative ledger paths to exact file digests). Obtain artifact metadata
through authenticated GitHub and independently pin the approval-file digest;
do not accept producer.json as its own approval. `verify-checkpoints` requires
that external approval digest. Ordinary checkpoint JSON cannot mint authority.

Continuation: review this corrected source and controller, then explicitly
approve an exact commit and manifest digest for one pilot. Do not invoke
`run_missing` or the worker directly to bypass the host. No dispatch has occurred.
Future B.Cu-after bootstrap still requires a reviewed pinned-native artifact
binding exact after-board/context/zone/layer/source-zone bytes and geometry;
none of the 103 after tasks is scheduled by this pilot.

## Registered-workflow wrapper (parent review required; no dispatch)

GitHub does not register the standalone new workflow before it exists on the
default branch. Its workflow endpoint returns 404; it exists at reviewed803dcd0
but not main. No merge or default-branch edit is proposed.

The registered `.github/workflows/routing-benchmark.yml` now has an explicit
`core_audit_task_pilot` boolean, default false, plus optional reviewed commit and
manifest digest inputs. The new `core-audit-task-pilot` job requires that flag,
`board=osc-core`, and all existing routing/adoption/recovery flags false. Every
old job is additionally gated by the pilot flag being false; all six old job
bodies, original predicate logic, default behavior, global permissions and
concurrency are preserved. The pilot job copies the standalone host steps exactly
and adds job-level read-only permissions and the same dedicated concurrency lock.

The wrapper still verifies the exact parent-reviewed commit and manifest file
SHA, prepares authenticated immutable artifacts, and invokes the guarded host
controller once. Its 50-minute job, one shared 40-minute command, two workers,
exact before-batches15–22/23–30, hard6GiB container caps, aggregate12GiB/available2GiB
memory guards, owned cleanup and always-upload partial checkpoints are unchanged.
It adds no new native scope, after tasks, routing, adoption or eligibility gate.

The registered workflow is separately included in orchestration-revision.json;
new checkpoint artifact authentication accepts this exact workflow path rather
than the unregistered standalone path. Kernel bindings, task IDs, manifest digest,
235prior receipts,191missing tasks and three geometry bindings remain unchanged.

Inexpensive verification:38focused tests PASS, including a frozen803dcd0 comparison
of every original job body/predicate and exact pilot-step equality; Python compile,
YAML parse, separate orchestration revision binding and diff checks PASS. Require
parent review of this wrapper revision AND successful new exact-head CI before
any dispatch. Planned dispatch inputs are core_audit_task_pilot=true,
board=osc-core, reviewed_commit=<new reviewed exact head>, and
reviewed_manifest_sha256=e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e.
No dispatch occurred while preparing this plumbing correction.
