# Swapping five OPA4196 input buffers for TSSOP-14 OPA4197 adds 17 to 25 mA on each analog rail, which is already over its ceiling

Stage 3 electrical comparison, 2026-11-21, for the owner's choice "Try a smaller chip package". OPA4196 is
orderable only in SOIC-14 (SBOS869 package addendum), so the TSSOP-14 option is OPA4197IPWR, already a
project part (`component-ti-opa4197ipwr`). U1518 is already OPA4197IDR; for it the change is a package
swap of the same die. **Nothing is substituted.**

## Retained facts side by side

| Property | OPA4196IDR (`component-ti-opa4196idr`) | OPA4197IPWR (`component-ti-opa4197ipwr`) |
| --- | --- | --- |
| Quiescent current per amplifier, typ / max 25 °C / max −40..125 °C | 0.14 / 0.20 / 0.25 mA | 1.0 / 1.3 / 1.5 mA |
| Input bias current, typ / max 25 °C | 5 / 20 pA | 5 / 20 pA |
| Output swing from rail at 10 kΩ, max | 110 mV | 125 mV |
| Supply, absolute max / recommended max | ±20 / ±18 V | ±20 / ±18 V |
| Input voltage, absolute | rails ±0.5 V, 10 mA | rails ±0.5 V, 10 mA |
| GBW | 2.5 MHz typ (`fact-op-audio-gbw`) | 10 MHz typ (`fact-op-precision-gbw`) |
| Input capacitance | 6.4 pF common-mode typ | 6.4 pF common-mode typ (`fact-op-precision-input-impedance`) |
| Capacitive-load guidance | no safe threshold stated | 1 nF unity-gain drive, no safe threshold stated (`fact-op-precision-capacitive-load-guidance`); vendor-model output-stability pass 12/12 in its precision role, not this one |

## The supply current is the decisive cost

Five packages change (U1216, U1416, U4346, U8314, U8417), which is 20 amplifiers:

- typical: 20 × (1.0 − 0.14) mA = **+17.2 mA** on +12 V and on −12 V;
- full-temperature maximum: 20 × (1.5 − 0.25) mA = **+25.0 mA** on each rail.

`design/power/rail-budget.json` already puts the −12 V reported typical subtotal at 761.3 mA against a
640 mA ceiling, and the planning upper subtotal 746.7 mA over it. The swap would add to an existing
overshoot that #34 owns. It does not create the problem, but it makes it worse.

## What a decision still needs

1. A ruling on the rail cost above, against #34's rail closure.
2. OPA4197 GBW, input capacitance and capacitive-load guidance are now retained from SBOS737C in
   `component-ti-opa4197ipwr`. The fourfold GBW (10 versus 2.5 MHz) changes loop dynamics in each
   follower and must be part of the electrical review.
3. An electrical review of the input stages with the new part. The protection path (TMUX7412, 10 kΩ,
   clamps) is unchanged, and the module tests (`test_envelope.py`, `test_mixers.py`, `test_oscillator.py`)
   must still pass.
4. The 25 mm radius rule for the four buffers that would land beyond it (`result.json`).

Paper comparison of retained facts only. No simulation, no measurement.
