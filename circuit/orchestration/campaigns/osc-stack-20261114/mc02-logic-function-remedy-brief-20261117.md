# MC02 logic-function remedy preparation brief

Task `MC02-R-LOGIC`, preparation attempt `20261117-source-1`. **PREPARATION ONLY; geometry, routing and hardware execution NOT ADMITTED.**

Engineering source `2c53715d49a4a7639723595590d1fd4eeb3a3c1f`; prepared from local review composition `9cf26f4f81e3e5ed31756c3fbb2b73f84e26fb7b`. This brief covers exactly six SN74HC00DR and two SN74HC74DR packages from the retained 26 unplaced ICs, all on K. It groups source evidence for review; it does not declare a relocation set or expand the DS-88 placement search.

## Exact package/unit and signal interfaces

Every package remains in its source `ENV_CORE` instance. Supply units are retained at pin 7=AGND and pin 14=+5V. They are omitted from the signal table only for readability; they remain part of each complete package. Units and local net names must not be reassigned across instances.

| Ref | Instance / MPN | Source unit role | Pin → signal-net mapping |
| --- | --- | --- | --- |
| `U4324` | `E3` / `SN74HC00DR` | 1: `envelope:NAND55` | `1→/E3/STAGE_FALL; 2→/E3/FALL; 3→/E3/L055` |
| `U4324` | `E3` / `SN74HC00DR` | 2: `envelope:NAND57` | `4→/E3/STAGE_FALL; 5→/E3/STAGE_FALL; 6→/E3/L057` |
| `U4324` | `E3` / `SN74HC00DR` | 3: `envelope:NAND58` | `9→/E3/L057; 10→/E3/RISE; 8→/E3/L058` |
| `U4324` | `E3` / `SN74HC00DR` | 4: `envelope:NAND60` | `12→/E3/L055; 13→/E3/L058; 11→/E3/STAGE_HIGH` |
| `U4417` | `E4` / `SN74HC00DR` | 1: `envelope:NAND19` | `1→/E4/L018; 2→/E4/L016; 3→/E4/L019` |
| `U4417` | `E4` / `SN74HC00DR` | 2: `envelope:NAND21` | `4→/E4/START; 5→/E4/START; 6→/E4/L021` |
| `U4417` | `E4` / `SN74HC00DR` | 3: `envelope:NAND22` | `9→/E4/L021; 10→/E4/L019; 8→/E4/D_RISE` |
| `U4417` | `E4` / `SN74HC00DR` | 4: `envelope:NAND23` | `12→/E4/RISE; 13→/E4/TOP; 11→/E4/L023` |
| `U4524` | `E5` / `SN74HC00DR` | 1: `envelope:NAND55` | `1→/E5/STAGE_FALL; 2→/E5/FALL; 3→/E5/L055` |
| `U4524` | `E5` / `SN74HC00DR` | 2: `envelope:NAND57` | `4→/E5/STAGE_FALL; 5→/E5/STAGE_FALL; 6→/E5/L057` |
| `U4524` | `E5` / `SN74HC00DR` | 3: `envelope:NAND58` | `9→/E5/L057; 10→/E5/RISE; 8→/E5/L058` |
| `U4524` | `E5` / `SN74HC00DR` | 4: `envelope:NAND60` | `12→/E5/L055; 13→/E5/L058; 11→/E5/STAGE_HIGH` |
| `U4526` | `E5` / `SN74HC00DR` | 1: `envelope:NAND66` | `1→/E5/RISE; 2→/E5/TOP_RAW; 3→/E5/L066` |
| `U4526` | `E5` / `SN74HC00DR` | 2: `envelope:NAND68` | `4→/E5/HOLD_N; 5→/E5/L066; 6→/E5/HOLD_ENABLE` |
| `U4526` | `E5` / `SN74HC00DR` | 3: `envelope:NAND69` | `9→/E5/CURVED; 10→/E5/CURVED; 8→/E5/L069` |
| `U4526` | `E5` / `SN74HC00DR` | 4: `envelope:NAND70` | `12→/E5/READY; 13→/E5/RISE; 11→/E5/L070` |
| `U4527` | `E5` / `SN74HC00DR` | 1: `envelope:NAND71` | `1→/E5/L070; 2→/E5/L070; 3→/E5/L071` |
| `U4527` | `E5` / `SN74HC00DR` | 2: `envelope:NAND72` | `4→/E5/L071; 5→/E5/L069; 6→/E5/L072` |
| `U4527` | `E5` / `SN74HC00DR` | 3: `envelope:NAND73` | `9→/E5/L072; 10→/E5/L072; 8→/E5/RISE_LINEAR` |
| `U4527` | `E5` / `SN74HC00DR` | 4: `envelope:NAND74` | `12→/E5/L071; 13→/E5/CURVED; 11→/E5/L074` |
| `U4623` | `E6` / `SN74HC00DR` | 1: `envelope:NAND51` | `1→/E6/L050; 2→/E6/BOTTOM; 3→/E6/L051` |
| `U4623` | `E6` / `SN74HC00DR` | 2: `envelope:NAND52` | `4→/E6/L051; 5→/E6/L051; 6→/E6/L052` |
| `U4623` | `E6` / `SN74HC00DR` | 3: `envelope:NAND53` | `9→/E6/L052; 10→/E6/L021; 8→/E6/L053` |
| `U4623` | `E6` / `SN74HC00DR` | 4: `envelope:NAND54` | `12→/E6/L053; 13→/E6/L053; 11→/E6/D_COMPLETE` |
| `U4433` | `E4` / `SN74HC74DR` | 1: `envelope:LOOP_SYNC1` | `1→/E4/READY; 2→/E4/LOOP_RAW; 3→/E4/CLOCK; 4→+5V; 5→/E4/LOOP_SYNC; 6→None` |
| `U4433` | `E4` / `SN74HC74DR` | 2: `envelope:LOOP_SYNC2` | `13→/E4/READY; 12→/E4/LOOP_SYNC; 11→/E4/CLOCK; 10→+5V; 9→/E4/LOOP; 8→None` |
| `U4635` | `E6` / `SN74HC74DR` | 1: `envelope:TOP_SYNC2` | `1→/E6/READY; 2→/E6/TOP_SYNC; 3→/E6/CLOCK; 4→+5V; 5→/E6/TOP; 6→/E6/TOP_N` |
| `U4635` | `E6` / `SN74HC74DR` | 2: `envelope:BOTTOM_SYNC1` | `13→/E6/READY; 12→/E6/BOTTOM_RAW; 11→/E6/CLOCK; 10→+5V; 9→/E6/BOTTOM_SYNC; 8→None` |

## Declared decouplers and shared source anchors

These eight capacitors are explicitly linked by `decouples_ref`, not inferred from proximity. They are source-associated parts to review with each package, not authorization to move them or to change power/AGND paths.

| IC | Declared decoupler | Project MPN | Supply connection |
| --- | --- | --- | --- |
| `U4324` | `C4341` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4417` | `C4434` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4524` | `C4541` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4526` | `C4543` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4527` | `C4544` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4623` | `C4640` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4433` | `C4450` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |
| `U4635` | `C4652` | `GRM188R71H104KA93D` | +5V / AGND; source generator specifies 100 nF |

The following exact reset/clock interface anchors are source-defined dependencies, not additional unplaced packages or an automatic move set. Each packed HC14/HC74 package may also serve other units. A later design proposal must account for the whole package and stationary endpoints rather than split units to fit.

| Instance | Source clock/reset anchors (ref:unit role) |
| --- | --- |
| `E3` | `R4332:0 envelope:R_POR_PULL`; `C4308:0 envelope:C_POR_DELAY`; `D4304:1 envelope:POR_DISCHARGE`; `R4333:0 envelope:R_CLOCK`; `C4309:0 envelope:C_CLOCK`; `U4312:2 envelope:POR_INVERT`; `U4312:3 envelope:POR_BUFFER`; `U4312:4 envelope:CLOCK_OSC`; `U4330:1 envelope:RESET_SYNC1`; `U4330:2 envelope:RESET_SYNC2` |
| `E4` | `R4432:0 envelope:R_POR_PULL`; `C4408:0 envelope:C_POR_DELAY`; `D4404:1 envelope:POR_DISCHARGE`; `R4433:0 envelope:R_CLOCK`; `C4409:0 envelope:C_CLOCK`; `U4412:2 envelope:POR_INVERT`; `U4412:3 envelope:POR_BUFFER`; `U4412:4 envelope:CLOCK_OSC`; `U4430:1 envelope:RESET_SYNC1`; `U4430:2 envelope:RESET_SYNC2` |
| `E5` | `R4532:0 envelope:R_POR_PULL`; `C4508:0 envelope:C_POR_DELAY`; `D4504:1 envelope:POR_DISCHARGE`; `R4533:0 envelope:R_CLOCK`; `C4509:0 envelope:C_CLOCK`; `U4512:2 envelope:POR_INVERT`; `U4512:3 envelope:POR_BUFFER`; `U4512:4 envelope:CLOCK_OSC`; `U4530:1 envelope:RESET_SYNC1`; `U4530:2 envelope:RESET_SYNC2` |
| `E6` | `R4632:0 envelope:R_POR_PULL`; `C4608:0 envelope:C_POR_DELAY`; `D4604:1 envelope:POR_DISCHARGE`; `R4633:0 envelope:R_CLOCK`; `C4609:0 envelope:C_CLOCK`; `U4612:2 envelope:POR_INVERT`; `U4612:3 envelope:POR_BUFFER`; `U4612:4 envelope:CLOCK_OSC`; `U4630:1 envelope:RESET_SYNC1`; `U4630:2 envelope:RESET_SYNC2` |

`envelope.py:174–190` defines the source reset/clock/state structure: a 100 kΩ / 1 µF POR network with discharge path and Schmitt stages; a 47 kΩ / 1 nF C0G clock network; RESET_SYNC1/2 producing READY; paired synchronizers for GATE/ASR/LOOP and TOP/BOTTOM; GATE_PREVIOUS and RISE/HOLD/FALL state flip-flops. The POR network is explicitly an initial proposal, not a guaranteed brownout supervisor. RC values alone do not establish actual clock frequency, skew, jitter or setup/hold margin.

U4433 contains both E4 LOOP synchronizer stages: LOOP_RAW → LOOP_SYNC → LOOP, sharing CLOCK and READY. U4635 contains E6 TOP_SYNC2 and BOTTOM_SYNC1 in one package, so its function boundary crosses two synchronizer chains; the counterpart stages cannot be omitted from later review. CLOCK/READY are shared interface nets, not permission to move the clock/reset circuitry. The HC00 role names in the table bind the original combinational network, including state-high masks, HOLD_ENABLE and READY-gated linear/curve paths.

## Existing executable invariants and their limits

- `envelope_logic.py` defines one-hot RISE/HOLD/FALL (all zero means IDLE) and START priority. `tick()` asserts at most one next state. `captured_logic()` recovers NAND and flip-flop connections from the packed physical pin numbers; its flip-flop extraction alone is not a metastability or propagation-delay test.
- `EnvelopeContract.test_truth_table_and_real_nand_capture` in `test_envelope.py:28–44` enumerates four states, three modes and five Boolean inputs (384 combinations). It compares `tick()` with expected transitions and evaluates the actual captured NAND network, requiring one expected active next-state signal or none for idle. This proves the tested Boolean/state correspondence only; it does not apply real delays or qualify a moved physical implementation.
- `test_physical_logic_domains_and_stage_masks` at lines 54–60 checks HC supply pin mapping, comparator supply scope, NOT_RISE/NOT_FALL stage-mask inputs and unique logical keys. `test_entire_instrument_references_unique` checks instance designator uniqueness. These remain applicable exact-source regression contracts for any later admitted source change.
- `envelope.py:134–143` creates per-package local decoupling and retains instance islands. Existing source values and declared decoupling association must not be turned into an invented placement distance.
- No incremental trace/via, propagation-delay, clock-skew, setup/hold or synchronizer reliability budget is assigned by this brief. The listed source/test scope cannot supply such physical acceptance limits.

## Prepared remedy and missing decisions

The next source-only comparison should list alternative review boundaries for each packed package, identify which source-associated parts remain stationary, and preserve every signal interface and complete-package obligation. For the eight ICs, compare source net/role tables and declared decouplers before proposing any geometry. A later qualified design authority must specify actual voltage/temperature/load corners, clock/reset conditions, permitted incremental timing/parasitics, return/decoupling constraints and the applicable validation sequence. Unused outputs and NC treatment must be carried from the full source, not invented from abbreviated diagram labels. No candidate position, layer, face, part or routing change is selected here.

## Authority, write scope and bounded execution proposal

Campaign `osc-stack-20261114`; parent #362/#365/#367 and DS-88/DS-97/DS-133. Current x0x WSL coordinator performs Moya's role. The author owns only this new brief. The final-source sequencing proposal remains pending; this brief assumes neither its approval nor release of DS-06 or the owner DRC/fill/adoption/manufacturing holds.

Allowed follow-up is source-only correspondence checking and preparation of a function-boundary comparison. A future job could be proposed as one isolated checkout, one CPU, 512 MiB, zero swap, 64 PIDs, setup 60 s + analysis 480 s + cleanup 60 s, with no automatic retry. These are draft ceilings, not actual measured admission or a launch command. Fill exact source, command, model/reviewer selection evidence, resource fingerprint and cleanup/recovery contract before dispatch. Keep shared heavy exclusion when applicable; do not infer extra host capacity from another worktree. No native budget is granted.

On changed inputs, ambiguous identity or an unsupported physical requirement, preserve the exact discrepancy and return it to the coordinator; do not retry identical searches or overwrite another writer. This document produces no background job, CAD checkpoint or artifact upload. Required fields for later geometry/hardware execution remain unfilled, so it is NOT DISPATCH-READY. Independent review is required before its prepared boundary is used.

## Acceptance and observed preparation checks

Acceptance: exact eight-package set and six/two split; unit/role/pin-net table correspondence; exact declared decouplers; correct reset/clock anchor identities; no invented physical timing budget or implied move/adoption. Future integrated-source/native obligations remain separate.

Pre-edit `pnpm circuit:check` passed (84 records; manual inventory, 445 declared placements unverified). Source fingerprints, eight-package membership, unit supplies, eight declared decouplers and reset/clock anchor sets were checked from the pinned source during preparation. Post-edit component validation and diff checks are recorded by the coordinator/author. Native/regeneration, placement search, routing, DRC/fill, physical checks and hardware adoption: NOT RUN. Existing unchanged aggregate evidence is not repeated.

## Immutable source fingerprints

- `design/reports/io-partition.json` SHA-256 `37a773282d723d7f689d1e6cf009e4edd1947827a5ee45f0051e42cd4e907a0b`.
- `design/stack/geometry/links/link-gate.json` SHA-256 `1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d`.
- `design/spec/modules/envelope.py` SHA-256 `015b02c5d84550e19bf92b9ec838a43b255a728e02de1e562e855ba632fc2ee5`.
- `design/spec/modules/envelope_logic.py` SHA-256 `860cb283d2712da94bca2b7e43148f0306fb6c35ba272f8efd3df947d36c6d73`.
- `design/spec/modules/test_envelope.py` SHA-256 `f7fd81ad2902c32d0951c4c7f08ef7a963a3dfb5b54a0768fd38d5e3ab682dfb`.
