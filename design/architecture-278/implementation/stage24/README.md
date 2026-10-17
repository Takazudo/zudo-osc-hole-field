# Stage24: candidate lands and a closed allocation feasibility result

This stage prepares source definitions only from d935179b. No production footprint,
board, netlist or selected component changes. The Stage23 selection patch remains
unapplied. The retained 2 mV static target is not relaxed; no AC, settling or wiring
requirement is invented. All dimensions below are millimetres unless stated otherwise.

## Concrete SMD definitions, with process choices identified

| Candidate | Copper pad size | Centers | Copper gap | Mask opening | Paste opening |
|---|---|---|---|---|---|
| YAGEO RT/RC 0603 reflow | 0.90 × 0.80 | x = ±0.85, y = 0 | 0.80 | 1.00 × 0.90 | 0.90 × 0.80 |
| KEMET 0603 density B | 0.95 × 1.00 | x = ±0.80, y = 0 | 0.65 | 1.05 × 1.10 | 0.95 × 1.00 |

The resistor copper comes from YAGEO mounting guide V10, printed page 4 / physical
PDF index 3, Figure 4 and Table 1. Capacitor copper and 3.1 × 1.5 courtyard come
from the retained KEMET C0G/X7R Table 3 density B rows. Both exact capacitor body
variants and all seven resistor identities remain Stage21/23 candidates. Resistor
courtyard 3.2 × 1.5 is an engineering proposal, not a YAGEO requirement. Pad 1 is
local left, pad 2 right; all 19 assignments retain original pin/net/unit identities.
These nonpolar components do not justify renumbering electrical pins.

The +0.05-per-side mask and 1:1 paste apertures are explicit conservative proposals,
not manufacturer mandates. [JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)
now permit 1:1 mask; the older/general mask article distinguishes process routes.
The proposed larger windows leave 0.70/0.55 gaps, above the stated black/white 1 oz
and any-color 2 oz spacing thresholds. Neighboring tracks must remain at least
0.09 from mask openings. This local pad check does not prove board-wide clearance.

[JLC's stencil standard](https://jlcpcb.com/help/article/opening-process-standard-of-stencil)
allows production aperture optimization. Its explicit 0603 dimensions belong to
**red glue**, not solder paste; they are not used here. The solder-paste anti-bead
rule names 0805 and larger parts. Candidate paste is therefore explicitly 1:1,
subject to assembler review. The report calculates rectangular aperture area ratios
and nominal deposited volumes for proposed 0.10 and 0.12 foil thicknesses; neither
foil nor paste transfer efficiency is qualified. Equal pads and aperture symmetry
are retained. There is no stencil-order file or fabrication output.

These patterns differ from the historical captured assets. Their extra occupied
area requires collision/thermal/assembly review before placement binding; locked
placements are not moved to make them fit. Definition, mask/paste proposal and
manufacturing acceptance remain separate states.

## DIN transforms preserve the manufacturer views

HARTING female 09032966824 uses drawing 0903296X824 revision C view A; male
09031966922 uses 0903196X922 revision B view B. The view arrows and solder-tail
sections show both drilling views looking from the component body toward the
board. The male's upward page arrow is not a reason to mirror it: its solder tails
point upward in that elevation. Female rows remain a/b/c and male c/b/a as drawn.

The candidate local frame keeps drawing x right and converts y up to y down:
`(x, y) → (x, -y)` for both. All 96 named positions on each connector are retained,
including NC contacts; no mating rotation or installed front/back transform is
inferred. The report retains every net/null assignment, so a future board transform
must preserve labeled identities, not simply make two unlabeled grids coincide.

The contact-pad proposal is Ø2.00 copper with Ø2.10 mask opening and no paste;
finished plated contact holes retain HARTING Ø1.00 ±0.10. Manufacturing drill size
is deliberately unspecified. Pitch remains 2.54. Female fixing holes are separate
non-electrical NPTH proposals, Ø2.8 +0.1/−0, x = ±45 and y = −0.3 in this frame.
The male drawing's flange holes remain body features, not invented PCB holes.
Board thickness, mechanical registration and through-hole soldering remain open.
These DIN parts are not newly qualified for reflow or pin-in-paste assembly.

JLC's standard +0.13/−0.08 finished-hole range cannot guarantee the drawing:
meeting the lower limit requires nominal ≥0.98, while the upper requires ≤0.97.
No nominal adjustment solves that contradiction. Published ±0.075 position also
does not guarantee HARTING's Ø0.05 position zone. This is a concrete **default-process
fabrication blocker**, requiring a confirmed tighter process or an independently
justified connector/process change before release. No supplier was contacted.
The Ø2.00 pad leaves about 0.329 conservative annular ring using the largest default
hole and independent ±0.075 axis errors, exceeding the 0.254 screen; that ring
margin does not waive the hole/position mismatch. Female NPTH tolerances also need
specific fabrication confirmation. All 22 wire/land annotations remain without a
physical definition until wire/strain-relief/serviceability is selected.

## Reference allocation is infeasible with the retained error terms

The report solves the allocation question instead of assigning an unsupported
resistor tolerance. It takes the existing Stage15 2 mV static target and each
retained state’s nominal loading error. At manual quarter/three-quarter settings,
loading alone is about 4.928 mV, leaving **−2.928 mV** before reference, amplifier,
ratio, temperature or other error. The mixed state leaves about −3.359 mV.
A nonnegative complete reference allocation does not exist for the retained
uncorrected model. This is a source-model infeasibility result, not a measurement
or a complete worst-case bound.

Independent 0.1% reference-inverter resistors allow 10.010 mV negative-reference
ratio error at 5 V. Separately, the retained REF5050AI initial 0.1% table-condition
sensitivity is 5 mV at 5 V. It alone cannot support a guaranteed uncalibrated 2 mV
absolute endpoint target. Do not add these different contributions indiscriminately
across different states or claim their worst signs necessarily coincide.

A matched ratio of 0.010%/0.0125% gives 0.500/0.625 mV ratio-only contribution at
5 V. The already retained LT5400AIMS8E-2#PBF RN7102 has spare elements R3 (pins 3–6)
and R4 (4–5), currently NC. Reuse would change the inverter's 10 kohm resistors to
100 kohm and alter those NC connections. At the retained 15 nA bias sensitivity,
nominal contribution rises from 0.150 to 1.500 mV (100 kohm +7.5% gives 1.6125 mV),
before offset and other effects. Matched spare reuse is therefore **not recommended
as a drop-in correction**. Full-range matching already includes its temperature
bound; do not add drift again or treat two elements as independent ±matching values.

Engineering recommendation: retain the 2 mV intent, first correct loading and
provide an explicit reference/calibration correction path, then allocate a positive
remainder to a low-impedance matched inverter and amplifier errors. Existing knob
fits do not implement calibration hardware (Stage13). No calibration or reference
replacement is adopted here. A component-only tolerance change cannot close the
existing deficit, so the selection patch remains unapplied. The next engineering work must address the control/reference path; repeating
supplier or tolerance audits cannot remove this deficit.

## Filter recommendation with numerical tradeoffs

For the manual control, increasing the 10 Mohm return to 100 Mohm reduces ideal
maximum loading from about 5.094 mV to about 0.510 mV, but increases open-wiper
leakage sensitivity from 10 to 100 mV/nA. A 1 Gohm option reaches about 0.051 mV
and 1 V/nA, an unattractive failure/leakage tradeoff. Recommend preserving a defined
fail-safe return and reviewing a buffered control topology rather than silently
raising resistance. This requires source topology review, not owner selection of
a resistor tolerance.

With the retained 100 kohm pot, 1 kohm series and 10 Mohm return, 10 nF gives about
1.194 ms to 1% at center; 1 nF gives about 0.119 ms with ten times higher RC corner frequency.
Changing capacitance does not fix DC loading. Recommend retaining approximately
this millisecond response as a **proposal**, and preferring a stable C0G control
filter if the eventual response requirement warrants it; C7105's X7R candidate
remains unapproved pending effective-capacitance and dielectric-policy resolution.
No new value, dielectric, MPN or settling requirement is selected.

For the attenuverter, retain the existing DC specification but do not call the
present center an audio-band null. At 20 kHz, the ideal existing 10 pF feedback-only
model leaves 6.234% center gain, about 312 mV from 5 V. A symmetric input/feedback
RC proposal cancels center leakage in the ideal equal-component model; independent
±5% capacitors still permit about 0.624% at 20 kHz, roughly 31 mV from 5 V.
It changes high-frequency noise gain and needs finite-amplifier, parasitic and
remote-path stability analysis. Removing compensation to improve a null is not a
qualified alternative. The report includes 1, 10 and 20 kHz sensitivities; none is
an adopted acceptance frequency.

The genuinely owner-dependent boundary is whether the center must suppress audio
through the intended band or is only a DC/CV null, and whether approximately 1 ms
manual response is acceptable. Recommend the symmetric-network investigation if
an audio null is required. Wiring serviceability is likewise still a product choice.
This stage stops at those behavior/architecture boundaries, with concrete source
patterns and numerical comparisons ready for the next decision.

## Validation and preserved boundaries

Run `stage24_patterns.py --check` and the Stage24 unit suite under
`scripts/architecture278/implementation/`. `--check-cache` verifies the three new
JLC receipts. Manufacturer drawings, primary electrical evidence and earlier reports
remain hash-bound, unchanged historical inputs. Independent review binds the final
files. Output is `patterns-budget-report.json`, not production CAD.

No native commands, admission reuse, purchase, supplier contact, merge or architecture
adoption. Canonical boards, locked placements, decision.json, KEEP_K1402_INCUMBENT
and prior FAIL receipts remain unchanged. PR286 remains draft/unmerged. Next native
request: **NONE**. Next bounded action is a scoped control/reference correction proposal, with owner
direction only where the audio-null or response behavior changes; no further unchanged audit is
needed to establish the negative allocation or default DIN tolerance mismatch.
