# Issue 189 exact continuation checkpoint

Updated 2026-10-09 18:35 UTC. **Issue #189 remains OPEN.** Accepted draft boards: **JL119 / JR134 / core1441**. Main: **JL119 / JR135 / core1441**, commit `4db1d3c009dbf7744541c01692bc626213832ca6`. Zero-edge completion, final regeneration/P/EL/O and renders remain unmet. No fabrication or hardware qualification is claimed.

## Blocking scope correction — supersedes eligibility statements below

At18:38UTC source review found that native silk DRC also tests outer copper zone fills. The candidate changes those fills; added-via fixtures do not cover this scope. The earlier reassessment is provisional, **not eligible for adoption**. Validator now rejects changed silk-relevant zone blocks and a regression passes. `native-hole-audit/reassessment.json` records the block; earlier result retained as explicitly provisional. Native zone evidence is still required. Do not dispatch ground adoption until the scope is complete; core19 remains sole writer and canonical core1441 unchanged.

## Current work and accepted evidence

PR209 is draft at `2c3afdedf9e999ef0b091db74805d10fc5687d44`, base main. CI37972341588 must be checked at that exact head; earlier e736 checks do not cover the context fix. PR210 is draft at `f2a5a025dc31bbc1f5ada2f6def486abc49db717`, stacked on209, CI37973580281. Current continuation branch is `agent-fix/189-finer-jack-continuation`. PR208 merged at4db1d3c only after all five exact-head checks; all five post-merge checks passed (`ci-main-4db1d3c.json`). Preserve branches and other sessions.

JR adoption37967123290 is accepted and integrated as133f2f6 from bota59ef366:135→134,+37segments/5reviewed cuts,all51140uncut full objects identical,0native DRC/parity,520unchanged warning identities,no original pad-group splits,fresh agreement. Published board35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445 and replay3c3495b6442d463366c39ccdee4c010f9ca3c030cb321cda4d1780c4a6971c61 match the eligible pilot. Artifact11633969149 ZIPafa07c7a1c2315162bcc62fa780a0e6e805f0082c4f59e5739ec000a097b8b5a. Proofs in `jr-c7413-endpoints/`.

Accepted JL119/core1441 retain their pinned boards below. All three have0native DRC/parity, no new reported warning identities or original group splits, fresh agreement and unchanged physical/electrical context. Warnings477/520/619. `retention-ledger-133f2f6.json` records full-object multisets including legacy duplicates: original JL32609retained/136reviewed changed or removed; original JR50287retained/24reviewed changed or removed; all132953original core objects retained. Latest stages preserve every uncut object. Do not claim all original jack copper survives.

## Complete native warning evidence — core1402 eligible, not adopted

Core ground run37950004600 produced1441→1402,+344segments/38vias,zero cuts,all133169prior full objects retained,0DRC/parity,no original group splits,fresh agreement. Raw gate rejected one newly reported hole pair on unchanged old vias. Candidate SHA `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66`, replay25a3de5583c9bb61611a4e46d9463a581a09cba43c1dc23bf2d45c5203a3b08c. Artifact11631867897 ZIP8919c769bba2f17fc3d695a80590f6e75e618d8767f464baf2d39fb027ca90d6. Full retention/rejection proof is in `core-finer-ground-batch/`.

Exact native10.0.6 caps hole and both silk warning domains at199reports. First geometry-keyed hole audit37967430188 is diagnostic only: complete validator caught SaveBoard resetting all fixture projects. No board was promoted. Corrected producer restores context after serialization and verifies bytes around DRC. Corrected run37972238437 at2c3afde passed:9815/9853holes,128fixtures each,1407identical full UUID and geometry-object identities,zero new/removed,all original full-board identities covered. Every raw report SHA and fixture project/rule file independently matches. Artifact11637606039 ZIP48c8b07dea13eeb4f2e257908e2ee49a80e460e6582e011a5d57cf8047d3e8db. Authoritative evidence is `native-hole-audit/context-*.json`; old files are retained as diagnostic history.

Silk audit37970119956 at e7364065 passed all38new-via fixtures: zero new silk_overlap/silk_over_copper identities, maximum69/0reports below199, exact project/rule bytes, unchanged3807nonrouting objects, native mask signatures and rendered text verified. Artifact11635870901 ZIP3c3ec3d0368d3fc4c2d2fc7dbf33963e664a8bbfc2d0c3f4198d447b49bd0957. Full result/receipt under `native-hole-audit/silk-*`.

Same saved inputs: `native-hole-audit/reassess.py` now passes, guardPASS30s. Raw gate rejects; appending complete native observations to both reports makes the **same ordinary gate eligible1441→1402**, with no original finding removed. `reassessment.json` binds all three audit result hashes and fresh native agreement. Canonical core remains1441.

Opt-in `route_shards.py merge --complete-native-warnings` generates all native audits against its actual baseline and fresh candidate, validates raw reports/context/coverage, then reruns the ordinary gate. Incomplete/stale/unsupported/new warning evidence rejects and retains receipts. Existing DRC, parity, membership, fresh-agreement and stale-publication gates remain enforced. Workflow choice `finer-ground-complete-warnings` is prepared but **NOT RUN**. Mask audit deliberately supports only the reviewed382object/38via scope. One hundred affected router tests pass; audit/evidence/workflow tests and nine rebase tests pass. `pnpm circuit:check` and `pnpm check` pass.

## Sole active core writer

Run **37965185751**, worker `agent-fix/189-core-short-no-via-worker`, source `08aec29e83d24d291f4d41a7bb10300e072a7260`:19outer segments/11signal nets,zero cuts/vias, rebased ontoa0e3cff1 with all133169prior objects retained. Still active at last check. **Do not start any competing core writer or overwrite its branch.** Read-only warning audits are terminal. No jack writer is active. Two read-only jack pilots are active; neither can promote canonical copper.

## Active read-only jack pilots

- JL R8276.2: run37973959441, worker `agent-fix/189-jl-r8276-finer-worker`, exact source880fe7422532b4d77705aada1eb6e7403c29df72. On current JL119, the0.0125mm prefilter finds38ground segments with two reviewed signal cuts/two victims in14.9×16.45mm. Earlier0.025mm prefilter found no path. Other ten previously negative cut targets remain negative on the finer screen (guardPASS49s). Native victim restoration/full gates remain pending. No placement moved. Plans/source evidence in `jl119-r8276-2-finer-ground-cut/`.
- JR RB4614.2: run37974220440, worker `agent-fix/189-jr-rb4614-worker`, exact sourceb3ba58e8e4c1363efe08e55324cecd68455c9625. Rebased old positive ground-only prefilter onto accepted JR134 by checking both selected full native track records unchanged; target remains isolated. Two cuts/two victims,13.6×25.2mm original frame,0.025mm. No accepted JR134 additions selected. Native restoration/full gates pending. Plans/rebase proof in `jr134-rb4614-2-ground-cut/`.

Parent steering at18:34UTC explicitly confirms incremental merges remain authorized after exact gates pass and requires core19reconciliation before another ground writer. Preserve single-writer order. Pending jobs are ongoing work, not completion.

## JL changed-method negative controls

C8142 pilot37967648679 rejected119→119,+21segments/11cuts,all33337uncut objects identical,0DRC/parity,477unchanged warnings,no original splits,fresh agreement; AGND16→15after cut→16after restoration. Artifact11634289502 ZIPa5697c04b3510063c1b0ea3198951f01debaa42a6f128e12faca021066606c2d. Correct original victim subset used. Coarse/finer joint routing and explicit In1fanout comparisons fail complete restoration; no partial proposal submitted. Saved under `jl119-c8142-2-ground-cut/`, `jl-c8142-joint*`, `jl-c8142-ground-fanout/`.

Source-defined R8127 move comparison preserves fixed geometry, orientation/side, all copper and a full0.2mm signal landing bridge. Of288translations within±0.8mm, seven pass exact JL outline/courtyard/copper screens. Unmoved control and all seven fail both direct ground routing and plane fanout at0.0125mm/300k. GuardPASS25s/29s. No placement changed/native moved-board validation run. R8276 similarly has14static candidates of288; its plane-fanout control and all14fail, guardPASS39s; direct comparison also fails the unmoved control and all14translations, guardPASS44s. No bridge-only proposal is eligible.

## Exact continuation

1. Refresh `gh run view 37965185751 --json status,conclusion,headSha,jobs`, PR209 exact-head CI37972341588, main and other-session refs. Keep189OPEN. Other-session heads last checked: core-rrr-escalate8315af55, jack-replace-region-230db43e0, jack-replace-jl-1470b3f0e. No unrelated watches.
2. Download terminal core19artifact; verify ZIP SHA, full copper multiset, all native topology/DRC/parity/warning/fresh/context invariants. Reconcile bot receipt and actual board before cherry-picking; workflow success alone is not adoption. Never replace newer accepted copper.
3. After core19is terminal/reconciled, run ground rebase with its **actual reviewed accepted board hash**: `bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/core-finer-ground-batch/rebase_proposal.py --accepted-sha256 HASH`. Guard allows unchanged core or the exact whole19signal additions, checks every full new geometry, all old copper, and0.25mm proposal conflicts. The older26trial rejected; no longer assume it may have been adopted.
4. Commit the actual ground rebase; push a new isolated worker. Dispatch `gh workflow run routing-benchmark.yml --ref WORKER -f board=osc-core -f recover_core=true -f core_replay=finer-ground-complete-warnings`. Native audits must be regenerated for the actual candidate; never reuse old source-bound evidence on changed core. All ordinary gates, fresh agreement and publication equivalence remain mandatory. No unchanged raw rejection retry.
5. Preserve current PR209 draft until exact checks finish. New continuation should have a reviewable draft PR and exact native evidence/checkpoint. Follow current user merge authorization; never infer merge permission from green checks. Final zero-edge/regeneration/P/EL/O/render gates remain unmet.

## Historical evidence (pending statements below are superseded above)

## Core negative controls and held proposals

Core26 run37936741388 rejected1441→1442: target signal joins but AGND252→254, splitting U1513.12 and C1547.2/C1545.2/C1546.2. All133169old objects survive,+26/zero cuts,0DRC/parity,619unchanged warnings,fresh agrees. Bot5e15231b4414064b3817ab207728c471ea90ac22, receipt-only cherry8e2514e. Full hashes/proofs are in `core-u1513-alternatives/`. Do not repeat unchanged. Because it rejected, the active ground batch retained J900237.2; its earlier conditional exclusion was NOT applied.

All252 core ground groups were screened at0.0125mm:39positive groups/394objects. Selection excludes J900215.2's whole12-object case because a new via is only0.025mm from another, leaving38groups/382objects/38vias. `core-finer-ground-batch/rebase.json` pins the unchanged accepted input. No ground objects are accepted yet.

The three completed short-signal screens cover144 F/B cases. Their saved19-segment/11-net subset is in `core-short-no-via/`, with minimum new/new foreign-net gap19.556740598mm and minimum gap to pending ground2.136739296mm. Geometry guard regression tests pass for53real native objects and same-UUID coordinate/width/net mutations. This is static preparation, not native acceptance.

Core143 run37925863664 rejected1441→1343 despite109 supply joins: original AGND groups split, and a new warning identity appeared on unchanged preexisting vias. No waiver. All133169old objects survived,+143/zero cuts. Full artifact/split attribution is in `core-short-power/`. The proximity-filtered supply successor remains heuristic, unrebased and unsubmitted; its conditional conflict is detailed below.

## Accepted immutable boards and retention

| Board | Published SHA256 | Latest accepted stage |
| --- | --- | --- |
|JL119|`554fa85a44d74c2ad2105e34f1bbc4de9b674e46dd7531ddc3e00c6d8e1c1291`|37960073108:120→119,+58segments/4reviewedcuts,all33290uncut objects identical|
|JR135|`d2a7d2c9d1d1135296e5a591748214ec4e16198bfdf4ec31e30e4199c2e1c0e8`|37960834229:136→135,+85segments/1via/4reviewedcuts,all51059uncut objects identical|
|Core1441|`a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932`|37895925149:1509→1441,+216segments/0cuts,all132953original objects identical|

Previous PR207 JL bot`abd7af3bcbbcdd25f553c5ed2aa7ea5863f60acb`, cherry`a8c0876`; artifact11625415141 ZIP`71a7b0d79fe22dbc99dfe4d089c154807cdcd5e43895b72fa883073c5f3fb123`; replay`8ec99ea42016282c19fcd4860c82a9ee402ff218eafb80d20c558d32354c847d`.

Previous PR207 JR bot`574025484e6b1413f97b9b761041ab4f3973b85f`, cherry`2b38e2e`; artifact11625175772 ZIP`d278a0f56c37007eea57ecab8e45d7bf17968ccc945e9c61e1c99ab04c422105`; replay`88f040c0318eccb93cf002f7a35e8d464b21c38c41d44f5bf765688468bcd953`.

Both adoption outputs exactly match their eligible pilot board and replay hashes. Native DRC/parity0/0,warnings477/520,no new identities/splits,fresh agreement. Full-object retention and physical invariants are in `{jl-u2204,jr-u8303}-endpoints/`: JL3925/JR3655pads,four outline edges,123/154rule areas,six layers unchanged; project/rules byte-identical.

JL30487segments/2861vias,103signal+16AGNDedges. JR48029segments/3116vias,111signal+24AGNDedges. Both jack supply rails have zero open edges. Core80+12V/80−12V/252AGND/1029signal edges. Latest cumulative full-object ledger records reviewed jack removals; do not claim all original jack copper survives. All original core copper survives. Fixed panel, electrical rules and placements remain unchanged.

Core native-filled hash`95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5`; cache-only publication equivalence proved. Artifact11603564190 ZIP`a01f06e5458221d6d013c5331110e0f60c849d756cec84dfdcf835750bda4cfc`.

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

## Successor cut results and next scopes

JL37950326215 rejected120→120:2adds/2cuts,all33292uncut objects identical,0DRC/parity,477unchanged warnings,no splits,fresh agreement. AGND17→16after cut→17after victim restoration. Victim obligations are J900047.5 and U1516.8/U1516.9. Exact endpoints, full native component terminals, and explicit ground-plane fanout methods all failed to find complete bounded joint paths in their saved two-variant screens. No partial rows were submitted.

JR37950331735 rejected136→136:7adds/3cuts,all51060uncut objects identical,0DRC/parity,520unchanged warnings,no splits,fresh agreement. AGND25→24→25. Victim obligations are U6105.10, J900107.5 and a five-object padless piece. Exact endpoint, full-component, and smaller two-cut reconstruction methods all failed to produce complete bounded proposals. The smaller cut set retains original0.15mm segment7ce0d76d-8094-5807-b95d-ce967dc887af; its pad/track contacts were checked exactly, but no native two-cut acceptance is claimed. Stop these unchanged configurations; no larger-cap retry.

Next source-pinned cut plans target JL120 C2248.2 (three cuts/one victim,15.4x13.1mm frame) and JR136 R7609.2 (three cuts/one victim,12.84x15.55mm frame). Every selected original track is identical on the accepted input, and neither cut set touches the recently accepted endpoint-repair copper. These are disposable native pilots, not canonical writers. Core37950004600 remains the sole core writer.

Active later jack pilots: JL37953994482 (`agent-fix/189-jl-c2248-ground-worker`) and JR37953998528 (`agent-fix/189-jr-r7609-ground-worker`), sourceab36b23ae2afbf371a72ff9990a5f353293a94df. The earlier U1502/J900107 pilots are terminal/rejected; do not repeat their saved unsuccessful joint configurations.

The saved94-case/120-segment supply heuristic has one static conflict with pending ground382: U4439.4, two segments,0.1947073557mm gap. If the exact ground batch is accepted, omit/redesign that complete unaccepted case before any supply rebase (93cases/118segments remain). Do not change accepted ground copper. This comparison is not a native result or proof that the remaining supply subset preserves ground fill. The19-segment signal successor has a ready guarded rebase/prepare path; neither successor is submitted while core37950004600 runs.


The supply successor now has a guarded `rebase_proposal.py`, native `prepare.py` and workflow replay choice `supply-away-from-splits`. It requires the actual accepted SHA, retains all original full blocks, and permits only exact whole known ground382 and/or short-signal19 additions. It drops whole unaccepted supply cases that conflict with accepted additions and records exclusions. Five regression tests pass; workflow YAML/all12shell steps pass syntax checks. Actual rebase, native serialization and acceptance are NOT RUN. See its README for commands. The19-segment signal trial remains the immediate core successor after current reconciliation.


## C2248/R7609 terminal controls and alternate scopes

JL37953994482 rejected120→120: AGND17→16after cut→17after restoration,10adds/3cuts,all33291uncut objects identical,0DRC/parity,477unchanged warnings,no original splits,fresh agrees. Candidatea9d3abdb77cd78fe21b1facaf1be1353b5cbe67a25e420794bd5d1a8eb6a1984; replay243b810ad831be18b935a794869d0faced708e2beb42895059fcdbe3f69691db. Artifact11628245582 ZIP11209263dd7578c5167d4bfab56224f5559cf8fafcb915038c5a2257befe5701. Saved under jl120-c2248-2-ground-cut/.

JR37953998528 rejected136→136: AGND25→24→25,12adds/3cuts,all51060uncut objects identical,0DRC/parity,520unchanged warnings,no original splits,fresh agrees. Candidate4f8819718a91544d53a17962ad748d85a6b89a63b349abc0523c2bb41bff4fb0; replay1d2f270a9233d5d5e7225f533e34d6ed5a8c42d8c1cfb20d77335b7c62e21101. Artifact11627612924 ZIP8f1fd70bbd4a1688902391d683790a827ea1fa2cb1bc678edde7dc234bc4f7e6. Saved under jr136-r7609-2-ground-cut/.

Both scopes then failed complete bounded joint routing on F/B and F/In2/B at0.025mm, a finer0.0125mm access comparison, and explicit ground-to-In1 fanout at0.025/0.0125mm. All local searches completed under heavy guard; no partial proposal was submitted. Stop those unchanged configurations. The endpoint search exhausts well below300000, so raising caps is not justified.

New distinct native cut/restoration scopes target JL U1518.10 (four original segments/two victim nets,16.25x13.1325mm) and JR R4207.2 (four segments/one victim,14.4x13.96mm). Source preparation verifies exact selected geometry against accepted JL120/JR136, target disconnection, finite bounds and existing repair limits; it does not cut newly accepted PR207 copper. Plans are in jl120-u1518-10-ground-cut/ and jr136-r4207-2-ground-cut/. These are new disposable native trials, not accepted gains.


Current alternate jack runs are JL37956537948 and JR37956542080, source5add51f584e077ad9529854ea27ba7ac2b512d2e, on the worker branches in the authoritative table. Both are pending, not accepted gains.

A read-only source-defined R7609 placement comparison tested288translations within±0.8mm while retaining all copper and orientation. Three pass exact source-outline and conservative courtyard clearance; all three conflict with existing segment638c8d71-8db4-5871-a197-ea0ffd3d7075. No static candidate survives, no placement changed and no native acceptance claimed. Exact input/floorplan hashes and results are in jr-r7609-placement-screen/. This negative result applies only to this small no-cut translation scope.


The expanded1680-case R7609±2mm translation comparison also yields zero candidates after applying the exact JR source outline and0.30mm inset. The preliminary panel-envelope outputs are retained and explicitly superseded; six apparently pad-clear larger shifts were outside JR and were ruled out before routing. Authoritative results pin the exact partition/floorplan hashes. No source placement or physical constraint changed.


JL37956537948 is now terminal/rejected120→120:AGND17→16→17,5adds/4cuts,all33290uncut objects identical,0DRC/parity,477unchanged warnings,no original splits,fresh agreement. Artifact11630850236 ZIP72c63a28cc78d4f140149fdc192eb29f580f3dc465179380a65d6af6d61a7013; candidate749845e4071e2fc51fae37c8e790b44cef86282bdab91c30b0cd86176583eaa6; replayba6cbb4144fa498a67fc31e56694c5417e0bf1b98455d684f6ac05a56b963954. Receipts are in jl120-u1518-10-ground-cut/.

The distinct joint U1518 search reserves explicit AGND then restores both actual native-cut victim components. First declared order completes58segments/no vias with the same4cuts at0.0125mm, F/In2/B,300000cap,original finite frame; heavy guardPASS6s. jl-u1518-joint/ and jl-coupled-plan.json pin this complete proposal for a strict native pilot, without automatic repair. Raster completeness is not native eligibility; retained-endpoint and all original acceptance gates remain mandatory. JR37956542080 and core37950004600 are still pending.


Active JL joint pilot37958624929 uses source161f734bd0319b0ce51a1e8d1331d0196ed416d0 on agent-fix/189-jl-u1518-joint-worker. Its two exposed retained endpoints are inside new same-net copper in the saved endpoint-screen.json; this is geometry evidence only, not a native warning result. A gated adoption replay is prepared as choice u1518-joint, with exact input/proposal/add/remove UUID checks and original project/rules copied for native cuts. Workflow YAML/all12shell steps and Python syntax checks pass. Native serialization/adoption is NOT RUN; dispatch only after the strict pilot is eligible and fully reconciled. Then commit/push a dedicated worker and use `gh workflow run routing-benchmark.yml --ref NEW_WORKER -f board=osc-jack-left -f replay_jl=true -f jl_replay=u1518-joint`.


JR37956542080 is terminal/rejected136→136:AGND25→24→25,3adds/4cuts,all51059uncut objects identical,0DRC/parity,520unchanged warnings,no original splits,fresh agreement. Artifact11629966173 ZIP5c2d6bc015f5a123c35d5efd183d43e5e825c7a990e2da87b83fab5c9723699b; candidate5d3029b1c03cb72c9e0054c72d23f517ab46f03ccbcffa22b3b3685f3f7f0a4d; replayc316dfb4e6108d1fdaf646396c8786dcbdf026bf3b214914b11ee3d7bc5f4bcd. Saved in jr136-r4207-2-ground-cut/.

The new joint R4207 proposal completes86objects/one via/same4cuts on F/B0.025mm. Initial setup asserted both cut components had retained-track anchors; actual native topology has bare D1401.2 and a96-object component. Corrected explicit topology checks pass, full components remain authoritative, guarded searchPASS4s. No partial/failed setup proposal was submitted. jr-r4207-joint/ and jr-coupled-plan.json pin the complete transaction for strict native validation; no automatic repair/adoption. Gated replay choice r4207-joint is prepared but must not run before native pilot eligibility and complete reconciliation. No new accepted copper yet.


JL joint pilot37958624929 is terminal/eligible120→119:58segments/no vias/4reviewed cuts,all33290uncut objects identical,0native DRC/parity,477unchanged warnings,no new identities/original group splits,fresh agrees. Candidate554fa85a44d74c2ad2105e34f1bbc4de9b674e46dd7531ddc3e00c6d8e1c1291; replayd7169d41e8005ec1602e959fa99209aaeeef5e04a877ef8c9134adaf594cadd6. Artifact11630198018 ZIPfebbf292f200a933d61f3eb8fe2bea85b053cbfe84bae4a5d50322f066bc8613. All3925pads,four edges,123keepouts,six layers unchanged; original project/rules byte-identical. Full proofs are in jl-u1518-joint/. Canonical JL remains120 until the separately gated adoption replay succeeds.

JR joint pilot37959238545 runs on agent-fix/189-jr-r4207-joint-worker, source26916954440c3e55eb2e486a9e34ea4bf9e291e4. Core37950004600 remains the sole core writer. Both are pending.


JR joint pilot37959238545 is terminal/eligible136→135:85segments/one via/4reviewed cuts,all51059uncut objects identical,0native DRC/parity,520unchanged warnings,no new identities/original group splits,fresh agrees. Candidate d2a7d2c9d1d1135296e5a591748214ec4e16198bfdf4ec31e30e4199c2e1c0e8; replay16477db73f800fe549663617069ddef71c33cb24090a6f18ae377707eedad300. Artifact11630523633 ZIPbd33dde2919b133b81dfa12b9582715a3caad607bd3545ded3bcc18a09ca6e70. All3655pads,four edges,154keepouts,six layers unchanged; original project/rules byte-identical. Full proofs are in jr-r4207-joint/. Canonical JR remains136 until separately gated adoption succeeds.

JL adoption37960073108 uses agent-fix/189-jl-u1518-adopt-worker, source72f563f09865426d8965b1780972479887f944c0, and is still running. Core37950004600 is unchanged and still pending. No canonical new copper is claimed before adoption receipts are reconciled.


JR adoption37960568111 (source5b25f2f097fb849b82f3737e70b9c42d30ca8781) failed before routing: r4207-joint was declared as an input/preparation option but missing from the separate shell allowlist. No native adoption ran and canonical JR remains136. The new dispatch regression reproduced that exact failure; adding the declared choice to the strict allowlist makes both tests pass, including unknown-choice rejection. YAML/all12shell steps pass. Failed logs are retained in jr-r4207-joint/dispatch-failure.txt. Retry on a new pinned worker after this correction, not the old worker.

JR adoption retry37960834229 is now active at exact source4ad55bd217e0a079d2c85e3ed0eccaf04bf3c49e; it supersedes the failed pre-routing attempt37960568111. The authoritative active table above has been refreshed.


JL adoption37960073108 is terminal/accepted120→119 and integrated on the draft branch via cherry67d2a1e from bot3f841f829d7eaab0dd02113264f16f43d257e4be. Published/native-filled board and replay exactly equal the eligible pilot hashes above; native adoption fresh signature/physical invariants were independently checked. Artifact11630024645 ZIPe3eeb406fbad529573cb72929e634349085d030d4c6fa0ee4bbf11a598526830. New native totals on the draft branch119/136/1441; JL30487segments/2861vias,103signals+16AGND,all railszero. Main is still9de20ab with120/136/1441 pending verified PR integration. JR retry37960834229 and core37950004600 remain active.

Local `pnpm circuit:check` and `pnpm check` pass after JL119 integration and current documentation updates. Exact-head CI still must pass before merge; issue189 stays open.


JR adoption37960834229 is terminal/accepted136→135 and integrated as cherry6b72bc2 from botd3a7044c32b9a19f50cd19ea4917c3454cfbfbca. Candidate/replay exactly match the eligible pilot, and native adoption fresh signature plus physical invariants were independently checked. Artifact11632196228 ZIPd4d50e7481e7c5e3f0f325e7e5d38c215deae8caf0a4321c82eef337a56cfde9. Draft-branch totals are119/135/1441; main remains120/136/1441 until verified merge.

Separate stacked draft PR209 (`agent-fix/189-following-ground-continuation`) pins the next JL119 U2205.9 cut trial37962133490, worker agent-fix/189-jl-u2205-ground-worker, source1924fa6548ae1ad756cd9c9c359153b82ab3afcb. Four original segments/two victim nets,14.7x15.75mm frame,all new U1518 copper explicitly preserved. It is read-only and pending, not an accepted gain. Carry later accepted JR/core changes forward into that continuation before more replays or retargeting it to main.


Cumulative full-block ledger retention-ledger-133f2f6.json is recomputed (heavy guardPASS24s): original JL32745→33348,32609identical,136reviewed original removed/changed,739new; JR50311→51145,50292identical,19reviewed original removed/changed,853new; core132953→133169,all132953identical,+216. Latest stages retain every uncut object. Do not claim all original jack copper survives. Local pnpm circuit:check and pnpm check pass after both119/135 documentation updates. Exact-head CI and normal PR verification remain required before merge.

The authoritative table is refreshed for PR209. Source6e37fdd includes PR208's accepted JR135 change through a normal merge; current boards remain119/135/1441. Neither current cut pilot touches the newly accepted jack copper.
