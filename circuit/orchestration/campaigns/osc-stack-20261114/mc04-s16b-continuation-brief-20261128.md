# MC04-S16b brief: one aimed continuation of the L03.01 re-plan study, Revision 2

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Written at head `56254df1` of `local/cloud-engineering-20261127`. Status: **Revision 2, pending
the reviewer's re-check; not admitted to run**.

Review applied: `reviews/mc04-s16b-brief-review-20261128.md` (`ec802347…e529d656`), ADMIT AFTER FIXES on
Revision 1 (`a3ffac9d…67926275`). All 7 required findings are applied and the 4 advisories are ruled on; see
"Revision 2 changes".

Basis: the owner chose option 1 of DS-213, "Run one aimed S16 continuation" (2026-11-28 18:25Z), on the terms of
`mc04-s16-disposition-20261128.md` (DS-210 to DS-212).

**This is an addendum, not Revision 5 of the S16 brief.** The S16 brief (Revision 4, `a638d4b8…7d36e7b4`) is a
pinned source of the recorded S16 run, and editing it would make that run's `--check` fail. Everything in that
brief holds here unless this document changes it. Where the two differ, this document rules.

Study only. Nothing is adopted. No board, schematic, specification, BOM, gate record, options file, generator or
generated file changes. Every board and schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318
stays HOLD. Panel hardware stays at `design/grid/placements.lock.json` (`297300b0…5b88dbe8`). Nothing is bought,
built or ordered.

## What this run answers

The S16 run gave `NO RE-PLAN FOUND (BOUNDED)` for U8409. It spent 1087 of its 1200 replays on slots that stand on
a part L03.01 displaces today, and all of those failed. Its 24 rows-level passers share one slot, which lies on
C8443 and R7213, and all 24 fail A8 and A9.

S16b asks the same question on the part of the domain that run did not reach: is there a re-plan of P-K-P-L03.01
whose blocks stand clear of the six freed parts, whose E1 block stands clear of C8443 and R7213, and which passes
stage 3?

## Facts this brief rests on

Read-only counts from the S16 cache (`.circuit-cache/mc04-s16/`, 189 files under S16's `bulk-manifest.json`,
`f031a429…2992caed`) and from `links_gate.candidate` on the S12 `World` at snapshot `6e5716e7`. No replay was run
for them. They are not reviewed; the controls below re-measure each one.

- **Class S slots.** 15 836 distinct census survivors over the 63 blocks; 8665 have no class S part under them.
  40 of the 63 blocks keep such a survivor (45 keep any survivor). The five 26-way blocks that had survivors lose
  all of them.
- **Slots on C8443 or R7213.** Of the 32 blocks that hold P-K-E1, 14 keep a class-S-free survivor: 1000 survivors
  in all, 285 of them directly on C8443 or R7213, 715 clear. P-K-E1 alone keeps 132 on 14 spots. The two 8-way
  pairs (with K-P-16 or K-P-20) keep 154 on 18 spots each. The eleven 14-way blocks keep 18 to 28 on 2 spots each,
  all in direction +y.
- **The same slots are open to other blocks.** 748 of the 7665 class-S-free survivors of blocks without P-K-E1
  also lie on C8443 or R7213.
- **Structures.** 502 of the 876 structures stay live: 254 are dead at S3 as before, and 120 have a block with no
  survivor (88 before, 32 more now). 118 of the 502 were searched in S16 and 384 were not. 170 of them hold
  P-K-E1 alone.
- **What S16 already tested here.** Of S16's 113 replays with no class S part under any block, 24 passed rows and
  89 failed. All 24 passers and 74 of the 89 had the E1 block on C8443 or R7213. Only 15 S16 replays lie inside
  the S16b domain, and all 15 failed. 14 of the 15 in-domain replays had a block without P-K-E1 on C8443 or
  R7213; one replay had every block clear of both.
- **A correction to the record.** The S16 report and the disposition say that all 155 live structures with
  P-K-E1 alone were unsearched. S16 had 170 such live structures; 15 were searched and 155 were not.

## Rulings

All are provisional until the independent review accepts them. Rulings P1, P2 and P4 to P9 of the S16 brief stand.

### Ruling Q1: the strict class S preflight replaces Ruling P3

Ruling P3 is withdrawn for this run. R5 rejects a slot that displaces any protected part which is not anchored,
class S included, as S12's T1 did (`class_s='strict'`, already in S16's code). Evidence: 0 of 1087 S16 replays
with a class S part under a block passed A0 to A6. A2 is unchanged and still judges every replay.

### Ruling Q2: an E1-block slot on C8443 or R7213 is left out

New test **R7**, after R6. It applies only to the block that holds P-K-E1. It fails when `links_gate.displaced`
at the block's slot geometry lists C8443 or R7213 under any heading. Evidence: all 24 rows-level passers of S16
have the E1 block on both parts, and all 24 fail A8 and A9.

For a block without P-K-E1 there is no such replay evidence, so R7 does not apply to it. The A8 failure of the
24 scenes comes from the slot standing on C8443, so a slot of another block there is expected to fail the same
way. It is kept only because no replay has tested it, and the order of Ruling Q3 takes it last.

R7 stays on the E1 block alone (advisory 10 of the review). DS-212, on which the owner chose this run, names
E1-block slots. R7 for every block would take 748 more survivors out of the study the owner chose, on an
expectation and not on a replay. That would change the choice, so it is not done here. No block would lose all its
survivors, and the 502 live structures are the same either way (review, advisory 10).

This is a labelled exclusion, **f**, beside exclusions a to e. For R7213 alone the evidence is indirect: no S16
scene had the E1 block on R7213 only and passed rows. The report says so with the verdict.

### Ruling Q3: the E1 block is taken first, across all its spots

- **Pools.** Each block's pool holds one survivor per spot, at most 20 spots, as before. A spot gives its
  cheapest survivor clear of C8443 and R7213, or its cheapest survivor if none is clear. Clear entries come first
  in the pool, then by (cost, `key`), as `pool_of` has it. The E1 block's pool is never cut: it has at most 18
  spots.
- **Scene order within a structure.** Let k be the number of spots in the structure's E1 pool, and o the
  structure's index among the live structures that share that E1 block, in stage order. Scene t (t = 0, 1, …) puts
  the E1 block on spot (o + t) mod k.
- **Completions of a spot.** The blocks other than the E1 block are taken in the structure's block order. A
  completion is one pool entry per other block, legal by `legal_block` with the blocks before it placed and
  passing `reverify_blocks`. Completions of a spot are ordered by this key, lowest first: (number of blocks on
  C8443 or R7213, summed cost, pool indices in block order). Scene t takes the first completion of its spot, in
  that order, that this structure has not replayed. A visit to a spot with no completion left uses no replay;
  the structure moves to the next spot in the same round. A structure whose spots are all used up has no legal
  scene left. The completion n of a spot is a function of the structure, the spot and n only; legality calls
  are counted once per structure.
- **Counting.** Replays count toward the cap of 1800 in round order and stage order, not in order of
  completion. A replay beyond the 1800th in that order is discarded and disclosed.
- **Time bound.** No round or scene starts after 80 minutes of stage 2b. This is a bound, named in the verdict.
  The 90 minute ceiling stays as STOP 6.
- **Rounds across structures.** Stage 2b runs in rounds. In each round every live, unfinished structure, in the
  S16 stage order (fewest links, then fewest circuits, then lowest summed cost), tries one scene. Rounds continue
  until a cap or until every structure is finished.
- **When a structure is finished.** It has a scene that passes stage 3 lite or is `LITE UNDECIDED` (Ruling
  Q4), or it has had 12 replays, or it has no legal scene left.

So every live structure is tried before any is tried twice, and the structures that share an E1 block start on
different spots of it.

### Ruling Q4: every rows-level passer is judged for A8 and A9 at once

- **Stage 3 lite.** A scene that passes A0 to A4 and A6 is judged at once by `judge_replan` with no S8 search. It
  passes stage 3 lite when it has no failure other than "overlay search not run". S16's stop at the first rows
  pass and its cap of 5 judged scenes are both dropped.
- **When a lite failure is final.** A lite failure is final only when the scene needs no search (no "overlay
  search not run" failure), or when it has an A8 failure of the kind "a decoupler row breaks the block rule
  while the IC row is unchanged", or an A5 failure. Any other scene with "overlay search not run" is
  `LITE UNDECIDED`: it finishes the structure as a lite passer does, and it goes to stage 3 full. The reason:
  with no search no overlay block is placed, so A7 and A9 to A11 are judged without the block poses.
- **Stage 3 full.** Every lite passer, and then every `LITE UNDECIDED` scene, is judged again with the S8
  search, each group in ranking order.
- **The overlay cap is checked before every search.** The cap stays at 10 block searches for the run. The count
  is checked before each search inside a scene, not only before a scene. A scene that needs a search beyond the
  cap is recorded as `STAGE 3 INCOMPLETE (CAP)`. It is neither a pass nor a failure, and it makes a negative
  result `BOUNDED`. No S12 file is edited for this; the executor wraps the search call.
- **The count is kept on disk.** The count is written to `checkpoints/stage3/overlay-count.json` before each
  search starts, and a resume reads it. Searches of a scene cut short by a restart stay counted. The wrapper
  raises its own exception type, never `TypeError`, because `judge_replan` turns a `TypeError` into an A8
  failure.

### Ruling Q5: a fresh pinned run, and a STOP ends it

- **Fresh run.** New code lives in `scripts/stack/studies/mc04_s16b_l0301_continuation/`. It imports S16's
  `replan.py` unchanged and adds a driver and `test_s16b.py`. No file of S12, S15 or S16 is edited, so S16's pins
  and `--check` stay valid. Pins are written before arm 0 and cover the new files, `replan.py`, the S12 and S15
  files it imports, `guard15.py`, the S16 brief and this brief. Every control and stage runs again; nothing is
  taken from S16 except as a control value.
- **S16's files stay untouched.** The S16b driver calls only library functions of `replan.py`. It never calls
  `drive`, `finish`, `stage1`, `stage1_one`, `stage2a`, `stage2b`, `search_one`, `stage3`, `stage4`,
  `stage4_one`, `block_pool`, `ck`, `bulk`, `write_pins`, `write_manifest` or the control functions that write a
  checkpoint, because they write under S16's paths. It does not set `S16_DEV_OUT`. Pins also cover S16's
  `bulk-manifest.json` and `result.json`.
- **A STOP ends the run.** On any STOP the driver writes `checkpoints/stop.json`, sets `stop` in
  `checkpoints/run.json`, copies `stop.json` to `/mnt/project-files/osc-s16b-cache/stops/` under a name with its
  SHA-256, and exits non-zero. It refuses to start, under any pins, while any of the three records exists,
  unless `checkpoints/ruling.json` gives a decision row ID and the SHA-256 of `stop.json`, and `decisions.md`
  holds a row with that ID whose text contains that SHA-256. The manager writes the row and the file, never the
  executor. The driver cannot tell who wrote a file: this is a tripwire and a record, not a lock. The result
  reviewer checks the durable `stops/` folder and the git history of the study directory. A run restarted after
  a STOP without such a row is inadmissible (DS-211). After pins are written, a defect found in
  the study code is a STOP. A resume after a container restart is not a STOP; at most 3 resumes, as before.
- **Development.** Dry runs are allowed only in the scratchpad, before pins, are disclosed with their time, and
  nothing from them is used.

### Ruling Q6: the stop rule

The stop rule applies only when the run reaches its end with a verdict of Ruling P6, no STOP, no scene recorded
as `STAGE 3 INCOMPLETE (CAP)` and no `LITE UNDECIDED` scene left unjudged. Then, if no scene passes stage 3 full,
the design authority will propose no further placement study for U8409, whatever bounds the verdict names. A run
that ends in a STOP has no verdict and does not trigger the rule. A negative result with an unjudged scene
returns to the design authority, which rules on that scene alone. That is DS-212, and the owner chose this run
on it.

## Tests a scene must pass

The table of the S16 brief stands, with these changes:

| # | Test | Change |
| --- | --- | --- |
| R5 | T1 | strict: no class N and no class S part under the block (Ruling Q1) |
| R7 | E1 block clear of C8443 and R7213 | new, after R6; the E1 block only (Ruling Q2) |
| A5, A7 to A11 | overlay items | on every rows-level passer, lite first and then full (Ruling Q4) |

The verdict vocabulary of Ruling P6 stands. A positive verdict needs a scene that passes stage 3 full. A
negative result is always `NO RE-PLAN FOUND (BOUNDED)`: the pool cut is in force for 12 blocks.
`CENSUS-COMPLETE` cannot be given while a structure is live. "This domain" is the S16 domain with exclusions a
to f.

## Procedure

### Arm 0: controls (stop on any failure)

| # | Control | Expected |
| --- | --- | --- |
| K1 | **real**: S16 is intact | `replan.py --check` of S16 with its cache present gives rc 0: pins verified, C3, C3b, C8b and C9 and the mutation results of `mutation_cases` equal, 219 digests. `python -m unittest test_s16` passes (34 tests; M19 to M21). S12 `joint_search.py --check` passes. K1 runs again as the last step of the run, and `git status` shows no change under S16's directory |
| K2 | S12 P8, the full base replay | equal to the base |
| K3 | detachment and guard, run again | as S16's C13, on this container after its restart |
| K4 | source pins | verified; a scratch copy with one byte changed is refused |
| K5 | **real**: the strict census against S16's | for each of the 63 blocks, the strict survivors equal S16's cached survivors with an empty class S list. 40 blocks keep a survivor; 8665 survivors of S16's 15 836. P-K-E1 alone: 179 on 19 spots. Evaluated after stage 1 |
| K6 | **real**: R7 on the census | 14 blocks with P-K-E1 keep a strict survivor: 1000 survivors, 285 on C8443 or R7213, 715 clear. P-K-E1 alone keeps 132 on 14 spots; K-P-16 + P-K-E1 and K-P-20 + P-K-E1 keep 154 on 18 spots each. Blocks without P-K-E1: 748 of 7665 lie on either part. Evaluated after stage 1 |
| K7 | **real**: the 24 rows-level passers of S16 | replayed again: 24 row digests equal S16's logs. R7 fails for the E1 block in all 24, on both parts. Stage 3 lite fails in all 24 at A8 (U8413: C8443 on face F in 12, at 16.672 mm in 12) and at A9 (R7213 at 49.858 mm in 8, at 50.567 mm in 16). Whether each is final or `LITE UNDECIDED` under Ruling Q4 is recorded as a reading, not an expected value |
| K8 | **real**: S16's replays under the new rules | of the 1200 replays in S16's logs, 1087 have a block that strict R5 rejects. Of the other 113, 24 pass and 89 fail A0 to A6; R7 rejects all 24 and 74 of the 89. 15 lie in the S16b domain: 14 with a block without P-K-E1 on C8443 or R7213, one with every block clear of both |
| K9 | the screen | 502 live structures of 876: 254 dead at S3, 120 at the census. By links and ride sites: (1, 3) 2; (2, 0) 9; (2, 1) 43; (2, 2) 53; (2, 3) 15; (3, 0) 66; (3, 1) 114; (3, 2) 54; (3, 3) 5; (4, 0) 61; (4, 1) 50; (4, 2) 9; (5, 0) 15; (5, 1) 5; (6, 0) 1. 170 hold P-K-E1 alone. Evaluated after stage 2a |
| K10 | pools | 12 of the 40 blocks have more than 20 spots; no E1 block has more than 18 |
| K11 | worker determinism, **first** | the first 12 scenes of round 1 are replayed in sequence before the pool starts, then again by the pool; equal row digests. With fewer than 12 scenes, all of them |
| K12 | overlap with S16 | every S16b scene that equals an S16 replayed scene (same structure, slots and directions) gives S16's row digest. Evaluated at the end of stage 2b; a difference is STOP 1 |

No real scene that passes stage 3 exists before the run, and none is invented.

### Stages

- **Stage 1.** The block census of all 63 site subsets, fresh, with the strict R5 and with R7 for blocks that hold
  P-K-E1. Complete, no cap. Then K5 and K6.
- **Stage 2a.** S1 to S3 as in S16 (every site order), then "every block has a survivor". Complete. Then K9 and
  K10.
- **Stage 2b.** K11 first. Then rounds as Ruling Q3 rules, one rows-only replay per scene, A0 to A4 and A6, and
  stage 3 lite on every passer. No round or scene starts after 80 minutes. Then K12.
- **Stage 3.** Stage 3 full on every lite passer and then on every `LITE UNDECIDED` scene, each group in ranking
  order, with the cap of Ruling Q4. Then K1 again, as the last step of the run (after stage 4).
- **Stage 4.** As in S16, on every scene that passes stage 3 full: the 23 survivors of P-K-P-L13.01.01.01, A0 to
  A4 and A6, and "U5210 has no row". A reading, never a verdict.

Ranking is that of the S16 brief.

## Mutations

S16's M1 to M28 are re-run by K1: `mutation_cases` under `--check`, and M19 to M21 in `test_s16`. The cases
below are new, in `test_s16b.py`, written and pinned before the run.
The vector has ten candidate tests (S1 S2 S3 R1 R2 R3 R4 R5 R6 R7), then six acceptance tests (A0 A1 A2 A3 A4
A6). `P` pass, `F` fail, `–` not evaluated. Candidate tests stop at the first failure. A block given at a slot
has no ride set, so S3 passes. A case given as a block at a slot has no replay, so its acceptance tests are not
evaluated. STOP 3 applies when a vector or a reason differs.

| # | Case | Vector | Source |
| --- | --- | --- | --- |
| N1 | block P-K-E1 (8-way) at (218.0, 181.25) −x, its first S16 survivor | `PPPPPPPF–– ––––––` | real: class S parts C7205 and U8411 under it; S16's default R5 passes it, and the test asserts that too |
| N2 | R5 alone on the record geometry of L03.01, no record exemption | R5 `F`, six class S parts, no class N | real (S16's M18 under the strict rule); not a vector, since R4 fails first |
| N3 | block {K-P-20, P-K-E1, P-K-E3} (14-way) at (235.25, 182.0833) −y, the rank 1 slot of S16 | `PPPPPPPPPF ––––––` | real: C8443 and R7213 under "K B (slot)" |
| N4 | block P-K-E1 at (227.0, 189.0) +x | `PPPPPPPPPF ––––––` | real: R7213 alone, under "K B (field)" |
| N5 | block P-K-E1 at (233.25, 181.25) −y, its first survivor clear of both parts | `PPPPPPPPPP ––––––` | real |
| N6 | block {K-P-16, K-P-18, K-P-20, P-K-E2} (14-way, no P-K-E1) at (234.75, 182.5) −y | `PPPPPPPPPP ––––––` | real: on C8443 and R7213, but R7 does not apply; the test asserts that the slot sorts after every clear slot of its pool |
| N7 | the rank 1 scene of S16 as a whole | `PPPPPPPPPF ––––––`; judged directly, A0 to A6 give `PPPPPP` and stage 3 lite fails at A8 and A9 | real (K7) |
| N8 | scene order: a structure with o = 3 and k = 14 | not a vector | scenes 0 to 13 use E1 spots 3, 4, …, 13, 0, 1, 2; scene 14 uses spot 3 with its second completion |
| N9 | overlay cap inside a scene: the count is 6 and a synthetic scene asks for 6 searches | not a vector | 4 searches run, the 5th is refused by the wrapper's own exception type (not `TypeError`), and the scene is `STAGE 3 INCOMPLETE (CAP)`; the count ends at 10, `checkpoints/stage3/overlay-count.json` holds each count before its search, and a resumed process reads 10 |
| N10 | `checkpoints/stop.json` present in a scratch copy | not a vector | the driver refuses to start, rc non-zero. With `stop.json` deleted but the `run.json` stop or the durable copy present, it refuses. With a `ruling.json` whose row ID is not in `decisions.md`, or whose hash differs, it refuses. With a `ruling.json` that gives a row ID and the hash, and a `decisions.md` row with that ID and hash, it starts |
| N11 | a rows-level passer whose only stage 3 failure is "overlay search not run" (synthetic failure list) | not a vector | it is a lite passer and goes to stage 3 full; with an A5 failure added it is a final lite failure |
| N12 | one byte of a pinned source changed; one cached bulk file altered, then removed | not a vector | the driver refuses to start; `--check` fails, then prints `PARTIAL CHECK` |
| N13 | a synthetic failure list with "overlay search not run" and one A9 failure | not a vector | it is `LITE UNDECIDED` and goes to stage 3 full; with the knock-on A8 failure added it is a final lite failure |
| N14 | cross-structure order: three synthetic structures share an E1 block with k = 2 | not a vector | round 1 gives spots 0, 1, 0 in stage order, round 2 gives 1, 0, 1; a structure finished in round 1 has no scene in round 2 |

"First" in N1 and N5 means first in the block's survivor order (sorted by `key`).

## Caps

| Cap | Value | Reaching it |
| --- | --- | --- |
| Stage 1, stage 2a | none: complete | a ceiling instead; STOP 5 |
| Pool per block | 20 spots; the E1 block is never cut | a bound for the 12 blocks it cuts |
| Legality calls per structure | 20 000 | a bound |
| Rows-only replays per structure | 12 | a bound |
| Rows-only replays in stage 2b | 1800, counted in round order and stage order | a bound; a replay beyond the 1800th in that order is discarded and disclosed |
| Stage 2b start time | no round or scene starts after 80 min | a bound, named in the verdict; 90 min stays STOP 6 |
| Stage 3 lite | every rows-level passer | no cap |
| Search after a lite passer | a structure is finished at its first lite passer or `LITE UNDECIDED` scene | a bound when that scene then fails stage 3 full: the structure was not searched further |
| Overlay block searches | 10, checked before each search | `STAGE 3 INCOMPLETE (CAP)`, a bound |
| Stage 4 replays | 23 per scene that passes stage 3 full, at most 230 | a bound |
| Worker processes | 3 | never more; K11 |
| Resumes | 3 | STOP 6 on a fourth |

Any bound reached makes a negative result `BOUNDED`. With 502 live structures, 1800 replays give every structure
three scenes and more than half a fourth.

## Run bounds

The run bounds of the S16 brief stand: one executor session on the Cloud container, the driver detached under
`guard15.py`, slices of at most 100 minutes, checkpoints no more than 15 minutes apart (per control, per 8 blocks,
per round of stage 2b and per 50 scenes within a round, per scene in stages 3 and 4), a cumulative clock, and
DS-196 for a stopped docker daemon. After a restart, the daemon is started and both start checks are repeated
**before** the resume.

| Step | Ceiling | Expected (from S16's times) |
| --- | --- | --- |
| Start `regen-all.sh` and `pnpm circuit:check` | 15 min | 7.5 min |
| Arm 0 (K2 about 4 min, K3 5 min, K7 about 3 min, K1 about 2 min plus S16's unit tests, not timed) | 30 min | 16 to 18 min |
| Stage 1 (63 censuses on 3 workers) | 55 min | 8 min |
| Stage 2a | 10 min | 1 min |
| Stage 2b (K11; at most 1800 replays, 2.2 s each on 3 workers; stage 3 lite on passers; nothing starts after 80 min) | 90 min | 70 min |
| Stage 3 full | 30 min | 0 to 10 min |
| Stage 4 | 20 min | 0 to 10 min |
| End K1, `--check`, tests, `regen-all.sh --check`, `pnpm circuit:check` | 20 min | 15 to 17 min |
| **Sum** | **270 min** | |

**Wall-time ceiling: 4.5 hours cumulative across resumes. Expected: about 2 to 2.4 hours.** Five minutes of ceiling
move from stage 1 to the end step, which now holds K1; the sum is unchanged.

## Outputs

Tracked, in the study directory: the code, `test_s16b.py`, `README.md`, `pins.json`, `result.json`, small
checkpoints, guard summaries, `bulk-manifest.json`, and `candidates/scene-N.json` for scenes that pass stage 3
full. The report is `mc04-s16b-report-20261128.md` in the campaign folder.

Not tracked: census records, search logs and replay records, in the ignored `.circuit-cache/mc04-s16b/` with a
durable copy at `/mnt/project-files/osc-s16b-cache/`, both under `bulk-manifest.json`, as in S16.

The report gives what the S16 brief asks for, and also:

- the verdict with every bound and with exclusions a to f, and the stop rule of Ruling Q6 applied to it;
- per round: structures tried, replays, rows-level passers and lite passers;
- per E1 block and spot: how many scenes used it, and how many passed rows;
- for every rows-level passer: its slots, hosts and every stage 3 lite failure with its figure (which part, which
  face, which distance against the base);
- every `STAGE 3 INCOMPLETE (CAP)` scene and every `LITE UNDECIDED` scene, with its stage 3 full result;
- per scene: the number of blocks without P-K-E1 on C8443 or R7213, and how the scenes with such a block fared
  against those with none;
- every replay discarded beyond the 1800th, every structure not searched past a lite passer that failed stage 3
  full, and the overlay count file at the end;
- the S16 and S16b results side by side: what each tested, and what neither did.

## STOP conditions

STOP 1 to 8 of the S16 brief stand, with K and N in place of C and M. In addition:

9. A STOP is final for the run (Ruling Q5). The executor writes what was found and returns. It does not edit a
   pinned source, write new pins, remove a stop record, write `ruling.json` or start again.
10. S16's cache or its durable copy is absent or differs from S16's `bulk-manifest.json`. K5, K7, K8 and K12 need
    it, and no substitute may be invented.

A result with no re-plan is a valid result, not a STOP.

## What the result can and cannot claim

The claims section of the S16 brief stands. In addition:

- **It can claim** that every live structure of the reduced domain was tried on at least the stated number of E1
  spots, and how every rows-level passer fares in stage 3.
- **It cannot claim** anything about slots under exclusion f, or about slots on a class S part beyond S16's 1087
  failed replays, which were a bounded sample.
- A kept scene adopts nothing. The adoption list of the S16 brief stands in full.

## What the independent reviewer must check

1. That Ruling Q1 only restores S12's rule, and that A2 is unchanged.
2. That Ruling Q2 is what the evidence supports, that R7 is defined on a function of record, and that exclusion f
   is labelled wherever the verdict is.
3. That the scene order of Ruling Q3 is deterministic and gives every structure a scene before any gets two.
4. That stage 3 lite cannot pass a scene which stage 3 full would fail without that being found, and that the
   overlay cap can no longer be overrun.
5. That the figures of K5 to K10 reproduce from the S16 cache.
6. That every N vector follows from the test order.
7. That Ruling Q5 states the STOP record as a tripwire and not a lock, that the three records and the
   `decisions.md` test are all checked, and that S16's files stay untouched.
8. That caps, ceilings and replay time are consistent.

## Decision rows

DS-214 is in `decisions.md`; it cites Revision 1 of this brief. The rows below are proposed, in the six columns
of the log. They are not appended; the manager appends them after the re-check.

| ID | Date | Decision | Decided by | Basis | Reverse by |
| --- | --- | --- | --- | --- | --- |
| DS-215 (proposed) | 2026-11-28 | S16b Rulings Q1 and Q2: the strict class S preflight of S12 replaces Ruling P3 for this run; an E1-block slot on C8443 or R7213 is left out as labelled exclusion f; slots of other blocks on those parts stay in the domain and are taken last | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s16b-continuation-brief-20261128.md`; `reviews/mc04-s16b-brief-review-20261128.md`; DS-212 | Design-authority ruling |
| DS-216 (proposed) | 2026-11-28 | S16b Rulings Q3 and Q4: the E1 block is taken first across all its spots, in rounds over the live structures, at most 1800 replays; every rows-level passer is judged without the S8 search and then with it; the cap of 10 overlay searches is checked before each search | Design authority (DS-03: Fable agent at high effort), owner notified | same | Design-authority ruling |
| DS-217 (proposed) | 2026-11-28 | S16b Rulings Q5 and Q6: a fresh pinned run in its own directory, S16's files untouched; a STOP ends the run and only a decision row reopens it; a completed run with no scene passing stage 3 full and no unjudged scene means no further placement study for U8409 is proposed | Design authority (DS-03: Fable agent at high effort), owner notified | same; DS-211, DS-212 | Design-authority ruling; the owner may still ask for a study |

## Evidenced, assumed and not established

- **Evidenced:** the S16 result and its review; the counts under "Facts", read-only and re-measured by K5 to K10.
- **Assumed:** that stage 3 lite can be had from `judge_replan` with no search (N11, N13 and K7 test it); that the
  search call can be wrapped without editing S12 (N9 tests it); the stage times, taken from S16.
- **Not established:** whether any structure of the reduced domain passes rows, or stage 3. Only 15 replays of
  S16 lie in this domain, and all failed.

## Revision 2 changes

Required findings of the review, all applied with the review's wording unless noted:

| # | Finding | Where it is applied |
| --- | --- | --- |
| 1 | completion order and cap counting | Ruling Q3: "Completions of a spot" and "Counting"; Facts and K8 carry the 14 and 1 split; Caps row |
| 2 | a lite failure is not always final | Ruling Q4: "When a lite failure is final"; `LITE UNDECIDED` finishes a structure and goes to stage 3 full after the lite passers; N13 added; N11's second half now names an A5 failure, since "any other failure" no longer holds |
| 3 | stop rule only on a completed run | Ruling Q6 replaced; a negative result is always `BOUNDED` under "Tests a scene must pass" |
| 4 | STOP record is a tripwire | Ruling Q5: three records, `ruling.json` with row ID and hash, the `decisions.md` test, "a tripwire and a record, not a lock"; N10 extended; STOP 9 names the records |
| 5 | overlay count persisted | Ruling Q4: "The count is kept on disk"; N9 extended |
| 6 | K1 and S16's writers | K1 replaced and repeated as the last step; Ruling Q5 lists the functions the driver must not call; pins cover S16's `bulk-manifest.json` and `result.json` |
| 7 | six-column rows | "Decision rows" |

Advisories, each ruled on by the design authority:

| # | Advisory | Ruling | Reason |
| --- | --- | --- | --- |
| 8 | stage 2b time bound | accepted | a slow stage 2b should end in a bounded verdict, not in a final STOP |
| 9 | cross-structure order test | accepted, as N14 | the order across structures had no test |
| 10 | R7 for every block | not accepted; R7 stays on the E1 block | it would change what the owner chose: DS-212 names E1-block slots. The review's sentence is in Ruling Q2 and the report counts those scenes |
| 11 | three wording points | accepted, all three | each states something the run already does: the extra bound, the mutation note and the `(cost, key)` tie-break |

Not asked for by the review, and changed with these: 5 minutes of ceiling move from stage 1 to the end step for
the second K1 (sum unchanged at 270 min); K7 records the lite status of the 24 scenes as a reading; reviewer check
7 is reworded to match finding 4.

## Erratum 1 (2026-11-28, after the first run's STOP 1 at K3)

Not a revision: no ruling, figure, cap, ceiling or expected vector of Revision 2 changes. The first recorded run
(commit `6d5e435f`) ended at STOP 1 on K3 after 13.3 min, before any replay. Its stop record is
`101c5ce0e7d251017e3c0ac02a967f8abcfd0417f5953437314fb36c39019cfb`.

- **E1, K3 acceptance.** The stop was a defect in the pinned study code, not a detachment failure. `k3_control`
  asked for a wrapper return code of 137. It calls `timeout -s KILL` through `subprocess.run` with no shell, and
  Python reports a process ended by SIGKILL as −9; S16's C13 read 137 because a shell reported it. Both values
  mean the same event. K3 passes when all of these hold: the wrapper return code is 137 or −9; the wrapper ran at
  least 119 s (so the kill at the 120 s limit ended it, and nothing earlier did); at least 150 heartbeat lines
  come after the wrapper's end; the guard finished; the child's return code is 0; at least one guard sample comes
  after the wrapper's end. The last four clauses are unchanged. The first run's K3 record meets all six (−9,
  120.0 s, 180 lines, finished, 0, 36 samples).
- **E2, mutation N15.** The acceptance is a function of the K3 detail record, tested in `test_s16b.py`. It passes
  the first run's recorded detail and the same detail with 137. It fails with a return code of 0, 124 or −15,
  with a wrapper time of 60 s, with 149 lines after the wrapper's end, with the guard not finished, with a child
  return code of 1, and with no guard sample after the wrapper's end. Not a vector.
- **E3, one real K3 before pins.** The defect was not seen in development because the dry runs stubbed K3. Before
  the new pins, K3 runs once for real in the scratchpad (about 5 min), disclosed with its time. Nothing from it is
  used.
- **E4, the note on N2.** The Source cell of N2 says "not a vector, since R4 fails first". That is wrong.
  Measured by the pinned test: without Ruling P8, R2 fails first (class distance); with P8, R2 and R4 pass and R5
  fails. N2's stated result stands: R5 fails with six class S parts and no class N. N2 stays "not a vector".
- **E5, how the run reopens (Ruling Q5).** A fresh pinned run, not a resume. Only the K3 acceptance, N15 and the
  README may change in the study code. New pins are written and cover this brief as it now stands. The first run's
  `checkpoints/` folder is moved unchanged to `stopped-run-1/` in the study directory and stays tracked; its
  durable stop copy is not removed. The new `checkpoints/` holds `ruling.json`, written by the manager, before the
  driver starts. Every control and stage runs again; nothing is taken from the first run. The ceilings, the
  cumulative clock and the count of resumes start again at zero. The first run's 13.3 min are disclosed in the
  report and are not charged.
- **E6, a second STOP.** The start test compares one hash with every stop record. After a second STOP it would
  hold two, and no single `ruling.json` could match. That is left as it is. A second STOP returns to the design
  authority.

## Revision history

| Revision | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-28 | First draft after the owner's choice of DS-213 option 1 |
| 2 | 2026-11-28 | Review `ec802347…e529d656` applied: 7 required findings, advisories 8, 9 and 11 accepted, advisory 10 not accepted (R7 stays on the E1 block). See "Revision 2 changes" |
| 2, erratum 1 | 2026-11-28 | After STOP 1 at K3 of the first run: K3 acceptance, N15, the N2 note, and the terms of the fresh run. No ruling or figure changed |
