# MC04-S10 Revision 2 prospective electrical decision packet (2026-11-27), packet revision 3

Issue #367 (MC-04 paper gate), lane B. Author: design session, model `claude-fable-5-2` (Fable 5.2). Repository
`zudo-osc-hole-field` at `80569b5375087df519b79ead67d1bf56c16301e6`, read-only. This is an investigation and a
recommendation. It adopts nothing, relaxes nothing and changes no file in the repository. Every board and schematic
stays an unvalidated draft. This revision answers the independent review `review-20261127.md` (RETURN, then ACCEPT WITH CORRECTIONS);
the change log is at the end.

## Verdict: no slot-only S10 Revision 2 exists within 24 mm, so the next step is an owner choice, not a run

- Holding R5257 and U5210 at exact paper coordinates is a zero-growth placement and replaces the 7.93 mm number.
  That is a design-authority ruling (proposed below), with the owner notified.
- It unlocks nothing. All 81 accepted P-K-P-L13.01.01.01 candidates in the complete S9-A2 enumeration put the K
  connector over R8356 (`/M4A/C24ce01_W_SENSE`). U5210 cannot return to paper unless that link moves. Under the
  DS-150 rule no slot-only scene on the 2.0, 0.5 and 0.25 mm grids within 24 mm places U5210.
- No study and no generator run is recommended. The negative result is recorded from retained data without a run.
- The feedback loop has no stability evidence at paper or anywhere else.

## 7.93 mm is the paper distance rounded to two decimals, not an electrical limit

| Step | Source | Value |
| --- | --- | --- |
| Paper poses | `adopted-placement-pins.json`, `floorplan-candidate.json` at `6093081c`, `8243acdf` and HEAD; interim K board | R5257 (174.66, 199.89) B 90°; U5210 (180.97, 204.70) B 0° |
| Unrounded distance | recomputed | 7.934242244852375 mm |
| Integer check (1/100 mm) | recomputed | 631² + 481² = 629522 > 793² = 628849 |
| First appearance of 7.93 | `slot_moves_a2.py` `describe()`, lines 207–208: `r2(dist(...))`, with `r2 = round(v, 2)` in `replacement.py` lines 66–67 | `distance_to_ic_before_mm: 7.93`, `distance_to_ic_paper_mm: 7.93` in `result-a2.json` `joint_scene.parts_re_placed[20]` |
| Carried into the report | `mc04-s9-a2-report-20261122.md` line 78 | "7.93 → 12.64" |
| Became a condition | DS-147, then `RULED = {'R5257': ('U5210', 7.93)}` in `overlay.py` line 33 | "at 7.93 mm or less" |

No file derives 7.93 mm from a capacitance, a trace length or a stability margin. I do not round the cap and I do
not propose a tolerance: against the literal number the paper pose is 0.004242 mm over.

## Proposed design-authority ruling: coordinate equality replaces the number

Proposed decision row (design authority under DS-03, which also issued DS-147; owner notified, no owner message
needed):

> R5257 stays at (174.66, 199.89) B 90° and U5210 returns to (180.97, 204.70) B 0°, their exact paper poses. R5259
> stays at (177.89, 194.16) B. The DS-147 condition "7.93 mm or less" is restated as coordinate equality; 7.93 was
> the paper distance 7.934242 mm rounded for display. No distance number is a limit. This asserts no electrical
> acceptance of the F2 loop.

Why this is within delegated scope, not an owner decision (review defect 6, accepted):

- DS-150 already forbids moving R5257 (it is on `/W1/F2_SUM`) and requires U5210 back at paper, so the distance is
  fixed at 7.934242 mm by that rule and the number is subsumed.
- DS-150's "Reverse by" asks for an evidence-backed prospective change, a separately admitted candidate and an
  independent review. It names no owner message.
- The 2026-11-23 review, finding 3, asked for exactly this wording.

| Quantity | Interim board (paper) | Pre-S10 `6e5716e7` | S10 candidate `32580f77` |
| --- | --- | --- | --- |
| R5257 pose | (174.66, 199.89) B | same, no gate row | same, no gate row |
| U5210 pose | (180.97, 204.70) B | none: gate row "no position" | (180.97, 204.70) B, row removed |
| Centre distance | 7.934242244852375 mm | undefined | 7.934242244852375 mm |
| R5257.2 → U5210.6 (`/W1/F2_SUM`) pad centres | 11.949 mm | undefined | 11.949 mm |
| R5257.1 → U5210.7 (`/W1/F2_OUT`) pad centres | 11.795 mm | undefined | 11.795 mm |

"No growth versus the pre-S10 state" cannot be shown literally, because U5210 had no position before S10. Paper is
the only comparable state, and against paper the pair is identical by construction.

## Centre-to-centre distance is not proof of routed electrical behaviour

Network, from `design/spec/modules/wavefolder.py` lines 97–104 and `io-partition.json`:

| Net | Pins | Role |
| --- | --- | --- |
| `/W1/F2_SUM` | U5210.6 (IN− B), R5256.2, R5257.2 | summing node, three pins, no capacitor |
| `/W1/F2_OUT` | U5210.7 (OUT B), R5257.1, R5258.1, R5259.1 | cell output, feeds F3 |
| `/W1/F2_CLIP` | U5210.5 (IN+ B), R5255.2, D5208.2, D5209.1 | diode-clamped non-inverting input |
| `/W1/F1_OUT` | U5210.1, R5254.1, R5255.1, R5256.1 | previous cell output |

| Ref | Identity | Value and role | Paper pose |
| --- | --- | --- | --- |
| U5210 | OPA4196IDR, TI, SOIC-14, C2057385, `line-op-audio`, owner `component-ti-opa4196idr` | W1 fold cells F1–F4 | (180.97, 204.70) B |
| R5257 | RT0603BRD07100KL, Yageo, `line-r-precision`, owner `component-passives-family` | 100 kΩ `F2_FEEDBACK` | (174.66, 199.89) B |
| R5256 | RT0603BRD07100KL | 100 kΩ `F2_INPUT` | (175.39, 196.16) **F** |
| R5259 | RT0603BRD07100KL | 100 kΩ `F3_INPUT` | (177.89, 194.16) B |
| R5255, R5258 | MPN field empty in `io-partition.json` | 10 kΩ `F2_CLIP_FEED`, `F3_CLIP_FEED` | (173.14, 192.41) B; (168.41, 195.39) B |
| D5208, D5209 | BAS16GW-QX | F2 clamp pair | (165.50, 190.35) B; (181.85, 191.25) B |

### The paper state has a routed F2 loop on the interim K board; the link era has none

Copper connectivity by geometry (pads as rectangles, tracks buffered by half width, vias across layers;
`scripts/rev2_verify.py`):

| Net | Copper | Connectivity | Track end at U5210 |
| --- | --- | --- | --- |
| `/W1/F2_SUM` | 26.160 mm, 3 vias (F.Cu 12.801, B.Cu 9.453, In3.Cu 3.905 mm) | one component, all three pads | (184.375, 207.05) B.Cu, 0.2 mm, inside pad 6 (1.95 × 0.6 mm at (183.445, 207.24)) |
| `/W1/F2_OUT` | 35.807 mm, 5 vias | one component, all four pads | (182.55, 208.25) B.Cu, 0.15 mm, inside pad 7 at (183.445, 208.51) |

Revision 1 of this packet said the copper did not reach U5210. That was wrong: my test window was ±0.45 mm in x on a
1.95 mm pad. What still stands:

- The interim board is an unvalidated, incompletely routed draft. Its F2 routing is a paper-state reference
  (summing node 26.16 mm, three vias, 5.2 pF at 0.20 pF/mm with vias excluded), not an accepted layout.
- The link era has no routing, so there is nothing to compare a link-era F2 loop against yet.
- No stability evidence exists. `design/reports/spice/wavefolder.json` used ideal amplifiers ("no
  bandwidth/current/slew/phase model"). `check_wavefolder.sh` and the module docstring disclaim amplifier stability.
  The OPA4196 owner bundle has one interaction, `NEEDS BENCH`.

### A first-order estimate suggests the node may be sensitive at paper (estimate only)

Inputs are the retained typical-only facts `fact-op-audio-gbw` (2.5 MHz, no minimum) and
`fact-op-audio-input-impedance` (1.6 pF differential, 6.4 pF common mode). Script `scripts/f2_loop_estimate.py`.

| Stray on `F2_SUM` | Node C | Zero | Crossover | Phase margin (model) |
| --- | --- | --- | --- | --- |
| 0 pF | 8.0 pF | 398 kHz | 652 kHz | 31° |
| 5.23 pF (interim routed 26.16 mm × 0.20 pF/mm, vias excluded) | 13.23 pF | 241 kHz | 523 kHz | 25° |
| 5.96 pF (paper pads, 1.5 × HPWL × 0.20 pF/mm) | 13.96 pF | 228 kHz | 510 kHz | 24° |
| 10 pF | 18.0 pF | 177 kHz | 454 kHz | 21° |
| 20 pF | 28.0 pF | 114 kHz | 369 kHz | 17° |

Assumptions, all unverified:

- single-pole amplifier; second pole and open-loop output impedance ignored, so the figure is **not a lower bound**;
- small-signal, clamp diodes not conducting;
- IN+ (`F2_CLIP`, 10 kΩ feed and clamp) treated as AC ground, so the 1.6 pF differential capacitance is lumped to
  ground;
- noise gain 2, 50 kΩ at the node, typical GBW and input capacitance, no tolerance or temperature;
- 0.20 pF/mm and route factor 1.5 are the project's estimate basis.

The numbers must not be cited as a margin. They are a reason to run the vendor-model simulation, nothing more.

### Evidence a real acceptance would need, and whether it exists

| Evidence | Exists? |
| --- | --- |
| Vendor-model loop gain of the fold cell (TI OPAx196 model, zip SHA-256 `9c264813…ccdf5`, already retained) with 0–20 pF on `F2_SUM`, clamp conducting and not conducting, by the MC04-S4 loop-break method | NOT RUN |
| A stated capacitance budget for `*_SUM` nodes of this cell | does not exist |
| Routed summing-node length, via count and loop area for U5210 unit B in the link era | does not exist; paper reference is 26.16 mm, 3 vias on the interim board |
| Extracted parasitic C against that budget | project estimate only |
| Bench stability | NOT RUN |

## The retained S9-A2 enumeration already decides the slot-only question: zero protected-clean scenes

`result-a2.json` has `caps_reached: []`, so its enumeration on the 2.0, 0.5 and 0.25 mm grids within 24 mm is
complete. Nothing was searched here; rows marked "geometric" are rectangle tests of retained candidate rectangles
against ungrown `floorplan-candidate.json` courtyards (gate growth can only add overlaps).

| Link | Complete accepted set | Protected parts at paper under each candidate | Basis |
| --- | --- | --- | --- |
| P-K-P-L13.01.01.01 (U5210) | 81 (3, 20, 81 per grid), all +y, x 200.92–202.92, y 197.42–201.67 | R8356 courtyard [204.75, 206.5, 206.57, 209.78] under the K connector in **81 of 81**, also under the K tail in 8 | record and geometric |
| same, knock-on | same 81 | R8456 (`/M4B/C24ce01_W_SENSE`) moves in 79 (7 directly, 72 with the U4222 block); R4238 (`/E2/REF9_FB`) in 72; C8408, R7215, R7219, R8471 in 4 | record |
| P-K-P-L13.01.01.02, 0.25 mm grid | 17: three at x 167.25–167.75 displace U5207, C5205, C5206; 14 at x = 176.0 | slot over R5254 (`/W1/F1_SUM`) for y 192.25–195.0; R5256 for y 194.75–197.0; R5257 for y 198.25, 198.5; R5259 (`/W1/F3_SUM`) for y 192.75–195.0. Every one of the 14 is over at least one | geometric |
| L13.01.01.02 + L13.01.02.01 pairs | 16 (first link y = 196.25, 196.5, 198.25, 198.5) | all 16 re-place R5249, R8221, R8331; R5259 is under the K tail at all four y values | record; tail geometric |

- The L13.01.01.01 rejection reasons name only L03.01, L15.02.01.01, panel hardware, fixing keep-outs, U8409 and
  U5210. None names L13.01.01.02 or L13.01.02.01, so moving those two links cannot add an L13.01.01.01 candidate.
- The ten unpaired first-link candidates are not an open question: each has its slot over R5254 or R5256.
- One qualification of my own: 370 L13.01.01.02 positions were rejected for "slot on K field of P-K-P-L13.01.02.01",
  so the L13.01.01.02 set depends on where L13.01.02.01 sits. For U5209 alone the retained set is all dirty but not
  proven exhaustive. This does not change the result, because U5210 is decided by L13.01.01.01 alone.

## All six protected movements, five locality discrepancies and both U4526 regressions reproduce

Recomputed by `scripts/recompute_s10.py` and confirmed by the reviewer's separate scripts: 56 effective movements,
16 face changes, none rotation-only.

### Six protected passives (newly displaced)

| Ref | Protected net | Paper → candidate | Moved | Cause | Node pad HPWL, paper → candidate | Part pad → IC pin |
| --- | --- | --- | --- | --- | --- | --- |
| R5249 | `/W1/FOLDER_SUM` | (158.64, 193.66) B → (157.765, 195.1755) **F** | 1.75 mm | gate row, under a slot | 85.875 → 85.875 mm | U5209.9: 15.613 → 14.019 mm |
| R5256 | `/W1/F2_SUM` | (175.39, 196.16) F → (181.6687, 199.785) F | 7.25 mm | gate row, under the L13.01.01.02 slot [173.25–178.75, 195.5–197.0] | 19.865 → 16.885 mm | U5210.6: 13.271 → 7.525 mm |
| R8221 | `/M5B/Ca92eeb_W_SENSE` | (160.39, 181.66) B → (164.9862, 177.0638) B | 6.5 mm | gate row, under a field | 80.395 → 80.395 mm | U8208.12: 53.083 → 54.176 mm |
| R8331 | `/M4A/C38051c_W_SENSE` | (164.39, 184.16) B → (169.265, 175.7163) B | 9.75 mm | gate row, under a field | 84.495 → 71.176 mm | U8310.5: 64.315 → 56.800 mm |
| R8356 | `/M4A/C24ce01_W_SENSE` | (205.66, 208.14) B → (200.887, 212.913) B | 6.75 mm | gate row, under a field | 84.395 → 93.941 mm | U8311.10: 60.171 → 66.872 mm |
| R4238 | `/E2/REF9_FB` | (208.14, 217.91) B → (210.89, 220.16) B | 3.55 mm | overlay only, displaced by the U4222 block | 34.013 → 33.552 mm | U4240.2: 33.330 → 31.141 mm |

### Four more sensitive parts move in shifted rows, which the "newly displaced" wording does not reach

| Ref | Net | Pre-S10 → candidate | Node pad HPWL: paper / pre-S10 / candidate |
| --- | --- | --- | --- |
| R8431 | `/M4B/C38051c_W_SENSE` | (199.41, 210.39) F → (186.66, 210.39) F, 12.75 mm | 48.765 / 45.515 / 55.015 mm |
| R5148 | `/W2/FOLDER_SUM` | (154.91, 195.64) F → (154.1887, 192.015) **B**, 3.70 mm | 74.980 / 69.480 / 73.105 mm |
| R5253 | `/W1/F1_SUM` | (163.209, 193.14) F → (162.9453, 190.0263) **B**, 3.12 mm | 30.555 / undefined / 33.383 mm |
| C8405 | `/M4B/Cfaa69a_FB` | (205.96, 189.64) B → (201.2837, 192.0988) B, 5.28 mm | undefined: U8409 has no position |

Eight sensitive parts return to paper (R5226, R5228, R5247, R5250, R5251, R5260, R5263 and input buffer U5207);
R5251, R5260, R5263 and U5207 change face in doing so.

### Five locality discrepancies are inherited record-scope mismatches

| Ref | Recorded | Recomputed, pre-S10 and candidate | Cause |
| --- | --- | --- | --- |
| U5113 (JL) | 65.97 mm to (93.93, 113.55) | **84.77 mm** (84.7728) to gate row (73.887, 118.9205) | record holds the interim-board pose; the link-era gate moves it again |
| U5112 (JL) | `C8df94f_SENSE` 106.2 mm, 21.2 pF, R5108 53.0 mm; `C74d1de_SENSE` 85.0 mm, 17.0 pF, R5112 44.7 mm | 118.3 mm, 23.7 pF, 59.8 mm; 84.3 mm, 16.9 pF, 44.3 mm | R5108 and R5112 have gate rows |
| U4646 (JR) | `C33e306_SENSE` D4601 47.1 mm; `C2882f4_SENSE` 101.9 mm, 20.4 pF, R4612 35.3 mm | 48.7 mm; 103.3 mm, 20.7 pF, 33.0 mm | D4601 and R4612 have gate rows |
| U4417 (K) | six nets, added run 78.75–85.5 mm | L016 114.51, L018 100.88, L021 72.56, RISE 112.26, START 100.88, TOP 96.08 mm (36.89–40.42 pF) | record model put gate-displaced parts at paper |
| U4526 (K) | CURVED 36.81, L069 36.81, L070 56.25, RISE 26.08, TOP_RAW 6.46 mm | 75.81, 75.81, 95.25, 27.03, 19.21 mm | same |

IC distances for U5112 (52.56), U4646 (46.89), U4417 (48.84) and U4526 (26.71 mm) match their records.

### U4526 regresses on two nets specifically in S10

| Net | Accepted record | Pre-S10 effective | Candidate, overlay | Candidate, overlay withheld |
| --- | --- | --- | --- | --- |
| `/E5/HOLD_N` added run | 39.81 mm, 25.01 pF | 39.81 mm, 25.01 pF | **65.25 mm, 30.10 pF** | 50.31 mm, 27.11 pF |
| `/E5/READY` added run | 4.12 mm, 32.73 pF | 22.39 mm, 36.38 pF | **30.64 mm, 38.03 pF** | 32.89 mm, 38.48 pF |

U4537 is the only changed footprint on both nets.

### Withheld overlay poses

| IC | Paper | Pre-S10 | Candidate gate pose | Withheld overlay pose | Decoupler to IC: pre-S10 / gate / overlay |
| --- | --- | --- | --- | --- | --- |
| U4222 (SN74HC00DR) | (195.70, 205.45) B | paper | (213.2009, 222.9509) B, 24.75 mm | (204.20, 220.45) B 0°, 17.24 mm, displaces R4238 | C4239 7.66 / 24.87 / 6.85 mm |
| U4227 (SN74HC00DR) | (198.68, 214.58) B | gate (213.1859, 222.955) B | (203.8564, 233.8985) B, 20.0 mm | (204.18, 232.58) B 180°, 18.82 mm from paper, 13.18 mm from pre-S10 | C4244 17.67 / 20.90 / 6.85 mm |
| U4537 (SN74HC74DR) | (166.97, 177.18) B | paper | (165.0936, 184.183) **F**, 7.25 mm | (149.97, 182.68) **F** 180°, 17.87 mm | C4554 5.06 / 7.04 on B / 5.06 on F |

`link-era-replacements.json` at HEAD lists `withheld_overlay_ics: [U4222, U4227, U4537]` and places only the ten S8
blocks. Open ICs are U5209, U5210, U1415, U5110, U8409 before and U1415, U5110, U8409 after.

## Ruling recommendation (b): record the negative result and put one choice to the owner

### What the design authority can rule now, with the owner notified

1. Coordinate equality for R5257, U5210 and R5259, as worded above.
2. The slot-only negative result: within 24 mm on the retained grids, no scene places U5210 without displacing
   R8356. No study is admitted to re-derive it.

### The owner question

**How should U5209 and U5210 be resolved, now that no connector spot within 24 mm spares the protected parts?**

| Option | What happens | Cost and risk |
| --- | --- | --- |
| **1. Search wider, all five ICs together (recommended)** | One study on the `6e5716e7` snapshot for all five open ICs. Movable: DS-149's four links (L07, L08, L12.02.01.02, L03.01), the three L13 links and P-K-P-L15.02.01.01, out to the 35 mm join radius. Every protected part is a hard keep-out. S10 Revision 1 stays returned. | One long run that may still return nothing; whether any scene exists out to 35 mm is not established. Needs its own design-authority brief and review. Changes four retained rows, listed below. |
| 2. Simulate first, then allow bounded moves | Vendor-model simulation of the fold cell, the wiper-sense buffer and the REF9 cell to set a capacitance budget per node; protected passives may then move within it. | The only route with real electrical evidence. Needs the ngspice oracle. May show the fold cell needs a feedback capacitor, which is a circuit and BOM change. Changes the DS-150 rule. |
| 3. Replace the displacement stop with a per-node no-growth test | A protected passive may move if its node's pad extent, pad-to-pin distance and face set are no worse than paper. | Geometric proxy only. The returned candidate still fails it on R8221, R8356, R5249 (face), R8431, R5148 and R5253, so a new candidate is needed anyway. Changes the DS-150 rule. |
| 4. Stop for these two | U5209 and U5210 join U1415, U5110 and U8409 on the open-IC card. | Check 5 fails for five ICs and the DS-60 alternatives return. S11 still needs a pin other than an accepted S10. |

Why option 1: it keeps the DS-150 protection intact, matches the owner's DS-149 choice for the other three ICs,
and removes the deadlock in which S11 waits for an S10 that cannot be accepted. Moving an endpoint (R5257 nearer
U5210) is not offered: once equality is ruled it solves nothing.

**Why L15.02.01.01 is released in the recommended version.** On the 0.25 mm grid the S9-A2 search of L13.01.01.01
rejected 36114 positions:

| Cause of rejection | Count | Can a link search change it? |
| --- | --- | --- |
| panel hardware (RV1001–RV1202, SW1301, SW1302) | 23656 | no |
| fixing keep-outs (POWER-P-+5V, POWER-P-AGND1) | 5335 | no |
| P outline and "slot not under its own front board" | 4094 | no |
| U8409 courtyard, still covers U5210 | 202 | no |
| P-K-P-L15.02.01.01 front field | 2684 | only if L15.02.01.01 moves |
| P-K-P-L03.01 (slot, K field, front tail) | 143 | yes, L03.01 is a DS-149 link |

L15.02.01.01 causes 2684 of the 2827 link-caused rejections (95 %); L03.01 causes 143 (5 %). With L15.02.01.01
held at (193.0, 213.0) +y, option 1 would rest on L03.01 and on the 24–35 mm ring alone. Releasing it is therefore
the version I recommend. Revision 2 of this packet wrongly said a joint search of the DS-149 and L13 links could
move both blockers; L15.02.01.01 was in neither group. Two cautions: these are tallies of rejection reasons, not
counts of positions that would open, and 33287 of 36114 rejections have fixed causes. L15.02.01.01 would be a
searched link with U5210's courtyard as a keep-out, not a free one; the first S10 attempt stopped because it
landed on U5210.

**Everything option 1 changes**, so the owner sees it in one place:

| Retained item | Change |
| --- | --- |
| DS-149 (owner) | widened: four more movable links (three L13 links and L15.02.01.01) and two more keep-out ICs (U5209, U5210), all to the 35 mm join radius |
| DS-150 (owner-supplied) | "S11 awaits an independently accepted S10 commit" is replaced: the study starts from the pre-S10 base |
| DS-148 (design authority) | the hold of P-K-P-L15.02.01.01 at (193.0, 213.0) +y is released for the study; the L13.01.01.02 hold at (176.0, 196.25) lapses with the returned candidate |
| S11 brief | superseded in its start gate, its `S10_RESULT_COMMIT` pin and "every slot hold in the pinned options file" |
| Inputs | read from the `6e5716e7` snapshot, not HEAD: HEAD carries the returned candidate's gate rows and holds |

The DS-150 protected-part rule, DS-06, the panel centres, sleeves, fixing keep-outs, cables and connectors are not
changed, and the three individual fallbacks stay as written.

**Options 1 and 2 are not exclusive.** The fold-cell vendor-model simulation is already U5110's DS-149 fallback and
this packet calls for it on its own grounds. It can be admitted alongside option 1 as model evidence without
changing the DS-150 rule; option 2 as a choice means waiting for it and then letting protected passives move.

### Requirements any future study brief must meet (from review defect 3)

| Item | Requirement |
| --- | --- |
| Reference pose | paper for every protected footprint and for U5209 and U5210; a return to paper, including its face change, is explicitly allowed |
| Protected set | every footprint on a `_FB`, `_SUM` or `_SENSE` net and every input-buffer IC; new, shifted, turned and overlay-moved cases all count |
| Open ICs | restate S9-A2 rule 4: no candidate covers the recorded courtyard, grown 0.35 mm, of U1415, U5110, U8409, U5209 or U5210 |
| Tail rule | follow the gate: it does not displace parts under a K tail (R5259 is in `under_tails` of L13.01.01.02 at `32580f77` and has no row); a stricter tail preflight must be ruled, not assumed |
| Preflight | deterministic rectangle test first; positive control: it must reproduce R5249, R5256, R8221, R8331, R8356 at `32580f77` before it is trusted |
| Mutations | candidates over R5256, R5257, R5259, R8356 and U8409's courtyard; a rotation-only protected member; a shifted protected row |
| Run bounds | process count, memory limit, wall-time ceiling and expected run time stated before the run (ORCHESTRATION.md section 3) |
| Locality basis | see the next section; not settled by this packet |

### Two ruling items this packet does not settle

- **Locality comparison basis.** Brief Revision 1 stops on "a worse figure in `locality-acceptances.json`". Comparing
  against pre-S10 effective geometry instead (for example `/E5/READY` 22.39 mm against the accepted 4.12 mm) changes
  that stop and needs a ruling. Revision 1 of this packet used the rebased figure without saying so.
- **The five inherited mismatches** need their own disposition outside S10, by whoever accepted the records: U5113
  sits at 84.77 mm against an accepted 65.97 mm, and U4417 nets exceed their records by up to 29.01 mm.

### DS-149 and the three fallbacks are preserved

No placement is proposed for U1415, U5110 or U8409. The fallbacks stand as written: a remote-buffer vendor-model
simulation for U8409, a dual op-amp for U1415, the 40.61 mm far pose with a fold-cell simulation for U5110. Option 1
widens the DS-149 study and changes its start gate, which is why it is the owner's to choose.

The `input-buffer-vendor.json` 0–50 pF result covers `high_impedance_input` instances U1216, U1416, U1518, U4346,
U8314 and U8417 only. It cannot be cited for U8208, U8310, U8311 or U4240.

## Evidenced, assumed and not established

| Class | Items |
| --- | --- |
| Evidenced from retained sources | origin of 7.93; paper poses and the integer inequality; net membership and identities; all movement, face, locality and U4526 figures; interim copper lengths and their connection to U5210 pins 6 and 7; absence of stability evidence; complete S9-A2 enumeration and R8356 under all 81 |
| Geometric, ungrown courtyards | the x = 176.0 slot overlaps; R5259 under the K tail |
| Assumed | 0.20 pF/mm and route factor 1.5; every loop-estimate assumption listed above; pad transform for displaced parts |
| Not established | any electrical behaviour; any link-era routing; whether a wider-radius scene exists; exhaustiveness for U5209 alone |

## Independent review required

1. `7.93` first appears as `round(7.934242…, 2)` in `slot_moves_a2.py` and has no electrical derivation.
2. Paper poses of R5257 and U5210 at five commits, and 631² + 481² = 629522 > 628849.
3. `/W1/F2_SUM` has exactly three pins; R5256 is on F at paper.
4. Pad-centre figures 11.949 mm and 11.795 mm.
5. Interim K copper: `F2_SUM` 26.160 mm, 3 vias, one component with all three pads; `F2_OUT` 35.807 mm, 5 vias, one
   component with all four pads; track ends inside U5210 pads 6 and 7.
6. `caps_reached: []`; R8356 under the K connector in 81 of 81; R8456 79, R4238 72; the 14 x = 176.0 overlaps; the
   rejection reasons of L13.01.01.01 naming neither other L13 link.
7. The qualification that the L13.01.01.02 set depends on L13.01.02.01 (370 rejections) and whether it matters.
8. The six protected movements, the four shifted-row movements and their node figures.
9. U5113 84.77 mm and the U5112, U4646, U4417, U4526 figures; all five predate S10.
10. `/E5/HOLD_N` 39.81 → 65.25 mm and `/E5/READY` 22.39 → 30.64 mm; withheld-overlay values 50.31 and 32.89 mm.
11. 56 movements, 16 face changes, none rotation-only; gate rows identical at `32580f77` and `557b5a6e`.
12. The loop estimate as arithmetic only, with its assumptions.
13. That `input-buffer-vendor.json` does not cover U8208, U8310, U8311 or U4240.
14. That coordinate equality is a design-authority ruling under DS-03 and that option 1 is the owner's.
15. The rejection tally of L13.01.01.01 on the 0.25 mm grid: 36114 total, 2684 naming L15.02.01.01, 143 naming L03.01.

## Inputs relied on

Commits: HEAD `80569b5375087df519b79ead67d1bf56c16301e6`; checker `557b5a6e92e2600fcb4319bd8528c4f5812d3177`;
candidate `32580f77c9d0aa9c6067cbad965a6f701050ca5d`; pre-S10 base `6e5716e7fc011e2f028982f645d18b8d802acb29`;
S9-A2 `8243acdf4ef76b18741ce3bcca4794e2abf3fee2`; locality baseline `6093081cc6d1fcbfc4e134e4dfa1861a3de39836`.

| File (at HEAD unless a commit is given) | SHA-256 |
| --- | --- |
| `AGENTS.md` | `05e2d1bbd1dce7d18d6236c9613820a06808a9ef577ac86683e7dbde9b7e1cb5` |
| `CLAUDE.md` | `e509b5171843f86f0992540c621e12883f74f5c5b8fcdf845ec572e347774b4e` |
| `circuit/WORKFLOW.md` | `dff26b3f0d7a05a556d42a19ee3b407bd85fe6f0b20cc8bbfac163409f906d14` |
| `circuit/ORCHESTRATION.md` | `e8b428418b0c7c4038790c20d6a29d44f5680c4560afdd256a55b3843a6ef5d0` |
| campaign `decisions.md` | `779f9ec437d5c0c1540513a5738ba2cca147f503d9eb891e2351369f68648295` |
| `mc04-s10-revision-2-feasibility.md` | `8af21e49ba1ed458bbfa9a9c9395cfc41384cfaa55e4101e74dc96c004fe9259` |
| `mc04-s10-report-20261122.md` | `63eca3c2e28b6831ae96fb4f140d5b8b98bfea4d4d0828cb0565ee8c6c7af94f` |
| `mc04-s10-l13-link-moves-generator-brief-20261122.md` | `1dc962163d1775941cdf24b9cbb53c0d0cc211305a6910955afd9376230c1714` |
| `wsl-s10-checker-review-20261125.md` | `a1afb0b8c167d1679202216c58406445e879e23baad8dea332e644348bdbfbb6` |
| `mc04-s11-link-replacement-study-brief-20261122.md` | `94714d66d126426946c32771853829320768c5daef54d7ee8e9335750cbd3c27` |
| `mc04-s10-review-20261123.md` | `73d3e4d387fc6b4695c40ee901d8b019414ca2a3e86a1e9b92bdb387844da17f` |
| `mc04-s9-a2-report-20261122.md` | `2a0a5b433a5c471b74758762e4ba3682e8aeea3012c5ebaa0c89127bd7b7aeb1` |
| `scripts/stack/studies/mc04_s9_slot_moves/result-a2.json` | `9d524988de302e6d0052ab26b503bf24c71ce5f2c693f30b111e66955cc348d2` |
| `scripts/stack/studies/mc04_s9_slot_moves/slot_moves_a2.py` | `26874e1f7d1e71923ccc88d977f6097bbf1a0c226cd9c9f54c8f00a5c58708d1` |
| `scripts/stack/studies/mc04_s8_replacement/replacement.py` | `543b02b7baf9d0a1ed531985c4b584fb1a254cc0507903e1c08b95e0ab07916e` |
| `scripts/stack/studies/mc04_s10_l13/overlay.py` | `8acf3bb86873612fed99daf798435fff8301bdd6302a83df2d67ec3b731f3519` |
| `scripts/stack/studies/mc04_s10_l13/test_s10.py` | `013ce46d228055a47bbce7a14252294a733290f59bfd74230af735a2c761aae3` |
| `scripts/stack/studies/mc04_s10_l13/overlay.json` | `c0f18373b46ec9097024b057905a41403aebd41a638d02355219b92f4a11efab` |
| `overlay.json` at `32580f77` | `5a7a07a8b2612d489d9c3709826a50066287b238ee591579293c55fa7fc07d3c` |
| `design/stack/geometry/links/link-gate.json` | `793b7f1962a1c14855b11a36cba57f7544f20ac7c889b3d2e3135ab96be54c9d` |
| `link-gate.json` at `32580f77` | `fa944359686a7afcd8d916c9b672f6c6d5d3f64b9119a27bf77f767e63ab03a6` |
| `link-gate.json` at `6e5716e7` | `bcbee2ca955ae06f0d42031899cb3d74501916545893f9454eaa18c89ccbecc3` |
| `design/stack/geometry/links/link-era-replacements.json` | `a2d09689f7376cf90db3164bc57ccff795f91bfec0b9e23caeb35044dadbd147` |
| `link-era-replacements.json` at `6e5716e7` | `a9af0e8ca4162822dc0608943c8c0813f347b9e5f8ca2b7b612a522ecd25f4d0` |
| `design/stack/geometry/links/link-gate-options.json` | `914dd6b1295a610142a938b37798f947d9f345ab44cce154c4cbe6a909218e92` |
| `design/partition/locality-acceptances.json` (same at `6e5716e7`) | `54f2c5a5fd64314a4cfee812fe7e781013c3a11bef176d1c31408bed7da45dc7` |
| `design/partition/adopted-placement-pins.json` (same at `8243acdf`) | `9e827879ebcccea57d247e433a496db71ee1213c87af27b90c81fada2d1218b2` |
| `design/partition/floorplan-candidate.json` (same blob at `6e5716e7`) | `12083ea177cad1492f07fa96ad6dbfea8e5f8d2d347199bb555475c5b9e75a38` |
| `design/partition/floorplan-candidate.json` at `6093081c` | `e58f80d987c420e5316a569da1a88280f8378c1bbf8913bf74c9e253cb1fdf92` |
| `design/reports/io-partition.json` (same at `8243acdf`, `6e5716e7`) | `235277959121d8599cbe1b6c6ae65ed4cd3fd3813cf2a8db05d2951ce5b633ce` |
| `design/reports/board-net-tokens.json` | `7ef8a93c0ced61f602448f53e1276d7164d6e5567096bc806685fcd3ea880c1c` |
| `design/spec/modules/wavefolder.py` | `e3a850e841a0f597571d6550e372d337c404fe4155ede3af7372be03ace37a93` |
| `design/spec/modules/check_wavefolder.sh` | `cc69aedd9df3d616f0c32b2383d65678eecd4c492c7c9e428a3654784dede2f4` |
| `design/reports/spice/wavefolder.json` | `7a0a8565d666bf1dea3e54accf0809cf7bcf3ea697a15f212bd5b425c2018c2c` |
| `design/reports/spice/input-buffer-vendor.json` | `12a0de40445d5156ccab2d583b45baa14f8b0420935ae57ca7a2f3d391654c9b` |
| `.claude/skills/component-spec-audit/references/inventory.json` | `dd31420dc068ef2953ada299f3a2a873c5da1ee86f645ce4dc95f12476256eba` |
| `.claude/skills/component-ti-opa4196idr/facts.json` | `7f297989aafdfec304c75583c41ecf33d2ad1e213add11d86ea7e5ab19a77ba5` |
| `.claude/skills/component-ti-opa4196idr/sources.json` | `cf3f20789c24745f3a1c8c03637b8bdd2f09ee39eb8b3a04d9cb68cf0c70b64c` |
| `.claude/skills/component-ti-opa4196idr/interactions.json` | `ac12dd29a2159de79a48fadfa51ef50960822b8e8b2414413a84eca6b5b4d43f` |
| `.claude/skills/component-ti-opa4196idr/pin-map.json` | `18ec31b66f3800139775a95773ccf4818560272d72f0cf655a9e0422abcd0b47` |
| `boards/osc-core/osc-core.kicad_pcb` (blob `5c6411be`, same since `8243acdf`) | `2c7535d13e88a0d4b9a438d51919829708c7c5825753dad7bb3e50a660c871b3` |
| `boards/osc-jack-left/osc-jack-left.kicad_pcb` | `35a4b3430dabbd93d83b00e200757c66e878f47f067142d12fdae2d9c5403a10` |
| `boards/osc-jack-right/osc-jack-right.kicad_pcb` | `c235cf4f6aa7c13bf1a12e839e0b3cd049b63f1453a6a06981a2a14e4f3cfad7` |
| `reviews/mc04-s10-revision-2-packet-review-20261127.md` (the returned review) | `8f51cf20282b1d7b0ddadddd7b624e6fab18693a008a20c8b63312b39741a7bc` (with the appended re-review) |
| `design/grid/placements.lock.json` | `297300b067fd646624b9e501791163fa2d60702862b61568753bf92e5b88dbe8` |

Not read: the owner bundle `component-passives-family` beyond its inventory line, and
`component-precision-feedback-passives`. The OPA4196 datasheet PDF itself was not opened; its facts are quoted from
`facts.json`.

## Analysis scripts

All in `scripts/stack/studies/mc04_s10_r2_packet/` (copied verbatim except the repository-root line; the withdrawn `f2_sum_connectivity.py` is not retained), read-only against the repository, each under five seconds.

| Script | Purpose |
| --- | --- |
| `trace_w1_f2.py` | net membership, identities and paper poses for the F2 network; integer check |
| `board_copper_w1_f2.py` | pad centres and copper per net on the interim K board |
| `rev2_verify.py` | copper connectivity by geometry; S9-A2 coverage, knock-on counts and the x = 176.0 rectangle tests |
| `recompute_s10.py` (output `recompute_s10.out.txt`) | independent scene, movements, protected-node extents, locality and U4526 figures, overlay blocks |
| `f2_loop_estimate.py` | first-order typical-only loop estimate |

`f2_sum_connectivity.py` from revision 1 was removed: its pad window was wrong.

## Checks not run

| Check | Status |
| --- | --- |
| `regen-all.sh`, `pnpm circuit:check`, `overlay.py --check`, `test_s10`, any generator | NOT RUN: read-only session |
| KiCad oracle, ngspice | NOT RUN: no board change, and no oracle step was admitted |
| Any candidate search or enumeration | NOT RUN: not admitted; only retained records and rectangle tests on retained rectangles were read |

## Change log: packet revision 1 → 2, against `review-20261127.md`

Each defect was re-verified with `scripts/rev2_verify.py` before it was accepted.

| # | Defect | My re-check | Disposition |
| --- | --- | --- | --- |
| 1 | HIGH: interim copper does reach U5210 pins 6 and 7 | Both nets are one component containing every pad; track ends (184.375, 207.05) and (182.55, 208.25) lie inside the 1.95 × 0.6 mm pads | **Accepted.** "No routed loop" and "gap at U5210" removed; paper routed reference 26.16 mm, 3 vias stated; 5.23 pF row added |
| 2 | HIGH: the proposed study is predetermined to return zero | `caps_reached: []`; R8356 under the K connector in 81 of 81; all 14 x = 176.0 candidates over R5254, R5256, R5257 or R5259 | **Accepted**, with one qualification: the L13.01.01.02 set depends on L13.01.02.01 (370 rejections), so U5209 alone is not proven exhaustive. The conclusion is unchanged because U5210 is decisive. Study dropped; negative result recorded; wider-radius joint search added as owner option 1 |
| 3 | HIGH if a study is kept: contract contradictions | Confirmed: four returns to paper change face; R5259 is in `under_tails` with no row | **Accepted.** No study kept; the points are carried as requirements for any future brief |
| 4 | MEDIUM: knock-on undercount and mislabelled source | R8456 named in 79 of 81 records (7 in `parts_re_placed`), R4238 in 72, four others in 4; R5259 under the K tail at all four paired y | **Accepted.** Counts corrected; x = 176.0 row labelled geometric |
| 5 | MEDIUM: rebased locality limit was an unlabelled ruling | Accepted record for `/E5/READY` is 4.12 mm; I used 22.39 mm | **Accepted.** Listed as an unsettled ruling item; inherited mismatches given their own disposition item |
| 6 | MEDIUM: coordinate equality is design-authority scope | DS-03 delegates; DS-147 is a design-authority row; DS-150 "Reverse by" names no owner message and already fixes both parts | **Accepted.** Proposed as a design-authority ruling with the owner notified |
| 7 | LOW: estimate worded as a finding | – | **Accepted.** Reworded; missing assumptions listed; "not a lower bound" stated |

No defect is disputed.

## Change log: packet revision 2 → 3, against the re-review (ACCEPT WITH CORRECTIONS)

| # | Correction | My re-check | Disposition |
| --- | --- | --- | --- |
| 1 | MEDIUM: option 1 did not move L15.02.01.01, the main link blocker | `result-a2.json`, U5210 search, 0.25 mm grid: 2684 rejections name L15.02.01.01, 143 name L03.01, 2827 link-caused of 36114 | **Accepted.** The wrong sentence is removed. Option 1 now releases L15.02.01.01 as a searched link, names the DS-148 change and gives the tally, with the caution that 33287 rejections have fixed causes |
| 2 | LOW: name everything option 1 changes | – | **Accepted.** Table added: DS-149, DS-150, DS-148, the S11 brief and the `6e5716e7` snapshot |
| 3 | LOW: options 1 and 2 are not exclusive | – | **Accepted.** Stated, with the U5110 fallback link |
| 4 | LOW: review hash | file now `8f51cf20…a7bc` | **Accepted.** Input table refreshed |

