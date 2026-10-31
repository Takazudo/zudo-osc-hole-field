# OPA4196 U110/U210 review (2026-10-31): model screen and land/assembly evaluation

**UNADOPTED candidate. This is a model screen and a desk comparison, not stability,
assembly or hardware qualification.** No schematic, footprint, paste or board file was
changed. TLV9364 is not considered as a substitute.

## Circuit under review

U110/U210 unit 1 is the `magnitude_indicator` cell (`design/standard/electrical-standard.json`,
cell `magnitude_indicator`). IN+ is `SLEW_BUFFERED`, the S&H output after the slew island.
The output DRIVE feeds a four-diode BAS16GW-QX bridge with the APHHS1005QWF/D LED on its
DC diagonal. SENSE returns to IN− and to AGND through R_SENSE 5.6 kΩ 1 %. The LED current
is |V(SLEW_BUFFERED)| / 5.6 kΩ. Units 2–4 are grounded followers. The rails are ±12 V.

## Requirements derived from the repository

| Corner | Value used | Source |
| --- | --- | --- |
| Supply | low +11.53 / −11.74 V; nominal ±12 V; high +12.48 / −12.37 V | load bands in `decisions/osc-supply-architecture.mdx` and `integration/power-contract/README.md` |
| Temperature | **not specified** by the project; model at 27 °C, plus 0 °C and 40 °C corners of a **PROPOSED** 0–40 °C range pending owner confirmation | `project/index.mdx` L53 states that operating temperature is unspecified |
| Signal | ±5 V full scale, 0.893 mA nominal LED current | `electrical-standard.json` magnitude full-scale disposition |
| Overload | input up to the rails (project fault range ±12 V) | `electrical-standard.json` cell notes |
| Fastest source edge | slew island R_MIN 2.2 kΩ × 5 × 100 nF = 1.1 ms time constant | candidate BOM R124, C107–C111 |
| R_SENSE | 5544 / 5600 / 5656 Ω (1 %) | candidate BOM R128, passive policy |
| Load parasitics | assumed brackets: diode Cj 1–4 pF, LED Cj 5–50 pF, DRIVE and SENSE node 0.1–20 pF | assumption; no extracted layout |
| Diode/LED DC | two assumed drop sets: about 0.63 V + 2.67 V and 0.76 V + 3.38 V at 0.9 mA | assumption; no BAS16GW-QX or APHHS1005QWF/D model or VF fact is retained |

No acceptance threshold for dark zone, recovery, ringing or phase margin is sourced. The
numbers below are reported against **proposed** screens only: PM ≥ 45°, overshoot ≤ 10 %
(borrowed from the precision-output cell screen), and no sustained oscillation.

## Model screen (`bridge_loop.py`, `bridge-loop-result.json`)

The screen used TI OPAx196 macro-model SBOMAF9 Final 1.5. The archive sha256
`9c264813…cdf5` and the `OPAx196.LIB` sha256 `31142f5d…c430` match the stage6 pins. The
simulator was ngspice-44.2 in `kicad/kicad@sha256:18693567…dd3ec` through
`scripts/kicad/run.sh`, with `ngbehavior=ps`. All 170 runs exited 0, with 0
nonconverged cases.

| Check | Cases | Result (model) | Status |
| --- | --- | --- | --- |
| Loop gain by voltage injection at IN−, ten operating points ±1 mV…±5 V | 960 | PM 47.5–122.1°; crossover 19.7 kHz–2.26 MHz. Worst case: high rails, +10 mV, 20 pF on both DRIVE and SENSE (47.5°). With ≤ 3 pF on SENSE the minimum is 55.8° | RUN; inside the proposed PM ≥ 45° screen with 2.5° to spare at the 20 pF / 20 pF bracket |
| Quasi-static transfer, 0 → ±12 V | 18 | SENSE error at ±5 V ≤ 0.03 mV; LED 0.884–0.902 mA at ±5 V; tracking holds to ±6.58 V at low rails with high drop (±7.0–8.5 V otherwise); headroom to the rail at ±5 V ≥ 1.62 V | RUN |
| Overload current | 18 | LED current while clipped at ±12 V input ≤ 1.51 mA (high rails, low drop) | RUN; well below the retained 30 mA LED electrical fact |
| Zero crossing, 5 V 100 Hz sine | 8 | 9.8–12.4 µs per crossing below 50 % of ideal current, within \|vin\| ≤ 58 mV | RUN |
| Zero crossing, 1 kHz sine (stress, above the 1.1 ms source bandwidth) | 8 | 4.9–5.7 µs; within ≤ 188 mV | RUN |
| Slow ramp through zero (2 V/ms) | 8 | 9.6–13.0 µs; within ≤ 46 mV | RUN |
| Recovery from ±10 V clipping, 1 µs edge to ∓3 V (stress) | 16 | tracks within 30 mV after 3.8–5.8 µs; overshoot 2.7–4.2 % | RUN; inside the proposed 10 % screen |
| Recovery from ±10 V clipping, 1.1 ms source time constant | 16 | error above 30 mV only while the source is beyond the clip point (154–352 µs); no overshoot | RUN |

The OPAx196 input does not use back-to-back diodes. Differential input up to the
supply span is within the absolute maximum of (V+) − (V−) + 0.2 V. The clipped bridge
therefore draws no input current, even with the 1.6–3.5 V input differential seen
before the steps (SBOS869 §7.3.3 and differential-input text, PDF index 18–20; absolute
maximum table, PDF index 4). The datasheet warns of ringing with light or capacitive
loads (§7.3.5, PDF index 21). This screen shows the near-zero, lightly loaded states
have the highest PM (about 96–122°), not the lowest.

## Temperature corners at a PROPOSED 0–40 °C range (`bridge_loop.py --temp 0|40`)

**The 0–40 °C range is a proposal pending owner confirmation, not a project requirement.**
The same 170 runs were repeated with `.options TEMP=<t> TNOM=27`. The macro-model's only
explicit temperature term is Vos drift (`E1 … DC+POL*DRIFT*(TEMP-27)`). GBW, Aol, slew,
output swing and overload recovery are not temperature-modelled, and the assumed diode
and LED models follow SPICE default temperature equations, not part data. These corners
therefore show the bridge's assumed-diode temperature shift, not the op-amp's.

| Check | 0 °C (`bridge-loop-result-t0C.json`, `61160842…4797`) | 40 °C (`bridge-loop-result-t40C.json`, `7b1c64e0…8b1c`) |
| --- | --- | --- |
| Runs exiting 0 | 170 / 170 | 170 / 170 |
| AC operating points converged | 960 / 960 | 912 / 960; **48 NOT CONVERGED**, all at +5.0 V input on nominal and high rails (every high-drop case on both rails, low-drop on one) |
| Phase margin (converged cases) | 48.9–121.9° | 48.6–122.7° |
| Tracking limit / headroom at ±5 V | ≥ 6.70 V / ≥ 1.74 V | ≥ 6.52 V / ≥ 1.562 V |
| SENSE error, LED current while clipped | ≤ 0.016 mV; ≤ 1.521 mA | ≤ 0.036 mV; ≤ 1.51 mA |
| 100 Hz crossing dark time / band | 9.9–12.6 µs; ≤ 57.6 mV | 9.85–12.53 µs; ≤ 58.1 mV |
| 1 µs-edge recovery / overshoot | 3.79–5.8 µs; ≤ 4.28 % | 3.8–5.85 µs; ≤ 4.33 % |

The 40 °C +5 V loop-gain cases are **UNKNOWN**. The DC and transient runs at 40 °C,
including +5 V operation, converged. One retry with solver-only aids
(`--conv-aid`: `ITL1=1000 GMINSTEPS=200 SRCSTEPS=200`) made 944 of 960 AC operating
points fail with NaN node voltages, so its results are not retained. No further solver
tuning was attempted.

**Not established:**
- Op-amp temperature behaviour beyond Vos drift: NOT RUN. The model does not support it.
- 40 °C loop gain at +5 V input: UNKNOWN (operating point not converged).
- Vendor diode and LED models: NOT RUN. None is retained.
- Layout parasitics: NOT RUN. There is no board for these trees.
- The ±13.2 V rail extremes used in the standard's ideal LED-current bound: NOT RUN in
  this screen.
- Visibility of the dead zone and of brightness: NEEDS BENCH.
- Model fidelity at the actual parts: UNKNOWN. A macro-model is not a guaranteed limit.

## Land pattern, paste and assembly (`land_compare.py`, `land-compare.json`)

| Item | Inherited footprint (`d686d259…2337`) | TI D0014A example (PDF index 40–41, 4220718/A) |
| --- | --- | --- |
| Pad | 1.95 × 0.60 mm at x = ±2.475, r = 0.15 | 1.55 × 0.60 mm at x = ±2.70, r = 0.05 |
| Edges | inner 1.500, outer 3.450 mm | inner 1.925, outer 3.475 mm |
| Toe extension beyond lead tip (E 5.8–6.2) | 0.35–0.55 mm | 0.375–0.575 mm |
| Heel coverage (L 0.40–1.27) | 0.13–1.20 mm | −0.295–0.775 mm (pad can end before the heel at E min / L max) |
| Pad length under the body (3.8–4.0 wide) | 0.40–0.50 mm | 0–0.075 mm |
| Gap between pads | 0.67 mm | 0.67 mm |
| Paste, if equal to copper (no margin is set in the footprint or the osc-core board setup) | 1.151 mm², 0.144 mm³ at 0.125 mm foil | 0.928 mm², 0.116 mm³ |
| Aperture area ratio at 0.125 mm | 1.84 | 1.73 |

Assessment, without changing geometry:

- **Bridging risk** is unchanged laterally, because pitch, pad width and gap are identical.
- **Joint geometry:** the longer land guarantees heel coverage across the whole lead
  tolerance. TI's example does not at one extreme.
- **Paste:** a 1:1 aperture deposits about 24 % more paste per lead. The extra paste sits
  at the inner end, under the package body (0.40–0.50 mm). There it adds nothing to the
  toe fillet and is the usual source of solder beads or balls under the body. It may
  also raise the package slightly.
- The aperture area ratio is high for both. Release is not the concern; volume and
  location are.
- **The assembler controls the final stencil.** The repository's stage24 record of JLC's
  stencil standard (`design/architecture-278/implementation/stage24/README.md`, source
  `jlc-stencil`) says production apertures may be optimised. The deposited volume is
  therefore not fixed by this footprint.

Options for the owner or assembler review, none applied here:

1. Keep the 1:1 paste and accept JLC DFM.
2. Specify a paste-only aperture for U110/U210 that drops about the inner 0.4 mm, close
   to TI's 1.55 mm example length. Copper stays unchanged.
3. Change the copper to the TI example. That is a footprint change across every
   SOIC-14 user and needs its own review.

The recommended path is option 1 or 2, decided at assembler review. Copper should not
change on this evidence alone.

**MSL and process.** TI's addendum lists OPA4196IDR as SOIC (D) 14, 2500 large T&R,
NiPdAu, Level-3-260C-168 HR, −40…125 °C (PDF index 34–35). JLC's handling of opened reels
(floor-life tracking, bake) and its reflow profile for this part are **not retained**:
there is an access/evidence gap. So are its JLC library class, stock and fees. 260 °C is
a peak rating, not a recipe.

## Evidence note

The datasheet bytes retrieved on 2026-10-31 from `https://www.ti.com/lit/ds/symlink/opa4196.pdf`
are SBOS869, JULY 2017, 52 pages, sha256 `c68223d5…5fde`. They differ from the owner bundle's
retained sha256 `d89dd600…793d`. The PDF creation date is 2026-10-16, so TI regenerated the
file. These bytes are **new evidence**, not recovery of the old bytes. They are cached
locally (git-ignored) and are promoted into `component-ti-opa4196idr` as the separate source
`src-op-audio-datasheet-20261031` (output swing, overload recovery, MSL and land-pattern
facts). The old source and its hash are unchanged.

## Paste-aperture proposal

[`paste-aperture-proposal.md`](paste-aperture-proposal.md) documents option 2 above, a
1.55 mm paste-only aperture on the unchanged 1.95 mm pad. It is a proposal only and is
not adopted.

## Status

| Check | Status |
| --- | --- |
| TI macro-model loop, transfer, crossing and recovery screen | RUN, within proposed screens; not PASS |
| Vendor diode/LED models | NOT RUN (not retained) |
| Temperature corners at PROPOSED 0 °C / 40 °C | RUN, model only; 48 AC cases at 40 °C UNKNOWN (not converged) |
| U110/U210 paste-aperture trim | PROPOSAL ONLY; not adopted |
| Land comparison | RUN (desk); assembly NOT accepted |
| JLC MSL/reflow/stencil conditions for this part | UNKNOWN (evidence gap) |
| Native KiCad, DRC, fill, hardware | NOT RUN (not authorized) |
