# X1 actual connector and harness interfaces

The three virtual signal handoffs now have explicit source-backed JST GH headers, housings, contacts, pad coordinates and harness conductors. The four harnesses retain the complete X1 circuit, including all 56 source packages, 76 units, 182 pin/NC records, ten bypass associations and seven fixed panel devices. Added transport is inventoried separately. Nothing is added to the unchanged 225-path OSC baseline.

| Harness | Header / housing positions | Pin assignment | Proposed wire cut |
|---|---:|---|---:|
| J-SIG | 4 | 1 A_BUFFER, 2 B_BUFFER, 3 SELECTOR_REMOTE, 4 AGND | 60±3 mm |
| J-PWR | 7 | 1 +12V, 3 −12V, 5 +5V, 7 AGND; 2/4/6 NC | 65±3 mm |
| C-SIG | 4 | Same map as J-SIG | 75±3 mm |
| C-PWR | 3 | 1 +12V, 2 −12V, 3 AGND | 75±3 mm |

Each harness has a header and housing at both ends. Exact mating identities are `BM03B/BM04B/BM07B-GHS-TBT(LF)(SN)`, matching `GHR-03V-S/GHR-04V-S/GHR-07V-S` housings and `SSHL-002T-P0.2` contacts. GH3/GH7 use committed footprints; GH4 has a candidate `.kicad_mod` under this implementation directory, derived from retained primary JST land geometry and the exact four-position dimensions. The generator verifies all numbered/MP pad coordinates, sizes and courtyard allocations against the retained source pattern. This is source validation, not native footprint or installed mating qualification.

The initial seven-position power change deliberately separates J-PWR from the four-position signal housings. Its three unused cavities have no wires or crimps; the corresponding six header NC lands across both ends remain isolated and soldered. Only the two signal harnesses have the same position count, and their pin maps are identical. This removes an exact-compatible conflicting power/signal map within this candidate. Partial insertion, wrong supplier parts, assembly coding and cable/service interchangeability still need review; polarization alone is not a complete assembly safeguard.

## Physical inventory and circuit graph

There are **four harnesses, eight headers, eight housings, 15 wires and 30 crimp contacts**. The wire roles are six signal conductors, five rail conductors and four AGND conductors. Header soldering comprises 30 active electrical pins, six NC pins and 16 mechanical mounting pads: **52 solder joints**. MP pads are not silently assigned to AGND. Exact wire order code, stranding, insulation and crimp-process qualification remain open; AWG26 is the proposed gauge matching the retained source current-rating condition.

Three middle copper edges connect corresponding J-SIG/C-SIG signal pins. Two edges connect J-PWR +12V/−12V to C-PWR. Three AGND edges connect the actual J-PWR pin7 pad to J-SIG pin4, C-SIG pin4 and C-PWR pin3. The +5V rail goes only to the jack-side population. All eight edges retain actual source/destination pads and separate un-routed copper allocations. The complete front-net inventory joins source pins to the applicable actual header pins without turning every source endpoint pair into another cable.

The four J-PWR middle pads identify the power/return boundary concretely. **The upstream POWER source connector, inlet, current capacity, distribution route and common-return impedance remain unselected.** The 13 source POWER packages are not silently relocated, and this report does not claim that all physical instrument interfaces are closed.

## Actual pad planes and service

Front headers mount on the rear PCB surface at Z21.6 mm, separate from the panel-facing Z20 mm surface. Middle headers mount toward the panel at Z48.4 mm. The report binds source package pad depths to the final mechanical placements and retains all package origins, rotations, units and nets.

Each conductor records actual endpoint XYZ, minimum/maximum cut, straight separation and four endpoint-motion cases: neither end withdrawn, either end withdrawn by 15 mm, or both withdrawn. Separate body/service boxes include the source 7.3 mm reference mated height plus the proposed 15 mm normal withdrawal. The minimum remaining wire slack is **12.768608 mm**, exceeding the 10 mm source allocation. J-PWR needed 65±3 mm after the wider GH7 pin span reduced its former 60±3 mm slack below that allocation.

Eight strain-relief locations are reserved on an enclosure-supported structure at Z30–34 mm, with the actual XY locations recorded. They must carry cable/mating loads rather than header solder joints. The mechanical report checks explicit mounts, package/header exclusions and service projections. Actual latch release stroke, retention force, bend radius, wire exit geometry, support stiffness and hardware order codes remain unknown. Endpoint-motion and clearance screens are not a measured unplugging or fatigue test.

## Electrical boundaries remain conditional

Every harness conductor has two mated GH contact interfaces; a complete jack-to-middle-to-control signal crosses four. The retained source maxima are 30 mΩ initial and 50 mΩ after specified tests **per mated contact**, so a two-contact branch has 60/100 mΩ before wire, crimp and copper resistance. This does not establish the inherited 0.5 mΩ return goal or 200 µV error term. Four AGND conductors are explicitly accounted, with no equal-sharing or cancellation credit. The nominal 1 A/contact source rating is conditional on AWG26 and the source thermal/test conditions; it is not a qualified assembled current rating.

Complete signal, rail and return allocations are in the separate electrical report. Direct capacitance, routed copper, delivered return error, source current capacity and analog stability remain unqualified. Local protection, feedback and switching topology are unchanged; geometric changes and source associations remain visible.

The source and mutation tests cover exact pin maps, missing link/source-pin rejection, footprint pad/face datums, NC cavities, middle joins, source-front connectivity, complete transport counts and insufficient wire slack. No native/ERC/DRC, simulator, fabrication or physical execution occurred. Hardware acceptance remains **false**.

## Reproduction identities

- `scripts/architecture278/implementation/stage7_interfaces.py`: `bcda866923f4cef4c7b154fa45823a044e64b11ac03adfe1054c239241aee984`
- `scripts/architecture278/implementation/test_stage7_interfaces.py`: `b9df7c0abf5db510c428ef5f60cb3785e50703af2e94e40a4a98aa1d95c321c4`
- `design/architecture-278/implementation/stage7/interface-input.json`: `4e665e4da5f8a72daee36c0660bd191423841d204f6726365341e091c3ad2b9e`
- `design/architecture-278/implementation/stage7/interfaces-report.json`: `45a472721d7541b3de02ca20d0c243e0d5f693a4535812c5ae8dc4d2b0e98fbd`
- `design/architecture-278/implementation/stage7/footprints/JST_GH4_BM_TopEntry_Candidate.kicad_mod`: `e31245b923b8fa03dc3fbe6419e6644ef7f6372e0088c4423b1b73ffa36d4a00`
