# Revised connection and electrical design — 2026-10-15

The owner authorized design choices. Recommend short front flexible links, one supported direct-mating signal connector per rear core, and separate supported, insulated copper power/return straps with captive service screws. This is a concrete implementation candidate, not architecture adoption or physical acceptance. `revision-electrical-report.json` supersedes the earlier unspecified connector topology; historical reports remain intact. Generate/check with `python3 scripts/architecture278/revision_electrical.py [--check]`.

## Manufacturer candidates and limits

Select HARTING female **09032966824** on middle and straight male **09031966922** on rear. The manufacturer's [Mezzanine Selection Guide](https://b2b.harting.com/files/livebooks/en/PRD0200000100124/downloads/livebook.pdf), type C table, explicitly pairs these at **18.3–20.0 mm PCB distance**. Thus the mechanical candidate specifies 19.2 ±0.3 mm, not a guessed mating height. The [Type C catalogue](https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf), female dimensions, gives 94.9 ±0.1 mm length, 90 ±0.1 mounting centres, three rows at 2.54 mm pitch, 78.74 mm contact span. Reserve 100×15 mm, not a footprint inferred from pitch alone. Source is manufacturer documentation retrieved 2026-10-15; linked guide was searchable but direct download timed out, so final vendor drawings must be retained in the later exact-component evidence bundle before production.

[HARTING product data](https://www.harting.com/en-US/p/type-C-FE-pressin-WW162-96POL-AFS2-09032966411) establish type-C family bounds: 20 mΩ contact resistance, 2 A at 20 °C requiring derating, 90 N insertion. The [type-C cable variant data](https://www.harting.com/en-US/p/DIN-Signal-C096FC-B-09030963217) give 60 N withdrawal. These are family sizing assumptions, **not exact selected-pair force qualification**; obtain selected-pair tolerance, cycle-life/contact-ageing and mating instructions before releasing a footprint. No hot plugging. Separate support posts, connector flange supports and axial guide pins carry the insertion/extraction load; screw release and pull handles load the frame, not solder. Qualify guides before contact engagement and the ±0.3 mm support stack; unknown connector misalignment tolerance is not substituted by guide clearance. Retain all96 contacts. No missing-pin coding is claimed: polarize the separate guides with asymmetric spacing/diameter, so incorrect orientation is stopped before contact engagement; mechanical drawing must verify this. Card identity/slot labels additionally prevent O1/O2 confusion; electrical interchangeability remains a test.

Existing JST GH headers/housings/SSHL contacts remain the front-flex candidate: exact original MPN per path, manufacturer geometry and envelope in `interface-contract.json` and `design/connectors/jst-gh.json`. They preserve the 0.5 A/contact project constraint, even if a manufacturer nominal rating is higher. They are not selected for the strict main power/ground path. DIN direct mating eliminates the rear cable's crimps but adds 192 soldered connector pins and service force; it is not automatically simpler.

## Complete connection ledger and comparison scope

The generator conserves all 51 original conductors, their two original faces and pin polarity. All 11 front links terminate on the middle. Six OSC_OCT0–5 conductors end at the shared source on middle, avoiding unnecessary rear stubs. The remaining 45 conductor positions get explicit rear pins; three new shared references each get a signal and adjacent AGND, producing **51 active contacts**, 45 fitted NC spares and no removed contacts in a nominal96-way connector. Both male and female pin labels are identical *electrical labels*, not mirrored drawing coordinates; manufacturer mating-view footprint parity is a production acceptance test. Multiple existing AGND conductors remain counted individually. All source endpoints on each net stay in `interface-contract.json`; this is a transport mapping, not new circuit netlisting. Shared-source IC packages remain whole on middle. No timing, exponential sum, compensation, VEE5 or feedback loop is moved across the interface.

| Per O1 transport subtotal | Original single span | Prior literal two cables | Mixed before regrouping | All-direct conditional |
|---|---:|---:|---:|---:|
| Harnesses / fitted wire conductors | 11 / 51 | 22 / 102 | 11 / 51 | 0 / 0 |
| Crimps | 102 | 204 | 102 | 0 |
| GH header-to-housing mating locations | 22 | 44 | 22 | 0 |
| GH signal solder joints | 102 | 204 | 102 | 0 |
| DIN pairs / fitted contact positions | 0 / 0 | 0 / 0 | 1 / 96 | 4 / 384 |
| DIN solder joints | 0 | 0 | 192 | 768 |

These are full counts for the conserved signal/control/service transport comparison, not whole-instrument totals. All-direct means three independently supported front regions (jack, controls, octave adapter) plus core, each with a96-way pair: conservative populated hardware, not a claimed optimized design. Different locked front planes require extra adapters and axial insertion paths; reject this candidate in favor of front flexibility. Core-only retains original front copper and front links; replacing the rear disconnect with DIN has the same transport subtotal as mixed, but requires retained-board adapters and their additional component/solder/support inventory before claiming equal complete burden. Existing195/911/1822 plus18 main-power wires remains historical whole-instrument baseline, not extrapolated savings.

**Add power rather than hide it:** two powered owners (front jack and rear core) × four separately fed nets (+12,−12,+5,AGND) give8 candidate copper straps,16 bolted contact interfaces,16bolts,32washers,16locking elements and16 strain-relief points. This common design bill is additional to every new-topology signal subtotal; exact existing baseline factory-wire lengths/terminations are not established by the51-signal-conductor figure. Source feeders remain shared, not multiplied by oscillator. The report preserves all36 factory terminals with original locations/net/pin: none is silently turned into user I/O. Keep their factory source/feed terminations on supported middle infrastructure; rear core gets four removable bolted tabs instead of owner-soldered wires. The passive O1 control board has no rail feed; its references and AGND remain in the51-conductor ledger. Front boards retain independent support and flex/formed strap strain relief. Four core straps mean eight contact interfaces, but only the four card-side captive screws are opened during replacement; fixed middle ends stay attached. Contacts, screws and connector pins are not structural card mounts. These arrangements need enclosure tab/insulator/tool detail before a hardware build.

GH header mechanical hold-down solder pads are **additional**: two per header gives44 original/mixed and88 literal-two-cable joints. DIN flanges use mechanical fasteners rather than solder hold-downs: four per pair. Add independent card guides/posts/retainers/pullers from mechanical bill; do not hide them as connector hardware. Actual harness cut lengths are taken from the revised mechanical routes when available, never51 times an arbitrary average. Continuity test covers every active pin and NC isolation before power; code checks conservation, not assembly. Assembly includes separately populating/test front boards, mounting supports, wiring middle, fitting straps, inserting core axially, torquing contacts/retainers, then checking continuity/insulation/resistance. Replacement is power-off, external patch sources isolated, discharged and voltage verified; detach four power tabs, release retainers, operate axial pullers and withdraw core. No routine middle removal or owner soldering.

## Electrical choices and bounded results

A single20mΩ DIN contact alone exceeds0.5mΩ combined branch+K ground and1mΩ rail limits; **reject DIN as the qualified main power/return path**. Parallel signal-ground contacts provide local return continuity but earn no strict-resistance credit. They do not permit a floating ground when power tabs are open; all supplies and external sources must be isolated for service. No contact-current sharing assumption is used.

Propose supported insulated copper straps with10×1mm cross-section and a50mm developed-length core design example. Copper at60°C (ρ20=.01724 Ω·mm²/m, α=.00393/K) gives0.09975mΩ bulk. Allocate at most0.10mΩ to two bolted interfaces, leaving0.30025mΩ of the unchanged0.5mΩ return limit for **all** common feed, middle spreading/vias and local core return. This is challenging, concrete and falsifiable. Contact allocation is a design requirement, not a manufacturer promise: four-wire assembled resistance, temperature/ageing, torque/locking and load-cycle validation must establish it before powered acceptance. Longer front straps must be resized by the same equation;50mm is not silently assigned to every route. Source regulation, each common edge, every owner branch, load and full return appear in eight explicit paths, including the two shared-middle ±12V reference load paths charged26/26mA once in the report. Per-state maxima remain null because lumped allowances cannot determine device startup/fault current. This revision does not invent full-load closure. Maintain20mV hot and0.20V complete-path budgets, and #57/#59/#65/#247 ownership. The prior704.5mA all-five sum-of-magnitudes envelope is not a fault maximum.

Five raw wipers remain raw. At assumed+20% pot tolerance, FM/PWM worst Rth=3kΩ, TUNE/FINE/PW=30kΩ, before source/contact additions. Remote1nF alone contributes3/30µs. The actual1kΩ local series resistor and10MΩ fail resistor apply to allfive; TUNE/FINE/PW additionally have10nF atW_SENSE, producing nominal local τ≈309µs at30kΩ source resistance, versus no such10nF onFM/PWM. Total response is a two-node network, not the remote-capacitance pole alone. At4/31kΩ total resistance,1nA produces4/31µV,10nA40/310µV. A proposed100µV additional leakage allocation requires≤25/3.23nA. Existing10MΩ pull-down separately attenuates about0.040/0.309% at these source resistances; this existing control-law loading is not connector error. These are actionable receiver/cleanliness/probe requirements, not guaranteed amplifier maxima; voltage/temperature-dependent bias, pot source impedance and nonlinear paths still require exact-part review. Keep≤300mm/≤1nF complete paths; a10MΩ probe on31kΩ is roughly0.31% incremental loading, unacceptable to infer precision calibration. Use high-impedance measurement at existing buffered test nodes where possible. No wiper buffer or circuit change is silently inserted.

Shared octave dynamics are now calculated separately from900pF direct parasitics. Five100nF receivers behind1kΩ draw an initial5mA for simultaneous1V steps,25mA for5V steps, compared with the historical2mA planning driver condition. The latter transfers2.5µC, taking at least1.25ms at2mA *even before linear settling*. Ideal τ=100µs gives0.782ms to2mV after5V, but that exponential is invalid while the source current-limits. Pull-down DC load is0.5µA/branch at5V, and source/return offsets remain. Therefore keep shared-source circuitry as baseline and require a five-receiver-equivalent switching/load/recovery test; do not claim the aggregate1nF condition absorbs500nF behind resistors or change feedback remotely. This exposed dynamic conflict is a specific implementation/test requirement, not a reason to abandon design refinement.

**NOT RUN:** populated source/schematic/PCB implementation, ERC/DRC/native campaigns, actual resistance/temperature/aging, safe energized ramp/missing-rail/off-state injection/output-short/recovery, reference stability,20-minute warmup/six-trim/five-octave/adjacent-unit tests. These belong to separately authorized implementation and physical stages; drawings and scalar arithmetic cannot pass them. Five cents at25°C and2mV adjacent steps remain targets. No new performance I/O is proposed.

## Switched-reference design alternative, not a canonical edit

The2mA condition comes from a **normal-powered planning fanout** report, not a guaranteed dynamic current clamp. Consequently25mA initial demand is outside retained evidence, not proof the amplifier physically current-limits at2mA. A concrete bounded alternative is15kΩ±1% receiver series resistance, retained100nF, and220MΩ±1% fail-to-zero resistor: five5.025V steps draw at most1.692mA through14.85kΩ, below2mA. At15.15kΩ and217.8MΩ, DC divider error at5.025V is0.350mV;15nA bias adds0.227mV, combined0.577mV before source, return and offset. Assuming±10% capacitor solely for sizing, τ≤1.6665ms and ideal5.025V→2mV settling≈13.05ms; input-parasitic1nF remains a separate aggregate constraint. Exact parts, temperature/leakage and closed-loop source stability must be verified. A serious tradeoff is open-switch fail-to-zero discharge becoming22s nominal rather than1s (100nF×220MΩ). Therefore recommend **retain1kΩ/10MΩ in the initial parity implementation and characterize25mA demand**, with15kΩ/220MΩ as an explicit design-change option only if controlled slower switch/disconnect response is accepted. It invalidates prior fanout/receiver transient and control-law evidence, needs source/schema updates, and is not silently part of this candidate. The owner need not select resistor values now; later measured driver recovery determines whether this alternative is needed. No numerical/native campaign was run.

### Exact male document corroboration

The independent reviewer read the [manufacturer-authored09031966922 PDF mirrored by RS](https://assets.rs-online.com/image/upload/v1763385649/Datasheets/c29c606e19ded3a09c39bbc6b0188822.pdf): printedpage2/5 specifies≤20mΩ,≤90N insertion,≤60N withdrawal,≥400 mating cycles and nohotplug. This corroborates the male choice; it is a manufacturer-authored mirrored document, not a successful official-host retrieval or exact-female verification. Printedpage4/5 describes actual contact-loss coding with female codingpin09020009901 and malecontact extractiontool09990000133; this candidate instead retains96 contacts and uses mechanically polarized guides. No connector removal/coding tooling is silently part of the bill. The selected female manufacturer-authored PDF was subsequently downloaded successfully from the EVG mirror and retained as `evidence/harting-09032966824-mirrored.pdf`; `connector-source-receipt.json` records its SHA256 and origin. Pages1–2 independently confirm the exact female2Aat20°C,20mΩ,90N/60N,400cycles,nohotplug. Official-host provenance and mating-alignment drawing capture remain production evidence tasks.

### Route refinement after populated review

A first path sum using the packed receiver positions exceeded300mm (O2PW approximately350mm), so it is rejected rather than hidden. Relocate all five existing R_W receiver packages intact to a reserved row immediately below the rear DIN bank; reassign their input contacts to a17/a5/a9/a13/a1 forFM/PWM/TUNE/FINE/PW. No part is omitted and the panel stays fixed. The generated ten O1/O2 wiper routes use actual panel positions, manufacturer contact pitch and populated R_W coordinates, plus10mm front trace,60mm front flex,5mm middle detour,25mm connector developed-path allowance (greater than19.2mm PCB spacing), and5mm rear pin-fanout allowance. The middle diagonal and rear Manhattan distances are calculated separately and returns follow their corridors. Each result retains its300mm comparison; these are routing allocations to enforce in the one-zone PCB implementation, not already routed traces. Capacitance, including test loading, must independently remain≤1nF. The generated all51-conductor planning bill now assigns60mm front wire each (3060mm total before cutting tolerance), uses the retained proposed header-bank coordinates for the unrefined paths, and calculates middle distance and maximum rear Manhattan distance to mapped package endpoints. Those proposed header centres are not locked hardware;30mm front trace and shared-reference source-zone reservations remain design allocations. The refined raw-wiper routes supersede that coarse bank-based estimate. No bank-based total is claimed as an achieved≤300mm path, and unplaced shared-source endpoints remain explicit. The later PCB must reconcile every pin route and return; no length or assembly savings is inferred from3060mm without actual baseline cut lengths.

Final populated route allocation maximum is **295.967mm forO2PWM**, leaving4.033mm against300mm; this small margin includes the declared10/60/5/25/5mm allowances and requires actual PCB route enforcement. The generator fails if the populated input makes any of the ten refined wiper allocations exceed300mm. It does not turn unrouted allocation into physical acceptance.

### Further front-bank relocation investigation

Moving old front headers was explicitly evaluated rather than assumed forbidden. `front_bank_relocation_comparison` places each harness bank at the midpoint of its actual associated panel functions, computes the longest front route plus10mm fanout, and uses driver/source endpoints rather than every local load on outgoing core nets. The unchanged11-harness grouping can combine functions84mm apart (PWM/RANGE), so relocating a header alone does not eliminate its trace burden. This comparison has the following exceeding allocations; the raw-wiper dedicated refinement already supersedes its wiper rows.

| Instance | Net | Complete proposed mm |
|---|---|---:|
| O1 | `/O1/1V_BUFFER` | 319.62 |
| O1 | `/O1/LOCAL_REF5` | 338.19 |
| O1 | `/O1/LOCAL_REFN5` | 332.93 |
| O1 | `/O1/PWM_REMOTE` | 302.27 |
| O1 | `/O1/RANGE_CV` | 332.62 |
| O2 | `/O1/1V_BUFFER` | 379.01 |
| O2 | `/O1/FM_BUFFER` | 304.59 |
| O2 | `/O1/PUL_SCALED` | 315.79 |
| O2 | `/O1/PWM_BUFFER` | 313.27 |
| O2 | `/O1/SYNC_BUFFER` | 326.27 |
| O2 | `/O1/OCT_SELECTED` | 302.86 |
| O2 | `/O1/C1eb779_W` | 318.41 |
| O2 | `/O1/FM_REMOTE` | 322.13 |
| O2 | `/O1/HARD_DRIVE` | 319.63 |
| O2 | `/O1/LOCAL_REF5` | 383.09 |
| O2 | `/O1/LOCAL_REFN5` | 381.75 |
| O2 | `/O1/PWM_REMOTE` | 352.84 |
| O2 | `/O1/RANGE_CV` | 384.77 |
| O2 | `/O1/SOFT_DRIVE` | 341.35 |

This rejects simple bank relocation as a complete solution, not the architecture. Next implementation must regroup front links by function, place complete local reference/receiver/feedback clusters near their assigned DIN pins, and consider rotating the connector bank while maintaining populated support/tool envelopes. The current package packing is a capacity arrangement, not circuit-aware placement. Moving only an isolation resistor would create undesirably long local feedback paths; that shortcut is rejected. O2's lateral rear-tile offset and widely spaced functions in retained mixed harnesses explain the residuals quantitatively. Routing changes alter the final harness/contact bill and require regeneration; the unchanged11/51 comparison must not be advertised as the finished production bill. AGND companion paths follow each signal corridor; traversing all AGND endpoints on a whole PCB is not one remote300mm signal, although complete power-return resistance remains constrained separately. No generic missing-measurement excuse or unmeasured PASS substitutes for these explicit layout constraints.

### Recommended functional front grouping

The original K-P pairings mix controls far apart and cannot physically support the refined per-pot routing. Replace those seven3-way links with seven **function-specific** links: FM, PWM, PW and RANGE each3-way; TUNE, FINE and SYNC each4-way including explicitAGND. The generated `functional_front_links` contains exact Ref/pin-derived nets, both faces and proposedGH MPNs. This preserves every original21control conductor and sevenreturns, adding twoLOCAL_REF5 branches and oneLOCAL_REFN5 branch at the middle (no extra rear DIN contacts or hidden normal). Hence the recommended fullO1 front transport is **11harnesses,54conductors,108crimps,22GH mating locations,108GH signal solder joints+44mechanical hold-down joints,one96-contact DIN pair with192solder joints**. Its60mm/link-conductor planning wire total is3240mm. Three4-way GH headers/housings are new exact-component evidence tasks; do not infer their completed procurement qualification from naming syntax. The historical51-conductor ledger and front-bank rejection table remain comparison evidence, not the recommended physical front routing. No claim of lower total assembly effort follows from saving96crimps relative to the literaltwo-cable candidate because supports,boltedpower,extra solder joints and testing remain.

### Final populated comparison after whole reference-cluster refinement

The mechanical model now keeps U1110's four amplifier units, all four feedback/compensation networks and both bypass capacitors together (15 packages), rather than moving only remote-feed isolation resistors. The following **current functional-grouped** allocations still exceed300mm; they supersede the earlier rejected bank table for current status. Each includes all declared front, flex, middle, connector and rear terms. The optimistic geometric endpoint bound demonstrates a layout challenge rather than an inherent architecture impossibility; it excludes detours, returns and contact geometry.

| Instance | Signal | Proposed complete mm | Straight-line geometric bound mm |
|---|---|---:|---:|
| O1 | `/O1/FM_BUFFER` | 305.69 | 160.45 |
| O1 | `/O1/PWM_REMOTE` | 334.94 | 141.02 |
| O2 | `/O1/1V_BUFFER` | 337.24 | 206.52 |
| O2 | `/O1/FM_BUFFER` | 349.78 | 212.22 |
| O2 | `/O1/PUL_SCALED` | 319.79 | 139.30 |
| O2 | `/O1/FM_REMOTE` | 326.50 | 170.56 |
| O2 | `/O1/PWM_REMOTE` | 374.93 | 201.71 |
| O2 | `/O1/LOCAL_REFN5` | 303.26 | 189.22 |
| O2 | `/O1/LOCAL_REFN5` | 311.80 | 195.26 |
| O2 | `/O1/LOCAL_REF5` | 306.46 | 182.89 |
| O2 | `/O1/LOCAL_REF5` | 326.56 | 198.17 |
| O2 | `/O1/RANGE_CV` | 304.27 | 161.04 |
| O2 | `/O1/HARD_DRIVE` | 313.48 | 154.88 |
| O2 | `/O1/SOFT_DRIVE` | 303.76 | 147.14 |

A deterministic search of every currently unallocated DIN position for each reference alone finds best worst-receiver lengths307.845mm(REF5,c25) and303.878mm(REFN5,c30). These experiments are rejected, not silently assigned: they still fail and do not establish adjacent-return pairing. Further shift/rotation of the complete reference cluster, complete pitch/summing cluster and remote-buffer package group is necessary during circuit-aware one-zone placement. R1140 andR1145 feed EXPO_SUM; moving them alone would create longer sensitive summing paths. Preserve those circuits as whole local clusters. The front functional regrouping is completed now; final interface placement/route acceptance remains explicitly incomplete.

Existing supported normal-power components are quantified in [revision-loads.md](revision-loads.md): front-jack8mA/rear-core22mA/shared18mA peranalograil atzero outputload, with exact source/device conditions. Allfive+shared168mA peranalograil is an IQ component, not whole-load or fault qualification. The original62.7/61.8/6mA O1 allowances remain unchanged; their non-IQ remainder is already allocated rather than spare headroom.

### Whole-card orientation and pin-position sweep

The final read-only scalar sweep (`orientation_sweep.py`, `revision-orientation-report.json`) rotates all packages, connector contacts and local feedback geometry together through0/90/180/270degrees, preserving each card origin.90/270 uses115×103mm;0/180 uses103×115mm. O2's rotated extent fits the proposed adjacent-card reservation, but this calculation does not substitute for transformed support/tool collision checks.

| Card | Rotation | Paths over300mm | Maximum complete mm | Maximum wiper mm |
|---|---:|---:|---:|---:|
| O1 | 0° | 2 | 334.94 | 266.41 |
| O1 | 90° | 4 | 339.58 | 284.53 |
| O1 | 180° | 7 | 399.32 | 213.19 |
| O1 | 270° | 4 | 375.79 | 203.88 |
| O2 | 0° | 12 | 374.93 | 295.97 |
| O2 | 90° | 26 | 419.16 | 343.99 |
| O2 | 180° | 14 | 456.78 | 294.18 |
| O2 | 270° | 9 | 406.51 | 244.39 |

No orientation closes the interface. O2at270° improves wiper margin and reduces the number of failing paths but increases the worst full-path allocation to406.51mm. Retain0° for the minimum worst-case allocation with the current pinout. An additional optimistic search independently moves each failing O2 signal through all96 DIN positions at0° and270°. Even before enforcing contact exclusivity and adjacent returns,0°PWM_REMOTE remains354.10mm and270°PWM_BUFFER331.93mm; multiple other signals still exceed300mm. These are rejected geometric experiments, not pinout proposals, and cannot be promoted to electrical acceptance. They establish why simple card rotation or pin reassignment alone does not close this populated placement. The next circuit-aware arrangement must regroup whole local functional clusters; it must not stretch sensitive summing/feedback loops to satisfy one transport length.

Further implementation may regroup the two original8-way jack links by physical and functional adjacency; they currently mix inputs and outputs, increasing front trace spans. This trades additional/different housings and assembly operations for shorter paths. It is not silently selected here, and the current11/54/108 count excludes such an unchosen change. The one-zone implementation must publish its changed full bill and close every applicable source-to-load path before acceptance; this design revision does not grant architecture adoption.

Net names in the failed-path comparison use the O1 template; the instance column selects the explicit O1/O2 Ref-pin mapping. No O1 signal is connected to O2. Manufacturer PDF bytes are retained in ignored local `.circuit-cache/sources/architecture278-harting/document.pdf`, with the exact hash in connector-source-receipt.json; the raw document is not republished.

The scalar routing checker now explicitly rejects any change to its supported103×115mm populated tile, connector-bank rectangle or50/69.2mm planes until the bounded geometry contract is updated. It also rejects a stack tolerance outside the exact18.3–20.0mm pair range or25mm developed-path allocation. This prevents changed mechanical inputs silently inheriting old contact coordinates or rotation formulas. Mutations of the bank, tile and stack tolerance are tested.
