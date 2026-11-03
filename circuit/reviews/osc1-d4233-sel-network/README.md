# D4233 SEL network review (OSC1, R6)

Status: source review of an unvalidated draft. Nothing here is routed, simulated
or measured. It replaces no decision; the D4233 exception stays `PROVISIONAL`.

## Result: a permanent D4233-only exception is not supported; the SEL hold placement needs a wider decision

The 24 mm protection-locality rule measures only the added BAT54S diodes. On the
adopted core PCB (`dda33a25479c9993f71e33d49129cf16414828b3dd2083b6d4f91a65421c728c`)
the SEL hold network of U4206 SEL4 is dominated by parts the rule does not cover:

| Part on `/E2/SLOPE_SELECT_SEL4` or its driver | Role | Centre distance to U4206 |
| --- | --- | ---: |
| D4232.1/.3 | BAT54S clamp to +12V | 17.10 mm |
| D4233.1/.3 | BAT54S pull-down into `/E2/FALL_CURVE` (the excepted part) | 27.61 mm |
| RB4234.2 | 100 kΩ pull-up to +5V | 95.18 mm |
| U4229.3 | SN74HC00DR output driving `/E2/FALL_CURVE` | 39.69 mm |

Across the core, 32 of 36 TMUX6112 SEL hold nets have at least one member
beyond 24 mm, the largest at 96.67 mm (RB4233, `/E2/SLOPE_SELECT_SEL3`). None of
the 36 SEL nets has copper yet. `sel-hold-geometry.json` holds every row and the
board hash; regenerate it with
`python3 scripts/checks/sel_hold_geometry.py -o circuit/reviews/osc1-d4233-sel-network/sel-hold-geometry.json`.

Centre distance is not trace length. With no copper on either net, the actual
SEL and FALL_CURVE trace lengths are not available, and the earlier "extra
3.6 mm adds a little capacitance" statement has no basis.

## Circuit facts and their evidence

| Item | Value | Evidence | Verdict |
| --- | --- | --- | --- |
| Topology | 100 kΩ RC0603FR-07100KL from +5V; BAT54S diode 2 clamps SEL to +12V; a second BAT54S pulls SEL into the logic output; no series resistor | `design/spec/modules/envelope.py` `flush_sel_holds`; K pad nets | Project state |
| Logic driving D4233 | `/E2/FALL_CURVE = READY AND FALL AND CURVED` (`design/spec/modules/envelope_logic.py`), so SEL4 changes at every fall-stage transition in curved mode, not only on a user switch | Project source | Project state |
| TMUX6112 thresholds | VIH min 2.0 V, VIL max 0.8 V, at VDD = 15 V / VSS = −15 V | `component-ti-tmux6112pwr` `fact-env-switch-t-logic-thresholds` | PASS at the stated supply; the project runs ±12 V, so the condition differs |
| SEL low level | ≤ 0.57 V at 25 °C; ≤ 0.65 V for 25..70 °C with a project 50 µA leakage bound | `fact-env-switch-t-sel-hold` | NEEDS BENCH |
| BAT54S VF over temperature | Maximum only at 25 °C; no curve below 25 °C | `component-nexperia-bat54s-215` `fact-clamp-diode-forward-voltage-temperature` | Cold low-level margin UNSOURCED |
| BAT54S reverse current | 2 µA max at 25 V, 25 °C; typical 85 °C curve about 15–60 µA; 125 °C about 200–500 µA | `fact-clamp-diode-reverse-current`, `fact-clamp-diode-reverse-current-temperature` | Typical only above 25 °C |
| Rising-edge time | Set by 100 kΩ and the SEL net capacitance; no retained capacitance for the diodes, switch input or trace | none | UNSOURCED |
| Startup | `READY` is low during reset, so `FALL_CURVE` is low and the switch is off; SEL ≤ VDD + 0.24 V at 25 °C with +12V absent | `fact-env-switch-t-sel-hold`, project logic | NEEDS BENCH for the full power sequence |

The high state is a 100 kΩ node. With RB4234 95 mm from the switch, any routed
SEL net will be long and high-impedance in the high state. Its coupling and
glitch susceptibility are not evaluated here.

## What the finite search does and does not show

The phase-36 record sampled 14,344 poses (1 mm steps, two faces, 0°/90°) and a
single-capacitor nudge. Finding no free pose in that sample is not a proof that no
placement exists; moves of two or more pinned parts were not tried.

## Decision this review prepares

1. Keep the D4233 exception `PROVISIONAL` as the comparison input for the
   current 27.61 mm placement (the checker now fails if that placement changes).
2. The evidence points to re-placing the SEL hold networks (pull-up, clamp and
   pull-down together, near each TMUX6112 SEL pin) rather than granting a
   permanent single-diode exception. That is a multi-part placement change on the
   core and needs the owner's decision before any re-placement or routing.
3. Before either outcome is called complete: route or estimate the SEL and
   FALL_CURVE traces, obtain the missing capacitance and low-temperature VF
   evidence, and bench the SEL levels, edge timing and power sequencing.
