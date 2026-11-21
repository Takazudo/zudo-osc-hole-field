# MC04 stage 6 native brief: carry the OPA4197IPWR swap into the JL/JR boards and the stack geometry

- Campaign / task ID / attempt ID: osc-stack-20261114 / MC04-S6-BOARD-SYNC / 20261121-1
- State: **PLANNED (not admitted)**. The WSL session fills the environment and admission fields before any run.
- Top-level manager: Claude Project lead, thread "Resume OSC instrument order-readiness campaign", branch
  `claude/project-thread-iw3gai`. Sole dispatcher on the device: the WSL Claude Code session the owner starts.
- Parent: MC04-S5 accepted (`mc04-remedy-decision-packet-20261120.md`, "Stage 5 result"); owner decisions
  2026-11-21 10:18Z and 12:55Z.
- Independent reviewer: a separate reviewer session or subagent that did not write the change.

## Why this stage

The schematic and floorplan now carry six OPA4197IPWR packages, but `boards/osc-jack-left` and
`boards/osc-jack-right` still hold the SOIC-14 footprints, so `instrument_readiness.py` reports 24 mismatches
(six refs × footprint, MPN, Value, LCSC). The stack geometry is also stale: a cloud run of
`python3 scripts/stack/geometry/links_gate.py --stdout` at `98a0cf22` differs from the committed
`design/stack/geometry/links/link-gate.json` in `ds97.displaced_counts` (OPA4197IDR 5→4, OPA4197IPWR 3→9) and
in three provenance hashes (`rail-ledger.json`, `floorplan-candidate.json`, `partition.json`). `regen-all.sh`
does not regenerate `link-gate.json`. The K-board block moves (stage 7) must start from a synchronized scene.

## Goal and non-goals

Goal: synchronize JL and JR with the current schematic and floorplan, regenerate the stack link gate, and report
the MC04 unresolved-IC set after the swap.

Non-goals: no K-board block moves (stage 7), no panel hardware movement (`design/grid/placements.lock.json` and
all 438 locked centres stay), no change to the stock-FFC links, no new routing, no fabrication files, no order.

## Steps

1. Start with `bash scripts/checks/regen-all.sh`; commit any tracked regeneration separately.
2. **D4309 distance cap (source change).** The floorplan's `local_pose` (`design/partition/partition35_floorplan.py`)
   ranks evicted parts by net-growth cost, which put D4309 21.5 mm from its slot (26.4 mm from U4346) although free
   B.Cu poses exist about 4–7 mm away (for example 261.85, 39.95). Add a distance cap for evicted input-protection
   diodes (the 24 mm rule of `design/partition/precision-tssop-retention.json` applied to the diode-to-IC distance,
   or nearest-legal first within it), with a unit test, then regenerate. Report D4309's new pose and distances.
   If the cap leaves no legal pose, report the conflict with dimensions and keep the current pose.
3. **Board sync.** Export the JL/JR netlists and run `scripts/pcbgen/sync.py` and `scripts/pcbgen/place.py`
   through `scripts/kicad/run.sh` as `scripts/pcbgen/README.md` describes, so the six TSSOP-14 footprints sit at
   the floorplan poses. Existing routed copper on these drafts must not be silently deleted. If sync would orphan
   or invalidate tracks, report which nets and stop before saving. Fixed hardware must return to its lock position.
4. **Stack geometry.** Regenerate `design/stack/geometry/links/link-gate.json` and `link-gate.md` with
   `python3 scripts/stack/geometry/links_gate.py` (about 3 minutes in the cloud) and the readme generators. Fix the
   two known gate defects first, each with a test: (a) `place()` ignores the caller's `accept` filter, so a way-2
   link could take a site without an accepted short-tail site; pass `accept` through `place()` and `search()`
   (callers in `scripts/stack/geometry/links_gate_part2.py` around lines 219–222). It is inert in the current
   record (61 placed links, 0 way-2 placements), so expect no placement change. (b) `generate()` embeds
   `link-gate-a7-comparisons.json` (`links_gate.py` around line 1566) but `input_hashes()` does not hash it; add
   it to the provenance inputs. Re-run `scripts/stack/geometry/check.py` and the
   stack geometry tests.
5. **MC04 recount.** Re-run the retained MC04 capacity census
   (`scripts/stack/studies/mc04_c1_capacity/capacity.py`) against the synchronized scene with a new output
   path, and report which of the original 26 unresolved ICs remain unresolved (expected: the six input buffers
   resolved on their front boards; 20 remain: U1417, U2218, U2119, U4347, U4348, U8318 and K's 14).

## Report (completion and hand-back)

Push to `claude/project-thread-iw3gai`, then report:
- the commits (source changes separate from regeneration) and the sha256 of every regenerated board,
  `link-gate.json` and the census result;
- D4309's pose and distances, and any other part whose distance from its slot grew;
- `instrument_readiness.py --check` (expected: 0 mismatches), KiCad 10.0.6 DRC with schematic parity on JL and JR
  (report counts by type; unrouted is expected), `pnpm circuit:check` before and after, `regen-all.sh --check`,
  the new tests, `scripts/stack/geometry/check.py`, and every other check run, with PASS / FAIL / NOT RUN and the
  reason.

## Environment and budget (WSL session fills these)

- Model / effort / session ID: record from the client, not self-description.
- KiCad 10.0.6 only through `scripts/kicad/run.sh` with the pinned image; a missing oracle is a failure.
- Use the machine-wide heavy guard; one native job at a time.

Native result: **NOT RUN** at this brief. Every schematic and PCB remains an unvalidated draft.

## Revision 1: manager ruling on the stopped board sync (2026-11-21)

The run (`285086b1`, `065df168`, `354beaf8`) stopped correctly before saving: syncing the six TSSOP-14
footprints would orphan 92 routed copper ends on 48 nets (JL 44 on 22, JR 48 on 26, including ±12 V), recorded in
`mc04-s6-sync-stop-20261122.json`. The link-gate fixes, the D4309 cap and the regeneration are accepted for
review separately. D4309 stays a reported fit conflict at 21.27 mm.

Ruling: these boards are unvalidated drafts, and stage 7 moves six blocks off JL/JR, which changes the routing on
those boards again. So do not re-route now. Proceed as follows:

1. Write a small, tested script (for example `scripts/pcbgen/strip_swapped_stubs.py`, run through
   `scripts/kicad/run.sh`) that removes only the copper attached to the swapped packages' pads. For each copper
   end on a pad of U1216, U1416, U1518, U4346, U8314 or U8417, follow the connected track segments to the first via,
   pad of another part, or T-junction, and remove that chain. Do not remove the via, any zone, any other track or any
   unowned item.
2. Write every removed item to a retained record
   (`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s6-stripped-stubs-20261122.json`): board, UUID,
   net, layer, endpoints, width. Fail if a chain reaches more than 20 mm or touches a zone; report it instead.
3. Run `sync.py` and `place.py` on the stripped boards and save. Then run KiCad 10.0.6 DRC with schematic parity on
   JL and JR. Report counts by type against the committed boards. New unconnected items on the 48 nets are
   expected and must be listed. Any other new violation (clearance, shorts, courtyard) is a failure to report, not
   to suppress.
4. Confirm `python3 scripts/checks/instrument_readiness.py --check` reaches 0 mismatches, then run
   `regen-all.sh --check`, `pnpm circuit:check` and the stack geometry checks.

The re-route of JL and JR is deferred to the routing pass after stage 7 and is recorded as open; it is not a pass.

### Revision 1 addendum from the independent review of `285086b1` and `354beaf8`

Both commits are accepted: the link-gate fixes are correct, and `links_gate.py --stdout` reproduces `link-gate.json`
byte for byte in the cloud. D4309 is a real fit conflict. Under the floorplan's own courtyard, panel-hardware,
outline and 0.35 mm gap model, no legal B.Cu pose lies closer than 21.27 mm. The "4–7 mm" poses came from a raster
scan that ignored those obstacles. Also do these in the same push:

5. Reword the comment at `scripts/checks/partition35_floorplan.py:47-49` (and this brief's step 2 premise stays as
   history) to "no legal pose within 21.27 mm under the floorplan's courtyard, hardware and gap model".
6. `scripts/stack/geometry/links_gate.py:70-72` builds the a7 path from `links.LINK_DIR`, not from `inp['root']`;
   with a non-default root `relative_to` raises. Build it from the root, with a test.
7. Add a test that the emitted D4309 distance is either within 24 mm or listed in `evicted_diodes_beyond_cap`.
8. Three stack-geometry tests already failed at `89ddd104`: `stack-candidate.json` and `link-candidate.json` are stale
   against `design/partition/partition.json`, and `GatePart3.test_finding_9` (71.96 vs 73.46) follows from that.
   Regenerate those two candidates with their own generators so that stage 7 starts from a consistent stack, and
   report the test results.

## Revision 2: manager rulings after the synced boards (2026-11-21)

Accepted from `3057f3fc`–`583140de`: the six TSSOP-14 packages are on JL/JR, 217 stub items were stripped and
recorded, readiness reconciles with 0 mismatches, and the stack and link candidates are regenerated. Three items
are open:

1. **The 25 reposed parts (JL 23, JR 2) are a regression and must be fixed now.** `sync.py` re-applied the
   netlisted side and angle to parts that the floorplan had reposed, which added shorts, clearance, hole, courtyard
   and mask errors (JL 86 / 40 / 27 / 39 / 96, JR 12 / 5 / 8 / 7 / 13). The floorplan is the generated source of
   poses, so the board must match it. Do not exclude parts from sync. Find why the schematic attributes
   (`BoardSide` / angle, or `FootprintOriginMm`) for these 25 disagree with `design/partition/floorplan-candidate.json`.
   Fix it at the source (the generator that writes those attributes from the floorplan), regenerate the netlists,
   re-sync and re-place, and save. Pass condition: DRC with parity on JL and JR shows no new shorts, clearance,
   hole, courtyard or mask errors relative to the pre-S6 committed boards (`2cd30044…` for JL and the JR
   equivalent); new unconnected items only on the 48 stripped nets. If a part cannot reach its floorplan pose,
   report it with dimensions; do not move panel hardware.
2. **Rebind the DA-03 c6 pass as a new attempt; do not hand-edit its pins.** `scripts/stack/geometry/links_gate_c6.py`
   refuses the regenerated source record because the displaced-footprint evidence changed. Run the pre-c6 gate on
   the synced scene. Then show whether c6's own output (positions and the three coupling riders) is identical to the
   retained `OUTPUT_LINKS_SHA256` output, apart from the displaced-footprint fields:
   - If it is identical, update the source pins with a comment naming this rebind and the source commit. Add a test
     that the output-link digest, excluding the displaced fields, is unchanged. Then regenerate
     `link-gate.json`/`link-gate.md` and re-run the three failing stack tests.
   - If any position, rider or link differs, stop and report the difference.
3. **The JL/JR re-route stays OPEN**, deferred to the routing pass after stage 7, as already ruled.

Report in the same format as before, with DRC counts by type before S6, after rev 1 and after rev 2.

## Revision 3: ruling after the stopped revision 2 (2026-11-21)

Finding accepted: the source already matches the floorplan. The routed JL/JR drafts had drifted from it before S6
(37 JL and 12 JR parts off-floorplan by up to 50.9 mm), and their copper was routed around the stale poses. That
copper has no validated status, and stage 7 re-routes these boards. Placement correctness comes first:

1. Move every off-floorplan part on JL and JR to its full floorplan pose (position, side and angle), as in the trial.
2. Then remove only the copper that DRC reports in a short, clearance, hole-clearance or mask conflict with a moved
   part. Follow each conflicting track segment to the nearest via, pad or T-junction, as the stub tool does, and do
   not remove zones, unowned items or any copper that is not in conflict. Re-run DRC and repeat until no new
   short, clearance, hole, courtyard or mask error remains relative to the pre-S6 boards.
3. Record every removed item in `mc04-s6-stripped-conflicts-20261122.json` (board, UUID, net, layer, endpoints,
   width, the DRC item it cleared). Report the removed track length as a share of each board's routed track length.
   **Stop and report before saving if either board would lose more than 25 % of its routed track length.** At that
   scale a fresh route is the better path, and the choice goes back to the manager.
4. Pass condition as in revision 2: no new non-unconnected DRC errors against pre-S6, parity clean, readiness 0
   mismatches. List the new unconnected items by net.
5. Then do revision 2 item 2 (the c6 rebind, identical output only) and push.

The re-route stays OPEN and moves to the routing pass after stage 7.
