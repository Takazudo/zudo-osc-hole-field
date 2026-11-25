# MC04-S10: the three L13 link moves (DS-147, DS-148)

```sh
python3 c6_rebind.py --check   # c6 rebind check for the four holds (replays the gate, about 3 minutes)
python3 overlay.py --check     # overlay rules over the canonical gate rows (seconds)
python3 -m unittest test_s10
```

Brief: `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s10-l13-link-moves-generator-brief-20261122.md`,
Revision 1. Report: `mc04-s10-report-20261122.md` in the same folder.

**Revision 1 disposition: STOP / returned for revision at `32580f77`.** Reproduction of this geometry is diagnostic. S11 awaits independent acceptance of a later S10 candidate.

## The holds

`design/stack/geometry/links/link-gate-options.json` gains four slot holds:

| Link | Held pose | Source |
| --- | --- | --- |
| P-K-P-L13.01.01.01 | (201.17, 197.42) +y | S9-A2, U5210 clean candidate 0 |
| P-K-P-L13.01.01.02 | (176.0, 196.25) −y | S9-A2, U5209 variant B pair 8 (R5257 on B exceeds the 7.93 mm limit before rounding) |
| P-K-P-L13.01.02.01 | (159.0, 193.0) −y | S9-A2, U5209 variant B pair 8 |
| P-K-P-L15.02.01.01 | (193.0, 213.0) +y | its recorded pose |

## The c6 rebind

`c6_rebind.py` replays the gate and writes
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s10-c6-rebind-check-20261122.json`. It records the following
against the base record at `8243acdf`:
- the signal and positions pins are unchanged;
- c6's eight links keep their conductor order and riders;
- rider hosts are unchanged, and rider distances change only on the held hosts;
- no unheld live link moves;
- the ways-out result and the dissolved set are unchanged.

The pins in `links_gate_c6.py` (geometry, output) are rebound to those values.

## The overlay

The gate replacement rows are canonical. `overlay.py` derives where the link-era record overlays a block pose, and
writes `overlay.json`:
1. ICs the gate leaves without a position. These are the ten link-era poses, re-checked in the new Field by
   `../mc04_s8_replacement/member_faces.py`, and U1415, U5110 and U8409, which stay open.
2. ICs with a new or shifted S10 row whose gate pose breaks the block rule: a decoupler on the other face, or farther
   from its IC than before. Each block is searched under the S8 rules. The poses: U4222 at 17.24 mm, U4227 at 18.82 mm,
   and U4537 at 17.87 mm on F (clock node `/E5/CLOCK`).
3. The ruled parts: R5257 and R5259 are on B, and RV4503, RV8407 and RV2310 are on the rear face.

`overlay.json` also holds:
- the row-change table (18 removed, 21 new, 15 shifted), with face, distance and step;
- the face changes, with their nets;
- the recomputed figures of `locality-acceptances.json`;
- the sensitive-net and ruled-part stops.

`replacement_r7.R7.load_overlay` places the overlay blocks in the current-record checks (`member_faces.py`,
`board_conflicts.py`). `link_era_replacements.py` writes them into the record with both poses.

## The S8 and S9 studies

The S8 and S9 studies are records of the model before S10. `replacement.Study` reads the gate, the Gate A list and
every link-gate input from a snapshot of commit `8243acdf` (`git archive` into the temporary directory), so their
`--check` stays reproducible. The checks of the current record set `snapshot = None`.
