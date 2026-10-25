# Issue 244 recovery checkpoint — parent review required

Disposition: **KEEP_K1402**. Retained semantic authentication is **355/426**;
71 exact after-stage tasks remain. Core1312 is unadopted. The complete original
artifact is still unavailable through this session's supported transports.
This is a proposed blocked disposition for the coordinator to accept, not an
architecture selection or permission to run wave2. All native/final gates below
remain NOT RUN. No routing, native audit, adoption, merge or workflow was started.

## Ownership and immutable inputs

- Assigned integration input: `1da1909846dc3255888ecd36c88cee9737c85834`, epic242-e0.
- Newer integration inspected: `6700ccb1a9a64630cd26bccf751f537f3cc25d42`.
  Changes are the reviewed trimmer lane and coordinator records/CI proposal;
  existing boards, audit implementation and hardware epoch are unchanged.
- Current main: `65cefd41fc39e064d38319115ad96016a1c6b71c`.
- Sole newly assigned recovery owner; old task01a11c9f-4ef8-717b-8aaf-a9fad47d1021
  remains stopped. Coordinator task01a12972-5482-766c-97c0-fb9a182940a4 alone owns
  integration/canonical adoption.
- Audit execution source: `b350905989de9b441aa4ff709a8491d3c753332b`.
  PR241 still targets `agent-fix/189-core236-isolated-audit-recovery`; its head
  branch `agent-fix/189-core236-task-checkpoints` is deliberately unchanged.
- Isolated evidence branch: `agent-fix/244-audit-recovery-20261011`, rooted at that
  audit source to preserve stacked ancestry. This branch contains only the owned
  `circuit/routing/epic-242/audit-recovery/` delta. Reuse PR241 by linking this
  immutable evidence commit; do not create a duplicate audit PR chain.
- This checkout's inherited JR130 is not accepted JR129. Never integrate its tree
  or board files. Only the owned evidence delta may be extracted by the coordinator.
  All 537 tracked board paths remain byte-identical to the execution source.

The complete #244/#242/#243 bodies and comments, PR236/238/239/240/241 bodies and
comments/reviews, AGENTS.md, circuit/WORKFLOW.md, source review and baseline
handoff/ownership/exchange contracts were read. Repository `.agents/skills` is
absent; relevant tracked `.claude/skills` were read. Startup instructions arrived
through the workspace AGENTS message; separate saved-start-field delivery is not
established. Runtime restoration and personal loading were rejected by automatic
approval review for runtime/home access. No workaround was used; personal context
and automatic discovery remain unverified. Repository-only recovery continued.

## Recovered evidence and limits

`recover_retained.py` invokes the original `load_approved`,
`authenticate_checkpoints`, `authenticate_binding`, `reconcile_wave`, `select_wave`
and `final_union` without patching any validator. It downloads no artifacts itself
and never starts Docker/KiCad. Full connector ZIPs were cached outside Git and
checked against fresh authenticated GitHub sizes/digests before use. The source
archive is the original inspected-input artifact11671779973, not a regeneration.

| Stage | Run | Artifact | Current result |
| --- | --- | --- | --- |
| Original candidate | 38044514132 | 11671963117 | SUCCESS metadata; full bytes blocked |
| Approved geometry bootstrap | 38098640864 | 11686834647 | Full embedded ZIP and original approval authenticated |
| After wave0 | 38101593158 | 11688551991 | SUCCESS; original semantic replay reaches339 |
| After wave1 | 38103580685 | 11689476370 | SUCCESS; original semantic replay reaches355 |
| After wave2 | none | none | Never dispatched; batches32–47 next |

The successful bootstrap full ZIP SHA256 is
`776d50d05aecd67a60cff1bd285c9a3aedf80c54517fdbde0545686d8716aba5`;
its original approval SHA256 is
`33dcc38ca02a185f9b96d980f8f92d7608cf6c8296710b5ed3afd7b88e684d00`.
Reauthentication rehashed the original nine producer blobs, matched the two
native reloads and all three controls, and reconstructed the `StageBindings`
capability. Failed bootstrap38095685843 remains excluded.

After-wave0 full ZIP SHA256:
`37c756ac69b8406436f4649d7974b1161214a8f3ac7dea356d1b201657e10515`.
Recovered wave0 approval matches the historical published hash
`66832bebab55136441c0ff0000066dbb79d34ac2879166f10819f541f5aff926`.
Recovered wave1 approval SHA256:
`cc8a2f2f800eeab7675cf343cdff5ca87e1b7aeab076d45e699c7acdc04b339e`.
After-wave1 full ZIP SHA256:
`cf54f38389c3a2b131520d8166f693539609a5c59dff55d564508359378b80cd`.
The wave1 approval is reconstructed from the authenticated artifact, not recovered from
the unavailable old local approval file. `after-resume.json` retains both exact
approval objects separately from the five original before approvals.

`recovered-artifacts.json` records all downloaded full archive identities;
`historical-runs.json` preserves actual success/failure states. The old235-task
legacy anchor continues to use its original reviewed compact-producer equivalence:
artifact11679136451 is fully byte-verified, but the 1.05GB legacy native
artifact11679236513 is **metadata-authenticated only, not locally byte-verified**.
That unchanged exception does not verify the required full original11671963117.
All subsequent pilot/five-before/two-after checkpoint archives are fully hashed
and semantically replayed using the original producer/source policy.

Exact immutable board hashes:

- Before: `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66`.
- Candidate: `f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1`.
- Geometry evidence: `25b5da073cf2e1380dd941a90a2e30362828cc2a451518988c372daf494119d8`.
- Original orchestration: `6f35dc2de1fce44f9227294ecb714009c0e07826add0c565fcea03f6258c55d5`.
- 103-task plan: `02c2bdd83b35da54f23093956ccf9658001ce4d2ecae132585838bad871db9ce`.

`recovery-proof.json` contains all355 completed IDs, all71 missing IDs, exact
context/kernel hashes and both proposed wave2 packets. Final union correctly
rejects incomplete coverage. Full warnings, original final eligibility,
publication equivalence and current-integration adoption remain **NOT RUN**.
Native task coverage is not board connectivity or instrument qualification.

Unavailable local-only material: old stopped-handoff ZIP, detached11-blob bundle,
owner-sequence blob3dda9748a834beaca1de834ce5ba9c5d93aaa39f without a published
tree/ref, `/tmp/issue189-after-owner-sequence.json`, wave0 proof/admission files,
wave1 admission and its run file, and the UNRUN final replay helper. None was
assumed available or used as proof. Durable source/artifacts reconstructed the
retained authentication above; no claimed recovery of those exact local bytes.

## Exact transport blocker and bounded proposal

Fresh `gh` repository/API reads succeed. Original artifact metadata says
unexpired,713393322 bytes,SHA256
`d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5`,
source4768f2f82e8a4d634f8dc2905429616bfcd20c37,run38044514132.
The normal authenticated ZIP read and its supported escalation each failed with
`Forbidden` at the blob redirect. Fresh connector attempt returned
`Artifact exceeds max size of 536870912 bytes: 713393322 bytes`.
These are observations, not a diagnosis of credentials or a general auth failure.
No unchanged retry, proxy/tunnel workaround or new credentials are proposed.
The existing102MB subset is insufficient.

Parent review proposal: **one nonnative supported runner job**, no matrix,
20-minute job maximum, one15-minute command,1GiB process address-space limit,
at least3GiB free disk and2GiB available memory before starting. Use only the
runner's existing read-only `contents`/`actions` authorization. No dispatch chaining.
The coordinator must supply/review a callable runner entrypoint; none is installed
by this evidence-only change, and no workflow source is modified. Do not modify
the pinned audit workflows or substitute a transport producer for a native one.

Exact command, from the reviewed evidence checkout on that runner:

```bash
ulimit -v 1048576
timeout --signal=INT --kill-after=30s 15m \
  python3 circuit/routing/epic-242/audit-recovery/transport_original.py \
  fetch-split "$RUNNER_TEMP/original-11671963117"
```

The script checks original run/source/availability metadata, downloads the complete
original ZIP through `gh api` with a600-second limit, and verifies its entire
size/hash **before splitting**. It produces five134217728-byte chunks and one
42350682-byte chunk. Upload each chunk as a separate retained Actions artifact
using the existing pinned upload action
`actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`, compression0,
retention30days; separately upload manifest/original metadata/run JSON. Do not
upload the713MB ZIP as a single connector-bound wrapper. Retain wrapper IDs and
digests; they are transport receipts only. Download and authenticate every new
wrapper, extract its one expected chunk into a fresh directory, then run:

```bash
python3 circuit/routing/epic-242/audit-recovery/transport_original.py \
  join /path/to/verified-chunks /path/to/new/original-11671963117.zip
```

The join rejects altered identities, missing/reordered/changed chunks, paths and
byte ranges; verifies the whole size/hash again; and never overwrites existing
work. Only that whole verified ZIP may enter the unchanged original final verifier.
This plan is **NOT RUN** and needs parent review/runner admission first.

## Held next native command

Only after parent reserves both global slots, reviews the exact command and
reauthenticates this checkpoint: same source, next wave2, two8-task packets,
batches32–39/40–47, expected371/426. Keep sixGiB/worker,twelveGiB aggregate RSS,
twoGiB available-memory floor,40-minute shared controller/50-minute job. Parent
must exclude other native jobs; workflow concurrency alone is insufficient.

`exact-source-admissions.json` is a paginated branch-independent lookup and shows
only wave0/1 at the reviewed source. Recheck before admission; the controller's
branch-local latest100 query alone cannot establish exclusive history. Ref must
still point to b350905989...; source CI38100142200's five jobs remain successful.
No branch rewind, new ref to hide history, or replay of wave0/1 is allowed.

From this evidence checkout, after those gates only:

```bash
gh workflow run 378789207 --repo Takazudo/zudo-osc-hole-field \
  --ref agent-fix/189-core236-task-checkpoints \
  -f board=osc-core -f core_audit_task_pilot=true \
  -f core_audit_task_mode=after-wave -f core_audit_wave=2 \
  -f core_audit_resume="$(cat circuit/routing/issue189/core236-task-checkpoints/owner-waves-a56f204/all-five-wave-resume-approvals.json)" \
  -f core_audit_after_resume="$(cat circuit/routing/epic-242/audit-recovery/after-resume.json)" \
  -f reviewed_commit=b350905989de9b441aa4ff709a8491d3c753332b \
  -f reviewed_manifest_sha256=e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e
```

Do not use the dedicated pilot workflow as a substitute: checkpoint authentication
requires producer workflow `.github/workflows/routing-benchmark.yml`. Stop after
the one admitted wave and reconcile its full artifact before any further request.

## Checks and remaining disposition

- Pre/post `pnpm circuit:check`: PASS, manual inventory68 lines,0 declared placements;
  no schematic/placement binding; pin-asset check performed. Initial store setup
  sandbox failure was resolved by scoped escalation; it is not a circuit failure.
- Retained replay: PASS323→339→355; original final union REJECTED_INCOMPLETE.
  No fresh native invocation. Observed process VmHWM2286464KiB before completion;
  this is an observed lower bound, not a measured final peak. Elapsed243seconds
  was sampled before completion; exact total time was not instrumented.
- Transport tests:10 PASS (byte corruption, order/ranges, incomplete originals,
  identity substitution, full-hash rejection and preservation of existing partials).
- Original audit unit tests:34 PASS (after, pilot, waves and geometry suites).
- Python compilation and `git diff --check`: PASS.
- Initial aggregate regeneration: NOT RUN pending parent native admission; the
  real script invokes native checks. Routed inputs were preserved/hashed first.
  No generated drift was produced, adopted or silently restored. The parent can
  review a separate preserved disposable-checkout regeneration command.
- Current-evidence-head CI: NOT RUN/DEFERRED. Push uses `[skip ci]` because default
  PR CI can start four native workers, above the epic cap. Historical source CI
  success is separate from current evidence checks and native acceptance.

The coordinator may formally accept this blocked **KEEP_K1402** disposition so
architecture comparison can proceed on unchanged accepted K. It does not close
#244/#189/#214 or adopt core1312. Exact missing proof:71 native after tasks, full
original713393322-byte archive and all unchanged final warning/eligibility/
publication/integration gates. Fixed panel, circuits, full harness identities and
accepted JL117/JR129/K1402 copper remain the canonical comparison input.
