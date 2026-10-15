> Historical revision-1 analysis below. The owner authorized the next bounded design revision; see [revision-connectors.md](revision-connectors.md), [current gate](GATE.md) and the revision-2 reports for the current recommendation. Earlier failed/partial evidence is retained, not superseded by a physical PASS.

# Adjacent assembly burden and service boundary

The report lists all 11 O1 harnesses, their conductor/return counts, historical cut-length upper bounds from `loom-candidate.json`, and both baseline and same-path candidate connection costs. Lengths are design upper bounds, not purchased cut lengths or measured wires. The two-link comparison retains every existing signal/return endpoint: front-to-middle plus middle-to-rear with no hidden deletion. Return multiplicity may increase after electrical allocation.

| Count | Historical O1 / core-only starting comparison | Functional same-path two-link proposal |
|---|---:|---:|
| Harness assemblies | 11 | 22 |
| Conductor segments | 51 | 102 |
| Crimps / cable socket contacts | 102 | 204 |
| Header pin/socket mating interfaces | 102 | 204 |
| Header pins | 102 | 204 |
| Individual conductive members (socket plus header) | 204 | 408 |
| Header housings / cable housings | 22 / 22 | 44 / 44 |
| Harness-end mating operations | 22 | 44 |
| Core disconnect groups for replacement | 11 | 11 rear link groups, subject to regrouping |

These are O1 same-path counters, not a final architecture BOM. Each added middle front or rear face is counted. Contacts mean mated interfaces unless the table explicitly says individual members. GH crimps exist at each cable end. A future direct mating connector changes the counts and load path and must be recalculated. Current proposed links are bounded at 90 mm front + 80 mm rear, with at most 100 mm middle trace: 270 mm remote path before any additional connector internal/probe length; the electrical 300 mm/1 nF requirements remain ceilings including everything. Baseline lengths are individually extracted, not replaced by a uniform 300 mm assumption. Reference aggregate capacitance across five receivers remains a separate electrical blocker.

The 13 service net classes are **not** 13 connector pins. Shared rail/return/current multiplicity, reference loading, front local decoupling and interface redesign add or redistribute endpoints. The two-link 204 contact count is therefore an explicit comparison subtotal, never a final total or claimed saving. Service feeds and the existing 18 main power wires/36 solder-terminal endpoints remain a separate unresolved supported connection conversion. Test adapters and their wires, crimps and probe loading have no final fixture bill yet and are **OPEN**, excluded from final product counters, never zero.

Historical five OSC = 55 harnesses/255 conductors; whole instrument = 195 harnesses/911 conductors/1,822 crimps plus 18 main power wires. These are retained comparison inputs. Multiplying the representative two-link O1 mapping by five gives only 110/510/1,020 crimps as a same-path arithmetic scenario, not an implementable final loom. O2/O4 selector geometry differs, and shared service allocation cannot be multiplied blindly. No savings in money, labour or time are established.

Hardware burden is unresolved: separate front posts/carriers, middle frame and fasteners, core guide carrier and two proposed end fastening stations per card, cable comb/strain relief at every link end, rear terminal restraint, cover screws, keying labels and calibration fixture. Exact screws, collars, rails and panel clamp dimensions are not selected. Core-only avoids the middle frame and new middle housings; it does not eliminate rear supports or factory strain relief. Assembly comparisons must include continuity/polarity checks for every conductor, crimp inspection for every termination, pull/retention checks, fixture mating operations and both adjacent installed tests. No reduction is inferred from board count alone.

Factory assembly sequence: (1) inspect locked-centre panel and install independent front carriers and jack/pot boards; (2) install 3+2 octave carriers, extensions and indexed knobs and verify pin continuity; (3) install separately supported middle test piece and secure front short links with local backing and strain relief; (4) install supported rear core carrier and rear service termination conversion; (5) mate individually keyed rear links, secure combs and verify every conductor/polarity and return before any separately authorized powering; (6) confirm all six rear adjustment/probe lanes and adjacent cover clearance; (7) fit cover. Structural retention is checked independently of electrical connection.

Routine replacement sequence: disconnect external source; demonstrate rails discharged using the separately defined procedure; remove rear cover; identify O1 without unplugging O2 or shared upstream feeds; release O1 combs and keyed rear links with local support; detach supported rear terminal conversion; hold carrier, release positive fasteners and draw rearward within reserved stroke; replace card and reverse order; run specified continuity and later authorized calibration checks. No owner soldering, energized disconnection or routine middle-board removal is acceptable. **This sequence is conditional until solder-terminal conversion and exact latch access exist.** Powered calibration is a later separately authorized safe bench operation and never part of replacement.

One electrical rear design may repeat across O1–O5 only after interface/package mapping proves it. Mechanical variants include O2/O4 selector depth/orientation and harness length, O1 edge versus interior supports, shared feed entry and neighboring function obstructions. VCF/VCA require protection and local loop boundaries; ENV/offset need timing/hold/control locality; utilities need their own package/shared-service mapping. None is licensed by OSC geometry alone.

Next proof is a supported local middle test piece with both connector faces and continuous return, then two adjacent O1/O2 mechanical coupons retaining real front hardware and 3+2 selectors. Exact production sources, net/Ref-pin parity, component solids, route/return checks and physical assembly are separately authorized future work. #55/#65 stay open. Recommendation: **REVISE**, primarily connector/services, package capacity and enclosure support evidence; do not adopt on these drawings.
