# MC04 stage 7 native brief: move six front-board blocks onto K and place K's unresolved ICs

- Campaign / task ID / attempt ID: osc-stack-20261114 / MC04-S7-K-BLOCK-MOVE / 20261121-1
- State: **PLANNED (not admitted)**. The WSL session fills the environment and admission fields before any run.
- Top-level manager: Claude Project lead, thread "Resume OSC instrument order-readiness campaign", branch
  `claude/project-thread-iw3gai`. Sole dispatcher on the device: the WSL Claude Code session the owner starts.
- Parents: the owner chose option D in stages (2026-11-21), and stages 1a, 1b and 4–6 were independently reviewed
  (`mc04-remedy-decision-packet-20261120.md`). The starting point is commit `42e78b4d` or later.
- Independent reviewer: a separate session or subagent that did not write the change.

## Scope

After stage 6, 20 of the original 26 unresolved ICs remain:

| Group | ICs | Action |
| --- | --- | --- |
| JL blocks | U1417, U2119, U2218 | move to K as functional blocks |
| JR blocks | U4347, U4348, U8318 | move to K as functional blocks |
| K | U1415, U4324, U4417, U4433, U4524, U4526, U4527, U4623, U4635, U5110, U5209, U5210, U8409, U4341 | place on K |

A functional block is the IC plus its decouplers and its one-hop passives and diodes, as
`scripts/stack/studies/mc04_c4_blocks/blocks.py` defines it. Use the reviewed **keep-front boundary**
(`--keep-front _PROTECTED ISO_MID`): the protection and isolation parts stay on the front board. Under the stage 1a
limits this moves U1417 and U2218 with no extra shielding. The indicator LED nets of U2119, U4347, U4348 and U8318
then cross, and stage 4 simulation allows that for one cable span only (about 15 pF per LED net; OPA4196 margin
53.8° at 7.2 pF, 48.1° at 15 pF, against the ASSUMED 45°).

Non-goals: no panel hardware movement (`design/grid/placements.lock.json`), no change to the stock-FFC cable family,
no routing (the JL/JR/K re-route is the next stage), no fabrication files, no order, no hardware.

## Part A: source change and regeneration (checkpoint before any board is saved)

1. Start with `bash scripts/checks/regen-all.sh`, and commit any tracked regeneration separately.
2. Recompute the block membership and crossing nets for this six-block subset with `blocks.py` and
   `scripts/stack/studies/mc04_c5_crossing_nets/nets.py` (new output paths). Then re-run
   `scripts/stack/studies/mc04_s1_budgets/budgets.py` and `mc04_s1b_indicator_loops/loops.py` on the new lists.
   Stop and report if any net fails its draft limit, if any crossing net is raw-sensitive or forbidden, or if an
   LED net would cross more than one cable span.
3. Find the source mechanism that assigns a part to a board region (the `io_partition` region / `BoardRegion`
   path). Implement the move as a reviewed, retained source input, for example a block-relocation list beside
   `design/partition/precision-tssop-retention.json`, that names each block's members and fails on a stale or
   unmatched entry. Add tests. Do not edit generated partitions, floorplans or netlists by hand. If the move needs
   changes to module cell definitions beyond region assignment, stop and report.
4. Regenerate the partition, io-partition, floorplan, schematics, netlists, rail and power reports. Report:
   - each moved block's K pose and its distance from its old front-board centre;
   - every K IC's pose;
   - every part whose distance from its slot grew;
   - the new cable-link signal assignment (positions used against the 75 JR and 128 JL spare positions).
5. U114 and U115: re-place each displaced IC together with its decouplers. Keep the bypass capacitors on the IC's
   face and within the pre-move distance (5.4 mm for U115), and the hold capacitors no farther than now. If that is
   impossible, report it and compare with retaining the old JL-L02 slot (cost 19.0, 11 parts covered).
6. **Checkpoint: push Part A and hand back before Part B.** The manager reviews it independently first.

## Part B: boards and stack (after the manager accepts Part A)

7. Sync and place JL, JR and K (`scripts/pcbgen/sync.py`, `place.py`). Strip only copper that DRC flags against
   moved parts, with the revision 3 tool and its rules (`scripts/pcbgen/strip_drc_conflicts.py`,
   `--max-share 25`), and record it. Pass condition: no new short, clearance, hole, courtyard or mask errors on any
   of the three boards, clean parity, and readiness 0 mismatches.
8. Regenerate the link gate. The link signals change in this stage, so DA-03 c6 needs a **new attempt**, not a
   rebind: run its conductor-order pass on the new signal set, re-pin all of its source pins with provenance, and
   keep the historical snapshot verifiable. Then regenerate the fixings and threading procedure and run every
   stack test file.
9. Push and hand back.

## Report (each hand-back)

Commits (source separate from regeneration); sha256 of every regenerated record and board; the tables in steps 2,
4 and 5; DRC counts by type before and after on JL, JR and K; every check with PASS / FAIL / NOT RUN and the
reason: `pnpm circuit:check` before and after, `regen-all.sh --check`, `instrument_readiness.py --check`, the new
tests, all stack tests, `scripts/stack/geometry/check.py`.

## Environment and budget (WSL session fills these)

- Model / effort / session ID: record from the client, not self-description.
- KiCad 10.0.6 only through `scripts/kicad/run.sh` with the pinned image; a missing oracle is a failure.
- Use the machine-wide heavy guard; one native job at a time.

Native result: **NOT RUN** at this brief. Every schematic and PCB remains an unvalidated draft.
