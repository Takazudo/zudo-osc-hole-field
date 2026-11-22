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

## Revision 3: manager ruling on the indicator crossings (2026-11-21)

The stop at step 3 is accepted (`f466a885`, `93197a3e`, report `mc04-s7-r2-report-20261122.md`). Ruling: option
(i), but narrow, and every piece of it reviewed before any board is touched.

1. **New crossing kind `indicator_led_bridge_one_span`** in `scripts/checks/io_partition60.crossing_kind`. A net
   qualifies only if every one of these holds, and each is checked from the partition, not from the net's name:
   - it is the `LED_A` or `LED_K` node of a `magnitude_indicator` unit;
   - the unit's op-amp, all four bridge diodes and its R_SENSE are in the same region, and only the panel LED is in
     the other region;
   - the op-amp is OPA4196IDR, the part MC04-S4 case 5 simulated at 7.2 pF (53.8°; 48.1° at 15 pF). An
     OPA4197 indicator does not qualify: the per-MPN paper screen now fails U8417's OPA4197 units at 30.9°, which
     needs its own simulation first;
   - the net crosses exactly one board boundary.

   Cite the evidence in a code comment: S4 report sha256 and case, the stage 1b result, and this ruling. Add tests
   for each failing condition (wrong MPN, a diode left on the other board, a second span, a non-indicator net).
2. **FILTER_LEDS island.** The panel LEDs D601–D604 keep `F1/FILTER_LEDS`. The moved indicator parts (U2119, its
   bridge diodes and RB2114–RB2117) take a new K-side island. Do this instance-scoped, through the same
   per-instance clone mechanism as the TSSOP retention, so F2 and F3 are unchanged. Update `test_filter.py` so it
   asserts the F1 split and the unchanged F2/F3.
3. **Instance-scoped relocation** for every moved block, as the report recommends.
4. **Recorded, no action:** U8417 units 3/4 screen at 30.9° only in the hypothetical cable case. U8417 stays on JR,
   where MC04-S5 simulated 61.2° at 0 pF.

Then finish Part A steps 3–6 and stop at the Part A checkpoint. The checkpoint report must show the io-partition
checker output, listing every allowed crossing by kind (the new kind's 22 nets by name) and zero forbidden
crossings.

## Revision 4: GH header sites (2026-11-21)

The stop is accepted (`651badb1`, `15876ae9`, report `mc04-s7-r3-report-20261122.md`). The io-partition checker
shows 0 errors, 0 forbidden crossings and 493 allowed crossings, 22 of them of the new kind.

Ruling: option (a). The GH board-to-board headers are the routed drafts' interim interconnect. DS-06 holds them
until Gate A, where the stack's FFC links replace them. Superseding them now (c) would be the Gate A integration
step, which this stage is not. Changing the 4-signals-per-header rule (b) would change a cable rule. So add sites
without changing any rule:

1. Add the two JL grid points (142, 122) and (159, 122) by extending that list's slice from 25 to 27 at its
   source. Make it a named, reviewed constant with this ruling, not a bare edit to the slice.
2. Add three JR sites, chosen by the same generator rules as the existing ones (same row or rule-consistent
   rows, same pitch and orientation). Check each new site against panel hardware pads, fixed footprints, outline,
   the stack link fields and slots in the current link gate, and every courtyard.
3. Report every new site with its coordinates, its nearest obstacle and clearance, and whether the link gate
   now displaces it or it displaces anything the gate placed.
4. Add a test that the packer fails clearly, not with an IndexError, when sites run short.
5. Then finish Part A steps 3–6 (floorplan, netlists, rail and power reports, pose tables, the acceptance note)
   and stop at the Part A checkpoint.

If no rule-consistent JR site exists for all three, stop and report the shortfall with dimensions. Do not
change the signals-per-header rule.

## Revision 5: Part A checkpoint review and rulings (2026-11-22)

Independent review of `651badb1`–`1c786a17` confirmed the following:
- Exactly the ruled 73 packages change region, instance-scoped, with F3 unchanged.
- The crossing count balances: 473 − 12 + 32 = 493.
- Exactly the 22 intended LED nets qualify for the new kind, with 0 forbidden crossings.
- The GH sites are legal and the bulk-capacitor reservation claim is correct.
- The acceptance records hold, and the rail and ledger are correctly unchanged.

One blocker and some follow-ups remain before Part B:

1. **Blocker: re-place header-released parts near their slots.** `header_conflicts`
   (`design/partition/partition35_floorplan.py` around 493–508, called around 689) puts released pins into `extra`,
   and `released = set(extra) | in_cluster` (around 220) sends them to the locality placer. That placer put U5112
   117.6 mm, U4523 108.1 mm and U4646 69.6 mm away. Fix:
   - keep the header-released parts as their own set;
   - re-place each displaced IC with its bypass capacitors as a rigid cluster from its pinned slot, as the swapped
     cluster loop does: `local_pose(nearest=True)` first, then `wide_pose`;
   - send passives through the near-slot loop on all three boards, adding JL to `EVICTED_LOCAL_BOARDS`.
   Add tests. Report every part still beyond 24 mm, with the blocking item and its dimensions.
2. **K reflow: minimal movement.** Unpinned K parts that the block moves or new headers do not displace keep their
   current poses: pin them from the 6093081c floorplan. Only displaced or relocated parts move. Report the
   resulting count and the largest moves per board, against 6093081c. The target is no part beyond 24 mm, except
   the ruled block moves and the accepted U1318/U8314.
3. **JR y=24 header row edge clearance.** It is 0.95 mm from the JR top outline (y=20). Every other jack header
   is at least 8.53 mm from an edge. Check it against the stack and enclosure edge features: card guides, the
   enclosure wall, K's outline in the stack projection, fixing sites and spacers. If any conflict exists, or the
   clearance is below the enclosure's stated edge keep-out, stop and report. Otherwise record the clearance in
   the report.
4. **Stale `k_poses`.** RB4313, D4319 and D8336 are evicted on K. Part B must use the floorplan poses, so make
   `k_block_poses.py` model the evictions or drop its pose output for evicted members.
5. NITs: make `sites.py` and `tables.py` use the repository root, not a home path. Require the indicator crossing's
   LED to carry a `panel_uid`, with a test. Note that the packer does not check reserves; the existing JR y=150
   row overlaps the `future-output-protection` reserve, which is recorded, not fixed here.

Then re-run Part A step 4 reporting and stop at the checkpoint again.

## Revision 6: rulings after the Revision 5 stop (2026-11-22)

The stop is accepted (`006ba3af`, `6da69765`, report `mc04-s7-r5-report-20261122.md`). Item 1 (near-slot rigid
clusters) and item 2 (reflow pins, 280 → 151 changed parts) are accepted.

1. **Replace JR-K-29 with (227, 24)**, option (a). It covers 8 small JR B-side parts and nothing on K. Option (b)
   would displace U4318 and U4343 on K. Re-place the 8 parts through the near-slot loop, and treat D4101 and
   D4102 as input-protection diodes under the existing diode locality rule.
2. **Check every GH site against fixings.** Add a generator check that every GH site, old and new, clears all
   active fixing and sleeve keep-outs on both mated boards, with a test, so this cannot recur. Revision 4's
   collision list missed fixings.
3. **The y=24 edge clearance is accepted**: 0.95 mm to the JR outline against the 0.30 mm rule, K mate 12.95 mm,
   enclosure wall 22.95 mm. Record that no card-guide or spacer geometry exists in the repository, so that
   interface is unchecked and stays open for the mechanical review.
4. **The 14 parts beyond 24 mm.** Classify each by function in a table: input protection, precision or 1V/oct
   path, decoupler, timing, general analog, logic. Then:
   - any decoupler beyond 3 mm from its IC supply pin, or any input-protection, precision or timing part beyond
     24 mm, is not accepted. For those, test the other rule-consistent GH site options on the same rows to see if
     any frees them, and report the cost (parts displaced) of each option;
   - general analog or logic parts beyond 24 mm may be recorded as locality exceptions caused by the interim GH
     headers, to be revisited when Gate A replaces GH with the stack links. Record them in
     `locality-acceptances.json` with this ruling.
5. Re-run the Part A step 4 reporting and stop at the checkpoint.

## Revision 7: Part A accepted, with two small items; then Part B (2026-11-22)

Revision 6 (`20e93027`, `ecfee728`, report `mc04-s7-r6-report-20261122.md`) is accepted: 154 changed parts, every
K move under 19 mm, the decouplers at 2.52–2.54 mm, and a test that fails on any unrecorded far move.

1. **The far input buffers get the U1318/U8314 conditions.** U5112 and U4646 (and U5113 if it is also a buffer;
   state its function) are high-impedance input buffers, not general analog. Keep their exception, but reclassify
   them in `locality-acceptances.json` under the Revision 2 conditions: input passives at the end their cell
   defines, a ground-flanked run, and added run capacitance under 50 pF, which MC04-S4 case 2 covers. Give each
   buffer's estimated on-board run length and capacitance. If any exceeds 50 pF, stop and report.
2. **The pre-existing JL-P utility header 4 at (91, 276) sits on the ruled sleeve SLV-L1 (93, 276).** Keep the ruled
   sleeve (DS-74/76) and move the header. Take the nearest rule-consistent site on its row that clears every
   fixing keep-out, every pad and every courtyard. Remove the entry from `KNOWN_FIXING_CONFLICTS`, so the fixing
   check has no exceptions. If no such site exists, keep the pin and report the options with dimensions. Do not
   take ALT-L1-A or ALT-L1-B; changing a ruled sleeve is a mechanical decision.
3. **Then run Part B (steps 7–9) without another checkpoint**, as long as items 1 and 2 pass. The pass and stop
   conditions in steps 7 and 8 still apply, and so does the `--max-share 25` stop for copper stripping. Part B
   ends with a full hand-back and an independent review before anything else.

## Revision 8: defer the pre-existing JL-P header conflict and run Part B (2026-11-22)

Item 1 of Revision 7 (`8471eedf`, report `mc04-s7-r7-report-20261122.md`) is accepted:
- U5112 and U4646 are under the input-buffer conditions, at 17–25 pF estimated (ASSUMED 0.20 pF/mm, 1.5 × HPWL);
- the input passives stay at the jack end;
- U5113 is the W2 indicator and stays an interim-GH exception.

Item 2: deferred, none of (a)–(c). The JL-P utility header 4 conflict with sleeve SLV-L1 predates this stage, and
every relocation trades it for a new displacement or a loom re-route. GH headers are the interim interconnect that
Gate A replaces with the stack links. Keep the `KNOWN_FIXING_CONFLICTS` pin, so the fixing check stays exact, with
its reason pointing to this ruling. Record the conflict in the stage report as **OPEN for the Gate A mechanical
review**, with the five candidate sites and their costs from the Revision 7 report. Do not move the header or the
sleeve in this stage.

Now run Part B (steps 7–9) with their pass and stop conditions, and the `--max-share 25` stripping stop. Then
push and give the full hand-back.

## Revision 9: stable GH header assignment, then finish Part B (2026-11-22)

The Revision 8 stop (`bb88acdc`, report `mc04-s7-r8-report-20261122.md`) is accepted as a correct stop: the
consecutive 4-net chunking in `connector_packing35` re-chunks every header after the first changed net, so 82
unchanged sites would carry different pin nets (322 moved signals) and the refdes would shift. Option (a) is
ruled. Option (b), re-routing all 82 headers, is not.

1. **Existing headers are stable.** Against the `6093081c` baseline, every header whose site still exists keeps
   its site, its refdes and every pin net whose net still crosses. Add the baseline assignment as a retained
   input (a JSON record with its source commit and SHA256), not as a value recomputed from the current netlist.
2. **Freed pins follow the existing rules.** A pin whose net no longer crosses becomes NC, unless the existing
   return/ground rule for that header class requires AGND at that position; then it becomes AGND. State which rule
   applied to each freed pin in the report.
3. **New nets fill the 5 new headers first, then freed pins.** Respect the existing signal-class grouping and the
   ground/return contact rule. Assignment order is deterministic (sorted by net name within class). Report every
   new net with its header, pin and the header's distance to the net's driving part.
4. **Refdes are site-stable.** Existing headers keep their refdes; new headers take the next unused numbers in a
   deterministic site order. A refdes is never reused for a different site.
5. **Tests.** Add tests that fail if (i) any baseline header changes site or refdes, (ii) any still-crossing net
   changes header or pin, (iii) a freed pin violates the NC/AGND rule, or (iv) two runs give different
   assignments. Keep `place.py`'s "board differs from source footprint origin" check as it is; the stable
   assignment must satisfy it, not bypass it.
6. **K region E5 overflow (R4547).** Resolve it by placing R4547 near its cell partner inside E5, or by a stated
   E5 region change with dimensions, under the near-slot rules of Revision 6. If neither fits, stop and report
   the overflow with dimensions and the candidates.
7. **Then re-run Part B steps 7–9** with the same pass and stop conditions: sync and place JL, JR and K; strip
   conflicting copper with the `--max-share 25` stop; DRC with no new non-unconnected errors; readiness 0;
   regenerate the link gate and attempt DA-03 c6 again (signals change, so a fresh c6 result is required, with
   the historical object still verified from its snapshot); regenerate fixings and the threading procedure; and
   run every stack test. The JL-P header 4 / SLV-L1 conflict stays OPEN for Gate A as ruled in Revision 8.
   Push and give the full hand-back, followed by an independent review.

## Revision 10: stable link clusters, then the rest of step 8 and step 9 (2026-11-22)

Step 7 of Revision 9 (`9601f0d5`, `65c8dd88`, `f0268f73`, report `mc04-s7-r9-report-20261122.md`) passes, subject to
the independent review now running. The step 8 stop is correct. Option (a) is ruled, for the same reason as the
Revision 9 header ruling: the link gate must not renumber links whose members did not change. Option (b) is not.

1. **Existing links are stable.** Retain the baseline gate's link membership and IDs as a recorded input (source
   commit and SHA256), as was done for the GH headers. Every baseline link whose member pairs all still exist keeps
   its members, ID and slot. A link that lost members keeps its ID with the remaining members. The greedy clustering
   runs only over pairs that no baseline link holds.
2. **New pairs.** A new pair joins an existing link with a spare position when it lies within that link's existing
   cluster radius; otherwise it forms a new link with the next unused ID. The order is deterministic.
3. **The JL-L02 hold stays valid.** The stale-hold rule must pass unchanged. Do not edit the hold to fit.
4. **The 4 new `fixing_reach` misses.** With stable clusters, re-check JL-K-26, JL-K-27, JR-K-28 and JR-K-29. If a
   pair now joins a link within the 40 mm reach, it passes. Any pair still beyond 40 mm is allowed only as an
   interim-GH exception: list it in the stage report with its distance and nearest declared fixing, and add a test
   pinning check.py at 108 plus exactly those listed misses. Do not change the reach limit, the fixing list or the
   declared flags. If any miss exceeds the exception reach in `fixings.exception_reach_mm`, stop and report.
5. **Tests.** Add tests that fail if a baseline link changes ID or members while its pairs exist, or if two runs
   give different clusters.
6. **Then finish step 8 and step 9.** Regenerate the link gate, attempt DA-03 c6 fresh (the historical object still
   verified from its snapshot), regenerate fixings and the threading procedure, and run every stack test. The
   staleness tests must pass. JL-P-4/SLV-L1 stays OPEN for Gate A. Push and give the full hand-back.

## Revision 11: the four new reach misses are interim-GH exceptions; finish step 8 and step 9 (2026-11-22)

The Revision 10 stop (`946e94b4`, report `mc04-s7-r10-report-20261122.md`) is accepted. My item 4 rested on a wrong
premise: `fixing_reach` measures each pair site against the declared fixings, so the link clusters cannot change
it, and the baseline already carries 108 misses, 91 of them beyond 50 mm (JR-K-1 at 119.5 mm). A 50 mm stop for new
pairs was stricter than the state it is measured against. Option (c) is ruled.

1. **Interim-GH exceptions.** JL-K-26 (41.6 mm), JL-K-27 (51.0 mm), JR-K-28 (118.5 mm) and JR-K-29 (84.5 mm) are
   recorded as interim-GH reach exceptions, with distance and nearest declared fixing, under the same Gate A revisit
   as the other interim-GH items. JR-K-30 (16.6 mm) passes. Add a test that pins check.py `fixing_reach` at the 108
   baseline missed pairs plus exactly these four, by pair ID; any other change fails it. Do not change the reach
   limits, the fixing list or the declared flags.
2. **Not ruled here.** Declaring the stack sleeves as fixings (option b) is a mechanical fixing-list decision for
   the Gate A review. Record it there as a candidate with the SLV-U2 figure (JR-K-29 to 17 mm), and do not apply it.
3. **Then run Revision 10 items 1–3, 5 and 6 as written:** stable link clusters, deterministic new links, the
   JL-L02 hold unchanged, the cluster tests, the gate and DA-03 c6 regeneration, fixings and procedure regeneration,
   and every stack test passing. Push and give the full hand-back.

## Revision 11 addendum: step 7 review findings to fold into the Part B hand-back (2026-11-22)

The independent review of `9601f0d5`, `65c8dd88` and `f0268f73` accepts step 7 with fixes. The baseline record, the
stable packer, the `--renetted-uuids` pass (all 49 removed items had changed net in the sync), the R4547 move and
readiness all check out, and no guard was weakened. Fold these fixes into the Revision 11 work and hand-back:

1. **Stale checkpoint tests.** Six tests that passed at `8ecc25fe` now fail because the K board bytes changed:
   four in `scripts/checks/test_osc_pcb_checkpoint.py`, `test_copper_identity.py::…six_known_legacy_groups` and
   `uuid305/test_run_protocol.py::…bound_exactly`. Do not refresh the K checkpoint now; the boards are re-routed next
   and the checkpoint is refreshed from that accepted evidence. List all six in the report as STALE (expected,
   pending re-route), together with the JL/JR checkpoint tests that were already stale at the base.
2. **Correct the report.**
   - K loss is 0.32 % (186.19 of 58546.66 mm), not 0.45 %.
   - The refilled headers are JR-K-12/13/20 and JL-K-3/4/21/22 (12 slots).
   - The missing commit `cf16f3a8` should be `f0268f73`.
   - The DRC summaries cap several types at 199 items, so "new" dangling or silk counts are not provable from them.
     Either commit the raw per-item DRC JSON for before and after and compute the deltas from it, or state the cap and
     claim only what the summaries show: no error-severity items before or after, parity 0, and unconnected items JL
     323→484, JR 245→358, K 499→499.
   - Also report the K H2 B.Cu region growth (y 132.61→138.22), R210's 13.0 mm move, and R4547's 23.58 mm distance
     from its `6093081c` position (0.42 mm under the far-move threshold).
3. **Deliver Revision 9 item 3:** a committed table of every new net with its header, pin and distance to its driving
   part. Refresh `scripts/stack/studies/mc04_s7_r4/tables.json` so `new_headers` includes JR-K-29.
4. **Tests.**
   - Run the `test_gh_stable` checks (i)–(iii) against a fresh `cp.candidate()` as well as the committed JSON. A packer
     reverted to consecutive chunking must fail them.
   - Make check (iv) run in two processes with different `PYTHONHASHSEED` values.
   - Remove the dead assertion at `test_gh_stable.py:62`, and add a pin-level test of freed-slot filling and NC/AGND.
   - Add a unit test for the `apertures=` path in `header_conflicts`.
   - Pin the site-overflow message again in `test_connector_packing35.py` with its new wording.
5. **Freed pin 7.** On a 7-pin octave header with a freed, unrefilled slot 3, pin 7 follows the fresh-header rule
   (AGND), per Revision 9 item 2. Add a test; the current data does not exercise it.
6. **Replayability.** Store the full baseline SHA (`6093081cc6d1…`) in the record, and commit the `--renetted-uuids`
   input list with its source DRC file hash.

## Revision 12: eviction avoids sleeve keep-outs; redo JR step 7 only (2026-11-22)

Revision 11 and its addendum (`9c87d534`, `60495931`, `26256e9a`, `55a879af`, report `mc04-s7-r11-report-20261122.md`)
are accepted up to the fixings stop: the reach pin, the stable clusters (JL-L02 hold unedited), the fresh c6 with
pre-c6 positions matching the snapshot, the regenerated chain and the review fixes. Option (a) is ruled, because the
fault is in the generator: near-slot eviction ignored active sleeve keep-outs. Option (b) would hand-place parts
around a generator bug.

1. **Generator fix.** Near-slot eviction in `scripts/checks/partition35_floorplan.py` treats every active sleeve
   keep-out (the ruled DS-74/76 sleeves, from the same source `fixings_check` uses) as occupied, on the board and
   side the keep-out applies to. Add a unit test where the nearest free position lies inside a sleeve keep-out and
   eviction must take the next one.
2. **Scope.** Re-run the floorplan. Only parts whose position changes because of item 1 may move; list them with
   the old and new positions and slot distances. If any part other than D4101, D4102, R8425 and R8426 moves, or any
   move exceeds the 24 mm far-move threshold, stop and report.
3. **Redo step 7 for JR only** (and for any other board item 2 shows changed): sync, place, strip with the
   `--max-share 25` stop, DRC with no new error-severity items, parity 0 and readiness 0. Then regenerate the gate,
   c6 check, fixings and procedure. `fixings_check` and every test in `test_fixings` must pass.
4. **K:U4129 under the JR-L04 slot.** List it with the other 13 unresolved re-placements, with its overlap
   dimensions, as an open item for the re-route. Do not move it in this stage unless item 1 moves it.
5. **Stale-test split.** Use `uv run --with pytest` (or a venv) to run `test_osc_pcb_checkpoint.py`,
   `test_copper_identity.py` and `uuid305/test_run_protocol.py` at `8ecc25fe` and at the new head. Report which
   failures are new against `8ecc25fe` and which are pre-existing, so the STALE list is exact.
6. Push and give the full hand-back. That closes Part B for the independent review.

## Revision 13: keep-out-displaced parts go last; D4101/D4102 as interim-GH acceptances (2026-11-22)

The Revision 12 stop (`bf161c00`, report `mc04-s7-r12-report-20261122.md`) is accepted. Option (a) is ruled. Run 1
cascades through three unrelated parts (D8311 moves 24.07 mm), and option (c) would move more parts with no
computed result. Run 2 confines the change to the four parts the sleeve keep-out displaced.

1. **Apply the patch with a placement-order rule.** Apply `scripts/stack/studies/mc04_s7_r12/sleeve-eviction.patch`
   to the generator, with the rule that parts displaced by a sleeve keep-out are placed after every other evicted
   part. Move the 4 study tests next to the generator's tests, and add one that pins the order: a keep-out-displaced
   part never takes a position another evicted part would have taken. Re-run the floorplan. It must reproduce run 2:
   only D4101, D4102, R8425 and R8426 move. If any other part moves, stop.
2. **D4101 and D4102** (BAT54S protection diodes, about 34 mm from their slots) go in `locality-acceptances.json` as
   interim-GH locality acceptances under this ruling, revisited at Gate A. Protection diodes are more sensitive to
   distance than pull resistors, so record for each: the net it protects, the protected pin, and the distance from
   the diode to that pin and to the GH header contact it guards. Add both to the Gate A open list as
   protection-locality items.
3. **Then run Revision 12 items 3–6 as written:** the JR-only step 7 redo, the gate, c6, fixings and procedure
   regeneration with `fixings_check` and `test_fixings` passing, K:U4129 on the open re-placement list, and the
   stale-test split against `8ecc25fe`. Push and give the full hand-back.

## Revision 14: Part B accepted with fixes (2026-11-22)

The independent review of `9c87d534` through `063aa6d6` accepts Part B with fixes. Confirmed:
- the link-cluster baseline (rebuilt from `93197a3e`) and the 32 stable clusters, with the JL-L02 hold unedited;
- the reach pin, exactly 108 + 4 by pair ID, with the limits and the 30 declared fixings unchanged;
- c6 rebinding only geometry and output, with all 8 c6 link records byte-identical;
- the floorplan moving only D4101, D4102, R8425 and R8426;
- the netlist distances in the acceptances;
- the JR redo (segments, vias and zones identical);
- the addendum items;
- the stale-test split.
No test was weakened or skipped. Fix the following, then give a short hand-back. This closes stage 7.

1. **Open re-placements are 15, not 14.** The r13 JR-K-JR-L01 slot move displaces JR:U4647 (SOIC-14, B, old position
   (296.68, 52.47)), which has no position. Add it to the open list for the re-route with its overlap dimensions,
   and report the other effects of the same move: front B also displaces C4675, D4402, D4514, D4515, D4517, D4601
   and R4612; K C4321 is newly displaced; U4324 and U4329 turn to F; and the totals shift (K B 270→269, K F 65→64,
   turned 7→9, ICs with no position 14→15).
2. **Stale drawing.** Regenerate `design/partition/board-stack-candidate.svg` so `partition35_drawing.py --check`
   passes, and run `scripts/partition/regen.sh --check` and `scripts/checks/regen-all.sh --check` to confirm
   nothing else is stale.
3. **The order rule needs a generator-level test.** Today, swapping `evicted_order(...)` for `sorted(evicted)` at
   `partition35_floorplan.py:546` still passes all 7 sleeve tests. Add a test that drives `apply_adopted_pins` (or
   compares a fresh floorplan build against the committed one) and fails under that mutation.
4. **Stale study table.** Regenerate `scripts/stack/studies/mc04_s7_r4/tables.json` for the four moved parts, and
   give `tables.py` a `--check` mode.
5. **Redo record.** Correct R8425 and R8426 `before_kicad` to F.Cu, −90, as on the `55a879af` board. Either commit
   the raw per-item DRC JSON behind the "132/129 re-keyed silk items" note, or reduce the note to what the summaries
   show.
6. **Report the slot drift.** `stable_clusters` keeps IDs and members, not slots, and new pairs join within the 35 mm
   gate radius. Both are accepted as built. State them in the stage report, and list JR-L03 (moved in r11) and
   JR-L01 (moved in r13) as slot drift for the Gate A review.
7. **Pre-existing failures.** List `test_partition35_evicted_cap.py::test_d4309_is_within_the_cap_or_reported` and
   the 13 failures in `scripts/stack/{mechanics,power_posts,sub_toggle,thermal,trimmers}` as PRE-EXISTING (failing
   since at least `8ecc25fe` or `69461dff`), and narrow the report's "tests pass" claim to match.
8. **Gate A open list.** Give `design/stack/gate-a-open-items.json` a small generator with `--check`, or a test that
   checks it against its sources. Add the four interim-GH reach exceptions by ID, the 15 open re-placements, the
   interim-GH locality exceptions and the slot drift from item 6. Rebuild the declared-count assertion in
   `test_fixing_reach_exceptions` from the `69461dff` source, not from the current report.
