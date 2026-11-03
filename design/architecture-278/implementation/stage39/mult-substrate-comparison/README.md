# Shared mult cells versus separate rear electronics — Stage39

**Recommend A for the next source-layout review: retain the shared JL substrate and repeat the B1/B2 circuit cell.** It removes the impossible board seam without extra signal connectors, cables, support sites or board depth. It achieves identical circuit-cell layout and population, **not interchangeable assembled mult boards**. This is the simplest candidate that passes the new necessary source geometry and electrical-boundary screens. It is not a routed, installed, manufacturing or electrical-performance qualification.

B can provide two interchangeable rear assemblies, but the requested combination of passive front adapters, a fixed front LED and wholly local feedback is not met by the retained circuit. An explicit active-front variant keeps the complete indicator loop front and moves23 circuit packages rear. Its populated proposal still fails the selected front-header/selector reservation and has unresolved support-anchor interference. Adding depth alone does not repair those front-side conflicts. Neither architecture is adopted.

Baseline `df3ae42a981a1459297f0994a38e4255780c164f`. Stage38's0.38mm negative result, all historical evidence, parent286, canonical CAD/manufacturing outputs and every fixed front position remain intact. Earlier owner-approved rear-face study does not approve these new placements, tabs, depth or interfaces. [Diagram](comparison.svg) · [checkable geometry/pins/counts](comparison.json) · [verification](VERIFICATION.md) · [independent review](REVIEW.md).

## Actual seam and substrate ownership

Retained WQP518MA lands leave0.62mm between the upper jack's tip pad and next row's sleeve pad. The current0.5mm copper-edge clearance on each disjoint coplanar board needs1.00mm, leaving **0.38mm overlap**. Recomputing every consecutive row at fixed x14.5/31.5/48.5/65.5 finds **36 failing seams across40 jack footprints**, from y29 through155. Absorbing only the neighboring y127 row moves the same failure upward. No notch changes the overlapping mandatory clearance sets on each common X centerline.

This forces shared substrate ownership through each affected ten-jack column if all pads and coplanar mounting are retained. It does not force every panel column onto one board: the17mm horizontal pitch still permits a separate vertical-boundary study. The minimum four-column shared area would carry32 foreign oscillator jacks plus8 mult jacks. Extracting it would require additional oscillator interfaces and is outside this bounded comparison. **Both concrete candidates therefore retain incumbent JL as their shared front substrate**; no foreign jack or circuit is silently moved onto a new mult board. A passive bottom-two-row adapter does not solve Stage38.

## A: repeat the cells on existing JL

The shared outline stays **x4..176.5,y20..164mm**, depth trial10..11.6mm, inherited from the source partition rather than measured seating. Each complete36-package/48-unit/115-pin mult cell retains its4 fixed jacks, fixed LED and31 nonpanel packages. Nonpanel footprints are repacked on the reverse face; B2 is exactly+34mmX with the same values, MPNs, rotations, pins and local-net aliases. U3102 remains the whole OPA4197 input-buffer/three-output package; U3103 retains its indicator and grounded spare units. The six499Ω1210 resistors, six bypasses and three unspecified resistor MPNs remain unchanged.

The necessary XY screen uses actual footprint courtyards/pads, the retained JL placement report, front through-terminal reservations expanded0.5mm, all13 rear keepouts intersecting the comparison region and the four retained JL mounting holes with a proposed8mm tool reservation. It jointly excludes obstacles for both translated cells, with0.25mm between package courtyards and0.5mm copper-edge clearance.28 fixed-terminal reservations and the one foreign rear-package projection (DH201, H2) are explicit. Final screens find no new package/terminal/keepout/mount-tool overlap and no edge violation. Marker positions are exact. The four mounting holes remain at(6.5,22.5/80/138/161.5), diameter2.2mm; actual fasteners, support stiffness and board bow remain unqualified.

These are **retained source-placement screens**, not a fresh native check of the current routed PCB. All original B1/B2 package placements would be replaced if adopted; other families retain their source placements. Existing copper cannot simply be left under relocated pads: new routing, bypass locality, sensitive-loop parasitics and integration with preserved foreign copper require a separate change and native verification. Same-board membership is not a low-noise or decoupling-quality result. Current optical seating remains unresolved.

Stage38's two P8 headers and two proposed standalone support sites are omitted. A uses existing shared supply ownership and existing JL mounts; it adds no mult-specific power or analog cables. No complete-board cost saving is claimed: JL remains a shared board and a fault still requires shared-board servicing.

## B: concrete split, ordinary connectors and explicit deeper plane

The passive adapter version would leave4 jacks+LED front and31 packages rear. It exports `LED_A`/`LED_K` from the indicator's feedback loop. That violates this study's local-feedback requirement. Moving the whole indicator and emitter rear could preserve that loop but would need a new optical guide/depth solution; it is not an established simple adapter option.

The conservative split instead leaves **13 packages per cell front**:4 jacks plus the entire9-package indicator (U3103, R3114, D3102..D3105, D109 and C3108/C3109; B2 aliases). It moves **23 packages per cell rear**, including whole U3101/U3102 packages, input protection/sense and all precision-output compensation. Front packages use the A placements. All package pins/units remain accounted for exactly once.

The eight crossing nets are raw `IN_TIP`, three `OUT_n_TIP`, buffered `IN_BUFFER`, +12V, −12V and AGND. The front indicator uses the existing shared JL supply; +5V is required only by the rear fault-enable circuit. `IN_PROTECTED`, `IN_SENSE`, amplifier FB nodes and the complete indicator feedback remain on their respective boards. The raw input cable lies before protection and adds an exposed high-impedance path. Precision feedback picks off the rear output node **before** cable/contact/return losses; keeping FB local therefore does not preserve guaranteed accuracy at the panel tip under load. Remote sensing would export a feedback path and is not silently substituted. Connector parasitics, return disturbance, output stability and fault behavior need a new analysis; no arbitrary acceptable cable length is assigned.

Two identical **32×56.5mm** rear trial boards span x7..39 /41..73,y118..174.5. They carry23 retained packages plus power8 and signal10 headers each. Rear front/rear planes are explicitly **40/41.6mm**,30mm deeper than the front board, not an adopted stack or established free volume. Package courtyards and proposed support/tool holes are packed and checked; header PTH reservations are excluded. Full mated height, rear component heights, cable exits, bows and clearances are unknown. Required enclosure increase is **null**, not30mm: the trial may fit within a deeper existing volume or conflict with core/supports; maximum occupied depth has not been established.

Ordinary retained3M candidates are **D2510-6002-AR /89110-0101** for signal10 and **D2508-6002-AR /89108-0101** for power8, without optional strain relief. Primary TS0770 Rev U/TS0449 Rev M evidence and coordinates are inherited from Stage36; width/height are read from its bound toleranced rectangles,20.1422×8.7122mm for10way and17.6022×8.7122mm for8way. Finished-hole recommendation0.8128..0.9652mm remains;1.6mm pads remain an unqualified project proposal. Retained source identity is not a present stock/price guarantee; existing10way lifecycle uncertainty remains. No new prices, ratings or purchases are claimed.

| Interface | Proposed pin map | Centers in panel-front XY |
|---|---|---|
| signal10 |1 IN_TIP,2 AGND,3 OUT1,4 AGND,5 OUT2,6 AGND,7 OUT3,8 AGND,9 IN_BUFFER,10 AGND |front and rear(23,169), B2+34X |
| power8 |1 +12,2 AGND,3 −12,4 AGND,5 +5,6 AGND,7–8 NC |rear(23,125), B2+34X |

Signal headers face each other across the gap: front substrate rear-facing header mirrorsX; rear PCB front-facing header does not. Every socket mating-face transform is checked against its same-number header pin. Opposing board pin1 positions differ in globalX; the cable must be wired by pin number, not visual alignment. These bespoke maps are incompatible with other same-count Stage36 connectors or Eurorack. Physical wrong-mate prevention remains required; labels alone are insufficient. No parallel-contact current sharing is assumed. The unchanged planning current worksheet is not a connector rating or guaranteed current maximum.

Two new front tabs at x7..39 /41..73,y164..174.5 support the front signal headers; they are proposed extensions of shared JL, not separate bottom-row adapters. Body+1mm and grip+3mm are planning envelopes. Their terminal XY screen passes, but **front headers conflict with the reserved octave1/3 envelopes**: nominal source plane16 leaves3.4mm after the1mm clearance allowance above11.6, versus the9.906mm nominal bare header. Body and grip reservations both fail. This is a concrete source-envelope rejection, not a measured physical collision or detailed molded-solid proof. Other selector projections at29mm remain unknown for mated height and withdrawal. Changing rear board depth cannot remove this front-header conflict.

Two proposed support sites per rear board at(11,137)/(11,157), translated for B2, use3.4mm drill,6.4mm body and8mm tool trials. They clear the rear package layout, but their proposed11.6..40 support columns project into front terminal reservations. They cannot be anchored to JL at those sites as if the region were empty. Four new anchors, material, carrier, torsional stiffness and supported removal remain unresolved. Both supports on one edge are not a strength or50N acceptance. No new support is adopted.

The comparison records all projected foreign board outlines, including core and stepped octave boards. Unknown populated Z, cable paths, anchors and service volumes remain occupied/unknown. No cut lengths, bend limits, withdrawal strokes or complete service pass are invented. The particular B layout is **blocked**, not a claim that every separate-rear architecture is impossible.

## Counts and achieved reuse — B1+B2 scope only

| Quantity | A shared cells | B active-front/rear23 trial |
|---|---:|---:|
| Assembly boards involved |1 shared JL |1 shared front JL +2 rear =3 |
| Unique designs involved |1 shared JL |1 modified shared JL +1 rear design =2 |
| Interchangeable assembled mult boards |0 |2 rear23 assemblies only |
| Mult circuit packages |72, all front substrate |26 front +46 rear =72 |
| Added board headers incl. distribution |0 |8:2 front signal+2 rear signal+2 rear power+2 distribution |
| Cable sockets / mating actions |0 /0 |8 /8 |
| Added ribbons |0 |2 signal+2 power |
| New mount holes/support sites |0 |4 rear sites plus unresolved anchors |
| Added main-board depth |0 |30mm trial separation; enclosure increase unknown |

B's rear boards carry50 packages including their4headers; front mult allocation is28 including its2signal headers. The2distribution headers and8cable sockets are outside those78 mounted front/rear packages. No extra optical board is included; the retained front emitter plane still needs measurement for both. These are scoped comparison counts, not new whole-instrument totals or savings estimates. No unrelated family is redesigned.

## Review decision and remaining inputs

Select A **for owner review and next source routing development**, because it resolves the seam while keeping all electrical loops local and avoiding new analog connectors. Reusable layout/BOM cells are real reuse; they are not individually replaceable modules. Owner preference for interchangeable boards is recorded as a benefit of B, but the present B's additional front circuitry, cables, support and selector changes make it less simple and not currently viable under retained reservations.

Next cloud-capable work, not performed: improve A's bypass/feedback locality and plan copper changes against current native board contents without moving foreign hardware, then independently review routing impact. If owner prioritizes removable modules despite added complexity, the next bounded B task is a different front connector/access and carrier location, preserving front indicator and all raw-input/output-error constraints. Do not begin that redesign or expand other families here.

Practical unpowered checks after an approved mock-up becomes available:

- Measure jack seating, tails and solder maximums, board bow and registration; reject any intrusion into reserved package/mount envelopes or reduced0.5mm copper edges. Do not attempt to qualify a failed coplanar seam by measurement.
- Measure actual front LED/window optical path. A/B front optics remain unresolved; moving the emitter rear requires a separate optical design.
- For B, first relocate the failed header/anchor proposal in source. Then measure exact closed sockets, exit direction, selector hardware/board/component volumes and all installation/removal sweeps; reject any occupied-volume intersection or unsupported board during unplugging.
- Verify each cable pin-to-pin and all NCs unpowered; reject crossed power/signals or any possible wrong-mate with another installed interface. Select actual ribbon/strain support and obtain maker static/repeated-flex bounds before assigning lengths or bend radii.
- Establish fastener/anchor material and load cases, including existing50N requirement, using approved mechanical evidence. No stiffness or load rating follows from the proposed circles.

Routing, optical fit, raw-input exposure, cable/load accuracy and stability, guaranteed rail/fault current, protection, thermal/assembly and physical qualification remain unresolved. No energization, fabrication, order, deployment or merge.
