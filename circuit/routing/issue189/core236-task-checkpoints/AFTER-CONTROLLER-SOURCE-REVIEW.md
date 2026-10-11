# After-stage implementation; stop before dispatch

This implements the independently approved narrow controller path at checkpoint
`502383805cc03e7dd8fec204c4664021041351e7`. It does not dispatch any audit,
route copper, refill or save source boards, adopt a candidate, or run final
eligibility/publication/integration gates. Issue #189 stays open; PR #241 is draft.

The original three-binding file and all 426 manifest task IDs are unchanged.
The proposed 103-task plan is also byte-identical, SHA256
`02c2bdd83b35da54f23093956ccf9658001ce4d2ecae132585838bad871db9ce`.
The controller implements its thirteen exact packets and seven waves, with
323→339→355→371→387→403→419→426 coverage. Before approvals and after approvals
have separate inputs, checkpoint filenames and wave numbering.

## Authentication path

`core_audit_after.StageBindings` is an in-process capability derived from the
full successful bootstrap ZIP, never a fourth signature loaded from JSON.
The sole compatible historical bootstrap is source
`d75c4a949e37ac545c7e5cebbd95c516faff8352`, run **38098640864**, artifact
**11686834647**, full ZIP SHA256
`776d50d05aecd67a60cff1bd285c9a3aedf80c54517fdbde0545686d8716aba5`,
approval SHA256
`33dcc38ca02a185f9b96d980f8f92d7608cf6c8296710b5ed3afd7b88e684d00`.
Its original nine orchestration blobs are rehashed from the original Git source
and must equal original orchestration
`abd9d8b7335ba9c2cb40873570ce7e7f53af601c3866213d46ce720ec1f21926`.
Failed bootstrap 38095685843 is excluded. Other producers retain strict current
orchestration equality; existing pilot/five-wave exceptions remain narrowly pinned.

1. **Host:** authenticate fresh artifact/run/head/digest metadata and terminal
   success, entire ZIP bytes, approval, producer/image/kernel, empty bootstrap
   task inventory, exact prior 323 IDs, native receipt and both matching reloads.
   Require all three old controls and exact board/context/reference identities.
2. **Worker:** read the ZIP from read-only `/inputs` and the exact approval from
   read-only `/plan`; rehash and extract into a new per-worker proof directory.
   The networkless path accepts only the exact compiled reviewed bootstrap tuple,
   approval and original producer blobs. It revalidates the receipt, reloads and
   controls. Generic task checkpoints still require fresh GitHub authentication.
   Require an exact proposed after packet, rebuild the immutable source manifest,
   and compare the actual native source geometry before fixture DRC.
3. **Leaf:** preserve original byte-level fixture/context/native/raw-report and
   warning-cap checks. Add `stage_geometry_sha256`, the identity of the full
   authenticated geometry fact, to the completed receipt before its ledger hash.
4. **Resume:** each after artifact includes the complete bootstrap ZIP and
   original approval. Freshly authenticate that artifact and its embedded
   bootstrap before sealing producer authority for its leaves. Match the fact
   and binding identity in producer and every leaf; reject wrong-stage leaves.
   Reconcile exact prior/requested IDs and mode/wave before the next admission.
5. **Aggregate:** the new read-only `aggregate` command authenticates the five
   before and seven after approvals, reconstructs the capability, reconciles each
   wave and invokes the original `final_union`/full paired-zone verifier. It
   propagates the same fact and identity into the aggregate checkpoint. Plain
   four-signature JSON, missing coverage or altered leaf/provenance cannot pass.

Max two global workers, 40-minute shared controller/50-minute job, 6 GiB per
worker, 12 GiB aggregate RSS and 2 GiB available-memory floor remain unchanged.
Both workflow paths retain the same global concurrency group and always-upload
partial outputs. Stop on failure, native errors, report cap, partial proof,
replay, wrong stage, altered provenance, guard or cleanup failure. No automatic
retry or budget increase is implemented.

## Proposed first wave — only after independent source/CI approval

Set `REVIEWED_AFTER_SHA` to the exact independently approved implementation head;
the PR handoff pins that head and its exact-head CI run. Recheck remote branch,
all five successful CI jobs, current admissions and the complete 323-leaf input
proof before one exclusive admission. Do not use the old sequential dispatcher.

```bash
gh workflow run 378789207 \
  --repo Takazudo/zudo-osc-hole-field \
  --ref agent-fix/189-core236-task-checkpoints \
  -f board=osc-core \
  -f core_audit_task_pilot=true \
  -f core_audit_task_mode=after-wave \
  -f core_audit_wave=0 \
  -f core_audit_resume="$(cat circuit/routing/issue189/core236-task-checkpoints/owner-waves-a56f204/all-five-wave-resume-approvals.json)" \
  -f core_audit_after_resume='[]' \
  -f reviewed_commit="$REVIEWED_AFTER_SHA" \
  -f reviewed_manifest_sha256=e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e
```

This selects B.Cu after batches **0–7 and 8–15**, exactly sixteen new tasks;
expected coverage is **339/426**. Authenticate the full terminal artifact,
construct an immutable approval and run `authenticate_checkpoints` followed by
`core_audit_after.reconcile_wave` with authenticated prior leaves before another
admission. Store after approvals separately and pass only successfully
reconciled preceding after waves through `core_audit_after_resume`.

After seven successful waves, prepare new disjoint inputs using `prepare --mode
after-wave --resume-json <five-before-approvals> --after-resume-json
<seven-after-approvals>`, then run `aggregate` with those same separate inputs.
The aggregate result explicitly says the original final gates have not run:
complete reports, full warnings, groups, connectivity, eligibility, publication
and integration remain required. 426 reports alone do not authorize adoption
or establish complete connectivity or hardware qualification.
