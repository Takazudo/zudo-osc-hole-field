# MC04-S9-A: slot moves (R1) and package room (R2) for the last five analog ICs

```sh
python3 slot_moves.py           # writes result.json (about 15 minutes)
python3 slot_moves.py --check   # rebuilds and compares
python3 -m unittest test_slot_moves
```

Study only (DS-145). No canonical geometry, spec, BOM, board or gate change. Brief:
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s9-a-slot-move-study-brief-20261122.md`.
Report: `mc04-s9-a-report-20261122.md` in the same folder.

**Model.** The link-era model (`links_gate_part2.Field`, GH headers dropped, gate-displaced parts at their paper
positions). Every placed link-era pose is applied the way `replacement_r7.R7` applies them, U4433 (DS-144) included.

**Inputs.** `result.json` pins the SHA-256 of every input under `inputs`. Under `base`, it records that the link-gate
links and the gate re-placement are byte-equal to commit `5c8e23b9`. The link-era record differs from that commit only
by the U4433 row.

## Method

**Arm 0.** Checks that the Field holds no keep-out for a dissolved link. Then rebuilds `result-r7.json` and compares it
byte for byte.

**Arm 1 (R1).** The named P-K link is searched again with the retained search (`links_gate.search`). The search keeps
the record's size, connector and cable and uses the 24 mm radius about the link's search centre. It runs on the 2.0,
0.5 and 0.25 mm grids.

A candidate is accepted only if all of these hold:
- it passes the retained class-distance accept of its members;
- every hosted rider stays within its class distance;
- loop ≥ 0 within the stock cable;
- K-field compliance ≤ 1.0 mm/N;
- it clears the target block at its recorded position (courtyard growth 0.35 mm).

Accepted candidates are evaluated cheapest first, up to 24 per grid, in the full scene. The parts lifted are:
- footprints the moved link newly displaces under the retained rule;
- re-placed parts it now covers;
- parts on the target's recorded area.

Each lifted part is re-placed within 24 mm of its paper position. A passive tries its own face, then the other face if
it is a surface-mount part on K. An IC moves as its S8 block, found by the S8 search. That search uses the Revision 1
class (iii) rules with the A2 turns and displacement, face-aware, and here it may not displace an input-buffer part.

A candidate is clean only if all of these hold:
- every lifted part finds a place;
- no placed link-era block moves;
- no input-buffer part moves (the S8 A3 definition: packages with a high-impedance-input or remote-buffer unit, their
  blocks, and the cell parts of those roles);
- the target block is legal at its recorded position.

The first clean candidate of each link is fixed before the next link. The chosen moves are then verified together.

For U1415, P-K-P-L07 and P-K-P-L08 are searched as a pair:
- up to 4 clean L07 candidates are kept;
- each one is tried with an L08 search.

**Arm 2 (R2, room only).** The links stay at the record. The target's courtyard becomes the repository TSSOP-14
courtyard, with the same origin, angle and side. The board SOIC-14 courtyard is reproduced from the library as a check.
The block is kept, and the S8 search runs within 24 mm. It runs twice:
- under the S8 rules as ruled;
- with the arm 1 input-buffer guard.

**Combined.** Arms 1 and 2 together, with the TSSOP courtyard and the link search. It runs only for the ICs that fail
both arms (R2 judged with the guard).

## Result (`result.json`)

| IC | R1 (local P-K slot move) | R2 (TSSOP room) | R1 with R2 | Outcome |
| --- | --- | --- | --- | --- |
| U5209 | not clean: the recorded area is also under P-K-P-L13.01.02.01 (kept fixed) | none (nearest 49.34 mm) | not clean | none |
| U5110 | not clean: 26 candidates. 23 move input-buffer parts. 3 newly cover U5205/U5206, whose blocks find no pose within 24 mm | none (40.61 mm) | not clean | none |
| U8409 | not clean: C8438 (decoupler of the input buffer U8411, gate-re-placed onto the area) must move for any candidate | none (113.22 mm) | not clean | none |
| U5210 | **clean**: P-K-P-L13.01.01.01 to slot (202.17, 195.67) +y | none (79.21 mm) | not run | R1 clean |
| U1415 | not clean: P-K-P-L08 has no accepted candidate within 24 mm on any grid | room at 22.5 mm only by displacing C1302, C1303 and R1321 (input-buffer parts); none with the guard | not clean | R2 room only by displacing input-buffer parts |

The cap was reached for P-K-P-L03.01 on the 0.5 and 0.25 mm grids (24 of 48, 24 of 131). The cap does not decide the
U8409 outcome, because C8438 lies on U8409's recorded area for every candidate.

## Not established

c6, coupling (check 4), current (check 3), latch access (check 2), threading, routing, DRC and any electrical
acceptance. None of these oracle checks was run (see `oracle_checks`).

## MC04-S9-A2 joint re-run (DS-146)

```sh
python3 slot_moves_a2.py           # writes result-a2.json (about 19 minutes)
python3 slot_moves_a2.py --check
python3 -m unittest test_slot_moves_a2
```

This is the same study under the four DS-146 rule changes:
- input-buffer parts are judged by kind;
- covered block members are re-placed;
- trimmers keep their face;
- no candidate may cover any of the five ICs.

Every accepted candidate is evaluated (cap 200 per link and grid), then one joint scene is built.

Result:
- U5209 (variant B, P-K-P-L13.01.01.02 and L13.01.02.01 moved) and U5210 (P-K-P-L13.01.01.01 moved) are clean together.
- U5110 and U8409 are not clean.

Report: `mc04-s9-a2-report-20261122.md`.
