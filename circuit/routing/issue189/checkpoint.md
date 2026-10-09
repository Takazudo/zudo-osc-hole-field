# Issue 189 exact continuation checkpoint

Updated 2026-10-09 14:53 UTC. **Issue189 remains OPEN.** Zero-edge connectivity and final completion gates are unmet. No fabrication/hardware qualification is claimed. Fixed panel/electrical rules, accepted copper and other sessions are preserved.

## Current authoritative state

| Location | Commit | Accepted native edges JL/JR/core |
| --- | --- | --- |
| Main, merged PR206 | `9376342b5767a8107ffeda4f8290b122fd1ce268` |121/137/1441|
| Merged PR206 source, `agent-fix/189-bounded-ground-continuation` | `ab0018bc332dfd18fb2e4a9e52da6d9128158c14` |121/137/1441|
| Native-trial source on working `agent-fix/189-ground-repair-continuation` | `0b38d659151730dad5fd65500fe9319dbb92df8c` |121/137/1441|

All three accepted boards have0native DRC/parity errors. JL477/JR520/core619 warning counts are unchanged by the latest accepted steps; no new warning identities or split original pad groups; fresh native connectivity agrees. Counts on a pending/rejected candidate are not accepted progress.

- PR205 exact-head37937443719 and preceding-main37937330204: all5PASS. Merged13:49:34Z; post-main37939632920 all5PASS.
- PR206 exact-head37938871985 all5PASS. Merged14:03:16Z as9376342b5767a8107ffeda4f8290b122fd1ce268; post-main37941329856 all5PASS (saved ci-main-9376342.json).
- PR204 exact-head37934945521 and post-main37937330204 all5PASS; mergeddf126be3c393c7841ac58408e620b82744a19e03.
- PR201 exact/post, PR203 exact/post all5PASS. PR202 exact passed; its post-run37932366842 was cancelled/superseded, never passed. PR203's subsequent integrated-main check passed. Evidence remains in ci-*.json and git history.

## Sole active native trials

| Board | Run | Source | Worker | Scope |
| --- | --- | --- | --- | --- |
| Core |37936741388|`cba4755227b52145a9dc9cd9e5e0f9880787ff1f`|`agent-fix/189-core-u1513-worker`|26 B.Cu signal segments,no vias/cuts; ordinary gated adoption |
| JL |37947364213|`330975fde822e4872fe0b5219788b1ab46b094c4`|`agent-fix/189-jl-u2204-adopt-worker`|Gated adoption replay of eligible native endpoint pilot:53objects/3vias/1reviewedcut |
| JR |37945797248|`0b38d659151730dad5fd65500fe9319dbb92df8c`|`agent-fix/189-jr-u8303-endpoints-worker`|Read-only joint39objects/1via/2reviewedcuts,including both retained endpoint links; no automatic repair |

Do not write these worker branches, duplicate same-board trials or count their pending output. The JR pilot cannot promote canonical boards; the JL gated adoption worker may publish only after all native gates. Reconcile actual terminal receipts/artifacts before selecting any next same-board action. Core alternatives must not be rebased before core26 is terminal/reconciled.

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

## Latest terminal JL control and completed core screen

JL37940189931 is now terminal/rejected for no strict improvement:121→121,0DRC/parity,477unchanged warnings,no splits,fresh agrees. All33241uncut objects identical,+8Bsegments/1cut. AGND returned to18while the victim was restored. Artifact11621538416 ZIPd6d7f2e285ae738b0634e49c24b6bfffc253bae68b8e929b84302013ae89c95d; candidate9a55a3efcacf41672abef2a97d2098fe8aa9ae19b3d66e9791c670e7975fc3d0; replaya518a11401feb003d1eb84cfaf7c75cbe35862d10dddcf76cfd6f5671aa0fd76. A distinct joint ground/victim raster transaction finds51objects/3vias/1reviewedcut on F/B. F/In2/B fails victim restoration. `jl-coupled-plan.json` now pins the complete F/B candidate; no automatic repair. Native NOT RUN at this commit.

All252core ground groups have now been screened at0.0125mm, without skipped frames:39positive groups/394objects. Pair-spacing selection excludes one0.025mm via conflict, retaining38groups/382objects/38vias. The saved batch and dynamic rebase helper are updated, but NOT rebased/dispatched while core26 remains active. Original .025/.0125 first24 comparison remains identical-input evidence; later groups have no speedup claim.

JR37940194109 is terminal; its artifact11622010297 (ZIPa40c3cb959ab9c67286dfe612b25b36fdef0aa000a52a382f41b9940acaefd3e) is downloaded/verified. Receipt says137→137,0DRC/parity,520unchanged warnings,no original splits,not adopted. Finish retention/topology reconciliation before a next JR trial.

## Next native trial sources after afc0edb

JL joint trial37942916185 is active on `agent-fix/189-jl-u2204-joint-worker`, exact source `afc0edb05e980739b52f9275a360cc75f3cd36d8`. It is read-only;51objects/3vias/1reviewedcut,explicit ground plus signal,F/B only. The previous JL outer control remains rejected.

JR37940194109 is fully reconciled/rejected137→137:14adds/2cuts,all51024uncut objects identical,0DRC/parity,520unchanged warnings,no splits,fresh agrees. Cut AGND26→25returned26after signal restoration; victim1→2→1. Candidate6861070eb3d554c0f25e7dce6075d0df4c8085ecba14c9da80a59b7e93467b06; replayb67a21c204a25f0f8585fba7dab690a92d6893658da05dd50a8b7ef3031c4112. JR joint F/B candidate now pins36objects/1via/2cuts after reserving explicit ground and restoring only the two native parts of the original cut component. Full original memberships remain the native acceptance baseline. Native NOT RUN at this commit.

Core38-group saved batch has exactly one proposal/proposal conflict with pendingcore26: J900237.2,−0.3375mm. If that exact core26 stage is accepted, explicitly exclude this entire unaccepted group with `select_candidates.py --exclude-pad J900237.2`, then rebase against the actual accepted hash and inspect proof. If it rejects, keep38groups. No exclusion/rebase has been applied while pending.

## Endpoint continuation (2026-10-09, supersedes earlier local-pilot table)

Main9376342 is nativeJL121/JR137/core1441; post-merge37941329856 all five checks passed (ci-main-9376342.json). Joint JL51 run37942916185 and JR36 run37943728586 improved to120/136 and preserved original pad groups, zero native DRC/parity errors and identical fresh connectivity, but were rejected for one/two new dangling warnings on retained tracks. Complete receipts, artifact hashes and full-object retention proofs are in the corresponding joint directories. No candidate copper was promoted.

New endpoints proposals preserve those joint objects and original reviewed cut sets, adding only two B.Cu JL segments and three F.Cu JR segments, no vias. Search anchors use the exact retained endpoints shared with removed original tracks, not the DRC item's displayed position (which may be the opposite track end). Helpers ran under heavy guard; JR initially failed a proposal-to-dump conversion and passed after explicit conversion was fixed. These are raster-only pending strict native pilots; original input hashes remain authoritative. No warning waiver or retained-track deletion.

Core next24 signal screen completed all48 F/B cases in296.535883952s (guardPASS299), eight positive cases/105objects. Native acceptance not run. Core26 run37936741388 remains the sole active core writer; do not rebase/submit the prepared finer-ground batch until its actual result is reconciled. Conditional J900237.2 exclusion and rebase instructions above still apply.

Endpoint native pilots: JL37945793199 and JR37945797248, both source0b38d659151730dad5fd65500fe9319dbb92df8c, dedicated `agent-fix/189-jl-u2204-endpoints-worker` and `agent-fix/189-jr-u8303-endpoints-worker`. Read actual `gate.adopted`, not top-level pilot status. If eligible, fixed replay choices `u2204-endpoints`/`u8303-endpoints` are prepared to serialize exactly the pinned objects and reviewed cuts, then run `route_shards.py merge` with all native gates. Do not dispatch until pilot evidence is reconciled; do not manually promote a pilot artifact.

The first48 plus next48 core signal cases now yield a conservative saved15-segment/10-net short subset (at most4segments and4mm per case), no vias/cuts. Full selection hashes and pairwise new/new gap checks are in `core-short-no-via`. This supersedes the earlier12-segment/7-net subset; it is still original-input-only, not rebased or native accepted. Ground batch remains the preferred next core transaction.

JL endpoint pilot37945793199 is terminal/eligible121→120:0DRC/parity,477unchanged warnings,no new warning identities/splits,fresh native agreement. Full33241uncut objects identical,+53/1reviewedcut. Artifact11624457321 ZIPda72aebbaa496eb93a4e43fdfe5e0b844bbcece35fe1bb9d3e8e0ab2b4a23c50; candidate2068e5e7fc0ab3f091423e3685e6793c36de24c6308c681233465b3ce100b437; replay8ec99ea42016282c19fcd4860c82a9ee402ff218eafb80d20c558d32354c847d. Native adoption replay is the next JL action; canonical remains121 until it succeeds.

Third core no-via screen completed48cases,6positivecases/92segments,zero vias,344.347644239s (guardPASS349). Short saved successor is now19segments/11nets; no rebase or native acceptance. Other longer paths remain separate evidence.

JL adoption37947364213 failed before routing: the newly copied additive prepare helper lacked the .kicad_pro required by grid_apply for cuts. Canonical copper is unchanged; no native adoption check passed in that failed job. Both endpoint prepare helpers now copy the original .kicad_pro and .kicad_dru beside the disposable output; the strict missing-project guard is unchanged. Retry through a new source-pinned worker after this correction.

JR endpoint pilot37945797248 is terminal/eligible137→136:0DRC/parity,520unchanged warnings,no new identities/splits,fresh agreement. All51024uncut objects identical,+39/2reviewedcuts. Artifact11624043283 ZIP990c17f4155dc6ad98b4f0db0c091f1b25bd265c16d834afa2bfa9fb68b6293b; candidate33747bfc15d66bc92e7fb7c563dfa853b13058a0056075626551ef3d385d6b84; replay88f040c0318eccb93cf002f7a35e8d464b21c38c41d44f5bf765688468bcd953. Canonical remains137 pending gated adoption.
