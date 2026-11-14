# ST-06 SUB toggle for OSC2 and OSC4

Campaign `osc-stack-20261114`, task ST-06, launch commit `78246cf`. This is a **proposal** inside owner decision DS-02 (PUL normal, −1 octave, −2 octaves). Every schematic and PCB stays an unvalidated draft; nothing here is adopted, and no schematic, board, lock, grid source, decision register or plan page is changed.

| File | Role |
| --- | --- |
| `spec.json` | Nets, parts by inventory line, pin maps, state table, rail and area deltas, the comparison netlist and the verification plan. Generated; do not hand-edit |
| `scripts/stack/sub_toggle/sub_toggle.py` | Source of `spec.json` and the gate-level model |
| `scripts/stack/sub_toggle/test_sub_toggle.py` | Exhaustive state-table and timing-corner tests; no network, no KiCad |

Regenerate with `python3 scripts/stack/sub_toggle/sub_toggle.py`; test with `python3 scripts/checks/frozen_studies.py discover scripts/stack/sub_toggle`.

## No pitch, timing or reference node changes; no item returns NEEDS_DESIGN

The SUB logic touches `PULSE_LOGIC`, `SAW_RAW` (one comparator input), the free half of `PULSE_CMP`, the `PUL_SCALE` input and the octave selector side of `R_OCT_SER`. `TIMING_CAP`, `EXPO_SUM`, the scale nodes, `LINEAR_REF`, `HF_PIN`, `LOCAL_REF5`, `REF25`, `REF4` and all `OSC_*` reference nets gain no connection. The test `test_no_sensitive_or_reference_net_is_touched` enforces this. Two rejected alternatives under item 5 would be NEEDS_DESIGN if chosen.

## 1. Clock node: proposed SAW_LOGIC from the free comparator half; the design authority decides

The free half B of `PULSE_CMP` (LM393BIDR pins 5, 6, 7) compares `SAW_RAW` (pin 6, 2IN−) with `SUB_THRESH` (pin 5, 2IN+). A 4.7 kΩ pull-up makes `SAW_LOGIC`; a 100 kΩ/100 kΩ divider from +5 V and 1 MΩ from the output give thresholds of 2.6185 V (rising saw) and 2.3810 V (falling), 0.238 V hysteresis at nominal values. `SAW_LOGIC` rises at the core reset, and the divider counts that edge.

| What the player hears | SAW_LOGIC (proposed) | PULSE_LOGIC |
| --- | --- | --- |
| PUL normal | Unchanged in both: the pulse passes through | same |
| −1 / −2 with PW inside its range | 50 % squares, PW and PWM inert | 50 % squares; if the pulse edge counted is the PW crossing (AS3340 pulse polarity is not retained), PWM phase-modulates the sub |
| PW or PWM at 0 % or 100 % | Sub keeps running | Sub stops on a static ±5 V level; a PWM sweep through an extreme drops cycles and jumps phase |
| Hard sync | Counts every reset after the saw passes 2.62 V, independent of PW | Counts a truncated cycle only if the pulse had changed state, so the count depends on PW |
| Soft sync | Follows the core's actual resets | Same, plus the PW dependence |
| Cost per SUB oscillator | 3 SOIC-14, 9 × 0603 R, 5 × 0603 C | 2 SOIC-14, 5 R, 4 C |

The pulse clock fits the five spare sections of the existing SYNC SN74HC14DR; the saw clock needs seven Schmitt sections and so one more package. `test_alternative_pulse_clock_stalls_at_extremes` and `test_pw_extremes_do_not_stop_the_sub` reproduce the stall and its absence on the gate model. The saw option depends on the AS3340 saw swing straddling about 2.4–2.6 V, which is an evidence need.

## 2. Divider: one SN74HC74DR, no reset network, no lock-up state

| Pin | Net | Pin | Net |
| --- | --- | --- | --- |
| 1 1CLR | +5V | 8 2Q̄ | SUB_Q2_N |
| 2 1D | SUB_D1 = NAND(Q1, SUB_DIV4_ON) | 9 2Q | SUB_Q2 |
| 3 1CLK | SUB_CLK | 10 2PRE | SUB_PUL_OFF |
| 4 1PRE | +5V | 11 2CLK | SUB_CLK2 = NAND(SUB_CLK_GATE, Q1) |
| 5 1Q | SUB_Q1 | 12 2D | SUB_Q2_N |
| 6 1Q̄ | no connect | 13 2CLR | +5V |
| 7 GND | AGND | 14 VCC | +5V, 100 nF GRM188R71H104KA93D to AGND |

- **−2:** FF1 toggles at each reset; FF2 clocks on every second reset.
- **−1:** `SUB_D1` = 1 holds Q1 = 1, so `SUB_CLK2` follows each reset and FF2 divides by two.
- **PUL:** 2PRE holds Q2 = 1.

All four power-up states lie on the count cycle, so no reset network is needed. SYNC does not reset the divider; the sub's phase against a sync master is one of two or four, and it stays fixed while sync persists.

The gate for `SUB_CLK2` is taken upstream of FF1's clock in the Schmitt chain. It is therefore low before Q1 can change, and no gate-delay corner can make a spurious edge. The test runs 18 delay sets (HC14 ≤ 31 ns, HC74 ≤ 44/58 ns retained; HC00 bracketed 1–60 ns). A mutation that takes the gate from the downstream stage fails it.

No unused-input rule is retained in the bundles, so the project convention applies (spare Schmitt: input AGND, output open). The divider and NAND have no unused input.

## 3. Select logic: two contact lines, the switch_button_input topology on K, and one HC00

Each line has a 10 kΩ pull-up (RC0603FR-0710KL), 1 kΩ (RC0603FR-071KL), 100 nF and a Schmitt section, all in the oscillator core on K. The NAND units are `SUB_PUL_TERM = NAND(PULSE_CLEAN, SUB_PUL_ON)`, `SUB_OUT = NAND(SUB_PUL_TERM, SUB_Q2)`, `SUB_CLK2` and `SUB_D1`.

| State | SEL_A | SEL_B | Output |
| --- | --- | --- | --- |
| PUL (pin-3 throw) | 0 | 1 | PULSE_LOGIC |
| −1 (centre) | 1 | 1 | f/2 square |
| −2 (pin-1 throw) | 1 | 0 | f/4 square |
| Travel PUL↔−1, travel −1↔−2 | 1 | 1 | f/2 square |
| Both low (short, or first 0.4–1.1 ms of +5 V) | 0 | 0 | PULSE_LOGIC |
| Joint unmated | 1 | 1 | f/2 square |

Opening switches after 0.41–1.08 ms (τ = 1.1 ms) and closing after 0.07–0.17 ms (τ = 0.1 ms), using the HC14 threshold rows retained at VCC 4.5 V. Tests cover every row with every initial flip-flop state and delay corner, all lever paths with bounce, and truncated hard-sync cycles.

## 4. PUL level stays inside the present −5 to +5 V envelope

`PUL_SCALED = 2·V(IN+) − V(LOCAL_REF5)`. Today IN+ is `PULSE_LOGIC`: 4.7 kΩ to +5 V high, LM393 VOL low. In the proposal IN+ is `SUB_SELECTED`, the HC00 output through `R_SUB_ISO` 4.7 kΩ, so the source is 4.7 kΩ in both states.

Both inputs lie in [0, V(+5V)], so PUL_SCALED lies in [−5, +5] V nominal, the `audio_nominal_V` range. The low level moves toward −5 V by 2·(VOL_LM393 − VOL_HC00); neither VOL is retained. With ±12 V absent, the 4.7 kΩ keeps current into the unpowered op-amp input at ≤ 1.064 mA, the same path as today, against the retained 10 mA limit.

## 5. Octave input held at zero by tying R_OCT_SER to AGND

`OCT_SELECTOR` (SRBV160803) goes. `R_OCT_SER` pin 1 moves to AGND. `R_OCT_SER`, `R_OCT_PD`, `C_OCT_FILTER`, `OCT_RECEIVER` and `PITCH_OCT` stay, so the pitch sum keeps its network and receives 0 V. `OSC_OCT0..5` only lose the O2/O4 selector branches that DS-02 removes; no reference value, buffer or ladder element changes.

The rejected alternatives would be NEEDS_DESIGN if chosen:

- Tying to `OSC_OCT2` adds fixed loads to a reference node.
- Deleting the chain removes a pitch-sum input.

## 6. Joint, toggle and panel binding: signal-AGND-signal, pin 3 is PUL

| Pair pin (P and K) | Net | Toggle pin |
| --- | --- | --- |
| 1 | SUB_SEL_A (PUL throw) | 3 |
| 2 | AGND | 2 (common) |
| 3 | SUB_SEL_B (−2 throw) | 1 |

Toggle pads 3/2/1 sit at −2.54/0/+2.54 mm, so the pair reaches them without a crossing. No audio crosses the joint.

On P, only the toggle and the pair half are added, and nothing is required near the 0.7 mm window. All conditioning sits anywhere in the K core.

The toggle's evidence is open: its pin labels are unverified, and the contact map and suffix equivalence are UNSOURCED. These are the same assumptions SYNC_SELECT already makes. Grid order follows SYNC: `["PUL", "-1", "-2"]`. SW201 stays at (31.5, 185) and SW401 at (65.5, 185).

Proposed grid revision for ST-10 (not applied):

- uid `C:Ox.OCT` → `C:Ox.SUB`, key and label SUB, kind switch.
- Component `dailywell-2ms3`, diameter 6.
- Domain O → P, hole 7.0 → 5.2 mm, rotation 0.
- Drop the selector assembly fields.

The rename is proposed because `io_partition.region()` classifies any `.OCT` uid as region "selector". The alternative keeps the uid and adds a special case there.

## 7. Each SUB oscillator adds 1.63 mA typical and 3.59 mA planning on +5 V, nothing on ±12 V

| Rail | Typical | Planning |
| --- | --- | --- |
| +5 V per SUB oscillator | 1.625 mA | 3.594 mA |
| +5 V, ledger total for O2 + O4 | 3.25 mA | 7.188 mA |
| +12 V, −12 V | 0 | 0 |

The pulse-clock alternative adds 0.9 / 2.0 mA per SUB oscillator. None of these is a guaranteed maximum.

On K, each SUB oscillator adds 17 parts with 299.0 mm² of courtyard: 3 × SOIC-14 at 71.26 mm², 9 × R0603 at 5.97 mm² and 5 × C0603 at 6.30 mm². The pulse alternative adds 11 parts with 197.6 mm². This is count and area only, with no placement.

## 8. ST-11 runs ERC, netlist parity, model contracts and a gate-level replay

`spec.json` lists the four ideal ngspice decks (saw comparator, logic, level, debounce) with pass criteria. ST-11 must also pass:

- ERC through `scripts/kicad/run.sh`, with no new error class.
- Netlist parity for O2/O4, with O1/O3/O5 unchanged.
- `test_oscillator`, `check_oscillator.sh` and `pnpm circuit:check`.
- The rail-ledger refresh.

ST-11 must also fix four implementation traps listed in `spec.json`:

- Split the family into a SUB variant that composes with O4's TSSOP split.
- Add SN74HC74DR and SN74HC00DR to the +5 V branch of `finish()`, or `refine()` raises "orphaned bypass capacitors".
- Avoid `b.cell("switch_button_input")`, which moves the parts to P.
- Use the exact contact-resistor MPNs.

## Evidence needs block exact levels, not the topology

The needs are listed by part in `spec.json`:

- **AS3340D:** saw swing, pulse polarity and PW span, sync behaviour.
- **LM393BIDR:** VOL, common-mode range and response time.
- **SN74HC00DR, SN74HC74DR and SN74HC14DR:** VOH/VOL rows and the HC00 delay and transition limits.
- **2MS3T1B1M2QES:** contact map and bounce.
- **OPA4196IDR:** input bias current.
- **The 1×3 connector:** not selected.
