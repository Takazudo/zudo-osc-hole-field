# New outline study: source progress, acceptance still open

This stage starts at PR286 checkpoint `4c0c5ffb4e4785b097680150fd1a18fb267f8a8d`. It changes only isolated implementation sources. PR285, canonical boards, all438 fixed panel centres, five oscillators,33 functions, KEEP_K1402_INCUMBENT and parked260/277 are preserved. No native, merge, adoption, fabrication or energized work is performed.

## Independent identity and requirement audit

`stage3-crossing-audit.json` independently maps all five oscillators to live canonical source, including previously omitted explicit O3/O4 mappings. It compares1435 oscillator and42 shared units,495 modeled signal endpoint rows across the retained alternatives,528 return groups and80 locked panel UIDs. No instance/ref/pin/net/UID mismatch was found. O1 template labels in assembly reports are now paired with exact actual identities; for example the old controlling O5 PWM-wiper path is RV508:2→R1525:1,488.311094mm. Its decomposition is16.002691 front trace +15 GH contacts +63 wire +295.209809 middle trace +25 DIN +74.098594 rear trace. Its307.68mm direct endpoint separation is independently fatal at those old locations.

Every modeled signal crossing, including PWM and raw wipers, retains300mm and1nF. Power/returns retain their distinct impedance/current/drop requirements; they are not given a blanket signal-length exemption or qualification. All nine shared nets retain aggregate five-instance capacitance obligations. Direct capacitance is unknown; the octave1kohm/100nF receiver dynamics remain separate from the direct1nF aggregate budget.

## New family and local refinement

`direct-study.json` specifies a new44×238mm outline, five side-by-side origins, four whole-cluster orders, three vertical origins, five connector centres and two connector orientations. This is120 new arrangements for each of two local-placement variants,240 cases total. It does not rerun the exhausted3840 fixed-slot permutations. Card outlines, complete clusters and connector locations move jointly; these dimensions are proposals, not requirements. All use the unchanged50/69.2/105mm depth stack,40mm withdrawal and100mm external workspace.

The independent bypass refinement retains154 whole packages,193 units, eight cluster boundaries and six original local trim axes. Worst actual supply-pad distance improves20.286→6.504mm. This is not a general electrical improvement: TIMING_CAP span grows12.513→13.516mm, HF_PIN7.963→13.776mm, TRI_RAW16.374→44.874mm and SINE_REF5_FB18.355→27.409mm. Every non-rail rear net's before/after endpoints and spans are retained. Return-plane loops, stability and routed copper remain unqualified. Both local-placement variants are compared, with neither adopted.

| New family best | O1 maximum | O2 maximum | All-five maximum | Rows above300mm |
|---|---:|---:|---:|---:|
| Original local placements |295.860|291.058|334.018|38|
| Bypass-refined placements |299.322|294.521|336.199|50|

Each best result includes all225 actual-pad signal paths, exact live identities, a common injective26-signal DIN mapping,26 adjacent return contacts, all240 recomputed return branch records, all nine shared aggregate budgets, and the retained full power/load/return inventory. Stored power inventory coordinates are explicitly in the prior compact frame, not the new geometry; new rail topology and impedance extraction remain OPEN. Every interface/routing allowance is unchanged:63mm wire,15mm GH,25mm DIN and1.15 octilinear geometry +5mm +2×1mm endpoint tolerance per copper segment. Existing front-wire minimum service slack is retained. Positive rear mechanical service clearance is not established.

The new baseline's controlling O5 LOCAL_REF5 path is RV507:3→RB1510:2:13.850673+15+63+156.369026+25+60.798599=334.018298mm. Direct separation is142.094285mm, so this result is a failure of this allocated interface/layout family, not a universal geometric impossibility proof. The refined variant's O5 PW-wiper path RV507:2→R1533:1 reaches336.198722mm. O1/O2 numerical margins alone do not qualify either arrangement.

## Occupied volume and mechanical blocker

All28 other functions are explicitly reserved:4766 retained packages, including2572 K-board packages across24 functions. B1/B2/X1/X2 occupy other boards; they are not missing or free space. Their new architecture placement/depth has not been specified. No unknown region is treated as available. Retaining the old K board at100..101.6mm intersects the proposed rear withdrawal sweep; its rear component allowance reaches106.6mm, beyond the105mm cover. This requires engineering placement/service work, not an invented owner waiver.

The local per-card courtyard/fixture screen passes, but it excludes the occupied middle assembly. The independent full screen identifies O2's DIN-body reservation overlapping the shared-reference island on the same middle rear face. The350 inherited hardware Z projections remain unresolved; a 2D overlap alone is not automatically a physical collision. See the separate stage3 mechanical screen for exact package intersections and classifications. Both variants have four same-face DIN conflicts (U1601/C1601/C1603/R1615),14 opposite-face DIN/GH projections and unresolved through-contact keepouts. The proposed two handles are16mm apart against an inherited20mm finger envelope, leaving a4mm grip-envelope overlap per card. Their grip procedure also needs revision. Both variants are RESERVED and unaccepted.

## Separately costed split-interface comparison, not selected

A possible comparison uses two fully populated96-position DIN mating pairs per rear card, partitioning the same26 signals into13+13 with matching adjacent AGND returns. No extra signal or return net is invented. Compared with one pair, this is192 versus96 mating positions,384 versus192 solder terminations,26 signals,26 AGND positions and140 versus44 NC positions per card. Across five cards it adds480 mating positions and960 solder terminations. The17 front GH links,54 conductors and108 crimps per oscillator are unchanged.

A bounded support proposal would add four fixed mount anchors, two guides and two captive retainers per card; removal/reinstallation would add two retainer releases and two refastenings, plus one additional connector unmating/mating engagement (potentially simultaneous). These counts are proposal costs, not manufacturer-qualified mounting geometry or demonstrated serviceability. Both connector sets, all52 active contacts per card, every return corridor, mechanical alignment/load distribution, support keepouts and swept volumes would need explicit source placement. No path reduction, qualified contact resistance, current sharing or capacitance benefit is credited without that model. This stage does not adopt a split interface or silently remove interface allowances.

Core-only front-copper reuse remains the retained comparison. It avoids assuming the new populated front rearrangement is selected, and still needs its own complete physical/path comparison.

## Next bounded work and acceptance

There is no feasible candidate established here. The smallest next engineering step is to allocate the shared-reference island plus all remaining28 functions and their service volumes in the unchanged depth stack, then jointly place direct connectors and complete rear clusters against that occupied model. Use the retained local-net tradeoffs to constrain timing/feedback/bypass placement together. Only then compare a separately modeled split interface or an explicit enclosure-change proposal. No owner decision is necessary merely to continue this source study; any architecture/enclosure adoption or limit change requires a concrete later decision. Native routing cannot cure the demonstrated missing volume and source allocation evidence.

Stage1 and issues278–284 remain OPEN. Native KiCad10.0.6, ERC, DRC, routed parasitics, mechanical solids/mating/service tests and physical validation are NOT RUN. Installed KiCad9.0.2 is not exact-version capability or admission. No native campaign or default CI/regen-all is triggered. Local deterministic, mutation, documentation and independent review receipts are recorded separately; passing them does not establish electrical or physical acceptance.
