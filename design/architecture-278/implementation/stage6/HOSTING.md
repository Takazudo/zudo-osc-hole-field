# X1 redesigned front hosting increment

The owner-approved direction favors redesigned behind-panel copper with fixed panel positions. This increment defines two candidate X1 hosts and a middle-board interface reservation; it does not adopt an architecture or require legacy front-board reuse. All **56 packages, 76 units, 182 physical pin records, ten bypass associations and seven fixed X1 panel centres** are preserved. The full 5,904-package assignment overlay changes only those 56 hosts, retains all 33 functions and 438 centres, and leaves **2,572 non-OSC K packages plus 13 POWER packages unhosted geometrically**. X1 has no K population, so this increment does not reduce that outstanding population.

X1 is the complete maintained A/B selector: three jacks, three magnitude LEDs and one selector. Its 47 jack-side packages remain together on `X1-jack`; its nine control-side packages remain together on `X1-control`. All five multi-unit ICs, grounded unused followers and source NC pins survive. No duplicate active circuit is introduced.

| Candidate host | Concrete source placement | Reserved envelope |
|---|---|---|
| X1-jack | All 47 packages retain source XY, face and rotation; fixed three jacks/three LEDs remain anchored | XY [101,111.6]–[176.7,165.22] mm including a 2 mm perimeter support strip |
| X1-control | Fixed SW608 at [99.5,283] mm; complete U3303/C3306/C3307 cluster rigidly translated to U3303 [111,275]; five complete resistors placed in one bounded local box | XY [90.09,265.59]–[119.12,288.25] mm including support strip |
| Middle interface | Three signal-net handoff pairs plus explicit four-rail/ground endpoint groups; virtual waypoints only | XY [110,155]–[122,275] mm at conditional Z50; reserved Z48.4–55 mm |

Both front hosts propose Z20 mm and 1.6 mm PCB thickness, matching the existing candidate front plane. The Z15–26.6 component envelope is a planning reservation, not manufacturer body/seating proof. Connector pads, board mounting holes, support attachments, harness cut lengths and installed body/tool volumes are unassigned. The handoff points are explicitly **virtual reservations, not physical pads**. No new wire count or connector topology is inferred from the source net count.

## Local circuits and interface effects

The inherited control placement scattered nine packages across about 301×114 mm. One bounded refinement reduces that envelope to 29.03×22.66 mm and removes its 85 intersections with existing OSC front-board envelopes. The U3303/bypass cluster moves rigidly, conserving every relative pad position. The five resistors move as whole packages; every non-rail net gets before/after actual-pad span reporting, including feedback and summing nodes.

This has a material tradeoff: A_BUFFER maximum pad separation increases from 80.086 to 153.987 mm. SELECT_A_CONTACT falls from 129.887 to 7.886 mm; SELECT_B_CONTACT from 129.696 to 11.907 mm; SELECTOR_COMMON from 125.593 to 14.519 mm; the local C33d018_DRIVE net from 216.864 to 7.238 mm; and ISO_MID from 19.925 to 4.955 mm. B_BUFFER and SELECTOR_REMOTE spans also decrease. These are geometric changes, not routed lengths or electrical acceptance. The source feedback pairs U3305 1↔2 and 7↔6 retain their original package geometry.

The exact three signal crossings are `/X1/A_BUFFER`, `/X1/B_BUFFER` and `/X1/SELECTOR_REMOTE`. Seven cross-board endpoint pairs are enumerated without counting shared conductors repeatedly as separate physical wires. Their via-reservation straight-segment sums reach 211.141 mm; complete trace/contact/harness/return budgets remain null. The source A/B buffers feed the control selector, and the selected buffered signal returns to the jack-side circuitry. No topology is changed.

All source rail/return endpoints are explicit: 12 +12V, 12 −12V, two +5V and 46 AGND pin records. +5V occurs only on the jack host; it is an external power interface, not an invented cross-board signal. The three other rails/ground span both hosts. Common middle/source impedance, current capacity, source placement and ground error remain unknown. All ten bypass associations remain on their owning hosts. Reported AGND nearest-pad distances can include grounded signal inputs; they do not assert that an amplifier has a dedicated AGND supply-return pad or establish loop inductance.

## Obstructions remain visible

The two new board envelopes do not overlap each other, and neither intersects existing OSC front-board envelopes after the bounded control refinement. The middle reservation intersects none of the registered 480 DIN contact-pad and ten flange-hole exclusion envelopes, existing middle GH headers or shared-reference packages. Flange hole exclusions do not include screw heads, washers or tools.

This is still **not a fitting design**. There are 25 opposite-face X1 courtyard overlaps, zero same-face courtyard overlaps, 13 perimeter-support-strip intersections with fixed hardware, and five middle-reservation projections onto existing rear guide/probe/power fixture envelopes. Their actual Z/solid/support consequences remain open. The support strips do not overlap their own X1 package courtyards. The 416 historical foreign package XY intersections are classified by retained board and explicitly lack new candidate depth; they are not asserted to be 416 physical collisions. Unknown new other-function geometry is never credited as free space.

The next bounded repair should choose actual support attachment locations and resolve front hardware through-pad/body exclusions, then specify the three signal interfaces and common rail/return realization with complete electrical budgets. Current OSC source geometry, 225 crossings and 240 return records are bound unchanged to the Stage6 candidate. Nothing in this increment qualifies the remaining non-OSC/POWER hosting or the full instrument.

Eleven focused source/mutation tests cover complete population and pins, missing package/unit rejection, fixed-centre and host-split rejection, exact net partition, all-instrument ownership conservation, rigid bypass transforms, visible obstruction/span tradeoffs and unknown budget handling. Native/ERC/DRC, simulation and physical checks: **NOT RUN**. Architecture adoption: **false**.

## Reproduction identities

- `scripts/architecture278/implementation/stage6_hosting.py`: `37d79f4ec76f44cc941b20371cb50053f9f1e3d9e607b75ca7c1af77ebafe157`
- `scripts/architecture278/implementation/test_stage6_hosting.py`: `feed9675611be8649dcdcb426c69962952fbe42cbcc95ad6573e6c7d2526a565`
- `design/architecture-278/implementation/stage6/hosting-report.json`: `1cd6edc53529d7f85e79c2acac6912b451e6b038218a5b047261721f8813f74a`
