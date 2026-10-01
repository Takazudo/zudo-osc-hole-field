# K foil-collar priority correction: separate native draft epoch

This change addresses the concrete `zones_intersect` error retained in `foil-collar-native-receipt.json`. The source now assigns priority 1 to the owned K collar zone and checks that its existing F.Cu AGND landing retains priority 0. No native rule is disabled. The compiler rejects equal same-face priorities before construction; the native constructor checks the actual retained priority and consumes the source value.

Only K is reconstructed. JL's prior candidate and proposal hashes remain historical: there is no JL refill, current-proposal replay or receipt rebinding. The corrected K board and full geometry export receive new hashes. The companion JSON records those hashes, the producer/source bindings, and the precise native outcome.

The source-declared scope is `full_refill_draft_epoch`. Its command result checks native rules, schematic parity, complete existing connectivity partitions, complete named open edges, actual AGND landing, and the full nominal dry section. It does not require the old local-only experiment to become true. The nonlocal refill deltas and source-polygon overshoot remain measured and visible; the historical failed receipt is unchanged. The result policy always leaves electrical/material/physical admission false.

The geometry dimensions and prospective material/etch intervals are unchanged. All original footprints/pads, net assignments, unretired explicit copper, board thickness and project rules remain protected by the constructor. Fixed panel hardware is not moved. Any native mask coverage is a CAD fact rather than a qualified process seal.

A complete refilled candidate is an explicit new conductor geometry. Existing electrical receipts are not reused; matched current/potential witnesses must be constructed against the fresh full export. The shoulder/flare excess needs a bounded source geometry classification, and all private collar and PCB-side access costs remain paid. The original 0.5 mΩ common, GH 0.5 A/contact, rail 1 mΩ, distribution 20 mV and full-path 0.20 V limits remain intact. Fixture isolation, contact-state/remating applicability and physical qualification stay open.

Portable tests inspect source priorities, failed-rule handling and the separation of native rule/connectivity success from local-only and physical/electrical admission. They do not manufacture native evidence when ignored artifacts are absent: actual native revalidation is **NOT RUN** in that environment.

## Recorded K-only result

Pinned KiCad 10.0.6 and the heavy guard completed successfully in 433 seconds. The corrected board has **zero rule errors and zero schematic-parity issues**. Its complete 7,354 named open edges, 551 reported warnings and existing physical connectivity partitions are unchanged. All 2,510 prior AGND members remain connected; the complete 0.200 × 0.760 mm nominal dry section passes without endpoint trimming. The 1.600 mm board stack and existing 0.150 mm outer-zone minimum remain unchanged.

The failed historical local-only conditions remain visible: outside-region filled-copper area is 0.415406613169 mm² on F.Cu and 1.54e-7 mm² on B.Cu. Collar-polygon excess is 1.290325e-7 mm², with zero intersection of the complete dry-neck guard. No area or offset tolerance is applied to turn those failures into a pass. The source explicitly declares a new complete refilled *draft epoch* for native evaluation, while fresh electrical witnesses and material/physical qualification remain open.

The new candidate SHA-256 is `a1c8f232821c778ce114f80fa12df8bd5e90b723b69617e687c1581676dacbd9`. The retained original K source, both historical failed-candidate receipts, and JL's old candidate/proposal hashes remain unchanged. The new receipt's native rule/connectivity scope passes; its local-only experiment and electrical/material/physical admission fields do not.
