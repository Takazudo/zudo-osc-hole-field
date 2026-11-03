# Stage15 implements two local matched networks; whole-cell precision remains open

This finite source increment starts at `cc005dc4d45bd516f9f00dd91eaa9a4243822b01` on existing draft PR286. Owner approval covers the two-network candidate and source verification only. Canonical schematics/boards, locked placements, decision.json, KEEP_K1402_INCUMBENT, five OSC,33 functions and438 panel centres remain unchanged. All predecessor evidence is frozen; only README, WORK and check_source integrate this stage. No native/CAD execution, simulation, physical work, adoption or merge occurs.

## The six resistor functions now occupy two local packages

[Package input](stage15/package-input.json), [candidate footprint source](stage15/footprints/LT5400_MS8E_Candidate.kicad_mod) and [complete package report](stage15/package-report.json) specify Analog Devices **LT5400AIMS8E-2#PBF**, A-grade, I-range−40…85°C, four nominal100kΩ resistors, MS8E exposed-pad package. Exact ordering/pinout/land geometry derives from [manufacturer RevC5400fc](https://www.analog.com/media/en/technical-documentation/data-sheets/5400fc.pdf), inspected SHA256 `3bd808eb2c603ce009456913cfacdd9339f645dec08a8bfa8437a6dd5ea71028`. Procurement/order allocation is unknown; no supplier claim or purchase is made. This candidate remains outside the canonical68-line component inventory and published catalog.

| Candidate | Existing functions preserved | Physical terminals | Local placement |
|---|---|---|---|
| RN7101 | R7121,R7122,R7123,R7124 | respectively1–8,2–7,3–6,4–5 | core, origin255.5,254mm; rear padsZ70.8mm |
| RN7102 | R7125,R7126 | respectively1–8,2–7 | front jack board, origin220.5,150mm; rear padsZ36.6mm |

Each original pin1 maps to the first listed terminal, originalpin2 to the second. All four summer resistors share RN7101, preserving IN/manual/CV ratios despite ±7.5% absolute resistance tolerance. Restore gain uses two elements of RN7102; no cross-package absolute matching credit is needed. The other four RN7102 resistor terminals remain NC, with both unused resistor elements and all lands retained. This unused termination is an explicit engineering choice; no manufacturer unused-pin prescription was found.

Pin9 is internally isolated from resistor terminals. Both exposed pads connect to **local AGND**, following ADI's quiet AC-ground shield recommendation; AGND quietness/impedance remains unqualified. It is not a common resistor terminal or a new DC resistor load. No remote feedback is introduced. Existing front ATTEN/OFFSET controls, their positions, all other packages, and the Stage13 capacitor candidates remain unchanged.

The source-derived land pattern uses0.65mm pitch,0.42×0.90mm terminal lands, row centres±2.17mm and1.88×1.68mm EP. Recommended land dimensions and pinout are independently checked against physicalPDFindices9/1, printed10/2. The4.0×5.8mm courtyard and1.5×1.3mm EP paste opening are engineering proposals, not vendor-qualified assembly rules. Maximum body including flash allowance3.406×3.406mm and1.10mm height is screened. Minimum modeled neighbor courtyard gaps are0.460mm core and0.510mm front. Both board-edge and retained mount/header/terminal-land/DIN/handle screens pass. Frozen support/strap/cassette envelopes are preserved and do not intersect these candidate boxes; foreign-function XY reservations remain explicitly unresolved in Z. No complete fit, solder-mask, paste/voiding,3D or DRC acceptance is claimed.

## Every incident path is rebound; lengths remain allocations

[Graph](stage15/interfaces-report.json), [paths](stage15/paths-report.json) and [rebudget](stage15/rebudget-report.json) map all12 former resistor endpoints, regenerate every walk and include two new EP returns. Resistor elements are not represented as zero-ohm copper edges.

| Source inventory | Before | Candidate |
|---|---:|---:|
| Whole physical packages |90|86|
| Physical source pads including NC |285|291|
| Unit records including unused resistor elements |118|120|
| Graph nodes/edges |555/318|561/320|
| Connected local endpoint paths |269|271|
| Crossing-signal paths |21|21|
| Power/return endpoints |106|108|
| Unselected strap core/front targets |26/80|27/81|

| Affected crossing allocation | Historical mm | Candidate mm |
|---|---:|---:|
| OFFSET_BUFFER driver → formerR7123:1 / RN7101:3 |376.111|388.232|
| SUM_NEG driver → formerR7124:1 / RN7101:4 |22.463|17.091|
| SUM_NEG driver → formerR7125:1 / RN7102:1 |433.670|370.882|

Sixteen retained incident edges change and two EP edges are added. Three crossing and16 local path allocations change; two new power/return paths are added. **Every original106 power/return walk is unchanged**, including the Stage14 capacitor geometry. Both historical PCB-only and expanded whole-path resistance comparisons remain on every old and new endpoint. Shared-edge endpoint-use counts increase correctly for shield paths; those counts are not current multiplicity. Strap geometry remains frozen/unselected; no sharing or cancellation credit is introduced.

For locality, the restore summing-pin separation from the replaced R7125 terminal falls46.482→2.715mm. Core ATTEN_OUT pad separation increases6.831→13.823mm. These are straight-line floors, not actual trace lengths. Complete graph lengths retain1.15×octileXY+7mm+absoluteZ per local segment; conductor widths, route obstructions, resistance, loop area and assembled parasitics remain unknown. The networks improve ratios, not automatic routing or stability qualification. Typical package capacitance is not an all-condition assembled bound.

## Better CV ratios do not establish total static accuracy

[Electrical input](stage15/electrical-input.json) retains exact primary conditions; [electrical report](stage15/electrical-report.json) evaluates coherent physical resistor witnesses at ten fixed input/control states. It includes coupled IN/manual/CV paths, ten amplifier offset coefficients, known bias impedances, common reference error once, and a ledger of unresolved loading/return/temperature terms. No knob fitting or new factory adjustment is performed. Historical Stage13 calibration evidence is unchanged.

The gain is `(R7124/R7123) × (R7126/R7125)`. At25°C, two network ratios each bounded by0.010% give a worst high ratio-only error of1.00005mV at5V. Across the I-range,0.0125% gives1.250078mV, leaving only0.749922mV of the **conditional2mV total static target before all other errors**. The special difference-amplifier CMRR matching figure is not used. Full-temperature matching is used once; matchingTC is not added to it. Separate initial calibration/drift/aging assumptions remain explicit, and typical long-term drift is not a lifetime guarantee.

These figures apply to isolated CV slope. With controls held fixed, unchanged negative-reference inverter mismatch moves the manual midpoint: coherent CV-only whole-cell resistor/loading witnesses extend approximately−6.24…+6.23mV. Nominal manual-quarter wiper loading alone contributes+4.928mV. Unchanged attenuator ratios also affect IN paths. These are conditioned source calculations, not observed hardware failures or complete worst-case guarantees. They prevent reporting the ratio improvement as a2mV total success.

The source's100µV amplifier-offset sensitivity uses its table conditions, not a guaranteed installed±12V/full-temperature bound. PW bias-current sensitivity includes absolute network resistance spread; source/protection/reference-output and return impedances remain additional. Network branch current/power/loading is assessed separately from ratio tolerance. At a declared12V differential and92.5kΩ minimum resistance, each used element allocates129.730µA/1.557mW; conditional package totals are6.227mW core and3.114mW front. These are assumed linear-envelope sensitivities, not guaranteed signals/fault limits or complete rail currents. The summer amplifier drives both R7124 and R7125; those loads are not omitted. Unused elements add no ideal DC load; EP displacement currents remain unknown. Reference initial error, drift/noise/regulation, raw-reference capacitor behavior, amplifier common-mode/headroom, external source impedance, switch leakage, pot track/contact effects, thermal gradients and actual shared returns remain unqualified. No source test or nominal KCL result closes those terms.

The distinct **1mV load-change target** compares the same setting open-to10kΩ at−5/0/+5V. Results remain null/NOT RUN; neither feedback-corrected series resistance nor this load-free algebra establishes residual load error. No new A01 pitch-CV specification is inferred.

## Stop with a bounded whole-cell precision decision

Disposition: **CONDITIONAL CANDIDATE; NOT ELECTRICALLY ACCEPTED**. Keep this passive ratio improvement as a candidate, without adoption. Next recommended scope is a finite whole-cell precision allocation: define the A01 operating temperature/calibration states and separately evaluate the existing reference-inverter and control-loading errors against a reserved remainder for amplifier/reference/loading/return effects. That assessment should identify one necessary correction with a closed contribution budget before any further implementation. Do not begin another component search, fit more knobs, widen mechanics, or silently downgrade to modulation-only use. Precision intent remains the preferred objective; any changed product role requires an explicit decision.

## Checks distinguish reproducible source from hardware acceptance

Generators `stage15_packages.py`, `stage15_paths.py`, `stage15_electrical.py` and `stage15_assessment.py` support `--check`. The full `check_source.py` preserves canonical and predecessor bytes. Historical Stage14 integration reviews are checked at exactcc005dc4; current integration gets new independent review. [WORK](WORK.md) and [validation](stage15/validation.json) record actual final-source results and review authorship exclusions.

NativeKiCad10.0.6/CAD/ERC/DRC/simulation/physical are **NOT RUN**, explicitly outside authorization. Default native CI remains excluded via `[skip ci]`. PR286 remains draft/unmerged, PR285/260/277 parked, and acceptance issues remain open. No production, fabrication, procurement or energization authority follows.
