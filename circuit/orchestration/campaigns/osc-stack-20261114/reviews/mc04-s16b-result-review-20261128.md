# MC04-S16b result review: ACCEPT AFTER CORRECTIONS

2026-11-28. Independent result reviewer. Read-only review at head `9f3accec` of
`local/cloud-engineering-20261127`. No commit, push, docker, KiCad or recorded run. This file is the only change.

| Reviewed item | Identity |
| --- | --- |
| Report | `mc04-s16b-report-20261128.md`, SHA-256 `2e6fe61c343ad4f666dc708b9d208e184369b8346e3690ef78a93ffbb47a5f87` |
| Brief | `mc04-s16b-continuation-brief-20261128.md`, Revision 2 with erratum 1, SHA-256 `fa8dde3edefb84bc098baba413b75564de120ff4c796f5ab92cea975e9dc0bb6` |
| Decisions | `decisions.md`, DS-212 to DS-219 |
| Code and records | `scripts/stack/studies/mc04_s16b_l0301_continuation/` at `9f3accec` |
| Cache | `.circuit-cache/mc04-s16b/` and `/mnt/project-files/osc-s16b-cache/`, 105 files under `bulk-manifest.json` |

All evidence is at rows level on unvalidated drafts. Nothing is adopted, and #318 stays HOLD.

## The measured result stands: 0 of 1800 replays pass rows, and every stated count matches the cache

Recounted from `stage2b/state.json` and the 40 scene chunks, without the study code:

| Report statement | Recount |
| --- | --- |
| Rounds 502/414, 414/413, 413/410, 410/410, 153/153 | equal; no-scene-left 84, 0, 2, 0, 0 |
| Replays per structure: 0 in 88, 1 in 1, 2 in 3, 4 in 257, 5 in 153 | equal |
| 88 with no replay: 84 with no completion, 4 at the legality cap | equal |
| 6 structures at the legality cap, all with 5 or 6 links | equal (indices 481, 483, 484, 486, 495, 501) |
| 410 unfinished, each with 4 or 5 scenes | equal |
| Vectors 1279 / 412 / 83 / 26 | equal; A2 fails in 1717, A3 in 1774, A4 in 412, and none on A0, A1 or A6 |
| A2, A3 and A4 text tallies | equal (R4275 1542, R7319 969, R7315 965; U4225 1549, U4631 1350, U4428 1262, U4422 570; RV4407 412) |
| E1 blocks by spot | equal for all 14 blocks |
| No rows passer, no lite record, stage 3 and 4 empty | equal; no scene carries a `lite` record |
| No non-E1 block on C8443 or R7213 | equal, and re-measured (below) |

## The run record follows Ruling Q3, R7 and the caps

- **Stage order.** The 502 state rows equal the live structures sorted by (links, circuits, summed cost, id).
- **Round order and counting.** Scene numbers 1 to 1800 rise with (round, stage index). No structure has two scenes
  in one round. Round 5 holds exactly the first 153 unfinished structures in stage order. Nothing was counted
  past the 1800th, and `discarded` is empty.
- **E1 spots.** Every offset `o` equals the structure's index among live structures that share its E1 block. In
  every structure the spots follow the cursor, each skipped spot is one recorded as exhausted, and the completion
  number equals the count of earlier scenes on that spot.
- **Completion key.** Within every structure and spot, successive completions rise strictly in (blocks on the two
  parts, summed pool cost, pool indices). The key uses the pool entry's cost. The `cost` field stored per scene
  block is the placed cost, which can differ (P-K-E3 pool entry 0 reads 13.856 or 11.356), so the stored field
  does not reproduce the order by itself.
- **E1 never cut.** The 40 pools were rebuilt from the cached stage 1 survivors: 12 blocks are cut to 20 spots,
  none of them holds P-K-E1, and all 14 E1 pools keep every spot (14, 18, 18 and 2 each).
- **R7.** No E1 pool entry lies on either part. `links_gate.displaced` was called again at the stored geometry of
  all 5350 block placements (191 distinct): 0 E1 blocks and 0 other blocks on C8443 or R7213.
- **Strict R5.** No scene block lists a class S part.
- **Stops and history.** The durable `stops/` folder holds only run 1's record `stop-101c5ce0…9019cfb.json`.
  The study directory's history is `6d5e435f`, `6e72c4b2`, `9f3accec`. `ruling.json` entered at `5caaac98` with
  DS-219. The code change between the two runs is `k3_accept` only, with N15 and the README.

## Issue (i) is a timing defect only: the digested file is reconstructed byte for byte

- `finish()` digests every `checkpoints/**/*.json` except `run.json` and `k3/`. That takes in the guard summaries.
  S16's `replan.py` leaves the `guard` folder out of its digests, which is why S16 does not show the defect.
- `guard15.py` rewrites its summary every 5 s and once more on exit. `result.json` was written at 21:04:20.03Z
  and `guard/run-2.json` at 21:04:24.89Z.
- The present file, with `returncode` set to null, `finished` to false and `wall_s` to 4786.8, hashes to
  `a8fa948f5c086242d510073836eea920fe073d9f712fd7964966839f0a735d89`. That is the digest in `result.json`.
  `samples` (957), the peak RSS, the minimum `MemAvailable` and every other field are unchanged.
- Independent of `--check`: 36 checkpoint digests were recomputed and 35 match, with `guard/run-2.json` the one
  difference. All 105 cached files match the manifest in the cache and in the durable copy, and the manifest
  copy is identical. All 12 pins match.
- `s16b.py --check` was run once in this review (17 s, cache present): rc 1 with the same single error.

No measured value depends on this file.

## Issue (i) is a STOP under the brief's text, so the report's "Ruling Q6 applies" is not yet supported

The brief's text:

- Ruling Q5: "After pins are written, a defect found in the study code is a STOP."
- Ruling Q6: "The stop rule applies only when the run reaches its end with a verdict of Ruling P6, no STOP, no
  scene recorded as `STAGE 3 INCOMPLETE (CAP)` and no `LITE UNDECIDED` scene left unjudged." And: "A run that ends
  in a STOP has no verdict and does not trigger the rule."
- STOP 9: "A STOP is final for the run (Ruling Q5). The executor writes what was found and returns."
- The run bounds list "End K1, `--check`, tests, `regen-all.sh --check`, `pnpm circuit:check`" as a step of the run.
- DS-218: a STOP met outside the driver "is reported to the manager at once, who records it here before any
  restart."

Reading:

- STOP 1 to 10 do not name the end `--check`. It is not a control, and no pin differs. The defect is a STOP only
  through the Q5 sentence, and the report itself calls it one.
- Q6 says "no STOP". The report writes "no STOP inside the driver". That qualifier is not in the brief. The
  executor cannot add it, and neither can this review.
- Three of the four Q6 conditions are met on the record: a P6 verdict written by the driver (rc 0, `stop: null`),
  no `STAGE 3 INCOMPLETE (CAP)` scene and no `LITE UNDECIDED` scene. The fourth is open.
- The driver's own `stop_rule` text is produced whenever no scene is `STAGE 3 INCOMPLETE (CAP)`. It does not test
  for a STOP, so it is not evidence that Q6 fired.

**View for the ruling.** The design authority can rule that this STOP does not void the verdict. The evidence
supports that: the pre-image is reconstructed exactly, the driver had written its verdict before the defect
appeared, no stage reads the file, and a re-run would repeat deterministic replays. Q6 then fires by that
decision row, not by the report. Until the row exists, Q6 has not fired. A re-run is not needed for the measured
result.

## Issue (ii) does not weaken the pins: the erratum brief is pinned and verified

- `pins.json` holds the brief at `fa8dde3e…`, equal to the file at `6e72c4b2` and at head. Pins were written at
  19:38:15Z, before the driver start at 19:44:33Z.
- `drive()` and `--check` call `verify_pins`, which reads `pins.json`. `BRIEF_SHA` is used only in `write_pins`
  and for the `brief_sha256` field of `result.json`. That field (`09e9a228…`) is a stale constant. `result.json`
  `pins` equals `pins.json`.
- Erratum 1, E5 allows only the K3 acceptance, N15 and the README to change, so `BRIEF_SHA` could not be updated.
  The executor took the stricter path and disclosed it in `pins.json`, the README and the report.

## Issue (iii) departs from erratum E3 by one extra K3 run, with no effect on the record

E3 says K3 "runs once for real in the scratchpad". It ran twice (19:27:41Z to 19:38Z), before the pins, and is
disclosed. The recorded K3 (`arm0/K3.json`: −9, 120.0 s, 180 lines, 36 samples, finished, rc 0) is from run 2.

## The verdict wording is right; the bounds understate the pool limit

`NO RE-PLAN FOUND (BOUNDED)` is the only negative verdict the brief allows. The report names the pool cut, the
1800 cap with 410 unfinished, the legality cap in 6 structures, and exclusions a to f with the R7213 note. It
states that `CENSUS-COMPLETE` cannot be given. The points below are not stated.

- **"No legal completion" holds inside the pools only.** A pool holds one survivor per spot. The 40 pools hold 400
  entries of the 8380 in-domain survivors. 64 of the 84 structures with no completion hold a cut block.
- **Slots of other blocks on C8443 or R7213 remain untested.** 748 survivors stay in the domain (Ruling Q2), and
  28 pool entries lie there. No replay used one, in S16b as a whole.
- **The replays repeat.** The 1800 scenes use 191 distinct block placements and give 857 distinct row digests.
- **Cut scope.** 439 of the 502 live structures hold a cut block. 309 of 709 spots are cut.
- **E1 spots per structure.** 246 of the 410 unfinished structures did not try every E1 spot: 4 or 5 of 14, 4 or
  5 of 18, and 2 of 18 in 8 structures. Every E1 spot was used by some structure.
- **Four structures at the legality cap had no replay at all** (indices 481, 483, 495, 501).

## "No further placement study" follows from Ruling Q6 alone, not from the evidence

The result shows that this ordered sample found no rows-level passer. It does not show that no re-plan exists,
and the report says so. The stop rule is a commitment of the design authority under DS-212 and DS-217, and the
owner may still ask for a study. It depends on the ruling asked for in finding 1.

## Findings

### REQUIRED

1. **Q6 is stated as fired while the report also records a STOP.** In "Verdict", replace the paragraph that
   begins "**Ruling Q6 applies.**" and the paragraph after it with:

   > **Ruling Q6 is pending a design-authority ruling.** Three of its four conditions are met: the driver reached
   > its end with a verdict of Ruling P6, no scene is `STAGE 3 INCOMPLETE (CAP)` and no `LITE UNDECIDED` scene is
   > unjudged. No scene passes stage 3 full. The fourth condition is "no STOP". After the driver ended, the end
   > `--check` found a defect in the pinned study code (see "End checks"), which Ruling Q5 makes a STOP. It
   > changes no measured result. Whether it voids the verdict or leaves Q6 to fire is the design authority's
   > ruling, recorded in `decisions.md`. Until that row exists, Q6 has not fired.

   The manager records the STOP and the ruling in `decisions.md` (DS-218). `result.json` and `run.json` keep
   their `stop_rule` text; the row states that this text does not test for a STOP.

2. **"No legal completion" lacks its bound.** In "Stage 2b", replace the bullet "Structures with no replay (88)"
   with:

   > **Structures with no replay (88):** 84 had no legal completion on any E1 spot within the pools, and 4 reached
   > the legality cap before their first. A pool holds one survivor per spot, 400 entries of the 8380 in-domain
   > survivors, and 64 of the 84 hold a block whose pool is cut. This is a bounded finding, not proof that these
   > structures have no legal scene.

   In "What the result can and cannot claim", replace the first paragraph with:

   > It can claim that every live structure of the reduced domain was tried within the pools. 414 had at least
   > one scene, and the 410 left unfinished had 4 or 5. No scene passed A0 to A4 and A6. 88 structures had no
   > replay: 84 had no legal completion within the pools and 4 reached the legality cap first.

3. **The untested part of the domain is not listed in full.** In the side-by-side table, replace the "Not tested
   by either" cell with:

   > slots of 12 blocks beyond their 20 pool spots (309 of 709 spots; 439 of the 502 live structures hold such a
   > block); survivors other than the one pool entry per spot; more completions per spot; scenes beyond the 4th
   > or 5th in 410 structures, 246 of which did not try every E1 spot; the 4 structures that reached the legality
   > cap with no replay; any scene with a block without P-K-E1 on C8443 or R7213 inside the S16b domain beyond
   > S16's 14 failed replays (748 survivors, 0 S16b replays); anything electrical; A12

   Add to the "cannot claim" list:

   > - anything about a slot of a block without P-K-E1 on C8443 or R7213: Ruling Q2 kept those slots in the
   >   domain, and no S16b replay used one;

4. **The end-check section does not give the checkable pre-image.** In "End checks", replace the sentence "The
   guard file as written at `finish()` is not kept, and `result.json` holds its digest `a8fa948f…`." with:

   > The guard file as written at `finish()` is not kept. `result.json` holds its digest `a8fa948f…`. The present
   > file with `returncode` null, `finished` false and `wall_s` 4786.8 gives that digest (result review), so only
   > those three fields changed.

### ADVISORY

5. The 1800 scenes use 191 distinct block placements and give 857 distinct row digests (289 in round 1). A
   sentence in "Stage 2b" would show how much the replays repeat. One S16b row digest equals an S16 replay digest
   under another structure id. K12 compares by structure, so it reports 0.
6. The brief asks for scenes "per E1 block and spot". The report gives totals per E1 block, and a range per spot
   for P-K-E1 only. With no passer the table adds little; a pointer to `stage2b/state.json` is enough.
7. The brief also asks for what the S16 brief lists: per-block census counts, and structures per class. They are
   in `result.json` (`stage1`) and `arm0/K9.json` but not in the report. Add a pointer or the tables.
8. State with the stop rule that the owner may still ask for a study (DS-217, "Reverse by").
9. Issue (iii): the ruling row can note that E3 named one K3 run and two were made before the pins.
10. A later study that reuses this driver should leave `guard/` out of the digests, as S16's `finish()` does.
    This is not a change for this run: STOP 9 forbids editing a pinned source.
11. `brief_sha256` in `result.json` stays stale. The ruling row can name `pins.json` as the governing hash.
12. The legality cap is read as 20 000 calls across a structure's spots. The recorded sums for the 6 structures
    are 15 443 to 19 491, because the calls of the spot in progress are not stored when the cap is reached.

## Checks run for this review

| Check | Result |
| --- | --- |
| `pnpm circuit:check`, before | rc 0, `PASS: component-spec contract; 84 lines` |
| `s16b.py --check`, cache present, `/home/user/venv312/bin/python`, no bytecode | rc 1, `CHECK FAILED: digest of checkpoints/guard/run-2.json differs` |
| Digests, pins, cache and durable copy, recomputed by a scratch script | 35 of 36 checkpoint digests, 12 of 12 pins, 105 of 105 files in both places |
| `links_gate.displaced` on all 5350 stored block placements, scratch script importing `s16b` read-only | 0 on C8443 or R7213 |
| `git status` after these checks | clean before this file |
| `pnpm circuit:check`, after | recorded in the reviewer's hand-back |
| KiCad, docker, `regen-all.sh`, unit tests | NOT RUN: outside a read-only review; the executor's logs were read |

## Overall verdict: ACCEPT AFTER CORRECTIONS

The measured result and the verdict `NO RE-PLAN FOUND (BOUNDED)` are accepted. Findings 1 to 4 are wording
corrections to the report. Ruling Q6 fires only by a design-authority decision row on the STOP of issue (i).
