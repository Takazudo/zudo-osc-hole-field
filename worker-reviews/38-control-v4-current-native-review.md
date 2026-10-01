# Fresh P v4 native chain and aggregate v6 — independent bounded review

## Conclusion

No concrete source/native/provenance blocker found in the fresh P v4 chain or aggregate v6 within their declared nominal scope. The strict current control_model_gate independently PASSed with111 dependencies. Aggregate v6's327 dependency hashes all independently match. P now uses the fresh native gate; the former P local epoch bridge is not imported or present in the v6 dependency map.

No native/DRC, full extraction or numerical solve was rerun. Guarded native execution is root's retained evidence. This review checked the actual receipts, exact source/artifact hashes, native geometry and source inventory. No shared source files were edited.

## Bare → arrays → full chain

- Bare-v4 receipt remains BARE SOURCE PLANNING ONLY with model_entry_allowed=False. Actual same-board KiCad10.0.6 DRC: zero rule errors/parity issues,430 warnings. All78 source and3 artifact digests matched.
- main-via-plan-v4 contains six array rows retaining150 sites. All six rows are exactly equal to the original v3 plan rows (whose a3848ba2… digest remains matched to the old receipt). Current plan's complete source map matches; it names the fresh bare-v4 board/export/receipt. Six arrays are TP990025/+12V,TP990027/-12V,TP990029/+5V and TP990031/33/35/AGND,25 sites each.
- Full-v4 actual same-board KiCad10.0.6 DRC: zero rule errors/parity issues,495 warnings. All344 exact source contacts are connected:214 own,127 GH,3 main. All75 declared AGND array vias connect; all150 array UUID rows match v3. Receipt preserves all prior footprints/pads/holes and reservations. Named open edges529 remain, so unfinished routing/physical acceptance is not waived.
- Independently calling the strict control_model_gate validates current source/artifact/definition/manifest/board/project/schematic/rule bindings, exact project derivation, full source/native inventory and AGND arrays, with111 dependencies. The bare planning receipt is not used as model admission and no old expected hash is replaced by a current digest.

## v3→v4 exact physical comparison

All1890 native items,813 holes and90 zones are unchanged by UUID. All65 connectivity member sets are unchanged; new feed_classification export metadata accounts for cluster differences. Main membership, outline, stackup, routing and native project rules are unchanged.

Raw PCB top-level block multisets are identical, including454 footprints,150 vias,90 zones,10 Edge.Cuts lines and all setup/general/layer blocks. Different board hashes reflect ordering/serialization, not changed physical blocks. Full companion projects differ only by meta.filename v3→v4. Array and complete ground-inventory receipt structures are identical. Added exporter fields report enabled foils/native depth/stack metadata already represented by that same native board.

This proves the compared nominal CAD geometry/source continuity; it does not rebind an old numerical matrix to new solver source or establish physical contact/material equivalence.

## Aggregate v6

PASS4143 own-source identities, same3620 convex SMD/218 drill-overlap SMD/305 PTH split. Every board's full own_source_contacts rows are exactly equal to v5. All board rows retain physical_source_support_qualified=False. P now reports `PASS complete P native prerequisite only; physical/electrical source adoption OPEN`, and the aggregate status accurately states current-native nominal geometry inventory only. Actual current P native export bytes are explicitly checked against the strict gate's bound export digest before the complete source inventory is computed. Earlier imported-helper snapshot/conflict/final checks remain.

## Exact bindings

- Bare-v4 native receipt: `b779a92009ad3ac476caa3b9d36d8eebf953d4ccf216c17a497319daa7874a76`
- Bare-v4 geometry: `26ef65b02d06cb0aefabbcb2724092b325f7b5a240bbbbe2f3bbe0b00d33f3d5`
- Six-array-v4 plan: `217e20facd66db8e9a11de9fda4a92bc9a5c15ca5abdd7c28dbfd559f58024a5`
- Full-v4 native receipt: `fc3e951718f9c48d042b61f0690679a08f5658a49d0c81386b0d0a80609a1c7b`
- Full-v4 native geometry: `977997bd280e438940f5b39916233e355f2834cb903845524bb50d33e1d693f9`
- Full-v4 PCB: `781b2e2c9b6d28c103a644281334f4dbb0b07d2455a11ad9e6bf958f301b00b0`
- Aggregate-v6 receipt: `a5bbda74de40c39dc21427aece3dc0a12857eb8c4f8257280dd8c9ab525b5d81`
- Aggregate script: `3f185a6ff7566f9a4f99af6837fba5bfc8abb031fb2067e925476fcc4d58a359`
- Strict control_model_gate: `5c9c342ce453fb023f7f91ff15ec3ee8a5d24d9f99834ac57da2bd68f66f9585`

The prior v3 and aggregate-v5/bridge receipts remain historical. Source/current/contact/process/material/3D dual-primal/joined common+positiveK electrical acceptance remains OPEN. `pnpm circuit:check` passed before writing this note; no heavy checks were run.
