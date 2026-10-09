# Issue 189 exact continuation checkpoint

Updated 2026-10-09 14:00 UTC. **Issue189 remains OPEN.** Zero-edge connectivity and final completion gates are unmet. No fabrication/hardware qualification is claimed. Fixed panel/electrical rules, accepted copper and other sessions are preserved.

## Current authoritative state

| Location | Commit | Accepted native edges JL/JR/core |
| --- | --- | --- |
| Main, merged PR205 | `1b8c6f8589fee431f542fb37a3c16e072865b8d3` |121/139/1441|
| Frozen draft PR206, `agent-fix/189-bounded-ground-continuation` | `ab0018bc332dfd18fb2e4a9e52da6d9128158c14` |121/137/1441|
| Native-trial source on working `agent-fix/189-ground-repair-continuation` | `29ce0d56c938198654e80e50f480be5e9e462906` |121/137/1441|

All three accepted boards have0native DRC/parity errors. JL477/JR520/core619 warning counts are unchanged by the latest accepted steps; no new warning identities or split original pad groups; fresh native connectivity agrees. Counts on a pending/rejected candidate are not accepted progress.

- PR205 exact-head37937443719 and preceding-main37937330204: all5PASS. Merged13:49:34Z; **post-main37939632920 running**. Finish this before the next merge.
- PR206 exact-head **37938871985 running**. Keep its head frozen. After both checks above pass, refresh head/reviews/mergeability, merge normally under existing authorization, retain branches and verify resulting main.
- PR204 exact-head37934945521 and post-main37937330204 all5PASS; mergeddf126be3c393c7841ac58408e620b82744a19e03.
- PR201 exact/post, PR203 exact/post all5PASS. PR202 exact passed; its post-run37932366842 was cancelled/superseded, never passed. PR203's subsequent integrated-main check passed. Evidence remains in ci-*.json and git history.

## Sole active native trials

| Board | Run | Source | Worker | Scope |
| --- | --- | --- | --- | --- |
| Core |37936741388|`cba4755227b52145a9dc9cd9e5e0f9880787ff1f`|`agent-fix/189-core-u1513-worker`|26 B.Cu signal segments,no vias/cuts; ordinary gated adoption |
| JL |37940189931|`29ce0d56c938198654e80e50f480be5e9e462906`|`agent-fix/189-jl-u2204-outer-worker`|Read-only fixed coupled proposal:8 B.Cu restoration segments/1reviewedcut,no vias,no automatic repair |
| JR |37940194109|`29ce0d56c938198654e80e50f480be5e9e462906`|`agent-fix/189-jr-u8303-ground-worker`|Read-only U8303 native cut/restoration:2 F.Cu cuts,one victim,outer-only routing,300000expansion cap |

Do not write these worker branches, duplicate same-board trials or count their pending output. The jack pilots cannot promote canonical boards. Reconcile actual terminal receipts/artifacts before selecting any next same-board action. Core alternatives must not be rebased before core26 is terminal/reconciled.

## Accepted immutable boards and retention

| Board | Published SHA256 | Latest accepted stage |
| --- | --- | --- |
|JL121|`95d10f2b21ee75831b370a97c2035e209ae296d0dfb2ec74f5bed610133d5070`|Run37934138351:124→121,all33222prior objects identical,+17segments/3vias,0cuts|
|JR137|`3f33128a85634798938b1d4b42c78d3e84e38f9818912fae02596fa8848838cd`|Run37936737740:139→137,all51017prior objects identical,+7segments/2vias,0cuts|
|Core1441|`a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932`|Run37895925149:1509→1441,all132953original objects identical,+216segments,0cuts|

JL: artifact11618501163 ZIP`7ba5dfcf88e628cef37c196d596160f37f445eb306005ef57a2758cc1b2b15eb`; replay`3e2a038f72e68a0b350583cd1d26d1c45983ab1161d17bf0dd98f191a585c628`; boteca35e63e3bbb495b734cd20f2963003a214cab5. Full physical invariants checked.

JR: artifact11618839122 ZIP`0a419810ae0c1a0edd69e9db594f8596de474c1d95a45fb525e0cb8ebb98d170`; replay`b2f991e5e46f2345a70f3c4382acfc4f6960779634a6cd434729772e74c57487`; botdd7184acfb0235e876ba57bd09669c1247ddf74b, integrated9dd9090. All3655pads,4edges,154keepouts,sixlayers unchanged. Evidence in jr-two-fine-ground/.

Core: native-filled SHA`95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5`; publication removes derived caches only, with native equivalence proved. Artifact11603564190 ZIP`a01f06e5458221d6d013c5331110e0f60c849d756cec84dfdcf835750bda4cfc`. See core-filtered/.

Current JL30384segments/2858vias,103signal+18ground edges. JR47912segments/3114vias,111signal+26ground edges. Core80+12V/80−12V/252AGND/1029signal edges. Rails on both jack boards are zero-open.

Latest additive steps retain every prior object. Earlier accepted JL/JR reroutes removed131/13reviewed objects respectively; do not claim all original jack copper survives. All original core copper survives. retention-ledger-*.json records exact cumulative multisets. Fixed .kicad_dru/.kicad_pro and placements.lock.json remain unchanged from1fe06ad5.

## Current rejected controls and prepared successors

- **Core143 run37925863664 rejected1441→1343**,0DRC/parity,619warnings,fresh agrees,all133169old objects retained,+143/0cuts. Ground groups split; one newly reported hole identity involves two unchanged preexisting vias, but the warning gate is not waived. Artifact11617518320 ZIP`d6dbd7428da9064c99581eff5e7e03dbf5684576eb0b4ff6a180695688012ab9`; candidate`bbdbbef213020a3700bd50b9e1d98201fe3b777056cc049b730cb2f4ada75968`; replay`8717c4c29145e1e860c924a0ea6d33f204edeb556e0efcbf30f1ca3b5b743fe6`. None adopted; core-short-power/ holds split attribution and retention.
- **JL U2204 run37937518106 rejected121→121**. Native cut alone joins AGND18→17 but splits U8213.3/J900027.1. In3 signal restoration split−12V and was dropped. Final candidate has0adds/1cut,0DRC/parity,479warnings(two new dangling tracks),unrestored signal. Artifact11620945674 ZIP`446c4b116bb6492b5aed0cd2df2a8dbc0a354212945d87582205accec3b69cc0`; candidate`b4101d38ea23e0cec644fe607afd2ed0aa47c7042d0fdc38fdef4b6563250de5`; replay`351ad125364cd52a1485d72231f5af29d06e38d0e7d7bf5a8f23850f777e2526`. jl-u2204-ground-cut/ preserves everything. Exact-cut outer raster probes found8Bsegments/no vias with F+B or B-only; F-only failed. The active coupled trial tests this actual cause change, with all original gates intact.
- **JR137 finer ground screen:**0/26paths at0.00625mm,guardPASS131s. Distinct cut prefilter:16ground-only paths/24cases,guardPASS65s. The active U8303 pilot selects2Fcuts/one victim,12.705×14.8mm frame; ground prefilter uses F/B and restoration is restricted to F/B.
- Older negative controls remain authoritative: D7504 repeatedly splits R7505/R7530; U2119 splits C2148; JR72's U5213 route split R5273. Isolated R8487 later accepted. Do not repeat failed configurations unchanged or just increase caps.

## Core successors held until actual reconciliation

1. Preferred **core-finer-ground-batch/**: completed168-group screen yielded25positive groups; pair-spacing selection excludes a0.025mm via conflict, leaving24groups/197objects/24vias. Full .3mm ground tracks/.6mm vias,zero cuts. NOT native accepted. Additional next48d.py screen of source groups168:216 is in progress locally; do not call a partial result complete.
2. After core26 is terminal/reconciled, invoke `.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-finer-ground-batch/rebase_proposal.py --accepted-sha256 ACTUAL_PUBLISHED_SHA256`. It permits only exact known26-object additions or no change, retains every full prior copper block including duplicate UUIDs, and fails on unexpected changes/cross-net conflicts. It has NOT been run on future output. Update selection/plan scope deliberately if adding later completed batches; then wire a dedicated native replay and all ordinary merge gates.
3. **core-supply-away-from-splits/**: original-input heuristic94targets/120segments,excluding15transactions within3mm of pads in observed smaller ground-split pieces and all four ground fanouts. Not causal proof,not rebased/submitted/accepted.
4. **core1441-no-via/**:48outer-layer cases completed,11positives/10nets/117segments/no vias,guardPASS377s. **core-short-no-via/** selects12segments/7nets,≤4segments/4mm per case,minnew/new foreign-net gap19.55674059807963mm. Original-input only; no native acceptance. Rebase only after preceding accepted core changes.

## H1/H2, benchmarks and validation

Original baseline `1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb`. Two red regressions in hypotheses-before.txt reproduce ghost drill occupancy after via removal (H1) and a soft probe through an immutable foreign pad (H2). Fixes and regressions are merged. Same saved native inputs:

|Board|Old native result/time|Fixed native result/time|Acceptance|
|---|---|---|---|
|JL|140→140 /325.5136s|140→139 /328.8692s|one accepted edge|
|JR|162→162 /327.2931s|162→162 /321.9534s|no gain|
|Core|1509→1499 /3545.3150s|1509→1499 /4729.8022s|both rejected for2AGND splits|

No speedup claim. Exact input/tool/source/output identities are in jl/jr/core-benchmark.json and benchmark-artifacts.json.

Same-input JL ground .025mm:1group/2objects/37.78s; .0125mm:4groups/22objects/51.20s. All four were subsequently native accepted across two stages. Same-code/core-input24group comparison: .025mm2groups/7objects/140.92s vs .0125mm4groups/12objects/154.17s; finer core proposals remain unaccepted.

Latest shared-router boundary fix has99affected tests passing. Its same-input native-A* control yields identical115objects at4.836299s before/4.924470s after; it does not fix the native−12V split. Blanket per-layer ground screening falsely flags three native-accepted controls and is not enabled. Native multilayer topology stays authoritative.

Current site/circuit checks pass. Real zero-edge completion gate is NOT RUN and cannot pass these nonzero counts. It requires all three canonical boards,settled/fresh connectivity,zero open edges,zero DRC/parity and unchanged context/warning identities. Full connection alone is not fabrication qualification.

## Execution notes

Use KiCad10.0.6 CI as the native oracle; localKiCad9 is not acceptance. Numerical scripts use `.circuit-cache/route-venv/bin/python`. Heavy runs use `bash "$HOME/.codex/scripts/heavy-guard.sh" -- COMMAND` with supported runtime-path escalation. Do not repull the oversized Docker image or bypass the guard.

Refresh `gh run view RUN --json status,conclusion,jobs` and remote refs before acting. For artifacts verify ZIP SHA before extraction; connector download can recover CLI failures. Workflow success alone is not adoption. Require original-group preservation,warning identities,DRC/parity,fresh agreement and exact retained-copper proof. Review bot deltas from pinned source; never overwrite a newer whole board from an old branch. Do not force-push,merge unverified heads,close189,change physical/electrical rules or resume unrelated watches. Other-session branch heads remain8315af55/30db43e0/470b3f0e and were freshly checked unchanged.
