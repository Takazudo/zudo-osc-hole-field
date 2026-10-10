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
provenance and ledger hashes before reuse. The Python API assumes its caller
provides that trusted anchor; arbitrary caller-provided provenance is not an
approved trust root. Parent must review this boundary before any native skip.

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

The packet plan is committed as data. A host controller enforcing pinned image,
aggregate guards, timeout/cleanup and always-upload behavior is still required
and must be reviewed before dispatch. There is no workflow dispatch entry point
in this proposal. Do not launch run_missing directly as a substitute.

## Exact continuation

1. Review this source, trust anchor, native geometry-reference binding and tests.
2. Authenticate the saved artifact metadata and approve or reject producer-proof
   equivalence; full raw artifact download may be required by that review.
3. Build/review bounded pilot host controller using the committed packet IDs,
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
scripts.pcbgen.test_zone_fixture_validation scripts.pcbgen.test_zone_batch_resume
scripts.pcbgen.test_zone_batch_evidence scripts.pcbgen.test_isolated_audit_recovery`
(27 tests). No fresh native validation or native DRC was run in this proposal.
