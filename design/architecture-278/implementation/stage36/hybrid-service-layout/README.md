# A01 hybrid: numbered IDC maps and revised support source proposal

This bounded continuation of `51aa218dc5eb17c22fd13531e04c115da87c8520` completes the numbered compatibility maps and removes the known control-carrier/access conflict in a revised support candidate. **It is not a complete collision-free instrument design.** Exact closed strain-relief geometry and neighboring installation datums block those dependencies. No canonical circuit/BOM/manufacturing, front positions, current editor or historical evidence changes.

[Support illustration](support-layout.svg) · [Deterministic proposal and coordinates](proposal.json) · [Maker CAD findings](cad-report.json) · [Sources](sources.json).

## Numbered compatibility

Both ends are bound directly to `stage17/generated/transport-component-rows.json`. A new board footprint and cable assembly would still require adoption; these are proposal maps, not changes to existing copper. Every original numbered net is preserved, with no added parallel returns/current credit.

| Link and references | Exact Würth header / strain-relief socket | New pin → net | Extra contacts |
|---|---|---|---|
| C-SIG J17901/02 | 61201021621 / 61201023021 | 1 REF5; 2 REFN5; 3 IN_REMOTE; 4 Cc045d2_W; 5 C38cac0_W; 6 AGND | 7–10 NC |
| J-PWR J17903/04 | 61200821621 / 61200823021 | 1 +12V; 2 −12V; 3 +5V; 4 AGND | 5–8 NC |
| J-SIG J17905/06 | 61201421621 / 61201423021 | 1 REF5; 2 AGND; 3 REFN5; 4 IN_BUFFER; 5 OFFSET_BUFFER; 6 SUM_NEG; 7 AGND | 8–14 NC |

Signal names carry `/A01/` prefixes in JSON. REF5/REFN5 remain references, **not supply rails**. J-PWR8 is a project-specific internal map, not conventional external power. Rear K-PWR remains the separate prior proposal: +12V,−12V,AGND and no+5V. Mechanical MP1/MP2 are not reassigned to extra contacts. NC means isolated connector contacts with no proposed copper; continuity must remain pin-for-pin through the cable.

Maker mating-face drawings: header key below, pin1 lower-left and2 upper-left; socket key above, pin1 upper-left and2 lower-left. In a centered drawing coordinate frame with X right/Y up, socket-to-header is `(x,y)→(x,−y)`, reversing face normal. Exact counts/spans come from the article table, not generic sketch hole counts. J-SIG local header rotates90°; all other local/middle headers rotate0°. Generated global pad coordinates and both face coordinates make this explicit. Pin1 stripe identification and equal-number continuity at both cable ends are required; a visible ribbon fold is not proof of mapping. No current or protection qualification follows.

## Exact source geometry and stopped closure dependency

All three exact header/socket PDF pairs and unmodified maker STEP pairs were inspected. 8/10-pin models were acquired in this task;14-pin models reuse bound receipts. Header board seat nativeZ−4.675, inner floor−2.075 and socket faceZ7 give nominal6.5 mm socket entry and9.6 mm seated socket-body top above the board. This is nominal source geometry, not contact-travel or force qualification.

Native STEP **Y180°,Z+4.925** makes matched8/8,10/10,14/14 socket/header plastic bodies disjoint. Blindly applying drawing-frame X180° to native STEP gives15.803809 mm³ plastic collision for each. This confirms native axes cannot be treated as drawing face axes; plastic matching alone does not number contacts. Electrical orientation is separately anchored to the explicit numbered maker diagrams.

The supplied full socket assembly remains an **open termination/relief state**, reaching18.3 mm above the seated board in all three exact counts. This now replaces the previous8/10 family extrapolation with exact-model evidence. It is still not a closed mated height or a guaranteed worst-case envelope.

The drawing's `Close 6.9` dimension is not an unambiguous assembled strain-relief datum. A naive cap translation+3.8 mm from that dimension produced body intersections172.679/207.261/270.504 mm³ for8/10/14; retained as **rejected**, not a closed model. The raw supplied model itself has small latch/body overlaps; no physical interference verdict is inferred from idealized snap details. Do not shrink the routing envelope to9.6 mm or the rejected closure result.

**Smallest input for this dependency:** an assembled manufacturer drawing/model, or three unpowered measurements (one per exact8/10/14 assembly) of (a) highest fully latched strain-relief Z above its seated PCB and (b) cable exit center plane and direction, using the actual ribbon. These dimensions resolve the layout datum; maker cable bend limits and cut tolerance remain separate. Stop finished cable routes, bends/cut lengths and final cover depth until these inputs exist. No supplier contact or purchase was made. Stock remains unverified.

## Revised support geometry

The24 mm Samtec/Würth970240321 middle/core proposal and four spacer sites are retained. The prior conditional engagement budget is unchanged; no new stiffness or50 N pass is claimed.

- **Middle:** two ordinary8×4 mm crossbars, x242–314,y176–184 and270–278,z44.4–48.4, support the PCB underside at48.4. Four M3x10 lower screw proposals through4 mm bar+1.6 mm PCB give4.4 mm nominal engagement into7 mm spacer thread. Install these before seating the middle frame; no in-place underside tool access is claimed. Exact screw/head/washer remains a mechanical detail to select before adoption.
- **Explicit rail change:** the crossbars originally intersected retained rails by1.6 mm. The new proposal **cuts1.6 mm-deep seats from z44.4 to46 in the retained middle rails**, limited to each crossbar's XY footprint. `effective_support_solids` subtracts those pockets and checks the resulting solids against the crossbars. This is a new rail-machining proposal, not silent acceptance of overlap. The remaining rail depth is10.4 mm locally; strength, fastening and joint tolerances remain unqualified.
- **Control:** retain upper rail portions to y289; offset lower sides to x203–206 and231–234; use a mounting bridge x203–234,y306–310,z18–20, and bottom crossmember x203–318,y314–320,z18–20. Move the proposed enclosure cleat to(315,317), requiring a new y322 minimum internal reservation. Existing enclosure remains unchanged. The tab endsy312, leaving2 mm nominal XY separation from the bottom member. The expanded header/access screen ends beforey306. The old lower members/anchor and old fastener arrangement are explicitly removed in this candidate.
- Control carrier members are modeled as a **single joined-frame material union**, not separate stock bars occupying each other's volume. Joint/weld/gusset and fabrication details are not qualified. This is an internal support revision; no custom connector alignment fixture is proposed. Prefer ordinary bar/angle fabrication when detailing that union.
- Control mounts(213,308)/(224,308) use6.4 mm post proposals from board rear11.6 to bridge18, with3.4 mm bridge holes and Ø6 rear driver reservations. Fastener/nut selection remains open. Bridge holes allow assembly from the rear; do not drive through solid bridge material. Pot body cradles and fixed shafts remain unchanged.

The preceding report's shorthand “tab conflict” included access/fastener interference: the PCB itself atz10–11.6 does not intersect the old crossmember startingz12. Its1 mm-expanded header/access envelope does intersect the old member. This continuation distinguishes the two rather than claiming an unobserved PCB collision.

Known-source screen: revised supports against A01 PCB solids, fixed LED substrate, pot-body rectangles and expanded connector/tail envelopes; new crossbars against explicitly pocketed retained rails; spacer/tool projections against package courtyards. These lists are empty. Source courtyards with unknown package heights, unmodeled joint fasteners and unknown neighbors remain exclusions, not cleared solids. The closed IDC, full finger/tool sweeps and removal/parking procedure remain unqualified.

## Neighbor evidence and exact remaining inputs

The138 original projection rows represent85 distinct fixed hardware references. Existing Bourns PTV09 source/datum supplies **21 neighboring pots' relative body range−6.8..0 and rear-shaft0..3.8 mm** from their rear seating plane. These values are now retained per reference; no absolute installation Z is invented. The inherited conditional PCB plane20 is not a measured installation datum. The source footprint supplies XY, not the entire terminal/harness solid.

New control right supports overlap RV1408's occupied/unknown projection; retained upper rail projections also include RV1407. Thus the revised control carrier is **only cleared against known A01 solids, not approved in the instrument**. Stop this dependency until the rear seating Z and furthest terminal/harness Z for RV1407/08 are supplied; the body/shaft dimensions themselves need not be remeasured. If the neighboring seating plane were20, its body could occupy13.2–20 and conflict with the proposed right rail: this hypothesis is explicitly not accepted as free space.

The upper middle crossbar projects over SW1501/1601/1701/1801. Required input is each exact installed switch seating datum and furthest tail/harnessZ; part height alone cannot place it. The lower crossbar projects over the listed PTV09 rows in `unknown_support_projection_hits`; their body/shaft ranges can be placed once seating datums are known. Neighbor functional-board allocations still lack complete populations/depths. No conceptual neighbor box is deleted or labeled free.

**Next useful source work after these small inputs:** adjust only the affected carrier branch if RV1408 conflicts; bind closed IDC exits and split the ribbon corridors; then place supported housing grips, cable parking and the7 mm disengagement/40 mm core withdrawal sweep. Independent mapping and known-support corrections in this checkpoint are complete; it does not pretend the blocked dependencies are solved. No unpowered mock-up construction, order, energization or native manufacturing check was performed.
