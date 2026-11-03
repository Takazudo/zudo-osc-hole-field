# Current A01–A06 musical utility acceptance

**This is the current owner-approved ATTEN/OFFSET acceptance scope.** It supersedes
the A-cell precision applicability in Stage15–25 and the inherited generic OSC-ES-1
precision-output target for these six modules only. The original standard, reports,
calculations and native FAIL receipts remain immutable historical evidence. No
historical failure is turned into a pass.

The owner stated on 2026-10-17 04:03 UTC that ATTEN/OFFSET is for coarse musical
CV manipulation and its requirements should be relaxed. The exact quote and scope
interpretation are in [acceptance.json](acceptance.json). The original 2 mV number
came from an owner-delegated engineering planning standard, not an initial owner
numeric specification. That inherited target is now **not applicable to A01–A06**.
No arbitrary replacement accuracy tolerance is introduced.

The associated 1 mV precision load-change limit is also retired for these utility
cells as an explicit engineering interpretation of the clarified use. This does
not waive output loading, current, thermal or stability checks. VCO 1 V/oct tracking,
octave-step requirements, buffered multiples, S&H/storage and every other precision
path retain their existing contracts. An upstream quantizer cannot correct a
downstream VCO scale or nonlinearity error. The resolver uses exact A01–A06 module
identities; it cannot relax an oscillator or an unrelated shared cell by prefix.

## Current requirements and removed work

Retain `OUT = gain * IN + manual OFFSET + OFFSET CV`, intended ATTEN −1..+1,
independent inputs, nominal ±5 V contributions, continuous no-detent OFFSET and
nominal ±10 V internal clip indication. A mathematical ±15 V combined command
still clips on ±12 V supplies; there is no new rail/headroom promise.

The [functional check contract](functional-checks.json) keeps safety, stable operation,
useful range, noise/control artifacts, clipping/recovery, sensible loading, practical
settling and manufacturing checks. It specifies what to observe and the method,
without manufacturing an unsupported millivolt/noise/settling limit. Physical checks
are NOT RUN, not passed. No sustained oscillation, uncontrolled faults or unusable
range is excused by the word “coarse.” Existing protection and remote-harness limits
remain. The output load envelope still includes 10 kΩ; load sag must be observed
at unchanged settings. Audio center-null precision is not a new requirement, and
existing compensation is not removed to chase an ideal null.

The following no longer block A-cell source work: closure of a complete 2 mV error
allocation, metrology-style baseline/temperature protocol, precision reference
replacement, reuse of spare matched inverter elements, a CV gain trim solely to
meet 2 mV, and a lower-impedance pot solely to reduce fixed-knob error. Existing
matched networks are left in place; no new teardown/cost-down redesign is required.
Operating temperature and time remain relevant to ratings/stability and practical
behavior, but an unanswered precision-service-envelope question from Stage25 is
no longer an A-cell accuracy blocker.

## Keep the 100 kΩ manual pot; select the sourced passives

RV1308 stays **PTV09A-4020F-B104, 100 kΩ**. Stage25's B103 option is superseded as
unnecessary for this intended use, not declared electrically defective. Retaining
B104 avoids tenfold reference-track current and the changed filtering response.
Its nominal center 1% RC settling remains about 1.194 ms, a diagnostic rather than
an acceptance deadline. No controls, nets, NCs or placement move.

The 19 exact Stage23 passive identities are now selected in a separate **source
candidate inventory**. All nine manufacturer MPN/JLC-code pairs and ratings are
preserved; no substitute search or fresh-stock promise. The retained dated JLC
receipts establish catalog identity/SMT route, not allocation or order readiness.
Every one of the 118 references, 561 pins and 154 unit UUIDs remains, including
all annotations and exclusion flags. The only unit-property changes are exact
MPN, Manufacturer, LCSC and a source-candidate identity status for those 19 passives.
Original unit metadata remains bound in the historical input. No native schematic,
board, library or canonical inventory was rewritten.

C7105's **KEMET C0603C103J5RACTU, 10 nF X7R** is accepted specifically as a candidate
for nonprecision manual OFFSET smoothing. It is not reclassified as bypass and
this is not a global `c_small`, timing, storage or reference dielectric exception.
Effective capacitance under bias, aging, microphonics, charging pulses, practical
response and assembly qualification still need their appropriate evidence. C7104
remains 10 pF C0G compensation with its actual loop obligations. The source inventory
selection is now useful without waiting for retired precision gates; it does not
claim installed thermal/fault/footprint/assembly acceptance.

## Oscillator calibration clarification — reuse the existing architecture

The additional owner statement asks for rear-accessible calibration to accommodate
individual oscillator differences, with final playing pitch manually tuned. This
already matches the source architecture: six rear trimmers per oscillator plus a
shared octave-span adjustment. [oscillator-calibration.json](oscillator-calibration.json)
binds the exact O1 package/pin/role records; O1–O5 share the generator. No additional
control is justified by this review, and none is added.

| Existing O1 control | Source function and range | What it does not establish |
|---|---|---|
| RVO1106 BASE_TRIM, 10 kΩ | Across buffered ±5 V, wiper through 1 MΩ to exponential sum; nominal ±5 µA injection, equivalent to ±0.5 V at the 100 kΩ pitch input | Shifts base pitch; does not correct V/oct scale or nonlinearity. Actual core adjustment reach remains unmeasured. |
| RVO1108 SCALE_TRIM, 1 kΩ | 1.5 kΩ fixed plus 0..1 kΩ adjustment at SCALE_PIN | Adjusts the voltage/frequency ratio. Base/scale interact and need iterative checks; guaranteed tracking is not inferred from resistance range. |
| RVO1107 RZ_TRIM, 10 kΩ | 24 kΩ fixed plus 0..10 kΩ on Scale1; existing current-balance/compensation function relative to Scale2 5.72 kΩ | Not another user pitch knob and not a blanket temperature guarantee. |
| RVO1109 HF_TRIM, 20 kΩ | Between HF_PIN and AGND, wiper to LINEAR_REF | High-frequency correction; no arbitrary full-band linearity guarantee. Exact 20 kΩ MPN remains missing. |
| RVO1110 SINE_SYMMETRY / RVO1111 SINE_LEVEL, 10 kΩ each | Existing waveform symmetry and level adjustments | Not pitch or tracking calibration. |
| Shared RV1601 | Octave-reference span adjustment | Does not replace per-oscillator scale/HF adjustment or prove every ladder step. |
| Front RV104 TUNE / RV105 FINE | Existing user coarse/fine pitch controls after calibration | Final musical tuning does not repair a wrong octave ratio. |

The ±0.5 V figure is a nominal current-equivalence calculation, not a guaranteed
frequency correction span of an AS3340 lot. Rear tool/access reservations remain
source intent, not measured access. The existing procedure already checks rails,
warmup, octave references, base frequency, a measured 0→1 V / 2:1 frequency ratio,
then high-frequency behavior and rechecks low frequencies before waveform trims.
Base-frequency adjustment cannot substitute for scale or nonlinear correction.
The historical nominal 65.406391 Hz calibration point is a setup reference, not a
new requirement to hold one absolute note during playing.

There is **no demonstrated missing calibration degree of freedom**. There is an
actual exact-part gap for RVO1109: its source requires 20 kΩ while the selected MPN
is blank; the generator's 10 kΩ symbol/template does not supply a 20 kΩ identity.
Adjustment reach over real component spread, interaction, temperature and core
nonlinearity is still unqualified. This is a sourcing/qualification gap, not grounds
to add redundant pots. No physical calibration or native run occurred, and no
oscillator tracking numeric target was relaxed by the A-cell decision.

## Checks, evidence and next bounded step

`stage26_acceptance.py` resolves current applicability and deterministically emits
`acceptance-report.json` and `candidate-inventory.json`. Negative tests reject
scope spillover, invented limits, safety omissions, false passes, substitutions,
rewiring, NC shorts, missing units, fitted annotations and oscillator calibration
role confusion. Source tests do not certify hardware.

The current `check_source.py` first reproduces the prior source checkpoint and its
180 regressions in a disposable detached checkout of f30d653e, then checks the live
Stage26 scope/inventory and independent review. This is necessary because historical
reports deliberately bind their old entrypoint bytes. It preserves rather than
rewrites those checks. The live whole-repository guard permits only the reviewed
README/WORK/check entrypoint changes plus Stage26 additions; all canonical files,
old stage artifacts, decision.json and KEEP_K1402_INCUMBENT are protected.

Next bounded engineering work is physical/source binding: the already prepared
DIN position/fixing/process specification and a concrete externally assembled
wire/termination/strain-relief proposal, retaining locked geometry. Exact HF-trimmer
sourcing can be addressed within the oscillator's existing function when that path
is resumed. No more A-cell precision-allocation, pot-change or reference redesign
audit is required. No third-party contact, purchase, merge, production CAD change,
architecture adoption or native admission follows. PR286 remains draft; native
request **NONE**.
