# Populated A01 ordinary-header / IDC proposal

Recommend the **24 mm middle-to-core spacing** candidate shown in [layout.svg](layout.svg), for an unpowered A01 assembly study only. This is not a whole-instrument fit approval. No canonical circuit, BOM, copper, panel, enclosure or manufacturing output is changed. The delivered editor is preserved byte-for-byte. P37 is a drawing identifier within Stage36, not an adopted new stage or hardware revision.

## Population and coordinate contract

`layout.json` binds the historical inputs by SHA256. Canonical A01 remains 90 references. The latest **unapplied Stage26 candidate is 118 references**, reconciled exactly as Stage15's 86 package placements plus Stage17's 10 transport connectors and 22 wire lands. Selection of the118-reference population is an engineering proposal, not owner adoption. This deliberately includes the larger C7101/C7102 and RN7101/RN7102 candidate packages, and excludes the six superseded R7121–R7126. Courtyards/pad extents are conservative XY screens, not fully measured 3D bodies. All 22 wire lands remain; no circuit remapping is adopted.

Global coordinates and boards follow Stage10. Jack remains z35–36.6; middle z48.4–50; control z10–11.6. Proposed core moves from z69.2–70.8 to **74–75.6**, +4.8 mm. All its package pad coordinates move with it. Core XY remains x236–312,y174–282.

| Interface | Proposed center (x,y) mm | Exact proposed part |
|---|---|---|
| Middle/core signal16 | 295,220 | TSW-108-18-L-D / SSW-108-01-L-D |
| Middle/core power8 | 295,250 | TSW-104-18-L-D / SSW-104-01-L-D |
| Jack J-SIG14 / middle | 208,108 / 258,154 | 61201421621 |
| Jack J-PWR8 / middle | 212,170 / 292,154 | 61200821621 |
| Control C-SIG10 / middle | 218.5,297.5 / 274,286 | 61201021621 |

The 18.3 mm IDC depth used in the drawing/route endpoints is a **provisional open-termination/relief-state screen**, not a verified closed mated height. Its extension to8/10-pin parts is unverified; all three exact mated heights and exit coordinates remain UNKNOWN. The illustration omits the22 retained wire lands and fixed LED substrate; inventory preservation is not a graphical/full-solid clearance check.

IDC mates/cable qualification remain as in the preserved practical-IDC study; header part numbers alone do not specify a complete cable assembly. Ordinary connector rectangles are conservative 5.5×21.2 and 5.5×11 mm screens. Signal has eight independent signals and eight AGND contacts; K-PWR is independently +12, −12, AGND, then five unused contacts. There is **no +5 V on K-PWR**. J-SIG7 remains jack-to-middle. The24-contact direct-header binding is the only pin audit generated here. Full14/8/10-pin IDC pad/net maps, including the10-pin adaptation of legacy6-signal C-SIG, remain unresolved; circuit counts do not establish those mappings. Generated contact coordinates mirror the opposite socket face. These are project pad-numbering requirements, not a claim that an unverified library footprint or vendor drawing orientation is already correct. Verify pin1 against the actual pair before footprint adoption.

## Why 24 mm

Samtec TSW -18 exposed post18.29, body2.54, and SSW socket8.51 give insertion `2.54+18.29+8.51-gap`. SSW catalog specifies insertion3.68–6.35. With three ±0.13 dimensional allowances, spacer±0.2 and **assumed aggregate seating/bow±0.2**, the conditional results are:

| Gap | Insertion interval mm | Decision |
|---|---|---|
| 12 with earlier short-pin pair | Earlier screen only | Not preferred for populated assembly access |
| 24 with long Samtec pair | 4.55–6.13 | Inside insertion range; 0.22 upper margin |
| 25 with same pair | 3.55–5.13 | Fails minimum by0.13 |

The resulting feasible nominal-gap interval is **23.78–24.87 mm** under these assumptions. This is not a proven tolerance budget: measured seating/bow must fit the assumed allowance. TSW drawing tow/sway2° can imply approximately0.64 mm lateral tip displacement over18.29; the four spacers do not establish connector registration or stiffness. Do not force mating. TSW catalog's lead-wave-only process warning must be resolved against the intended assembly process; no lead-free wave process is approved. Catalog current ratings are not installed-circuit or fault-current qualification. Stock and exact procurement availability are unverified.

Use four ordinary **Würth970240321 M3 female/female 24 mm steel spacers**, proposed centers (254,180),(300,180),(254,274),(300,274). Manufacturer drawing wrench size5.5, thread depth7. Proposed holeØ3.4 and Ø8 tool reservations are engineering allowances. Screw length/head/washer and actual driver must be selected and checked before drilling. 970250321 is the rejected25 mm comparison. Spacer tolerance assumes ISO2768-m length range6–30; confirm supplier interpretation.

## Supports, access and removal

The old rear carrier rails are removed **only in this proposal**. New spacer sites clear source package projections, but do not coincide with all old frame rails. A load path from the four sites to the middle carrier/backer is therefore still required; the populated PCB is not credited as a 50 N structural support. A plain bench backer can hold an unpowered mock-up, but does not prove installed retention. No bespoke alignment fixture is the default solution.

Control requires a NEW lower PCB tab x206.5–230.5,y290–312 and relocated mounts (213,308),(224,308). The existing control crossmember y303–313,z12–20 conflicts with that tab/fasteners and must be revised in a later proposal. Fixed controls retain their positions. This is additional unadopted hardware, distinct from the owner-approved earlier rear-face study.

Assembly: attach middle board to supported backer; install front IDC headers and verify latch/finger access with the core absent; dress the three ribbons in individually tagged reservations; loosely register core over both ordinary headers; mate axially without force; seat and fasten four spacers. Proposed grip is at core's two side edges with the cover removed; actual finger volumes are unknown, so use a temporary supported handle for the bench measurement and do not claim in-case hand access.

Removal: remove cover, support core continuously, release four fasteners, withdraw axially at least7 mm (exceeds conditional6.13 engagement), then to total40 mm, reaching board z114–115.6. Park the core externally on an insulated support; it must not hang from headers or ribbons. Disconnect front IDC by housing after the core is clear, then service front boards. Core removal path, screw-driver approach and housing grip are reservations awaiting the integrated mock-up. A cover innerz110 is only a comparison proposal (+5 from105); unknown component heights prevent declaring it sufficient or necessary. No cover change is adopted.

## Neighbor and cable limits

Every corridor in `layout.json` is explicitly `ROUTE_RESERVATION_NOT_FREE`. The generated list records intersected other-function board envelopes, including W1/M4B and adjacent A02–A06/E blocks. There are also **138 foreign hardware projections with unknown depth**. The C-SIG broad reservation overlaps the core projection by0.75 mm at its lower edge; a routed split volume below the core and then beyond y282 needs a new bend/exit model. This has not been waved away as free space. Other-board envelopes are conceptual allocations, not a populated component survey.

Therefore this candidate does **not** close ribbon length, cut tolerance, bend radius, sleeve behavior, service slack, neighboring clearance, housing exits, or parking during withdrawal. No invented ribbon/wire radius or cut length is given. Preserve the earlier Stage35 cover/service findings; this proposal does not supersede them with a nominal cable fix. Source work can next model split cable corridors and exact IDC mate/grip geometry once the neighbor depth and cable data are available.

## Preserved first failures

The first jack power location (224,108),9.5×18.02 intersected D7101,D7102,R7127,R7128,R7130. Moving it to (212,170),long axisX removed those source intersections. The first control header at (218.5,295) intersected RV1308; moving to297.5 required the explicit new tab/mount proposal. The25 mm option fails the stated engagement tolerance screen. Zero final source package intersections does not erase these failures or establish full solid clearance.

## Practical unpowered decision sheet

1. Inventory the actual118-reference candidate versus canonical90 before preparing a mock-up. Measure missing component heights, adjacent hardware XYZ, cover inner surface and frame crossmember; until recorded, mark their volume occupied/unknown.
2. Measure actual spacer length, PCB thickness/bow and seating at four sites. Accept the assumed engagement screen only if their combined additional seating/bow deviation is ≤0.2 mm and measured insertion stays3.68–6.35 at both connectors throughout tolerance extremes. Verify all24 contacts/pin1 with continuity, separate supplies and no unintended shorts, unpowered.
3. Measure long-pin lateral offset and housing parallelism; reject any forced mating, bent pin, incomplete seating or bow beyond the budget. Measure force/stiffness separately; no50 N pass is claimed.
4. With representative neighbor solids installed, demonstrate four-fastener tool access, supported7 mm disengagement and40 mm removal without collision. Demonstrate housing grip/latch release for all three IDC links and external insulated core parking; reject a procedure that pulls cable conductors or loses support.
5. Obtain the actual cable construction, maker static/repeated-flex limits, thickness and cut tolerance. Measure each straight housing exit and full installed/service centerline at all extremes. Allocate cut tolerance and slack explicitly; reject any bend below the applicable maker limit, sleeve migration, tension at withdrawal, pinch or neighbor contact. No cable should be cut from this source-only report.
6. Only after those results choose cover depth and permanent support/crossmember changes. Existing105 mm cover remains canonical. No energization, fabrication, order or native CAD check is authorized by this study.
