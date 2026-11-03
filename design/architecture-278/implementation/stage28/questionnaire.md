# Unsent questionnaire

**Not sent. No supplier, fabricator or manufacturer has been contacted.** Each question lists what is decided after the answer.

## Connector Manufacturer

### Q-M02

Does &#x27;board drillings 96x Ø1±0,1&#x27; on 0903296X824 rev C and 0903196X922 rev B specify the finished plated hole diameter or the drill tool diameter? If tool diameter, what finished diameter range do you recommend for the solder tails?

Why: The two readings give different fabrication instructions; Stage24/25 used finished diameter as a proposal only.

- If **Finished plated 0.90-1.10** → Keep D03 interpretation; require the fabricator to guarantee finished size (Q-F01).
- If **Drill tool diameter** → Replace D03 with HARTING&#x27;s finished range; recompute pad/annular ring; re-ask Q-F01 with the new interval.

### Q-M03

Is the ⊕ Ø0,05 position tolerance on the 96 board drillings intended relative to the basic 2.54 grid only (no datum), and what measurement reference do you expect (pattern best fit or a stated datum)?

Why: The frame carries no datum letters; per-axis ±0.05 is not an acceptable substitute.

- If **Pattern-only best fit** → Ask fabricators for pattern positional capability (Q-F02); first-article report uses best fit.
- If **Datum-referenced** → Add the datum to the drilling specification and the first-article report.

### Q-M04

For 09032966824, are the 2x Ø2,8 +0,1 fixing holes intended plated or non-plated, which side of row b is the 0,3 offset, and what fastener or rivet and torque do you recommend?

Why: Drawing states size, spacing and symmetry but not plating or fastener.

- If **Non-plated, offset toward row a** → Stage24 NPTH candidate and Stage10 flange XY stay; ask Q-F03 for NPTH tolerance.
- If **Plated** → Change the candidate to plated with finished 2.8 +0.1/-0; recheck copper clearance to contacts.
- If **Offset toward row c** → Stage10 flange XY is 0.6 mm off; raise a geometry correction decision before any board binding.

### Q-M05

Do you recommend board fastening for the male 09031966922 (flange Ø2,55 holes) when mated with 09032966824 in a board-to-board stack with 40 mm axial withdrawal service?

Why: Board drillings show no fixing holes, but retention under service load is not documented here.

- If **Not required** → Keep D06: no male board holes.
- If **Required** → Record a separate geometry change proposal; locked positions unchanged.

### Q-M06

What board thickness range, and minimum tail protrusion, do you specify for the solder tails of both parts?

Why: Drawings give tail lengths but no board thickness.

- If **Range includes 1.6 mm with adequate protrusion** → Propose 1.6 mm as candidate; confirm with assembler (Q-A02).
- If **Range excludes 1.6 mm** → Pick the nearest fabricator standard inside the range; recheck seating window D08.

### Q-M07

Confirm the board-to-board distance window for this exact pair (catalogue 18.3-20 mm) and the reference surfaces it is measured between.

Why: Catalogue value was retained in Stage5; reference surfaces are not stated in the repository.

- If **Window confirmed between mounting surfaces** → Keep Stage10 19.2 mm; set spacer tolerance so the stack stays inside.
- If **Different reference** → Recompute the stack before any mechanical binding.

### Q-M08

State insertion and withdrawal force and rated mating cycles for 09032966824 with 09031966922 (performance level 2).

Why: Not retained; carrier and handle load path depend on it.

- If **Values provided** → Replace the 90 N planning load with the stated maximum; rerun carrier deflection sensitivity.
- If **Not provided** → Measure on samples (M-08) before carrier acceptance.

### Q-M09

State wave and selective soldering temperature/time limits and any reflow prohibition for both parts.

Why: Mixed-process acceptance needs exact-part limits.

- If **Wave/selective allowed within assembler profile** → Proceed to Q-A01 with these limits.
- If **Hand soldering only** → Ask assembler for hand soldering by a certified operator with inspection; owner hand soldering remains excluded.

### Q-M10

Which cleaning processes and agents are allowed for both parts after soldering?

Why: No cleaning data retained.

- If **Aqueous allowed** → Still check any open-frame trimmer on the same board (Stage27).
- If **No-clean only** → Specify no-clean flux on the DIN boards.

### Q-M01

Do you confirm that the drawing view A (female) and view B (male) board drillings are seen from the connector body toward the board, i.e. the copper pattern on the component side reproduces the drawing unmirrored?

Why: Stage28 reading of the arrows conflicts with the Stage6/Stage10 labeled placement. The answer, together with the fixing-hole offset side (Q-M04), selects column or row reversal.

- If **Confirmed** → Resolve D02 with the proper-handed candidate (Q-O01).
- If **Views are from the solder side** → Stage10 labeled positions are correct; close D02 as consistent.

## Pcb Fabricator

### Q-F01

Can you guarantee finished plated hole 0.90-1.10 mm (nominal 1.00) for 192 soldered THT contact holes on a multilayer ENIG FR4 board using your ±0.05 &#x27;press-fit hole&#x27; option, and does that option change plating thickness or solderability?

Why: The option is published for press-fit holes.

- If **Yes, applicable to soldered holes** → D14 route remains first choice for size; continue with Q-F02.
- If **Press-fit only / no** → Default +0.13/-0.08 cannot meet 0.90-1.10 at any nominal; go to precision fabricator comparison.

### Q-F02

Can you hold a Ø0.05 mm positional zone for a 3x32 hole pattern at 2.54 basic pitch relative to the pattern itself, and how would you report it (CMM/optical, sample size)?

Why: Published default position is ±0.075 per axis.

- If **Yes with report** → Accept the route pending first-article M-03.
- If **Only ±0.075 per axis** → Not compliant (up to 0.106 radial vs 0.025); compare a precision fabricator; adapter/connector change stays a separate design decision.

### Q-F03

What size tolerance can you hold for two Ø2.80 +0.10/-0 holes (plated and non-plated variants), at 90.00 ±0.10 centres and symmetric within 0.1 to the contact pattern?

Why: The ±0.05 option range 0.55-2.0 excludes 2.8 mm; no round NPTH tolerance is published.

- If **Meets +0.10/-0 and 0.1 symmetry** → Keep D05 candidate.
- If **Only ±0.2 or default** → Not compliant; precision fabricator or reamed/post-drilled holes need a separate decision.

### Q-F04

Will you supply a first-article report with measured finished diameters and positions for all 96 contact holes and both fixing holes per board type?

Why: Sample evidence is required before any route acceptance.

- If **Yes** → Use it as M-02/M-03/M-04 evidence for the sampled boards only.
- If **No** → Plan independent measurement on received boards.

## Pcb Assembler

### Q-A01

Will you place and solder HARTING 09032966824 and 09031966922 (customer-supplied or sourced by you) on your THT line in a mixed SMD+THT order, by wave or selective soldering, holding the body seated and square in a fixture?

Why: Generic mixed capability is not exact-part acceptance.

- If **Yes with fixture** → Proceed to process definition with Q-M09 limits.
- If **Hand solder only** → Accept only with a named certified operator, inspection class and records.
- If **No** → Compare another assembler; no owner soldering.

### Q-A02

Which board thickness do you require for wave/selective soldering of these tails, and what minimum tail protrusion do you accept?

Why: Economic PCBA is limited to 0.8-1.6 mm.

- If **Compatible with Q-M06** → Fix the candidate thickness.
- If **Conflict** → Owner decision on thickness versus process.

### Q-A03

Can you build or accept a soldering fixture that seats the female against its two fixing holes and holds the male square, optionally soldering the pair mated on a gauge?

Why: Seating and squareness drive mating and position.

- If **Yes** → Specify fixture datums from D05 and the mated-gauge check M-07.
- If **No** → Fixture becomes an owner-supplied item; separate decision.

### Q-A04

State your THT solder profile, flux type and preheat for these parts and confirm it is within the manufacturer limits from Q-M09.

Why: Process record is required for traceability.

- If **Within limits** → Record profile as process evidence.
- If **Unknown limits** → Hold until Q-M09 answered.

### Q-A05

Do you clean after THT soldering; with what process? Can boards be processed no-clean?

Why: Cleaning compatibility is unconfirmed.

- If **No-clean available** → Prefer no-clean pending Q-M10.
- If **Aqueous only** → Check compatibility for every part on the board.

### Q-A06

What THT joint acceptance class and hole-fill criterion apply, what inspection records do you supply, and how are nonconforming boards dispositioned?

Why: Inspection evidence must be defined before ordering.

- If **Class and records stated** → Bind them to D13 and M-11 records.
- If **Visual only, no class** → Not sufficient for acceptance; agree a class before ordering.

## Harness Maker

### Q-H01

Can you build the four GH cable assemblies (7, 4, 6 and 3 positions, 1:1 straight, JST GHR-0nV-S housings with SSHL-002T-P0.2 contacts crimped with the JST-specified applicator) at lengths we provide after fit-up measurement, with 100% continuity/isolation test and per-cable test records?

Why: Termination and test must be completed by the vendor.

- If **Yes with records** → Harness route H1 (assembler or harness vendor builds and tests).
- If **Only stock lengths** → Choose stock length only if M-09 slack window contains it; otherwise custom.

### Q-H02

Which wire do you propose (AWG 26 to 30 within JST GH range, insulation OD 0.76-1.0 mm, rated &gt;=50 V and &gt;=105 C), and state its MPN, insulation material and rating?

Why: JST states 1.0 A only at AWG26; Stage10 power-return contract retains 0.5 A contact limit.

- If **AWG26 with OD in range** → Accept as candidate for GH conductors.
- If **Thinner gauge** → Accept only for signal conductors after current check; power/return stay AWG26.

### Q-H03

Can you supply and factory-solder the 14 permanent tail wires (LED lands and jack S/T terminals to A01-jack tail lands, through carrier guide bores whose minimum open diameter is 1.0 mm (Stage10); state the wire OD and the clearance you require), with ID marking, pull test and continuity records?

Why: Owner hand soldering is excluded.

- If **Yes** → Tail route T1 at PCBA assembler or harness vendor.
- If **No** → Replace permanent tails by a connectorized design only as a separate design decision.

### Q-H04

Which harness workmanship standard and class (for example IPC/WHMA-A-620 class 2 or 3) and which test voltage/limit for insulation resistance do you apply?

Why: Inspection limits are not yet defined.

- If **Standard and limits stated** → Bind to inspection items I-IR and I-VIS.
- If **None** → Define acceptance criteria in the order before release.

## Owner

### Q-O01

Owner decision: adopt the proper-handed DIN label-to-position candidate (contact numbers and nets kept, positions within the fixed 96-hole grid reassigned along columns) for future board copper, or keep the Stage10 assignment pending Q-M01?

Why: Changing which hole carries which net is a design change; not adopted here.

- If **Adopt candidate after Q-M01/M-01 confirm** → Separate source update of the DIN placement transform; Stage10 bytes remain historical.
- If **Keep Stage10** → D02 stays CONFLICT; no board binding allowed.

### Q-O02

Owner decision: plated or non-plated female fixing holes, after Q-M04 and Q-F03?

Why: Process and grounding choice.

- If **NPTH** → Keep Stage24 candidate.
- If **Plated** → Update candidate and clearance check.

### Q-O03

Owner decision: approve fit-up measurement on a mechanical mock (unpowered) to measure harness paths, slack and anchors (M-09, M-10, M-12)?

Why: Lengths cannot be fixed from straight-line proxies.

- If **Approved** → Run measurement checklist; record values; then order custom lengths.
- If **Not approved** → Harness lengths remain UNDETERMINED; no harness order.
