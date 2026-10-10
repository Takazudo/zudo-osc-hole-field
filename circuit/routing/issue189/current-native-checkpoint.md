# Issue189 checkpoint — 2026-10-10 04:20 UTC

Issue189 remains OPEN. PR220 merged at9f953c53e9b777ba517d7f0aa29d7c83a9139f1d and PR218 merged atd25854092d89fa1253d05c95c21a225629f8c3f9 after all five exact-head checks passed for each and explicit OSC merge authorization was supplied. The earlier automatic-review rejection is resolved; retry succeeded without changing gates. Main now has JL118/JR133/core1402. Actual main PCB hashes independently match the accepted worker bytes:
- JL:a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a
- JR:22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd
- core:fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10

Post-main CI38023410816 atd258540 is RUNNING (documentation and both jack DRC gates passed; Python/core DRC pending). Do not claim its final result yet. CLI connection now succeeds without credential/config changes. No unrelated projects, watches, branches or fabrication actions were touched.

## Sole active routing runs — do not duplicate

- Core38023611361, source47bb19a42f6612a114e4aff51c4b120301fe5e71, branchagent-fix/189-core-supply-complete, draftPR222. Native adoption replay of93whole supply cases/118full-width0.25mm outer segments, zero vias/cuts. Input core hashfa60b4e...; proposal SHA25656121445db0986dbf846fd4e7f95339bd195f101ae876b8106353f4112b1564d. Guarded rebase PASS18s retained every133551current core copper object, including all382accepted ground additions, and excluded the entire U4439.4 case for0.194707mm separation. All33targeted regressions and five rebase guards pass. Complete warning audits with batch16 are mandatory. Native acceptance and output counts are UNKNOWN. Own through terminal artifact validation; workflow success alone is insufficient.
- JL38023623800, sourcec6fda679ba8cb58b9b1e3a85b1db2b08f7d0bda9, branchagent-fix/189-jl-layer-escape, draftPR221. Read-only coupled pilot, no automatic restoration. One whole U2119.12–U2117.13 candidate111segments/4vias onF/In2/B; inputJL118 hashabove. Proposal46c07604968b3e84a870efe4c2d2888ae9d5ccb435d8238f882f704296765844. Native result UNKNOWN. Historical outer-only candidates split C2148 AGND; every original group remains mandatory. Prepared local checker /tmp/issue189-reconcile-jl-layer-pilot.py is compiled but UNRUN; invoke with actual run/artifact/SHA. Even a positive raw pilot still requires full source-bound warning audits and fresh adoption.
- No JR routing worker is active. All earlier native workers are terminal. Active-run list was empty before these two dispatches.

PR222 remote47bb19a tree3dec9728f5ef29d0bdc75528873a87f147c4db1e matches local53745d4; remote preserves prior2a867b5 and integratedd258540 ancestry. Retargeted to main. Six source/proposal files differ; all PCB bytes equal integrated main. Require checks on each final bot head before later integration. Never overwrite successful copper with stale branches.

## Completed independent proof

JR full run38018592247/source3553574/bota4ec09b:134x3→133x3/fresh133x3,51177old retained+74segments/5vias,0cuts,1080nonrouting unchanged,0DRC/parity/no splits/new warnings. All24hole identities,79copper fixtures and50paired zone fixtures checked;520original findings retained. Artifact11657699680 SHA2560f9d6751e37ceebf1a889e2d1378fffd5a2a0cd030a9d9b6b920a76efa4de50f. IndependentPASS117s. Full proof/checker in jr-neighbour-return-repair/full-adoption-*; ci-a4ec09b.json records all-fivePASS38020346206.

Core full run38011194282/source44d1151/botcebde33:1441x3→1402x3/fresh1402x3/native publication refill1402x3,133169old retained+344segments/38vias,0cuts,3807nonrouting unchanged,0DRC/parity/no splits/new warning identities. All1407hole identities,382copper fixtures and42paired zone fixtures checked.619original findings retained, complete1827observations each. Artifact11658776367 SHA2561ed58a9cd4c5796654a9e3e5c9b6e1c1129c353f3451e04c990b95032012479f. Native filledb9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66; compact publishedfa60b4e... has verified native refill equivalence. IndependentPASS332s. Full proof/checker pointers in core-batched-native-accepted/, ci-cebde33.json records all-fivePASS38021229431.

Remaining native groups: JL103signals/15AGND/0rails; JR110signals/23AGND/0rails; core1029signals/213AGND/80+12V/80−12V. Exact fresh dumps are pinned in issue189-accepted-native-net-counts.json.

## Continuation and constraints

Follow both current runs and post-main CI. Download complete terminal artifacts, pin ZIP/source/output/replay hashes, independently verify settled/fresh native topology, original groups, complete raw warning fixtures/context, zero DRC/parity errors and all retained copper. For successful adoption verify published bot PCB hash and exact final-head CI before authorized integration; for rejection preserve receipts and do not promote candidate copper. One writer per board.

H1/H2 both reproduced on1fe06ad5: removed-via ghost drill exclusion and soft probing through fixed foreign pads. Fix/regressions mergedPR190. Identical-input benchmarks: JL old140→140 vsfixed140→139(325.514/328.869s); JRboth162→162(327.293/321.953s); coreboth1509→1499(3545.315/4729.802s), both rejected for2AGND splits. No speedup claim. Immutable inputs/receipts remain in benchmark-artifacts.json and jl/jr/core-benchmark.json.

Preserve318×298fixed panel, all electrical constraints,438locked centres, successful copper and original pad groups. Full zero-edge connectivity and final P/EL/O/full regeneration/docs/renders remain unmet. Keep189OPEN. No fabrication/order/deploy/hardware-qualification claim. Separate ZFB prototype remains unmerged.

Local pinned KiCad10.0.6 unpack blocker remains; do not retry Docker cleanup/reconfiguration or substitute9.x. Cloud native runners supply the pinned toolchain. Runtime startup loader was fully consumed earlier in this unchanged session; do not rerun it.
