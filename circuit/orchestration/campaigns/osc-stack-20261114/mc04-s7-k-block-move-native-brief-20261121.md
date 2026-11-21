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

## Revision 1: manager rulings on the stopped Part A (2026-11-21)

The stop is accepted. The current gate (`16ef5ab8`) leaves 23 unresolved ICs, not 20.

**Ruling 1: tooling.** Leave the pinned MC04-R1 scene and the retained study results untouched as history. Add a
current-scene mode to `blocks.py` and the capacity census. It takes the unresolved list from the current
`design/stack/geometry/links/link-gate.json` displacement record and the current boards, records the input
sha256 of every file it reads, and fails on a stale input. It must not hard-code an IC set. Add tests. Re-run the
stage 1a and 1b budget scripts against the current-scene output the same way.

**Ruling 2: block set, by function.** Stage 1a found that an input buffer cannot move across the cable, because
its protected node fails crosstalk. So:

| IC | Function | Treatment |
| --- | --- | --- |
| U1417, U2218 | general output | move to K (keep-front boundary) |
| U4347, U4348, U8318, U2219 | magnitude indicator | move to K; each LED net one cable span only |
| U2119 | magnitude indicator | no longer displaced; leave it |
| U1318 (O3, OPA4197IDR), U2217 (F2, OPA4196IDR), U8314 (M4A, OPA4197IPWR) | high-impedance input buffer | stay on their own front board; re-place locally |
| K's 14 | — | place on K |

**Ruling 3: evidence before any source change (Part A0).** The new displacements come from the link moves after
stage 6 (JL-L02's new slot covers U2217 and U2219, JL-L08 covers U1318, JR-L04 covers U8314). Before changing any
source, report two cases from the current-scene census:

- (a) the current gate selection, with U1318, U2217 and U8314 re-placed locally on their own board and face. Give
  the nearest legal pose for each in its current package, with distance from its slot and whether it is within
  24 mm;
- (b) the retained JL-L02 slot ([121.5, 80]; cost 19.0, 11 parts covered). List those 11 parts by function and
  the unresolved-IC set that results.

Do not swap U2217 to OPA4197IPWR. That would add about +3.4 mA typical and +5 mA maximum on each analog rail, and
the +12 V contract margin is already 0 mA, so it is an owner decision. If a buffer has no legal local pose in case
(a), say so with dimensions. Push the tooling, tests and the A0 report, hand back, and wait for the manager's
choice between (a) and (b) before Part A step 3.

## Revision 2: manager choices after Part A0 (2026-11-21)

Part A0 (`7e11ad70`, `afca53ca`, report `mc04-s7-a0-report-20261122.md`) is accepted. Choices:

1. **Case (b): hold JL-L02 at its retained slot (121.5, 80).** It costs 2.5 more than the current slot, but it
   leaves U2217 and U2219 where they are, which avoids U2217's 60.25 mm move. U2119, an F1 indicator, moves to K
   as a function block instead of U2219. D2243 is re-placed locally. Record the hold as a retained, reviewed gate
   input with a reason and a test; do not change the gate's general selection rule. Also report the four K parts
   the slot's field displaces (C133, U111, U113, U118) and where they land.
2. **U4347 takes the keep-front boundary**, the same rule as U1417 and U2218. Its ISO_MID nets stay on JR, and no
   shielding is needed.
3. **U1318 and U8314 are accepted beyond 24 mm** (27.65 mm and 32.25 mm, on their own board and face). The 24 mm
   rule is a locality rule. The electrical question it stands for is the added node capacitance, and MC04-S4
   case 2 covers that: 0–50 pF on `*_SENSE` and `*_BUFFER`, no oscillation, settling and overshoot recorded, for
   both OPA4196 and OPA4197, including the precision follower. Conditions, to be carried into the re-route:
   - keep the input passives (R_LIMIT, clamp) of each buffer at the IC end or the jack end as their
     cell defines, and report which;
   - route the lengthened run as a ground-flanked trace;
   - keep the added run capacitance under 50 pF.
   Record this acceptance in the floorplan report.
4. **Budgets table:** make `scripts/stack/studies/mc04_s1_budgets/budgets.py` read the input-capacitance and GBW
   facts per MPN. OPA4197IPWR has `fact-op-precision-input-impedance` (6.4 pF common mode) and
   `fact-op-precision-gbw` in `.claude/skills/component-ti-opa4197ipwr/`. Regenerate the retained 1a/1b results,
   and report any verdict that changes.

Then continue with Part A steps 3–6 for this block set and stop at the Part A checkpoint:
- JL: U1417 and U2218 (keep-front), U2119 (indicator);
- JR: U4347 (keep-front), U4348 and U8318 (indicators);
- K: its 14 ICs;
- local: U1318, U8314 and D2243, plus U114/U115 with their decouplers.
