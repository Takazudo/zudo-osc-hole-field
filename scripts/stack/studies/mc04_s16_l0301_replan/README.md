# MC04-S16: L03.01 re-plan study

Study code for MC04-S16. The brief is
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s16-l0301-replan-brief-20261128.md` (Revision 4,
SHA-256 `a638d4b8…36e7b4`). The report is `mc04-s16-report-20261128.md` in the same folder. All output is rows-level
evidence on unvalidated drafts and adopts nothing.

## Two recorded runs are on record

| Run | Brief | Where | Outcome |
| --- | --- | --- | --- |
| Revision 3 | `b0ccdea8…3460c415` | `run-rev3/` | STOP 3 in arm 0 (commit `9d5de4ad`) |
| Revision 4 | `a638d4b8…36e7b4` | top level (`pins.json`, `checkpoints/`, `result.json`) | see `result.json` and the report |

The Revision 3 run is kept as it was and nothing from it is reused:

- its cache was moved to `.circuit-cache/mc04-s16-rev3/`;
- its durable copy was moved to `/mnt/project-files/osc-s16-cache-rev3/`;
- its `bulk-manifest.json` keeps the paths that applied at that time.

## Files

| File | Role |
| --- | --- |
| `replan.py` | the library (Ruling P7 builder, rides, blocks, census, rules R1 to R6, scene checker), controls C1 to C16, mutations, stages 1 to 4, the driver and `--check` |
| `test_s16.py` | builder tests, the record block, M19 to M21, and every mutation vector copied from the brief |
| `c13_heartbeat.py` | the C13 heartbeat (a copy of S15's C17 heartbeat) |
| `pins.json` | SHA-256 of the pinned sources, written before arm 0 |
| `checkpoints/` | guard summaries, C13, arm 0 control records, mutation slots and results, stage summaries, `run.json` |
| `candidates/` | the scenes that pass stage 3, if any |
| `bulk-manifest.json` | SHA-256 and size of each file in `.circuit-cache/mc04-s16/`; the durable copy is at `/mnt/project-files/osc-s16-cache/` |
| `result.json` | pins, controls, mutations, per-block census counts, the per-structure outcome, stages, verdict, digests |

## Commands

```sh
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --pin     # before arm 0 only
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --run     # refuses to start on a pin mismatch
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --resume  # continues from the checkpoints
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --check   # PARTIAL CHECK without the cache
python3 -m unittest scripts/stack/studies/mc04_s16_l0301_replan/test_s16.py
```

`S16_DEV_OUT=<dir>` sends every output of a development dry run to `<dir>`, which is in the scratchpad. Nothing
from a dry run is used.

## Derived functions and what differs from the original

| S16 function | Original | Lines that differ |
| --- | --- | --- |
| `capped_order` | split of L01.02.01 and L03.01 in `links_gate_c6.apply` | it starts from `allocation` on 60 positions and drops the unused ones. It splits each LOGIC run of n > 3 into ⌈n/3⌉ runs, longer first, with one ground between them. It pads to the size and returns None when the order is too long |
| `host_signals` | `links_gate_part2.link_signals` | it keeps only the signals on the recorded positions, members first and recorded riders after, not in position order |
| `ride_capped` | `links_gate_part2.ride` | its host test is "eligible, and `capped_order` at the host size passes `order_errors`" in place of `circuits_needed`. Host state comes from `host_signals`. The reason texts are unchanged |
| `rehost` | `links_gate_part2.reallocate` | it takes positions from `capped_order` |
| `block_record` | `s12.World.rec`, `links_gate.link_record` | it works on any site subset, at the smallest stock size with a built order, or at a forced size |
| `record_block` | `s12.World.rec` | the recorded link with the signals on its recorded positions, built by `capped_order` (Ruling P9); used in controls and mutations only |
| `census_block` | `s12.census` | it takes a block record and a `placed` index. R5 follows Ruling P3, and `class_s='strict'` restores S12. At a record slot, R2 drops its class-distance clause (Ruling P8, `Rules.r2_record`) |
| `legal_block` | `joint_search.legal_entry` | it places the structure's earlier blocks. It also accepts prebuilt `Rules` and `placed` objects, which are identical to the ones it would build itself |
| `scene_links_replan` | `s12.World.scene_links` | it removes L03.01, adds the blocks, and re-hosts the riders |
| `judge_replan` | `s12.judge`, `s12.overlay_part` | it accepts a link set that differs from the base; A5 for blocks comes from `block_figures`. When `overlay_part` stops on an earlier overlay block with no pose (a `TypeError` in S12's own code), the scene fails A8 and the remaining items are evaluated without the S8 search |

## Selection rules for the named mutation rows

- **M12:** the first anchored protected K footprint, in (board, ref) order, with a face-B base row. Its base-row
  courtyard, put in place of the K tail of the first accepted C5 slot, passes R2, R4 and R5.
- **M14:** the first K row in (board, ref) order that has a position and is not protected, a trimmer or one of the
  five ICs.

## Readings made in the code

- **C12** is evaluated after the pool has produced the first 12 complete legal scenes. Those scenes are known only
  then. They are replayed again in sequence in the driver process before any pool result is used.
- **Stage 4** takes the 23 distinct (slot, direction) survivors of `census.json` in their first-occurrence order.
