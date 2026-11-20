# Task C step 2b: five link moves with re-placement bring the unplaced ICs from 26 to 19

```sh
python3 -B shift_replace.py --output new-result.json   # about 7 minutes
python3 -B test_shift_replace.py
```

This replaces the inconclusive step 2a study (`../mc04_c2_link_shift`). It runs against the
cumulative MC04-R1 scene: 412 accepted moves, with the 26 unresolved bodies frozen.

**Which links.** All 19 links whose field, slot, tail or latch margin covers an unresolved IC.

**Candidates.** Each link gets up to six cheapest candidates from the retained `links_gate.search`:
- the class-distance accept applies;
- the search stays inside the retained radius;
- every candidate must clear the courtyards of the ICs the link covered, grown 0.35 mm.

**Re-placement.** For each candidate, the study re-places two groups of parts:
- parts the moved link newly covers;
- parts that block an uncovered IC from staying at its original place.

Re-placement is greedy and uses the retained ring pattern (0.25 mm steps, 24 directions, 25 mm
cap). It tries the part's own face first, then the other face for surface-mount parts. Panel
hardware and dropped footprints never move. Each link keeps its candidate with the best net change
(parts left without a place minus ICs freed). The study then applies all improving moves together.

Result (`result.json`, SHA-256 `535f76706098ca023859bab5e4d2fb690733ec3b7c9208bb8b2196a49914b187`):

| Moves | Net change |
| --- | --- |
| JL-L08 | −2 (U1416, U1417) |
| JR-L06 | −2 (U4524, U4526, U4527 freed; U6101 left without place) |
| P-L02.01.01 | −1 (U4433) |
| P-L12.02.01.02 | −1 (U5110) |
| P-L13.01.01.02 | −1 (U5209) |
| **All five together** | **−7**: 8 freed, U6101 left without place, 101 parts re-placed, no link clashes |
| JL-L01, JL-L02, JL-L07, JR-L02, JR-L03, JR-L04, P-L07, P-L13.01.01.01 | 0: a 1-for-1 swap or no gain |
| JR-L05, JR-L07, P-L03.01, P-L05.01.01 | worse |
| JR-L01, P-L08 | no candidate clears its ICs inside the retained radius |

19 ICs would remain unplaced:

| Board | ICs |
| --- | --- |
| JL | U1216, U1518, U2119, U2218 |
| JR | U4346, U4347, U4348, U8314, U8318, U8417 |
| K | U1415, U4324, U4341, U4417, U4623, U4635, U5210, U8409, U6101 |

No link move improves JR. Together with the step 1 joint-capacity bound (3 of 6 fit), this points
to a JR block relocation or a partition change, not link reshaping.

Not established:
- **Room only.** The moved links' cable lengths, loop and coupling ratio at their new order are not
  recomputed (ST-04 part 2 and the c6 contract).
- **No electrical review.** The 101 re-placed parts, including decouplers moved away from their ICs,
  have not been reviewed electrically.
- **Search limits.** Candidates per link are capped at six, and re-placement is greedy, so neither
  result is a minimum.
- **Mirroring.** Flipped footprints are not mirrored.
- **No canonical change.** Nothing here changes canonical geometry. Adopting any move goes through the
  links_gate generator, with the place() accept and input-hash fixes, followed by regeneration and
  independent review.
