# Draft limits: six input-buffer blocks cannot cross the cable; three output blocks can with a ground between signals

Stage 1a of the remedy the owner accepted on 2026-11-21 (option D, developed in stages). **These are DRAFT
criteria for independent review, not accepted budgets.**

```sh
python3 -B scripts/stack/studies/mc04_s1_budgets/budgets.py --output scripts/stack/studies/mc04_s1_budgets/result.json
```

`result.json` sha256 `e9b012fe7538a8b4d6a263a395ea32fa13b3a57c1ab65eedc2427c3a20646f01`.

## Inputs

- The 55 new crossing nets of both block boundaries (steps 5a and 5b, pinned by hash).
- Node type from the io-partition pin map (OPA4196/OPA4197 output, inverting or non-inverting input, or
  passive-only), and resistor values from the generated board netlists `schematic/boards/osc-jack-left.net`,
  `osc-jack-right.net` and `osc-core.net`.
- Added cable capacitance from the retained flat-link model (`scripts/stack/link_electrical`): 0.5 mm stock
  FFC, the 80 mm long case, ε_eff 3.2, one ground per two signals. That gives 7.22 pF, plus 6.4 pF where an
  op-amp input is on the node.
- OPA4196 datasheet TI SBOS869 (sha256 `c68223d5…5fde`, the retained `src-op-audio-datasheet-20261031`
  bytes): GBW 2.5 MHz, common-mode input 1 MΩ ‖ 6.4 pF, 1 nF unity-gain capacitive drive, and the note that
  unity-gain ringing can occur below 100 pF with light loads.

## Draft criteria

| Node | Criterion | Basis |
| --- | --- | --- |
| Op-amp output | added C ≤ 100 pF | datasheet ringing note |
| Inverting (feedback) input | node-R × added-C pole ≥ 2.5 MHz | datasheet GBW |
| Non-inverting input or passive node | RC corner ≥ 200 kHz, and ANALOGUE edge crosstalk at the node's own source resistance ≤ 10 mV | retained 20 kHz sine × 10; retained ANALOGUE victim limit |

## Every protected 10 kΩ input node fails the crosstalk limit, even with two grounds between

| Node | Source R | Corner | Edge crosstalk, side by side / rule A / B / C | 20 kHz bleed |
| --- | ---: | ---: | --- | ---: |
| `*_PROTECTED` and the clamped `*_SENSE` inputs (15 per boundary) | 10 kΩ | 1.2–2.2 MHz | 536 / 106 / 127 / 67 mV | 33.7 mV |
| `ISO_MID` (14, default boundary) | 499 Ω | 44 MHz | 26.9 / **5.3** / 6.4 / 3.3 mV | 1.7 mV |
| Op-amp `*_DRIVE` outputs (14, keep-front boundary) | — | — | added C 7.2 pF ≤ 100 pF | — |

Bandwidth passes everywhere; crosstalk decides. The retained model's 100 Ω ANALOGUE assumption does not
hold behind a 10 kΩ protection resistor.

## Per block: three can move, six cannot, three need an indicator criterion

| Verdict | Blocks |
| --- | --- |
| Can move, with a ground between signals (rule A across ground), or plain on the keep-front boundary | U1417 (O4), U2218 (F2), U4347 (E3, plus 2 LED nets) |
| Cannot move under these criteria: a 10 kΩ input node would cross | U1216 (O2), U1416 (O4), U1518 (O5), U4346 (E3), U8314 (M4A), U8417 (M4B) |
| Undetermined: LED bridge nets to the panel LED, with no victim criterion drafted | U2119 (F1), U4348 (E3), U8318 (M4A) |

Three of the six blocked ones are JR's (U4346, U8314, U8417), and JR is the board short of room. A next
study is to move other JR parts to K to make room for these input buffers on JR itself.

## Scope

First-order RC and the retained quasi-static cable model only. No loop-gain simulation, measured cable data
or measured crosstalk. The 10 mV peak limit, the aggressor (20 V at 20 V/µs, adjacent) and the 200 kHz
corner are ASSUMED criteria for the reviewer.
