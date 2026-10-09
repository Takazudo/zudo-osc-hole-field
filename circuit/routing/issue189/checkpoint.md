# Issue 189 exact continuation checkpoint

Updated 2026-10-09 19:49 UTC. **Issue #189 remains OPEN.** Main `835f4036c82aed4333f6323cf8571f085d1d767d` accepts **JL118 / JR134 / core1441**. PR211 merged exact head57aa5247c5cdd8bfb559ae65a9bd202c2d0d7f90 after all five checks37980437155 passed. Post-merge37982818544 is active. Current follow-up branch is `agent-fix/189-ground-scope-continuation`, containing read-only movement comparisons and an audit timeout that retains upload time. Zero-edge completion, final regeneration/P/EL/O and renders remain unmet. No fabrication or hardware qualification is claimed.

## Active work and hard gates

- **JL adoption37978945582 completed and independently verified**, isolated branch `agent-fix/189-jl-r8276-adopt-worker`, source `8b0a7701a680a9df7fd3272c4749365a5911ad74`. Bot534dd3e60985799502420dd326fe41bca9e15875 cherry-picked asd50853d3d56984c204c45ae5918dfa87d8956fee after exact3file blobs matched the SHA-verified artifact. Temporary worker-only workflow is excluded. No jack writer is active.
- **Core zone classification37976003780** is read-only and still active, source `bacd089f36a12d839a96cb6888640918cefe1e35`, worker `agent-fix/189-complete-silk-worker`. It must finish and its full raw evidence must validate before the saved core1402 candidate is eligible. **No core writer is active.** Do not infer eligibility from the earlier provisional reassessment.
- Core19run37965185751 is terminal and rejected, fully reconciled below. It is safe to prepare a successor after completing the warning evidence; never reuse source-bound audits on a changed candidate.
- CLI API authentication expired at19:08 and recovered after host runtime refresh at19:25; a harmless repository API read succeeded. Git/connector access remained functional. Same container and snapshot verified; bridge already valid; loader not repeated. Regular workflow dispatch is available again. The temporary JL worker push trigger retained identical gates and is not part of PR211.

Parent steering at18:34UTC explicitly authorizes incremental merges once exact gates pass and requires core19reconciliation before a ground writer. Preserve other sessions and all branches. No unrelated watches. Previously checked other-session heads: `core-rrr-escalate`8315af554132b283e4e6e9b62d76bbfdcea560c0, `jack-replace-region-2`30db43e0c63cc4e380fd1525e74e76d27d8b0694, `jack-replace-jl-1`470b3f0e074b7f1254b529c58932e57ed456d195. Refresh them before any adoption/merge.

## Merges and validation

PR211 merged as835f4036c82aed4333f6323cf8571f085d1d767d at19:49UTC after all five exact-head checks37980437155 passed (`ci-57aa524.json`), with clean state and no comments/reviews. Other-session refs were unchanged immediately before merge. Post-merge37982818544 is active; do not claim it passed yet.

PR209 merged head2c3afdedf9e999ef0b091db74805d10fc5687d44 as98820acfefa293f7c2558aacb2059d3de8da5ae8 after all five exact-head checks37972341588 passed. It adopted JR134. Its post-merge run37975245292 was cancelled/superseded, **not passed**.

PR210 merged heada95f936cca551742267e36dde9276a8b813739f1 as2ca29f2550366d5b31f6eb2ce9dbdbfd9a6b27c2 after all five exact-head checks37974947048 passed. It changed verification, not canonical boards. Post-merge37977274128: all five checks passed, including native regeneration (`ci-main-2ca29f2.json`). Exact-head receipts are `ci-2c3afde.json` and `ci-a95f936.json`. Earlier main4db1d3c all-five post-check proof is `ci-main-4db1d3c.json`.

## Accepted immutable boards

| Board | Published SHA256 | Latest accepted evidence |
| --- | --- | --- |
| JL118 main | `a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a` | 37978945582:119→118,+75segments/2reviewed cuts,all33346uncut objects identical |
| JL119 historical | `554fa85a44d74c2ad2105e34f1bbc4de9b674e46dd7531ddc3e00c6d8e1c1291` | 37960073108:120→119,+58segments/4reviewed cuts,all33290uncut objects identical |
| JR134 | `35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445` | 37967123290:135→134,+37segments/5reviewed cuts,all51140uncut objects identical |
| Core1441 | `a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932` | 37895925149:1509→1441,+216segments/zero cuts,all132953original objects identical |

All three have0native DRC/parity, no new reported warning identities, no original pad-group splits and fresh agreement. Reported warnings477/520/619. Native10.0.6 is pinned by `scripts/kicad/run.sh`; local9.0.2 is not acceptance. Fixed panel/placements/pads/outline/rule areas/layers and project/rules remain unchanged. Jack rails are fully joined. JL103signal+15AGND; JR111signal+23AGND; core80+12V/80−12V/252AGND/1029signal edges.

JR134bot a59ef3669cdac3d6ca31131722c082aefd92b507, cherry133f2f6; replay3c3495b6442d463366c39ccdee4c010f9ca3c030cb321cda4d1780c4a6971c61; artifact11633969149,ZIPafa07c7a1c2315162bcc62fa780a0e6e805f0082c4f59e5739ec000a097b8b5a. Proof `jr-c7413-endpoints/`.

`retention-ledger-d50853d.json` uses full-object multisets including legacy duplicates. From issue baseline: JL32607original retained/138reviewed changed or removed/814new; JR50287original retained/24reviewed changed or removed/890new; all132953original core retained/216new. Latest stages preserve every uncut object. Do not claim all original jack copper survives.

## JL118 native adoption verified and integrated

Pilot37976521780 atd1dd53fea72278434ae40e6ef4c4d02ac2c54afd:119→118,+75segments/zero vias/2reviewed cuts,all33346uncut full objects identical,33348→33421. Native0DRC/0parity,477unchanged warnings,no original splits,fresh agreement,physical/context invariance. Candidate `a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a`; replay `b1678187a5365202fe12a97e80ff4f33bc264a0616b8269af0ffa84aaa253f67`. Artifact11639497498,ZIP0d643e9bfa906f9f45f2daa8ec87835a64ca2ec8c05bbc9ad2d3071fb5fd12b6.

`jl-r8276-joint/` contains proposal, native pilot, full retention proof, exact source/UUID preparation and adoption plan. First reserve the permanent AGND join, then restore both actual native cut victim groups within the same14.9×16.45mm frame, F/In2/B at0.0125mm/300k. The earlier cut-and-restore pilot37973959441 was119→119 and rejected; the changed joint method is material. Adoption37978945582 reproduced both hashes and all native gates. Artifact11641021167,ZIP83335f6ba6e189458a6d5b66caa5ba0f96590a7838dabaf92f6d5b7f70f56610. `reconcile_adoption.py` passed under the guard in8s: all start/merge/fresh DRC/parity0,warnings477,exact physical/context invariance and full copper retention. Published candidatea01df89d is now on main viaPR211/835f403. Post-merge CI remains pending.

## Core19 rejected and reconciled

Run37965185751 at08aec29e83d24d291f4d41a7bb10300e072a7260:1441→1432 rejected. All133169old full objects unchanged,+19outer segments/11nets/zero cuts or vias.0DRC/0parity,619unchanged warnings,fresh agreement. Original1928-padAGND group splits into1/1/2/1924: J900311.2, C4445.2, and U4606.5/C4623.2 isolated. AGND252→255. No board adopted.

Candidate40ace01e555e637a1faa369990fecc715ba8ee9b49dd5d717fddef004ddf8233, replayda1d5262b945e51aa45eb500e1296efd2324d515b164132c4da9e36cec67cf49. Artifact11638511202,ZIP60524fca152e069c17d8880e0a740df9b6a082273f7a879a88764d17f509e414. `core-short-no-via/{reconcile.py,retention,artifact}.json`. Bot9ac2677 contains exactly two receipt files, both whole blobs matched verified artifact; receipt-only cherry7028f17. Do not retry unchanged. `core-short-no-via/split-proximity.json` measures nearest new copper4.95–7.22mm from the four split pads: a3mm exclusion would miss them. `core-short-split-filter/` holds8whole cases/13segments after excluding the three closest transactions; this is a hypothesis only, not causal attribution or native acceptance, and must rebase after the current ground work.

## Complete core warning evidence: provisional, NOT eligible yet

Saved run37950004600:1441→1402,AGND252→213,+344segments/38vias/zero cuts,all133169prior objects retained.0DRC/parity,no original group splits,fresh agreement. Raw gate rejects a newly reported pair of unchanged old vias because native warning domains cap at199. Candidate `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66`, replay25a3de5583c9bb61611a4e46d9463a581a09cba43c1dc23bf2d45c5203a3b08c. Artifact11631867897,ZIP8919c769bba2f17fc3d695a80590f6e75e618d8767f464baf2d39fb027ca90d6. Baseline native-filled hash95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5. Canonicalcore stays1441.

Exact10.0.6 source proves hole and both silk domains cap at199, and native silk checks include tracks and outer filled zones. `native-hole-audit/silk-scope-sources.json` pins URLs/hashes. Complete scope requires all of the following:

1. **Hole audit37972238437 PASS**,source2c3afde:9815/9853holes,128fixtures each,1407identical UUID and geometry-object identities,zero new/removed. All256raw reports and exact project/rules independently verified. Artifact11637606039,ZIP48c8b07dea13eeb4f2e257908e2ee49a80e460e6582e011a5d57cf8047d3e8db. `context-*.json` authoritative. Earlier37967430188 is invalid-context diagnostic, not acceptance.
2. **All382added-copper audit37975999346 PASS**,sourcebacd089:344segments/38vias,zero new silk_overlap/silk_over_copper identities;maximum80/0reports below199. All382raw report hashes/contexts verified. Artifact11639436792,ZIP9a3cd7c803a956cc5d5d82c426543f3f9717b6b4994dac0620dd3e2b6c7ef5f0. `all-copper-silk-{result,artifact}.json`. Earlier38via audit is partial and cannot establish complete scope.
3. **Zone classification37976003780 PENDING**. Growth-only37975143005 proves F.Cu grows25.535mm²/four regions and B.Cu23.415mm²/six regions. Metadata/outline unchanged; shapes are not subsets. Artifact11637879760,ZIPf676bb4b70145249e9f948df1410bc4749fbb20cc5c53aa6d44b752166b804a4. Current paired fixtures retain complete native zone shape and exact context, select conservative native bounding-box artwork near growth, and compare uncapped native identities.

`complete_native_warnings.py` fails closed on missing/stale/incomplete evidence, changed context, new native warnings, unsupported domains, missing copper or zone scope. It only appends complete hole observations and removes no original finding. Ordinary DRC/parity/membership/fresh/source-publication gates remain. Opt-in `route_shards.py merge --complete-native-warnings` regenerates all audits on actual sources. No core adoption using this option has run.

`reassessment-before-zone-scope.json` is explicitly provisional. Current `reassessment.json` records the zone-scope block. Updated `reassess.py` expects both full382copper and zone classification evidence; do not run it against old partial evidence. 25focused audit/workflow tests and100affected router tests pass; `pnpm circuit:check` and `pnpm check` pass. A new serializer regression also passes. The exact saved-input fixture benchmark produces byte-identical outputs: two fixtures per source take11.106→7.125s and10.776→6.770s; no native acceptance is inferred from serialization timing. See `zone-fixture-benchmark/`.

## JR rejected successor and changed-method controls

Run37974220440 atb3ba58e8e4c1363efe08e55324cecd68455c9625:134→133 rejected,+22segments/2cuts,all51175uncut full objects identical,0DRC/parity,522unchanged warnings,fresh agreement. AGND joins improve but original X67A5B6E02FA33495DE9E splits: R7628.1/R7627.2, native groups4/58. Candidate d8765ecc82f188e7302ea4525b2aa446ac4aa68e4cf92b06e0577f837d02ab0b; replaye1e3011e587df334a6a44782311f526b70a08bb3d931c2ca14add11ffe257d57. Artifact11638981471,ZIPed1c64bb976d116756344c672d7743e8df811236f7df235b04bb24d488ce9f4b. `jr134-rb4614-2-ground-cut/` full proof.

Explicit endpoint routing at0.025and0.0125 finds no path; joint permanent-ground-first restoration at0.0125fails both declared victim orders. `jr-rb4614-endpoints/`, `jr-rb4614-joint/` preserve negatives. The additional `jr-rb4614-plane-joint/` control restores signals first then attempts explicit In1 AGND fanout; both declared orders still fail X67A5B6E02FA33495DE9E (guardPASS12s). No partial proposal submitted or unchanged-budget retry. JL C8142 joint/fanout and R8127/R8276 bounded source-defined move comparisons also preserve negative controls; no actual placement moved.

## JL118 source-defined movement controls

`jl118-r8127-placement-screen/` expands physical translations to±2mm at0.1mm steps:1,680cases, only the same seven feasible moves as the older±0.8mm screen; no unchanged route rerun. `jl118-movable-ground/` screens seven other source-defined movable resistors outside bypass clusters,1,680translations each, unchanged orientation/side, fixed outline,0.35mm source courtyards,0.25mm copper and full0.2mm signal landing bridge. R8105/R8173havezero static candidates; R8273/RB2214/RB2315/R8270/R8107have1/4/8/10/86. All228direct/plane-fanout comparisons including unmoved controls fail (guardPASS697s). A changed-target R8107→actual isolated R8105group comparison also fails all87cases (guardPASS280s). Diagnostics are exhausted searches/no legal via sites, not expansion-limit failures. No footprint moved, no copper changed, no native moved-board acceptance claimed. Preserve results and do not repeat unchanged scopes or raise the budget.

Future standalone zone-audit steps now have an80minute command timeout inside the90minute job, leaving time to upload incomplete evidence. This does not alter the active old run or classify incomplete evidence as passed.

## H1/H2 and identical-input benchmarks

Baseline1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb. `hypotheses-before.txt` reproduces ghost drill occupancy after via removal(H1) and soft traversal through an immutable foreign pad(H2). Fixes/regressions are merged. Paired saved native inputs:

|Board|Old result/wall time|Fixed result/wall time|Acceptance|
|---|---|---|---|
|JL|140→140/325.5136s|140→139/328.8692s|one accepted edge|
|JR|162→162/327.2931s|162→162/321.9534s|no gain|
|Core|1509→1499/3545.3150s|1509→1499/4729.8022s|both rejected for2AGND splits|

No speedup claim. Immutable inputs/toolchain/source/results: `jl-benchmark.json`, `jr-benchmark.json`, `core-benchmark.json`, `benchmark-artifacts.json`. Later bounded raster optimization is separately tested; it does not imply whole-router speedup or native acceptance.

## Exact continuation

1. Refresh main, PR211 and other-session refs. Query active zone run37976003780 and post-merge37982818544 and the current follow-up PR CI. JL adoption37978945582 and post-main37977274128 are completed/pass and independently reconciled. CLI API authentication works again. Never restart unrelated watches or duplicate a writer.
2. JL adoption is already integrated asd50853d; do not replay/cherry-pick twice. PR211 is already merged; verify post-merge37982818544 rather than replaying it. Keep worker-only workflow out and verify post-merge main.
3. For terminal zone classification: download SHA-verified artifact, retain raw DRC/project/rules and `result.json` at `.circuit-cache/issue189-downloaded/native-zone-classification/`. Run `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/native-hole-audit/reassess.py`. Full382copper data is at `native-all-copper-silk`, holes at `native-hole-context`, candidate at `core-finer-ground-batch/.circuit-cache`, under the same download root. Any new zone warning rejects; preserve exact identities and change the proposal, never waive them.
4. Only after complete evidence passes and fresh main still has actual corea0e3cff1: run guarded `core-finer-ground-batch/rebase_proposal.py --accepted-sha256 a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932`. Check whole old copper and new geometry. Push isolated worker and run ordinary merge with `--complete-native-warnings`; regenerate native evidence against actual candidate. CLI dispatch choice is `finer-ground-complete-warnings` if auth returns; otherwise use equivalent exact-branch push trigger as for JL, worker-only. Native ground adoption remains NOT RUN.
5. Keep the follow-up PR draft until all exact-head gates and review complete. After an authorized merge, verify main and post-merge checks; distinguish cancelled from passed. Preserve issue189OPEN until all3boards are zero edges with required settled/fresh repeats, final regeneration/P/EL/O/docs/renders.
6. Continue remaining JL/JR signals/grounds and core supplies/signals through bounded native checks. `core-supply-away-from-splits/` is only prepared:94wholecases/120segments,zero cuts/vias; conditional ground conflict removes one whole U4439.4 case only if ground is actually adopted. No native acceptance claimed. After two negligible comparable trials change cause/method, not just budget.
