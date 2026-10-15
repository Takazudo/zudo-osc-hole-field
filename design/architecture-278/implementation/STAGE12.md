# Stage12: A01 resistance domains, capacitor candidate and DC/CV budget

Stage12 continues Stage11 `32317689d7e4b41b6c46c9f628d8b1156a3bf418` on draft PR286. It preserves all267 predecessor candidate files and all canonical sources. Five OSC,33 functions and438 fixed panel centres remain unchanged. Further strap, cassette and support elaboration is frozen. Stage1 and hardware acceptance remain OPEN.

## Resistance requirements

[Criteria history](stage12/CRITERIA-HISTORY.md) provides ten immutable source excerpts. [Budget](stage12/BUDGET.md) maps all106 retained power/return endpoints to actual source boundaries, pad coordinates and physical graph edges. PCB spreading/necks/vias, wires, crimps, GH mating/header terminations, DIN mating/pin terminations and upstream feeds remain separate. Original0.5mΩ return/1mΩ rail PCB limits and expanded architecture comparisons both remain visible; neither check is relaxed. Shared-edge endpoint counts are not current multipliers or equal-sharing credit.

The recommended domain clarification is **PROPOSED/UNAPPROVED**. Complete source/return transfer resistance, downstream state currents and regulation errors remain unknown. Owner review of the conflicting requirement wording is needed before adopting a mapping; no geometry should be elaborated to satisfy an unresolved interpretation.

## One capacitor candidate

[Capacitor evaluation](stage12/CAPACITORS.md) evaluates only C7101/C7102 as YAGEO CC0603KRX5R8BB475,4.7µF±10%,25V,X5R,0603. C7107 remains100nF. All90 packages/118 units, pins, ownership and geometry are conserved. These are candidate values only.

The initial minimum is4.23µF; retaining at least23.6407% after that initial tolerance would be necessary for1µF effective capacitance. Typical manufacturer bias curves are not guarantees: at proposed13.2V the diagnostic interval is only0.705–1.081µF. Actual combined bias/temperature/aging capacitance and ESR remain unknown. Neither REF5050AI stability ESR nor its separate noise recommendation is proven. The85°C X5R ceiling also requires product-environment review. **This candidate does not close the capacitor application gap.** Reproducible primary URLs, hashes and page locators are retained; raw PDFs remain ignored.

## Coherent accuracy study

The budget evaluates225 nominal DC states and five representative1024-corner studies of ten physical resistors. Shared R7124 changes the three summer ratios together. Loaded pots, reference inversion, summer/restore gains and ten amplifier-offset sensitivities are explicit. Conditional uncalibrated corners can reach approximately−35.10..+34.88mV for the named−5V state; this is neither a measured failure nor a complete error bound.

Historical2mV calibrated static precision,1mV output-load change and5-cent oscillator tracking criteria have distinct domains. The oscillator criterion is not automatically an A01 target. No A01 settling target or new factory calibration is invented. Proposed test grids remain unapproved; input source/protection/bias effects, calibration limits, actual operating envelopes and complete DC/CV error bounds remain open.

## Verification and next boundary

Deterministic source and mutation tests cover endpoint omission, domain relabeling, contact/shared-edge accounting, historical-limit changes, capacitor topology/arithmetic, invented guarantees and criterion promotion. Independent electrical, mechanical and code reviews disclose authorship and bind exact source bytes in stage12 review receipts. The WORK log records final executed check counts.

Native KiCad10.0.6, ERC, DRC, simulation and physical validation are **NOT RUN**. No exact-run admission exists; user continuation is not admission or hardware authority. Publication retains `[skip ci]` because default CI invokes excluded native work. No architecture adoption, merge, replication, POWER hosting, fabrication, purchase or energization is authorized. KEEP_K1402_INCUMBENT; PR285 and parked260/277 remain intact.

Recommended next bounded work: obtain an explicit requirement-domain and A01 calibration/accuracy decision, then investigate one better-supported reference-capacitor option against guaranteed effectiveC/ESR and the intended environment. Continue to freeze new mechanical elaboration until the resistance interpretation is resolved.
