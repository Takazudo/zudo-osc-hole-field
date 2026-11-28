# MC04-S16 disposition: result accepted as bounded rows-level evidence; U8409 is not decided; one aimed continuation is worth its cost

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Written at head `6291737c` of `local/cloud-engineering-20261127`. Status: **draft, uncommitted,
pending the manager and the owner**.

Subject: the Revision 4 run of MC04-S16 (`mc04-s16-report-20261128.md`, `4cfb457b…ece3ed2`, as corrected), brief
Revision 4 (`a638d4b8…7d36e7b4`), independent result review `reviews/mc04-s16-result-review-20261128.md`
(`f55e5ad2…fc67e94`, ACCEPT WITH CORRECTIONS, corrections applied in `6291737c`).

Nothing is adopted. No board, schematic, specification, BOM, gate record, generator or generated file changes.
Every board and schematic stays an unvalidated draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD. Panel
hardware stays at `design/grid/placements.lock.json`. Nothing is bought, built or ordered.

## Ruling on the result: accepted as rows-level geometric evidence, with every bound

- The verdict `NO RE-PLAN FOUND (BOUNDED)` for U8409 is accepted. It is the right verdict of the three in Ruling
  P6, and the review reproduced it.
- It is evidence at rows level on the link gate's own functions and on courtyard geometry. A12 (the full gate
  replay), the DS-122 pair ratio, checks 2 to 4, routing, DRC and ERC are `NOT RUN`. It says nothing electrical.
- It is not a finding that no re-plan exists. 411 of 534 live structures were not searched, 93 searched ones
  stopped at 12 replays, pools were cut to 20 spots, and exclusions a to e of Ruling P1 apply.
- The reviewer's judging of all 24 passing scenes is accepted as reviewer evidence, beside the run's own "5
  judged, none passes".

## The run 1 STOP 1 override is ratified for this run only, and the rule stands

The executor's run 1 stopped at STOP 1 (control C8). The executor then edited the pinned `replan.py`, wrote new
pins 102 s later and started run 2 without returning to the design authority. The brief allows neither step.

**Ruling.** The override was a breach of the brief. Its effect on this result is ratified after the fact, on
these grounds:

- **The cause was a defect in a study control, not in a rule.** `judge_replan` always added one key that
  `s12.judge` does not have. Every shared item was equal.
- **The change is on record.** Run 1's source is retained with SHA-256 `5bdd8c12…f139816`, equal to the run 1
  pin, with a diff of one line becoming two.
- **Nothing measured changed.** C1, C3, C3b, C4 to C7, the mutation slots and every mutation result of run 1 equal
  those of run 2. The reviewer re-ran C8 on the pinned source, and it passes.
- **The verdict does not pass through the changed line.** The stage 3 failures are raised in the unchanged
  `s12.overlay_part`.

**What is not ratified.** No executor may clear a STOP by itself. A STOP caused by a defect in study code still
returns to the design authority before any pinned source changes. A second override in this campaign makes the run
inadmissible, whatever its effect.

Other deviations, as the review ranked them:

| Deviation | Ruling |
| --- | --- |
| 12 overlay block searches against a cap of 10 | executor defect, recorded. Searches 11 and 12 are over-cap observations and are not evidence. No verdict uses them |
| C12 ran after the pool search, not first; C13 was run once before the run 1 pins | accepted: C12 passed, `--check` re-ran 3 replays and the reviewer re-ran 24 with equal digests |
| Resume ran before `dockerd` was started and the start checks repeated | accepted under DS-196: stages 2b to 4 use no oracle, and the repeated checks passed with no tracked change |
| First end `regen-all.sh --check` failed, second passed | accepted; the cause stays the executor's account |

## Interpretation: the run tested less than its numbers suggest

The figures in this section are read-only counts from the run's cache (`.circuit-cache/mc04-s16/`, 189 files
under `bulk-manifest.json`) and from the gate's geometry functions, made for this disposition. They are not
reviewed. No replay was run.

| Replays of stage 2b | Count | Passed A0 to A6 |
| --- | --- | --- |
| With a class S part under some block | 1087 | 0 |
| With no class S part under any block, E1 block outside the one slot family | 82 | 0 |
| With no class S part under any block, E1 block in the slot family | 31 | 24 |
| **All** | **1200** | **24** |

- **Ruling P3 cost the run most of its budget.** P3 let a slot stand on one of the six parts L03.01 displaces
  today and left the judgement to the replay. 1087 replays tried such a slot and every one failed, 1009 of them at
  U8411. The pools were filled with such slots before the others were reached. That was this design authority's
  ruling, not an executor choice. S12's stricter preflight would have been the better rule.
- **The one family that passes rows cannot pass the overlay items.** In all 24 passing scenes the block that holds
  P-K-E1 sits at (234.75 to 235.25, 182.08 to 182.25), direction −y. At the three judged slots checked here, that
  block's slot lies directly on C8443 and R7213 on the K rear face. So C8443, the decoupler of U8413, and R7213
  must move in every scene of the family. The reviewer found A8 and A9 failing in all 24. The family is closed.
- **The misses are not all small.** R7213 ends 0.7 to 1.4 mm farther from U7204 than its 49.159 mm at the base.
  C8443 ends on the other face, or at 16.672 mm against 5.690 mm. Whether either matters is an electrical
  question. Nothing on record answers it, and S13 and S14 spoke against growth on protected nodes.
- **Only 82 replays tested the open question.** They used 15 distinct E1-block slots in 24 structures, and all
  failed A2 to A4: U8413 with no position (29), the trimmer RV8408 changing face (29), U4225, R4275, U4631 and
  U4428 with no position or a new protected row.
- **What a passing scene looks like so far.** Ranks 1 and 2 replace the 26-way link by one 14-way link, with three
  sites riding on P-K-P-L05.01.01 and P-K-P-L01.01.02. The link count would stay 62. These scenes fail stage 3, so
  no link, latch or hand-work figure is established.

## The open domain is smaller than "411 structures" suggests

P-K-E1 never rides, so every structure has one block that holds it. With slots on a class S part left out:

| Block holding P-K-E1 | Census survivors | With no class S part | On how many spots | Of all survivors, clear of C8443 and R7213 |
| --- | --- | --- | --- | --- |
| P-K-E1 alone (8-way) | 613 | 179 | 19 | 566 of 613 |
| K-P-16 + P-K-E1 or K-P-20 + P-K-E1 (8-way) | 635 each | 201 each | 23 each | 588 of 635 |
| K-P-18 + P-K-E1, P-K-E1 + P-K-E2 (14-way) | 186 each | 42 each | 4 each | 172 of 186 |
| 14-way blocks with P-K-E1 and P-K-E3 | 35 to 42 | all | 4 | 21 to 28 of 35 to 42 |

So the untested part is: class-S-free slots of the E1 block away from the failed family, mostly in directions +y
and +x, together with the other blocks of each structure. All 155 structures with P-K-E1 alone are in it, and
none was searched.

## A bounded continuation is worth one run, and no more

**For it:**

- U8409 is not decided. The study the owner chose was meant to decide it, and 1087 of its 1200 replays were spent
  on slots that could not pass.
- The fix is known and small: restore S12's strict class S preflight, leave the failed family out, take the E1
  block first and spread the budget over its class-S-free spots, and judge every rows-level passer for A8 and A9
  before any S8 search.
- The cost is low (below).

**Against it:**

- The informative evidence so far is negative: 0 of 82 outside the family, with failures at several different
  parts. The region is crowded.
- A positive would most likely be a structure of three or more links. That raises the link count from 62 to 64 or
  more and the latches from 124 to 128 or more, against DS-128's 61 and 122. It would still need a generator
  change, a rewritten c6 pass, the full gate and their reviews.
- A positive frees U8409 only. U5110, U5209 and U1415 stay open whatever it finds, and the gate needs all five.

**Judgement.** One aimed continuation is justified, because the alternative is to put a much larger question to
the owner on a result that mostly did not test what it set out to test. A second continuation is not. If the
aimed run finds no scene that passes stage 3, the design authority will propose no further placement study for
U8409.

**Estimated cost of the continuation** (estimates, from this run's times):

| Item | Estimate |
| --- | --- |
| Brief revision by the design authority, and an independent review | one short cycle; the rules change in one place (class S), which needs a reviewer |
| Run: start checks, arm 0, stage 1 from cache or re-run, stage 2b at 1200 replays, stage 3 on every passer | 1.5 to 2 hours of wall time on the same container, under the same 4.5 hour ceiling |
| Result review and disposition | one short cycle |
| Money, hardware, outside contact | none |

The result would again be bounded unless the reduced domain can be completed; the brief revision must say which.

## What this means for the open ICs and for #318

- **U8409.** Open. For the first time there are rows-level scenes with U8409 at its paper pose and no protected
  row new, shifted or lost: 24 of them, in one slot family. None passes the overlay items, so none is a candidate.
  No re-plan is found, and the search is bounded.
- **U5210.** No reading: stage 4 runs only on a scene that passes stage 3. Under the present rules it stays
  blocked with U8409, as S12 and S15 recorded.
- **U5110, U5209, U1415.** Untouched by this study. Their position is as the route costing left it
  (`mc04-route-costing-20261128.md`, Revision 2): a part route exists for U1415 only, with candidates that are not
  in the inventory.
- **The five together.** After S12 to S16, no IC of the five is placed and no route with support closes the gate
  for all five. The class-distance count (`mc04-class-distance-count-20261128.md`) adds one condition to S15's
  U8409 result and changes no verdict.
- **#318.** Stays HOLD. Check 5 stays NEEDS_DESIGN. Nothing in this result moves either.

## What is the owner's to decide

Whether to spend one more bounded run on U8409, to stop placement work and take up the stack question, or to work
on U1415's part route first. The design authority rules on evidence and rules of study; it does not choose among
these.

## Owner options

Question: What should happen next for the five open ICs after the bounded S16 result?

| # | Label | Consequence |
| --- | --- | --- |
| 1 (recommended) | Run one aimed S16 continuation | One more bounded run of about 2 hours, on slots clear of the six freed parts and of the failed slot family. A no ends placement work on U8409. Nothing changes and the order stays held. |
| 2 | Stop here; leave the ICs open | No more placement work. The paper gate fails for five ICs, the earlier alternatives to the flat-link stack return for your decision, and the prototype order review stays on hold. |
| 3 | Start with U1415's part route | An evidence task for a dual or smaller op-amp, then a room study. A new BOM line; frees U1415 at best. U8409 and the other three ICs stay open and the order stays held. |

Recommended: 1. Reason: The run spent 1087 of its 1200 replays on slots that could not pass, so U8409 is not
decided yet. One small aimed run settles it before the larger question of the stack comes to you.

Byte counts: labels 30, 29 and 29 (limit 40); consequences 184, 178 and 168 (limit 200); reason 182 (limit 200).

Not offered: accepting the 24 scenes by relaxing A8 or A9, and a re-plan of all five blocking links. The first is
growth on protected parts, which S13 and S14 spoke against and nothing on record supports. The second is the same
kind of search five times over, and S16 gives no reason to expect it to be easier. The owner can still ask for
either. Options 1 and 3 each need a design-authority brief and an independent review before anything runs. Any
adopted change is a separate reviewed generator task and an owner decision.

## Decision rows proposed for the manager

| ID | Date | Decision | Decided by | Basis | Reverse by |
| --- | --- | --- | --- | --- | --- |
| DS-210 | 2026-11-28 | MC04-S16 result accepted as rows-level geometric evidence with its bounds: `NO RE-PLAN FOUND (BOUNDED)` for U8409. 534 of 876 structures are live, 123 were searched before the 1200-replay bound and 411 were not; 24 pass A0 to A6 at rows level in one slot family, and all 24 fail A8 (C8443, the decoupler of U8413) and A9 (R7213 farther from U7204), 5 by the run and 19 by the reviewer. No scene is a candidate, U5210 has no reading, and nothing is adopted. A12, the pair ratio and checks 2 to 4 are `NOT RUN`. #318 stays HOLD | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s16-disposition-20261128.md`; `mc04-s16-report-20261128.md`; `reviews/mc04-s16-result-review-20261128.md` | Design-authority ruling |
| DS-211 | 2026-11-28 | The executor's override of STOP 1 in run 1 of the Revision 4 run was a breach of the brief. Its effect on this result is ratified after the fact: the cause was one extra key in a study control, run 1's source is retained (`5bdd8c12…f139816`) with its diff, every run 1 control and mutation equals run 2, and the stage 3 failures come from unchanged S12 code. No executor may clear a STOP itself; a second override in this campaign makes the run inadmissible. The overlay-search cap overrun (12 against 10) is an executor defect, and searches 11 and 12 are not evidence | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s16-disposition-20261128.md`; `reviews/mc04-s16-result-review-20261128.md`, findings 2 and 3 | Design-authority ruling |
| DS-212 | 2026-11-28 | Design-authority finding on the S16 brief: Ruling P3 (class S left to the replay) let 1087 of the 1200 replays go to slots on a part L03.01 displaces today, and none passed; only 82 replays tested class-S-free slots outside the one passing family, and none passed. Any continuation restores S12's strict class S preflight, leaves out E1-block slots that lie on C8443 or R7213, takes the E1 block first across its class-S-free spots, and judges every rows-level passer for A8 and A9. One aimed continuation is justified; if it finds no scene that passes stage 3, no further placement study for U8409 is proposed. The counts are read-only and not reviewed | Design authority (DS-03: Fable agent at high effort), owner notified | `mc04-s16-disposition-20261128.md` | Design-authority ruling |
| DS-213 | 2026-11-28 | Owner choice pending after S16: (1) run one aimed S16 continuation (recommended), (2) stop here and leave the ICs open, or (3) start with U1415's part route. #318 stays HOLD and no rule, part or link changes until the owner answers | Owner (pending) | `mc04-s16-disposition-20261128.md`, "Owner options" | Owner message |

## Not established

- Whether any structure of the domain passes stage 3. The run and the review show only that the 24 rows-level
  passers do not.
- Whether a class-S-free slot outside the family can pass A0 to A6: 82 tried, none passed, and the untried set is
  much larger.
- The counts in "Interpretation" and "The open domain": made read-only for this disposition, not reviewed. "Clear
  of C8443 and R7213" was computed with `links_gate.candidate` for direct cover only; a part can also be moved by
  a knock-on.
- Whether the A8 and A9 misses of the 24 scenes matter electrically.
- Anything about a gate replay, a ruled conductor order, routing, DRC or ERC for any scene.
- Whether detachment still holds after the container restart (C13 was not repeated).
