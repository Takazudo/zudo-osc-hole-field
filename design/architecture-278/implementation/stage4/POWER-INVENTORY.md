# Complete power endpoint rebinding

The new source report binds actual candidate pads for five oscillators and the one shared reference circuit, while retaining every other physical package without inventing its placement. It supersedes use of the compact comparison's stored supply XY as new-card geometry. It does not establish rail routing, impedance, current sharing, state maxima or electrical acceptance.

The retained source inventory contains **5,904 packages, 8,226 units and 20,419 pins, including 939 NC pins**. Every source unit and pin/net assignment is retained; `pin_to_unit` binds each pin back to its full physical package unit. The one-oscillator/shared template's 249 physical packages expand through the audited Ref/key/unit/pin correspondence to **1,125 placed packages and 1,472 units**: five sets of 219 OSC packages plus 30 shared packages. All **4,766 other-function packages and 13 POWER packages** remain unplaced in the new candidate. Historical coordinates are not silently transplanted.

Three coordinate bindings are provided: stage 3 baseline, stage 3 bypass-refined and baseline with the complete shared circuit translated +6 mm X. The last is the stage 4 local repair input. Every actual Ref/pin coordinate comes from the front instance transform, the new rear-card package pose plus its card origin, or the shared middle pose plus the declared translation. PCB-plane Z is a conditional design datum, not a body/lead solid or measured installed height. Selector stagger/rotation is preserved through the existing actual instance placement.

| Global net | Placed pin nodes | Unplaced pin nodes | Total |
|---|---:|---:|---:|
| +12V | 214 | 900 | 1114 |
| +5V | 50 | 679 | 729 |
| -12V | 171 | 764 | 935 |
| AGND | 755 | 3396 | 4151 |

The **6,929 global supply/ground pin nodes** resolve through one authoritative coordinate table per variant. A graph endpoint `REF:PIN` resolves to `placed_packages[REF].pads_xyz_mm[PIN]`; an absent package resolves to null. This normalization avoids both stale duplicated coordinates and oversized repeated geometry. The report remains a compact, reproducible JSON source artifact, with no LFS or binary acquisition.

All **1,067 retained bypass associations** (including the eight explicitly retained shared associations) are preserved with their exact target packages. The association records reference the same coordinate table. No grounded op-amp signal input is promoted into a proven supply-current return, and no bypass loop is claimed routed.

Each variant accounts for all **225 crossing endpoint identities, 240 return groups and nine shared nets**. Counts alone are insufficient: the generator checks complete crossing tuples, actual live aliases, unique return-group identities and each return group's complete source AGND endpoint set. Old stage 3 crossing totals are labeled inherited; the +6 mm shared translation changes 65 route rows, which the separate stage 4 candidate generator recalculates. This inventory does not silently reuse those totals as updated route evidence.

`routed_edges`, common resistance, contact tolerances, current-sharing solution, source regulation and load maxima remain null. Four external-source placeholders do not replace the thirteen physical POWER packages or assert an exact source/inlet selection. Complete source/common/branch/load/return current and voltage-drop budgets remain OPEN. Historical scalar length comparisons retain their stated source definition and uncertainty; this report makes no claim that 300 mm is physically safe or longer paths unsafe.

Reproduce with `python3 scripts/architecture278/implementation/stage4_power_inventory.py --check`. The API `rebind_variant(name, best, assembly, ledger, ctx, shared_translation)` exposes the same binding for a declared scenario. Thirteen tests cover full package/unit/pin/NC and bypass conservation, all three variants, shared-only translation, stale rear coordinates, dropped supply/return nodes, omitted/duplicated crossing or return groups, wrong actual source aliases, invented POWER placement and unextracted routing.

Native KiCad/ERC/DRC/physical checks: **NOT RUN**. Stage 1 remains OPEN.

Final source/artifact SHA-256:

- `scripts/architecture278/implementation/stage4_power_inventory.py`: `985f9ce633c1c77069108051534cf0bae8876f08218294bb38ada789861408b6`
- `scripts/architecture278/implementation/test_stage4_power_inventory.py`: `5286aade8477e02916da237d54048b0c7a8ae5ed0f8ffd703e91a20e3001797d`
- `design/architecture-278/implementation/stage4/power-inventory-report.json`: `e49574f6be6567d8df68d0cd4cb1d68cae068b5a2438c21757bfd835285e9a2d`
