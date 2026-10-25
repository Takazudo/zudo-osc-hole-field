# Feed process and tolerance proposal

This is an integration-owned reconciliation overlay for the published #246/#247
sources at29140d4e, not a rewrite of those producers or physical qualification.
The historical F/F single-row/local-corridor model remains reproducible. The
two-deep candidate now has an explicit B/F, two-row,58mm-offset feed proposal.
All CS247 wire/terminal identities, net order, loads, layer roles, protection,
factory soldering and the existing195 harnesses remain governed by their frozen
sources. Three-core alternatives are unaffected.

## Selected proposed process and datums

Use machined split dielectric collets on machined carrier brackets, assembled in
a metrology fixture before factory soldering. This selects a process class for
engineering; no shop, material grade, orderable part, capability certificate or
supplier tolerance is claimed. Grade selection must cover insulation, creep,
temperature and retention without damaging the Alpha5859 insulation. The old
0.3mm-thick stem construction is not accepted as a load-bearing design.

Datum A is the measured board-face plane established at three existing support
locations. Datum B is the existing board X direction registered optically to two
existing land/feature locations; C locates the remaining in-plane translation.
Existing loose support holes provide retention only, not precision location.
No new board holes, cutouts, panel moves or copper removal are authorized.
The fixed KA carrier and translating KB carrier each register to their own A/B/C
frame. KB's carrier moves through the10mm service stroke; it cannot be bonded to
a fixed enclosure wall. The carrier-to-enclosure joints and load path remain
to be dimensioned and checked.

The following are proposed, inspectable acceptance requirements. They are
engineering allocations, not manufacturer guarantees. Use worst-case sums,
not RSS. Inspection must account for measurement uncertainty within each bound.

| Quantity | Proposed requirement | Verification needed |
| --- | --- | --- |
| Anchor height from measured face |2.00±0.05mm|Dimensional inspection after assembly|
| Installed face-to-face gap |24.40±0.10mm|Metrology in installed position|
| Withdrawal end stop |10.00mm,+0.10/−0.00mm|Gauge through complete travel|
| Free reference-curve length |66.00±0.10mm|Registered curve metrology|
| New wire cut |84.75±0.25mm;85mm ceiling|100%cut inspection, including uncertainty|
| Existing main wire cut |103.75±0.25mm;104mm ceiling|Requalify full fan/adapter/solder assembly|
| Carrier registration to board |0.10mm position bound|Optical inspection of assembled datums|
| Machined noncontact surfaces |0.05mm outward profile bound|Dimensional inspection|
| Post-assembly retention motion |0.05mm bound|Repeated service/load qualification|
| Thermal/load displacement |0.05mm relative bound|Material-specific thermal/load test|
| Wire deviation from registered reference |0.20mm position bound|Continuous-shape qualification over travel|
| Local board warp beyond datum plane |0.10mm bound|Assembled-board flatness measurement|

The reference gap envelope20.2..30.7mm covers installed24.4±0.1 minus both
anchor heights2.0±0.05 plus travel0..10.1. Endpoints' remaining lateral errors
belong to the registered wire-shape/position requirements; they are not silently
ignored. Unsupported thermal or load conditions fail qualification rather than
automatically receiving the proposed0.05mm bound.

## Shape constraint and bending

`robust_curve.py` independently parameterizes the new fixed-tangent family. It
checks all free-length and gap cells, not only nominal poses. Under arclength
registration require `|e|<=0.20mm`, `|e'|<=0.01`, and `|e''|<=0.002/mm` throughout
each smooth flexible segment. Then

`R_actual >= (1-0.01)^2 / (1/R_reference + 0.002)`.

Position tolerance alone cannot bound curvature: small high-frequency waves
remain inside a position tube but can violate minimum bend radius. The C1/C2
requirements are therefore essential. They are not established by endpoint
clamping, CAD control points or a few photographed poses. Actual passive wire
shape, collet exit transitions, manufacturing history and service forces need
qualification. If those bounds cannot be measured/maintained, a dimensioned
guided-flex mechanism and a new complete collision proof are required. No such
mechanism has yet been qualified.

The retained supplier OD maximum2.5908mm and minimum bend radius25.908mm already
include the published OD tolerance. Do not add that OD tolerance twice. The
new85mm cut ceiling includes both straight tails, land bridges, the worst C1
length increase and at least4.5mm combined stripping/solder preparation. The
preparation amount is a proposed minimum requiring assembly validation. The
104mm main-wire ceiling is also a process requirement, not proof of a produced
harness. Copper must meet the stronger proposed0.1mΩ rail and0.1mΩ return targets
at the specified worst operating condition; the old1mΩ/0.5mΩ ceilings do not
establish the new joined20mV result.

## Required clearance after worst-case closure

Use0.25mm residual service clearance as a proposed design criterion, not a
regulatory insulation rating. Electrical insulation/creepage remain separately
unqualified. Before acceptance, the complete new solids and source obstacle
sweep must meet at least these nominal gaps:

| Interface | Closure budget | Required nominal gap |
| --- | --- | --- |
| Wire to source part/reserve |0.20shape+0.10register+0.10part profile+0.05thermal|0.70mm|
| Wire to support arm |0.20shape+0.05machining+0.05retention+0.05thermal|0.60mm|
| Wire to wire |2×0.20shape+0.10relative registration+2×0.05thermal|0.85mm|
| Collet to board |0.05outer profile+0.10warp+0.05thermal|0.45mm|

Anchor-height tolerances are already included in the gap family, and must not be
double-counted there. Outward arm/part deviations above are independent of that
axial gap. Shared errors may be reduced only with demonstrated common-datum
correlation, never by assuming cancellation.

The old0.145325mm wire/arm result fails the new0.60mm criterion. It cannot be
carried forward as acceptance. Proposed collet outer radius2.0mm and grip
1.0..2.5mm along the tangent raise its nominal board clearance, but bore grip,
outer solids, thicker arms, joints and full collision checks remain open.
Moving the unselected KB monitor reserve from[80,12,100,32] to[120,12,140,32]
removes the known near-feed obstacle without moving an existing circuit part.
The reconciliation script checks its full source clearance, but that is not a
substitute for the new whole-wire/clamp sweep. Do not inherit the old120mm broad
phase cutoff after moving that reserve.

## Acceptance boundary

This checkpoint closes face/identity reconciliation and quantifies a defensible
proposed tolerance and bend/length/electrical allocation. It does not close the
complete support-arm geometry, continuous physical wire shape, realized copper,
factory process capability, all100 trimmer access, thermal/load tests or native
gates. The whole feed is **not physically qualified or architecture-adopted**.
The old nominal preview remains labeled as the old proposal; it does not depict
this revised family. No fabrication, orders or energization are authorized.
