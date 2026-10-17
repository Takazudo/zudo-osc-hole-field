# Stage 8 — X1 substrate, feedback locality and current-path repair

This bounded source repair preserves all56 X1 packages,76 units,182 pin records,10 bypasses and7 fixed devices. The instrument remains fiveOSC/33functions/438fixed centres/5904packages. Stage1 acceptance remains OPEN. Stage7 and the Stage6 OSC225paths/240returns are unchanged. No A01 implementation or replication occurred.

[Geometry view](stage8/geometry.svg), [mechanical assessment](stage8/MECHANICAL-ASSESSMENT.md), [locality study](stage8/LOCALITY.md), [current-path study](stage8/electrical.md) and their reproducible JSON reports contain the detailed evidence. This is source geometry, not fabrication CAD.

## Substrate and enclosure constraints

The42 original foreign-pin apertures are traced to their exact0.42/0.54mm ligaments and other selected narrow strips. Joining those cuts removes the obsolete ligaments; no copper or structural load is credited through them. Both substrates remain connected under the proposed worst manufacturing envelope and mounting holes. No universal minimum-web rule is asserted.

Standard published contour tolerances do not fit the six fixed jack lands. The candidate requires total boundary allowance at most0.135mm; it proposes±0.05mm dimension plus±0.05mm position, total0.10mm. Enlarging the nominal cut by that allowance protects inward motion; screening twice that allowance protects outward motion. All208 actual front lands retain at least0.32mm to the resulting cut envelope against the named0.25mm candidate criterion. Supplier acceptance is absent. If the precision requirement is unavailable, a different front hosting/cutout arrangement is necessary; fixed panel centres are not movable relief.

Six PCB mounts connect through proposed3×17mm carrier ribs to six new enclosure anchors. The proposed inner enclosure width becomes322mm, with ribs atZ2..19mm; neither those holes nor the width are existing accepted hardware. Known438fixed hardware projections and panel-side X1 packages are excluded. Straight-beam planning arithmetic is explicit and does not qualify the folded frame, anchor joints, perforated plate, neighboring boards or installation sequence.

Jack user force must react through panel bushings. Connector service needs a defined local backing fixture or stronger local support: an unrestricted5N jack-header unplug is not accepted by the conservative strip study. Actual PCB forces, mass distribution and plate/frame stiffness remain unknown. After excluding own through-holes and mount holes, the conditional jack-header strip budgets are0.978/1.501N; the control headers give21.912N. SW608 has no conservative1mm strip route and requires a separately supported load path. See the mechanical assessment for the full limitations. Enclosure and service changes need coordination before hardware acceptance; they are revisable engineering proposals.

## Critical copper geometry and complete budgets

Eight whole packages move; C3308 also rotates as a whole package. R3316–J1009 sense pad separation falls54.147→12.774mm; C3301 feedback branches fall9.118/9.374→2.560/4.081mm. Ten critical corridors coexist on the actual proposed substrate with explicit0.20mm copper,0.20mm copper clearance,0.25mm edge clearance and0.60/0.30mm vias. The independent checker reconstructs pads, cuts, mounts, headers and all different-net trace/via reservations, checks every segment/layer, and includes via and through-hole terminal barrels in developed lengths.

This is a bounded corridor demonstration. Output isolation feed copper is26.875mm with three vias; the capacitor AGND tie is24.100mm. Bypass and some feedback spans grow. No universal feedback length threshold, stability qualification, complete ground plane or complete routing is claimed.

The actual-pad interface recomputation retains GH4/7/4/3, four harnesses,15wires,30crimps,52header solder joints,26rail and46AGND endpoint groups. Two jack headers move0.25mm inX. Minimum cable-motion proxy slack is12.942457mm. Full X1 signal allocations become348.781825/347.272873/332.898544mm versus309.791747/307.939411/320.238251mm inStage7: moving the whole shared quad improves output locality but worsens remote A/B paths. Each still contains141mm maximum cable against the retained300mm cable envelope and1nF aggregate capacitance envelope; there is no newly invented300mm complete-X1-path limit. Noncritical PCB allocations remain geometric allowances, not obstacle-aware routes. These regressions are retained, not hidden by the ten local corridors.

## Operating-state current and return paths

The54 conditional cases capture all12 amplifier sections, including five unused followers, both ADG packages and ten bypasses. Quiescent amplifier current flows primarily between rails rather than automatically intoAGND. LED bridge currents retain their signs; the output indicator senses OUT_BUFFERED, including the998ohm output-chain drop under nominal load. Headroom is an assumption, not a guaranteed operating point.

Four AGND branches physically join; current sharing and external patch return fractions are unknown. Each board's modeled magnitude envelope is charged to one complete branch without equal sharing or cancellation. GH two-ended contact cases are60/100milliohms before wire/crimp/copper, never0.5milliohms. ADG primary RevC ground-current data retain their±16.5V conditions and are only sensitivity inputs at project±12V.

At the named selected+5/+5V scenario, modeled jack ground current is about4.666mA and the specified contact/upstream case gives about468.97microvolts. The ideal selector's control-to-jack ground coefficient gives about0.103microvolts for that one coupling term; this does not cancel local jack gradients, external ground errors, bias, PSRR or dynamic effects. Actual total current/error guarantees remain UNKNOWN. Bypass AGND connectivity is local only; supply/ground routing, POWER handoff, fault states, transient behavior and stability remain open.

## Verification and next bounded work

Deterministic generators, mutation/source tests and independent code/electrical/mechanical review check this source stage. Exact final commands and counts are recorded in WORK.md and the PR receipt. NativeKiCad10.0.6/ERC/DRC/simulation/physical validation are NOT RUN; available CLI9.0.2 is not exact-run admission. Default CI is deliberately skipped because it invokes excluded native work. No merge, adoption, fabrication export, purchase or energization occurred. KEEP_K1402_INCUMBENT and parked campaigns260/277 remain unchanged; issues278–284 stay open.

The next bounded task is to resolve X1's precision-process and local service-support choice, then complete supply/return and remaining-signal route geometry with real neighboring occupied volumes. If the required manufacturing or service conditions are rejected, redesign front hosting before implementing another function. A01 remains inventory-only until that handoff.
