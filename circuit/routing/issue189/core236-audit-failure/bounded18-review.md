# Bounded native comparison — stop for parent review

The sole corrected comparison run [38067093430](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38067093430) completed successfully on PR239 head `7add2a44e5cd3ef1f28be55a9ef5af71897f8dd8`. Exact-head prerequisite CI38066067047 passed all five jobs; 37 focused local tests passed. Parent confirmed the namespace correction before this dispatch.

Both serial modes completed all 18 pinned controls under one shared 900-second command/20-minute job. The original leg executes the frozen 617/4768 inline statements; no refactored flag-off substitute was used. Eight matched F.Cu before/after pairs and B.Cu batches 0/1 preserved exact fixture bytes, artwork scope, rendered text, native geometry, context and native KiCad10.0.6. All four B.Cu DRC calls completed. Known-control batch0 raw native identities matched the saved report; both modes' batch1 raw and scoped identities matched each other. All four reports have zero errors and zero zone/silk identities. Their raw isolated_copper199 and library-footprint findings remain retained and incomplete evidence for those other warning domains.

Sampled aggregate process-tree RSS: original peak 3,601,436 KiB (3,517.0 MiB), isolated peak 2,361,044 KiB (2,305.7 MiB), 34.4% lower in this bounded sample. Minimum MemAvailable: original11,937,212 KiB; isolated13,176,652 KiB. Sample spans446.25s/417.67s; original includes the first pinned-image pull, isolated uses the cached image, so these times do not establish a controlled speedup. Both modes exited0 without a time/memory guard stop. Post-cleanup telemetry shows no owned containers and empty owned process trees. No unchanged retry or budget extension occurred.

Artifact11676280694 is226,534,869bytes, SHA256 `c695ea8f653546e443daa8aba67811441b31787684e162f2583465f2dfd11601`. Independently checked archive inputs, all36 completed receipts, geometry/context/rendering gates, saved report bindings, allfour raw/scoped reports, telemetry and cleanup. `bounded18-result.json` records exact inputs, outputs and summaries; `bounded18-comparison.json` is the unmodified terminal controller receipt.

Reproduce read-only reconciliation from repository root on the tested source (or this evidence branch):

```sh
gh api repos/Takazudo/zudo-osc-hole-field/actions/artifacts/11676280694/zip > /tmp/core236-bounded18.zip
sha256sum /tmp/core236-bounded18.zip
python3 circuit/routing/issue189/core236-audit-failure/reconcile_bounded18.py /tmp/core236-bounded18.zip
```

The checker does not invoke native tools. The native artifact retains every manifest input, original baseline, mode receipts, requests, raw reports and telemetry. Keep the ZIP local/ignored; no Git LFS.

**STOP for parent review.** This18-control result does not establish220+/206-fixture memory stability or complete warning coverage. No full warning resume, routing, adoption or merge is authorized. Core1312 candidate remains rejected/unpublished until the full mandatory audit and publication gates pass. Main remains65cefd41/JL117/JR129/core1402/nativeDRC-parity0/0; all accepted copper remains unchanged. Issue189 remains OPEN. Review this result before specifying any further bounded native recovery.
