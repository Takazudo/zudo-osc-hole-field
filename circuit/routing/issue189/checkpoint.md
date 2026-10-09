# Issue 189 exact continuation checkpoint

Updated 2026-10-09 15:55 UTC. **Issue #189 remains OPEN.** Accepted native open edges are **JL120 / JR136 / core1441**. Zero-edge connectivity and final completion gates are unmet. No fabrication or hardware qualification is claimed.

## Current authoritative state

Main is merged PR207, commit `9de20ab442dca2940da0a201d5ef5e764dcdbea3`. Its exact-head CI37950014675 and post-merge CI37952715447 passed all five jobs; receipts are `ci-0d6a444.json` and `ci-main-9de20ab.json`. Current continuation is draft PR208, branch `agent-fix/189-next-ground-continuation`. It preserves negative evidence and prepares bounded successors; it adds no accepted copper beyond PR207. Refresh its exact head and checks before any merge.

All accepted boards have zero native DRC/parity errors, no new warning identities or split original pad groups, and fresh native agreement. Warnings: JL477/JR520/core619. Fixed panel/electrical rules, accepted copper and other sessions remain preserved. PR202 post-CI was cancelled/superseded, never passed; subsequent accepted main states have passed post-CI.

## Active native trials — reconcile before further board work

| Board | Run | Dedicated worker branch | Pinned source |
| --- | --- | --- | --- |
| Core |37950004600|`agent-fix/189-core-finer-ground-worker`|`0d6a444aa1ad648ce6146d0e893e93307bd98f14`|
| JL |37953994482|`agent-fix/189-jl-c2248-ground-worker`|`ab36b23ae2afbf371a72ff9990a5f353293a94df`|
| JR |37953998528|`agent-fix/189-jr-r7609-ground-worker`|`ab36b23ae2afbf371a72ff9990a5f353293a94df`|

All three were in progress at this checkpoint. The core run is the sole core writer:38 ground groups/382objects/38vias/zero cuts, full0.3mm AGND tracks. Jack runs are disposable cut/restoration pilots, not canonical writers. Each selects three unchanged original signal segments on one victim net, F/B restoration,300000 cap. Neither cuts PR207's new copper. Do not dispatch overlapping trials or change pinned worker branches.

## Exact next actions

1. Refresh each run with `gh run view RUN --json status,conclusion,headSha,jobs`; refresh main, PR208 and the other-session refs before changing boards. Download terminal artifacts, verify their published ZIP SHA256, and retain the full native baseline/candidate/fresh evidence. Workflow success alone is not adoption.
2. For the jack pilots read actual `gate.adopted`, original native pad-group memberships, warning identities, DRC/parity and fresh agreement. Prove all uncut full copper objects remain identical. If rejected, preserve receipts and change the demonstrated cause; no unchanged retries or larger-cap substitute. If eligible, implement a pinned replay through normal native adoption gates rather than copying the pilot board manually.
3. For core37950004600 inspect `boards/osc-core/reports/grid-routing/shards-issue189-finer-ground-batch.json` and the native artifact. Require all133169 prior full copper objects, including duplicate UUID blocks, to survive, plus every usual native gate. Reconcile the bot delta from its pinned source. Adopted copper may be integrated only after those proofs; a rejected bot receipt must not be treated as a board gain.
4. Only after core reconciliation, run `.circuit-cache/route-venv/bin/python circuit/routing/issue189/core-short-no-via/rebase_proposal.py --accepted-sha256 ACTUAL_ACCEPTED_SHA256`. It accepts only unchanged core or the exact whole known382 ground additions, verifies their full native geometry and all prior blocks, and rejects unexpected changes. It writes proposal/plan/rebase receipts for19short signal segments/11nets, no vias/cuts. Inspect those receipts, commit/push a new dedicated worker, then dispatch `gh workflow run routing-benchmark.yml --ref NEW_WORKER -f board=osc-core -f recover_core=true -f core_replay=short-no-via`. All native gates remain mandatory. This future rebase has NOT run.
5. Do not close #189 until all three canonical boards pass zero-edge completion, settled/fresh native connectivity, unchanged constraints, regeneration/P/EL/O checks and same-revision final documentation/renders. Verified intermediate progress is not hardware qualification.

## Core negative controls and held proposals

Core26 run37936741388 rejected1441→1442: target signal joins but AGND252→254, splitting U1513.12 and C1547.2/C1545.2/C1546.2. All133169old objects survive,+26/zero cuts,0DRC/parity,619unchanged warnings,fresh agrees. Bot5e15231b4414064b3817ab207728c471ea90ac22, receipt-only cherry8e2514e. Full hashes/proofs are in `core-u1513-alternatives/`. Do not repeat unchanged. Because it rejected, the active ground batch retained J900237.2; its earlier conditional exclusion was NOT applied.

All252 core ground groups were screened at0.0125mm:39positive groups/394objects. Selection excludes J900215.2's whole12-object case because a new via is only0.025mm from another, leaving38groups/382objects/38vias. `core-finer-ground-batch/rebase.json` pins the unchanged accepted input. No ground objects are accepted yet.

The three completed short-signal screens cover144 F/B cases. Their saved19-segment/11-net subset is in `core-short-no-via/`, with minimum new/new foreign-net gap19.556740598mm and minimum gap to pending ground2.136739296mm. Geometry guard regression tests pass for53real native objects and same-UUID coordinate/width/net mutations. This is static preparation, not native acceptance.

Core143 run37925863664 rejected1441→1343 despite109 supply joins: original AGND groups split, and a new warning identity appeared on unchanged preexisting vias. No waiver. All133169old objects survived,+143/zero cuts. Full artifact/split attribution is in `core-short-power/`. The proximity-filtered supply successor remains heuristic, unrebased and unsubmitted; its conditional conflict is detailed below.

## Accepted immutable boards and retention

| Board | Published SHA256 | Latest accepted stage |
| --- | --- | --- |
|JL120|`2068e5e7fc0ab3f091423e3685e6793c36de24c6308c681233465b3ce100b437`|37947934139:121→120,+53/1reviewedcut,all33241uncut objects identical|
|JR136|`33747bfc15d66bc92e7fb7c563dfa853b13058a0056075626551ef3d385d6b84`|37947938555:137→136,+39/2reviewedcuts,all51024uncut objects identical|
|Core1441|`a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932`|37895925149:1509→1441,+216segments/0cuts,all132953original objects identical|

JL bot`abd7af3bcbbcdd25f553c5ed2aa7ea5863f60acb`, cherry`a8c0876`; artifact11625415141 ZIP`71a7b0d79fe22dbc99dfe4d089c154807cdcd5e43895b72fa883073c5f3fb123`; replay`8ec99ea42016282c19fcd4860c82a9ee402ff218eafb80d20c558d32354c847d`.

JR bot`574025484e6b1413f97b9b761041ab4f3973b85f`, cherry`2b38e2e`; artifact11625175772 ZIP`d278a0f56c37007eea57ecab8e45d7bf17968ccc945e9c61e1c99ab04c422105`; replay`88f040c0318eccb93cf002f7a35e8d464b21c38c41d44f5bf765688468bcd953`.

Both adoption outputs exactly match their eligible pilot board and replay hashes. Native DRC/parity0/0,warnings477/520,no new identities/splits,fresh agreement. Full-object retention and physical invariants are in `{jl-u2204,jr-u8303}-endpoints/`: JL3925/JR3655pads,four outline edges,123/154rule areas,six layers unchanged; project/rules byte-identical.

JL30433segments/2861vias,103signal+17AGNDedges. JR47948segments/3115vias,111signal+25AGNDedges. Both jack supply rails have zero open edges. Core80+12V/80−12V/252AGND/1029signal edges. Latest cumulative full-object ledger records reviewed jack removals; do not claim all original jack copper survives. All original core copper survives. Fixed panel, electrical rules and placements remain unchanged.

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
