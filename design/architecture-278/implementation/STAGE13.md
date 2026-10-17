# Stage13: larger reference capacitors and existing-control limits

Stage13 continues Stage12 `5452566c3622f8c382f5be026f23b29b511abdca` on draft PR286. It implements one candidate capacitor pair with local package placement and assesses A01 calibration using its two existing controls. All289 predecessor files remain unchanged, including both resistance-domain reports and all strap/cassette/support geometry. FiveOSC,33functions and438fixed panel centres remain intact. Stage1 and hardware acceptance remain OPEN.

## Candidate implementation and evidence

[Capacitor study](stage13/CAPACITORS.md) selects KEMET **T491C475K050AT**,4.7µF±10%50V MnO2 tantalum for C7101, and **T491D226K035AT**,22µF±10%35V for C7102. C7107 remains100nF. Candidate value/identity/package changes are isolated; canonical0603 footprints and BOM remain unchanged.

Primary exact-part and family documents provide nominal/tolerance, temperature-stability and endurance test conditions, leakage, ESR, dimensional maxima and recommended lands. Source URLs/hashes/physical and printed page locators are committed. These improve the evidence over Stage12's typical MLCC bias curves, while combined operating bias/temperature/age capacitance remains unknown. Separate qualification tests are not multiplied into a lifetime guarantee.

Input/output initial intervals are4.23–5.17µF and19.8–24.2µF. The output ESR maximum0.7Ω at100kHz/25°C is below TI's1.5Ω stability limit at that condition; it does not prove full-condition stability or satisfy the separate1–1.5Ω noise recommendation. The pair is polarized. Power reversal, sequencing, inrush and output discharge remain unqualified. Output charge at5V increases5→110µC; startup current/time and the reference's complete load budget remain open.

## Local package result

[Package study](stage13/PACKAGES.md) replaces only the two candidate packages using manufacturer density-B lands and courtyard envelopes. Maximum bodies are6.3×3.5×2.8mm and7.6×4.6×3.1mm. All90packages/118units and the other88 placement records are preserved. The larger packages clear the checked A01-core envelopes and frozen Stage11 modeled support/strap/service envelopes; this does not select those options or establish installed fit. Eight historical other-function projections remain reserved with unknown new depths.

Six local capacitor-to-REF5050 pad distances include both positive and return legs. C7101's ground separation grows4.101→8.904mm, despite shorter input-positive separation. C7107 remains local. These are geometric lower bounds, not routes or loop-impedance qualification. Four moved source pads and their incident baseline graph edges are explicitly invalidated for this overlay. Historical full-path budgets remain intact; complete overlay path metrics are null until rebudgeted.

## What the existing controls can adjust

[Calibration study](stage13/CALIBRATION.md) uses captured RV1307/RV1308 and the coherent Stage12 resistor model. IN gain, CV gain and offset are three observable affine quantities. The two controls provide two adjustment directions: ATTEN changes IN gain and can also change intercept when input offsets exist; OFFSET changes intercept. **Neither adjusts OFFSET-CV gain.** A fitted three-coefficient correction is not implemented in hardware.

The study retains11 nominal/physical-corner cases with33 bounded presets and297 independent IN/CV residual points, plus two offset-coupling/range examples with18 further points. Nominal zero gain occurs near electrical fraction0.500175; the loaded clockwise endpoint reaches approximately0.999800. Exact+1 is then unreachable, without by itself violating the historical0.5% endpoint target. Conditional retained resistor witnesses leave CV-only5V residuals approximately−19.960..+20.040mV after IN-gain and zero-offset adjustment. These are source calculations, not measured failures or an exhaustive tolerance envelope.

The documented centre/endpoints, manual span, CV unity, output DC/drift/load and clip-threshold observations remain distinct. Temporary knob settings do not establish persistent calibration across user settings. Retained2mV static and1mV load-change criteria are not relaxed or conflated; complete errors remain unknown. No new trim, network, firmware or calibration policy is introduced.

## Checks and continuation boundary

Source/mutation tests and independent electrical/mechanical/code reviews cover exact evidence and polarity, whole-package conservation, local pad transforms and path invalidation, coherent resistor witnesses, control coupling/range, mathematical-fit boundaries and unqualified acceptance. Final executed check counts are recorded in WORK.md; review receipts bind exact source bytes and disclose authorship exclusions.

Native KiCad10.0.6, CAD generation, ERC/DRC, simulation and physical validation are **NOT RUN**. No exact-run admission exists. Publication retains `[skip ci]` because default CI invokes excluded native work. PR286 stays draft/unmerged; canonical sources, KEEP_K1402_INCUMBENT and parked260/277 are preserved. No adoption, replication, POWER hosting, purchase, fabrication or energization follows.

Recommended next bounded source work: recompute the candidate graph paths affected by the four moved capacitor pads and assess the exact REF5050 startup/charge/leakage/discharge budget for this pair. Retain both resistance-domain interpretations until an explicit decision resolves them. A01 acceptance must also distinguish achievable temporary operating presets from unsupported persistent calibration. Keep mechanical elaboration frozen; further topology changes require a separate scope decision.
