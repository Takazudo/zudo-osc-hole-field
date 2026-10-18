# Ordinary headers versus ribbon IDC — source planning checkpoint

Baseline `5f86e5b38f6399965daa82213bdfa54fe290bd0c`, draft PR287 / Issue278. The panel editor and all historical studies are unchanged. This is an unadopted connector architecture recommendation, not a BOM, manufacturing change or fit approval. Owner preference: start with ordinary 2.54 mm headers/sockets, allow extra spacing/depth, and avoid unnecessary special connectors or custom anti-misconnection fixtures. No special connector is justified by the evidence below. GH4 coupon remains NOT ORDERED / DEFERRED / not a gate.

## Recommendation

Use **ordinary direct header/socket mating for overlapping boards that can be removed as a stack**, with ordinary screw spacers carrying mechanical loads. Start the next source layout with A01 middle/core direct mating; use **ribbon IDC for spatially separated boards or boards needing independent removal**, notably the jack/middle link. Do not require cables merely because prior studies used them. Conversely, do not move fixed jack/pot positions to make a header fit. The current studies do not yet contain enough populated-board geometry to adopt either placement.

For a direct A01 link, an internal 2×4 signal pair can carry the existing seven J-SIG nets plus one NC; a separate 2×4 power pair can carry +12, −12, +5, AGND and four NC without changing return topology. Counts are proposals, not an external power standard. Keep existing net identities and do not assign extra grounds or parallel rail capacity by assumption. Number each mating face explicitly and bind pad-to-pad net correspondence before layout. For a cable link, retain the researched 16-pin power + 14-pin signal option (8-pin internal power alternative) in [practical IDC research](../practical-idc-layout/README.md). Neither its full pin map nor routing is adopted here.

| Architecture | Parts and assembly effort per interconnect | Service / layout consequence |
| --- | --- | --- |
| Ordinary direct pair | One male strip and one socket, soldered; shared ordinary spacers/screws; no cable, crimp or IDC press | Align both boards; remove accessible screws, support both boards and withdraw axially before the historical 40 mm core-removal move. Board component clearance and spacer access determine the stack. |
| Ribbon IDC | Two board headers, two cable sockets/reliefs, correct-count 1.27 mm ribbon; square cut, two press operations, numbered continuity/short inspection | Boards can separate independently after unplugging at an accessible edge; reserve connector body, grip and bend/parking space. Raw ribbon is not a finished assembly. |
| GH or other small specialty family | Smaller pitch, exact housings/contacts and termination tooling or sourced assemblies | Only revisit if a demonstrated occupied-space conflict defeats ordinary options. No such necessity established here. |

The direct pair removes cable length/cut tolerance, bend-radius, sleeve, slack and cable-support problems **on that replaced link only**. It replaces them with board spacing/alignment and axial extraction requirements. It does not resolve the remaining flexible links or establish carrier stiffness.

## Owner's Tayda references: what the attached drawings actually establish

[Tayda A-1389, 1×6 female](https://www.taydaelectronics.com/6-pin-2-54mm-single-row-female-pin-header.html), [A-195, 2×20 female](https://www.taydaelectronics.com/2x20-pin-2-54mm-double-row-female-pin-header.html), and [A-196, 1×40 female](https://www.taydaelectronics.com/40-pin-2-54-mm-single-row-female-pin-header.html) identify ULO/FH series, but give descriptive MPNs rather than complete variant codes. All three attach the same **FH411.pdf** drawing: body height A=8.4 mm, tails 3.0 mm, width 2.54 single / 5.0 double, length `2.54N+0.5 ±0.3`, where N is positions per row. Thus lengths are 15.74±0.3, 51.30±0.3 and 102.10±0.3 mm respectively. Drawing has no height tolerance, mating insertion interval, electrical rating or exact 0.64-square acceptance statement.

[A-198, 2×40 male strip](https://www.taydaelectronics.com/2x40-pin-2-54-mm-double-row-pin-header-strip.html) attaches A-198.pdf: 0.64 square pins, 2.54 pitch, 2.5 body height and 5.0 width, but table B lists many **C/D pin-length variants**. Type1 has C=3.0 / D=6.10; the seller page does not select Type1. Neither a unique mating length nor a 3 A rating can be assigned to A-198 from that drawing. A nominal 8.4+2.5=10.9 mm housing-abutment height is therefore only an illustration, not a selected spacer or an electrical mating guarantee.

These are useful low-cost procurement starting points. Seller pages are listings, not verified regional stock or a locked quote. Long female strips require cutting/waste and inspection; do not assume a clean breakaway socket or zero lost positions. Prefer an exact-count socket when practical. Resolve the supplied male length and the socket's matching pin specification before choosing a spacer. This is ordinary part identification, **not a requirement for a new component qualification campaign**. No supplier contacted, cart changed or purchase made.

## Documented ordinary pair and spacer arithmetic

Würth **61300821121** (WR-PHD 2×4 male, rev002.000 2025-11-08) and **61300821821** (WR-PHD 2×4 socket, rev001.004 2022-07-11) are ordinary 2.54 mm through-hole alternatives with manufacturer drawings, not a specialty architecture requirement. Exact PDFs/hashes in [sources.json](sources.json), visually inspected page1; page2 gives 3 A rated current and 25 mating cycles for each. This rating does not establish A01 fault current, equal parallel sharing or the thermal capacity of a complete assembly. No stock/price or explicit paired-system qualification is asserted.

Male: body 2.54±0.15, exposed mating pin 6.0±0.20, tail 3.0±0.20 mm, nominal 0.64 square. Socket: height8.5±0.2, tail3.1±0.2, section dimensions2.25±0.15 to the upper contact region and6.11±0.15 to the lower cavity region. Lengths10.16±0.3 /10.66±0.3; both width5.08±0.15. These section dimensions are **geometric bounds, not a manufacturer specified working insertion range**. Pin/aperture tolerance acceptance, spring deflection and contact wipe are not established by subtracting nominal widths.

Let S be facing PCB surface separation, M male body height, P exposed pin, F socket body height. Geometric pin penetration is `d=M+P+F−S`. For the drawing extrema, `M+P+F=[16.49,17.59]`. Conservatively asking the tip to pass the deepest upper section (2.40) and stop before the shallowest lower section (5.96), plus a **proposed ±0.10 mm total separation tolerance** (spacer, seating and local bow combined), gives a necessary screening interval:

`11.73 < S_nominal < 13.99 mm`.

Housing nonintersection separately requires `S_min >= M_max+F_max=11.39`. A **12.00±0.10 mm illustrative spacer stack** yields d=[4.39,5.69] and ≥0.51 mm between housings. It passes this axial geometric screen only. The ±0.10 is not measured or sourced spacer/bow performance. A 12 mm stock spacer is a procurement target, not an exact selected part. Full mating/contact acceptance and combined tolerances remain open; do not label this interval qualified. At nominal12 the 1.6 mm upper board's far surface is13.6 mm above the lower facing surface, before component/tail heights. Pins must fully clear before lateral motion; allow >5.69 mm axial extraction for this scenario, with the actual assembly clearance margin still to be allocated.

## Fit against the retained A01 study, not imaginary empty space

[Whole-layout source](../whole-layout-review/view-data.json) contains **unadopted outer envelopes**, not populated board geometry. Its A01 jack is XY[195,94,240,182], z[35,36.6]; middle[232,142,314,292], z[48.4,50]; core[236,174,312,282], z[69.2,70.8].

| Link | Facing gap | XY outer-envelope overlap | Source implication |
| --- | ---: | --- | --- |
| Jack → middle | 11.8 mm | 8×40 mm | Near the illustrative direct-pair interval, but narrow overlap must also contain edge clearances, holes, components and extraction. No populated fit established; IDC is a practical first layout choice here. |
| Middle → core | 19.2 mm | 76×108 mm | The documented short-pin pair cannot even enter the socket: worst maximum reach17.59 <19.2. Direct mating needs a different ordinary long-pin variant or a revised core plane; current spacing is not accepted for this pair. |
| Control → middle | No XY overlap (5 mm x gap) | None | Ordinary opposing straight headers cannot connect these retained outlines without a board-outline/position change; use a flexible link as the starting point. |

A 12 mm middle/core facing gap would put the core near face at z62 and far face63.6 instead of69.2/70.8: **a new unadopted core relocation**, not a drop-in component substitution or permission to change canonical CAD. It could collide with components/supports; unknown volumes remain occupied/unknown. Alternatively keep or enlarge the existing gap and select a documented longer male pin. With the same M/F and the ±0.10 scenario, a male nominal length P with assumed ±0.20 tolerance needs **11.21 < P <13.47 mm at S=19.2** under the same axial screen. No exact long-pin MPN has been selected. A-198's multi-variant table is not evidence that its shipped part has that length.

The next source layout should compare these two ordinary direct-mating variants against actual populated middle/core geometry before selecting the core plane. Extra depth and board separation are allowed, with 5 mm neither target nor ceiling; increasing separation alone makes the short pins less suitable. The fixed front holes, pots and seated front hardware stay fixed. Earlier owner-approved rear-face study is preserved; these new stack/connector/support proposals are not adopted by that earlier permission.

## Alignment, service and current checks

Use one board datum and a mirrored mating-face pin map so every intended net meets its matching contact; pitch alone does not define orientation. Position spacers so screws are accessible with the cover removed and carry both boards during disconnect. Seat connectors without pulling misaligned boards into place with screws; inspect simultaneous entry at both ends. Quantify hole clearance, board bow and connector solder-seating tolerance before claiming the ±0.10 scenario. Do not invent a 1 mm registration allowance or use a connector as a structural retention post.

Proposed unpowered service sequence: support the frame and core, remove rear cover, disconnect/park any IDC links, access and remove core spacer screws, withdraw the direct pair along its mating axis until fully clear, then carry out the retained40 mm core removal. For jack service remove blocking boards/harness clips first. Every screw/tool/grip column, moved board, adjacent connector, cable parking volume and core-removal swept volume must be checked in the complete layout; neither a transparent viewer nor an outer-envelope overlap proves these clear. No new custom guide, collar or anti-misconnection fixture is the default.

Required ordinary checks are correct pin/net mapping, polarity, no shorts and suitable current/voltage/contact use. Optional misuse protection is a separate owner choice. Bare headers permit reversal/one-pitch offset; different counts do not prevent partial wrong insertion. Keyed IDC controls normal orientation but the earlier CAD shows possible wrong-size/partial mating; an external10-pin power plug can reach SIG14. Labels and accessible inspection reduce assembly confusion, not eliminate it. Residual wrong-port risk remains explicit for parent review, not a universal gate forcing custom hardware.

[A01 current ledger](../a01-current-ledger/README.md) retains conditional rail subtotals about20.621mA +12,19.421mA −12 and0.1041mA +5, with unknown load/fault terms. Each AGND full-return envelope is11.2915mA, not an equal-sharing allocation. These small planning values do not certify either 3A ordinary pair or the IDC chain (3A header /1A socket and ribbon). REF5/REFN5 remain references. Fault protection and patch-ground conditions stay open independently of connector architecture.

## Practical integrated unpowered decision sheet

Use an existing sample or the eventual ordinary prototype assembly; no mandatory standalone GH coupon or purchasing gate. Record exact parts, spacer length/tolerance, both board faces and connector orientations. These are assembly-fit observations, not a request to requalify standard connectors.

1. Measure assembled face separation at each connector corner, pin exposed length and socket height. Evaluate the selected drawing's mating range (or retain only the axial screen if that remains all that is known). Reject bottoming, incomplete contact engagement or forced board bow. Do not substitute the illustrative±0.10 for measurements.
2. Verify every pin-to-net correspondence and adjacent-pin isolation unpowered before connecting a supply. Record pin1 and opposite-face mirroring; reject reversal/offset. No energization authorized here.
3. Demonstrate screw and connector access with all neighboring parts present. Support both boards, unmate axially, then execute the full40 mm removal and jack-board access sequence. Reject lateral pin loading, unsupported board hanging, blocked fasteners or any occupied-volume crossing.
4. For each IDC link, record exact ribbon/socket, termination orientation, finished length/cut allowance, bend/parking envelope and strain-relief fit. Reject taut cable, force on contacts, trapped ribbon or dependence on a guessed bend radius. No repetitive-flex rating is claimed.
5. Record cover closure and all component/support clearances at measured bow/alignment extremes. Unknown occupied geometry is a hold for layout, not a pass. This integrated check cannot establish missing protection/current limits or a retention load rating.

Next cloud-capable work: populated A01 middle/core placement and spacer/tool reservations, exact long-pin ordinary-header sourcing if keeping19.2mm, mirrored net-map binding, and IDC layout only for the independent-service links. Minimal parent decision: accept this direct-first/hybrid direction, or prefer independently removable boards throughout. Exact hardware adoption and remaining measurements follow the dimensioned layout.
