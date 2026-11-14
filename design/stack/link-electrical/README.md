# Flat-link electrical bounds: ST-04 attempt a2 (paper, DS-41 checks 3 and 4 without positions)

Task `osc-stack-20261114/ST-04 attempt a2 (DS-41 checks 3 and 4 without positions; DS-48, DS-51)`, launch commit `21d1cd9`. **Status: unvalidated paper bound.** Coupling, current share and resistance are NOT RUN as measurements; nothing is selected, adopted or bought. Every class, impedance, edge rate and limit below is ASSUMED unless a row says otherwise, and the limits are criteria for the design ruling (NEEDS_DESIGN).

This file and `results.json` are written by `python3 scripts/stack/link_electrical/link_electrical.py` from [`inputs.json`](inputs.json); the tests fail if either differs from a fresh run. Status words: SOURCED (file and locator in `inputs.json`), DERIVED (formula below), ASSUMED (reason in `inputs.json`), NOT RUN (reason given).

## 492 link signal positions in four coupling classes; 2 of them are NC

Every K pair of the retained candidate except the six adapter pairs, rail and AGND positions removed: 492 positions (490 signals and 2 NC positions on one JR pair), against 513 − 21 = 492 in DA-03 F4. The class comes from the partition's signal kind and the net name (`inputs.json` → `classes`, ASSUMED). Four planning nets of the SUB pairs (`O2:SUB_SEL_A` etc.) are not in the partition harnesses and are taken as LOGIC.

| Joint | PRECISION | WIPER | ANALOGUE | LOGIC | NC | Total |
| --- | --- | --- | --- | --- | --- | --- |
| JL to K | 12 | 0 | 88 | 0 | 0 | 100 |
| JL to P through K | 0 | 0 | 16 | 0 | 0 | 16 |
| JR to K | 16 | 0 | 90 | 0 | 2 | 108 |
| P to K (with SUB and EL pass-through) | 50 | 99 | 68 | 51 | 0 | 268 |
| **Total** | 78 | 99 | 262 | 51 | 2 | 492 |

| Class | Victim source impedance (sweep, nominal) | Victim limit | As aggressor |
| --- | --- | --- | --- |
| PRECISION | 10, 100, 1000 Ω, nominal 100 Ω | 1 mV | ANALOGUE row (op-amp slew) |
| WIPER | 2500, 25000, 125000 Ω, nominal 25000 Ω | 1 mV | none (hand-turned; STATIC) |
| ANALOGUE | 10, 100, 1000 Ω, nominal 100 Ω | 10 mV | 20 V at 20 V/µs (10 to 40), and a 10 V 20 kHz sine |
| LOGIC | 25, 50, 100 Ω, nominal 50 Ω | 500 mV | 5 V in 5 ns (2 to 15), load 15 pF |

## Coupling: LOGIC edges must not share a flat cable with ANALOGUE, PRECISION, WIPER at either pitch; 3 of 16 pitch-and-class pairs may sit side by side, 0 need a grounded neighbour

Pairs that fail even with grounds on both sides (upper permittivity 3.2, nominal impedance and edge): ANALOGUE onto PRECISION, ANALOGUE onto WIPER, LOGIC onto ANALOGUE, LOGIC onto PRECISION, LOGIC onto WIPER. The table gives the worst bound over 50 and 80 mm per pitch; voltage in mV, dB relative to the aggressor swing; "sine" is the steady 20 kHz bleed. Rule A adjacent is two signals side by side; A across ground and B are one grounded conductor between them (B also has grounds on the outer sides).

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

Three ASSUMED terms carry these verdicts, and each is a design input. (1) The wiper victim has no receiver filter capacitor credited: at 25 kΩ the coupled edge decays over R·C_tot of about 0.1 µs, and any filter capacitor at the receiver divides it by C_filter/C_tot. (2) PRECISION nets are counted as aggressors at full analogue slew; most are DC references or slow CVs, and PRECISION beside PRECISION is counted with a ground between although the 80 mm bound exceeds 1 mV even then. (3) The victim limits (1 mV, 10 mV, 0.5 V) are peak criteria for nanosecond to microsecond spikes; a pitch error depends on the area that the receiving stage integrates, which no retained source states. No 2-layer flex with a ground layer is computed (DS-41 check 4): NOT RUN.

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

Formulas. Capacitance: 2-D method of moments for coplanar strips in a homogeneous medium (ε_eff swept 1.0 / 2.1 / 3.2), zero total charge, the other conductors of the window held at AC ground; checked against ε K(k\′)/K(k) for two strips in the tests. Inductance: Grover's parallel-filament mutual and Ruehli's bar self term, valid for length ≫ spacing; the aggressor return divides among the window's grounds by least inductance. Victim bound = capacitive term V·R·Cm/t_r·(1 − e^(−t_r/(R·C_tot))) plus the full loop term M·di/dt, di/dt = 2·I/t_r (both ASSUMED same sign). Each end adds 5 mm of parallel run for the connector and fan-in (ASSUMED).

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

## The computed rule needs 94 to 109 grounds for the 490 signals, against 245 or more under rule A and 517 or more under rule B

Per joint and option, with free ordering inside a joint: classes in blocks, a ground between same-class neighbours only where the class pair needs one, one ground between blocks that share a cable, one ground per link, and class pairs that may not share a cable put in cables of their own (cable groups below). Rule A and rule B of DS-51 are counted the same way. This is a lower bound: the class mix per link follows the clustering of ST-02 a4, which this count does not know.

| Pitch | Circuits | Grounds / links, computed rule | Grounds / links, rule A | Grounds / links, rule B |
| --- | --- | --- | --- | --- |
| 1.00 mm | 20 | 109 / 34 | 245 / 39 | 544 / 54 |
| 1.00 mm | 22 | 107 / 32 | 245 / 36 | 539 / 49 |
| 0.5 mm | 30 | 100 / 25 | 245 / 26 | 526 / 36 |
| 0.5 mm | 40 | 94 / 19 | 245 / 20 | 517 / 27 |

Per joint at 1.00 mm, 20 circuits (the other options differ only in link counts, see `results.json`):

| Joint | Signals | Cable groups | Grounds / links, computed rule | Rule A | Rule B |
| --- | --- | --- | --- | --- | --- |
| JL to K | 100 | ANALOGUE; PRECISION | 18 / 7 | 50 / 8 | 111 / 11 |
| JL to P through K | 16 | ANALOGUE | 1 / 1 | 8 / 2 | 18 / 2 |
| JR to K | 106 | ANALOGUE; PRECISION | 22 / 7 | 53 / 8 | 118 / 12 |
| P to K (with SUB and EL pass-through) | 268 | LOGIC; ANALOGUE; PRECISION; WIPER | 68 / 19 | 134 / 21 | 297 / 29 |

## Ground current: the worst link ground contact carries at most 0.086 A normally and 0.095 A with one post open, inside the lowest rating swept (0.3 A) at both pitches

One link ground path is two contacts and one conductor. The bound gives the candidate path its minimum resistance (conductor minimum, contacts 0 Ω ASSUMED) and no PCB term, and every alternative its maximum and the whole 0.5 mΩ common neck (the partition35 method of the power-post README). Branch current 4.6 A (SOURCED, `single_return_A`). Post joints from `power_posts.py` (0.4045 / 0.3952 mΩ).

| Pitch | Link ground path, min / max, mΩ |
| --- | --- |
| 1.00 mm | 33.2 / 104.2 (conductor DERIVED, contact max SOURCED) |
| 0.5 mm | 65.3 / 206.4 (conductor DERIVED, contact max SOURCED) |

| Pitch | Branch | AGND posts in place | Worst contact, one ground in the branch, A | Worst contact, rule A grounds (n), A | Smallest grounds per board meeting each rating |
| --- | --- | --- | --- | --- | --- |
| 1.00 mm | JL | 3 (normal) | 0.086 | 0.0851 (58) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 2 (one post open) | 0.095 | 0.0926 (58) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JL | 0 (all posts open) | 4.600 | 0.3014 (58) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | JR | 3 (normal) | 0.086 | 0.0852 (54) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 2 (one post open) | 0.095 | 0.0928 (54) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | JR | 0 (all posts open) | 4.600 | 0.3181 (54) | 0.4 A: 41, 0.5 A: 31 |
| 1.00 mm | P | 3 (normal) | 0.086 | 0.0834 (134) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 2 (one post open) | 0.095 | 0.0894 (134) | 0.4 A: 1, 0.5 A: 1 |
| 1.00 mm | P | 0 (all posts open) | 4.600 | 0.1712 (134) | 0.4 A: 41, 0.5 A: 31 |
| 0.5 mm | JL | 3 (normal) | 0.044 | 0.0440 (58) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 2 (one post open) | 0.049 | 0.0482 (58) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JL | 0 (all posts open) | 4.600 | 0.2731 (58) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | JR | 3 (normal) | 0.044 | 0.0440 (54) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 2 (one post open) | 0.049 | 0.0483 (54) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | JR | 0 (all posts open) | 4.600 | 0.2900 (54) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |
| 0.5 mm | P | 3 (normal) | 0.044 | 0.0434 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 2 (one post open) | 0.049 | 0.0471 (134) | 0.3 A: 1, 0.35 A: 1, 0.4 A: 1, 0.5 A: 1 |
| 0.5 mm | P | 0 (all posts open) | 4.600 | 0.1401 (134) | 0.3 A: 52, 0.35 A: 44, 0.4 A: 38, 0.5 A: 29 |

With any post of the branch in place a single link ground stays far inside every rating, because one link ground path (tens of mΩ) is about a hundred times the post path (under 1 mΩ). So current sets no minimum beyond one ground per link; the coupling rule sets the count. With every AGND post of a branch open (not a design case) the link grounds carry the whole return, and the count in the last column applies.

### The final share at the field positions needs four inputs from the geometry task

- the K-side and front-side field centre of every link and its branch (ST-02 a4 `link-candidate.json`);
- the ground positions of each link after the ruling (count and pin numbers);
- the AGND plane spreading on K and on each front board from each field to the three post lands of its branch (routed planes, or the ASSUMED sheet model of the power-post README);
- the cable length per link (a shorter link lowers its path resistance and raises its share).

## Checks: calculator and tests run; every measurement and native check NOT RUN

- **Run:** this calculator twice with a clean `git status`; `python3 scripts/checks/frozen_studies.py discover scripts/stack/link_electrical`; `pnpm circuit:check` before and after.
- **NOT RUN, crosstalk, current share and resistance measurements:** no cable, connector or board exists.
- **NOT RUN, field solver for the real laminate:** the permittivity of the LX cable is not on its drawing; the homogeneous model is bracketed by the ε_eff sweep.
- **NOT RUN, connector contact coupling:** no connector coupling data is retained; covered only by the ASSUMED end length.
- **NOT RUN, ground share at the field positions:** waits for ST-02 a4 and the ruling.
- **NOT RUN, KiCad, DRC and `regen-all.sh`:** no board is changed.
