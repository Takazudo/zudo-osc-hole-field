# D4233 SEL network review (OSC1, R6)

Record of 2026-11-03 on K3409 (`dda33a25…`); the 2026-11-07 recheck on K3363 and the
placement comparison are appended at the end and leave this record unchanged.

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

## 2026-11-07 recheck on K3363: unchanged, 32 of 36 SEL nets still have a member beyond 24 mm and none has copper

The accepted core is now K3363 (`2c1d67b7e306a3ebf8ebed276a37d899cca43f683d6686afed6a1688e0ec6751`,
the OSC3 power/return pilot). That pilot added rail copper only. Every SEL hold
member and logic driver sits where it sat on K3409, row for row.

| Item on K3363 | Value |
| --- | --- |
| SEL hold nets (12 TMUX6112, SEL pins 1/16/9/8 not tied to AGND) | 36 |
| Nets with a member beyond 24 mm | 32 (32 pull-ups and D4233) |
| Largest member distance | 96.67 mm (RB4233, `/E2/SLOPE_SELECT_SEL3`) |
| U4206 SEL4 | D4232 17.10 mm, D4233 27.61 mm, RB4234 95.18 mm, driver U4229.3 39.69 mm |
| Tracks or vias on any SEL net | none |
| Tracks or vias on any pull-down driver net | none |

`sel-hold-geometry-k3363-20261107.json` holds every row. It was regenerated
from the board text by the existing host-only script, which needs no pcbnew:
`python3 scripts/checks/sel_hold_geometry.py -o circuit/reviews/osc1-d4233-sel-network/sel-hold-geometry-k3363-20261107.json`.
The K3409 file `sel-hold-geometry.json` stays as the record bound to
`design/partition/protection-locality-exceptions.json`.

## 2026-11-07 placement comparison: re-placing only the far parts leaves 10 nets beyond 24 mm, moving all 108 leaves 8 and one part without a pose

This is a proposal for the owner's decision, not a placement change. No board,
spec or placement file was edited. Nothing was routed, refilled or DRC-checked.
D4233 stays `PROVISIONAL`.

`scripts/checks/sel_hold_placement_compare.py` searches free poses for the SEL
hold parts near each SEL pad and writes
`sel-hold-placement-compare-k3363-20261107.json`.

- **Pose search.** It uses a 0.5 mm grid within 24 mm of the switch, at 0°, 90°, 180° and 270°, on the part's own side.
- **Legality.** A pose must fit inside the Edge.Cuts polygon, including the notch, less 0.5 mm.
- **Spacing.** It must keep 0.6 mm from every staying courtyard, matching the generator's K gap. It must also clear through-hole pads and footprint keepouts.
- **Cost.** The cost is the distance to the SEL pad plus 4 mm per foreign copper object under a new pad.
- **Ordering.** Greedy placement is order-dependent. Six orders were tried, and the best is kept and listed in `order_trials`.

| | Status quo | A: move only parts beyond 24 mm | B: move all 108 SEL hold parts |
| --- | ---: | ---: | ---: |
| Parts moved | 0 | 22 | 102 |
| Parts with no legal pose within 40 mm | 0 | 0 | 1 (D4436) |
| SEL nets with a member beyond 24 mm | 32 | 10 | 8 |
| U4206 SEL4 (D4233 network) resolved | no | no | yes: D4233 16.5 mm, D4232 23.6 mm, RB4234 14.1 mm |
| Existing tracks/vias invalidated at old poses | 0 | 38 (+5V) | 97 (+5V and +12V) |
| Foreign copper under new pads | 0 | 5 objects, 5 signal nets | 2 objects (+12V, one signal net) |
| Moved parts over the AGND surface pours | 0 | 22 | 102 |
| Locked R21 panel hardware on K | none in `placements.lock.json` | no conflict | no conflict |
| Nearest locked footprint (JST / test point) courtyard gap | | 0.60 mm | 0.60 mm |

What the comparison shows:

- **A is legal but incomplete.** Re-placing the far pull-ups next to their switches fixes 22 of 32 networks. The remaining 10 are all on E2 (U4206, U4208) and E4 (U4406, U4408). D4233 has no legal pose within 24 mm while its neighbours stay, which agrees with the phase-36 search.
- **B fixes the D4233 network but is not a complete placement.** It uses space that A cannot. D4436 then has no legal pose at all, and 8 networks on E2, E4 and E5 stay beyond 24 mm. Its copper cost is 2.5 times larger, because the +12V clamp connections are re-made too.
- **E2 and E4 need a regional decision.** Neither variant clears them. A complete fix there also needs other parts moved, beyond the SEL hold networks. That is a wider floorplan decision for the owner, not something to adopt implicitly.
- **Every move needs native work later.** It needs AGND pour refill, +5V or +12V reconnection, the listed foreign-copper rip-ups and a native DRC. Those runs need admission and are NOT RUN here.

Limits: courtyards are axis-aligned bounds and side changes are not searched.
Silkscreen, assembly, thermal and electrical effects are not checked. Centre
distance is not trace length. The finite greedy search does not prove that no
better placement exists.

Reproduce (host only, about 5 minutes):
`python3 scripts/checks/sel_hold_placement_compare.py -o circuit/reviews/osc1-d4233-sel-network/sel-hold-placement-compare-k3363-20261107.json`.

## 2026-11-08 K2518: 5 SEL nets now have copper, placement outcomes unchanged

The manager adopted K2518 (`7251dd933af810b7c659c9b90c6f6d9ba32d55ea432b0414c26c8b26b6b4be42`)
in place of K3363. Its signal chain added copper only and moved no part. The
2026-11-07 statement that no SEL net has copper holds for K3363 only.

| Item on K2518 | Value |
| --- | --- |
| SEL nets with a member beyond 24 mm | 32 of 36 (unchanged) |
| SEL nets with copper | 5: `/E1/STORAGE_CLAMP_SEL2`, `/E6/SLOPE_SELECT_SEL2`, `/E6/SLOPE_SELECT_SEL3`, `/E6/STORAGE_CLAMP_SEL1`, `/E6/STORAGE_CLAMP_SEL2` |
| Pull-down driver nets with copper | 13 |
| U4206 SEL4 and `/E2/FALL_CURVE` | still no copper |

The placement comparison was rerun on K2518. Its placement results are
identical: variant A moves 22 parts and leaves 10 nets beyond 24 mm, and
variant B moves 102 parts, leaves 8 beyond and finds no pose for D4436. The
copper cost is higher, because a move now also invalidates the new signal
copper.

| | A on K3363 | A on K2518 | B on K3363 | B on K2518 |
| --- | ---: | ---: | ---: | ---: |
| Tracks and vias invalidated at old poses | 38 | 42 | 97 | 147 |
| Foreign copper objects under new pads | 5 | 6 | 2 | 9 |

Files: `sel-hold-geometry-k2518-20261108.json` and `sel-hold-placement-compare-k2518-20261108.json`.
The K3363 files are kept as the 2026-11-07 record.
