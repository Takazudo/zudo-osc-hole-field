# AO and buffered-mult family reuse comparison — Stage37

**Recommendation: develop the conservative family boundaries; do not adopt a new hardware architecture yet.** Repeated AO cores and complete active mult boards merit the next populated source layout. Neither the rear trial nor the front adapters have demonstrated integrated fit. This is an additive comparison against `c3bbcf0c890aff329bb7a3374cc51cd38c072929`, not permission to change canonical CAD, panel positions, nets, enclosure or manufacturing files. Earlier owner-approved rear-face study does not approve these new boards or interfaces. PR287 stays draft; parent286 and historical stages remain intact.

[Diagram](comparison.svg) · [machine-readable package assignments, pins, counts and conflicts](proposal.json) · [generator](generate.py) · [verification](VERIFICATION.md). Coordinates are panel-front XY, x right/y down; rear depth is positive. All64 AO/mult locked markers are copied exactly, including all LEDs. Marker circles are schematic symbols, not hardware envelopes.

## What can actually be identical

The current family generator shares values, footprints, population and circuit structure across six AO and two MULT instances. `proposal.json` records every physical package and every unit/pin at representative A01/B1, with current reference labels; local nets are instantiated separately for every module. No package/channel repacking is proposed. Blank MPNs remain unresolved orderable identities. Existing ten partition boards are not ten modular family designs: AO occupies JR/P/K; mult occupies JL. Those shared boards cannot simply be deleted when these functions are extracted.

| Candidate | AO per instance | MULT per instance | Consequence |
|---|---|---|---|
| Current regions, reused individually |29 core +59 active jack +2 control packages, on3 boards |36 packages on one active jack board |20 electrical-region boards,4 unique designs for these8 functions |
| Shared AO front strips |Six identical29-package cores; one354-package active jack strip; one12-pot control strip |Two identical36-package active jack boards |10 electrical-region boards,4 unique designs; large strip replacement/handling burden |
| Passive front, all electronics rear |81 rear +9 panel packages |31 rear +5 panel packages |Not recommended now: new cable feedback/protection boundary, even though declared sensitive-net annotations do not cross |

These are **electrical-region board lower bounds**, not fabrication board totals. Fixed LED seating may require separate optical substrates: one per instance adds8 boards to the individual option (28), or one AO strip plus two mult substrates adds3 to the shared option (13), at least2 further unique designs. Exact optical planes and links are unresolved. If52 LED conductors use discrete wires soldered at both ends, this adds104 solder joints; this is an explicit alternative, not adopted wiring. Panel/jack/pot tail adaptation can add further boards and terminations. Do not present the lower bounds as a complete assembly BOM. No savings claim is possible without populated layouts, assembly scope, yield/rework assumptions and quotes.

## Electrical boundary and proposed semantic pinouts

Conservative AO preserves existing BoardRegion ownership. ATTEN_SUM/SUM_NODE stay core; RESTORE_NODE/OUT_INTERNAL/CLIP_HALF stay active jack. Whole U7104/U7105 packages stay core; U7106 (input buffers, restore and precision output) and U7109 (indicator channels) stay jack. Supply units, spare units and associated bypasses follow their complete package. Reference generation remains per AO: shared front strips must not short different modules' REF5/REFN5 nets together. Only already-global supply/AGND nets may be common; no hidden functional normals.

Conservative mult keeps input protection, high-impedance sense, buffer, all three compensated precision outputs and indicator circuitry together. U3102 contains input and output amplifiers; splitting those functions would split a package. No analog transport is needed for a complete local board. Optical separation remains an explicit qualification issue rather than a claimed solved LED mounting arrangement.

The following are **new project-specific numbered proposals**, not current harness assignments. Each list is pin1 through pin10/8; sockets connect matching numbers. Physical pad-face orientation/keying and exact footprint integration are NOT established by this semantic table.

| Proposed link | Numbered nets |
|---|---|
| AO-C10, controls↔core |REF5, AGND, REFN5, AGND, IN_REMOTE, AGND, ATTEN_W=`Cc045d2_W`, AGND, OFFSET_W=`C38cac0_W`, AGND |
| AO-J10, active jack↔core |IN_BUFFER, AGND, OFFSET_BUFFER, AGND, REF5, AGND, REFN5, AGND, SUM_NEG, AGND |
| P8, distribution↔active jack/MULT |+12V, AGND, −12V, AGND, +5V, AGND, NC, NC |
| P8-core, distribution↔AO core |+12V, AGND, −12V, AGND, NC, AGND, NC, NC |

AO core does not consume +5V. Returns are the same AGND net, not isolated grounds or automatic extra-current credit. Pot wipers remain cable-bound high-impedance concerns; keep their paired returns and establish leakage, capacitance, crosstalk and open-wiper behavior. SUM_NEG is an amplifier output into the restore stage, not the SUM_NODE summing junction. References are signal references, not general power rails. Current, simultaneous load/fault, contact derating and shared-strip thermal limits must be rederived; one A01 budget cannot qualify six channels.

Existing 3M D2510-6002-AR/89110-0101 and D2508-6002-AR/89108-0101 are candidate standard hardware families for these10/8-way links, with exact primary evidence retained in Stage36. No connector center, orientation, cable length or current limit is inherited. Same10-way shell for C and J creates a mis-mating hazard; different physical coding or connector sizes plus an assembly-proof routing arrangement must be selected before adoption. Labels alone are insufficient. P8 is bespoke internal power, **not Eurorack power**.

The passive-front alternative exports17 AO nets and7 mult nets including AGND (complete lists in JSON). It passes the narrow declared-sensitive-net locality test, but adds cable parasitics to LED bridge feedback, moves raw-input protection away from the jack, and puts adapter/contact resistance after the precision output's feedback pickoff. It is retained as a rejected first boundary, not called electrically equivalent merely because source nets have the same names.

## Rear arrangement and front alternatives

Six identical **40×45mm capacity trials** form a3×2 array: x=180/225/270, y=180/230, PCB z74..75.6. These dimensions are project choices for testing a packing idea, not dimensions derived from a successful29-package layout. Each board needs its three headers, bypass locality, routing, mounting and removal reservations populated before capacity can pass. There is5mm nominal edge spacing; expanding both boards by2mm leaves1mm. All trials lie within318×298; they do not overlap each other with that allowance.

However, the conservative XY screen finds **95 foreign reservation projection pairs**, retained by identity in JSON. Existing whole-instrument concept reservations are occupied/unknown, regardless of their illustrative z. Incumbent K, KEEP_K1402_INCUMBENT, exact component tails, mounts, ribbons and service space also remain occupied/unknown; no removal or relocation is authorized. Consequently **integrated fit is BLOCKED**, not a packing success. The array is useful evidence that a free-standing repeated-core geometry can be considered separately from17mm front pitch, and that it cannot be adopted at these coordinates without resolving other allocations.

Front AO centres are x218.5+17n: jacks y127/141/155, pots y269/283; LEDs retain their exact independent coordinates. Individual active jack boards must fit those17mm translations without overlapping populations/connectors; existing45mm A01 jack boards cannot be copied six times. Shared strips avoid individual edge constraints but must host354 jack-region packages and service all six modules; their capacity remains unknown. A source-populated strip versus narrower individual board is the next comparison, not a chosen result.

B2's complete fixed pattern translates B1 by34mm. B1 jack centres are (14.5,141),(31.5,141),(14.5,155),(31.5,155), plus LED(20.65,141). Repeat the same local mult board only after fitting all36 packages, exact jack bodies, optical solution and power header; a rectangle around centres alone is not sufficient. Both proposed approaches require panel-supported jacks and independent board support; cable loads must not be carried by solder joints. No strength, registration/bow or50N retention qualification is inferred.

## Counts and assembly operations

| Scoped quantity | Current canonical partition | Individual front boards | Shared AO strips |
|---|---:|---:|---:|
| Whole-instrument boards / designs |10 /10 |Unknown; requires redesign of shared incumbents |Unknown; same limitation |
| AO+MULT electrical-region boards / designs |0 exclusive boards |20 /4 |10 /4 |
| Signal bundles touching AO/MULT |23 |12 |12 |
| Signal header ends touching AO/MULT |46 |24 |24 |
| Proposed dedicated power links |Not separately attributable |14 |14 |
| All proposed link cables / board-header ends |Not comparable from scoped signal count |26 /52 |26 /52 |
| Socket terminations / mating actions |Existing technology and shared power scope differ |52 /52 |52 /52 |
| AO rear trial mounting sites |Not attributable |24 (four per core assumption) |24 (same assumption) |

The baseline23 bundles include mixed-module harnesses; their removal is not authorized and23→12 is not an instrument-wide savings claim. New52 header ends include14 distribution-side headers;38 are on the family boards. Each of26 ribbons assumes two factory-fitted sockets, two termination operations and two final mating actions, excluding support clamps, strain relief, optical/tail adapters, inspection, rework and fasteners. Four sites per core is a counting assumption only; hole locations and strength are unknown. Shared strips retain six separate jack power feeds to avoid pretending one8-way feed is qualified for six channels. A lower-power-feed variant needs its own budgets and is not counted here. Ribbon length SKUs remain location-specific even if assembled circuit boards are identical.

## Compatibility with previous candidates

Stage34 guide/shorter-cable and later Stage35 work remain historical. Stage36 `idc-service-placement` is a different single-A01 hybrid:10-way C-SIG,8-way J-PWR,14-way J-SIG, middle board and separate Samtec rear links. It retains revised connector positions, unqualified cable/support geometry and all reported failures/unknowns. This study instead removes the proposed middle-board function from its counted family topology and introduces AO-J10/newP8; it is **not plug-compatible**, does not supersede its pin maps, and cannot borrow its clearance results. The40×45 core is not the populated76×108 A01 board. No deeper cover, carrier change or reservation release is adopted.

## Test plan and decision criteria

Before considering adoption, a source-only follow-up can populate one29-package AO core plus both front alternatives and one36-package mult at locked positions using actual footprints. Preserve package membership and all nets; mechanically bind exact header/socket polarity, support and optical/tail adapters. Require no unexplained connector nets or NC continuity, no split packages, complete fixed-marker coverage and explicit BOM/assembly counts. Any unknown obstacle remains a blocker; a successful source screen is not physical qualification.

Practical unpowered mock-up checklist (no build is performed here):

1. Record actual jack/pot/LED seated datums, maximum body/tail heights, board thickness/bow, carrier registration and fastener/tool envelopes. Reject any collision or allowance exceedance; for the trial packing, actual combined lateral allowances above4mm consume its remaining gap. No nominal dimension substitutes for measured bounds.
2. Fit exact assembled connectors and selected ribbon. Measure seated height, cable exits, clamp positions and full withdrawal/removal trajectories including neighboring boards. Require manufacturer-supported static/repeated-flex bend limits and maintained support throughout service; wire construction, limits and length/cut tolerance remain unresolved. Reject unsupported, pinched or overstretched states.
3. With power disconnected, verify every numbered contact end-to-end, NC isolation, rail polarity and module reference isolation; attempt wrong C/J mating with the chosen coding. Reject any electrically possible mis-mate. Confirm every unit can be removed without moving locked front hardware or loading solder joints.
4. Count actual adapters, sockets, terminations, clamps, screws and assembly actions; revise the comparison before seeking any future quotes. Nothing here requests a quote or authorizes purchase.

Later electrical tests require separate authorization and accepted numerical criteria: AO gain −1/0/+1, offset/CV addition, clipping/headroom, reference loading, pot endpoints/open-wiper behavior; mult individual and simultaneous output load error, noise/crosstalk with indicators active, cable/load stability, startup/partial-power, port faults and return/contact resistance. Test each unit, not just one representative board. There is no invented accuracy/noise/current pass threshold; obtain applicable retained worksheet limits and resolve missing system criteria before testing. Calibration procedure, trim provisions and allowable drift are unresolved. Existing protection/source gates remain open.

**Next bounded cloud work:** source-populate and compare the two AO front alternatives and the front-active mult, starting with real footprint capacity and optical separation. Resolve the95 reservation projections before assigning rear coordinates. Family reuse merits further development; this candidate does not yet merit hardware adoption or expansion into unrelated families.
