# Issue 66: two J schematic and source handoff

This supersedes the J topology, counts and affected interfaces in `downstream-handoff-35.md`. Manager owns remote issue amendments. Every schematic/PCB remains an unvalidated draft. No half-board PCB or fabrication output was generated in #66.

## Current manifest

| Board | Outline in panel mm | Plane / stack | Master packages | Fixed features | GH headers |
| --- | --- | --- | ---: | --- | --- |
| JL / `osc-jack-left` | (4,20),(176.5,20),(176.5,164),(4,164) | F z=-10; 4 layers, 1.6 mm, 2 oz proposal | 1,060 | 100 jacks, 43 LEDs | 25 GH8 + 4 GH3 |
| JR / `osc-jack-right` | (177.5,20),(314,20),(314,164),(177.5,164) | Same as JL | 1,031 | 80 jacks, 59 LEDs | 27 GH8 |

The other eight boards retain their selected outlines/planes. K remains a distinct rear core. The ten-board manifest preserves 33 modules, all 438 UID x/y/hole diameters and all 114 current Kingbright indicators. Whole J module ownership is explicit in `partition-input.json:jack_split`; no source island/package recut and no raw/sensitive crossing was introduced. UID/x/y SHA256 remains `8354aed4a72bf5357e1ccfb4da7c3234f139ba19f75a49d825d733c30a6da843`. Only jack/LED domain metadata changes to JL/JR.

## Exact placement and electrical locality

Both halves use 0.10 mm search cells; P/K retain 0.25 mm cells. Every footprint keeps its real dimensions, 0.35 mm drawn courtyard spacing and 0.30 mm board edge allocation. All 44 resistors that overflowed the coarser bypass-aware trial now fit. Final master rows: JL 754 B / 306 F; JR 527 B / 504 F, including fixed hardware.

All 414 J bypass capacitors are clustered on their IC's face using actual source supply-pin and capacitor rail-pad coordinates. Worst pad-centre distance is 2.8875 mm against the explicit 3 mm **project proposal**. TI OPAx196 SBOS869 §10.1 and OPAx197 SBOS737C §10.1 require close 0.1 uF bypasses but give no numeric mm guarantee; retained evidence is `bypass-placement-evidence.json`. Actual short supply/AGND return copper and stability remain #38/#65. No opposite-face bypass-via proposal is needed.

Pinned KiCad checks all 46 used footprint/face/rotation classes and every 2,147 J package/header courtyard plus through-hole pad exclusions. The worst native cached gap is 0.260 mm: **0.350 mm drawn separation minus 0.045 mm cached inflation on each edge**. The unchanged native acceptance limit is 0.250 mm. This is geometry evidence, not routed DRC or solid fit.

## Supports, reservations and interfaces

Retain four original outer M2 supports per half (eight total); no seam or front-panel mounting holes. Proposed seam carrier: rear x172..182/y20..164/z-13.6..-11.6; front lips x175.2..178.8/y20..164/z-10..-9.5. Two rear cross-members span x-2..320 at y17..19 and y165..167, z-13.6..-11.6, seating into the enclosure side frame. Carrier/lips and looms clear nominal hardware/pad envelopes. Profile, exact fastening, strength, tolerance and disassembly are NOT RUN #65; no solder/header structural support is assumed.

JL bulk slots: x122..127; JR: x292..297; each has y145..148,149..152,153..156. Each reserves a full 5x3 mm capacitor courtyard. #59 protection receipts subtract fixed jack envelopes, actual power lands, bulk and carrier reservations; exact protection fit is still OPEN. Residual #59 reservations are330.6 mm² JL and774.0 mm² JR after these exclusions. Do not reuse the historical single-J remaining-area number.

There are still 195 GH harnesses, 390 PCB headers, 390 external housings, 1,830 positions and 1,822 fitted crimps. Across all harnesses at one end: 513 signals + 380 AGND + 18 rail + 4 NC positions. Four NC positions are total, not four per harness. Preserve the exact audited GH3/GH7/GH8 top-entry parts and manufacturer numbering.

J/K signals regroup into 100 JL and 106 JR signals. Four JL/P utility loops retain x40/57/74/91. Regenerated K sites, pin maps, service apertures and source-native angles are authoritative. Whole-driver <=1 nF and <=300 mm remain acceptance requirements. All 195 GH plus 18 load-wire corridors pass the nominal mutual/support/EXT checks; installed loom qualification is NOT RUN #65.

## Power and current acceptance

18 factory Alpha Wire 5859 AWG14 load wires join 36 custom solder terminals. JL, JR and P each have three rail wires and three independent AGND wires. JL's six routes have an explicit 8 mm smooth lateral bow to clear utility loops; the combined curvature is checked, not inferred from the former planar route. Use manifest endpoints/terminal references, not historical J identifiers.

Worst hot distribution remains 16.6275 mV with the whole 4.6 A return charged to one main path. Conditional GH return bounds are JL 0.496114333 A, JR 0.492091887 A, P 0.491875226 A and JL/P utility 0.249524108 A. JL has only **3.885667 mA** margin to the unchanged 0.5 A proposal. Combined branch-board plus K AGND spreading/neck must be <=0.5 mOhm hot, with wire/contact extrema as recorded. This is not measured margin, guaranteed cold operation or equal-current sharing. Failed actual resistance limits require redesign. Main-return-open, partial mating and external patch-ground faults remain #59/#65.

Five powered boards reserve 4.7 uF per rail: nominal fitted-plus-reserved totals 73.4/66.2/48.0 uF. Full +20% capacitor ramp at >=10 ms adds 116.2656/104.8608/31.68 mA; combined with conservative continuous minima this gives 1816.2656/1704.8608/331.68 mA, below the 2000/1900/400 mA transient minima. No added independent copies of existing ledger loads. Source/inlet remains unselected; CN301/XB301 stay abstract with no conductive bridge. EXT x260..308/y248..293/z-85..-45 and separate source-inlet 20 AWG contract remain.

## Downstream issue amendment text

### #38

Generate, place and route `osc-jack-left` and `osc-jack-right` from the current ten-board manifest and native netlists. Consume exact per-reference origins/faces/native angles and source-defined IC/bypass clusters; do not copy the historical single-J coordinates or assume translated module replication. Preserve the real seam carrier, eight outer posts, six power lands and three bulk slots per half, all #59 residual reservations and exact fixed UID coordinates. Verify actual native courtyard/THT/edge checks, supply/AGND loops and combined hot ground-neck requirement; run each half through bounded pinned routing and complete native ratsnest reporting. Run the preserved tools with an explicit board argument, for example `audit_exact_j.py osc-jack-left` and `analyze_replication.py osc-jack-left` (repeat for right). Source geometric PASS does not mean routing PASS. Historical `osc-jack` produced zero copper after 180 s fanout and 900 s no-fanout attempts and remains rejected, not a routed half-board baseline.

### #39

P and five selected 3+2 adapters retain their geometry. Consume current P interface/terminal references and the four JL/P utility harnesses from regenerated projection; preserve exact pin/native-angle data. Recheck P/K and utility return paths against the conditional 0.5 mOhm combined-board hot neck requirement. No hardware coordinate or selector-family change is authorized by #66.

### #43

Retain distinct K at proposed z=-100 and its selected outline/stack. Consume regenerated J-half header sites, pin maps, service apertures and **18 K load-side lands**, including three AGND wires per JL/JR/P branch. Preserve exact source reservations and reference fanout. Recheck all changed looms and short rail/AGND paths; the old J pad map and single-J rail-plane geometry are historical. Verify hot branch+K neck resistance, actual power distribution and service access; installed qualification remains #65.

### #44

Use ten current board projects. Assembly inventory is 390 headers, 390 housings, 1,822 fitted crimps, 195 GH harnesses, 18 load wires and 36 PCB solder terminals. Keep four aggregate NC positions per harness end unwired. Bulk/protection and source inlet remain explicitly unselected; do not turn their reserved area into fictitious fitted BOM parts. Distinguish 5,896 fitted master parts / 8 DNP from added interface hardware and still-unselected board bulk.

### #45

Audit joined native parity across all ten current boards: 5,904 master physical rows / 20,419 pins / 4,106 master nets, 650 fitted ICs; complete declared interfaces and abstract source break. Include both J halves' independent routing/DRC/native-ratsnest outcomes and the conditional bypass/current/carrier receipts. #55 selector, #57 source, #64 optics and #65 installed supports/loom/hot/cold-wire qualification remain NOT RUN; #59 protection remains OPEN. No fabrication-release claim follows from source parity.

### #36 / #37 reconciliation

#66 regenerates ten schematic projects and joined-native parity, replacing the old J projection; original #36 is historical provenance. The panel retains 324 NPTH holes, 114 optical windows and all 438 coordinates. Domain metadata and internal split/carrier documentation are updated; there are no new panel or seam drills. Compare regenerated panel bytes/geometry against merged #37 and preserve owner artwork.

Native per-board ERC reports zero errors across all ten schematics. Retained warnings: JL123, JR153, P137, K218, EL32, and two on each octave adapter (673 total). All228 pin-to-pin warning identities match the master baseline;445 endpoint-off-grid warnings remain visible. No warning suppression or electrical qualification is claimed.
