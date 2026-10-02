# Conditional EXT boundary handoff after issue 52

This is a non-orderable, non-energizable schematic draft. The exact protection circuit is #59; source and physical qualification are #57. No rail or output is protected by the two abstract symbols.

## What is actually connected

The master native netlist contains `CN301` (`OSC_EXT_INLET_R1`) and `XB301` (`OSC_EXT_BOUNDARY_R1`). Logical inlet pins 1/2/3 terminate on `+12V_IN`/`-12V_IN`/`+5V_IN`; pin 4 is NC; pins 5–8 join AGND. Each raw rail has exactly the corresponding inlet pin and boundary input. Boundary output pins 4/5/6 are on conditional load rails `+12V`/`-12V`/`+5V`. Pin 7 is an **ERC-only** AGND power declaration. A KiCad component has no internal conducting connection between its pins in this netlist. The three raw and three load nets remain distinct. `scripts/schgen/check_power_boundary.py` checks these exact nodes against the pinned native KiCad export and checks that the KiCad BOM omits both abstract references.

Both abstract instances carry `AbstractBoundary=true` and `Implementation=REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE`, an empty MPN and footprint, and `in_bom=no`. KiCad's native netlist omits `on_board=no` symbols, so the schematic instances serialize `on_board=yes` solely to retain auditable pins. They have no footprint and are not placed. The source library fragments themselves remain `on_board=no`.

## Instructions for #35/#36 and PCB work #38–#43

- Consume one `EXT` source domain and the #48 requirement-only inlet reservation. Retain 33 signal modules, `OCTAVE_REF`, 438 fixed centres and all sensitive islands. Keep all 180 sleeves on AGND. Do not place rejected three-source pockets or the old 16-contact inlet/PTCs.
- In per-board projection, preserve the master source-domain report and `CN301`/`XB301` pin-net evidence, then exclude both abstract references from board component lists, placement area, BOM/CPL and PCB footprint generation. `scripts/pcbgen/netlist.py` now filters only refs with the exact `AbstractBoundary=true` marker, expected status, blank footprint and blank MPN; a malformed marker fails. This filter also removes their pin nodes before board copper nets are built. Do not infer a conductive rail bridge through `XB301`.
- Any board needing real power input/output requires a separately specified, non-abstract circuit/interface and exact physical connectors from #59. Until then, board-level rail nets remain conditional and affected packing/routing closure is OPEN. The abstract boundary occupies no PCB area and provides no routable pad.
- Reconcile unplaced 4.7 µF per powered board/rail against the current master inventory below. The ten-board partition is a proposal; final board reservoir placement, proximity and effective capacitance remain unproved.
- The #58 prospective 35 local quad output-isolation packages imply 45.5 mA +12 V sensitivity, 25.5 mA above the whole-instrument 20 mA auxiliary allocation before any supervisor/switch demand. They are **not fitted or booked as savings**. #59 must recompute the contract from selected circuits, including current and added capacitors.
- Keep all 82 output, 16 precision-feedback and 30 octave-receiver paths OPEN. No implementation or physical test is claimed by schematic ERC, native netlist parity, BOM exclusion, or the conditional-draft gate.

The generated `design/reports/power-boundary.json` reports exact native netlist facts. `design/power/supply-architecture.json` retains historical single/two/three-source comparisons and reports the selected conditional allocation separately from the historical 1.1 A PTC failure.

## Current master capacitance allocation

<!-- power-capacitance:start -->

The captured master rail-attributed capacitor inventory is **49.9 / 42.7 / 24.5 µF** on +12/−12/+5 V, leaving **100.1 / 107.3 / 75.5 µF** nominal against the source-contract ceilings before unplaced board bulk. Local VEE5 and filtered NOISE_VDD capacitors count against their upstream rails. This is the master inventory, not a census of completed board copper or the unfitted protection candidate. Reconcile every board reservoir and selected protection capacitor; per-pin proximity and effective ceramic capacitance remain open.

<!-- power-capacitance:end -->
