# Flat-link electrical bounds: ST-04 attempts a2 and a3 (paper, DS-41 checks 3 and 4 without positions; harness baseline DS-54)

Task `osc-stack-20261114/ST-04 attempt a2 (DS-41 checks 3 and 4 without positions; DS-48, DS-51)`, launch commit `21d1cd9`. **Status: unvalidated paper bound.** Coupling, current share and resistance are NOT RUN as measurements; nothing is selected, adopted or bought. Every class, impedance, edge rate and limit below is ASSUMED unless a row says otherwise, and the limits are criteria for the design ruling (NEEDS_DESIGN).

This file, `results.json` and `harness-baseline.json` are written by `python3 scripts/stack/link_electrical/link_electrical.py` from [`inputs.json`](inputs.json); the tests fail if any differs from a fresh run. Status words: SOURCED (file and locator in `inputs.json`), DERIVED (formula below), ASSUMED (reason in `inputs.json`), NOT RUN (reason given).

## 490 link signals in four coupling classes, the count of ST-02's room study (490)

Every K pair of the retained candidate except the six adapter pairs, with rail, AGND and NC positions removed (as `NON_SIGNAL` in `scripts/stack/geometry/links.py`): 511 K-pair signals less 21 on the adapter pairs = 490; 2 NC positions on link pairs are not signals. The class comes from the partition's signal kind and the net name (`inputs.json` → `classes`, ASSUMED). Four planning nets of the SUB pairs (`O2:SUB_SEL_A` etc.) are not in the partition harnesses and are taken as LOGIC.

| Joint | PRECISION | WIPER | ANALOGUE | LOGIC | Total |
| --- | --- | --- | --- | --- | --- |
| JL to K | 12 | 0 | 88 | 0 | 100 |
| JL to P through K | 0 | 0 | 16 | 0 | 16 |
| JR to K | 16 | 0 | 90 | 0 | 106 |
| P to K (with SUB and EL pass-through) | 50 | 99 | 68 | 51 | 268 |
| **Total** | 78 | 99 | 262 | 51 | 490 |

| Class | Victim source impedance (sweep, nominal) | Victim limit | As aggressor |
| --- | --- | --- | --- |
| PRECISION | 10, 100, 1000 Ω, nominal 100 Ω | 1 mV | ANALOGUE row (op-amp slew) |
| WIPER | 2500, 25000, 125000 Ω, nominal 25000 Ω | 1 mV | none (hand-turned; STATIC) |
| ANALOGUE | 10, 100, 1000 Ω, nominal 100 Ω | 10 mV | 20 V at 20 V/µs (sweep 10 / 20 / 40 V/µs), and a 10 V peak 20 kHz sine |
| LOGIC | 25, 50, 100 Ω, nominal 50 Ω | 500 mV | 5 V in 5 ns (sweep 2 / 5 / 15 ns), load 15 pF |

## Coupling under the ASSUMED absolute limits: at both pitches 3 of 8 class pairs side by side, 0 with a grounded neighbour, 5 not in one cable (LOGIC onto PRECISION, LOGIC onto WIPER, LOGIC onto ANALOGUE, ANALOGUE onto PRECISION, ANALOGUE onto WIPER)

Upper permittivity 3.2, nominal impedance and edge. The table gives the worst bound over 50 and 80 mm per pitch; voltage in mV, dB relative to the aggressor swing; "sine" is the steady 20 kHz bleed. Rule A adjacent is two signals side by side; A across ground and B are one grounded conductor between them (B also has grounds on the outer sides).

### 1.00 mm pitch: worst crosstalk per class pair, 50 / 80 mm

| Aggressor → victim | Limit, mV | Side by side, mV (dB) | Ground between (A), mV (dB) | Ground between (B), mV (dB) | 20 kHz sine side by side, mV | Rule that follows |
| --- | --- | --- | --- | --- | --- | --- |
| LOGIC → PRECISION | 1 | 269 (-25) / 400 (-22) | 59.7 (-38) / 88.9 (-35) | 57 (-39) / 84.7 (-35) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → WIPER | 1 | 1.02e+03 (-14) / 1.25e+03 (-12) | 198 (-28) / 245 (-26) | 224 (-27) / 274 (-25) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → ANALOGUE | 10 | 269 (-25) / 400 (-22) | 59.7 (-38) / 88.9 (-35) | 57 (-39) / 84.7 (-35) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → LOGIC | 500 | 173 (-29) / 260 (-26) | 42.3 (-41) / 63.3 (-38) | 36.1 (-43) / 54.1 (-39) | — / — | side by side |
| ANALOGUE → PRECISION | 1 | 3.98 (-74) / 5.97 (-71) | 0.742 (-89) / 1.11 (-85) | 0.868 (-87) / 1.3 (-84) | 0.244 / 0.365 | not in the same flat cable (separate link or ground layer) |
| ANALOGUE → WIPER | 1 | 950 (-26) / 1.39e+03 (-23) | 174 (-41) / 255 (-38) | 208 (-40) / 305 (-36) | 60.8 / 91.2 | not in the same flat cable (separate link or ground layer) |
| ANALOGUE → ANALOGUE | 10 | 3.98 (-74) / 5.97 (-71) | 0.742 (-89) / 1.11 (-85) | 0.868 (-87) / 1.3 (-84) | 0.244 / 0.365 | side by side |
| ANALOGUE → LOGIC | 500 | 2.04 (-80) / 3.06 (-76) | 0.387 (-94) / 0.581 (-91) | 0.444 (-93) / 0.666 (-90) | 0.122 / 0.183 | side by side |

### 0.5 mm pitch: worst crosstalk per class pair, 50 / 80 mm

| Aggressor → victim | Limit, mV | Side by side, mV (dB) | Ground between (A), mV (dB) | Ground between (B), mV (dB) | 20 kHz sine side by side, mV | Rule that follows |
| --- | --- | --- | --- | --- | --- | --- |
| LOGIC → PRECISION | 1 | 255 (-26) / 380 (-22) | 60.1 (-38) / 89.5 (-35) | 57.3 (-39) / 85.3 (-35) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → WIPER | 1 | 978 (-14) / 1.2e+03 (-12) | 203 (-28) / 252 (-26) | 231 (-27) / 283 (-25) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → ANALOGUE | 10 | 255 (-26) / 380 (-22) | 60.1 (-38) / 89.5 (-35) | 57.3 (-39) / 85.3 (-35) | — / — | not in the same flat cable (separate link or ground layer) |
| LOGIC → LOGIC | 500 | 167 (-30) / 250 (-26) | 42.7 (-41) / 64 (-38) | 36.4 (-43) / 54.6 (-39) | — / — | side by side |
| ANALOGUE → PRECISION | 1 | 3.68 (-75) / 5.51 (-71) | 0.738 (-89) / 1.11 (-85) | 0.866 (-87) / 1.3 (-84) | 0.224 / 0.337 | not in the same flat cable (separate link or ground layer) |
| ANALOGUE → WIPER | 1 | 878 (-27) / 1.29e+03 (-24) | 173 (-41) / 254 (-38) | 208 (-40) / 306 (-36) | 56.1 / 84.1 | not in the same flat cable (separate link or ground layer) |
| ANALOGUE → ANALOGUE | 10 | 3.68 (-75) / 5.51 (-71) | 0.738 (-89) / 1.11 (-85) | 0.866 (-87) / 1.3 (-84) | 0.224 / 0.337 | side by side |
| ANALOGUE → LOGIC | 500 | 1.89 (-80) / 2.83 (-77) | 0.386 (-94) / 0.578 (-91) | 0.443 (-93) / 0.665 (-90) | 0.112 / 0.168 | side by side |

Three ASSUMED terms carry these verdicts, and each is a design input. (1) The wiper victim has no receiver filter capacitor credited: at 25 kΩ the coupled edge decays over R·C_tot, and any filter capacitor at the receiver divides it by C_filter/C_tot. (2) PRECISION nets are counted as aggressors at full analogue slew; most are DC references or slow CVs. (3) The victim limits (PRECISION 1 mV, WIPER 1 mV, ANALOGUE 10 mV, LOGIC 500 mV) are peak criteria for nanosecond to microsecond spikes; a pitch error depends on the area that the receiving stage integrates, which no retained source states. No 2-layer flex with a ground layer is computed (DS-41 check 4): NOT RUN.

### Per-unit-length terms behind the table (DERIVED)

| Pitch | Configuration | ε_eff | Cm at 50 mm + ends, pF | Victim total C, pF | Partial mutual a–v, nH | Loop mutual with ground return, nH |
| --- | --- | --- | --- | --- | --- | --- |
| 1.00 mm | A adjacent | 1.0 | 0.606 | 1.602 | 45.6 | 12.72 |
| 1.00 mm | A adjacent | 2.1 | 1.272 | 3.364 | 45.6 | 12.72 |
| 1.00 mm | A adjacent | 3.2 | 1.938 | 5.127 | 45.6 | 12.72 |
| 1.00 mm | A across ground | 1.0 | 0.111 | 1.602 | 37.5 | 4.09 |
| 1.00 mm | A across ground | 2.1 | 0.233 | 3.364 | 37.5 | 4.09 |
| 1.00 mm | A across ground | 3.2 | 0.355 | 5.127 | 37.5 | 4.09 |
| 1.00 mm | B across ground | 1.0 | 0.133 | 1.573 | 37.5 | 2.48 |
| 1.00 mm | B across ground | 2.1 | 0.278 | 3.304 | 37.5 | 2.48 |
| 1.00 mm | B across ground | 3.2 | 0.424 | 5.035 | 37.5 | 2.48 |
| 0.5 mm | A adjacent | 1.0 | 0.558 | 1.504 | 53.9 | 12.89 |
| 0.5 mm | A adjacent | 2.1 | 1.172 | 3.158 | 53.9 | 12.89 |
| 0.5 mm | A adjacent | 3.2 | 1.786 | 4.812 | 53.9 | 12.89 |
| 0.5 mm | A across ground | 1.0 | 0.110 | 1.504 | 45.6 | 4.18 |
| 0.5 mm | A across ground | 2.1 | 0.231 | 3.158 | 45.6 | 4.18 |
| 0.5 mm | A across ground | 3.2 | 0.352 | 4.812 | 45.6 | 4.18 |
| 0.5 mm | B across ground | 1.0 | 0.132 | 1.475 | 45.6 | 2.55 |
| 0.5 mm | B across ground | 2.1 | 0.278 | 3.097 | 45.6 | 2.55 |
| 0.5 mm | B across ground | 3.2 | 0.423 | 4.719 | 45.6 | 2.55 |

Formulas. Capacitance: 2-D method of moments for coplanar strips in a homogeneous medium (ε_eff swept 1 / 2.1 / 3.2), zero total charge, the other conductors of the window held at AC ground; checked against ε K(k')/K(k) for two strips in the tests. Inductance: Grover's parallel-filament mutual and Ruehli's bar self term, valid for length ≫ spacing; the aggressor return divides among the window's grounds by least inductance. Victim bound = capacitive term V·R·Cm/t_r·(1 − e^(−t_r/(R·C_tot))) plus the full loop term M·di/dt, di/dt = 2·I/t_r (both ASSUMED same sign). Each end adds 5 mm of parallel run for the connector and fan-in (ASSUMED).

### The verdicts turn on the victim impedance and the logic edge: sensitivity at 0.5 mm, 80 mm, ε_eff 3.2

| Configuration | Aggressor → victim | Edge or slew sweep (rows) × victim impedance sweep (columns), mV |
| --- | --- | --- |
| A adjacent | LOGIC → PRECISION | 793 / 1.27e+03 / 1.74e+03; 143 / 380 / 1.02e+03; 21.8 / 102 / 644 |
| A adjacent | LOGIC → WIPER | 1.79e+03 / 1.82e+03 / 1.82e+03; 1.13e+03 / 1.2e+03 / 1.21e+03; 879 / 1.08e+03 / 1.1e+03 |
| A adjacent | LOGIC → ANALOGUE | 793 / 1.27e+03 / 1.74e+03; 143 / 380 / 1.02e+03; 21.8 / 102 / 644 |
| A adjacent | LOGIC → LOGIC | 893 / 1.05e+03 / 1.27e+03; 183 / 250 / 380; 35.2 / 57.6 / 102 |
| A adjacent | ANALOGUE → PRECISION | 0.326 / 2.74 / 26.9; 0.691 / 5.51 / 53.7; 1.54 / 11.2 / 108 |
| A adjacent | ANALOGUE → WIPER | 67 / 669 / 2.45e+03; 134 / 1.29e+03 / 3.22e+03; 268 / 2.16e+03 / 3.74e+03 |
| A across ground | LOGIC → PRECISION | 248 / 341 / 434; 42.9 / 89.5 / 215; 5.94 / 21.8 / 129 |
| A across ground | LOGIC → WIPER | 444 / 450 / 451; 237 / 252 / 253; 175 / 215 / 219 |
| A across ground | LOGIC → ANALOGUE | 248 / 341 / 434; 42.9 / 89.5 / 215; 5.94 / 21.8 / 129 |
| A across ground | LOGIC → LOGIC | 268 / 298 / 341; 50.8 / 64 / 89.5; 8.58 / 13 / 21.8 |
| A across ground | ANALOGUE → PRECISION | 0.0716 / 0.547 / 5.3; 0.156 / 1.11 / 10.6; 0.362 / 2.26 / 21.3 |
| A across ground | ANALOGUE → WIPER | 13.2 / 132 / 482; 26.5 / 254 / 634; 53 / 426 / 738 |
| B across ground | LOGIC → PRECISION | 159 / 272 / 385; 29.3 / 85.3 / 238; 4.66 / 23.7 / 153 |
| B across ground | LOGIC → WIPER | 397 / 405 / 406; 265 / 283 / 285; 210 / 259 / 264 |
| B across ground | LOGIC → ANALOGUE | 159 / 272 / 385; 29.3 / 85.3 / 238; 4.66 / 23.7 / 153 |
| B across ground | LOGIC → LOGIC | 183 / 220 / 272; 38.8 / 54.6 / 85.3; 7.83 / 13.1 / 23.7 |
| B across ground | ANALOGUE → PRECISION | 0.0749 / 0.646 / 6.36; 0.157 / 1.3 / 12.7; 0.345 / 2.63 / 25.5 |
| B across ground | ANALOGUE → WIPER | 15.9 / 158 / 582; 31.8 / 306 / 768; 63.5 / 513 / 894 |

## The a2 class rule needs 94 to 109 grounds for the 490 signals; counted per link, rule A needs 245 to 264, rule B 440 to 464 without outer grounds and 518 to 546 with them

Own class rule, per joint and option, with free ordering inside a joint: classes in blocks, a ground between same-class neighbours only where the class pair needs one, one ground between blocks that share a cable, one ground per link (at a cable edge; no other outer grounds), and class pairs that may not share a cable put in cables of their own. A lower bound: the class mix per link follows the clustering of ST-02 a4. DS-51 rules are counted per link with the capacities of the room study (links filled to capacity per joint): rule A one ground per two signals; rule B read without outer grounds (s − 1 grounds per link, the room study's reading and the present harness pattern) and with them (s + 1). Filling every link to capacity per joint gives fewer links than the room study's clustering, which also respects site distances.

| Pitch | Circuits | Own rule, grounds / links | Rule A, signals per link: grounds / links | Rule B inner only, signals per link: grounds / links | Rule B with outer grounds, signals per link: grounds / links |
| --- | --- | --- | --- | --- | --- |
| 1.00 mm | 20 | 109 / 34 | 13: 264 / 40 | 10: 440 / 50 | 9: 546 / 56 |
| 1.00 mm | 22 | 107 / 32 | 14: 245 / 38 | 11: 443 / 47 | 10: 541 / 50 |
| 0.5 mm | 30 | 100 / 25 | 20: 245 / 26 | 15: 455 / 35 | 14: 528 / 38 |
| 0.5 mm | 40 | 94 / 19 | 26: 245 / 21 | 20: 464 / 26 | 19: 518 / 28 |

Per joint at 1.00 mm, 20 circuits (the other options in `results.json`):

| Joint | Signals | Cable groups | Own rule | Rule A | Rule B inner | Rule B outer |
| --- | --- | --- | --- | --- | --- | --- |
| JL to K | 100 | ANALOGUE; PRECISION | 18 / 7 | 54 / 8 | 90 / 10 | 112 / 12 |
| JL to P through K | 16 | ANALOGUE | 1 / 1 | 9 / 2 | 14 / 2 | 18 / 2 |
| JR to K | 106 | ANALOGUE; PRECISION | 22 / 7 | 57 / 9 | 95 / 11 | 118 / 12 |
| P to K (with SUB and EL pass-through) | 268 | LOGIC; ANALOGUE; PRECISION; WIPER | 68 / 19 | 144 / 21 | 241 / 27 | 298 / 30 |

## Ground current: the worst link ground contact carries at most 0.086 A normally and 0.095 A with one post open, inside the lowest rating swept (0.3 A) at both pitches

One link ground path is two contacts and one conductor. The bound gives the candidate path its minimum resistance (conductor minimum, contacts 0 Ω ASSUMED) and no PCB term, and every alternative its maximum and the whole 0.5 mΩ common neck (the partition35 method of the power-post README). Branch current 4.6 A (SOURCED, `single_return_A`). Post joints from `power_posts.py` (JL 0.4045 / JR 0.4045 / P 0.3952 mΩ).

| Pitch | Link ground path, min / max, mΩ |
| --- | --- |
| 1.00 mm | 33.2 / 104.2 (conductor DERIVED, contact max SOURCED) |
| 0.5 mm | 65.3 / 206.4 (conductor DERIVED, contact max SOURCED) |

| Pitch | Branch | AGND posts in place | Worst contact, one ground in the branch, A | Worst contact, rule A grounds per link at the first option (n), A | Smallest grounds per board meeting each rating |
| --- | --- | --- | --- | --- | --- |
| 1.00 mm | JL | 3 (normal) | 0.086 | 0.0850 (62) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 2 (one post open) | 0.095 | 0.0924 (62) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 0 (all posts open) | 4.600 | 0.2869 (62) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | JR | 3 (normal) | 0.086 | 0.0851 (57) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 2 (one post open) | 0.095 | 0.0926 (57) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 0 (all posts open) | 4.600 | 0.3054 (57) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | P | 3 (normal) | 0.086 | 0.0832 (144) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 2 (one post open) | 0.095 | 0.0891 (144) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 0 (all posts open) | 4.600 | 0.1642 (144) | 0.4 A: 41, 0.5 A: 31 |
| 0.5 mm | JL | 3 (normal) | 0.044 | 0.0440 (58) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 2 (one post open) | 0.049 | 0.0482 (58) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 0 (all posts open) | 4.600 | 0.2731 (58) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | JR | 3 (normal) | 0.044 | 0.0440 (53) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 2 (one post open) | 0.049 | 0.0483 (53) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 0 (all posts open) | 4.600 | 0.2947 (53) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | P | 3 (normal) | 0.044 | 0.0434 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 2 (one post open) | 0.049 | 0.0471 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 0 (all posts open) | 4.600 | 0.1401 (134) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |

With any post of the branch in place a single link ground stays far inside every rating, because one link ground path (tens of mΩ) is about a hundred times the post path (under 1 mΩ). So current sets no minimum beyond one ground per link; the coupling rule sets the count. With every AGND post of a branch open (not a design case) the link grounds carry the whole return, and the count in the last column applies.

### The final share at the field positions needs four inputs from the geometry task

- the K-side and front-side field centre of every link and its branch (ST-02 a4 `link-candidate.json`);
- the ground positions of each link after the ruling (count and pin numbers);
- the AGND plane spreading on K and on each front board from each field to the three post lands of its branch (routed planes, or the ASSUMED sheet model of the power-post README);
- the cable length per link (a shorter link lowers its path resistance and raises its share).

## The present harness puts a ground between every two signals in all 195 harnesses and shares 9 class pairs across that one ground (attempt a3, DS-54)

From `partition.json` (harness header pin maps, both ends in the same order: True) with the class rules of `inputs.json`: 127 of 3 contacts, 10 of 7 contacts, 58 of 8 contacts. Signals side by side with no ground between: 0. Signals beside a rail conductor: 6 (EL-E1, EL-E2, EL-E3, EL-E4, EL-E5, EL-E6, all ANALOGUE). Harnesses that start on a ground: 0; that end on one: 56 (the 8-contact pattern S G S G S G S G ends on its fourth ground). DERIVED.

| Class pair across one ground | Triples | Harnesses |
| --- | --- | --- |
| ANALOGUE/ANALOGUE | 172 | 80 |
| ANALOGUE/LOGIC | 2 | 2 |
| ANALOGUE/PRECISION | 39 | 34 |
| ANALOGUE/WIPER | 14 | 14 |
| LOGIC/LOGIC | 17 | 17 |
| LOGIC/PRECISION | 11 | 11 |
| PRECISION/PRECISION | 18 | 18 |
| PRECISION/WIPER | 5 | 5 |
| WIPER/WIPER | 40 | 40 |

The manager's count (DS-54) has ANALOGUE/ANALOGUE at 147 triples in 70 harnesses. The difference, 25 triples in 10 harnesses, is the ten K-to-adapter harnesses K-O1-1 to K-O5-2, whose local nets `OSC_OCT0` to `OSC_OCT5` (kind "buffered signal/reference") fall to ANALOGUE under the fallback rule. NC positions (two on JR-K-27) are not signals here. Every other count matches.

## Against the quietest present harness, a 50 mm flat link with one ground between stays at or below it for every class pair the harness shares (largest ratio 0.80)

Harness geometry: round conductors of 0.4826 mm (SOURCED, Alpha 6821; stranding taken as solid, ASSUMED) at 1.25 mm pitch in a flat lay (SOURCED pitch; spacing along the run ASSUMED), insulation 0.889 mm (SOURCED) with unknown permittivity (ASSUMED sweep), each harness at its own cut length from the loom candidate plus 5 mm per end, the whole length in parallel (ASSUMED upper bound). Same aggressors, victim impedances and equations as attempt a2, both at ε_eff 3.2. Capacitance by charge simulation for round wires (checked against π·ε/acosh(D/2r) in the tests). Every figure is a paper bound (DERIVED from ASSUMED terms); no harness coupling was ever measured.

| Aggressor > victim | Triples | Harness bound, mV: shortest / median / longest cut (mm) | Quietest harness, mV | Flat 1.00 mm, 50 mm: side by side / one ground / two grounds, ratio (dB) | Flat 0.5 mm, 50 mm: same |
| --- | --- | --- | --- | --- | --- |
| ANALOGUE>ANALOGUE | 172 | 1.37 (66) / 1.67 (85) / 8.17 (204) | 0.923 | 4.31 (+12.7) / 0.80 (-1.9) / 0.49 (-6.2) | 3.98 (+12.0) / 0.80 (-1.9) / 0.49 (-6.1) |
| ANALOGUE>LOGIC | 2 | 1.86 (83) / 1.86 (83) / 1.86 (83) | 1.86 | 1.09 (+0.8) / 0.21 (-13.6) / 0.12 (-18.1) | 1.01 (+0.1) / 0.21 (-13.7) / 0.13 (-18.1) |
| ANALOGUE>PRECISION | 39 | 3.55 (83) / 1.67 (85) / 1.67 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| ANALOGUE>WIPER | 14 | 823 (83) / 823 (83) / 823 (83) | 823 | 1.15 (+1.3) / 0.21 (-13.5) / 0.13 (-17.6) | 1.07 (+0.6) / 0.21 (-13.5) / 0.13 (-17.5) |
| LOGIC>ANALOGUE | 2 | 301 (83) / 301 (83) / 301 (83) | 301 | 0.89 (-1.0) / 0.20 (-14.0) / 0.10 (-20.0) | 0.85 (-1.4) / 0.20 (-14.0) / 0.10 (-19.9) |
| LOGIC>LOGIC | 17 | 218 (83) / 218 (83) / 218 (83) | 218 | 0.79 (-2.0) / 0.19 (-14.3) / 0.09 (-21.1) | 0.76 (-2.3) / 0.20 (-14.2) / 0.09 (-21.0) |
| LOGIC>PRECISION | 11 | 301 (83) / 301 (83) / 301 (83) | 301 | 0.89 (-1.0) / 0.20 (-14.0) / 0.10 (-20.0) | 0.85 (-1.4) / 0.20 (-14.0) / 0.10 (-19.9) |
| PRECISION>ANALOGUE | 39 | 3.55 (83) / 1.67 (85) / 1.67 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| PRECISION>LOGIC | 11 | 1.86 (83) / 1.86 (83) / 1.86 (83) | 1.86 | 1.09 (+0.8) / 0.21 (-13.6) / 0.12 (-18.1) | 1.01 (+0.1) / 0.21 (-13.7) / 0.13 (-18.1) |
| PRECISION>PRECISION | 18 | 3.55 (83) / 3.55 (83) / 1.17 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| PRECISION>WIPER | 5 | 823 (83) / 823 (83) / 823 (83) | 823 | 1.15 (+1.3) / 0.21 (-13.5) / 0.13 (-17.6) | 1.07 (+0.6) / 0.21 (-13.5) / 0.13 (-17.5) |

Ratio = flat-link bound over the quietest harness instance of the same directed pair (ratio ≤ 1 keeps the flat link at or below every present harness). Rule B (grounds on every side) is in `harness-baseline.json`; it is within a few per cent of rule A here. The ratio barely depends on ε_eff because both sides use the same value, and the logic rows are dominated by the inductive term, which ε does not touch.

### The harness rule: one ground between every two signals, except LOGIC/LOGIC, WIPER/WIPER side by side; LOGIC/WIPER never in one cable

Same rule at both pitches: True. A class pair the harness never places across one ground (LOGIC/WIPER) has no harness level to match, so it stays in separate cables, as in the harness. WIPER/WIPER is side by side because wipers are STATIC aggressors; LOGIC/LOGIC because the flat side-by-side bound is below the quietest LOGIC/LOGIC harness.

| Pitch | Circuits | Harness rule, grounds / links | Attempt a2 rule (absolute limits) | Rule A | Rule B inner only (as the harness) | Rule B with outer grounds |
| --- | --- | --- | --- | --- | --- | --- |
| 1.00 mm | 20 | 384 / 47 | 109 / 34 | 264 / 40 | 440 / 50 | 546 / 56 |
| 1.00 mm | 22 | 379 / 42 | 107 / 32 | 245 / 38 | 443 / 47 | 541 / 50 |
| 0.5 mm | 30 | 368 / 31 | 100 / 25 | 245 / 26 | 455 / 35 | 528 / 38 |
| 0.5 mm | 40 | 361 / 24 | 94 / 19 | 245 / 21 | 464 / 26 | 518 / 28 |

Cable groups per joint under the harness rule: JL to K: ANALOGUE + PRECISION; JL to P through K: ANALOGUE; JR to K: ANALOGUE + PRECISION; P to K (with SUB and EL pass-through): LOGIC + ANALOGUE + PRECISION | WIPER. Same counting method and lower-bound caveat as attempt a2.

### What the comparison shows, and what it does not

It shows that, on the same equations and ASSUMED drive and impedance terms, a 50 mm flat link with one ground conductor between two signals couples less than the 66 to 204 mm GH harnesses that carry the same class pairs today, mainly because it is shorter and its return sits closer. It does not show that either is good enough: the present harness is an unvalidated draft too, its coupling was never computed before nor measured, and the absolute limits of attempt a2 (PRECISION 1 mV, WIPER 1 mV, ANALOGUE 10 mV, LOGIC 500 mV peak) would fail many harness instances as well. Those limits stay ASSUMED criteria for the ruling; no verdict on them is given here (NEEDS_DESIGN).

## Checks: calculator and tests run; every measurement and native check NOT RUN

- **Run:** this calculator twice with a clean `git status`; `python3 scripts/checks/frozen_studies.py discover scripts/stack/link_electrical`; `pnpm circuit:check` before and after.
- **NOT RUN, crosstalk, current share and resistance measurements:** no cable, connector or board exists.
- **NOT RUN, field solver for the real laminate:** the permittivity of the LX cable is not on its drawing; the homogeneous model is bracketed by the ε_eff sweep.
- **NOT RUN, connector contact coupling:** no connector coupling data is retained; covered only by the ASSUMED end length.
- **NOT RUN, ground share at the field positions:** waits for ST-02 a4 and the ruling.
- **NOT RUN, KiCad, DRC and `regen-all.sh`:** no board is changed.
- **NOT RUN, harness coupling measurement and a field solver for the insulated wire bundle:** no harness is built; the wire permittivity is not on the Alpha sheet.
