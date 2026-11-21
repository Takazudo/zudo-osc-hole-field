# Draft limits: six input-buffer blocks cannot cross the cable, two output blocks can, four depend on their indicator nets

Stage 1a of the remedy the owner accepted on 2026-11-21 (option D, developed in stages). **These are DRAFT
criteria for independent review, not accepted budgets.** Revised after the first independent review
(findings B1, B2, S1 to S6 and N1 to N5 applied).

```sh
python3 -B scripts/stack/studies/mc04_s1_budgets/budgets.py --output scripts/stack/studies/mc04_s1_budgets/result.json
```

`result.json` sha256 `22304bca637eab86d4a23111e68c1006f7ebe1b69d299be55732bfdd90961dfd`.

## Inputs

- The new crossing nets of each block boundary: 55 per boundary (steps 5a and 5b, pinned by hash); the 26
  indicator LED nets are the same in both.
- Connectivity from `design/reports/io-partition.json`; resistor values from the generated board netlists
  `schematic/boards/osc-jack-left.net`, `osc-jack-right.net` and `osc-core.net`. An unparsed resistor
  value on a crossing net stops the run.
- Cable capacitance from the retained flat-link model (`scripts/stack/link_electrical`): 0.5 mm stock FFC,
  the 80 mm long case, ε_eff 3.2, one ground per two signals: 7.22 pF added per net.
- Retained OPA4196 facts (`component-ti-opa4196idr`, from SBOS869, sha256 `c68223d5…5fde`):
  `fact-op-audio-input-impedance` (6.4 pF common-mode), `fact-op-audio-gbw` (2.5 MHz) and
  `fact-op-audio-capacitive-load-guidance`, which gives no safe capacitive-load threshold. The OPA4197IDR
  input capacitance (U1518) is not retained, so it is left out and flagged per net.
- TMUX7412 on-resistance bound of 15 Ω (`component-ti-tmux7412frrpr`, fact-fault-switch-t-ron-12v-single,
  a 12 V single-supply row extrapolated to ±12 V).

## Draft criteria and assumptions

| Node | Criterion |
| --- | --- |
| Op-amp output (every one here is a unity-gain follower) | total node C (cable plus the follower's own input) ≤ 100 pF, ASSUMED |
| Input-side node | RC corner ≥ 200 kHz (ASSUMED) and edge crosstalk at the node's source impedance within its victim class: ANALOGUE 10 mV, or PRECISION 1 mV where the receiving op-amp unit carries a PRECISION net |
| Indicator LED bridge net | inside the op-amp feedback loop: needs a loop-stability criterion and an aggressor class; neither is drafted |

Source impedance: a protection-switch drain (TMUX7412) is evaluated patched (an ASSUMED 1 kΩ jack source
plus 15 Ω) and unpatched (its 100 kΩ pull-down), and the worse case decides. Other input-side nodes use the
smallest resistor on the node, a lower bound. The aggressor is the retained ANALOGUE one (20 V at
20 V/µs); OPA4196 itself slews 7.5/5.5 V/µs typical, which would lower edge crosstalk about 2.7 times.
No inverting (feedback) node is among the crossings, so no feedback-pole criterion is applied.

## Input nodes fail by a wide margin; isolation midpoints need a ground on both sides

| Nodes | Source R (worst case) | Corner | Edge crosstalk: side by side / ground both sides / two grounds both sides | 20 kHz bleed | Limit |
| --- | ---: | ---: | --- | ---: | ---: |
| 14 `*_PROTECTED` switch drains, default boundary | 100 kΩ unpatched | 220 kHz | 2995 / 715 / 374 mV | 333 mV | 10 mV |
| `/O5/1V_PROTECTED` (pitch CV, PRECISION) | 100 kΩ unpatched | 220 kHz | 2995 / 715 / 374 mV | 333 mV | 1 mV |
| Same nodes, patched case | 1.015 kΩ | 21.7 MHz | 54.6 / 12.9 / 6.8 mV | 3.4 mV | as above |
| 15 `*_SENSE` inputs, keep-front boundary | ≥ 10 kΩ | 1.2–2.2 MHz | 536 / 127 / 67 mV | 33.7 mV | 10 mV (1 mV for O5) |
| 14 `ISO_MID`, default boundary | 499 Ω | 44 MHz | 26.9 / **6.4** / 3.3 mV | 1.7 mV | 10 mV |
| 14 `*_DRIVE` outputs, keep-front boundary | — | — | node total 13.6 pF ≤ 100 pF | — | — |

## Per block

| Verdict | Default boundary | Keep-front boundary |
| --- | --- | --- |
| Can move | — | U1417 (O4), U2218 (F2) |
| Can move with a ground on both sides of each signal | U1417, U2218 | — |
| Cannot move: an input node would cross | U1216 (O2), U1416 (O4), U1518 (O5), U4346 (E3), U8314 (M4A), U8417 (M4B) | same six |
| Conditional: indicator LED nets undetermined | U2119 (F1), U4347 (E3), U4348 (E3), U8318 (M4A) | same four |

Three of the six blocked ones are JR's (U4346, U8314, U8417). The capacity census
(`../mc04_c1_capacity/`) found JR short of room for three ICs; `../mc04_s2_jr_inputs/` checks whether
these three fit on JR if JR's other blocks go to K.

## Scope

First-order RC and the retained quasi-static cable model only. No loop-gain simulation, measured cable data
or measured crosstalk. Every ASSUMED value above is a criterion for the reviewer.
