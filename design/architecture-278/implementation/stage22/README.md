# Stage22: requirements and physical evidence closure

This source-only follow-up starts at 052eb53b. It adopts no candidate, modifies no
production CAD and requests no native execution. Historical native FAIL receipts
and the later Stage20 representation replay remain separate and unchanged.

## Blockers removed

- Normal or explicitly conditional electrical loading is now derived for all 19
  passive references, with complete frozen package records checked against Stage21.
- The YAGEO mounting guide supplies process-specific 0603 pad recommendations;
  the RT family data sheet supplies the correct 70–155 °C derating curve.
- Exact HARTING drawings establish both 96-contact drilling patterns and their
  distinct A/B pin views. The report retains 192 labeled drawing coordinates.
- All three previously unresolved candidate distributor identities are now resolved
  in DigiKey catalog tables. This closes identity research, not JLC allocation,
  availability, purchasing or candidate adoption.

`evidence.json` records primary URLs, dated receipts, hashes, drawing locators and
exact supplier codes. Raw receipts remain in ignored local cache. DigiKey receipts
are browser text extractions, explicitly not raw HTML; earlier blocked lookups
remain historical and never establish absence.

## Derived electrical requirements

These are ideal nominal models or named conditional bounds, not installed ratings.
The existing source specifies nominal ±12 V rails, ±5 V signals and ±12 V external
continuous input faults. Proposed ±13.2 V, 85 °C and 20 kHz sensitivities are not
owner-approved requirements. The deterministic report gives full precision.

| References | Derived load or accuracy | Remaining technical qualification |
|---|---|---|
| R7101, R7102 | 5 V, 2.5 mW each; independent 0.1% values permit 10.010 mV reference ratio error | Complete 2 mV static error allocation, tracking and temperature |
| R7103 | Retained 100 kohm lower leg gives 40.984 µA, 0.902 V top-resistor drop and 36.952 µW | Buffer bias and divider ratio error |
| R7106, R7110 | Enable feed gives 49.505 µA and 2.451 µW; grounded enable at nominal 5 V gives 25.025 mW at minimum resistance | Logic leakage, clamps and sequencing |
| R7108, R7112 | Input leakage produces 10 µV/nA; conditional 24 V across the part gives 57.658 mW | Protection must actually enforce the declared node envelope |
| R7113 | 2 mA driver obligation gives 0.2002 V and 0.4004 mW at maximum resistance | Harness short and loop stability; 24 V would dissipate 5.766 W |
| R7114 | 10 µV/nA bias sensitivity; 100 pF feedback capacitor gives a 159.155 kHz RC frequency | This frequency is not phase-margin evidence |
| R7115, R7119 | Ideal return-current bound 0.5 µA gives 0.5 mV and 0.25 nW | Pot loading, input bias and capacitor charging pulses |
| R7116, R7120 | 5 V gives 2.5 µW; open wiper gives 10 mV/nA | Fail-safe tendency is not a guaranteed zero |
| R7130–R7132 | 5 V gives 4.464 mW; conditional rail-to-ground 12 V gives 25.740 mW | Amplifier/LED headroom; ideal A01 sum can reach ±15 V and clip |
| R7135 | Conservative zero LED/transistor drop across nominal rails gives 1.087 mA and 26.089 mW | Brightness/headroom; this resistor does not set clip threshold |
| C7104 | Ideal normal voltage ≤5 V; 10 pF across 100 kohm gives 159.155 kHz pole | AC center leakage and finite-amplifier stability |
| C7105 | Ideal normal voltage ≤5 V; ideal full 10 V reversal dissipates 0.5 µJ in the resistive path | Effective capacitance, dielectric policy and pulse qualification |

Allocating the entire 2 mV static target to the negative-reference pair would
require individual initial tolerance about 0.020%, with nothing left for other
errors. That is an engineering budget failure to resolve, not a reason to silently
adopt a tighter part or ask the owner to choose resistor tolerances.

For the nominal 100 kohm manual pot, 1 kohm series resistor and 10 Mohm return,
the center RC time constant is 0.2593 ms and 1% settling is about 1.194 ms.
Endpoint loading is about 0.500 mV, but interior loading exceeds 5 mV. The exact
stationary point is calculated in the report. Stored capacitor energy at either ±5 V endpoint is 0.125 µJ. The full-reversal initial resistor
pulse is about 100.1 mW at minimum resistance; this is not a continuous load.

For equal nominal attenuverter resistors and an ideal amplifier,
`H(alpha,s) = alpha + (alpha - 1)/(1 + sRC)`. At center the DC gain is zero, but
at the proposed 20 kHz sensitivity the residual is about 6.23% of input, or
312 mV for a 5 V input. This is not a failure against a DC-only criterion.
An illustrative 0.5% center-leakage limit would extend only to about 1.592 kHz
in this ideal model. No AC null-bandwidth requirement has yet been approved.

The RT0603 curve permits 82.35 mW at a proposed 85 °C ambient; PCB heat flow and
solder-joint temperature still need qualification. The mounting guide's example
thermal resistance is not an installed board value. C7105's `c_small` control
filter role has no explicit bypass classification: the X7R candidate needs a
policy classification or a reviewed exception, not automatic acceptance.

## Assembly recommendation and exact drawings

Use contract reflow as the default proposal: YAGEO 0603 reflow pads are 0.9 × 0.8 mm,
with 0.8 mm gap and 2.6 mm outer span. Wave pads instead have 0.9 mm gap and
2.7 mm outer span. The captured resistor pads differ. For KEMET capacitors,
use the Stage21 manufacturer density B pattern as the practical reflow proposal;
density A offers more soldering access/area, while density C saves area at a
qualification and assembly-process cost. No pattern is adopted here. Mask, paste,
annulus, courtyard and thermal qualification remain implementation work.

Female 09032966824 drawing 0903296X824, revision C, view A, has rows a/b/c top to
bottom and columns 32 to 1 left to right. Male 09031966922 drawing 0903196X922,
revision B, view B, has rows c/b/a. Both specify 96 holes Ø1 ±0.1 mm on 2.54 mm
pitch, with Ø0.05 positional tolerance. These distinct drawing views must not be
silently converted to a common top view. Female PCB fixing holes are Ø2.8 +0.1 mm,
90 ±0.1 mm apart, offset 0.3 ±0.1 mm toward row a. Male Ø2.55 flange holes are
connector-body features: no corresponding PCB fixing holes are inferred.
The male is straight. Generic press-in drilling is not applicable.

Coordinates in the report use drawing-view x right/y up and array-center origin.
They are not footprints. Board-side transforms, board thickness, pad annulus,
plating interpretation and manufacturing drill tools remain engineering work.

For the 22 wire/land annotations, propose direct soldering with mechanical strain
relief and service only while unpowered. This keeps area, cost and contact count
low. If frequent field replacement is required, choose pluggable termination and
accept extra connector area, cost and contact interfaces. Wire gauge and strain
relief details follow the load and mechanical design; the annotations remain
excluded from fitted-part counts.

## Precise next choices and stop boundary

1. Confirm the proposed mixed-source reflow prototype route, with the three exact
   DigiKey candidates populated separately if necessary, or require JLC-only
   sourcing. JLC-only still requires exact codes or separately reviewed substitutions
   and assembly-route confirmation. Catalog identity does not establish stock.
2. Confirm permanent soldered/strain-relieved wiring, or require field-replaceable
   pluggable wiring. This decides the termination architecture before footprint work.
3. Define the required attenuverter center-null bandwidth and acceptable manual
   control settling. These are product behavior choices; the engineering follow-up
   should then close the error budget, filter dielectric classification and stability.

Do not ask the owner to specify drill transforms, leakage calculations or individual
resistor tolerances. Those remain engineering tasks after these product/process
choices. The 19 candidate selections and 24 physical bindings remain unadopted.
No electrical acceptance, procurement release, PCB release or new native admission
is implied. The next native request is **NONE** for this unchanged-CAD work.

## Reproduction

Run `python3 scripts/architecture278/implementation/stage22_requirements.py --check`
for deterministic derivation and preservation checks. Add `--check-cache` where
retained raw receipts are available. The Stage22 unit suite includes topology,
identity, omission, view, supplier and assumption-promotion regressions. Review
receipts bind implementation inputs; later changes require renewed review.
