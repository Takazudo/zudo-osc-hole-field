# MC04-S16: L03.01 re-plan study

Study code for MC04-S16. The brief is
`circuit/orchestration/campaigns/osc-stack-20261114/mc04-s16-l0301-replan-brief-20261128.md` (Revision 3,
SHA-256 `b0ccdea8…c415`). The report is `mc04-s16-report-20261128.md` in the same folder. All output is rows-level
evidence on unvalidated drafts and adopts nothing.

## The recorded run stopped at STOP 3 in arm 0

The mutation control found four vectors that differ from the brief: M1, M9, M10 and M12. The driver in this
revision covers arm 0 up to that control: C14, C13, C1, C3, C3b, C4 and C5, the mutation slots, then the mutations.
It does not contain C2, C6 to C12, C15 or C16, or stages 1 to 4. `result.json` lists these items under `not_run`.

## Files

| File | Role |
| --- | --- |
| `replan.py` | library (Ruling P7 builder, rides, blocks, census, rules R1 to R6, scene checker), arm 0 driver, `--check` |
| `test_s16.py` | builder tests, M19 to M21, and every mutation vector copied from the brief |
| `c13_heartbeat.py` | the C13 heartbeat (a copy of S15's C17 heartbeat) |
| `pins.json` | SHA-256 of the pinned sources, written before arm 0 |
| `checkpoints/` | guard summaries, C13, arm 0 control records, mutation slots and results, `run.json` |
| `bulk-manifest.json` | SHA-256 and size of each file in `.circuit-cache/mc04-s16/` and its durable copy |
| `result.json` | pins, controls, mutations, stop, items not run, digests |

## Commands

```sh
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --pin     # before arm 0 only
python3 scripts/stack/studies/mc04_s16_l0301_replan/replan.py --run     # refuses to start on a pin mismatch
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
| `census_block` | `s12.census` | it takes a block record and a `placed` index. R5 follows Ruling P3, and `class_s='strict'` restores S12 |
| `legal_block` | `joint_search.legal_entry` | it places the structure's earlier blocks |
| `scene_links_replan` | `s12.World.scene_links` | it removes L03.01, adds the blocks, and re-hosts the riders |
| `judge_replan` | `s12.judge`, `s12.overlay_part` | it accepts a link set that differs from the base; A5 for blocks comes from `block_figures` |

## Selection rules for the named mutation rows

- **M12:** the first anchored protected K footprint, in (board, ref) order, with a face-B base row. Its base-row
  courtyard, put in place of the K tail of the first accepted C5 slot, passes R2, R4 and R5.
- **M14:** the first K row in (board, ref) order that has a position and is not protected, a trimmer or one of the
  five ICs.
