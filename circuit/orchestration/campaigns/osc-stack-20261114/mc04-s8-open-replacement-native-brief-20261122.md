# MC04-S8 native brief: place the 15 open re-placements (Gate A check 5)

Date: 2026-11-22. Owner: the Claude Project lead. Executor: the Windows/WSL Claude Code session. Branch:
`claude/project-thread-iw3gai`, from `f0d02f88` (stage 7 closed by Revision 14).

## Why this stage comes before the re-route

Stage 7 closed with 15 SOIC-14 ICs that have no legal position: 13 on K, one on JL (U1318) and one on JR (U4647). Each
sits under a link slot, tail, connector or field keep-out. `design/stack/gate-a-open-items.json`, kind
"open re-placement (re-route)", lists them with their overlaps. Gate A check 5 stays NEEDS_DESIGN while any IC has no
position. Routing JL, JR and K before these parts land would be thrown away, so the re-route waits for this stage.

## Rules (unchanged from stage 7)

- Keep all 438 locked panel hardware centres (`design/grid/placements.lock.json`), all 33 module instances, the
  stock-FFC direction and the ruled sleeves. Do not move a link slot to make room; the link gate stays as regenerated
  in stage 7, including the JL-L02 hold.
- Each IC moves as one rigid block with its decouplers and its cell-local passives, as stage 7 did: bypass on the IC's
  face, no farther than before the move; feedback and gain-set passives no farther than before.
- The 24 mm far-move threshold, the locality acceptances and the Revision 2 input-buffer conditions apply. An input
  buffer may go farther only under those conditions (input passives at the cell end, ground-flanked, added run
  capacitance under 50 pF).
- Sleeve keep-outs are occupied (Revision 12/13 rule). Keep-out-displaced parts are placed last.
- Edit generators and sources, then regenerate. Never hand-edit generated outputs. KiCad 10.0.6 runs only through
  `scripts/kicad/run.sh` with the pinned image. Every board is an unvalidated draft; report unavailable checks as
  NOT RUN.
- No outward actions: no purchase, quote, supplier contact, fabrication order or site deploy.

## Part A: study, no board change (stop at the checkpoint)

1. For each of the 15 ICs, state its function (cell, role, and whether it is an input buffer, indicator driver, output
   stage, logic or precision part) and list its block (IC plus the passives that move with it).
2. Search for the nearest legal block pose on the IC's own board, on either face, using the floorplan's hardware,
   outline, gap, sleeve and link keep-out model. For each candidate, give the pose, its distance from the old position,
   the distance from each block member to its pre-move partner, and which other parts it would displace (if any).
3. Classify each IC:
   - **(i) fits within 24 mm** with no other part displaced;
   - **(ii) fits only beyond 24 mm**: give the distance and the locality condition it would need;
   - **(iii) fits only by displacing other parts**: list them and their own moves;
   - **(iv) no legal pose on its board**: give the free-area shortfall in mm², with the nearest candidate.
4. Report the board fill per region (E-regions on K, JL and JR) before and after, so the shortfall is visible.
5. Commit the study under `scripts/stack/studies/mc04_s8_replacement/` with a `--check` mode and tests, and push.
   Write the report as `mc04-s8-a-report-20261122.md` in this folder and stop for a ruling. Do not modify any board.

## Part B (after the ruling): apply, sync and check

To be ruled after Part A. It will follow the stage 7 Part B pattern: apply the poses in the generator, sync and place
the affected boards, strip conflicting copper with the `--max-share 25` stop, DRC with no new error-severity items,
parity 0, readiness 0, regenerate the link gate (holds unchanged), c6, fixings and procedure, and all stack tests.

## Part C (later): JL, JR and K re-route

Out of scope here. It will be briefed separately once every IC has a position.

## Revision 1: accept classes (i) and (iii); widen the search for the seven class (ii) ICs (2026-11-22)

Part A (`463e6821`, report `mc04-s8-a-report-20261122.md`) is accepted as a study; `replacement.py --check` passes here
too. The finding that the regions are 40–68 % full and fail on fragmentation, not area, sets the next step.

1. **Accepted for Part B, not yet applied:** K:U4129 (class i, F, 23.14 mm) and the seven class (iii) ICs (U1415,
   U4433, U4526, U4527, U4623, U4635, U5110) with their displaced passives, as studied. Do not apply them alone; Part B
   applies every ruled pose in one pass.
2. **Widen the search for the seven class (ii) ICs** (JL:U1318, U4417, U4524, U5209, U5210, U8409, JR:U4647), as Part A2,
   still with no board change:
   - try block rotations of 90°, 180° and 270° as well as 0°, on both faces;
   - allow class (iii) displacement of any unlocked SMD R/C/D part up to 12 mm², provided each displaced part
     lands within 24 mm of its own pre-move position and keeps its own block rules;
   - apply the poses ruled in item 1 first, so A2 searches the board as Part B would leave it;
   - keep the block definition (decouplers plus cell-local R/C within 12 mm). Do not shrink blocks.
3. **For any IC still beyond 24 mm after A2,** give the electrical facts I need to rule:
   - for an input buffer (U1318, U8409, U4647, and any other), the estimated added SENSE/BUFFER run length and
     capacitance (0.20 pF/mm, 1.5 × HPWL, as in stage 7), and whether the Revision 2 conditions (input passives at the
     cell end, ground-flanked run, under 50 pF) can hold;
   - for other functions, the added length on each signal net and whether any net is a high-impedance node, a
     feedback node or a timing node;
   - for U4647, which LED drivers share the package and how far each LED is from the new pose.
4. Add tests for the rotation search and the widened displacement rule. Commit with `--check`, push, and stop at the
   checkpoint with `mc04-s8-a2-report-20261122.md`.

## Revision 2: rule three more ICs; search block-on-block moves for the last four (2026-11-22)

Part A2 (`95bdafd5`, report `mc04-s8-a2-report-20261122.md`) is accepted as a study.

1. **U4524** joins the Part B set: F, 90°, 18.34 mm, displacing R4545, R4586 and R4589 as studied.
2. **JL:U1318** is accepted under the Revision 2 input-buffer conditions at B 90°, 29.09 mm. Its SENSE run is an estimated
   13.4 pF (66.8 mm), the input passives stay at the cell end, and the run must be ground-flanked. Record it in
   `locality-acceptances.json` with these figures.
3. **K:U4417** (logic, no clock or RC timing node) is accepted as an interim-GH locality exception at B 90°, 48.84 mm,
   with its 8 grown nets and their 23–38 pF estimates recorded, and listed for Gate A. HC logic drives that load; the
   cost is edge rate and crosstalk, which the re-route must keep away from analog high-impedance nodes.
4. **The far poses of U5209, U5210, U8409 and U4647 are not accepted.** They add about 37–144 mm to summing,
   feedback, rectifier-feedback and high-impedance sense nodes (up to 36.5 pF), and U4647 would put D1801 119 mm from
   its driver. Those nodes are where length causes instability, noise pickup and offset, so an interim exception is not
   enough.
5. **Part A3 study (no board change): block-on-block moves for these four.** Apply every pose ruled so far (items 1–3
   and Revision 1) first. Then allow a target IC to displace up to two other IC blocks, provided:
   - each displaced block moves rigidly within 24 mm of its own position, keeps its own block rules (bypass on face and
     no farther than before, cell passives no farther than before), and is not an input buffer that would leave the
     Revision 2 conditions;
   - the panel hardware, through-hole jacks, locked parts, link slots, sleeves and keep-outs stay where they are;
   - rotations 0/90/180/270° and both faces are allowed for every moving block.
   Report each target's best result with every block moved and the target's distance. For any target still beyond
   24 mm, give the smallest set of obstacles that would have to move, by type (jack, slot, sleeve, locked part), so the
   remaining options (a slot move, a package split, or a partition change) can go to the owner with numbers.
6. Add tests for the block-on-block rule. Commit with `--check`, push, and stop with `mc04-s8-a3-report-20261122.md`.

## Revision 3: rule U4647 and the three narrow relaxations; then Part B (2026-11-22)

Part A3 (`117da5f7`, report `mc04-s8-a3-report-20261122.md`) is accepted as a study. None of the remaining targets needs
a jack, slot, sleeve or locked part to move, so no owner decision is needed yet.

1. **JR:U4647** joins Part B at B 180°, (295.18, 74.97), 22.55 mm, with the U4502 block (TMUX7412, C4515, C4516) moved
   13.73 mm at B 180° and R4516 moved 6.25 mm. D1801 goes from 26.82 to 48.19 mm from its driver (unit 4). The LED
   drive is a low-impedance output, so this is accepted; record it in `locality-acceptances.json` as an interim-GH
   LED-drive distance and list it for Gate A. U4502's input-fault path must stay on its own face, with C4515/C4516 no
   farther than before.
2. **Three narrow relaxations, for Part A4 only:**
   - **U5209:** R8263 may move again, provided its final position is within 24 mm of its `6093081c` position and no
     farther from its cell partner than before the gate moved it.
   - **U5210:** C5210 (1206 AC-coupling cap) may be displaced as a passive, within 24 mm, provided the added length on
     its high-impedance side is reported and kept under 10 mm.
   - **U8409:** a chain of up to three IC blocks is allowed (the target, U8412 and one more). Each block keeps its own
     rules and the 24 mm limit, and none is an input buffer. U8412 beyond 24 mm is not allowed.
3. **Part A4 (study).** Apply every ruled pose first, then rerun the three targets with these relaxations only. Add a
   test for each relaxation. If all three land within the rules, go straight to Part B without another checkpoint.
   If any fails, stop with `mc04-s8-a4-report-20261122.md` and the obstacle set.
4. **Part B: apply, sync and check.** Apply every ruled pose:
   - U4129 and the seven class (iii) ICs (Revision 1);
   - U4524, U1318 and U4417 (Revision 2);
   - U4647 with U4502 (item 1);
   - the Part A4 results.
   Apply them through the generator, with their displaced passives and blocks, in one pass. Then follow the stage 7
   Part B pattern:
   - sync and place the affected boards;
   - strip conflicting copper with the `--max-share 25` stop;
   - run DRC with no new error-severity items, and require parity 0 and readiness 0;
   - regenerate the link gate (holds unchanged), c6, fixings, procedure and `gate-a-open-items.json`, which must show
     0 open re-placements;
   - run `regen-all.sh --check` and every stack test;
   - split any newly failing test against `f0d02f88` into new and pre-existing.
   Push and give the full hand-back for the independent review.

## Revision 4: one joint search for the U8412 neighbourhood, then Part B either way (2026-11-22)

Part A4 (`61de180b`, report `mc04-s8-a4-report-20261122.md`) is accepted as a study. U5209 lands (F 90°, 10.2 mm, R8263
6.56 mm from its `6093081c` position) and joins Part B. U5210 and U8409 fail in the same neighbourhood: both contend for
the space U8412 and U5208 need, and both blockers fit easily on their own. That points at the one-at-a-time search
order, not at the rules, so no rule is relaxed further.

1. **Part A5: joint search (study).** Search U5210, U8409, U8412, U5208 and U8408 (and any other block within 24 mm of
   them that the census names) together as one set, instead of target-first. The rules stay the same: every block is
   rigid, within 24 mm of its own position, under its own block rules, with any turn and face; displaced passives follow
   the A2 rule, C5210 follows the Revision 3 rule; and no input buffer other than the target U8409 moves. Jacks, slots,
   sleeves and locked parts stay where they are. Use an exhaustive or branch-and-bound search over the candidate
   poses of the set, so a failure is a proof for this set, not a greedy miss. Add a test that the search is complete
   for a small synthetic case.
2. **Then run Part B (Revision 3 item 4) without stopping:**
   - if A5 places both, apply all 15;
   - if it places one, apply 14;
   - if it places neither, apply the 13 ruled ICs and leave U5210 and U8409 open in `gate-a-open-items.json`, with the
     A5 proof and the cheapest option for each (U8412 or U5208 beyond 24 mm, the A2 far pose, or a fourth block) and its
     distance and electrical cost.
3. Write `mc04-s8-a5-report-20261122.md` and the Part B hand-back. Push and give the full hand-back for the independent
   review.

## Revision 5: stage 8 is the link-era re-placement record; the interim re-route waits for Gate A-paper (2026-11-22)

The Revision 4 stop (`d870ff95`, report `mc04-s8-a5-report-20261122.md`) is accepted. The finding is correct: the 15 ICs
are open only in the link-era model, where they sit under link keep-outs that do not exist on the interim GH boards.
Option (a) is ruled. Option (b) would move parts that have no reason to move on the interim boards.

1. **Record, don't apply.** Stage 8 becomes the link-era re-placement record. Record the 13 ruled poses, with their
   displaced passives and blocks and their acceptances, in the gate record (as a link-era re-placement set with its
   source commit and the model it was searched in). In `gate-a-open-items.json`, mark them resolved for the link era,
   pending application when the links replace the GH headers. The interim boards do not change.
2. **Run Part A5 under (a)**, as Revision 4 item 1 defines it, in the same link-era model. Record the result the same
   way. Leave any IC that A5 cannot place open, with the proof and the cheapest option, its distance and its electrical
   cost.
3. **State the model in every record.** Each S8 record and acceptance says "link-era model (`links_gate_part2.Field`,
   GH headers dropped, gate-displaced parts at paper positions); not checked against the interim boards". Keep
   `board_conflicts.py --check` as the evidence that the poses do not fit the interim boards.
4. **Part B is withdrawn, and Part C (the interim re-route) is on hold.** The stack is NOT ADOPTED until Gate A-paper
   (MC-04, #367). If it is adopted, the boards convert to links and are routed then, so an interim re-route now would
   be thrown away. If it is not adopted, the interim boards stay canonical and get routed. The Gate A-paper ruling
   decides which layout is routed.
5. Add tests for the record and the open-items status. Commit with `--check`, push, and give the hand-back. Stage 8
   then closes for the independent review.

## Revision 6: stage 8 accepted with fixes (2026-11-22)

The independent review of `463e6821` through `b37aa49c` accepts stage 8 with fixes, and finds nothing of high severity.
It confirmed that:
- the block rules and relaxations match the rulings;
- the electrical figures recompute (U1318 13.36 pF, U4417 23.1–38.13 pF, D1801 48.19 mm, R8263, C5210);
- `solve()` is complete over its grid, tested against an independent brute force;
- the record is deterministic, and `link-gate.json` changed only by the added section;
- no board, schematic or floorplan placement changed, and no test was weakened.

Fix the following, then give a short hand-back. This closes stage 8.

1. **Grid caveat.** The A5 proof and the 25–28 mm infeasibility hold on a 0.5 mm shift grid about each block's
   original origin, with 4 turns. Continuous poses are not covered. State this in the `proof` and `cheapest_option`
   fields of `link-era-replacements.json` and in the Gate A item. State that the 30 mm option is first-found, and
   that the true minimum farthest move lies in (28, 28.04] mm on that grid.
2. **The U8409 option supersedes U5210's pose.** The cheapest U8409 option re-places U5210 at B 0°, 16.81 mm, not at
   the recorded F 90°, 5.83 mm. Flag this in the record and the Gate A item, and correct the comment at
   `replacement_a5.py:188`.
3. **Electrical cost of the option.** Give run estimates (1.5 × HPWL, 0.20 pF/mm) for U5208 at 28.04 mm and U8408 at
   25.81 mm, per signal net, marking high-impedance, feedback and timing nodes, as Revision 4 required. Also state
   that the fourth-block alternative was not evaluated.
4. **Domain construction test.** Add a test of A5 domain construction: a synthetic case where a feasible pose must
   survive the filters. Make the infeasible-case test assert infeasibility, not `nodes >= 0`.
5. **C5210.** Record that its F→B flip adds a via on AC_NODE, which the HPWL metric does not count.
6. **U1318.** Mark the stage 7 U1318 acceptance (27.65 mm) superseded by the stage 8 link-era entry, and keep only the
   current one active in the floorplan report.
7. **Gate A items.** Add the link-era model statement to GA-LOC-U4417 and GA-LED-U4647, and use a move-distance
   field instead of `distance_from_slot_mm`. Count only re-placement rows in `re_placement_status`.
8. **board_conflicts.** Correct the A5 report: 10 of the 13 ruled ICs overlap a GH header (plus U4502), and U4417,
   U4526 and U4623 do not. Add U5210's A5 pose to `board_conflicts.py` so its evidence covers all 14.

## Revision 7: face-aware re-search of the four mixed-face blocks and the U5210/U8409 neighbourhood (2026-11-22)

Revision 6 (`1fbb22ea`, `e2d40451`, report `mc04-s8-r6-report-20261122.md`) is accepted; all eight fixes are done. The
new mixed-face finding is a real defect in the S8 search, and finding it was right. Revision 1–4 rulings accepted poses
"as studied". Those poses were never valid for U1415, U5110, U5209 and U5210, because the search put their
other-face passives on the block's face.

1. **Face-aware search.** Each block member keeps its own face relative to the block's IC. When the block flips face,
   every member flips with it. Members on either face are checked against the obstacles on their own face. Add a test
   with a mixed-face block, where an obstacle that only the other-face member hits must reject the pose.
2. **Re-search under the same rules.** Re-run U1415, U5110, U5209 and U5210 with the face-aware search under the rules
   each one was ruled with:
   - U1415 and U5110: the Revision 1 class (iii) rules, plus the A2 rotation and displacement;
   - U5209: the Revision 3 R8263 relaxation;
   - U5210, U8409 and the neighbourhood: the A5 joint search.
   Apply the 10 confirmed poses first. Also re-check those 10 with `member_faces.py`, and treat any that now fails the
   same way.
3. **What I accept without another ruling.** A new pose that lands within the same rules replaces the old one in the
   record, with the reason "face-aware re-search, Revision 7". Any block that no longer lands goes back to OPEN (link
   era), with its proof on the stated grid and its cheapest option: distance, which blocks move beyond 24 mm, and run
   estimates.
4. **U8409 option.** Re-run the 30 mm option search face-aware, and update the cheapest option and its run estimates.
5. Regenerate the record, the gate, the Gate A list and the reports. Every `--check` and all stack tests must pass.
   Push and give a short hand-back. Stage 8 then closes after a targeted review.

## Revision 8: two logic acceptances; the five analog blocks go to Gate A-paper (2026-11-22)

Revision 7 (`eacc7814`, `8fbcd06c`, report `mc04-s8-r7-report-20261122.md`) is accepted, pending a targeted review. The
second defect (Part A placed displaced passives on the block's own pose) was found and handled correctly.

1. **U4433 (25.5 mm) and U4526 (26.71 mm)** are logic blocks just past 24 mm. They are accepted as link-era locality
   exceptions on the U4417 terms. Record the poses and their per-net run estimates in `locality-acceptances.json` with
   the link-era model statement. Mark them RESOLVED FOR THE LINK ERA in the record and the Gate A list, and confirm
   they have no clock or RC timing node. If either has one, leave it OPEN and say so.
2. **U1415, U5110, U5209, U5210 and U8409 stay OPEN (link era).** Each would put a feedback, summing or high-impedance
   node 45–113 mm away, so no interim acceptance applies. They go to the Gate A-paper packet as NEEDS_DESIGN, with
   the remedies the packet must weigh: a slot move, a package split, a partition change, or the far pose with an
   electrical budget. Do not evaluate those remedies in this stage.
3. Regenerate the record, the gate, the Gate A list and the reports. Every `--check` and all stack tests must pass.
   Push and give a short hand-back. That closes stage 8.
