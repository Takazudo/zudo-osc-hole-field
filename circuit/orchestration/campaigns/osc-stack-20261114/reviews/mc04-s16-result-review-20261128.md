# MC04-S16 result review: ACCEPT WITH CORRECTIONS (2 blocking, 8 non-blocking); the verdict NO RE-PLAN FOUND (BOUNDED) stands

2026-11-28. Issue #367 (MC-04 paper gate). Independent review, model `claude-fable-5-2`. The reviewer is not the
executor or the author of the brief. Read-only, except for this file.

Subject: the Revision 4 run of MC04-S16 at head `b8af96e1` of `local/cloud-engineering-20261127` (run commit
`05900bb8`): `mc04-s16-report-20261128.md`, `scripts/stack/studies/mc04_s16_l0301_replan/` and the cache in
`.circuit-cache/mc04-s16/`. Brief: `mc04-s16-l0301-replan-brief-20261128.md`, Revision 4, SHA-256
`a638d4b8d6d20def85c63ed51e236153d889da790dee7e7cc0bebe657d36e7b4` (verified).

The verdict is the right one of the three in Ruling P6, and no reviewed fact changes it. Two corrections block
acceptance of the report as written: the verdict does not list every bound, and a STOP 1 was overridden by the
executor without a ruling. Neither changes the verdict.

All evidence is at rows level on unvalidated drafts. Nothing is adopted. The reviewer ran no driver, no docker
command, no `regen-all.sh` and no KiCad oracle; those are NOT RUN here because the review is read-only.

## The recorded results reproduce

| Check | Result |
| --- | --- |
| Brief SHA-256; `pins.json` against the seven pinned files | match |
| `replan.py --check`, cache present | rc 0: pins verified, offline controls and mutations re-run equal, 219 digests, 3 stage 2b replays equal |
| `test_s16.py` | rc 0, 34 tests |
| Cache and durable copy against `bulk-manifest.json` | 189 of 189 files match in both places; the copy holds one more file, the manifest |
| Controls C1 to C16, C3b and C8b against the brief's expected values | all 18 records match the brief |
| Mutation vectors M1 to M28 and reason texts against the brief's table | all match; M17, M18, M26 and M27 as described |
| Mutation slots written before stage 1 | yes, 16:39Z; stage 1 followed |
| C8 re-run by the reviewer on the pinned source | passes: `judge_replan` equals `s12.judge` on the S10 scene, nine A2 rows |
| Stage 2a figures: 254 dead at S3, 88 at the census, 534 live; class table sums | consistent (254 + 88 + 534 = 876; live, searched and passing columns sum to 534, 123 and 24) |
| Stage 2b order (links, circuits, cheapest sum) | reproduced from `stage2a/structures.json`; the 123 logs match it by id |
| Replay count | 1186 at the restart, 12 in structure 121, 2 kept in structure 122: 1200 |
| The 24 passing scenes, replayed by the reviewer | 24 of 24 row digests equal the logs; all pass A0 to A4 and A6 |
| Ranking of the 24 by the brief's five keys | the five judged scenes are ranks 1 to 5 (stage 2b indices 1, 0, 33, 36, 16) |
| Stage 3 for scenes 1 and 3, re-judged by the reviewer with the S8 search | the same failures and the same texts as `checkpoints/stage3/` |
| Clock: 3525.9 s driver, 1320 s executor-timed, 803 s end checks | each sum reproduces from `run.json` and the guard files; 94.1 min of 270 |

The reviewer's replays ran from scratch scripts outside the repository and wrote nothing into it.

## Stage 3 failures are real, and none is a defect of `judge_replan`

`judge_replan` passes the scene rows and the re-planned link list to `s12.overlay_part`, which is unchanged. Both
common failures are raised there, before and independently of the S8 search. The text "stricter reading: no
knock-on exemption" is S12's own, not an executor reading, so STOP 7 does not apply.

| Item | What the reviewer measured | Scenes |
| --- | --- | --- |
| A8, U8413 | U8413's row is unchanged and its decoupler C8443 gets a new row. With the E1 block holding P-K-E3, C8443 goes to face F, 1.493 mm from the IC on face B. With the block holding P-K-E2, it stays on face B at 16.672 mm, against 5.690 mm at the base | all 5 judged |
| A9, R7213 | R7213 gets a new row and stands 49.858 mm (one block) or 50.567 mm (two blocks) from U7204, against 49.159 mm at the base | all 5 judged |
| A8, U4111 | no S8 pose within 24 mm; nearest 32.9 mm (scenes 1 and 2), 73.54 mm (scene 3) | scenes 1 to 3 |
| A10 | C8308 and R8334 are moved by the S8 pose of the U8313 block | scenes 1 to 3 |

For scene 3 the last two rows rest only on searches beyond the cap (finding 3).

## The 19 unjudged passing scenes fail the same two items, so none of the 24 can pass stage 3

This is reviewer evidence, not a result of the recorded run. The reviewer judged all 24 passing scenes with
`judge_replan` and no S8 search.

- All 24 fail A8 at U8413 (C8443) and A9 at R7213: 12 with C8443 on face F, 12 with it at 16.672 mm; 8 with
  R7213 at 49.858 mm, 16 at 50.567 mm.
- All 24 put the block that holds P-K-E1 at one place: (234.75 to 235.25, 182.08 to 182.25), direction −y. The 22
  two-link scenes put the second block at (218.5, 216.0), direction +y. The 24 structures are one slot family.
- A passing structure stopped at its first passing scene, as the brief rules. Other slots of the same 24
  structures were not judged, and neither were the 411 unsearched structures. P-K-E1 alone has 613 survivors on
  40 spots, and every structure with that block is among the unsearched.

So the bounded verdict is right, and the open part of the domain is not small.

## Blocking findings

### 1. The verdict omits the per-structure replay bound, so the bounds are not stated in full

- **Location:** report, "Verdict for U8409" (list of bounds), "Caps", the table "Outcome of a searched structure";
  `result.json` and `checkpoints/run.json`, key `bounds`; `verdict_of` in `replan.py`.
- **Defect:** The brief requires the verdict "with every bound". The cap of 12 rows-only replays per structure was
  reached in 93 of the 123 searched structures and is missing from the verdict's list and from `bounds`. Only 5
  searched structures were exhausted. Structure 122 is counted under "Reached 12 replays with no pass" (94), but
  it was cut by the 1200 cap with 2 replays kept and 10 computed replays discarded; none of the 12 passed. The
  rule that a structure stops at its first passing scene is also a limit on the stage 3 result and is not named.
- **Required correction:** Add to the verdict's bounds: "12 rows-only replays per structure, reached in 93
  structures", and "one scene judged per passing structure (first pass)". State that 122 structures were searched
  to a per-structure end and one was cut at 2 replays. Change 94 to 93 plus 1. Say that the pool takes the
  cheapest survivor of each spot and that the 20-spot limit binds on 15 of the 45 blocks with survivors. Do not
  hand-edit `result.json`; state in the report that its `bounds` list lacks the entry.

### 2. Run 1's STOP 1 was overridden by the executor, against the brief, and the stopped source is not on record

- **Location:** report, "Restart, resume and discarded work" (recorded run 1); `discarded-rev4-run1/`; brief,
  "Source pins" and STOP 1.
- **Defect:** Run 1 stopped at STOP 1 (C8). The brief says to stop and return to the design authority, and that
  no pinned source is edited after the recorded run starts. The executor edited `replan.py`, wrote new pins 102 s
  later and started run 2. The report calls run 1 "discarded" and does not name this as a deviation. The run 1
  source (`5bdd8c12…f139816`) is in neither git nor the cache, so the claim "one key, nothing measured changes"
  cannot be checked against a diff.
- **Acceptable under the brief:** no, not without a ruling.
- **Can it affect the verdict:** no evidence that it can. C1, C3, C3b, C4 to C7, the mutation slots and every
  mutation result of run 1 equal those of run 2. C8 passes on the pinned source when re-run. The stage 3 failures
  come from the unchanged `s12.overlay_part`.
- **Required correction:** The report names the deviation from STOP 1 and from the pin rule. The design authority
  ratifies or rejects it in the disposition with a decision row, as DS-196 did for S15. If the run 1 source can
  still be recovered, retain it or its diff beside `discarded-rev4-run1/`; if not, the report says it is lost.

## Non-blocking findings

### 3. Scene 3's A10 and U4111 results come only from overlay searches 11 and 12, beyond the cap

- **Location:** report, "Kept scenes" (other failures, scenes 1 to 3) and "Caps"; `checkpoints/stage3/33.json`.
- **Defect:** Scene 3 searched U4213, U4227, U4228, U8301, U8313 and U4111 in that order from a count of 6. The
  U8313 search (which moves C8308 and R8334, hence A10) is the 11th and the U4111 search is the 12th. The report
  lists both as failures of scene 3 beside those of scenes 1 and 2, which are within the cap.
- **Acceptable under the brief:** no; the cap is a stated bound. **Can it affect the verdict:** no. A8 at U8413
  and A9 at R7213 hold for all five scenes without any search.
- **Required correction:** Mark scene 3's A10 and U4111 results as over-cap observations, not study evidence, and
  give its recorded failures as A8 (U8413) and A9. The disposition notes the overrun as an executor defect.

### 4. The figures behind A8 and A9 are not on record, and the five judged scenes are not described

- **Location:** report, "Kept scenes"; `checkpoints/stage3/*.json`, which keep the failure texts but drop
  `block_rule` and `placed_ic_blocks`.
- **Defect:** The two decisive failures are given as texts only. No slot, direction, ride host or changed host
  order is given for any judged scene. The brief's "kept scene" reads either as the 5 taken to stage 3 or as a
  scene that passes it; the report uses the second without saying so.
- **Required correction:** Add the reviewer's figures above, or the executor's own, in a new file the driver does
  not import. Per judged scene give the block slots and directions and the ride hosts (P-K-P-L05.01.01 and
  P-K-P-L01.01.02). State which reading of "kept" the report uses.

### 5. The report may not rest on the 19 unjudged scenes, and should say what the reviewer found

- **Location:** report, "Kept scenes" and "What the result can and cannot claim".
- **Defect:** The run judged 5 of 24. The report does not say whether the other 19 could pass. It also does not
  say that the 24 share one slot family.
- **Required correction:** Keep "5 judged" as the run's result. Cite the reviewer's re-judging of all 24 as
  reviewer evidence without the S8 search. Add to "cannot claim": other slots of the 24 passing structures.

### 6. C12 ran after the whole pool search, not first, and C13 was run once before run 1 and reused

- **Location:** report, "Controls" (C12 sentence, C13 row); `stage2b` in `replan.py`; `checkpoints/c13/`
  (16:28Z to 16:33Z, before the run 1 pins).
- **Defect:** The brief puts C12 first in stage 2b. The driver evaluated it after the 1200th replay, in the
  resume segment; the workers had already used pool results to stop at a first pass. The report says "after the
  pool produced its first 12 scenes". C13's record predates both sets of pins, and run 2 read it in 0.0 s.
  Detachment was not shown again after the container restart.
- **Acceptable:** yes. **Can it affect the verdict:** no. C12 passed, `--check` re-ran 3 replays, and the
  reviewer re-ran 24 with equal digests. The resume finished under its guard with rc 0.
- **Required correction:** State when C12 and C13 actually ran.

### 7. The resume ran before the docker daemon was started and the start checks were repeated

- **Location:** report, "Restart, resume and discarded work".
- **Defect:** Resume 1 ran from 17:34:38Z to 17:38:01Z. `dockerd` was started at 17:38:44Z and the start checks
  were repeated from 17:38:53Z to 17:45:59Z. DS-196's conditions were met, but after the resumed work. The
  report gives the times without saying so. The daemon log and the digest check are in the scratchpad only.
- **Acceptable:** yes. Stages 2b to 4 use no oracle, and the repeated checks passed with no tracked change.
  **Can it affect the verdict:** no.
- **Required correction:** One sentence on the order, and the reason it is harmless.

### 8. The cause given for the failed `regen-all.sh --check` is not shown by its log

- **Location:** report, "End checks"; `checkpoints/end-regen-all-check.log`.
- **Defect:** Try 1 and try 2 differ only in temporary directory names and in the last line, "Regeneration
  changed tracked files". The log does not name the file, so the stated cause (the report edited during the
  check) is the executor's account.
- **Acceptable:** yes. Try 2 is rc 0, and the pushed tree is clean. **Can it affect the verdict:** no.
- **Required correction:** Say that the cause is the executor's account and that the log names no file.

### 9. Two small gaps in the accounting

- **Location:** report, "Wall time" and "Restart, resume and discarded work".
- **Defect:** The driver clock ends its first segment at the last tick (17:33:22.6Z), so the seconds up to the
  restart are not in it. The development dry runs are given as a window (16:10Z to 16:37Z), not as a time, which
  the brief asks for.
- **Acceptable:** yes. The total is 94 min of 270. **Can it affect the verdict:** no.
- **Required correction:** Give the dry-run time, and note the uncounted seconds.

### 10. Two NOT RUN items are missing from the table

- **Location:** report, "NOT RUN items and their reasons" and the "Fails" column for scenes 4 and 5.
- **Defect:** The S8 search for scenes 4 and 5 is NOT RUN (cap reached). Their A7, A10 and A11 were evaluated
  without overlay blocks, so "A8, A9" in the table can read as a pass of A10. The reviewer's own NOT RUN items
  (driver, docker, `regen-all.sh`, oracle) belong to this review, not to the report.
- **Required correction:** Add the row, and mark A10 for scenes 4 and 5 as evaluated without the search.

## The six process deviations: one needs a ruling, none can change the verdict

| Deviation | Acceptable under the brief | Can affect the verdict | Finding |
| --- | --- | --- | --- |
| Run 1 STOP overridden, pinned source edited | no, needs a design-authority ruling | no | 2 |
| Overlay searches 12 against 10 | no, an executor defect | no | 3 |
| Restart and resume, bound in structure 122 | yes: per-structure checkpoints, 1 of 3 resumes, pins re-verified; the result equals an uninterrupted run | no | 1 (count of 93) |
| `dockerd` restart under DS-196 | yes, with the order stated | no | 7 |
| First end `regen-all.sh --check` failed | yes | no | 8 |
| Clock, caps and storage | yes; the sums, the 189-file cache and its durable copy reproduce | no | 1, 9 |

## Wording passes on the four fixed points

- The report and `result.json` state rows-level evidence only, unvalidated drafts, and nothing adopted.
- The verdict is in the brief's vocabulary. `CENSUS-COMPLETE` is rightly not claimed, with 534 structures live.
- Exclusions a to e are listed with the verdict as Ruling P1 gives them.
- A12, the pair ratio, checks 2 to 4, stage 4 and the 411 structures are NOT RUN with reasons (finding 10 adds one).
- "U5210 stays blocked with U8409" is the brief's own sentence for a result with no scene.

## What this review does not establish

- Nothing electrical, and nothing about a gate replay: A12 stays NOT RUN.
- That no re-plan exists. 411 live structures are unsearched and 93 searched ones were not exhausted.
- The S8 results of the 19 unjudged scenes: the reviewer judged them without the search.
