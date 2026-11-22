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
