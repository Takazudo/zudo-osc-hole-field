# MC04-S16b brief review: admit after 7 required fixes

2026-11-28. Independent review of `mc04-s16b-continuation-brief-20261128.md`, Revision 1. Reviewer: Fable agent
(`claude-fable-5-2`), read-only. This review is model output for the manager. It is not an owner approval and it
admits nothing by itself.

Study brief only. Every board and schematic stays an unvalidated draft. Nothing here is validated, qualified or
released. No replay, docker, KiCad or study run was made for this review.

## Target hash matches: `a3ffac9d…67926275`

`sha256sum` of the brief gives `a3ffac9de5b1f81a6d66bc7a7427702163d9e582146f8d72c229c39067926275`. The S16 brief
is `a638d4b8…7d36e7b4`, the S16 report `4cfb457b…ece3ed2`, the result review `f55e5ad2…fc67e94`, and S16's
`bulk-manifest.json` `f031a429…2992caed` with 189 files, all as the brief cites them.

## How the figures were checked: cache counts, plus one geometry probe with no replay

- Cache counts: `/home/user/venv312/bin/python` over `.circuit-cache/mc04-s16/` (`stage1/*.json` survivors,
  `stage2a/structures.json`, `stage2b/*.json` replay logs).
- The cache keeps no survivor geometry and no `displaced` list, so "on C8443 or R7213" cannot be counted from the
  cache alone. For those figures the reviewer built the S12 `World` once (2.5 s, existing snapshot `6e5716e7` in
  the system temporary directory) and called `replan.legal_block` and `links_gate.displaced` on the cached slots,
  with `PYTHONDONTWRITEBYTECODE=1`. No rows-only replay, judgement or oracle ran. `git status` is unchanged by it.

## Q1 strict class S: unambiguous, and it is S12's rule

- `Rules.t1` adds class S refs to the rejection list when `class_s == 'strict'` (`replan.py:451-452`);
  `census_block` and `legal_block` already take the switch (`replan.py:500`, `replan.py:694`).
- S16's control C4 ran that switch against S12's `census.json` (813, 183, 183, 0) and passed. A2 is untouched:
  `check_rows16` calls `s12.check_rows` unchanged (`replan.py:610-618`).
- 0 of 1087 replays with a class S part passed rows: confirmed from the logs.

## Q2 R7 scope: matches DS-212's words, but the cause is the slot, not the block

- DS-212 says "leaves out E1-block slots that lie on C8443 or R7213" (`decisions.md:335`), so E1-only is the text
  the owner chose on. The owner card says "slots clear of … the failed slot family", which reads as any block.
- The A8 failure is `K U8413: a decoupler row breaks the block rule while the IC row is unchanged`. It is raised
  in `s12.overlay_part` from the rows of C8443 alone (`s12.py:641-646`). Nothing in it depends on which sites the
  block carries. A same-size block of other sites at the same slot cuts the same K slot.
- Probe: every one of the 26 non-E1 blocks with a strict survivor has slots on the two parts (12 to 47 each, 748
  of 7665 in all). None loses its last clear survivor, so applying R7 to every block would leave 502 live
  structures.
- Keeping the 748 "last" is coherent only if "last" is enforced. Today it is not (finding 1). In S16, 14 of the
  15 in-domain replays had a non-E1 block on C8443 or R7213, and for 6 of the 26 non-E1 blocks the cheapest strict
  survivor is on the two parts.
- R7 is wider than the failed family. The +x slots at (227.0 to 229.0, 189.0) lie on R7213 only, under
  "K B (field)". S16 has 60 replays there, all failing rows at other parts, and no A8 or A9 judgement. The brief
  says the R7213 evidence is indirect; that is accurate.

## Q3 round order: deterministic across structures, not yet inside a structure

The round rule, the index o and the spot (o + t) mod k are fixed by the text. "The next legal completion …
best-first" is not: the pool order is "clear first, then cost", while S16's best-first is a cost heap
(`replan.py:1650-1716`). The two give different scenes (finding 1).

## Q4 overlay cap: the before-each-search check closes S16's overrun; two gaps remain

- S16 overran because it tested the count once per scene and added `len(overlay_blocks)` afterwards
  (`replan.py:1971-1973`). A wrapper on `w.s.search` (`s12.py:666`) can refuse search 11 without editing S12.
- Gap 1: a lite failure can depend on the search that lite does not run (finding 2).
- Gap 2: the count is not said to survive a resume (finding 5).

## Q5 STOP mechanism: a tripwire and a record, not yet enforceable

A driver that only tests for two files can be passed by deleting `stop.json`, by clearing `checkpoints/`, or by
the executor writing `ruling.json`. S16's override was exactly an edit, new pins and a restart (DS-211). See
finding 4.

## Q6 and the verdicts: two outcomes are undefined

A run that ends in a STOP, and a negative run with a `STAGE 3 INCOMPLETE (CAP)` scene, both have "no scene that
passes stage 3 full". As written, Ruling Q6 would end placement study for U8409 on either (finding 3).

## Controls and mutations: vectors complete and slots real; K1 overstates what `--check` re-runs

- All N vectors have ten candidate and six acceptance positions, and each follows from the test order.
- Slots confirmed against the cache and the probe: N1 (218.0, 181.25) −x is the first survivor of P-K-E1 with
  class S `C7205, U8411`; N3 (235.25, 182.0833) −y gives `K B (slot)`: C8443, R7213; N4 (227.0, 189.0) +x gives
  `K B (field)`: R7213 only; N5 (233.25, 181.25) −y is the first strict survivor clear of both (index 198); N6
  (234.75, 182.5) −y is a strict survivor of the 14-way block on both parts, and all 28 clear survivors of that
  block cost less than its 14 on-part ones.
- N1 to N4 and N7 fail the test they target (R5, R5, R7, R7, R7). N5 and N6 are the matching passes.
- S16's `--check` re-runs `mutation_cases` and four controls only: C3, C3b, C8b and C9 (`replan.py:2274-2285`).
  M19 to M21 live in `test_s16.py` (`test_s16.py:82-160`). See finding 6.
- No case tests the order across structures, or the lite rule of finding 2 (findings 2 and 9).

## Caps and times: consistent with each other and with S16's measured times

- Ceilings sum to 270 min, which is 4.5 h. Expected steps sum to 115.5 to 135.5 min, which is 1.9 to 2.3 h.
- S16 stage 2b took 2593.6 s for 1200 replays, 2.16 s each on 3 workers (`checkpoints/run.json`). 1800 replays
  are about 65 min; 70 min expected leaves 20 min to the 90 min ceiling. Stage 1 took 465 s in S16; 8 min fits.
- 1800 over 502 structures is three rounds (1506) and 294 of the fourth, 58.6 %: "more than half a fourth" holds.
- The cap of 12 per structure cannot bind unless fewer than 150 structures stay unfinished. It is harmless.
- The 90 min stage ceiling is STOP 6, and a STOP is now final (finding 8).

## Figures: all four CONFIRMED

| Figure | Result | Evidence |
| --- | --- | --- |
| 502 live structures in the domain | CONFIRMED | cache: 534 live in S16, 502 keep a class-S-free survivor in every block; probe: R7 empties no E1 block, so 502 stands. 254 dead at S3, 88 + 32 at the census. The K9 table by links and ride sites matches cell by cell |
| Only 15 S16 replays inside the domain, all failed | CONFIRMED | cache: 113 replays with no class S part, 24 pass and 89 fail; probe: 15 of the 113 have the E1 block clear, vector not `PPPPPP` in all 15 |
| 74 of 89 class-S-free failing replays had the E1 block on C8443 or R7213 | CONFIRMED | probe on the logged geometries: fail and on 74, pass and on 24, fail and clear 15 |
| 170 live P-K-E1-only structures, 15 searched and 155 not | CONFIRMED | cache: 170 live structures hold the block `[P-K-E1]`, in S16 and under the strict rule; 15 have a stage 2b log |

Also confirmed: 15 836 survivors, 8665 strict, 40 of 63 blocks; 14 E1 blocks with 1000 strict survivors, 285 on
and 715 clear; P-K-E1 alone 179 on 19 spots, then 132 on 14; the two 8-way pairs 201 on 23, then 154 on 18;
748 of 7665 for blocks without P-K-E1; 118 searched and 384 not; 12 blocks above 20 spots and no E1 pool above
18; 1087 replays with a class S part, 0 passing.

NOT CHECKED: the K7 values at A8 and A9 for the 24 passers (they need replays; they are the result review's
figures), the stage times of S16b, and the 18:25Z time of the owner's choice (the message is not in the
repository).

## Decision rows: DS-214 is accurate and has six columns; DS-215 to DS-217 have two

`git diff` on `decisions.md` shows one added line, DS-214, with the six columns of the log header and terms that
match the brief. The brief's own table gives DS-215 to DS-217 as `ID | Decision` only (finding 7).

## Pinning: the plan leaves S16's sources alone, but `replan.py` writes under S16's paths

The brief adds a new directory and imports `replan.py` unchanged. That module fixes its output paths at import:
`OUTDIR = HERE`, `BULK = .circuit-cache/mc04-s16` (`replan.py:737-745`). Its stage, checkpoint, pin and manifest
functions write there (`ck`, `bulk`, `write_pins`, `write_manifest`, `stage1_one`, `stage2b`). A driver that
reuses one of them changes S16's record (finding 6).

## Findings

### 1. REQUIRED: the order of completions is undefined, and a cost order takes on-part slots first

Evidence: `replan.py:1629-1636` and `1650-1716`; 14 of 15 in-domain S16 replays had a non-E1 block on the two
parts; 6 of 26 non-E1 blocks have their cheapest strict survivor there.

Fix, in Ruling Q3 under "Scene order within a structure", replace the sentence "It is the next legal completion
…" with:

> The blocks other than the E1 block are taken in the structure's block order. A completion is one pool entry per
> other block, legal by `legal_block` with the blocks before it placed and passing `reverify_blocks`. Completions
> of a spot are ordered by this key, lowest first: (number of blocks on C8443 or R7213, summed cost, pool indices
> in block order). Scene t takes the first completion of its spot, in that order, that this structure has not
> replayed. A visit to a spot with no completion left uses no replay; the structure moves to the next spot in the
> same round. A structure whose spots are all used up has no legal scene left. The completion n of a spot is a
> function of the structure, the spot and n only; legality calls are counted once per structure.
>
> Replays count toward the cap of 1800 in round order and stage order, not in order of completion. A replay
> beyond the 1800th in that order is discarded and disclosed.

Add to "Facts": "14 of the 15 in-domain replays had a block without P-K-E1 on C8443 or R7213; one replay had
every block clear of both." Add the same count to K8.

### 2. REQUIRED: a stage 3 lite failure is not always final

Evidence: with no search, `overlay_part` places no overlay block (`s12.py:650-687`), and A7, A9, A10 and A11 are
then judged on a scene without the block poses (`s12.py:688-752`). A search could change those items. Only the
knock-on A8 failure (`s12.py:641-646`) and scenes that need no search are independent of it.

Fix, in Ruling Q4 under "Stage 3 lite", add:

> A lite failure is final only when the scene needs no search (no "overlay search not run" failure), or when it
> has an A8 failure of the kind "a decoupler row breaks the block rule while the IC row is unchanged", or an A5
> failure. Any other scene with "overlay search not run" is `LITE UNDECIDED`: it finishes the structure as a lite
> passer does, and it goes to stage 3 full.

Add mutation N13: "a synthetic failure list with 'overlay search not run' and one A9 failure is `LITE UNDECIDED`
and goes to stage 3 full; with the knock-on A8 failure added it is a final lite failure."

### 3. REQUIRED: Ruling Q6 must not fire on a STOP or on an unjudged scene

Fix, replace the first sentence of Ruling Q6 with:

> The stop rule applies only when the run reaches its end with a verdict of Ruling P6, no STOP, no scene recorded
> as `STAGE 3 INCOMPLETE (CAP)` and no `LITE UNDECIDED` scene left unjudged. Then, if no scene passes stage 3 full,
> the design authority will propose no further placement study for U8409, whatever bounds the verdict names. A
> run that ends in a STOP has no verdict and does not trigger the rule. A negative result with an unjudged scene
> returns to the design authority, which rules on that scene alone.

Add under "Tests a scene must pass": "A negative result is always `NO RE-PLAN FOUND (BOUNDED)`: the pool cut is in
force for 12 blocks. `CENSUS-COMPLETE` cannot be given while a structure is live."

### 4. REQUIRED: the STOP lock must bind to a decision row and survive a deleted file

Fix, replace the second bullet of Ruling Q5 from "On any STOP the driver writes" to "never the executor." with:

> On any STOP the driver writes `checkpoints/stop.json`, sets `stop` in `checkpoints/run.json`, copies
> `stop.json` to `/mnt/project-files/osc-s16b-cache/stops/` under a name with its SHA-256, and exits non-zero.
> It refuses to start, under any pins, while any of the three records exists, unless `checkpoints/ruling.json`
> gives a decision row ID and the SHA-256 of `stop.json`, and `decisions.md` holds a row with that ID whose text
> contains that SHA-256. The manager writes the row and the file, never the executor. The driver cannot tell who
> wrote a file: this is a tripwire and a record, not a lock. The result reviewer checks the durable `stops/`
> folder and the git history of the study directory. A run restarted after a STOP without such a row is
> inadmissible (DS-211).

Extend N10: "with `stop.json` deleted but the `run.json` stop or the durable copy present, it refuses; with a
`ruling.json` whose row ID is not in `decisions.md`, or whose hash differs, it refuses."

### 5. REQUIRED: the overlay count must survive a resume

Fix, in Ruling Q4 under "The overlay cap is checked before every search", add:

> The count is written to `checkpoints/stage3/overlay-count.json` before each search starts, and a resume reads
> it. Searches of a scene cut short by a restart stay counted. The wrapper raises its own exception type, never
> `TypeError`, because `judge_replan` turns a `TypeError` into an A8 failure.

### 6. REQUIRED: K1 must run S16's unit tests, and S16 must be shown intact at the end

Evidence: `replan.py:2274-2285` (controls re-run by `--check`), `test_s16.py:82-160` (M19 to M21),
`replan.py:737-745` (paths fixed at import).

Fix, replace the K1 "Expected" cell with:

> `replan.py --check` of S16 with its cache present gives rc 0: pins verified, C3, C3b, C8b and C9 and the
> mutation results of `mutation_cases` equal, 219 digests. `python -m unittest test_s16` passes (34 tests; M19 to
> M21). S12 `joint_search.py --check` passes. K1 runs again as the last step of the run, and `git status` shows
> no change under S16's directory.

Fix, in Ruling Q5 under "Fresh run", add:

> The S16b driver calls only library functions of `replan.py`. It never calls `drive`, `finish`, `stage1`,
> `stage1_one`, `stage2a`, `stage2b`, `search_one`, `stage3`, `stage4`, `stage4_one`, `block_pool`, `ck`, `bulk`,
> `write_pins`, `write_manifest` or the control functions that write a checkpoint, because they write under
> S16's paths. It does not set `S16_DEV_OUT`. Pins also cover S16's `bulk-manifest.json` and `result.json`.

### 7. REQUIRED: give DS-215 to DS-217 in the six columns of the log

Fix, replace the three proposed rows in "Decision rows" with:

> | ID | Date | Decision | Decided by | Basis | Reverse by |
> | --- | --- | --- | --- | --- | --- |
> | DS-215 (proposed) | 2026-11-28 | S16b Rulings Q1 and Q2: the strict class S preflight of S12 replaces Ruling P3 for this run; an E1-block slot on C8443 or R7213 is left out as labelled exclusion f; slots of other blocks on those parts stay in the domain and are taken last | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s16b-continuation-brief-20261128.md`; `reviews/mc04-s16b-brief-review-20261128.md`; DS-212 | Design-authority ruling |
> | DS-216 (proposed) | 2026-11-28 | S16b Rulings Q3 and Q4: the E1 block is taken first across all its spots, in rounds over the live structures, at most 1800 replays; every rows-level passer is judged without the S8 search and then with it; the cap of 10 overlay searches is checked before each search | Design authority (DS-03: Fable agent at high effort), owner notified | same | Design-authority ruling |
> | DS-217 (proposed) | 2026-11-28 | S16b Rulings Q5 and Q6: a fresh pinned run in its own directory, S16's files untouched; a STOP ends the run and only a decision row reopens it; a completed run with no scene passing stage 3 full and no unjudged scene means no further placement study for U8409 is proposed | Design authority (DS-03: Fable agent at high effort), owner notified | same; DS-211, DS-212 | Design-authority ruling; the owner may still ask for a study |

### 8. ADVISORY: make the stage 2b time a bound, not a STOP

A step ceiling is STOP 6 and a STOP is final. A slow stage 2b would end the one run with no verdict. Wording: "No
round or scene starts after 80 minutes of stage 2b. This is a bound, named in the verdict. The 90 minute ceiling
stays as STOP 6."

### 9. ADVISORY: add a case for the order across structures

Wording for N14: "three synthetic structures share an E1 block with k = 2: round 1 gives spots 0, 1, 0 in stage
order, round 2 gives 1, 0, 1; a structure finished in round 1 has no scene in round 2."

### 10. ADVISORY: consider R7 for every block, or state why not

The A8 mechanism is the slot on C8443, whichever block cuts it. Applying R7 to all blocks removes 748 survivors,
empties no block and keeps 502 live structures. If the E1-only scope stays, add to Ruling Q2: "The A8 failure of
the 24 scenes comes from the slot standing on C8443, so a slot of another block there is expected to fail the
same way. It is kept only because no replay has tested it, and finding 1's order takes it last." Either way the
report should count, per scene, the blocks without P-K-E1 on either part and how those scenes fared.

### 11. ADVISORY: name two more bounds and one wording point

- "A structure that finished on a lite passer which then failed stage 3 full was not searched further" is a
  bound and belongs in the verdict.
- Under "Mutations", add: "A case given as a block at a slot has no replay, so its acceptance tests are not
  evaluated."
- Ruling Q3, "Pools": state the tie-break, "(cost, `key`)", as `pool_of` has it (`replan.py:1634`).

## Overall verdict: ADMIT AFTER FIXES

Findings 1 to 7 are required before admission. They change wording, order rules and controls; they change no
figure. Every figure the brief rests on that could be counted reproduces. Findings 8 to 11 are advisory. A
re-review can be by inspection of the seven changes.

## `pnpm circuit:check`: PASS before and after

Both runs from `/home/user/wt-a`: `PASS: component-spec contract; 84 lines; offline=True; refreshed=none`, exit 0.
The scope line reads: inventory provider manual, schematic and placement binding not performed (445 declared
placements unverified).

## Re-check of Revision 2: ADMIT, no required fix remains

2026-11-28. Re-check of Revision 2 of the brief, read-only, by the same reviewer. Nothing was run except
`sha256sum`, `git status`, `git diff` and `pnpm circuit:check`. This is model output for the manager, not an owner
approval. The brief is still a study brief; every board and schematic stays an unvalidated draft.

### Revision 2 hash matches: `09e9a228…8100e625`

`sha256sum` gives `09e9a22855b141429abb55b842085bb4e9ce2daae696e3bb596579b38100e625`. The brief cites this
review at `ec802347…e529d656`, which was its hash before this section was appended.

### All 7 required findings are closed by the text

| # | Finding | Closed by | Result |
| --- | --- | --- | --- |
| 1 | completion order | Ruling Q3, "Completions of a spot" (key: blocks on the two parts, summed cost, pool indices), the skip rule, "Counting"; Facts and K8 carry the 14 and 1 split | CLOSED |
| 2 | lite failure not always final | Ruling Q4, "When a lite failure is final"; `LITE UNDECIDED` goes to stage 3 full; N13 | CLOSED |
| 3 | stop rule conditions | Ruling Q6 replaced; "always `BOUNDED`" under the tests table | CLOSED |
| 4 | STOP record | Ruling Q5: three records, `ruling.json` with row ID and hash tested against `decisions.md`, "a tripwire and a record, not a lock"; N10 extended; STOP 9 | CLOSED |
| 5 | overlay count across a resume | Ruling Q4, "The count is kept on disk"; own exception type; N9 | CLOSED |
| 6 | K1 and S16's writers | K1 cell replaced, K1 repeated as the last step; the list of functions not to call; pins on S16's `bulk-manifest.json` and `result.json` | CLOSED |
| 7 | six-column rows | "Decision rows": DS-215 to DS-217 with ID, Date, Decision, Decided by, Basis, Reverse by | CLOSED |

### The six edits beyond the review's wording are sound

- **Stage 3 full order.** Lite passers first, then `LITE UNDECIDED`, each in ranking order. This spends the 10
  searches on the scenes with no known failure first. Sound.
- **N11 names an A5 failure.** A5 comes from `block_figures` and does not depend on the search
  (`replan.py:625-651`), so it is a final lite failure under Ruling Q4. N11 and N13 now agree with the rule.
- **N9 extended.** It tests the exception type, the count file before each search and the value a resumed
  process reads. It covers finding 5.
- **K7 as a reading.** The final-or-undecided status of the 24 scenes is not on record for 19 of them, so a
  reading is right. The 5 judged scenes carry the knock-on A8 text (`checkpoints/stage3/*.json`), which Ruling Q4
  makes final.
- **Ceilings.** 15 + 30 + 55 + 10 + 90 + 30 + 20 + 20 = 270 min. Expected steps sum to 117.5 to 141.5 min, which
  is 2.0 to 2.4 h. Stage 1 took 7.75 min in S16, so 55 min is ample.
- **STOP 9 and check 7.** Both now match Ruling Q5 and claim no lock.

### Advisory rulings: 8, 9 and 11 are applied as written

The 80 minute bound is in Ruling Q3, the stage list and the caps table, with 90 minutes kept as STOP 6. N14
gives spots 0, 1, 0 and then 1, 0, 1 for o = 0, 1, 2 and k = 2, which follows from (o + t) mod k. The extra
bound, the mutation note and the `(cost, key)` tie-break are all present.

### Rejecting advisory 10 is coherent

- DS-212 names E1-block slots (`decisions.md:335`), so the scope is the one the owner chose on.
- A completion with a block on C8443 or R7213 now sorts after every all-clear completion of the same E1 spot.
  Each scene of a structure uses a different spot until the spots repeat, so such a scene is replayed only when
  a spot has no all-clear completion left.
- Ruling Q2 states that such a slot is expected to fail and why it is kept, and the report counts those scenes
  against the others. The run then supplies the replay evidence that is missing today.

### DS-215 to DS-217: six columns, accurate to Revision 2

The three rows match Rulings Q1 to Q6 as revised. DS-214 in `decisions.md` still cites Revision 1
(`a3ffac9d…`); the brief says so. The admission row should cite the hash of the revision that is admitted.

### No new defect; two wording points, neither blocks admission

1. ADVISORY. N10 must not touch the real durable folder, or the test leaves a stop record that blocks the run.
   Wording, added to N10: "The durable folder is a scratch path in this test; no file is written under
   `/mnt/project-files/osc-s16b-cache/stops/`."
2. ADVISORY. A STOP raised by the executor outside the driver (STOP 2 at the start checks) writes no record.
   Wording, added to Ruling Q5: "For a STOP outside the driver, the executor runs the driver with
   `--record-stop <reason>`, which writes the same three records."

The manager can apply both by inspection. They change no rule, figure, cap or vector.

### Verdict on Revision 2: ADMIT

No required fix remains. Not re-checked: the figures (unchanged from Revision 1, confirmed above), and anything
that needs a replay.

### `pnpm circuit:check`: PASS before and after the re-check

Both runs from `/home/user/wt-a`: `PASS: component-spec contract; 84 lines; offline=True; refreshed=none`, exit 0.
Schematic and placement binding was not performed (445 declared placements unverified).
