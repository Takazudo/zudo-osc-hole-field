# A01 conductor-current reconciliation — Issues 278 / 282

Baseline: `40ab8df2c4275d024957f5dc6a4cfd834a2e43fb`. This additive source study preserves Stage34 and all canonical files. No component or geometry is adopted. Stage26 candidate identities are not manufacturing selections. No simulation, native CAD, routing, energization or physical verification was performed.

## Primary evidence and exact scope

* [TI SLCS005AH, April 2025](https://www.ti.com/lit/ds/symlink/lm393b.pdf), section 5.5, printed page 6: LM393B IQ is **total for all comparators in one package**. At 5 V, no load, 25°C: 400 µA typical, 600 µA maximum. At 36 V, no load, −40…85°C: 550 µA typical, 800 µA maximum. VCM is V−. These are guaranteed maxima only at the stated conditions; no interpolation or fault guarantee is asserted at A01's nominal 24 V or conditional 24.85 V rail difference.
* [ADI ADG5412F/5413F Rev C](https://www.analog.com/media/en/technical-documentation/data-sheets/adg5412f_5413f.pdf), Table 1 page 3: digital input current ±0.7 µA typical (25°C), ±1.2 µA maximum (−40…125°C), VIN = GND or VDD; table supplies ±15 V ±10%, 0.1 µF decoupling. A01 uses ±12 V and approximately 4.9505 V enable, so these are not an established A01 input-current maximum.
* [TI SBOS737C, March 2018](https://www.ti.com/lit/ds/symlink/opa4197.pdf), section 6.7 page 8: ±65 mA ISC is **typical**, VS = ±18 V, 25°C. The absolute short-circuit duration allowance is to ground, one amplifier per package; it does not guarantee current or simultaneous faults. No guaranteed ISC at A01 ±12 V was found. Existing OPA4197 IQ uses four amplifiers per package, 1 mA typical / 1.5 mA full-temperature maximum at zero output current; output load terms remain separate.

The downloaded primary tables were also inspected visually. `sources.json` records retrieval hashes; PDFs are not committed. Existing component bundles establish identities; the frozen Stage26 inventory binds package pins and candidate resistor ratings in `ledger.json`.

## Package and conductor allocation

U7107 and U7108 are two LM393BIDR SOIC-8 packages, two comparators each. Unit 3 is a power unit, not another comparator. Pin 8 is +12 V and pin 4 is −12 V. Charge package IQ once to J-PWR1 and once to J-PWR2 as rail-current magnitudes, never to +5 V or AGND. Pin 7 is unused but its comparator remains powered. The two pin-1 outputs share CLIP_N; R7135 feeds one common LED path from +12 V to the negative rail. Count that resistor once, not once per comparator. J-SIG1/3 terminate at U7107.3/U7108.2; J-PWR3 also supplies U7107.6/U7108.6 input bias, not package IQ.

U7102/U7103 are two ADG5412FBRUZ TSSOP-16 packages. Pin 13 is +12 V, pin 4 −12 V, pin 5 GND. Each pin 1 is enabled through R7106/R7110 (1 kΩ) with R7105/R7109 (100 kΩ) to ground. Pins 8, 9 and 16 are grounded: only **two**, not eight, inputs load +5 V. Transferring the source maximum would suggest a 2.4 µA input allowance, but VIN and supply conditions differ. The input-return partition relative to the existing IGND term is unestablished. Neither that allowance nor six grounded-input magnitudes are silently added to the summed ledger; ADG logic current remains an explicit unknown. This avoids claiming an unsupported independent ground-current sum. Divider current alone is not the complete +5 V budget.

J-SIG drivers: REF5 U7104.1, REFN5 U7104.7, IN_BUFFER U7106.1, OFFSET_BUFFER U7106.7, SUM_NEG U7105.8. All are OPA4197IPWR source candidates. `pin_bindings` retains complete inventories for these packages and loads. No 65 mA typical value is used as a fault bound.

## Before and after

`ledger.json` reproduces every Stage34 conductor's conditional numeric subtotal (unknowns excluded), then changes only the four candidate resistor denominators. R7130–32 already have Yageo RT0603BRD075K6L 5.6 kΩ / 0.1% candidates; R7135 has RT0603BRD0722K1L 22.1 kΩ / 0.1%. Initial minima are 5594.4 Ω and 22077.9 Ω. Candidate-only, CAD-applied=false, order-ready=false remain explicit. This corrects Stage34's missing-candidate explanation without adopting parts. The 25 ppm/°C rating is retained; temperature excursion, aging, assembly drift and self-heating are not included in these initial-tolerance scenarios.

A separate scenario adds 2 × 800 µA = 1.6 mA to each analog rail. **This transfers a 36 V no-load value to actual rails as an engineering assumption**, not a guaranteed maximum or measured typical current. The 550 µA typical is not substituted as an A01 typical. Stage34's numeric subtotals omitted the unknown LM supply term; its narrative 1 mA/package planning allowance was not a numeric manufacturer bound.

All three AGND conductors retain the full-return envelope individually. They must not be summed or divided equally: sharing and patch-cable ground-loop current are unknown. Existing fault increments remain conditional historical scenarios, not validated protection. Neither rail totals nor +5 V nor signal rows acquire an established maximum. Unselected upstream protection/source limits remain unresolved.

<!-- generated comparison follows -->

| Conductor | Stage34 subtotal mA | Candidate R only mA | With assumed LM allowance mA |
|---|---:|---:|---:|
| J-SIG.1 /A01/REF5 | 0.000050 | 0.000050 | 0.000050 |
| J-SIG.2 AGND | 11.284839 | 11.291532 | 11.291532 |
| J-SIG.3 /A01/REFN5 | 0.000050 | 0.000050 | 0.000050 |
| J-SIG.4 /A01/IN_BUFFER | 0.124940 | 0.124940 | 0.124940 |
| J-SIG.5 /A01/OFFSET_BUFFER | 0.134919 | 0.134919 | 0.134919 |
| J-SIG.6 /A01/SUM_NEG | 0.134919 | 0.134919 | 0.134919 |
| J-SIG.7 AGND | 11.284839 | 11.291532 | 11.291532 |
| J-PWR.1 +12V | 19.013152 | 19.020970 | 20.620970 |
| J-PWR.2 -12V | 17.813152 | 17.820970 | 19.420970 |
| J-PWR.3 +5V | 0.104100 | 0.104100 | 0.104100 |
| J-PWR.4 AGND | 11.284839 | 11.291532 | 11.291532 |

## Remaining inputs and next boundary

Manufacturer evidence covering LM393B actual supply/common-mode/load conditions and ADG actual enable/supply conditions is required before those terms can become guaranteed maxima. OPA fault maximum, supply protection, patch-ground conditions and temperature/drift envelopes remain unknown. No wire/contact or ground-loop qualification follows. Further cloud work can reconcile a bounded primary-data update if supplied; physical current tests would require separate authorization and cannot establish a universal fault maximum by themselves. Stop for parent review; no mechanism redesign or channel replication.
