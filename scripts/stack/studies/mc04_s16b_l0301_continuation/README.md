# MC04-S16b: the aimed continuation of the L03.01 re-plan study

Study only. Rows-level evidence on unvalidated drafts. Nothing is adopted. Every board and schematic stays an
unvalidated draft, and #318 stays HOLD.

- Brief: `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s16b-continuation-brief-20261128.md`, Revision 2,
  SHA-256 `09e9a228…8100e625`. It was admitted by DS-218. It is an addendum to the S16 brief (Revision 4).
- Erratum 1 of the brief (SHA-256 `fa8dde3e…dc0bb6`) and DS-219 reopen the study as a fresh pinned run after the first
  run's STOP 1 at K3. The first run's checkpoints are kept unchanged in `stopped-run-1/`. Its pins and code are at
  commit `6d5e435f`.
- Report: `mc04-s16b-report-20261128.md` in the same campaign folder.

## What changed under erratum 1

The erratum allows exactly these changes:

- `k3_accept` checks K3 on its detail record. The wrapper return code must be 137 or −9, and the wrapper must
  have run at least 119 s. The four survival clauses are unchanged: at least 150 heartbeat lines after the wrapper's
  end, the guard finished, child return code 0, and at least one guard sample after the wrapper's end.
- `test_s16b.py` adds N15, which tests that acceptance.
- This README.

`BRIEF_SHA` in `s16b.py` still holds the Revision 2 hash (`09e9a228…`), since nothing else may change. The fresh
`pins.json` therefore records the erratum text as it now stands (`fa8dde3e…`). It is written by the same
`compute_pins`, without `write_pins`' check against `BRIEF_SHA`.

## Files

| File | Role |
| --- | --- |
| `s16b.py` | The driver and the S16b library. It imports S16's `replan.py` unchanged |
| `test_s16b.py` | Cases N1 to N15, with the brief's vectors and reasons copied in |
| `k3_heartbeat.py` | The no-op child for control K3 (detachment) |
| `pins.json` | Source pins, written before arm 0 |
| `result.json` | Verdict, bounds, exclusions a to f, controls, counts and digests |
| `bulk-manifest.json` | SHA-256 and size of every file in `.circuit-cache/mc04-s16b/` |
| `stopped-run-1/` | The first run's checkpoints, unchanged (STOP 1 at K3) |
| `checkpoints/` | `ruling.json` (DS-219, from the manager), then controls, per-stage summaries, guard summaries, logs, the overlay count and the clock |
| `candidates/` | `scene-N.json` for each scene that passes stage 3 full |

## How S16's files stay untouched (Ruling Q5)

`s16b.py` calls only library functions of `replan.py`. These are `block_record`, `Rules`, `Anchors`,
`placed_except`, `census_block`, `distinct`, `legal_block`, `reverify_blocks`, `scene_rows`, `check_rows16`,
`acceptance_vector`, `judge_replan`, `scene_rank_key`, `scene_body`, `structures`, `screen_s123`, `Rides` and
`bulk_state`, plus pure helpers.

It never calls `drive`, `finish`, `stage1`, `stage1_one`, `stage2a`, `stage2b`, `search_one`, `stage3`, `stage4`,
`stage4_one`, `block_pool`, `ck`, `bulk`, `write_pins`, `write_manifest`, or any control function that writes a
checkpoint. It does not set `S16_DEV_OUT`, and it refuses to import while that variable is set.

The full base replay for K2 and the stage 4 test are rewritten here, because S16's versions write under S16's paths.
K1 runs S16's `--check` and unit tests as subprocesses. It then checks that `git status` is clean under S16's
directory, and that S16's cache and its durable copy match S16's manifest.

## What is new

The code for each ruling of the brief:

| Ruling | Code |
| --- | --- |
| Q1, strict R5 | `census_block(..., 'strict')` and `Rules(..., 'strict')`, S12's T1 |
| Q2, R7 | `on_parts`: `links_gate.displaced` at the slot geometry. A block that holds P-K-E1 fails when C8443 or R7213 is listed under any heading (`census_one`, `legal16b`, `case_vector16b`) |
| Q3, pools | `pool_of16b`: one survivor per spot, clear first, then (cost, key). At most 20 spots, and the E1 block is never cut |
| Q3, scene order | `e1_offsets` gives o. `spot_visits` visits spots from the cursor. `nth_completion` is a best-first search on (blocks on the two parts, summed cost in micro-units, pool indices), which is exact because both bounds are admissible. It counts legality calls per structure and spot, taking the largest fresh run. `scene_one` is the worker for one structure in one round. `stage2b` runs the rounds, the 1800-replay count in round and stage order, the 80-minute start bound, and checkpoints every 50 scenes and every round |
| Q4, stage 3 lite | `classify_lite`: `pass`, `final` or `undecided` (`LITE UNDECIDED`) |
| Q4, stage 3 full | `stage3` judges lite passers first, then `LITE UNDECIDED` scenes, each group in S16's ranking order |
| Q4, overlay cap | `OverlayCounter` wraps `w.s.search` without editing S12. It checks the count on disk and writes it before each search. The 11th search raises `OverlayCap`, which is not a `TypeError`. `judge_full_guarded` records such a scene as `STAGE 3 INCOMPLETE (CAP)` |
| Q5, STOP records | `record_stop` writes `checkpoints/stop.json`, the `stop` key in `run.json`, and a durable `stops/stop-<sha256>.json`. `start_gate` refuses while any of these exists, unless `ruling.json` and a `decisions.md` row with that ID and hash clear it. This is a tripwire and a record, not a lock |

## Running

| Command | Effect |
| --- | --- |
| `s16b.py --write-pins` | Writes the pins, once, before the recorded run |
| `s16b.py --run` | Starts the recorded run |
| `s16b.py --resume` | Resumes the recorded run, at most 3 times |
| `s16b.py --check` | Pins, digests and the cache against its manifest (`PARTIAL CHECK` when the cache is absent), and 3 replays |
| `s16b.py --gate` | Evaluates only the start gate; tests use it on scratch paths |

The driver runs detached under `scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py`.
