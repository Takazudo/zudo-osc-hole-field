# MC04 stage 1b: indicator-loop paper screen

Status: **DRAFT paper screen, not a stability result.** Every schematic and PCB remains an unvalidated draft.

Stage 1a ([`mc04_s1_budgets`](../mc04_s1_budgets/)) left the magnitude-indicator LED bridge nets undetermined, because
they sit inside the op-amp feedback loop. This study screens those loops so that the four blocks held only by them
(U2119, U4347, U4348, U8318) have a stated reason either to proceed to simulation or to stop.

## Result: the screen passes, simulation still decides

In both pinned boundaries, only `*_LED_A` and `*_LED_K` cross for every indicator unit; `*_DRIVE` and `*_SENSE` stay
on the op-amp's board. With 7.22 pF added to each LED net:

| Bridge current | V(SENSE) at 5.6 kΩ | Phase margin, no cable | Phase margin, cable |
| --- | --- | --- | --- |
| 1 µA | 5.6 mV | 88.9° | 73.2° |
| 10 µA | 56 mV | 83.8° | 69.0° |
| 100 µA | 0.56 V | 84.6° | 77.9° |
| 1 mA | 5.6 V | 89.2° | 88.2° |

All 13 crossing units have R_SENSE 5.6 kΩ and OPA4196, so they share these numbers. The worst margin, about 69°,
does not depend on the diode ideality (it only moves the current where the worst case occurs). It falls to 57° at
twice the cable capacitance and 40° at four times (29 pF), below the ASSUMED 45° criterion.

## Method

`beta(f) = V(SENSE)/V(OUT)` for the ladder OUT, diode r_d, LED_A (C), LED r_d, LED_K (C), diode r_d, SENSE
(R_SENSE in parallel with the op-amp input capacitance), with `r_d = n·V_T/I`. Loop gain `GBW/(j f)·beta`; the phase
margin is taken at its unity crossover. GBW and input capacitance come from the retained OPA4196 facts.

ASSUMED: ideality 2 for the BAS16GW and the LED (no retained fact), a single-pole amplifier with ideal output, the
45° criterion. Not modelled: off-path diode junction capacitance, PCB parasitics, amplifier output resistance and
higher poles, the bridge dead band, and large-signal slewing. Those are exactly what case 5 of the
[WSL brief](../../../../circuit/orchestration/campaigns/osc-stack-20261114/mc04-s4-input-buffer-native-brief-20261121.md)
checks with the vendor model.

## Reproduce

```sh
python3 scripts/stack/studies/mc04_s1b_indicator_loops/loops.py
```

It refuses to run if either pinned crossing-net list changed. `result.json` sha256
`edc5c59b50d7b9551e8a5a07793beb2c3831ce58f742cefdf3837777b68580ad`.
