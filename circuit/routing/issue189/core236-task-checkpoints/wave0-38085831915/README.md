# Authenticated wave 0:267/426; sequence stopped

Reviewed execution source f67bef8211b40e43e93a8e16004ac1d77079f12f.
Exact-head CI38084423588 passed all5jobs before one admission.
Registered workflow run38085831915 SUCCESS; all6otherjobs SKIPPED.
Two eight-task packets B.Cu-before31–38 and39–46 completed.
Controller1143s(19m03),job1211s(20m11), within40min/50min.
No wave1, bootstrap, after tasks, retry, routing, adoption or merge was admitted.

Artifact11682309044,73881190bytes,
SHA256fdaf3588096971f2100f2911e4c54e0667eb70388e7b513743161f6330ab59a4;
fully downloaded through the GitHub artifact connector and locally byte-verified.
Approval SHA2567283f40ef77d149a334642fa4b98c079f52f1f8dcb4ecc05a138d0b96bef9974.
Authenticates exact producer/workflow/run/head, manifest/kernel/orchestration,
actual pinned image, ledger/receipt/file hashes, geometry, native10.0.6,
source/context, target warnings and all-severity native reports.
All16rawnativeerrors0. Peak aggregateRSS5261008KiB(5.02GiB),
minimumavailable10450108KiB(9.97GiB); cleanup errors[],containers[],process tree{}.
Raw warning counts are fixture diagnostics, not complete-warning equivalence.

Saved-input baseline reconstruction plus all16leaf validations PASS under
heavy-guard178s; no fresh native DRC or validator execution locally.
Coverage Fbefore110,Fafter110,Bbefore47,Bafter0 =267/426;
159missing =56before47–102 +103after0–102. Exact159IDs in missing-task-ids.json.
Full union rejects incomplete coverage as required; other final gates unrun.
Original426manifest, nativekernel,3geometry bindings and old53approval unchanged.
All PCB/copper unchanged; no new routing/connectivity result.

## Why stopped

The reviewed sequence stopped at its terminal artifact download: gh's GitHub
artifact redirect returned HTTP403, although the native workflow succeeded.
Its stopped-sequence.json is preserved verbatim, including the admission marker.
No additional POST occurred. Connector retrieval and read-only reconciliation
subsequently recovered the complete authenticated wave0 evidence. This is not
an automatic dispatch retry or authorization to continue. Root cause of403 has
not been established; an expired URL was initially suspected but not proven.
The failed heavy-guard verdict belongs to artifact transport, not native tests;
the later178s proof reconstruction verdict is PASS.

## Exact continuation checkpoint

STOP FOR PARENT REVIEW of this failure/recovered evidence and transport/resume
implementation. Do not rerun core_audit_sequence.py: it has no resume mode and
must reject this existing exact-source admission. Never replay before31–46.
resume-approvals.json contains the authenticated wave0 approval reference.
An explicitly reviewed continuation must reconstruct all267prior leaves,
select wave1 at47–54/55–62, then continue wave2(63–78),wave3(79–94),wave4(95–102),
authenticating terminal artifacts before each next POST. Preserve the identical
plan/native kernel/426manifest, max2workers,40mincommand/50minjob and guard/cleanup
stops. Require all5CIgreen for the exact continuation source. Fix artifact transport
without relaxing authentication or replay protection. Once323/426 is reached,
run the independently approved read-only bootstrap under the same global max2,
authenticate its receipt, then stop for after-stage review. No103aftertasks yet.

The raw archive is local /tmp/issue189-wave0-38085831915.zip; extracted native
fixtures /tmp/issue189-wave0-authenticated; prepared original inputs
/tmp/issue189-f67bef8-wave-input-cached. These are ignored, never Git LFS.
On a fresh environment retrieve artifact11682309044 via the GitHub connector,
verify its digest above, prepare authenticated baseline archives/source/context,
and run this read-only reconciliation with NEW disjoint paths:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- python3 \
  circuit/routing/issue189/core236-task-checkpoints/wave0-38085831915/reconcile.py \
  /tmp/issue189-wave0-proof-fresh-input \
  circuit/routing/issue189/core236-task-checkpoints/wave0-38085831915/artifact-metadata.json \
  /tmp/issue189-wave0-38085831915.zip \
  /tmp/issue189-wave0-proof-fresh-extract \
  /tmp/issue189-wave0-proof-fresh.json \
  /tmp/issue189-f67bef8-wave-input-cached
```

Use the reviewed source files and the project Python environment. The script
rehashes current orchestration and native policy, authenticates immutable remote
metadata, reconstructs235legacy+16oldpilot leaves, and rechecks all16new leaves.
It does not dispatch, reroute or run native DRC. Source/context reconstruction and
final proof data are explicit; no assertion of eligibility is accepted.
