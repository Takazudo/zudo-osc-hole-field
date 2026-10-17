# Stage 3 independent occupied-volume reservation study

No new rear area can yet be called qualified free space for the whole instrument. The study distinguishes actual **source declarations**, **conditional engineering envelopes**, and **unknown installed volumes**. It does not turn a blank drawing region into capacity, transfer an old board to a new depth, or adopt an architecture.

Reproduce with `python3 scripts/architecture278/implementation/stage3_reservations.py --check`. The editable candidate input is `reservations-input.json`; `reservations-report.json` records all source hashes, the 28 function inventories, historical envelopes, geometry queries, projection counts and actual-pad locality rankings. Seven focused tests cover missing free-space evidence, unchanged depth/service assumptions, the old-board extraction obstruction, the board notch, static versus cover-removed space, inventory completeness and pad-based locality. No native, routing campaign, fabrication or physical test was run.

## What the other 28 functions actually occupy in the retained source

They total **4,766 retained physical packages** across their old boards. Twenty-four functions have **2,572 packages on K**, the old monolithic rear board. B1/B2/X1/X2 have no source K packages: together they have 166 JL and 18 P packages. They remain real front electronics/carrier/harness populations; zero K packages does not make these functions absent.

The complete old K placement contains 3,385 packages: 2,572 for the other functions, 770 for the five oscillators, 30 for shared references, and 13 POWER packages. The generator joins each retained Ref to its function, board, side and actual courtyard placement. Per-function envelopes are conservative bounds around those source courtyards, not manufacturer solids. All 28 functions and all 438 fixed panel centres remain present.

The canonical K outline is the orthogonal polygon [4,8]→[314,8]→[314,246]→[258,246]→[258,292]→[4,292], with projected area 85,464 mm². Its old front/back board planes are 100/101.6 mm behind the panel. The retained 5 mm rear component allowance reaches 106.6 mm; the old mechanical proposal used a 120 mm inner enclosure. This source evidence cannot be imported silently into the candidate's middle50/core69.2/cover105 mm arrangement.

Two concrete conditional conflicts follow if that old K board is retained:

- A new core withdrawing from 69.2 mm through a 40 mm stroke crosses the old K plane at 100..101.6 mm wherever their projections overlap. Including the 18 mm handle projection sweeps to 127.2 mm. Cover removal supplies external workspace; it does not remove the intervening K board.
- The old back-component allowance extends 1.6 mm beyond the candidate's 105 mm inner cover, before extra clearance or tolerance. This is a conflict of proposed envelopes, not a measurement of actual parts. The old K board also prevents calling the 69.2 mm candidate board rear-most in those overlapping regions.

Canonical files remain unchanged and KEEP_K1402_INCUMBENT remains the incumbent. The candidate may propose a new distribution, but must explicitly account for all whole packages, units, bypasses, supports, connectors and service volumes. Keeping the incumbent source unchanged does not mean it physically coexists with the proposed candidate stack.

## Region qualification

| Region/evidence | Classification | Permitted conclusion |
|---|---|---|
| Fixed hardware centres, source package identities and retained XY courtyards | Known source declarations | Bind new proposals to these inputs; do not claim installed solids |
| Existing candidate rear boxes, middle/core/cover datums and service stroke | Conditional engineering reservations | Compare source proposals with unchanged baseline assumptions |
| Old K board at100..101.6 mm and its original package courtyards | Historical occupied source envelope | If retained physically, reject intersecting service sweeps; it is not a new-stack assignment |
| Unassigned space for the other28 at the candidate stack | UNKNOWN | Do not approve placement or infer capacity from absence of objects |
| Historical lower-right K notch x258..314/y246..292 | UNKNOWN in the new architecture | Absence of old K substrate alone does not qualify this as free space |
| Installed volume extending beyond105 mm | Outside current installed enclosure proposal | Revise geometry explicitly; cover-removed service space cannot justify installed protrusion |
| Certified free region | None | `qualified_free_regions` stays empty; mutations claiming otherwise are rejected |

The input evaluates genuinely changed direct-mating proposals, not another fixed-slot permutation: a 97×115 mm core at [5,82], its full withdrawal volume, a relocated103×115 mm right-side core at [211,130], and a new vertical signal bank x92..107/y80..180. Every inside-envelope candidate is UNKNOWN with respect to unassigned other-function space. The core-removal proposal additionally intersects the historical K board if that board is retained. These findings do not prove the new architecture infeasible; they identify exactly which missing occupancy evidence prevents acceptance.

Rear enclosure XY dimensions and card geometry remain engineering variables, subject to the fixed front centres. A region outside the current projection requires an explicit revised lateral enclosure/carrier proposal; it is not a permanent physical prohibition or an automatic request for owner permission.

## The 350 unresolved hardware projections

The current independent assembly screen's 350 XY projection pairs comprise 246 jack, 52 pot, 32 octave-selector, 19 toggle and one button overlap. They are not 350 proven collisions. The relevant packages may be on opposite PCB faces or different depths. The one middle-header/R1616 projection also remains a face/board-detail check, not a same-face packing collision.

The retained selector source supplies conditional installed body/tail intervals 8.5..20 mm for O1/O3/O5 and21.5..33 mm for O2/O4. Other front placements still use conditional datums. Exact package/body/lead/tail/plug/latch/optical/tool solids must use one common face datum, with tolerances and an explicit provenance for each height. A PCB separating nominal bodies does not by itself establish clearance from through tails, solder, cable bends, latches, optical paths or guide hardware. No projection is promoted to a physical PASS merely because its PCB-plane numbers differ.

The smallest useful evidence increment is a per-part or defensibly conservative per-family envelope table: fixed datum, side, XY extent, occupied Z interval, terminal/solder reach, tolerance, and source/status. Apply that table to each of these pairs and to the shared middle island, DIN flanges/tails, power straps and extraction/tool corridors. Exact-source unknowns stay UNKNOWN; explicit procurement bounds stay conditional until reconciled.

## Local electrical placement refinements

The compact arrangement preserves eight cluster memberships and six trim tool reservations, but membership alone does not establish electrical locality. Actual-pad distances expose the highest priorities:

| Bypass | Exact IC supply pad | Direct source-pad distance |
|---|---|---:|
| C1129 | U1105 pin16, +12V | 20.286 mm |
| C1148 | U1115 pin4, +12V | 19.526 mm |
| C1149 | U1115 pin11, −12V | 18.419 mm |
| C1130 | U1105 pin3, VEE5 | 17.597 mm |

These are geometric comparisons, not permissible limits or routed loop lengths. Repack each complete capacitor immediately beside its actual supply pad, giving its return pad a short connection to the same local reference plane. Preserve all source package units, NCs, supply pins, spare amplifiers and six trim/service reservations. Move whole packages and their complete associated circuitry; do not use a single detached resistor to improve a remote-path score.

Further source spans requiring attention are VEE5 R1148:2→U1105:3 (43.313 mm), EXPO_SUM R1147:2→U1105:15 (24.071 mm), LINEAR_REF U1105:13→R1154:1 (23.203 mm), SCALE_PIN U1105:14→R1152:1 (22.401 mm), SINE_GAIN_SUM R1199:2→RVO1111:2 (18.704 mm), TIMING_CAP U1105:11→C1111:1 (12.513 mm), and HF_PIN U1105:7→RVO1109:1 (7.963 mm). Reposition the complete tune/octave/VEE group beside the core's relevant pins and arrange timing/summing components around those pins. This can change connector and remote-path geometry, so complete path/return/capacitance budgets must be recomputed afterward. No remote feedback or unshaped waveform transport is introduced.

The study gives ranked placement targets; it does not modify candidate or canonical component coordinates and does not claim a source-backed maximum local-loop distance. Ground return planes/vias and shared impedance remain unextracted.

## Smallest next source work and authorization boundary

1. Join all other28 whole-package/units/NC/bypass assignments to candidate boards and conservative occupied volumes in the retained50/69.2/105 mm stack. Include the separate13POWER packages, shared services, supports, harnesses and removal corridors. For the four front-only functions, reconcile their old front PCB/carrier datums with the new front-board proposal rather than inventing rear packages.
2. Produce at least a conservative disjoint volume reservation for every function before consuming apparent empty space for a changed OSC outline, bank or card origin. Same XY may be reused at different depths only with explicit nonintersecting solids and an unobstructed service sequence. Source courtyard area alone cannot supply that proof.
3. If the bounded O1 test piece intentionally omits neighbors, inventory their conservative surrogates and scope the result to that isolated candidate. It cannot establish full-instrument packaging or authorize replication.
4. Improve the actual-pin locality above, then recompute complete paths and ground/reference budgets. The reservation study is independent of any finite assignment/orientation search.

This is missing engineering evidence, not a missing owner choice. The delegated source stage already permits revised geometry and engineering proposals. Ask the owner only if a real product tradeoff becomes necessary outside that scope, such as removing functions, moving fixed front centres, adopting the architecture or authorizing hardware. Native KiCad10.0.6 admission, fabrication/purchase and energization remain separate. All native and physical checks here are **NOT RUN**.
