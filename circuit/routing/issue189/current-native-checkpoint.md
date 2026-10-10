# Issue189 exact continuation — 2026-10-10

Issue189 is OPEN and connectivity remains incomplete. No fabrication, release, deployment or hardware qualification is authorized. Incremental OSC merges were explicitly authorized during this session; retain all exact-head native/CI/integration gates. Do not restart unrelated watches or change credentials/toolchains.

## Accepted main

Main **a0f240887f80786e1df1791fe15b5074b2af73d7**, tree **7d5dc4d0737441ecb5e231a95e151609110f2455**: **JL117 / JR130 / core1402**, native DRC/parity0/0. PR231 strict cut audits, PR230 JL117, PR224 JR130 and PR234 current documentation are merged. Every PR passed all five exact-head checks. Mained6f158 CI38041900562 passed all five; current post-doc main CI38044061215 is pending. PR234 actual tree matches preview and changes only two documentation pages; all board bytes unchanged.

Board SHA256:
- JL e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107
- JR e06b7471ddc8f5c8c498c5eb5bf8655cc6de539e92826a5701cf1de06356e136
- core fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10

JL117:103signal/14AGND/0rails,30564segments/2861vias. JR130:107signal/23AGND/0rails,48445segments/3129vias. Core1402:1029signal/213AGND/80+12V/80−12V,123905segments/9646vias. The paired jack merge preserved every unrelated board path including core/P/EL/O. See paired-jack-board-preservation.json.

## JR129 fully native accepted, unmerged pending exact-head CI approval

PR232, branch `agent-fix/189-jr130-rb4615-via-branch`, source2a10cae7ef3bd7d4df8e9500c25cada930419432, bot **7a245c751e1bcf8e15d7d1e49aaf6c324a5b75f4**. Native38041389680 and sourceCI38041392709 SUCCESS. **BotCI38042777010 action_required**; user asked once and has not replied. Earlier09:14approval covered only PR230/224; do not reuse it.

Artifact11665973838, ZIP SHA09a205f6fad78aabc490ee07124c827a18cacfde575cc1afdb2b8d3bad47f2d1. Independent full reconciliation PASS121s:130×3→129×3/fresh129×3,51571uncut retained/3exactcuts/27new,1080nonrouting unchanged,0DRC/parity/nooriginalsplits/newwarningidentities,520complete findings,24hole identities per side,27copper fixtures,34pairedzone fixtures. Published/fresh PCB9e164f9e8e23a5c3911d117fd08973fc877e5f2f382be20500b8e01040b20a55; replay5d7aa24e5927e9f2148ccc3ac1a19eec7253bc66a67e0dc6c641da7ea52ecd7c. No optional publication compaction/refill; ordinaryfreshPASS.

After user approval, query actual bot head and all5exact checks. Refresh actual main via `git/ref/heads/main` (PR base.sha may be stale), fetch bothrefs, recompute `git merge-tree --write-tree BASE HEAD`, require only expected JR PCB/receipts and preserve JL/core/P/EL/O. Then authorized ready+merge with expected head, verify actual merge tree and post-mainCI. Do not push older local2a source over the bot.

## Core worker terminal: REJECTED, not an audit-only continuation

PR222/source47bb19a42f6612a114e4aff51c4b120301fe5e71/run38023611361 timed out exit124 during zone audit. Artifact11666004488,517575493bytes, ZIP0855bdbccdc250a3a273511b8d519cedc3f110a86cc0c887ac08a5f94596d8e4. Local `/tmp/issue189-core-supply-terminal.zip`; do not extract all2.3GB with1.5GBfree.

Saved native snapshots1402×3→1311×3/fresh1311×3,0DRC/parity. However **two original AGND groups split**:1988→1985+3 (C4170.2/U4145.12/C4171.2),9→7+2 (C4270.2/J900155.2). Raw promotion gate rejects both merge and fresh. No completed warning proof, publication or canonical adoption. Completing the timed-out audit would not repair these splits; do not resume that unchanged candidate or repeat it with a larger budget.

Beforeb9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66; merge/fresh4f90bfc16d5e338cc31adc3a41f0da8ff8f289a24b963ab8f9c9caf9d98cec10. Source-bound proposal56121445db0986dbf846fd4e7f95339bd195f101ae876b8106353f4112b1564d:93wholecases,118outer0.25mmsegments,0vias/cuts. All133551accepted objects and3807nonrouting objects must remain. Zone601e02b2-8ccb-5c28-83e5-03789d47fbbd has146/230completed paired batches (1833selected artwork);84remaining for this zone, not necessarily entire audit.

Independent negative checker `/tmp/issue189-reconcile-core-supply-partial.py` runs through heavy guard, verifies exactZIP/snapshots/retention/rejection and completed fixture hashes; success proof `/tmp/issue189-core-supply-partial-proof.json`. It does not claim unrun native reconstruction/full warning audit. Initial checker correctly failed an acceptance assertion, exposing these splits. Negative reconciliation PASS197s (guard verdict=PASS). All completed146fixture/report hashes and ordered progress verified; full audit remains incomplete.

New isolated branch `agent-fix/189-core-supply-rejection-evidence`, current **aaa2649936cd2782746d11c44e6dfe9f4fc8a964**, `/workspace/issue189-core-supply-complete`. It preserves old PR222/source47bb, merges accepted main, adds exact rejection evidence and rejects structurally ineligible outcomes before expensive supplemental audits. Four regression cases RED→GREEN;33affected tests and circuit check PASS. No native gate weakened: eligible candidates still need every complete warning audit. Pushed draft **PR235**; exactCI **38044313314** pending. Worktree clean. Do not merge before all five exact checks and fresh current-main preview.

Next routing work: identify and repair or omit whole supply cases causing these two original-group splits, using saved native memberships/geometry. Proximity is not causal proof. Require bounded native snapshots showing original groups preserved before full warning/publication checks. Current core1402 remains canonical. No active core native worker; no duplicate dispatch.

## JL U8202 full candidate rejected and rolled back

PR233 branch `agent-fix/189-jl117-u8202-via-branch`, current729dff64c507f6014e05f302be6b880f76ca75fa. Fullsourcec0665fffed85e4790aaa2ffb921cf8334ee6c0f0/run38041226566; workflowSUCCESS means receipt generation, not acceptance. Artifact11666153064 ZIP4c09d2684114b9ca8bb39694406ccbf1bfc55d03b6570142e4b49892029d3f3f. Independent rollback reconciliation PASS104s.

Initial186new/3cuts candidate open117,0DRC/parity but −12V270→264+6 isolates C8122.1/C2322.1/U8106.4/C8124.1/U2304.4/U8105.4. Partial signal rollback open116 caused90native errors. Finalmerge/fresh byte-identical acceptedJL117e984...,33425objects,0cuts/additions,0DRC/parity. Full warning audits NOT RUN (actual cuts differ after nooprollback). No copper adopted. Preserve remote bot negative receipts merged into729; no unchangedproposal retry. Next candidate must preserve/restore this exact six-pad −12group plus AGND/signal boundaries.

## Original H1/H2 and identical-input benchmarks

Both regressions failed on1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb and pass after mergedPR190: removed-via ghost drill cache (H1), foreign fixed pad softened by probe (H2). Tests `ObstacleTransactionTests.test_removed_via_hole_is_rebuilt_and_rollback_restores_it` and `test_soft_probe_keeps_fixed_foreign_pad_hard`. See hypotheses-before.txt and benchmark JSON evidence.

Identical saved native inputs:
- JL37824198833:old140→140,fixed140→139;325.5136/328.8692seconds.
- JR37824203279:both162→162;327.2931/321.9534seconds.
- core37824207235:both1509→1499 but both rejected2AGNDsplits;0acceptedgain;3545.315/4729.8022seconds.
No speedup claim. All saved artifact/input identifiers in benchmark-artifacts.json and jl/jr/core-benchmark.json. Later same-input portable screens reproduce exact outcomes/diagnostics/proposals; timings excluded.

## Environment and retained evidence

Startup loader fully consumed earlier; do not rerun unless environment replaced. Native KiCad10.0.6 local image unpack cannot fit32GB; verified twice. No Docker fallback/retry. Remote pinned native toolchain required. Heavy local runs use `bash /home/agent/.codex/scripts/heavy-guard.sh -- COMMAND`; Python `/workspace/zudo-osc-hole-field/.circuit-cache/route-venv/bin/python`. Never claim unrun tests passed.

Own ZIP archives and successful boards remain. Only byte-verified duplicate audit extractions were removed (core1402 and JR131); receipts retained. Do not remove canonical or other-session work. No Git LFS. Previous detailed checkpoint retained separately; this current checkpoint supersedes its stale worker/approval state.
