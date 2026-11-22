# MC04-S9-A brief: slot-move and package-room study for U1415, U5110, U5209, U5210 and U8409

2026-11-22. Ruled by the design authority (DS-145) on packet `mc04-s9-remaining-five-decision-packet-20261122.md`.
Executor: the Windows/WSL Claude Code session. Branch `claude/project-thread-iw3gai`.

**Kind:** study only. No canonical geometry, spec, BOM, board or gate change. The result is a decision table.

## Inputs (pin each by SHA-256 in the result)

- `design/stack/geometry/links/link-gate.json` and `link-era-replacements.json` at `5c8e23b9`
- `scripts/stack/geometry/links_gate.py`, `links_gate_part2.py` (`Field`, retained `search`)
- `scripts/stack/studies/mc04_s8_replacement/` (face-aware block rules, `member_faces.py`)
- `scripts/stack/studies/mc04_c2b_link_shift_replace/` and `mc04_c2c_moved_link_checks/` (method precedent; their
  results predate stage 7 and must be re-run, not reused)
- `design/partition/locality-acceptances.json`, `design/grid/placements.lock.json`
- `footprints/kicad/zudo-osc-hole-field.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod`

## Allowed changes

- A new directory `scripts/stack/studies/mc04_s9_slot_moves/`: script with `--check`, tests, `result.json`, README.
- The report `mc04-s9-a-report-20261122.md` in this folder.
- **Separate commit:** filter `gone` links in `gate_a_open_items.py overlaps()`, add a test, and regenerate
  `gate-a-open-items.json`. P-K-P-L03.02.02.01 is dissolved and must no longer be cited for U8409.
- **Separate commit, U4433:** record the manager's acceptance as its own exception (DS-144, not "on the U4417 terms").
  First run `member_faces.py` and `board_conflicts.py` on its F 270°, 25.5 mm pose. Only if both pass, mark it
  RESOLVED FOR THE LINK ERA, with these conditions recorded:
  - the `/E4/CLOCK` edge is checked against `fact-flipflop-input-transition45` at re-route;
  - no E4 clock-load budget exists;
  - 25.5 mm exceeds the DS-88 25 mm radius, so it is an interim Gate A item.

## Fixed

- the 438 panel centres and `placements.lock.json`;
- the 33 modules;
- every link's connector size, cable code, stock length and stock-FFC direction;
- the ruled sleeves and fixing keep-outs;
- DS-06 and all holds;
- the link-era poses and their acceptances;
- the input-buffer blocks;
- every link other than the six named in arm 1.

Start with `bash scripts/checks/regen-all.sh` and `pnpm circuit:check`.

## Arm 0: premise

Assert that `Field` holds no keep-out for any `gone` link. Then reproduce the five OPEN results from `result-r7.json`
byte for byte.

## Arm 1: R1, local P-K slot moves

Links, in this order:
1. P-K-P-L13.01.01.02 (U5209: 0.07 mm inside the growth);
2. P-K-P-L12.02.01.02 (U5110);
3. P-K-P-L03.01 (U8409: about 0.81 mm of +x relief);
4. P-K-P-L13.01.01.01 (U5210: about 5.65 mm);
5. P-K-P-L07 and P-K-P-L08 (U1415).

Take candidates from the retained search on the 2.0, 0.5 and 0.25 mm grids, cheapest first, with a stated cap. A
candidate is clean only if all of these hold:
- it is inside the retained join radius; member and rider class distances are kept (PRECISION 40, ANALOGUE 45,
  WIPER 55, LOGIC 55 mm); there is no way-4 growth;
- the cable fits its stock length with loop ≥ 0, and compliance is ≤ 1.0 mm/N, listed above 0.25;
- the target IC and its whole block stay at their recorded position, clear of every keep-out grown 0.35 mm;
- every footprint newly covered on K or P is re-placed under the S8 face-aware rules within 24 mm; none is stranded,
  no resolved IC becomes open, and no input buffer moves;
- the chosen moves are verified together in one scene.

Report each move as step 2c did: loop, compliance, hold-by-hand, leads to trim, riders against limits and parts
re-placed. For L07 and L08, report why only the 40-way size was tried (L07 needs 23 circuits).

## Arm 2: R2, package room only

Keep the links at the record. Swap each target's footprint geometry for the repository TSSOP-14, keep its block, and
run the S8 search within 24 mm. Label every row `ROOM ONLY, NO PART SELECTED`. Run a third column, arms 1 and 2
combined, only for ICs that fail both. R2 does not mean OPA4197IPWR; it means an OPA4196-family TSSOP-14, which
needs the evidence task in DS-145 before any spec change.

## Acceptance

- `--check` reproduces `result.json`.
- The tests pin the per-IC outcome, include a mutation that fails, and include a moved-link candidate that breaks a
  rider limit and is rejected.
- Every existing `--check` and the stack suite still pass, and `pnpm circuit:check` is unchanged.
- The report gives one row per IC: R1 clean, R1 not clean (with the reason), R2 room, or none.
- The report lists what is not established: c6, coupling (check 4), current (check 3), latch access (check 2),
  threading, routing, DRC and any electrical acceptance.
- Oracle checks that did not run are written `NOT RUN`, with the reason.

## Stop conditions

Stop on any of these:
- input hash drift;
- arm 0 fails to reproduce;
- a clean result needs a panel centre, sleeve, hold, cable or connector change;
- the candidate cap or the admitted time ceiling is reached. Report it as a cap, not as "no fit".

No second run, no wider radius, no adoption and no supplier contact. Push and stop at the checkpoint with the report.
