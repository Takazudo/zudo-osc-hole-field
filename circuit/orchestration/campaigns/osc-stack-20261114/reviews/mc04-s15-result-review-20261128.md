# MC04-S15 result review: ACCEPT WITH CORRECTIONS (2 blocking, 10 non-blocking)

2026-11-28. Independent review of the completed MC04-S15 study at `dd9ef192` on
`local/cloud-engineering-20261127`. The reviewer is not the executor and not the brief author. Read-only, except
for this file. The search driver (`--run`) and docker were not started. Geometric evidence only; every board and
schematic stays an unvalidated draft and nothing is adopted.

Reviewed: the brief Revision 3 (SHA-256 `8283667186ae355ac0b18c94cdd21f30fbc0ea8fd02286633aef1e338ad2c378`,
verified), its review (`d1ffe455…e2b73856`), DS-188 to DS-192, `mc04-s15-report-20261128.md`
(`2e558a04…e2037a92`), `scripts/stack/studies/mc04_s15_no_growth_moves/` and the ignored cache
`.circuit-cache/mc04-s15/`.

Both blocking findings are corrections to the report text. Neither needs a re-run, and neither changes a verdict.

## The four verdicts stand: every count re-derives from the cache, and no verdict rests on a set-aside failure

All four ICs keep `NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD)`. The verdict is the one the
brief's Ruling N5 allows: every distinct rule-4 survivor that is gate-legal at record was replayed and failed, the
stage 2 cap was not reached (489 of 1000), and the illegal-at-record count stands beside each verdict.

Re-derived by a script written for this review, from `checkpoints/stage1.json` and `screen.json` in the cache:

| IC | Link | Distinct after rule 4 | Legal at record | Replayed | Same slot set | Pass | Joint-only | Dropped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| U5110 | L12.02.01.02 | 44 | 16 | 16 | yes | 0 | 28 | 0 |
| U8409 | L03.01 | 131 | 131 | 131 | yes | 0 | 0 | 0 |
| U5209 | L13.01.01.02 | 57 | 25 | 25 | yes | 0 | 32 | 0 |
| U5210 | L13.01.01.01 | 5439 | 81 | 81 | yes | 0 | 5358 | 0 |

- **U8409.** All 131 records pass A1 and fail A3. All 131 also fail NG1.
- **Where NG decides.** U5110: 16 of 16 records pass A1, A3, A4 and A6 and fail NG. U5210: 51 of 81. U5209: 1 of
  25. Every one of the 253 records on the four needed links fails NG1.
- **NG1 and NG2 recomputed.** For every evaluated net and board of all 489 records, the stored paper, base and
  scene figures and the Ruling N3 limit give the recorded NG1 and NG2 result: 0 differences.
- **Dependence, stronger test than the brief asks.** With both set-asides applied together (nets without a mover
  ignored, and `max(paper, base)` as the limit), no record on a needed link passes. Each of the 68 NG-decided
  records keeps a failing net that has a mover, or an NG4 failure. The smallest worst-case excess over
  `max(paper, base)` on a protected-mover net is 6.25 mm (L13.01.01.01) and 13.45 mm (L13.01.01.02).
- **Joint-only survivors are outside "complete".** The driver sets `complete_screen` from the legal-at-record
  count alone, and each verdict line gives the joint-only and dropped counts. No verdict counts a joint-only
  survivor as screened.
- **Tallies.** First failures 224 NG1, 176 A3, 45 A1, 42 A4. Vectors 273, 180, 23, 8 and 3. 193 failing nets,
  median 22, maximum 42. 15 ICs and 123 passives. The after-each-test table equals `result.json` for all six links.
  All four strictness flags are unset in all 489 stage 2 records and all 16 stage 3 rejected scenes.
- **Replays by the reviewer.** `--check` re-ran records 0 to 2. Five further records were replayed for this review
  (indices 15, 16, 151, 264 and 452, one per link except L13.01.02.01): all equal `screen.json` apart from
  `wall_s`.

## Controls C1 to C18 and the mutations passed as specified, and the derived code equals S12 on a real moved scene

- **Records.** All 18 control records are `pass: true` and the figures in the report equal them. `test_s15.py`
  gives 30 tests OK when run by the reviewer. Its vectors equal the brief's table. Its file time (12:59Z) is before
  the development dry run and the recorded run.
- **C10.** S12 survivors 0, 0, 27, 0, 0 and 73, and 66, 183, 6903, 86, 179 and 3469 after rule 4, with no
  difference from `census.json`.
- **C11.** The eight S12 sets are reproduced, {U5210} with 13 legality calls and no complete scene. See finding 7
  for how little S12 code that exercises.
- **C8.** `judge_ng` with `rules='s12'` equals both the P11 record and `s12.judge` on the all-stay scene.
- **Reviewer's extra check.** On the returned S10 scene (`s12.RETURNED`), `check_rows_ng` and `judge_ng` with
  `rules='s12'` equal `s12.check_rows` and `s12.judge` (fails A2; and A2, A8, A9, A10, A11). The README's line
  counts for all seven derived functions equal a fresh `difflib` run, and the diffs hold only the rule switch.
- **C18.** 2357 nets on 2782 net-boards. The reviewer ran `Model._board_tests` with the base limit on each: 0
  failures. 457 nets have a base figure above paper. See finding 6 for the wording.
- **C17.** 180 heartbeat lines and 35 of 59 guard samples after the wrapper ended.

## The storage split verifies: 23 cached files match the manifest, and an absent cache is reported as NOT RUN

- **Hashes.** All 23 cached files equal `bulk-manifest.json` and `result.json` in SHA-256 and size (70 916 984
  bytes). The 29 tracked digests also match.
- **Cache present.** `--check` run by the reviewer: PASS in 38 s, 52 digests, 3 replays, summaries and verdicts
  rebuilt equal. No tracked file changed.
- **Cache absent** (simulated by pointing the cache path at an empty location; the real cache was not touched):
  29 digests and the stage 3 and 4 rebuilds pass, and one `NOT RUN:` line names the 23 digests, the 3 replays and
  the stage 1, stage 2 and verdict rebuilds. Exit code 0.
- **Cache altered** (a scratch copy with one changed byte): `--check` fails and names the file.

## The run-time fixes, the dockerd restart and the clock left the measure unchanged

- **Fixes.** The 52 checkpoint digests are unchanged by the 14:08 split, and `--check` with the committed code
  reproduces 11 controls and 8 stage 2 records. See finding 11 for the missing run-time code hash.
- **Dockerd.** Only `regen-all.sh` uses the oracle. Start try 2 and the end `--check` both returned 0 with no
  tracked change. The search is pure Python. See finding 10 for the procedure.
- **Clock.** `run.json`: 2170.1 s driver plus 1253.1 s executor-timed, 3423 s. The executor-timed sum includes the
  discarded first start try (15.8 s). Every step is inside its ceiling: start 465 s of 900, arm 0 with C17 989 s
  of 2100, end 487 s of 900. Resumes 0. See finding 9 for the uncounted items.
- **Allowed paths.** `dd9ef192` adds only the report and the study directory. No S12 file changed.

## Findings

### 1. Blocking: the two stage 2 "passers" are the record slots, so no single move of any link passes

- **Location.** Report, heading "Per link … only two single moves pass (neither claims an IC)", the two lines after
  the stage 2 table, and the stage 3 table; `result.json` `stage2.per_link.*.pass`.
- **Defect.** L13.01.02.01 at (159.0, 198.5) −y and L15.02.01.01 at (193.0, 213.0) +y are those links' own record
  slots. Their pool geometry equals the stay entry, `links_changed` is empty, 0 rows change, and both have the
  same rows digest (`f82917e1…`). They are the all-stay scene, not moves. 487 of 487 real moves fail. The stage 3
  pools of these two links therefore hold the record twice, and three of the 16 set 8 scenes are repeats (L15
  choices 0 and 1 are the same geometry): 13 distinct scenes.
- **Required correction.** State that the two passing records are the record slots and that no real single move
  of any of the six links passes. Give 487 of 487. Reword the pool note and give 13 distinct scenes for set 8.

### 2. Blocking: the stage 3 bound is understated; no joint-only survivor of U5110's or U5210's link was ever judged

- **Location.** Report: the paragraph "The qualifier is required", the stage 3 table, the caps row "this cut is
  the stage 3 bound", and "What this result can and cannot claim".
- **Defect.** The 60-entry cut is not the operative bound. From `stage3/pools.json` and `set-N.json`:
  - L12.02.01.02: 28 joint-only survivors, 7 spot representatives, 7 legality calls, all illegal, 0 replays. The
    South cluster is searched with the East links at record, where a joint-only candidate is illegal by
    definition. No cross-cluster scene was formed.
  - L13.01.01.01: 5358 joint-only survivors, 167 spots, 60 pooled, 0 ever legal, 0 replays. Most are blocked by
    L03.01, and L03.01 has no pool entry because all 131 of its single moves fail.
  - L13.01.01.02: 32 joint-only survivors, 8 spot representatives, all 8 replayed, in scenes that also move
    L13.01.02.01 to one pool entry.
  - One representative per spot (direction and 2.0 mm cell) is itself a bound: 28 to 7, 32 to 8, 27 to 7,
    5358 to 167 and 2527 to 89.
- **Required correction.** Say per IC how many joint-only survivors reached a replay: U5110 0 of 28, U5210 0 of
  5358, U5209 8 representatives of 32. Name every bound: the per-spot representative, the 60 cut, the cluster
  split, the empty L03.01 pool and the dropping of failed single moves. Replace "this cut is the stage 3 bound".

### 3. Non-blocking: the heading "No cap was reached" contradicts its own table

- **Location.** Report, caps section.
- **Defect.** The pool cap was reached on two links, and the row says so. Ruling N5 says "no cap was reached"
  without naming the cap. The report reads it as the stage 2 cap and does not list that reading.
- **Required correction.** Head the section with the caps that were and were not reached. Add the reading to the
  list, citing the brief's stage 2 text, which ties "complete" to the stage 2 replays alone.

### 4. Non-blocking: `screen.json` is a named brief output and now exists only in this container

- **Location.** Report, "Bulky intermediates"; README; brief "Outputs".
- **Defect.** The brief lists `screen.json` in the study directory. "Everything the brief requires stays tracked"
  is therefore false. "The owner rule" has no citation; the written rule is `circuit/ORCHESTRATION.md` section 6,
  which also requires recovery-critical bytes to be stored outside an ephemeral VM. The cache is ignored and
  local. A re-run cannot reproduce the manifest hashes, because every record carries `wall_s`.
- **Required correction.** Record the move as a deviation from "Outputs" and cite the rule. Before the container
  is released, either store the 23 files as a budgeted artifact with verified hashes, or track a compact table
  (per record: link, slot, direction, claimed ICs, acceptance, NG vector, rows digest; per link: class counts).

### 5. Non-blocking: `--check` on a partly present cache ends in a traceback

- **Location.** `no_growth.py`, `check()`.
- **Defect.** With `screen.json` missing and other cached files present, `--check` raises `FileNotFoundError`
  instead of `CHECK FAILED` naming the file. With the cache absent it exits 0, which a caller cannot tell from a
  full pass.
- **Required correction.** Stop with the `bulk_state` problems before reading the cache. Consider a distinct exit
  code or first line for the partial check.

### 6. Non-blocking: C18 is described with the wrong limit

- **Location.** Report, controls table, C18; `no_growth.py` `c18`.
- **Defect.** "Forced through min(paper, base)" is wrong. The control compares against the base figure, as the
  brief says. Under `min(paper, base)` 459 net-boards would fail. The control tests figure equality and does not
  call the test function.
- **Required correction.** Write "against the base figure". Optionally call `_board_tests` in `c18`; the reviewer
  did and found 0 failures.

### 7. Non-blocking: C11 exercises very little of the S12 search

- **Location.** Report, controls table, C11.
- **Defect.** The S12 stage 3 record holds 13 legality calls and 0 replays, so C11 never runs the A2 rejection
  path. The control passed as the brief specifies.
- **Required correction.** State the size of what C11 reproduces. The reviewer's extra check above may be cited.

### 8. Non-blocking: the counts are on the distinct basis, which the verdict lines do not say

- **Location.** Report, verdict table and stage 1 table.
- **Defect.** The brief expected "about 104" legal-at-record survivors for L13.01.01.01. The run has 81 distinct,
  which is 104 across the three grids. The same holds for the illegal counts: 28, 32 and 5358 distinct are 42, 48
  and 6799 across grids.
- **Required correction.** Add "distinct" to the verdict lines and give the 104 beside the 81.

### 9. Non-blocking: the clock omits about 9.5 minutes of disclosed work

- **Location.** Report, run table and "Discarded work".
- **Defect.** Not in the 3423 s: the dry run (about 450 s, on real data: C10, stage 1 and three replays), three
  rebuilds (about 45 s) and the checks after the split (about 70 s). All-in the total is about 66 minutes. C17
  overlapped start try 2, so those two are counted twice. Try 1 ran at 12:52Z, not "about 12:53Z".
- **Required correction.** Give the all-in figure beside the 57.1 minutes. No ceiling is affected.

### 10. Non-blocking: the dockerd restart was a STOP 2 condition handled by the executor

- **Location.** Report, "Discarded work", start try 1.
- **Defect.** STOP 2 names a missing oracle at the start and forbids a workaround. The executor started the daemon
  and continued without returning to the design authority. The measure is unaffected.
- **Required correction.** The disposition should ratify the restart, or record the reading that a stopped daemon
  after a reboot is an environment fault and not a missing oracle.

### 11. Non-blocking: the code as run was not hashed

- **Location.** `checkpoints/pins.json`, `result.json` fingerprint, report fix table.
- **Defect.** `no_growth.py` was edited after the run ended (13:55Z; file time 14:11Z). The fingerprint commit is
  `ec161b30`, which does not hold the code. "Storage only" cannot be shown by a diff.
- **Required correction.** State this, and cite the evidence that stands in for it: unchanged checkpoint digests
  and the replays that equal the records. Pin the three study source hashes in later studies before the run.

### 12. Non-blocking: the set 8 failure note is incomplete

- **Location.** Report, stage 3 table, set 8.
- **Defect.** All 16 scenes fail A3. Two of them also fail A1 and A4. "14 also fail A3, and 2 also fail A1 and A4"
  reads as if those two pass A3.
- **Required correction.** Write "all 16 also fail A3; 2 of them also fail A1 and A4".

## The seven readings change no verdict; three more were taken and are not listed

R1 matches the brief's own C5 wording (1 run skipped, 6 extents and 12 pin distances compared). R2, R5 and R7 are
the stricter readings. R3 and R4 are ordering. R6 restates the brief. Unlisted readings: the meaning of "no cap"
(finding 3), the distinct basis (finding 8) and the place of `screen.json` (finding 4).

## Wording is within the brief's limits

The report, README and `result.json` say geometric evidence only and unvalidated draft. The NOT RUN table gives a
reason per item. No text says "exhaustive", validated, qualified or released. Adoption is left to a separate
reviewed change and an owner decision on DS-150 (DS-192).
