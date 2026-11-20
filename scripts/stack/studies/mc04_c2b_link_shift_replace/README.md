# Task C step 2b: three link moves free 3 ICs cleanly (26 to 23); six moves reach 20 but strand 3 small parts

```sh
python3 -B shift_replace.py --output new-result.json   # about 8 minutes
python3 -B test_shift_replace.py
```

This replaces the inconclusive step 2a study (`../mc04_c2_link_shift`). It runs against the
cumulative MC04-R1 scene: 412 accepted moves, with the 26 unresolved bodies frozen.

**Which links.** All 19 links whose field, slot, tail or latch margin covers an unresolved IC.

**Candidates.** Each link gets up to six cheapest candidates from the retained `links_gate.search`.
Every candidate must:
- pass the class-distance accept;
- stay inside the retained radius;
- keep every rider the link hosts within its class distance;
- clear the courtyards of the ICs the link covered, grown 0.35 mm.

**Re-placement.** For each candidate, the study re-places three groups of parts:
- parts the moved link newly covers;
- parts the recorded link only crossed with its tail, if the moved link now displaces them under the
  retained rule;
- parts that block an uncovered IC from staying at its original place.

Re-placement is greedy and follows the retained DS-97 step order: own face up to 12 mm, then the
other face up to 12 mm (K, surface mount only), then either face up to 25 mm. ICs go first, larger
courtyards first. Every placed part becomes an obstacle with the retained growth. Panel hardware and
dropped footprints never move.

**Selection.** Each link keeps the candidate with the best net IC change (unresolved ICs left without
a place minus ICs freed). The re-placed positions are recorded in `placed`.

Result (`result.json`, SHA-256 `75ca3997b563600e90e940e3ae42c8d172ece79a760a384f1146d49b126f0b1d`):

| Combination | Links | Freed | Left without a place | Unplaced ICs after |
| --- | --- | --- | --- | --- |
| Clean: no part stranded | P-L02.01.01, P-L12.02.01.02, P-L13.01.01.02 | U4433, U5110, U5209 | none (41 parts re-placed) | **23** |
| All IC-improving moves | the three above plus JR-L02, JR-L04, JR-L06 | 9: U8314, U8318, U8417, U4433, U4524, U4526, U4527, U5110, U5209 | U4102, U4148, U6101, C4177, D4113, D8411 (106 re-placed) | 20, plus 3 stranded small parts |

No combination clashes between moved links.

Moves that do not help:
- Every JL link nets zero after the correction. Each one frees its ICs only by pushing out others:
  JL-L01 swaps U2218 for U2317, JL-L02 swaps two for two, JL-L07 swaps U1216 for U1316, and JL-L08
  swaps U1416/U1417 for U1516/U1517.
- JR-L03, P-L07 and P-L13.01.01.01 also net zero.
- JR-L05, P-L03.01 and P-L05.01.01 are worse.
- JR-L07 nets zero ICs but strands three small parts.
- JR-L01 and P-L08 have no candidate inside the retained radius.

A stranded passive or diode is as unacceptable as a stranded IC, so the honest figure is **23**. The
20 figure needs room for C4177, D4113 and D8411 on JR plus U4102, U4148 and U6101. JR remains the
board where capacity runs out.

Correction history: a first version of this study reported 26 to 19. An independent review found
four problems, which are now fixed:
- parts the moved JL-L08 displaced were never counted;
- a P-L12.02.01.02 candidate broke its riders' 55 mm limit;
- re-placed parts were added without growth;
- the step order was simplified.

Not established:
- **Electrical review.** The re-placed parts, including decouplers moved from their ICs, have not
  been reviewed electrically.
- **Contracts.** Rider, coupling and c6 contracts have not been re-run. c6 pins the geometry digest.
- **Search limits.** Candidates per link are capped at six, and re-placement is greedy, so neither
  result is a minimum.
- **Mirroring.** Flipped footprints are not mirrored.
- **No canonical change.** Nothing here changes canonical geometry.
