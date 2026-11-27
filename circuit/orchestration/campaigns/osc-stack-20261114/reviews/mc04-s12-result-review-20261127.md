# Review of the MC04-S12 result (DS-151): ACCEPT WITH CORRECTIONS

Reviewer: independent read-only session, model Fable 5.2 (`claude-fable-5-2`). Not the executor (`claude-opus-5-5`)
and not the author of the brief, but the same model family as the brief's author. Nothing was edited, committed or
pushed. This file is the only file written. Scratch scripts ran outside the repository.

Under review: study commit `6708d192`, brief Revision 2 (SHA-256 `1ecf7da6…9a2a`, matches), report
`../mc04-s12-report-20261127.md`, `scripts/stack/studies/mc04_s12_five_ic_joint/`. Every board and schematic stays an
unvalidated draft. Nothing here is an electrical acceptance.

## All five verdicts stand

| IC | Executor's verdict | Review |
| --- | --- | --- |
| U1415 | `NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)` | confirmed; rests on P-K-P-L08 alone |
| U5110 | `NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)` | confirmed |
| U8409 | `NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)` | confirmed |
| U5209 | `NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)`, class S disclosed | confirmed, disclosure correct |
| U5210 | `NO SCENE FOUND (BOUNDED BY THE POOL REDUCTION)` | confirmed; the label is the right one |

## All nine census runs reproduce exactly with reviewer code

Method: one scratch script. It takes rule 1 from the retained `links_gate.candidate` on
`links_gate.grid_offsets(step, 35.0)` for 2.0, 0.5 and 0.25 mm, with all eight searched links out of `placed`. Rules
2, 4, 5 and 6 are re-implemented, not called from `s12.py`:

- rule 2: class distances 40 / 45 / 55 / 55 mm written as literals, riders, cable, compliance;
- rule 4: the five recorded courtyards grown 0.35 mm against K field, K tail, slot (both faces) and latch margin;
- T1: displaced footprints by direct courtyard intersection, protected set derived from `io-partition.json`, anchors
  derived from `link-gate.json` and `fixing-sites.json` at `6e5716e7`;
- T2: base-row courtyards grown 0.35 mm on the row's face.

| Link | Legal | After 2 | After 4 | After T1 | After T2 | Class S alone | Equal to `census.json` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P-K-P-L07 (40) | 1929 | 728 | 620 | 0 | 0 | 0 | yes |
| P-K-P-L07 (26) | 4601 | 922 | 904 | 0 | 0 | 59 | yes |
| P-K-P-L08 | 2189 | 787 | 0 | 0 | 0 | 0 | yes |
| P-K-P-L12.02.01.02 | 287 | 120 | 66 | 0 | 0 | 0 | yes |
| P-K-P-L03.01 | 813 | 183 | 183 | 0 | 0 | 0 | yes |
| P-K-P-L13.01.01.01 | 9464 | 8841 | 6903 | 27 | 27 | 465 | yes |
| P-K-P-L13.01.01.02 | 1451 | 497 | 86 | 0 | 0 | 3 | yes |
| P-K-P-L13.01.02.01 | 1962 | 396 | 179 | 0 | 0 | 3 | yes |
| P-K-P-L15.02.01.01 | 6278 | 5440 | 3469 | 73 | 73 | 42 | yes |

The reviewer's T1 violation list equals the driver's on every candidate that reached T1 (0 mismatches in all nine
runs). Protected set: 1734 (K 1182, JL 287, JR 265, P 0), 131 with a base row (K 103, JL 16, JR 12), seven
positionless (U1318, U1415, U4647, U5110, U5209, U5210, U8409). 368 anchored keys, 13 from fixing part moves; equal to
the driver's.

## The driver implements rules 1 to 6 as the brief states them

- **Rule 1.** `s12.census` repeats the loop of `links_gate.search` (same `candidate` call, `spare`, `GeoMaker`,
  directions) on `ctx.grid(step, radius=35.0)`, centred on the recorded search centre, `placed` built with all eight
  searched links skipped. None of the eight carries a slot hold at the base.
- **Rule 2.** `slot_moves.Arm1.accept_for`, unchanged. The limits read 40 / 45 / 55 / 55 mm.
- **Rule 3.** 35.0 mm, plus the ring label. It rejects nothing because the grid is already cut there.
- **Rule 4.** `slot_moves_a2.Arm1A2.accept_for`; gap 0.35 mm, latch margin 1.0 mm.
- **Rule 5.** `links_gate.displaced` with the latch rule; anchors only from non-searched live links and active fixings;
  classes N and S as defined.
- **Rule 6.** Anchored protected rows with a position, courtyard grown 0.35 mm, matched on board and face against all
  eight rectangles of `link_rects`. It changes no count in this run (27 to 27, 73 to 73), so no zero depends on it.
- **26-way L07.** The record is rebuilt with `links_gate.link_record` at the 26-circuit size; 23 circuits needed, no
  allocation error; connector, cable and length come from `link-gate-options.json`. No 26-way scene exists, so nothing
  is presented as a candidate.

## No census zero is an artefact of a strict or faulty rule

- **L08 (U1415).** All 787 class-legal slots put the K field itself on U1415's courtyard, as well as the K tail and
  the latch margin. None passes with an ungrown courtyard, without the latch margin, or without the tail. The 1402
  earlier rejections are all member class distance.
- **L03.01 (U8409).** Rule 4 rejects none of its 183. Every one displaces C8313 and R7216 (class N). The zero does not
  depend on class S.
- **L12.02.01.02 (U5110).** 66 reach T1; all fail on class N (U5205 48, C5218 29, R5149 27, R5268 24, R5162 6).
- **L13.01.02.01.** 179 reach T1; 176 fail with a class N footprint; 3 are class S alone.
- **Growth in T1.** The retained obstacle model grows every courtyard 0.35 mm inside `links_gate.displaced`. With
  ungrown courtyards a first version of the reviewer script let (142.0, 207.0) −y of L13.01.02.01 through; the gate
  itself displaces R2336 and R2381 there. The driver follows the gate, as rule 5 requires.
- **Domain.** One geometry per slot and direction: the shortest legal front and K extensions, as
  `links_gate.candidate` returns it. That is the brief's definition of a candidate. "Exhaustive" does not cover longer
  extensions.

## U5209's class S dependence is characterised correctly

- The three class-S-only candidates of L13.01.01.02 are (159.0, 198.5) −y on the 0.5 and 0.25 mm grids and
  (159.0, 198.75) −y on the 0.25 mm grid. Each displaces R5228, R5250, R5251 and R5253 and meets no T2 courtyard.
- (159.0, 198.5) −y is the recorded slot of L13.01.02.01.
- L13.01.02.01's own three class-S-only candidates are the same three positions. It has no other survivor.
- The report's conclusion follows: relaxing class S gives U5209 no scene unless L13.01.02.01 leaves, and it cannot.

## U5210 is blocked by L03.01, and a wider reviewer test than the executor's agrees

The executor's diagnostic re-tests only the 27 census survivors. It cannot see a slot whose census geometry failed
rules 4 to 6 but which gets another extension once L03.01 is placed. The reviewer therefore enumerated the whole
domain again:

| L13.01.01.01, three grids, 35 mm | Legal | After 2 | After 4 | After T1 |
| --- | --- | --- | --- | --- |
| every other live link at its record | 404 | 404 | 104 | 0 (R8356, class N, on all 104) |
| the same without L15.02.01.01 | 404 | 404 | 104 | 0 |
| the same without L03.01 | 9026 | 8403 | 6901 | 27 |

- With L03.01 at its record, L13.01.01.01 has no rule-legal slot, whether L15.02.01.01 stays or is absent.
- L03.01, L13.01.01.02 and L13.01.02.01 have empty pools, so they stay in every scene.
- `BOUNDED BY THE POOL REDUCTION` remains the correct label under the brief. A scene with L15.02.01.01 at one of its
  moved slots was not enumerated by the reviewer.

## The resume and the dirty-tree flag do not change the result

- **Resume.** `run.json` lists stage 1 only after a child returns 0, and `census.json` is written once at the end of
  the stage. The resumed driver kept arm 0 and the pilot and ran stages 1 to 4 complete. It re-checked the input pins
  first. No partial census was reused.
- **Evidence the kept stages are sound.** `joint_search.py --check` at `6708d192` passes (P1, P3 to P7, P10, P11;
  16 s here). The census reproduces with reviewer code.
- **Not verifiable.** The driver text of the first invocation is not in Git, so "the stage code was not changed" is
  the executor's statement. P2, P8 and P9 come from that invocation.
- **Dirty tree.** The commit adds only the study directory and the report, which fits "the only untracked entry was
  the study directory". Inputs come from a `git archive` of `6e5716e7`, and P1 pins the ten code files.
- **Gap.** The admission bound asks for a clean tree, and the first invocation has no tree-RSS summary. The recorded
  child peaks (1916 and 1887 MiB) are far below 8 GiB.

## The forbidden-writes list is respected

`git show --stat 6708d192`: 24 files, all under `scripts/stack/studies/mc04_s12_five_ic_joint/` plus the report.
Nothing under `design/`, `boards/` or `doc/`; `link-gate-options.json` is byte-equal before and after; `decisions.md`
is untouched. No output calls a draft validated, qualified or released. `candidates/` is empty.

## Corrections required in the report (none changes a verdict)

1. **"9 legality calls" is 13.** `checkpoints/stage3.json` and `result.json` record 13 for the {U5210} set: 1 for
   L03.01, 8 for L15.02.01.01 and 4 for L13.01.01.01.
2. **Survivor counts repeat slots across grids.** The 27 survivors of L13.01.01.01 are 23 distinct slot-and-direction
   pairs; the 73 of L15.02.01.01 are 54. Every census count is a sum over grids, and a 0.5 mm point is also a
   0.25 mm point. Say so beside the table.
3. **L07 as a 26-way also depends on class S.** 59 of its candidates are rejected for class S alone. The table shows
   it; the text names only U5209. It does not affect U1415, which rests on L08.
4. **State the U5210 reasons as first reasons.** `links_gate.candidate` reports the reason of the first extension
   tried. The 22 slot conflicts with L03.01 are definite; the 5 "front field" reasons are the first of several
   extensions that all failed.
5. **Name the extra files.** `s12.py`, `guard.py` and `checkpoints/guard/` are not in the brief's output list. They are
   inside the allowed directory, and checkpoints are required by the run bounds.

## Checks the reviewer did not run

| Check | Status |
| --- | --- |
| `joint_search.py --check` | PASS, 16 s |
| `python -m unittest test_s12` | PASS, 17 tests, 7 s |
| P2 (`slot_moves_a2.py --check`), P8 and P9 full gate replays | NOT RUN: about 20 and 3 minutes each, above this review's limit; read from `checkpoints/arm0.json` only |
| P5 to P7 with reviewer code | NOT RUN: only the executor's code re-ran them under `--check` |
| `--verify-scene N`, reviewer items 4 to 8 and 15 | NOT RUN: no scene was written |
| `regen-all.sh --check`, `pnpm circuit:check` | NOT RUN: the reviewer changed no tracked file; read from the guard records |
| KiCad DRC and ERC, c6, checks 2 to 4, ngspice | NOT RUN: a study edits no board or schematic |
