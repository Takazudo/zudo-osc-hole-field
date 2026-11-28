# MC04-S15 disposition: no-growth moves place no IC, no placement route is left under the present rules, and the next step is the owner's

2026-11-28. Issue #367 (MC-04 paper gate). Design authority under DS-03 (Fable design agent at high effort, model
`claude-fable-5-2`). Draft, uncommitted.

Subject: the S15 study at `fc457585` (study commit `dd9ef192`), run under brief Revision 3
(`82836671…8ad2c378`, admitted by DS-192). Inputs read: report `mc04-s15-report-20261128.md`
(`82e9229f…df6904ce`), result review `reviews/mc04-s15-result-review-20261128.md` (`d92d4652…ba455558`, ACCEPT WITH
CORRECTIONS, 2 blocking and 10 non-blocking findings, all applied, no verdict changed) and
`scripts/stack/studies/mc04_s15_no_growth_moves/result.json` (`e7fb8477…cf1610f3`).

This disposition changes no file but itself. Nothing is adopted. Every board and schematic stays an unvalidated
draft, check 5 stays NEEDS_DESIGN and #318 stays HOLD.

## Ruling on the result: accepted as geometric evidence, with its bounds

| IC | Link it needs | Verdict accepted | What decided it |
| --- | --- | --- | --- |
| U5110 | L12.02.01.02 | NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD) | all 16 legal slots lengthen a node (NG1); 28 more slots are illegal while the East links stand at record, and none was judged |
| U8409 | L03.01 | same | all 131 legal slots leave a displaced footprint with no free position (A3), before the no-growth rule is reached |
| U5209 | L13.01.01.02 | same | all 25 legal slots fail; 8 representatives of 32 joint-only slots were replayed in joint scenes and failed NG and A3 |
| U5210 | L13.01.01.01 | same | all 81 legal slots fail; 5358 joint-only slots were never legal in a scene, most because L03.01 cannot move |

- 487 of 487 real single moves of the six links fail. The two "passes" in the screen are record slots, not moves.
- No failure rests on the strict readings. All four strictness tallies are zero, and the reviewer set aside the
  link-end clause and the stricter limit together and still found no pass.
- Stage 4 had nothing to combine. No candidate scene exists.

**What it establishes.** With every other link at its record, no slot of the four needed links passes the
no-growth rule and S12's rules as a single move, on pad-centre geometry at courtyard level.

**What it does not establish.**

- Anything electrical. No figure here bounds capacitance, coupling, noise or stability.
- That no joint scene exists. The joint search was bounded five ways (one representative per spot, pools of 60,
  clusters, the empty L03.01 pool, failed single moves dropped). It judged 0 of U5110's 28 and 0 of U5210's 5358
  joint-only slots.
- That no placement exists outside the 35 mm radius, the three grids, the fixed non-searched links or the gate's
  own re-placement steps.
- Routing, c6, checks 2 to 4, latch access, threading, DRC and ERC: NOT RUN, as the report states.

## Interpretation: the failures are large, not marginal

1. **A link move displaces many parts, and the gate puts them back net-blind.** A failing move lengthens a median
   of 22 nets, up to 42. 193 distinct nets fail at least once. That is far from a near miss which a finer grid or a
   different pool order could turn.
2. **U8409 does not fail on the protected-part rule at all.** Every one of L03.01's 131 slots leaves some displaced
   footprint without a free position. That is the re-placement check of DS-60, older than DS-150. Loosening the
   protected rule alone does not help U8409.
3. **U5210 hangs on U8409's link.** Most of its 5358 joint-only slots collide with L03.01 at its record, and
   L03.01 has no slot to go to. S12 found the same dependency.
4. **The unjudged joint scenes are unlikely to differ, and that is a judgement, not a proof.** A joint scene moves
   two or more links, each of which fails alone on many nets. The landing of displaced parts can change in a joint
   scene, so a pass is not excluded. Nothing in four studies suggests one.
5. **The rule did what the owner asked of it.** It was the one move rule the S13 and S14 evidence could support:
   add nothing to any node. Under it the nodes cannot stay as short as they are while the connectors move.

## Four studies now agree

| Study | Rule tried | Result |
| --- | --- | --- |
| S12 | protected parts fixed, links may move to 35 mm | no scene; four census zeros |
| S13 | capacitance budget per node, as specified | no node with headroom that frees an IC |
| S14 | the same with 10 pF of feedback as a what-if | weak loops cured in the model; no IC freed |
| S15 | protected parts may move if no node grows | no single move passes; no scene |

Read together: with the link connectors where the accepted link plan puts them, board K around these four ICs
cannot hold both the connectors and the ICs while the sensitive nodes stay as they are. S12 and S15 are geometric
evidence, S13 and S14 are model evidence. None is a measurement.

U1415 is unchanged. Its blocker is L08's class distance (S12), and no study since has addressed it. Five ICs
remain open.

## No placement route remains under the present rules

**Ruling.** The design authority admits no further placement search for these ICs under the present rules, and
none under the no-growth rule. Closed are: link-only search (S12 disposition), capacitance-budget studies
(DS-186) and no-growth moves (this disposition). A wider joint search, a finer grid, another pool order or a
smarter re-placement inside the same rules is not admitted without an owner decision, because each would be
chosen after four negative results.

The no-growth rule (DS-189 to DS-191) was a rule inside the study. It lapses with the study. DS-150 stands as
written.

Every route that is left changes something only the owner can change:

| Route | What it changes | What is known |
| --- | --- | --- |
| Re-plan the blocking links | the link set and with it the workload accepted in DS-128 (61 links, 122 latches, 83 parts with cut leads) | the blockers are four connectors (L12.02.01.02, L03.01, L13.01.01.01, L13.01.01.02) and L08 for U1415; moving their signals to other links or splitting them has not been studied |
| Move the ICs, not the links | the locality rule (a far pose) | S8 and S9 found no pose within 24 mm; U5110 has a 40.61 mm far pose that needs a rule exception and a simulation (DS-149 fallback) |
| Let protected nodes grow by a bound | DS-150 | no evidence supports any growth: S13 and S14 found no headroom in the model; it does not help U8409 (point 2 above) |
| Change the circuit | a specification, the BOM, the evidence bundles | S14: 10 pF cures the weak loops in the model at about 7° of phase at 20 kHz and frees no IC; a remote buffer for U8409 and a dual op-amp for U1415 are DS-149 fallbacks, each a new evidence task |
| Leave the ICs open | nothing | check 5 fails for five ICs; the DS-60 alternatives return; #318 stays held |

Costs of the first four routes are not known. No workload, part count or study size has been worked out for any of
them.

## What this means for the order review (#318)

- #318 stays HOLD. The MC-04 paper gate cannot pass while five ICs have no pose, and no admitted work is left that
  could give them one.
- This is not a finding that the product cannot be built. It is a finding that the present link plan, the present
  protected-part rule and the present circuit do not fit together on paper for five of the ICs.
- The two open design items of DS-185 (eleven weak-loop rows; the class G stage under 4° on a weak model) stand
  regardless. They are model readings, not measured defects.

## Two executor deviations are ratified

**The dockerd restart (review finding 10).** Ratified, with this reading recorded for later briefs. A "missing
oracle" under STOP 2 means the pinned KiCad image or its `kicad-cli` cannot be provided. A docker daemon that is
not running after a VM reboot is an environment fault. An executor may start the daemon and continue if all of
these hold: the oracle then runs from the pinned digest through `scripts/kicad/run.sh`; both start checks are
repeated in full and pass; the failed try is kept and disclosed. All three held here, and the search itself is
pure Python. An executor may not change the image, the digest, the wrapper or a check to get past the start.

**The storage of bulky intermediates.** Ratified as a deviation from the brief's "Outputs". 23 files (about
71 MB), `screen.json` included, sit in the ignored `.circuit-cache/mc04-s15/` and in a verified copy at
`/mnt/project-files/osc-s15-cache/`, pinned by the tracked `bulk-manifest.json`. This follows
`circuit/ORCHESTRATION.md` section 6 and the owner's rule against committed large dumps. Conditions: the durable
copy stays until the campaign closes, and `--check` keeps reporting an absent cache as `PARTIAL CHECK` and an
altered one as a failure. The copy is the only recovery source, because a re-run cannot reproduce the hashes.

**Carried to later briefs (review finding 11).** A study pins the hashes of its own sources before the recorded
run. S15 did not, and its code was edited afterwards for storage and reporting. The unchanged 52 checkpoint digests
and the reviewer's replays stand in for that proof here; I accept them for this study.

## What is the owner's to decide

- Which of the routes above, if any, is pursued.
- Any change to DS-150, to the link plan and its DS-128 workload, to the locality rule, or to any circuit value or
  part.
- Leaving the ICs open, and with that the return of the DS-60 alternatives.

## Owner options

Question: How should the open ICs be pursued now that no connector move can place them?

| # | Label | Consequence |
| --- | --- | --- |
| 1 (recommended) | Cost the remaining routes first | A desk comparison of what is left for each IC: re-planned links, far poses, a new part, circuit changes. No search, nothing changes. You then pick with workload, parts and risk side by side. |
| 2 | Re-plan the four blocking links | One study moves the signals of the blocking connectors to other links or splits them. It changes the link count and hand work you accepted, and may still fail. No part or rule changes yet. |
| 3 | Let sensitive nodes grow a little | You set how far a protected node may lengthen, then one search. No evidence supports any growth: both simulations found no headroom. It does not help U8409, which fails an older rule. |
| 4 | Leave ICs open; order stays held | No more work on these ICs now. The paper gate fails for five ICs, the earlier alternatives to the flat-link stack return, and the prototype order review stays on hold. |

Recommended: 1. Reason: Four studies exhausted every move the rules allow. What is left changes the link plan, a
rule or the circuit, and those costs are unknown; compare them before spending a study on one.

Option 1 is a document, not a study: it runs no search and no simulation, adopts nothing, and ends in a new owner
card. Options 2 and 3 each need a design-authority brief and an independent review before anything runs. In every
case nothing is bought, built or ordered, and any adopted change is a separate reviewed generator task.

## Decision rows proposed for the manager

| ID | Decision |
| --- | --- |
| DS-193 | The S15 result at `fc457585` is accepted as geometric evidence only: all four ICs are NO SINGLE-MOVE CANDIDATE (COMPLETE SCREEN, OTHER LINKS AT RECORD), 487 of 487 real single moves fail, no candidate scene exists, and the joint search is bounded as the report states. Nothing is adopted |
| DS-194 | Interpretation: the failures are large (median 22 lengthened nets per move), U8409 fails the DS-60 re-placement check and not the protected rule, and U5210 depends on U8409's link. S12 to S15 agree that the present link plan, DS-150 and the present circuit do not fit on paper for these ICs |
| DS-195 | No further placement search for U5110, U8409, U5209 and U5210 is admitted under the present rules or under the no-growth rule. The no-growth rule (DS-189 to DS-191) lapses with the study; DS-150 stands. The route reopens only by an owner decision |
| DS-196 | STOP 2 reading: a docker daemon stopped by a VM reboot is an environment fault, not a missing oracle. The S15 restart is ratified. An executor may start the daemon if the pinned digest is used, both start checks are repeated and pass, and the failed try is disclosed |
| DS-197 | The storage of S15's bulky intermediates outside git, under a tracked manifest and a verified durable copy, is ratified as a deviation from the brief's "Outputs". The copy stays until the campaign closes. Later studies pin their own source hashes before the recorded run |
| DS-198 | Owner choice pending on the open ICs: (1) cost the remaining routes first (recommended), (2) re-plan the four blocking links, (3) let sensitive nodes grow a little, or (4) leave the ICs open with the order review held. #318 stays HOLD and no rule changes until the owner answers |

## Not established

- Any behaviour of real hardware, and any electrical property of any scene.
- That no joint scene passes the no-growth rule: 0 of U5110's 28 and 0 of U5210's 5358 joint-only slots were
  judged.
- The cost, feasibility or outcome of any remaining route. None has been studied.
- Anything about U1415 beyond the S12 result.
