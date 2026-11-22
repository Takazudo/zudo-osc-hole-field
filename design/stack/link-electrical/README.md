# Flat-link electrical bounds: ST-04 attempts a2 to a4 (paper; DS-41 checks 3 and 4 without positions, harness baseline DS-54, DS-62 table; gate checks 3 and 4 on the record of the room study)

Task `osc-stack-20261114/ST-04 attempt a2 (DS-41 checks 3 and 4 without positions; DS-48, DS-51)`, launch commit `21d1cd9`. **Status: unvalidated paper bound.** Coupling, current share and resistance are NOT RUN as measurements; nothing is selected, adopted or bought. Every class, impedance, edge rate and limit below is ASSUMED unless a row says otherwise, and the limits are criteria for the design ruling (NEEDS_DESIGN).

This file, `results.json`, `harness-baseline.json` and `ds62-table.json` are written by `python3 scripts/stack/link_electrical/link_electrical.py` from [`inputs.json`](inputs.json); the tests fail if any differs from a fresh run. Status words: SOURCED (file and locator in `inputs.json`), DERIVED (formula below), ASSUMED (reason in `inputs.json`), NOT RUN (reason given).

## 510 link signals in four coupling classes, the count of ST-02's room study (510)

Every K pair of the retained candidate except the six adapter pairs, with rail, AGND and NC positions removed (as `NON_SIGNAL` in `scripts/stack/geometry/links.py`): 531 K-pair signals less 21 on the adapter pairs = 510; 2 NC positions on link pairs are not signals. The class comes from the partition's signal kind and the net name (`inputs.json` → `classes`, ASSUMED). Four planning nets of the SUB pairs (`O2:SUB_SEL_A` etc.) are not in the partition harnesses and are taken as LOGIC.

| Joint | PRECISION | WIPER | ANALOGUE | LOGIC | Total |
| --- | --- | --- | --- | --- | --- |
| JL to K | 12 | 0 | 96 | 0 | 108 |
| JL to P through K | 0 | 0 | 16 | 0 | 16 |
| JR to K | 16 | 0 | 102 | 0 | 118 |
| P to K (with SUB and EL pass-through) | 50 | 99 | 68 | 51 | 268 |
| **Total** | 78 | 99 | 282 | 51 | 510 |

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

## The a2 class rule needs 94 to 111 grounds for the 510 signals; counted per link, rule A needs 255 to 275, rule B 458 to 483 without outer grounds and 539 to 569 with them

Own class rule, per joint and option, with free ordering inside a joint: classes in blocks, a ground between same-class neighbours only where the class pair needs one, one ground between blocks that share a cable, one ground per link (at a cable edge; no other outer grounds), and class pairs that may not share a cable put in cables of their own. A lower bound: the class mix per link follows the clustering of ST-02 a4. DS-51 rules are counted per link with the capacities of the room study (links filled to capacity per joint): rule A one ground per two signals; rule B read without outer grounds (s − 1 grounds per link, the room study's reading and the present harness pattern) and with them (s + 1). Filling every link to capacity per joint gives fewer links than the room study's clustering, which also respects site distances.

| Pitch | Circuits | Own rule, grounds / links | Rule A, signals per link: grounds / links | Rule B inner only, signals per link: grounds / links | Rule B with outer grounds, signals per link: grounds / links |
| --- | --- | --- | --- | --- | --- |
| 1.00 mm | 20 | 111 / 36 | 13: 275 / 42 | 10: 458 / 52 | 9: 569 / 58 |
| 1.00 mm | 22 | 107 / 32 | 14: 255 / 39 | 11: 462 / 48 | 10: 562 / 52 |
| 0.5 mm | 30 | 100 / 25 | 20: 255 / 27 | 15: 474 / 36 | 14: 549 / 39 |
| 0.5 mm | 40 | 94 / 19 | 26: 255 / 22 | 20: 483 / 27 | 19: 539 / 29 |

Per joint at 1.00 mm, 20 circuits (the other options in `results.json`):

| Joint | Signals | Cable groups | Own rule | Rule A | Rule B inner | Rule B outer |
| --- | --- | --- | --- | --- | --- | --- |
| JL to K | 108 | ANALOGUE; PRECISION | 19 / 8 | 58 / 9 | 97 / 11 | 121 / 12 |
| JL to P through K | 16 | ANALOGUE | 1 / 1 | 9 / 2 | 14 / 2 | 18 / 2 |
| JR to K | 118 | ANALOGUE; PRECISION | 23 / 8 | 64 / 10 | 106 / 12 | 132 / 14 |
| P to K (with SUB and EL pass-through) | 268 | LOGIC; ANALOGUE; PRECISION; WIPER | 68 / 19 | 144 / 21 | 241 / 27 | 298 / 30 |

## Ground current: the worst link ground contact carries at most 0.086 A normally and 0.095 A with one post open, inside the lowest rating swept (0.3 A) at both pitches

One link ground path is two contacts and one conductor. The bound gives the candidate path its minimum resistance (conductor minimum, contacts 0 Ω ASSUMED) and no PCB term, and every alternative its maximum and the whole 0.5 mΩ common neck (the partition35 method of the power-post README). Branch current 4.6 A (SOURCED, `single_return_A`). Post joints from `power_posts.py` (JL 0.4045 / JR 0.4045 / P 0.3952 mΩ).

| Pitch | Link ground path, min / max, mΩ |
| --- | --- |
| 1.00 mm | 33.2 / 104.2 (conductor DERIVED, contact max SOURCED) |
| 0.5 mm | 65.3 / 206.4 (conductor DERIVED, contact max SOURCED) |

| Pitch | Branch | AGND posts in place | Worst contact, one ground in the branch, A | Worst contact, rule A grounds per link at the first option (n), A | Smallest grounds per board meeting each rating |
| --- | --- | --- | --- | --- | --- |
| 1.00 mm | JL | 3 (normal) | 0.086 | 0.0849 (67) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 2 (one post open) | 0.095 | 0.0922 (67) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 0 (all posts open) | 4.600 | 0.2711 (67) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | JR | 3 (normal) | 0.086 | 0.0850 (64) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 2 (one post open) | 0.095 | 0.0924 (64) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 0 (all posts open) | 4.600 | 0.2803 (64) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | P | 3 (normal) | 0.086 | 0.0832 (144) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 2 (one post open) | 0.095 | 0.0891 (144) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 0 (all posts open) | 4.600 | 0.1642 (144) | 0.4 A: 41, 0.5 A: 31 |
| 0.5 mm | JL | 3 (normal) | 0.044 | 0.0439 (62) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 2 (one post open) | 0.049 | 0.0482 (62) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 0 (all posts open) | 4.600 | 0.2582 (62) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | JR | 3 (normal) | 0.044 | 0.0439 (59) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 2 (one post open) | 0.049 | 0.0482 (59) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 0 (all posts open) | 4.600 | 0.2692 (59) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | P | 3 (normal) | 0.044 | 0.0434 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 2 (one post open) | 0.049 | 0.0471 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 0 (all posts open) | 4.600 | 0.1401 (134) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |

With any post of the branch in place a single link ground stays far inside every rating, because one link ground path (tens of mΩ) is about a hundred times the post path (under 1 mΩ). So current sets no minimum beyond one ground per link; the coupling rule sets the count. With every AGND post of a branch open (not a design case) the link grounds carry the whole return, and the count in the last column applies.

### The final share at the field positions needs four inputs from the geometry task

- the K-side and front-side field centre of every link and its branch (ST-02 a4 `link-candidate.json`);
- the ground positions of each link after the ruling (count and pin numbers);
- the AGND plane spreading on K and on each front board from each field to the three post lands of its branch (routed planes, or the ASSUMED sheet model of the power-post README);
- the cable length per link (a shorter link lowers its path resistance and raises its share).

## The present harness puts a ground between every two signals in all 200 harnesses and shares 9 class pairs across that one ground (attempt a3, DS-54)

From `partition.json` (harness header pin maps, both ends in the same order: True) with the class rules of `inputs.json`: 127 of 3 contacts, 10 of 7 contacts, 63 of 8 contacts. Signals side by side with no ground between: 0. Signals beside a rail conductor: 6 (EL-E1, EL-E2, EL-E3, EL-E4, EL-E5, EL-E6, all ANALOGUE). Harnesses that start on a ground: 0; that end on one: 61 (the 8-contact pattern S G S G S G S G ends on its fourth ground). DERIVED.

| Class pair across one ground | Triples | Harnesses |
| --- | --- | --- |
| ANALOGUE/ANALOGUE | 187 | 85 |
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

| Aggressor > victim | Directed cases | Harness bound, mV: shortest / median / longest cut (mm) | Quietest harness, mV | Flat 1.00 mm, 50 mm: side by side / one ground / two grounds, ratio (dB) | Flat 0.5 mm, 50 mm: same |
| --- | --- | --- | --- | --- | --- |
| ANALOGUE>ANALOGUE | 374 | 1.37 (66) / 1.12 (85) / 8.17 (204) | 0.923 | 4.31 (+12.7) / 0.80 (-1.9) / 0.49 (-6.2) | 3.98 (+12.0) / 0.80 (-1.9) / 0.49 (-6.1) |
| ANALOGUE>LOGIC | 2 | 1.86 (83) / 1.86 (83) / 1.86 (83) | 1.86 | 1.09 (+0.8) / 0.21 (-13.6) / 0.12 (-18.1) | 1.01 (+0.1) / 0.21 (-13.7) / 0.13 (-18.1) |
| ANALOGUE>PRECISION | 39 | 3.55 (83) / 1.67 (85) / 1.67 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| ANALOGUE>WIPER | 14 | 823 (83) / 823 (83) / 823 (83) | 823 | 1.15 (+1.3) / 0.21 (-13.5) / 0.13 (-17.6) | 1.07 (+0.6) / 0.21 (-13.5) / 0.13 (-17.5) |
| LOGIC>ANALOGUE | 2 | 301 (83) / 301 (83) / 301 (83) | 301 | 0.89 (-1.0) / 0.20 (-14.0) / 0.10 (-20.0) | 0.85 (-1.4) / 0.20 (-14.0) / 0.10 (-19.9) |
| LOGIC>LOGIC | 34 | 218 (83) / 218 (83) / 218 (83) | 218 | 0.79 (-2.0) / 0.19 (-14.3) / 0.09 (-21.1) | 0.76 (-2.3) / 0.20 (-14.2) / 0.09 (-21.0) |
| LOGIC>PRECISION | 11 | 301 (83) / 301 (83) / 301 (83) | 301 | 0.89 (-1.0) / 0.20 (-14.0) / 0.10 (-20.0) | 0.85 (-1.4) / 0.20 (-14.0) / 0.10 (-19.9) |
| PRECISION>ANALOGUE | 39 | 3.55 (83) / 1.67 (85) / 1.67 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| PRECISION>LOGIC | 11 | 1.86 (83) / 1.86 (83) / 1.86 (83) | 1.86 | 1.09 (+0.8) / 0.21 (-13.6) / 0.12 (-18.1) | 1.01 (+0.1) / 0.21 (-13.7) / 0.13 (-18.1) |
| PRECISION>PRECISION | 36 | 3.55 (83) / 3.55 (83) / 1.17 (85) | 1.12 | 3.57 (+11.0) / 0.67 (-3.5) / 0.41 (-7.8) | 3.30 (+10.4) / 0.66 (-3.6) / 0.41 (-7.8) |
| PRECISION>WIPER | 5 | 823 (83) / 823 (83) / 823 (83) | 823 | 1.15 (+1.3) / 0.21 (-13.5) / 0.13 (-17.6) | 1.07 (+0.6) / 0.21 (-13.5) / 0.13 (-17.5) |

Ratio = flat-link bound over the quietest harness instance of the same directed pair (ratio ≤ 1 keeps the flat link at or below every present harness). Rule B (grounds on every side) is in `harness-baseline.json`; it is within a few per cent of rule A here. The ratio barely depends on ε_eff because both sides use the same value, and the logic rows are dominated by the inductive term, which ε does not touch.

### The harness rule: one ground between every two signals, except LOGIC/LOGIC, WIPER/WIPER side by side; LOGIC/WIPER never in one cable

Same rule at both pitches: True. A class pair the harness never places across one ground (LOGIC/WIPER) has no harness level to match, so it stays in separate cables, as in the harness. WIPER/WIPER is side by side because wipers are STATIC aggressors; LOGIC/LOGIC because the flat side-by-side bound is below the quietest LOGIC/LOGIC harness.

| Pitch | Circuits | Harness rule, grounds / links | Attempt a2 rule (absolute limits) | Rule A | Rule B inner only (as the harness) | Rule B with outer grounds |
| --- | --- | --- | --- | --- | --- | --- |
| 1.00 mm | 20 | 406 / 49 | 111 / 36 | 275 / 42 | 458 / 52 | 569 / 58 |
| 1.00 mm | 22 | 401 / 44 | 107 / 32 | 255 / 39 | 462 / 48 | 562 / 52 |
| 0.5 mm | 30 | 390 / 33 | 100 / 25 | 255 / 27 | 474 / 36 | 549 / 39 |
| 0.5 mm | 40 | 382 / 25 | 94 / 19 | 255 / 22 | 483 / 27 | 539 / 29 |

Cable groups per joint under the harness rule: JL to K: ANALOGUE + PRECISION; JL to P through K: ANALOGUE; JR to K: ANALOGUE + PRECISION; P to K (with SUB and EL pass-through): LOGIC + ANALOGUE + PRECISION | WIPER. Same counting method and lower-bound caveat as attempt a2.

### What the comparison shows, and what it does not

It shows that, on the same equations and ASSUMED drive and impedance terms, a 50 mm flat link with one ground conductor between two signals couples less than the 66 to 204 mm GH harnesses that carry the same class pairs today, mainly because it is shorter and its return sits closer. It does not show that either is good enough: the present harness is an unvalidated draft too, its coupling was never computed before nor measured, and the absolute limits of attempt a2 (PRECISION 1 mV, WIPER 1 mV, ANALOGUE 10 mV, LOGIC 500 mV peak) would fail many harness instances as well. Those limits stay ASSUMED criteria for the ruling; no verdict on them is given here (NEEDS_DESIGN).

## The seven lines of each adapter are static: 8 circuits, seven signals side by side and one ground (attempt a4, part 1, DS-64)

From the retained schematic specification (`inputs.json` → `ds62.adapter_evidence`, each with its file and object):

- OSC_OCT0 to OSC_OCT5 are six buffered taps of one shared octave ladder fed from the 5 V reference; they are global references shared by all oscillators. Source: design/spec/modules/oscillator.py, octave_family() (b.cell octave_reference with REF_5V OSC_REF5 and OCT0..OCT5 -> OSC_OCT0..5) and REFS (line 16); design/spec/cells/build_doc.py octave_reference: buffered endpoints, five 10k resistors, six buffered octave taps (SOURCED).
- each tap is driven by an OPA4197 voltage follower (U1602 to U1604); the ladder is fed by REF5050 U1601; source impedance is the closed-loop output impedance of the follower, not stated as a number (UNSOURCED); the 100 Ohm victim value of PRECISION is kept. Source: schematic/sheets/octave_reference.kicad_sch symbols U1601 REF5050AIDR, U1602..U1604 OPA4197IDR; design/architecture-278/implementation/candidate-netlist.json endpoints U1602 pins 13/14 OSC_OCT0, U1603 pins 1/2, 6/7, 8/9, 13/14 OSC_OCT1..4, U1604 pins 1/2 OSC_OCT5 (output tied to inverting input) (SOURCED (driver); UNSOURCED (impedance figure)).
- OCT_SELECTED is the common of the hand-turned octave selector SRBV160803 (pins 1 and 10), whose positions 2 to 7 take OSC_OCT0 to OSC_OCT5; it is received through OCT_SER 1 kOhm into OCT_FILTER (100 nF and OCT_PD 10 MOhm to AGND), rebuffered by the precision amplifier OCT_RECEIVER to OCT_CV, which enters EXPO_SUM through PITCH_OCT 100 kOhm. Source: design/spec/modules/oscillator.py, family(): pins dict and b.device(SRBV160803, OCT_SELECTOR), b.r(OCT_SER), b.r(OCT_PD), b.c(OCT_FILTER), b.amp(OCT_RECEIVER, precision), PITCH_OCT 100 kOhm (lines 168 to 176) (SOURCED).
- nothing on the seven lines is modulated, clocked or switched while the instrument plays; OCT_SELECTED steps only when the selector is turned by hand; the taps never change. Source: the same objects: no modulation, clock or switch other than the panel selector connects to OSC_OCT0..5 or OCT_SELECTED (DERIVED).

Class for DS-62: STATIC for all 21 adapter signals (`inputs.json` → `classes_adapter`, beside the unchanged `classes.rules`). STATIC exerts nothing while the instrument plays, so two static lines need no ground between them; as victims they are PRECISION, because they set the pitch.

| Order | Circuits | Order (circuit 1 first) | Grounds |
| --- | --- | --- | --- |
| part 1 order | 8 | OCT_SELECTED, OSC_OCT0, OSC_OCT1, OSC_OCT2, OSC_OCT3, OSC_OCT4, OSC_OCT5, AGND | 1 |
| DS-79 order | 8 | OSC_OCT0, OSC_OCT1, OSC_OCT2, OSC_OCT3, OSC_OCT4, OSC_OCT5, AGND, OCT_SELECTED | 1 |
| 14 circuits, a ground after each line | 14 | OCT_SELECTED, AGND, OSC_OCT0, AGND, OSC_OCT1, AGND, OSC_OCT2, AGND, OSC_OCT3, AGND, OSC_OCT4, AGND, OSC_OCT5, AGND | 7 |

### One selector step couples 25.3 mV peak and 0.74 µV filtered into the worst tap on the DS-79 order at 40 mm (30.3 mV and 0.887 µV on the 50 mm fallback); it stays outside the criterion

A step of 1 V on OCT_SELECTED with a 5 ns edge into the 1000 Ω receiver (terms in `inputs.json` → `ds62.selector_step`), victim every tap at the PRECISION impedance and the worst one shown, every conductor of the cable in the solve. The filtered figure is the spike's area over the receiver's 100 µs filter (V·R·Cm + M·ΔI, DERIVED), i.e. what reaches OCT_CV of an oscillator whose selector sits on the struck tap. It happens only during a hand turn, when the pitch changes by an octave anyway, so it does not enter the DS-62 criterion (DS-79). Each order is computed on every cable in use for its size, so 8 and 14 circuits compare at the same 50 mm.

| Order | Cable | Length, mm | Worst tap (position) | Peak, mV | Filtered, µV | Ratio to the quietest present adapter harness (peak / filtered) |
| --- | --- | --- | --- | --- | --- | --- |
| part 1 order | C81339 | 40 | OSC_OCT0 (2) | 100 | 3.36 | 5.07 / 4.04 |
| part 1 order | C29534 | 50 | OSC_OCT0 (2) | 120 | 4.04 | 6.09 / 4.86 |
| DS-79 order | C81339 | 40 | OSC_OCT0 (1) | 25.3 | 0.74 | 1.28 / 0.89 |
| DS-79 order | C29534 | 50 | OSC_OCT0 (1) | 30.3 | 0.887 | 1.53 / 1.07 |
| 14 circuits, a ground after each line | C68390 | 50 | OSC_OCT0 (3) | 13.7 | 0.577 | 0.69 / 0.69 |
| Present harness K-O2-1 (one ground between) | loom | 66 | | 19.8 | 0.831 | 1 |

## DS-62 at the lengths in use (NEEDS_DESIGN): the largest ratio is 0.90 at 40 mm, 1.08 at 50 mm, 1.17 at 60 mm; 3 pair-and-cable rows are above 1.0

0.5 mm pitch, ε_eff 3.2 on both sides, each cable at its own length and size (`inputs.json` → `ds62.cables`), on the DS-62 link pattern (S G S G …, no outer ground); each bound is the worse of the pair at the cable edge and in the middle, with every conductor of the cable in the solve. Reference: the quietest present harness of the same directed pair, with the adapter lines STATIC, so the adapter harnesses no longer count as ANALOGUE/ANALOGUE.

Reference changes against attempt a3: ANALOGUE>ANALOGUE 0.923 → 1.12 mV.

| Aggressor > victim | Lies | C81339 (8, 40 mm) | C26618 (40, 50 mm) | C68390 (14, 50 mm) | C29534 (8, 50 mm) | C32128 (26, 60 mm) |
| --- | --- | --- | --- | --- | --- | --- | 
| ANALOGUE>ANALOGUE | across one ground | 0.77 (-2.3 dB) | 0.83 (-1.6 dB) | 0.86 (-1.3 dB) | 0.92 (-0.7 dB) | 0.98 (-0.2 dB) |
| ANALOGUE>LOGIC | across one ground | 0.24 (-12.5 dB) | 0.26 (-11.9 dB) | 0.27 (-11.5 dB) | 0.28 (-10.9 dB) | 0.30 (-10.4 dB) |
| ANALOGUE>PRECISION | across one ground | 0.77 (-2.3 dB) | 0.83 (-1.6 dB) | 0.86 (-1.3 dB) | 0.92 (-0.7 dB) | 0.98 (-0.2 dB) |
| ANALOGUE>WIPER | across one ground | 0.25 (-12.0 dB) | 0.27 (-11.4 dB) | 0.28 (-11.0 dB) | 0.30 (-10.5 dB) | 0.32 (-10.0 dB) |
| LOGIC>ANALOGUE | across one ground | 0.20 (-13.8 dB) | 0.22 (-13.3 dB) | 0.23 (-12.8 dB) | 0.25 (-12.2 dB) | 0.26 (-11.8 dB) |
| LOGIC>LOGIC | side by side | 0.90 (-0.9 dB) | 0.99 (-0.1 dB) | 1.03 (+0.2 dB) | 1.08 (+0.7 dB) | 1.17 (+1.3 dB) |
| LOGIC>PRECISION | across one ground | 0.20 (-13.8 dB) | 0.22 (-13.3 dB) | 0.23 (-12.8 dB) | 0.25 (-12.2 dB) | 0.26 (-11.8 dB) |
| PRECISION>ANALOGUE | across one ground | 0.77 (-2.3 dB) | 0.83 (-1.6 dB) | 0.86 (-1.3 dB) | 0.92 (-0.7 dB) | 0.98 (-0.2 dB) |
| PRECISION>LOGIC | across one ground | 0.24 (-12.5 dB) | 0.26 (-11.9 dB) | 0.27 (-11.5 dB) | 0.28 (-10.9 dB) | 0.30 (-10.4 dB) |
| PRECISION>PRECISION | across one ground | 0.77 (-2.3 dB) | 0.83 (-1.6 dB) | 0.86 (-1.3 dB) | 0.92 (-0.7 dB) | 0.98 (-0.2 dB) |
| PRECISION>WIPER | across one ground | 0.25 (-12.0 dB) | 0.27 (-11.4 dB) | 0.28 (-11.0 dB) | 0.30 (-10.5 dB) | 0.32 (-10.0 dB) |

Rows above 1.0, with the ratio at the cable edge and in the middle of the link:

| Cable | Length, mm | Aggressor > victim | Lies | Edge | Middle |
| --- | --- | --- | --- | --- | --- |
| C68390 | 50 | LOGIC>LOGIC | side by side | 1.03 | 0.71 |
| C29534 | 50 | LOGIC>LOGIC | side by side | 1.08 | 0.75 |
| C32128 | 60 | LOGIC>LOGIC | side by side | 1.17 | 0.82 |

Worst row: LOGIC>LOGIC on C32128 at 60 mm, edge, 255 mV against 218 mV. WIPER>WIPER and STATIC pairs exert nothing and are left out; LOGIC/WIPER may not share a cable (DS-62). Every figure is a paper bound; the harness was never measured either.

## Gate check 4 on the record of the room study (DONE): the largest ratio of the 62 links is 0.98 on P-K-P-L03.01; 0 links read above 1.0 (attempt a4, part 2, DS-77)

Record: `design/stack/geometry/links/link-gate.json` (ST-02 a8 part 2, DS-110), read only and pinned by the hash of a projection of what is read (`inputs.json` → `link_record.projection_sha256`). Each link is solved at its actual order on its actual cable, every conductor in the 2-D solve, every ground and unused position at AGND (DS-77), every other signal held by its driver. Every directed pair whose aggressor class has an aggressor term is evaluated, not only neighbours, against the quietest present harness of the same pair of classes (the references of part 1). The ratio of a link is its largest pair.

Every pair of classes that shares a link has a reference.

| Cable | Links | Largest ratio | Link |
| --- | --- | --- | --- |
| C26618 (40, 50 mm) | 19 | 0.83 | P-K-P-L08 |
| C29534 (8, 50 mm) | 28 | 0.93 | P-K-P-L10.01.01.01 |
| C32128 (26, 60 mm) | 3 | 0.98 | P-K-P-L03.01 |
| C68390 (14, 50 mm) | 9 | 0.87 | P-K-P-L06.01.01 |

### Links above 0.8, with their largest pair

| Link | Cable | Ratio | Largest pair | Host of riders (ratio without them) |
| --- | --- | --- | --- | --- |
| P-K-P-L03.01 | C32128 | 0.978 | PRECISION>ANALOGUE: /E1/REF5 (pos 3) on /E1/ENV_BUFFER (pos 1), across one ground | no |
| P-K-P-L06.02 | C32128 | 0.978 | PRECISION>PRECISION: /O3/LOCAL_REF5 (pos 3) on /O1/LOCAL_REF5 (pos 1), across one ground | no |
| P-K-P-L10.02 | C32128 | 0.978 | PRECISION>ANALOGUE: /F1/FREQ_REMOTE (pos 3) on /F1/GAIN_REMOTE (pos 1), across one ground | yes (0.98) |
| P-K-P-L10.01.01.01 | C29534 | 0.931 | PRECISION>ANALOGUE: /O4/RANGE_CV (pos 6) on /O4/PWM_REMOTE (pos 8), across one ground | no |
| P-K-P-L11.01.02.01 | C29534 | 0.931 | ANALOGUE>ANALOGUE: /M5A/1_REMOTE (pos 6) on /M5A/2_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L12.01.01.02 | C29534 | 0.931 | PRECISION>ANALOGUE: /F2/FREQ_REMOTE (pos 6) on /F2/GAIN_REMOTE (pos 8), across one ground | no |
| P-K-P-L13.01.02.01 | C29534 | 0.931 | ANALOGUE>ANALOGUE: /M5B/1_REMOTE (pos 6) on /M5B/2_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L15.01.01.01 | C29534 | 0.931 | PRECISION>ANALOGUE: /A03/REFN5 (pos 6) on /A04/IN_REMOTE (pos 8), across one ground | no |
| P-K-P-L15.01.01.02 | C29534 | 0.931 | ANALOGUE>ANALOGUE: /M4A/ATTEN_REMOTE (pos 6) on /M4B/ATTEN_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L04.01.01.01 | C29534 | 0.923 | PRECISION>ANALOGUE: /A01/REFN5 (pos 6) on /A01/IN_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L04.01.01.02 | C29534 | 0.923 | PRECISION>ANALOGUE: /A02/REFN5 (pos 6) on /A02/IN_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L04.02.01.01 | C29534 | 0.923 | PRECISION>PRECISION: /A03/REF5 (pos 6) on /A04/REFN5 (pos 8), across one ground; /A03/REF5 rides from P-K-P-L04.01.02.02 | yes (0.36) |
| P-K-P-L12.02.01.01 | C29534 | 0.923 | ANALOGUE>ANALOGUE: /M5A/3_REMOTE (pos 6) on /M5A/4_REMOTE (pos 8), across one ground | yes (0.92) |
| P-K-P-L14.01.02.02 | C29534 | 0.923 | ANALOGUE>ANALOGUE: /M5B/5_REMOTE (pos 6) on /W1/FOLD_REMOTE (pos 8), across one ground; /M5B/5_REMOTE rides from P-K-P-L14.01.01.01 | yes (0.36) |
| P-K-P-L04.02.01.02 | C29534 | 0.920 | PRECISION>ANALOGUE: /A06/REF5 (pos 3) on /A05/IN_REMOTE (pos 1), across one ground | no |
| P-K-P-L13.01.01.02 | C29534 | 0.920 | PRECISION>ANALOGUE: /F3/REF5 (pos 3) on /F3/RES_REMOTE (pos 1), across one ground | yes (0.92) |
| P-K-P-L14.01.02.01 | C29534 | 0.920 | PRECISION>ANALOGUE: /W2/REF5 (pos 3) on /W2/FOLD_REMOTE (pos 1), across one ground | no |
| P-K-P-L15.01.02.01 | C29534 | 0.920 | ANALOGUE>ANALOGUE: /M4B/3_REMOTE (pos 3) on /M4A/3_REMOTE (pos 1), across one ground | no |
| JL-P-K-P-L01.01.01.01 | C29534 | 0.920 | ANALOGUE>ANALOGUE: /X1/A_BUFFER (pos 3) on /H1/SLEW_BUFFERED (pos 1), across one ground | no |
| JL-P-K-P-L01.01.01.02 | C29534 | 0.920 | ANALOGUE>ANALOGUE: /X2/B_BUFFER (pos 3) on /X1/SELECTOR_REMOTE (pos 1), across one ground; /X2/B_BUFFER rides from JL-P-K-P-L01.01.02.01 | yes (0.30) |
| P-K-P-L06.01.01 | C68390 | 0.868 | PRECISION>ANALOGUE: /O2/LOCAL_REFN5 (pos 12) on /O1/FM_REMOTE (pos 14), across one ground | no |
| P-K-P-L03.02.01 | C68390 | 0.867 | PRECISION>ANALOGUE: /E5/REF5 (pos 3) on /H1/RAW_HELD (pos 1), across one ground | yes (0.87) |
| P-K-P-L01.02.01 | C68390 | 0.866 | PRECISION>ANALOGUE: /E4/REF5 (pos 3) on /E4/ENV_BUFFER (pos 1), across one ground | no |
| P-K-P-L01.01.02 | C68390 | 0.865 | ANALOGUE>ANALOGUE: /E5/NOT_FALL (pos 3) on /E5/ENV_BUFFER (pos 1), across one ground | no |
| P-K-P-L01.01.01 | C68390 | 0.839 | LOGIC>LOGIC: /E4/ASR_RAW (pos 4) on /E3/LOOP_RAW (pos 3), side by side | no |
| P-K-P-L08 | C26618 | 0.829 | PRECISION>ANALOGUE: /O3/RANGE_CV (pos 3) on /O3/PWM_REMOTE (pos 1), across one ground | no |
| JR-K-JR-L01 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /M4A/C2169e5_LED_K (pos 3) on /E3/Ce82060_DRIVE (pos 1), across one ground | no |
| JR-K-JR-L02 | C26618 | 0.829 | PRECISION>ANALOGUE: /A01/REF5 (pos 3) on /A01/IN_BUFFER (pos 1), across one ground | no |
| JR-K-JR-L06 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /E5/BIP_CORE (pos 3) on /E4/SIG_BUFFER (pos 1), across one ground | no |
| P-K-P-L07 | C26618 | 0.829 | PRECISION>ANALOGUE: /O1/LFO_REF (pos 3) on /O1/PWM_REMOTE (pos 1), across one ground | no |
| JR-K-JR-L05 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /M4A/2_BUFFER (pos 3) on /M4A/1_BUFFER (pos 1), across one ground | no |
| JL-K-JL-L01 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /F3/LP_CORE (pos 3) on /F3/HP_CORE (pos 1), across one ground | no |
| JL-K-JL-L02 | C26618 | 0.829 | PRECISION>ANALOGUE: /O1/1V_BUFFER (pos 3) on /O1/FM_BUFFER (pos 1), across one ground | no |
| JL-K-JL-L03 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /O4/SYNC_BUFFER (pos 3) on /O4/Cc66d82_DRIVE (pos 1), across one ground | no |
| JL-K-JL-L05 | C26618 | 0.829 | PRECISION>ANALOGUE: /F1/FREQ_BUFFER (pos 3) on /F1/BP_CORE (pos 1), across one ground | no |
| JL-K-JL-L07 | C26618 | 0.829 | PRECISION>ANALOGUE: /M5A/REF5 (pos 3) on /M5A/5_BUFFER (pos 1), across one ground | no |
| JR-K-JR-L03 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /E2/SIG_BUFFER (pos 3) on /E2/FALL_BUFFER (pos 1), across one ground | no |
| JL-K-JL-L04 | C26618 | 0.829 | PRECISION>ANALOGUE: /O3/1V_BUFFER (pos 3) on /O3/FM_BUFFER (pos 1), across one ground | no |
| JR-K-JR-L04 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /E2/ENV_BUFFER (pos 3) on /E1/STAGE_HIGH (pos 1), across one ground | no |
| JR-K-JR-L07 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /E6/SIG_BUFFER (pos 3) on /E6/FALL_BUFFER (pos 1), across one ground | no |
| JL-K-JL-L09 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /F1/Cb3d4a2_LED_A (pos 3) on /F1/C9fcdd2_LED_A (pos 1), across one ground | no |
| JL-P-K-JL-L01 | C26618 | 0.829 | ANALOGUE>ANALOGUE: /X1/A_BUFFER (pos 3) on /H1/SLEW_BUFFERED (pos 1), across one ground | no |
| JL-K-JL-L06 | C26618 | 0.828 | PRECISION>ANALOGUE: /F3/FREQ_BUFFER (pos 3) on /F3/BP_CORE (pos 1), across one ground | no |
| JL-K-JL-L08 | C26618 | 0.828 | PRECISION>ANALOGUE: /M5B/REF5 (pos 3) on /M5B/SUM_POSTLEVEL (pos 1), across one ground | no |

### 22 hosts carry 45 riders; none reads above 1.0

| Host | Riders (from) | Ratio | Without riders |
| --- | --- | --- | --- |
| P-K-P-L03.02.01 | /E1/STAGE_FALL at 11 (P-K-P-L13.01.01.01) | 0.87 | 0.87 |
| P-K-P-L04.01.01.01 | /E4/Cd69090_W at 2 (P-K-P-L04.01.02.02) | 0.92 | 0.92 |
| P-K-P-L04.01.01.02 | /E4/Cb80f06_W at 2 (P-K-P-L04.01.02.02) | 0.92 | 0.92 |
| P-K-P-L04.01.02.01 | /A03/IN_REMOTE at 8 (P-K-P-L04.01.02.02) | 0.30 | — |
| P-K-P-L04.02.01.01 | /A03/REF5 at 6 (P-K-P-L04.01.02.02) | 0.92 | 0.36 |
| P-K-P-L05.01.01 | /E5/ASR_RAW at 5 (P-K-P-L01.01.01), /E5/CURVED at 6 (P-K-P-L01.01.01) | 0.74 | 0.73 |
| P-K-P-L06.01.02.01 | /O3/C83f36b_W at 7 (P-K-P-L06.01.02.02) | — | — |
| P-K-P-L06.03.01 | /O3/Ce35646_W at 4 (P-K-P-L06.01.02.02), /M5A/C2c2153_W at 5 (P-K-P-L06.01.02.02), /M5A/C445167_W at 6 (P-K-P-L06.01.02.02), /O3/Ca449b7_W at 7 (P-K-P-L10.01.01.02), /O3/FM_REMOTE at 11 (P-K-P-L06.01.02.02) | 0.58 | 0.04 |
| P-K-P-L10.01.02 | /O5/Ce35646_W at 7 (P-K-P-L10.01.01.02), /F1/Cb3b460_W at 8 (P-K-P-L10.01.01.02), /F1/Cb5b1dc_W at 9 (P-K-P-L10.01.01.02) | 0.63 | 0.62 |
| P-K-P-L10.02 | /O5/FM_REMOTE at 5 (P-K-P-L10.01.01.02) | 0.98 | 0.98 |
| P-K-P-L11.01.02.01 | /F3/C2b474d_W at 1 (P-K-P-L12.01.02.01), /F1/C8c344f_W at 2 (P-K-P-L12.01.01.01), /F1/Ca72ec0_W at 3 (P-K-P-L12.01.01.01), /F2/C14689f_W at 4 (P-K-P-L12.01.01.01) | 0.93 | 0.92 |
| P-K-P-L12.01.02.02 | /M5A/C0f3556_W at 5 (P-K-P-L14.01.01.01), /M5A/5_REMOTE at 7 (P-K-P-L14.01.01.01) | 0.21 | — |
| P-K-P-L12.02.01.01 | /M4B/C38051c_W at 2 (P-K-P-L12.01.02.01) | 0.92 | 0.92 |
| P-K-P-L12.02.01.02 | /M4B/C75c2e7_W at 2 (P-K-P-L12.01.02.01), /M4A/C75c2e7_W at 3 (P-K-P-L12.01.01.01), /F3/C14689f_W at 4 (P-K-P-L12.01.01.01) | 0.20 | 0.10 |
| P-K-P-L13.01.01.02 | /M4B/2_REMOTE at 5 (P-K-P-L03.02.02.01), /M4B/1_REMOTE at 7 (P-K-P-L03.02.02.01) | 0.92 | 0.92 |
| P-K-P-L13.01.02.01 | /F3/C8c344f_W at 1 (P-K-P-L12.01.02.01), /F3/Ca72ec0_W at 2 (P-K-P-L12.01.02.01), /F2/C2b474d_W at 3 (P-K-P-L12.01.01.01), /M4A/C38051c_W at 4 (P-K-P-L12.01.01.01) | 0.93 | 0.92 |
| P-K-P-L14.01.01.02 | /W1/C4c1698_W at 7 (P-K-P-L14.01.01.01) | — | — |
| P-K-P-L14.01.02.02 | /W1/C629978_W at 1 (P-K-P-L14.01.01.01), /M5B/C0f3556_W at 2 (P-K-P-L14.01.01.01), /M5B/5_REMOTE at 6 (P-K-P-L14.01.01.01) | 0.92 | 0.36 |
| P-K-P-L14.02.01.02 | /W1/C75db46_W at 1 (P-K-P-L14.02.01.01), /W1/Cb36f8a_W at 2 (P-K-P-L14.02.01.01) | 0.62 | 0.62 |
| P-K-P-L15.01.01.02 | /M4A/C1c45d6_W at 3 (P-K-P-L14.02.01.01), /M4A/C24ce01_W at 4 (P-K-P-L14.02.01.01) | 0.93 | 0.92 |
| P-K-P-L15.01.02.02 | /M5B/Ce67982_W at 1 (P-K-P-L14.02.01.01), /M5B/LEVEL_REMOTE at 5 (P-K-P-L14.02.01.01) | 0.66 | 0.23 |
| JL-P-K-P-L01.01.01.02 | /X2/B_BUFFER at 3 (JL-P-K-P-L01.01.02.01), /X2/SELECTOR_REMOTE at 5 (JL-P-K-P-L01.01.02.01) | 0.92 | 0.30 |

## The rule per link holds on every link: 10 links carry logic, with 17 runs of two or more (DS-62, DS-77, DS-79)

Checked on the record: a ground or unused position between every two signals except LOGIC, WIPER or STATIC beside its own class; logic and wiper never in one cable; at least one ground or unused position; a logic run of two or more never on position 1 or the last and with a ground on each side; a single logic line at an outer position with a ground beside it; the adapter order OSC_OCT0 to OSC_OCT5, AGND, OCT_SELECTED.

## Gate check 3 on the record: the worst link ground contact carries at most 0.047 A with one post open, inside 0.35 A on every branch in all three post cases; one contact alone would carry 0.049 A

Per branch as the calculator defines it, with every ground and unused position of its links as a contact in parallel (DS-77), each possible candidate contact at its own cable length and minimum path resistance, every alternative at its own cable length and maximum path resistance, and no board term on the link path. The positions of the fields enter only through the number of contacts and the cable lengths.

| Branch | Links | Contacts (grounds + unused) | Fewest on a link | Shortest cable, mm | Normal, A | One post open, A | All posts open, A | One contact, one post open, A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JL | 12 | 292 (112 + 180) | 4 | 50 | 0.0428 | 0.0458 | 0.0836 | 0.0489 |
| JR | 7 | 162 (111 + 51) | 20 | 50 | 0.0434 | 0.0470 | 0.1222 | 0.0489 |
| P | 40 | 224 (133 + 91) | 1 | 50 | 0.0430 | 0.0463 | 0.0998 | 0.0486 |

The bound of attempt a2 (0.049 A with one post open, one ground per link at 50 mm) still covers every link: every link has at least 1 contact and no cable on JL, JR or P is shorter than 50 mm.

### Each adapter is a branch of its own whose one ground carries no designed current; a selector step drives at most 0.34 mA into it for 5 ns

The O boards carry no supply post and no active part on the adapter: the taps leave K, pass the selector and return on OCT_SELECTED to the 1 kΩ / 100 nF / 10 MΩ receiver on K, whose 10 MΩ returns on K. The only current in the adapter ground is the displacement current of OCT_SELECTED to the ground position during a step (ASSUMED 1 V in 5 ns).

| Adapter | Ground contacts | DC, A | Step into the ground, mA | Step into all neighbours, mA |
| --- | --- | --- | --- | --- |
| O-K-O1 | 1 | 0 | 0.34 | 0.6 |
| O-K-O3 | 1 | 0 | 0.34 | 0.6 |
| O-K-O5 | 1 | 0 | 0.34 | 0.6 |

## Checks: calculator and tests run; every measurement and native check NOT RUN

- **Run:** this calculator twice with a clean `git status`; `python3 scripts/checks/frozen_studies.py discover scripts/stack/link_electrical`; `pnpm circuit:check` before and after.
- **NOT RUN, crosstalk, current share and resistance measurements:** no cable, connector or board exists.
- **NOT RUN, field solver for the real laminate:** the permittivity of the LX cable is not on its drawing; the homogeneous model is bracketed by the ε_eff sweep.
- **NOT RUN, connector contact coupling:** no connector coupling data is retained; covered only by the ASSUMED end length.
- **NOT RUN, ground share with board terms at the field positions:** the model keeps its stated terms (no board term on the link path); the record enters only through the contact count and the cable length.
- **NOT RUN, `bash scripts/checks/regen-all.sh`, `pnpm check` and the full Python suite:** native KiCad steps run in the pull request's CI; the suite outside this folder is run by the manager on the integrated tree.
- **NOT RUN, KiCad, DRC and `regen-all.sh`:** no board is changed.
- **NOT RUN, harness coupling measurement and a field solver for the insulated wire bundle:** no harness is built; the wire permittivity is not on the Alpha sheet.
