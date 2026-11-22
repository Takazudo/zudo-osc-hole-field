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
