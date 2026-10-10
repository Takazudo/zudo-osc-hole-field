# Issue189 exact checkpoint — 2026-10-10 04:13 UTC

Issue189 is OPEN. Mainbf2daa9a62d3ce173363b5f3f25211965926fc02 remains **JL118/JR134/core1441**, native DRC/parity errors0/0; warnings remain. Both native workers are now TERMINAL and independently reconciled; no active core/JR writer remains. This evidence branch preserves proofs and does not integrate either bot head or replace an approval gate.

## Verified native increments

- PR220 branch agent-fix/189-jr-neighbour-pilot, source35535749cf7f9f10dc3f2257767e3346250b3de1, bot a4ec09bcdbb9f8f29ed2737bad4e0f8b9ee3377f, run38018592247:134x3→133x3/fresh133x3,all51177old+74segments/5vias,zero cuts,1080nonrouting unchanged,0DRC/parity,no splits/new identities.24hole identities before/after,79copper fixtures,50paired zone fixtures;520original findings remain520. Artifact11657699680 SHA2560f9d6751e37ceebf1a889e2d1378fffd5a2a0cd030a9d9b6b920a76efa4de50f. Full proof/checker/resume in jr-neighbour-return-repair/full-adoption-*. Published22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd; independent guardPASS117s. Immutable bot download matches.
- PR218 branch agent-fix/189-core-batched-warning-worker, source44d1151cd41f285d5168c433c76664c44a3d97ac, botcebde33e63436b22e257ee29c419c305f8bed08f, run38011194282:1441x3→1402x3/fresh1402x3/post-compaction1402x3,all133169old+344segments/38vias,zero cuts,3807nonrouting unchanged,0DRC/parity,no splits/new identities.1407hole identities before/after,382copper fixtures,42paired zone fixtures;619original findings retained and extended to1827each. Artifact11658776367 SHA2561ed58a9cd4c5796654a9e3e5c9b6e1c1129c353f3451e04c990b95032012479f. Full proof in core-batched-native-accepted/. Nativeb9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66; publishedfa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10; native refill equivalence independently verified,guardPASS332s. Immutable bot download matches.

## Exact-head CI and integration blocker

JR CI38020346206 at a4ec09b passes all five jobs. Core CI38021229431 at cebde33 also passes all five jobs. Both accepted heads now have complete exact-head CI. Approval is not passing checks.

Automatic approval review rejected the attempted PR220 merge because the original delegation explicitly prohibits merging; later continuation-context authorization was not accepted. No merge occurred. PR220 was returned to draft, and explicit approval is pending. Do not bypass this rejection. Main remains bf2daa9 and both accepted native increments remain on their draft PR branches.

Clean local merge previews verify that each increment preserves the other current boards byte-for-byte and matches its accepted artifact. Fresh remote protected refs are unchanged; PR218/220 have no review submissions or unresolved threads. These checks are not integration.

CLI git/gh began returning401/Bad credentials; normal and supported-escalation branch pushes failed. No credentials/profile/daemon changes. Existing GitHub app reads/writes remain authorized; it published identical-tree JL and these evidence commits. The app has no workflow-dispatch action. Local pinned KiCad10.0.6Docker unpack remains blocked under214; do not retry unpack/cleanup or substitute9.x.

## Prepared JL pilot

PR221 branch agent-fix/189-jl-layer-escape, remote c6fda679ba8cb58b9b1e3a85b1db2b08f7d0bda9; local23012f3b29a593f29bd3892bdbeeba4fc52f887a has identical tree3dd40babd20c4eb46ca29c14beb674805989f1d6. All five exact source checks pass38018924349. Routing pilot NOT dispatched. Eight same-input bounded layer-domain trials on acceptedJL118 gave one whole U2119.12–U2117.13 candidate111segments/4vias,F/In2/B,zero cuts/moves;0.025mm/300000/6mm unchanged,guardPASS43s. Baseline four-layer case failed at300001expansions in2.856s; restricted case completes in4.400s. No speedup claim. Historical outer-only attempts split C2148 ground, so every original AGND group remains mandatory. Candidate is not native-accepted.

Once dispatch is available, first confirm no duplicate active run and exact c6fda679 head, then:
`gh workflow run routing-benchmark.yml --ref agent-fix/189-jl-layer-escape -f board=osc-jack-left -f local_repair=true -f local_mode=coupled`
Record run/source; own through terminal artifact reconciliation. This is read-only, with automatic restoration disabled. A positive pilot still needs full fresh capped-warning audits and all native publication gates before adoption. Local prepared pilot checker /tmp/issue189-reconcile-jl-layer-pilot.py is compiled only, not yet run on native evidence.

## Next work

1. After all five checks on each approved exact-head CI run pass, refresh current main, exact heads/reviews and concurrent refs. Integrate only after explicit approval resolves the automatic-review rejection, preserving both boards' successful copper; verify exact resulting head/current base and post-main checks. Do not claim main118/133/1402 until integration actually occurs.
2. After actual accepted core integration, rebase the saved core-supply-away-from-splits proposal with its guard and actual accepted PCB hash. Conditional ground382 addition omits the whole U4439.4 conflict, yielding93cases/118full-width outer segments,zero vias/cuts. This remains UNRUN. **Do not dispatch its existing workflow unchanged:** first require --complete-native-warnings --native-zone-batch-size16 for that case, retain all existing gates, and add argument regressions. It needs the source-scope fix3553574; the old382-only auditor is incompatible. No duplicate core writer.
3. Continue bounded native-checked JL/JR/core connectivity. Zero-edge completion, final P/EL/O/full regeneration/docs/renders remain unmet; a connected design alone is not hardware qualification. Preserve fixed318×298panel, all electrical constraints, original groups and accepted copper. No fabrication/orders/deployment; no unrelated paused watches or recurring automation.

## H1/H2 and original comparison

Both failures reproduced on1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb in hypotheses-before.txt: removed-via ghost drill exclusion and soft probing through an immovable foreign pad. Fix/regressions merged inPR190. Same-input saved native benchmark:JL old140→140 versus fixed140→139(325.514/328.869s);JR both162→162(327.293/321.953s);core both1509→1499(3545.315/4729.802s),both core candidates rejected for2AGND splits. No router speedup claim. Exact inputs/receipts are jl-benchmark.json,jr-benchmark.json,core-benchmark.json,benchmark-artifacts.json.

Remote protected branches remain8315af5(core-rrr-escalate),30db43e(jack-replace-region-2),470b3f0(jack-replace-jl-1). Additionally observed ground-domain-continuation6be7684 is an October9historical checkpoint, not a new active writer. Preserve all of them. Original JR full run38016800065 rejected at hard-coded382/38mask scope, and its receipts remain in history; corrected3553574 has32targeted regressions plus exact saved JR79/5/core382/38source-scope checks(PASS77s).


## Prepared successor and remaining native groups

Draft PR222, branch agent-fix/189-core-supply-complete, remote2a867b547d28e48fb7dbae5883c6fe9fdb7c5964 (local8f079d7, identical tree57909484751c61a410dbd5bcb46ebbf24e20c7b4), now requires complete native warning audits with batch16 for the future supply replay. New dispatch regression failed before the fix;33 targeted tests and five existing rebase-guard tests pass. No board or proposal rebasing occurred. Temporarily stacked on PR220; after authorized integration retarget/rebase onto refreshed main, preserve both accepted boards, then produce the93case/118segment proposal. Its exact source CI38022620874 is running, not passed.

Native fresh dumps partition core1402 into213AGND/80+12V/80−12V/1029signal and JR133 into23AGND/110signal/zero rails. The added net-count proof pins both fresh dump hashes. JR/core merge-preview hashes are also preserved. JL pilot still has zero workflow_dispatch runs on its branch as of04:10 UTC.
