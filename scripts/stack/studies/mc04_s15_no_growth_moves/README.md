# MC04-S15: a no-growth rule for protected parts, then one search for U5110, U8409, U5209 and U5210 (DS-192)

Study only, one run. It produces geometric evidence and adopts nothing. Every board and schematic stays an
unvalidated draft. Brief: `circuit/orchestration/campaigns/osc-stack-20261114/mc04-s15-no-growth-moves-brief-20261128.md`
(Revision 3, SHA-256 `8283667186ae355ac0b18c94cdd21f30fbc0ea8fd02286633aef1e338ad2c378`). Report:
`mc04-s15-report-20261128.md` in the same folder.

```sh
PY=/home/user/venv312/bin/python
# the driver, detached, under the guard (from the repository root)
setsid nohup $PY scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py <summary.json> -- \
  env PYTHONDONTWRITEBYTECODE=1 $PY scripts/stack/studies/mc04_s15_no_growth_moves/no_growth.py --run &
$PY no_growth.py --resume           # continue from the checkpoints (resume cap 4; the clock is never restarted)
$PY no_growth.py --finish           # rebuild result.json from the checkpoints
$PY no_growth.py --check            # pins, 11 offline controls, digests, 3 stage 2 replays, rebuilt summaries, scenes
                                    # cache absent: first line PARTIAL CHECK, tracked part only, the rest printed as NOT RUN
                                    # cache partly present or altered: CHECK FAILED (non-zero exit) naming the files
$PY no_growth.py --verify-scene N   # rows-only replay and NG of candidates/scene-N.json
$PY -m unittest test_s15            # from this directory: mutations M1 to M26 and the hand-value tests
```

## Files

| File | Content |
| --- | --- |
| `no_growth.py` | Rulings N1 to N3 (`Model.evaluate`: NG1 to NG7 per board), the S12 adapter `G15`, the derived functions, controls C1 to C18, stages 1 to 4, `--check`, `--verify-scene` |
| `guard15.py` | memory guard: tree RSS every 5 s (budget 8 GiB), `MemAvailable` floor 7 GiB, docker stats every 30 s; every sample appended to `<summary>.samples.jsonl`, summary rewritten at every sample |
| `c17_heartbeat.py` | the detached child of control C17 (one line per second for 300 s) |
| `test_s15.py` | fixtures F to F9, mutations M1 to M26 with full vectors, the brute-force tree test, the C4 hand values, the C7 constants |
| `result.json` | fingerprint, pins, run clock, controls, guards, compact stage 1 and stage 2 per-link summaries, tallies, verdict per IC, digests of every checkpoint (tracked or cached) |
| `bulk-manifest.json` | SHA-256 and size of each bulky intermediate kept in the ignored cache (see below) |
| `checkpoints/` | `run.json` (cumulative clock, executor-timed checks, resumes), `pins.json`, `arm0/C*.json`, `stage3/pools.json` and `set-N.json`, `stage4/log.json`, `c17/`, `guard/`, the driver and end-check logs |
| `candidates/` | written scenes only; empty in this run |

## Bulky intermediates are kept out of git, a deviation from the brief's Outputs

The brief's "Outputs" puts `screen.json` in this directory. The run's four bulky intermediates (about 71 MB) are
kept out of git instead. The owner's instruction forbids Git LFS and committed large intermediate dumps.
`circuit/ORCHESTRATION.md` section 6 says to keep large intermediates as budgeted artifacts, not as repeated Git
blobs, and to store recovery-critical bytes outside an ephemeral VM. The files are in two places, with the same
relative paths as in this directory:

- the ignored local cache `.circuit-cache/mc04-s15/` at the repository root;
- a durable copy in the project file storage at `/mnt/project-files/osc-s15-cache/` (a network mount). It holds a
  copy of the manifest. After a 10 s settle, every file was re-read and its SHA-256 and size were verified against
  the manifest.

The files are:

| Cached path | Content |
| --- | --- |
| `screen.json` | stage 2: one record per replayed candidate (acceptance items, NG summary, failing nets, tallies) |
| `checkpoints/census_ng.json` | C10: the NG census per link and grid, with accepted entries (stage 1 input) |
| `checkpoints/stage1.json` | stage 1: every distinct candidate with its legality class |
| `checkpoints/stage2/part-NNN.json` | stage 2 checkpoints, one per 25 replays |

`bulk-manifest.json` pins the SHA-256 and size of all 23 files, and `result.json` carries the same digests. With the
cache present, `--check` verifies each file against the manifest and then runs the full check. Without it,
`--check` prints `PARTIAL CHECK` first. It then verifies the tracked files and the manifest against `result.json`,
rebuilds the stage 3 and stage 4 summaries, and prints the 23 digests, the 3 stage 2 replays and the stage 1,
stage 2 and verdict rebuilds as NOT RUN. A cache that is partly present or that differs from the manifest stops the
check with `CHECK FAILED` and a non-zero exit. To restore the cache, copy the durable files back into `.circuit-cache/mc04-s15/`. A re-run does not reproduce
these hashes, because every record carries its `wall_s`. `--finish` refuses to run without the cache.

## Derived functions

Each derived function keeps the S12 behaviour with `rules='s12'` (controls C8, C10 and C11) and adds the NG mode.
Line counts are from `difflib.unified_diff` of `inspect.getsource` of the original and the derived function.

| Derived | Original | Original lines | Diff |
| --- | --- | --- | --- |
| `check_rules_ng` | `s12.World.check_rules` | 17 | 17 removed, 14 added (rules 2 to 4 only in NG mode; T1 and T2 replaced by NG) |
| `census_ng` | `s12.census` | 67 | 6 removed, 12 added (records displaced and unanchored protected parts) |
| `legal_entry_ng` | `joint_search.legal_entry` | 25 | 2 removed, 2 added |
| `check_rows_ng` | `s12.check_rows` | 52 | 12 removed, 21 added (NG on the effective scene in place of A2) |
| `cluster_search_ng` | `joint_search.cluster_search` | 83 | 15 removed, 23 added (rejects on NG; pool order from stage 2) |
| `judge_ng` | `s12.judge` | 22 | 6 removed, 10 added |
| `overlay_part_ng` | `s12.overlay_part` | 148 | 9 removed, 19 added (A2 and A10 dropped; NG on the post-overlay scene) |

The S12 modules are imported read-only, with `sys.dont_write_bytecode` set, so nothing is written into the S12 folder.

## Scope of the result

Every figure is a pad-centre or connector-centre figure at courtyard level on unvalidated drafts. Nothing is routed.
Electrical behaviour, c6, checks 2 to 4, latch access, threading, DRC and ERC are NOT RUN here.
